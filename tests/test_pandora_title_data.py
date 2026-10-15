"""Original bounded title initialization, fade step and indexed glyph copying."""
from __future__ import annotations

import pytest

from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import resolve_project_paths
from tests.test_pandora_state_transitions import BASE, TARGET, cpu_fixture

APP = 0x39FC


@pytest.fixture
def title_slots():
    return {s.symbol: s.offset for s in effective_target_metadata(resolve_project_paths(TARGET).target_dir).rsset_layout_regions}


def test_title_clear_uses_32_gradient_colors_but_only_eight_palette_colors(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = APP
    memory[BASE+0xAC8:BASE+0xAE8] = b'\xA5'*32
    increments = bytes(memory[BASE+0xAE8:BASE+0xAF8])
    gradient_increments = bytes(memory[BASE+0xB68:BASE+0xBA8])
    memory[BASE+0xAF8:BASE+0xB68] = b'\xA5'*112
    run(0xD20, stop=0xD52, budget=2048)
    assert bytes(memory[BASE+0xAC8:BASE+0xAD8]) == bytes(16)
    assert bytes(memory[BASE+0xAD8:BASE+0xAE8]) == b'\xA5'*16
    assert bytes(memory[BASE+0xAF8:BASE+0xB68]) == bytes(112)
    assert bytes(memory[BASE+0xAE8:BASE+0xAF8]) == increments
    assert bytes(memory[BASE+0xB68:BASE+0xBA8]) == gradient_increments
    assert bytes(memory[BASE+0xB3A8:BASE+0xB468]) == bytes(192)


@pytest.mark.parametrize('count,enabled', [(16, True), (1, True), (7, False)])
def test_title_fade_updates_eight_colors_and_counts_service_steps(cpu_fixture, title_slots, count, enabled):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = APP
    # Names are the canonical results of this swath. Tests execute original bytes.
    counter = APP+title_slots['app_title_star_palette_steps_remaining']
    status = APP+title_slots['app_status_flags']
    write(counter, count, 1)
    write(status, 0xA0 | (4 if enabled else 0), 1)
    memory[BASE+0xAC8:BASE+0xAE8] = b'\xA5'*32
    memory[BASE+0xAF8:BASE+0xB28] = bytes(48)
    increments = bytes(memory[BASE+0xAE8:BASE+0xAF8])
    run(0xDB6)
    assert read(counter, 1) == count-int(enabled)
    assert read(status, 1) == (0xA0 | (4 if enabled and count > 1 else 0))
    assert bytes(memory[BASE+0xAD8:BASE+0xAE8]) == b'\xA5'*16
    assert bytes(memory[BASE+0xAE8:BASE+0xAF8]) == increments
    if enabled:
        # One step stores fractional accumulators; these small increments need
        # sixteen services to reach their final integer RGB12 colors.
        for index in range(8):
            packed = int.from_bytes(increments[2*index:2*index+2], 'big')
            expected = [(packed>>8)&15, (packed>>4)&15, packed&15]
            assert [read(BASE+0xAF8+6*index+2*c, 2) for c in range(3)] == expected
    else:
        assert bytes(memory[BASE+0xAC8:BASE+0xAD8]) == b'\xA5'*16
        assert bytes(memory[BASE+0xAF8:BASE+0xB28]) == bytes(48)


def test_title_glyph_index_and_first_raster_cover_uppercase_and_lowercase(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[6] = APP
    cursor_slot = APP+title_slots['app_text_cursor_ptr']
    destination = 0x80000
    for lowercase in [False, True]:
        for index in range(26):
            cpu.d[0], cpu.d[7] = 65+index+(32 if lowercase else 0), 0x12345678
            write(cursor_slot, destination)
            memory[destination:destination+5248] = b'\xA5'*5248
            run(0x7750, stop=0x7786, budget=128)
            glyph = BASE+0xC3A8+128*index
            target = destination+120
            assert bytes(memory[target:target+4]) == bytes(memory[glyph:glyph+4])
            assert read(target-1, 1) == 0xA5 and read(target+4, 1) == 0xA5
            assert cpu.a[0] == glyph+4 and cpu.a[1] == target+160
            assert cpu.d[7] == 31 and read(cursor_slot) == destination
            # This bounded witness stops before DBF. Static D7=31 and the
            # original back edge establish32 rows; no full-copy trace claimed.
