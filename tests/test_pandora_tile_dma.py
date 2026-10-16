"""Original tile-copy packets and row/grid wrapping; custom registers are a shadow."""

import pytest

from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import resolve_project_paths
from tests.test_pandora_render_order import sequencer
from tests.test_pandora_state_transitions import BASE, TARGET
from tests.test_pandora_state_transitions import cpu_fixture as cpu_fixture

pytestmark = pytest.mark.parametrize("cpu_fixture", [0x1000000], indirect=True)
APP = 0x39FC
CUSTOM = 0xDFF000


def tile_inputs(fixture, width, height, start_row):
    cpu, memory, schemas, read, write, run = fixture
    slots = {
        s.symbol: s.offset
        for s in effective_target_metadata(
            resolve_project_paths(TARGET).target_dir
        ).rsset_layout_regions
    }
    grid, destination = 0x81000, 0x70000
    columns, rows = max(width, 1), 3
    stride = columns * 4
    pointers = [0x82000 + 128 * i for i in range(columns * rows)]
    for i, pointer in enumerate(pointers):
        write(grid + 4 * i, pointer)
    write(APP + slots["app_tile_pointer_grid_row_stride_bytes"], stride)
    write(APP + slots["app_tile_pointer_grid_end"], grid + stride * rows)
    write(APP + slots["app_tile_pointer_grid_byte_size"], stride * rows)
    cpu.a[0], cpu.a[1], cpu.a[6] = grid + start_row * stride, destination, APP
    cpu.d[0], cpu.d[1] = width, height
    for i in range(2, 6):
        cpu.d[i] = 0x12340000 + i
    write(CUSTOM + 0x1E, 0x40, 2)
    return grid, destination, stride, pointers


@pytest.mark.parametrize(
    ("width", "height", "start_row"),
    [(1, 1, 0), (3, 2, 2), (20, 8, 1), (21, 1, 0), (20, 9, 0)],
)
def test_tile_packets_keep_source_destination_and_wrapped_grid_relationships(
    cpu_fixture, width, height, start_row
):
    cpu, memory, schemas, read, write, run = cpu_fixture
    grid, destination, stride, pointers = tile_inputs(
        cpu_fixture, width, height, start_row
    )
    saved = list(cpu.d)[2:6]
    before = bytes(memory[destination : destination + 0x8000])
    advance = sequencer(cpu, memory, write)
    extents = []
    for y in range(height):
        for x in range(width):
            trace = advance(0x68A0 if (x, y) == (0, 0) else None, stop=0x68F8)
            assert trace.stop_reason == 1
            source = pointers[((start_row + y) % 3) * width + x]
            target = destination + 2560 * y + 2 * x
            assert read(CUSTOM + 0x50) == source and read(CUSTOM + 0x54) == target
            assert read(CUSTOM + 0x40, 2) == 0x09F0
            assert read(CUSTOM + 0x46, 2) == 0xFFFF
            assert read(CUSTOM + 0x64, 2) == 0 and read(CUSTOM + 0x66, 2) == 38
            assert read(CUSTOM + 0x58, 2) == 0x1001 and read(CUSTOM + 0x9C, 2) == 0x40
            assert cpu.a[5] == CUSTOM and cpu.d[4] == target
            # One-word rows, 64 rows: 128 packed source bytes; destination
            # advances 2+38 bytes per row. The last row has no following modulo.
            extents.append((source, source + 128, target, target + 63 * 40 + 2))
            if (x, y) != (width - 1, height - 1):
                assert advance(stop=0x68FA).stop_reason == 1
    assert advance().stop_reason == 1
    assert list(cpu.d)[2:6] == saved and cpu.a[7] == 0x9004
    assert cpu.a[2] == grid + ((start_row + height) % 3) * stride
    assert cpu.a[4] == destination + height * 2560
    assert cpu.a[5] == destination + (height - 1) * 2560 + 2 * width
    assert bytes(memory[destination : destination + 0x8000]) == before
    end = max(e[3] for e in extents) - destination
    assert end == (height - 1) * 2560 + 2 * (width - 1) + 2522
    if width == 20:
        assert end == height * 2560
    # Extents beyond the original 20-column/8-row view are unchecked by the
    # helper. These synthetic calls do not establish caller admission or DMA.
    if width > 20:
        assert end > 2560
    if height > 8:
        assert end > 20480


