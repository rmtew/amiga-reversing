"""Original packed tunnel direction, linked emission and sentinel update paths.

Fixtures supply backed records and explicit call contexts. They preserve partial
initialization and WORD/LONG edge cases, without a normal-play or lifetime proof.
"""
import pytest

from tests.test_starglider2_gbml_targeting import fields, prepare, OBJ, CHILD, FREE
from tests.test_starglider2_text_editor import (
    original_image, memory, state, run, put, get, RETURN,
)
from tests.test_starglider2_homing_updates import signed32


@pytest.mark.parametrize('high', [0, 1, 128, 255])
@pytest.mark.parametrize('context', [32768, 65535, 0, 16, 32767])
def test_packed_tunnel_header_copies_one_direction_byte_before_clearing_tag_high(original_image, memory, fields, high, context):
    prepare(memory, fields, 48)
    put(memory, OBJ, high*256+48, 2)
    memory[OBJ+28] = 0x25; memory[OBJ+37] = 0x5A
    expected = bytearray(memory[OBJ:OBJ+68])
    expected[0] = 0; expected[36] = high; expected[43] = 1; expected[28] |= 128
    if context < 32768:
        expected[29] = 2; expected[2] |= 0x42
    cpu = state(memory, 0x185D6); cpu.a[0] = OBJ; cpu.d[4] = 0xBEEF0000|context
    run(original_image, memory, cpu, {RETURN}, limit=14)
    assert bytes(memory[OBJ:OBJ+68]) == expected


@pytest.mark.parametrize('high', [0, 1, 2, 127, 128, 255])
def test_constructor_direction_reaches_original_interior_entry_consumer(original_image, memory, fields, high):
    from tests.test_starglider2_structure_transitions import prepare as entry_prepare
    from tests.test_starglider2_structure_profiles import STRUCT, OBJECT
    from tests.test_starglider2_text_editor import APP
    entry_prepare(memory)
    put(memory, STRUCT, high*256+48, 2); memory[STRUCT+37] = 0x5A
    cpu = state(memory, 0x185D6); cpu.a[0] = STRUCT; cpu.d[4] = 65535
    run(original_image, memory, cpu, {RETURN}, limit=14)
    assert get(memory, STRUCT, 2) == 48 and memory[STRUCT+36] == high
    cpu = state(memory, 0xB92E); cpu.a[0] = OBJECT; cpu.a[2] = STRUCT
    run(original_image, memory, cpu, {0xBF74}, limit=100)
    assert get(memory, APP+0x70C) == (19500 if high else 21600)
    assert memory[APP+0xBBA] == (254 if high else 255)
    assert memory[STRUCT+37] == 0x5A


@pytest.mark.parametrize('remaining', [0, 1, 2, 255])
@pytest.mark.parametrize('free', [0, 50, 51, 65535])
@pytest.mark.parametrize('pattern', [0, 0xCC])
def test_tunnel_emission_partial_record_and_first_update(original_image, memory, fields, remaining, free, pattern):
    prepare(memory, fields, 48)
    memory[CHILD:CHILD+68] = bytes([pattern])*68
    memory[CHILD+2] = 255 if pattern else 0
    memory[OBJ+43] = remaining
    put(memory, fields['free_object_count'], free, 2)
    before = bytes(memory[CHILD:CHILD+68]); parent_direction = memory[OBJ+36]
    cpu = state(memory, 0xA136); cpu.a[0] = OBJ
    run(original_image, memory, cpu, {fields['continue_primary_object_update_loop']}, limit=100)
    accepted = remaining != 0 and free > 50
    assert get(memory, fields['free_object_count'], 2) == free-int(accepted)
    assert get(memory, fields['free_object_stack_cursor']) == FREE+(0 if accepted else 4)
    assert memory[OBJ+43] == ((remaining-1)&255 if accepted else remaining)
    assert memory[OBJ+36] == parent_direction
    if not accepted:
        assert bytes(memory[CHILD:CHILD+68]) == before
        return
    expected = bytearray(before)
    put(expected, 0, 20, 2)
    expected[2] &= ~16; expected[3] = 0; expected[28] = 2
    expected[29] = 4; expected[30] = 255; expected[42] = 48
    for offset in [4, 12]: expected[offset:offset+4] = bytes(memory[OBJ+offset:OBJ+offset+4])
    put(expected, 8, (-60)&0xFFFFFFFF)
    for offset, value in [(16, 0), (18, 3072), (20, 0), (44, 0), (46, 65412), (48, 0)]:
        put(expected, offset, value, 2)
    put(expected, 60, OBJ)
    assert bytes(memory[CHILD:CHILD+68]) == expected
    assert get(memory, OBJ+60) == CHILD and memory[OBJ+42] == 20
    cpu = state(memory, 0x93CE); cpu.a[0] = CHILD
    run(original_image, memory, cpu, {fields['continue_primary_object_update_loop']}, limit=40)
    assert get(memory, CHILD+36, 2) == ((pattern*257)-1)&65535
    assert get(memory, CHILD+8) == (-184)&0xFFFFFFFF
    assert get(memory, CHILD+46, 2) == (-120)&65535


CASES = [(-100, -32768), (-100, -124), (-100, -92), (-100, -88),
         (-100, -84), (-100, 0), (-100, 84), (-100, 88),
         (-1000, 120), (-1000, 124), (-1000, 128), (-40, 0),
         (-39, 0), (-41, 0), (2147483647, 32767), (-2147483648, -1),
         (-100000, 32764)]


@pytest.mark.parametrize('y,velocity', CASES)
@pytest.mark.parametrize('counter', [0, 1, 9, 65535])
def test_sentinel_reset_paths_skip_counter_and_attack_uses_post_acceleration_speed(original_image, memory, fields, y, velocity, counter):
    prepare(memory, fields, 20)
    put(memory, OBJ+8, y&0xFFFFFFFF); put(memory, OBJ+46, velocity&65535, 2)
    put(memory, OBJ+36, counter, 2); put(memory, OBJ+18, 65530, 2)
    next_y = (y+velocity)&0xFFFFFFFF; next_velocity = velocity&65535
    reset = signed32(next_y) >= -40
    if reset: next_y = (-60)&0xFFFFFFFF
    else:
        next_velocity = (velocity+4)&65535
        reset = next_velocity == 128
    next_counter = counter if reset else (counter-1)&65535
    if reset: next_velocity = (-124)&65535
    magnitude = (-next_velocity)&65535 if next_velocity&32768 else next_velocity
    fire = not reset and bool((magnitude-88)&32768) and not(next_counter&7)
    cpu = state(memory, 0x93CE); cpu.a[0] = OBJ
    run(original_image, memory, cpu, {fields['continue_primary_object_update_loop'], 0x9F02}, limit=40)
    assert cpu.pc == (0x9F02 if fire else fields['continue_primary_object_update_loop'])
    assert get(memory, OBJ+8) == next_y and get(memory, OBJ+46, 2) == next_velocity
    assert get(memory, OBJ+36, 2) == next_counter
    assert get(memory, OBJ+18, 2) == 10 and memory[OBJ+42] == 48
