"""Original tile-grid expansion and CPU blit packets; MMIO performs no DMA."""
import pytest

from tests.test_pandora_state_transitions import BASE, RETURN, cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_render_order import sequencer

pytestmark = pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
APP, CUSTOM, GRID, BACK = 0x39FC, 0xDFF000, 0x50000, 0x70000


def configure(cpu_fixture, slots, width=90, height=129, column=0, row=0):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = APP
    for name, value, size in [('app_tilemap_base', GRID, 4), ('app_back_bitplane_base', BACK, 4),
                              ('app_tilemap_width', width, 2), ('app_tilemap_height', height, 2),
                              ('app_tile_column', column, 2), ('app_tile_row', row, 2)]:
        write(APP+slots[name], value, size)
    return cpu, memory, read, write, run


def test_all_original_macro_ids_expand_into_the_exact_90_by_129_pointer_grid(cpu_fixture, title_slots):
    cpu, memory, read, write, run = configure(cpu_fixture, title_slots)
    write(APP+title_slots['app_tilemap_base'], 0x4000)
    ids = [read(BASE+0x3502+2*i, 2) for i in range(43*30)]
    offsets = [read(BASE+0x3F16+2*i, 2) for i in range(468*9)]
    assert min(ids) == 0 and max(ids) == 467
    assert min(offsets) == 0 and max(offsets) == 0xFD80 and all(o%128==0 for o in offsets)
    expected = bytearray(90*129*4)
    for macro, tile_id in enumerate(ids):
        macro_row, macro_col = divmod(macro, 30)
        for cell in range(9):
            r, c = divmod(cell, 3)
            address = 4*((3*macro_row+r)*90+3*macro_col+c)
            expected[address:address+4] = (BASE+0xD0A8+offsets[9*tile_id+cell]).to_bytes(4, 'big')
    fences = bytes(memory[0x3FFC:0x4000]), bytes(memory[0xF568:0xF56C])
    cpu.a[5] = 0xABCD8765
    advance = sequencer(cpu, memory, write)
    # The default fixture stack would overlap the fixed destination grid.
    cpu.a[7] = 0x98000
    write(0x98000, RETURN)
    assert advance(0xA198, budget=100000).stop_reason == 1
    assert bytes(memory[0x4000:0xF568]) == expected
    assert (bytes(memory[0x3FFC:0x4000]),bytes(memory[0xF568:0xF56C])) == fences
    assert cpu.a[5] == 0xABCD8765 and cpu.a[7] == 0x98004
    assert cpu.a[2] == BASE+0x3F16 and cpu.a[4] == 0xF568
    assert read(APP+title_slots['app_tile_pointer_grid_row_stride_bytes']) == 360
    assert read(APP+title_slots['app_tile_pointer_grid_byte_size']) == 46440
    assert read(APP+title_slots['app_tile_pointer_grid_end']) == 0xF568


def test_builder_footer_uses_current_metadata_with_word_wrapped_row_stride(cpu_fixture, title_slots):
    for width, height in [(90,129),(20,8),(0x4000,3),(0xFFFF,0xFFFF),(0x8001,0)]:
        cpu, memory, read, write, run = configure(cpu_fixture, title_slots,width,height)
        advance = sequencer(cpu, memory, write)
        write(0x9000, 0x87654321)  # Footer's saved A5 before its return address.
        write(0x9004, RETURN)
        assert advance(0xA238).stop_reason == 1
        stride = (width*4)&0xFFFF
        size = stride*height
        assert read(APP+title_slots['app_tile_pointer_grid_row_stride_bytes']) == stride
        assert read(APP+title_slots['app_tile_pointer_grid_byte_size']) == size
        assert read(APP+title_slots['app_tile_pointer_grid_end']) == (GRID+size)&0xFFFFFFFF
        assert cpu.a[5] == 0x87654321


def test_macro_record_lookup_sign_extends_word_index_but_zero_extends_pixel_offsets(cpu_fixture, title_slots):
    cpu, memory, read, write, run = configure(cpu_fixture, title_slots)
    for tile_id in (0,467,1820,1821,0x7FFF,0xFFFF):
        displacement = (tile_id*18)&0xFFFF
        if displacement&0x8000:displacement -= 65536
        values = [0,1,0x7FFF,0x8000,0xFFFF,128,256,384,512]
        for i,value in enumerate(values):write(BASE+0x3F16+displacement+2*i,value,2)
        write(BASE+0x3502,tile_id,2)
        run(0xA198,stop=0xA228,budget=100)
        for value,offset in zip(values,(0,4,8,360,364,368,720,724,728)):
            assert read(0x4000+offset) == BASE+0xD0A8+value
    # Synthetic IDs witness unchecked signed index arithmetic, not valid records.


