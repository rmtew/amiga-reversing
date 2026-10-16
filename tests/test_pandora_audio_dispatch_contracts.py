"""Original primary-audio dispatch and base preservation; no DMA timing claim."""
import pytest

from tests.test_pandora_state_transitions import BASE
from tests.test_pandora_state_transitions import cpu_fixture as cpu_fixture

PLAYER = BASE + 0x4D7DE
CHANNEL = 0x81000
DMA = 0x82000
PROGRAM = 0x83000

pytestmark = pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)


@pytest.mark.parametrize('opcode', range(0x80, 0x8B))
@pytest.mark.parametrize('channel_index', range(4))
def test_all_original_control_handlers_preserve_channel_bases(cpu_fixture, opcode, channel_index):
    cpu, memory, schemas, read, write, run = cpu_fixture
    target = PLAYER + int.from_bytes(memory[BASE+0x4DCE8+2*(opcode-0x80):BASE+0x4DCEA+2*(opcode-0x80)], 'big', signed=True)
    cpu.a[0], cpu.a[1], cpu.a[3], cpu.a[4], cpu.a[5] = CHANNEL, PROGRAM, PLAYER, DMA, 0x84000
    cpu.d[0] = opcode
    cpu.d[7], cpu.a[6] = 0x5A5A0000 | channel_index, 0xDFF000 + 16*channel_index
    run(0x4DC20, stop=target-BASE, budget=8)
    assert (cpu.a[0], cpu.a[4], cpu.a[5]) == (CHANNEL, DMA, 0x84000)
    assert cpu.d[7] == 0x5A5A0000 | channel_index and cpu.a[6] == 0xDFF000 + 16*channel_index
    # The original target is exercised with controlled valid operands. Silence's
    # pending latch skips hardware stores; reset executes through its RTS.
    memory[PROGRAM:PROGRAM+2] = bytes((3, 5))
    write(DMA+11, 1, 1)
    write(CHANNEL+28, 0x1234, 2)
    write(CHANNEL+8, 0x700, 2)
    write(CHANNEL+10, 0, 2)
    write(PLAYER+0x700, 0x800, 2)
    stop = None if opcode == 0x84 else {0x82:0x4DAAE, 0x83:0x4DA98}.get(opcode, 0x4DA1A)
    run(target-BASE, stop=stop, budget=64)
    assert (cpu.a[0], cpu.a[4], cpu.a[5]) == (CHANNEL, DMA, 0x84000)
    assert cpu.d[7] == 0x5A5A0000 | channel_index and cpu.a[6] == 0xDFF000 + 16*channel_index
    if opcode == 0x80:
        assert cpu.a[1] == PLAYER+0x800 and read(CHANNEL+10, 2) == 2
    elif opcode == 0x81:
        assert read(CHANNEL+20, 2) == 0x0305 and read(CHANNEL+32, 2) == 0 and read(CHANNEL, 1) == 2
    elif opcode == 0x82:
        assert read(CHANNEL+30, 2) == 0x1234 and read(CHANNEL+4) == PROGRAM and read(DMA+4, 2) == 32
    elif opcode == 0x85:
        assert read(PLAYER+0x52A, 1) == 3
    elif opcode == 0x86:
        assert [read(CHANNEL+n, 1) for n in (1,44,45,46)] == [255,3,0,5]
    elif opcode == 0x87:
        assert read(CHANNEL+1, 1) == 0
    elif opcode == 0x88:
        assert read(CHANNEL+3, 1) == 3
    elif opcode == 0x89:
        assert read(CHANNEL+8, 2) == 0x0305 and read(CHANNEL+10, 2) == 0
    elif opcode == 0x8A:
        assert read(PLAYER+0x520, 2) == 3


@pytest.mark.parametrize('channel_index', range(4))
def test_original_channel_stride_producers(cpu_fixture, channel_index):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.d[7] = channel_index
    run(0x4D968, stop=0x4D990, budget=32)
    assert cpu.a[0] == BASE+0x4DD14+48*channel_index
    assert cpu.a[4] == BASE+0x4E690+12*channel_index
    assert cpu.a[6] == 0xDFF000+16*channel_index


@pytest.mark.parametrize('channel_index', range(4))
def test_silence_handler_writes_the_selected_hardware_channel(cpu_fixture, channel_index):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[0], cpu.a[1], cpu.a[3], cpu.a[4] = CHANNEL, PROGRAM, PLAYER, DMA
    cpu.a[6], cpu.d[7] = 0xDFF000 + 16*channel_index, channel_index
    sample = 0x84000
    write(PLAYER+0x52E, sample)
    write(DMA+11, 0, 1)
    write(CHANNEL+28, 7, 2)
    run(0x4DC6A, stop=0x4DAAE, budget=32)
    for channel in range(4):
        assert read(0xDFF0A0+16*channel) == (sample if channel == channel_index else 0)
        assert read(0xDFF0A4+16*channel, 2) == (32 if channel == channel_index else 0)
    assert cpu.a[6] == 0xDFF000+16*channel_index and cpu.d[7] == channel_index
