"""Original modal entry/loop/exit and warm setup with controlled RAM/MMIO.

No DMA, asynchronous frame producer, ordinary gameplay admission or whole restart
completion is claimed. Large display writes are checked in guest memory rather
than treated as a complete bounded write trace.
"""
import itertools

import pytest

from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import resolve_project_paths
from tests.test_pandora_state_transitions import BASE, TARGET, cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_self_destruct_console import console
from tests.test_pandora_render_order import sequencer

pytestmark=pytest.mark.parametrize('cpu_fixture',[0x1000000],indirect=True)
APP,CUSTOM,DESCRIPTORS,DESCRIPTOR,STATE,ATTACHMENT=0x39FC,0xDFF000,0x81000,0x82000,0x83000,0x83100
MODES={'terminal':(0x9016,0x901E,0x9024),'self_destruct':(0x9C2A,0x9C32,0x9C38)}


@pytest.fixture
def modal(console):
    cpu,memory,read,write,run,slots,held,prepare,submit=console
    m=effective_target_metadata(resolve_project_paths(TARGET).target_dir)
    names={e.name:BASE+e.addr for e in m.seeded_entities if e.name}
    names.update({e.name:BASE+e.addr for e in m.seeded_code_labels if e.name})
    names.update({e.name:e.addr for e in m.absolute_code_labels if e.name})
    schemas={s.name:{f.name:f.offset for f in s.fields} for s in m.custom_structs}
    obj,desc,state=schemas['world_object_shared_prefix'],schemas['world_position_descriptor_prefix'],schemas['world_position_state_record']
    constants={e.name:e.value for e in m.target_equates}
    header=names['modal_tilemap_context'];player=names['player_world_object']
    fields=['app_tilemap_width','app_tilemap_height','app_tile_column','app_tile_row']
    derived=['app_tile_pointer_grid_row_stride_bytes','app_tile_pointer_grid_byte_size','app_tile_pointer_grid_end']
    def app(name,value,size=2):write(APP+slots['app_'+name],value&((1<<(8*size))-1),size)
    def value(name,size=2):return read(APP+slots['app_'+name],size)
    def reset(item=0):
        prepare(state=0,item=item,cached=0x55,fire=0,ui=0)
        cpu.a[6],cpu.a[5]=APP,CUSTOM
        for name,v in zip(fields,[90,129,70,128]):write(APP+slots[name],v,2)
        for i,v in enumerate([20,8,0,0]):write(header+2*i,v,2)
        for i,name in enumerate(derived):write(APP+slots[name],0x12340000+i)
        app('tilemap_base',0x4000,4);app('front_bitplane_base',0x78000,4)
        app('back_bitplane_base',0x70000,4);app('display_bitplane_base',0x78000,4)
        app('active_world_object_ptr_table',DESCRIPTORS,4)
        write(APP+slots['active_world_object_count'],1,2)
        write(DESCRIPTORS,DESCRIPTOR);write(DESCRIPTOR+desc['position_state_ptr'],STATE)
        write(DESCRIPTOR+desc['world_x'],0x00200030);write(DESCRIPTOR+desc['previous_world_x'],0xAABBCCDD)
        memory[STATE:STATE+30]=bytes(30);memory[ATTACHMENT:ATTACHMENT+30]=bytes(30)
        for address,geometry,previous in [(STATE,0x90000,0x11111111),(ATTACHMENT,0x90100,0x22222222)]:
            write(address+state['current_geometry_ptr'],geometry)
            write(address+state['previous_geometry_ptr'],previous)
        write(STATE+state['attachment_state_ptr'],ATTACHMENT)
        write(player+obj['world_object_flags'],0,1)
        write(player+obj['behavior_script_delay_ticks'],0x7777,2)
        app('self_destruct_service_ticks_remaining',0xBEEF)
        app('earth_orbit_countdown_bcd',0x4000);app('earth_orbit_countdown_divider',60,1)
        app('status_flags',0xA0,1)
        write(0x397C+80,0,1);write(0x397C+64,0,1);write(0x397C+0x56,0,1)
        write(CUSTOM+0xC,0,2);write(0xBFE001,0xFF,1);write(CUSTOM+0x1E,0x40,2)
    def enter(mode):
        advance=sequencer(cpu,memory,write)
        trace=advance(names['run_'+mode+'_modal_loop']-BASE,stop=MODES[mode][0],budget=200000)
        assert trace.stop_reason==1
        return advance
    reset()
    return cpu,memory,read,write,slots,held,names,obj,desc,state,constants,header,fields,derived,app,value,reset,enter


