"""Original planar reader/callback RAM writes after original Amiga table init.

Only supplied span records and backing are qualified. This is not boot,
palette/RGB, scanout, global row/selector validity or shared lifetime proof.
"""
import ctypes

import pytest

from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, FB, INPUT, STACK, RETURN
from tests.test_starglider2_control_normalization import signed

ENTRY, ROWS, MASK32, MASK16 = 0x3DD12, 0x416B8, 0x3FFBA, 0x40FBA
PACKET, SNAPSHOT, DIAGNOSTIC = INPUT + 0x1000, 0x416A8, 0xE103


def word(m, p, value):
    put(m, p, value & 65535, 2)


@pytest.fixture(scope='module')
def initialized(original_image):
    raw = original_image[0]
    m = (ctypes.c_uint8 * 0xA1000)()
    ctypes.memmove(ctypes.addressof(m) + 0x1000, raw, len(raw))
    word(m, 0x1002, 0x8000)
    cpu = state(m, 0x3E96E)
    run(original_image, m, cpu, {RETURN}, limit=50000)
    assert all(get(m, ROWS + 2 * y, 2) == 40 * y for y in range(200))
    for bits, base in [(32, MASK32), (16, MASK16)]:
        for a in range(bits):
            for b in range(bits):
                lo, hi = min(a, b), max(a, b)
                inside = ((1 << (hi - lo + 1)) - 1) << (bits - 1 - hi)
                assert get(m, base + (a * bits + b) * (bits // 8), bits // 8) == ((1 << bits) - 1) ^ inside
    return bytes(m)


def prepare(m, initialized, records, pattern=0xA5):
    if initialized is not None:
        ctypes.memmove(ctypes.addressof(m), initialized, len(initialized))
    m[FB - 16:FB + 0x8010] = bytes([pattern]) * 0x8020
    put(m, SNAPSHOT, FB)
    p = PACKET
    for i, (style, y, spans) in enumerate(records):
        put(m, INPUT + 4 * i, p)
        word(m, p, style)
        word(m, p + 2, y)
        p += 4
        for left, right in spans:
            word(m, p, left)
            word(m, p + 2, right)
            p += 4
        word(m, p, 65535)
        p += 2
    put(m, INPUT + 4 * len(records), 0xFFFFFFFF)
    cpu = state(m, ENTRY)
    cpu.a[2] = INPUT
    return cpu


def expected_memory(m, records):
    result = bytearray(m)
    result[DIAGNOSTIC] = 5
    for style, y, spans in records:
        style = signed(style)
        if style >= 0:
            colour, bits, base_x = style, None, None
        else:
            negated = signed(-style)
            bits = 16 if negated < 16 else 32
            colour = ((negated * 2) & 65535) // 2 if bits == 16 else negated & 15
            base_x = ((min(spans[0]) if bits == 32 else spans[0][0]) // bits) * bits if spans else 0
        first_offset = signed(get(m, ROWS + 2 * y, 2))
        for row, (left, right) in enumerate(spans):
            if bits:
                left, right = base_x + min(left % bits, right % bits), base_x + max(left % bits, right % bits)
            else:
                left, right = min(left, right), max(left, right)
            for x in range(left, right + 1):
                for plane in range(4):
                    address = FB + 8192 * plane + first_offset + 40 * row + x // 8
                    bit = 0x80 >> (x % 8)
                    result[address] = (result[address] & (~bit & 255)) | (bit if colour & (1 << plane) else 0)
    return result


def callback(raw, style):
    if style >= 0:
        base, index = 0x3DD8E, style
    else:
        negated = signed(-style)
        base = 0x3EDC4 if negated < 16 else 0x3EA92
        index = ((2 * negated) & 65535) // 2 if negated < 16 else negated & 15
    p = base - 0x1000 + 2 * index
    return base + int.from_bytes(raw[p:p + 2], 'big', signed=True)


SPANS = [(0, 0), (1, 1), (0, 31), (31, 32), (0, 319), (5, 69),
         (63, 127), (287, 319), (16, 15), (32, 95), (10, 200), (319, 319)]


@pytest.mark.parametrize('colour', range(16))
@pytest.mark.parametrize('span', SPANS)
@pytest.mark.parametrize('pattern', [0, 0xA5])
def test_complete_regular_reader_and_all_callbacks(original_image, memory, initialized, colour, span, pattern):
    records = [(colour, 17, [span, span[::-1], (7, 43)])]
    cpu = prepare(memory, initialized, records, pattern)
    expected = expected_memory(memory, records)
    target, seen = callback(original_image[0], colour), []
    run(original_image, memory, cpu, {RETURN}, lambda pc: seen.append(pc) if pc == target else None)
    assert seen
    assert bytes(memory) == expected
    assert cpu.a[2] == INPUT + 8 and cpu.a[7] == STACK + 4
    assert INPUT + 4 in cpu.c  # The original reader transports the next reference through USP.


MASKED = [-16 - c for c in range(16)] + [-c for c in range(1, 16)] + [-32768]


@pytest.mark.parametrize('style', MASKED)
@pytest.mark.parametrize('local', [(0, 0), (1, 3), (0, 15), (15, 0), (7, 7), (4, 12),
                                 (0, 31), (16, 31), (31, 16)])
def test_masked_colour_families_use_original_generated_tables(original_image, memory, initialized, style, local):
    records = [(style, 197, [(32 + local[0], 32 + local[1]), (34, 38), (37, 35)])]
    cpu = prepare(memory, initialized, records)
    expected = expected_memory(memory, records)
    target, seen = callback(original_image[0], style), []
    run(original_image, memory, cpu, {RETURN}, lambda pc: seen.append(pc) if pc == target else None)
    assert seen
    assert bytes(memory) == expected
    assert cpu.a[2] == INPUT + 8 and cpu.a[7] == STACK + 4


@pytest.mark.parametrize('style', [-17, -1, -32768])
def test_masked_rows_keep_the_first_cell_column(original_image, memory, initialized, style):
    records = [(style, 3, [(35, 37), (70, 71), (110, 108)])]
    cpu = prepare(memory, initialized, records)
    expected = expected_memory(memory, records)
    run(original_image, memory, cpu, {RETURN})
    assert bytes(memory) == expected


@pytest.mark.parametrize('style', [-32, -32767])
def test_large_negative_selectors_keep_only_the_low_colour_nibble(original_image, memory, initialized, style):
    records = [(style, 0, [(35, 37)])]
    cpu = prepare(memory, initialized, records)
    expected = expected_memory(memory, records)
    run(original_image, memory, cpu, {RETURN})
    assert bytes(memory) == expected


def test_reference_and_empty_span_handoffs_restore_usp_cursor(original_image, memory, initialized):
    records = [(3, 0, []), (-17, 2, [(35, 37)]), (-32768, 4, []), (12, 7, [(90, 10), (1, 1)])]
    cpu = prepare(memory, initialized, records)
    expected = expected_memory(memory, records)
    run(original_image, memory, cpu, {RETURN})
    assert bytes(memory) == expected
    assert cpu.a[2] == INPUT + 4 * (len(records) + 1) and cpu.a[7] == STACK + 4


def test_empty_reference_list_never_enters_a_callback(original_image, memory, initialized):
    cpu = prepare(memory, initialized, [])
    expected = expected_memory(memory, [])
    run(original_image, memory, cpu, {RETURN})
    assert bytes(memory) == expected and cpu.a[2] == INPUT + 4
    assert cpu.a[7] == STACK + 4 and not any(cpu.c)


def test_first_row_lookup_then_constant_stride_not_per_row_lookup(original_image, memory, initialized):
    records = [(5, 3, [(0, 5), (8, 12)])]
    cpu = prepare(memory, initialized, records)
    word(memory, ROWS + 6, 200)
    word(memory, ROWS + 8, 900)
    expected = expected_memory(memory, records)
    run(original_image, memory, cpu, {RETURN})
    assert bytes(memory) == expected


def test_uninitialized_mask_is_an_entry_state_difference_not_a_new_table_definition(original_image, memory):
    records = [(-17, 0, [(4, 6)])]
    cpu = prepare(memory, None, records)
    assert get(memory, MASK32 + (4 * 32 + 6) * 4) == 0
    expected = expected_memory(memory, [(1, 0, [(0, 31)])])
    run(original_image, memory, cpu, {RETURN})
    assert bytes(memory) == expected


@pytest.mark.parametrize('style', [16, 16383, 16384, 32767])
def test_regular_selector_is_not_clamped_to_dispatch_table(original_image, memory, initialized, style):
    cpu = prepare(memory, initialized, [(style, 0, [(0, 1)])])
    run(original_image, memory, cpu, {0x3DD3E})
    assert cpu.d[3] & 65535 == (2 * style) & 65535


@pytest.mark.parametrize('flags', [0, 32767])
def test_nonnegative_platform_gate_leaves_planar_setup_to_the_other_reader(original_image, memory, initialized, flags):
    cpu = prepare(memory, initialized, [(3, 0, [(0, 1)])])
    word(memory, 0x1002, flags)
    before = bytes(memory)
    run(original_image, memory, cpu, {0x3F084})
    assert bytes(memory) == before and cpu.a[2] == INPUT and not any(cpu.c)
