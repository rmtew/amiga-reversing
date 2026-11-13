"""Original GBML scheduling, visible-tag selection and missile construction.

Backed local RAM/call contexts qualify CPU transitions and partial records only;
they do not establish normal-play reachability, target lifetime or pool safety.
"""
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_text_editor import (
    original_image, memory, state, run, put, get, APP, INPUT, RETURN,
)
from tests.test_starglider2_scan_acquisition import signed16, project

OBJ, PLAYER, CHILD, TARGET, LIST, FREE = [INPUT+i*0x100 for i in range(6)]
APPS = ['player_object_reference', 'player_world_y', 'visible_object_count',
        'visible_objects_cursor', 'model_type_target_selection_tags_prefix',
        'free_object_count', 'free_object_stack_cursor', 'ai_type12_projectile_request',
        'sine_lookup_pointer', 'cosine_lookup_pointer', 'space_environment_flag']
GLOBALS = ['continue_primary_object_update_loop', 'try_ai_projectile_attack_if_aligned',
           'object_projectile_spawn_y_offsets', 'object_default_motion_words']


@pytest.fixture(scope='module')
def fields(tmp_path_factory, original_image):
    target = Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    folder = tmp_path_factory.mktemp('gbml'); asm, out = folder/'map.s', folder/'map.raw'
    names = APPS+GLOBALS
    asm.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(names)+'\n')
    result = subprocess.run([str(target.parents[1]/'ext/vasm/vasmm68k_mot'),
        '-quiet', '-Fbin', '-m68000', '-no-opt', '-I'+str(target/'includes'),
        '-o', str(out), str(asm)], cwd=target, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout+result.stderr
    raw = out.read_bytes(); size = 4*len(names)
    assert raw[:-size] == original_image[0]
    values = dict(zip(names, struct.unpack('>'+'I'*len(names), raw[-size:])))
    values.update({name: APP+values[name] for name in APPS})
    return values


def prepare(m, f, kind=23):
    for address in [OBJ, PLAYER, CHILD, TARGET]: m[address:address+68] = b'\xA5'*68
    put(m, OBJ, kind, 2); put(m, PLAYER, 30, 2); put(m, TARGET, 14, 2)
    # These zero-axis cached coordinates give heading 3072, without a DIVS path.
    for address, x, z in [(OBJ, 10, 0), (PLAYER, 0, 0), (TARGET, 100, 1000)]:
        put(m, address+50, x, 2); put(m, address+54, z, 2)
    put(m, f['player_object_reference'], PLAYER)
    put(m, f['visible_objects_cursor'], LIST); put(m, f['visible_object_count'], 0, 2)
    put(m, f['free_object_stack_cursor'], FREE+4); put(m, FREE, CHILD)
    m[f['ai_type12_projectile_request']] = 0xA5


def blended_heading(yaw, target):
    current = yaw&4095
    step = signed16(target-current) >> 4
    return (current-step if abs(current-target)>2048 else current+step)&65535


@pytest.mark.parametrize('kind', [23, 50, 59])
@pytest.mark.parametrize('space', [0, 128])
def test_shared_initializer_then_type_specific_counter_or_junk_update(original_image, memory, fields, kind, space):
    prepare(memory, fields, kind)
    memory[fields['space_environment_flag']] = space
    memory[OBJ+2] = 0xA4
    expected = bytearray(memory[OBJ:OBJ+68]); expected[2] |= 1
    put(expected, 36, 2, 2)
    cpu = state(memory, 0x18430); cpu.a[0] = OBJ
    run(original_image, memory, cpu, {RETURN}, limit=5)
    assert bytes(memory[OBJ:OBJ+68]) == expected
    if kind == 59:
        cpu = state(memory, 0x83D8); cpu.a[0] = OBJ
        run(original_image, memory, cpu, {fields['continue_primary_object_update_loop']}, limit=12)
        for offset in [16, 20]:
            assert get(memory, OBJ+offset, 2) == ((0xA5A5+16)&4095 if space else 0xA5A5)
        assert get(memory, OBJ+36, 2) == 2
    else:
        for invocation in range(2):
            cpu = state(memory, 0x9CFC if kind == 23 else 0x9C80); cpu.a[0] = OBJ
            run(original_image, memory, cpu,
                {fields['continue_primary_object_update_loop'], 0xA52A, fields['try_ai_projectile_attack_if_aligned']}, limit=100)
            assert get(memory, OBJ+36, 2) == (1 if invocation == 0 else 0 if kind == 23 else 15)


@pytest.mark.parametrize('yaw', [0, 1024, 2048, 3072, 4095, 65535])
@pytest.mark.parametrize('counter', [0, 1, 2, 17, 513, 65535])
@pytest.mark.parametrize('player_y', [-251, -250, 1])
def test_gbml_wrapped_counter_scan_and_low_altitude_routes(original_image, memory, fields, yaw, counter, player_y):
    prepare(memory, fields)
    put(memory, OBJ+18, yaw, 2); put(memory, OBJ+36, counter, 2)
    put(memory, fields['player_world_y'], player_y&0xFFFFFFFF)
    cpu = state(memory, 0x9CFC); cpu.a[0] = OBJ
    run(original_image, memory, cpu, {fields['continue_primary_object_update_loop'], 0xA52A, 0x9F02}, limit=100)
    left = (counter-1)&65535
    route = 0xA52A if not(left&511) else 0x9F02 if not(left&15) and player_y < -250 else fields['continue_primary_object_update_loop']
    assert cpu.pc == route
    assert get(memory, OBJ+18, 2) == blended_heading(yaw, 3072)
    assert get(memory, OBJ+36, 2) == left
    assert cpu.d[1]&65535 == 3072
    assert memory[fields['ai_type12_projectile_request']] == 0xA5


@pytest.mark.parametrize('yaw', [0, 1024, 2048, 3072, 4095, 65535])
@pytest.mark.parametrize('counter', [0, 1, 2, 65535])
@pytest.mark.parametrize('y', [-2147483648, -1, 0, 2147483647])
def test_cannon_half_turn_altitude_bits_and_exact_zero_reload(original_image, memory, fields, yaw, counter, y):
    prepare(memory, fields, 50)
    put(memory, OBJ+18, yaw, 2); put(memory, OBJ+36, counter, 2)
    put(memory, OBJ+8, y&0xFFFFFFFF); put(memory, fields['player_world_y'], 0x7FFFFFFF)
    cpu = state(memory, 0x9C80); cpu.a[0] = OBJ
    run(original_image, memory, cpu, {fields['continue_primary_object_update_loop'], fields['try_ai_projectile_attack_if_aligned']}, limit=100)
    fire = counter == 1
    assert cpu.pc == fields['try_ai_projectile_attack_if_aligned'] if fire else cpu.pc == fields['continue_primary_object_update_loop']
    assert get(memory, OBJ+18, 2) == blended_heading(yaw, 1024)
    assert memory[OBJ+3] == (((y-0x7FFFFFFF)&0xFFFFFFFF)>>8)&7
    assert get(memory, OBJ+36, 2) == (15 if fire else (counter-1)&65535)
    assert memory[fields['ai_type12_projectile_request']] == (0 if fire else 0xA5)


@pytest.mark.parametrize('order', [[], [OBJ], [OBJ, TARGET], [PLAYER, TARGET], [TARGET, PLAYER]])
@pytest.mark.parametrize('tag', [0, 1, 255])
@pytest.mark.parametrize('heading', [0xABCD03FF, 0x1234FFFF])
@pytest.mark.parametrize('wrong_first', [False, True])
def test_visible_selector_uses_first_equal_byte_tag_without_activity_or_heading_test(original_image, memory, fields, order, tag, heading, wrong_first):
    prepare(memory, fields)
    for address in [OBJ, PLAYER, TARGET]:
        kind = get(memory, address, 2)
        memory[fields['model_type_target_selection_tags_prefix']+kind] = tag
        memory[address+30] = 0  # inactive candidates are not filtered here
    if wrong_first and order:
        memory[fields['model_type_target_selection_tags_prefix']+get(memory, order[0], 2)] = tag^1
    for index, address in enumerate(order): put(memory, LIST+4*index, address)
    put(memory, fields['visible_object_count'], len(order), 2)
    expected = next((address for address in order if address != OBJ and
        memory[fields['model_type_target_selection_tags_prefix']+get(memory, address, 2)] == tag), PLAYER)
    cpu = state(memory, 0xA4FA); cpu.a[0] = OBJ
    cpu.d[0] = 0xFFFF0000|tag; cpu.d[1] = heading
    run(original_image, memory, cpu, {RETURN}, limit=50)
    assert cpu.a[4] == expected and cpu.d[1] == heading


@pytest.mark.parametrize('kind', [1, 23])
@pytest.mark.parametrize('yaw,target_yaw', [(0, 0), (0, 99), (0, 100), (0, 65535), (4095, 0), (4095, 4095), (0, 32768)])
@pytest.mark.parametrize('free', [24, 25, 65535])
def test_stored_target_missile_gate_and_exact_partial_constructor(original_image, memory, fields, kind, yaw, target_yaw, free):
    prepare(memory, fields, kind)
    run(original_image, memory, state(memory, 0x1F0E), {RETURN})
    put(memory, OBJ+18, yaw, 2); put(memory, fields['free_object_count'], free, 2)
    before = bytes(memory[CHILD:CHILD+68]); expected = bytearray(before)
    difference = (target_yaw-(yaw&4095))&65535
    magnitude = (-difference)&65535 if difference&32768 else difference
    accepted = free > 24 and bool((magnitude-100)&32768)
    cpu = state(memory, 0xA52A); cpu.a[0] = OBJ; cpu.a[4] = TARGET; cpu.d[1] = target_yaw
    run(original_image, memory, cpu, {fields['continue_primary_object_update_loop']}, limit=100)
    assert get(memory, fields['free_object_count'], 2) == free-int(accepted)
    assert get(memory, fields['free_object_stack_cursor']) == FREE+(0 if accepted else 4)
    if not accepted:
        assert bytes(memory[CHILD:CHILD+68]) == before
        return
    reverse = get(memory, 0xAE60+2*kind, 2) != 0
    heading = ((yaw&65535)-(2048 if reverse else 0))&4095
    put(expected, 0, 25, 2)
    expected[3] = 0; expected[28] = 2; expected[29] = 4; expected[30] = 255
    expected[34] = 255; expected[42] = kind
    for offset in [4, 12]: expected[offset:offset+4] = bytes(memory[OBJ+offset:OBJ+offset+4])
    height = signed16(get(memory, fields['object_projectile_spawn_y_offsets']+2*kind, 2))
    put(expected, 8, (get(memory, OBJ+8)+height)&0xFFFFFFFF)
    for offset, value in [(16, 0), (18, heading), (20, 0), (36, 100), (46, 0)]: put(expected, offset, value, 2)
    scale = get(memory, fields['object_default_motion_words']+50, 2)
    put(expected, 32, scale, 2)
    sine = get(memory, get(memory, fields['sine_lookup_pointer'])+2*heading, 2)
    cosine = get(memory, get(memory, fields['cosine_lookup_pointer'])+2*heading, 2)
    put(expected, 44, (-project(scale, sine))&65535, 2)
    put(expected, 48, project(scale, cosine)&65535, 2)
    put(expected, 60, TARGET)
    assert bytes(memory[CHILD:CHILD+68]) == expected
    assert memory[OBJ+42] == 25


@pytest.mark.parametrize('candidate', [PLAYER, TARGET])
@pytest.mark.parametrize('phase', [0, 127, 255])
def test_gbml_scan_to_construction_keeps_player_heading_and_selected_reference(original_image, memory, fields, candidate, phase):
    prepare(memory, fields)
    run(original_image, memory, state(memory, 0x1F0E), {RETURN})
    put(memory, OBJ+18, 3072, 2); put(memory, OBJ+36, 513, 2)
    put(memory, fields['free_object_count'], 25, 2)
    own_tag = 0x37
    memory[fields['model_type_target_selection_tags_prefix']+23] = own_tag
    memory[fields['model_type_target_selection_tags_prefix']+get(memory, candidate, 2)] = own_tag^255
    memory[candidate+30] = phase
    put(memory, fields['visible_object_count'], 1, 2); put(memory, LIST, candidate)
    cpu = state(memory, 0x9CFC); cpu.a[0] = OBJ
    run(original_image, memory, cpu, {fields['continue_primary_object_update_loop']}, limit=170)
    assert get(memory, CHILD+60) == candidate
    assert get(memory, CHILD+18, 2) == 3072
    assert get(memory, CHILD+38, 2) == 0xA5A5  # cadence remains uninitialized here
    assert get(memory, OBJ+36, 2) == 512
    cpu = state(memory, 0x9694); cpu.a[0] = CHILD
    run(original_image, memory, cpu, {fields['continue_primary_object_update_loop']}, limit=100)
    assert memory[CHILD+30] == (0 if phase < 128 else 255)
    assert get(memory, CHILD+36, 2) == (100 if phase < 128 else 99)
