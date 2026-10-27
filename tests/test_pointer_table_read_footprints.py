"""Typed pointer reads use decoded input EAs, not an updated cursor guess."""
import pytest
from tests.test_runtime_pointer_table_depth import table_artifact


@pytest.mark.parametrize('read', ['movea.l (a0),a1','movea.l (a0)+,a1',
    'movea.l -(a0),a1','movea.l 4(a0),a1','movea.l -4(a0),a1'])
def test_single_long_runtime_table_read_uses_its_effective_address(tmp_path,read):
    artifact,original=table_artifact(tmp_path,'movea.l $200(a2),a0\n '+read+'\n move.l 4(a1),d0')
    try:
        accesses=artifact.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
        assert any(r['base_register']=='A1' and r['field_name']=='world_x' for r in accesses)
        assert not [r for r in accesses if r['base_register']=='A0']
        from amiga_reversing.disasm import c_backend
        source=artifact.inline_source_text_with_profile()[0]
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',source)[0]==original
    finally:
        artifact.close()


@pytest.mark.parametrize('tail', ['addq.l #2,a0\n movea.l (a0),a1',
    'movea.l 2(a0),a1','movea.l (a0)+,a0\n movea.l a0,a1',
    'movea.l -(a0),a0\n movea.l a0,a1'])
def test_misaligned_or_conflicting_read_cannot_invent_pointee_type(tmp_path,tail):
    artifact,_=table_artifact(tmp_path,'movea.l $200(a2),a0\n '+tail+'\n move.l 4(a1),d0')
    try:
        assert not artifact.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
    finally:
        artifact.close()


@pytest.mark.parametrize(('delta','read','valid'), [
    (8,'movea.l -(a3),a0',True), (0,'movea.l 4(a3),a0',True),
    (4,'movea.l -4(a3),a0',True), (0,'movea.l -(a3),a0',False),
    (0,'movea.l 2(a3),a0',False), (8,'movea.l (a3),a0',False),
])
def test_source_table_effective_address_requires_a_whole_aligned_owned_entry(tmp_path,delta,read,valid):
    from tests.test_static_pointer_table_cursor import header_table_artifact
    artifact,original=header_table_artifact(tmp_path,False,initial_delta=delta,read=read)
    try:
        section=artifact.analysis_payload()[0]['sections'][0]
        fields={r['field_name'] for r in section['recovered_platform_typed_accesses']
                if r['base_register']=='A0'}
        assert fields == ({'count','flags'} if valid else set())
        from amiga_reversing.disasm import c_backend
        source=artifact.inline_source_text_with_profile()[0]
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',source)[0]==original
    finally:
        artifact.close()
