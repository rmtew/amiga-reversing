"""Proven app coordinates are access evidence, not inferred object ownership."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact, derived_refs


@pytest.mark.parametrize(('operation', 'width', 'count'), [
    ('move.b d0,-(a3)', 1, 1), ('move.w d0,-(a3)', 2, 1),
    ('move.l d0,-(a3)', 4, 1), ('movem.w d0-d1/a1-a2,-(a3)', 2, 4),
    ('movem.l d0-d1/a1-a2,-(a3)', 4, 4),
])
def test_proven_unowned_cursor_retains_exact_access_and_update(tmp_path, operation, width, count):
    size = width * count
    artifact, original = cursor_artifact(tmp_path,
        f'lea.l ${0x9C + size:X}(a2),a3\n {operation}\n move.b (a3)+,d5\n move.b (a3),d6',
        source_reg='a2', seeded=True, regions=False)
    try:
        refs = [r for r in derived_refs(artifact) if r['access'] != 'address']
        assert [r['displacement'] for r in refs] == [0x9C, 0x9C, 0x9D]
        assert [r['data_access_size'] for r in refs] == [size, 1, 1]
        assert refs[0]['element_width'] == width
        assert refs[0]['transfer_count'] == count
        assert all(r['base_evidence'] == 'register_state' for r in refs)
        assert not artifact.analysis_payload()[0]['incomplete_analysis']
        from amiga_reversing.disasm import c_backend
        rendered, _ = artifact.inline_source_text_with_profile()
        rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', rendered,
            include_dir=c_backend.PROJECT_ROOT / 'ext/amiga_includes/ndk_2.0/include')
        assert rebuilt == original
    finally:
        artifact.close()


@pytest.mark.parametrize('body', [
    'lea.l $AC(a6),a3\n movem.l d0-d1/a1-a2,-(a3)', # weak fallback without owner
    'lea.l $AC(a2),a3\n movea.l d0,a3\n movem.l d0-d1/a1-a2,-(a3)',
    'lea.l $AC(a2),a3\n movem.l d0-d1/a3,-(a3)\n move.b (a3),d0',
    'lea.l $AC(a2),a3\n movep.l d0,0(a3)',
    'lea.l $AC(a2),a3\n move.w d0,0(a3,d1.w)',
    'lea.l 0(a2),a3\n move.l d0,-(a3)', # negative coordinate, not an app slot
])
def test_unowned_discovery_keeps_existing_evidence_and_footprint_guards(tmp_path, body):
    artifact, _ = cursor_artifact(tmp_path, body, source_reg='a2', seeded=True, regions=False)
    try:
        assert not [r for r in derived_refs(artifact) if r['access'] != 'address']
    finally:
        artifact.close()


def test_direct_grouped_footprint_uses_shared_metadata(tmp_path):
    # Native helper coverage is in the existing decoded-footprint C fixture;
    # this end-to-end site must remain one grouped access, not four fake sites.
    artifact, _ = cursor_artifact(tmp_path, 'movem.l d0-d1/a1-a2,$9C(a2)',
        source_reg='a2', seeded=True, regions=False)
    try:
        refs = artifact.analysis_payload()[0]['sections'][0]['app_slot_refs']
        assert len(refs) == 1
        assert refs[0]['displacement'] == 0x9C
        assert refs[0]['base_evidence'] == 'register_state'
        # The direct catalogue still has no grouped footprint JSON projection;
        # do not treat its normalized scalar declaration as the transfer extent.
    finally:
        artifact.close()


@pytest.mark.parametrize(('extent', 'admitted'), [(4, False), (16, True)])
def test_direct_weak_base_requires_owner_for_whole_group(tmp_path, extent, admitted):
    artifact, _ = cursor_artifact(tmp_path, 'movem.l d0-d1/a1-a2,$9C(a6)',
        regions=False, metadata_extra=dict(rsset_layout_regions=[dict(layout_name='app',
            offset=0x9C, size=extent, storage_kind='byte_array', symbol='frame')]))
    try:
        refs = artifact.analysis_payload()[0]['sections'][0]['app_slot_refs']
        assert bool(refs) == admitted
        if admitted:
            assert refs[0]['base_evidence'] == 'declared_layout_a6_fallback'
    finally:
        artifact.close()


@pytest.mark.parametrize(('other', 'expected'), [('$9C', True), ('$A0', False)])
def test_proven_unowned_cursor_join_keeps_only_agreed_coordinate(tmp_path, other, expected):
    body = f'''tst.w d0
 beq other
 lea.l $9C(a2),a3
 bra joined
other:
 lea.l {other}(a2),a3
joined:
 move.l (a3),d1'''
    artifact, _ = cursor_artifact(tmp_path, body, source_reg='a2', seeded=True, regions=False)
    try:
        reads = [r for r in derived_refs(artifact) if r['access'] == 'read']
        assert bool(reads) == expected
        if expected:
            assert reads[0]['displacement'] == 0x9C
            assert reads[0]['base_evidence'] == 'register_state'
    finally:
        artifact.close()
