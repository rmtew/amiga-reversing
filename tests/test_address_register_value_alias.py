"""Register value equality does not depend on inferred pointee type."""
import os
import shutil
import subprocess
from pathlib import Path
import pytest


def test_alias_lattice_transfer_meet_and_interpretation_lifecycle(tmp_path):
    root=Path(__file__).resolve().parents[1]
    cc=shutil.which('cc');backend=Path(os.environ.get('AMIGA_TEST_BACKEND',root/'src/build/libamiga_backend.so'))
    if not cc or not backend.exists():pytest.skip('native compiler and backend required')
    c=tmp_path/'value-alias.c'
    c.write_text(r'''#include "m68k_analysis_render_lookup.c"
#include <assert.h>
static void step(M68kRenderTypedState *state,const char *text) {
 M68kRenderLookup lookup={0};M68kAnalysisPolicy policy;M68kRenderPlatformState platform={0};
 m68k_analysis_policy_init_default(&policy);lookup.policy=&policy;
 M68kInstructionIR instruction=m68k_plain_parse_instruction_to_ir(text,M68K_ASM_CPU_68000,m68k_diag_sink(NULL));
 assert(m68k_sim_metadata_for_instruction(&instruction));
 typed_state_update_after_instruction(state,&lookup,&platform,0,&instruction,NULL,NULL,0,0);
 m68k_analysis_policy_destroy(&policy);
}
int main(void) {
 M68kRenderTypedState unknown={0},known={0};
 known.addr_regs[5].known=known.addr_regs[5].raw_long_value_known=known.addr_regs[5].raw_long_candidate_count=1;
 known.addr_regs[5].raw_long_value=known.addr_regs[5].raw_long_candidates[0]=0x12345678;
 step(&unknown,"movea.l a5,a1");step(&known,"movea.l a5,a1");
 assert(typed_state_addr_alias_equal(&unknown,1,5) && typed_state_addr_alias_equal(&known,1,5));
 assert(unknown.register_alias_known==known.register_alias_known);
 assert(!memcmp(unknown.register_alias_sources,known.register_alias_sources,8));
 /* MOVEA.W sign-extends the low word; it is not a full-register identity. */
 unknown=(M68kRenderTypedState){0};step(&unknown,"movea.w a2,a5");
 assert(!typed_state_addr_alias_equal(&unknown,2,5));
 M68kRenderTypedState left={0},right={0},a,b;
 step(&left,"movea.l a0,a1");step(&left,"movea.l a0,a2");
 step(&right,"movea.l a1,a2");
 a=left;b=right;typed_state_merge_into(&a,&right, NULL);typed_state_merge_into(&b,&left, NULL);
 assert(typed_state_addr_alias_equal(&a,1,2) && !typed_state_addr_alias_equal(&a,0,1));
 assert(a.register_alias_known==b.register_alias_known && !memcmp(a.register_alias_sources,b.register_alias_sources,8));
 M68kRenderTypedState top={0};typed_state_merge_into(&a,&top, NULL);typed_state_merge_into(&a,&right, NULL);
 assert(!a.register_alias_known); /* An unknown path remains unknown. */
 step(&left,"movea.l (a3),a0");
 assert(typed_state_addr_alias_equal(&left,1,2) && !typed_state_addr_alias_equal(&left,0,1));
 step(&left,"exg.l a0,a2");
 assert(typed_state_addr_alias_equal(&left,0,1) && !typed_state_addr_alias_equal(&left,1,2));
 step(&left,"lea.l (a1),a4");
 assert(typed_state_addr_alias_equal(&left,0,4));
 step(&left,"movea.l a4,a4");
 assert(typed_state_addr_alias_equal(&left,0,4));
 step(&left,"move.l a4,(a6)");
 assert(typed_state_addr_alias_equal(&left,0,4)); /* Memory does not rewrite held values. */
 step(&left,"move.l (a4)+,d0");
 assert(!typed_state_addr_alias_equal(&left,0,4));
 right=(M68kRenderTypedState){0};step(&right,"movea.l a1,a2");
 step(&right,"movem.l (a0),a1-a2");assert(!typed_state_addr_alias_equal(&right,1,2));
 /* API precondition refinement and opaque memory effects do not rewrite a
  * preserved register, erase its entry identity or sever value equality. */
 right=(M68kRenderTypedState){0};step(&right,"movea.l a5,a1");
 right.addr_regs[5].entry_value_id=9;
 right.base_slot_count=1;right.base_slots[0].known=1;right.base_slots[0].base_reg=5;
 M68kAnalysisFunctionSummary summary={0};function_summary_set_register_partition(&summary,255,255);
 M68kAnalysisFunctionSummaryInput input={0};input.location.kind=M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER;
 input.location.register_count=1;input.location.registers[0].register_kind=AMIGA_OS_REGISTER_ADDRESS;
 input.location.registers[0].register_index=1;
 typed_flow_apply_call_input_alias_type(&summary,0,0,&right,&input,AMIGA_OS_STRUCT_ID_LIB,NULL);
 assert(right.addr_regs[5].struct_id==AMIGA_OS_STRUCT_ID_LIB && right.addr_regs[5].entry_value_id==9);
 assert(right.base_slot_count==1 && typed_state_addr_alias_equal(&right,1,5));
 right.addr_regs[5].origin.kind=M68K_RENDER_TYPED_ORIGIN_LOOKUP_STORAGE;
 summary.memory_effect_state=M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_UNKNOWN;
 typed_state_apply_function_summary_effects(&right,&summary);
 assert(typed_state_addr_alias_equal(&right,1,5) && right.addr_regs[5].entry_value_id==9);
 function_summary_set_register_partition(&summary,255,223);
 typed_state_apply_function_summary_effects(&right,&summary);
 assert(!typed_state_addr_alias_equal(&right,1,5));
 right=(M68kRenderTypedState){0};step(&right,"movea.l a7,a0");
 assert(typed_state_addr_alias_equal(&right,0,7));
 step(&right,"pea.l (a1)");assert(!typed_state_addr_alias_equal(&right,0,7));
 right=(M68kRenderTypedState){0};step(&right,"movea.l a7,a0");
 step(&right,"link.w a6,#0");assert(!typed_state_addr_alias_equal(&right,0,7));
 /* Full-width transport through data registers shares the same relation.
  * Overwriting an intermediate register does not rewrite held copies. */
 right=(M68kRenderTypedState){0};
 step(&right,"move.l a0,d0");step(&right,"move.l d0,d7");step(&right,"movea.l d7,a1");
 assert(typed_state_addr_alias_equal(&right,0,1));
 assert(typed_register_alias_root(&right,0)==typed_register_alias_root(&right,8));
 step(&right,"moveq.l #0,d0");
 assert(typed_state_addr_alias_equal(&right,0,1));
 assert(typed_register_alias_root(&right,0)!=typed_register_alias_root(&right,8));
 step(&right,"move.w #0,d7");assert(typed_state_addr_alias_equal(&right,0,1));
 step(&right,"addq.l #1,a1");assert(!typed_state_addr_alias_equal(&right,0,1));
 right=(M68kRenderTypedState){0};step(&right,"move.l a0,d0");
 step(&right,"move.w #0,d0");step(&right,"movea.l d0,a1");
 assert(!typed_state_addr_alias_equal(&right,0,1));
 right=(M68kRenderTypedState){0};step(&right,"move.l a0,d0");
 step(&right,"exg.l d0,a1");assert(typed_state_addr_alias_equal(&right,0,1));
 assert(typed_register_alias_root(&right,0)!=typed_register_alias_root(&right,8));
 /* Type assertions are not CPU assignments to either register kind. */
 right=(M68kRenderTypedState){0};step(&right,"move.l a0,d0");
 typed_state_set_reg_struct_id(&right,M68K_ANALYSIS_REGISTER_DATA,0,AMIGA_OS_STRUCT_ID_LIB,NULL);
 typed_state_set_reg_struct_id(&right,M68K_ANALYSIS_REGISTER_ADDRESS,0,AMIGA_OS_STRUCT_ID_LIB,NULL);
 assert(typed_register_alias_root(&right,0)==typed_register_alias_root(&right,8));
 left=(M68kRenderTypedState){0};step(&left,"move.l a0,d0");step(&left,"move.l d0,d1");
 right=(M68kRenderTypedState){0};step(&right,"move.l d0,d1");
 a=left;b=right;typed_state_merge_into(&a,&right, NULL);typed_state_merge_into(&b,&left, NULL);
 assert(a.register_alias_known==b.register_alias_known && !memcmp(a.register_alias_sources,b.register_alias_sources,8));
 assert(typed_register_alias_root(&a,0)==typed_register_alias_root(&a,1));
 assert(typed_register_alias_root(&a,0)!=typed_register_alias_root(&a,8));
 /* Constant differences extend the same register relation, not pointee types. */
 uint32_t delta;
 right=(M68kRenderTypedState){0};step(&right,"lea.l -32(a0),a6");
 assert(typed_register_relative_difference(&right,14,8,&delta) && delta==(uint32_t)-32);
 assert(!typed_state_addr_alias_equal(&right,0,6));
 step(&right,"move.l a6,d3");step(&right,"lea.l 8(a6),a1");
 assert(typed_register_relative_difference(&right,9,8,&delta) && delta==(uint32_t)-24);
 step(&right,"movea.l (a4),a6");
 assert(typed_register_relative_difference(&right,9,3,&delta) && delta==8);
 step(&right,"move.b #1,d3");
 assert(!typed_register_relative_difference(&right,9,3,&delta));
 assert(typed_register_relative_difference(&right,9,8,&delta) && delta==(uint32_t)-24);
 right=(M68kRenderTypedState){0};step(&right,"lea.l -1(a0),a1");step(&right,"lea.l 1(a1),a2");
 assert(typed_state_addr_alias_equal(&right,0,2));
 left=(M68kRenderTypedState){0};right=(M68kRenderTypedState){0};
 step(&left,"lea.l 8(a0),a1");step(&left,"lea.l 16(a0),a2");
 step(&right,"lea.l 24(a3),a1");step(&right,"lea.l 32(a3),a2");
 a=left;b=right;typed_state_merge_into(&a,&right,NULL);typed_state_merge_into(&b,&left,NULL);
 assert(typed_register_relative_difference(&a,10,9,&delta) && delta==8);
 assert(!typed_register_relative_difference(&a,9,8,&delta));
 assert(a.register_alias_known==b.register_alias_known && !memcmp(a.register_alias_sources,b.register_alias_sources,8));
 assert(!memcmp(a.register_alias_offsets,b.register_alias_offsets,sizeof(a.register_alias_offsets)));
 step(&right,"lea.l 36(a3),a2");typed_state_merge_into(&a,&right,NULL);
 assert(!typed_register_relative_difference(&a,10,9,&delta));
 /* A counter update conflicts with its entry relation; it cannot create a must invariant. */
 right=(M68kRenderTypedState){0};step(&right,"movea.l a0,a1");a=right;
 step(&right,"lea.l 1(a1),a1");typed_state_merge_into(&a,&right,NULL);
 assert(!typed_register_relative_difference(&a,9,8,&delta));
 /* An opaque trap cannot leave held-value relations for a later fresh tag. */
 right=(M68kRenderTypedState){0};step(&right,"lea.l -32(a0),a6");
 step(&right,"trap #0");assert(!typed_register_relative_difference(&right,14,8,&delta));
 /* Unmodelled named-register writes must not retain a potentially switched SP. */
 right=(M68kRenderTypedState){0};step(&right,"movea.l a7,a0");
 step(&right,"move.w #0,sr");assert(!typed_state_addr_alias_equal(&right,0,7));
 /* Frame instructions own both their explicit frame register and implicit SP. */
 right=(M68kRenderTypedState){0};step(&right,"lea.l -32(a0),a6");
 step(&right,"link.w a6,#0");assert(!typed_register_relative_difference(&right,14,8,&delta));
 right=(M68kRenderTypedState){0};step(&right,"lea.l -32(a0),a6");
 step(&right,"unlk a6");assert(!typed_register_relative_difference(&right,14,8,&delta));
 for(unsigned reg=0;reg<8;++reg)for(unsigned unlink=0;unlink<2;++unlink) {
  char text[32];snprintf(text,sizeof(text),unlink?"unlk a%u":"link.w a%u,#0",reg);
  M68kInstructionIR ins=m68k_plain_parse_instruction_to_ir(text,M68K_ASM_CPU_68000,m68k_diag_sink(NULL));
  assert(m68k_sim_sp_effect_bound_register_write_mask(&ins)==(uint16_t)(1U<<(reg+8U)));
  assert(platform_operand_register_write_mask(&ins,0)&(1U<<(reg+8U)));
 }
 /* Pairwise mathematical relation intersection, independent of representatives. */
 uint32_t random=0x13579BDF;
 for(unsigned trial=0;trial<128;++trial) {
  M68kRegisterAliasSnapshot x,y;M68kRenderTypedState l={0},r={0},lr,rl;
  for(unsigned i=0;i<16;++i) {
   random=random*1664525U+1013904223U;x.roots[i]=(random>>16)%4;
   random=random*1664525U+1013904223U;x.offsets[i]=((random>>16)%5)*8U-16U;
   random=random*1664525U+1013904223U;y.roots[i]=(random>>16)%4;
   random=random*1664525U+1013904223U;y.offsets[i]=((random>>16)%5)*8U-16U;
  }
  typed_register_alias_store(&l,&x);typed_register_alias_store(&r,&y);lr=l;rl=r;
  typed_register_alias_meet(&lr,&r);typed_register_alias_meet(&rl,&l);
  assert(lr.register_alias_known==rl.register_alias_known);
  assert(!memcmp(lr.register_alias_sources,rl.register_alias_sources,8));
  assert(!memcmp(lr.register_alias_offsets,rl.register_alias_offsets,sizeof(lr.register_alias_offsets)));
  for(unsigned i=0;i<16;++i)for(unsigned j=0;j<16;++j) {
   int expected=x.roots[i]==x.roots[j] && y.roots[i]==y.roots[j] &&
    x.offsets[i]-x.offsets[j]==y.offsets[i]-y.offsets[j];
   assert(typed_register_relative_difference(&lr,i,j,&delta)==expected);
   if(expected)assert(delta==x.offsets[i]-x.offsets[j]);
   assert((typed_register_alias_root(&l,i)==typed_register_alias_root(&l,j))==
    (x.roots[i]==x.roots[j] && x.offsets[i]==x.offsets[j]));
  }
  rl=lr;assert(!typed_register_alias_meet(&rl,&lr));
 }
 /* Relative circular spans conservatively include 24-bit bus aliases. */
 M68kRenderScalarReadRelation tag={0};M68kRenderLookup tags={0};
 tag.tag_kind=2;tag.base_type=1;tags.scalar_read_relations=&tag;tags.scalar_read_relation_count=1;
 right=(M68kRenderTypedState){0};step(&right,"lea.l (a0),a6");
 right.addr_regs[0].known=1;right.addr_regs[0].struct_id=1;right.addr_regs[0].read_relation=2;
 const uint32_t distances[]={0,1,2,0xFFFFFF,0xFFFFFF,0x1000000,0x1000002,0xFFFFFFFC,0xFFFFFFF8};
 const uint8_t spans[]={2,1,2,2,1,2,2,8,8},disjoint[]={0,0,1,0,1,0,1,0,1};
 for(size_t k=0;k<sizeof(distances)/sizeof(distances[0]);++k) {
  right.register_alias_offsets[14]=distances[k];
  assert(typed_tag_relative_write_disjoint(&tags,&right,&tag,6,0,spans[k])==disjoint[k]);
 }
 right.register_alias_offsets[14]=2;
 assert(!typed_tag_relative_write_disjoint(&tags,&right,&tag,6,-2,2));
 tag.field_cursor=2;right.register_alias_offsets[14]=3;
 assert(!typed_tag_relative_write_disjoint(&tags,&right,&tag,6,0,1));
 right.register_alias_offsets[14]=4;assert(typed_tag_relative_write_disjoint(&tags,&right,&tag,6,0,1));
 right.register_alias_offsets[14]=1;assert(typed_tag_relative_write_disjoint(&tags,&right,&tag,6,0,1));
 typed_state_clear_addr_alias_for_reg(&right,6);
 assert(!typed_tag_relative_write_disjoint(&tags,&right,&tag,6,0,2));
 /* Only sixteen modular deltas were added to the existing state. */
 fprintf(stderr,"typed_state_bytes=%zu alias_delta_bytes=%zu\n",sizeof(M68kRenderTypedState),sizeof(a.register_alias_offsets));
 assert(sizeof(a.register_alias_offsets)==16*sizeof(uint32_t));
 assert(sizeof(M68kRegisterAliasSnapshot)==16*(sizeof(uint32_t)+sizeof(uint8_t)));
 return 0;
}''')
    exe=tmp_path/'value-alias'
    built=subprocess.run([cc,'-Isrc','-D_POSIX_C_SOURCE=200809L','-std=c11','-O0',str(c),str(backend),
        f'-Wl,-rpath,{backend.parent}','-o',str(exe)],cwd=root,capture_output=True,text=True,timeout=60)
    assert built.returncode==0,built.stderr
    run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
    assert run.returncode==0,run.stdout+run.stderr
