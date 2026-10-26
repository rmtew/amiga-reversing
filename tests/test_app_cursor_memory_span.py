"""Known app cursors retain exact scalar/grouped footprints, not loop bounds."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact, derived_refs


@pytest.mark.parametrize(('tail', 'targets', 'widths'), [
    ('move.b 12(a5),d5', [0xC4A], [1]),
    ('move.b d5,3(a5)', [0xC41], [1]),
    ('move.w (a5)+,d0\n move.l (a5),d1', [0xC3E, 0xC40], [2, 4]),
    ('addq.l #6,a5\n move.w (a5),d0', [0xC44], [2]),
    ('movem.w (a5),d0-d2', [0xC3E], [6]),
    ('movem.l d0-d2,(a5)', [0xC3E], [12]),
    ('movem.w (a5)+,d0-d2\n move.w (a5),d3', [0xC3E, 0xC44], [6, 2]),
])
def test_known_app_cursor_reports_full_preupdate_spans(tmp_path, tail, targets, widths):
    artifact, original = cursor_artifact(tmp_path, 'lea.l $BC6(a6),a4\n lea.l $78(a4),a5\n' + tail)
    try:
        refs = [r for r in derived_refs(artifact) if r['access'] != 'address']
        assert [r['displacement'] for r in refs] == targets
        assert [r['data_access_size'] for r in refs] == widths
        assert all(r['base_evidence'] == 'a6_fallback' for r in refs)
        from amiga_reversing.disasm.app_access_audit import build_app_access_audit
        rows = artifact.query_payload('instructions', limit=100)['items']
        analysis, _ = artifact.analysis_payload()
        audit = build_app_access_audit(rows, analysis['base_layout_fields'], app_base=0x20000, identity={})
        audited = {(r['source_offset'], r['operand_index']): r for r in audit['sites']}
        for ref in refs:
            site = audited[ref['offset'], ref['operand_index']]
            assert site['footprint_known']
            assert site['footprint_width_bytes'] == ref['data_access_size']
            assert site['footprint_source'] == 'native_derived_span'
            assert site['app_attributions'][0]['base_evidence'] == 'a6_fallback'

        for ref in refs:
            assert ref['data_access_size'] == ref['element_width'] * ref['transfer_count']
            row = artifact.row_for_source_offset(section_index=0, offset=ref['offset'])
            item, = [r for r in row['app_slot_refs'] if r.get('derived')]
            assert item['data_access_size'] == ref['data_access_size']
            assert item['element_width'] == ref['element_width']
            assert item['transfer_count'] == ref['transfer_count']
        from amiga_reversing.disasm import c_backend
        rendered, _ = artifact.inline_source_text_with_profile()
        rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', rendered,
            include_dir=c_backend.PROJECT_ROOT / 'ext/amiga_includes/ndk_2.0/include')
        assert rebuilt == original
    finally:
        artifact.close()


@pytest.mark.parametrize('tail', [
    'lea.l $74(a5),a5\n movem.w (a5),d0-d2',
    'movem.w (a5),a5\n move.w (a5),d0',
    'movem.w (a5)+,a5\n move.w (a5),d0',
    'movea.l (a5)+,a5\n move.w (a5),d0',
    'movem.w d0-d2,-(a5)\n move.w (a5),d0',
    'movem.w 0(a5,d0.w),d0-d2',
    'cmpm.w (a5)+,(a5)+\n move.w (a5),d0',
    'adda.w #$FFFF,a5\n move.w (a5),d0',
    'adda.l d0,a5\n move.w (a5),d0',
])
def test_unproved_or_ambiguous_app_span_is_not_admitted(tmp_path, tail):
    artifact, _ = cursor_artifact(tmp_path, 'lea.l $BC6(a6),a4\n lea.l $78(a4),a5\n' + tail)
    try:
        assert not [r for r in derived_refs(artifact) if r['access'] != 'address']
    finally:
        artifact.close()


def test_mutating_loop_join_is_not_a_claim_of_a_bounded_range(tmp_path):
    body = """lea.l $BC6(a6),a4
 lea.l $78(a4),a5
 move.w d1,d7
again:
 move.w (a5)+,d0
 dbf d7,again"""
    artifact, _ = cursor_artifact(tmp_path, body)
    try:
        assert not [r for r in derived_refs(artifact) if r['access'] != 'address']
        assert not artifact.analysis_payload()[0]['incomplete_analysis']
    finally:
        artifact.close()
