"""Original post-picture cockpit re-entry and inventory-HUD reconstruction.

Entry skips picture decode/frame handoff and supplies valid RAM sprite backing.
No whole startup, inventory consistency, pool lifetime or hardware proof follows.
"""
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, FB, INPUT, STACK, RETURN

APP_FIELDS = ['station_construction_steps_remaining', 'carried_neutron_bomb_reference',
              'tractor_target_reference', 'previous_tractor_target_reference',
              'growing_projector_part_reference', 'nearby_space_station_reference',
              'station_report_primary_message', 'station_report_secondary_message',
              'world_object_pool', 'model_type_population_counts', 'neutron_bomb_spawn_request',
              'neutron_bomb_retract_request', 'homing_missile_hud_icon_count',
              'bouncing_bomb_hud_icon_count', 'periodic_display_update_countdown',
              'message_display_countdown', 'pending_message_count', 'modal_command_input_flag']
GLOBALS = ['enable_midframe_copper_blocks_continuation', 'model_header_pointers',
           'amiga_copper_list_a_mode_gate', 'amiga_copper_list_b_mode_gate',
           'amiga_copper_list_c_mode_gate', 'hud_coordinate_bcd_pair_cache',
           'game_over_sequence_countdown', 'carried_neutron_bomb_y_offset',
           'homing_missile_hud_screen_origin', 'bouncing_bomb_hud_screen_origin',
           'hud_sprite_conversion_directory_control_words_9',
           'add_homing_missile_hud_icon', 'add_bouncing_bomb_hud_icon']
REFERENCES = APP_FIELDS[1:8]


