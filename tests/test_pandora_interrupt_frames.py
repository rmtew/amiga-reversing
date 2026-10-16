"""Original IRQ dispatcher with explicit frames/MMIO; no asynchronous IRQ or DMA."""
from __future__ import annotations

import pytest

from tests.test_pandora_overlay_pipeline import overlay_fixture
from tests.test_pandora_render_order import sequencer
from tests.test_pandora_state_transitions import BASE, cpu_fixture

pytestmark = pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)


@pytest.mark.parametrize('irq_request,slot,return_site,rte', [
    (0x10, 'app_copper_interrupt_callback', 0x904, 0x90E),
    (0x20, 'app_vertical_blank_callback', 0x91C, 0x926),
    (0x40, 'app_blitter_interrupt_callback', 0x934, 0x93E),
    (0x70, 'app_copper_interrupt_callback', 0x904, 0x90E),
])
def test_dispatcher_frame_offsets_and_restore_with_original_noop_callback(
    overlay_fixture, irq_request, slot, return_site, rte
):
    cpu, memory, fields, read, write, run, hw, slots, queue, make_descriptor = overlay_fixture
    # These are modeled inputs, not evidence that BLIT IRQ is enabled or that
    # the unconnected palette routine is installed as a callback.
    callback = BASE+0x750
    assert bytes(memory[callback:callback+2]) == bytes.fromhex('4e75')
    app = 0x39FC
    for name in ['app_copper_interrupt_callback', 'app_vertical_blank_callback',
                 'app_blitter_interrupt_callback']:
        write(app+slots[name], callback)
    write(hw['INTREQR'], irq_request, 2)
    advance = sequencer(cpu, memory, write)
    for i in range(8):
        cpu.d[i], cpu.a[i] = 0x11220000+i, 0x22330000+i
    cpu.a[7] = 0x9000
    write(0x9000, 0x2000, 2)       # Explicit 68000 hardware frame.
    write(0x9002, BASE+0x5CA)
    before_d, before_a = list(cpu.d), list(cpu.a)
    frame = bytes(memory[0x9000:0x9006])
    cpu.sr = 0x2300
    assert advance(0x8E4, stop=0x750).stop_reason == 1
    assert cpu.a[7] == 0x9000-24
    assert read(cpu.a[7]) == BASE+return_site
    assert [read(cpu.a[7]+off) for off in [4, 8, 12, 16, 20]] == [
        before_d[0], before_a[0], before_a[1], before_a[5], before_a[6]
    ]
    assert cpu.a[0] == read(app+slots[slot]) == callback
    assert advance(stop=rte).stop_reason == 1
    assert cpu.a[7] == 0x9000
    assert list(cpu.d) == before_d and list(cpu.a) == before_a
    assert bytes(memory[0x9000:0x9006]) == frame
    assert read(hw['INTREQ'], 2) == irq_request & -irq_request
    # Stop before RTE: this tests saved-register/return-slot placement, not
    # exception admission, interrupt timing, arbitrary callbacks or stack bounds.


def test_native_supervisor_stack_setup_is_an_address_not_an_extent(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    for source, stop in [(0x47A, 0x47E), (0x4BA, 0x4BE)]:
        run(source, stop=stop)
        assert cpu.a[7] == BASE+0x452
    # No lower bound, maximum call depth or IRQ envelope is inferred from LEA.
