"""Original title-to-gameplay continuation with explicit counter/MMIO inputs.

No asynchronous interrupts or DMA are simulated. Tile source addresses and
programmed packets establish CPU consumption, not pixels, allocation or a bug.
The title counter is deliberately controlled for equality/loop-boundary cases.
"""
import pytest

from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import resolve_project_paths
from tests.test_pandora_state_transitions import TARGET
from tests.test_pandora_state_transitions import BASE, RETURN, cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_self_destruct_console import console
from tests.test_pandora_modal_handoff import modal
from tests.test_pandora_render_order import sequencer

pytestmark=pytest.mark.parametrize('cpu_fixture',[0x1000000],indirect=True)
APP,CUSTOM,SAFE_STACK,SCRATCH=0x39FC,0xDFF000,0xF0000,BASE+0xB3A8


@pytest.fixture
def title(modal):
    cpu,memory,read,write,slots,held,names,obj,desc,state,k,header,fields,derived,app,v,reset,enter=modal
    metadata=effective_target_metadata(resolve_project_paths(TARGET).target_dir)
    for layout in metadata.data_block_layouts:
        names.setdefault(layout.name,BASE+layout.source_start)
    def start(source,stop=None,budget=1000000):
        advance=sequencer(cpu,memory,write)
        cpu.a[7]=SAFE_STACK;write(SAFE_STACK,RETURN)
        trace=advance(names[source]-BASE if isinstance(source,str) else source,stop=names[stop]-BASE if isinstance(stop,str) else stop,budget=budget)
        assert trace.stop_reason==1
        return advance
    def prepare(mode='world',counter=0):
        reset()
        start('build_world_tilemap_pointer_grid')
        if mode!='world':start('run_'+mode+'_modal_loop',0x9016 if mode=='terminal' else 0x9C2A)
        write(0x397C+0x56,255,1);write(CUSTOM+2,0,2)
        write(0x7E8,0x67FD67FD);write(0x7EC,0xE432A55A)
        memory[0x400:0x7E8]=b'\xA5'*1000;write(0x3FF,0x5A,1)
        app('frame_counter',counter,4)
        key='check_main_keyboard_shortcuts' if mode=='world' else 'check_'+mode+'_restart_key'
        advance=start(key,'run_title_starfield_until_fire')
        assert (read(0x7E8),read(0x7EC))==(0x67FD67FD,0xE432A55A)
        assert advance(stop=0xFD2,budget=1000000).stop_reason==1
        return advance
    return cpu,memory,read,write,slots,names,k,header,derived,app,v,start,prepare


def test_actual_f7_title_exit_reaches_both_gameplay_render_banks_with_retained_context(title):
    cpu,memory,read,write,slots,names,k,header,derived,app,v,start,prepare=title
    for mode in ['world','terminal','self_destruct']:
        advance=prepare(mode)
        initial_derived=[read(APP+slots[n]) for n in derived]
        assert cpu.d[5]==150 and v('front_bitplane_base',4)==0x70000
        write(0xBFE001,0x7F,1)
        assert advance(stop=names['render_tilemap_view_to_back_buffer']-BASE,budget=1000000).stop_reason==1
        base,width,height=(0x4000,90,129) if mode=='world' else (header+8,20,8)
        assert (v('tilemap_base',4),v('tilemap_width'),v('tilemap_height'),v('tile_row'),v('tile_column'))==(base,width,height,51,0)
        assert [read(APP+slots[n]) for n in derived]==initial_derived
        assert v('world_interaction_audio_flags',1)&1==0
        assert v('status_flags',1)&2
        all_addresses=[]
        for bank,returned in [(0x78000,0x55E),(0x70000,0x56A)]:
            assert v('back_bitplane_base',4)==bank
            assert advance(stop=0x677E).stop_reason==1
            row_address=base+4*51*width
            for row in range(8):
                for column in range(20):
                    assert advance(stop=0x679A).stop_reason==1
                    source=row_address+4*column
                    assert cpu.a[3]-4==source
                    assert read(CUSTOM+0x50)==read(source)
                    assert read(CUSTOM+0x54)==bank+2560*row+2*column
                    assert read(CUSTOM+0x58,2)==0x1001
                    all_addresses.append(source)
                    assert advance(stop=returned if (row,column)==(7,19) else 0x677E).stop_reason==1
                row_address+=4*width
                if row_address>=base+4*width*height:row_address-=4*width*height
            if bank==0x78000:
                assert advance(stop=names['render_tilemap_view_to_back_buffer']-BASE).stop_reason==1
        if mode=='world':assert all(0x4000<=a<0xF568 for a in all_addresses)
        else:
            assert [all_addresses[20*r]-base for r in range(8)]==[4080,3520,2960,2400,1840,1280,720,160]
            assert sum(not base<=a<base+640 for a in all_addresses)==280
        assert (v('front_bitplane_base',4),v('display_bitplane_base',4))==(0x70000,0x78000)
        assert advance(stop=0x572).stop_reason==1
        assert v('front_bitplane_base',4)==0x78000
        assert advance(stop=0x576,budget=1000000).stop_reason==1
        queue=names['ui_overlay_update_queue']
        expected=[names[n+'_overlay'] for n in ['pocket_inventory','backpack_inventory','player_health','nearby_distance','nearby_character','nearby_carrying','player_holding']]
        assert [read(queue+4*i) for i in range(16)]==expected+[0]*9
        assert advance(stop=names['wait_for_next_frame_counter']-BASE,budget=1000000).stop_reason==1
        assert (v('tilemap_base',4),v('tilemap_width'),v('tilemap_height'))==(base,width,height)
        counter=v('frame_counter',4)
        assert advance(stop=names['wait_for_completed_frame']-BASE,budget=32).stop_reason==3
        app('frame_counter',counter+1,4)
        assert advance(stop=names['wait_for_completed_frame']-BASE).stop_reason==1
        assert (v('front_bitplane_base',4),v('back_bitplane_base',4),v('display_bitplane_base',4))==(0x78000,0x70000,0x78000)
        assert v('palette_transition_steps_remaining',1)==k['GAMEPLAY_FADE_SETUP_STEPS']


