"""Specialize generic EA access roles once for shared inspection exports."""
from pathlib import Path
import pytest
from amiga_reversing.disasm.app_access_audit import decode_retained_instruction
from amiga_reversing.disasm import c_backend
from tests.test_app_cursor_propagation import cursor_artifact


@pytest.mark.parametrize('asm,roles', [
    ('move.l #16,d0',['immediate','register_write']),
    ('adda.l #$8000,a0',['immediate','register_write']),
    ('cmpi.w #16,(a0)',['immediate','memory_read']),
    ('move.w $1002.l,d0',['memory_read','register_write']),
    ('move.w d0,$1002.l',['register_read','memory_write']),
    ('move.l a0,d1',['register_read','register_write']),
    ('movea.l (a0),a1',['memory_read','register_write']),
    ('addq.w #1,d0',['immediate','register_write']),
    ('addq.w #1,(a0)',['immediate','memory_write']),
    ('cmp.w (a0),d0',['memory_read','register_read']),
    ('btst #1,d0',['immediate','register_read']),
    ('sne d0',['register_write']), ('sne (a0)',['memory_write']),
    ('lea.l $1000.l,a0',['address','register_write']),
    ('movem.l d0-d1,-(a0)',['register_list_read','memory_write']),
    ('movem.l (a0)+,d0-d1',['memory_read','register_list_write']),
])
def test_decoded_access_roles_match_actual_register_or_memory_operand(asm,roles):
    code,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',
        ' SECTION code,code\n ORG 0\n '+asm+'\n')
    ev=decode_retained_instruction(code,project_root=Path(__file__).resolve().parents[1])
    assert [o['access']for o in ev['operand_facts']]==roles
    assert not [o for o in ev['operand_facts']if o['direct_register'] and o['access'].startswith('memory_')]


def test_listing_rows_use_same_specialized_roles(tmp_path):
    a,_=cursor_artifact(tmp_path,'move.w $1002.l,d0\nrts')
    try:
        row=a.row_for_source_offset(section_index=0,offset=0)
        assert row['operand_accesses']==['memory_read','register_write']
    finally:a.close()
