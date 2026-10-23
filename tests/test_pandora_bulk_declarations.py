"""Bounded original consumers and stored text, without allocation/activation claims."""
from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_render_order import sequencer


TEXT_SPANS = [
    (0x2B9A, 0x2BC4, 'blank_scrolling_message_text', b' ' * 41 + b'\0'),
    (0x2EE0, 0x2EE5, 'four_digit_formatted_text', b'9999\0'),
    (0x8D07, 0x8D28, 'retained_terminal_blank_text', b' ' * 32 + b'\0'),
    (0x7176, 0x7182, 'retained_gunfire_data_filename', b'gunfire.dat\0'),
    (0xAAF5, 0xAAF9, 'hit_feedback_overlay_title_text', b'HIT\0'),
    (0xAAF9, 0xAAFE, 'opponent_health_overlay_title_text', b'ENMY\0'),
]


def test_original_complete_text_bounds_and_overlay_title_links(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    for lo, hi, name, expected in TEXT_SPANS:
        actual = bytes(memory[BASE + lo:BASE + hi])
        assert actual == expected and actual[-1] == 0 and 0 not in actual[:-1], name
    assert read(BASE + 0x3362) == BASE + 0xAAF5
    assert read(BASE + 0x330A) == BASE + 0xAAF9
    # The formatter's second trailing zero is outside the proven five-byte text.
    assert memory[BASE + 0x2EE5] == 0
    run(0x2BC4, stop=0x2BC8)
    assert cpu.a[0] == BASE + 0x2B9A


def test_original_retained_nonzero_offer_prefixes_scan_four_records(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    for base, item in [(0xB350, 45), (0xB380, 39)]:
        first = bytes(memory[BASE + base:BASE + base + 8])
        assert first == bytes([item, 20, 0, 0, 0, 0, 0, 0])
        assert first == bytes(memory[BASE + base + 8:BASE + base + 16])
        for root in [base, base + 8]:
            cpu.a[2], cpu.d[0], cpu.d[7] = BASE + root, item, 3
            run(0x7C2A, stop=0x7C36)
            assert cpu.a[2] == BASE + root
            cpu.a[5] = 0x81000
            write(0x81000 + schemas['world_object_shared_prefix']['item_state'], 21, 1)
            run(0x7C36, stop=0x7C3E)
            assert cpu.d[0] & 255 == 20
            cpu.a[2], cpu.d[0], cpu.d[7] = BASE + root, 2, 3
            run(0x7C2A, stop=0x7C34)
            assert cpu.a[2] == BASE + root + 8
        assert memory[BASE + base:BASE + base + 16] == first * 2


def test_original_seven_weapon_pairs_and_fallback_cover_all_item_bytes(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[5] = 0x81000
    reloads, damages = bytes([4, 5, 2, 1, 4, 3, 2]), bytes([35, 21, 9, 7, 25, 14, 8])
    assert memory[BASE + 0x8670:BASE + 0x8677] == reloads
    assert memory[BASE + 0x8677:BASE + 0x867E] == damages
    for item in range(256):
        write(cpu.a[5] + schemas['world_object_shared_prefix']['selected_item_id'], item, 1)
        cpu.d[0], cpu.d[1] = 0x12345678, 0xABCD9876
        run(0x864C)
        if 7 <= item <= 13:
            assert (cpu.d[0], cpu.d[1]) == (0x12340000 | reloads[item - 7], 0xABCD0000 | damages[item - 7])
            assert cpu.sr & 1
        else:
            assert (cpu.d[0], cpu.d[1]) == (3, 5) and not cpu.sr & 1


def test_original_workspace_clear_stops_before_coordinate_discontinuity(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    start, end, grid = 0x39FC, 0x3D68, 0x4000
    memory[start - 4:grid + 4] = bytes([0xA5]) * (grid - start + 8)
    trace = sequencer(cpu, memory, write)(0x46A, stop=0x47A, budget=2048)
    assert trace.stop_reason == 1 and cpu.a[0] == end
    assert memory[start:end] == bytes(0x36C)
    assert memory[start - 4:start] == memory[grid:grid + 4] == bytes([0xA5]) * 4
    assert memory[end:grid] == bytes([0xA5]) * 664
    # This is a write bound, not proof of app allocation or unused gap storage.
