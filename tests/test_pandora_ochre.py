from amiga_reversing.tools.pandora_ochre import approach
from amiga_reversing.tools.copperline_session import validate_capture
from amiga_reversing.tools.copperline_runtime import (
    MAX_SCENARIO_PHASES, MAX_SCENARIO_INPUT_EVENTS,
    validate_memory_goal, validate_phase_frame_budget, validate_phase_occurrences,
)


def test_ochre_cold_route_has_valid_inputs_and_real_trade_postconditions():
    scenario = approach(cold=True)
    names = [p['name'] for p in scenario['phases']]
    assert len(names) == len(set(names)) == 293 <= MAX_SCENARIO_PHASES
    assert len(scenario['input_events']) == 190 <= MAX_SCENARIO_INPUT_EVENTS
    assert scenario['phases'][0]['observable'] == 'direct_payload_handoff'
    assert all(p.get('transition', 'continue') == 'continue' for p in scenario['phases'])
    for p in scenario['phases'][1:]:
        validate_capture(p['capture'])
        validate_phase_occurrences(p)
        if 'until_memory' in p:
            validate_memory_goal(p['until_memory'])
            validate_phase_frame_budget(p['max_frames'])
    for event in scenario['input_events']:
        assert names.index(event['after_phase']) < names.index(event['release_after_phase'])
    final = scenario['phases'][-1]
    trade = next(p for p in scenario['phases'] if p['name']=='oc_trade_sonicdriver_for_ochre')
    assert trade['until_memory'] == {'address': 0x5C368, 'size': 1, 'expect_hex': '24'}
    checks = final['capture']['memory_reads']
    # Equal held ID alone must not substitute for the actual exchange or item preservation.
    assert {'address': 0x1B230, 'size': 8, 'expect_hex': '060a021405280a64'} in checks
    assert {'address': 0x1B370, 'size': 8, 'expect_hex': '0028043c00000000'} in checks
    assert {'address': 0x3B92, 'size': 8, 'expect_hex': '3032312600002123'} in checks
    assert {'address': 0x5B3E4, 'size': 1, 'expect_hex': '05'} in checks
    assert any(e['control'] == 'port1 fire' and e['release_after_phase'] == trade['name']
               for e in scenario['input_events'])


def test_patrol_crossings_wait_for_observed_safe_side_before_moving():
    phases = approach()['phases']
    by_name = {p['name']: p for p in phases}
    for wait, crossing, address in [
        ('oc_wait_defence_south', 'oc_engineering_8', 0x5BAEC),
        ('oc_wait_wackobrain_south', 'oc_engineering_11', 0x5BB40),
    ]:
        p = by_name[wait]
        assert p['until_memory'] == {'address': address, 'size': 2,
                                    'expect_hex': '0500', 'expect_mask_hex': 'ff00'}
        assert p['occurrences'] == 1024 and p['max_frames'] == 1600
        assert phases.index(p) < phases.index(by_name[crossing])


def test_exchange_postconditions_are_checked_after_wait_not_on_its_first_visit():
    phases=approach()['phases']
    trade=next(p for p in phases if p['name']=='oc_trade_sonicdriver_for_ochre')
    assert not any(r.get('address') in (0x1B230,0x1B370,0x5B3E4) for r in trade['capture']['memory_reads'])
    assert phases[-1]['name']=='oc_ochre_objective' and 'until_memory' not in phases[-1]
