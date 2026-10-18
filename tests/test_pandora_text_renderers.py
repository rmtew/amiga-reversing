"""Original text CPU copies/packets; bounded RAM and MMIO shadows, no pixel DMA."""
import json

import pytest

from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_render_order import sequencer

APP, TEXT, FONT, DEST = 0x39FC, 0x80000, 0x85000, 0x88000


def prepare(cpu_fixture, slots, text=b'A\0', shift=0, mask=1):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6], cpu.a[3] = APP, TEXT
    memory[TEXT:TEXT+len(text)] = text
    write(APP+slots['app_text_cursor_ptr'], DEST)
    write(APP+slots['app_proportional_text_word_cursor_ptr'], DEST)
    write(APP+slots['app_proportional_text_pixel_shift'], shift, 1)
    write(APP+slots['app_text_plane_mask'], mask, 1)
    write(APP+slots['app_font_glyph_bitmap_table_ptr'], FONT)
    write(APP+slots['app_font_glyph_layout_table_ptr'], FONT)
    return cpu, memory, read, write, run


def test_compact_glyph_all_plane_masks_copy_or_clear_exactly_eight_rows(cpu_fixture, title_slots):
    cpu, memory, read, write, run = prepare(cpu_fixture, title_slots)
    glyph = bytes([0x81, 0x42, 0x24, 0x18, 0x3C, 0x66, 0xC3, 0xFF])
    memory[FONT:FONT+8] = glyph
    for mask in range(256):
        original = bytes([0xA5])*1288
        memory[DEST-4:DEST+1284] = original
        expected = bytearray(original)
        for plane in range(4):
            for row in range(8):expected[4+40*plane+160*row] = glyph[row] if mask & (1<<plane) else 0
        cpu.a[0], cpu.a[1], cpu.a[2], cpu.a[3] = FONT, DEST, 0x12345678, TEXT
        write(APP+title_slots['app_text_plane_mask'], mask, 1)
        before_a = list(cpu.a[:7])
        assert sequencer(cpu, memory, write)(0x60A2, budget=256).stop_reason == 1
        assert memory[DEST-4:DEST+1284] == expected
        assert list(cpu.a[:7]) == before_a
        assert read(APP+title_slots['app_text_cursor_ptr']) == DEST


def test_compact_string_controls_reload_stored_origin_and_cr_uses_saved_line_origin(cpu_fixture, title_slots):
    # Each glyph is drawn at all four planes, including clearing disabled planes.
    # Byte one moves the stored line origin, independent of live A1 glyph advances.
    for text, final_offset, placements in [
        (b'\0', 0, []), (b'AB\0', 2, [(0, 65), (1, 66)]),
        (b'AB\x01C\0', 2, [(0, 65), (1, 67)]),
        (b'AB\rC\0', 1281, [(0, 65), (1, 66), (1280, 67)]),
        (b'A\x01B\rC\0', 1281, [(0, 65), (1, 66), (1280, 67)]),
        (b'\r\rA\0', 2561, [(2560, 65)]),
        (b'a{\xff\0', 3, [(0, 65), (1, 91), (2, 223)]),
    ]:
        cpu, memory, read, write, run = prepare(cpu_fixture, title_slots, text=text)
        for code in range(256):memory[FONT+code*8:FONT+code*8+8] = bytes((code+row)&255 for row in range(8))
        memory[DEST-4:DEST+4004] = bytes([0xA5])*4008
        expected = bytearray(memory[DEST-4:DEST+4004])
        for column, code in placements:
            for row in range(8):
                for plane in range(4):expected[4+column+row*160+plane*40] = (code+row)&255 if plane==0 else 0
        assert sequencer(cpu, memory, write)(0x6056, budget=4096).stop_reason == 1
        assert memory[DEST-4:DEST+4004] == expected
        assert cpu.a[1] == read(APP+title_slots['app_text_cursor_ptr']) == DEST+final_offset
        assert cpu.a[3] == TEXT+len(text) and cpu.a[7] == 0x9004


