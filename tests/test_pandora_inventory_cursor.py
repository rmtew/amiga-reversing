"""Original inventory cursor, selection and sprite handoff in controlled RAM.

MMIO shadows execute no DMA. Explicit call orders and synthetic cursor/map states
establish encoded behavior, not ordinary gameplay reachability or allocation.
"""
import itertools

import pytest

from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import resolve_project_paths
from tests.test_pandora_state_transitions import BASE, TARGET, cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_render_order import sequencer

pytestmark = pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
APP, CUSTOM, FLAGS, SNAPSHOT = 0x39FC, 0xDFF000, 0x20A, 0x218


@pytest.fixture
def cursor(cpu_fixture,title_slots):
    cpu,memory,schemas,read,write,run = cpu_fixture
    m=effective_target_metadata(resolve_project_paths(TARGET).target_dir)
    names={e.name:BASE+e.addr for e in m.seeded_entities if e.name}
    names.update({e.name:BASE+e.addr for e in m.seeded_code_labels if e.name})
    names.update({e.name:e.addr for e in m.absolute_code_labels if e.name})
    constants={e.name:e.value for e in m.target_equates}
    slots,obj=title_slots,schemas['world_object_shared_prefix']
    player,palette=names['player_world_object'],names['gameplay_current_rgb12_palette']
    def app(name,value,size=2):write(APP+slots['app_'+name],value&((1<<(8*size))-1),size)
    def value(name,size=2):return read(APP+slots['app_'+name],size)
    def call(name,stop=None,budget=20000):
        source=names[name]-BASE if isinstance(name,str) else name
        end=names[stop]-BASE if isinstance(stop,str) else stop
        trace=sequencer(cpu,memory,write)(source,stop=end,budget=budget)
        assert trace.stop_reason==1 and trace.steps<budget
        return trace
    def reset(x=0,y=139):
        memory[APP:APP+876]=bytes(876)
        cpu.a[4],cpu.a[5],cpu.a[6]=player,CUSTOM,APP
        run(0x9EBE,stop=0x9ED4,budget=2048)
        app('ui_flags',4,1);app('inventory_cursor_x',x);app('inventory_cursor_y',y)
        app('inventory_selection_latched',1,1)
        write(player+obj['world_object_flags'],0,1)
        write(player+obj['selected_item_id'],18,1)
        write(CUSTOM+0x1E,0x40,2)
        memory[palette:palette+32]=b''.join((0x1234+0x111*i).to_bytes(2,'big') for i in range(16))
        write(APP+SNAPSHOT,0xABCD0123)
        write(APP+FLAGS,0xA4,1)
    reset()
    return cpu,memory,read,write,names,slots,obj,constants,player,palette,app,value,call,reset


def test_reset_reloads_cursor_latch_and_palette_without_resetting_hidden_or_snapshot(cursor):
    cpu,memory,read,write,names,slots,obj,k,player,palette,app,v,call,reset=cursor
    for held in [0,1,2,18,19,255]:
        reset();write(player+obj['selected_item_id'],held,1)
        for field in ['scrolling_message_timer','inventory_cursor_x_step','inventory_cursor_y_step','inventory_cursor_move_countdown']:
            app(field,0xFFFF)
        before=[read(palette+2*i,2) for i in range(16)]
        call('reset_inventory_panel_state')
        assert (v('inventory_cursor_x'),v('inventory_cursor_y'),v('inventory_selection_latched',1))==(0,139,1)
        assert all(v(field)==0 for field in ['scrolling_message_timer','inventory_cursor_x_step','inventory_cursor_y_step','inventory_cursor_move_countdown'])
        expected=[(word&0xF00 if held<2 else word|0xA0) if i in [4,5,6] else word for i,word in enumerate(before)]
        assert [read(palette+2*i,2) for i in range(16)]==expected
        assert [read(CUSTOM+0x1A0+2*i,2) for i in range(16)]==expected
        assert read(APP+FLAGS,1)==0xA4 and read(APP+SNAPSHOT)==0xABCD0123
        assert (v('cursor_sprite0_dma_ptr',4),v('cursor_sprite1_dma_ptr',4))==(k['cursor_sprite0_dma_buffer'],k['cursor_sprite1_dma_buffer'])


