"""Original CPU mask contracts; no chipset, image grouping or lifetime claim."""

import json
from pathlib import Path

import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture


INVENTORY = json.loads(
    (Path(__file__).resolve().parents[1]
     / 'docs/validation/pandora-planar-mask-inputs.json').read_text()
)


@pytest.mark.parametrize('bank', INVENTORY['banks'], ids=lambda bank: bank['source_name'])
def test_original_constant_packet_generates_exact_mask_words_and_cursor_extents(cpu_fixture, bank):
    cpu, memory, schemas, read, write, run = cpu_fixture
    # Execute the actual LEA/count/BSR packet before checking its contract.
    first_packet_instruction = int(bank['evidence_refs'][0].split(':')[1], 16)
    run(first_packet_instruction, stop=0x7730)
    source = BASE + bank['source_start']
    end = BASE + bank['source_end']
    mask = bank['mask_runtime_start']
    mask_end = mask + bank['mask_bytes']
    assert (cpu.a[0], cpu.a[1]) == (source, mask)
    assert (cpu.d[6] & 0xFFFF, cpu.d[7] & 0xFFFF) == (
        bank['last_group_index'], bank['cells_per_group'])
    assert not (source < mask_end and mask < end)
    original = bytes(memory[source:end])
    expected = b''.join(
        (int.from_bytes(original[i:i+2], 'big')
         | int.from_bytes(original[i+2:i+4], 'big')
         | int.from_bytes(original[i+4:i+6], 'big')
         | int.from_bytes(original[i+6:i+8], 'big')).to_bytes(2, 'big')
        for i in range(0, len(original), 8)
    )
    memory[mask-2:mask_end+2] = b'\xA5' * (bank['mask_bytes'] + 4)
    run(0x7730, budget=15000)
    assert bytes(memory[mask:mask_end]) == expected
    assert bytes(memory[mask-2:mask]) == bytes(memory[mask_end:mask_end+2]) == b'\xA5\xA5'
    assert bytes(memory[source:end]) == original
    assert (cpu.a[0], cpu.a[1]) == (end, mask_end)
    assert cpu.d[6] & 0xFFFF == 0xFFFF
    assert cpu.d[7] & 0xFFFF == bank['cells_per_group'] - 1


def test_original_inner_loop_preserves_cursors_and_saved_full_registers(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    source, mask = 0x81000, 0x81200
    cells = [(0x8000, 0x4000, 0x2000, 0x1000),
             (0, 0, 0, 0), (0x1234, 0x4321, 0xAAAA, 0x5555)]
    for index, planes in enumerate(cells):
        for plane, value in enumerate(planes):
            write(source + index * 8 + plane * 2, value, 2)
    cpu.a[0], cpu.a[1] = source, mask
    cpu.d[0], cpu.d[7] = 0x89ABCDEF, 0x76540002
    before = (cpu.a[0], cpu.a[1], cpu.d[0], cpu.d[7])
    memory[mask-2:mask+8] = b'\xA5' * 10
    run(0x7718)
    assert (cpu.a[0], cpu.a[1], cpu.d[0], cpu.d[7]) == before
    assert [read(mask + 2 * i, 2) for i in range(3)] == [0xF000, 0, 0xFFFF]
    assert bytes(memory[mask-2:mask]) == bytes(memory[mask+6:mask+8]) == b'\xA5\xA5'