@pytest.mark.parametrize(("width", "height"), [(0, 1), (1, 0), (0, 0)])
def test_zero_tile_dimensions_underflow_before_first_packet(cpu_fixture, width, height):
    cpu, memory, schemas, read, write, run = cpu_fixture
    tile_inputs(cpu_fixture, width, height, 0)
    write(CUSTOM + 0x58, 0x1234, 2)
    run(0x68A0, stop=0x68C4)
    assert cpu.d[0] & 65535 == (width - 1) & 65535
    assert cpu.d[1] & 65535 == (height - 1) & 65535
    assert cpu.d[2] & 65535 == (width - 1) & 65535
    assert read(CUSTOM + 0x58, 2) == 0x1234


def test_tile_wait_stalls_before_packet_and_final_start_has_no_following_wait(
    cpu_fixture,
):
    cpu, memory, schemas, read, write, run = cpu_fixture
    tile_inputs(cpu_fixture, 1, 1, 0)
    write(CUSTOM + 0x1E, 0, 2)
    write(CUSTOM + 0x58, 0x1234, 2)
    advance = sequencer(cpu, memory, write)
    assert advance(0x68A0, stop=0x68F8, budget=64).stop_reason == 3
    assert read(CUSTOM + 0x58, 2) == 0x1234
    write(CUSTOM + 0x1E, 0x40, 2)
    assert advance(stop=0x68F8).stop_reason == 1
    write(CUSTOM + 0x1E, 0, 2)
    assert advance().stop_reason == 1
    assert cpu.a[7] == 0x9004


@pytest.mark.parametrize("entry", [0x691E, 0x6A1E, 0x6B18, 0x6C60])
@pytest.mark.parametrize("height", [0, 1, 48, 49])
def test_masked_packets_keep_world_and_scratch_stride_relationships(
    cpu_fixture, entry, height
):
    cpu, memory, schemas, read, write, run = cpu_fixture
    metadata = effective_target_metadata(resolve_project_paths(TARGET).target_dir)
    scratch = BASE + next(
        l.source_start
        for l in metadata.data_block_layouts
        if l.name == "cursor_sprite_initial_rows_shared_scratch"
    )
    pixels, mask, destination = 0x82000, 0x83000, 0x70000
    cpu.a[0], cpu.a[1], cpu.a[2], cpu.a[3], cpu.a[5] = (
        pixels,
        mask,
        destination,
        0x86000,
        0x84000,
    )
    saved_a = list(cpu.a)[:7]
    cpu.d[4], cpu.d[5], cpu.d[6], cpu.d[7] = 0x12348001, 16, 4, height
    write(CUSTOM + 0x1E, 0x40, 2)
    write(CUSTOM + 0x58, 0x1234, 2)
    run(entry, budget=4096)
    assert list(cpu.a)[:7] == saved_a and cpu.a[7] == 0x9004
    # Original MOVEM.W restores sign-extended words, rather than full LONGs.
    # The aligned entry zeroes D6 before saving the WORD register list.
    assert list(cpu.d)[4:8] == [0xFFFF8001, 16, 0 if entry == 0x691E else 4, height]
    if height == 0:
        assert read(CUSTOM + 0x58, 2) == 0x1234
    elif entry in (0x691E, 0x6A1E):
        words = 1 if entry == 0x691E else 2
        assert read(CUSTOM + 0x58, 2) == (height << 6) | words
        assert read(CUSTOM + 0x50) == mask and read(CUSTOM + 0x4C) == pixels + 6
        assert read(CUSTOM + 0x54) == destination + 120
        assert read(CUSTOM + 0x60, 2) == read(CUSTOM + 0x66, 2) == 160 - 2 * words
        assert read(CUSTOM + 0x64, 2) == 4 - 2 * words
        assert read(CUSTOM + 0x62, 2) == 16 - 2 * words
    else:
        second = entry == 0x6C60
        assert read(CUSTOM + 0x58, 2) == ((height * 4) << 6) | 1
        assert read(CUSTOM + 0x50) == scratch + 2 * second
        assert read(CUSTOM + 0x54) == destination
        assert read(CUSTOM + 0x64, 2) == 2 and read(CUSTOM + 0x66, 2) == 38
        rows = read(CUSTOM + 0x58, 2) >> 6
        stride = 2 + read(CUSTOM + 0x64, 2)
        last_read = read(CUSTOM + 0x50) + (rows - 1) * stride + 2
        assert last_read == scratch + 16 * height - (0 if second else 2)
        # 49 is intentionally accepted by the helper and exceeds the earlier
        # original-frame bound. No pixel DMA or scratch allocation is inferred.
        assert (last_read <= scratch + 768) == (height <= 48)
