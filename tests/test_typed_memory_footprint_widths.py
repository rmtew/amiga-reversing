"""Typed fields and diagnostics consume the shared physical memory footprint."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact


def artifact_for(tmp_path, body, flag=False):
    fields = [dict(name='head', type='LONG', offset=0, size=4)]
    if flag:
        fields.append(dict(name='flag', type='UBYTE', offset=8, size=1))
    return cursor_artifact(tmp_path, body, regions=False, metadata_extra=dict(
        custom_structs=[dict(name='Record', size=32, fields=fields)],
        entry_register_seeds=[dict(hunk=0, entry_offset=0, register='A0',
                                  kind='struct_ptr', struct_name='Record', note='Fixture original input contract')]))


@pytest.mark.parametrize('operation', ['bset #7,8(a0)', 'btst #3,8(a0)', 'sf 8(a0)'])
@pytest.mark.parametrize('flag', [False, True])
def test_fixed_width_form_does_not_need_an_explicit_source_suffix(tmp_path, operation, flag):
    artifact, _ = artifact_for(tmp_path, operation, flag)
    try:
        section = artifact.analysis_payload()[0]['sections'][0]
        if flag:
            assert any(r['field_expr'] == 'Record_flag' for r in section['recovered_platform_typed_accesses'])
        else:
            rows = section['recovered_platform_unresolved_typed_accesses']
            assert len(rows) == 1
            assert rows[0]['access_size'] == 1
    finally:
        artifact.close()


def test_interior_movem_diagnostic_uses_the_whole_cross_field_write(tmp_path):
    artifact, _ = artifact_for(tmp_path, 'movem.l d0-d1,2(a0)')
    try:
        section = artifact.analysis_payload()[0]['sections'][0]
        assert not section['recovered_platform_typed_accesses']
        assert section['recovered_platform_unresolved_typed_accesses'][0]['access_size'] == 8
    finally:
        artifact.close()


def test_fixed_movem_keeps_exact_start_identity_without_proving_field_coverage(tmp_path):
    artifact, _ = artifact_for(tmp_path, 'movem.l d0-d1,(a0)')
    try:
        section = artifact.analysis_payload()[0]['sections'][0]
        row, = section['recovered_platform_typed_accesses']
        # This API names the starting field; field_size is not the transfer span.
        assert (row['field_expr'], row['field_size']) == ('Record_head', 4)
        instruction = artifact.query_payload('instructions', section_index=0,
            source_offset=0, end_offset=4, limit=1)['items'][0]
        assert instruction['operand_facts'][1]['bulk_transfer']
        assert instruction['operand_facts'][0]['register_list'] == ['D0', 'D1']
    finally:
        artifact.close()


def test_predecrement_movem_diagnostic_uses_the_full_update(tmp_path):
    artifact, _ = artifact_for(tmp_path, 'movem.l d0-d1,-(a0)')
    try:
        rows = artifact.analysis_payload()[0]['sections'][0]['recovered_platform_unresolved_typed_accesses']
        assert len(rows) == 1
        assert (rows[0]['displacement'], rows[0]['access_size']) == (-8, 8)
    finally:
        artifact.close()


def test_striped_move_is_not_a_contiguous_scalar_field(tmp_path):
    artifact, _ = artifact_for(tmp_path, 'movep.l d0,0(a0)')
    try:
        section = artifact.analysis_payload()[0]['sections'][0]
        assert not section['recovered_platform_typed_accesses']
        assert section['recovered_platform_unresolved_typed_accesses'][0]['access_size'] == 0
    finally:
        artifact.close()


def test_address_formation_keeps_its_existing_symbol_without_claiming_a_span(tmp_path):
    artifact, _ = artifact_for(tmp_path, 'lea 0(a0),a1')
    try:
        assert 'lea.l Record_head' in artifact.inline_source_text_with_profile()[0]
    finally:
        artifact.close()
