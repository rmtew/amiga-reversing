"""A directory's typed pointee must not require a later memory read."""
import pytest
from amiga_reversing.disasm import c_backend
from tests.test_source_pointer_loop_domain import header_table_artifact


def test_constant_selected_pointer_exposes_write_only_record_field(tmp_path):
    artifact, original = header_table_artifact(tmp_path, count=104, loop=False, indexed=True,
        index_code='move.w #99,d1\n asl.w #2,d1', index_register='d1',
        record_access='move.w #7,2(a0)\n')
    try:
        section = artifact.analysis_payload()[0]['sections'][0]
        assert any(r['field_name'] == 'flags' and r['base_register'] == 'A0'
                   for r in section['recovered_platform_typed_accesses'])
        source = artifact.inline_source_text_with_profile()[0]
        assert 'Header_flags' in source
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', source)[0] == original
    finally:
        artifact.close()


@pytest.mark.parametrize('body,index', [
    ('move.w #1,(a1)', 99), ('jsr (a1)', 99), ('', 104),
])
def test_write_consumer_cannot_override_alias_call_or_directory_bounds(tmp_path, body, index):
    artifact, _ = header_table_artifact(tmp_path, count=104, loop=False, indexed=True,
        body=body, index_code=f'move.w #{index},d1\n asl.w #2,d1', index_register='d1',
        record_access='move.w #7,2(a0)\n')
    try:
        section = artifact.analysis_payload()[0]['sections'][0]
        assert not section['recovered_platform_typed_accesses']
    finally:
        artifact.close()


@pytest.mark.parametrize('selector', [2, 127, 256])
def test_byte_sign_guard_is_not_a_word_directory_bound(tmp_path, selector):
    artifact, original = header_table_artifact(tmp_path, count=2, loop=False, indexed=True,
        index_code=f'move.w #{selector},d1\n tst.b d1\n bmi.w selector_done\n asl.w #2,d1',
        index_register='d1', record_access='move.w #7,2(a0)\n',
        code_tail='selector_done:\n rts\n')
    try:
        section = artifact.analysis_payload()[0]['sections'][0]
        assert not section['recovered_platform_typed_accesses']
        assert not any(r['resolution'] == 'resolved' for r in section['address_values'])
        source = artifact.inline_source_text_with_profile()[0]
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', source)[0] == original
    finally:
        artifact.close()
