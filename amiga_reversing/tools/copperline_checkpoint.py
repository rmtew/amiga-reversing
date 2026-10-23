"""Local, content-bound checkpoints created only after verified scenarios.

Snapshots are private runtime inputs, not source artifacts or substitutes for
original-versus-derived execution. Each layout must establish its own root.
"""
import hashlib
import json
from pathlib import Path

from .copperline_control import CopperlineError
from amiga_reversing.disasm.behaviour_validation import LoadedSource

LOADED_SOURCE=LoadedSource(__file__)

PROFILE = 'A500OCS PAL 68000 512K chip + 512K slow'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def binding(session, contract, scenario):
    if session.host_directory is not None or not session.floppy0:
        raise CopperlineError('Checkpoint requires fixed direct media without a host mount')
    payload_hash=digest(session.target_payload_path)
    if payload_hash != contract.payload_sha256 or scenario.get('target_id') != contract.target_id:
        raise CopperlineError('Checkpoint target/payload differs from the direct contract')
    return {'profile':PROFILE, 'target_id':contract.target_id,
            'contract_id':contract.identifier,
            'payload_sha256':payload_hash,
            'rom_sha256':digest(session.rom_path),
            'emulator_sha256':digest(session.binary_path),
            'floppy_sha256':digest(session.floppy0),
            'derived_manifest_sha256':digest(session.derived_artifact_manifest)
                if session.derived_artifact_manifest else None,
            'runtime_view':scenario.get('symbols',{}).get('runtime_view')}


def snapshot_path(path):
    path=Path(path)
    if path.suffix != '.json':
        raise CopperlineError('Checkpoint receipt must use a .json filename')
    return path.with_suffix('.clstate')


def read_checkpoint(path, expected):
    LOADED_SOURCE.require_current()
    path=Path(path); record=json.loads(path.read_text())
    snapshot=snapshot_path(path)
    if (record.get('schema_version')!=1 or record.get('binding')!=expected
            or record.get('inputs_released') is not True
            or record.get('snapshot_sha256')!=digest(snapshot)):
        raise CopperlineError('Checkpoint identity, context or snapshot digest mismatch')
    root=record.get('root',{})
    if (root.get('handoff',{}).get('status')!='verified'
            or root.get('handoff',{}).get('payload_sha256')!=expected['payload_sha256']
            or root.get('reverse_boundary',{}).get('materialization',{}).get('status')!='verified'
            or record.get('payload',{}).get('status')!='pc_matched'):
        raise CopperlineError('Checkpoint has no verified root or canonical stopped PC')
    return record


def restore(client, path, record, scenario, payload_path, identify):
    first=scenario['phases'][0]
    if (first.get('stable_key')!=record['stable_key']
            or first.get('occurrences',1)!=1 or first.get('transition','continue')!='continue'
            or first.get('source_offset')!=int(record['payload']['payload_offset'],0)
            or first.get('breakpoint_address')!=record['registers']['pc']
            or first.get('runtime_view')!=record['runtime_view']):
        raise CopperlineError('Resume scenario must begin at the saved canonical source PC')
    client.request('state.load',{'path':str(snapshot_path(path).resolve())})
    regs=client.registers()
    if regs!=record['registers']:
        raise CopperlineError('Loaded checkpoint register state differs from receipt')
    detection=identify(client,payload_path,regs['pc'],runtime_view=first.get('runtime_view'))
    if detection!=record['payload']:
        raise CopperlineError('Loaded checkpoint canonical payload identity differs')
    client.request('reverse_anchor')
    return {'status':'restored','receipt_sha256':digest(path),
            'snapshot_sha256':record['snapshot_sha256'],
            'root_verification':'inherited_from_saved_execution',
            'reverse_anchor':'after_state_load','replay_across_load':False}


def save(client,path,context,scenario,result,handoff,boundary,*,parent=None,identify,payload_path):
    path=Path(path);snapshot=snapshot_path(path)
    if path.exists() or snapshot.exists():
        raise CopperlineError('Checkpoint destination already exists; choose a fresh name')
    phases=result['phases']
    if (not phases or len(phases)!=len(scenario['phases'])
            or any(p['status']!='hit' for p in phases)):
        raise CopperlineError('Checkpoint requires a completed, verified scenario')
    last=scenario['phases'][-1];regs=client.registers()
    detection=identify(client,payload_path,regs['pc'],runtime_view=last.get('runtime_view'))
    if (detection.get('status')!='pc_matched'
            or int(detection['payload_offset'],0)!=last['source_offset']
            or regs['pc']!=last['breakpoint_address']):
        raise CopperlineError('Checkpoint needs exact final canonical source identity')
    root=parent['root'] if parent else {'handoff':handoff,'reverse_boundary':boundary}
    if (root.get('handoff',{}).get('status')!='verified'
            or root.get('handoff',{}).get('payload_sha256')!=context['payload_sha256']
            or root.get('reverse_boundary',{}).get('materialization',{}).get('status')!='verified'):
        raise CopperlineError('Checkpoint requires matching root handoff and materialization provenance')
    path.parent.mkdir(parents=True,exist_ok=True)
    client.request('state.save',{'path':str(snapshot.resolve())})
    if client.registers()!=regs:
        raise CopperlineError('State changed while saving checkpoint')
    record={'schema_version':1,'binding':context,'inputs_released':True,
            'snapshot_sha256':digest(snapshot),'stable_key':last['stable_key'],
            'runtime_view':last.get('runtime_view'),'registers':regs,'payload':detection,
            'root':root,'parent_snapshot_sha256':parent['snapshot_sha256'] if parent else None,
            'scenario_sha256':hashlib.sha256(json.dumps(scenario,sort_keys=True).encode()).hexdigest(),
            'completed_phases':[{'name':p['name'],'payload':p['payload']} for p in phases]}
    path.write_text(json.dumps(record,indent=2)+'\n')
    return {'status':'saved','receipt':str(path),'receipt_sha256':digest(path),
            'snapshot_sha256':record['snapshot_sha256'],'stable_key':last['stable_key']}
