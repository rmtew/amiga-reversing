"""Original ray sampling: bounded tile lookup witnesses, not route termination."""
import pytest
from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import resolve_project_paths
from tests.test_pandora_state_transitions import TARGET, cpu_fixture

pytestmark = pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
APP = 0x39FC


@pytest.mark.parametrize('x,y,dx,dy', [(32, 48, 2, 0), (32, 48, 0, -2),
                                       (0xFFFE, 48, 2, 0), (32, 0, 0, -2),
                                       (1438, 2062, 2, 2), (32, 48, 0, 0)])
def test_ray_uses_word_wrapped_point_and_low_word_grid_offset(cpu_fixture, x, y, dx, dy):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = APP
    cpu.d[0], cpu.d[1] = x, y
    cpu.d[2], cpu.d[3] = dx & 0xFFFF, dy & 0xFFFF
    run(0x92DE, stop=0x92FA)
    sample_x, sample_y = (x+dx) & 0xFFFF, (y+dy) & 0xFFFF
    assert (cpu.d[5] & 0xFFFF, cpu.d[6] & 0xFFFF) == (sample_x, sample_y)
    assert cpu.d[0] == (4*((sample_y >> 4)*90+(sample_x >> 4))) & 0xFFFF
    assert (cpu.d[2] & 0xFFFF, cpu.d[3] & 0xFFFF) == (dx & 0xFFFF, dy & 0xFFFF)


@pytest.mark.parametrize('tile,blocked', [(0, False), (7, True), (8, True), (507, True), (507, False)])
def test_original_tile_pointer_selects_msb_first_block_bit(cpu_fixture, tile, blocked):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = APP
    # Controlled valid grid and index; preserve the original instructions/helper.
    grid = 0x80000
    slots = {r.symbol: r.offset for r in effective_target_metadata(
        resolve_project_paths(TARGET).target_dir).rsset_layout_regions if r.symbol}
    write(APP+slots['app_tilemap_base'], grid)
    write(grid, 0x1D0A8+128*tile)
    memory[0x1A822:0x1A862] = bytes(64)
    if blocked:
        memory[0x1A822+(tile >> 3)] = 0x80 >> (tile & 7)
    cpu.d[0], cpu.d[5], cpu.d[6] = 0, 123, 456
    run(0x92FA, stop=0x9410 if blocked else 0x931C)
    if not blocked:
        assert (cpu.d[0], cpu.d[1]) == (123, 456)


def test_empty_descriptor_scan_returns_to_ray_without_advancing_zero_step(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    slots = {r.symbol: r.offset for r in effective_target_metadata(
        resolve_project_paths(TARGET).target_dir).rsset_layout_regions if r.symbol}
    cpu.a[6] = APP
    write(APP+slots['app_active_world_object_ptr_table'], 0x80000)
    write(0x80000, 0)
    cpu.d[0], cpu.d[1], cpu.d[2], cpu.d[3] = 123, 456, 0, 0
    run(0x931C, stop=0x92DE)
    run(0x92DE, stop=0x92E2)
    assert (cpu.d[0], cpu.d[1]) == (123, 456)
