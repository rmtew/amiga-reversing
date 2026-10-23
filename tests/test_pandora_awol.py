from amiga_reversing.tools.pandora_awol import acquire
from amiga_reversing.tools.copperline_runtime import MAX_SCENARIO_PHASES,MAX_SCENARIO_INPUT_EVENTS
from amiga_reversing.tools.copperline_session import validate_capture


def test_awol_route_preserves_required_cards_and_uses_normal_inputs():
    scenario=acquire(cold=True)
    names=[p['name'] for p in scenario['phases']]
    assert len(names)==len(set(names))==340<=MAX_SCENARIO_PHASES
    assert len(scenario['input_events'])==217<=MAX_SCENARIO_INPUT_EVENTS
    assert all(p.get('transition','continue')=='continue' for p in scenario['phases'])
    for p in scenario['phases'][1:]:validate_capture(p['capture'])
    for event in scenario['input_events']:
        assert names.index(event['after_phase'])<names.index(event['release_after_phase'])
    checks=scenario['phases'][-1]['capture']['memory_reads']
    assert {'address':0x3B92,'size':8,'expect_hex':'3000312624372123'} in checks
    assert {'address':0x5C368,'size':1,'expect_hex':'32'} in checks


def test_awol_inventory_requires_actual_body_owner_after_proximity_update():
    phases=acquire()['phases'];names=[p['name'] for p in phases]
    ready=phases[names.index('aw_body_context_ready')]
    assert ready['breakpoint_stable_key']=='s0:000005EA:instruction'
    assert ready['until_memory']=={'address':0x3B9A,'size':4,'expect_hex':'0005aa7e'}
    assert names.index('aw_wait_kwik_kleen_east')<names.index('aw_body_context_ready')<names.index('aw_inventory_open_2')
    event=next(e for e in acquire()['input_events'] if e['release_after_phase']=='aw_inventory_open_2')
    assert event=={'after_phase':'aw_body_context_ready','control':'key 64','release_after_phase':'aw_inventory_open_2'}
