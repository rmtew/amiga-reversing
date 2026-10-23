from amiga_reversing.tools.pandora_icelord import cold_fight,fight
from amiga_reversing.tools.copperline_session import validate_capture


def test_icelord_route_fits_existing_phase_and_runner_event_limits():
    s=cold_fight();names=[p['name'] for p in s['phases']]
    assert len(names)==len(set(names))<=64
    assert 32<len(s['input_events'])<=64
    for p in s['phases'][1:]:validate_capture(p['capture'])
    for e in s['input_events']:
        assert names.index(e['after_phase'])<names.index(e['release_after_phase'])


def test_combat_waits_for_reachable_charge24_and_signed_defeat_flag():
    s=fight()
    charges=[p for p in s['phases'] if p['name'].startswith('charge_')]
    assert len(charges)==5
    assert all(p['until_memory']['expect_hex']=='0018' for p in charges)
    assert s['phases'][-1]['until_memory']=={'address':0x59D7A+72,'size':1,'expect_hex':'02','expect_mask_hex':'02'}
    # Enemy HP underflows on the fifth hit; zero HP is not the defeat oracle.
    assert s['phases'][-1]['breakpoint_stable_key']=='s0:000005D6:instruction'
