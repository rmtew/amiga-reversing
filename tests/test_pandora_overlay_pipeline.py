"""Original CPU register packets and queue control; no DMA/IRQ device simulation."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import resolve_project_paths
from tests.test_pandora_state_transitions import TARGET, BASE, cpu_fixture

pytestmark = pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
APP, DESCRIPTOR, SNAPSHOT = 0x4000, 0x6000, 0x68000


@pytest.fixture
def overlay_fixture(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    root = Path(__file__).resolve().parents[1]
    hardware = json.loads((root / 'knowledge/amiga_hw_registers.json').read_text())
    registers = {r['name']: int(r['address_68k'], 16) for r in hardware['registers']}
    metadata = effective_target_metadata(resolve_project_paths(TARGET).target_dir)
    slots = {r.symbol: r.offset for r in metadata.rsset_layout_regions if r.symbol}
    fields = schemas['ui_overlay_descriptor']
    queue = next(l.source_start for l in metadata.data_block_layouts if l.name == 'ui_overlay_update_queue') + BASE
    cpu.a[6] = APP
    # A memory shadow with the observed BLIT request set allows the original
    # polling loop to proceed. INTREQ writes do not emulate acknowledgement.
    write(registers['INTREQR'], 0x40, 2)

    def descriptor(address=DESCRIPTOR, *, width=6, height=3, flags=0xE3, callback=0):
        memory[address:address+44] = bytes(44)
        write(address + fields['x'], 5, 1)
        write(address + fields['y'], 3, 1)
        write(address + fields['width'], width, 1)
        write(address + fields['height'], height, 1)
        write(address + fields['state_flags'], flags, 1)
        write(address + fields['bitmap_ptr'], SNAPSHOT + address-DESCRIPTOR)
        write(address + fields['update_callback'], callback)
        # Opaque caller-supplied row lookup, not a claimed producer/layout proof.
        write(APP + 16*3, 0x1200, 2)
        return address

    return cpu, memory, fields, read, write, run, registers, slots, queue, descriptor


@pytest.mark.parametrize('width,height', [(2, 1), (3, 3), (6, 7), (40, 3), (6, 8), (19, 3), (6, 3), (7, 3), (12, 3), (12, 6)])
def test_background_capture_restore_and_clear_program_original_packets(overlay_fixture, width, height):
    cpu, memory, fields, read, write, run, hw, slots, queue, make_descriptor = overlay_fixture
    address = make_descriptor(width=width, height=height)
    cpu.a[5] = address
    screen = 0x70000 + 0x1200 + 5
    ceil_words = (width+1)//2
    # Capture/restore retain inherited first-mask and shift-control state.
    write(hw['BLTAFWM'], 0xA55A, 2)
    write(hw['BLTCON1'], 0x2345, 2)
    def call_with_partition(entry, clobbered):
        # Vary otherwise-unused registers so preservation is actually exercised.
        for index in range(8):
            cpu.d[index] = 0xA5B60000 + index
            if index < 5:
                cpu.a[index] = 0xC7D80000 + index
        before_d, before_a = list(cpu.d), list(cpu.a)[:7]
        run(entry)
        for index in range(8):
            if f'D{index}' not in clobbered:
                assert cpu.d[index] == before_d[index]
            if index < 7 and f'A{index}' not in clobbered:
                assert cpu.a[index] == before_a[index]
        assert cpu.a[7] == 0x9004

    call_with_partition(0x6332, {'D0', 'D1', 'D2', 'A0', 'A1'})
    assert cpu.a[5] == address
    assert read(hw['BLTAPTH']) == screen and read(hw['BLTDPTH']) == SNAPSHOT
    assert read(hw['BLTAMOD'], 2) == 40-2*ceil_words and read(hw['BLTDMOD'], 2) == 0
    assert read(hw['BLTSIZE'], 2) == ((height*32 << 6) | ceil_words) & 0xFFFF
    assert read(hw['BLTCON0'], 2) == 0x09F0
    assert read(hw['BLTAFWM'], 2) == 0xA55A and read(hw['BLTCON1'], 2) == 0x2345
    assert read(hw['INTREQ'], 2) == 0x40
    assert read(APP + slots['app_text_cursor_ptr']) == screen
    assert read(address + fields['state_flags'], 1) == 0xE3

    call_with_partition(0x639A, {'D0', 'D1', 'D2', 'A0', 'A1'})
    assert cpu.a[5] == address
    assert read(hw['BLTAPTH']) == SNAPSHOT and read(hw['BLTDPTH']) == screen
    assert read(hw['BLTAMOD'], 2) == 0 and read(hw['BLTDMOD'], 2) == 40-2*ceil_words
    assert read(hw['BLTSIZE'], 2) == (((height*32 & 0xFF) << 6) | ceil_words)
    assert read(address + fields['state_flags'], 1) == 0x43
    assert read(hw['BLTAFWM'], 2) == 0xA55A and read(hw['BLTCON1'], 2) == 0x2345

    # Rectangle clearing repeats the zero datum using negative source modulo.
    call_with_partition(0x6444, {'D0', 'D1', 'D2', 'D3', 'A0'})
    floor_words = width//2
    assert read(hw['BLTAPTH']) == BASE + 0x4D5DE and read(hw['BLTDPTH']) == screen
    assert read(hw['BLTCON1'], 2) == 0 and read(hw['BLTAFWM'], 2) == 0xA55A
    assert read(hw['BLTAMOD'], 2) == (-2*floor_words) & 0xFFFF
    assert read(hw['BLTDMOD'], 2) == 40-2*floor_words
    assert read(hw['BLTSIZE'], 2) == ((height*32 << 6) | floor_words) & 0xFFFF
    # These calls program registers; the fixture performs no pixel DMA.
    assert memory[SNAPSHOT:SNAPSHOT+32] == bytes(32)


def test_update_scan_visits_sixteen_slots_and_keeps_registrations(overlay_fixture):
    cpu, memory, fields, read, write, run, hw, slots, queue, make_descriptor = overlay_fixture
    active = make_descriptor(callback=BASE+0x639A)
    inactive = make_descriptor(DESCRIPTOR+0x100, flags=0x63, callback=BASE+0x639A)
    write(inactive + fields['line_style_flags'], 0xFF, 1)
    no_callback = make_descriptor(DESCRIPTOR+0x200, callback=0)
    last = make_descriptor(DESCRIPTOR+0x300, callback=BASE+0x639A)
    outside = make_descriptor(DESCRIPTOR+0x400, callback=BASE+0x639A)
    for index, pointer in [(0, active), (4, inactive), (8, no_callback), (15, last), (16, outside)]:
        write(queue+4*index, pointer)
    before = bytes(memory[queue:queue+68])
    run(0x6676, budget=2048)
    assert read(active + fields['state_flags'], 1) == 0x43
    assert read(last + fields['state_flags'], 1) == 0x43
    assert read(inactive + fields['state_flags'], 1) == 0x63
    assert read(no_callback + fields['state_flags'], 1) == 0xE3
    assert read(outside + fields['state_flags'], 1) == 0xE3
    assert bytes(memory[queue:queue+68]) == before
    assert cpu.a[0] == queue+64 and cpu.d[7] & 0xFFFF == 0xFFFF
    # Restored descriptors remain registered but no longer enable callbacks.
    write(hw['BLTDPTH'], 0x12345678)
    run(0x6676, budget=2048)
    assert read(hw['BLTDPTH']) == 0x12345678


@pytest.mark.parametrize('kind', ['existing', 'new', 'hole', 'beyond_scan'])
def test_registration_search_is_prefix_based_and_has_no_scan_bound(overlay_fixture, kind):
    cpu, memory, fields, read, write, run, hw, slots, queue, make_descriptor = overlay_fixture
    pointer = make_descriptor()
    if kind == 'existing':
        write(queue, pointer)
        expected = 0
    elif kind == 'new':
        write(queue, pointer+0x100)
        expected = 1
    elif kind == 'hole':
        write(queue+4, pointer)
        expected = 0
    else:
        for index in range(16):
            write(queue+4*index, pointer+0x100)
        write(queue+64, 0)
        expected = 16
    cpu.a[5] = pointer
    run(0x66A0, stop=0x66B0)
    assert read(queue+4*expected) == pointer
    if kind == 'hole':
        assert read(queue+4) == pointer  # A later duplicate is not searched.
    # Stop before capture/drawing; this proves admission behavior only.


def test_fixed_panel_family_matches_shared_geometry_and_snapshot_roles(overlay_fixture):
    cpu, memory, fields, read, write, run, hw, slots, queue, make_descriptor = overlay_fixture
    metadata = effective_target_metadata(resolve_project_paths(TARGET).target_dir)
    constants = {e.name: e.value for e in metadata.target_equates}
    assert constants['UI_OVERLAY_SAVE_BACKGROUND_MASK'] == 1 << constants['UI_OVERLAY_SAVE_BACKGROUND_BIT']
    owners = {l.source_start: l for l in metadata.data_block_layouts
              if 0x32AA <= l.source_start < 0x3462}
    assert set(owners) == {0x32AA+44*index for index in range(10)}
    buffers = []
    for source, owner in owners.items():
        assert owner.source_end == source+44 and len(owner.elements) == 1
        binding = owner.elements[0].type_binding
        assert binding['binding_kind'] == 'custom_struct' and binding['bound_type_id'] == 'ui_overlay_descriptor'
        address = BASE+source
        width, height = read(address+fields['width'], 1), read(address+fields['height'], 1)
        # Every initialized panel stays below the restore helper's byte wrap.
        assert 1 <= width <= 40 and 1 <= height < 8
        flags = read(address+fields['state_flags'], 1)
        bitmap = read(address+fields['bitmap_ptr'])
        assert bool(flags & constants['UI_OVERLAY_SAVE_BACKGROUND_MASK']) == bool(bitmap)
        assert read(address+fields['update_callback']) == 0
        if bitmap:
            buffers.append(bitmap)
    assert sorted(buffers) == [0x7F0, 0x77D00]
