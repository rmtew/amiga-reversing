"""Declared inventory identities, not inferred index bounds or live quantities.

Both 104-byte owners retain gaps. Delivered ingredients have no weapon fields;
an advanced delivered pointer must not acquire a fresh inventory interpretation.
"""
import json
from pathlib import Path

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from tests.test_app_cursor_propagation import cursor_artifact
from tests.test_starglider2_text_editor import original_image

INGREDIENTS = {
    29: ('mini_rocket_count', 'Egron Mini Rocket'),
    38: ('flat_diamond_count', 'Flat Diamond'),
    73: ('asteroid_count', 'Asteroid'),
    83: ('vistan_wine_count', 'Cask of Vistan Wine'),
    87: ('nodules_count', 'Cluster of Nodules'),
    100: ('castrobars_count', 'Crate of Castrobars'),
    101: ('mineral_rock_count', 'Lump of Mineral Rock'),
    102: ('nuclear_fuel_count', 'Case of Nuclear Fuel'),
}


@pytest.fixture(scope='module')
def contracts(original_image):
    target = Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    with effective_metadata_file(target) as path:
        md = json.loads(path.read_text())
    records = [r for r in md['custom_structs'] if r['name'] in
               ['SG2IngredientCounts', 'SG2ModelInventoryCounts']]
    regions = [r for r in md['rsset_layout_regions'] if r['symbol'] in
               ['model_type_population_counts', 'taymar_delivered_model_counts_prefix']]
    assert len(records) == len(regions) == 2
    assert all(r['size'] == 104 and r['storage_kind'] == 'struct_instance' for r in regions)
    by_name = {r['name']: r for r in records}
    assert {f['offset']: f['name'] for f in by_name['SG2IngredientCounts']['fields']} == {
        i: value[0] for i,value in INGREDIENTS.items()}
    assert {f['offset']: f['name'] for f in by_name['SG2ModelInventoryCounts']['fields']} == {
        12: 'homing_missile_count', 84: 'energy_cube_launcher_available',
        91: 'bouncing_bomb_count', 98: 'neutron_bomb_count'}
    raw = original_image[0]
    assert set(raw[0x39126-0x1000:0x39126-0x1000+8]) == set(INGREDIENTS)
    names = {**{i: value[1] for i,value in INGREDIENTS.items()},
             12: 'Homing Missile', 84: 'Energy Cube Launcher', 91: 'Bouncing Bomb', 98: 'Neutron Bomb'}
    for i,text in names.items():
        address = 0xF334-0x1000+4*i
        offset = int.from_bytes(raw[address:address+4], 'big')-0x1000
        assert raw[offset:raw.index(b'\0', offset)].decode('ascii') == text
    return dict(custom_structs=records, rsset_layout_regions=regions)


def exact(artifact, original):
    source = artifact.inline_source_text_with_profile()[0]
    assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', source)[0] == original
    return source


@pytest.mark.parametrize('inventory', [False, True])
@pytest.mark.parametrize('seeded', [False, True])
def test_fixed_counter_reads_expose_shared_ingredient_names_and_separate_weapon_fields(tmp_path, contracts, inventory, seeded):
    record = 'SG2ModelInventoryCounts' if inventory else 'SG2IngredientCounts'
    region = next(r for r in contracts['rsset_layout_regions'] if r['struct_name'] == record)
    by_name = {r['name']: r for r in contracts['custom_structs']}
    expected = by_name['SG2IngredientCounts']['fields'][:]
    if inventory: expected += by_name[record]['fields']
    body = f"lea.l ${region['offset']:X}(a6),a0\n" + ''.join(
        f"move.b {f['offset']}(a0),d1\n" for f in expected)
    artifact, original = cursor_artifact(tmp_path, body, seeded=seeded, regions=False, metadata_extra=contracts)
    try:
        accesses = artifact.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
        assert [(r['root_struct_name'], r['field_name']) for r in accesses] == [
            (record, f['name']) for f in expected]
        source = exact(artifact, original)
        for f in by_name['SG2IngredientCounts']['fields']:
            assert 'SG2IngredientCounts_'+f['name']+'(a0)' in source
        if inventory:
            for f in by_name[record]['fields']:
                assert record+'_'+f['name']+'(a0)' in source
    finally: artifact.close()


@pytest.mark.parametrize('inventory', [False, True])
@pytest.mark.parametrize('offset', [0, 85, 104, 105])
def test_padding_and_outside_bytes_gain_no_field(tmp_path, contracts, inventory, offset):
    region = next(r for r in contracts['rsset_layout_regions'] if r['struct_name'] ==
                  ('SG2ModelInventoryCounts' if inventory else 'SG2IngredientCounts'))
    body = f"lea.l ${region['offset']:X}(a6),a0\n move.b {offset}(a0),d1"
    artifact, original = cursor_artifact(tmp_path, body, seeded=True, regions=False, metadata_extra=contracts)
    try:
        section = artifact.analysis_payload()[0]['sections'][0]
        assert not section['recovered_platform_typed_accesses']
        assert any(r['displacement'] == offset for r in section['recovered_platform_unresolved_typed_accesses'])
        exact(artifact, original)
    finally: artifact.close()


@pytest.mark.parametrize('offset', [12, 84, 91, 98])
def test_delivered_ingredient_owner_does_not_borrow_inventory_weapon_fields(tmp_path, contracts, offset):
    body = f'lea.l $B4D(a6),a0\n move.b {offset}(a0),d1'
    artifact, original = cursor_artifact(tmp_path, body, seeded=True, regions=False, metadata_extra=contracts)
    try:
        assert not artifact.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
        exact(artifact, original)
    finally: artifact.close()


@pytest.mark.parametrize('inventory', [False, True])
def test_unknown_index_does_not_acquire_a_directory_bound_from_record_length(tmp_path, contracts, inventory):
    address = 0xAE5 if inventory else 0xB4D
    artifact, original = cursor_artifact(tmp_path,
        f'lea.l ${address:X}(a6),a0\n move.b 0(a0,d0.w),d1', seeded=True,
        regions=False, metadata_extra=contracts)
    try:
        section = artifact.analysis_payload()[0]['sections'][0]
        assert not section['recovered_platform_typed_accesses']
        assert any(r['classification'] == 'indexed_dynamic' for r in section['recovered_platform_unresolved_typed_accesses'])
        exact(artifact, original)
    finally: artifact.close()


def test_cleared_delivered_prefix_leaves_following_app_write_outside_both_count_formats(tmp_path, contracts):
    body = ('lea.l $B4D(a6),a1\n move.w #103,d0\nclear_next: clr.b (a1)+\n'
            'dbf d0,clear_next\n move.b #1,98(a1)')
    artifact, original = cursor_artifact(tmp_path, body, seeded=True, regions=False, metadata_extra=contracts)
    try:
        source = exact(artifact, original)
        write, = [line for line in source.splitlines() if '\tmove.b ' in line]
        assert 'SG2IngredientCounts_' not in write and 'SG2ModelInventoryCounts_' not in write
    finally: artifact.close()