def test_nearby_inventory_stages_four_ids_and_name_consumer_preserves_record_values(cursor):
    cpu,memory,read,write,names,slots,obj,k,player,palette,app,v,call,reset=cursor
    npc,inventory=0x82000,0x83000
    ids=[0,18,54,113]
    records=bytes(itertools.chain.from_iterable(zip(ids,[0xA1,0xB2,0xC3,0xD4])))
    memory[inventory:inventory+8]=records
    write(npc+obj['inventory_slots_ptr'],inventory);cpu.a[5]=npc
    call('open_nearby_object_inventory_panel',stop=0x280A)
    staged=APP+slots['app_inventory_display_item_ids']
    assert memory[staged:staged+4]==bytes(ids) and memory[inventory:inventory+8]==records
    call('build_carried_item_name_list')
    expected=[names['item_name_string_table']+read(names['item_name_offset_table']+2*item,2) for item in ids]
    assert [read(names['body_inventory_overlay_line_0_ptr']+4*i) for i in range(4)]==expected
    assert memory[inventory:inventory+8]==records and memory[staged:staged+4]==bytes(ids)


def test_all_panel_and_inactive_bytes_gate_release_before_latch_or_steps(cursor):
    cpu,memory,read,write,names,slots,obj,k,player,palette,app,v,call,reset=cursor
    for gate in ['ui','object']:
        for flags in range(256):
            reset();app('inventory_selection_latched',0xA5,1)
            app('inventory_cursor_x_step',0x1234);app('inventory_cursor_y_step',0x5678)
            if gate=='ui':app('ui_flags',flags,1)
            else:write(player+obj['world_object_flags'],flags,1)
            eligible=bool(flags&4) if gate=='ui' else not flags&2
            call('handle_inventory_panel_input')
            assert v('inventory_selection_latched',1)==(0 if eligible else 0xA5)
            assert (v('inventory_cursor_x_step'),v('inventory_cursor_y_step'))==(0x1234,0x5678)


def test_all_joystick_masks_choose_horizontal_first_then_vertical_and_finish_exact_steps(cursor):
    cpu,memory,read,write,names,slots,obj,k,player,palette,app,v,call,reset=cursor
    for nearby,x,y,mask in itertools.product([False,True],[0,96,192],[139,147,155,163],range(16)):
        reset(x,y);app('ui_flags',4|(16 if nearby else 0),1)
        up,down,left,right=[bool(mask&(1<<i)) for i in range(4)]
        joy=(right<<1)|(left<<9)|((down^right)<<0)|((up^left)<<8)
        write(CUSTOM+0xC,joy,2);write(0xBFE001,0xFF,1)
        call('poll_joystick1_directions_and_fire')
        sx=-1 if left else 1 if right else 0
        sy=-1 if up else 1 if down else 0
        horizontal=bool(sx) and ((x+sx)&65535)<(192 if nearby else 96)
        vertical=not horizontal and bool(sy) and 139<=((y+2*sy)&65535)<164
        count=8 if horizontal else 4 if vertical else 0
        call('handle_inventory_panel_input')
        assert (v('inventory_cursor_x'),v('inventory_cursor_y'))==(x,y)
        assert v('inventory_cursor_move_countdown')==count
        assert v('inventory_selection_latched',1)==0
        if mask:
            assert (v('inventory_cursor_x_step'),v('inventory_cursor_y_step'))==((12*sx)&65535 if horizontal else 0,(2*sy)&65535 if vertical else 0)
        # Fire during movement cannot select until a later zero-count visit.
        app('input_fire_pressed_ff',255,1)
        for remaining in range(count-1,-1,-1):
            call('handle_inventory_panel_input')
            assert v('inventory_cursor_move_countdown')==remaining
            assert v('inventory_selection_latched',1)==0
        assert (v('inventory_cursor_x'),v('inventory_cursor_y'))==((x+96*sx)&65535 if horizontal else x,(y+8*sy)&65535 if vertical else y)
        assert read(player+obj['selected_item_id'],1)==18


