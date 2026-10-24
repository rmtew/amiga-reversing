"""Execute the DOS application's acquisition/unwind, not a game or Exec model."""
import re
import subprocess
from pathlib import Path
import machine68k
import pytest
from amiga_reversing.tools.direct_payload_adapter import VASM,NDK_INCLUDE
from amiga_reversing.tools.pandora_OS_application import own_code

ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('encoding,width,expected',[
    ('absolute_long_data',4,0x9f040),('dma_address_high_word',2,9),
    ('dma_address_low_word',2,0xf040)])
def test_native_field_value_keeps_full_pointer_and_physical_encoding_separate(encoding,width,expected):
    from amiga_reversing.tools.pandora_OS_application import runtime_field_value
    assert runtime_field_value(dict(encoding=encoding,width=width,region_offset=0x40),0x9f000)==expected


@pytest.mark.parametrize('field,base',[
    (dict(encoding='dma_address_low_word',width=4,region_offset=0),0),
    (dict(encoding='unknown',width=2,region_offset=0),0),
    (dict(encoding='absolute_long_data',width=4,region_offset=1),0xffffffff)])
def test_native_field_value_refuses_bad_width_kind_or_overflow(field,base):
    from amiga_reversing.tools.pandora_OS_application import runtime_field_value
    with pytest.raises(ValueError):runtime_field_value(field,base)

