"""Canonical owner endpoints are address expressions, never memory extents."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact
from tests.test_app_cursor_predecrement import frame_artifact
from amiga_reversing.disasm import c_backend


def exact_source(artifact, original):
    source = artifact.inline_source_text_with_profile()[0]
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', source,
        include_dir=c_backend.PROJECT_ROOT / 'ext/amiga_includes/ndk_2.0/include')
    assert rebuilt == original
    return source


@pytest.mark.parametrize('displacement', [0x9C, 0xAC])
def test_known_base_names_start_or_one_past_end(tmp_path, displacement):
    artifact, original = frame_artifact(tmp_path,
        f'lea.l ${displacement:X}(a2),a3', seeded=True)
    try:
        source = exact_source(artifact, original)
        line = next(s for s in source.splitlines() if '\tlea.l ' in s)
        assert 'saved_frame' in line
        assert ('saved_frame+' in line) == (displacement == 0xAC)
        # Exact reassembly checks the numeric addend as well as the name.
        assert '(a2),a3' in line
    finally:
        artifact.close()


@pytest.mark.parametrize('operation', ['move.w $AC(a2),d0', 'lea.l $AE(a2),a3'])
def test_endpoint_memory_or_beyond_owner_does_not_gain_endpoint_expression(tmp_path, operation):
    artifact, original = frame_artifact(tmp_path, operation, seeded=True)
    try:
        source = exact_source(artifact, original)
        line = next(s for s in source.splitlines() if s.startswith('\tmove.w ') or s.startswith('\tlea.l '))
        assert 'saved_frame' not in line
    finally:
        artifact.close()


def test_unknown_hardware_collision_at_endpoint_is_not_a_base_proof(tmp_path):
    artifact, original = frame_artifact(tmp_path, 'lea.l $A0(a6),a3', extent=4)
    try:
        line = next(s for s in exact_source(artifact, original).splitlines() if '\tlea.l ' in s)
        assert 'saved_frame' not in line
    finally:
        artifact.close()


def test_foreign_library_base_does_not_gain_an_app_endpoint(tmp_path):
    artifact, original = cursor_artifact(tmp_path, 'lea.l $AC(a2),a3', regions=False,
        metadata_extra=dict(rsset_layout_regions=[dict(layout_name='app', offset=0x9C,
            size=16, storage_kind='byte_array', symbol='saved_frame')],
            entry_register_seeds=[dict(hunk=0, entry_offset=0, register='A2',
                kind='library_base', library_name='timer.device')]))
    try:
        line = next(s for s in exact_source(artifact, original).splitlines() if '\tlea.l ' in s)
        assert 'saved_frame' not in line
    finally:
        artifact.close()


@pytest.mark.parametrize('adjacent', [False, True])
def test_ambiguous_endpoint_views_do_not_pick_an_owner(tmp_path, adjacent):
    other = dict(layout_name='app', offset=0xAC if adjacent else 0x98,
                 size=4 if adjacent else 20, symbol='other_owner', storage_kind='byte_array')
    artifact, original = cursor_artifact(tmp_path, 'lea.l $AC(a2),a3', source_reg='a2', seeded=True,
        metadata_extra=dict(rsset_layout_regions=[dict(layout_name='app', offset=0x9C,
            size=16, symbol='saved_frame', storage_kind='byte_array'), other]))
    try:
        line = next(s for s in exact_source(artifact, original).splitlines() if '\tlea.l ' in s)
        assert 'saved_frame+' not in line
        assert 'other_owner+' not in line
        if adjacent:
            assert 'other_owner(a2)' in line
    finally:
        artifact.close()


def test_existing_weak_app_interpretation_can_name_unambiguous_nonhardware_end(tmp_path):
    artifact, original = cursor_artifact(tmp_path, 'lea.l $720(a6),a1', regions=False,
        metadata_extra=dict(rsset_layout_regions=[dict(layout_name='app', offset=0x71C,
            size=4, symbol='score', storage_kind='scalar')]))
    try:
        source = exact_source(artifact, original)
        line = next(s for s in source.splitlines() if '\tlea.l ' in s)
        assert 'score+' in line
        ref, = artifact.analysis_payload()[0]['sections'][0]['app_slot_refs']
        assert ref['access'] == 'address'
        assert ref['displacement'] == 0x720
        assert ref['base_evidence'] == 'a6_fallback' # naming is not a proof upgrade
    finally:
        artifact.close()


@pytest.mark.parametrize(('body', 'extra'), [
    ('lea.l $720(a4),a1', {}),
    ('movea.l #$DFF000,a6\n lea.l $720(a6),a1', {}),
    ('lea.l $720(a6),a1', dict(entry_register_seeds=[dict(hunk=0, entry_offset=0,
        register='A6', kind='library_base', library_name='timer.device')])),
])
def test_endpoint_naming_does_not_create_app_identity(tmp_path, body, extra):
    metadata = dict(rsset_layout_regions=[dict(layout_name='app', offset=0x71C,
        size=4, symbol='score', storage_kind='scalar')]);metadata.update(extra)
    artifact, original = cursor_artifact(tmp_path, body, regions=False, metadata_extra=metadata)
    try:
        source = exact_source(artifact, original)
        line = next(s for s in source.splitlines() if '\tlea.l ' in s)
        assert 'score' not in line
    finally:
        artifact.close()
