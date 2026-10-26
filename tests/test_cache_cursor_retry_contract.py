"""A local cursor/retry invariant is distinct from physical app-store alias proof."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact, derived_refs


@pytest.mark.parametrize('intervening,expected', [
    ('', True),
    ('move.w #0,other.l', True),
    ('bsr.w helper', True),
    ('move.w #2,$120(a6)', False),
    ('jsr (a3)', False),
])
def test_local_cache_word_quick_update_and_retry(tmp_path, intervening, expected):
    artifact, original = cursor_artifact(tmp_path, '''lea.l $C3E(a6),a1
 move.l a1,holder.l
 '''+intervening+'''
 move.w #19,d7
head:
 movea.l holder.l,a0
 movem.w (a0),d1-d3
 addq.w #6,a0
 move.l a0,holder.l
 tst.w d0
 beq.w done
 subq.l #6,holder.l
 bra.w head
done:
 dbf d7,head
 rts
helper:
 rts
holder:
 dc.l 0
other:
 dc.l 0''')
    try:
        analysis = artifact.analysis_payload()[0]
        ranges = [r for r in derived_refs(artifact)
                  if r.get('loop_iteration_count') and r['base_register']=='A0']
        assert bool(ranges) == expected
        if expected:
            assert len(ranges) == 1
            assert ranges[0]['loop_iteration_count'] == 20
            assert ranges[0]['loop_iteration_stride'] == 6
            assert ranges[0]['data_access_size'] == 6
        assert not analysis['incomplete_analysis']
        from amiga_reversing.disasm import c_backend
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',
            artifact.inline_source_text_with_profile()[0])[0] == original
    finally:
        artifact.close()
