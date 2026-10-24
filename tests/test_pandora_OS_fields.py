"""Own loader field/dispatch semantics; these fixtures are not gameplay evidence."""
import re
import subprocess
from pathlib import Path
import machine68k
import pytest
from amiga_reversing.tools.direct_payload_adapter import VASM,NDK_INCLUDE
from amiga_reversing.tools.pandora_OS_application import own_code
ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def executable(tmp_path):
    (tmp_path/'pandora_OS_plan.i').write_text('HOSTED_GAME EQU 1\nOWNER_COUNT EQU 6\nFIXED_COUNT EQU 4\nFIXUP_COUNT EQU 2\nINPUT_ADDRESS EQU $20000\nPAYLOAD_SIZE EQU 16\nPAYLOAD_CRC32 EQU 0\nEXIT_IMPORT_OFFSET EQU 8\nORIGINAL_WORLD_INITIALIZER EQU $80000\n')
    (tmp_path/'pandora_OS_tables.i').write_text('fixed_table: dc.l $20000,$5C000,$7D000,$2EB8,$80000,$55370,$E0000,$D000\nowner_sizes: dc.l 8,128,2304,1000,48056,10040\nruntime_fields: dc.l 0,$7F0\n dc.w 0,2\n dc.l 2\n dc.l 4,$6000\n dc.w 4,4\n dc.l $40\ncrc_table: dcb.l 256,0\n')
    (tmp_path/'pandora_OS_seeds.i').write_text(' move.w INPUT_ADDRESS+12,$40000\n')
    target=tmp_path/'app';listing=tmp_path/'app.list'
    p=subprocess.run([str(VASM),'-Fhunkexe','-m68000','-no-opt','-I'+str(NDK_INCLUDE),'-I'+str(ROOT/'tools'),'-I'+str(tmp_path),'-L',str(listing),'-o',str(target),str(ROOT/'tools/amiga_pandora_OS.s')],capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    labels={m[2]:int(m[1],16) for m in re.finditer(r'^([0-9A-F]{8}) (\w+)$',listing.read_text(),re.M)}
    return own_code(target.read_bytes()),labels


def machine(executable):
    code,labels=executable;m=machine68k.Machine(machine68k.CPUType.M68000,1024)
    m.mem.w_block(0x1000,code);m.cpu.w_sr(0x2700);m.cpu.w_reg(machine68k.Register.A7,0xf8000)
    m.cpu.w_reg(machine68k.Register.A5,0x1000+labels['host_state'])
    m.mem.w_block(0x1000+labels['state_owners'],b''.join(n.to_bytes(4,'big') for n in (0x1998,0x10170,0x101f0,0x10af0,0x10ed8,0x1ca90)))
    data=bytes.fromhex('07f000000000600000080000b17e0000');m.mem.w_block(0x20000,data)
    return m,labels,data


def call(m,entry):
    stop=0xfe000;sp=m.cpu.r_reg(machine68k.Register.A7);m.mem.w32(sp,stop);m.cpu.w_pc(entry)
    steps=0
    class Done(Exception):pass
    def hook(pc):
        nonlocal steps
        steps+=1;assert steps<3000
        if pc==stop:raise Done
    m.cpu.set_instr_hook_callback(hook)
    try:m.cpu.execute(300000)
    except Done:pass
    else:raise AssertionError('Own bounded routine did not return')

@pytest.mark.parametrize('bad',['none','WORD_reach','unaligned_owner','late_stale_field'])
def test_validate_all_before_apply_and_preserve_WORD_LONG_fields(executable,bad):
    m,l,data=machine(executable)
    if bad=='WORD_reach':m.mem.w32(0x1000+l['state_owners'],0x8000)
    if bad=='unaligned_owner':m.mem.w32(0x1000+l['state_owners']+4,0x10171)
    if bad=='late_stale_field':m.mem.w32(0x20004,0x6002);data=m.mem.r_block(0x20000,16)
    call(m,0x1000+l['validate_runtime_fields'])
    assert m.cpu.r_reg(machine68k.Register.D0)==(bad=='none')
    assert m.mem.r_block(0x20000,16)==data,'Validation must never partially patch'
    if bad=='none':
        call(m,0x1000+l['apply_runtime_fields'])
        assert m.mem.r16(0x20000)==0x199a and m.mem.r32(0x20004)==0x101b0
        assert m.mem.r32(0x20008)==0x1000+l['mission_restart_dispatch']
        assert m.mem.r16(0x40000)==0xb17e


@pytest.mark.parametrize('sr',[0x2700,0x270a,0x271b,0x271f])
def test_first_dispatch_preserves_every_register_SR_and_stack_link(executable,sr):
    m,l,_=machine(executable)
    for index in range(16):m.cpu.w_reg(machine68k.Register(index),0x10000+index*0x100)
    m.cpu.w_reg(machine68k.Register.A7,0xf8000);m.mem.w32(0xf8000,0x89fdc)
    m.cpu.w_sr(sr);before=[m.cpu.r_reg(machine68k.Register(i)) for i in range(16)]
    m.cpu.w_pc(0x1000+l['mission_restart_dispatch'])
    observed={}
    class Done(Exception):pass
    def hook(pc):
        if pc==0x80000:
            # Sample at the execution boundary: raising out of the oracle hook
            # before reading SR may expose its deferred host-side flag cache.
            observed['sr']=m.cpu.r_sr()
            raise Done
    m.cpu.set_instr_hook_callback(hook)
    try:m.cpu.execute(3000)
    except Done:pass
    else:raise AssertionError('Original initializer was not reached')
    assert [m.cpu.r_reg(machine68k.Register(i)) for i in range(16)]==before
    assert observed['sr']==sr and m.mem.r32(0xf8000)==0x89fdc
    assert m.mem.r32(0x1000+l['state_dispatch_count'])==1

@pytest.mark.parametrize('opened,locked,signal,expected',[
    (False,False,-1,[]),(False,False,3,['signal']),
    (True,False,3,['free_channels','close_device','signal']),
    (True,True,3,['free_channels','wait_lock','close_device','signal'])])
def test_audio_cleanup_completes_lock_before_close_and_frees_signal(executable,opened,locked,signal,expected):
    m,l,_=machine(executable);base=0x1000;execbase=0xf0000
    m.mem.w32(4,execbase)
    m.mem.w32(base+l['state_audio_open'],int(opened));m.mem.w32(base+l['state_audio_lock'],int(locked))
    m.mem.w32(base+l['state_signal'],signal&0xffffffff)
    # The NDK fixes these library offsets; this is a black-box call observer,
    # not an implementation of audio.device or a timing/DMA proof.
    calls={execbase-456:'free_channels',execbase-474:'wait_lock',execbase-450:'close_device',execbase-336:'signal'}
    for address in calls:m.mem.w_block(address,b'\x4e\x75')
    stop=0xfe000;m.mem.w32(0xf8000,stop);m.cpu.w_pc(base+l['release_audio']);seen=[]
    class Done(Exception):pass
    def hook(pc):
        if pc==stop:raise Done
        if pc in calls:
            seen.append(calls[pc]);a1=m.cpu.r_reg(machine68k.Register.A1)
            if calls[pc]=='wait_lock':assert a1==base+l['state_audio_lock_request']
            elif calls[pc]=='signal':assert m.cpu.r_reg(machine68k.Register.D0)==3
            else:
                assert a1==base+l['state_audio_request']
                if calls[pc]=='free_channels':assert m.mem.r16(a1+l['IO_COMMAND'])==l['ADCMD_FREE']
    m.cpu.set_instr_hook_callback(hook)
    try:m.cpu.execute(30000)
    except Done:pass
    else:raise AssertionError('Audio release did not return')
    assert seen==expected
    assert m.mem.r32(base+l['state_audio_open'])==0
    assert m.mem.r32(base+l['state_audio_lock'])==0
    assert m.mem.r32(base+l['state_signal'])==0xffffffff
