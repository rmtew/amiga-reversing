"""Input memory effects name pre-call values, even if the ABI clobbers them."""
import os
import shutil
import subprocess
from pathlib import Path
import pytest


@pytest.mark.parametrize('transport', ['address', 'data'])
@pytest.mark.parametrize('clobber_input', [False, True])
@pytest.mark.parametrize('effect', ['none', 'write', 'escape'])
def test_input_write_uses_pre_call_identity(tmp_path, clobber_input, effect, transport):
    root = Path(__file__).resolve().parents[1]
    cc = shutil.which('cc')
    backend = Path(os.environ.get('AMIGA_TEST_BACKEND', root/'src/build/libamiga_backend.so'))
    if not cc or not backend.exists():
        pytest.skip('native compiler and backend required')
    source = tmp_path/'input-write.c'
    source.write_text(r'''#include "m68k_analysis_render_lookup.c"
#include <assert.h>
int main(void) {
 M68kRenderTypedState state={0};M68kRenderLookup lookup={0};M68kRenderPlatformState platform={0};
 const char *copies[]={COPY_SETUP};
 for(size_t i=0;i<sizeof(copies)/sizeof(*copies);++i) {
  M68kInstructionIR copy=m68k_plain_parse_instruction_to_ir(copies[i],M68K_ASM_CPU_68000,m68k_diag_sink(NULL));
  typed_state_update_after_instruction(&state,&lookup,&platform,0,&copy,NULL,NULL,0,0);
 }
 assert(typed_state_addr_alias_equal(&state,0,1));
 state.base_slot_count=1;state.base_slots[0].known=1;state.base_slots[0].base_reg=0;
 state.base_slots[0].value.known=1;state.base_slots[0].value.struct_id=AMIGA_OS_STRUCT_ID_LIB;
 state.addr_regs[2].known=1;state.addr_regs[2].struct_id=AMIGA_OS_STRUCT_ID_LIB;
 state.addr_regs[2].origin.kind=M68K_RENDER_TYPED_ORIGIN_BASE_SLOT;
 state.addr_regs[2].origin.base_reg=0;state.addr_regs[2].entry_value_id=41;
 M68kAnalysisFunctionSummary summary={0};
 function_summary_set_register_partition(&summary,255,PRESERVED);
 summary.input_count=1;summary.inputs[0].location.kind=M68K_FUNCTION_SUMMARY_ABI_LOCATION_REGISTER;
 summary.inputs[0].location.register_count=1;
 summary.inputs[0].location.registers[0].register_kind=M68K_ANALYSIS_REGISTER_ADDRESS;
 summary.inputs[0].location.registers[0].register_index=1;
 summary.memory_effect_state=summary.escape_effect_state=M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_EXPLICIT;
 summary.memory_effect_count=HAS_WRITE;
 summary.memory_effects[0].kind=M68K_FUNCTION_SUMMARY_MEMORY_WRITE;
 summary.memory_effects[0].subject.kind=M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_INPUT;
 summary.memory_effects[0].subject.input_index=0;
 summary.escape_count=HAS_ESCAPE;
 summary.escapes[0].sink_subject.kind=M68K_FUNCTION_SUMMARY_EFFECT_SUBJECT_INPUT;
 summary.escapes[0].sink_subject.input_index=0;
 typed_state_apply_function_summary_effects(&state,&summary);
 assert(state.base_slot_count==(MEMORY_CHANGED ? 0U : 1U));
 assert(state.addr_regs[2].known==!MEMORY_CHANGED);
 assert(state.addr_regs[2].entry_value_id==41);
 assert(typed_state_addr_alias_equal(&state,0,1)==(PRESERVED==255));
 return 0;
}'''.replace('COPY_SETUP', '"movea.l a0,a1"' if transport=='address' else '"move.l a0,d0","movea.l d0,a1"').replace('PRESERVED', str(253 if clobber_input else 255)).replace('HAS_WRITE', str(int(effect=='write'))).replace('HAS_ESCAPE', str(int(effect=='escape'))).replace('MEMORY_CHANGED', str(int(effect!='none'))))
    executable=tmp_path/'input-write'
    built=subprocess.run([cc,'-Isrc','-D_POSIX_C_SOURCE=200809L','-std=c11','-O0',str(source),str(backend),
        f'-Wl,-rpath,{backend.parent}','-o',str(executable)],cwd=root,capture_output=True,text=True,timeout=60)
    assert built.returncode==0,built.stderr
    run=subprocess.run([str(executable)],capture_output=True,text=True,timeout=20)
    assert run.returncode==0,run.stdout+run.stderr
