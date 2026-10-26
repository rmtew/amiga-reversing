"""A known pointee field outranks an inferred global app-name coincidence."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact


@pytest.mark.parametrize('explicit', [False, True])
def test_exec_field_overrides_app_guess_but_not_explicit_use_site(tmp_path, explicit):
    metadata = dict(
        entry_register_seeds=[dict(hunk=0, entry_offset=6, register='A6', kind='struct_ptr',
            struct_name='ExecBase', note='The original preceding LONG load is from SysBase location4.')],
        rsset_layout_regions=[dict(layout_name='app', offset=0x127, size=1,
            storage_kind='byte_array', symbol='coincident_app_byte')])
    if explicit:
        metadata['rsset_use_site_bindings'] = [dict(rsset_use_site_binding_id='chosen-view',
            hunk=0, addr=6, operand_index=1, base_register='A6', displacement=0x127,
            layout_name='app', base_symbol='__amiga_app_base__',
            base_evidence_id='selected-base:A6:__amiga_app_base__',
            access='read-write', width_bytes=1, render_state='linked_gap_or_raw')]
    artifact, original = cursor_artifact(tmp_path, '''movea.l 4.l,a6
 addq.b #1,$127(a6)''', metadata_extra=metadata)
    try:
        typed = artifact.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
        assert any(r['offset']==6 and r['field_name']=='TDNestCnt' for r in typed)
        source = artifact.inline_source_text_with_profile()[0]
        wanted = 'coincident_app_byte' if explicit else 'TDNestCnt'
        assert f'{wanted}(a6)' in source
        from amiga_reversing.disasm import c_backend
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', source,
            include_dir=c_backend.PROJECT_ROOT/'ext/amiga_includes/ndk_2.0/include')[0] == original
    finally:
        artifact.close()
