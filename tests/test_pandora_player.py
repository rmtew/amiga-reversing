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


def test_movement_guards_actual_selected_item_after_inventory_action():
    p=player.PlayerPlan(modal=False,held=49,expected_health=32)
    p.select('switch',48).move_to('walk','down',[241,946])
    reads=p.scenario['phases'][-1]['capture']['memory_reads']
    assert {'address':player.PLAYER+22,'size':1,'expect_hex':'30'} in reads
    assert {'address':player.PLAYER+12,'size':2,'expect_hex':'0020'} in reads


def test_failed_move_reports_stop_state_instead_of_old_successful_move():
    old=bytearray(36);old[:4]=bytes.fromhex('042b06a2');old[12:14]=(32).to_bytes(2,'big')
    stopped=bytearray(old);stopped[:2]=(11067).to_bytes(2,'big');stopped[12:14]=(5).to_bytes(2,'big')
    def capture(block,ui):return {'memory_reads':[{'address':hex(player.PLAYER),'bytes':block.hex()},{'address':hex(player.UI),'bytes':bytes([ui]).hex()}]}
    phase={'name':'move','status':'not_hit','stable_key':'s0:00009844:instruction',
           'termination':'frame_budget_exhausted','stop_event':{'frame':10721},
           'capture':capture(old,48),'diagnostic_capture':capture(stopped,50)}
    result=player.summarize({'status':'incomplete','observation':{'scenario':{'phases':[phase]}}})['actions'][0]
    assert result['state']['health']==5 and result['state']['xy']==[11067,1698]
    assert result['reason']=='combat_blocks_movement' and result['frame']==10721
    assert result['state_origin']=='diagnostic_stop' and result['last_canonical_state']['health']==32
    stopped[12:14]=b'\x00\x00';stopped[24]=2;phase['diagnostic_capture']=capture(stopped,32)
    assert player.summarize({'status':'incomplete','observation':{'scenario':{'phases':[phase]}}})['actions'][0]['reason']=='player_dead'
