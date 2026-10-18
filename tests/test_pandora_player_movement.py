"""Original movement in controlled RAM; no ordinary tile/call reachability claim.

Modal entries and camera processing are explicit stops. Synthetic maps establish
probe order and encoded arithmetic, not admission of oversized maps by the game.
"""
import itertools

import pytest

from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import resolve_project_paths
from tests.test_pandora_state_transitions import BASE, TARGET, cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_render_order import sequencer

pytestmark = pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
APP, GRID, NODE, GEOMETRY = 0x39FC, 0x80000, 0x85000, 0x86000
PIXELS, BLOCKS = 0x1D0A8, BASE+0xA822


@pytest.fixture
def movement(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    m = effective_target_metadata(resolve_project_paths(TARGET).target_dir)
    names = {e.name: BASE+e.addr for e in m.seeded_entities if e.name}
    names.update({e.name:BASE+e.addr for e in m.seeded_code_labels if e.name})
    names.update({e.name:e.addr for e in m.absolute_code_labels if e.name})
    slots, obj = title_slots, schemas['world_object_shared_prefix']
    state, node = schemas['world_position_state_record'], schemas['WorldPositionStateNode']
    frame = schemas['WorldPositionAnimationFrame']
    player, fixed = names['player_world_object'], names['player_position_state']
    constants = {e.name:e.value for e in m.target_equates}
    def app(name, value, size=2):write(APP+slots['app_'+name], value & ((1<<(8*size))-1), size)
    def reset(x=0, y=1, direction=0):
        cpu.a[6],cpu.a[4] = APP,player
        for name in ['ui_flags','status_flags','context_flags','game_event_flags','player_movement_commit_inhibited']:
            app(name,0,1)
        for name,value in [('input_x_step',x),('input_y_step',y),('tilemap_width',32),('tilemap_height',64),
                           ('player_lateral_drift',0x7777),('player_move_request_x_step',0x1111),
                           ('player_move_request_y_step',0x2222),('last_accepted_move_request_x_step',0x3333),
                           ('last_accepted_move_request_y_step',0x4444)]:app(name,value)
        app('tilemap_base',GRID,4)
        write(player+obj['world_x'],100,2);write(player+obj['world_y'],100,2)
        write(player+obj['world_object_flags'],0,1)
        write(player+obj['movement_direction_flags'],direction,1)
        write(fixed+state['current_geometry_ptr'],GEOMETRY)
        write(fixed+state['state_node_ptr'],NODE)
        write(fixed+state['world_x_offset'],0,2);write(fixed+state['world_y_offset'],0,2)
        memory[GEOMETRY:GEOMETRY+18] = bytes(18)
        write(GEOMETRY+frame['frame_width'],32,2);write(GEOMETRY+frame['frame_height'],32,2)
        write(NODE+node['mode_flags'],0xFF,1);write(NODE+node['frame_index_and_phase'],0xBEEF,2)
        memory[GRID:GRID+8192] = PIXELS.to_bytes(4,'big')*2048
        memory[BLOCKS:BLOCKS+64] = bytes(64)
        write(names['player_movement_script_delay_ticks'],0xABCD,2)
    def tile(column,row,tile_id):write(GRID+4*(32*row+column),PIXELS+128*tile_id)
    def call(source=0x95E2, stop=0x98AE):
        trace = sequencer(cpu,memory,write)(source,stop=stop,budget=1024)
        assert trace.stop_reason == 1 and trace.steps < 1024
        return trace
    def value(name,size=2):return read(APP+slots['app_'+name],size)
    reset()
    return cpu,memory,read,write,run,names,slots,obj,state,node,frame,constants,app,reset,tile,call,value


def test_all_ui_status_and_object_bytes_preserve_early_gate_order(movement):
    cpu,memory,read,write,run,names,slots,obj,state,node,frame,k,app,reset,tile,call,v = movement
    player,fixed = names['player_world_object'],names['player_position_state']
    for gate in ['ui','status','object']:
        for flags in range(256):
            reset()
            if gate=='object':write(player+obj['world_object_flags'],flags,1)
            else:app(gate+'_flags',flags,1)
            blocked = flags & (6 if gate=='ui' else 16 if gate=='status' else 2)
            if not blocked:
                call(stop=0x9632)
                assert (v('player_move_request_x_step'),v('player_move_request_y_step'),v('player_lateral_drift')) == (0,4,0)
                continue
            call(stop=None)
            assert (v('player_move_request_x_step'),v('player_move_request_y_step'),v('player_lateral_drift')) == (0x1111,0x2222,0x7777)
            assert read(fixed+state['state_node_ptr']) == NODE
            hold = gate=='ui'
            assert read(NODE+node['frame_index_and_phase'],2) == (0 if hold else 0xBEEF)
            assert read(NODE+node['mode_flags'],1) == (0xFD if hold else 0xFF)
    reset();app('ui_flags',6,1);app('status_flags',0xFF,1)
    call(stop=None)
    assert v('status_flags',1)==0xBF  # UI hold precedes camera skip; bit6 meaning unknown.


def test_scaled_axis_requests_reject_diagonal_and_word_zero(movement):
    *_,app,reset,tile,call,v = movement
    for x,y in itertools.product([-1,0,1,0x4000,0x8000,0xFFFF],repeat=2):
        reset(x,y)
        sx,sy=(7*x)&65535,(4*y)&65535
        if bool(sx)==bool(sy):call(stop=None)
        else:call(stop=0x9632)
        assert (v('player_move_request_x_step'),v('player_move_request_y_step'),v('player_lateral_drift'))==(sx,sy,0)


def test_horizontal_probe_uses_directional_edge_and_bottom_inset(movement):
    cpu,memory,read,write,run,names,slots,obj,state,node,frame,k,app,reset,tile,call,v = movement
    for x,edge in [(-1,93),(1,139)]:
        reset(x,0)
        call(stop=0x9770)
        assert (cpu.d[0]&65535,cpu.d[1]&65535)==(edge,128)
        assert read(names['player_movement_script_delay_ticks'],2)==2
        advance=sequencer(cpu,memory,write)
        assert advance(0x9770,stop=0x9774).stop_reason==1
        assert cpu.a[0]==GRID+4*(8*32+(edge>>4))


def test_vertical_three_probes_use_left_midpoint_right_and_signed_y_inset(movement):
    cpu,memory,read,write,run,names,slots,obj,state,node,frame,k,app,reset,tile,call,v = movement
    for y,row in [(-1,7),(1,8)]:
        reset(0,y)
        for column,tile_id in [(6,3),(7,9),(8,15)]:tile(column,row,tile_id)
        advance=sequencer(cpu,memory,write)
        for index,(stop,tile_id) in enumerate([(0x9706,3),(0x9726,9),(0x9744,15)]):
            trace=advance(0x95E2 if index==0 else None,stop=stop)
            assert trace.stop_reason==1 and cpu.d[0]==tile_id
        assert read(names['player_movement_script_delay_ticks'],2)==1


def test_all_tile_ids_horizontal_modal_priority_and_original_block_bits(movement):
    cpu,memory,read,write,run,names,slots,obj,state,node,frame,k,app,reset,tile,call,v = movement
    original=resolve_project_paths(TARGET).binary_source.path.read_bytes()[0xA822:0xA862]
    modal={156:names['run_terminal_modal_loop'],159:names['run_terminal_modal_loop'],
           398:names['run_self_destruct_modal_loop'],400:names['run_self_destruct_modal_loop']}
    for tile_id in range(508):
        reset(1,0);memory[BLOCKS:BLOCKS+64]=original
        tile(8,8,tile_id);app('player_movement_commit_inhibited',255,1)
        blocked=original[tile_id>>3] & (0x80>>(tile_id&7))
        stop=modal.get(tile_id,BASE+(0x9984 if blocked else 0x97FE))-BASE
        call(stop=stop)
        assert (v('last_accepted_move_request_x_step'),v('last_accepted_move_request_y_step'))==(0x3333,0x4444)


def test_vertical_consoles_only_third_probe_precedes_block_and_commit_gate(movement):
    cpu,memory,read,write,run,names,slots,obj,state,node,frame,k,app,reset,tile,call,v = movement
    for tile_id in [156,159,398,400]:
        for probe,column in enumerate([6,7,8]):
            for blocked in [False,True]:
                reset();tile(column,8,tile_id);app('player_movement_commit_inhibited',255,1)
                memory[BLOCKS+(tile_id>>3)] = (0x80>>(tile_id&7)) if blocked else 0
                target=names['run_terminal_modal_loop' if tile_id<160 else 'run_self_destruct_modal_loop']-BASE
                stop=target if probe==2 else 0x9984 if blocked else 0x97FE
                call(stop=stop)


def test_all_direction_bytes_drift_moves_only_x_but_records_and_animates_y(movement):
    cpu,memory,read,write,run,names,slots,obj,state,node,frame,k,app,reset,tile,call,v = movement
    player,fixed=names['player_world_object'],names['player_position_state']
    for y,animation,bit in [(-1,'player_move_negative_y_animation',k['INPUT_DIRECTION_UP_BIT']),
                             (1,'player_move_positive_y_animation',k['INPUT_DIRECTION_DOWN_BIT'])]:
        for direction in range(256):
            reset(0,y,direction)
            drift=7 if direction & (1<<k['INPUT_DIRECTION_LEFT_BIT']) else 0
            if direction & (1<<k['INPUT_DIRECTION_RIGHT_BIT']):drift=-7
            call()
            assert v('player_lateral_drift')==drift&65535
            assert (read(player+obj['world_x'],2),read(player+obj['world_y'],2))==(100+drift,100 if drift else 100+4*y)
            assert (v('last_accepted_move_request_x_step'),v('last_accepted_move_request_y_step'))==(0,(4*y)&65535)
            assert read(fixed+state['state_node_ptr'])==names[animation]
            assert read(player+obj['movement_direction_flags'],1)==1<<bit


def test_all_commit_inhibition_bytes_hold_after_probes_without_accepting(movement):
    cpu,memory,read,write,run,names,slots,obj,state,node,frame,k,app,reset,tile,call,v = movement
    player=names['player_world_object']
    for inhibited in range(256):
        reset();app('player_movement_commit_inhibited',inhibited,1)
        call(stop=None if inhibited else 0x98AE)
        assert read(player+obj['world_y'],2)==(100 if inhibited else 104)
        assert v('last_accepted_move_request_y_step')==(0x4444 if inhibited else 4)
        assert read(names['player_movement_script_delay_ticks'],2)==1


def test_commit_y_performs_only_one_word_correction_and_x_wraps(movement):
    cpu,memory,read,write,run,names,slots,obj,state,node,frame,k,app,reset,tile,call,v = movement
    player=names['player_world_object']
    for height,old_y,step in itertools.product([0,1,64,4096],[0,1,1023,32767,65535],[-4096,-4,4,4096]):
        reset();app('tilemap_height',height);app('player_lateral_drift',0)
        app('player_move_request_x_step',0);app('player_move_request_y_step',step)
        write(player+obj['world_y'],old_y,2)
        total=(old_y+step)&65535;extent=(height<<4)&65535
        expected=((total+extent) if total&0x8000 else total-extent if total>=extent else total)&65535
        call(0x97FE)
        assert read(player+obj['world_y'],2)==expected
    reset();app('player_lateral_drift',0);app('player_move_request_x_step',7);app('player_move_request_y_step',0)
    write(player+obj['world_x'],65534,2);call(0x97FE)
    assert read(player+obj['world_x'],2)==5


def test_reusing_animation_keeps_clock_switch_resets_and_hold_clears_only_two_mode_bits(movement):
    cpu,memory,read,write,run,names,slots,obj,state,node,frame,k,app,reset,tile,call,v = movement
    fixed=names['player_position_state']
    for x,y,animation in [(-1,0,'negative_x'),(1,0,'positive_x'),(0,-1,'negative_y'),(0,1,'positive_y')]:
        for same in [False,True]:
            reset(x,y);selected=names['player_move_'+animation+'_animation']
            write(selected+node['mode_flags'],255,1);write(selected+node['frame_index_and_phase'],0x1234,2)
            if same:write(fixed+state['state_node_ptr'],selected)
            call()
            assert read(selected+node['mode_flags'],1)==252
            assert read(selected+node['frame_index_and_phase'],2)==(0x1234 if same else 0)
    for flags in range(256):
        reset(0,0);write(NODE+node['mode_flags'],flags,1);app('status_flags',0xEF,1)
        call(stop=None)
        assert read(NODE+node['mode_flags'],1)==(flags|1)&~2
        assert v('status_flags',1)==0xAF


def test_vertical_row_low_word_differs_from_shared_helper_full_product(movement):
    cpu,memory,read,write,run,names,slots,obj,state,node,frame,k,app,reset,tile,call,v = movement
    reset();app('tilemap_width',512)
    cpu.d[0],cpu.d[1]=67,4096
    run(0x67EC)
    assert cpu.a[0]==GRID+0x80010 and (cpu.d[0],cpu.d[1])==(67,4096)
    # Enter the actual vertical prefix with explicitly supplied candidate bounds.
    app('player_move_request_y_step',4)
    cpu.d[2],cpu.d[3],cpu.d[5]=64,96,4096
    write(GRID+16,PIXELS+128*23)
    call(0x96CE,0x9706)
    assert cpu.d[0]==23
