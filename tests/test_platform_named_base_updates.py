"""Register-held base identity follows complete copies, not changed values."""
import shutil
import subprocess
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_named_base_register_write_invalidation(tmp_path):
    compiler = shutil.which('cc')
    if compiler is None:
        pytest.skip('native host compiler required')
    source = tmp_path / 'named_base.c'
    source.write_text(r'''#include "m68k_render_ir.c"
#include "m68k_plain_parse.h"
#include <assert.h>
static void apply(M68kRenderPlatformState *state, const char *text) {
  M68kRenderLookup lookup = {0};
  M68kInstructionIR i = m68k_plain_parse_instruction_to_ir(text, M68K_ASM_CPU_68000, m68k_diag_sink(NULL));
  assert(m68k_sim_metadata_for_instruction(&i));
  platform_state_update_after_instruction(state, &lookup, &i);
}
int main(void) {
  const char *changes[] = {"addq.l #2,a0", "movea.w a6,a0", "clr.l d0", "move.w a6,d0", "move.w (a0)+,d1", "move.l d1,-(a0)"};
  unsigned int k, layout;
  for(layout=0;layout<2;++layout) for(k=0;k<6;++k) {
    M68kRenderPlatformState state = {0};
    if(layout) platform_state_set_register_layout_base(&state, M68K_ANALYSIS_REGISTER_ADDRESS, 6, "workspace");
    else platform_state_set_register_app_base(&state, M68K_ANALYSIS_REGISTER_ADDRESS, 6);
    apply(&state, "movea.l a6,a0");
    apply(&state, "move.l a6,d0");
    apply(&state, "movea.l a0,a0");
    apply(&state, "move.l d0,d0");
    assert(m68k_bitset_u32_has(layout ? state.address_layout_base_known : state.address_app_base_known,0));
    assert(m68k_bitset_u32_has(layout ? state.data_layout_base_known : state.data_app_base_known,0));
    apply(&state, "move.w (a0),d1"); /* reading does not change the base */
    assert(m68k_bitset_u32_has(layout ? state.address_layout_base_known : state.address_app_base_known,0));
    apply(&state, changes[k]);
    if(k<2 || k>=4) {
      assert(!m68k_bitset_u32_has(state.address_app_base_known,0));
      assert(!m68k_bitset_u32_has(state.address_layout_base_known,0));
    } else {
      assert(!m68k_bitset_u32_has(state.data_app_base_known,0));
      assert(!m68k_bitset_u32_has(state.data_layout_base_known,0));
    }
  }
  return 0;
}
''')
    build = ROOT / 'src/build'
    executable = tmp_path / 'named_base'
    result = subprocess.run([compiler,'-std=c11','-D_POSIX_C_SOURCE=200809L','-O0','-Isrc',str(source),
        '-L'+str(build),'-lamiga_backend','-Wl,-rpath,'+str(build),'-lm','-o',str(executable)],
        cwd=ROOT,capture_output=True,text=True,timeout=60)
    assert result.returncode == 0,result.stderr
    result = subprocess.run([str(executable)],capture_output=True,text=True,timeout=10)
    assert result.returncode == 0,result.stderr