def test_nonzero_countdown_words_advance_without_sampling_release_or_fire(cursor):
    cpu,memory,read,write,names,slots,obj,k,player,palette,app,v,call,reset=cursor
    for count,fire in itertools.product([1,2,0x7FFF,0x8000,0xFFFF],[0,1,255]):
        reset(65534,1);app('inventory_cursor_move_countdown',count)
        app('inventory_cursor_x_step',12);app('inventory_cursor_y_step',-2)
        app('inventory_selection_latched',0xA5,1);app('input_fire_pressed_ff',fire,1)
        call('handle_inventory_panel_input')
        assert (v('inventory_cursor_x'),v('inventory_cursor_y'),v('inventory_cursor_move_countdown'))==(10,65535,(count-1)&65535)
        assert v('inventory_selection_latched',1)==0xA5


def test_real_carried_swap_requires_eligible_release_before_next_fire(cursor):
    cpu,memory,read,write,names,slots,obj,k,player,palette,app,v,call,reset=cursor
    reset();app('inventory_selection_latched',0,1)
    write(player+obj['selected_item_id'],0,1);app('carried_item_ids',18,1)
    app('input_fire_pressed_ff',255,1)
    call('handle_inventory_panel_input')
    assert (read(player+obj['selected_item_id'],1),v('carried_item_ids',1))==(18,0)
    assert v('inventory_selection_latched',1)==255
    for _ in range(3):call('handle_inventory_panel_input')
    assert (read(player+obj['selected_item_id'],1),v('carried_item_ids',1))==(18,0)
    app('input_fire_pressed_ff',0,1);call('handle_inventory_panel_input')
    assert v('inventory_selection_latched',1)==0
    app('input_fire_pressed_ff',255,1);call('handle_inventory_panel_input')
    assert (read(player+obj['selected_item_id'],1),v('carried_item_ids',1))==(0,18)


def test_all_fire_and_selection_latch_bytes_use_nonzero_gates(cursor):
    cpu,memory,read,write,names,slots,obj,k,player,palette,app,v,call,reset=cursor
    for fire in range(256):
        reset();app('input_fire_pressed_ff',fire,1);app('context_flags',0x55,1)
        call('handle_inventory_panel_input')
        assert v('inventory_selection_latched',1)==(255 if fire else 0)
        assert v('context_flags',1)==(0xD5 if fire else 0x55)
        assert read(player+obj['selected_item_id'],1)==18
    for latch in range(256):
        reset();app('input_fire_pressed_ff',255,1);app('inventory_selection_latched',latch,1)
        call('handle_inventory_panel_input')
        assert read(player+obj['selected_item_id'],1)==(18 if latch else 0)
        assert v('carried_item_ids',1)==(0 if latch else 18)
        assert v('inventory_selection_latched',1)==255


def test_latched_fire_classifies_inherited_a4_byte_while_palette_uses_fixed_player(cursor):
    cpu,memory,read,write,names,slots,obj,k,player,palette,app,v,call,reset=cursor
    inherited=0x82000
    for item in range(256):
        reset();cpu.a[4]=inherited;write(inherited+obj['selected_item_id'],item,1)
        app('input_fire_pressed_ff',1,1);app('context_flags',0xFF,1)
        call('handle_inventory_panel_input')
        assert v('context_flags',1)==(0xFF if item in [18,19] else 0x7F)
        assert read(player+obj['selected_item_id'],1)==18 and cpu.a[4]==inherited
        assert v('inventory_selection_latched',1)==255


def test_real_main_call_order_carries_grid_end_a4_into_latched_fire(cursor):
    cpu,memory,read,write,names,slots,obj,k,player,palette,app,v,call,reset=cursor
    grid,end=0x80000,0x82000
    for inherited_item in [7,18,19,255]:
        reset();app('input_fire_pressed_ff',255,1)
        app('tilemap_base',grid,4);app('tilemap_width',32);app('tilemap_height',64)
        app('back_bitplane_base',0x70000,4);app('camera_scroll_ticks_remaining',1,1)
        memory[grid:end]=(0x1D0A8).to_bytes(4,'big')*2048
        write(end+70,inherited_item,1)
        # Native incoming references identify these three adjacent real BSRs:
        # availability, camera service, panel input. Stop before snapshot work.
        call(0x5CE,stop=0x5DA)
        assert cpu.a[4]==end
        assert read(player+obj['selected_item_id'],1)==18
        assert bool(v('context_flags',1)&128)==(inherited_item in [18,19])


