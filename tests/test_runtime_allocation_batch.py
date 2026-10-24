"""Atomic canonical returned bases, never intermediate mixed-layout admission."""
import hashlib
import json
import subprocess
import pytest
from tests.test_bootstrap_layouts import metadata,build
from tests.test_memory_layouts import region,layout
from amiga_reversing.tools.direct_payload_adapter import VASM


def owners(tmp_path,*,numeric=False,word=False,a_size=32,b_stage=0x7000):
    source=tmp_path/'owners.s';binary=tmp_path/'owners.bin'
    source.write_text(' nop\n cmpa.l a2,a1\n bra.s entry\n rts\nentry:\n'+
        (' lea.l $4000.w,a0\n' if word else ' lea.l $4000.l,a0\n')+
        ' lea.l $5000.l,a1\n move.l $4008.l,d0\n rts\n')
    subprocess.run([str(VASM),'-quiet','-Fbin','-m68000','-no-opt','-o',str(binary),str(source)],check=True,capture_output=True)
    data=binary.read_bytes();data+=bytes(512-len(data));m=metadata()
    m['memory_regions'][0]['size']=512
    m['memory_regions'] += [region('owner_a',0x4000,a_size,kind='storage')|dict(dma_access='none'),
        region('owner_b',0x5000,32,kind='storage')|dict(dma_access='none'),
        region('child_a',0x4008,8,parent='owner_a')|dict(dma_access='none')]
    m['memory_layouts'][0]['placements'] += [dict(region_id='owner_a',runtime_address=0x6000),dict(region_id='owner_b',runtime_address=b_stage)]
    m['bootstrap_contracts'][0].update(input_sha256=hashlib.sha256(data).hexdigest(),file_size=512,copied_source_end=512)
    m['execution_views'][0]['source_end']=512
    m['target_equates']=[dict(name=name,value=value,extent_bytes=size,group='storage',address_domain='runtime') for name,value,size in [('OWNER_A',0x4000,a_size),('OWNER_B',0x5000,32),('CHILD_A',0x4008,8)]]
    first=4 if word else 6
    m['manual_representations']=[dict(hunk=0,addr=off,end=off+size,element_kind='absolute_address',operand_index=0,style='symbol',symbol=name,value=value,width_bytes=width)
        for off,size,name,value,width in [(8,first,'OWNER_A',0x4000,2 if word else 4),(8+first,6,'OWNER_B',0x5000,4),(14+first,6,'CHILD_A',0x4008,4)]]
    if numeric:m['manual_representations']=m['manual_representations'][1:];m['target_equates']=m['target_equates'][1:]
    return build(tmp_path,m,data)


def actual(a=0x7000,b=0x6000):return layout([('owner_a',a),('owner_b',b)])


def test_swap_is_admitted_atomically_with_children_and_original_field_identity(tmp_path):
    a=owners(tmp_path)
    try:
        assert a.runtime_allocation_plan('owner_a','diagnostic',0x7000)['status']=='refused'
        result=a.runtime_allocation_batch_plan('diagnostic',actual())
        assert result['status']=='actual_placements_valid',result
        assert result['owner_count']==2 and result['fixup_count']==3
        final={r['region_id']:r for r in result['layout']['items'][0]['regions']}
        assert [final[k]['runtime_address'] for k in ('owner_a','child_a','owner_b')]==[0x7000,0x7008,0x6000]
        fields={p['region_id']:p['fixups'] for p in result['members']}
        assert [f['staged_value'] for f in fields['owner_a']]==[0x6000,0x6008]
        assert [f['staged_value'] for f in fields['owner_b']]==[0x7000]
        reverse=actual();reverse['placements'].reverse()
        assert a.runtime_allocation_batch_plan('diagnostic',reverse)==result
        assert a.runtime_allocation_plan('owner_a','diagnostic')['staged_address']==0x6000
    finally:a.close()


@pytest.mark.parametrize('a_base,b_base',[(0x7000,0x7010),(0x300,0x6000),(0x20000,0x6000),(0x80000,0x6000),(0,0x6000),(0x7001,0x6000),(0x7004,0x6000)])
def test_overlap_input_image_NULL_and_alignment_fail_closed(tmp_path,a_base,b_base):
    a=owners(tmp_path)
    try:assert a.runtime_allocation_batch_plan('diagnostic',actual(a_base,b_base))['status']=='refused'
    finally:a.close()


@pytest.mark.parametrize('identity',['unknown','child_a','image'])
def test_only_explicit_supported_roots_can_be_allocator_returns(tmp_path,identity):
    a=owners(tmp_path)
    try:assert a.runtime_allocation_batch_plan('diagnostic',layout([(identity,0x9000)]))['status']=='refused'
    finally:a.close()


def test_WORD_reach_is_retained_in_atomic_admission(tmp_path):
    a=owners(tmp_path,word=True)
    try:
        assert a.runtime_allocation_batch_plan('diagnostic',actual(0x7ff8,0x6000))['status']=='actual_placements_valid'
        result=a.runtime_allocation_batch_plan('diagnostic',actual(0x8000,0x6000))
        assert result['status']=='refused'
        assert result['members'][0]['reason']=='absolute_word_encoding_overflow'
    finally:a.close()


def test_numeric_member_does_not_yield_partial_batch_success(tmp_path):
    a=owners(tmp_path,numeric=True)
    try:
        result=a.runtime_allocation_batch_plan('diagnostic',actual())
        assert result['status']=='refused' and 'fixup_count' not in result
        assert result['members'][0]['reason']=='numeric_or_unbound_absolute_operand'
    finally:a.close()


@pytest.mark.parametrize('placement',[1,{'region_id':'owner_a','runtime_address':24576.5}, {'region_id':'owner_a','runtime_address':True}])
def test_native_bindings_parser_rejects_nonintegral_or_nonobject_entries(tmp_path,placement):
    a=owners(tmp_path)
    try:
        raw=layout();raw['placements']=[placement]
        value=json.loads(a._text_from_artifact_call(a._dll.platform_file_facts_v2_listing_artifact_runtime_allocation_batch_json_alloc,'diagnostic',json.dumps(raw)))
        assert value['status']=='refused'
    finally:a.close()


def test_fixed_root_padding_is_not_mistaken_for_free_storage(tmp_path):
    a=owners(tmp_path,a_size=30,b_stage=0x701e)
    try:
        result=a.runtime_allocation_batch_plan('diagnostic',layout([('owner_a',0x7000)]))
        assert result['status']=='refused' and result['reason']=='actual_lease_overlaps_other_root_backing'
    finally:a.close()


@pytest.mark.parametrize('change',[{'chip_bytes':0x80000},{'layout_id':'different'}])
def test_actual_profile_cannot_replace_template_assumptions(tmp_path,change):
    a=owners(tmp_path)
    try:assert a.runtime_allocation_batch_plan('diagnostic',actual()|change)['status']=='refused'
    finally:a.close()
