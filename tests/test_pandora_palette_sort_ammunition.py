"""Bounded original CPU evidence for mutable scratch, RGB words and ammunition.

No full gameplay, interrupt/DMA scheduling, or arbitrary partition bound claim.
"""
from __future__ import annotations

import pytest

from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import resolve_project_paths
from tests.test_pandora_state_transitions import BASE, TARGET, cpu_fixture

APP = 0x39FC


@pytest.fixture
def original(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    slots = {r.symbol: r.offset for r in effective_target_metadata(
        resolve_project_paths(TARGET).target_dir).rsset_layout_regions if r.symbol}
    cpu.a[6] = APP
    return cpu, memory, schemas, read, write, run, slots


def test_palette_clear_and_add_use_exact_16_rgb_word_records(original):
    cpu, memory, schemas, read, write, run, slots = original
    components, palette, increments = BASE+0x3462, BASE+0x34C2, BASE+0x34E2
    memory[components:palette+32] = b'\xA5'*128
    before_low = bytes(memory[components-8:components])
    before_inputs = bytes(memory[increments:increments+40])
    cpu.a[0], cpu.a[1], cpu.a[2], cpu.d[7] = palette, increments, components, 15
    run(0x2640)
    assert memory[components:palette+32] == bytes(128)
    colors = [read(increments+2*i, 2) for i in range(16)]
    for step in range(1, 17):
        run(0x25DE, budget=2048)
        assert [read(components+6*i+2*j, 2) for i in range(16) for j in range(3)] == [
            step*((color >> shift) & 15) for color in colors for shift in (8, 4, 0)]
        assert [read(palette+2*i, 2) for i in range(16)] == [
            sum((step*((color >> shift) & 15)//16) << shift for shift in (8, 4, 0))
            for color in colors]
    assert bytes(memory[components-8:components]) == before_low
    assert bytes(memory[increments:increments+40]) == before_inputs
    assert (cpu.a[0], cpu.a[1], cpu.a[2], cpu.d[7]) == (palette, increments, components, 15)


def test_palette_unpack_accepts_shared_snapshot_input_without_owning_it(original):
    cpu, memory, schemas, read, write, run, slots = original
    colors = [(i*0x137) & 0xFFF for i in range(16)]
    source = b''.join(c.to_bytes(2, 'big') for c in colors)
    memory[0x77FE0:0x78000] = source
    run(0x7190)
    assert cpu.a[0] == BASE+0x34C2 and cpu.a[1] == 0x77FE0 and cpu.a[2] == BASE+0x3462
    run(0x2614)
    assert bytes(memory[BASE+0x34C2:BASE+0x34E2]) == source
    assert [read(BASE+0x3462+2*i, 2) for i in range(48)] == [
        16*((color >> shift) & 15) for color in colors for shift in (8, 4, 0)]
    assert bytes(memory[0x77FE0:0x78000]) == source
    # This leaf call establishes access extents, not snapshot/palette phase exclusion.


@pytest.mark.parametrize('middle_count', [1, 16, 32])
def test_partition_scratch_is_refreshed_and_deferred_prefix_consumed(original, middle_count):
    cpu, memory, schemas, read, write, run, slots = original
    # Use controlled valid descriptor/state records, preserving original CPU code.
    # Non-middle entries split between the original flag-6 and flag-7 branches.
    data = memory[BASE+0x849A:BASE+0x849E]
    assert data[:2] == b'\x41\xfa'
    displacement = int.from_bytes(data[2:4], 'big', signed=True)
    source_start = BASE+0x849C+displacement
    copy, deferred = BASE+0x31AA, BASE+0x322A
    for pass_index in range(2):
        pointers = [0x80000+pass_index*0x2000+0x40*i for i in range(32)]
        middle = []
        for i, descriptor in enumerate(pointers):
            state = descriptor+0x20
            flag = 0 if i < middle_count else (0x40 if i & 1 else 0x80)
            write(source_start+4*i, descriptor)
            write(descriptor, state)
            write(descriptor+6, (i*7) % 32, 2)
            write(state+0x19, flag, 1)
            if not flag: middle.append(descriptor)
        memory[copy:copy+128] = b'\xA5'*128
        memory[deferred:deferred+128] = b'\x5A'*128
        before_high = bytes(memory[deferred+128:deferred+136])
        run(0x849A, stop=0x84BC, budget=1024)
        # The current simulator zero-extends MOVEQ #$FF, unlike the manual's
        # signed byte transfer. Start this bounded suffix with its specified
        # architectural D5 input; do not claim whole-routine simulation.
        cpu.d[5] = 0xFFFFFFFF
        run(0x84BE, stop=0x84E8, budget=1024)
        assert [read(copy+4*i) for i in range(32)] == pointers
        assert [read(deferred+4*i) for i in range(middle_count)] == middle
        assert bytes(memory[deferred+4*middle_count:deferred+128]) == b'\x5A'*(128-4*middle_count)
        assert cpu.a[5] == deferred+4*middle_count and cpu.d[5] & 0xFFFF == middle_count-1
        # Continue the original copy-back and sort suffix without replaying the producer.
        # run() resets only PC/stack; the partition's registers stay live.
        run(0x84E8, budget=4096)
        assert bytes(memory[deferred+128:deferred+136]) == before_high
        assert [read(copy+4*i) for i in range(32)] == pointers
        first = [pointers[i] for i in range(middle_count, 32) if i & 1]
        last = [pointers[i] for i in range(middle_count, 32) if not i & 1][::-1]
        assert [read(source_start+4*i) for i in range(32)] == (
            first + sorted(middle, key=lambda address: read(address+6, 2)) + last)


def test_empty_deferred_partition_has_no_guard_before_first_predecrement(original):
    cpu, memory, schemas, read, write, run, slots = original
    displacement = int.from_bytes(memory[BASE+0x849C:BASE+0x849E], 'big', signed=True)
    source_start = BASE+0x849C+displacement
    for i in range(32):
        descriptor = 0x80000+0x40*i
        write(source_start+4*i, descriptor)
        write(descriptor, descriptor+0x20)
        write(descriptor+0x20+0x19, 0x40, 1)
    run(0x849A, stop=0x84BC, budget=1024)
    cpu.d[5] = 0xFFFFFFFF  # Explicit entry condition; see MOVEQ limitation above.
    run(0x84BE, stop=0x84EA, budget=1024)
    assert cpu.a[5] == BASE+0x322A and cpu.d[5] & 0xFFFF == 0xFFFF
    assert read(BASE+0x84EA, 2) == 0x22E5  # move.l -(a5),(a1)+
    # Stop before that underflowing read/write. No claim of an all-input safe bound.


@pytest.mark.parametrize('item,initial', [(18, 5), (19, 1)])
def test_ammunition_is_initialized_and_consumed_only_on_a_new_fire_press(original, item, initial):
    cpu, memory, schemas, read, write, run, slots = original
    player = BASE+0x4C322
    write(player+schemas['world_object_shared_prefix']['world_object_flags'], 0, 1)
    write(player+schemas['world_object_shared_prefix']['selected_item_id'], item, 1)
    run(0x9F26, stop=0x9F32)
    assert memory[BASE+0x924E:BASE+0x9250] == b'\x05\x01'
    write(APP+slots['app_ui_flags'], 0, 1)
    write(APP+slots['app_input_fire_pressed_ff'], 0xFF, 1)
    write(APP+0x31B, 0, 1)
    run(0x9250, stop=0x92BA)
    assert read(BASE+0x924E+item-18, 1) == initial-1
    assert read(APP+0x31B, 1) == 1
    after = bytes(memory[BASE+0x924E:BASE+0x9250])
    for _ in range(3):
        run(0x9250)  # Held fire: no repeat decrement and no audio/ray suffix.
        assert bytes(memory[BASE+0x924E:BASE+0x9250]) == after
    write(APP+slots['app_input_fire_pressed_ff'], 0, 1)
    run(0x9250)
    assert read(APP+0x31B, 1) == 0
    assert bytes(memory[BASE+0x924E:BASE+0x9250]) == after


@pytest.mark.parametrize('item,charge', [(18, 0), (19, 0), (17, 5), (20, 5)])
def test_empty_or_unselected_weapon_does_not_consume_ammunition(original, item, charge):
    cpu, memory, schemas, read, write, run, slots = original
    player = BASE+0x4C322
    write(player+schemas['world_object_shared_prefix']['world_object_flags'], 0, 1)
    write(player+schemas['world_object_shared_prefix']['selected_item_id'], item, 1)
    memory[BASE+0x924E:BASE+0x9250] = bytes([charge, charge])
    write(APP+slots['app_input_fire_pressed_ff'], 0xFF, 1)
    before = bytes(memory[BASE+0x924E:BASE+0x9250])
    run(0x9250)
    assert bytes(memory[BASE+0x924E:BASE+0x9250]) == before
    assert read(APP+0x31B, 1) == 1