@pytest.mark.parametrize('width,height,column,row', [(90,129,70,128),(20,3,19,2)])
def test_viewport_programs_160_packets_with_vertical_wrap_and_no_horizontal_clamp(cpu_fixture,title_slots,width,height,column,row):
    cpu,memory,read,write,run = configure(cpu_fixture,title_slots,width,height,column,row)
    for i in range(width*height+40):write(GRID+4*i,0x90000+128*i)
    write(CUSTOM+0x44,0xA55A,2)
    write(CUSTOM+0x42,0x2345,2)
    write(CUSTOM+0x1E,0x40,2)
    before = bytes(memory[BACK:BACK+0x6000])
    advance = sequencer(cpu,memory,write)
    cursor = 4*(row*width+column)
    for r in range(8):
        for c in range(20):
            assert advance(0x6728 if r==c==0 else None,stop=0x679A).stop_reason == 1
            assert read(CUSTOM+0x50) == 0x90000+128*(cursor//4+c)
            assert read(CUSTOM+0x54) == BACK+2560*r+2*c
            assert read(CUSTOM+0x58,2) == 0x1001
            assert read(CUSTOM+0x64,2) == 0 and read(CUSTOM+0x66,2) == 38
            assert read(CUSTOM+0x40,2) == 0x9F0 and read(CUSTOM+0x46,2) == 0xFFFF
            assert read(CUSTOM+0x44,2) == 0xA55A and read(CUSTOM+0x42,2) == 0x2345
        cursor += width*4
        if cursor>=width*height*4:cursor -= width*height*4
    write(CUSTOM+0x1E,0,2)
    assert advance().stop_reason == 1
    assert cpu.a[2] == GRID+cursor and cpu.a[1] == BACK+8*2560
    assert bytes(memory[BACK:BACK+0x6000]) == before


def test_viewport_initial_word_arithmetic_preserves_unscaled_product_high_word(cpu_fixture,title_slots):
    for width in (0,20,90,8191,8192,0xFFFF):
        for row in (0,1,128,0x7FFF,0xFFFF):
            for col in (0,19,0xFFFF):
                cpu,memory,read,write,run = configure(cpu_fixture,title_slots,width,129,col,row)
                run(0x6728,stop=0x677A)
                product = width*row
                offset = (product&0xFFFF0000)|(((product+col)*4)&0xFFFF)
                assert cpu.a[2] == (GRID+offset)&0xFFFFFFFF
                assert cpu.a[4] == GRID+width*129*4
                assert cpu.d[2]&0xFFFF == (width*4)&0xFFFF


def test_both_tile_blitters_poll_before_packets_and_return_without_final_wait(cpu_fixture,title_slots):
    for entry,wait,stop in [(0x6728,0x677E,0x679A),(0x67B2,0x67BA,0x67E8)]:
        cpu,memory,read,write,run = configure(cpu_fixture,title_slots)
        cpu.a[0],cpu.a[1],cpu.a[5] = 0x82000,BACK,0x12345678
        for offset,value in [(0x1E,0),(0x44,0xA55A),(0x46,0x5AA5),(0x42,0x2345),(0x58,0x1234)]:write(CUSTOM+offset,value,2)
        advance = sequencer(cpu,memory,write)
        assert advance(entry,stop=wait).stop_reason == 1
        assert advance(stop=stop,budget=9).stop_reason == 3
        assert cpu.pc == BASE+wait and read(CUSTOM+0x58,2) == 0x1234
        write(CUSTOM+0x1E,0x40,2)
        assert advance(stop=stop).stop_reason == 1
        if entry==0x67B2:
            assert read(CUSTOM+0x50) == 0x82000 and read(CUSTOM+0x54) == BACK
            assert read(CUSTOM+0x58,2) == 0x401
            assert read(CUSTOM+0x44,2) == 0xA55A and read(CUSTOM+0x46,2) == 0x5AA5
            assert read(CUSTOM+0x42,2) == 0x2345
            write(CUSTOM+0x1E,0,2)
            assert advance().stop_reason == 1 and cpu.a[5] == 0x12345678


def test_cell_pointer_and_packed_bounds_preserve_original_word_wrap(cpu_fixture,title_slots):
    values = (0,15,16,319,0x7FFF,0x8000,0xFFFF)
    for width in (0,20,90,0xFFFF):
        cpu,memory,read,write,run = configure(cpu_fixture,title_slots,width)
        for x in values:
            for y in values:
                cpu.d[0],cpu.d[1] = 0xABCD0000|x,0xDCBA0000|y
                saved = list(cpu.d[:2])
                run(0x67EC)
                product = (y>>4)*width
                cells = (product&0xFFFF0000)|((product+(x>>4))&0xFFFF)
                assert cpu.a[0] == (GRID+4*cells)&0xFFFFFFFF and list(cpu.d[:2]) == saved
                write(APP+title_slots['app_tilemap_scroll_x'],x,2)
                write(APP+title_slots['app_tilemap_scroll_y'],y,2)
                run(0x680A)
                assert cpu.d[0] == (((x+320)&0xFFFF)<<16)|x
                assert cpu.d[1] == (((y+128)&0xFFFF)<<16)|y


def test_modal_exchange_swaps_four_words_but_always_selects_modal_cells(cpu_fixture,title_slots):
    cpu,memory,read,write,run = configure(cpu_fixture,title_slots,90,129,70,128)
    fields = ['app_tilemap_width','app_tilemap_height','app_tile_column','app_tile_row']
    original = [90,129,70,128]
    modal = [20,8,0,0]
    for i,value in enumerate(modal):write(BASE+0x8A18+2*i,value,2)
    derived = ['app_tile_pointer_grid_row_stride_bytes','app_tile_pointer_grid_byte_size','app_tile_pointer_grid_end']
    for i,name in enumerate(derived):write(APP+title_slots[name],0x12340000+i)
    for incoming,outgoing in [(modal,original),(original,modal)]:
        run(0x921A)
        assert [read(APP+title_slots[n],2) for n in fields] == incoming
        assert [read(BASE+0x8A18+2*i,2) for i in range(4)] == outgoing
        assert read(APP+title_slots['app_tilemap_base']) == BASE+0x8A20
        assert cpu.a[0] == BASE+0x8A18
        assert [read(APP+title_slots[n]) for n in derived] == [0x12340000+i for i in range(3)]
