"""Original proximity gate and callees in flat RAM; no audible/DMA claim."""
import pytest

from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import resolve_project_paths
from tests.test_pandora_state_transitions import BASE, TARGET, cpu_fixture
from tests.test_pandora_render_order import sequencer

pytestmark = pytest.mark.parametrize("cpu_fixture", [0x1000000], indirect=True)
APP = 0x70000


@pytest.fixture
def audio_gate(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    metadata = effective_target_metadata(resolve_project_paths(TARGET).target_dir)
    names = {e.name: BASE+e.addr for e in metadata.seeded_entities if e.name}
    slots = {e.symbol: e.offset for e in metadata.rsset_layout_regions}
    flags = APP+slots['app_world_interaction_flags']
    actor = names['world_object_pianist_actor_world_object_flags']
    xy = names['player_world_object_world_x']
    volume = names['audio_player_globals_master_volume']
    cpu.a[6] = APP
    write(actor, 0, 1)
    write(xy, 840, 2)
    write(xy+2, 168, 2)
    write(volume, 0x1234, 2)
    return cpu_fixture, flags, actor, xy, volume


def magnitude(value, center):
    word = (value-center) & 0xFFFF
    return (-word) & 0xFFFF if word & 0x8000 else word


def test_every_coordinate_word_and_both_axis_sign_branches(audio_gate):
    (cpu, memory, schemas, read, write, run), flags, actor, xy, volume = audio_gate
    # Active input avoids initialization, but far visits execute the real reset.
    for axis, center in [(0, 840), (2, 168)]:
        for value in range(65536):
            write(xy, 840, 2)
            write(xy+2, 168, 2)
            write(xy+axis, value, 2)
            write(flags, 0xA1, 1)
            write(volume, 0x1234, 2)
            distance = magnitude(value, center)
            run(0x552FE, budget=256)
            assert read(flags, 1) == (0xA1 if distance < 256 else 0xA0)
            assert read(volume, 2) == (64-(distance >> 2) if distance < 256 else 64)


@pytest.mark.parametrize('dx,dy', [(128, 127), (128, 128), (-128, -127),
                                (32768, 32768), (32768, 32767),
                                (32767, 32767), (0, 0), (255, 0)])
def test_word_sum_wrap_and_unsigned_threshold(audio_gate, dx, dy):
    (cpu, memory, schemas, read, write, run), flags, actor, xy, volume = audio_gate
    write(xy, (840+dx) & 0xFFFF, 2)
    write(xy+2, (168+dy) & 0xFFFF, 2)
    write(flags, 0xFD, 1)
    distance = (magnitude((840+dx) & 0xFFFF, 840)+magnitude((168+dy) & 0xFFFF, 168)) & 0xFFFF
    run(0x552FE, budget=256)
    assert read(flags, 1) == (0xFD if distance < 256 else 0xFC)
    assert read(volume, 2) == (64-(distance >> 2) if distance < 256 else 64)


@pytest.mark.parametrize('active', [False, True])
def test_actor_inhibit_resets_only_on_active_edge_and_writes_high_byte(audio_gate, active):
    (cpu, memory, schemas, read, write, run), flags, actor, xy, volume = audio_gate
    write(actor, 2, 1)
    write(flags, 0xF0 | active, 1)
    for i in range(8):
        cpu.d[i] = 0xCAFE0000+i
        if i < 6:
            cpu.a[i] = 0xBEEF0000+i
    before_d, before_a = list(cpu.d), list(cpu.a[:7])
    run(0x552FE, budget=256)
    assert read(flags, 1) == 0xF0
    # Big-endian BYTE store at the WORD's address: this is $4034, not $0040.
    assert read(volume, 2) == (0x4034 if active else 0x1234)
    assert list(cpu.d[1:]) == before_d[1:] and list(cpu.a[:7]) == before_a
    assert cpu.a[7] == 0x9004
    if active:
        assert read(0xDFF096, 2) == 15
        assert all(read(0xDFF0A8+16*i, 2) == 0 for i in range(4))


def test_far_inactive_retains_volume_and_near_inactive_initializes_then_attenuates(audio_gate):
    (cpu, memory, schemas, read, write, run), flags, actor, xy, volume = audio_gate
    write(flags, 0xA0, 1)
    write(xy, 1096, 2)
    run(0x552FE, budget=256)
    assert read(flags, 1) == 0xA0 and read(volume, 2) == 0x1234
    write(xy, 963, 2)
    # Complete initialization exceeds the bounded write-summary capacity.
    # Check guest memory and normal return, without treating it as a full trace.
    trace = sequencer(cpu, memory, write)(0x552FE, budget=1024)
    assert trace.stop_reason == 1 and trace.steps < 1024
    assert read(flags, 1) == 0xA1 and read(volume, 2) == 34
    assert cpu.a[6] == APP and cpu.a[7] == 0x9004
    # Existing near visits must not initialize/reset again; MMIO stays untouched.
    write(0xDFF096, 0x5678, 2)
    run(0x552FE, budget=256)
    assert read(0xDFF096, 2) == 0x5678


@pytest.mark.parametrize('active', [False, True])
def test_shared_start_latch_preserves_saved_registers_and_returns_clear_carry(audio_gate, active):
    (cpu, memory, schemas, read, write, run), flags, actor, xy, volume = audio_gate
    write(flags, 0xB0 | active, 1)
    write(0xDFF096, 0x5678, 2)
    for i in range(8):
        cpu.d[i] = 0xCAFE0000+i
        if i < 6:
            cpu.a[i] = 0xBEEF0000+i
    before_d, before_a = list(cpu.d), list(cpu.a[:7])
    trace = sequencer(cpu, memory, write)(0x4D34C, budget=1024)
    assert trace.stop_reason == 1 and trace.steps < 1024
    assert read(flags, 1) == 0xB1
    assert read(0xDFF096, 2) == (0x5678 if active else 15)
    assert list(cpu.d[1:]) == before_d[1:] and list(cpu.a[1:7]) == before_a[1:]
    assert cpu.d[0] == (before_d[0] if active else 28)
    assert cpu.a[7] == 0x9004 and not cpu.sr & 1
