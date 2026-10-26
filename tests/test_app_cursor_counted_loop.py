"""Counted loop footprints require CFG, counter and affine cursor evidence."""
from tests.test_app_cursor_propagation import cursor_artifact, derived_refs


def test_original_shape_initializes_both_twenty_triplet_arrays(tmp_path):
    body = '''move.w #19,d7
 lea.l $BC6(a6),a4
 lea.l $78(a4),a5
again:
 move.w d0,(a4)+
 move.w d1,(a4)+
 move.w d2,(a4)+
 clr.l (a5)+
 clr.w (a5)+
 dbf d7,again'''
    artifact, original = cursor_artifact(tmp_path, body)
    try:
        ranges = [r for r in derived_refs(artifact) if r.get('loop_iteration_count')]
        assert len(ranges) == 5
        assert [r['displacement'] for r in ranges] == [0xBC6, 0xBC8, 0xBCA, 0xC3E, 0xC42]
        assert all(r['loop_iteration_count'] == 20 and r['loop_iteration_stride'] == 6 for r in ranges)
        assert [r['data_access_size'] for r in ranges] == [2, 2, 2, 4, 2]
        assert all(r['base_evidence'] == 'a6_fallback' for r in ranges)
        from amiga_reversing.disasm import c_backend
        from amiga_reversing.disasm.app_access_audit import build_app_access_audit
        analysis, _ = artifact.analysis_payload()
        rows = artifact.query_payload('instructions', limit=100)['items']
        report = build_app_access_audit(rows, analysis['base_layout_fields'], app_base=0x20000, identity={})
        indexed = {(s['source_offset'], s['operand_index']): s for s in report['sites']}
        for ref in ranges:
            site = indexed[ref['offset'], ref['operand_index']]
            assert site['footprint_known'] and site['footprint_iteration_count'] == 20
            assert site['footprint_iteration_stride'] == 6
            assert not site['undeclared_intersections'] and not site['undeclared_intersection_patterns']
        rendered, _ = artifact.inline_source_text_with_profile()
        rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', rendered,
            include_dir=c_backend.PROJECT_ROOT / 'ext/amiga_includes/ndk_2.0/include')
        assert rebuilt == original

    finally:
        artifact.close()


import pytest


@pytest.mark.parametrize('case', ['unknown_count', 'counter_modified', 'call', 'conditional_body',
                                 'pointer_reassigned', 'owner_overrun', 'large_owner_overrun', 'extra_entry'])
def test_unproved_count_or_non_affine_body_cannot_claim_loop_footprints(tmp_path, case):
    prefix = 'move.w #19,d7\n lea.l $BC6(a6),a4\n lea.l $78(a4),a5\n'
    body = 'move.w (a5)+,d0\n'
    if case == 'unknown_count': prefix = prefix.replace('move.w #19,d7', 'move.w d1,d7')
    elif case == 'counter_modified': body += 'subq.w #1,d7\n'
    elif case == 'call': body += 'jsr (a0)\n'
    elif case == 'conditional_body': body += 'tst.w d0\n bne done\n'
    elif case == 'pointer_reassigned': body += 'lea.l $C3E(a6),a5\n'
    elif case == 'owner_overrun': prefix = prefix.replace('#19', '#60')
    elif case == 'large_owner_overrun': prefix = prefix.replace('#19', '#65535')
    elif case == 'extra_entry':
        prefix = 'tst.w d0\n bne middle\n' + prefix
        body += 'middle:\n clr.w (a5)+\n'
    artifact, _ = cursor_artifact(tmp_path, prefix + 'again:\n' + body + 'dbf d7,again\ndone:\n nop')
    try:
        assert not [r for r in derived_refs(artifact) if r.get('loop_iteration_count')]
        assert not artifact.analysis_payload()[0]['incomplete_analysis']
    finally:
        artifact.close()


@pytest.mark.parametrize(('counter', 'increment', 'iterations', 'stride'), [
    (0, True, 1, 2), (59, True, 60, 2), (65535, False, 65536, 0),
])
def test_counter_extremes_are_symbolic_bounds_not_iteration_expansion(tmp_path, counter, increment, iterations, stride):
    post = '+' if increment else ''
    body = f'''move.w #{counter},d7
 lea.l $BC6(a6),a4
 lea.l $78(a4),a5
again:
 move.w (a5){post},d0
 dbf d7,again'''
    artifact, _ = cursor_artifact(tmp_path, body)
    try:
        refs = [r for r in derived_refs(artifact) if r.get('loop_iteration_count')]
        ref, = refs
        assert ref['loop_iteration_count'] == iterations
        assert ref['loop_iteration_stride'] == stride
        assert ref['data_access_size'] == 2
        assert not artifact.analysis_payload()[0]['incomplete_analysis']
    finally:
        artifact.close()