def test_both_entries_exchange_display_banks_but_keep_and_snapshot_the_active_list(modal):
    cpu,memory,read,write,slots,held,names,obj,desc,state,k,header,fields,derived,app,v,reset,enter=modal
    for mode in MODES:
        reset();enter(mode)
        assert [read(APP+slots[n],2) for n in fields]==[20,8,0,0]
        assert [read(header+2*i,2) for i in range(4)]==[90,129,70,128]
        assert v('tilemap_base',4)==header+8
        assert (v('front_bitplane_base',4),v('back_bitplane_base',4),v('display_bitplane_base',4))==(0x70000,0x78000,0x70000)
        assert v('active_world_object_ptr_table',4)==DESCRIPTORS and read(APP+slots['active_world_object_count'],2)==1
        assert read(DESCRIPTOR+desc['previous_world_x'])==0x00200030
        assert [read(a+state['previous_geometry_ptr']) for a in [STATE,ATTACHMENT]]==[0x90000,0x90100]
        assert [read(APP+slots[n]) for n in derived]==[0x12340000+i for i in range(3)]
        assert v('modal_last_selected_item_id',1)==(0 if mode=='terminal' else 0x80)
        assert read(names['player_world_object']+obj['behavior_script_delay_ticks'],2)==0x7777
        assert v('self_destruct_service_ticks_remaining')==0xBEEF


def test_initial_modal_release_gate_uses_direction_and_not_fire(modal):
    cpu,memory,read,write,slots,held,names,obj,desc,state,k,header,fields,derived,app,v,reset,enter=modal
    for mode,fire in itertools.product(MODES,[0xFF,0x7F]):
        reset();advance=enter(mode)
        write(CUSTOM+0xC,2,2);write(0xBFE001,fire,1)
        assert advance(stop=MODES[mode][1],budget=64).stop_reason==3
        assert v('status_flags',1)==0xA0
        write(CUSTOM+0xC,0,2)
        assert advance(stop=MODES[mode][1],budget=128).stop_reason==1
        assert v('input_fire_pressed_ff',1)==(255 if fire==0x7F else 0)
        assert v('input_direction_mask')==0


def test_frame_wait_and_idle_modal_visit_keep_entry_snapshot_and_world_timers(modal):
    cpu,memory,read,write,slots,held,names,obj,desc,state,k,header,fields,derived,app,v,reset,enter=modal
    for mode in MODES:
        reset();advance=enter(mode)
        assert advance(stop=MODES[mode][2]).stop_reason==1
        assert v('status_flags',1)==0x80
        assert advance(stop=names['service_keyboard_pause_gate']-BASE,budget=32).stop_reason==3
        write(STATE+state['current_geometry_ptr'],0x90200)
        write(DESCRIPTOR+desc['world_x'],0x00400050)
        app('status_flags',0xA0,1)
        assert advance(stop=MODES[mode][1],budget=10000).stop_reason==1
        assert read(STATE+state['previous_geometry_ptr'])==0x90000
        assert read(DESCRIPTOR+desc['previous_world_x'])==0x00200030
        assert read(names['player_world_object']+obj['behavior_script_delay_ticks'],2)==0x7777
        assert v('self_destruct_service_ticks_remaining')==0xBEEF
        assert v('earth_orbit_countdown_divider',1)==59


def test_normal_exit_restores_world_header_base_and_refresh_without_exchanging_banks(modal):
    cpu,memory,read,write,slots,held,names,obj,desc,state,k,header,fields,derived,app,v,reset,enter=modal
    for mode in MODES:
        reset();advance=enter(mode)
        assert advance(stop=MODES[mode][2]).stop_reason==1
        app('status_flags',0xA0,1);app('camera_scroll_delta_x',16);app('camera_scroll_delta_y',-16)
        write(CUSTOM+0xC,2,2)
        if mode=='terminal':
            assert advance(stop=0x9088,budget=10000).stop_reason==1
            assert advance(budget=64).stop_reason==3
            write(CUSTOM+0xC,0,2)
        trace=advance(budget=10000)
        assert trace.stop_reason==1 and cpu.a[7]==0x9004
        assert [read(APP+slots[n],2) for n in fields]==[90,129,70,128]
        assert [read(header+2*i,2) for i in range(4)]==[20,8,0,0]
        assert v('tilemap_base',4)==0x4000
        assert (v('camera_scroll_delta_x'),v('camera_scroll_delta_y'),v('camera_scroll_ticks_remaining',1))==(0,0,2)
        assert v('status_flags',1)&16
        assert (v('front_bitplane_base',4),v('back_bitplane_base',4),v('display_bitplane_base',4))==(0x70000,0x78000,0x70000)
        assert read(CUSTOM+0xC,2)==(0 if mode=='terminal' else 2)


