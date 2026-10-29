"""A declared table owns bytes; it must not hide independently observed reads."""
import pytest
from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.manual_actions import append_manual_actions, ManualActionKind as Kind
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata


def table_artifact(tmp_path, owner, prefix='', index_width='w'):
    asm=''' SECTION code,code
 ORG $1000
 bsr.w first
 bsr.w second
 lea.l directory(pc),a0
 movea.l $0(a0,d0.w),a1
 jsr (a1)
 lea.l directory(pc),a2
 movea.l $0(a2,d1.w),a3
 jmp (a3)
 first:
 rts
 second:
 moveq #1,d0
 rts
 directory:
 dc.l first,second,first
'''
    if prefix:
        asm=asm.replace(' lea.l directory(pc),a0',prefix+'\n lea.l directory(pc),a0')
        asm=asm.replace(' movea.l $0(a0,d0.w),a1',
                        f'read:\n movea.l $0(a0,d0.{index_width}),a1')
        asm=asm.replace(' jsr (a1)',' jsr (a1)\ndone:')
    if owner=='word_read':
        asm=asm.replace('movea.l $0(a0,d0.w),a1','move.w $0(a0,d0.w),d2').replace(
            'movea.l $0(a2,d1.w),a3','move.w $0(a2,d1.w),d2')
    if owner=='unknown_base':
        asm=asm.replace('lea.l directory(pc),a0','movea.l a4,a0').replace(
            'lea.l directory(pc),a2','movea.l a4,a2')
    original,_=c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',asm)
    table=len(original)-12
    binary=tmp_path/'table.bin';binary.write_bytes(original)
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,load_address=0x1000,entrypoint=0x1000,
        code_start_offset=0,display_path=str(binary),analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    actions=[]
    if owner!='inferred':
        unit='long'
        role='lookup_table' if owner=='scalar' else 'pointer_table'
        actions.append((Kind.CREATE_MANUAL_SEED,{'seed':dict(seed_id='owner',kind='data',mode='required',
            hunk=0,addr=table,end=table+12,name='named_callbacks',unit=unit,data_role=role)}))
    if owner=='ambiguous_extent':
        actions.append((Kind.CREATE_MANUAL_SEED,{'seed':dict(seed_id='other-owner',kind='data',mode='required',
            hunk=0,addr=table,end=table+8,name='other_callbacks',unit='long',data_role='pointer_table')}))
    append_manual_actions(tmp_path,binary_source=source,actions=actions)
    with effective_metadata_file(tmp_path) as metadata:
        artifact=c_backend.build_listing_artifact_profile_from_binary_source(source,metadata_path=metadata)[2]
    return artifact,original,table


@pytest.mark.c_backend
@pytest.mark.parametrize('owner',['inferred','pointer'])
def test_independent_indexed_reads_survive_table_ownership(tmp_path,owner):
    artifact,original,table=table_artifact(tmp_path,owner)
    try:
        analysis=artifact.analysis_payload()[0];section=analysis['sections'][0]
        consumers=[r for r in section['table_consumers'] if r['table_start_offset']==table]
        assert len(consumers)==2,consumers
        assert len({r['consumer_offset']for r in consumers})==2
        assert {r['index_register']for r in consumers}=={0,1}
        assert all(r['entry_count']==3 and r['access_width']==4 for r in consumers)
        assert all(r['index_mask_domain'] is None and r['index_compare_domain'] is None
                   and r['index_loop_domain'] is None for r in consumers)
        expressions=[r for r in section['address_expressions']
                     if r['kind']=='indexed_table' and r['base_offset']==table]
        assert {r['consumer_offset']for r in expressions}=={r['consumer_offset']for r in consumers}
        source=artifact.inline_source_text_with_profile()[0]
        if owner=='pointer': assert 'named_callbacks:' in source
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',source)[0]==original
    finally: artifact.close()


@pytest.mark.c_backend
@pytest.mark.parametrize('owner',['scalar','word_read','unknown_base'])
def test_pointer_consumer_projection_does_not_retype_other_owners(tmp_path,owner):
    artifact,original,table=table_artifact(tmp_path,owner)
    try:
        section=artifact.analysis_payload()[0]['sections'][0]
        assert not [r for r in section['table_consumers'] if r['table_start_offset']==table
                    and r['source_pattern']=='indexed_local_pointer_read']
        source=artifact.inline_source_text_with_profile()[0]
        assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',source)[0]==original
    finally:artifact.close()


@pytest.mark.c_backend
def test_conflicting_table_extents_do_not_create_consumer_proof(tmp_path):
    artifact,_,table=table_artifact(tmp_path,'ambiguous_extent')
    try:
        section=artifact.analysis_payload()[0]['sections'][0]
        assert not [r for r in section['table_consumers'] if r['table_start_offset']==table]
    finally:artifact.close()


@pytest.mark.c_backend
@pytest.mark.parametrize('noise',[
    '', 'moveq.l #100,d1', 'sub.w d0,d2',
])
def test_local_mask_domain_survives_only_unrelated_writes(tmp_path,noise):
    prefix=' andi.w #3,d0\n '+noise+'\n add.w d0,d0\n add.w d0,d0'
    artifact,original,_=table_artifact(tmp_path,'pointer',prefix)
    try:
        rows=artifact.analysis_payload()[0]['sections'][0]['table_consumers']
        row=next(r for r in rows if r['index_register']==0)
        assert row['index_mask_domain']==dict(min=0,max=3)
        assert c_backend.assemble_platform_source_text_with_c_backend(
            'amiga-raw',artifact.inline_source_text_with_profile()[0])[0]==original
    finally:artifact.close()