def test_proportional_all_real_map_entries_select_existing_68_record_headers(cpu_fixture, title_slots):
    cpu, memory, read, write, run = prepare(cpu_fixture, title_slots)
    write(APP+title_slots['app_font_glyph_layout_table_ptr'], BASE+0xAAFE)
    for code in range(32, 128):
        memory[TEXT:TEXT+2] = bytes([code, 0])
        cpu.a[3] = TEXT
        run(0x6146, stop=0x6172)
        index = read(BASE+0xAF3E+code-32, 1)
        assert index < 68
        assert cpu.a[1] == BASE+0xAAFE+16*index+2
        assert cpu.d[1] & 65535 == read(BASE+0xAAFE+16*index, 2)
    # Invalid non-NUL bytes use wrapped BYTE subtraction with no map-length guard.
    for code in (1, 13, 31, 128, 255):
        memory[TEXT:TEXT+2] = bytes([code, 0])
        cpu.a[3] = TEXT
        run(0x6146, stop=0x6172)
        index = read(BASE+0xAF3E+((code-32)&255), 1)
        assert cpu.a[1] == BASE+0xAAFE+16*index+2


def test_proportional_phase_and_advance_byte_wrap_choose_original_one_or_two_word_geometry(cpu_fixture, title_slots):
    cpu, memory, read, write, run = prepare(cpu_fixture, title_slots)
    glyph_index = read(BASE+0xAF3E+65-32, 1)
    cases = {(shift, width) for shift in range(256) for width in (0, 1, 15, 16, 17, 255)}
    cases |= {(shift, width) for width in range(256) for shift in (0, 1, 15, 16, 255)}
    for shift, width in sorted(cases):
        write(APP+title_slots['app_proportional_text_pixel_shift'], shift, 1)
        write(FONT+16*glyph_index, 0xAB00|width, 2)
        cpu.a[3] = TEXT
        cpu.d[6] = 0xABCD1357
        run(0x6146, stop=0x61A4)
        summed = (shift+width)&255
        straddles = summed > 16
        assert cpu.d[0] & 65535 == 160-(4 if straddles else 2)
        assert cpu.d[2] & 65535 == ((shift<<12)|0xBFA)&65535
        assert cpu.d[3] == (0 if straddles else 0xFFFFFFFF)
        assert cpu.d[4] == (2 if summed>=16 else 0)
        assert cpu.d[5] & 65535 == 0x1C1+int(straddles)
        assert cpu.d[6] == (0xFFFFFFFE if straddles else 0xABCD0000)
        assert cpu.d[7] & 255 == summed


@pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
def test_proportional_packets_preserve_inherited_first_mask_and_saved_registers(cpu_fixture, title_slots):
    hardware = json.loads((PROJECT_ROOT/'knowledge/amiga_hw_registers.json').read_text())
    hw = {r['name']: int(r['address_68k'], 16) for r in hardware['registers']}
    for phase, width in [(0, 6), (10, 6), (11, 6), (255, 1)]:
        for mask in range(16):
            cpu, memory, read, write, run = prepare(cpu_fixture, title_slots, shift=phase, mask=mask)
            glyph = FONT+16*read(BASE+0xAF3E+65-32, 1)
            write(glyph, width, 2)
            write(hw['INTREQR'], 0x40, 2)
            write(hw['BLTAFWM'], 0xA55A, 2)
            write(hw['BLTSIZE'], 0x1234, 2)
            for r in range(3, 8):cpu.d[r] = 0x12340000+r
            cpu.a[4], cpu.a[5] = 0x12345678, 0x87654321
            before_d, before_a = list(cpu.d[3:]), list(cpu.a[4:7])
            run(0x6146, budget=512)
            summed = (phase+width)&255
            assert read(APP+title_slots['app_proportional_text_pixel_shift'], 1) == summed&15
            assert read(APP+title_slots['app_proportional_text_word_cursor_ptr']) == DEST+(2 if summed>=16 else 0)
            assert list(cpu.d[3:]) == before_d and list(cpu.a[4:7]) == before_a
            assert cpu.a[3] == TEXT+2
            assert read(hw['BLTAFWM'], 2) == 0xA55A
            if not mask:assert read(hw['BLTSIZE'], 2) == 0x1234
            else:
                plane = mask.bit_length()-1
                assert read(hw['BLTDPTH']) == read(hw['BLTCPTH']) == DEST+40*plane
                assert read(hw['BLTAPTH']) == glyph+2
                assert read(hw['BLTCON0'], 2) == ((phase<<12)|0xBFA)&65535
                assert read(hw['BLTCON1'], 2) == 0
                assert read(hw['BLTSIZE'], 2) == 0x1C1+int(summed>16)
                assert read(hw['BLTALWM'], 2) == (0 if summed>16 else 65535)
                assert read(hw['BLTAMOD'], 2) == (65534 if summed>16 else 0)
                assert read(hw['BLTCMOD'], 2) == read(hw['BLTDMOD'], 2) == 160-(4 if summed>16 else 2)
            # The MMIO shadow performs no pixel transfers.
            assert memory[DEST:DEST+1280] == bytes(1280)


@pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
def test_proportional_poll_waits_before_packet_but_returns_after_final_launch_and_empty_needs_no_font(cpu_fixture, title_slots):
    hardware = json.loads((PROJECT_ROOT/'knowledge/amiga_hw_registers.json').read_text())
    hw = {r['name']: int(r['address_68k'], 16) for r in hardware['registers']}
    cpu, memory, read, write, run = prepare(cpu_fixture, title_slots)
    glyph = FONT+16*read(BASE+0xAF3E+65-32, 1)
    write(glyph, 6, 2)
    write(hw['INTREQR'], 0, 2); write(hw['BLTSIZE'], 0x1234, 2)
    advance = sequencer(cpu, memory, write)
    assert advance(0x6146, stop=0x61BA).stop_reason == 1
    assert advance(stop=0x61F4, budget=12).stop_reason == 3
    assert cpu.pc == BASE+0x61BA and read(hw['BLTSIZE'], 2) == 0x1234
    write(hw['INTREQR'], 0x40, 2)
    assert advance(stop=0x61F4).stop_reason == 1
    assert read(hw['BLTSIZE'], 2) == 0x1C1
    write(hw['INTREQR'], 0, 2)
    assert advance().stop_reason == 1  # No completion wait after final launch.
    assert read(APP+title_slots['app_proportional_text_pixel_shift'], 1) == 6
    prepare(cpu_fixture, title_slots, text=b'\0', shift=0xA5)
    write(APP+title_slots['app_font_glyph_layout_table_ptr'], 0xFFFFFFFF)
    run(0x6146)
    assert read(hw['BLTSIZE'], 2) == 0x1C1
    assert read(APP+title_slots['app_proportional_text_pixel_shift'], 1) == 0xA5
    assert read(APP+title_slots['app_proportional_text_word_cursor_ptr']) == DEST


def test_text_cursor_masks_then_sign_extends_wrapped_word_lookup_even_outside_row_table(cpu_fixture, title_slots):
    cpu, memory, read, write, run = prepare(cpu_fixture, title_slots)
    for y in (0, 24, 25, 31, 0xFFFF):
        for row_value in (0, 0x7FFF, 0x8000, 0xFFFF):
            write(APP+2*((y&31)*8), row_value, 2)
            write(APP+title_slots['app_front_bitplane_base'], 0x78000)
            for x in (0, 39, 63, 64, 0xFFFF):
                for entry, base in [(0x6108, 0x78000), (0x6126, 0x70000)]:
                    cpu.d[0], cpu.d[1] = 0xABCD0000|x, 0xDCBA0000|y
                    run(entry)
                    offset = (row_value+(x&63))&65535
                    expected = (base+offset-(65536 if offset&0x8000 else 0))&0xFFFFFFFF
                    assert cpu.a[0] == read(APP+title_slots['app_text_cursor_ptr']) == expected
