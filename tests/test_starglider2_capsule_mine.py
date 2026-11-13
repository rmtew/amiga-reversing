"""Original capsule lifecycle and mine gates in supplied, backed RAM contexts.

Execute original CPU instructions, not a replacement implementation. Constructor
and next-update tests retain reused bytes. No normal-play reachability, unique
ownership, hardware, message-display or interrupt-scheduling claim is made.
"""
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_text_editor import (
    original_image, memory, state, run, put, get, APP, INPUT, RETURN,
)
from tests.test_starglider2_palette_priority import rng

OBJ, CHILD, FREE = INPUT, INPUT+0x100, INPUT+0x500
APPS = ['free_object_count', 'free_object_stack_cursor',
        'space_environment_flag', 'horizontal_world_wrap_mask',
        'icarus_shield_strength', 'icarus_hits_received',
        'player_rotation2_damage_impulse']
GLOBALS = ['continue_primary_object_update_loop',
           'format_and_enqueue_object_coordinate_message',
           'mine_detected_message_prefix', 'SG2_OBJECT_TYPE_ESCAPE_CAPSULE',
           'SG2_ROTATION2_DAMAGE_JITTER_MASK', 'SG2_ROTATION2_DAMAGE_JITTER_BIAS']


@pytest.fixture(scope='module')
def fields(tmp_path_factory, original_image):
    target = Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    folder = tmp_path_factory.mktemp('capsule-mine')
    asm, out = folder/'map.s', folder/'map.raw'
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


def capsule_step(record, space, mask):
    """Independent finite state transition, with explicit WORD/LONG wrapping."""
    expected = bytearray(record)
    spin = get(expected, 38, 2)
    if spin:
        spin = (spin-2)&65535
        put(expected, 38, spin, 2)
        put(expected, 18, (get(expected, 18, 2)+spin)&65535, 2)
    stopped = expected[40] != 0
    if not stopped:
        for velocity, position in [(44, 4), (48, 12)]:
            value = get(expected, velocity, 2) >> 1  # original LSR, never ASR
            put(expected, velocity, value, 2)
            put(expected, position, ((get(expected, position)+value)&0xFFFFFFFF)&mask)
        y = get(expected, 8)
        signed_y = y-0x100000000 if y&0x80000000 else y
        if not space and signed_y < -45:
            put(expected, 8, (y+8)&0xFFFFFFFF)
            return expected
        expected[40] = 255
    if spin:
        put(expected, 38, (spin-2)&65535, 2)
    return expected


@pytest.mark.parametrize('spin', [0, 1, 2, 3, 4, 144, 65516, 65535])
@pytest.mark.parametrize('stopped', [0, 1, 128, 255])
@pytest.mark.parametrize('space,y', [(0, -54), (0, -46), (0, -45), (0, 0x7FFFFFFF), (1, -100), (128, -100)])
def test_capsule_word_parity_logical_decay_and_stopping(original_image, memory, fields, spin, stopped, space, y):
    memory[OBJ:OBJ+68] = b'\xA5'*68
    for offset, value, width in [(4, 0xFFFFFFFE, 4), (8, y&0xFFFFFFFF, 4),
                                 (12, 0x12345678, 4), (18, 65534, 2),
                                 (38, spin, 2), (44, 65535, 2), (48, 32768, 2)]:
        put(memory, OBJ+offset, value, width)
    memory[OBJ+40] = stopped
    memory[fields['space_environment_flag']] = space
    put(memory, fields['horizontal_world_wrap_mask'], 0xFFFF)
    expected = capsule_step(bytes(memory[OBJ:OBJ+68]), space, 0xFFFF)
    cpu = state(memory, 0x99BC); cpu.a[0] = OBJ
    run(original_image, memory, cpu, {fields['continue_primary_object_update_loop']}, limit=45)
    assert bytes(memory[OBJ:OBJ+68]) == expected


@pytest.mark.parametrize('stopped', [0, 1, 255])
@pytest.mark.parametrize('count', [0, 10, 11, 65535])
@pytest.mark.parametrize('y', [-100, -90, -89, 0x7FFFFFFF])
def test_capsule_spawn_preserves_stop_byte_and_next_update(original_image, memory, fields, stopped, count, y):
    memory[OBJ:OBJ+68] = b'\x5A'*68
    memory[CHILD:CHILD+68] = b'\xA5'*68
    memory[OBJ+43] = 1; memory[CHILD+40] = stopped
    put(memory, OBJ, 32, 2); put(memory, OBJ+8, y&0xFFFFFFFF)
    put(memory, FREE, CHILD)
    put(memory, fields['free_object_stack_cursor'], FREE+4)
    put(memory, fields['free_object_count'], count, 2)
    before = bytes(memory[CHILD:CHILD+68])
    cpu = state(memory, 0x992E); cpu.a[0] = OBJ
    run(original_image, memory, cpu, {fields['continue_primary_object_update_loop']}, limit=45)
    if count <= 10:
        assert bytes(memory[CHILD:CHILD+68]) == before
        assert memory[OBJ+43] == 1 and get(memory, fields['free_object_stack_cursor']) == FREE+4
        assert get(memory, fields['free_object_count'], 2) == count
        return
    expected = bytearray(before)
    put(expected, 0, fields['SG2_OBJECT_TYPE_ESCAPE_CAPSULE'], 2)
    expected[3] = 0; expected[28] = 2; expected[29] = 7; expected[30] = 255; expected[42] = 32
    for offset, width in [(4, 4), (12, 4), (16, 2), (20, 2), (44, 2), (48, 2)]:
        expected[offset:offset+width] = bytes(memory[OBJ+offset:OBJ+offset+width])
    raised = (y+90)&0xFFFFFFFF
    put(expected, 8, raised if raised&0x80000000 else 0xFFFFFFF6)
    put(expected, 38, 144, 2)
    assert bytes(memory[CHILD:CHILD+68]) == expected
    assert memory[OBJ+43] == 0 and memory[OBJ+42] == fields['SG2_OBJECT_TYPE_ESCAPE_CAPSULE']
    assert get(memory, fields['free_object_stack_cursor']) == FREE
    assert get(memory, fields['free_object_count'], 2) == count-1
    memory[fields['space_environment_flag']] = 1
    put(memory, fields['horizontal_world_wrap_mask'], 0xFFFF)
    cpu = state(memory, 0x99BC); cpu.a[0] = CHILD
    run(original_image, memory, cpu, {fields['continue_primary_object_update_loop']}, limit=45)
    assert bytes(memory[CHILD:CHILD+68]) == capsule_step(expected, 1, 0xFFFF)


