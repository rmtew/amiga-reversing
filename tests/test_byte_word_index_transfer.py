"""Partial BYTE writes feed the shared low-WORD index domain without memory assumptions."""
import pytest
from tests.test_base_candidates import candidate_artifact
from tests.test_masked_word_index_fields import metadata
from tests.test_typed_index_symbol_compensation import exact


@pytest.mark.parametrize('prefix',[
    'moveq.l #0,d0\n move.b (a1)+,d0',
    'clr.w d0\n move.b (a1)+,d0',
    'clr.l d0\n move.b (a1)+,d0',
    'moveq.l #0,d0\n move.b d7,d0',
    'moveq.l #0,d0\n move.b #255,d0',
    'moveq.l #0,d2\n move.b (a1)+,d2\n move.w d2,d0',
    'moveq.l #0,d0\n move.b (a1)+,d0\n move.b d0,d0',
    'moveq.l #0,d0\n move.b (a1)+,d0\n clr.b d0',
    'clr.w d0', 'clr.l d0',
    'move.w #$8000,d0\n move.b (a1)+,d0',  # doubling wraps the WORD to 0..510
    'moveq.l #0,d0\n tst.w d7\n beq.s other\n move.b (a1)+,d0\n bra.s joined\nother: move.b d6,d0\njoined:',
])
def test_zero_extended_bytes_bound_a_word_table_index(tmp_path,prefix):
    with candidate_artifact(tmp_path,prefix+'\n add.w d0,d0\n move.w 0(a0,d0.w),d2\n rts',[],
            metadata(count=256,size=2,offset=0,width=2))as(a,raw):
        p=a.analysis_payload()[0];assert not p['incomplete_analysis']
        refs=[r for r in p['sections'][0]['recovered_platform_typed_accesses']if r['field_name']=='value']
        assert len(refs)==1
        exact(a,raw,tmp_path)


@pytest.mark.parametrize('prefix,count,index',[
    ('move.b (a1)+,d0',256,'w'),
    ('clr.b d0\n move.b (a1)+,d0',256,'w'),
    ('move.w #$4000,d0\n move.b (a1)+,d0',256,'w'),
    ('move.w #$100,d0\n clr.b d0',256,'w'),
    ('moveq.l #0,d0\n move.b (a1)+,d0',255,'w'),
    ('moveq.l #0,d0\n move.b (a1)+,d0\n jsr (a3)',256,'w'),
    ('moveq.l #0,d0\n move.b (a1)+,d0\n move.w d7,d0',256,'w'),
    ('moveq.l #0,d0\n move.b (a1)+,d0\n movem.w (a1),d0',256,'w'),
    ('moveq.l #0,d0\n tst.w d7\n beq.s joined\n move.w #$100,d0\njoined: move.b (a1)+,d0',256,'w'),
    ('moveq.l #0,d0\n move.b (a1)+,d0',256,'l'),
])
def test_unknown_upper_bits_calls_owner_extent_and_index_width_refuse(tmp_path,prefix,count,index):
    with candidate_artifact(tmp_path,prefix+f'\n add.w d0,d0\n move.w 0(a0,d0.{index}),d2\n rts',[],
            metadata(count=count,size=2,offset=0,width=2))as(a,raw):
        p=a.analysis_payload()[0];assert not p['incomplete_analysis']
        assert not [r for r in p['sections'][0]['recovered_platform_typed_accesses']if r['field_name']=='value']
        exact(a,raw,tmp_path)