@pytest.fixture(scope='module')
def symbols(tmp_path_factory, original_image):
    target = Path(__file__).resolve().parents[1] / 'targets/amiga_raw_starglider2_game'
    temp = tmp_path_factory.mktemp('cockpit-restore-symbols'); asm, out = temp / 'fields.s', temp / 'fields.bin'
    names = APP_FIELDS + GLOBALS
    asm.write_text((target / 'starglider2_game.s').read_text()
                   + '\n dc.l ' + ','.join(names) + '\n')
    result = subprocess.run([str(target.parents[1] / 'tools/vasmm68k_mot.exe'), '-quiet', '-Fbin', '-m68000', '-no-opt',
                             '-I' + str(target / 'includes'), '-o', str(out), str(asm)],
                            cwd=target, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    data = out.read_bytes(); size = 4 * len(names)
    assert data[:-size] == original_image[0]
    values = struct.unpack('>' + str(len(names)) + 'I', data[-size:])
    return {n: v + (APP if n in APP_FIELDS else 0) for n, v in zip(names, values)}


def word(m, p, v): put(m, p, v & 65535, 2)


def prepare(m, symbols, construction=0, bomb_count=0, found=-1, phase=255, homing=0, bouncing=0):
    for n in REFERENCES: put(m, symbols[n], 0xDEADBEEF)
    word(m, symbols['station_construction_steps_remaining'], construction)
    for n in ['periodic_display_update_countdown', 'message_display_countdown', 'pending_message_count']:
        word(m, symbols[n], 0xA5A5)
    m[symbols['modal_command_input_flag']] = 255
    word(m, symbols['hud_coordinate_bcd_pair_cache'], 0xA5A5)
    m[symbols['neutron_bomb_spawn_request']] = 0x12
    m[symbols['neutron_bomb_retract_request']] = 0x34
    put(m, symbols['carried_neutron_bomb_y_offset'], 0xA5B6C7D8)
    pool = symbols['world_object_pool']; m[pool:pool + 250 * 68] = b'\0' * (250 * 68)
    if found >= 0:
        word(m, pool + found * 68, 98); m[pool + found * 68 + 30] = phase
    counts = symbols['model_type_population_counts']
    m[counts + 98], m[counts + 12], m[counts + 91] = bomb_count, homing, bouncing
    word(m, symbols['homing_missile_hud_icon_count'], 0xA5A5)
    word(m, symbols['bouncing_bomb_hud_icon_count'], 0xA5A5)
    put(m, symbols['homing_missile_hud_screen_origin'], FB + 0x4800)
    put(m, symbols['bouncing_bomb_hud_screen_origin'], FB + 0x6000)
    put(m, symbols['hud_sprite_conversion_directory_control_words_9'], INPUT)
    for row in range(14):
        word(m, INPUT + 4 + 4 * row, 0x1001 + row)
        word(m, INPUT + 6 + 4 * row, 0x8000 >> row)


def restore(image, m, symbols):
    cpu = state(m, symbols['enable_midframe_copper_blocks_continuation'])
    scans, calls = [], {'homing': 0, 'bouncing': 0}
    entries = {symbols['add_homing_missile_hud_icon']: 'homing',
               symbols['add_bouncing_bomb_hud_icon']: 'bouncing'}
    def observe(pc):
        if pc == 0x2218: scans.append(cpu.a[0])
        if pc in entries: calls[entries[pc]] += 1
    run(image, m, cpu, {RETURN}, observe)
    assert cpu.a[6] == APP and cpu.a[7] == STACK + 4
    return scans, calls


@pytest.mark.parametrize('construction', [-32768, -1, 0, 1, 51, 52, 53, 32767])
def test_restore_mutates_station_header_face_count_and_clears_reentry_state(original_image, memory, symbols, construction):
    prepare(memory, symbols, construction=construction)
    header = get(memory, symbols['model_header_pointers'] + 4 * 99)
    before = bytes(memory[header:header + 28])
    assert restore(original_image, memory, symbols) == ([], {'homing': 0, 'bouncing': 0})
    assert get(memory, header + 2, 2) == (52 - max(0, construction)) & 65535
    assert bytes(memory[header:header + 2]) == before[:2] and bytes(memory[header + 4:header + 28]) == before[4:]
    for n in REFERENCES: assert get(memory, symbols[n]) == 0
    for n in ['amiga_copper_list_a_mode_gate', 'amiga_copper_list_b_mode_gate', 'amiga_copper_list_c_mode_gate']:
        assert get(memory, symbols[n]) == 0x4A01FF00
    assert get(memory, symbols['periodic_display_update_countdown'], 2) == 1
    for n in ['message_display_countdown', 'pending_message_count', 'hud_coordinate_bcd_pair_cache']:
        assert get(memory, symbols[n], 2) == 0
    assert memory[symbols['modal_command_input_flag']] == 0
    assert get(memory, symbols['game_over_sequence_countdown'], 2) == 200


@pytest.mark.parametrize('bomb_count', [0, 1])
@pytest.mark.parametrize('found', [-1, 0, 249])
@pytest.mark.parametrize('phase', [0, 255])
def test_bomb_recovery_scans_only_when_population_nonzero_and_does_not_filter_phase(original_image, memory, symbols, bomb_count, found, phase):
    prepare(memory, symbols, bomb_count=bomb_count, found=found, phase=phase)
    scanned, calls = restore(original_image, memory, symbols)
    assert calls == {'homing': 0, 'bouncing': 0}
    visits = 0 if not bomb_count else 250 if found < 0 else found + 1
    assert scanned == [symbols['world_object_pool'] + 68 * i for i in range(visits)]
    recover = bool(bomb_count) and found < 0
    assert memory[symbols['neutron_bomb_spawn_request']] == (255 if recover else 0x12)
    assert memory[symbols['neutron_bomb_retract_request']] == (0 if recover else 0x34)
    assert get(memory, symbols['carried_neutron_bomb_y_offset']) == (120 if recover else 0xA5B6C7D8)
    assert get(memory, symbols['carried_neutron_bomb_reference']) == 0


@pytest.mark.parametrize('homing', [0, 1, 4, 5, 255])
@pytest.mark.parametrize('bouncing', [0, 1, 4, 5, 255])
def test_actual_icon_helpers_cap_each_rebuilt_bank_at_four(original_image, memory, symbols, homing, bouncing):
    prepare(memory, symbols, homing=homing, bouncing=bouncing)
    scanned, calls = restore(original_image, memory, symbols)
    assert scanned == [] and calls == {'homing': homing, 'bouncing': bouncing}
    assert get(memory, symbols['homing_missile_hud_icon_count'], 2) == min(homing, 4)
    assert get(memory, symbols['bouncing_bomb_hud_icon_count'], 2) == min(bouncing, 4)
