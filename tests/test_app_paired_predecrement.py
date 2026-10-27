"""Independent decoded EA updates must not discard a known app cursor."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact, derived_refs


@pytest.mark.parametrize(('op', 'width'), [('abcd', 1), ('sbcd', 1),
    ('addx.w', 2), ('subx.w', 2), ('addx.l', 4), ('subx.l', 4)])
def test_distinct_predecrement_operands_keep_destination_cursor(tmp_path, op, width):
    artifact, original = cursor_artifact(tmp_path,
        f'lea.l $A0(a2),a3\n {op} -(a0),-(a3)\n move.b (a3),d5',
        source_reg='a2', seeded=True, regions=False)
    try:
        refs = [r for r in derived_refs(artifact) if r['access'] != 'address']
        assert [r['displacement'] for r in refs] == [0xA0-width, 0xA0-width]
        assert [r['data_access_size'] for r in refs] == [width, 1]
        assert refs[0]['access'] == 'read-write'
        assert all(r['base_evidence'] == 'register_state' for r in refs)
        from amiga_reversing.disasm import c_backend
        rendered, _ = artifact.inline_source_text_with_profile()
        rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', rendered,
            include_dir=c_backend.PROJECT_ROOT / 'ext/amiga_includes/ndk_2.0/include')
        assert rebuilt == original
    finally:
        artifact.close()


def test_two_known_cursors_update_independently_even_when_their_cells_alias(tmp_path):
    artifact, _ = cursor_artifact(tmp_path, 'lea.l $A0(a2),a3\n lea.l $A0(a2),a4\n'
        'abcd -(a3),-(a4)\n move.b (a3),d0\n move.b (a4),d1',
        source_reg='a2', seeded=True, regions=False)
    try:
        refs = [r for r in derived_refs(artifact) if r['access'] != 'address']
        assert [r['displacement'] for r in refs] == [0x9F]*4
        assert [r['access'] for r in refs] == ['read', 'read-write', 'read', 'read']
        assert refs[0]['offset'] == refs[1]['offset']
        assert refs[0]['operand_index'] != refs[1]['operand_index']
    finally:
        artifact.close()


@pytest.mark.parametrize('body', [
    'lea.l $A0(a2),a3\n abcd -(a3),-(a3)\n move.b (a3),d0',
    'lea.l $A0(a2),a3\n movea.l d0,a3\n abcd -(a0),-(a3)',
    'lea.l $A0(a6),a3\n abcd -(a0),-(a3)', # unowned weak interpretation
])
def test_shared_register_clobber_and_weak_base_still_refuse(tmp_path, body):
    artifact, _ = cursor_artifact(tmp_path, body, source_reg='a2', seeded=True, regions=False)
    try:
        assert not [r for r in derived_refs(artifact) if r['access'] != 'address']
    finally:
        artifact.close()


@pytest.mark.parametrize(('op', 'width'), [('cmpm.b', 1), ('cmpm.w', 2), ('cmpm.l', 4)])
def test_distinct_postincrement_cursors_both_survive(tmp_path, op, width):
    artifact, _ = cursor_artifact(tmp_path,
        f'lea.l $A0(a2),a3\n lea.l $A0(a2),a4\n {op} (a3)+,(a4)+\n'
        ' move.b (a3),d0\n move.b (a4),d1', source_reg='a2', seeded=True, regions=False)
    try:
        refs = [r for r in derived_refs(artifact) if r['access'] != 'address']
        assert [r['displacement'] for r in refs] == [0xA0, 0xA0, 0xA0+width, 0xA0+width]
        assert [r['data_access_size'] for r in refs] == [width, width, 1, 1]
        assert all(r['access'] == 'read' for r in refs)
    finally:
        artifact.close()
