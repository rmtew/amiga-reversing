"""Original projector report selection for the 56 stored rebuild slots.

Supplied local inputs establish part/body selection and signed flag gates,
not a global cursor bound, rebuilt-station lifetime or gameplay completion.
"""
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, INPUT

NAMES = ['projector_rebuild_cursor', 'projector_part_message_pointers',
         'projector_body_message_pointers', 'projector_message_egron_projector_base',
         'projector_base_report_selected_flag', 'station_report_primary_message',
         'station_report_secondary_message']


@pytest.fixture(scope='module')
def fields(tmp_path_factory, original_image):
    target = Path(__file__).resolve().parents[1] / 'targets/amiga_raw_starglider2_game'
    folder = tmp_path_factory.mktemp('projector-reports')
    source, output = folder / 'fields.s', folder / 'fields.raw'
    source.write_text((target / 'starglider2_game.s').read_text() + '\n dc.l ' + ','.join(NAMES) + '\n')
    result = subprocess.run([str(target.parents[1] / 'tools/vasmm68k_mot.exe'), '-quiet', '-m68000',
        '-no-opt', '-Fbin', '-I' + str(target / 'includes'), '-o', str(output), str(source)],
        cwd=target, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    raw = output.read_bytes()
    assert raw[:-4 * len(NAMES)] == original_image[0]
    values = dict(zip(NAMES, struct.unpack('>' + 'I' * len(NAMES), raw[-4 * len(NAMES):])))
    for name in ['projector_rebuild_cursor', 'station_report_primary_message', 'station_report_secondary_message']:
        values[name] += APP
    return values


def table(memory, fields, name, index):
    return get(memory, fields[name] + 4 * index)


@pytest.mark.parametrize('initial', [0, 1, 55])
@pytest.mark.parametrize('missing_at', [1, 2, 3, 4, None])
def test_backward_search_wraps_and_tests_at_most_four_slots(original_image, memory, fields, initial, missing_at):
    memory[INPUT:INPUT + 56] = b'\xFF' * 56
    if missing_at is not None:
        memory[INPUT + (initial - missing_at) % 56] = 0
    put(memory, fields['projector_rebuild_cursor'], initial, 2)
    cpu = state(memory, 0x34CE0)
    cpu.a[0], cpu.d[7] = INPUT, 3
    run(original_image, memory, cpu, {0x34CFE, 0x34E78})
    attempts = missing_at if missing_at is not None else 4
    assert get(memory, fields['projector_rebuild_cursor'], 2) == (initial - attempts) % 56
    assert cpu.pc == (0x34CFE if missing_at is not None else 0x34E78)
    assert cpu.d[7] & 0xFFFF == (4 - attempts if missing_at is not None else 0xFFFF)


@pytest.mark.parametrize('index', range(56))
def test_part_selection_marks_one_slot_and_only_base_parts_set_the_sign(original_image, memory, fields, index):
    memory[INPUT:INPUT + 56] = bytes(56)
    put(memory, fields['projector_rebuild_cursor'], index, 2)
    memory[fields['projector_base_report_selected_flag']] = 0x5A
    cpu = state(memory, 0x34CFE)
    cpu.a[0], cpu.d[0] = INPUT, index
    run(original_image, memory, cpu, {0x34D28})
    assert bytes(memory[INPUT:INPUT + 56]) == bytes(index) + b'\xFF' + bytes(55 - index)
    assert cpu.a[1] == table(memory, fields, 'projector_part_message_pointers', index)
    assert cpu.a[2] == fields['projector_message_egron_projector_base']
    assert memory[fields['projector_base_report_selected_flag']] == (0xFF if index % 8 == 0 else 0)
    assert cpu.d[0] & 0xFFFF == index * 4


@pytest.mark.parametrize('index', range(56))
def test_nonnegative_flag_copies_both_reports_without_calling_display(original_image, memory, fields, index):
    put(memory, fields['projector_rebuild_cursor'], index, 2)
    memory[fields['projector_base_report_selected_flag']] = 0x7F
    cpu = state(memory, 0x34D44)
    old_sp = cpu.a[7]
    run(original_image, memory, cpu, {0x34D88})
    primary = table(memory, fields, 'projector_part_message_pointers', index)
    secondary = table(memory, fields, 'projector_body_message_pointers', index)
    assert get(memory, fields['station_report_primary_message']) == primary
    assert get(memory, fields['station_report_secondary_message']) == secondary
    assert cpu.a[7] == old_sp and cpu.a[1] == secondary
    # Stored order is seven bodies, each with the same eight part names.
    assert primary == table(memory, fields, 'projector_part_message_pointers', index % 8)
    assert secondary == table(memory, fields, 'projector_body_message_pointers', (index // 8) * 8)


@pytest.mark.parametrize('flag', [0x80, 0xFF])
def test_negative_flag_calls_enqueue_after_primary_before_secondary(original_image, memory, fields, flag):
    put(memory, fields['projector_rebuild_cursor'], 9, 2)
    memory[fields['projector_base_report_selected_flag']] = flag
    put(memory, fields['station_report_secondary_message'], 0x12345678)
    cpu = state(memory, 0x34D44)
    old_sp = cpu.a[7]
    # Stop at the original BSR: no helper injection and no display assertion.
    run(original_image, memory, cpu, {0x34D60})
    assert get(memory, fields['station_report_primary_message']) == table(memory, fields, 'projector_part_message_pointers', 9)
    assert get(memory, fields['station_report_secondary_message']) == 0x12345678
    assert cpu.a[7] == old_sp
