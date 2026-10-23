"""Original input routines with controlled MMIO shadows; no CIA/IRQ timing claim."""
import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_render_order import sequencer

APP = 0x39FC
KEYS = 0x397C
CUSTOM = 0xDFF000


@pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
def test_every_serial_key_press_release_and_absent_ports_input(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    last = APP+title_slots['app_last_pressed_raw_key']
    for decoded in range(256):
        wire = (~decoded) & 255
        wire = ((wire << 1) | (wire >> 7)) & 255
        memory[KEYS-1:KEYS+129] = bytes([0xC7])*130
        write(last, 0xA5, 1)
        write(0xBFEC01, wire, 1)
        write(CUSTOM+0x1E, 8, 2)
        cpu.a[5], cpu.a[6] = CUSTOM, APP
        run(0x858, stop=0x886)
        expected = bytearray([0xC7])*130
        expected[1+(decoded & 127)] = 0 if decoded & 128 else 255
        assert memory[KEYS-1:KEYS+129] == expected
        assert read(last, 1) == (0xA5 if decoded & 128 else decoded)
        assert cpu.a[0] == 0xBFE001 and cpu.a[1] == KEYS
    # Stop before the original acknowledgement: absent PORTS does not initialize
    # A0. This intentionally does not claim the following CIA write is safe.
    cpu.a[0] = 0x7654
    write(CUSTOM+0x1E, 0, 2)
    before = bytes(memory[KEYS:APP+0x100])
    run(0x858, stop=0x886)
    assert cpu.a[0] == 0x7654 and memory[KEYS:APP+0x100] == before


@pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
def test_all_joystick_combinations_and_fire_preserve_opposed_bits(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = APP
    for mask in range(16):
        up, down, left, right = [bool(mask & (1 << i)) for i in range(4)]
        joy = (right << 1) | (left << 9) | ((down ^ right) << 0) | ((up ^ left) << 8)
        for fire in (False, True):
            write(CUSTOM+0xC, joy, 2)
            write(0xBFE001, 0x7F if fire else 0xFF, 1)
            run(0x7F0)
            assert read(APP+title_slots['app_input_direction_mask'], 2) == mask
            assert read(APP+title_slots['app_input_x_step'], 2) == ((-1 if left else 1 if right else 0) & 65535)
            assert read(APP+title_slots['app_input_y_step'], 2) == ((-1 if up else 1 if down else 0) & 65535)
            assert read(APP+title_slots['app_input_fire_pressed_ff'], 1) == (255 if fire else 0)
            assert bool(cpu.sr & 4) == (mask == 0)
            assert cpu.a[5] == CUSTOM


def test_pause_bypass_and_release_press_release_sequence(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    flags = APP+title_slots['app_ui_flags']
    cpu.a[6] = APP
    for value, key in [(0xA1, 255), (0xA0, 0)]:
        write(flags, value, 1); write(KEYS+80, key, 1)
        run(0x2D2A)
        assert read(flags, 1) == value
    write(flags, 0x20, 1); write(KEYS+80, 255, 1)
    advance = sequencer(cpu, memory, write)
    assert advance(0x2D2A, stop=0x2D46).stop_reason == 1
    assert read(flags, 1) == 0xA0 and cpu.a[0] == KEYS+80
    assert advance(stop=0x2D4A, budget=8).stop_reason == 3
    write(KEYS+80, 0, 1)
    assert advance(stop=0x2D4A).stop_reason == 1
    assert advance(stop=0x2D4E, budget=8).stop_reason == 3
    write(KEYS+80, 255, 1)
    assert advance(stop=0x2D4E).stop_reason == 1
    assert advance(budget=8).stop_reason == 3
    write(KEYS+80, 0, 1)
    assert advance().stop_reason == 1
    assert read(flags, 1) == 0x20 and cpu.a[0] == KEYS+80 and cpu.a[7] == 0x9004


def test_inventory_key_gates_retain_latch_until_eligible_release(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    flags = APP+title_slots['app_ui_flags']
    player_flags = BASE+0x4C322+schemas['world_object_shared_prefix']['world_object_flags']
    cpu.a[6] = APP
    for obj, ui, key, expected in [(2, 8, 0, 8), (0, 9, 0, 9), (0, 10, 0, 10), (0, 8, 0, 0), (0, 8, 255, 8), (0, 0x88, 0, 0x80)]:
        write(player_flags, obj, 1); write(flags, ui, 1); write(KEYS+64, key, 1)
        run(0x26EC)
        assert read(flags, 1) == expected
    write(player_flags, 0, 1); write(flags, 0, 1); write(KEYS+64, 255, 1)
    run(0x26EC, stop=0x2720)
    assert read(flags, 1) == 8 and cpu.d[0] & 65535 == 0x311


def test_cold_workspace_and_restart_key_clear_have_distinct_exact_fences(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    memory[KEYS-1:APP+877] = bytes([0xC7])*(128+878)
    run(0x46A, stop=0x47A, budget=3000)
    assert memory[KEYS-1:APP] == bytes([0xC7])*129
    assert memory[APP:APP+876] == bytes(876) and memory[APP+876] == 0xC7
    write(APP, 0xA5, 1)
    run(0x9F58, stop=0x9F66)
    assert memory[KEYS:APP] == bytes(128)
    assert memory[KEYS-1] == 0xC7 and memory[APP] == 0xA5
    assert cpu.a[0] == APP and cpu.d[7] & 65535 == 65535


@pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
def test_warm_restart_waits_for_blitter_then_joins_shared_setup(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    write(CUSTOM+2, 0x4000, 2)
    advance = sequencer(cpu, memory, write)
    assert advance(0x456, stop=0x464, budget=32).stop_reason == 3
    assert cpu.a[5] == CUSTOM+2
    write(CUSTOM+2, 0, 2)
    assert advance(stop=0x498).stop_reason == 1
    assert cpu.sr == 0x2700


def test_all_three_restart_consumers_and_main_shortcut_inhibit(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = APP
    for source, continuation in [(0x690, 0x6A2), (0x9062, 0x9074), (0x9C76, 0x9C88)]:
        for held in (0, 255):
            write(KEYS+86, held, 1)
            run(source, stop=0x456 if held else continuation)
            assert cpu.a[0] == KEYS
    write(APP+title_slots['app_status_flags'], 16, 1)
    write(KEYS+86, 255, 1)
    run(0x688, stop=0x6D2)
    # Status bit 4 prevents the main loop from even reading its restart key.


def test_main_camera_keys_prioritize_profile_zero_and_skip_unchanged_profile(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = APP
    profile = APP+title_slots['app_camera_scroll_profile_index']
    write(KEYS+86, 0, 1)
    for key0, key1, before, after, stop in [
        (255, 255, 0, 0, 0x6D2), (255, 255, 1, 0, 0x6B2),
        (0, 255, 0, 1, 0x6CC), (0, 255, 1, 1, 0x6D2),
        (0, 0, 1, 1, 0x6D2)]:
        write(KEYS+11, key0, 1); write(KEYS+12, key1, 1); write(profile, before, 2)
        run(0x690, stop=stop)
        assert read(profile, 2) == after
    # Stops precede the configuration calls; no camera callback closure claim.
