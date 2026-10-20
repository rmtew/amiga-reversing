"""Finite DMA job/consumer predicates; private evidence never becomes test data."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from amiga_reversing.disasm import behaviour_validation as bv
from amiga_reversing.tools import copperline_bus_trace as bus,pandora_scratch_behaviour as scratch
from tests.test_behaviour_validation import DATA,ROOT
from tests.test_behaviour_identity_regressions import TARGET

CAPTURE=ROOT/'.runtime-state/pandora-behaviour/scratch-second-entry-boundary/capture.json'


@pytest.fixture
def window():
    if not CAPTURE.exists():pytest.skip('Private second-buffer fixture absent; no DMA case evaluated')
    phase=json.loads(CAPTURE.read_text())['runner']['observation']['scenario']['phases'][1]
    trace=phase['chip_bus_trace'];ranges=trace['ranges']
    tail=dict(name='world_destination_tail',address=ranges[-1]['address']+4096,length=1024)
    profile=bus.read_bus_partitions(Path(trace['profile_request']['path']),[ranges[:3],ranges[3:],[tail]],2)
    return phase,profile


def final_writes(profile):
    return {e['address']:e['data'] for e in profile['records'] if e['access']=='write'}


def test_five_jobs_and_prefetched_FIFO_feed_the_second_destination(window):
    entry,profile=window;result=scratch.validate_second_buffer_window(profile,entry)
    assert result['status']=='pass' and result['configured_jobs_checked']==5
    assert result['observed_job_events']==1280 and result['destination_FIFO_pairs']==128
    assert result['observed_maximum_pending_reads']==2
    assert len(profile['records'])==5120
    assert scratch.validate_renderer_stream([e for e in profile['records'] if 'shared_scratch' in e['ranges']])['status']=='pass'


def test_profile_container_labels_do_not_define_a_global_native_frame_offset(window):
    entry,profile=window;profile=copy.deepcopy(profile)
    for frame in profile['frames']:frame['frame']+=37
    for e in profile['records']:e['frame']+=37
    result=scratch.validate_second_buffer_window(profile,entry)
    assert result['status']=='pass'
    assert result['frame_association']['native_entry_frame']==entry['stop_event']['frame']
    assert result['frame_association']['profile_container_frame']==profile['frames'][0]['frame']


@pytest.mark.parametrize('failure,status',[
    ('modulo','mismatch'),('descending','unsupported'),('truncated','incomplete_truncated'),
    ('cross_frame','unsupported'),('missing_job','incomplete_truncated'),
    ('source_width','mismatch'),('missing_source','mismatch'),
])
def test_job_and_source_boundaries_fail_closed(window,failure,status):
    entry,profile=window;profile=copy.deepcopy(profile);job=profile['frames'][0]['blits'][0]
    if failure=='modulo':job['modulos'][1]+=2
    elif failure=='descending':job['descending']=True
    elif failure=='truncated':job['render_truncated']=True
    elif failure=='cross_frame':job['end_frame']+=1
    elif failure=='missing_job':profile['frames'][0]['blits']=profile['frames'][0]['blits'][:4]
    else:
        i=next(i for i,e in enumerate(profile['records']) if e['engine']=='blitter' and e['subtype']==1)
        if failure=='source_width':profile['records'][i]['size']=1
        else:profile['records'].pop(i)
    assert scratch.validate_second_buffer_window(profile,entry)['status']==status


def copy_positions(profile):
    return [i for i,e in enumerate(profile['records']) if e['engine']=='blitter'
            and ((e['access']=='read' and 'shared_scratch' in e['ranges'])
                 or (e['access']=='write' and e['address']==0x7aa80))][:3]


def test_equal_final_buffer_cannot_excuse_a_write_before_its_consumer_read(window):
    entry,profile=window;bad=copy.deepcopy(profile);positions=copy_positions(bad)
    events=[bad['records'][i] for i in positions]
    assert [e['access'] for e in events]==['read','read','write']
    for i,payload in zip(positions,[events[2],events[0],events[1]]):
        position={k:bad['records'][i][k] for k in ('frame','row','hpos')}
        bad['records'][i]=dict(payload,**position)
    assert final_writes(bad)==final_writes(profile)
    assert scratch.validate_renderer_stream([e for e in bad['records'] if 'shared_scratch' in e['ranges']])['status']=='pass'
    result=scratch.validate_second_buffer_window(bad,entry)
    assert result['status']=='mismatch' and result['comparison_stream']=='destination_FIFO'
    assert result['first_divergence']==0


def test_transient_wrong_copy_value_fails_even_when_a_later_blit_repairs_it(window):
    entry,profile=window;bad=copy.deepcopy(profile)
    i=copy_positions(bad)[2];bad['records'][i]['data']=hex(int(bad['records'][i]['data'],0)^1)
    assert final_writes(bad)==final_writes(profile)
    result=scratch.validate_second_buffer_window(bad,entry)
    assert result['status']=='mismatch' and result['comparison_stream']=='destination_FIFO'


def test_consumed_reference_hash_must_match_the_reviewed_baseline(tmp_path,monkeypatch):
    monkeypatch.setattr(scratch,'PROJECT_ROOT',tmp_path)
    scenario=tmp_path/'runtime/scenarios/model.json';scenario.parent.mkdir(parents=True);scenario.write_text('{}')
    binding=dict(profile=scratch.checkpoint.PROFILE,contract_id='pandora',derived_manifest_sha256=None,
                 target_id=TARGET,payload_sha256=hashlib.sha256(DATA).hexdigest())
    receipt=tmp_path/'.runtime-state/checkpoint.json';receipt.parent.mkdir();receipt.write_text(json.dumps(dict(binding=binding)))
    baseline=tmp_path/'.runtime-state/reference.json';baseline.write_bytes(b'reviewed snapshot')
    contract=dict(contract_id='pandora.scratch.second-word.v1',entry_source=0x6c60,
        scenario_file=str(scenario.relative_to(tmp_path)),scenario_sha256=scratch.sha(scenario),
        checkpoint_receipt=str(receipt.relative_to(tmp_path)),checkpoint_receipt_sha256=scratch.sha(receipt),
        baseline_capture=str(baseline.relative_to(tmp_path)),baseline_capture_sha256=scratch.sha(baseline))
    monkeypatch.setattr(scratch.checkpoint,'read_checkpoint',lambda *args:dict(snapshot_sha256=bv.digest('model')))
    def read(*args):return None,None,bv.digest('different consumed reference')
    monkeypatch.setattr(scratch,'read_capture',read)
    with pytest.raises(bv.BehaviourError) as exc:scratch.evaluate(TARGET,baseline,dict(contract=contract),'revision')
    assert exc.value.result['status']=='stale' and 'Consumed baseline' in exc.value.result['reason']
