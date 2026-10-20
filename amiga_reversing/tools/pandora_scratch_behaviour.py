"""Bounded original Copperline scratch contract, not candidate equivalence.

Capture with the public copperline_session scenario first. This evaluator reuses
checkpoint admission and re-decodes the owned full bus sidecars. It never edits,
executes or publishes a guest image/state, and never seeds unknown scratch bytes.
"""
from __future__ import annotations

import hashlib
import json
from collections import deque
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
SECOND_BUFFER='pandora.scratch.second-buffer.v1'


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
    second=contract.get('contract_id')==SECOND_BUFFER
    if second:
        first=p.get('first_capture',{}).get('registers',{})
        if (p.get('occurrences_requested')!=2 or p.get('occurrences_observed')!=2
                or int(first.get('a2','-1'),0)!=contract['first_entry_destination']
                or any(first.get(k)!=regs.get(k) for k in ('d5','d6','d7','a0','a1','a7'))):
            raise BehaviourError('unsupported','Requires the two natural buffer entries with the same geometry')
    sp=int(regs['a7'],0)
    stack=next((r for r in p['capture']['memory_reads'] if int(r['address'],0)==sp),None)
    if not stack or bytes.fromhex(stack['bytes'])[:4]!=(0x17090).to_bytes(4,'big'):
        raise BehaviourError('missing_prerequisite','Captured caller return bytes are required')
    trace=p.get('chip_bus_trace',{})
    spec=trace.get('requested_trace',{})
    expected_spec=(contract['trace_request'] if second else dict(frames=2,wait_seconds=5,
            ranges=[dict(name='shared_scratch',address=0x1b3a8,length=768)]))
    resolved=contract['resolved_ranges'] if second else expected_spec['ranges']
    if (trace.get('status')!='captured' or spec!=expected_spec or trace.get('ranges')!=resolved):
        raise BehaviourError('incomplete_truncated','Requires the complete bounded shared-scratch profile')
    try:
        profile=read_bus_profile(owned(trace['profile_request']['path']),trace['ranges'],2)
    except CopperlineError as exc:
        raise BehaviourError('incomplete_truncated','Full bus sidecars are unsupported or incomplete',detail=str(exc)) from exc
    if profile!=trace.get('profile'):
        raise BehaviourError('stale','Reported transfers differ from re-decoded sidecars')
    if profile['profile_summary'].get('samples_dropped')!=0:
        raise BehaviourError('incomplete_truncated','Dropped or omitted trace records')
    if second:
        # The original four-range report is explicitly truncated. Normative
        # evidence is the complete re-decode of declared bounded partitions.
        reported=profile
        try:
            profile=copperline_bus_trace.read_bus_partitions(owned(trace['profile_request']['path']),
                contract['analysis_partitions'],2,max_total=contract['maximum_analysis_records'])
        except CopperlineError as exc:
            raise BehaviourError('incomplete_truncated','Full-sidecar partition analysis refused',detail=str(exc)) from exc
        if any(profile[k]!=reported[k] for k in ('frames','profile_summary','scanned_slots')):
            raise BehaviourError('stale','Reported and partitioned sidecar identities differ')
        if len(profile['records'])!=contract['expected_window_records']:
            raise BehaviourError('mismatch','Bounded window record count differs',expected=contract['expected_window_records'],actual=len(profile['records']))
        profile['reported_omitted_records']=reported['omitted_matching_records']
    elif profile['omitted_matching_records']:
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


