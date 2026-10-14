import json
from pathlib import Path
import pytest
from amiga_reversing.tools.pandora_patrol_timing import PatrolState, tick

ROOT=Path(__file__).resolve().parents[1]
MODEL=json.loads((ROOT/'runtime/observations/pandora-world-model.json').read_text())
ACTOR=next(a for a in MODEL['actors'] if a['name']=='world_object_pianist')
DATA=(ROOT/'targets/amiga_disk_pandora-1988-firebird/targets/amiga_raw_pandora_3e1ee0f1_bk_00_000000e8/binary.bin').read_bytes()
START=ACTOR['initial_script']

def advance(s, **kw):
    return tick(DATA,s,0x10000,MODEL['opcode_values'],script_start=START,**kw)


def test_delay_two_and_one_dispatch_on_zero_call():
    s=advance(PatrolState(START,(0,0),0))
    assert (s.xy,s.delay,s.pc)==((816,728),1,START+0xA)
    s=advance(s)
    assert (s.xy,s.delay,s.pc)==((816,730),2,START+0x20)
    waiting=advance(s)
    assert waiting.xy==s.xy and waiting.delay==1 and waiting.counters==s.counters
    moving=advance(waiting)
    assert moving.xy==(816,732) and moving.delay==2


def test_whole_original_cycle_has_377_calls_and_exact_envelope():
    s=advance(PatrolState(START,(0,0),0)); initial=s
    ys=[]
    for _ in range(377):
        s=advance(s); ys.append(s.xy[1])
    assert (s.pc,s.xy,s.delay)==(initial.pc,initial.xy,initial.delay)
    assert min(ys)==728 and max(ys)==974
    assert len([y for y in ys if y==974])==32  # slow endpoint +30-call rest


@pytest.mark.parametrize('flags',[2,64,66])
def test_outer_exclusion_does_not_even_decrement_delay(flags):
    s=PatrolState(START+0x20,(816,730),2,flags=flags)
    assert advance(s)==s


def test_unknown_opcode_and_zero_budget_refuse_prediction():
    with pytest.raises(ValueError,match='unmodelled'):
        advance(PatrolState(START+2,(816,730),0))
    with pytest.raises(ValueError,match='budget'):
        advance(PatrolState(START,(0,0),0),max_commands=0)


def checkpoint():
    return json.loads((ROOT/'runtime/observations/pandora-pianist-timing.json').read_text())


def decode(phase):
    from amiga_reversing.tools.pandora_patrol_timing import state_from_capture
    fields=checkpoint()['fields']
    return state_from_capture(phase,DATA,0x10000,MODEL['opcode_values'],actor_source=ACTOR['source_offset'],script_start=START,fields=fields)


def test_five_real_consecutive_loop_transitions_match_all_mutable_counters():
    phases=checkpoint()['observation']['scenario']['phases']
    states=[decode(p) for p in phases]
    assert [s.xy[1] for s in states]==[836,834,832,830,828,826]
    for before,after in zip(states,states[1:]):
        predicted=advance(before)
        assert predicted==after


@pytest.mark.parametrize('damage',['script','pc_identity','missing_byte','overlap'])
def test_patrol_capture_refuses_changed_script_or_unverified_or_partial_input(damage):
    p=checkpoint()['observation']['scenario']['phases'][-1]
    if damage=='script':
        read=p['capture']['memory_reads'][4]
        read['bytes']='ffff'+read['bytes'][4:]
    elif damage=='pc_identity':
        p['payload']['status']='ambiguous'
    elif damage=='missing_byte':
        p['capture']['memory_reads'][4]['bytes']=p['capture']['memory_reads'][4]['bytes'][:-2]
    else:
        read=dict(p['capture']['memory_reads'][0]);read['bytes']='ffff'+read['bytes'][4:]
        p['capture']['memory_reads'].append(read)
    with pytest.raises(ValueError):decode(p)


def test_current_gate_is_unsafe_but_rest_gate_admits_bounded_corridor_route():
    from amiga_reversing.tools.pandora_patrol_timing import assess_crossing
    from amiga_reversing.tools.pandora_world_model import move
    s=decode(checkpoint()['observation']['scenario']['phases'][-1]);pose=(780,794,'right');path=[]
    for direction,count in [('right',6),('down',1),('up',14),('right',7)]:
        for _ in range(count):
            pose,_,_=move(pose,direction);path.append((direction,pose))
    assert pose==(864,738,'right')
    assert assess_crossing(DATA,s,0x10000,MODEL['opcode_values'],path,script_start=START,max_calls_per_move=6)['status']=='unsafe'
    for _ in range(249):s=advance(s)
    assert s.xy==(816,974) and s.delay==30
    result=assess_crossing(DATA,s,0x10000,MODEL['opcode_values'],path,script_start=START,max_calls_per_move=6)
    assert result['status']=='conditional_clearance'
    assert not any(c['unsafe_calls'] for c in result['checks'])


def test_all_28_real_crossing_states_match_the_timing_bound_and_expected_positions():
    from dataclasses import replace
    r=json.loads((ROOT/'runtime/observations/pandora-pianist-crossing.json').read_text())
    def state(raw):
        return PatrolState(raw['pc'],tuple(raw['xy']),raw['delay'],{int(k):v for k,v in raw['counters'].items()},raw['flags'])
    previous=state(r['gate']);elapsed=0
    assert len(r['runtime_steps'])==28
    for row in r['runtime_steps']:
        actual=state(row['actor']);calls=row['eligible_calls_since_previous']
        assert 1<=calls<=6
        for _ in range(calls):previous=advance(previous)
        # Proximity bits4/5 are external; the outer-loop exclusion bits match.
        assert previous.flags&0x42==actual.flags&0x42
        assert replace(previous,flags=actual.flags)==actual
        assert row['player_xy']==row['expected_pose'][:2]
        assert row['ui_flags']&6==0 and row['camera_reload']==6
        previous=actual;elapsed+=calls
    assert elapsed==49 and row['player_xy']==[864,738]


def test_consistent_duplicate_capture_bytes_do_not_create_ambiguity():
    p=checkpoint()['observation']['scenario']['phases'][-1]
    expected=decode(p)
    p['capture']['memory_reads'].append(dict(p['capture']['memory_reads'][0]))
    assert decode(p)==expected


def test_same_interpreter_matches_flight_controller_without_pianist_coordinates():
    from amiga_reversing.tools.pandora_patrol_timing import state_from_capture
    r=json.loads((ROOT/'runtime/observations/pandora-corridor-actors.json').read_text())
    actor=next(a for a in MODEL['actors'] if a['name']=='world_object_flight_controller')
    phases=r['observation']['scenario']['phases']
    states=[state_from_capture(p,DATA,0x10000,MODEL['opcode_values'],actor_source=actor['source_offset'],script_start=actor['initial_script'],fields=checkpoint()['fields']) for p in phases]
    assert [(s.xy,s.delay) for s in states]==[((1104,746),1),((1104,748),2),((1104,748),1)]
    for before,after in zip(states,states[1:]):
        assert tick(DATA,before,0x10000,MODEL['opcode_values'],script_start=actor['initial_script'])==after
