"""A slot loads a table cursor; one entry read yields exactly one pointee."""
from tests.test_app_cursor_propagation import cursor_artifact


def table_artifact(tmp_path, body):
    return cursor_artifact(tmp_path, body, source_reg='a2', seeded=True, regions=False,
        metadata_extra=dict(custom_structs=[dict(name='Record',size=8,fields=[
            dict(name='tag',type='UWORD',offset=0,size=2),
            dict(name='world_x',type='LONG',offset=4,size=4)])],
            rsset_layout_regions=[dict(layout_name='app',offset=0x200,size=4,
                storage_kind='pointer_table',pointer_struct='Record',symbol='cursor')]))


def test_cursor_is_not_its_first_object_and_both_entries_are_objects(tmp_path):
    artifact, original = table_artifact(tmp_path,
        'movea.l $200(a2),a0\n tst.l 4(a0)\n'
        ' movea.l (a0)+,a1\n tst.w (a1)\n'
        ' movea.l (a0)+,a3\n tst.w (a3)')
    try:
        accesses = artifact.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
        assert not [r for r in accesses if r['base_register']=='A0'], accesses
        tags = [r for r in accesses if r['owner_struct_name']=='Record' and r['field_name']=='tag']
        assert [r['base_register'] for r in tags] == ['A1','A3']
        from amiga_reversing.disasm import c_backend
        source = artifact.inline_source_text_with_profile()[0]
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',source)[0] == original
    finally:
        artifact.close()


def test_entry_value_no_longer_carries_the_source_table_identity(tmp_path):
    artifact, _ = table_artifact(tmp_path,
        'movea.l $200(a2),a0\n movea.l (a0)+,a1\n'
        ' movea.l (a1),a3\n tst.w (a3)\n tst.w (a1)')
    try:
        accesses = artifact.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
        assert not [r for r in accesses if r['base_register']=='A3'], accesses
        assert any(r['base_register']=='A1' and r['field_name']=='tag' for r in accesses)
    finally:
        artifact.close()



def test_saved_cursor_reload_is_value_transport_not_an_entry_read(tmp_path):
    artifact, _ = table_artifact(tmp_path,
        'movea.l $200(a2),a0\n move.l a0,-(a7)\n suba.l a0,a0\n'
        ' movea.l (a7)+,a0\n tst.l 4(a0)\n movea.l (a0)+,a1\n tst.w (a1)')
    try:
        accesses = artifact.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
        assert not [r for r in accesses if r['base_register']=='A0'], accesses
        assert any(r['base_register']=='A1' and r['field_name']=='tag' for r in accesses)
    finally:
        artifact.close()



def test_register_transport_does_not_consume_a_table_entry(tmp_path):
    artifact, _ = table_artifact(tmp_path,
        'movea.l $200(a2),a0\n move.l a0,d0\n movea.l d0,a3\n'
        ' tst.l 4(a3)\n movea.l (a3)+,a1\n tst.w (a1)')
    try:
        accesses = artifact.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
        assert not [r for r in accesses if r['base_register']=='A3'], accesses
        assert any(r['base_register']=='A1' and r['field_name']=='tag' for r in accesses)
    finally:
        artifact.close()


def test_foreign_library_extension_cannot_supply_an_app_table_contract(tmp_path):
    artifact,_=table_artifact(tmp_path,'movea.l $4.w,a6\n movea.l $200(a6),a0\n movea.l (a0)+,a1\n tst.w (a1)')
    try:
        assert not [r for r in artifact.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
            if r['base_register']=='A1'and r['field_name']=='tag']
    finally:artifact.close()
