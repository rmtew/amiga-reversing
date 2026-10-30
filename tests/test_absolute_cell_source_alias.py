"""Indirect source-backed writes share direct absolute-cell alias coordinates."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact, derived_refs


@pytest.mark.parametrize('middle,preserved', [
    ('move.w #0,other.l', True),
    ('lea.l other.l,a2\n move.w #0,(a2)', True),
    ('lea.l holder.l,a2\n move.w #0,(a2)', False),
    ('lea.l holder.l,a2\n move.b #0,3(a2)', False),
    ('lea.l holder.l,a2\n move.b #0,4(a2)', True),
    ('lea.l holder.l,a2\n move.b #0,-1(a2)', True),
    ('lea.l holder.l,a2\n movem.l d0-d1,-4(a2)', False),
    ('lea.l holder.l,a2\n movem.w d0-d2,-4(a2)', False),
    ('lea.l holder.l,a2\n movem.w d0-d1,-4(a2)', True),
    ('lea.l other.l,a2\n movea.l a2,a3\n move.w #0,(a3)', True),
    ('lea.l other.l,a2\n addq.l #2,a2\n move.w #0,(a2)', True),
    ('lea.l other.l,a2\n subq.l #4,a2\n move.w #0,(a2)', False),
    ('lea.l other.l,a2\n movea.w d0,a2\n move.w #0,(a2)', False),
    ('lea.l holder.l,a2\n move.w #0,0(a2,d0.w)', False),
    ('move.w #0,(a2)', False),
    ('move.w #0,$54(a6)', False),
    ('tst.w d0\n beq.w use_holder\n lea.l other.l,a2\n bra.w joined\n'
     'use_holder:\n lea.l holder.l,a2\njoined:\n move.w #0,(a2)', False),
])
def test_source_backed_write_aliases_exact_cell_span(tmp_path, middle, preserved):
    body = ('lea.l $C3E(a6),a0\n move.l a0,holder.l\n ' + middle +
            '\n movea.l holder.l,a1\n move.w (a1),d0\n rts\n'
            'holder:\n dc.l 0\nother:\n dc.l 0,0,0')
    artifact, original = cursor_artifact(tmp_path, body)
    try:
        reads = [r for r in derived_refs(artifact)
                 if r['base_register'] == 'A1' and r['access'] == 'read']
        assert bool(reads) == preserved
        from amiga_reversing.disasm import c_backend
        source, _ = artifact.inline_source_text_with_profile()
        rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', source)
        assert rebuilt == original
    finally:
        artifact.close()


def test_alias_span_mapping_refuses_ambiguous_partial_and_wrapping_views(tmp_path):
    import os
    import shutil
    import subprocess
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    compiler = shutil.which('cc')
    backend = Path(os.environ.get('AMIGA_TEST_BACKEND', root / 'src/build/libamiga_backend.so'))
    if not compiler or not backend.exists():
        pytest.skip('host compiler and backend required')
    source = tmp_path / 'runtime-span.c'
    source.write_text(r'''#include "m68k_render_lookup_internal.h"
#include <assert.h>
int main(void) {
  M68kRenderLookup lookup={0};
  M68kFact facts[2]={{0}};
  M68kRenderRuntimeAddressRange ranges[2]={{0}};
  uint32_t address;
  for(unsigned i=0;i<2;++i) {
    facts[i].kind=M68K_FACT_RUNTIME_ADDRESS_RANGE;
    facts[i].section_index=0;facts[i].has_runtime_address=1;
    facts[i].size=16;facts[i].runtime_address=0x1000;
    ranges[i].fact=&facts[i];ranges[i].materialization_cached=1;ranges[i].materialized=1;
  }
  lookup.build_complete=1;lookup.runtime_address_ranges=ranges;lookup.runtime_address_range_count=1;
  assert(lookup_source_unique_runtime_span(&lookup,0,8,2,&address)&&address==0x1008);
  assert(lookup_source_unique_runtime_span(&lookup,0,14,2,&address)&&address==0x100E);
  assert(!lookup_source_unique_runtime_span(&lookup,0,15,2,&address));
  assert(!lookup_source_unique_runtime_span(&lookup,1,8,2,&address));
  assert(!lookup_source_unique_runtime_span(&lookup,0,8,0,&address));
  assert(!lookup_source_unique_runtime_span(&lookup,0,UINT32_MAX,2,&address));
  lookup.runtime_address_range_count=2;
  assert(lookup_source_unique_runtime_span(&lookup,0,8,2,&address)&&address==0x1008);
  facts[1].runtime_address=0x2000;
  assert(!lookup_source_unique_runtime_span(&lookup,0,8,2,&address));
  ranges[1].materialized=0;
  assert(lookup_source_unique_runtime_span(&lookup,0,8,2,&address)&&address==0x1008);
  ranges[1].materialized=1;facts[1].offset=8;facts[1].size=2;facts[1].runtime_address=0x1008;
  assert(!lookup_source_unique_runtime_span(&lookup,0,7,4,&address));
  lookup.runtime_address_range_count=1;facts[0].runtime_address=UINT32_MAX-7;
  assert(!lookup_source_unique_runtime_span(&lookup,0,7,2,&address));
  return 0;
}
''')
    executable = tmp_path / 'runtime-span'
    build = subprocess.run([compiler, '-Isrc', str(source), str(backend),
                            f'-Wl,-rpath,{backend.parent}', '-o', str(executable)],
                           cwd=root, capture_output=True, text=True, timeout=30)
    assert build.returncode == 0, build.stderr
    result = subprocess.run([str(executable)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr


def test_no_runtime_mapping_work_without_live_absolute_cells(tmp_path):
    import os
    import shutil
    import subprocess
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    compiler = shutil.which('cc')
    backend = Path(os.environ.get('AMIGA_TEST_BACKEND', root / 'src/build/libamiga_backend.so'))
    if not compiler or not backend.exists():
        pytest.skip('host compiler and backend required')
    source = tmp_path / 'lazy-span.c'
    source.write_text(r'''#include "m68k_analysis_render_lookup.c"
#include <assert.h>
static unsigned mappings;
int lookup_source_unique_runtime_span(const M68kRenderLookup *l,size_t s,uint32_t o,uint32_t w,uint32_t *r) {
  (void)l;(void)s;(void)o;(void)w;(void)r;++mappings;return 0;
}
int main(void) {
  M68kRenderLookup lookup={0};M68kRenderTypedState state={0};M68kRenderTypedStoredValue value={0};
  M68kInstructionIR write=m68k_plain_parse_instruction_to_ir("clr.w (a2)",M68K_ASM_CPU_68000,m68k_diag_sink(NULL));
  typed_state_set_memory_base(&state,M68K_ANALYSIS_REGISTER_ADDRESS,2,0,16);
  for(unsigned i=0;i<10000;++i)typed_state_note_storage_write(&state,&lookup,NULL,0,&write,0,2);
  assert((state.memory_write_barriers & M68K_CELL_WRITTEN_ABSOLUTE) && !mappings);
  value.known=1;value.layout_base_id=1;typed_state_set_base_slot(&state,3,0,&value);
  typed_state_note_storage_write(&state,&lookup,NULL,0,&write,0,2);assert(!mappings);
  typed_state_set_memory_cell(&state,1,&value);
  typed_state_note_storage_write(&state,&lookup,NULL,0,&write,0,2);assert(mappings==1);
  assert(!typed_state_memory_cell(&state,1));return 0;
}
''')
    executable = tmp_path / 'lazy-span'
    build = subprocess.run([compiler, '-Isrc', '-Isrc/generated', '-w', str(source), str(backend),
                            f'-Wl,-rpath,{backend.parent}', '-lm', '-o', str(executable)],
                           cwd=root, capture_output=True, text=True, timeout=30)
    assert build.returncode == 0, build.stderr
    result = subprocess.run([str(executable)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
