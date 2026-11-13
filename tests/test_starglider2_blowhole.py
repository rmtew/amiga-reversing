"""Original blowhole/diamond windows with explicit records and no other writers.

These CPU cases establish local construction, gates and arithmetic. A repeated
initializer-to-update slice is not a normal-play or renderer/interruption proof.
"""
import pytest

from tests.test_starglider2_gbml_targeting import fields, prepare, OBJ, CHILD, FREE
from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, RETURN
from tests.test_starglider2_scan_acquisition import signed16, project
from tests.test_starglider2_homing_updates import signed32


def setup(image, m, f, counter=0, remaining=3, variant=9, step=1, free=35, pattern=0xCC):
    prepare(m, f, 64)
    run(image, m, state(m, 0x1F0E), {RETURN})
    m[CHILD:CHILD+68] = bytes([pattern])*68
    m[CHILD+2] = 255 if pattern else 0
    m[OBJ+3] = variant; m[OBJ+31] = step; m[OBJ+43] = remaining; m[OBJ+28] = 2
    put(m, OBJ+36, counter, 2); put(m, OBJ+18, 1024, 2)
    put(m, f['free_object_count'], free, 2); put(m, APP+0x6FC, 65535)


def oscillator(variant, step):
    value = (variant+step)&255
    return value, 1 if value == 0 else 255 if value == 9 else step


@pytest.mark.parametrize('counter', [0, 1, 2, 0xF700, 0xF701, 65535])
@pytest.mark.parametrize('remaining', [0, 1, 3, 255])
@pytest.mark.parametrize('free', [34, 35, 65535])
@pytest.mark.parametrize('variant', [8, 9])
@pytest.mark.parametrize('pattern', [0, 0xCC])
def test_rearm_gate_precedes_partial_diamond_construction(original_image, memory, fields, counter, remaining, free, variant, pattern):
    setup(original_image, memory, fields, counter, remaining, variant, free=free, pattern=pattern)
    next_counter = (counter-1)&65535 if counter else 0
    rearm = counter != 0 and next_counter == 0xF700
    next_remaining = 3 if rearm else remaining
    accepted = (counter == 0 or rearm) and next_remaining != 0 and free > 34 and variant == 9
    expected = bytearray(memory[CHILD:CHILD+68])
    cpu = state(memory, 0xA1C4); cpu.a[0] = OBJ
    run(original_image, memory, cpu, {fields['continue_primary_object_update_loop']}, limit=130)
    assert get(memory, fields['free_object_count'], 2) == free-int(accepted)
    assert get(memory, fields['free_object_stack_cursor']) == FREE+(0 if accepted else 4)
    assert get(memory, OBJ+36, 2) == (100 if accepted else next_counter)
    assert memory[OBJ+43] == (next_remaining-1 if accepted else next_remaining)
    if not accepted:
        assert (memory[OBJ+3], memory[OBJ+31]) == oscillator(variant, 1)
        assert bytes(memory[CHILD:CHILD+68]) == expected
        return
    assert memory[OBJ+3] == variant and memory[OBJ+31] == 255
    assert memory[OBJ+28] == 130 and memory[OBJ+42] == 38 and get(memory, OBJ+60) == CHILD
    put(expected, 0, 38, 2); expected[2] &= ~16
    expected[3] = 0; expected[28] = 130; expected[29] = 4; expected[30] = 255; expected[42] = 38
    for offset in [4, 12]: expected[offset:offset+4] = bytes(memory[OBJ+offset:OBJ+offset+4])
    put(expected, 8, (-60)&0xFFFFFFFF); put(expected, 18, 1024, 2)
    scale = get(memory, fields['object_default_motion_words']+76, 2)
    for offset, value in [(32, scale), (36, 1), (38, 1), (46, 65474)]: put(expected, offset, value, 2)
    sine = get(memory, get(memory, fields['sine_lookup_pointer'])+2048, 2)
    cosine = get(memory, get(memory, fields['cosine_lookup_pointer'])+2048, 2)
    vx, vz = (-project(scale, sine))&65535, project(scale, cosine)&65535
    put(expected, 44, vx, 2); put(expected, 48, vz, 2); put(expected, 60, OBJ)
    assert bytes(memory[CHILD:CHILD+68]) == expected
    # The next body overwrites the child's exclusion from type38 to type64.
    cpu = state(memory, 0x932E); cpu.a[0] = CHILD
    run(original_image, memory, cpu, {fields['continue_primary_object_update_loop']}, limit=40)
    assert memory[CHILD+42] == 64 and memory[OBJ+42] == 38
    assert get(memory, CHILD+36, 2) == get(memory, CHILD+38, 2) == 1
    assert get(memory, CHILD+8) == (-122)&0xFFFFFFFF and get(memory, CHILD+46, 2) == 65478
    assert get(memory, CHILD+4) == (get(expected, 4)+signed16(vx))&65535
    assert get(memory, CHILD+12) == (get(expected, 12)+signed16(vz))&65535


