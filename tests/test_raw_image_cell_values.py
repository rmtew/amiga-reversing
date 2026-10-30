"""Exact initial raw bytes are local entry values, never global reader seeds."""
import pytest
from tests.test_source_pointer_loop_domain import header_table_artifact, typed_fields
from amiga_reversing.disasm import c_backend


def initial_frame(tmp_path, *, target='raw_binary', initial='$60000', middle='', expose=False):
    setup=('tst.w d7\nbeq use_frame\nlea.l $61000.l,a6\nmove.l a6,saved_frame.l\n'
           'use_frame:\n'+middle+'\nmovea.l saved_frame.l,a6')
    if expose:
        setup='lea.l use_frame.l,a5\n'+setup
    return header_table_artifact(tmp_path,count=104,setup=setup,target_type=target,
        record_access='move.w (a0)+,d0\nmove.w (a0),d1\nmove.w d0,$40(a6)\n',
        code_tail='unknown:move.b #0,(a2)\nrts\nsaved_frame:dc.l '+initial+'\n')


@pytest.mark.parametrize('target', ['raw_binary', 'program'])
def test_raw_image_initial_cell_joins_actual_conditional_writer(tmp_path, target):
    a, original=initial_frame(tmp_path, target=target)
    try:
        assert typed_fields(a)=={('A0','count'),('A0','flags')}
        assert any(r['offset']==0 and r['evidence_kind']=='raw_image_entry' for r in
                   a.analysis_payload()[0]['sections'][0]['code_start_refs'])
        assert c_backend.assemble_platform_source_text_with_c_backend(
            'amiga-raw',a.inline_source_text_with_profile()[0])[0]==original
    finally:a.close()


@pytest.mark.parametrize('changes', [
    {'initial':'directory-$40'}, # Actual initial alias may not be replaced by the writer elsewhere.
    {'middle':'move.w #0,saved_frame.l'},
    {'middle':'move.b #0,(a2)'},
    {'middle':'jsr unknown'},
    {'expose':True},
])
def test_initial_bytes_do_not_bypass_provenance_or_lifetime(tmp_path,changes):
    a,_=initial_frame(tmp_path,**changes)
    try:assert not typed_fields(a)
    finally:a.close()


def test_callee_owns_counter_and_reloads_preserved_cell(tmp_path):
    a,original=header_table_artifact(tmp_path,count=104,
        setup='lea.l $60000.l,a6\nmove.l a6,saved_frame.l\nlea.l $68000.l,a1\n'
              'move.w #7,d2\nclear:clr.w (a1)+\ndbf d2,clear\nbsr initialize\nrts\n'
              'initialize:lea.l directory(pc),a3\nmove.w #103,d4\nmovea.l saved_frame.l,a6',
        record_access='move.w (a0)+,d0\nmove.w (a0),d1\nmove.w d0,$40(a6)\n',
        code_tail='saved_frame:dc.l 0\n')
    try:
        assert typed_fields(a)=={('A0','count'),('A0','flags')}
        assert c_backend.assemble_platform_source_text_with_c_backend(
            'amiga-raw',a.inline_source_text_with_profile()[0])[0]==original
    finally:a.close()


def test_unmodelled_platform_branch_prevents_whole_callee_preservation(tmp_path):
    # Original bytes choose the first path, but a summary without that entry
    # predicate must not silently ignore the alternate TRAP's unknown effects.
    a,_=header_table_artifact(tmp_path,count=104,target_type='raw_binary',
        setup='lea.l $60000.l,a6\nmove.l a6,saved_frame.l\nbsr platform_init\n'
              'movea.l saved_frame.l,a6',
        record_access='move.w (a0)+,d0\nmove.w (a0),d1\nmove.w d0,$40(a6)\n',
        code_tail='platform_init:tst.w platform_flags.l\nbpl alternate\nrts\n'
                  'alternate:trap #1\nrts\nplatform_flags:dc.w $8001\nsaved_frame:dc.l 0\n')
    try:
        section=a.analysis_payload()[0]['sections'][0]
        assert not typed_fields(a)
        assert any(s.get('terminal_reason')=='direct_body_unsupported' for s in section['function_summaries'])
    finally:a.close()


@pytest.mark.parametrize('initial,expected', [('$60000',True), ('directory-$40',False)])
def test_initial_value_of_declared_base_holder_reaches_initializer(tmp_path,initial,expected):
    a,_=header_table_artifact(tmp_path,count=104,target_type='raw_binary',
        setup='tst.w d7\nbeq use_frame\nlea.l $61000.l,a6\nmove.l a6,saved_frame.l\n'
              'use_frame:movea.l saved_frame.l,a1\nmove.w #7,d2\n'
              'clear:clr.w (a1)+\ndbf d2,clear\nbsr initialize\nrts\n'
              'initialize:lea.l directory(pc),a3\nmove.w #103,d4\nmovea.l saved_frame.l,a6',
        record_access='move.w (a0)+,d0\nmove.w (a0),d1\nmove.w d0,$40(a6)\n',
        code_tail='saved_frame:dc.l '+initial+'\n',
        extra_actions=lambda start:[('target.rsset_region.add',dict(offset=0x40,size=2,
            symbol='frame_word',layout_name='app',storage_kind='scalar')),
            ('target.absolute_storage_slot.add',dict(address=0x1000+start-4,
            size=4,symbol='saved_frame',storage_kind='pointer',semantic_type='layout_base:__amiga_app_base__'))])
    try:
        assert bool(typed_fields(a))==expected, typed_fields(a)
        payload=a.analysis_payload()[0]
        assert not payload['incomplete_analysis']
        section=payload['sections'][0]
        assert section['address_values']  # Converged producer evidence, not orphaned type facts.
    finally:a.close()
