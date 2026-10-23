"""Original proximity prefix, isolated from sorting, callbacks and prompt rendering."""
from __future__ import annotations

import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture

pytestmark = pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
APP, PLAYER, TABLE = 0x39FC, 0x5C322, BASE+0x300A
FLAGS, NEAREST, DISTANCE = APP+0x2A6, APP+0x19E, APP+0x356


def scene(fixture, distances, *, previous=None, cooldown=0, object_flags=4):
    cpu, memory, schemas, read, write, run = fixture
    obj = schemas['world_object_shared_prefix']
    cpu.a[6] = APP
    write(PLAYER+obj['world_x'], 1000, 2)
    write(PLAYER+obj['world_y'], 1000, 2)
    addresses = [0x80000+0x100*i for i in range(len(distances))]
    for i, (address, distance) in enumerate(zip(addresses, distances)):
        write(TABLE+4*i, address)
        write(address+obj['position_descriptor_ptr'], address+0x80)
        write(address+obj['world_x'], 1000+distance, 2)
        write(address+obj['world_y'], 1000, 2)
        write(address+obj['world_object_flags'], object_flags, 1)
        write(address+obj['context_prompt_cooldown'], cooldown, 2)
    write(TABLE+4*len(addresses), 0)
    write(NEAREST, addresses[previous] if previous is not None else 0)
    write(DISTANCE, 0x7777, 2)
    return addresses


@pytest.mark.parametrize('cooldown,distances,previous,winner,threshold', [
    (0, [10, 5], None, 0, 0),  # Changed first candidate replaces the threshold.
    (0, [10, 5], 0, 1, 0),     # Stable first candidate retains distance until next change.
    (60, [10, 20], None, 1, 59),  # A farther object can replace a nearer one.
    (0, [10, 10], 0, 0, 10),   # Strict distance tie when the pointer is unchanged.
    (60, [10, 10], None, 1, 59),  # A changed pointer destroys that tie guarantee.
])
def test_changed_candidate_reuses_threshold_register(cpu_fixture, cooldown, distances, previous, winner, threshold):
    cpu, memory, schemas, read, write, run = cpu_fixture
    addresses = scene(cpu_fixture, distances, previous=previous, cooldown=cooldown)
    run(0x82F0, stop=0x83AE, budget=512)
    assert read(NEAREST) == addresses[winner]
    assert read(DISTANCE, 2) == distances[winner]
    assert cpu.d[0] & 0xFFFF == threshold
    assert not read(FLAGS, 1) & 4
    obj = schemas['world_object_shared_prefix']
    for address, distance in zip(addresses, distances):
        assert read(address+obj['proximity_distance'], 2) == distance
        assert read(address+0x80+4, 2) == 1000+distance
        assert read(address+0x80+6, 2) == 1000


def test_scan_sets_every_improvement_flag_not_just_final_pointer(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    addresses = scene(cpu_fixture, [10, 20], cooldown=60)
    run(0x82F0, stop=0x83AE, budget=512)
    flag = schemas['world_object_shared_prefix']['world_object_flags']
    assert read(NEAREST) == addresses[1]
    assert all(read(address+flag, 1) & 32 for address in addresses)
    assert all(read(address+schemas['world_object_shared_prefix']['context_prompt_cooldown'], 2) == 59 for address in addresses)


@pytest.mark.parametrize('distance', [90, 91])
def test_initial_threshold_is_exclusive_and_stale_pointer_survives_prefix(cpu_fixture, distance):
    cpu, memory, schemas, read, write, run = cpu_fixture
    addresses = scene(cpu_fixture, [distance], previous=0, object_flags=36)
    run(0x82F0, stop=0x83AE, budget=512)
    assert read(FLAGS, 1) & 4
    assert read(NEAREST) == addresses[0] and read(DISTANCE, 2) == 0x7777
    assert not read(addresses[0]+schemas['world_object_shared_prefix']['world_object_flags'], 1) & 32


@pytest.mark.parametrize('object_flags', [0, 2])
def test_first_visit_latches_even_without_a_message_or_when_inactive(cpu_fixture, object_flags):
    cpu, memory, schemas, read, write, run = cpu_fixture
    addresses = scene(cpu_fixture, [10], object_flags=object_flags)
    run(0x82F0, stop=0x83AE, budget=512)
    assert read(addresses[0]+schemas['world_object_shared_prefix']['world_object_flags'], 1) & 4
    assert read(FLAGS, 1) & 2
    assert cpu.a[7] == 0x9000  # No queue call in either bounded case.


def test_player_descriptor_is_synced_before_self_exclusion(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    scene(cpu_fixture, [10])
    obj = schemas['world_object_shared_prefix']
    descriptor = read(PLAYER+obj['position_descriptor_ptr'])
    assert descriptor
    write(TABLE, PLAYER)
    write(TABLE+4, 0)
    write(PLAYER+obj['proximity_distance'], 0x1234, 2)
    write(PLAYER+obj['world_object_flags'], 32, 1)
    run(0x82F0, stop=0x83AE, budget=512)
    assert read(descriptor+4, 2) == read(descriptor+6, 2) == 1000
    assert read(PLAYER+obj['proximity_distance'], 2) == 0x1234
    assert read(PLAYER+obj['world_object_flags'], 1) == 32
    assert read(FLAGS, 1) & 4


def test_word_arithmetic_can_admit_wrapped_zero_distance(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    addresses = scene(cpu_fixture, [0x8000])
    obj = schemas['world_object_shared_prefix']
    write(addresses[0]+obj['world_y'], 1000+0x8000, 2)
    run(0x82F0, stop=0x83AE, budget=512)
    assert read(NEAREST) == addresses[0]
    assert read(DISTANCE, 2) == read(addresses[0]+obj['proximity_distance'], 2) == 0
