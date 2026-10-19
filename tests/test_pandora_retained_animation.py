"""Original retained records under explicit animation-reader preconditions.

No incoming caller is established for these extra variants. CPU selection and
nominal stored spans do not prove gameplay scheduling or graphics DMA reads.
"""
import pytest

from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import resolve_project_paths
from tests.test_pandora_state_transitions import BASE, TARGET, cpu_fixture


@pytest.mark.parametrize('start,count', [(0x4ABD4, 1), (0x4ACFA, 6), (0x4AF24, 5), (0x4B41E, 3)])
def test_original_extra_headers_feed_geometry_reader_and_fit_known_nominal_banks(cpu_fixture, start, count):
    cpu, memory, schemas, read, write, run = cpu_fixture
    metadata = effective_target_metadata(resolve_project_paths(TARGET).target_dir)
    pixels = [l for l in metadata.data_block_layouts if l.name and l.name.startswith('scene_pixel_cells_for_mask_bank_')]
    masks = [e for e in metadata.target_equates if e.group == 'scene_generated_masks' and e.extent_bytes]
    state, descriptor = 0x81000, 0x81100
    sf, df = schemas['world_position_state_record'], schemas['world_position_descriptor_prefix']
    for index in range(count):
        frame = BASE + start + 18 * index
        pixel, mask = read(frame), read(frame + 4)
        stride, height = read(frame + 8, 2), read(frame + 10, 2)
        assert stride in (1, 2) and 0 < height <= 48
        assert any(BASE + l.source_start <= pixel and pixel + 8 * stride * height <= BASE + l.source_end for l in pixels)
        assert any(e.value <= mask and mask + 2 * stride * height <= e.value + e.extent_bytes for e in masks)
        write(state + sf['current_geometry_ptr'], frame)
        write(state + sf['position_descriptor_ptr'], descriptor)
        write(state + sf['world_x_offset'], 11, 2)
        write(state + sf['world_y_offset'], 13, 2)
        write(descriptor + df['world_x'], 50, 2)
        write(descriptor + df['world_y'], 70, 2)
        cpu.a[0] = state
        before = bytes(memory[frame:frame + 18])
        run(0x6F6E, stop=0x6F9E)
        assert (cpu.a[2], cpu.a[3], cpu.a[4]) == (frame, pixel, mask)
        assert cpu.d[1] & 0xFFFF == (83 + read(frame + 16, 2)) & 0xFFFF
        assert memory[frame:frame + 18] == before


def test_original_menial_chain_uses_22_byte_node_then_three_frame_loop(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    state, node, sequence, successor = 0x81000, BASE + 0x4AE1A, BASE + 0x4AE30, BASE + 0x4AE50
    assert (read(node + 4, 1), read(node + 5, 1), read(node + 10, 1)) == (7, 64, 8)
    assert read(node + 6) == sequence and read(node + 18) == successor
    write(state + 8, node);write(state, 0x12345678);cpu.a[4] = state
    for index in range(1, 7):
        previous = read(state)
        run(0x951A);assert read(state) == previous
        run(0x951A);assert read(state) == read(sequence + 4 + 4 * index)
        assert read(state + 8) == node
    previous = read(state)
    run(0x951A);run(0x951A)
    assert read(state + 8) == successor and read(state) == previous
    assert read(successor + 16, 2) == 0 and not read(successor + 10, 1) & 1
    successor_sequence = read(successor + 6)
    for index in [1, 2, 0]:
        run(0x951A)
        assert read(state) == read(successor_sequence + 4 + 4 * index)


def test_original_menial_return_variant_holds_header_after_seven_frames(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    state, node = 0x81000, BASE + 0x4AE72
    sequence = read(node + 6)
    assert (read(node + 4, 1), read(node + 5, 1), read(node + 10, 1)) == (7, 64, 4)
    write(state + 8, node);cpu.a[4] = state
    for index in range(1, 7):
        run(0x951A);run(0x951A)
        assert read(state) == read(sequence + 4 + 4 * index)
    run(0x951A);run(0x951A)
    assert read(state) == read(sequence) and read(node + 10, 1) == 5
    assert read(node + 16, 1) == 6
    for _ in range(3):
        run(0x951A);assert read(state) == read(sequence)


def test_original_gardener_retained_node_loops_without_changing_xy(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    state, node = 0x81000, BASE + 0x4AFD0
    sequence = read(node + 6)
    assert (read(node + 4, 1), read(node + 5, 1), read(node + 10, 1)) == (5, 64, 0)
    assert read(BASE + 0x4AFB6 + 16) == BASE + 0x4AF90
    assert read(BASE + 0x4AFB6 + 12, 2) == 0xFFEB
    write(state + 8, node);write(state + 12, 0x12345678);cpu.a[4] = state
    for index in [1, 2, 3, 4, 0, 1]:
        run(0x951A);run(0x951A)
        assert read(state) == read(sequence + 4 + 4 * index)
        assert read(state + 12) == 0x12345678 and read(node + 10, 1) == 0


def test_additional_fixed_npc_reference_run_targets_existing_frame_starts(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    metadata = effective_target_metadata(resolve_project_paths(TARGET).target_dir)
    starts = set()
    for layout in metadata.data_block_layouts:
        for element in layout.elements:
            if element.type_binding and element.type_binding['bound_type_id'] == 'WorldPositionAnimationFrame':
                starts.update(BASE + layout.source_start + element.offset + 18 * i for i in range(element.array_count or 1))
    pointers = [read(BASE + 0x4C04A + 4 * i) for i in range(15)]
    assert set(pointers) <= starts and len(set(pointers)) == 8
