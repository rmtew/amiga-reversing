"""Original shared message FIFO and ticker contracts; controlled RAM/font inputs."""
from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_render_order import sequencer

APP, HEAD, LIMIT, TAIL, CONTEXT = 0x39FC, 0x232, 0x272, 0x276, 0x2A6
TEXT, NEXT, FONT = 0x80000, 0x81000, 0x85000


def initialize(cpu_fixture, slots, count=0):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6], cpu.sr = APP, 0x2000
    memory[APP+HEAD:APP+LIMIT+4] = bytes(68)
    write(APP+TAIL, APP+HEAD+4*count)
    write(APP+slots['app_ui_flags'], 0, 1)
    write(APP+CONTEXT, 0, 1)
    write(APP+slots['app_scrolling_message_timer'], 0, 2)
    write(APP+slots['app_message_palette_flash_countdown'], 0, 1)
    return cpu, memory, read, write, run


def test_both_dequeues_shift_all_16_slots_and_have_no_empty_tail_guard(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    for source in (0x2C0A, 0x9A2E):
        for count in (0, 1, 16):
            initialize(cpu_fixture, title_slots, count)
            values = [TEXT+16*i if i < count else 0 for i in range(16)]+[0]
            for i, pointer in enumerate(values): write(APP+HEAD+4*i, pointer)
            memory[APP+HEAD-4:APP+HEAD] = b'GUAR'
            run(source)
            assert [read(APP+HEAD+4*i) for i in range(16)] == values[1:]
            assert read(APP+LIMIT) == 0 and read(APP+TAIL) == APP+HEAD+4*(count-1)
            assert memory[APP+HEAD-4:APP+HEAD] == b'GUAR'
            assert bool(cpu.sr & 4) == (count <= 1)


def test_scrolling_enqueue_bounds_flash_gate_and_forced_sr_discard_failure_carry(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    memory[TEXT:TEXT+2] = b'A\0'
    for count, pointer, status, ui, accepted in [
        (0, TEXT, 32, 0, False), (0, 0, 0, 0, False), (16, TEXT, 0, 0, False),
        (0, TEXT, 0, 0, True), (15, TEXT, 0, 64, True)]:
        initialize(cpu_fixture, title_slots, count)
        write(APP+CONTEXT, status, 1); write(APP+title_slots['app_ui_flags'], ui, 1)
        write(APP+title_slots['app_message_palette_flash_countdown'], 7, 1)
        before = bytes(memory[APP+HEAD:APP+LIMIT+4])
        cpu.a[0], cpu.sr = pointer, 0x2511
        run(0x2BC8)
        assert cpu.sr == 0x2000  # Even rejection's CCR=1 is overwritten.
        assert read(APP+TAIL) == APP+HEAD+4*(count+bool(accepted))
        if accepted:
            assert read(APP+HEAD+4*count) == pointer
            assert read(APP+HEAD+4*(count+1)) == 0
            assert read(APP+title_slots['app_ui_flags'], 1) == ui | 64
            assert read(APP+title_slots['app_message_palette_flash_countdown'], 1) == (7 if ui & 64 else 20)
        else:
            assert memory[APP+HEAD:APP+LIMIT+4] == before
            assert read(APP+title_slots['app_ui_flags'], 1) == ui
            assert read(APP+title_slots['app_message_palette_flash_countdown'], 1) == 7


def test_status_enqueue_changes_shared_duration_even_when_full_and_word_math_wraps(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    duration = APP+title_slots['app_status_message_service_ticks_remaining']
    for text, units in [(b'\0', 0), (b'   \0', 1), (b'a b c\0', 3),
                        (b'  ab  cd   \0', 4), (b'ab\rcd ef\0', 1), (b'a b\rc d\0', 2)]:
        for count in (1, 16):
            initialize(cpu_fixture, title_slots, count)
            memory[TEXT:TEXT+len(text)] = text
            write(APP+HEAD, NEXT); write(APP+CONTEXT, 32, 1)
            write(duration, 999, 2)
            before = bytes(memory[APP+HEAD:APP+LIMIT+4])
            cpu.a[0] = TEXT
            run(0x99DE, budget=1024)
            assert read(duration, 2) == units*10
            assert bool(cpu.sr & 1) == (count == 16)
            assert read(APP+HEAD) == NEXT
            assert read(APP+CONTEXT, 1) == 32
            if count == 16:
                assert memory[APP+HEAD:APP+LIMIT+4] == before
            else:
                assert read(APP+HEAD+4) == TEXT and read(APP+HEAD+8) == 0
    initialize(cpu_fixture, title_slots, 16)
    text = b'a '*6553+b'\0'
    memory[TEXT:TEXT+len(text)] = text
    write(APP+CONTEXT, 32, 1); cpu.a[0] = TEXT
    advance = sequencer(cpu, memory, write)
    assert advance(0x99DE, budget=200000).stop_reason == 1
    assert read(duration, 2) == ((6553+1)*10) & 65535 == 4
    assert cpu.sr & 1 and cpu.a[0] == TEXT


def test_status_service_underflow_empty_expiry_and_next_message_prefix(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    duration = APP+title_slots['app_status_message_service_ticks_remaining']
    for active, initial in [(False, 0), (False, 2), (True, 0), (True, 2)]:
        initialize(cpu_fixture, title_slots, 1)
        write(APP+HEAD, TEXT); write(APP+CONTEXT, 0x83 | (32 if active else 0), 1)
        write(duration, initial, 2)
        for i in range(4): cpu.a[i] = 0xABCD0000+i
        cpu.d[0], cpu.d[1] = 0x12345678, 0xAABBCCDD
        before_a, before_d = list(cpu.a)[:4], list(cpu.d)[:2]
        run(0x9A48)
        assert read(duration, 2) == ((initial-1) & 65535 if active else initial)
        assert list(cpu.a)[:4] == before_a and list(cpu.d)[:2] == before_d
        assert read(APP+HEAD) == TEXT and read(APP+TAIL) == APP+HEAD+4
    initialize(cpu_fixture, title_slots, 1)
    write(APP+HEAD, TEXT); write(APP+CONTEXT, 0xA3, 1); write(duration, 1, 2)
    memory[0x777FC:0x77D04] = bytes([0xC7])*1288
    run(0x9A48, budget=1024)
    assert read(APP+CONTEXT, 1) == 0x83 and read(APP+TAIL) == APP+HEAD
    assert memory[0x77800:0x77D00] == bytes(1280)
    assert memory[0x777FC:0x77800] == bytes([0xC7])*4 and memory[0x77D00:0x77D04] == bytes([0xC7])*4
    assert cpu.sr & 1
    initialize(cpu_fixture, title_slots, 2)
    write(APP+HEAD, TEXT); write(APP+HEAD+4, NEXT); write(APP+CONTEXT, 32, 1)
    memory[NEXT:NEXT+4] = b'a b\0'; write(duration, 1, 2)
    run(0x9A48, stop=0x9A7A, budget=1024)
    assert read(APP+HEAD) == NEXT and read(APP+TAIL) == APP+HEAD+4
    assert read(duration, 2) == 20 and cpu.a[3] == NEXT


def test_inactive_ticker_still_services_timer_and_flash_but_leaves_band_untouched(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    for timer in (0, 1, 2, 65535):
        for flash in (0, 1, 2, 4, 5, 20, 255):
            initialize(cpu_fixture, title_slots)
            write(APP+title_slots['app_scrolling_message_timer'], timer, 2)
            write(APP+title_slots['app_message_palette_flash_countdown'], flash, 1)
            write(APP+title_slots['app_ticker_highlight_rgb12'], 0x123, 2)
            before = bytes(memory[0x77800:0x77D00])
            run(0x2C24)
            remaining = max(flash-1, 0)
            expected_color = 0x123 if not flash else (0xF55 if remaining & 4 else 0xFFF)
            assert read(APP+title_slots['app_scrolling_message_timer'], 2) == max(timer-1, 0)
            assert read(APP+title_slots['app_message_palette_flash_countdown'], 1) == remaining
            assert read(APP+title_slots['app_ticker_highlight_rgb12'], 2) == expected_color
            assert memory[0x77800:0x77D00] == before and cpu.sr & 1


def test_ticker_all_byte_indices_seven_row_writes_and_live_queue_cursor(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    for glyph in range(256):
        for row in range(8): write(FONT+8*glyph+row, (17*glyph+row) & 255, 1)
    original = bytes((7*i+11) & 255 for i in range(1288))
    for code in range(256):
        initialize(cpu_fixture, title_slots, 1)
        write(APP+HEAD, TEXT); write(APP+title_slots['app_ui_flags'], 64, 1)
        write(APP+title_slots['app_font_glyph_bitmap_table_ptr'], FONT)
        memory[TEXT:TEXT+2] = bytes([code, 0])
        memory[0x777FC:0x77D04] = original
        expected = bytearray(original)
        glyph = code if code < 97 else code & ~32
        for row in range(7):
            index = 0x778A0+160*row-0x777FC
            expected[index:index+39] = original[index+1:index+40]
            expected[index+39] = (17*glyph+row+1) & 255
        run(0x2C24, budget=1024)
        assert memory[0x777FC:0x77D04] == expected
        assert read(APP+HEAD) == 0 and read(APP+TAIL) == APP+HEAD
        assert not read(APP+title_slots['app_ui_flags'], 1) & 64 and cpu.sr & 1
    initialize(cpu_fixture, title_slots, 2)
    memory[TEXT:TEXT+3], memory[NEXT:NEXT+2] = b'Aa\0', b'B\0'
    write(APP+HEAD, TEXT); write(APP+HEAD+4, NEXT)
    write(APP+title_slots['app_ui_flags'], 64, 1)
    write(APP+title_slots['app_font_glyph_bitmap_table_ptr'], FONT)
    run(0x2C24, budget=1024)
    assert read(APP+HEAD) == TEXT+1 and not cpu.sr & 1
    run(0x2C24, budget=1024)
    assert read(APP+HEAD) == NEXT and not cpu.sr & 1
    run(0x2C24, budget=1024)
    assert read(APP+HEAD) == 0 and cpu.sr & 1
