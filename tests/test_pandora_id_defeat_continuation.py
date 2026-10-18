"""Original missing-ID defeat and subsequent movement/exit consumers.

Controlled RAM and ready-bit MMIO establish CPU paths, not ordinary gameplay
admission, asynchronous frames, DMA pixels or intended behavior. No instruction
or callee is patched. The fixed movement state and active defeat state differ.
"""
import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_player_movement import movement
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_message_queue import initialize, HEAD, TAIL
from tests.test_pandora_framebuffer_lifetime import fill_rows
from tests.test_pandora_render_order import sequencer

APP=0x39FC
pytestmark=pytest.mark.parametrize('cpu_fixture',[0x1000000],indirect=True)


@pytest.fixture
def failure(movement,cpu_fixture):
    cpu,memory,read,write,run,names,slots,obj,state,node,frame,k,app,reset,tile,call,v=movement
    fill_rows(cpu,memory,run)
    cpu.d[0]=0
    assert sequencer(cpu,memory,write)(0x4D7DE,budget=4096).stop_reason==1
    player,fixed=names['player_world_object'],names['player_position_state']
    descriptor=read(player+obj['position_descriptor_ptr'])
    incoming,animation=names['player_animated_defeat_state'],names['player_animated_defeat_node']
    def prepare(x=1,y=0,inhibited=0,occupancy=0):
        reset(x,y)
        initialize(cpu_fixture,slots,occupancy)
        app('context_flags',0x30,1);app('player_movement_commit_inhibited',inhibited,1)
        app('font_glyph_bitmap_table_ptr',BASE+0xA7E2,4)
        app('front_bitplane_base',0x78000,4)
        app('game_exit_service_ticks_remaining',0xA5,1)
        write(0xDFF01E,0x40,2)
        write(descriptor,fixed)
        write(player+obj['selected_item_id'],0,1)
        for name in ['carried_item_ids','pocket_item_ids']:
            memory[APP+slots['app_'+name]:APP+slots['app_'+name]+4]=bytes(4)
        for i in range(occupancy):write(APP+HEAD+4*i,0x81000+4*i)
        write(animation+node['mode_flags'],4,1)
        write(animation+node['frame_index_and_phase'],0xBEEF,2)
        return sequencer(cpu,memory,write)
    return movement,prepare,descriptor,incoming,animation


def test_full_missing_id_helper_restores_registers_and_clears_only_pending_context_bit(failure):
    m,prepare,descriptor,incoming,animation=failure
    cpu,memory,read,write,run,names,slots,obj,state,node,frame,k,app,reset,tile,call,v=m
    player,fixed=names['player_world_object'],names['player_position_state']
    for flags in range(256):
        advance=prepare();app('context_flags',flags|32,1)
        write(animation+node['mode_flags'],flags,1)
        for i in range(8):cpu.d[i]=0x12340000+i
        for i in [0,1,2,3,5]:cpu.a[i]=0x87650000+i
        saved_d,saved_a=list(cpu.d),list(cpu.a[:7])
        assert advance(0x86CA,budget=20000).stop_reason==1
        assert list(cpu.d)==saved_d and list(cpu.a[:7])==saved_a and cpu.a[7]==0x9004
        assert v('context_flags',1)==(flags|32)&~16
        assert read(descriptor)==incoming and read(player+obj['saved_position_state_ptr'])==fixed
        assert read(animation+node['mode_flags'],1)==flags&~1
        assert read(animation+node['frame_index_and_phase'],2)==0
        assert read(player+obj['world_object_flags'],1)&2
        assert read(player+obj['hit_points'],2)==0 and v('game_exit_service_ticks_remaining',1)==70
        assert v('player_movement_commit_inhibited',1)==0
        assert v('game_event_flags',1)==0xC0
        assert read(player+obj['selected_item_id'],1)==2  # Outcome's existing ID-bit mutation.
        assert read(APP+TAIL)==APP+HEAD+12


def test_missing_id_defeat_returns_to_axis_commit_without_an_inactive_recheck(failure):
    m,prepare,descriptor,incoming,animation=failure
    cpu,memory,read,write,run,names,slots,obj,state,node,frame,k,app,reset,tile,call,v=m
    player,fixed=names['player_world_object'],names['player_position_state']
    for x,y in [(1,0),(-1,0),(0,1),(0,-1)]:
        for inhibit in [0,255]:
            advance=prepare(x,y,inhibit)
            assert advance(0x95E2,stop=None if inhibit else 0x98AE,budget=80000).stop_reason==1
            expected=(100,100) if inhibit else (100+7*x,100+4*y)
            assert (read(player+obj['world_x'],2),read(player+obj['world_y'],2))==expected
            assert read(descriptor)==incoming
            assert read(player+obj['saved_position_state_ptr'])==fixed
            assert read(incoming+state['state_node_ptr'])==animation
            assert read(animation+node['frame_index_and_phase'],2)==0
            assert read(fixed+state['state_node_ptr'])!=animation
            assert v('player_movement_commit_inhibited',1)==inhibit
            assert read(player+obj['world_object_flags'],1)&2
            assert not v('context_flags',1)&16
            if not inhibit:
                assert (v('last_accepted_move_request_x_step'),v('last_accepted_move_request_y_step'))==(7*x&65535,4*y&65535)
            # The next actual movement call does see the inactive player.
            assert sequencer(cpu,memory,write)(0x95E2,budget=64).stop_reason==1
            assert (read(player+obj['world_x'],2),read(player+obj['world_y'],2))==expected


