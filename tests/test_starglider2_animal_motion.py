"""Original placement, animation and shared horizontal steering CPU windows.

Record backing and cached player coordinates are explicit inputs. These cases
do not establish normal-game reachability, slot lifetime or complete rendering.
"""
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_gbml_targeting import fields, prepare, OBJ, PLAYER, LIST
from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, RETURN
from tests.test_starglider2_palette_priority import rng
from tests.test_starglider2_homing_updates import heading
from tests.test_starglider2_scan_acquisition import signed16


@pytest.fixture(scope='module')
def extra(tmp_path_factory, original_image):
    target = Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    names = ['selected_celestial_body_index', 'model_rotation_0', 'model_rotation_1', 'model_rotation_2']
    folder = tmp_path_factory.mktemp('animal-fields'); asm, out = folder/'map.s', folder/'map.raw'
    asm.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(names)+'\n')
    result = subprocess.run([str(target.parents[1]/'ext/vasm/vasmm68k_mot'), '-quiet', '-Fbin',
        '-m68000', '-no-opt', '-I'+str(target/'includes'), '-o', str(out), str(asm)],
        cwd=target, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout+result.stderr
    raw = out.read_bytes(); size = 4*len(names)
    assert raw[:-size] == original_image[0]
    return dict(zip(names, [APP+x for x in struct.unpack('>'+'I'*len(names), raw[-size:])]))


@pytest.mark.parametrize('kind', [10, 11])
@pytest.mark.parametrize('body', [0, 8, 14])
@pytest.mark.parametrize('seed', [(0,0), (1,0), (0xFFFFFFFF,0x80000000), (0x12345678,0xABCDEF01)])
@pytest.mark.parametrize('dirty', [0, 0xA5])
def test_shared_animal_constructor_correlates_counters_and_preserves_other_bytes(original_image, memory, fields, extra, kind, body, seed, dirty):
    prepare(memory, fields, kind); memory[OBJ:OBJ+68] = bytes([dirty])*68; put(memory, OBJ, kind, 2)
    put(memory, extra['selected_celestial_body_index'], body, 2)
    put(memory, APP+0x60, seed[0]); put(memory, APP+0x64, seed[1])
    a, b = seed; values = []
    for _ in range(3): a, b = rng(a,b); values.append(b)
    expected = bytearray(memory[OBJ:OBJ+68])
    put(expected, 18, values[0]&4095, 2); put(expected, 32, 65406, 2)
    y = (get(memory, 0x17642+4*body)+1024+(values[1]&8191))&0xFFFFFFFF
    put(expected, 8, y); put(expected, 38, values[2]&1023, 2); put(expected, 36, values[2]&7, 2)
    expected[31] = 1; expected[2] |= 32
    cpu = state(memory, 0x182F0); cpu.a[0] = OBJ; old_a1 = cpu.a[1]
    run(original_image, memory, cpu, {RETURN}, limit=100)
    assert bytes(memory[OBJ:OBJ+68]) == expected and cpu.a[1] == old_a1
    assert [get(memory, APP+o)for o in [0x60,0x64]] == [a,b]
    assert get(memory, OBJ+36, 2) == get(memory, OBJ+38, 2)&7


@pytest.mark.parametrize('entry', [0x94E6, 0x8A4E])
@pytest.mark.parametrize('variant', range(256))
def test_whale_wrap_and_pac_worm_motion_gate_cover_the_byte_domain(original_image, memory, fields, entry, variant):
    prepare(memory, fields, 10 if entry == 0x94E6 else 36); memory[OBJ+3] = variant
    expected = (variant+1)&255
    if entry == 0x94E6: expected = 0 if expected == 22 else expected; moving = True
    else:
        moving = expected > 14
        if expected == 24: expected = 0
    cpu = state(memory, entry); cpu.a[0] = OBJ
    run(original_image, memory, cpu, {0x9500, fields['continue_primary_object_update_loop']}, limit=12)
    assert memory[OBJ+3] == expected
    assert cpu.pc == (0x9500 if moving else fields['continue_primary_object_update_loop'])


@pytest.mark.parametrize('variant', [0,1,5,6,7,8,255])
@pytest.mark.parametrize('step', [0,1,255,128])
def test_duck_holds_turn_frames_and_zero_sum_skips_motion(original_image, memory, fields, variant, step):
    prepare(memory, fields, 11); memory[OBJ+3] = variant; memory[OBJ+31] = step
    value = (variant+step)&255
    expected_variant, expected_step, moving = variant, step, False
    if step:
        if value == 0: expected_step = 1
        elif value == 7: expected_step, moving = 255, True
        else: expected_variant, moving = value, True
    cpu = state(memory, 0x9390); cpu.a[0] = OBJ
    run(original_image, memory, cpu, {0x9500, fields['continue_primary_object_update_loop']}, limit=15)
    assert (memory[OBJ+3],memory[OBJ+31]) == (expected_variant,expected_step)
    assert cpu.pc == (0x9500 if moving else fields['continue_primary_object_update_loop'])


@pytest.mark.parametrize('x,z', [(801,701), (800,701), (801,700), (32768,701)])
@pytest.mark.parametrize('evasion', [0,1,2,32768])
@pytest.mark.parametrize('counter', [0,1,33,513,65535])
@pytest.mark.parametrize('upper', [0,0x12340000])
def test_shared_steering_or_windows_and_byte_mask_leave_counter_high_byte(original_image, memory, fields, x, z, evasion, counter, upper):
    prepare(memory, fields, 10)
    put(memory, OBJ+50, x, 2); put(memory, OBJ+54, z, 2)
    put(memory, OBJ+36, counter, 2); put(memory, OBJ+38, evasion, 2)
    put(memory, OBJ+44, 65535, 2); put(memory, OBJ+48, 32768, 2); put(memory, APP+0x6FC, 65535)
    old_x, old_z = get(memory, OBJ+4), get(memory, OBJ+12)
    left = (evasion-1)&65535 if evasion else 0
    mag_x, mag_z = [signed16(-signed16(v)) if signed16(v)<0 else signed16(v) for v in [x,z]]
    near = mag_x <= 800 or mag_z <= 700
    quarter = left != 0 or near
    periodic = not quarter and not((counter-1)&31)
    next_counter = counter if quarter else (counter-2 if periodic else counter-1)&65535
    cpu = state(memory, 0x9500); cpu.a[0] = OBJ; cpu.d[0] = cpu.d[1] = upper|1
    run(original_image, memory, cpu, {0xACB0, fields['continue_primary_object_update_loop']}, limit=120)
    assert get(memory, OBJ+4) == (old_x-1)&65535 and get(memory, OBJ+12) == (old_z-32768)&65535
    assert get(memory, OBJ+38, 2) == (left if left else 50 if near else 0)
    assert get(memory, OBJ+36, 2) == next_counter
    assert cpu.pc == (0xACB0 if quarter or periodic else fields['continue_primary_object_update_loop'])
    if quarter or periodic:
        base = heading(memory, x, z, 0, 0, upper, upper)
        delta = 1024 if quarter else ((next_counter&0xFF1F)-16)&65535
        assert cpu.d[1]&65535 == (base+delta)&65535


@pytest.mark.parametrize('nibble', range(16))
@pytest.mark.parametrize('dirty', [0,0xA5])
def test_tree_pitch_and_partial_height_choices_feed_the_regular_model_pose(original_image, memory, fields, extra, nibble, dirty):
    prepare(memory, fields, 24); memory[OBJ:OBJ+68] = bytes([dirty])*68; put(memory, OBJ, 24, 2)
    memory[OBJ+30] = 255
    first, second = 0, 0xABC00000|(0xFFF9^nibble)
    put(memory, APP+0x60, first); put(memory, APP+0x64, second)
    expected = bytearray(memory[OBJ:OBJ+68]); put(expected, 16, 1024, 2); expected[2] |= 128
    choice = (3,-10) if nibble == 0 else (2,-20) if nibble == 8 else (5,-5) if nibble in [4,12] else None
    if choice:
        expected[29] = choice[0]; put(expected, 8, choice[1]&0xFFFFFFFF)
    cpu = state(memory, 0x1843E); cpu.a[0] = OBJ
    run(original_image, memory, cpu, {RETURN}, limit=40)
    assert bytes(memory[OBJ:OBJ+68]) == expected
    assert [get(memory, APP+o)for o in [0x60,0x64]] == list(rng(first, second))
    put(memory, LIST, OBJ)
    cpu = state(memory, 0x3F50); cpu.a[5] = LIST; cpu.d[7] = 0
    run(original_image, memory, cpu, {0x4A2A}, limit=40)
    assert [get(memory, extra[f'model_rotation_{i}'], 2)for i in range(3)] == [1024, get(expected,18,2), get(expected,20,2)]
