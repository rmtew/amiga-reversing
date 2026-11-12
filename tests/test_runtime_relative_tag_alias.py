"""Relative register EAs preserve tags only for proved disjoint writes."""
import pytest
from tests.test_writable_tagged_layout import check,extras


@pytest.mark.parametrize('body',[
 'lea.l -32(a0),a6\n move.w #12,(a0)\n move.l a0,8(a6)\n move.w 4(a0),d2',
 'move.w #12,(a0)\n lea.l -32(a0),a6\n move.l a0,8(a6)\n move.w 4(a0),d2',
 'lea.l 32(a0),a6\n move.w #12,(a0)\n move.l a0,(a6)\n move.w 4(a0),d2',
 'lea.l -32(a0),a6\n move.w #12,(a0)\n move.l a6,d3\n movea.l d3,a1\n move.l a0,8(a1)\n move.w 4(a0),d2',
 'lea.l -32(a0),a6\n move.w #12,(a0)\n move.l a0,d7\n movea.l (a3),a0\n move.l d7,8(a6)\n movea.l d7,a1\n move.w 4(a1),d2',
 'lea.l -32(a0),a6\n move.w #12,(a0)\n movem.l d0-d1,8(a6)\n move.w 4(a0),d2',
 'lea.l -32(a0),a6\n move.w #12,(a0)\n move.l d0,-(a6)\n move.w 4(a0),d2',
 'lea.l -32(a0),a6\n move.w #12,(a0)\n move.l d0,(a6)+\n move.w 4(a0),d2',
])
def test_same_live_register_root_and_whole_write_footprint_preserve_tag(tmp_path,body):
    section,source=check(tmp_path,body)
    assert len(extras(section))==1 and 'Child_extra' in source


@pytest.mark.parametrize('between',[
 'move.l a0,32(a6)',  # exact tag overlap
 'move.b d0,33(a6)',  # partial tag overlap
 'movem.l d0-d1,28(a6)',  # bulk span crosses the tag
 'lea.l 8(a0),a6\n movem.l d0-d1,-(a6)',  # predecrement bulk starts at tag
 'movea.l (a1),a6\n move.l a0,8(a6)',  # clobbered relation
 'move.l a6,d3\n move.w #0,d3\n movea.l d3,a6\n move.l a0,8(a6)',
 'jsr $2000.l',
 'move.l d0,8(a1)',  # unrelated unknown root
])
def test_overlap_clobber_partial_transfer_unknown_call_and_root_refuse(tmp_path,between):
    section,_=check(tmp_path,'lea.l -32(a0),a6\n move.w #12,(a0)\n'+between+'\n move.w 4(a0),d2')
    assert not extras(section)


@pytest.mark.parametrize('other,expected',[( -32,1),(-16,0),(0,0)])
def test_only_agreed_relative_differences_survive_cfg_join(tmp_path,other,expected):
    section,_=check(tmp_path,f'''tst.w d7
 beq.w other
 lea.l -32(a0),a6
 bra.w joined
other: lea.l {other}(a0),a6
joined: move.w #12,(a0)
 move.l a0,8(a6)
 move.w 4(a0),d2''')
    assert len(extras(section))==expected


def test_unknown_predecessor_absorbs_a_relation(tmp_path):
    section,_=check(tmp_path,'''tst.w d7
 beq.w joined
 lea.l -32(a0),a6
joined: move.w #12,(a0)
 move.l a0,8(a6)
 move.w 4(a0),d2''')
    assert not extras(section)


@pytest.mark.parametrize('helper,expected',[('rts',1),('movea.l d0,a6\n rts',0)])
def test_fresh_tag_after_call_uses_only_summary_preserved_register_relations(tmp_path,helper,expected):
    section,_=check(tmp_path,f'''lea.l -32(a0),a6
 bsr.w helper
 move.w #12,(a0)
 move.l a0,8(a6)
 move.w 4(a0),d2
 rts
helper: {helper}''')
    assert len(extras(section))==expected


@pytest.mark.parametrize('control',['move.w #0,sr','andi.b #$FB,ccr'])
@pytest.mark.parametrize('fresh',[False,True])
def test_unmodelled_control_effect_discards_old_predicates_and_relative_evidence(tmp_path,control,fresh):
    tail='move.w #12,(a0)\n move.l a0,8(a6)\n'if fresh else''
    section,_=check(tmp_path,'lea.l -32(a0),a6\n move.w #12,(a0)\n'+control+'\n'+tail+'move.w 4(a0),d2')
    assert not extras(section)