def test_full_status_fifo_does_not_prevent_defeat_handoff_or_audio(failure):
    m,prepare,descriptor,incoming,animation=failure
    cpu,memory,read,write,run,names,slots,obj,state,node,frame,k,app,reset,tile,call,v=m
    advance=prepare(occupancy=16)
    before=bytes(memory[APP+HEAD:APP+HEAD+68])
    assert advance(0x86CA,budget=20000).stop_reason==1
    assert bytes(memory[APP+HEAD:APP+HEAD+68])==before
    assert read(APP+TAIL)==APP+HEAD+64
    assert read(descriptor)==incoming and v('game_exit_service_ticks_remaining',1)==70
    assert read(names['player_world_object']+obj['hit_points'],2)==0
    assert v('game_event_flags',1)==0xC0 and not v('context_flags',1)&16


def test_all_exit_counter_bytes_decrement_with_wrap_and_restart_only_from_one(failure):
    m,prepare,descriptor,incoming,animation=failure
    cpu,memory,read,write,run,names,slots,obj,state,node,frame,k,app,reset,tile,call,v=m
    restart=names['wait_for_blitter_then_restart_runtime']-BASE
    for entry,continued in [(0x66C,'check_main_keyboard_shortcuts'),(0x904C,'check_terminal_restart_key'),(0x9C60,'check_self_destruct_restart_key')]:
        for ticks in range(256):
            advance=prepare();app('context_flags',0,1);app('game_exit_service_ticks_remaining',ticks,1)
            write(names['player_world_object']+obj['world_object_flags'],2,1)
            assert advance(entry,stop=restart if ticks==1 else names[continued]-BASE,budget=32).stop_reason==1
            assert v('game_exit_service_ticks_remaining',1)==(ticks-1)&255


def test_main_exit_clock_pauses_for_status_context_while_both_modal_clocks_do_not(failure):
    m,prepare,descriptor,incoming,animation=failure
    cpu,memory,read,write,run,names,slots,obj,state,node,frame,k,app,reset,tile,call,v=m
    for entry,continued in [(0x66C,'check_main_keyboard_shortcuts'),(0x904C,'check_terminal_restart_key'),(0x9C60,'check_self_destruct_restart_key')]:
        for flags in range(256):
            advance=prepare();app('context_flags',flags,1);app('game_exit_service_ticks_remaining',2,1)
            write(names['player_world_object']+obj['world_object_flags'],2,1)
            assert advance(entry,stop=names[continued]-BASE,budget=32).stop_reason==1
            assert v('game_exit_service_ticks_remaining',1)==(2 if entry==0x66C and flags&32 else 1)
            assert v('context_flags',1)==flags


def test_all_player_flag_bytes_gate_the_three_inactive_exit_prefixes(failure):
    m,prepare,descriptor,incoming,animation=failure
    cpu,memory,read,write,run,names,slots,obj,state,node,frame,k,app,reset,tile,call,v=m
    for entry,continued in [(0x66C,'check_main_keyboard_shortcuts'),(0x904C,'check_terminal_restart_key'),(0x9C60,'check_self_destruct_restart_key')]:
        for flags in range(256):
            advance=prepare();app('context_flags',0,1);app('game_exit_service_ticks_remaining',2,1)
            write(names['player_world_object']+obj['world_object_flags'],flags,1)
            assert advance(entry,stop=names[continued]-BASE,budget=32).stop_reason==1
            assert v('game_exit_service_ticks_remaining',1)==(1 if flags&2 else 2)


def test_failure_seventy_service_delay_freezes_for_status_then_reaches_restart(failure):
    m,prepare,descriptor,incoming,animation=failure
    cpu,memory,read,write,run,names,slots,obj,state,node,frame,k,app,reset,tile,call,v=m
    advance=prepare()
    assert advance(0x86CA,budget=20000).stop_reason==1
    for _ in range(3):
        assert sequencer(cpu,memory,write)(0x66C,stop=names['check_main_keyboard_shortcuts']-BASE,budget=32).stop_reason==1
        assert v('game_exit_service_ticks_remaining',1)==70
    app('context_flags',0,1)
    for remaining in range(69,-1,-1):
        stop=names['check_main_keyboard_shortcuts' if remaining else 'wait_for_blitter_then_restart_runtime']-BASE
        assert sequencer(cpu,memory,write)(0x66C,stop=stop,budget=32).stop_reason==1
        assert v('game_exit_service_ticks_remaining',1)==remaining
    assert read(descriptor)==incoming
