"""Encoder-derived CPU field identities, signed-W bounds and child aliases."""
import hashlib
import subprocess
from pathlib import Path
import pytest
from tests.test_bootstrap_layouts import metadata,build
from tests.test_memory_layouts import region
from amiga_reversing.tools.direct_payload_adapter import VASM


DEFAULT_CODE='lea.l $4000.w,a0\n move.l #$12345678,$4004.l\n move.l $4008.l,$400c.w'

def fixture(tmp_path,code=DEFAULT_CODE,*,named=True,stage=0x5000,child_dma='none'):
    source=tmp_path/'cpu.s';binary=tmp_path/'cpu.bin'
    source.write_text(' nop\n cmpa.l a2,a1\n bra.s entry\n rts\nentry:\n '+code+'\n rts\n')
    result=subprocess.run([str(VASM),'-quiet','-Fbin','-m68000','-no-opt','-o',str(binary),str(source)],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    data=binary.read_bytes();data+=bytes(512-len(data))
    m=metadata();m['memory_regions'][0]['size']=512
    m['memory_regions'] += [(region('cpu',0x4000,32)|dict(dma_access='none')),(region('child',0x4008,8,parent='cpu')|dict(dma_access=child_dma))]
    m['memory_layouts'][0]['placements'].append(dict(region_id='cpu',runtime_address=stage))
    m['bootstrap_contracts'][0].update(input_sha256=hashlib.sha256(data).hexdigest(),file_size=512,copied_source_end=512)
    m['execution_views'][0]['source_end']=512
    if named:
        m['target_equates']=[dict(name=f'CPU_{offset:02X}',value=0x4000+offset,extent_bytes=4,group='cpu',address_domain='runtime') for offset in (0,4,8,12)]
        if code==DEFAULT_CODE:
            m['manual_representations']=[dict(hunk=0,addr=start,end=end,element_kind='absolute_address',operand_index=operand,style='symbol',symbol=f'CPU_{offset:02X}',value=0x4000+offset,width_bytes=width)
                for start,end,operand,offset,width in [(8,12,0,0,2),(12,22,1,4,4),(22,30,0,8,4),(22,30,1,12,2)]]
    return build(tmp_path,m,data)


def test_exact_extension_coordinates_skip_immediate_and_preserve_both_EAs(tmp_path):
    a=fixture(tmp_path)
    try:
        plan=a.runtime_allocation_plan('cpu','diagnostic')
        assert plan['status']=='bounded_allocation_candidate',plan
        fixes=plan['fixups']
        assert [(f['source_offset'],f['width'],f['instruction_source_offset'],f['operand_index'],f['staged_value']) for f in fixes]==[
            (10,2,8,0,0x5000),(18,4,12,1,0x5004),(24,4,22,0,0x5008),(28,2,22,1,0x500c)]
        assert [f['symbol'] for f in fixes]==['CPU_00','CPU_04','CPU_08','CPU_0C']
        assert all(f['opcode'] for f in fixes)
        assert plan['maximum_actual_base']==0x7fff-12
        actual=a.runtime_allocation_plan('cpu','diagnostic',0x6000)
        assert actual['status']=='actual_placement_valid',actual
        rows={r['region_id']:r for r in actual['layout']['items'][0]['regions']}
        assert rows['child']['runtime_address']==0x6008
        assert a.runtime_allocation_plan('cpu','diagnostic')==plan
    finally:a.close()


@pytest.mark.parametrize('actual,status',[(0x7ff2,'actual_placement_valid'),(0x7ff4,'refused')])
def test_absolute_W_limit_applies_to_each_base_plus_offset(tmp_path,actual,status):
    a=fixture(tmp_path)
    try:
        result=a.runtime_allocation_plan('cpu','diagnostic',actual)
        assert result['status']==status,result
        if status=='refused':assert result['reason']=='absolute_word_encoding_overflow'
    finally:a.close()


def test_DMA_child_cannot_enter_CPU_only_contract(tmp_path):
    a=fixture(tmp_path,child_dma='chip')
    try:assert a.runtime_allocation_plan('cpu','diagnostic')==dict(status='refused',reason='allocation_subregion_materialization_unsupported')
    finally:a.close()


def test_partially_owned_absolute_read_refuses(tmp_path):
    a=fixture(tmp_path,code='move.w $3fff.l,d0')
    try:
        result=a.runtime_allocation_plan('cpu','diagnostic')
        assert result==dict(status='refused',reason='partial_absolute_operand_access',refusal_site=dict(source_section_index=0,source_offset=8,operand_index=0))
    finally:a.close()


def test_numeric_absolute_site_is_not_admitted_as_symbolic(tmp_path):
    a=fixture(tmp_path,named=False)
    try:
        result=a.runtime_allocation_plan('cpu','diagnostic')
        assert result==dict(status='refused',reason='numeric_or_unbound_absolute_operand',refusal_site=dict(source_section_index=0,source_offset=8,operand_index=0))
    finally:a.close()


@pytest.mark.parametrize('stage,expected',[(0x5000,'bounded_allocation_candidate'),
    (0x6080,'refused')])
def test_priest_cell_offset_exposes_word_reach_instead_of_truncating(tmp_path,stage,expected):
    # Pandora's fixed cell is app+$2AC4. The existing $6080 template would
    # produce $8B44, which absolute-W sign extension cannot address as Chip RAM.
    data=bytes.fromhex('4e71b3ca60024e7521fc0001e92864c04e75')
    data+=bytes(512-len(data))
    m=metadata();m['memory_regions'][0]['size']=512
    m['memory_regions'] += [region('cpu',0x39fc,0xbbb3)|dict(dma_access='none'),
        region('grid',0x4000,0xb568,parent='cpu')|dict(dma_access='none')]
    m['memory_layouts'][0]['placements'].append(dict(region_id='cpu',runtime_address=stage))
    m['bootstrap_contracts'][0].update(input_sha256=hashlib.sha256(data).hexdigest(),
        file_size=512,copied_source_end=512)
    m['execution_views'][0]['source_end']=512
    m['target_equates']=[dict(name='PASSAGE_CELL',value=0x64c0,extent_bytes=4,
        group='cpu',address_domain='runtime')]
    m['manual_representations']=[dict(hunk=0,addr=8,end=16,
        element_kind='absolute_address',operand_index=1,style='symbol',
        symbol='PASSAGE_CELL',value=0x64c0,width_bytes=2)]
    a=build(tmp_path,m,data)
    try:
        result=a.runtime_allocation_plan('cpu','diagnostic')
        assert result['status']==expected,result
        if expected=='refused':
            assert result['reason']=='staged_absolute_word_encoding_overflow'
            assert result['refusal_site']==dict(source_section_index=0,source_offset=8,operand_index=1)
        else:
            assert result['maximum_actual_base']==0x553b
            assert result['fixups'][0]['staged_value']==0x7ac4
            assert result['fixups'][0]['source_offset']==14
    finally:a.close()
