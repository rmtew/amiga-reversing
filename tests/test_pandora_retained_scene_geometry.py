"""Retained geometry storage and original readers under supplied state only."""
import pytest

from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import resolve_project_paths
from tests.test_pandora_state_transitions import BASE, TARGET, cpu_fixture


@pytest.mark.parametrize('offset', [0x4C376, 0x4C816, 0x4C828, 0x4C83A])
def test_original_retained_scene_headers_supply_pixels_masks_and_bounds(cpu_fixture, offset):
    cpu, memory, schemas, read, write, run = cpu_fixture
    metadata = effective_target_metadata(resolve_project_paths(TARGET).target_dir)
    pixels = [layout for layout in metadata.data_block_layouts
              if layout.name and layout.name.startswith('scene_pixel_cells_for_mask_bank_')]
    generated_masks = [equate for equate in metadata.target_equates
                       if equate.group == 'scene_generated_masks' and equate.extent_bytes]
    frame, state, descriptor = BASE + offset, 0x81000, 0x81100
    pixel, mask = read(frame), read(frame + 4)
    stride, height, width, x_offset, y_offset = [read(frame + member, 2)
                                              for member in (8, 10, 12, 14, 16)]
    assert stride in (1, 2) and 0 < height <= 48
    assert any(BASE + bank.source_start <= pixel and
               pixel + 8 * stride * height <= BASE + bank.source_end for bank in pixels)
    if offset == 0x4C816:
        # This stored mask is inside source bank 51, not a generated-mask EQU.
        bank = next(bank for bank in pixels if bank.name.endswith('_51'))
        assert mask == BASE + bank.source_start + 0x30
        assert mask + 2 * stride * height <= BASE + bank.source_end
    else:
        assert any(bank.value <= mask and mask + 2 * stride * height <=
                   bank.value + bank.extent_bytes for bank in generated_masks)
    sf, df = schemas['world_position_state_record'], schemas['world_position_descriptor_prefix']
    write(state + sf['current_geometry_ptr'], frame)
    write(state + sf['position_descriptor_ptr'], descriptor)
    write(state + sf['world_x_offset'], 11, 2)
    write(state + sf['world_y_offset'], 13, 2)
    write(descriptor + df['world_x'], 50, 2)
    write(descriptor + df['world_y'], 70, 2)
    cpu.a[0] = state
    before = bytes(memory[frame:frame + 18])
    run(0x6F6E, stop=0x6FB6)
    assert (cpu.a[2], cpu.a[3], cpu.a[4]) == (frame, pixel, mask)
    y = (83 + y_offset) & 0xFFFF
    assert cpu.d[2] == (((61 + x_offset + width) & 0xFFFF) << 16) | 61
    assert cpu.d[3] == (((y + height) & 0xFFFF) << 16) | y
    assert memory[frame:frame + 18] == before


def test_original_player_positive_x_held_path_selects_original_header(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    node, state = BASE + 0x4C744, 0x81000
    # Locate from the original frame-sequence pointer, not the restored label.
    assert read(node + 6) == BASE + 0x4C756
    assert read(read(node + 6)) == BASE + 0x4C376
    write(state + 8, node)
    write(node + 10, read(node + 10, 1) | 1, 1)
    cpu.a[4] = state
    run(0x951A)
    assert read(state) == BASE + 0x4C376


def test_retained_feedback_pointer_matches_original_clear_target(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    retained = read(BASE + 0x48606)
    assert retained == BASE + 0x48588
    run(0x7B6E)
    assert read(cpu.a[0]) == read(cpu.a[1]) == retained
    # The clear routine selects the header directly; this does not extend the
    # eight-entry indexed feedback table into its retained trailing pointer.
