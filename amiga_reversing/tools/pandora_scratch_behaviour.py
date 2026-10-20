"""Bounded original Copperline scratch contract, not candidate equivalence.

Capture with the public copperline_session scenario first. This evaluator reuses
checkpoint admission and re-decodes the owned full bus sidecars. It never edits,
executes or publishes a guest image/state, and never seeds unknown scratch bytes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from amiga_reversing.disasm.behaviour_validation import (
    BehaviourError, LoadedSource, check_producer_consumer, compare_ordered, digest,
)
from amiga_reversing.disasm.project_paths import PROJECT_ROOT, resolve_project_paths
from amiga_reversing.disasm import behaviour_validation as checks
from amiga_reversing.tools import copperline_checkpoint as checkpoint
from amiga_reversing.tools.copperline_bus_trace import read_bus_profile
from amiga_reversing.tools import copperline_bus_trace
from amiga_reversing.tools.copperline_control import CopperlineError

LOADED_SOURCE=LoadedSource(__file__)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def owned(path):
    path=(PROJECT_ROOT/path).resolve()
    if not path.is_relative_to((PROJECT_ROOT/'.runtime-state').resolve()):
        raise BehaviourError('unsupported','Scratch evidence must stay in owned local runtime storage')
    return path


def read_capture(path, original, contract, receipt):
    if path.stat().st_size>8_000_000:
        raise BehaviourError('incomplete_truncated','Capture exceeds bounded evidence size')
    encoded=path.read_bytes();capture_sha256=hashlib.sha256(encoded).hexdigest()
    raw=json.loads(encoded);o=raw.get('runner',{}).get('observation',{})
    phases=o.get('scenario',{}).get('phases',[])
    if raw.get('runner',{}).get('status')!='ok' or o.get('status')!='ok':
        if any(p.get('status')=='timeout' for p in phases):
            status='timeout_not_observed_within_bounds'
        elif any('expectation_mismatch' in p.get('termination','') for p in phases):
            status='mismatch'
        elif any(p.get('chip_bus_trace',{}).get('status')=='unavailable' for p in phases):
            status='unsupported'
        else:
            status='incomplete_truncated'
        raise BehaviourError(status,'Canonical scenario did not complete')
    if (len(phases)!=3 or [p.get('stable_key') for p in phases]!=
            ['s0:000005D6:instruction','s0:00006C60:instruction','s0:000005D6:instruction']
            or any(p.get('status')!='hit' for p in phases)):
        raise BehaviourError('incomplete_truncated','Requires all three canonical scenario anchors')
    identity=hashlib.sha256(original).hexdigest()
    if (o.get('direct_payload_handoff',{}).get('status')!='verified'
            or o['direct_payload_handoff'].get('payload_sha256')!=identity
            or o.get('checkpoint',{}).get('status')!='restored'
            or o['checkpoint'].get('snapshot_sha256')!=receipt['snapshot_sha256']
            or o['checkpoint'].get('receipt_sha256')!=contract['checkpoint_receipt_sha256']
            or o.get('reverse_boundary',{}).get('materialization',{}).get('copied_sha256')
            !=hashlib.sha256(original[:349040]).hexdigest()):
        raise BehaviourError('stale','Capture root, checkpoint or copied payload identity differs')
    p=phases[1];payload=p.get('payload',{});regs=p.get('capture',{}).get('registers',{})
    if (payload.get('status')!='pc_matched' or payload.get('payload_sha256')!=identity
            or payload.get('payload_offset')!='0x6c60' or int(payload.get('runtime_base','0'),0)!=0x10000
            or p.get('stack_return_address')!='0x00017090'):
        raise BehaviourError('stale','Canonical renderer/caller identity differs')
    for name,value in contract['entry_registers'].items():
        if int(regs.get(name,'-1'),0)!=value:
            raise BehaviourError('unsupported','Captured setup is outside this bounded contract',register=name)
    sp=int(regs['a7'],0)
    stack=next((r for r in p['capture']['memory_reads'] if int(r['address'],0)==sp),None)
    if not stack or bytes.fromhex(stack['bytes'])[:4]!=(0x17090).to_bytes(4,'big'):
        raise BehaviourError('missing_prerequisite','Captured caller return bytes are required')
    trace=p.get('chip_bus_trace',{})
    spec=trace.get('requested_trace',{})
    if (trace.get('status')!='captured' or spec!=dict(frames=2,wait_seconds=5,
            ranges=[dict(name='shared_scratch',address=0x1b3a8,length=768)])
            or trace.get('ranges')!=spec['ranges']):
        raise BehaviourError('incomplete_truncated','Requires the complete bounded shared-scratch profile')
    try:
        profile=read_bus_profile(owned(trace['profile_request']['path']),trace['ranges'],2)
    except CopperlineError as exc:
        raise BehaviourError('incomplete_truncated','Full bus sidecars are unsupported or incomplete',detail=str(exc)) from exc
    if profile!=trace.get('profile'):
        raise BehaviourError('stale','Reported transfers differ from re-decoded sidecars')
    if profile['omitted_matching_records'] or profile['profile_summary'].get('samples_dropped')!=0:
        raise BehaviourError('incomplete_truncated','Dropped or omitted trace records')
    return p,profile,capture_sha256


def semantic(events):
    # Native raster/frame labels remain in coverage, not silently joined to
    # different frame domains. This contract compares relative transfer order.
    return [dict(engine=e['engine'],access=e['access'],address=e['address'],
                 size=e['size'],data=e['data'],subtype=e['subtype'],reg=e['reg']) for e in events]


def validate_renderer_stream(events):
    result=check_producer_consumer(events,start=0x1b3a8,end=0x1b5a8)
    if result['status']!='pass':return result
    for index,event in enumerate(events):
        # Documented full-slot channel subtype: A=0, D=3. Retain the raw
        # register selector independently in repeatability comparisons.
        if event.get('subtype')!=(3 if event['access']=='write' else 0):
            return dict(status='mismatch',first_divergence=index,
                        reason='Requires D staging writes and A copy reads',actual=event)
    # Original named helper stages four planes as two WORDs per 16-byte row,
    # then reads the second WORD of each pair in its final A-only copy.
    expected=[dict(access='write',address=0x1b3a8+4*p+16*r+2*w,size=2)
              for p in range(4) for r in range(32) for w in range(2)]
    expected += [dict(access='read',address=0x1b3aa+4*r,size=2) for r in range(128)]
    actual=[{k:e[k] for k in ('access','address','size')} for e in events]
    shape=compare_ordered(expected,actual)
    if shape['status']!='pass':return dict(shape,reason='Renderer producer/consumer address order differs')
    return dict(result,address_order_sha256=shape['stream_sha256'])


def evaluate(target_id,capture,canonical,subject_revision):
    LOADED_SOURCE.require_current()
    checkpoint.LOADED_SOURCE.require_current()
    copperline_bus_trace.LOADED_SOURCE.require_current()
    contract=canonical['contract']
    if contract.get('contract_id')!='pandora.scratch.second-word.v1' or contract.get('entry_source')!=0x6c60:
        raise BehaviourError('unsupported','Unsupported scratch contract version/entry')
    if sha(PROJECT_ROOT/'runtime/scenarios/pandora-shared-scratch-producer-consumer.json')!=contract['scenario_sha256']:
        raise BehaviourError('stale','Reviewed scratch scenario changed')
    receipt_path=owned(contract['checkpoint_receipt'])
    if sha(receipt_path)!=contract['checkpoint_receipt_sha256']:
        raise BehaviourError('stale','Checkpoint receipt changed')
    binding=json.loads(receipt_path.read_text())['binding']
    try:
        receipt=checkpoint.read_checkpoint(receipt_path,binding)
    except CopperlineError as exc:
        raise BehaviourError('stale','Checkpoint identity or guest state changed',detail=str(exc)) from exc
    if binding.get('profile')!=checkpoint.PROFILE or binding.get('contract_id')!='pandora' or binding.get('derived_manifest_sha256') is not None:
        raise BehaviourError('unsupported','Requires the original pinned A500OCS checkpoint profile')
    original=resolve_project_paths(target_id).binary_source.path.read_bytes()
    if binding['target_id']!=target_id or binding['payload_sha256']!=hashlib.sha256(original).hexdigest():
        raise BehaviourError('stale','Checkpoint target/payload differs')
    baseline=owned(contract['baseline_capture'])
    if sha(baseline)!=contract['baseline_capture_sha256']:
        raise BehaviourError('stale','Reference original capture changed')
    old,old_profile,old_sha=read_capture(baseline,original,contract,receipt)
    current,profile,current_sha=read_capture(capture,original,contract,receipt)
    old_contract=validate_renderer_stream(old_profile['records'])
    outcome=validate_renderer_stream(profile['records'])
    repeatability=compare_ordered(semantic(old_profile['records']),semantic(profile['records']))
    if old_contract['status']!='pass':outcome=old_contract
    elif outcome['status']=='pass' and repeatability['status']!='pass':outcome=repeatability
    def frames(profile):
        return [{k:v for k,v in frame.items() if k!='blits'} for frame in profile['frames']]
    result=dict(outcome=outcome,comparison_kind='original_self_replay',candidate_equivalence=False,
        repeatability=repeatability,baseline_sha256=old_sha,capture_sha256=current_sha,
        canonical_entry=dict(stable_key=current['stable_key'],payload=current['payload'],
                             registers=current['capture']['registers'],caller_return=current['stack_return_address']),
        coverage=dict(B_ids=['B01','B02','B04','B05','B07','B08','B09'],
                      scenario='pandora-shared-scratch-producer-consumer',
                      entry_stop=current['stop_event'],frames=frames(profile),
                      requested_range=[0x1b3a8,0x1b6a8],observed_scratch_range=[0x1b3a8,0x1b5a8],
                      counts=profile['counts'],omitted_records=0),
        limits=['Original replay proves repeatability and this bounded predicate, not candidate equivalence.',
                'No original seed interpretation, unused remainder, whole-stack allocation, all-callers lifetime or relocation safety claim.',
                'CPU architectural events and physical DMA transfers are different streams; no CPU programming PC is inferred from a bus slot.',
                'Destination bitmap writes and final image equivalence are outside this scratch-only predicate.',
                'No bank30/defeat sequence, font, bank45 or EQU/RS policy coverage.'])
    identities=dict(original=binding['payload_sha256'],candidate=binding['payload_sha256'],
        fixture=digest(dict(checkpoint_sha256=contract['checkpoint_receipt_sha256'],
                            scenario_sha256=sha(PROJECT_ROOT/'runtime/scenarios/pandora-shared-scratch-producer-consumer.json'),
                            entry_registers=current['capture']['registers'])),
        contract=canonical['contract_sha256'],backend=binding['emulator_sha256'],
        profile=digest(dict(binding=binding,subject_revision=subject_revision,
                            checker_sha256=LOADED_SOURCE.require_current(),
                            shared_sha256=checks.LOADED_SOURCE.require_current(),
                            bus_decoder_sha256=copperline_bus_trace.LOADED_SOURCE.require_current(),
                            checkpoint_service_sha256=checkpoint.LOADED_SOURCE.require_current())))
    return result,identities
