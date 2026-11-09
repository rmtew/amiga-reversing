"""Original viewer command, rotation and two-range variant stepping.

Supplied CPU frames are not normal-game reachability, arbitrary selector bounds,
input-device delivery, renderer/hardware proof or whole-loop timing equivalence.
"""
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, STACK, RETURN
from tests.test_starglider2_control_normalization import signed

BOUNDS, DISPATCH = 0xECA2, 0xEE6A
FIELDS = ['model_viewer_animation_state', 'model_viewer_bounds_pair_offset', 'active_model_type_index',
          'model_viewer_rotation_step_0', 'model_viewer_rotation_step_1', 'model_viewer_rotation_step_2',
          'model_rotation_0', 'model_rotation_1', 'model_rotation_2', 'world_object_pool',
          'active_model_scale_shift', 'model_face_culling_disabled_flag', 'debug_features_enabled_flag']


@pytest.fixture(scope='module')
def slots(tmp_path_factory):
    target = Path(__file__).resolve().parents[1] / 'targets/amiga_raw_starglider2_game'
    temp = tmp_path_factory.mktemp('viewer-fields'); asm, out = temp / 'fields.s', temp / 'fields.bin'
    asm.write_text((target / 'starglider2_game.s').read_text().split('    SECTION code,code', 1)[0]
                   + '\n SECTION constants,data\n dc.l ' + ','.join(FIELDS) + '\n')
    result = subprocess.run([str(target.parents[1] / 'tools/vasmm68k_mot.exe'), '-quiet', '-Fbin', '-no-opt',
                             '-I' + str(target / 'includes'), '-o', str(out), str(asm)],
                            cwd=target, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    return dict(zip(FIELDS, struct.unpack('>' + str(len(FIELDS)) + 'I', out.read_bytes())))


def slot(slots, name): return APP + slots[name]
def word(m, p, value): put(m, p, value & 65535, 2)


@pytest.mark.parametrize('axis,key,delta', [(0, 'X', 4), (0, 'S', -4), (1, 'Y', 4),
                                         (1, 'T', -4), (2, 'Z', 4), (2, 'A', -4)])
@pytest.mark.parametrize('old', [-32768, -132, -129, -128, -127, 0, 127, 128, 129, 132, 32767])
def test_command_rotation_limits_test_old_value_before_word_update(original_image, memory, slots, axis, key, delta, old):
    cpu = state(memory, DISPATCH); cpu.d[0] = ord(key)
    before = [11, 22, 33]; before[axis] = old
    for i, v in enumerate(before): word(memory, slot(slots, 'model_viewer_rotation_step_' + str(i)), v)
    run(original_image, memory, cpu, {RETURN})
    expected = before[:]
    if (delta > 0 and old <= 128) or (delta < 0 and old >= -128): expected[axis] = signed(old + delta)
    assert [signed(get(memory, slot(slots, 'model_viewer_rotation_step_' + str(i)), 2)) for i in range(3)] == expected
    assert cpu.a[7] == STACK + 4


@pytest.mark.parametrize('key', ['P', 'R'])
def test_stop_and_reset_have_different_angle_effects(original_image, memory, slots, key):
    cpu = state(memory, DISPATCH); cpu.d[0] = ord(key)
    for i in range(3):
        word(memory, slot(slots, 'model_viewer_rotation_step_' + str(i)), 4 + i)
        word(memory, slot(slots, 'model_rotation_' + str(i)), 100 + i)
    run(original_image, memory, cpu, {RETURN})
    assert [get(memory, slot(slots, 'model_viewer_rotation_step_' + str(i)), 2) for i in range(3)] == [0] * 3
    assert [get(memory, slot(slots, 'model_rotation_' + str(i)), 2) for i in range(3)] == ([0] * 3 if key == 'R' else [100, 101, 102])


@pytest.mark.parametrize('key', list('0123456789'))
def test_scale_accepts_only_digits_zero_through_eight(original_image, memory, slots, key):
    cpu = state(memory, DISPATCH); cpu.d[0] = 0xABCD0000 | ord(key)
    word(memory, slot(slots, 'active_model_scale_shift'), 17)
    memory[slot(slots, 'model_viewer_animation_state')] = 0
    run(original_image, memory, cpu, {RETURN})
    assert get(memory, slot(slots, 'active_model_scale_shift'), 2) == (int(key) if key != '9' else 17)
    assert cpu.d[0] == (0xABCD0000 | int(key) if key != '9' else 0xABCD0039)


@pytest.mark.parametrize('key', [ord('Q'), 27])
def test_quit_discards_control_call_frame_before_outer_return(original_image, memory, slots, key):
    cpu = state(memory, DISPATCH); cpu.d[0] = key
    put(memory, STACK, 0xEABC); put(memory, STACK + 4, RETURN)
    run(original_image, memory, cpu, {RETURN})
    assert cpu.d[0] == 0 and cpu.a[7] == STACK + 8


@pytest.mark.parametrize('debug', [0, 1, 128, 255])
@pytest.mark.parametrize('old', [0, 1, 128, 255])
def test_culling_toggle_is_debug_gated_and_bitwise(original_image, memory, slots, debug, old):
    cpu = state(memory, DISPATCH); cpu.d[0] = ord('H')
    memory[slot(slots, 'debug_features_enabled_flag')] = debug
    memory[slot(slots, 'model_face_culling_disabled_flag')] = old
    memory[slot(slots, 'model_viewer_animation_state')] = 0
    run(original_image, memory, cpu, {RETURN})
    assert memory[slot(slots, 'model_face_culling_disabled_flag')] == (old ^ 255 if debug else old)


def expected_variant_step(bounds, pair, selector, toward_end):
    target, other = (bounds[pair + 1], bounds[pair]) if toward_end else (bounds[pair], bounds[pair + 1])
    if selector != target: return (selector + (1 if target >= other else -1)) & 255, pair
    if pair or bounds[2] & 128: return bounds[0 if toward_end else 1], 0
    return bounds[2 if toward_end else 3], 2


@pytest.mark.parametrize('model', [0, 1, 3, 4, 103])  # includes actual ascending/descending second-range record4
@pytest.mark.parametrize('pair', [0, 2])
@pytest.mark.parametrize('toward_end', [False, True])
@pytest.mark.parametrize('selector_kind', ['zero', 'maximum', 'start', 'end'])
def test_actual_two_range_records_step_and_wrap_byte_without_saturation(original_image, memory, slots, model, pair, toward_end, selector_kind):
    bounds = list(memory[BOUNDS + 4 * model:BOUNDS + 4 * model + 4])
    selector = {'zero': 0, 'maximum': 255, 'start': bounds[pair], 'end': bounds[pair + 1]}[selector_kind]
    word(memory, slot(slots, 'active_model_type_index'), model)
    memory[slot(slots, 'model_viewer_bounds_pair_offset')] = pair
    record = slot(slots, 'world_object_pool'); memory[record + 3] = selector
    before = bytes(memory[record:record + 68])
    cpu = state(memory, 0xEFAA if toward_end else 0xEF4C); cpu.a[4] = record
    run(original_image, memory, cpu, {RETURN})
    expected, next_pair = expected_variant_step(bounds, pair, selector, toward_end)
    assert memory[record + 3] == expected and memory[slot(slots, 'model_viewer_bounds_pair_offset')] == next_pair
    assert bytes(memory[record:record + 3]) == before[:3] and bytes(memory[record + 4:record + 68]) == before[4:]


@pytest.mark.parametrize('animation', [0, 1, 2, 128, 255])
def test_idle_command_steps_only_active_unpaused_animation(original_image, memory, slots, animation):
    cpu = state(memory, DISPATCH); cpu.d[0] = 0
    word(memory, slot(slots, 'active_model_type_index'), 1)
    memory[slot(slots, 'model_viewer_animation_state')] = animation
    memory[slot(slots, 'model_viewer_bounds_pair_offset')] = 0
    record = slot(slots, 'world_object_pool'); memory[record + 3] = 255
    bounds = list(memory[BOUNDS + 4:BOUNDS + 8])
    run(original_image, memory, cpu, {RETURN})
    expected = (255, 0) if animation in [0, 128] else expected_variant_step(bounds, 0, 255, animation == 1)
    assert (memory[record + 3], memory[slot(slots, 'model_viewer_bounds_pair_offset')]) == expected


@pytest.mark.parametrize('key,new_state,step', [(ord('E'), 128, None), (0x8F, 128, True),
                                               (0x8E, 128, False), (0x8D, 255, None), (0x8C, 1, None)])
@pytest.mark.parametrize('enabled', [False, True])
def test_animation_commands_are_gated_and_single_steps_remain_paused(original_image, memory, slots, key, new_state, step, enabled):
    cpu = state(memory, DISPATCH); cpu.d[0] = key
    word(memory, slot(slots, 'active_model_type_index'), 1)
    memory[slot(slots, 'model_viewer_animation_state')] = int(enabled)
    memory[slot(slots, 'model_viewer_bounds_pair_offset')] = 0
    record = slot(slots, 'world_object_pool'); memory[record + 3] = 255
    run(original_image, memory, cpu, {RETURN})
    expected = expected_variant_step(list(memory[BOUNDS + 4:BOUNDS + 8]), 0, 255, step) if enabled and step is not None else (255, 0)
    assert (memory[record + 3], memory[slot(slots, 'model_viewer_bounds_pair_offset')]) == expected
    assert memory[slot(slots, 'model_viewer_animation_state')] == (new_state if enabled else 0)


@pytest.mark.parametrize('old', [0, 1, 128, 255])
def test_clear_latch_toggle_preserves_adjacent_draw_buffer_byte(original_image, memory, slots, old):
    cpu = state(memory, DISPATCH); cpu.d[0] = ord('D')
    memory[0xFD4C], memory[0xFD4D] = old, 0xA5
    run(original_image, memory, cpu, {RETURN})
    assert memory[0xFD4C] == old ^ 255 and memory[0xFD4D] == 0xA5


def test_previous_at_zero_retains_original_out_of_table_selector(original_image, memory, slots):
    cpu = state(memory, DISPATCH); cpu.d[0] = ord(',')
    word(memory, slot(slots, 'active_model_type_index'), 0)
    run(original_image, memory, cpu, {0xF054})  # name-display handoff, before dereferencing its out-of-range pointer
    assert get(memory, slot(slots, 'active_model_type_index'), 2) == 65535
    assert cpu.a[0] == BOUNDS and signed(cpu.d[0] & 65535) == -4
    assert memory[slot(slots, 'model_viewer_animation_state')] == (0 if memory[BOUNDS - 4] & 128 else 1)
