"""Finite H30/S13 boundary: original observations, never candidate equivalence."""
import copy
import json
from pathlib import Path

import pytest

from amiga_reversing.disasm.behaviour_validation import compare_ordered
from amiga_reversing.tools import copperline_bus_trace as bus,pandora_scratch_behaviour as scratch
from tests.test_behaviour_validation import ROOT

BASE=ROOT/'.runtime-state/pandora-behaviour/natural-shifted-H30-S13'


def decode(path):
    raw=json.loads(path.read_text());entry=raw['runner']['observation']['scenario']['phases'][2]
    trace=entry['chip_bus_trace'];ranges=trace['ranges']
    return entry,bus.read_bus_partitions(Path(trace['profile_request']['path']),[ranges[:2],ranges[2:]],2)


@pytest.fixture
def window():
    if not (BASE/'capture.json').exists():pytest.skip('Private H30/S13 evidence absent; no DMA case evaluated')
    return decode(BASE/'capture.json')


def test_natural_H30_S13_control_WORDs_and_four_channel_footprints(window):
    entry,profile=window;result=scratch.validate_shifted_boundary(profile,entry)
    assert result['status']=='pass' and result['observed_job_events']==960
    assert result['control_WORDs']==dict(bltcon0=0xdfca,bltcon1=0xd000,bltsize=0x782)
    assert result['masked_output_recomputation'] is False
    assert len(profile['records'])==4480 and entry['stack_return_address']=='0x0001715c'


def test_original_replay_preserves_all_ordered_ROI_events(window):
    path=BASE.with_name(BASE.name+'-replay')/'capture.json'
    if not path.exists():pytest.skip('Private replay absent; no repeatability evaluation')
    entry,profile=decode(path)
    assert scratch.validate_shifted_boundary(profile,entry)['status']=='pass'
    assert compare_ordered(scratch.semantic(window[1]['records']),scratch.semantic(profile['records']))['status']=='pass'


@pytest.mark.parametrize('failure,status',[
    ('signed_control','mismatch'),('height','mismatch'),('shift','unsupported'),
    ('row_stride','mismatch'),('source_width','mismatch'),('missing_read','mismatch'),
    ('cross_frame','unsupported'),('truncated','incomplete_truncated'),('missing_job','incomplete_truncated'),
])
def test_boundary_negatives_refuse_or_mismatch(window,failure,status):
    entry,profile=copy.deepcopy(window);job=profile['frames'][0]['blits'][0]
    if failure=='signed_control':job['bltcon0']='0x5fca'
    elif failure=='height':job['height']=32
    elif failure=='shift':entry['capture']['registers']['d6']='0x4'
    elif failure=='row_stride':job['modulos'][3]=12
    elif failure=='cross_frame':job['end_frame']+=1
    elif failure=='truncated':job['render_truncated']=True
    elif failure=='missing_job':profile['frames'][0]['blits']=profile['frames'][0]['blits'][:3]
    else:
        i=next(i for i,e in enumerate(profile['records']) if e['engine']=='blitter' and e['subtype']==1)
        if failure=='source_width':profile['records'][i]['size']=1
        else:profile['records'].pop(i)
    assert scratch.validate_shifted_boundary(profile,entry)['status']==status


def test_opaque_container_labels_do_not_define_native_frame_offsets(window):
    entry,profile=copy.deepcopy(window)
    for f in profile['frames']:f['frame']+=99
    for e in profile['records']:e['frame']+=99
    assert scratch.validate_shifted_boundary(profile,entry)['status']=='pass'


def contract_for_capture():
    path=BASE/'capture.json'
    if not path.exists():pytest.skip('Private H30/S13 evidence absent; no admission evaluated')
    p=json.loads(path.read_text())['runner']['observation']['scenario']['phases'][2]
    trace=p['chip_bus_trace'];ranges=trace['ranges']
    def regs(cap):return {k:int(cap['registers'][k],0) for k in ('a0','a1','a2','a7','d5','d6','d7')}
    cp=ROOT/'.runtime-state/pandora-span-trace/route/post-route-checkpoint.json'
    receipt=json.loads(cp.read_text())
    contract=dict(contract_id=scratch.SHIFTED_BOUNDARY,entry_registers=regs(p['capture']),
        first_entry_registers=regs(p['first_capture']),checkpoint_receipt_sha256=scratch.sha(cp),
        trace_request=trace['requested_trace'],resolved_ranges=ranges,
        analysis_partitions=[ranges[:2],ranges[2:]],maximum_analysis_records=8192,expected_window_records=4480)
    original=(ROOT/'targets/amiga_disk_pandora-1988-firebird/targets/amiga_raw_pandora_3e1ee0f1_bk_00_000000e8/binary.bin').read_bytes()
    return path,contract,receipt,original


def test_complete_capture_admission_includes_caller_and_immutable_bytes():
    path,contract,receipt,original=contract_for_capture()
    entry,profile,identity=scratch.read_capture(path,original,contract,receipt)
    assert identity==scratch.sha(path) and len(profile['records'])==4480
    assert entry['payload']['payload_offset']=='0x6a1e'


@pytest.mark.parametrize('failure,status', [('caller','stale'),('return_bytes','missing_prerequisite'),
    ('first_geometry','unsupported'),('anchor','incomplete_truncated')])
def test_capture_admission_refuses_wrong_context(tmp_path,failure,status):
    path,contract,receipt,original=contract_for_capture();raw=json.loads(path.read_text())
    phases=raw['runner']['observation']['scenario']['phases'];entry=phases[2]
    if failure=='caller':entry['stack_return_address']='0x00017090'
    elif failure=='return_bytes':
        sp=int(entry['capture']['registers']['a7'],0)
        read=next(r for r in entry['capture']['memory_reads'] if int(r['address'],0)==sp)
        read['bytes']='00017090'+read['bytes'][8:]
    elif failure=='first_geometry':entry['first_capture']['registers']['d7']='0x1e'
    else:phases[1]['stable_key']='s0:00006A1E:instruction'
    mutated=tmp_path/'mutated.json';mutated.write_text(json.dumps(raw))
    with pytest.raises(scratch.BehaviourError) as exc:scratch.read_capture(mutated,original,contract,receipt)
    assert exc.value.result['status']==status
