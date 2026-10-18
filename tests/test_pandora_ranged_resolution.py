"""Original complete ranged calls and hit continuation in controlled RAM.

The synthetic map/table establish admitted CPU paths, not ordinary gameplay,
DMA pixels or general ray termination. Instructions and callees remain original.
"""
import pytest

from tests.test_pandora_state_transitions import BASE,cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_message_queue import initialize,APP,HEAD,TAIL
from tests.test_pandora_render_order import sequencer

pytestmark=pytest.mark.parametrize('cpu_fixture',[0x1000000],indirect=True)
PLAYER,TABLE,AMMO=BASE+0x4C322,BASE+0x300A,BASE+0x924E
OBJ,DESC,ROOT,SAVED,INCOMING,OLD,GEOM,ACTIVE,FRAMES=range(0x90000,0x90900,0x100)
GRID,PIXELS=0x80000,BASE+0xD0A8
VISUAL,VISUAL_NODE,VISUAL_DESC=0x585B2,0x58688,0x5859A


@pytest.fixture
def shot(cpu_fixture,title_slots):
    cpu,memory,schemas,read,write,run=cpu_fixture
    obj,state,node,desc,bounds=(schemas[n] for n in ['world_object_shared_prefix','world_position_state_record','WorldPositionStateNode','world_position_descriptor_prefix','world_position_collision_bounds'])
    slots=title_slots
    cpu.d[0]=0
    assert sequencer(cpu,memory,write)(0x4D7DE,budget=4096).stop_reason==1
    def app(name,value,size=1):write(APP+slots['app_'+name],value,size)
    def v(name,size=1):return read(APP+slots['app_'+name],size)
    def prepare(*,variant=0,hp=31,item_state=100,callback=0,flags=0,interaction=0,blocked=False,matched=True):
        initialize(cpu_fixture,slots)
        app('context_flags',32);app('game_event_flags',0);app('defeated_object_count',0)
        app('ranged_weapon_fire_latched',0);app('ranged_weapon_variant_index',variant,2)
        app('ranged_hit_visual_ticks_remaining',0,2);app('input_fire_pressed_ff',255)
        app('last_accepted_move_request_x_step',7,2);app('last_accepted_move_request_y_step',0,2)
        app('tilemap_base',GRID,4);app('active_world_object_ptr_table',ACTIVE,4)
        write(PLAYER+obj['world_object_flags'],0,1)
        write(PLAYER+obj['selected_item_id'],18+variant,1)
        write(PLAYER+obj['world_x'],100,2);write(PLAYER+obj['world_y'],100,2)
        write(PLAYER+obj['item_state'],10,1)
        memory[AMMO:AMMO+2]=bytes([2,2])
        memory[GRID:GRID+4*90*129]=(PIXELS+128*(7 if blocked else 0)).to_bytes(4,'big')*(90*129)
        memory[BASE+0xA822:BASE+0xA862]=bytes(64)
        if blocked:write(BASE+0xA822,1,1)
        memory[OBJ:FRAMES+8]=bytes(FRAMES+8-OBJ)
        write(OBJ+obj['position_descriptor_ptr'],DESC);write(OBJ+obj['saved_position_state_ptr'],SAVED)
        write(OBJ+obj['interaction_completion_callback'],callback)
        write(OBJ+obj['world_object_flags'],flags,1);write(OBJ+obj['hit_points'],0xAB00|hp,2)
        write(OBJ+obj['item_state'],item_state,1)
        write(DESC+desc['position_state_ptr'],ROOT)
        write(DESC+desc['world_x'],132,2);write(DESC+desc['world_y'],104,2)
        for record,animation in [(ROOT,OLD),(SAVED,INCOMING)]:
            write(record+state['current_geometry_ptr'],GEOM)
            write(record+state['state_node_ptr'],animation)
            write(record+state['position_descriptor_ptr'],DESC)
            write(record+state['interaction_flags'],interaction,1)
            write(animation+node['mode_flags'],5,1);write(animation+node['frame_index_and_phase'],0xBEEF,2)
            write(animation+node['frame_count'],1,1);write(animation+node['phase_step'],64,1)
            write(animation+node['frame_sequence_ptr'],FRAMES)
        write(FRAMES,GEOM);write(FRAMES+4,GEOM)
        write(GEOM+bounds['world_x_extent'],20,2);write(GEOM+bounds['world_y_extent'],20,2)
        write(ACTIVE,DESC);write(ACTIVE+4,0)
        write(TABLE,PLAYER);write(TABLE+4,OBJ if matched else 0);write(TABLE+8,0)
        write(VISUAL+state['state_node_ptr'],0)
        write(0x64C0,0xDEADBEEF)
        cpu.a[5],cpu.a[6]=OBJ,APP
        return sequencer(cpu,memory,write)
    return cpu,memory,read,write,obj,state,node,desc,bounds,app,v,prepare


