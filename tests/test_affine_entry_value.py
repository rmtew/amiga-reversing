"""Affine entry identities are a component of shared values, never pointers."""
import os,shutil,subprocess
from pathlib import Path
import pytest

def test_shared_affine_entry_packet_transfers_and_refusals(tmp_path):
    root=Path(__file__).resolve().parents[1]
    compiler=shutil.which('cc');backend=Path(os.environ.get('AMIGA_TEST_BACKEND',root/'src/build/libamiga_backend.so'))
    if not compiler or not backend.exists():pytest.skip('host compiler and backend required')
    source=tmp_path/'entry-value.c'
    source.write_text(r'''#include "m68k_analysis_render_lookup.c"
#include "m68k_plain_parse.h"
#include <assert.h>
static void step(M68kRenderTypedState *state,M68kRenderLookup *lookup,const char *text) {
  M68kRenderPlatformState platform={0};
  M68kInstructionIR instruction=m68k_plain_parse_instruction_to_ir(text,M68K_ASM_CPU_68000,m68k_diag_sink(NULL));
  assert(m68k_sim_metadata_for_instruction(&instruction));
  typed_state_update_after_instruction(state,lookup,&platform,0,&instruction,NULL,NULL,0,0);
}
static void expect(M68kAffineEntryContext *c,uint32_t id,uint32_t root,int offset) {
  const M68kAffineEntryValue *v=affine_entry_value(c,id);assert(v && v->root==root && v->offset==offset && v->coefficient==1);
}
int main(void) {
  M68kAffineEntryContext context={0}; M68kRenderLookup lookup={0};
  M68kRenderTypedState state={0},other;M68kRenderTypedStoredValue value;
  M68kAnalysisPolicy policy; m68k_analysis_policy_init_default(&policy);
  lookup.policy=&policy;lookup.affine_entry_context=&context;
  uint32_t a=affine_entry_intern(&context,1,0,4),sp=affine_entry_intern(&context,2,0,4);
  assert(a && sp && a!=sp && a==affine_entry_intern(&context,1,0,4));
  assert(!affine_entry_adjust(&context,affine_entry_intern(&context,1,INT32_MAX,4),1));
  expect(&context,affine_entry_adjust(&context,affine_entry_intern(&context,3,32767,2),1),3,-32768);
  expect(&context,affine_entry_adjust(&context,affine_entry_intern(&context,3,-1,2),1),3,0);
  state.data_regs[6].entry_value_id=a;
  step(&state,&lookup,"dbf d6,$1000");
  assert(!state.data_regs[6].entry_value_id); /* WORD decrement invalidates a LONG identity. */
  state.data_regs[6].entry_value_id=a;
  step(&state,&lookup,"dbne d6,$1000");
  assert(!state.data_regs[6].entry_value_id); /* Unknown CCR: conditional decrement is a may-write. */
  state.addr_regs[4].entry_value_id=a;state.addr_regs[7].entry_value_id=sp;
  step(&state,&lookup,"lea.l 6(a4),a0");expect(&context,state.addr_regs[0].entry_value_id,1,6);
  assert(!state.addr_regs[0].known && !state.addr_regs[0].pointer_value_known);
  step(&state,&lookup,"move.l a0,d0");expect(&context,state.data_regs[0].entry_value_id,1,6);
  step(&state,&lookup,"move.l d0,-(a7)");
  step(&state,&lookup,"move.w d2,-(a7)");
  step(&state,&lookup,"addq.l #2,a7");
  step(&state,&lookup,"moveq #0,d0");assert(!state.data_regs[0].entry_value_id);
  step(&state,&lookup,"move.l (a7)+,d0");expect(&context,state.data_regs[0].entry_value_id,1,6);
  expect(&context,state.addr_regs[7].entry_value_id,2,0);
  step(&state,&lookup,"movem.l d0/a4,-(a7)");
  step(&state,&lookup,"movea.l #0,a4");
  step(&state,&lookup,"movem.l (a7)+,d0/a4");expect(&context,state.addr_regs[4].entry_value_id,1,0);
  step(&state,&lookup,"movem.w (a4)+,d1-d3");expect(&context,state.addr_regs[4].entry_value_id,1,6);
  step(&state,&lookup,"subq.l #6,a4");expect(&context,state.addr_regs[4].entry_value_id,1,0);
  step(&state,&lookup,"movea.w a4,a0");assert(!state.addr_regs[0].entry_value_id);
  step(&state,&lookup,"move.l a4,-(a7)");typed_state_clear_stack_write(&state,1,1);
  step(&state,&lookup,"movea.l (a7)+,a0");assert(!state.addr_regs[0].entry_value_id);
  other=state;typed_state_merge_into(&state,&other, NULL);expect(&context,state.addr_regs[4].entry_value_id,1,0);
  other.addr_regs[4].entry_value_id=affine_entry_adjust(&context,a,2);
  typed_state_merge_into(&state,&other, NULL);assert(!state.addr_regs[4].entry_value_id);
  other.addr_regs[4].entry_value_id=a;typed_state_merge_into(&state,&other, NULL);assert(!state.addr_regs[4].entry_value_id);
  state.addr_regs[4].entry_value_id=a;
  value=typed_stored_value_for_address_register(&state,4);assert(value.entry_value_id==a && !value.known);
  typed_state_set_memory_cell(&state,1,&value);
  assert(typed_state_memory_cell(&state,1)->value.entry_value_id==a);
  M68kAnalysisFunctionSummary summary={0};
  function_summary_set_register_partition(&summary,255,254);
  summary.memory_effect_state=summary.escape_effect_state=M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_EXPLICIT;
  summary.input_count=summary.result_count=1;
  summary.inputs[0].seed_kind=M68K_ANALYSIS_REGISTER_SEED_ABI_POINTER;
  summary.inputs[0].location.kind=summary.results[0].location.kind=M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER;
  summary.inputs[0].location.width=summary.results[0].location.width=4;
  summary.inputs[0].location.register_count=summary.results[0].location.register_count=1;
  summary.inputs[0].location.registers[0].register_kind=summary.results[0].location.registers[0].register_kind=M68K_ANALYSIS_REGISTER_ADDRESS;
  summary.inputs[0].location.registers[0].register_index=4;
  summary.results[0].location.registers[0].register_index=0;
  summary.results[0].kind=M68K_ANALYSIS_FUNCTION_SUMMARY_RESULT_IDENTITY_INPUT;
  other=state;typed_state_apply_function_summary_effects(&state,&summary);
  typed_state_apply_function_summary_results(&state,&other,&lookup,&summary,0,0);
  expect(&context,state.addr_regs[0].entry_value_id,1,0);
  function_summary_set_register_partition(&summary,0,0);
  typed_state_apply_function_summary_effects(&state,&summary);assert(!state.addr_regs[4].entry_value_id);
  state.data_regs[6].entry_value_id=affine_entry_intern(&context,7,3,2);
  step(&state,&lookup,"move.w d6,d2");
  step(&state,&lookup,"add.w d6,d2");
  const M68kAffineEntryValue *sum=affine_entry_value(&context,state.data_regs[2].entry_value_id);
  assert(sum && sum->coefficient==2 && sum->offset==6);
  step(&state,&lookup,"sub.w d6,d2");expect(&context,state.data_regs[2].entry_value_id,7,3);
  step(&state,&lookup,"move.w d6,d0");expect(&context,state.data_regs[0].entry_value_id,7,3);
  step(&state,&lookup,"lsl.w #2,d0");
  const M68kAffineEntryValue *scaled=affine_entry_value(&context,state.data_regs[0].entry_value_id);
  assert(scaled && scaled->root==7 && scaled->coefficient==4 && scaled->offset==12 && scaled->width==2);
  uint32_t four=state.data_regs[0].entry_value_id;
  assert(four==affine_entry_intern_scaled(&context,7,4,12,2));
  step(&state,&lookup,"add.w d0,d0");
  scaled=affine_entry_value(&context,state.data_regs[0].entry_value_id);
  assert(scaled && scaled->coefficient==8 && scaled->offset==24);
  step(&state,&lookup,"subq.w #2,d0");
  scaled=affine_entry_value(&context,state.data_regs[0].entry_value_id);
  assert(scaled && scaled->coefficient==8 && scaled->offset==22);
  step(&state,&lookup,"movea.w d0,a0");
  scaled=affine_entry_value(&context,state.addr_regs[0].entry_value_id);
  assert(scaled && scaled->width==2 && scaled->coefficient==8 && !state.addr_regs[0].known);
  step(&state,&lookup,"lsr.w #1,d0");assert(!state.data_regs[0].entry_value_id);
  state.data_regs[0].entry_value_id=four;
  step(&state,&lookup,"move.b #0,d0");assert(!state.data_regs[0].entry_value_id);
  state.data_regs[0].entry_value_id=a;
  step(&state,&lookup,"lsl.w #2,d0");assert(!state.data_regs[0].entry_value_id);
  assert(!affine_entry_scale(&context,affine_entry_intern(&context,7,INT32_MAX,4),2));
  assert(!affine_entry_intern_scaled(&context,7,0,0,2));
  assert(!context.failed);
  printf("sizes reg=%zu stored=%zu state=%zu node=%zu\n",sizeof(M68kRenderTypedRegValue),sizeof(M68kRenderTypedStoredValue),sizeof(M68kRenderTypedState),sizeof(M68kRenderTypedFlowNode));
  affine_entry_destroy(&context);m68k_analysis_policy_destroy(&policy);return 0;
}
''')
    exe=tmp_path/'entry-value'
    built=subprocess.run([compiler,'-Isrc','-Isrc/generated','-w',str(source),str(backend),f'-Wl,-rpath,{backend.parent}','-lm','-o',str(exe)],cwd=root,capture_output=True,text=True,timeout=60)
    assert built.returncode==0,built.stderr
    result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=10)
    assert result.returncode==0,result.stdout+result.stderr
    print(result.stdout)
