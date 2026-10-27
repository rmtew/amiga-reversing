"""Per-operand app footprints keep independent postincrement streams separate."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact


def metadata(destination_size=16):
    return dict(rsset_layout_regions=[
        dict(layout_name='app', offset=0x100, size=destination_size, storage_kind='byte_array', symbol='destination'),
        dict(layout_name='app', offset=0x200, size=16, storage_kind='byte_array', symbol='source')])


@pytest.mark.parametrize('loop', [False, True])
def test_independent_streams_have_two_separate_original_footprints(tmp_path, loop):
    body = 'lea $100(a6),a0\n lea $200(a6),a1\n'
    if loop:
        body += 'moveq #3,d0\ncopy:\n move.l (a1)+,(a0)+\n dbf d0,copy'
    else:
        body += 'move.l (a1)+,(a0)+'
    artifact, _ = cursor_artifact(tmp_path, body, regions=False, seeded=True, metadata_extra=metadata())
    try:
        refs = artifact.analysis_payload()[0]['sections'][0]['app_slot_refs']
        rows = [r for r in refs if r.get('derived') and r['access'] != 'address']
        if loop:
            rows = [r for r in rows if r.get('loop_iteration_count') == 4]
        assert {(r['displacement'], r['access'], r['data_access_size']) for r in rows} == {
            (0x100, 'write', 4), (0x200, 'read', 4)}
        if loop:
            assert all(r['loop_iteration_stride'] == 4 for r in rows)
    finally:
        artifact.close()


@pytest.mark.parametrize('case', ['same_register', 'predecrement', 'short_owner', 'unknown_counter'])
def test_ambiguous_update_or_unproved_envelope_does_not_gain_loop_extent(tmp_path, case):
    op = 'move.l (a1)+,(a0)+'
    if case == 'same_register': op = 'move.l (a0)+,(a0)+'
    if case == 'predecrement': op = 'move.l -(a1),(a0)+'
    counter = 'move.w d7,d0' if case == 'unknown_counter' else 'moveq #3,d0'
    body = f'lea $100(a6),a0\n lea $200(a6),a1\n {counter}\ncopy:\n {op}\n dbf d0,copy'
    artifact, _ = cursor_artifact(tmp_path, body, regions=False, seeded=True,
        metadata_extra=metadata(destination_size=8 if case == 'short_owner' else 16))
    try:
        refs = artifact.analysis_payload()[0]['sections'][0]['app_slot_refs']
        assert not any(r.get('loop_iteration_count') for r in refs)
    finally:
        artifact.close()