def test_all_item_and_health_bytes_follow_signed_result_tests_and_preserve_hp_on_fatal_branch(shot):
    cpu,memory,read,write,obj,state,node,desc,bounds,app,v,prepare=shot
    for variant,health_damage,item_damage in [(0,30,50),(1,90,100)]:
        for hp in range(256):
            advance=prepare(variant=variant,hp=hp,item_state=200)
            assert advance(0x93AC,budget=8192).stop_reason==1
            result=(hp-health_damage)&255;fatal=result==0 or result>=128
            assert read(OBJ+obj['hit_points'],2)==0xAB00|(hp if fatal else result)
            item=(200-item_damage)&255
            assert read(OBJ+obj['item_state'],1)==(item if item<128 else 0)
            assert bool(read(OBJ+obj['world_object_flags'],1)&2)==fatal
            assert v('defeated_object_count')==int(fatal)
            assert read(DESC)==(SAVED if fatal else ROOT)
        for initial in range(256):
            advance=prepare(variant=variant,hp=127,item_state=initial)
            assert advance(0x93AC,budget=8192).stop_reason==1
            result=(initial-item_damage)&255
            assert read(OBJ+obj['item_state'],1)==(result if result<128 else 0)
            assert read(OBJ+obj['hit_points'],2)==0xAB00|(127-health_damage)
            assert read(DESC)==ROOT and v('defeated_object_count')==0


def test_complete_shots_use_accepted_request_and_write_the_loaded_effect_descriptor(shot):
    cpu,memory,read,write,obj,state,node,desc,bounds,app,v,prepare=shot
    for variant in [0,1]:
        for outside in [0,1]:
            advance=prepare(variant=variant,hp=95,interaction=outside)
            assert advance(0x9250,budget=20000).stop_reason==1
            assert v('ranged_weapon_variant_index',2)==variant
            assert bytes(memory[AMMO:AMMO+2])==(b'\x01\x02' if variant==0 else b'\x02\x01')
            assert read(OBJ+obj['hit_points'],2)==0xAB00|(65 if variant==0 else 5)
            target=DESC if outside else VISUAL_DESC
            assert (read(target+4,2),read(target+6,2))==(142,114)
            if not outside:assert (read(DESC+4,2),read(DESC+6,2))==(132,104)
            assert v('ranged_hit_visual_ticks_remaining',2)==(0 if outside else 25)
            assert v('ranged_weapon_fire_latched')==1
            assert cpu.a[7]==0x9004


def test_completion_broadcast_runs_before_deactivation_without_combat_passage_reset(shot):
    cpu,memory,read,write,obj,state,node,desc,bounds,app,v,prepare=shot
    for callback,delta,passage in [(0,0,0xDEADBEEF),(BASE+0x552FC,0,0xDEADBEEF),(BASE+0x4B10A,15,0xDEADBEEF),(BASE+0x4B112,15,0xDEADBEEF),(BASE+0x4B0CE,-15,0x1E928)]:
        advance=prepare(hp=30,item_state=50,callback=callback)
        app('defeated_object_count',255)
        assert advance(0x9250,budget=20000).stop_reason==1
        assert cpu.a[5]==OBJ
        assert read(OBJ+obj['item_state'],1)==delta&255
        assert read(PLAYER+obj['item_state'],1)==(10+delta)&255
        assert read(OBJ+obj['hit_points'],2)==0xAB1E
        assert read(OBJ+obj['world_object_flags'],1)&2
        assert read(DESC)==SAVED and read(OBJ+obj['saved_position_state_ptr'])==ROOT
        assert read(INCOMING+node['frame_index_and_phase'],2)==0
        assert read(INCOMING+node['mode_flags'],1)==4
        assert v('defeated_object_count')==0
        assert read(0x64C0)==passage


def test_two_admitted_fatal_hits_exchange_states_and_count_again_despite_inactive_victim(shot):
    cpu,memory,read,write,obj,state,node,desc,bounds,app,v,prepare=shot
    advance=prepare(hp=30,item_state=50)
    assert advance(0x9250,budget=20000).stop_reason==1
    assert read(DESC)==SAVED and v('defeated_object_count')==1
    # Retain the explicit table and state flags; no world repartition is modeled.
    app('input_fire_pressed_ff',0)
    assert sequencer(cpu,memory,write)(0x9250,budget=64).stop_reason==1
    app('input_fire_pressed_ff',255)
    assert sequencer(cpu,memory,write)(0x9250,budget=20000).stop_reason==1
    assert read(DESC)==ROOT and read(OBJ+obj['saved_position_state_ptr'])==SAVED
    assert v('defeated_object_count')==2 and read(OBJ+obj['hit_points'],2)==0xAB1E
    assert read(OBJ+obj['world_object_flags'],1)&2 and read(AMMO,1)==0


