import hashlib
import json
from pathlib import Path

import pytest

from amiga_reversing.tools.pandora_camera_timing import Camera,decode,idle_tick,call_windows
from amiga_reversing.tools.pandora_volume_local_compare import load_context,load_engine,compare_store

ROOT=Path(__file__).resolve().parents[1]
DATA=(ROOT/'targets/amiga_disk_pandora-1988-firebird/targets/amiga_raw_pandora_3e1ee0f1_bk_00_000000e8/binary.bin').read_bytes()
CAM=json.loads((ROOT/'runtime/observations/pandora-camera-return-boundary.json').read_text())
LOCAL=json.loads((ROOT/'runtime/observations/pandora-volume-local-comparison.json').read_text())
CONTEXT=ROOT/'runtime/observations/pandora-volume-local-context.json'


def test_seven_real_idle_transitions_match_countdown_scroll_and_mutable_delay():
    phases=CAM['camera_idle']['observation']['scenario']['phases'];profiles={int(k):tuple(v) for k,v in CAM['rule_sources']['profiles'].items()}
    states=[decode(p,profiles=profiles) for p in phases]
    assert len(states)==8
    assert [s.remaining for s in states]==[5,4,3,2,1,0,255,254]
    assert [s.x for s in states]==[976,992,1008,1024,1040,1040,1040,1040]
    assert states[0].script_delay==2 and states[-1].script_delay==1
    assert all(idle_tick(a)==b for a,b in zip(states,states[1:]))


def test_cumulative_bound_fits_forward_and_reverse_observations_without_qualifying_health():
    forward=CAM['forward_crossing_validation'];c=Camera(**forward['camera_start'])
    path=[(p['direction'],p['pose']) for p in json.loads((ROOT/'runtime/observations/pandora-rifle-composition.json').read_text())['flight_timing']['proof']['checks']]
    result=call_windows(c,path)
    assert result==forward['bound'] and result['max_calls_through_final_wait']==45
    assert forward['actual_eligible_calls']==41
    reverse=CAM['reverse_timing'];result=call_windows(Camera(**reverse['plan']['camera']),reverse['plan']['path'])
    assert result==reverse['plan']['camera_bound'] and result['max_calls_through_final_wait']==68
    assert reverse['actual_eligible_calls']==64
    assert all(r['window'][0]<=r['cumulative_calls']<=r['window'][1] for r in reverse['actual_move_calls'])
    stop=CAM['guarded_return_stop']['last_phase']
    assert stop['name']=='reverse_34_up' and stop['termination']=='capture_expectation_mismatch'
    assert next(r['bytes'] for r in stop['capture']['memory_reads'] if r['address']=='0x0005c35e')=='002c'
    assert CAM['guarded_return_stop']['snapshot_saved'] is False


def test_security_cause_is_an_observed_normal_store_not_a_synthesized_branch():
    c=CAM['security_cause'];p=c['phase'];registers=p['capture']['registers']
    assert p['status']=='hit' and p['payload']['payload_offset']=='0x887c'
    assert int(registers['a5'],0)==0x5c322 and int(registers['d0'],0)&255==44
    assert p['capture']['memory_reads'][1]['bytes']=='005f'
    assert c['HP_before']-c['D0_pending_HP']==51 and c['zone']==0
    start=c['clearance_table_source_offset'];assert list(DATA[start:start+6])==c['clearance_tier']
    assert c['Amy_ID_54_accepted'] is False and not 48<=54<54


def test_exhaustive_store_receipt_does_not_claim_whole_routine_or_gameplay_success():
    store=LOCAL['BYTE_instruction_comparison']
    assert store['initial_words_tested']==65536 and store['write_width']==1
    expected=b''.join((0x4000|(v&255)).to_bytes(2,'big') for v in range(65536))
    assert store['outputs_sha256']==hashlib.sha256(expected).hexdigest()
    failure=LOCAL['routine_comparison']
    assert failure['status']=='refused_generated_simulator_bit_memory_width'
    assert failure['expected_flag_write_width']==1 and failure['observed_flag_write_width']==4
    assert LOCAL['cases_before_refusal']==[]


def test_actual_generated_move_executor_preserves_byte_lane_and_guards():
    library=ROOT/'src/build/libamiga_backend.so'
    if not library.exists():pytest.skip('native generated backend not built')
    _,_,regs=load_context(CONTEXT,DATA);derived=bytearray(DATA);derived[0x552f0:0x552f8]=bytes.fromhex(LOCAL['BYTE_instruction_comparison']['derived_instruction'])
    result=compare_store(load_engine(library),DATA,bytes(derived),regs,values=[0,6,0x40,0xff,0x1234,0xaa55,0xffff])
    assert result['initial_words_tested']==7 and result['guards_unchanged']


