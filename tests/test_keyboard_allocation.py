"""Keyboard-shaped leaf: native field projection, staged guard and exact unwind."""
import copy
import hashlib
import subprocess
import pytest
from tests.test_bootstrap_layouts import metadata,build
from tests.test_memory_layouts import region
from tests.test_CPU_allocation_boot import run_loader
from amiga_reversing.tools.direct_payload_adapter import VASM,DirectPayloadContract
from amiga_reversing.tools.runtime_allocation import capsule
from amiga_reversing.disasm.c_backend import assemble_platform_source_text_with_c_backend


def leaf(tmp_path):
    source=tmp_path/'keyboard.s';binary=tmp_path/'keyboard.bin'
    source.write_text(' nop\n cmpa.l a2,a1\n bra.s entry\n rts\nentry:\n'+
        ' lea.l $4000.l,a0\n lea.l $4000.l,a1\n'*2+' lea.l $4000.l,a0\n lea.l $4040.l,a5\n lea.l $4050.l,a0\n rts\n')
    subprocess.run([str(VASM),'-quiet','-Fbin','-m68000','-no-opt','-o',str(binary),str(source)],check=True,capture_output=True)
    data=binary.read_bytes();data+=bytes(512-len(data));m=metadata()
    m['memory_regions'][0]['size']=512
    m['memory_regions'].append(region('keyboard',0x4000,128,kind='storage')|dict(dma_access='none'))
    m['memory_layouts'][0]['placements'].append(dict(region_id='keyboard',runtime_address=0x6000))
    m['bootstrap_contracts'][0].update(input_sha256=hashlib.sha256(data).hexdigest(),file_size=512,copied_source_end=512)
    m['execution_views'][0]['source_end']=512
    m['target_equates']=[dict(name=name,value=0x4000+offset,extent_bytes=width,group='keyboard',address_domain='runtime') for name,offset,width in [('KEYBOARD_BASE',0,128),('KEYBOARD_INVENTORY_KEY_STATE',64,1),('KEYBOARD_PAUSE_KEY_STATE',80,1)]]
    m['manual_representations']=[dict(hunk=0,addr=8+i*6,end=14+i*6,element_kind='absolute_address',operand_index=0,style='symbol',symbol=name,value=0x4000+offset,width_bytes=4) for i,(name,offset) in enumerate([('KEYBOARD_BASE',0)]*5+[('KEYBOARD_INVENTORY_KEY_STATE',64),('KEYBOARD_PAUSE_KEY_STATE',80)])]
    a=build(tmp_path,m,data)
    try:
        p=a.runtime_allocation_plan('keyboard','diagnostic')
        staged,_=assemble_platform_source_text_with_c_backend('amiga-raw',a.inline_source_text_with_profile()[0])
    finally:a.close()
    assert p['status']=='bounded_allocation_candidate',p
    assert len(p['fixups'])==7
    assert [f['source_offset'] for f in p['fixups']]==[10,16,22,28,34,40,46]
    assert [f['region_offset'] for f in p['fixups']]==[0,0,0,0,0,64,80]
    path=tmp_path/'payload.bin';path.write_bytes(staged)
    return p,path


@pytest.mark.parametrize('fault',[None,'before_owner','after_owner'])
def test_leaf_native_fixups_and_guest_failure_unwind(tmp_path,fault):
    p,path=leaf(tmp_path)
    c=DirectPayloadContract('keyboard','fixture',hashlib.sha256(path.read_bytes()).hexdigest(),0x20000,0x20000,{},0x7fff8,0x48414e44,
        runtime_allocation=capsule(p,fault=fault))
    run_loader(tmp_path,c,path,fault=fault)


@pytest.mark.parametrize('mutation',['frame','numeric','child','data'])
def test_leaf_does_not_waive_frame_or_unresolved_reference_guards(tmp_path,mutation):
    p,_=leaf(tmp_path);p=copy.deepcopy(p)
    if mutation=='frame':p['address_frame_guards']=[]
    elif mutation=='numeric':p['numeric_immediate_candidates_not_fixups']=1
    elif mutation=='child':p['layout']['items'][0]['regions'].append(dict(region_id='alias',parent_region_id='keyboard'))
    elif mutation=='data':p['fixups'][0]['encoding']='absolute_long_data'
    with pytest.raises(ValueError):capsule(p)


@pytest.mark.parametrize('field',['opcode','operand'])
def test_leaf_staged_bytes_are_still_checked_before_runtime_patching(tmp_path,field):
    from amiga_reversing.tools.runtime_allocation import validate_payload
    p,path=leaf(tmp_path);value=capsule(p);data=bytearray(path.read_bytes())
    f=p['fixups'][0];offset=f['instruction_source_offset'] if field=='opcode' else f['source_offset']
    data[offset]^=1
    with pytest.raises(ValueError):validate_payload(value,bytes(data),0x20000,0x7fff8)