def test_both_real_modal_call_pairs_leave_player_a4_for_latched_fire(cursor):
    cpu,memory,read,write,names,slots,obj,k,player,palette,app,v,call,reset=cursor
    for (source,end),held in itertools.product([(0x9036,0x903E),(0x9C4A,0x9C52)],[7,18,19,255]):
        reset();app('input_fire_pressed_ff',255,1);write(player+obj['selected_item_id'],held,1)
        call(source,stop=end)
        assert cpu.a[4]==player and bool(v('context_flags',1)&128)==(held in [18,19])


def test_hidden_latch_and_rebinding_are_independent_until_snapshot_rearms_hide(cursor):
    cpu,memory,read,write,names,slots,obj,k,player,palette,app,v,call,reset=cursor
    blank=names['blank_sprite_data']
    for flags in range(256):
        reset(96,147);write(APP+FLAGS,flags,1)
        app('cursor_sprite0_dma_ptr',0x11111111,4);app('cursor_sprite1_dma_ptr',0x22222222,4)
        cpu.a[0]=0x12345678
        call('hide_cursor_sprite_pointers')
        assert cpu.a[0]==0x12345678 and read(APP+FLAGS,1)==flags|1
        assert v('inventory_cursor_x')==(96 if flags&1 else 420)
        assert (v('cursor_sprite0_dma_ptr',4),v('cursor_sprite1_dma_ptr',4))==((0x11111111,0x22222222) if flags&1 else (blank,blank))
        call('bind_cursor_sprites_and_palette');call('hide_cursor_sprite_pointers')
        assert (v('cursor_sprite0_dma_ptr',4),v('cursor_sprite1_dma_ptr',4))==(k['cursor_sprite0_dma_buffer'],k['cursor_sprite1_dma_buffer'])
        call('snapshot_inventory_cursor_and_clear_hidden_latch')
        assert read(APP+FLAGS,1)==flags&~1
        assert (read(APP+SNAPSHOT,2),read(APP+SNAPSHOT+2,2))==(v('inventory_cursor_x'),147)
        call('hide_cursor_sprite_pointers')
        assert (v('cursor_sprite0_dma_ptr',4),v('cursor_sprite1_dma_ptr',4))==(blank,blank)


def test_vblank_writes_both_headers_even_when_hidden_and_consumes_pointer_slots(cursor):
    cpu,memory,read,write,names,slots,obj,k,player,palette,app,v,call,reset=cursor
    first,second=k['cursor_sprite0_dma_buffer'],k['cursor_sprite1_dma_buffer']
    for x,y,hidden in itertools.product([0,96,192,420,65535],[139,163,65535],[False,True]):
        reset(x,y);app('ui_flags',0x80,1)
        app('display_bitplane_base',0x78000,4);app('current_palette',palette,4)
        call('bind_cursor_sprites_and_palette')
        if hidden:call('hide_cursor_sprite_pointers')
        before=b'\xA5'*140;memory[first-4:second+68]=before
        call('handle_vertical_blank_frame_update',stop='service_frame_audio_and_keyboard')
        actual_x=v('inventory_cursor_x')
        pos=((((actual_x+128)&65535)>>1)|(((y+44)<<8)&65535))&65535
        ctl=((((y+44)<<8)+4224)&65535)
        expected=bytearray(before)
        for offset in [4,72]:expected[offset:offset+4]=pos.to_bytes(2,'big')+ctl.to_bytes(2,'big')
        assert memory[first-4:second+68]==expected
        assert (read(CUSTOM+0x120),read(CUSTOM+0x124))==(v('cursor_sprite0_dma_ptr',4),v('cursor_sprite1_dma_ptr',4))
        assert read(APP+SNAPSHOT)==0xABCD0123