def test_width_fixed_routine_receipt_preserves_store_proof_and_refuses_new_contract_failure():
    result=json.loads((ROOT/'runtime/observations/pandora-volume-local-comparison-width-fixed.json').read_text())
    assert result['BYTE_instruction_comparison']==LOCAL['BYTE_instruction_comparison']
    assert result['routine_comparison']['accepted_cases']==8
    dead=[c for c in result['accepted_cases'] if c['BYTE_writer_executed_locally']]
    assert len(dead)==5 and all(c['steps_per_layout']==26 and c['CPU_state_equal'] for c in dead)
    assert [c['logical_output'] for c in dead]==['4040','4006','40ff','4055','40ff']
    failure,=result['routine_comparison']['refused_cases']
    assert failure['status']=='refused_local_routine_contract'
    assert failure['case']=='alive_near_armed' and failure['shared_flag_write_width']==1
    assert failure['expected_logical_word']==53 and failure['observed_logical_word']==64


def test_arithmetic_fixed_receipt_qualifies_all_bounded_routine_cases():
    result=json.loads((ROOT/'runtime/observations/pandora-volume-local-comparison-arithmetic-fixed.json').read_text())
    assert result['BYTE_instruction_comparison']==LOCAL['BYTE_instruction_comparison']
    assert result['status']=='bounded_local_routine_and_BYTE_equivalence'
    assert result['routine_comparison']=={'status':'bounded_CPU_only_routine_equivalence',
                                           'accepted_cases':9,'refused_cases':[]}
    near=next(c for c in result['accepted_cases'] if c['name']=='alive_near_armed')
    assert near['logical_output']=='0035' and near['CPU_state_equal']
    assert sum(c['BYTE_writer_executed_locally'] for c in result['accepted_cases'])==5


def test_corrected_native_near_routine_takes_absolute_distance_and_returns():
    from amiga_reversing.tools.pandora_volume_local_compare import execute
    library=ROOT/'src/build/libamiga_backend.so'
    if not library.exists():pytest.skip('native generated backend not built')
    _,projection,regs=load_context(CONTEXT,DATA)
    r=execute(load_engine(library),DATA,projection,regs,relocated=False,dead=False,armed=True,volume=64,xy=(808,154))
    assert r['logical_word']==53 and r['state']['pc']==0x800
    assert 0x65316 in r['pcs'] and 0x65320 in r['pcs']  # both negative deltas must be negated
    assert not r['BYTE_writer_executed']


@pytest.mark.parametrize('volume',[0x40,6,0x1ff,0xaa55,0xffff])
def test_fixed_native_guarded_dead_routine_reaches_writer_and_returns(volume):
    from amiga_reversing.tools.pandora_volume_local_compare import execute
    library=ROOT/'src/build/libamiga_backend.so'
    if not library.exists():pytest.skip('native generated backend not built')
    _,projection,regs=load_context(CONTEXT,DATA)
    derived=bytearray(DATA)
    # CPU regression isolates the BYTE relocation. The real report separately
    # validates and executes the complete manifest, including all five rewrites.
    derived[0x552f0:0x552f8]=bytes.fromhex(LOCAL['BYTE_instruction_comparison']['derived_instruction'])
    run=load_engine(library)
    a=execute(run,DATA,projection,regs,relocated=False,dead=True,armed=True,volume=volume)
    b=execute(run,bytes(derived),projection,regs,relocated=True,dead=True,armed=True,volume=volume)
    assert a['BYTE_writer_executed'] and b['BYTE_writer_executed']
    assert a['steps']==b['steps']==26 and a['state']['pc']==0x800
    assert a['logical_word']==b['logical_word']==(0x4000|(volume&255))
    assert (a['state'],a['effects'],a['pcs'])==(b['state'],b['effects'],b['pcs'])


@pytest.mark.parametrize('damage',['identity','copy','live_code','missing_input'])
def test_local_comparison_refuses_unverified_or_incomplete_donor(tmp_path,damage):
    r=json.loads(CONTEXT.read_text());p=r['observation']['scenario']['phases'][0]
    if damage=='identity':p['payload']['status']='ambiguous'
    elif damage=='copy':r['observation']['reverse_boundary']['materialization']['copied_sha256']='0'*64
    elif damage=='live_code':p['capture']['memory_reads'][0]['bytes']='ffff'+p['capture']['memory_reads'][0]['bytes'][4:]
    else:p['capture']['memory_reads'].pop(7)
    file=tmp_path/'donor.json';file.write_text(json.dumps(r))
    with pytest.raises(ValueError):load_context(file,DATA)


def test_partial_cli_result_is_a_nonzero_refusal(monkeypatch,tmp_path):
    from amiga_reversing.tools import pandora_volume_local_compare as tool
    monkeypatch.setattr(tool,'compare',lambda *a:LOCAL)
    output=tmp_path/'result.json'
    assert tool.main(['--target','unused','--context','unused','--manifest','unused','--output',str(output)])==2
    assert json.loads(output.read_text())['routine_comparison']['status'].startswith('refused_')
