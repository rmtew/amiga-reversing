"""Original overlay text, registration and startup-clear composition.

Explicit RAM/MMIO inputs; no instruction patches, pixel DMA or ordinary overflow
claim. Queue callback processing remains bounded to its original sixteen slots.
"""
import pytest

from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import resolve_project_paths
from tests.test_pandora_state_transitions import BASE,TARGET,cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_render_order import sequencer

pytestmark=pytest.mark.parametrize('cpu_fixture',[0x1000000],indirect=True)
APP,DESC,TEXT,OUTPUT=0x39fc,0x81000,0x83000,0x85000


@pytest.fixture
def overlays(cpu_fixture,title_slots):
    cpu,memory,schemas,read,write,run=cpu_fixture
    m=effective_target_metadata(resolve_project_paths(TARGET).target_dir)
    names={a.name:BASE+a.addr for a in m.seeded_entities if a.name}
    names.update({a.name:BASE+a.addr for a in m.seeded_code_labels if a.name})
    names.update({a.name:a.addr for a in m.absolute_code_labels if a.name})
    fields=schemas['ui_overlay_descriptor'];queue=BASE+next(a.source_start for a in m.data_block_layouts if a.name=='ui_overlay_update_queue')
    def app(name,value,size=4):write(APP+title_slots['app_'+name],value,size)
    def call(source,stop=None,budget=100000):
        source=names[source]-BASE if isinstance(source,str) else source
        stop=names[stop]-BASE if isinstance(stop,str) else stop
        trace=sequencer(cpu,memory,write)(source,stop=stop,budget=budget)
        assert trace.stop_reason==1 and trace.steps<budget
        return trace
    def descriptor(width=6,height=3,x=5,y=3):
        memory[DESC:DESC+44]=bytes(44)
        for name,value in [('x',x),('y',y),('width',width),('height',height)]:write(DESC+fields[name],value,1)
        write(DESC+fields['bitmap_ptr'],0x68000)
        cpu.a[5],cpu.a[6]=DESC,APP
    cpu.a[6]=APP;run(0x9ebe,stop=0x9ed4,budget=2048)
    app('font_glyph_bitmap_table_ptr',names['compact_font_index_origin'])
    app('font_glyph_layout_table_ptr',BASE+0xaafe)
    write(0xdff01e,0x40,2);descriptor()
    assert queue+128==BASE+0xa8e2
    return cpu,memory,read,write,fields,names,title_slots,queue,app,call,descriptor


def test_startup_clear_covers_queue_and_64_byte_tail_but_not_first_font_glyph(overlays):
    cpu,memory,read,write,f,names,slots,queue,app,call,descriptor=overlays
    memory[queue-4:queue+132]=bytes([0xa5])*136
    call('clear_overlay_pointer_storage')
    assert memory[queue:queue+128]==bytes(128)
    assert memory[queue-4:queue]==memory[queue+128:queue+132]==bytes([0xa5])*4
    assert cpu.a[0]==queue+128 and cpu.d[7]&65535==65535


def test_selected_row_clear_retains_byte_width_wrap_and_saved_inputs(overlays):
    cpu,memory,read,write,f,names,slots,queue,app,call,descriptor=overlays
    for width in [0,1,2,3,4,6,40,255]:
        for index in [0,1,5,6,31,127,255,256]:
            descriptor(width=width);memory[0x70000:0x78000]=bytes([0xa5])*0x8000
            origin=1280*((3+1+(index&255))&31)+6
            columns=((width-3)&255)+1
            expected=bytearray(memory[0x70000:0x78000])
            for column in range(columns):
                for row in range(8):
                    for plane in range(4):expected[origin+column+row*160+plane*40]=0
            cpu.d[0],cpu.d[7]=0xabcd0000|index,0x12345678
            cpu.a[0],cpu.a[1],cpu.a[2]=0x12340000,0x56780000,0x9abc0000
            before=(cpu.d[0],cpu.d[7],tuple(cpu.a[:3]))
            call(0x640e)
            assert memory[0x70000:0x78000]==expected
            assert (cpu.d[0],cpu.d[7],tuple(cpu.a[:3]))==before
            assert read(APP+slots['app_text_cursor_ptr'])==0x70000+origin
            assert read(APP+slots['app_text_plane_mask'],1)==0 and cpu.a[5]==DESC


