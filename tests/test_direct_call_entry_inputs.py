"""Known direct-call CFG inputs are distinct from independent entry contracts."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact
from tests.test_absolute_layout_base import slot


@pytest.mark.parametrize('setup', [
    'movea.l $1800.l,a0',
    'movea.l $1800.l,a4\n movea.l a4,a0',
    'movea.l $1800.l,a4\n move.l a4,-(a7)\n movea.l (a7)+,a0',
])
def test_direct_call_uses_pre_call_register_packet(tmp_path, setup):
    a,original=cursor_artifact(tmp_path, setup+'''
 bsr.w callee
 rts
callee:
 move.w $BC6(a0),d0
 movea.l #0,a0
 rts''', metadata_extra={'absolute_storage_slots':[slot()]})
    try:
        s=a.analysis_payload()[0]['sections'][0]
        refs=[r for r in s['app_slot_refs'] if r['base_register']=='A0']
        assert len(refs)==1 and refs[0]['base_evidence']=='register_state'
        from amiga_reversing.disasm import c_backend
        source=a.inline_source_text_with_profile()[0]
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',source,
            include_dir=c_backend.PROJECT_ROOT/'ext/amiga_includes/ndk_2.0/include')[0]==original
    finally:a.close()


@pytest.mark.parametrize('other_setup,expected', [
    ('movea.l $1800.l,a0', True),
    ('movea.l #$1234,a0', False),
    ('movea.w $1800.l,a0', False),
    ('nop', False),
])
def test_all_known_callers_join_conservatively(tmp_path, other_setup, expected):
    a,_=cursor_artifact(tmp_path, '''tst.w d0
 beq.w other
 movea.l $1800.l,a0
 bsr.w callee
 rts
other:
 '''+other_setup+'''
 bsr.w callee
 rts
callee:
 move.w $BC6(a0),d0''',metadata_extra={'absolute_storage_slots':[slot()]})
    try:
        assert bool([r for r in a.analysis_payload()[0]['sections'][0]['app_slot_refs']
            if r['base_register']=='A0'])==expected
    finally:a.close()


@pytest.mark.parametrize('exposure', ['entry', 'address'])
def test_independent_entry_cannot_inherit_subset_of_callers(tmp_path, exposure):
    # fixed encodings: LEA(6)+BSR.W(4)+RTS(2), callee at offset12.
    prefix='lea.l callee.l,a1\n' if exposure=='address' else ''
    metadata={'absolute_storage_slots':[slot()]}
    if exposure=='entry':metadata['seeded_code_entrypoints']=[{'hunk':0,'addr':12}]
    a,_=cursor_artifact(tmp_path,prefix+'''movea.l $1800.l,a0
 bsr.w callee
 rts
callee:
 move.w $BC6(a0),d0''',metadata_extra=metadata)
    try:
        assert not [r for r in a.analysis_payload()[0]['sections'][0]['app_slot_refs']
            if r['base_register']=='A0']
    finally:a.close()


def test_call_does_not_import_caller_private_stack(tmp_path):
    a,_=cursor_artifact(tmp_path,'''movea.l $1800.l,a0
 move.l a0,-(a7)
 bsr.w callee
 addq.l #4,a7
 rts
callee:
 movea.l (a7),a1
 move.w $BC6(a1),d0''',metadata_extra={'absolute_storage_slots':[slot()]})
    try:
        assert not [r for r in a.analysis_payload()[0]['sections'][0]['app_slot_refs']
            if r['base_register']=='A1']
    finally:a.close()


def test_nested_call_chain_uses_same_worklist(tmp_path):
    a,_=cursor_artifact(tmp_path,'''movea.l $1800.l,a0
 bsr.w first
 rts
first:
 movea.l a0,a4
 bsr.w second
 rts
second:
 move.w $BC6(a4),d0''',metadata_extra={'absolute_storage_slots':[slot()]})
    try:
        analysis=a.analysis_payload()[0]
        assert not analysis['incomplete_analysis']
        assert [(r['base_register'],r['base_evidence']) for r in analysis['sections'][0]['app_slot_refs']]==[('A4','register_state')]
    finally:a.close()


@pytest.mark.parametrize('mutation', ['', 'addq.l #2,a0'])
def test_recursive_call_inputs_converge_without_inventing_a_fixed_cursor(tmp_path, mutation):
    a,_=cursor_artifact(tmp_path,'''movea.l $1800.l,a0
 bsr.w recurse
 rts
recurse:
 move.w $BC6(a0),d0
 tst.w d1
 beq.w done
 '''+mutation+'''
 bsr.w recurse
done:
 rts''',metadata_extra={'absolute_storage_slots':[slot()]})
    try:
        p=a.analysis_payload()[0]
        assert not p['incomplete_analysis']
        refs=[r for r in p['sections'][0]['app_slot_refs'] if r['base_register']=='A0']
        assert bool(refs)==(not mutation)
    finally:a.close()


def test_input_projection_keeps_registers_not_private_memory(tmp_path):
    import os,shutil,subprocess
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    compiler=shutil.which('cc');backend=Path(os.environ.get('AMIGA_TEST_BACKEND',root/'src/build/libamiga_backend.so'))
    if not compiler or not backend.exists():pytest.skip('native compiler and backend required')
    source=tmp_path/'call-input.c'
    source.write_text(r'''#include "m68k_analysis_render_lookup.c"
#include <assert.h>
int main(void) {
 M68kRenderLookup lookup={0};M68kDecodeSectionIR section={0};
 M68kDecodeCandidate candidate={0};M68kRenderTypedFlowNode caller={0};
 M68kRenderTypedState entry;M68kRenderPlatformState platform;
 M68kAnalysisPolicy policy={0};
 M68kAnalysisRegisterSeed seed={0};
 M68kAnalysisEntryPoint code_entry={0};
 seed.has_section_index=seed.has_entry_offset=1;seed.section_index=0;seed.entry_offset=8;
 m68k_analysis_policy_init_default(&policy);
 policy.register_seeds[0]=seed;policy.register_seed_count=1;lookup.policy=&policy;
 assert(!typed_flow_exposed_entry(&lookup,0,8));
 code_entry.has_section_index=1;code_entry.section_index=0;code_entry.offset=8;
 policy.entry_points[0]=code_entry;policy.entry_point_count=1;
 assert(typed_flow_exposed_entry(&lookup,0,8));
 lookup.policy=NULL;
 caller.candidate=&candidate;
 caller.typed_in.addr_regs[0].known=caller.typed_in.addr_regs[0].raw_long_value_known=1;
 caller.typed_in.addr_regs[0].raw_long_value=0x1800;
 caller.typed_in.addr_regs[0].entry_value_id=41;
 caller.typed_in.app_addr_regs[0].known=1;caller.typed_in.app_addr_regs[0].displacement=20;
 caller.typed_in.addr_regs[7]=caller.typed_in.addr_regs[0];
 caller.typed_in.app_addr_regs[7]=caller.typed_in.app_addr_regs[0];
 caller.typed_in.stack_slot_count=caller.typed_in.base_slot_count=caller.typed_in.field_slot_count=1;
 caller.typed_in.stack_slots[0].known=caller.typed_in.base_slots[0].known=caller.typed_in.field_slots[0].known=1;
 caller.platform_in.address_app_base_known=1U<<7;
 caller.platform_in.local_base_slots[0].valid=1;
 typed_flow_call_entry_input(&lookup,&section,&caller,&entry,&platform);
 assert(entry.addr_regs[0].raw_long_value==0x1800 && entry.addr_regs[0].entry_value_id==41);
 assert(entry.app_addr_regs[0].known && entry.app_addr_regs[0].displacement==20);
 assert(!entry.addr_regs[7].known && !entry.app_addr_regs[7].known);
 assert(!entry.stack_slot_count && !entry.base_slot_count && !entry.field_slot_count);
 assert(!entry.stack_slots[0].known && !entry.base_slots[0].known && !entry.field_slots[0].known);
 assert((entry.memory_write_barriers == M68K_CELL_WRITTEN_ALL) && !platform.address_app_base_known && !platform.local_base_slots[0].valid);
 assert(caller.typed_in.stack_slot_count==1 && caller.typed_in.addr_regs[7].known);
 /* A canonical memory identity is not caller-private register-relative state. */
 caller.typed_in.base_slot_count=2;
 caller.typed_in.base_slots[1].known=1;
 caller.typed_in.base_slots[1].storage_id=1;
 caller.typed_in.base_slots[1].value.known=1;
 caller.typed_in.base_slots[1].value.raw_long_value_known=1;
 caller.typed_in.base_slots[1].value.raw_long_value=0x1234;
 typed_flow_call_entry_input(&lookup,&section,&caller,&entry,&platform);
 assert(entry.base_slot_count==1 && entry.base_slots[0].storage_id==1);
 assert(entry.base_slots[0].value.raw_long_value_known && entry.base_slots[0].value.raw_long_value==0x1234);
 assert(!entry.base_slots[1].known && !entry.stack_slot_count && !entry.field_slot_count);
 assert(caller.typed_in.base_slot_count==2);
 return 0;
}''')
    exe=tmp_path/'call-input'
    built=subprocess.run([compiler,'-Isrc','-D_POSIX_C_SOURCE=200809L','-std=c11','-O0',str(source),str(backend),
        f'-Wl,-rpath,{backend.parent}','-o',str(exe)],cwd=root,capture_output=True,text=True,timeout=60)
    assert built.returncode==0,built.stderr
    run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
    assert run.returncode==0,run.stdout+run.stderr


def test_conflicting_call_retires_prior_noncall_path_projection(tmp_path):
    a,_=cursor_artifact(tmp_path,'''tst.w d0
 beq.w via_branch
 movea.l #$1234,a0
 bsr.w callee
 rts
via_branch:
 movea.l $1800.l,a0
 bra.w callee
callee:
 move.w $BC6(a0),d0''',metadata_extra={'absolute_storage_slots':[slot()]})
    try:
        assert not [r for r in a.analysis_payload()[0]['sections'][0]['app_slot_refs']
                    if r['base_register']=='A0']
    finally:a.close()


def test_proven_hardware_call_input_retires_conditional_a6_app_fallback(tmp_path):
    a,_=cursor_artifact(tmp_path,'''lea.l $DFF000.l,a6
 bsr.w callee
 rts
callee:
 move.w $BC6(a6),d0''')
    try:
        assert not a.analysis_payload()[0]['sections'][0]['app_slot_refs']
    finally:a.close()


def test_typed_pointer_escape_keeps_independent_entry_unknown(tmp_path):
    a,_=cursor_artifact(tmp_path,'''move.l #callee,$1804.l
 movea.l $1800.l,a0
 bsr.w callee
 rts
callee:
 move.w $BC6(a0),d0''',metadata_extra={'absolute_storage_slots':[
        slot(),dict(address=0x1804,size=4,symbol='callback_holder',storage_kind='pointer')]})
    try:
        assert not [r for r in a.analysis_payload()[0]['sections'][0]['app_slot_refs']
            if r['base_register']=='A0']
    finally:a.close()


@pytest.mark.parametrize('adjustment,nonapp', [
    ('addq.l #2,a6', True),
    ('suba.l #$D00000,a6', False),
    ('movea.l (a0),a6', False),
    ('movea.w a6,a6', False),
])
def test_exact_hardware_domain_uses_current_bits_not_stale_root(tmp_path, adjustment, nonapp):
    a,_=cursor_artifact(tmp_path,'''lea.l $DFF000.l,a6
 '''+adjustment+'''
 bsr.w callee
 rts
callee:
 move.w $BC6(a6),d0''')
    try:
        refs=a.analysis_payload()[0]['sections'][0]['app_slot_refs']
        assert bool(refs)==(not nonapp)
        if refs:assert all(r['base_evidence']=='a6_fallback' for r in refs)
    finally:a.close()


def test_pointer_escape_discovered_through_call_cannot_certify_other_entry(tmp_path):
    a,_=cursor_artifact(tmp_path,'''movea.l #callee,a1
 bsr.w publish_callback
 movea.l $1800.l,a0
 bsr.w callee
 rts
publish_callback:
 move.l a1,$1804.l
 rts
callee:
 move.w $BC6(a0),d0''',metadata_extra={'absolute_storage_slots':[
        slot(),dict(address=0x1804,size=4,symbol='callback_holder',storage_kind='pointer')]})
    try:
        assert not [r for r in a.analysis_payload()[0]['sections'][0]['app_slot_refs']
            if r['base_register']=='A0']
    finally:a.close()


def test_computed_pointer_escape_discovered_after_input_propagation(tmp_path):
    a,_=cursor_artifact(tmp_path,'''movea.l #$70000,a1
 bsr.w publish_callback
 movea.l $1800.l,a0
 bsr.w callee
 rts
publish_callback:
 suba.l #$6EFDC,a1
 move.l a1,$1804.l
 rts
callee:
 move.w $BC6(a0),d0''',metadata_extra={'absolute_storage_slots':[
        slot(),dict(address=0x1804,size=4,symbol='callback_holder',storage_kind='pointer')]})
    try:
        section=a.analysis_payload()[0]['sections'][0]
        assert any(e['kind']==3 and e['source_offset']==16 and e['target_offset']==36 for e in section['edges'])
        assert any(v['source_value']==0x1024 for v in section['address_values'])
        assert not [r for r in section['app_slot_refs']
            if r['base_register']=='A0']
    finally:a.close()


def test_declared_callback_table_is_independent_without_rendered_pointer_labels(tmp_path):
    summary=dict(function_summary_id='callbacks',hunk=0,callable_kind='callback_table',
        table_offset=18,entry_count=1,inputs=[],results=[],note='Original callback entry.',
        effects=dict(schema_version=1,registers=dict(state='unknown'),
            memory=dict(state='unknown'),escapes=dict(state='unknown')))
    a,_=cursor_artifact(tmp_path,'''movea.l $1800.l,a0
 bsr.w callee
 rts
callee:
 move.w $BC6(a0),d0
 rts
callback_table:
 dc.l $100C''',metadata_extra={'absolute_storage_slots':[slot()], 'function_summaries':[summary]})
    try:
        assert not [r for r in a.analysis_payload()[0]['sections'][0]['app_slot_refs']
            if r['base_register']=='A0']
    finally:a.close()


@pytest.mark.parametrize('independent', [False, True])
def test_type_annotation_is_not_a_new_control_flow_entry(tmp_path, independent):
    # MOVE.W immediate(4) + LEA d16(An)(4): loop header at source offset8.
    # A pointee annotation at that instruction constrains A0; it neither
    # invents an inbound edge nor makes the already initialized D7 unknown.
    metadata = {'entry_register_seeds': [dict(hunk=0, entry_offset=8,
        register='A0', kind='struct_ptr', struct_name='Task')]}
    if independent:
        metadata['seeded_code_entrypoints'] = [dict(hunk=0, addr=8)]
    a, _ = cursor_artifact(tmp_path, '''move.w #19,d7
 lea.l $BC6(a6),a4
head:
 move.w (a4)+,d0
 dbf d7,head
 bsr.w helper
 rts
helper:
 nop''', metadata_extra=metadata)
    try:
        ranges = [r for r in a.analysis_payload()[0]['sections'][0]['app_slot_refs']
                  if r.get('loop_iteration_count')]
        assert bool(ranges) == (not independent)
        if ranges:
            assert ranges[0]['loop_iteration_count'] == 20
            assert ranges[0]['loop_iteration_stride'] == 2
    finally:
        a.close()
