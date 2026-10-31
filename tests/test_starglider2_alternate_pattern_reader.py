"""Original alternate reader, supplied finite spans and retained row table.

These CPU cases establish neither production queue bounds/lifetime nor full
alternate startup, palette colours, device timing or normal-game reachability.
"""
import pytest

from tests.test_starglider2_text_editor import original_image, memory, run, get, put, FB, INPUT, STACK, RETURN
from tests.test_starglider2_interleaved_reader_context import prepare, ROWS, word

PATTERNS = 0x415BE


def setup(memory, records):
    cpu = prepare(memory, None, records)
    memory[0x416A5] = 2
    return cpu


def expected(memory, records):
    result = bytearray(memory)
    for style, y, spans in records:
        index = ((-style) & 15) if style < 0 else style
        offset = ((index << 3) & 65535)
        offset = offset - 65536 if offset & 32768 else offset
        patterns = [get(memory, PATTERNS + offset + 4 * bank) for bank in range(2)]
        row_offset = get(memory, ROWS + 2 * y, 2)
        row_offset = row_offset - 65536 if row_offset & 32768 else row_offset
        for row, (left, right) in enumerate(spans):
            for x in range(min(left, right), max(left, right) + 1):
                shift = 30 - 2 * (x % 16)
                for bank, pattern in enumerate(patterns):
                    address = FB + row_offset + row * 160 + bank * 80 + 4 * (x // 16)
                    value = int.from_bytes(result[address:address + 4], 'big')
                    value = (value & ~(3 << shift)) | (pattern & (3 << shift))
                    result[address:address + 4] = value.to_bytes(4, 'big')
    # Every original completion path writes this fixed four-row sample block.
    for row, pattern in enumerate([0x33333333, 0x22222222, 0, 0x55555555]):
        for column in [0, 4]:
            address = FB + 0x700C + row * 80 + column
            result[address:address + 4] = pattern.to_bytes(4, 'big')
    return result


@pytest.mark.parametrize('style', list(range(16)) + [-v for v in range(1, 33)] + [-32768])
@pytest.mark.parametrize('span', [(0, 0), (0, 15), (15, 16), (5, 69), (0, 319), (319, 319), (127, 63)])
def test_pattern_pairs_and_masked_boundaries(original_image, memory, style, span):
    records = [(style, 1, [span, span[::-1], (3, 37)])]
    cpu = setup(memory, records)
    result = expected(memory, records)
    run(original_image, memory, cpu, {RETURN})
    assert bytes(memory) == result
    assert cpu.a[2] == INPUT + 8 and cpu.a[7] == STACK + 4


@pytest.mark.parametrize('records', [[], [(3, 1, [])], [(2, 3, [(1, 1)]), (-17, 7, []), (-32768, 5, [(31, 64)])]])
def test_all_completion_paths_write_the_fixed_sample_block(original_image, memory, records):
    cpu = setup(memory, records)
    result = expected(memory, records)
    run(original_image, memory, cpu, {RETURN})
    assert bytes(memory) == result
    assert cpu.a[2] == INPUT + 4 * (len(records) + 1)


def test_uses_retained_first_row_then_constant_stride_without_generated_masks(original_image, memory):
    records = [(7, 3, [(2, 25), (4, 17)])]
    cpu = setup(memory, records)
    word(memory, ROWS + 6, 200)
    word(memory, ROWS + 8, 900)
    # Shared generated masks are not consulted by this reader.
    memory[0x3FFBA:0x411BA] = b'\x63' * 0x1200
    result = expected(memory, records)
    run(original_image, memory, cpu, {RETURN})
    assert bytes(memory) == result


@pytest.mark.parametrize('style', [16, 4095, 4096, 8191, 8192, 32767])
def test_nonnegative_selector_shift_wraps_without_clamping(original_image, memory, style):
    cpu = setup(memory, [(style, 0, [(0, 0)])])
    run(original_image, memory, cpu, {0x413B2})
    assert cpu.d[0] & 65535 == (style * 8) & 65535


def test_signed_endpoint_order_is_retained(original_image, memory):
    cpu = setup(memory, [(3, 0, [(0, 65535)])])
    run(original_image, memory, cpu, {0x413D6})
    assert cpu.d[2] & 65535 == 65535 and cpu.d[3] & 65535 == 0


def test_prefix_mask_table_is_sixteen_two_bit_pixel_masks(original_image, memory):
    assert [get(memory, 0x4146E + 4 * i) for i in range(16)] == [
        (0xFFFFFFFF << (32 - 2 * i)) & 0xFFFFFFFF for i in range(16)]


def test_supplied_pattern_pair_changes_each_bank_independently(original_image, memory):
    records = [(5, 2, [(3, 41)])]
    cpu = setup(memory, records)
    put(memory, PATTERNS + 5 * 8, 0x12345678)
    put(memory, PATTERNS + 5 * 8 + 4, 0x9ABCDEF0)
    result = expected(memory, records)
    run(original_image, memory, cpu, {RETURN})
    assert bytes(memory) == result
