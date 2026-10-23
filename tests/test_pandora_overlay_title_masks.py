"""Original five-row title masks and packed four-plane border cells."""
from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_title_data import APP, title_slots
from tests.test_pandora_render_order import sequencer

FONT = 0xAF9E
TITLE_POINTER_FIELDS = tuple(0x32B2 + 44 * i for i in range(10))
BORDER_CELLS = tuple(0xB020 + 32 * i for i in range(6))


def punch_title(cpu_fixture, title_slots, text, source=0x8000):
    cpu, memory, schemas, read, write, run = cpu_fixture
    destination = 0x80000
    before = bytes((0xA5 ^ i) & 255 for i in range(1280))
    memory[destination:destination + len(before)] = before
    memory[source:source + len(text) + 1] = text + b'\0'
    write(APP + title_slots['app_text_cursor_ptr'], destination)
    cpu.a[0], cpu.a[6] = source, APP
    expected = bytearray(before)
    for column, char in enumerate(text):
        index = (char - ord('A')) & 255  # original BYTE subtraction wraps
        glyph = bytes(memory[BASE + FONT + 5 * index:BASE + FONT + 5 * index + 5])
        for row, mask in enumerate(glyph):
            for plane in range(4):
                expected[320 + (4 * row + plane) * 40 + column] &= mask
    trace = sequencer(cpu, memory, write)(0x62A8, budget=4096)
    assert trace.stop_reason == 1
    assert bytes(memory[destination:destination + len(before)]) == expected
    assert cpu.a[0] == source + len(text) + 1
    assert cpu.a[1] == read(APP + title_slots['app_text_cursor_ptr']) == destination + 320 + len(text)
    assert cpu.a[7] == 0x9004
    if text:
        assert cpu.a[2] == BASE + FONT + 5 * (((text[-1] - 65) & 255) + 1)
    # The trace's bounded write summary is not assumed to cover every row.


def test_all_26_masks_and_ten_initialized_overlay_titles(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    resources = bytes(memory[BASE + FONT:BASE + 0xB0E0])
    assert all(mask & 1 for mask in resources[:130])  # seven active columns
    for char in range(ord('A'), ord('Z') + 1):
        punch_title(cpu_fixture, title_slots, bytes([char]))
    for field in TITLE_POINTER_FIELDS:
        source = read(BASE + field)
        end = memory.index(0, source)
        text = bytes(memory[source:end])
        assert text and all(ord('A') <= char <= ord('Z') for char in text)
        punch_title(cpu_fixture, title_slots, text, source)
    assert bytes(memory[BASE + FONT:BASE + 0xB0E0]) == resources


def test_empty_title_and_unchecked_byte_indices(cpu_fixture, title_slots):
    punch_title(cpu_fixture, title_slots, b'')
    # Invalid input still reads outside the 26-glyph owner; it is not clipped.
    for char in [1, ord('@'), ord('['), 255]:
        punch_title(cpu_fixture, title_slots, bytes([char]))


def test_all_six_border_cells_copy_32_packed_rows_and_preserve_inputs(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    destination = 0x80000
    for source in BORDER_CELLS:
        before = bytes([0xA5]) * 1280
        memory[destination:destination + 1280] = before
        expected = bytearray(before)
        cell = bytes(memory[BASE + source:BASE + source + 32])
        for packed_row, value in enumerate(cell):
            expected[40 * packed_row] = value
        write(APP + title_slots['app_text_cursor_ptr'], destination)
        cpu.a[0], cpu.a[1], cpu.a[6], cpu.d[0] = BASE + source, 0x87654321, APP, 0x12345678
        advance = sequencer(cpu, memory, write)
        before_d, before_a = list(cpu.d), list(cpu.a[:7])
        assert advance(0x620E, budget=512).stop_reason == 1
        assert bytes(memory[destination:destination + 1280]) == expected
        assert list(cpu.d) == before_d and list(cpu.a[:7]) == before_a
        assert read(APP + title_slots['app_text_cursor_ptr']) == destination
        assert cpu.a[7] == 0x9004