@pytest.mark.parametrize('variant', [0, 1, 8, 9, 10, 255])
@pytest.mark.parametrize('step', [0, 1, 255])
def test_animation_writes_before_turn_tests_without_general_clamps(original_image, memory, fields, variant, step):
    setup(original_image, memory, fields, counter=2, variant=variant, step=step)
    cpu = state(memory, 0xA1C4); cpu.a[0] = OBJ
    run(original_image, memory, cpu, {fields['continue_primary_object_update_loop']}, limit=20)
    assert (memory[OBJ+3], memory[OBJ+31]) == oscillator(variant, step)


def test_initializer_update_slice_emits_three_then_stops_without_other_writers(original_image, memory, fields):
    setup(original_image, memory, fields, variant=0)
    for index in range(3):
        address = CHILD+128*index
        memory[address:address+68] = b'\0'*68
        put(memory, FREE+4*index, address)
    put(memory, fields['free_object_stack_cursor'], FREE+12)
    put(memory, fields['free_object_count'], 40, 2)
    put(memory, APP+0x60, 0x12345678); put(memory, APP+0x64, 0xABCDEF01)
    cpu = state(memory, 0x18626); cpu.a[0] = OBJ
    run(original_image, memory, cpu, {RETURN}, limit=40)
    assert get(memory, OBJ+36, 2) == 1 and memory[OBJ+43] == 3 and memory[OBJ+31] == 1
    variants = {memory[OBJ+3]}; events = []; old_free = 40
    for invocation in range(384):
        cpu = state(memory, 0xA1C4); cpu.a[0] = OBJ
        run(original_image, memory, cpu, {fields['continue_primary_object_update_loop']}, limit=130)
        variants.add(memory[OBJ+3])
        free = get(memory, fields['free_object_count'], 2)
        if free != old_free: events.append(invocation+1)
        old_free = free
    assert variants == set(range(10)) and events == [10, 119, 228]
    assert get(memory, OBJ+36, 2) == 0 and memory[OBJ+43] == 0
    assert get(memory, fields['free_object_count'], 2) == 37
    assert get(memory, fields['free_object_stack_cursor']) == FREE
    assert get(memory, OBJ+60) == CHILD
    assert all(get(memory, CHILD+128*i, 2) == 38 and
        get(memory, CHILD+128*i+60) == OBJ for i in range(3))


@pytest.mark.parametrize('y,velocity', [(-60,-62), (-1000,62), (-1000,66), (-40,0),
    (-41,0), (2147483647,32767), (-2147483648,-1), (-100000,32764)])
def test_diamond_ballistic_body_keeps_unused_words_and_exact_velocity_turnaround(original_image, memory, fields, y, velocity):
    setup(original_image, memory, fields)
    put(memory, OBJ+8, y&0xFFFFFFFF); put(memory, OBJ+46, velocity&65535, 2)
    put(memory, OBJ+44, 65535, 2); put(memory, OBJ+48, 32768, 2)
    put(memory, OBJ+18, 65530, 2)
    before = bytes(memory[OBJ:OBJ+68]); next_y = (y+velocity)&0xFFFFFFFF
    if signed32(next_y) >= -40: next_y, next_velocity = (-60)&0xFFFFFFFF, 65474
    else:
        next_velocity = (velocity+4)&65535
        if next_velocity == 66: next_velocity = 65474
    cpu = state(memory, 0x932E); cpu.a[0] = OBJ
    run(original_image, memory, cpu, {fields['continue_primary_object_update_loop']}, limit=40)
    assert get(memory, OBJ+18, 2) == 10 and memory[OBJ+42] == 64
    assert get(memory, OBJ+8) == next_y and get(memory, OBJ+46, 2) == next_velocity
    assert bytes(memory[OBJ+36:OBJ+40]) == before[36:40]
