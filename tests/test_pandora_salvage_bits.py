"""Original bit helper and bounded salvage-count consumers, without UI reachability."""
from __future__ import annotations

import pytest

from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import resolve_project_paths
from tests.test_pandora_state_transitions import BASE, TARGET, cpu_fixture

APP = 0x39FC
SET_IDS = {0x17, 0x18, 0x19, 0x1B, 0x1C, 0x68, 0x69, 0x6B, 0x6C, 0x6D, 0x6F, 0x70}


def test_original_bit_helper_matches_every_stored_salvage_bit(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    before = bytes(memory[BASE+0xA813:BASE+0xA822])
    assert before.hex() == '000001d8000000000000000000dd80'
    for item in range(120):
        cpu.a[0] = BASE+0xA813
        cpu.d[0], cpu.d[1] = item, 0x12345678
        run(0x5FFE)
        assert (cpu.sr & 4 == 0) == (item in SET_IDS)
        assert cpu.d[0] == item and cpu.d[1] == 0x12345678
        assert cpu.a[0] == BASE+0xA813
    assert bytes(memory[BASE+0xA813:BASE+0xA822]) == before


@pytest.mark.parametrize('item', [0, 0x17, 0x1A, 0x68, 0x70, 0x71])
def test_terminal_deposit_suffix_counts_only_eligible_ids(cpu_fixture, item):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6], cpu.d[0] = APP, item
    # app_salvage_item_count is the existing durable slot; avoid a second offset.
    slots = {s.symbol: s.offset for s in effective_target_metadata(resolve_project_paths(TARGET).target_dir).rsset_layout_regions}
    count = APP+slots['app_salvage_item_count']
    write(count, 7, 1)
    run(0x89EA, stop=0x89FA)
    assert read(count, 1) == 7+(item in SET_IDS)
    assert cpu.d[0] == item


@pytest.mark.parametrize('items', [(0, 0, 0, 0), (0x17, 0x18, 0x1A, 0x70), (0x17, 0x17, 0x17, 0x17)])
def test_outcome_counts_four_carried_slots_including_duplicates(cpu_fixture, items):
    cpu, memory, schemas, read, write, run = cpu_fixture
    slots = {s.symbol: s.offset for s in effective_target_metadata(resolve_project_paths(TARGET).target_dir).rsset_layout_regions}
    cpu.a[6] = APP
    carried, count = APP+slots['app_carried_item_ids'], APP+slots['app_salvage_item_count']
    memory[carried:carried+5] = bytes(items)+b'\x17'
    write(count, 3, 1)
    run(0x4C9E2, stop=0x4CA02)
    assert read(count, 1) == 3+sum(x in SET_IDS for x in items)
    assert cpu.a[1] == carried+4 and read(carried+4, 1) == 0x17
