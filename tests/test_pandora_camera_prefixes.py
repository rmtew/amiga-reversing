"""Original camera prefixes and profile/trigger decisions; no renderer/DMA model."""
from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_title_data import title_slots

APP = 0x39FC
PLAYER = BASE+0x4C322


def put(write, slots, name, value, size=2):
    write(APP+slots[name], value & ((1 << (8*size))-1), size)


def get(read, slots, name, size=2):
    return read(APP+slots[name], size)


def test_profiles_use_word_margins_and_low_reload_byte_without_clamping(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = APP
    original = bytes(memory[BASE+0xA146:BASE+0xA152])
    for index, reload, mx, my in [(0, 4, 0, 0), (1, 6, 32, 16)]:
        for x, y in [(0, 0), (976, 1936), (0xFFF0, 0x7FF0)]:
            put(write, title_slots, 'app_camera_scroll_profile_index', index)
            put(write, title_slots, 'app_tilemap_scroll_x', x)
            put(write, title_slots, 'app_tilemap_scroll_y', y)
            run(0xA152)
            assert get(read, title_slots, 'app_camera_scroll_countdown_reload_word') == reload
            assert get(read, title_slots, 'app_configured_camera_scroll_ticks', 1) == reload
            assert [get(read, title_slots, n) for n in [
                'app_camera_scroll_left_trigger', 'app_camera_scroll_right_trigger',
                'app_camera_scroll_top_trigger', 'app_camera_scroll_bottom_trigger']] == [
                    (x+mx) & 65535, (x+320-mx) & 65535, (y+my) & 65535, (y+128-my) & 65535]
            assert cpu.a[0] == BASE+0xA146+6*(index+1)
    assert title_slots['app_configured_camera_scroll_ticks'] == title_slots['app_camera_scroll_countdown_reload_word']+1
    assert memory[BASE+0xA146:BASE+0xA152] == original


def test_begin_uses_reload_low_byte_and_refresh_replaces_both_deltas(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = APP
    for reload in (0x0104, 0xAB06, 0x1200):
        put(write, title_slots, 'app_status_flags', 0xA5, 1)
        put(write, title_slots, 'app_camera_scroll_countdown_reload_word', reload)
        put(write, title_slots, 'app_camera_scroll_delta_x', -16)
        put(write, title_slots, 'app_camera_scroll_delta_y', 16)
        run(0x7D24)
        assert get(read, title_slots, 'app_status_flags', 1) == 0xB5
        assert get(read, title_slots, 'app_camera_scroll_ticks_remaining', 1) == reload & 255
        assert get(read, title_slots, 'app_camera_scroll_delta_x') == 65520
        assert get(read, title_slots, 'app_camera_scroll_delta_y') == 16
        run(0x7D32)
        assert get(read, title_slots, 'app_status_flags', 1) == 0xB5
        assert get(read, title_slots, 'app_camera_scroll_ticks_remaining', 1) == 2
        assert get(read, title_slots, 'app_camera_scroll_delta_x') == 0
        assert get(read, title_slots, 'app_camera_scroll_delta_y') == 0
        assert get(read, title_slots, 'app_camera_scroll_countdown_reload_word') == reload


def test_all_countdown_bytes_move_without_testing_active_flag_and_expire_before_motion(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = APP
    for count in range(256):
        for name, value in [('app_tilemap_scroll_x', 256), ('app_tilemap_scroll_y', 2048),
                            ('app_camera_scroll_delta_x', -16), ('app_camera_scroll_delta_y', 16),
                            ('app_tilemap_height', 129), ('app_tile_column', 0x55AA), ('app_tile_row', 0x55AA)]:
            put(write, title_slots, name, value)
        flags = 0xA0 | (16 if count & 1 else 0)
        put(write, title_slots, 'app_status_flags', flags, 1)
        put(write, title_slots, 'app_camera_scroll_ticks_remaining', count, 1)
        run(0x7D48, stop=0x7D9C)
        expired = count == 1
        assert get(read, title_slots, 'app_camera_scroll_ticks_remaining', 1) == (count-1) & 255
        assert get(read, title_slots, 'app_status_flags', 1) == (flags & ~16 if expired else flags)
        assert get(read, title_slots, 'app_tilemap_scroll_x') == (256 if expired else 240)
        assert get(read, title_slots, 'app_tilemap_scroll_y') == (2048 if expired else 1936)
        assert get(read, title_slots, 'app_tile_column') == (0x55AA if expired else 15)
        assert get(read, title_slots, 'app_tile_row') == (0x55AA if expired else 121)
        assert get(read, title_slots, 'app_camera_scroll_delta_x') == (0 if expired else 65520)
        assert get(read, title_slots, 'app_camera_scroll_delta_y') == (0 if expired else 16)


def test_scroll_y_clamp_and_x_word_wrap_keep_unchecked_height_arithmetic(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = APP
    for height in (7, 8, 16, 129):
        for x, y, dx, dy in [(0, 0, -16, -16), (65520, 65520, 16, 16), (64, 32, 16, -16), (64, 1935, -16, 16)]:
            for name, value in [('app_tilemap_scroll_x', x), ('app_tilemap_scroll_y', y),
                                ('app_camera_scroll_delta_x', dx), ('app_camera_scroll_delta_y', dy),
                                ('app_tilemap_height', height)]:put(write, title_slots, name, value)
            put(write, title_slots, 'app_camera_scroll_ticks_remaining', 2, 1)
            run(0x7D48, stop=0x7D9C)
            maximum = (((height-8) & 65535) << 4) & 65535
            ey = (y+dy) & 65535
            if ey & 0x8000: ey = 0
            ey = min(ey, maximum)
            ex = (x+dx) & 65535
            assert get(read, title_slots, 'app_tilemap_scroll_x') == ex
            assert get(read, title_slots, 'app_tilemap_scroll_y') == ey
            assert get(read, title_slots, 'app_tile_column') == ex >> 4
            assert get(read, title_slots, 'app_tile_row') == ey >> 4


def select(cpu_fixture, slots, profile, direction, x, y, sx=100, sy=200):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6], cpu.a[4] = APP, PLAYER
    for name, value in [('app_camera_scroll_profile_index', profile), ('app_tilemap_scroll_x', sx),
                        ('app_tilemap_scroll_y', sy), ('app_tilemap_width', 90), ('app_tilemap_height', 129),
                        ('app_camera_scroll_delta_x', 0), ('app_camera_scroll_delta_y', 0)]:put(write, slots, name, value)
    put(write, slots, 'app_camera_scroll_ticks_remaining', 0, 1)
    put(write, slots, 'app_status_flags', 0x80, 1)
    run(0xA152)
    obj = schemas['world_object_shared_prefix']
    write(PLAYER+obj['world_x'], x, 2); write(PLAYER+obj['world_y'], y, 2)
    cpu.d[0], cpu.d[1] = direction[0] & 0xFFFFFFFF, direction[1] & 0xFFFFFFFF
    run(0x9844)
    return (get(read, slots, 'app_status_flags', 1) & 16,
            get(read, slots, 'app_camera_scroll_ticks_remaining', 1),
            get(read, slots, 'app_camera_scroll_delta_x'), get(read, slots, 'app_camera_scroll_delta_y'))


def test_axis_trigger_equalities_map_guards_and_vertical_wraps(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    obj = schemas['world_object_shared_prefix']
    for profile, mx, my, reload in [(0, 0, 0, 4), (1, 32, 16, 6)]:
        for direction, x, y, sx, sy, expected in [
            ((-1, 0), 99+mx, 250, 100, 200, (16, reload, 65520, 0)),
            ((-1, 0), 100+mx, 250, 100, 200, (0, 0, 0, 0)),
            ((-1, 0), 46+mx, 250, 47, 200, (0, 0, 0, 0)),
            ((-1, 0), 47+mx, 250, 48, 200, (16, reload, 65520, 0)),
            ((1, 0), 396-mx, 250, 100, 200, (16, reload, 16, 0)),
            ((1, 0), 395-mx, 250, 100, 200, (0, 0, 0, 0)),
            ((1, 0), 1367-mx, 250, 1071, 200, (16, reload, 16, 0)),
            ((1, 0), 1368-mx, 250, 1072, 200, (0, 0, 0, 0)),
            ((0, -1), 250, 199+my, 100, 200, (16, reload, 0, 65520)),
            ((0, -1), 250, 200+my, 100, 200, (0, 0, 0, 0)),
            ((0, 1), 250, 296-my, 100, 200, (16, reload, 0, 16)),
            ((0, 1), 250, 295-my, 100, 200, (0, 0, 0, 0)),
        ]:assert select(cpu_fixture, title_slots, profile, direction, x, y, sx, sy) == expected
        assert select(cpu_fixture, title_slots, profile, (0, -1), 250, 15) == (16, 2, 0, 0)
        assert get(read, title_slots, 'app_tilemap_scroll_y') == 1936
        assert read(PLAYER+obj['world_y'], 2) == 2016
        assert select(cpu_fixture, title_slots, profile, (0, 1), 250, 2016) == (16, 2, 0, 0)
        assert get(read, title_slots, 'app_tilemap_scroll_y') == 0
        assert read(PLAYER+obj['world_y'], 2) == 16


def test_two_profiles_move_reload_minus_one_times_and_wide_profile_can_wrap_x(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    for profile, margin, reload, expected in [(0, 0, 4, 0), (1, 32, 6, 65504)]:
        assert select(cpu_fixture, title_slots, profile, (-1, 0), 47+margin, 250, sx=48) == (16, reload, 65520, 0)
        for _ in range(reload):run(0x7D48, stop=0x7D9C)
        assert get(read, title_slots, 'app_tilemap_scroll_x') == expected
        assert get(read, title_slots, 'app_camera_scroll_ticks_remaining', 1) == 0
        assert not get(read, title_slots, 'app_status_flags', 1) & 16
        assert get(read, title_slots, 'app_camera_scroll_delta_x') == 0
    # These are original service prefixes with controlled entries and no
    # intervening writes. Renderer/DMA behavior and gameplay reachability remain separate.
