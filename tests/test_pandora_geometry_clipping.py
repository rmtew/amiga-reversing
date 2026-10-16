"""Original unsigned clip decisions; CPU only, without chipset scheduling."""

from __future__ import annotations

from itertools import product

import pytest

from tests.test_pandora_state_transitions import cpu_fixture as cpu_fixture

APP = 0x39FC


def test_original_clipper_boundaries_and_packed_coordinate_contract(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    from amiga_reversing.disasm.effective_metadata import effective_target_metadata
    from amiga_reversing.disasm.project_paths import resolve_project_paths
    from tests.test_pandora_state_transitions import TARGET

    slots = {
        s.symbol: s.offset
        for s in effective_target_metadata(
            resolve_project_paths(TARGET).target_dir
        ).rsset_layout_regions
    }
    cpu.a[6] = APP
    write(APP + slots["app_tilemap_scroll_x"], 100, 2)
    write(APP + slots["app_tilemap_scroll_y"], 200, 2)
    # Nonwrapping inclusive rectangle endpoints against half-open view bounds.
    # Equality at left/top survives; equality at right/bottom is outside.
    xs = [
        (a, b)
        for a in [0, 99, 100, 101, 419, 420, 421]
        for b in [99, 100, 101, 419, 420, 421, 500]
        if a <= b
    ]
    ys = [
        (a, b)
        for a in [0, 199, 200, 201, 327, 328, 329]
        for b in [199, 200, 201, 327, 328, 329, 500]
        if a <= b
    ]
    for (left, right), (top, bottom) in product(xs, ys):
        packed_x, packed_y = right << 16 | left, bottom << 16 | top
        cpu.d[2], cpu.d[3] = packed_x, packed_y
        cpu.d[4] = 0xDEADBEEF
        run(0x684A)
        if left >= 420 or right < 100 or top >= 328 or bottom < 200:
            expected = 15
        else:
            expected = (
                (top < 200)
                | ((bottom >= 328) << 1)
                | ((left < 100) << 2)
                | ((right >= 420) << 3)
            )
        assert cpu.d[4] == expected, (left, right, top, bottom)
        if (left, right, top, bottom) == (0, 500, 0, 500):
            assert expected == 15  # Overlaps the whole view but aliases REJECT.
        assert (cpu.d[0], cpu.d[1]) == (420 << 16 | 100, 328 << 16 | 200)
        assert (cpu.d[2], cpu.d[3]) == (packed_x, packed_y)
        assert cpu.a[6] == APP and cpu.a[7] == 0x9004


def test_original_point_helper_swap_clears_carry_and_rejects_interior_points(
    cpu_fixture,
):
    cpu, memory, schemas, read, write, run = cpu_fixture
    from amiga_reversing.disasm.effective_metadata import effective_target_metadata
    from amiga_reversing.disasm.project_paths import resolve_project_paths
    from tests.test_pandora_state_transitions import TARGET

    slots = {
        s.symbol: s.offset
        for s in effective_target_metadata(
            resolve_project_paths(TARGET).target_dir
        ).rsset_layout_regions
    }
    cpu.a[6] = APP
    write(APP + slots["app_tilemap_scroll_x"], 100, 2)
    write(APP + slots["app_tilemap_scroll_y"], 200, 2)
    for x, y in product(
        [0, 99, 100, 101, 419, 420, 65535], [0, 199, 200, 201, 327, 328, 65535]
    ):
        cpu.d[2], cpu.d[3] = x, y
        cpu.d[4] = 0x12340000
        run(0x6828)
        # SWAP D0 at $6836 clears C before BCC at $6838; the low-word
        # rejection value survives even for otherwise interior coordinates.
        assert cpu.d[4] == 0x1234FFFF, (x, y, cpu.d[0], cpu.d[1])
        assert (cpu.d[2], cpu.d[3]) == (x, y)


def test_point_rejection_carry_clobber_with_independent_musashi(cpu_fixture):
    import pytest

    machine68k = pytest.importorskip("machine68k")
    from amiga_reversing.disasm.effective_metadata import effective_target_metadata
    from amiga_reversing.disasm.project_paths import resolve_project_paths
    from tests.test_pandora_state_transitions import BASE, RETURN, TARGET

    cpu, memory, schemas, read, write, run = cpu_fixture
    slots = {
        s.symbol: s.offset
        for s in effective_target_metadata(
            resolve_project_paths(TARGET).target_dir
        ).rsset_layout_regions
    }
    write(APP + slots["app_tilemap_scroll_x"], 100, 2)
    write(APP + slots["app_tilemap_scroll_y"], 200, 2)
    write(0x9000, RETURN)
    machine = machine68k.Machine(machine68k.CPUType.M68000, 1024)
    machine.mem.w_block(0, bytes(memory))
    oracle = machine.cpu

    class Returned(Exception):
        pass

    def stop_at_return(pc):
        if pc == RETURN:
            raise Returned

    oracle.set_instr_hook_callback(stop_at_return)
    for x, y in [(99, 200), (100, 200), (200, 250), (419, 327), (420, 328)]:
        oracle.w_sr(0x2000)
        for reg, value in [
            ("D2", x),
            ("D3", y),
            ("D4", 0x12340000),
            ("A6", APP),
            ("A7", 0x9000),
        ]:
            oracle.w_reg(getattr(machine68k.Register, reg), value)
        oracle.w_pc(BASE + 0x6828)
        with pytest.raises(Returned):
            oracle.execute(10000)
        assert oracle.r_reg(machine68k.Register.D4) == 0x1234FFFF
        assert oracle.r_reg(machine68k.Register.A7) == 0x9004


@pytest.mark.parametrize("cpu_fixture", [0x1000000], indirect=True)
def test_draw_preserves_typed_state_across_all_clip_side_families(cpu_fixture):
    # MMIO is a ready-bit shadow here; no pixels or DMA completion are modeled.
    import ctypes as C

    from amiga_reversing.disasm.effective_metadata import effective_target_metadata
    from amiga_reversing.disasm.project_paths import resolve_project_paths
    from src.tests.test_m68k_simulator_arithmetic import Trace, engine
    from tests.test_pandora_state_transitions import BASE, RETURN, TARGET

    cpu, memory, schemas, read, write, run = cpu_fixture
    buffer = (C.c_uint8 * len(memory)).from_buffer(memory)
    slots = {
        s.symbol: s.offset
        for s in effective_target_metadata(
            resolve_project_paths(TARGET).target_dir
        ).rsset_layout_regions
    }
    state, descriptor, geometry = 0x81000, 0x81100, 0x81200
    sf, df, gf = (
        schemas["world_position_state_record"],
        schemas["world_position_descriptor_prefix"],
        schemas["world_position_collision_bounds"],
    )
    write(state + sf["current_geometry_ptr"], geometry)
    write(state + sf["position_descriptor_ptr"], descriptor)
    write(geometry + gf["bitplane_data_ptr"], 0x82000)
    write(geometry + gf["mask_data_ptr"], 0x83000)
    write(geometry + gf["row_stride_words"], 2, 2)
    write(geometry + gf["world_x_extent"], 31, 2)
    write(geometry + gf["world_y_extent"], 16, 2)
    write(APP + slots["app_back_bitplane_base"], 0x78000)
    write(APP + slots["app_tilemap_scroll_x"], 100, 2)
    write(APP + slots["app_tilemap_scroll_y"], 200, 2)
    for y in range(200):
        write(APP + 2 * y, 160 * y, 2)
    write(0xDFF01E, 0x40, 2)
    for x, y in [
        (100, 200),
        (101, 201),
        (80, 200),
        (95, 190),
        (400, 200),
        (419, 320),
        (50, 200),
        (420, 200),
        (100, 328),
        (100, 180),
    ]:
        write(descriptor + df["world_x"], x, 2)
        write(descriptor + df["world_y"], y, 2)
        write(state + sf["interaction_flags"], 0xA4, 1)
        cpu.a[0], cpu.a[5], cpu.a[6], cpu.a[7] = state, 0x12345678, APP, 0x9000
        write(0x9000, RETURN)
        cpu.pc = BASE + 0x6F6E
        trace = Trace()
        rc = engine()(
            0,
            buffer,
            len(memory),
            C.byref(cpu),
            4096,
            RETURN,
            RETURN + 2,
            None,
            C.byref(trace),
        )
        assert rc == 0 and trace.stop_reason == 1 and not trace.overflow, (
            x,
            y,
            trace.stop_reason,
        )
        assert (cpu.a[0], cpu.a[5], cpu.a[6], cpu.a[7]) == (
            state,
            0x12345678,
            APP,
            0x9004,
        )
        rejected = x >= 420 or x + 31 < 100 or y >= 328 or y + 16 < 200
        assert read(state + sf["interaction_flags"], 1) == 0xA4 | rejected


@pytest.mark.parametrize("source", [0x6E5C, 0x6E72])
def test_previous_geometry_helpers_retain_state_and_origin_registers(
    cpu_fixture, source
):
    cpu, memory, schemas, read, write, run = cpu_fixture
    state, geometry = 0x81000, 0x81200
    sf, gf = (
        schemas["world_position_state_record"],
        schemas["world_position_collision_bounds"],
    )
    write(state + sf["previous_geometry_ptr"], geometry)
    write(state + sf["world_x_offset"], 7, 2)
    write(state + sf["world_y_offset"], 9, 2)
    for name, value in [
        ("world_x_origin_offset", 3),
        ("world_y_origin_offset", 5),
        ("world_x_extent", 31),
        ("world_y_extent", 16),
    ]:
        write(geometry + gf[name], value, 2)
    for i in range(8):
        cpu.d[i] = 0x12340000 + i
        cpu.a[i] = 0x56780000 + i
    cpu.d[0], cpu.d[1], cpu.a[4] = 100, 200, state
    before_d, before_a = list(cpu.d), list(cpu.a)[:7]
    run(source)
    assert [cpu.d[i] for i in [0, 1, 2, 3, 6, 7]] == [
        before_d[i] for i in [0, 1, 2, 3, 6, 7]
    ]
    assert [cpu.a[i] for i in [0, 1, 2, 4, 5, 6]] == [
        before_a[i] for i in [0, 1, 2, 4, 5, 6]
    ]
    assert cpu.a[3] == geometry and cpu.a[7] == 0x9004
    if source == 0x6E5C:
        assert cpu.d[4] & 0xFFFF == 107 and cpu.d[5] & 0xFFFF == 214
    else:
        assert cpu.d[4] == (141 << 16) | (before_d[4] & 0xFFFF)
        assert cpu.d[5] == (230 << 16) | (before_d[5] & 0xFFFF)


def test_top_clipping_retains_original_row_count_arithmetic(cpu_fixture):
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
    state, descriptor, geometry = 0x81000, 0x81100, 0x81200
    sf, df, gf = (
        schemas["world_position_state_record"],
        schemas["world_position_descriptor_prefix"],
        schemas["world_position_collision_bounds"],
    )
    write(state + sf["current_geometry_ptr"], geometry)
    write(state + sf["position_descriptor_ptr"], descriptor)
    write(geometry + gf["bitplane_data_ptr"], 0x82000)
    write(geometry + gf["mask_data_ptr"], 0x83000)
    write(geometry + gf["row_stride_words"], 2, 2)
    write(geometry + gf["world_x_extent"], 31, 2)
    write(geometry + gf["world_y_extent"], 16, 2)
    write(descriptor + df["world_x"], 100, 2)
    write(APP + slots["app_tilemap_scroll_x"], 100, 2)
    write(APP + slots["app_tilemap_scroll_y"], 200, 2)
    for y in [199, 190, 184]:
        write(descriptor + df["world_y"], y, 2)
        cpu.a[0], cpu.a[6] = state, APP
        run(0x6F6E, stop=0x7008)
        # Keep the original +1 in visible = Y+H+1-view_top. Do not silently
        # substitute an idealized half-open clip algorithm for this program.
        visible = y + 16 + 1 - 200
        computed_skip = 16 - visible
        assert cpu.d[7] & 0xFFFF == visible
        assert cpu.a[4] == 0x83000 + 2 * 2 * computed_skip
        assert cpu.a[3] == 0x82000 + 4 * 2 * 2 * computed_skip
        assert cpu.a[2] == geometry
