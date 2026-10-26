"""Loop bounds come from converged shared values at every external entry."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact,derived_refs

@pytest.mark.parametrize('shape',['same_count_branches','constant_arithmetic','direct_call_before_setup'])
def test_external_loop_entries_keep_equal_counter_and_cursor(tmp_path,shape):
    if shape=='same_count_branches':
        prefix='tst.w d0\n beq.w alternate\n move.w #19,d7\n lea.l $BC6(a6),a4\n bra.w head\nalternate:\n move.w #19,d7\n lea.l $BC6(a6),a4\n'
    elif shape=='constant_arithmetic':prefix='move.w #18,d7\n addq.w #1,d7\n lea.l $BC6(a6),a4\n'
    else:prefix='bsr.w helper\n move.w #19,d7\n lea.l $BC6(a6),a4\n'
    a,_=cursor_artifact(tmp_path,prefix+'head:\n move.w (a4)+,d1\n dbf d7,head\n rts\nhelper:\n rts')
    try:
        refs=[r for r in derived_refs(a)if r.get('loop_iteration_count')]
        assert len(refs)==1
        assert refs[0]['loop_iteration_count']==20 and refs[0]['loop_iteration_stride']==2
    finally:a.close()

@pytest.mark.parametrize('counter,cursor',[('18','$BC6(a6)'),('19','$C3E(a6)'),('d2','$BC6(a6)')])
def test_disagreeing_or_unknown_external_entry_cannot_claim_whole_loop(tmp_path,counter,cursor):
    count=f'#{counter}'if counter.isdigit()else counter
    prefix='tst.w d0\n beq.w alternate\n move.w #19,d7\n lea.l $BC6(a6),a4\n bra.w head\nalternate:\n '+f'move.w {count},d7\n lea.l {cursor},a4\n'
    a,_=cursor_artifact(tmp_path,prefix+'head:\n move.w (a4)+,d1\n dbf d7,head')
    try:assert not [r for r in derived_refs(a)if r.get('loop_iteration_count')]
    finally:a.close()

@pytest.mark.parametrize('setup,expected',[
    ('move.w #65535,d7\n addq.w #1,d7',1),
    ('move.w #0,d7\n subq.w #1,d7',65536),
    ('move.w #1,d7\n subq.w #1,d7',1),
    ('move.w #19,d7\n addi.l #65536,d7',20),
    ('move.w #19,d7\n addq.b #1,d7',None),
    ('move.w #19,d7\n addx.w d0,d7',None),
])
def test_low_word_modular_bounds_do_not_invent_partial_or_carry_values(tmp_path,setup,expected):
    a,_=cursor_artifact(tmp_path,setup+'\n lea.l $BC6(a6),a4\nhead:\n move.w (a4),d1\n dbf d7,head')
    try:
        refs=[r for r in derived_refs(a)if r.get('loop_iteration_count')]
        assert len(refs)==(0 if expected is None else 1)
        if refs:assert refs[0]['loop_iteration_count']==expected and refs[0]['loop_iteration_stride']==0
    finally:a.close()


def test_incomplete_scalar_solve_publishes_no_stale_count(tmp_path):
    import os,shutil,subprocess
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    compiler=shutil.which('cc');backend=Path(os.environ.get('AMIGA_TEST_BACKEND',root/'src/build/libamiga_backend.so'))
    if not compiler or not backend.exists():pytest.skip('host compiler and backend required')
    source=tmp_path/'scalar-limit.c'
    source.write_text(r'''#include "m68k_analysis_render_lookup.c"
#include <assert.h>
int main(void) {
  M68kObject object; M68kSection section={0}; M68kDecodeIR decode;
  M68kRenderLookup lookup={0}; M68kRenderTypedFlowGraph graph={0};
  M68kRenderTypedFlowNode nodes[2]={{0}}; Arena *arena=arena_create(65536);
  uint8_t raw[]={0x4e,0x71,0x4e,0x75}; size_t offsets[]={0,0,1},pred[]={0};
  assert(arena && !m68k_object_create(&object));
  section.kind=M68K_SECTION_CODE;section.data=raw;section.size=section.data_size=4;
  assert(m68k_object_add_section(&object,&section).ok);m68k_decode_ir_init(&decode);
  assert(!m68k_decode_ir_build_object_sections(&decode,&object,m68k_diag_sink(NULL)));
  for(unsigned i=0;i<2;++i)assert(!m68k_decode_ir_ensure_candidate_at(&decode,0,2*i,
    M68K_ASM_CPU_68000,&nodes[i].candidate,m68k_diag_sink(NULL)));
  nodes[0].is_root=1;nodes[0].successor_count=1;nodes[0].successors[0]=1;
  nodes[1].platform_out.word_values[7].count=1;nodes[1].platform_out.word_values[7].values[0]=19;
  graph.nodes=nodes;graph.node_count=2;graph.predecessor_offsets=offsets;graph.predecessors=pred;
  lookup.arena=arena_create(65536);assert(lookup.arena);
  assert(!setenv("AMIGA_REVERSING_TYPED_FLOW_MAX_NODE_VISITS","1",1));
  assert(!hardware_relative_analyze_graph(&lookup,&decode.sections[0],&graph,arena));
  assert(nodes[1].platform_out.word_values[7].count==0);
  assert(lookup.typed_flow_incomplete_count==1 && lookup.typed_flow_incomplete[0].hit_count==1);
  assert(lookup.typed_flow_incomplete[0].offset==2);
  m68k_decode_ir_destroy(&decode);m68k_object_destroy(&object);arena_destroy(lookup.arena);arena_destroy(arena);return 0;
}
''')
    exe=tmp_path/'scalar-limit'
    built=subprocess.run([compiler,'-Isrc','-Isrc/generated','-D_POSIX_C_SOURCE=200809L','-w',str(source),
        str(backend),f'-Wl,-rpath,{backend.parent}','-lm','-o',str(exe)],cwd=root,capture_output=True,text=True,timeout=60)
    assert built.returncode==0,built.stderr
    result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=10)
    assert result.returncode==0,result.stderr