def test_title_initialization_and_iteration_preserve_record_byte9_and_grid_context(title):
    cpu,memory,read,write,slots,names,k,header,derived,app,v,start,prepare=title
    advance=prepare('terminal')
    assert memory[0x409:0x7E8:10]==b'\xA5'*100
    assert read(0x3FF,1)==0x5A and read(0x7E7,1)==0xA5
    assert (v('tilemap_base',4),v('tilemap_width'),v('tilemap_height'))==(header+8,20,8)
    before=v('title_star_palette_steps_remaining',1)
    assert advance(stop=0x1070,budget=1000000).stop_reason==1
    assert v('frame_counter',4)==0 and v('title_star_palette_steps_remaining',1)==before-1
    assert memory[0x409:0x7E8:10]==b'\xA5'*100


def test_title_deadline_is_wrapped_entry_plus150_and_skipping_equality_does_not_reveal(title):
    cpu,memory,read,write,slots,names,k,header,derived,app,v,start,prepare=title
    for counter in [0,0xFFFFFFC0]:
        advance=prepare(counter=counter);deadline=(counter+150)&0xFFFFFFFF
        assert cpu.d[5]==deadline
        for observed in [(deadline-1)&0xFFFFFFFF,(deadline+1)&0xFFFFFFFF,deadline]:
            app('frame_counter',observed,4)
            assert advance(stop=0x1070,budget=1000000).stop_reason==1
            assert cpu.d[5]==deadline
            assert bool(v('world_interaction_audio_flags',1)&1)==(observed==deadline)
            assert v('palette_transition_steps_remaining',1)==(15 if observed==deadline else 0)
            assert advance(stop=0xFD2).stop_reason==1


def test_repeated_equal_counter_reloads_gradient_then_loop_clock_advances_without_frame_change(title):
    cpu,memory,read,write,slots,names,k,header,derived,app,v,start,prepare=title
    advance=prepare();app('frame_counter',150,4)
    assert advance(stop=0x1070,budget=1000000).stop_reason==1
    first=bytes(memory[SCRATCH:SCRATCH+192])
    assert v('palette_transition_steps_remaining',1)==15
    assert advance(stop=0xFD2).stop_reason==1
    assert advance(stop=0x1070,budget=1000000).stop_reason==1
    assert v('palette_transition_steps_remaining',1)==15 and memory[SCRATCH:SCRATCH+192]==first
    assert advance(stop=0xFD2).stop_reason==1
    app('frame_counter',151,4)
    for remaining in range(14,-1,-1):
        assert advance(stop=0x1070,budget=1000000).stop_reason==1
        assert v('palette_transition_steps_remaining',1)==remaining and v('frame_counter',4)==151
        assert advance(stop=0xFD2).stop_reason==1
    assert v('title_star_palette_steps_remaining',1)==0 and not v('status_flags',1)&4


def test_title_gradient_writers_touch_only_the192_byte_shared_prefix(title):
    cpu,memory,read,write,slots,names,k,header,derived,app,v,start,prepare=title
    memory[SCRATCH-4:SCRATCH+260]=b'\xA5'*264
    advance=prepare()
    assert memory[SCRATCH:SCRATCH+192]==bytes(192)
    assert memory[SCRATCH-4:SCRATCH]==b'\xA5'*4 and memory[SCRATCH+192:SCRATCH+260]==b'\xA5'*68
    app('frame_counter',150,4)
    assert advance(stop=0x1070,budget=1000000).stop_reason==1
    assert memory[SCRATCH-4:SCRATCH]==b'\xA5'*4 and memory[SCRATCH+192:SCRATCH+260]==b'\xA5'*68


def test_all_audio_flag_bytes_gate_the_real_foreground_service_and_feedback_clears_only_bit0(title):
    cpu,memory,read,write,slots,names,k,header,derived,app,v,start,prepare=title
    advance=prepare()
    for flags in range(256):
        app('world_interaction_audio_flags',flags,1);deadline=cpu.d[5]
        if flags&1:
            assert advance(stop=names['update_audio_channels']-BASE,budget=1000000).stop_reason==1
            assert advance(stop=0xFEC,budget=100000).stop_reason==1
        else:assert advance(stop=0xFEC,budget=1000000).stop_reason==1
        assert cpu.d[5]==deadline and cpu.a[6]==APP
        assert v('world_interaction_audio_flags',1)==flags
        assert advance(stop=0x1070,budget=100000).stop_reason==1
        assert advance(stop=0xFD2).stop_reason==1
    for flags in range(256):
        app('world_interaction_audio_flags',flags,1);cpu.d[0]=0x107
        start('start_feedback_audio_sequence')
        assert v('world_interaction_audio_flags',1)==flags&~1 and cpu.a[6]==APP
