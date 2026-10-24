"""Chip mask constructors: only typed LONG LEA plus runtime LONG table fields."""
import hashlib
import subprocess
import pytest
from tests.test_bootstrap_layouts import metadata,build
from tests.test_memory_layouts import region
from tests.test_CPU_allocation_boot import run_loader
from amiga_reversing.tools.direct_payload_adapter import VASM,DirectPayloadContract
from amiga_reversing.disasm.c_backend import assemble_platform_source_text_with_c_backend
from amiga_reversing.tools.runtime_allocation import capsule,DMA_ADDRESS_SCOPE


def mask(tmp_path,code='lea.l $4000.l,a1',*,named=True):
    s=tmp_path/'mask.s';b=tmp_path/'mask.bin'
    s.write_text(' nop\n cmpa.l a2,a1\n bra.s entry\n rts\nentry:\n '+code+'\n rts\n dc.l $4008\n')
    subprocess.run([str(VASM),'-quiet','-Fbin','-m68000','-no-opt','-o',str(b),str(s)],check=True,capture_output=True)
    data=b.read_bytes();table=data.index(bytes.fromhex('00004008'));data+=bytes(512-len(data))
    m=metadata();m['memory_regions'][0]['size']=512
    m['memory_regions'].append(region('masks',0x4000,256,kind='storage'))
    m['memory_layouts'][0]['placements'].append(dict(region_id='masks',runtime_address=0x6000))
    m['bootstrap_contracts'][0].update(input_sha256=hashlib.sha256(data).hexdigest(),file_size=512,copied_source_end=512)
    m['execution_views'][0]['source_end']=512
    if named:
        m['target_equates']=[dict(name='MASKS',value=0x4000,extent_bytes=256,group='masks',address_domain='runtime')]
        m['manual_representations']=[dict(hunk=0,addr=8,end=table-2,element_kind='immediate' if code.startswith('movea') else 'absolute_address',operand_index=0,style='symbol',symbol='MASKS',value=0x4000,width_bytes=2 if '.w,' in code else 4)]
    m['seeded_entities']=[dict(addr=table,end=table+4,hunk=0,unit='long',struct_name='Frame',field_name='mask',field_type='long',value_kind='target_pointer',pointer_address_domain='runtime_only',pointer_symbol_group='masks')]
    return build(tmp_path,m,data)


@pytest.mark.parametrize('fault',[None,'before_owner','after_owner'])
def test_typed_LEA_and_table_patch_together_and_unwind_owned_leases(tmp_path,fault):
    a=mask(tmp_path)
    try:
        p=a.runtime_allocation_plan('masks','diagnostic')
        assert p['status']=='bounded_allocation_candidate' and p['scope']==DMA_ADDRESS_SCOPE,p
        assert [(f['source_offset'],f['encoding'],f['region_offset']) for f in p['fixups']]==[(10,'absolute_long_operand',0),(16,'absolute_long_data',8)]
        staged,_=assemble_platform_source_text_with_c_backend('amiga-raw',a.inline_source_text_with_profile()[0])
    finally:a.close()
    path=tmp_path/'payload.bin';path.write_bytes(staged)
    c=DirectPayloadContract('masks','fixture',hashlib.sha256(staged).hexdigest(),0x20000,0x20000,{},0x7fff8,0x48414e44,runtime_allocation=capsule(p,fault=fault))
    run_loader(tmp_path,c,path,fault=fault)


@pytest.mark.parametrize('code,reason',[('move.l $4000.l,d0','non_data_pointer_reference_unsupported'),('lea.l $4000.w,a1','DMA_address_operand_requires_LONG'),('movea.l #$4000,a1','DMA_immediate_pointer_reference_unsupported')])
def test_DMA_scope_does_not_admit_reads_WORD_fields_or_immediates(tmp_path,code,reason):
    a=mask(tmp_path,code)
    try:
        p=a.runtime_allocation_plan('masks','diagnostic');assert p['status']=='refused' and p['reason']==reason,p
    finally:a.close()


def test_numeric_constructor_is_not_promoted_by_range_coincidence(tmp_path):
    a=mask(tmp_path,named=False)
    try:
        p=a.runtime_allocation_plan('masks','diagnostic');assert p['status']=='refused' and p['reason']=='numeric_or_unbound_absolute_operand',p
    finally:a.close()
