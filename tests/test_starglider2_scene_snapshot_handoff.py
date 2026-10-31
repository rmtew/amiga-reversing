"""Original display setup/rotation to scene snapshot and finite HUD drawing.

Device addresses are anonymous RAM. These are CPU handoffs, not physical
scanout, normal startup, sequence capacity, phase exclusion or lifetime proofs.
"""
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_text_editor import original_image, state, run, put, get, APP, FB, INPUT, STACK, RETURN
from tests.test_starglider2_alternate_palette_interrupt import sparse_memory
from tests.test_starglider2_scene_packets import polygon

FIELDS = ['draw_buffer_base', 'display_buffer_base', 'frame_handoff_counter',
          'vblank_tick_counter', 'drawing_fill_style_word', 'view_clip_min_x',
          'view_clip_max_x', 'view_clip_min_y', 'view_clip_max_y',
          'projection_screen_origin_x', 'projection_screen_origin_y',
          'reticle_neutral_screen_x', 'reticle_neutral_screen_y',
          'active_model_scale_shift', 'pending_message_count',
          'message_display_countdown', 'mouse_input_scale_shift',
          'alternate_graphics_mode', 'player_rotation_2', 'display_buffer_table_byte_offset']


@pytest.fixture(scope='module')
def slots(tmp_path_factory):
    target = Path(__file__).resolve().parents[1] / 'targets/amiga_raw_starglider2_game'
    temp = tmp_path_factory.mktemp('snapshot-fields')
    asm, out = temp / 'fields.s', temp / 'fields.bin'
    asm.write_text((target / 'starglider2_game.s').read_text().split('    SECTION code,code', 1)[0]
                   + '\n SECTION constants,data\n dc.l ' + ','.join(FIELDS) + '\n')
    result = subprocess.run([str(target.parents[1] / 'tools/vasmm68k_mot.exe'), '-quiet', '-Fbin', '-no-opt',
                             '-I' + str(target / 'includes'), '-o', str(out), str(asm)],
                            cwd=target, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    return dict(zip(FIELDS, struct.unpack('>' + str(len(FIELDS)) + 'I', out.read_bytes())))


def common_defaults(expected, slots):
    values = dict(frame_handoff_counter=0, vblank_tick_counter=0, drawing_fill_style_word=1,
                  view_clip_min_x=16, view_clip_max_x=303, view_clip_min_y=30, view_clip_max_y=128,
                  projection_screen_origin_x=159, projection_screen_origin_y=79,
                  reticle_neutral_screen_x=160, reticle_neutral_screen_y=79,
                  active_model_scale_shift=7, pending_message_count=0,
                  message_display_countdown=0, mouse_input_scale_shift=4)
    for name, value in values.items():
        put(expected, APP + slots[name], value, 2)
    for off, value in [(0x1B0, 0x1357), (0x198, 143), (0x19A, 79)]:
        put(expected, APP + off, value, 2)
    for name in ['draw_buffer_base', 'display_buffer_base']:
        put(expected, APP + slots[name], 0x77B50)


@pytest.mark.parametrize('flags', [0, 0x7FFF, 0x8000, 0xFFFF])
def test_common_initializer_aliases_bases_and_retains_mode_until_profile_setup(original_image, sparse_memory, slots, flags):
    m = sparse_memory
    m[APP:APP + 0x1000] = b'\xA5' * 0x1000
    put(m, 0x1002, flags, 2)
    put(m, 0xDFF180, 0xA55A, 2)
    expected = bytearray(m[APP:APP + 0x1000])
    # Reuse absolute addressing for the independent expected slot writes.
    low = bytearray(APP + 0x1000)
    low[APP:] = expected
    common_defaults(low, slots)
    if flags & 0x8000:
        low[APP + 0x1EF] = 255
    cpu = state(m, 0x3410)
    run(original_image, m, cpu, {RETURN, 0x3C0A})
    assert bytes(m[APP:APP + 0x1000]) == low[APP:]
    assert get(m, 0xDFF180, 2) == (0x555 if flags & 0x8000 else 0xA55A)
    assert cpu.pc == (RETURN if flags & 0x8000 else 0x3C0A)
    assert m[APP + slots['alternate_graphics_mode']] == 0xA5


@pytest.mark.parametrize('alternate', [False, True])
@pytest.mark.parametrize('index', range(0, 256, 2))
def test_rotation_reads_byte_offset_and_wraps_only_at_exact_twelve(original_image, sparse_memory, slots, alternate, index):
    m = sparse_memory
    m[APP + slots['display_buffer_table_byte_offset']] = index
    entry, display, draw = (0x3A8F0, 0x3A92C, 0x3A938) if alternate else (0x38EE, 0x392E, 0x393A)
    expected_display, expected_draw = get(m, display + index), get(m, draw + index)
    high, middle = m[0x3A944 + index], m[0x3A945 + index]
    copper = get(m, 0x3922 + index)
    cpu = state(m, entry)
    cpu.d[0] = 0xA5A5FEDC
    run(original_image, m, cpu, {RETURN})
    next_index = 0 if index + 4 == 12 else index + 4
    assert m[APP + slots['display_buffer_table_byte_offset']] == next_index & 255
    assert get(m, APP + slots['display_buffer_base']) == expected_display
    assert get(m, APP + slots['draw_buffer_base']) == expected_draw
    if alternate:
        assert (m[0xFFFF8201], m[0xFFFF8203]) == (high, middle)
    else:
        assert get(m, 0xDFF080) == copper
    assert cpu.d[0] == (0 if alternate and index == 8 else 0xA5A50000 | next_index)
    assert cpu.a[7] == STACK + 4


@pytest.mark.parametrize('index', [0, 4, 8])
@pytest.mark.parametrize('mode', [0, 1, 2, 3, 128, 255])
def test_original_rotation_to_empty_amiga_scene_still_refreshes_all_snapshots(original_image, sparse_memory, slots, index, mode):
    m = sparse_memory
    m[APP + slots['display_buffer_table_byte_offset']] = index
    run(original_image, m, state(m, 0x38EE), {RETURN})
    m[APP + slots['alternate_graphics_mode']] = mode
    put(m, APP + slots['player_rotation_2'], 0xFEDC, 2)
    put(m, 0x1002, 0x8000, 2)
    m[INPUT:INPUT + 16] = b'\xA7' * 16
    cpu = state(m, 0x3D9DA)
    cpu.a[2], cpu.d[0] = INPUT, 0
    run(original_image, m, cpu, {RETURN})
    assert get(m, 0x416A8) == get(m, 0x393A + index)
    assert m[0x416A5] == mode and get(m, 0x416A6, 2) == 0xEDC
    assert bytes(m[INPUT:INPUT + 16]) == b'\xA7' * 16
    assert cpu.a[6] == APP and cpu.a[7] == STACK + 4


@pytest.mark.parametrize('mode', [0, 2])
@pytest.mark.parametrize('angle', [0x340, 0x341, 0xB40, 0xB41])
def test_setup_prefix_to_full_finite_scene_hud_drawing(original_image, sparse_memory, slots, mode, angle):
    m = sparse_memory
    # Execute existing original setup from its software mode-byte input.
    setup = state(m, 0x3A2F8)
    setup.d[0] = mode
    run(original_image, m, setup, {0x3A450, RETURN}, limit=5000)
    assert m[APP + slots['alternate_graphics_mode']] == (255 if mode else 0)
    # Conversion beyond3A450 is deliberately outside this finite CPU chain.
    put(m, 0x1002, 0, 2)
    put(m, APP + slots['draw_buffer_base'], FB)
    put(m, APP + slots['player_rotation_2'], angle | 0xF000, 2)
    polygon(m, 0x3A0D2, [(20, 40), (60, 40)], style=0)
    m[FB - 16:FB + 0x8010] = b'\xA5' * 0x8020
    expected = bytearray(m[FB - 16:FB + 0x8010])
    inside = 0x340 < angle <= 0xB40
    style = (7 if inside else 3) if mode else (2 if inside else 1)
    for row in range(33 if mode else 34):
        for column in ([0, 80] if mode else [0]):
            start = 16 + (0x5B6C if mode else 0x5B98) + row * 160 + column
            expected[start:start + (8 if mode else 16)] = bytes(8 if mode else 16)
    for x in range(20, 61):
        if mode:
            for bank in range(2):
                value = get(m, 0x415BE + style * 8 + bank * 4)
                offset = 16 + 40 * 160 + bank * 80 + 4 * (x // 16)
                old = int.from_bytes(expected[offset:offset + 4], 'big')
                mask = 3 << (30 - 2 * (x % 16))
                expected[offset:offset + 4] = ((old & ~mask) | (value & mask)).to_bytes(4, 'big')
        else:
            for plane in range(4):
                offset = 16 + 40 * 160 + 8 * (x // 16) + plane * 2
                old = int.from_bytes(expected[offset:offset + 2], 'big')
                bit = 0x8000 >> (x % 16)
                expected[offset:offset + 2] = ((old & ~bit) | (bit if style & (1 << plane) else 0)).to_bytes(2, 'big')
    if mode:
        for row, value in enumerate([0x33333333, 0x22222222, 0, 0x55555555]):
            for column in [0, 4]:
                offset = 16 + 0x700C + row * 80 + column
                expected[offset:offset + 4] = value.to_bytes(4, 'big')
    cpu = state(m, 0x3D9DA)
    cpu.a[2], cpu.d[0] = INPUT, 0
    run(original_image, m, cpu, {RETURN})
    assert bytes(m[FB - 16:FB + 0x8010]) == expected
    assert m[0x416A5] == (255 if mode else 0) and get(m, 0x416A6, 2) == angle
    assert get(m, 0x416A8) == FB and get(m, 0x3A0D4, 2) == style
    assert cpu.a[2] == INPUT + 8 and cpu.a[7] == STACK + 4


@pytest.mark.parametrize('count', [0, 1])
def test_disc_snapshot_writer_does_not_refresh_scene_mode_or_rotation(original_image, sparse_memory, slots, count):
    m = sparse_memory
    put(m, APP + slots['draw_buffer_base'], FB)
    m[0x416A5] = 0x5A
    put(m, 0x416A6, 0x1357, 2)
    put(m, 0x416A8, 0x12345678)
    put(m, INPUT, INPUT + 128)
    cpu = state(m, 0x62C8)
    cpu.a[2], cpu.a[1] = INPUT, INPUT + 4 * count
    run(original_image, m, cpu, {RETURN, 0x6304})
    assert m[0x416A5] == 0x5A and get(m, 0x416A6, 2) == 0x1357
    assert get(m, 0x416A8) == (FB if count else 0x12345678)
