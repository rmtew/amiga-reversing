"""Known bits/bounds prove uniform fields without enlarging finite value sets."""
import pytest
from tests.test_base_candidates import candidate_artifact
from tests.test_typed_index_symbol_compensation import exact


def metadata(count=32,size=8,offset=4,width=2):
    return dict(custom_structs=[dict(name='Packet',size=size,fields=[dict(name='value',type='WORD',offset=offset,size=width)])],
        entry_register_seeds=[dict(hunk=0,entry_offset=0,register='A0',kind='struct_ptr',struct_name='Packet',array_length=count,note='Bounded input array')])


@pytest.mark.parametrize('middle,wanted',[
    ('',True),('move.w d0,d2\n move.w d2,d0',True),
    ('ori.w #1,d0',False),('move.b d7,d0',False),('move.w d7,d0',False),
    ('ori.w #256,d0',False),('jsr $4000.l',False),
    ('tst.w d7\n beq.s unchanged\n move.w d7,d0\nunchanged:',False),
    ('bsr.w helper',True),
])
def test_stride_alias_mutation_calls_and_joins(tmp_path,middle,wanted):
    code=f'andi.w #31,d0\n lsl.w #3,d0\n {middle}\n move.w 4(a0,d0.w),d1\n rts\nhelper: rts\n'
    with candidate_artifact(tmp_path,code,[],metadata())as(a,raw):
        p=a.analysis_payload()[0];assert not p['incomplete_analysis']
        refs=[r for r in p['sections'][0]['recovered_platform_typed_accesses']if r['field_name']=='value']
        assert bool(refs)==wanted,p['sections'][0]['recovered_platform_unresolved_typed_accesses']
        if refs:
            evidence=refs[0]['word_index']
            assert evidence['evidence']=='bounded_cfg_mask'
            assert evidence['index_domain']['upper_bound']==248
            assert evidence['record_count']==32
            assert 'byte_offsets'not in evidence  # Never fabricate a singleton or truncate the set.
        exact(a,raw,tmp_path)


@pytest.mark.parametrize('count,size,offset,width,access',[
    (31,8,4,2,'move.w 4(a0,d0.w),d1'),
    (32,8,4,2,'move.l 4(a0,d0.w),d1'),
    (64,7,4,2,'move.w 4(a0,d0.w),d1'),
    (32,8,4,2,'move.w -4(a0,d0.w),d1'),
])
def test_owner_stride_and_cross_field_refusals(tmp_path,count,size,offset,width,access):
    with candidate_artifact(tmp_path,'andi.w #31,d0\n lsl.w #3,d0\n '+access+'\n rts',[],metadata(count,size,offset,width))as(a,raw):
        refs=a.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
        assert not refs
        exact(a,raw,tmp_path)


@pytest.mark.parametrize('prefix',[
    'tst.w d7\n beq.s outside\n andi.w #15,d0\n bra.s joined\noutside: nop\njoined:',
    'andi.w #15,d0\n cmp.w #64,d0\n bge.w outside\n bra.s done\noutside: move.w 0(a0,d0.w),d1\ndone:',
])
def test_unknown_predecessor_and_contradictory_bounds_refuse(tmp_path,prefix):
    code=prefix+'\n move.w 0(a0,d0.w),d1\n rts'if'joined:'in prefix else prefix+'\n rts'
    with candidate_artifact(tmp_path,code,[],metadata(count=16,size=2,offset=0,width=2))as(a,raw):
        assert not a.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']
        exact(a,raw,tmp_path)


@pytest.mark.parametrize('access,wanted',[
    ('move.w d1,4(a0,d0.w)',True),
    ('move.w (a0)+,4(a0,d0.w)',False),
    ('move.w 4(a0,d0.l),d1',False),
])
def test_write_footprint_base_update_and_index_width(tmp_path,access,wanted):
    with candidate_artifact(tmp_path,'andi.w #31,d0\n lsl.w #3,d0\n '+access+'\n rts',[],metadata())as(a,raw):
        refs=[r for r in a.analysis_payload()[0]['sections'][0]['recovered_platform_typed_accesses']if r['field_name']=='value']
        assert bool(refs)==wanted
        if refs:assert refs[0]['word_index']['evidence']=='bounded_cfg_mask'
        exact(a,raw,tmp_path)
