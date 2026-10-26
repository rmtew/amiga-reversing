"""Canonical absolute cells have local reaching values, not a merged history."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact,derived_refs

@pytest.mark.parametrize('update,expected',[
    ('',0xC3E),('addq.l #6,$1800.l',0xC44),('subq.l #6,$1800.l',0xC38),
    ('addi.l #12,$1800.l',0xC4A),('subi.l #12,$1800.l',0xC32),
    ('move.b #0,$1801.l',None),('clr.w $1802.l',None),('movem.l d0-d1,$17FC.l',None),
    ('move.l #0,$1800.l',None),('move.b #0,(a2)',None),('jsr $2000.l',None),
    ('addq.w #6,$1800.l',None),('addq.l #6,$1802.l',None),
    ('move.b #0,$17FF.l',0xC3E),('move.b #0,$1804.l',0xC3E),
])
def test_absolute_cell_reaching_update_and_clobber(tmp_path,update,expected):
    a,_=cursor_artifact(tmp_path,'lea.l $C3E(a6),a0\n move.l a0,$1800.l\n '+update+
        '\n movea.l $1800.l,a1\n move.w (a1),d0')
    try:
        reads=[r['displacement']for r in derived_refs(a)if r['access']=='read']
        assert reads==([]if expected is None else[expected])
        assert not a.analysis_payload()[0]['incomplete_analysis']
    finally:a.close()

@pytest.mark.parametrize('other,expected',[(0xC3E,0xC3E),(0xBC6,None)])
def test_absolute_cell_join_keeps_only_identical_reaching_values(tmp_path,other,expected):
    a,_=cursor_artifact(tmp_path,'tst.w d0\n beq.w alternate\n lea.l $C3E(a6),a0\n move.l a0,$1800.l\n bra.w join\nalternate:\n '+
        f'lea.l ${other:X}(a6),a0\n move.l a0,$1800.l\njoin:\n movea.l $1800.l,a1\n move.w (a1),d0')
    try:
        assert [r['displacement']for r in derived_refs(a)if r['access']=='read']==([]if expected is None else[expected])
    finally:a.close()

def test_load_before_later_store_is_not_a_reaching_definition(tmp_path):
    a,_=cursor_artifact(tmp_path,'movea.l $1800.l,a1\n move.w (a1),d0\n lea.l $C3E(a6),a0\n move.l a0,$1800.l')
    try:
        assert not [r for r in derived_refs(a)if r['access']=='read']
    finally:a.close()

@pytest.mark.parametrize('callee,preserved',[
    ('rts',True),('move.l #0,$1800.l\n rts',False),('move.b #0,(a2)\n rts',False),
])
def test_existing_callee_memory_contract_controls_local_cells(tmp_path,callee,preserved):
    a,_=cursor_artifact(tmp_path,'lea.l $C3E(a6),a0\n move.l a0,$1800.l\n bsr.w helper\n '+
        'movea.l $1800.l,a1\n move.w (a1),d0\n rts\nhelper:\n '+callee)
    try:
        assert bool([r for r in derived_refs(a)if r['access']=='read'])==preserved
    finally:a.close()