def validate_second_buffer_window(profile, entry):
    """Five finite area-blit jobs, observed channel footprints and FIFO copy.

    Descriptor native frames and profile-container labels are distinct domains.
    Admit only jobs completed in the entry's native frame and declared first
    container; raster coordinates are associated within that container, without
    inferring a global frame offset or a CPU programming PC.
    """
    def number(v):
        if type(v) is int:return v
        if isinstance(v,str):return int(v,0)
        raise ValueError('Expected integer or hexadecimal field')
    try:
        regs={k:number(entry['capture']['registers'][k]) for k in ('a0','a1','a2','d5','d6','d7')}
        frame=profile['frames'][0];jobs=frame['blits'][:5];native=entry['stop_event']['frame']
        previous=(entry['stop_event']['vpos'],entry['stop_event']['hpos'])
    except (KeyError,ValueError,TypeError,IndexError):
        return dict(status='incomplete_truncated',reason='Missing bounded blit descriptors or entry')
    if (regs['d5'],regs['d6'],regs['d7'])!=(16,4,32):
        return dict(status='unsupported',reason='Only H32, shift4 and16-byte source rows are admitted')
    if len(jobs)!=5:return dict(status='incomplete_truncated',reason='Five completed job descriptors required')
    prefix_events=0;copy_events=[]
    for index,job in enumerate(jobs):
        if job.get('render_truncated') is not False:
            return dict(status='incomplete_truncated',reason='Job channel capture is truncated',descriptor_index=index)
        if any(job.get(k) is not False for k in ('line_mode','descending','fill_mode')):
            return dict(status='unsupported',reason='Only ascending unfilled area blits are admitted',descriptor_index=index)
        if job.get('start_frame')!=native or job.get('end_frame')!=native:
            return dict(status='unsupported',reason='Cross-frame descriptor association is unvalidated',descriptor_index=index)
        try:
            start=tuple(job['start']);end=tuple(job['end'])
            if (len(start)!=2 or len(end)!=2 or any(type(v) is not int for v in start+end)
                    or not previous<start<=end or not 0<=end[0]<frame['rows']
                    or not 0<=start[1]<frame['line_cck'] or not 0<=end[1]<frame['line_cck']):
                raise ValueError('Invalid job raster bounds')
            actual={k:job[k] for k in ('width_words','height','channels','captured_words','modulos')}
            actual.update({k:number(job[k]) for k in ('apt','dpt','bltcon0','bltcon1')})
            actual['masks']=[number(v) for v in job['masks']]
            if index<4:actual.update({k:number(job[k]) for k in ('bpt','cpt')})
        except (KeyError,ValueError,TypeError):
            return dict(status='incomplete_truncated',reason='Incomplete job geometry',descriptor_index=index)
        expected=dict(width_words=2,height=32,channels=[True]*4,captured_words=[64]*4,
            modulos=[0,12,156,12],apt=regs['a1'],bpt=regs['a0']+2*index,
            cpt=regs['a2']-2+40*index,dpt=0x1b3a8+4*index,
            bltcon0=0x4fca,bltcon1=0x4000,masks=[65535,0]) if index<4 else dict(
            width_words=1,height=128,channels=[True,False,False,True],captured_words=[128,0,0,128],
            modulos=[2,12,156,38],apt=0x1b3aa,dpt=regs['a2'],bltcon0=0x09f0,bltcon1=0x4000,masks=[65535]*2)
        if actual!=expected:
            return dict(status='mismatch',comparison_stream='blit_descriptor',first_divergence=index,
                        reason='Configured job differs from the bounded contract',expected=expected,actual=actual)
        events=[e for e in profile['records'] if e['engine']=='blitter' and e['frame']==frame['frame']
                and start<=(e['row'],e['hpos'])<=end]
        channels=range(4) if index<4 else (0,3)
        layouts=((regs['a1'],4),(regs['a0']+2*index,16),(regs['a2']-2+40*index,160),(0x1b3a8+4*index,16)) if index<4 else ((0x1b3aa,4),(0,0),(0,0),(regs['a2'],40))
        if any(e['subtype'] not in channels for e in events):
            return dict(status='mismatch',reason='Unexpected observed channel in job',descriptor_index=index)
        for channel in channels:
            base,stride=layouts[channel];width=2 if index<4 else 1;height=32 if index<4 else 128
            expected_events=[dict(address=base+stride*r+2*w,size=2,reg=(0x50,0x4c,0x48,0x54)[channel],
                                  access='write' if channel==3 else 'read') for r in range(height) for w in range(width)]
            observed=[{k:e[k] for k in ('address','size','reg','access')} for e in events if e['subtype']==channel]
            comparison=compare_ordered(expected_events,observed)
            if comparison['status']!='pass':return dict(comparison,reason='Observed channel footprint/order differs',descriptor_index=index,channel=channel)
        prefix_events+=len(events);previous=end
        if index==4:copy_events=events
    pending=deque();reads=writes=maximum=0
    for i,e in enumerate(copy_events):
        if e['subtype']==0:
            pending.append((regs['a2']+40*reads,int(e['data'],0)));reads+=1;maximum=max(maximum,len(pending))
        elif not pending:
            return dict(status='mismatch',comparison_stream='destination_FIFO',descriptor_index=4,first_divergence=i,reason='Destination write precedes its scratch read')
        else:
            expected=pending.popleft();actual=(e['address'],int(e['data'],0))
            if actual!=expected:return dict(status='mismatch',comparison_stream='destination_FIFO',descriptor_index=4,first_divergence=i,reason='FIFO destination address/value differs',expected=expected,actual=actual)
            writes+=1
    if pending or reads!=128 or writes!=128:
        return dict(status='incomplete_truncated',reason='Scratch-to-destination FIFO did not drain',reads=reads,writes=writes)
    return dict(status='pass',configured_jobs_checked=5,observed_job_events=prefix_events,
                mask_reads=256,pixel_reads=256,background_reads=256,destination_FIFO_pairs=128,
                observed_maximum_pending_reads=maximum,
                frame_association=dict(native_entry_frame=native,profile_container_frame=frame['frame'],
                                       scope='Declared container and within-frame raster bounds only; no global offset inferred'))


