"""Original display identity lookup and stable overlay line-prefix behavior."""
from __future__ import annotations

import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture

ACTORS = [
    (0x4943E, 0x62, 0xA626, 'Wackobrain'),
    (0x4BA66, 0x53, 0xA598, 'Secdroid ALPHA 1'),
    (0x4BABA, 0x57, 0xA5BA, 'Secdroid DELTA 1'),
    (0x4BB0E, 0x58, 0xA5CB, 'Secdroid DELTA 2'),
    (0x4BB62, 0x59, 0xA5DC, 'Secdroid PI'),
    (0x4BBB6, 0x5B, 0xA5E8, 'Secdroid OMEGA'),
    (0x4BC0A, 0x54, 0xA5A9, 'Secdroid ALPHA 2'),
    (0x4C1D2, 0x5D, 0xA5F7, 'Pianist'),
]


@pytest.mark.parametrize('source,item,name_source,text', ACTORS)
def test_restart_resolves_actor_display_id_independently_of_inventory(cpu_fixture, source, item, name_source, text):
    cpu, memory, schemas, read, write, run = cpu_fixture
    obj = BASE+source
    inventory = read(obj+0x14)
    before = bytes(memory[inventory:inventory+8])
    cpu.a[5] = obj
    assert read(obj+0x4A, 1) == item
    run(0xA0E2, stop=0xA0F0)
    assert read(obj) == BASE+name_source
    assert bytes(memory[BASE+name_source:BASE+name_source+len(text)+1]) == text.encode()+b'\0'
    assert read(obj+0x14) == inventory and bytes(memory[inventory:inventory+8]) == before


@pytest.mark.parametrize('prefix', range(7))
@pytest.mark.parametrize('styles', [0, 0x3F])
def test_overlay_reads_only_contiguous_nonnull_line_prefix(cpu_fixture, prefix, styles):
    cpu, memory, schemas, read, write, run = cpu_fixture
    app, descriptor, empty = 0x39FC, 0x7000, 0x82000
    cpu.a[6], cpu.a[5] = app, descriptor
    fields = schemas['ui_overlay_descriptor']
    memory[descriptor:descriptor+44] = bytes(44)
    write(descriptor+fields['line_style_flags'], styles, 1)
    line0 = descriptor+fields['line_0_ptr']
    for index in range(6):
        write(line0+4*index, empty if index < prefix else 0 if index == prefix else 0xFFFFFF)
    before = bytes(memory[descriptor:descriptor+44])
    # Stop before saved A4/D7 are restored so the original traversal is visible.
    run(0x65E0, stop=0x662C, budget=2048)
    assert cpu.a[4] == line0+4*prefix and cpu.d[7] == 6
    assert bytes(memory[descriptor:descriptor+44]) == before
    # A later poison string pointer would exceed fixture RAM if consumed.


def test_six_security_droids_share_saved_art_but_have_distinct_state_records(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    obj, state, node = (schemas[n] for n in ['world_object_shared_prefix', 'world_position_state_record', 'WorldPositionStateNode'])
    actors = [BASE+x[0] for x in ACTORS[1:7]]
    descriptors = [read(a+obj['position_descriptor_ptr']) for a in actors]
    saved = [read(a+obj['saved_position_state_ptr']) for a in actors]
    nodes = [read(a+state['state_node_ptr']) for a in saved]
    assert len(set(descriptors)) == len(set(saved)) == len(set(nodes)) == 6
    assert len({read(a+state['current_geometry_ptr']) for a in saved}) == 1
    assert len({read(a+node['frame_sequence_ptr']) for a in nodes}) == 1
    assert all(read(s+state['position_descriptor_ptr']) == d for s, d in zip(saved, descriptors))
    # Shared frame identities remain generic; an actor name does not grant
    # exclusive ownership of an image or the mutable render-state population.
