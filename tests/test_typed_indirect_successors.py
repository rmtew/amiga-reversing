"""Typed flow follows canonical possible JMP targets, never guessed returns."""
import pytest

from tests.test_app_cursor_propagation import cursor_artifact


def input_contract():
    return dict(custom_structs=[dict(name='Record', size=16, fields=[
        dict(name='value', offset=4, size=4, type='LONG')])], entry_register_seeds=[
            dict(hunk=0, entry_offset=0, register='A0', kind='struct_ptr',
                 struct_name='Record', note='Fixture original record input')])


def dispatch(count, *, prefix='', operation='jmp', unrelated=False):
    load = 'move.w offsets(pc,d1.w),d2' if unrelated else 'move.w offsets(pc,d1.w),d1'
    transfer = 'jmp (a3)' if unrelated else f'{operation} offsets(pc,d1.w)'
    return 'moveq #0,d1\n' + prefix + '\n' + load + '\n' + transfer + '\n' + (
        'rts\n' if operation == 'jsr' else '') + 'offsets:\n dc.w ' + ','.join(
            f'case{i}-offsets' for i in range(count)) + '\n' + '\n'.join(
                f'case{i}:\n move.l 4(a0),d0\n rts' for i in range(count))


@pytest.mark.parametrize('count', [2, 3, 8, 32])
def test_existing_relative_dispatch_targets_transport_the_same_input(tmp_path, count):
    artifact, original = cursor_artifact(tmp_path, dispatch(count), regions=False,
                                         metadata_extra=input_contract())
    try:
        analysis = artifact.analysis_payload()[0]
        assert not analysis['incomplete_analysis']
        section = analysis['sections'][0]
        site = next(r for r in section['recovered_indirect_sites'] if r['status'] == 'jump_table')
        assert site['target_count'] == count
        targets = {r['target_offset'] for r in section['edges']
                   if r['source_offset'] == site['offset'] and r['kind'] == 4}
        assert 0xFFFFFFFF in targets  # A known set is not a closed-set proof.
        rows = section['recovered_platform_typed_accesses']
        assert sum(r['field_expr'] == 'Record_value' for r in rows) == count
        source = artifact.inline_source_text_with_profile()[0]
        from amiga_reversing.disasm import c_backend
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', source)[0] == original
    finally:
        artifact.close()


@pytest.mark.parametrize('case', ['clobbered', 'unrelated_load', 'indirect_call'])
def test_new_edges_do_not_supply_unknown_values_or_call_returns(tmp_path, case):
    text = dispatch(3, prefix='movea.l d7,a0' if case == 'clobbered' else '',
                    unrelated=case == 'unrelated_load',
                    operation='jsr' if case == 'indirect_call' else 'jmp')
    artifact, _ = cursor_artifact(tmp_path, text, regions=False, metadata_extra=input_contract())
    try:
        section = artifact.analysis_payload()[0]['sections'][0]
        assert not section['recovered_platform_typed_accesses']
    finally:
        artifact.close()


def test_independent_address_exposure_keeps_an_unknown_entry(tmp_path):
    artifact, _ = cursor_artifact(tmp_path, dispatch(3, prefix='lea case0(pc),a2'),
                                  regions=False, metadata_extra=input_contract())
    try:
        section = artifact.analysis_payload()[0]['sections'][0]
        cases = sorted({r['offset'] for r in section['code_start_refs']
                        if r['evidence_kind'] == 'dispatch_table_control_target'})
        rows = section['recovered_platform_typed_accesses']
        assert cases
        assert not any(r['offset'] == cases[0] for r in rows)
        assert sum(r['field_expr'] == 'Record_value' for r in rows) == 2
    finally:
        artifact.close()


def test_graph_pool_has_no_byte_fanout_cap_and_deduplicates_provenance(tmp_path):
    import os
    from pathlib import Path
    import shutil
    import subprocess
    from amiga_reversing.disasm import c_backend
    root = Path(__file__).resolve().parents[1]
    backend = Path(os.environ.get('AMIGA_TEST_BACKEND', root / 'src/build/libamiga_backend.so'))
    compiler = shutil.which('cc')
    if compiler is None or not backend.exists():
        pytest.skip('Host compiler and native backend required')
    raw = c_backend.assemble_platform_source_text_with_c_backend(
        'amiga-raw', ' SECTION code,code\n jmp (a1)\n' + ' rts\n' * 300)[0]
    assert len(raw) == 602
    source = tmp_path / 'fanout.c'
    source.write_text('#include "m68k_analysis_render_lookup.c"\n#include <assert.h>\n'
                      'static uint8_t raw[]={' + ','.join(map(str, raw)) + '};\n' + r'''
int main(void) {
  enum { N=300, R=2*N+5 };
  M68kObject object; M68kSection section={0}; M68kDecodeIR decode;
  M68kRenderLookup lookup={0}; M68kRenderTypedFlowGraph graph={0};
  M68kFact *facts=calloc(R,sizeof(*facts));
  M68kRenderCodeStartRef refs[R]; uint8_t accepted[sizeof(raw)]={0};
  Arena *arena=arena_create(65536); assert(facts && arena);
  assert(!m68k_object_create(&object)); section.kind=M68K_SECTION_CODE;
  section.data=raw; section.size=section.data_size=sizeof(raw);
  assert(m68k_object_add_section(&object,&section).ok);
  m68k_decode_ir_init(&decode);
  assert(!m68k_decode_ir_build_object_sections(&decode,&object,m68k_diag_sink(NULL)));
  for(unsigned i=0;i<=N;++i) {
    const M68kDecodeCandidate *candidate;
    accepted[2*i]=1;
    assert(!m68k_decode_ir_ensure_candidate_at(&decode,0,2*i,
      M68K_ASM_CPU_68000,&candidate,m68k_diag_sink(NULL)));
  }
  for(unsigned i=0;i<R;++i) {
    facts[i].reason=M68K_FACT_CODE_START_REASON_CONTROL_TARGET;
    facts[i].offset=i<2*N ? 2+2*(i%N) : 0;
    refs[i].fact=&facts[i];
  }
  facts[2*N].reason=0; facts[2*N+1].section_index=1;
  facts[2*N+2].source_section_index=1;
  facts[2*N+3].offset=1; facts[2*N+4].source_offset=1;
  lookup.code_start_refs=refs; lookup.code_start_ref_count=R;
  assert(!typed_flow_graph_build(&graph,&lookup,NULL,&decode.sections[0],accepted,arena));
  assert(graph.node_count==N+1 && graph.nodes[0].successor_count==N);
  unsigned seen[N+1]={0};
  for(size_t i=0;i<graph.nodes[0].successor_count;++i) {
    size_t target=graph.nodes[0].successors[i];
    assert(target>0 && target<=N && !seen[target]); seen[target]=1;
  }
  for(unsigned i=1;i<=N;++i) {
    assert(seen[i] && !graph.nodes[i].is_root);
    assert(graph.predecessor_offsets[i+1]-graph.predecessor_offsets[i]==1);
  }
  typed_flow_graph_destroy(&graph); arena_destroy(arena); free(facts);
  m68k_decode_ir_destroy(&decode); m68k_object_destroy(&object); return 0;
}
''')
    executable = tmp_path / 'fanout'
    built = subprocess.run([compiler, '-Isrc', '-Isrc/generated', '-w', str(source),
                            str(backend), f'-Wl,-rpath,{backend.parent}', '-lm', '-o', str(executable)],
                           cwd=root, capture_output=True, text=True, timeout=60)
    assert built.returncode == 0, built.stderr
    result = subprocess.run([str(executable)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