def test_warm_setup_reaches_title_with_modal_dimensions_and_base_still_selected(modal):
    cpu,memory,read,write,slots,held,names,obj,desc,state,k,header,fields,derived,app,v,reset,enter=modal
    for mode in MODES:
        reset();enter(mode)
        write(CUSTOM+2,0,2)
        write(0x397C+0x56,255,1)
        advance=sequencer(cpu,memory,write)
        assert advance(names['check_'+mode+'_restart_key']-BASE,stop=names['wait_for_blitter_then_restart_runtime']-BASE).stop_reason==1
        assert (v('tilemap_width'),v('tilemap_height'),v('tilemap_base',4))==(20,8,header+8)
        assert advance(stop=names['run_title_starfield_until_fire']-BASE,budget=100000).stop_reason==1
        assert (v('tilemap_width'),v('tilemap_height'),v('tilemap_base',4))==(20,8,header+8)
        assert [read(header+2*i,2) for i in range(4)]==[90,129,70,128]
        assert v('tile_row')==k['WORLD_RESTART_INITIAL_TILE_ROW']
        assert v('self_destruct_service_ticks_remaining')==k['WORLD_RESTART_SELF_DESTRUCT_STEPS']
        assert v('ui_flags',1)==0 and v('status_flags',1)==0


def test_terminal_clear_has_the_shared_exact_plane_row_fences(modal):
    cpu,memory,read,write,slots,held,names,obj,desc,state,k,header,fields,derived,app,v,reset,enter=modal
    origin=0x78000+2*1280+2
    memory[origin-40:origin+384*40+40]=b'\xA5'*(386*40)
    assert sequencer(cpu,memory,write)(names['redraw_terminal_selected_item']-BASE,stop=0x90F0,budget=10000).stop_reason==1
    for row in range(384):
        assert memory[origin+40*row:origin+40*row+30]==bytes(30)
        assert memory[origin+40*row+30:origin+40*(row+1)]==b'\xA5'*10
    assert memory[origin-40:origin]==b'\xA5'*40 and memory[origin+384*40:origin+385*40]==b'\xA5'*40


def test_unchanged_terminal_cache_skips_all_item_bytes_before_display_writes(modal):
    cpu,memory,read,write,slots,held,names,obj,desc,state,k,header,fields,derived,app,v,reset,enter=modal
    for item in range(256):
        write(held,item,1);app('modal_last_selected_item_id',item,1)
        memory[0x78000:0x78100]=b'\xA5'*256
        trace=sequencer(cpu,memory,write)(names['update_terminal_selected_item']-BASE)
        assert trace.stop_reason==1 and trace.steps==4
        assert memory[0x78000:0x78100]==b'\xA5'*256
        assert v('modal_last_selected_item_id',1)==item


def test_changed_terminal_cache_redraws_all_eight_cards_and_invalid_samples_without_fire_gate(modal):
    cpu,memory,read,write,slots,held,names,obj,desc,state,k,header,fields,derived,app,v,reset,enter=modal
    for item in [0,47,*range(48,56),56,255]:
        reset(item);app('ui_flags',255,1);app('input_fire_pressed_ff',0,1)
        trace=sequencer(cpu,memory,write)(names['update_terminal_selected_item']-BASE,budget=200000)
        assert trace.stop_reason==1 and cpu.a[7]==0x9004
        assert v('modal_last_selected_item_id',1)==item and read(held,1)==item


def test_invalid_terminal_lines_use_the_first_renderer_return_as_second_text_input(modal):
    cpu,memory,read,write,slots,held,names,obj,desc,state,k,header,fields,derived,app,v,reset,enter=modal
    trace=sequencer(cpu,memory,write)(names['redraw_terminal_selected_item']-BASE,stop=0x920A,budget=200000)
    assert trace.stop_reason==1
    assert cpu.a[3]==BASE+0x8D47
    assert bytes(memory[cpu.a[3]:cpu.a[3]+12])==b'ID REQUIRED\0'


def test_terminal_redraw_resamples_held_item_after_its_clear_stage(modal):
    cpu,memory,read,write,slots,held,names,obj,desc,state,k,header,fields,derived,app,v,reset,enter=modal
    reset(48);advance=sequencer(cpu,memory,write)
    assert advance(names['update_terminal_selected_item']-BASE,stop=0x90F0,budget=10000).stop_reason==1
    assert v('modal_last_selected_item_id',1)==48
    write(held,49,1)
    assert advance(budget=200000).stop_reason==1
    assert v('modal_last_selected_item_id',1)==49 and read(held,1)==49
