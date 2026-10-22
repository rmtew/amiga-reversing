import pytest
from amiga_reversing.tools import pandora_player as player
from amiga_reversing.tools.copperline_session import validate_capture
from amiga_reversing.tools.copperline_runtime import validate_memory_goal


def test_plans_use_supported_capture_guards_and_bounded_goals():
    for make in [player.card_interaction,player.northern_approach,player.inventory_deposit,player.walkthrough,lambda:player.walkthrough(provision=True)]:
        plan=make();names=[p['name'] for p in plan['phases']]
        assert len(names)==len(set(names))
        for p in plan['phases'][1:]:
            validate_capture(p['capture'])
            if 'until_memory'in p:
                validate_memory_goal(p['until_memory'])
                assert p['max_frames']>0 and 1<=p['occurrences']<=64
        for e in plan['input_events']:
            assert names.index(e['after_phase'])<names.index(e['release_after_phase'])


def test_cursor_action_brakes_then_settles_before_selecting():
    s=player.card_interaction();ph={p['name']:p for p in s['phases']}
    assert ph['cursor_to_192_147_down_brake']['until_memory']['expect_hex']=='00c00091'
    assert ph['cursor_to_192_147_down_settled']['until_memory']['expect_hex']=='00c00093'
    e=next(e for e in s['input_events'] if e['control']=='port1 down')
    assert e['release_after_phase']=='cursor_to_192_147_down_brake'


def test_observer_does_not_turn_dead_snapshot_into_success():
    block=bytearray(36);block[24]=2
    report={'status':'incomplete','observation':{'scenario':{'phases':[{
        'name':'move','status':'not_hit','termination':'frame_budget_exhausted',
        'diagnostic_capture':{'memory_reads':[{'address':hex(player.PLAYER),'bytes':block.hex()}]}}]}}}
    r=player.summarize(report)
    assert r['status']=='incomplete' and r['actions'][0]['reason']=='player_dead'
