"""Loop exit must-cells require closed effects and fresh external entries."""
import pytest
from tests.test_source_pointer_loop_domain import header_table_artifact, typed_fields
from amiga_reversing.disasm import c_backend


def frame_loop(tmp_path, setup='', body='', count='move.w #7,d2', cursor='lea.l $68000.l,a1'):
    return header_table_artifact(tmp_path, count=104,
        setup='lea.l $60000.l,a6\nmove.l a6,saved_frame.l\n'+setup+'\n'+cursor+'\n'+count+
              '\nclear_words:clr.w (a1)+\n'+body+'\ndbf d2,clear_words\nmovea.l saved_frame.l,a6',
        record_access='move.w (a0)+,d0\nmove.w (a0),d1\nmove.w d0,$40(a6)\n',
        code_tail='unknown:move.b #0,(a2)\nrts\nsaved_frame:dc.l 0\n')


@pytest.mark.parametrize('changes', [
    {}, {'count':'move.w #$32CB,d2'}, {'count':'move.w #$FFFF,d2'},
    {'setup':'tst.w d7\nbeq other\nlea.l $61000.l,a6\nmove.l a6,saved_frame.l\nother:'},
    {'body':'tst.w d7\nbeq skip\nnop\nskip:'},
])
def test_closed_loop_preserves_only_reaching_cells(tmp_path, changes):
    a, original = frame_loop(tmp_path, **changes)
    try:
        assert typed_fields(a) == {('A0', 'count'), ('A0', 'flags')}
        assert not a.analysis_payload()[0]['incomplete_analysis']
        assert c_backend.assemble_platform_source_text_with_c_backend(
            'amiga-raw', a.inline_source_text_with_profile()[0])[0] == original
    finally:
        a.close()


@pytest.mark.parametrize('changes', [
    {'cursor':'lea.l saved_frame-14.l,a1'}, # Last iteration aliases the cell.
    {'cursor':'lea.l saved_frame.l,a1\nadda.l #$1000000,a1'},
    {'cursor':'movea.l d6,a1'},
    {'count':'move.w d6,d2'},
    {'body':'addq.w #1,d2'},
    {'body':'move.b #0,(a2)'},
    {'body':'jsr unknown'},
    {'setup':'lea.l clear_words.l,a5'}, # Independently exposed loop entry.
    {'setup':'tst.w d7\nbeq join_frame\nmove.w #0,saved_frame.l\njoin_frame:'},
    {'setup':'lea.l saved_frame+4.l,sp', 'body':'pea.l 0(pc)\naddq.l #4,sp'},
])
def test_loop_effects_do_not_revive_invalid_or_conflicting_cells(tmp_path, changes):
    a, _ = frame_loop(tmp_path, **changes)
    try:
        assert not typed_fields(a)
    finally:
        a.close()