@pytest.mark.c_backend
@pytest.mark.parametrize('noise',[
    'moveq.l #100,d0', 'move.b #100,d0', 'addi.w #100,d0',
    'exg d0,d1', 'movem.l (a7)+,d0-d1', 'bsr.w first',
])
def test_local_mask_domain_rejects_clobbers_and_calls(tmp_path,noise):
    prefix=' andi.w #3,d0\n '+noise+'\n add.w d0,d0\n add.w d0,d0'
    artifact,_,_=table_artifact(tmp_path,'pointer',prefix)
    try:
        rows=artifact.analysis_payload()[0]['sections'][0]['table_consumers']
        assert next(r for r in rows if r['index_register']==0)['index_mask_domain']is None
    finally:artifact.close()


@pytest.mark.c_backend
@pytest.mark.parametrize('target',['scale','read'])
def test_local_mask_domain_rejects_alternative_entry_after_bound(tmp_path,target):
    prefix=f' tst.w d1\n beq.s {target}\n andi.w #3,d0\nscale:\n add.w d0,d0\n add.w d0,d0'
    artifact,_,_=table_artifact(tmp_path,'pointer',prefix)
    try:
        rows=artifact.analysis_payload()[0]['sections'][0]['table_consumers']
        assert next(r for r in rows if r['index_register']==0)['index_mask_domain']is None
    finally:artifact.close()


@pytest.mark.c_backend
@pytest.mark.parametrize('prefix,width',[
    (' move.l (a7),d0\n andi.w #3,d0\n add.w d0,d0\n add.w d0,d0','l'),
    (' andi.w #32767,d0\n add.w d0,d0\n add.w d0,d0','w'),
])
def test_local_word_domain_cannot_bound_long_upper_bits_or_wrapped_word_index(tmp_path,prefix,width):
    artifact,_,_=table_artifact(tmp_path,'pointer',prefix,width)
    try:
        rows=artifact.analysis_payload()[0]['sections'][0]['table_consumers']
        assert next(r for r in rows if r['index_register']==0)['index_mask_domain']is None
    finally:artifact.close()


@pytest.mark.c_backend
@pytest.mark.parametrize('branch',['bhi','bgt'])
def test_local_compare_domain_retains_guarded_fallthrough(tmp_path,branch):
    prefix=f' andi.w #7,d0\n cmp.w #3,d0\n {branch}.s done\n add.w d0,d0\n add.w d0,d0'
    artifact,_,_=table_artifact(tmp_path,'pointer',prefix)
    try:
        rows=artifact.analysis_payload()[0]['sections'][0]['table_consumers']
        row=next(r for r in rows if r['index_register']==0)
        assert row['index_compare_domain']['min']==0 and row['index_compare_domain']['max']==3
    finally:artifact.close()


@pytest.mark.c_backend
@pytest.mark.parametrize('guard,expected',[
    ('cmp.w #3,d0\n bhi.s done',True),
    ('cmp.w #3,d0\n bgt.s done',False),
    ('cmp.w #3,d0\n bgt.s done\n andi.w #7,d0',False),
])
def test_signed_compare_requires_prior_nonnegative_evidence(tmp_path,guard,expected):
    artifact,_,_=table_artifact(tmp_path,'pointer',
        ' '+guard+'\n add.w d0,d0\n add.w d0,d0')
    try:
        rows=artifact.analysis_payload()[0]['sections'][0]['table_consumers']
        domain=next(r for r in rows if r['index_register']==0)['index_compare_domain']
        assert (domain is not None)==expected
    finally:artifact.close()


@pytest.mark.c_backend
def test_descriptor_consumer_is_owned_by_instruction_section(tmp_path):
    import subprocess
    from amiga_reversing.disasm.project_paths import PROJECT_ROOT
    source=tmp_path/'consumer-domain.c'
    source.write_text(r'''#include "m68k_ir.h"
#include "util_arena.h"
#include <assert.h>
#include <string.h>
int main(void) {
  Arena *arena=arena_create(4096);
  M68kSectionAnalysisIR table={0}, code={0};
  M68kTableDescriptorIR descriptor={0};
  assert(arena); table.arena=code.arena=arena;
  table.section_index=3; code.section_index=5;
  descriptor.start_offset=32; descriptor.end_offset=44;
  descriptor.entry_size=4; descriptor.entry_count=3;
  descriptor.table_kind_id=M68K_ANALYSIS_TABLE_KIND_POINTER;
  descriptor.has_consumer=1; descriptor.consumer_section_index=5;
  descriptor.consumer_offset=12; descriptor.has_index_register=1;
  descriptor.index_register_kind=M68K_ANALYSIS_REGISTER_DATA;
  descriptor.index_register=1;
  assert(!m68k_ir_section_analysis_append_table_descriptor(&table,&descriptor));
  assert(table.table_descriptor_count==1 && table.table_consumer_count==0);
  assert(!m68k_ir_section_analysis_append_table_consumer_from_descriptor(&code,3,&descriptor));
  assert(code.table_consumer_count==1);
  assert(code.table_consumers[0].table_section_index==3);
  assert(code.table_consumers[0].consumer_offset==12);
  assert(code.table_consumers[0].index_register==1);
  assert(!m68k_ir_section_analysis_append_table_consumer_from_descriptor(&code,3,&descriptor));
  assert(code.table_consumer_count==1);
  arena_destroy(arena); return 0;
}
''')
    executable=tmp_path/'consumer-domain'
    subprocess.run(['cc','-std=c11','-I'+str(PROJECT_ROOT/'src'),str(source),
        '-L'+str(PROJECT_ROOT/'src/build'),'-lamiga_backend',
        '-Wl,-rpath,'+str(PROJECT_ROOT/'src/build'),'-o',str(executable)],check=True,capture_output=True)
    subprocess.run([str(executable)],check=True,capture_output=True)
