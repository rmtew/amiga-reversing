"""Original mode0 reader and profile-dependent mask initialization.

Finite fixture queues do not establish a homogeneous production sequence,
allocation bounds or lifetime. Mode1 is tested only through its entry gate;
full alternate startup, palette RGB and scanout remain outside these cases.
"""
import ctypes

import pytest

from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, FB, INPUT, STACK, RETURN
from tests.test_starglider2_planar_span_reader import initialized as amiga_initialized, MASK32, MASK16, ROWS, PACKET, SNAPSHOT, word
from tests.test_starglider2_control_normalization import signed

ENTRY, MODE = 0x3F084, 0x416A5


def inside_masks():
    result = bytearray()
    for a in range(16):
        for b in range(16):
            lo, hi = min(a, b), max(a, b)
            mask = ((1 << (hi - lo + 1)) - 1) << (15 - hi)
            result.extend(((mask << 16) | mask).to_bytes(4, 'big'))
    return bytes(result)


@pytest.fixture(scope='module')
def initialized(original_image):
    raw = original_image[0]
    m = (ctypes.c_uint8 * 0xA1000)()
    ctypes.memmove(ctypes.addressof(m) + 0x1000, raw, len(raw))
    word(m, 0x1002, 0)
    before = bytes(m)
    cpu = state(m, 0x3E96E)
    run(original_image, m, cpu, {RETURN}, limit=50000)
    assert bytes(m[ROWS:ROWS + 400]) == before[ROWS:ROWS + 400]
    assert all(get(m, ROWS + 2 * y, 2) == 160 * y for y in range(200))
    assert bytes(m[MASK32:MASK32 + 1024]) == inside_masks()
    assert bytes(m[MASK32 + 1024:MASK16 + 512]) == before[MASK32 + 1024:MASK16 + 512]
    return bytes(m)


def prepare(m, initialized, records, pattern=0xA5):
    if initialized is not None:
        ctypes.memmove(ctypes.addressof(m), initialized, len(initialized))
    m[FB - 16:FB + 0x8010] = bytes([pattern]) * 0x8020
    put(m, SNAPSHOT, FB)
    m[MODE] = 0
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


