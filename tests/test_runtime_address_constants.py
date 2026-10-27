"""Exact external address producers use shared raw bits, not guessed pointers."""
import os
import shutil
import subprocess
from pathlib import Path

import pytest
from tests.test_app_cursor_propagation import cursor_artifact
from tests.test_absolute_layout_base import slot


def test_raw_address_producer_arithmetic_partial_copy_and_join(tmp_path):
    root = Path(__file__).resolve().parents[1]
    compiler = shutil.which('cc')
    backend = Path(os.environ.get('AMIGA_TEST_BACKEND', root / 'src/build/libamiga_backend.so'))
    if not compiler or not backend.exists():
        pytest.skip('host compiler and backend required')
    source = tmp_path / 'runtime-constants.c'
    source.write_text(r'''#include "m68k_analysis_render_lookup.c"
#include <assert.h>
static unsigned pc;
static void step(M68kRenderTypedState *s,M68kRenderLookup *l,const char *text) {
  M68kRenderPlatformState p={0};
  M68kInstructionIR i=m68k_plain_parse_instruction_to_ir(text,M68K_ASM_CPU_68000,m68k_diag_sink(NULL));
  assert(m68k_sim_metadata_for_instruction(&i));
  typed_state_update_after_instruction(s,l,&p,0,&i,NULL,NULL,pc++,0);
}
static void raw(M68kRenderTypedRegValue *v,uint32_t expected) {
  assert(v->known && v->raw_long_value_known && v->raw_long_candidate_count==1);
  assert(v->raw_long_value==expected && v->raw_long_candidates[0]==expected);
  assert(!v->pointer_value_known && !v->pointer_target_known && !v->layout_base_id && !v->byte_cursor);
}
int main(void) {
  M68kRenderTypedState state={0},low,unknown={0};M68kRenderLookup lookup={0};
  M68kAnalysisPolicy policy;m68k_analysis_policy_init_default(&policy);lookup.policy=&policy;
  step(&state,&lookup,"lea.l $68000.l,a0");raw(&state.addr_regs[0],0x68000);
  low=state;step(&low,&lookup,"suba.l #$6998,a0");raw(&low.addr_regs[0],0x61668);
  step(&state,&lookup,"adda.l #$8000,a0");raw(&state.addr_regs[0],0x70000);
  step(&state,&lookup,"suba.l #$6998,a0");raw(&state.addr_regs[0],0x69668);
  assert(state.addr_regs[0].provenance.kind==M68K_PLATFORM_TYPE_PROVENANCE_CONSTANT_VALUE);
  typed_state_merge_into(&state,&low, NULL);
  assert(state.addr_regs[0].raw_long_value_known && state.addr_regs[0].raw_long_candidate_count==2);
  assert(state.addr_regs[0].raw_long_candidates[0]==0x69668 && state.addr_regs[0].raw_long_candidates[1]==0x61668);
  typed_state_merge_into(&state,&unknown, NULL);assert(!state.addr_regs[0].raw_long_value_known);
  typed_state_merge_into(&unknown,&low, NULL);assert(!unknown.addr_regs[0].raw_long_value_known);
  step(&state,&lookup,"movea.l #$68000,a0");step(&state,&lookup,"suba.l #$6998,a0");raw(&state.addr_regs[0],0x61668);
  step(&state,&lookup,"move.l a0,d0");step(&state,&lookup,"movea.l d0,a1");raw(&state.addr_regs[1],0x61668);
  step(&state,&lookup,"movea.w a0,a1");assert(!state.addr_regs[1].raw_long_value_known);
  step(&state,&lookup,"move.w a0,d1");assert(!state.data_regs[1].raw_long_value_known);
  step(&state,&lookup,"adda.w #1,a0");assert(!state.addr_regs[0].raw_long_value_known);
  step(&state,&lookup,"movea.l #$FFFFFFFF,a0");step(&state,&lookup,"addq.l #1,a0");raw(&state.addr_regs[0],0);
  step(&state,&lookup,"movea.l #$68000,a0");step(&state,&lookup,"adda.l d2,a0");assert(!state.addr_regs[0].raw_long_value_known);
  step(&state,&lookup,"movea.l #$68000,a0");step(&state,&lookup,"suba.l #$FFFFFFFF,a0");assert(!state.addr_regs[0].raw_long_value_known);
  M68kRenderTypedStoredValue value={0};value.known=1;value.raw_long_value_known=1;value.raw_long_value=0x12345678;
  value.pointer_value_known=1;value.pointer_value=0x12345678;
  typed_stored_value_forget_concrete_long(&value);assert(!value.known && !value.raw_long_value_known && !value.pointer_value_known);
  state=(M68kRenderTypedState){0};
  step(&state,&lookup,"movea.l #$68000,a0");
  for(unsigned i=1;i<=5;++i) {
    low=(M68kRenderTypedState){0};
    low.addr_regs[0].known=low.addr_regs[0].raw_long_value_known=low.addr_regs[0].raw_long_candidate_count=1;
    low.addr_regs[0].raw_long_value=low.addr_regs[0].raw_long_candidates[0]=0x68000+i;
    typed_state_merge_into(&state,&low, NULL);
  }
  assert(!state.addr_regs[0].raw_long_value_known && state.addr_regs[0].address_value_candidate_overflow);
  step(&state,&lookup,"addq.l #1,a0");assert(!state.addr_regs[0].raw_long_value_known);
  state=(M68kRenderTypedState){0};step(&state,&lookup,"movea.l #$68000,a0");
  state.addr_regs[0].pointer_value_known=state.addr_regs[0].pointer_candidate_count=1;
  state.addr_regs[0].pointer_value=state.addr_regs[0].pointer_candidates[0]=0x68000;
  step(&state,&lookup,"addq.l #6,a0");
  assert(!state.addr_regs[0].raw_long_value_known && state.addr_regs[0].pointer_value_known);
  assert(state.addr_regs[0].pointer_value==0x68000 && state.addr_regs[0].byte_cursor==6);
  state=(M68kRenderTypedState){0};step(&state,&lookup,"movea.l #$68000,a0");
  M68kRenderTypedStorageSlot cells[1]={{0}};cells[0].kind=M68K_RENDER_TYPED_STORAGE_ABSOLUTE;
  cells[0].address=0x1800;lookup.typed_storage_slots=cells;lookup.typed_storage_slot_count=1;
  M68kRenderPlatformState platform={0};
  M68kInstructionIR word=m68k_plain_parse_instruction_to_ir("move.w a0,$1800.l",M68K_ASM_CPU_68000,m68k_diag_sink(NULL));
  assert(!render_lookup_record_typed_storage_store(&lookup,&state,&platform,0,&word,NULL,0,0,NULL));
  assert(!typed_state_absolute_cell(&state,1));
  state=(M68kRenderTypedState){0};
  state.addr_regs[6].known=1;state.addr_regs[6].layout_base_id=1;state.addr_regs[6].entry_value_id=3;
  state.addr_regs[6].struct_id=7;state.addr_regs[6].origin.kind=M68K_RENDER_TYPED_ORIGIN_LOOKUP_STORAGE;
  state.addr_regs[6].raw_long_value_known=state.addr_regs[6].raw_long_candidate_count=1;
  state.addr_regs[6].raw_long_value=state.addr_regs[6].raw_long_candidates[0]=0x69668;
  state.app_addr_regs[6].known=1;state.app_addr_regs[6].displacement=0;
  M68kAnalysisFunctionSummary summary={0};function_summary_set_register_partition(&summary,255,255);
  summary.memory_effect_state=M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_UNKNOWN;
  typed_state_apply_function_summary_effects(&state,&summary);
  assert(state.addr_regs[6].layout_base_id==1 && state.addr_regs[6].entry_value_id==3);
  assert(state.addr_regs[6].raw_long_value_known && state.addr_regs[6].raw_long_value==0x69668);
  assert(!state.addr_regs[6].struct_id && !state.addr_regs[6].origin.kind && state.app_addr_regs[6].known);
  function_summary_set_register_partition(&summary,255,191);summary.memory_effect_state=M68K_FUNCTION_SUMMARY_EFFECT_COMPONENT_UNKNOWN;
  typed_state_apply_function_summary_effects(&state,&summary);
  assert(!state.addr_regs[6].layout_base_id && !state.addr_regs[6].entry_value_id && !state.addr_regs[6].raw_long_value_known);
  M68kRenderTypedRegValue role={0},literal={0};role.known=1;role.layout_base_id=1;
  literal.known=literal.raw_long_value_known=literal.raw_long_candidate_count=1;
  literal.raw_long_value=literal.raw_long_candidates[0]=0x68000;
  M68kRenderTypedRegValue joined=role;typed_reg_merge(&joined,&literal, NULL);assert(!joined.raw_long_value_known);
  joined=literal;typed_reg_merge(&joined,&role, NULL);assert(!joined.raw_long_value_known);
  M68kRenderTypedStoredValue typed={0},number={0};typed.known=1;typed.struct_id=1;
  number=typed;number.raw_long_value_known=number.raw_long_candidate_count=1;number.raw_long_value=number.raw_long_candidates[0]=0x68000;
  M68kRenderTypedStoredValue merged=typed;typed_stored_value_merge(&merged,&number, NULL);assert(!merged.raw_long_value_known && merged.struct_id==1);
  merged=number;typed_stored_value_merge(&merged,&typed, NULL);assert(!merged.raw_long_value_known && merged.struct_id==1);
  role=(M68kRenderTypedRegValue){0};role.known=1;role.struct_id=1;
  literal=role;literal.pointer_value_known=literal.pointer_candidate_count=1;
  literal.pointer_value=literal.pointer_candidates[0]=0x68000;
  joined=role;typed_reg_merge(&joined,&literal, NULL);assert(!joined.pointer_value_known && joined.struct_id==1);
  joined=literal;typed_reg_merge(&joined,&role, NULL);assert(!joined.pointer_value_known && joined.struct_id==1);
  assert(sizeof(M68kRenderTypedState)==32616 && sizeof(M68kRenderTypedStoredValue)==248);
  m68k_analysis_policy_destroy(&policy);return 0;
}
''')
    executable = tmp_path / 'runtime-constants'
    build = subprocess.run([compiler, '-Isrc', '-Isrc/generated', '-w', str(source), str(backend),
                            f'-Wl,-rpath,{backend.parent}', '-lm', '-o', str(executable)],
                           cwd=root, capture_output=True, text=True, timeout=45)
    assert build.returncode == 0, build.stderr
    result = subprocess.run([str(executable)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize('producer,expected', [
    ('lea.l $68000.l,a0\n suba.l #$6998,a0', 0x61668),
    ('lea.l $68000.l,a0\n adda.l #$8000,a0\n suba.l #$6998,a0', 0x69668),
    ('movea.l #$68000,a0\n suba.l #$6998,a0', 0x61668),
    ('movea.l #$1080,a0\n addq.l #4,a0', 0x1084),
])
def test_typed_store_uses_computed_bits_without_rewriting_initial_expression(tmp_path, producer, expected):
    suffix = '\n rts\n dcb.b $90,0' if expected == 0x1084 else ''
    artifact, original = cursor_artifact(tmp_path, producer + '\n move.l a0,$1800.l' + suffix,
                                        metadata_extra={'absolute_storage_slots': [slot()]})
    try:
        analysis, _ = artifact.analysis_payload()
        values = [v for v in analysis['sections'][0]['address_values'] if v['source_value'] == expected]
        assert values and all(v['origin_kind'] == 'constant_value' and not v['has_source_expression'] for v in values)
        from amiga_reversing.disasm import c_backend
        source, _ = artifact.inline_source_text_with_profile()
        rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', source)
        assert rebuilt == original
    finally:
        artifact.close()


@pytest.mark.parametrize('left,right', [(0x1080, 0x68000), (0x68000, 0x1080),
                                      (0x68000, 0x70000), (0x1080, 0x1084)])
def test_numeric_candidates_have_independent_optional_source_targets(tmp_path, left, right):
    body = (f'tst.w d0\n beq.w second\n movea.l #${left:X},a0\n bra.w joined\n'
            f'second:\n movea.l #${right:X},a0\njoined:\n addq.l #4,a0\n'
            'move.l a0,$1800.l\n rts\n dcb.b $90,0')
    artifact, original = cursor_artifact(tmp_path, body,
                                        metadata_extra={'absolute_storage_slots': [slot()]})
    try:
        analysis, _ = artifact.analysis_payload()
        expected = {left + 4, right + 4}
        value = next(v for v in analysis['sections'][0]['address_values']
                     if set(v['candidate_source_values']) == expected)
        assert len(value['candidate_targets']) == len(expected)
        targets = dict(zip(value['candidate_source_values'], value['candidate_targets']))
        for address in expected:
            if address < 0x1100:
                assert targets[address] == {'has_target': True, 'section_index': 0, 'offset': address - 0x1000}
            else:
                assert targets[address] == {'has_target': False, 'section_index': None, 'offset': None}
        assert value['resolution'] == ('finite_candidate_targets' if max(expected) < 0x1100
                                        else 'outside_known_address_space')
        assert 'target_section_index' not in value
        from amiga_reversing.disasm import c_backend
        source, _ = artifact.inline_source_text_with_profile()
        rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', source)
        assert rebuilt == original
    finally:
        artifact.close()


def test_candidate_projection_keeps_native_index_width_and_clears_old_targets(tmp_path):
    root = Path(__file__).resolve().parents[1]
    compiler = shutil.which('cc')
    backend = Path(os.environ.get('AMIGA_TEST_BACKEND', root / 'src/build/libamiga_backend.so'))
    if not compiler or not backend.exists():
        pytest.skip('host compiler and backend required')
    source = tmp_path / 'candidate-indices.c'
    source.write_text(r'''#include "m68k_analysis_render_lookup.c"
#include <assert.h>
int main(void) {
  M68kRenderLookup lookup={0};M68kRenderTypedAddressConsumer observed={0};M68kSectionAnalysisIR section={0};
  observed.fact.kind=M68K_ADDRESS_VALUE_CONSUMER_STORAGE;observed.fact.offset=24;
  observed.candidate_target_count=3;observed.resolution=M68K_ADDRESS_VALUE_RESOLUTION_OUTSIDE_KNOWN_ADDRESS_SPACE;
  observed.candidate_source_values[0]=0x1000;observed.candidate_source_values[1]=0x2000;observed.candidate_source_values[2]=0x3000;
  observed.candidate_target_section_indices[0]=2;observed.candidate_target_section_indices[1]=7;
  observed.candidate_target_section_indices[2]=SIZE_MAX;
  observed.candidate_target_offsets[0]=4;observed.candidate_target_offsets[1]=8;
  lookup.address_value_consumers=&observed;lookup.address_value_consumer_count=lookup.address_value_consumer_capacity=1;
  section.arena=arena_create(4096);assert(section.arena);
  assert(!append_render_lookup_address_value_consumers_for_section(&lookup,&section));assert(section.address_value_count==1);
  assert(section.address_values[0].candidate_target_section_indices[0]==2);
  assert(section.address_values[0].candidate_target_section_indices[1]==7);
  assert(section.address_values[0].candidate_target_section_indices[2]==UINT32_MAX);
  assert(section.address_values[0].candidate_target_offsets[1]==8);
  arena_destroy(section.arena);
  observed.candidate_target_count=1;observed.has_target=1;observed.target_section_index=2;observed.target_offset=4;
  observed.value.known=observed.value.pointer_value_known=observed.value.pointer_candidate_count=1;
  observed.value.pointer_value=observed.value.pointer_candidates[0]=0x1000;
  M68kRenderTypedStoredValue other=observed.value;other.pointer_value=other.pointer_candidates[0]=0x2000;
  assert(!render_lookup_add_typed_address_consumer(&lookup,0,&observed.fact,&other,NULL));
  assert(observed.candidate_target_count==2 && !observed.has_target);
  assert(observed.candidate_target_section_indices[0]==SIZE_MAX && observed.candidate_target_section_indices[1]==SIZE_MAX);
  return 0;
}
''')
    executable = tmp_path / 'candidate-indices'
    build = subprocess.run([compiler, '-Isrc', '-Isrc/generated', '-w', str(source), str(backend),
                            f'-Wl,-rpath,{backend.parent}', '-lm', '-o', str(executable)],
                           cwd=root, capture_output=True, text=True, timeout=45)
    assert build.returncode == 0, build.stderr
    result = subprocess.run([str(executable)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize('producer', ['', 'lea.l $68000.l,a0\n suba.l #$6998,a0\n move.l a0,$1800.l\n'])
@pytest.mark.parametrize('callee', ['opaque_memory', 'static_write', 'register_clobber'])
def test_memory_effects_do_not_erase_preserved_declared_base_identity(tmp_path, producer, callee):
    inner = {'opaque_memory': 'move.w #0,(a2)', 'static_write': 'move.w #0,$1800.l',
             'register_clobber': 'movea.l #0,a6'}[callee]
    body = ('bsr.w helper\n rts\nhelper:\n ' + producer + 'movea.l $1800.l,a6\n bsr.w inner\n'
            'move.w $BC6(a6),d0\n rts\ninner:\n ' + inner + '\n rts')
    artifact, _ = cursor_artifact(tmp_path, body,
                                 metadata_extra={'absolute_storage_slots': [slot()]})
    try:
        refs = [r for r in artifact.analysis_payload()[0]['sections'][0]['app_slot_refs']
                if r['displacement'] == 0xBC6 and r['base_register'] == 'A6']
        assert refs
        assert all((r['base_evidence'] == 'register_state') == (callee != 'register_clobber') for r in refs)
    finally:
        artifact.close()


@pytest.mark.parametrize('order', ['before', 'after'])
def test_future_writer_is_not_a_reaching_numeric_definition(tmp_path, order):
    from amiga_reversing.disasm import c_backend
    producer = 'lea.l $68000.l,a1\n suba.l #$6998,a1\n move.l a1,holder.l\n'
    consumer = 'movea.l holder.l,a0\n move.l a0,$1800.l\n'
    body = (consumer + producer if order == 'before' else producer + consumer) + 'rts\nholder:\n dc.l 0'
    encoded, _ = c_backend.assemble_platform_source_text_with_c_backend(
        'amiga-raw', ' SECTION code,code\n ORG $1000\n' + body + '\n rts')
    holder = dict(address=0x1000 + len(encoded) - 6, size=4, symbol='holder_cell', storage_kind='pointer')
    artifact, original = cursor_artifact(tmp_path, body,
                                        metadata_extra={'absolute_storage_slots': [slot(), holder]})
    try:
        section = artifact.analysis_payload()[0]['sections'][0]
        consumers = [r for r in section['address_value_consumers'] if r['contract_name'] == 'workspace_holder']
        ids = {r['address_value_id'] for r in consumers}
        values = [r for r in section['address_values'] if r['id'] in ids]
        assert values and all((r['source_value'] == 0x61668) == (order == 'after') for r in values)
        source, _ = artifact.inline_source_text_with_profile()
        rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', source)
        assert rebuilt == original
    finally:
        artifact.close()


@pytest.mark.parametrize('reverse', [False, True])
def test_unknown_numeric_bits_absorb_constant_at_typed_join(tmp_path, reverse):
    arms = ['movea.l $1900.l,a0', 'movea.l #$68000,a0']
    if reverse:
        arms.reverse()
    body = ('tst.w d0\n beq.w other\n ' + arms[0] + '\n bra.w joined\nother:\n ' +
            arms[1] + '\njoined:\n suba.l #$6998,a0\n move.l a0,$1800.l\n rts')
    other = slot(); other.update(address=0x1900, symbol='unknown_base_holder')
    artifact, _ = cursor_artifact(tmp_path, body,
                                 metadata_extra={'absolute_storage_slots': [slot(), other]})
    try:
        section = artifact.analysis_payload()[0]['sections'][0]
        ids = {r['address_value_id'] for r in section['address_value_consumers']
               if r['contract_name'] == 'workspace_holder'}
        values = [r for r in section['address_values'] if r['id'] in ids]
        assert values and all(r['source_value'] == 0 and not r['candidate_target_count'] for r in values)
    finally:
        artifact.close()


def test_incomplete_cfg_does_not_publish_provisional_address_value(tmp_path, monkeypatch):
    monkeypatch.setenv('AMIGA_REVERSING_TYPED_FLOW_MAX_NODE_VISITS', '1')
    artifact, _ = cursor_artifact(tmp_path, 'move.l #$68000,$1800.l\n nop\n nop\n rts',
                                 metadata_extra={'absolute_storage_slots': [slot()]})
    try:
        analysis, _ = artifact.analysis_payload()
        assert analysis['incomplete_analysis']
        assert not analysis['sections'][0]['address_value_consumers']
    finally:
        artifact.close()
