"""Original CPU address producers and packet extents, without DMA scheduling."""
from __future__ import annotations

import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_overlay_pipeline import overlay_fixture

pytestmark = pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
APP = 0x39FC


def fill_rows(cpu, memory, run):
    cpu.a[6] = APP
    memory[APP:APP+402] = b'\xA5' * 402
    run(0x9EBE, stop=0x9ED4, budget=2048)
    assert memory[APP+400:APP+402] == b'\xA5\xA5'


def test_original_row_producer_writes_exactly_200_word_offsets(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    fill_rows(cpu, memory, run)
    assert [read(APP+2*i, 2) for i in range(200)] == [160*i for i in range(200)]
    assert cpu.d[1] == 400 and cpu.d[7] & 0xFFFF == 0xFFFF


@pytest.mark.parametrize('x,y', [(0, 0), (39, 24), (24, 17), (63, 31), (0xFFFF, 0xFFFF)])
def test_text_origins_distinguish_front_buffer_from_fixed_overlay(cpu_fixture, x, y):
    cpu, memory, schemas, read, write, run = cpu_fixture
    fill_rows(cpu, memory, run)
    # Out-of-table y values read adjacent workspace; no clamp is invented.
    row_index = (y & 31)*8
    offset = 160*row_index if row_index < 200 else 0x1234
    if row_index >= 200:
        write(APP+2*row_index, offset, 2)
    write(APP+0x1D4, 0x78000)
    for entry, base in [(0x6108, 0x78000), (0x6126, 0x70000)]:
        cpu.d[0], cpu.d[1] = x, y
        run(entry)
        expected = base+offset+(x & 63)
        assert cpu.a[0] == expected == read(APP+0x1E4)


def test_front_back_exchange_changes_selected_world_bank_not_snapshot_or_ui(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = APP
    write(APP+0x1D4, 0x78000)
    write(APP+0x1D8, 0x70000)
    write(APP+0x1DC, 0x78000)
    write(APP+0x27B, 0xFF, 1)
    memory[0x77D00:0x78000] = b'\xA5'*0x300
    for front, back in [(0x70000, 0x78000), (0x78000, 0x70000)]:
        run(0x5A8, stop=0x5C2)
        assert read(APP+0x1D4) == read(APP+0x1DC) == front
        assert read(APP+0x1D8) == back
        assert read(APP+0x27B, 1) == 0xDF
        assert memory[0x77D00:0x78000] == b'\xA5'*0x300


@pytest.mark.parametrize('front', [0x70000, 0x78000])
def test_vblank_prefix_installs_four_interleaved_plane_pointers(overlay_fixture, front):
    cpu, memory, fields, read, write, run, hw, slots, queue, make_descriptor = overlay_fixture
    cpu.a[6] = APP
    cpu.a[5] = hw['INTREQR']-0x1E
    write(APP+slots['app_display_bitplane_base'], front)
    # Stop before palette, sprites, audio and keyboard; no full ISR claim.
    run(0x94E, stop=0x97C)
    assert [read(hw[f'BPL{i+1}PTH']) for i in range(4)] == [front+40*i for i in range(4)]


@pytest.mark.parametrize('descriptor,buffer,extent', [(0x335A, 0x77D00, 0x300), (0x33DE, 0x7F0, 0x900)])
def test_initialized_snapshot_packets_use_packed_storage_outside_screen_fetch(overlay_fixture, descriptor, buffer, extent):
    cpu, memory, fields, read, write, run, hw, slots, queue, make_descriptor = overlay_fixture
    fill_rows(cpu, memory, run)
    address = BASE+descriptor
    cpu.a[5] = address
    x, y = read(address, 1), read(address+1, 1)
    width, height = read(address+2, 1), read(address+3, 1)
    words, rows = (width+1)//2, height*32
    assert extent == 2*words*rows
    run(0x6332)
    assert read(hw['BLTAPTH']) == 0x70000+1280*y+x
    assert read(hw['BLTDPTH']) == buffer
    assert read(hw['BLTDMOD'], 2) == 0
    assert read(hw['BLTSIZE'], 2) == (rows<<6) | words
    screen_end = read(hw['BLTAPTH'])+(rows-1)*40+2*words
    assert screen_end <= 0x77D00
    run(0x639A)
    assert read(hw['BLTAPTH']) == buffer
    assert read(hw['BLTDPTH']) == 0x70000+1280*y+x
    assert read(hw['BLTAMOD'], 2) == 0
    assert read(address+fields['state_flags'], 1) & 0xA0 == 0
    # Capturing/restoring merely programs DMA in this memory-only fixture.
    assert memory[buffer:buffer+extent] == bytes(extent)


def test_seeded_clear_reuses_hit_snapshot_address_but_does_not_wait_after_start(overlay_fixture):
    cpu, memory, fields, read, write, run, hw, slots, queue, make_descriptor = overlay_fixture
    cpu.a[6] = APP
    memory[0x70000:0x70028] = b'\xA5'*40
    memory[0x77D00:0x78000] = b'\x5A'*0x300
    run(0x66D6)
    assert memory[0x70000:0x70028] == bytes(40)
    assert read(hw['BLTAPTH']) == 0x70000 and read(hw['BLTDPTH']) == 0x70028
    assert read(hw['BLTSIZE'], 2) == (656<<6) | 40
    assert read(hw['BLTAMOD'], 2) == read(hw['BLTDMOD'], 2) == 0
    # Programmed destination range crosses snapshot storage and bank-1 prefix.
    end = read(hw['BLTDPTH'])+656*80
    assert 0x77D00 < 0x78000 < end == 0x7CD28
    assert memory[0x77D00:0x78000] == b'\x5A'*0x300


@pytest.mark.parametrize('flags', [0x40, 0xE0])
def test_existing_registration_recaptures_even_with_saved_and_ready_bits_set(overlay_fixture, flags):
    cpu, memory, fields, read, write, run, hw, slots, queue, make_descriptor = overlay_fixture
    fill_rows(cpu, memory, run)
    address = BASE+0x335A
    write(queue, address)
    write(address+fields['state_flags'], flags, 1)
    cpu.a[5] = address
    for x in [4, 6]:
        write(address+fields['x'], x, 1)
        # Stop before clear/border/text drawing. A queue match still runs save.
        run(0x66A0, stop=0x66C2)
        assert read(queue) == address and read(queue+4) == 0
        assert read(address+fields['state_flags'], 1) == flags | 0x20
        assert read(hw['BLTAPTH']) == 0x70000+1280*19+x
        assert read(hw['BLTDPTH']) == 0x77D00


def test_prepared_palette_input_reads_last_32_hit_snapshot_bytes(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    palette = b''.join((i*0x111).to_bytes(2, 'big') for i in range(16))
    memory[0x77FE0:0x78000] = palette
    run(0x7190)
    assert cpu.a[1] == 0x77D00+0x2E0 and cpu.d[7] == 15
    output = cpu.a[0]
    components = cpu.a[2]
    run(0x2614, budget=512)
    assert memory[output:output+32] == palette
    assert memory[0x77FE0:0x78000] == palette
    assert [read(components+2*i, 2) for i in range(48)] == [16*(i//3) for i in range(48)]
    # This executes the preparation and palette leaf, not the stack-trampoline
    # overlay/fade caller or its unproven gameplay phase ordering.
