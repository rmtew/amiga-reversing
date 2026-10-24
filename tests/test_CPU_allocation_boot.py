"""CPU allocation loader: exact resources and staged-byte guards, no gameplay."""
from dataclasses import replace
from pathlib import Path
import hashlib
import re

import machine68k
import pytest

from tests.test_address_frame_layout import model
from tests.test_bootstrap_layouts import build
from amiga_reversing.disasm.c_backend import assemble_platform_source_text_with_c_backend
from amiga_reversing.tools.runtime_allocation import capsule,validate_payload,consume_return
from amiga_reversing.tools.direct_payload_adapter import DirectPayloadContract,build_boot_adf,reservation_plan


def contract_fixture(tmp_path,prior=0,fault=None):
    m,data=model();a=build(tmp_path,m,data)
    try:
        p=a.runtime_allocation_plan('cpu','diagnostic')
        staged,_=assemble_platform_source_text_with_c_backend('amiga-raw',a.inline_source_text_with_profile()[0])
    finally:a.close()
    path=tmp_path/'payload.bin';path.write_bytes(staged)
    c=DirectPayloadContract('CPU-fixture','fixture',hashlib.sha256(staged).hexdigest(),0x20000,0x20000,{},0x7fff8,0x48414e44,
        reservations=((0x6000,0x80),),runtime_allocation=capsule(p,prior_allocation_bytes=prior,fault=fault))
    return c,path,p


@pytest.mark.parametrize('prior',[0,4096])
@pytest.mark.parametrize('fault',[None,'before_owner','after_owner'])
def test_CPU_boot_positive_and_failure_unwind_exactly_owned_resources(tmp_path,prior,fault):
    c,payload,plan=contract_fixture(tmp_path,prior,fault)
    run_loader(tmp_path,c,payload,fault=fault)


def run_loader(tmp_path,c,payload,*,fault=None,fail_static=None):
    report=build_boot_adf(c,payload,tmp_path/'fixture.adf');size=report['allocation_boot_code_size']
    code=(tmp_path/'fixture.adf').read_bytes()[12:12+size]
    spans=reservation_plan(c,payload.stat().st_size)
    assert size<=1012
    listing=(tmp_path/'fixture.bootcode.allocation.lst').read_text()
    unowned=int(re.search(r'^([0-9A-Fa-f]{8}) reservation_unowned$',listing,re.M)[1],16)+0x1000
    closed=0x1000+report['allocation_boot_symbols']['allocation_closed']
    m=machine68k.Machine(machine68k.CPUType.M68000,1024);m.mem.w_block(0x1000,code)
    execbase=0xf0000
    allocabs,allocmem,freemem,doio=[execbase-d for d in (204,198,210,456)]
    for pc in (allocabs,allocmem,freemem,doio):m.mem.w_block(pc,b'\x4e\x75')
    m.cpu.w_reg(machine68k.Register.A6,execbase);m.cpu.w_reg(machine68k.Register.A1,0x18000)
    m.cpu.w_reg(machine68k.Register.A7,0xf8000);m.cpu.w_sr(0x2700);m.cpu.w_pc(0x1000)
    owned={};acquired=[];freed=[];requests=[];steps=0;abort_seen=False;handoff=False
    prior=c.runtime_allocation.get('prior_allocation_bytes',0);base=0x7080 if prior else 0x6080
    class Done(Exception):pass
    class Memory:
        def read_memory(self,address,count):return m.mem.r_block(address,count)
    def hook(pc):
        nonlocal steps,abort_seen,handoff
        steps+=1;assert steps<3000,'Unbounded CPU loader fixture'
        if pc==unowned:
            assert fail_static==0 and not owned and not acquired and not freed
            assert m.mem.r_block(c.handoff_marker_address,4)==bytes(4)
            raise Done
        if pc==closed:
            assert abort_seen and not owned
            raise Done
        if pc==allocabs:
            address=m.cpu.r_reg(machine68k.Register.A1);n=m.cpu.r_reg(machine68k.Register.D0)
            assert (address,n)==spans[len(acquired)]
            if len(acquired)==fail_static:m.cpu.w_reg(machine68k.Register.D0,0)
            else:
                assert address not in owned;owned[address]=n;acquired.append((address,n));m.cpu.w_reg(machine68k.Register.D0,address)
        elif pc==allocmem:
            n=m.cpu.r_reg(machine68k.Register.D0);requests.append(n)
            address=0x6080 if prior and len(requests)==1 else base
            assert address not in owned
            owned[address]=n;m.cpu.w_reg(machine68k.Register.D0,address)
        elif pc==freemem:
            address=m.cpu.r_reg(machine68k.Register.A1);n=m.cpu.r_reg(machine68k.Register.D0)
            assert owned.pop(address)==n,'FreeMem must match one exact owned request'
            freed.append((address,n))
        elif pc==doio:
            m.mem.w_block(c.load_address,payload.read_bytes());m.cpu.w_reg(machine68k.Register.D0,0)
        marker=m.mem.r_block(c.handoff_marker_address,4)
        if marker==b'HAND' and not handoff:
            handoff=True;assert fault is None and fail_static is None
            expected,lease=consume_return(Memory(),c,payload.read_bytes())
            assert lease['base']==base and lease.get('prior_size',0)==prior
            assert m.mem.r_block(c.load_address,len(expected))==expected
            # Stop before game GO, exercising the ordinary ABRT/FREE protocol.
            m.mem.w_block(c.handoff_marker_address,b'ABRT')
        elif marker==b'ABOR' and not abort_seen:
            abort_seen=True;m.mem.w_block(c.handoff_marker_address,b'FREE')
    m.cpu.set_instr_hook_callback(hook)
    try:m.cpu.execute(500000)
    except Done:pass
    else:raise AssertionError('Loader did not reach its exact bounded outcome')
    if fail_static is None:
        assert acquired==list(spans)
        if fault=='before_owner':assert requests==[]
        else:assert requests==([4096] if prior else [])+[plan_size(c)]
        assert handoff==(fault is None)
    else:assert acquired==list(spans[:fail_static]) and not requests
    assert len(freed)==len(set(a for a,n in freed))


def plan_size(c):return c.runtime_allocation['plan']['size']


@pytest.mark.parametrize('index',range(5))
def test_CPU_partial_static_prefix_failure_never_frees_unowned_rows(tmp_path,index):
    c,payload,_=contract_fixture(tmp_path,4096)
    assert len(reservation_plan(c,payload.stat().st_size))==5
    run_loader(tmp_path,c,payload,fail_static=index)


@pytest.mark.parametrize('field',['opcode','frame_opcode','frame_displacement'])
def test_CPU_staged_instruction_guards_refuse_changes(tmp_path,field):
    c,path,p=contract_fixture(tmp_path)
    data=bytearray(path.read_bytes())
    off=p['fixups'][0]['instruction_source_offset'] if field=='opcode' else p['address_frame_guards'][0]['instruction_source_offset' if field=='frame_opcode' else 'displacement_source_offset']
    data[off]^=1
    with pytest.raises(ValueError,match='stale'):validate_payload(c.runtime_allocation,bytes(data),c.load_address,c.handoff_marker_address)
