"""Positive original-routine alias witnesses; no gameplay reachability claim.

Inputs deliberately include out-of-prefix rows/counts/full storage. These cases
refute unconditional dead/write-only claims; they do not invent normal callers.
"""
import pytest
from tests.test_pandora_state_transitions import BASE, cpu_fixture as cpu_fixture

APP = 0x39fc


@pytest.mark.parametrize('offset', [0x190, 0x2d4, 0x368])
def test_original_unchecked_row_lookup_can_read_each_questioned_slot(cpu_fixture, offset):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = APP
    write(APP + 0x1d8, 0x70000)
    write(APP + offset, 0x1234, 2)
    cpu.d[0], cpu.d[1] = 0, offset // 2
    run(0x6dae)
    assert cpu.a[1] == 0x71234


@pytest.mark.parametrize('entry, bank', [(0x6108, 0x78000), (0x6126, 0x70000)])
def test_masked_text_y25_reads_startup_pointer_high_word(cpu_fixture, entry, bank):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = APP
    write(APP + 0x190, 0x12345678)
    write(APP + 0x1d4, 0x78000)
    cpu.d[0], cpu.d[1] = 0, 25
    run(entry)
    assert cpu.a[0] == bank + 0x1234
    assert read(APP + 0x190) == 0x12345678


@pytest.mark.parametrize('first_zero', [0, 63, 0x368-0x2da])
def test_deposit_scan_has_no_64_byte_guard_and_can_write_callback_byte(cpu_fixture, first_zero):
    cpu, memory, schemas, read, write, run = cpu_fixture
    start = APP + 0x2da
    memory[start:APP+0x36c] = b'\x11' * (0x36c-0x2da)
    write(start + first_zero, 0, 1)
    cpu.a[6], cpu.a[0], cpu.d[0] = APP, start, 0x7f
    run(0x89da, stop=0x89e0, budget=512)
    assert read(start + first_zero, 1) == 0x7f
    assert read(APP+0x368, 1) == (0x7f if first_zero == 0x368-0x2da else 0x11)


def test_submitted_name_index15_aliases_blitter_callback(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6], cpu.a[0], cpu.d[2] = APP, BASE+0x6d6, 15*4
    write(APP+0x368, 0)
    # Starts after name resolution, with its original output register/frame
    # modeled explicitly. It is not evidence that original count reaches15.
    run(0x9d3e, stop=0x9d46)
    assert read(APP+0x368) == BASE+0x6d6


def test_changed_candidate_mirror_and_reset_are_the_original_direct_writers(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = APP
    candidate = cpu.a[5]
    run(0x8362, stop=0x836a)
    assert read(APP+0x19e) == read(APP+0x2d4) == candidate
    run(0x9fae, stop=0x9fb6)
    assert read(APP+0x19e) == read(APP+0x2d4) == 0


@pytest.mark.parametrize('base,entry,stop,display', [
    (0x196,0x2ac2,0x2ad0,False),
    (0x19a,0x2b38,0x2b46,False),
    (0x2ba,0x2a7c,0x2a86,True),
])
@pytest.mark.parametrize('target', [None,0x2d4,0x368])
def test_inventory_cursor_indices_can_alias_questioned_slots_outside_four_rows(cpu_fixture, base, entry, stop, display, target):
    cpu, memory, schemas, read, write, run = cpu_fixture
    offset=base+3 if target is None else target
    cpu.a[6],cpu.a[4],cpu.d[0],cpu.d[2]=APP,0x80000,offset-base,0x7f
    write(0x80000+0x46,0x7f,1)
    write(APP+0x2d4,0x11223344);write(APP+0x368,0x11223344)
    write(APP+offset,0x11,1)
    run(entry,stop=stop)
    assert read(APP+offset,1)==0x7f
    if not display:assert read(0x80000+0x46,1)==0x11
    if target is None:
        assert read(APP+0x2d4)==read(APP+0x368)==0x11223344