def test_selected_line_pointer_uses_wrapped_signed_word_index_not_six_line_bound(overlays):
    cpu,memory,read,write,f,names,slots,queue,app,call,descriptor=overlays
    for index in [0,1,5,6,7,0x3fff,0x4000,0x7fff,0x8000,0xbfff,0xc000,0xffff]:
        descriptor();word=(index*4)&65535;offset=word if word<32768 else word-65536
        write(DESC+12+offset,TEXT)
        cpu.d[0]=index;call('redraw_ui_overlay_selected_line_proportional',stop='draw_proportional_ui_text_string')
        origin=0x70000+1280*((3+1+(index&255))&31)+5
        assert cpu.a[3]==TEXT
        assert read(APP+slots['app_proportional_text_word_cursor_ptr'])==origin
        assert read(APP+slots['app_proportional_text_pixel_shift'],1)==8
        assert read(APP+slots['app_text_cursor_ptr'])==origin+1
    # Out-of-prefix reads above are controlled injections, not admitted UI rows.


def test_six_line_dispatch_combines_prefix_nulls_and_style_bits_with_actual_fonts(overlays):
    cpu,memory,read,write,f,names,slots,queue,app,call,descriptor=overlays
    for style in range(64):
        for prefix in range(7):
            descriptor(height=3);write(DESC+f['line_style_flags'],style|0xc0,1)
            for line in range(6):
                memory[TEXT+16*line:TEXT+16*line+2]=b'A\0'
                write(DESC+f['line_0_ptr']+4*line,TEXT+16*line if line<prefix else 0)
            memory[0x70000:0x78000]=bytes([0xa5])*0x8000
            expected=bytearray(memory[0x70000:0x78000])
            for line in range(prefix):
                if style&(1<<line):continue  # Mask zero emits no proportional DMA.
                origin=1280*(4+line)+6
                for row in range(8):
                    for plane in range(4):expected[origin+row*160+plane*40]=0
            cpu.d[7]=0x12345678;cpu.a[4]=0x456789ab
            call('draw_ui_overlay_text_lines')
            assert memory[0x70000:0x78000]==expected
            assert cpu.d[7]==0x12345678 and cpu.a[4]==0x456789ab and cpu.a[5]==DESC
            assert read(APP+slots['app_text_cursor_ptr'])==0x70000+1280*9+6+int(prefix==6 and not style&32)
            assert read(DESC+f['height'],1)==3  # Height does not bound the six visits.


def test_full_registration_can_reach_space_glyph_and_startup_clear_does_not_restore_it(overlays):
    cpu,memory,read,write,f,names,slots,queue,app,call,descriptor=overlays
    font=queue+128
    assert memory[font:font+8]==bytes(8)
    for index in range(32):write(queue+4*index,DESC+0x100)
    descriptor(width=3,height=3)
    call('enqueue_ui_overlay_update')
    assert read(font)==DESC and read(DESC+f['state_flags'],1)&128
    assert all(read(queue+4*i)==DESC+0x100 for i in range(32))
    assert memory[font+4:font+8]==bytes(4)
    call('clear_overlay_pointer_storage')
    assert memory[queue:queue+128]==bytes(128) and read(font)==DESC
    memory[TEXT:TEXT+2]=b' \0';cpu.a[3]=TEXT
    app('text_cursor_ptr',OUTPUT);app('text_plane_mask',1,1)
    call('draw_compact_text_string')
    assert [read(OUTPUT+160*row,1) for row in range(8)]==list(memory[font:font+8])
    assert any(read(OUTPUT+160*row,1) for row in range(8))
    # The full prefix is injected. No normal 33-registration route is claimed.


def test_callback_ready_word_uses_state_sign_not_low_style_byte_and_null_still_skips(overlays):
    cpu,memory,read,write,f,names,slots,queue,app,call,descriptor=overlays
    memory[queue:queue+128]=bytes(128);write(queue+60,DESC)
    for flags in range(256):
        for style in [0,128,255]:
            descriptor();write(DESC+f['state_flags'],flags,1);write(DESC+f['line_style_flags'],style,1)
            write(DESC+f['update_callback'],names['snapshot_inventory_cursor_and_clear_hidden_latch'])
            app('inventory_cursor_x',0x12345678);app('inventory_cursor_snapshot_x',0xccccdddd)
            app('inventory_cursor_sprite_flags',255,1)
            call('process_ui_overlay_update_queue')
            assert read(APP+slots['app_inventory_cursor_snapshot_x'])==(0x12345678 if flags&128 else 0xccccdddd)
            assert read(APP+slots['app_inventory_cursor_sprite_flags'],1)==(254 if flags&128 else 255)
            assert read(DESC+f['state_flags'],1)==flags and read(DESC+f['line_style_flags'],1)==style
            assert cpu.a[0]==queue+64 and cpu.d[7]&65535==65535
    write(DESC+f['update_callback'],0);write(DESC+f['state_flags'],255,1)
    app('inventory_cursor_snapshot_x',0xccccdddd);call('process_ui_overlay_update_queue')
    assert read(APP+slots['app_inventory_cursor_snapshot_x'])==0xccccdddd