@pytest.mark.parametrize('seed', [0, 1, 31, 63, 0xABCDEF01])
def test_placement_capsule_random_stop_and_retained_word_bytes(original_image, memory, fields, seed):
    memory[OBJ:OBJ+68] = b'\xA5'*68
    put(memory, APP+0x60, 0x12345678); put(memory, APP+0x64, seed)
    expected = bytearray(memory[OBJ:OBJ+68])
    next_rng = rng(0x12345678, seed); choice = next_rng[1]&63
    for offset, value, width in [(8, 0xFFFFFE70, 4), (38, 65516, 2),
                                 (32, 200, 2), (36, choice, 2)]:
        put(expected, offset, value, width)
    expected[40] = choice
    cpu = state(memory, 0x1834E); cpu.a[0] = OBJ
    run(original_image, memory, cpu, {RETURN}, limit=40)
    assert bytes(memory[OBJ:OBJ+68]) == expected
    assert [get(memory, APP+o) for o in [0x60, 0x64]] == list(next_rng)


@pytest.mark.parametrize('spin', [1, 3, 144, 65516])
def test_stopped_capsule_repeated_spin_keeps_odd_residues(original_image, memory, fields, spin):
    memory[OBJ:OBJ+68] = b'\0'*68
    memory[OBJ+40] = 1; put(memory, OBJ+38, spin, 2)
    expected = bytes(memory[OBJ:OBJ+68])
    for _ in range(40):
        expected = capsule_step(expected, 0, 0xFFFF)
        cpu = state(memory, 0x99BC); cpu.a[0] = OBJ
        run(original_image, memory, cpu, {fields['continue_primary_object_update_loop']}, limit=20)
        assert bytes(memory[OBJ:OBJ+68]) == expected
        if spin&1:
            assert get(memory, OBJ+38, 2)&1


@pytest.mark.parametrize('z', [-32768, -1537, -1536, -769, -768, -1, 0, 767, 768, 1536, 1537, 32767])
@pytest.mark.parametrize('shield', [0, 1499, 1500, 1501, 65535])
def test_mine_unsigned_magnitude_then_n_only_gate_and_shield_borrow(original_image, memory, fields, z, shield):
    memory[OBJ:OBJ+68] = b'\xA5'*68
    put(memory, OBJ+26, z&65535, 2); put(memory, OBJ+18, 65520, 2)
    put(memory, fields['icarus_shield_strength'], shield, 2)
    put(memory, fields['icarus_hits_received'], 0xFFFFFFFF)
    put(memory, fields['player_rotation2_damage_impulse'], 65530, 2)
    put(memory, APP+0x60, 0x12345678); put(memory, APP+0x64, 0xABCDEF01)
    magnitude = (abs(z)&65535)
    inside = magnitude <= 1536
    warning = inside and not ((z-768)&0x8000)
    damage = inside and not warning
    cpu = state(memory, 0x8DE2); cpu.a[0] = OBJ
    stops = {fields['continue_primary_object_update_loop'], fields['format_and_enqueue_object_coordinate_message']}
    run(original_image, memory, cpu, stops, limit=45)
    assert (cpu.pc == fields['format_and_enqueue_object_coordinate_message']) == warning
    if warning:
        assert cpu.a[1] == fields['mine_detected_message_prefix']
        # Stop at the real call; message formatting and its return are unqualified.
    assert get(memory, OBJ+18, 2) == (65520 if warning else (65520+64)&65535)
    assert memory[OBJ+30] == (0 if damage else 0xA5)
    assert get(memory, fields['icarus_shield_strength'], 2) == (max(0, shield-1500) if damage else shield)
    assert get(memory, fields['icarus_hits_received']) == (0 if damage else 0xFFFFFFFF)
    random = rng(0x12345678, 0xABCDEF01) if damage else (0x12345678, 0xABCDEF01)
    assert [get(memory, APP+o) for o in [0x60, 0x64]] == list(random)
    delta = (random[1]&fields['SG2_ROTATION2_DAMAGE_JITTER_MASK'])-fields['SG2_ROTATION2_DAMAGE_JITTER_BIAS'] if damage else 0
    assert get(memory, fields['player_rotation2_damage_impulse'], 2) == (65530+delta)&65535
