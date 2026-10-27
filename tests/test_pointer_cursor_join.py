"""A pointer origin is not an exact current address after cursor disagreement."""
import os
import shutil
import subprocess
from pathlib import Path
import pytest


def test_current_pointer_position_join_is_conservative_and_order_independent(tmp_path):
    root=Path(__file__).resolve().parents[1]
    cc=shutil.which('cc');backend=Path(os.environ.get('AMIGA_TEST_BACKEND',root/'src/build/libamiga_backend.so'))
    if not cc or not backend.exists():pytest.skip('host compiler and backend required')
    c=tmp_path/'cursor-join.c'
    c.write_text(r'''#include "m68k_analysis_render_lookup.c"
#include <assert.h>
int main(void) {
 M68kRenderTypedRegValue a={0},b,x,y;
 a.known=a.pointer_value_known=a.pointer_candidate_count=1;
 a.pointer_value=a.pointer_candidates[0]=0x1000;
 b=a;b.byte_cursor=4;
 x=a;y=b;typed_reg_merge(&x,&b, NULL);typed_reg_merge(&y,&a, NULL);
 assert(typed_reg_values_equal(&x,&y));
 assert(!x.pointer_value_known && !x.known && x.byte_cursor==0);
 /* A genuine equal-position join retains its exact pointer. */
 x=a;typed_reg_merge(&x,&a, NULL);assert(x.pointer_value_known && x.pointer_value==0x1000);
 /* Register, stack and memory packets must have the same position rule. */
 M68kRenderTypedStoredValue sa={0},sb,sx,sy;
 sa.known=sa.pointer_value_known=sa.pointer_candidate_count=1;
 sa.pointer_value=sa.pointer_candidates[0]=0x1000;
 sb=sa;sb.byte_cursor=4;sx=sa;sy=sb;
 typed_stored_value_merge(&sx,&sb, NULL);typed_stored_value_merge(&sy,&sa, NULL);
 assert(typed_stored_values_equal(&sx,&sy));
 assert(!sx.pointer_value_known && !sx.known && sx.byte_cursor==0);
 /* Orthogonal whole-value identities survive a lost pointee position. */
 a.layout_base_id=b.layout_base_id=1;
 a.entry_value_id=b.entry_value_id=9;
 x=a;typed_reg_merge(&x,&b, NULL);
 assert(x.layout_base_id==1 && x.entry_value_id==9 && !x.pointer_value_known);
 /* Different array elements can keep their common pointee contract, but
  * cannot claim the same exact source pointer/current element coordinate. */
 a=(M68kRenderTypedRegValue){0};a.known=a.pointer_value_known=a.pointer_candidate_count=1;
 a.pointer_value=a.pointer_candidates[0]=0x1000;
 a.struct_id=AMIGA_OS_STRUCT_ID_LIB;a.array_element_count=4;
 b=a;b.array_element_index=1;x=a;y=b;
 typed_reg_merge(&x,&b, NULL);typed_reg_merge(&y,&a, NULL);
 assert(typed_reg_values_equal(&x,&y));
 assert(x.known && x.struct_id==AMIGA_OS_STRUCT_ID_LIB && !x.pointer_value_known);
 assert(!x.array_element_count && !x.array_element_index);
 /* Losing bounds alone at element zero must not erase a common field
  * coordinate, exact pointer or pointee contract. */
 a.array_element_index=0;a.byte_cursor=4;b=a;b.array_element_count=0;
 x=a;y=b;typed_reg_merge(&x,&b, NULL);typed_reg_merge(&y,&a, NULL);
 assert(typed_reg_values_equal(&x,&y));
 assert(x.pointer_value_known && x.byte_cursor==4 && !x.array_element_count);
 sa.struct_id=AMIGA_OS_STRUCT_ID_LIB;sa.byte_cursor=4;sa.array_element_count=4;
 sb=sa;sb.array_element_count=0;sx=sa;sy=sb;
 typed_stored_value_merge(&sx,&sb, NULL);typed_stored_value_merge(&sy,&sa, NULL);
 assert(typed_stored_values_equal(&sx,&sy));
 assert(sx.pointer_value_known && sx.byte_cursor==4 && !sx.array_element_count);
 /* Backedge-first visitation must converge, not keep choosing the advancing
  * cursor over the entry value on every pass. Use the actual transfer. */
 M68kRenderTypedState loop={0};M68kRenderLookup lookup={0};M68kRenderPlatformState platform={0};
 M68kAnalysisPolicy policy;m68k_analysis_policy_init_default(&policy);lookup.policy=&policy;
 M68kRenderTypedRegValue entry={0};entry.known=entry.pointer_value_known=entry.pointer_candidate_count=1;
 entry.pointer_value=entry.pointer_candidates[0]=0x1000;loop.addr_regs[1]=entry;
 M68kInstructionIR increment=m68k_plain_parse_instruction_to_ir("addq.l #4,a1",M68K_ASM_CPU_68000,m68k_diag_sink(NULL));
 for(unsigned i=0;i<16;++i) {
   typed_state_update_after_instruction(&loop,&lookup,&platform,0,&increment,NULL,NULL,0,0);
   typed_reg_merge(&loop.addr_regs[1],&entry, NULL);
   assert(!loop.addr_regs[1].known && !loop.addr_regs[1].pointer_value_known && !loop.addr_regs[1].byte_cursor);
 }
 m68k_analysis_policy_destroy(&policy);
 return 0;
}''')
    exe=tmp_path/'cursor-join'
    built=subprocess.run([cc,'-Isrc','-D_POSIX_C_SOURCE=200809L','-std=c11','-O0',str(c),str(backend),
        f'-Wl,-rpath,{backend.parent}','-o',str(exe)],cwd=root,capture_output=True,text=True,timeout=60)
    assert built.returncode==0,built.stderr
    run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
    assert run.returncode==0,run.stdout+run.stderr


@pytest.mark.parametrize('test_branch', ['beq.w', 'bne.w'])
def test_source_cursor_through_called_nested_retry_loops_converges(tmp_path, monkeypatch, test_branch):
    from tests.test_app_cursor_propagation import cursor_artifact
    monkeypatch.setenv('AMIGA_REVERSING_TYPED_FLOW_MAX_NODE_VISITS','1000')
    a,_=cursor_artifact(tmp_path,'''lea.l queue(pc),a2
 bsr.w sorter
 rts
sorter:
 movea.l a2,a0
 moveq #1,d0
outer:
 movea.l a0,a1
 addq.l #4,a1
 move.w d0,d2
inner:
 tst.w d3
 '''+test_branch+''' skip
 move.l a4,(a1)
skip:
 addq.l #4,a1
 dbf.w d2,inner
 addq.l #4,a0
 dbf.w d0,outer
 rts
queue:
 dcb.l 4,0''')
    try:assert not a.analysis_payload()[0]['incomplete_analysis']
    finally:a.close()