def paint(result, first_offset, row, left, right, colour):
    for x in range(left, right + 1):
        for plane in range(4):
            address = FB + first_offset + 160 * row + 8 * (x // 16) + 2 * plane
            value = int.from_bytes(result[address:address + 2], 'big')
            bit = 0x8000 >> (x % 16)
            value = (value & (~bit & 65535)) | (bit if colour & (1 << plane) else 0)
            result[address:address + 2] = value.to_bytes(2, 'big')


def expected_memory(m, records):
    result = bytearray(m)
    for style, y, spans in records:
        negated = signed(-style)
        cell = style < 0 and negated < 16
        colour = (((2 * negated) & 65535) // 2 if cell else negated & 15) if style < 0 else style
        column = (spans[0][0] // 16) * 16 if cell and spans else 0
        first_offset = signed(get(m, ROWS + 2 * y, 2))
        for row, (left, right) in enumerate(spans):
            if cell:
                left, right = column + min(left % 16, right % 16), column + max(left % 16, right % 16)
            else:
                left, right = min(left, right), max(left, right)
            paint(result, first_offset, row, left, right, colour)
    return result


SPANS = [(0, 0), (0, 15), (15, 16), (0, 319), (5, 69), (63, 127), (287, 319), (16, 15), (319, 319)]


@pytest.mark.parametrize('colour', range(16))
@pytest.mark.parametrize('span', SPANS)
@pytest.mark.parametrize('negative', [False, True])
def test_complete_regular_reader_and_wide_negative_styles(original_image, memory, initialized, colour, span, negative):
    style = -16 - colour if negative else colour
    records = [(style, 197, [span, span[::-1], (7, 43)])]
    cpu = prepare(memory, initialized, records)
    expected = expected_memory(memory, records)
    run(original_image, memory, cpu, {RETURN})
    assert bytes(memory) == expected
    assert cpu.a[2] == INPUT + 8 and cpu.a[7] == STACK + 4


@pytest.mark.parametrize('style', [-v for v in range(1, 16)] + [-32768])
@pytest.mark.parametrize('span', [(32, 32), (33, 37), (47, 32), (47, 47), (32, 63), (49, 62)])
def test_fixed_cells_keep_the_initial_column_and_use_initialized_inside_masks(original_image, memory, initialized, style, span):
    records = [(style, 3, [span, (70, 71), (110, 108)])]
    cpu = prepare(memory, initialized, records)
    expected = expected_memory(memory, records)
    run(original_image, memory, cpu, {RETURN})
    assert bytes(memory) == expected
    assert cpu.a[2] == INPUT + 8 and cpu.a[7] == STACK + 4


def test_mixed_finite_records_do_not_require_usp_to_transport_reference_cursor(original_image, memory, initialized):
    records = [(3, 0, []), (-1, 2, [(35, 37)]), (-32768, 4, []), (-28, 7, [(90, 10), (1, 1)])]
    cpu = prepare(memory, initialized, records)
    expected = expected_memory(memory, records)
    run(original_image, memory, cpu, {RETURN})
    assert bytes(memory) == expected
    assert cpu.a[2] == INPUT + 4 * (len(records) + 1) and cpu.a[7] == STACK + 4


def test_empty_reference_list_returns_without_frame_writes(original_image, memory, initialized):
    cpu = prepare(memory, initialized, [])
    before = bytes(memory)
    run(original_image, memory, cpu, {RETURN})
    assert bytes(memory) == before and cpu.a[2] == INPUT + 4 and cpu.a[7] == STACK + 4


def test_shipped_zero_inside_masks_do_not_cover_the_requested_pixels(original_image, memory):
    cpu = prepare(memory, None, [(-1, 0, [(4, 6)])])
    word(memory, 0x1002, 0)
    assert get(memory, MASK32 + (4 * 16 + 6) * 4) == 0
    before = bytes(memory)
    run(original_image, memory, cpu, {RETURN})
    assert bytes(memory) == before


def test_actual_cycle_interpolate_and_interleaved_draw_pipeline(original_image, memory, initialized):
    from tests.test_starglider2_span_interpolation import prepare as prepare_geometry, polygon_pairs, CONTOURS
    ctypes.memmove(ctypes.addressof(memory), initialized, len(initialized))
    memory[FB - 16:FB + 0x8010] = b'\xA5' * 0x8020
    put(memory, SNAPSHOT, FB)
    memory[MODE] = 0
    packets = [CONTOURS[2], CONTOURS[0]]
    fraction, records = 65535, []
    for i, points in enumerate(packets):
        pairs, fraction = polygon_pairs(memory, points, fraction)
        records.append((7 + i, min(y for x, y in points), pairs))
    cpu = prepare_geometry(memory, packets)
    expected = expected_memory(memory, records)
    run(original_image, memory, cpu, {RETURN})
    assert bytes(memory[FB - 16:FB + 0x8010]) == expected[FB - 16:FB + 0x8010]
    assert get(memory, INPUT) == 0x41848 and get(memory, INPUT + 4) > 0x41848
    assert cpu.a[2] == INPUT + 12 and cpu.a[7] == STACK + 4


def test_nonnegative_initializer_preserves_prior_rows_and_unwritten_mask_tail(original_image, memory, amiga_initialized):
    ctypes.memmove(ctypes.addressof(memory), amiga_initialized, len(amiga_initialized))
    word(memory, 0x1002, 0)
    expected = bytearray(memory)
    expected[MASK32:MASK32 + 1024] = inside_masks()
    cpu = state(memory, 0x3E96E)
    run(original_image, memory, cpu, {RETURN}, limit=50000)
    assert bytes(memory) == expected
    assert all(get(memory, ROWS + 2 * y, 2) == 40 * y for y in range(200))


def test_first_row_lookup_then_fixed_160_byte_advance(original_image, memory, initialized):
    records = [(5, 3, [(0, 5), (8, 12)])]
    cpu = prepare(memory, initialized, records)
    word(memory, ROWS + 6, 200)
    word(memory, ROWS + 8, 900)
    expected = expected_memory(memory, records)
    run(original_image, memory, cpu, {RETURN})
    assert bytes(memory) == expected


@pytest.mark.parametrize('style', [16, 16383, 16384, 32767])
def test_regular_nonnegative_selector_remains_unclamped(original_image, memory, initialized, style):
    cpu = prepare(memory, initialized, [(style, 0, [(0, 1)])])
    run(original_image, memory, cpu, {0x3F0C6})
    assert cpu.d[2] & 65535 == (2 * style) & 65535


def test_endpoint_order_uses_signed_comparison_before_masks(original_image, memory, initialized):
    cpu = prepare(memory, initialized, [(2, 0, [(0, 65535)])])
    run(original_image, memory, cpu, {0x3F0EC})
    assert cpu.d[2] & 65535 == 65535 and cpu.d[3] & 65535 == 0


@pytest.mark.parametrize('mode', [2, 255])
def test_other_graphics_mode_is_only_qualified_through_its_gate(original_image, memory, initialized, mode):
    cpu = prepare(memory, initialized, [(3, 0, [(0, 1)])])
    memory[MODE] = mode
    before = bytes(memory)
    run(original_image, memory, cpu, {0x41394})
    assert bytes(memory) == before and cpu.a[2] == INPUT and not any(cpu.c)
