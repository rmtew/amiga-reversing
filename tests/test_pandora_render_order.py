"""Original CPU rendering order with explicit MMIO inputs; no DMA scheduler."""
from __future__ import annotations

import ctypes as C
import pytest

from src.tests.test_m68k_simulator_arithmetic import Trace, engine
from tests.test_pandora_state_transitions import BASE, RETURN, cpu_fixture
from tests.test_pandora_overlay_pipeline import overlay_fixture
from tests.test_pandora_framebuffer_lifetime import APP, fill_rows

pytestmark = pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)


def sequencer(cpu, memory, write):
    buffer = (C.c_uint8 * len(memory)).from_buffer(memory)
    cpu.a[7] = 0x9000
    write(0x9000, RETURN)

    def advance(source=None, *, stop=None, budget=512):
        if source is not None:
            cpu.pc = BASE+source
        trace = Trace()
        end = BASE+stop if stop is not None else RETURN
        rc = engine()(0, buffer, len(memory), C.byref(cpu), budget, end, end+2, None, C.byref(trace))
        messages = [bytes(d.message).split(b'\0')[0].decode() for d in trace.diagnostics.items[:trace.diagnostics.count]]
        assert rc == 0 and not any(d.severity >= 3 for d in trace.diagnostics.items[:trace.diagnostics.count]), messages
        return trace
    return advance


def test_enqueue_waits_before_packets_but_cpu_border_and_ready_do_not_wait(overlay_fixture):
    cpu, memory, fields, read, write, run, hw, slots, queue, make_descriptor = overlay_fixture
    fill_rows(cpu, memory, run)
    descriptor = BASE+0x335A
    cpu.a[5] = descriptor
    write(hw['INTREQR'], 0, 2)
    write(hw['BLTSIZE'], 0x1234, 2)
    before = bytes(memory[0x70000:0x77D00])
    advance = sequencer(cpu, memory, write)
    assert advance(0x66A0, stop=0x6366).stop_reason == 1
    assert read(queue) == descriptor
    assert read(descriptor+fields['state_flags'], 1) == 0x60
    assert advance(budget=6, stop=0x6478).stop_reason == 3
    assert cpu.pc == BASE+0x6366 and read(hw['BLTSIZE'], 2) == 0x1234
    write(hw['INTREQR'], 0x40, 2)
    assert advance(stop=0x6478).stop_reason == 1
    assert read(hw['BLTDPTH']) == 0x77D00 and read(hw['BLTSIZE'], 2) == (96<<6)|4
    write(hw['INTREQR'], 0, 2)
    assert advance(stop=0x64AE, budget=6).stop_reason == 3
    assert cpu.pc == BASE+0x6478
    assert bytes(memory[0x70000:0x77D00]) == before
    write(hw['INTREQR'], 0x40, 2)
    assert advance(stop=0x64AE).stop_reason == 1
    assert read(hw['BLTSIZE'], 2) == (96<<6)|3
    # No request bit is supplied after clear starts. Border/title and the NULL
    # text prefix still finish and mark ready. No DMA is performed by the shadow.
    write(hw['INTREQR'], 0, 2)
    trace = advance(budget=10000)
    assert trace.stop_reason == 1
    assert bytes(memory[0x70000:0x77D00]) != before
    assert read(hw['BLTSIZE'], 2) == (96<<6)|3
    assert read(descriptor+fields['state_flags'], 1) == 0xE0
    assert read(queue) == descriptor and cpu.a[5] == descriptor and cpu.a[7] == 0x9004
    # Border writes may exceed the bounded 32-range trace summary; assertions
    # use guest memory directly, not an assumed complete write trace.


