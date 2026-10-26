"""Local pointer cells lose identity on any overlapping scalar/bulk write."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact
from tests.test_absolute_layout_base import slot

@pytest.mark.parametrize('named',[False,True])
@pytest.mark.parametrize('write,preserved',[
    ('move.b #0,5(a1)',False),
    ('move.w #0,6(a1)',False),
    ('clr.b 7(a1)',False),
    ('movem.l d0-d1,0(a1)',False),
    ('movem.w d0-d2,0(a1)',False),
    ('move.b #0,3(a1)',True),
    ('move.b #0,8(a1)',True),
    ('movem.w d0-d1,0(a1)',True),
])
def test_local_cell_write_uses_full_shared_footprint(tmp_path,named,write,preserved):
    metadata=slot()
    extra={'absolute_storage_slots':[metadata]}
    if named:
        metadata['semantic_type']='layout_base:other_base'
        extra['rsset_layout_regions']=[dict(layout_name='other',base_symbol='other_base',
            offset=0xBC6,size=120,storage_kind='byte_array',symbol='other_points')]
    a,_=cursor_artifact(tmp_path,
        'movea.l $1800.l,a0\n movea.l #$1900,a1\n move.l a0,4(a1)\n '+write+
        '\n movea.l #0,a0\n movea.l 4(a1),a0\n move.w $BC6(a0),d1',metadata_extra=extra)
    try:
        source,_=a.inline_source_text_with_profile()
        refs=a.analysis_payload()[0]['sections'][0]['app_slot_refs']
        if named:
            assert ('other_points(a0)'in source)==preserved
            assert not refs
        else:
            assert bool(refs)==preserved
            if refs:assert refs[0]['base_evidence']=='register_state'
    finally:a.close()


def test_typed_field_cell_uses_owning_cursor_and_shared_bulk_span(tmp_path):
    import os
    import shutil
    import subprocess
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    compiler=shutil.which('cc')
    backend=Path(os.environ.get('AMIGA_TEST_BACKEND',root/'src/build/libamiga_backend.so'))
    if compiler is None or not backend.exists():pytest.skip('host compiler and native backend required')
    source=tmp_path/'fields.c'
    source.write_text(r'''
#include "m68k_analysis_render_lookup.c"
#include "m68k_plain_parse.h"
#include <assert.h>
int main(void) {
  const char *writes[] = {"clr.b 5(a1)", "movem.l d0-d1,0(a1)", "movem.w d0-d1,0(a1)"};
  unsigned i;
  for (i=0; i<3; ++i) {
    M68kRenderLookup lookup = {0};
    M68kRenderTypedState state = {0};
    M68kRenderPlatformState platform = {0};
    M68kRenderTypedStoredValue value = {0};
    M68kInstructionIR instruction = m68k_plain_parse_instruction_to_ir(
      writes[i], M68K_ASM_CPU_68000, m68k_diag_sink(NULL));
    value.known = 1; value.layout_base_id = 1;
    state.addr_regs[1].known = 1; state.addr_regs[1].struct_id = 7;
    state.addr_regs[1].byte_cursor = 16;
    typed_state_set_field_slot(&state, 1, 7, 20, &value);
    assert(typed_state_field_slot_value(&state,1,7,20));
    assert(!render_lookup_record_untyped_memory_writes(&lookup,&state,&platform,0,&instruction,0,0,NULL));
    assert((typed_state_field_slot_value(&state,1,7,20)!=NULL)==(i==2));
  }
  return 0;
}
''')
    executable=tmp_path/'fields'
    build=subprocess.run([compiler,'-Isrc','-D_POSIX_C_SOURCE=200809L','-std=c11','-O0',str(source),
        str(backend),f'-Wl,-rpath,{backend.parent}','-o',str(executable)],cwd=root,capture_output=True,text=True,timeout=60)
    assert build.returncode==0,build.stderr
    result=subprocess.run([str(executable)],capture_output=True,text=True,timeout=10)
    assert result.returncode==0,result.stdout+result.stderr
