"""Declared custom inline records use the same field resolver as typed values."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact


@pytest.mark.parametrize('seeded',[False,True])
@pytest.mark.parametrize('delta,field', [(4, 'DemoRecord_second'), (5, 'DemoRecord_second+1')])
def test_custom_inline_record_interior_field_expression(tmp_path, delta, field, seeded):
    metadata = dict(custom_structs=[dict(name='DemoRecord', size=8, fields=[
        dict(name='first', type='WORD', offset=0, size=2),
        dict(name='second', type='WORD', offset=4, size=2)])],
        rsset_layout_regions=[dict(layout_name='app', offset=0x100, size=8,
            symbol='demo_record', storage_kind='struct_instance', struct_name='DemoRecord')])
    artifact, original = cursor_artifact(tmp_path, f'move.b ${0x100+delta:X}(a6),d0', seeded=seeded, metadata_extra=metadata)
    try:
        source = artifact.inline_source_text_with_profile()[0]
        assert f'demo_record+{field}(a6)' in source
        fields = artifact.analysis_payload()[0]['base_layout_fields']
        assert next(r for r in fields if r['symbol']=='demo_record')['size'] == 8
        from amiga_reversing.disasm import c_backend
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', source)[0] == original
    finally:
        artifact.close()


@pytest.mark.parametrize('seeded',[False,True])
def test_custom_inline_padding_keeps_unknown_offset_buildable(tmp_path, seeded):
    metadata = dict(custom_structs=[dict(name='Padded', size=8, fields=[
        dict(name='first', type='WORD', offset=0, size=2),
        dict(name='last', type='WORD', offset=6, size=2)])],
        rsset_layout_regions=[dict(layout_name='app', offset=0x100, size=8,
            symbol='padded', storage_kind='struct_instance', struct_name='Padded')])
    artifact, original = cursor_artifact(tmp_path, 'move.b $104(a6),d0', seeded=seeded, metadata_extra=metadata)
    try:
        source = artifact.inline_source_text_with_profile()[0]
        # An extent/owner does not invent a named field in its padding.
        assert 'padded+Padded_' not in source
        from amiga_reversing.disasm import c_backend
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', source)[0] == original
    finally:
        artifact.close()


@pytest.mark.parametrize('mode', ['short_extent', 'other_layout', 'pointer'])
@pytest.mark.parametrize('seeded',[False,True])
def test_inline_projection_requires_full_app_instance_contract(tmp_path, mode, seeded):
    region = dict(layout_name='app', offset=0x100, size=8, symbol='object',
                  storage_kind='struct_instance', struct_name='Bounded')
    if mode=='short_extent':
        region['size']=4
    elif mode=='other_layout':
        region.update(layout_name='work', base_symbol='__work_base__')
    else:
        region.update(storage_kind='struct_pointer', pointer_struct='Bounded')
        region.pop('struct_name')
    artifact, original = cursor_artifact(tmp_path, 'move.w $106(a6),d0', seeded=seeded, metadata_extra=dict(
        custom_structs=[dict(name='Bounded', size=8, fields=[dict(name='last', type='WORD', offset=6, size=2)])],
        rsset_layout_regions=[region]))
    try:
        source = artifact.inline_source_text_with_profile()[0]
        line = next(l for l in source.splitlines() if '\tmove.w ' in l)
        assert 'Bounded_last' not in line
        from amiga_reversing.disasm import c_backend
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', source)[0] == original
    finally:
        artifact.close()


@pytest.mark.parametrize('seeded',[False,True])
def test_inline_field_expression_keeps_explicit_use_site_choice(tmp_path, seeded):
    metadata = dict(custom_structs=[dict(name='Explicit', size=8, fields=[
        dict(name='last', type='WORD', offset=6, size=2)])],
        rsset_layout_regions=[dict(layout_name='app', offset=0x100, size=8,
            symbol='object', storage_kind='struct_instance', struct_name='Explicit')],
        rsset_use_site_bindings=[dict(rsset_use_site_binding_id='chosen-view', hunk=0, addr=0,
            operand_index=0, base_register='A6', displacement=0x106, layout_name='app',
            base_symbol='__amiga_app_base__', base_evidence_id='selected-base:A6:__amiga_app_base__',
            access='read', width_bytes=2, render_state='linked_gap_or_raw')])
    artifact, original = cursor_artifact(tmp_path, 'move.w $106(a6),d0', seeded=seeded, metadata_extra=metadata)
    try:
        source = artifact.inline_source_text_with_profile()[0]
        line = next(l for l in source.splitlines() if '\tmove.w ' in l)
        assert 'object' in line and 'Explicit_last' not in line
        from amiga_reversing.disasm import c_backend
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', source)[0] == original
    finally:
        artifact.close()


@pytest.mark.parametrize('seeded',[False,True])
def test_overlapping_inline_views_do_not_choose_a_field(tmp_path, seeded):
    metadata = dict(custom_structs=[dict(name='First', size=8, fields=[
        dict(name='value', type='WORD', offset=4, size=2)]),
        dict(name='Second', size=8, fields=[dict(name='value', type='WORD', offset=2, size=2)])],
        rsset_layout_regions=[dict(layout_name='app', offset=0x100, size=8,
            symbol='first_view', storage_kind='struct_instance', struct_name='First'),
            dict(layout_name='app', offset=0x102, size=8,
            symbol='second_view', storage_kind='struct_instance', struct_name='Second')])
    artifact, original = cursor_artifact(tmp_path, 'move.w $104(a6),d0', seeded=seeded, metadata_extra=metadata)
    try:
        source = artifact.inline_source_text_with_profile()[0]
        line = next(l for l in source.splitlines() if '\tmove.w ' in l)
        assert 'First_value' not in line and 'Second_value' not in line
        from amiga_reversing.disasm import c_backend
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', source)[0] == original
    finally:
        artifact.close()
