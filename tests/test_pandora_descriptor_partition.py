"""Original descriptor partition/sort, with bounded explicit input families."""
from collections import Counter

import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture

SOURCE = BASE + 0x310E
COPY = BASE + 0x31AA
DEFERRED = BASE + 0x322A


@pytest.mark.parametrize('case', ['original', 'mixed', 'all_deferred', 'one_deferred'])
def test_partition_preserves_32_descriptors_and_sorts_only_deferred(cpu_fixture, case):
    cpu, memory, schemas, read, write, run = cpu_fixture
    descriptors = [read(SOURCE + 4*i) for i in range(32)]
    flag_offset = schemas['world_position_state_record']['world_object_flags']
    states = [read(p) for p in descriptors]
    if case != 'original':
        for i, (descriptor, state) in enumerate(zip(descriptors, states)):
            flags = ([0x40, 0x80, 0, 0xC0][i % 4] if case == 'mixed'
                     else 0 if case == 'all_deferred' or i == 0 else 0x40)
            write(state + flag_offset, flags, 1)
            # Exercise unsigned comparison, duplicate keys, and reversed order.
            write(descriptor + 6, [0xFFFF, 0x8000, 0, 19, 19, 7][i % 6], 2)
    front, back, middle = [], [], []
    for descriptor, state in zip(descriptors, states):
        flags = read(state + flag_offset, 1)
        (front if flags & 0x40 else back if flags & 0x80 else middle).append(descriptor)
    assert middle  # Empty middle has a separate, unproven lifetime precondition.
    original_source = bytes(memory[SOURCE:SOURCE+128])
    steps = run(0x849A, budget=20000)
    actual = [read(SOURCE + 4*i) for i in range(32)]
    assert Counter(actual) == Counter(descriptors)
    assert actual[:len(front)] == front
    if back:
        assert actual[-len(back):] == list(reversed(back))
    selected = actual[len(front):32-len(back)]
    assert Counter(selected) == Counter(middle)
    assert [read(p+6, 2) for p in selected] == sorted(read(p+6, 2) for p in middle)
    assert bytes(memory[COPY:COPY+128]) == original_source
    assert [read(DEFERRED+4*i) for i in range(len(middle))] == middle
    assert steps < 20000