def test_original_combat_entry_serializes_packets_but_not_cpu_border_after_clear(overlay_fixture):
    cpu, memory, fields, read, write, run, hw, slots, queue, make_descriptor = overlay_fixture
    fill_rows(cpu, memory, run)
    write(APP+slots['app_ui_flags'], 0, 1)  # No inventory close prefix.
    write(hw['INTREQR'], 0, 2)
    advance = sequencer(cpu, memory, write)
    # The actual entry queues the non-snapshot opponent panel before hit feedback.
    assert advance(0x7792, stop=0x6478, budget=1024).stop_reason == 1
    assert cpu.a[7] < 0x9000
    assert advance(stop=0x64AA, budget=6).stop_reason == 3
    write(hw['INTREQR'], 0x40, 2)
    assert advance(stop=0x64AA).stop_reason == 1  # First panel's clear started.
    write(hw['INTREQR'], 0, 2)
    # Original CPU border/text runs without another request check, then the
    # second enqueue reaches the hit capture wait. No actual pixel DMA is done.
    assert advance(stop=0x6366, budget=20000).stop_reason == 1
    assert read(queue+4) == BASE+0x335A
    assert advance(stop=0x6396, budget=6).stop_reason == 3
    write(hw['INTREQR'], 0x40, 2)
    assert advance(stop=0x6396).stop_reason == 1
    assert read(hw['BLTDPTH']) == 0x77D00
    assert read(hw['BLTSIZE'], 2) == (96<<6)|4
    write(hw['INTREQR'], 0, 2)
    assert advance(stop=0x6478).stop_reason == 1
    assert advance(stop=0x64AA, budget=6).stop_reason == 3
    write(hw['INTREQR'], 0x40, 2)
    assert advance(stop=0x64AA).stop_reason == 1
    write(hw['INTREQR'], 0, 2)
    assert advance(stop=0x77B8, budget=20000).stop_reason == 1
    assert read(BASE+0x335A+fields['state_flags'], 1) == 0xE0
    assert read(BASE+0x335A+fields['update_callback']) == 0
    assert cpu.a[7] == 0x9000
    # This establishes the original combat-entry prefix under its stated guard,
    # not cold-start encounter reachability, DMA completion, or bus arbitration.


@pytest.mark.parametrize('saved', [False, True])
def test_close_inventory_directly_restores_body_without_queue_callback_or_saved_guard(overlay_fixture, saved):
    cpu, memory, fields, read, write, run, hw, slots, queue, make_descriptor = overlay_fixture
    fill_rows(cpu, memory, run)
    from amiga_reversing.disasm.effective_metadata import effective_target_metadata
    from amiga_reversing.disasm.project_paths import resolve_project_paths
    from tests.test_pandora_state_transitions import TARGET
    metadata = effective_target_metadata(resolve_project_paths(TARGET).target_dir)
    bits = {e.name: e.value for e in metadata.target_equates}
    write(APP+slots['app_ui_flags'], (1 << bits['UI_FLAG_INVENTORY_PANEL_ACTIVE']) |
          (1 << bits['UI_FLAG_NEARBY_OBJECT_INVENTORY']), 1)
    body = BASE+0x33DE
    write(body+fields['state_flags'], 0xE0 if saved else 0x40, 1)
    write(body+fields['update_callback'], 0)
    memory[queue:queue+64] = bytes(64)
    write(hw['INTREQR'], 0, 2)
    advance = sequencer(cpu, memory, write)
    # Interior close path follows the original inventory/flag housekeeping.
    # Direct restore is not conditional on queue membership or saved bit 5.
    assert advance(0x27AE, stop=0x63CE).stop_reason == 1
    assert advance(stop=0x6400, budget=6).stop_reason == 3
    write(hw['INTREQR'], 0x40, 2)
    assert advance(stop=0x6400).stop_reason == 1
    assert read(hw['BLTAPTH']) == 0x7F0
    assert read(hw['BLTSIZE'], 2) == (192<<6)|6
    write(hw['INTREQR'], 0, 2)
    assert advance(stop=0x6478, budget=1024).stop_reason == 1
    assert read(body+fields['state_flags'], 1) == 0x40
    assert read(queue) != body
    # Next nearby panel blocks on completion request before its clear. Restore
    # return/flag clearing alone never certifies physical DMA consumption.
