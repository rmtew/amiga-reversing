"""Original collision predicate and palette-stack control; no reachability claim."""
from __future__ import annotations

import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_render_order import sequencer

pytestmark = pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)


@pytest.mark.parametrize('point, expected', [
    ((91, 199), True), ((109, 217), True), ((100, 208), True),
    ((90, 208), False), ((110, 208), False),
    ((100, 198), False), ((100, 218), False),
    ((89, 208), False), ((100, 219), False),
])
def test_collision_uses_strict_unsigned_geometry_bounds(cpu_fixture, point, expected):
    cpu, memory, schemas, read, write, run = cpu_fixture
    obj, desc, state, geom = [schemas[n] for n in [
        'world_object_shared_prefix', 'world_position_descriptor_prefix',
        'world_position_state_record', 'world_position_collision_bounds']]
    o, p, s, g = 0x90000, 0x90080, 0x90100, 0x90140
    write(o+obj['position_descriptor_ptr'], p)
    write(p+desc['position_state_ptr'], s)
    write(s+state['current_geometry_ptr'], g)
    for address, value in [(p+desc['world_x'], 100), (p+desc['world_y'], 200),
                           (s+state['world_x_offset'], -8), (s+state['world_y_offset'], 4),
                           (g+geom['world_x_origin_offset'], -2), (g+geom['world_y_origin_offset'], -6),
                           (g+geom['world_x_extent'], 20), (g+geom['world_y_extent'], 20),
                           (0x5C322+obj['world_x'], point[0]-16),
                           (0x5C322+obj['world_y'], point[1]-31)]:
        write(address, value & 0xFFFF, 2)
    cpu.a[5] = o
    cpu.d[0:3] = [0x12345678, 0xAABBCCDD, 0x77889900]
    cpu.a[0:3] = [0x81234, 0x82345, 0x83456]
    before_d, before_a = list(cpu.d[:3]), list(cpu.a[:3])
    run(0x268E)
    assert bool(cpu.sr & 1) is expected
    assert list(cpu.d[:3]) == before_d and list(cpu.a[:3]) == before_a
    assert cpu.a[4] == 0x5C322 and cpu.a[5] == o


@pytest.mark.parametrize('site, size', [(0x71E0, 2), (0x71EE, 2), (0x7220, 2), (0x7230, 4)])
@pytest.mark.parametrize('following_word', [0, 0xC0DE])
def test_palette_helper_splices_return_word_instead_of_balanced_bsr_return(cpu_fixture, site, size, following_word):
    cpu, memory, schemas, read, write, run = cpu_fixture
    advance = sequencer(cpu, memory, write)
    write(0x9000, following_word, 2)
    trace = advance(site, budget=4)  # BSR, MOVE.L, ADDQ.L, RTS; no fetch at new target.
    assert trace.stop_reason == 3 and trace.steps == 4
    low_return = (BASE+site+size) & 0xFFFF
    assert cpu.pc == (low_return << 16) | following_word
    assert cpu.a[7] == 0x9002
    assert read(0x8FF8) == BASE+0x34C2  # Pointer push remains below the consumed return.
    bus_target = cpu.pc & 0xFFFFFF
    assert not BASE <= bus_target < BASE+0x55370


@pytest.mark.parametrize('render_prefix', [False, pytest.param(True, marks=pytest.mark.xfail(
    strict=True, reason='Original CLR.W -(A7) currently writes at SP without applying predecrement; do not trust this complete prefix trace.'))])
def test_palette_wrapper_prefix_before_first_spliced_return(cpu_fixture, render_prefix):
    cpu, memory, schemas, read, write, run = cpu_fixture
    advance = sequencer(cpu, memory, write)
    colors = [(i*0x123) & 0xFFFF for i in range(16)]
    tail = b''.join(v.to_bytes(2, 'big') for v in colors)
    memory[0x77FE0:0x78000] = tail
    memory[BASE+0x3462:BASE+0x34E2] = b'\xA5'*128
    offset = 10 if render_prefix else 0
    write(0x9000+offset, 0xC0DE, 2)
    start, call = (0x71AC, 0x71E0) if render_prefix else (0x7216, 0x7220)
    assert advance(start, stop=call).stop_reason == 1
    assert cpu.a[7] == 0x9000+offset
    assert cpu.a[1] == 0x77FE0 and cpu.d[7] == 15
    assert bytes(memory[0x77FE0:0x78000]) == tail
    if render_prefix:
        assert cpu.a[4] == 0x77FDE
        assert bytes(memory[BASE+0x3462:BASE+0x34E2]) == bytes(128)
    else:
        assert bytes(memory[BASE+0x34C2:BASE+0x34E2]) == tail
        expected = [part for word in colors for part in
                    [((word >> 8) & 15) << 4, ((word >> 4) & 15) << 4, (word & 15) << 4]]
        assert [read(BASE+0x3462+2*i, 2) for i in range(48)] == expected
    # Execute only the BSR + three helper instructions, not the escaped target.
    assert advance(budget=4).stop_reason == 3
    assert cpu.pc == (((BASE+call+2) & 0xFFFF) << 16) | 0xC0DE
    assert cpu.a[7] == 0x9002+offset
