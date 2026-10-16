"""Original star color dispatch, selector bounds and continuation ABI."""
import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_framebuffer_lifetime import APP


@pytest.mark.parametrize('continuation', [0xD68, 0xD9C, 0xDAE])
@pytest.mark.parametrize('color', range(8))
def test_original_star_dispatch_writes_color_and_tail_continues(cpu_fixture, color, continuation):
    cpu, memory, structs, read, write, run = cpu_fixture
    record, bitmap = 0x400, 0x70000
    fields = structs['title_star_record']
    cpu.a[2], cpu.a[3], cpu.a[6] = record, BASE + continuation, APP
    # Projected (-160,-100) selects row zero, byte zero, bit seven.
    write(record + fields['projected_x'], (-160) & 0xFFFF, 2)
    write(record + fields['projected_y'], (-100) & 0xFFFF, 2)
    write(record + fields['lifetime'], 17 if color <= 1 else 8 * (color - 1) + 16, 1)
    write(APP, 0, 2)  # row-zero offset table
    write(APP + 0x1D4, bitmap)  # original app_front_bitplane_base slot
    for plane in range(3):
        write(bitmap + 40 * plane, 0xD5, 1)
    write(bitmap + 120, 0xA5, 1)  # the fourth display plane is outside this writer
    before_a = list(cpu.a)
    source = 0xC58 if color == 0 else 0xC5C
    run(source, stop=continuation)
    assert [read(bitmap + 40 * p, 1) for p in range(3)] == [0x55 | (((color >> p) & 1) << 7) for p in range(3)]
    assert read(bitmap + 120, 1) == 0xA5
    assert cpu.d[1] & 0xFFFF == 7
    assert cpu.a[0] == bitmap and cpu.a[1] == BASE + 0xCC0 + 12 * color
    assert cpu.a[2:7] == before_a[2:7]
    assert cpu.a[7] == 0x9000  # tail JMP neither pushes nor consumes a return


def test_original_valid_lifetimes_select_only_seven_nonzero_colors(cpu_fixture):
    cpu, memory, structs, read, write, run = cpu_fixture
    cpu.a[2] = 0x400
    for lifetime in range(17, 65):
        write(0x400 + structs['title_star_record']['lifetime'], lifetime, 1)
        run(0xC5C, stop=0xC6A)
        assert cpu.d[2] == 1 + ((lifetime - 16) >> 3)
        assert 1 <= cpu.d[2] <= 7


def test_original_world_opcode_dispatch_is_unsigned_and_bounded(cpu_fixture):
    cpu, memory, structs, read, write, run = cpu_fixture
    command = 0x8000
    cpu.a[4] = command
    for opcode in range(33):
        write(command, opcode, 2)
        run(0x1412, stop=0x1424)
        assert cpu.a[0] == read(BASE + 0x1432 + 4 * opcode)
        assert cpu.d[0] & 0xFFFF == 4 * opcode
    for opcode in (33, 34, 127, 128, 0x7FFF, 0x8000, 0xFFFF):
        write(command, opcode, 2)
        cpu.a[0] = 0xDEADBEEF
        run(0x1412, stop=0x14B6)
        assert cpu.a[0] == 0xDEADBEEF