@pytest.fixture
def executable(tmp_path):
    (tmp_path/'pandora_OS_plan.i').write_text('OWNER_COUNT EQU 6\nFIXED_COUNT EQU 4\nINPUT_ADDRESS EQU $20000\nPAYLOAD_SIZE EQU 16\nPAYLOAD_CRC32 EQU 0\n')
    (tmp_path/'pandora_OS_tables.i').write_text('fixed_table: dc.l $20000,$5C000,$7D000,$2EB8,$80000,$55370,$E0000,$D000\nowner_sizes: dc.l 8,128,2304,1000,48056,10040\ncrc_table: dcb.l 256,0\n')
    target=tmp_path/'app';listing=tmp_path/'app.list'
    p=subprocess.run([str(VASM),'-Fhunkexe','-m68000','-no-opt','-I'+str(NDK_INCLUDE),'-I'+str(tmp_path),'-L',str(listing),'-o',str(target),str(ROOT/'tools/amiga_pandora_OS.s')],capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    labels={m[2]:int(m[1],16) for m in re.finditer(r'^([0-9A-F]{8}) (\w+)$',listing.read_text(),re.M)}
    assert labels['state_leases_end']-labels['state_leases']==80
    code=own_code(target.read_bytes())
    assert labels['state_leases_end']<=len(code)
    return code,labels

@pytest.mark.parametrize('fail_index',range(11))
def test_every_allocation_prefix_or_library_failure_frees_only_exact_owned_pairs(executable,fail_index):
    code,labels=executable;m=machine68k.Machine(machine68k.CPUType.M68000,1024)
    base=0x1000;execbase=0xf0000;stop=0xfe000
    m.mem.w_block(base,code);m.mem.w32(4,execbase)
    for n in (198,204,210,552):m.mem.w_block(execbase-n,b'\x4e\x75')
    m.cpu.w_reg(machine68k.Register.A7,0xf8000);m.mem.w32(0xf8000,stop)
    m.cpu.w_sr(0x2000);m.cpu.w_pc(base)
    acquired=[];freed=[];owned={};calls=0;dynamic=0;steps=0
    class Done(Exception):pass
    def hook(pc):
        nonlocal calls,dynamic,steps
        steps+=1;assert steps<1500
        if pc==stop:raise Done
        if pc in (execbase-198,execbase-204):
            n=m.cpu.r_reg(machine68k.Register.D0)
            if pc==execbase-204:address=m.cpu.r_reg(machine68k.Register.A1)
            else:
                address=(0x2000,0x10170,0x101f0,0x10af0,0x10ed8,0x1ca90)[dynamic]
                dynamic+=1
            if calls==fail_index:m.cpu.w_reg(machine68k.Register.D0,0)
            else:
                assert address not in owned;owned[address]=n;acquired.append((address,n));m.cpu.w_reg(machine68k.Register.D0,address)
            calls+=1
        elif pc==execbase-552:m.cpu.w_reg(machine68k.Register.D0,0)
        elif pc==execbase-210:
            address=m.cpu.r_reg(machine68k.Register.A1);n=m.cpu.r_reg(machine68k.Register.D0)
            assert owned.pop(address)==n
            freed.append((address,n))
    m.cpu.set_instr_hook_callback(hook)
    try:m.cpu.execute(200000)
    except Done:pass
    else:raise AssertionError('Owned application did not return within bounds')
    assert m.cpu.r_reg(machine68k.Register.D0)==20
    assert not owned and freed==list(reversed(acquired))
    assert len(acquired)==min(fail_index,10)
    assert m.mem.r32(base+labels['state_count'])==0

@pytest.mark.parametrize('failure',['open','read_error','short_read','extra_byte','CRC_mismatch'])
def test_file_admission_failures_close_file_once_and_unwind_all_ten(executable,failure):
    code,labels=executable;m=machine68k.Machine(machine68k.CPUType.M68000,1024)
    base=0x1000;execbase=0xf0000;dosbase=0xf1000;stop=0xfe000
    m.mem.w_block(base,code);m.mem.w32(4,execbase)
    for address in [execbase-n for n in (198,204,210,552,414)]+[dosbase-n for n in (30,36,42,48,60)]:
        m.mem.w_block(address,b'\x4e\x75')
    m.cpu.w_reg(machine68k.Register.A7,0xf8000);m.mem.w32(0xf8000,stop)
    m.cpu.w_sr(0x2000);m.cpu.w_pc(base)
    owned={};acquired=[];freed=[];dynamic=0;read_count=0;closes=0;steps=0
    class Done(Exception):pass
    def hook(pc):
        nonlocal dynamic,read_count,closes,steps
        steps+=1;assert steps<3000
        if pc==stop:raise Done
        if pc in (execbase-198,execbase-204):
            size=m.cpu.r_reg(machine68k.Register.D0)
            if pc==execbase-204:address=m.cpu.r_reg(machine68k.Register.A1)
            else:
                address=(0x2000,0x10170,0x101f0,0x10af0,0x10ed8,0x1ca90)[dynamic];dynamic+=1
            owned[address]=size;acquired.append((address,size));m.cpu.w_reg(machine68k.Register.D0,address)
        elif pc==execbase-552:m.cpu.w_reg(machine68k.Register.D0,dosbase)
        elif pc==dosbase-30:m.cpu.w_reg(machine68k.Register.D0,0 if failure=='open' else 0x55)
        elif pc==dosbase-42:
            read_count+=1
            assert m.cpu.r_reg(machine68k.Register.D1)==0x55
            if read_count==1:
                size=-1 if failure=='read_error' else 15 if failure=='short_read' else 16
                if size>0:m.mem.w_block(0x20000,bytes(size))
            else:size=1 if failure=='extra_byte' else 0
            m.cpu.w_reg(machine68k.Register.D0,size&0xffffffff)
        elif pc==dosbase-36:
            closes+=1;assert m.cpu.r_reg(machine68k.Register.D1)==0x55
        elif pc==dosbase-60:m.cpu.w_reg(machine68k.Register.D0,0x66)
        elif pc==dosbase-48:m.cpu.w_reg(machine68k.Register.D0,m.cpu.r_reg(machine68k.Register.D3))
        elif pc==execbase-210:
            address=m.cpu.r_reg(machine68k.Register.A1);size=m.cpu.r_reg(machine68k.Register.D0)
            assert owned.pop(address)==size;freed.append((address,size))
    m.cpu.set_instr_hook_callback(hook)
    try:m.cpu.execute(500000)
    except Done:pass
    else:raise AssertionError('File failure did not return within bounds')
    assert m.cpu.r_reg(machine68k.Register.D0)==20
    assert not owned and freed==list(reversed(acquired)) and len(acquired)==10
    assert closes==(failure!='open')
    assert m.mem.r32(base+labels['state_phase'])==1
    assert m.mem.r32(base+labels['state_file'])==0
