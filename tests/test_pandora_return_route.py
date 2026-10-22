from amiga_reversing.tools.pandora_escape import prepare_departure,inspect_return
from amiga_reversing.tools.copperline_session import validate_capture
from amiga_reversing.tools.copperline_runtime import MAX_SCENARIO_PHASES,MAX_SCENARIO_INPUT_EVENTS,validate_memory_goal,validate_phase_occurrences


def validate_plan(s):
    names=[p['name'] for p in s['phases']]
    assert len(names)==len(set(names))<=MAX_SCENARIO_PHASES
    assert len(s['input_events'])<=MAX_SCENARIO_INPUT_EVENTS
    for p in s['phases'][1:]:
        validate_capture(p['capture']);validate_phase_occurrences(p)
        assert p.get('transition','continue')=='continue'
        if 'until_memory'in p:validate_memory_goal(p['until_memory'])
    for e in s['input_events']:assert names.index(e['after_phase'])<names.index(e['release_after_phase'])


def test_cold_preparation_preserves_unarmed_console_and_required_items():
    s=prepare_departure(cold=True);validate_plan(s)
    assert len(s['phases'])==385 and len(s['input_events'])==256
    checks=s['phases'][-1]['capture']['memory_reads']
    assert {'address':0x3D27,'size':18,'expect_hex':'00'*18,'expect_mask_hex':'ff'+'00'*17} in checks
    assert any(r.get('address')==0x3B92 and r.get('expect_hex')=='3000312624372123' for r in checks)


def test_return_inspection_uses_game_wrap_and_stops_before_unresolved_encounter():
    s=inspect_return();validate_plan(s)
    assert len(s['phases'])==55 and len(s['input_events'])==45
    assert s['phases'][0]['observable']=='verified_checkpoint'
    assert all(e['control'] in ['port1 up','port1 down','port1 left','port1 right'] for e in s['input_events'])
    wrap=next(p for p in s['phases'] if p['name']=='bottom_camera_wrap')
    assert wrap['breakpoint_stable_key']=='s0:00009966:instruction'
    assert {'address':0x5C352,'size':4,'expect_hex':'05120010'} in wrap['capture']['memory_reads']
    assert s['phases'][-1]['name']=='return_inspection_stop'
    assert any(r.get('address')==0x3D27 and r.get('expect_hex')=='00' for r in s['phases'][-1]['capture']['memory_reads'])
