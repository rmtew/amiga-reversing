from amiga_reversing.tools.pandora_completion import lieutenant
from amiga_reversing.tools.copperline_session import MAX_SCENARIO_PHASES,validate_capture


def test_required_id_route_omits_optional_fight_and_preserves_tools():
    s=lieutenant(cold=True);names=[p['name'] for p in s['phases']]
    assert len(names)==len(set(names))==69<=MAX_SCENARIO_PHASES
    assert all('icelord' not in n for n in names)
    for p in s['phases'][1:]:validate_capture(p['capture'])
    for e in s['input_events']:
        assert names.index(e['after_phase'])<names.index(e['release_after_phase'])
    checks=s['phases'][-1]['capture']['memory_reads']
    assert {'address':0x5C352+22,'size':1,'expect_hex':'31'} in checks
    assert {'address':0x3B92,'size':2,'expect_hex':'3205'} in checks


def test_commander_codes_route_preserves_both_codes_and_tools():
    from amiga_reversing.tools.pandora_completion import commander
    from amiga_reversing.tools.copperline_session import MAX_SCENARIO_INPUT_EVENTS
    s=commander(cold=True);names=[p['name'] for p in s['phases']]
    assert len(names)==len(set(names))==112<=MAX_SCENARIO_PHASES
    assert len(s['input_events'])==66<=MAX_SCENARIO_INPUT_EVENTS
    for p in s['phases'][1:]:validate_capture(p['capture'])
    for e in s['input_events']:
        assert names.index(e['after_phase'])<names.index(e['release_after_phase'])
    checks=s['phases'][-1]['capture']['memory_reads']
    assert any(r.get('expect_hex')=='3205000000002123' for r in checks)


def test_sdi_route_preserves_required_items_and_models_real_combat():
    from amiga_reversing.tools.pandora_completion import captain
    from amiga_reversing.tools.copperline_session import MAX_SCENARIO_INPUT_EVENTS
    s=captain(cold=True);names=[p['name'] for p in s['phases']]
    assert len(names)==len(set(names))==218<=MAX_SCENARIO_PHASES
    assert len(s['input_events'])==128<=MAX_SCENARIO_INPUT_EVENTS
    for p in s['phases'][1:]:validate_capture(p['capture'])
    for e in s['input_events']:
        assert names.index(e['after_phase'])<names.index(e['release_after_phase'])
    assert any(p['name']=='cp_hooligan_encounter' and p['breakpoint_stable_key']=='s0:00007792:instruction' for p in s['phases'])
    assert all(p.get('transition','continue')=='continue' for p in s['phases'])
    checks=s['phases'][-1]['capture']['memory_reads']
    assert any(r.get('expect_hex')=='3205312600002123' for r in checks)
