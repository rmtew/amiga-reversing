"""Original bootstrap preservation and seeded-clear return values; no pixel DMA."""

import pytest

from tests.test_pandora_render_order import sequencer
from tests.test_pandora_state_transitions import cpu_fixture as cpu_fixture

pytestmark = pytest.mark.parametrize("cpu_fixture", [0x1000000], indirect=True)
CUSTOM = 0xDFF000
APP = 0x39FC


@pytest.mark.parametrize("value", [CUSTOM, 0x81234, 0xFEDCBA98])
def test_world_initialization_restores_the_entry_a5(cpu_fixture, value):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[5], cpu.a[6] = value, APP
    trace = sequencer(cpu, memory, write)(0x9F26, budget=10000)
    assert trace.stop_reason == 1 and trace.steps < 10000
    # The write-range summary may overflow; register state is read directly.
    assert cpu.a[5] == value and cpu.a[6] == APP and cpu.a[7] == 0x9004


def test_priming_blit_preserves_every_register_except_a0(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    for i in range(8):
        cpu.d[i] = 0x12340000 + i
        cpu.a[i] = 0x23450000 + i
    cpu.a[5] = CUSTOM
    before_d, before_a = list(cpu.d), list(cpu.a)[:7]
    run(0x7CC)
    assert list(cpu.d) == before_d
    assert list(cpu.a)[1:7] == before_a[1:7]
    assert cpu.a[7] == 0x9004
    assert read(CUSTOM + 0x58, 2) == 65


@pytest.mark.parametrize("value", [0, CUSTOM, 0x81234])
def test_seeded_clear_returns_the_fixed_custom_base_not_the_input(cpu_fixture, value):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[5], cpu.a[6] = value, APP
    write(CUSTOM + 0x1E, 0x40, 2)
    run(0x66D6)
    assert cpu.a[5] == CUSTOM and cpu.a[7] == 0x9004
    assert read(CUSTOM + 0x58, 2) == (656 << 6) | 40


@pytest.mark.parametrize("seed", [0x12345678, 0xA5A55A5A])
def test_initialized_starfield_preserves_its_register_partition(cpu_fixture, seed):
    from amiga_reversing.disasm.effective_metadata import effective_target_metadata
    from amiga_reversing.disasm.project_paths import resolve_project_paths
    from tests.test_pandora_state_transitions import TARGET

    cpu, memory, schemas, read, write, run = cpu_fixture
    slots = {
        s.symbol: s.offset
        for s in effective_target_metadata(
            resolve_project_paths(TARGET).target_dir
        ).rsset_layout_regions
    }
    for i in range(8):
        cpu.d[i] = 0x12340000 + i
        cpu.a[i] = 0x23450000 + i
    cpu.a[5], cpu.a[6] = 0x81234, APP
    write(APP + slots["app_front_bitplane_base"], 0x70000)
    write(0x7E8, seed)
    write(0x7EC, seed ^ 0x98765432)
    before_d, before_a = list(cpu.d), list(cpu.a)
    trace = sequencer(cpu, memory, write)(0xD20, budget=200000)
    assert trace.stop_reason == 1 and trace.steps < 200000
    assert list(cpu.d)[4:7] == before_d[4:7]
    assert list(cpu.a)[4:7] == before_a[4:7] and cpu.a[7] == 0x9004
