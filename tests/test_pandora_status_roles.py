"""Original bounded status/deposit paths; no UI reachability or admission claim."""
from __future__ import annotations

import re
import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture

APP = 0x39FC


@pytest.mark.parametrize('text', [b'\0', b'   \0', b'abc\0', b'abc def\0',
    b'  abc  \0', b'a   b  c\0', b'abc\rignored\0', b'a\0ignored\0'])
def test_status_duration_measure_counts_space_runs_plus_one_nonspace_presence(cpu_fixture, text):
    cpu, memory, schemas, read, write, run = cpu_fixture
    start = 0x80000
    memory[start:start+len(text)] = text
    cpu.a[0] = start
    run(0x99AC, budget=1024)
    prefix = re.split(b'[\0\r]', text, maxsplit=1)[0]
    expected = len(re.findall(b' +', prefix)) + bool(prefix.replace(b' ', b''))
    assert cpu.d[0] == expected
    assert cpu.a[0] == start and cpu.a[1] == start+len(prefix)+1
    assert bytes(memory[start:start+len(text)]) == text


def test_status_band_clear_is_1280_bytes_and_stops_at_hit_snapshot(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    memory[0x777FC:0x77D04] = b'\xA5'*(1280+8)
    run(0x9AB2, budget=512)
    assert bytes(memory[0x77800:0x77D00]) == bytes(1280)
    assert bytes(memory[0x777FC:0x77800]) == b'\xA5'*4
    assert bytes(memory[0x77D00:0x77D04]) == b'\xA5'*4
    # Eight 160-byte interleaved raster rows, not a one-plane-only clear.


def test_deposit_reset_extent_preserves_adjacent_modal_selection(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = APP
    memory[APP+0x2D6:APP+0x31E] = b'\xA5'*72
    run(0x9FBE, stop=0x9FCA, budget=128)
    assert bytes(memory[APP+0x2DA:APP+0x31A]) == bytes(64)
    assert bytes(memory[APP+0x2D6:APP+0x2DA]) == b'\xA5'*4
    assert bytes(memory[APP+0x31A:APP+0x31E]) == b'\xA5'*4


@pytest.mark.parametrize('first_zero', [3, 64])
def test_deposit_scan_has_no_64_byte_admission_guard(cpu_fixture, first_zero):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = APP
    start = APP+0x2DA
    memory[start:start+65] = b'\x01'*65
    write(start+first_zero, 0, 1)
    cpu.d[0] = 42
    run(0x89D6, stop=0x89E0, budget=256)
    assert cpu.a[0] == start+first_zero and read(start+first_zero, 1) == 42
    if first_zero == 64:
        assert start+first_zero == APP+0x31A  # Adjacent modal-selection byte.
    # Deliberately bounded prefix with modeled input, not full deposit reachability.