def evaluate(target_id,capture,canonical,subject_revision):
    LOADED_SOURCE.require_current()
    checkpoint.LOADED_SOURCE.require_current()
    copperline_bus_trace.LOADED_SOURCE.require_current()
    contract=canonical['contract']
    second=contract.get('contract_id')==SECOND_BUFFER
    if contract.get('contract_id') not in ('pandora.scratch.second-word.v1',SECOND_BUFFER) or contract.get('entry_source')!=0x6c60:
        raise BehaviourError('unsupported','Unsupported scratch contract version/entry')
    scenario=(PROJECT_ROOT/contract.get('scenario_file','runtime/scenarios/pandora-shared-scratch-producer-consumer.json')).resolve()
    if not scenario.is_relative_to((PROJECT_ROOT/'runtime/scenarios').resolve()):
        raise BehaviourError('unsupported','Scenario must stay in canonical runtime scenarios')
    scenario_identity=sha(scenario)
    if scenario_identity!=contract['scenario_sha256']:
        raise BehaviourError('stale','Reviewed scratch scenario changed')
    receipt_path=owned(contract['checkpoint_receipt'])
    receipt_bytes=receipt_path.read_bytes()
    if hashlib.sha256(receipt_bytes).hexdigest()!=contract['checkpoint_receipt_sha256']:
        raise BehaviourError('stale','Checkpoint receipt changed')
    binding=json.loads(receipt_bytes)['binding']
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
    if old_sha!=contract['baseline_capture_sha256']:
        raise BehaviourError('stale','Consumed baseline differs from the reviewed capture')
    current,profile,current_sha=read_capture(capture,original,contract,receipt)
    def scratch(profile):
        return [r for r in profile['records'] if 'shared_scratch' in r['ranges']]
    old_contract=validate_renderer_stream(scratch(old_profile))
    outcome=validate_renderer_stream(scratch(profile))
    destination=None
    if second:
        old_destination=validate_second_buffer_window(old_profile,old)
        destination=validate_second_buffer_window(profile,current)
        if old_contract['status']=='pass' and old_destination['status']!='pass':old_contract=old_destination
        if outcome['status']=='pass' and destination['status']!='pass':outcome=destination
    repeatability=compare_ordered(semantic(old_profile['records']),semantic(profile['records']))
    if old_contract['status']!='pass':outcome=old_contract
    elif outcome['status']=='pass' and repeatability['status']!='pass':outcome=repeatability
    if sha(scenario)!=scenario_identity:
        raise BehaviourError('stale','Reviewed scenario changed during evaluation')
    def frames(profile):
        return [{k:v for k,v in frame.items() if k!='blits'} for frame in profile['frames']]
    result=dict(outcome=outcome,comparison_kind='original_self_replay',candidate_equivalence=False,
        repeatability=repeatability,baseline_sha256=old_sha,capture_sha256=current_sha,
        canonical_entry=dict(stable_key=current['stable_key'],payload=current['payload'],
                             registers=current['capture']['registers'],caller_return=current['stack_return_address']),
        coverage=dict(B_ids=['B01','B02','B04','B05','B07','B08','B09'],
                      scenario=scenario.stem,
                      entry_stop=current['stop_event'],frames=frames(profile),
                      requested_range=[0x1b3a8,0x1b6a8],observed_scratch_range=[0x1b3a8,0x1b5a8],
                      counts=profile['counts'],omitted_records=0,
                      **(dict(window_events=len(profile['records']),configured_job_predicate=destination,
                              analysis_partitions=contract['analysis_partitions'],
                              reported_omitted_records=profile['reported_omitted_records']) if second else {})),
        limits=['Original replay proves repeatability and this bounded predicate, not candidate equivalence.',
                'No original seed interpretation, unused remainder, whole-stack allocation, all-callers lifetime or relocation safety claim.',
                'CPU architectural events and physical DMA transfers are different streams; no CPU programming PC is inferred from a bus slot.',
                'Only five configured jobs and their observed ROI channel streams/FIFO copy are attributed; later window blits are not all attributed to this call. No final pixel or global outside-ROI bounds proof.' if second else 'Destination bitmap writes and final image equivalence are outside this scratch-only predicate.',
                'Second natural buffer entry retains H32/shift4; no new height/shift boundary coverage.' if second else 'One fixed H32/shift4 fixture.',
                'No bank30/defeat sequence, font, bank45 or EQU/RS policy coverage.'])
    identities=dict(original=binding['payload_sha256'],candidate=binding['payload_sha256'],
        fixture=digest(dict(checkpoint_sha256=contract['checkpoint_receipt_sha256'],
                            scenario_sha256=scenario_identity,
                            entry_registers=current['capture']['registers'])),
        contract=canonical['contract_sha256'],backend=binding['emulator_sha256'],
        profile=digest(dict(binding=binding,subject_revision=subject_revision,
                            checker_sha256=LOADED_SOURCE.require_current(),
                            shared_sha256=checks.LOADED_SOURCE.require_current(),
                            bus_decoder_sha256=copperline_bus_trace.LOADED_SOURCE.require_current(),
                            checkpoint_service_sha256=checkpoint.LOADED_SOURCE.require_current())))
    return result,identities
