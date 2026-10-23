"""Original command-byte consumers and note arithmetic, not audio/DMA playback."""
from __future__ import annotations

import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture


@pytest.mark.parametrize('index,opcode,delta', [
    (0, 0x85, -1), (1, 0x85, 0), (2, 0x85, 1), (3, 0x85, 2),
    (4, 0x85, 3), (5, 0x88, -1), (6, 0x88, -2), (7, 0x88, -3),
])
def test_three_byte_commands_write_selected_offset_and_transpose_a_note(cpu_fixture, index, opcode, delta):
    cpu, memory, schemas, read, write, run = cpu_fixture
    player_base = BASE+0x4D7DE
    channel = BASE+0x4DD14
    command = BASE+0x4E34C+3*index
    assert bytes(memory[command:command+3]) == bytes([opcode, delta & 255, 0x80])
    global_offset = player_base+0x52A
    channel_offset = channel+schemas['audio_channel_runtime_state']['note_offset']
    write(global_offset, 0, 1)
    write(channel_offset, 0, 1)
    cpu.a[0], cpu.a[1], cpu.a[3] = channel, command+1, player_base
    run(0x4DC9E if opcode == 0x85 else 0x4DCC2, stop=0x4DA1A, budget=16)
    assert cpu.a[1] == command+2
    assert read(global_offset, 1) == (delta & 255 if opcode == 0x85 else 0)
    assert read(channel_offset, 1) == (delta & 255 if opcode == 0x88 else 0)
    cpu.d[0] = 0x12340040
    run(0x4DA26, stop=0x4DA2E, budget=8)
    assert cpu.d[0] == 0x12340000 | ((64+delta) & 255)
    assert read(command+2, 1) == 0x80
    # Interpreter dispatch, selector bounds, pitch lookup and DMA are outside this slice.