def test_all_ui_and_player_flag_bytes_separate_timer_service_from_fire_release(shot):
    cpu,memory,read,write,obj,state,node,desc,bounds,app,v,prepare=shot
    prepare()
    for flags in range(256):
        app('ui_flags',flags);app('input_fire_pressed_ff',0);app('ranged_weapon_fire_latched',1)
        app('ranged_hit_visual_ticks_remaining',1,2)
        write(VISUAL+state['state_node_ptr'],VISUAL_NODE)
        assert sequencer(cpu,memory,write)(0x9250,budget=64).stop_reason==1
        assert v('ranged_hit_visual_ticks_remaining',2)==0
        assert read(VISUAL+state['state_node_ptr'])==0
        assert v('ranged_weapon_fire_latched')==(1 if flags&6 else 0)
    app('ui_flags',0)
    for flags in range(256):
        write(PLAYER+obj['world_object_flags'],flags,1)
        app('ranged_weapon_fire_latched',1);app('ranged_hit_visual_ticks_remaining',1,2)
        write(VISUAL+state['state_node_ptr'],VISUAL_NODE)
        assert sequencer(cpu,memory,write)(0x9250,budget=64).stop_reason==1
        assert v('ranged_hit_visual_ticks_remaining',2)==(1 if flags&2 else 0)
        assert read(VISUAL+state['state_node_ptr'])==(VISUAL_NODE if flags&2 else 0)
        assert v('ranged_weapon_fire_latched')==(1 if flags&2 else 0)


def test_all_held_fire_latch_and_ammunition_bytes_consume_only_an_eligible_new_press(shot):
    cpu,memory,read,write,obj,state,node,desc,bounds,app,v,prepare=shot
    prepare()
    for domain in ['item','fire','latch','ammo']:
        for value in range(256):
            write(PLAYER+obj['selected_item_id'],value if domain=='item' else 18,1)
            app('input_fire_pressed_ff',value if domain=='fire' else 255)
            app('ranged_weapon_fire_latched',value if domain=='latch' else 0)
            memory[AMMO:AMMO+2]=bytes([value if domain=='ammo' else 2,2])
            eligible=value in [18,19] if domain=='item' else bool(value) if domain in ['fire','ammo'] else value==0
            assert sequencer(cpu,memory,write)(0x9250,stop=0x92BA if eligible else None,budget=128).stop_reason==1
            assert sum(memory[AMMO:AMMO+2])==(value+2 if domain=='ammo' else 4)-int(eligible)
            expected=value if domain=='latch' and value else int(domain!='fire' or value!=0)
            assert v('ranged_weapon_fire_latched')==expected


def test_anonymous_hit_warns_only_for_the_resistance_bit_and_stops_without_object_damage(shot):
    cpu,memory,read,write,obj,state,node,desc,bounds,app,v,prepare=shot
    prepare(matched=False)
    for flags in range(256):
        app('ranged_weapon_fire_latched',0);app('context_flags',0)
        write(PLAYER+obj['selected_item_id'],18,1);write(AMMO,2,1)
        write(ROOT+state['world_object_flags'],flags&~0x48,1)
        # Bits3/6 are scan filters tested earlier; preserve all other bits here.
        write(APP+HEAD,0);write(APP+TAIL,APP+HEAD)
        assert sequencer(cpu,memory,write)(0x9250,budget=20000).stop_reason==1
        assert read(APP+TAIL)==APP+HEAD+(8 if flags&16 else 0)
        assert read(OBJ+obj['hit_points'],2)==0xAB1F and v('defeated_object_count')==0


def test_unblocked_zero_step_empty_scan_has_no_termination_and_keeps_consumed_press(shot):
    cpu,memory,read,write,obj,state,node,desc,bounds,app,v,prepare=shot
    advance=prepare()
    app('last_accepted_move_request_x_step',0,2);write(ACTIVE,0)
    assert advance(0x9250,budget=4096).stop_reason==3
    assert v('ranged_weapon_fire_latched')==1 and read(AMMO,1)==1
    assert read(OBJ+obj['hit_points'],2)==0xAB1F and v('defeated_object_count')==0


def test_switching_held_weapon_does_not_rearm_or_replenish_shared_ammunition(shot):
    cpu,memory,read,write,obj,state,node,desc,bounds,app,v,prepare=shot
    prepare(blocked=True)
    memory[AMMO:AMMO+2]=bytes([2,1])
    def visit(item,fire):
        write(PLAYER+obj['selected_item_id'],item,1);app('input_fire_pressed_ff',fire)
        assert sequencer(cpu,memory,write)(0x9250,budget=20000).stop_reason==1
        return bytes(memory[AMMO:AMMO+2])
    assert visit(18,255)==b'\x01\x01'
    assert visit(19,255)==b'\x01\x01'  # Held fire retains the first press.
    assert visit(19,0)==b'\x01\x01'
    assert visit(19,255)==b'\x01\x00'
    assert visit(17,0)==b'\x01\x00'
    assert visit(17,255)==b'\x01\x00' and v('ranged_weapon_fire_latched')==1
    assert visit(18,255)==b'\x01\x00'
    assert visit(18,0)==b'\x01\x00'
    assert visit(18,255)==bytes(2)
    assert visit(18,0)==bytes(2)
    assert visit(18,255)==bytes(2)  # Reacquiring the ID does not refill it.
    # Execute the original initializer's exact copy prefix, not a whole restart.
    assert sequencer(cpu,memory,write)(0x9F26,stop=0x9F32,budget=8).stop_reason==1
    assert bytes(memory[AMMO:AMMO+2])==b'\x05\x01'
