"""Original packed-BCD field updates and three digit renderers with supplied RAM.

Valid packed-BCD arithmetic only; no caller-wide decimal validity, IRQ cadence,
framebuffer lifetime, mode-switch or hardware scanout claim.
"""
import ctypes
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state as initial_state,put,get,APP,INPUT,STACK

RETURN=0x9F000


def state(memory,entry):
    cpu=initial_state(memory,entry);put(memory,STACK,RETURN)
    return cpu


def run(image,memory,cpu,stops,stimulus=None,limit=30000,observe=None):
    # Independent black-box oracle: the generated concrete executor currently
    # refuses ABCD. No guest instructions or transfer semantics are replaced.
    machine68k=pytest.importorskip('machine68k')
    oracle=machine68k.Machine(machine68k.CPUType.M68000,1024)
    oracle.mem.w_block(0,bytes(memory));oracle.cpu.w_sr(cpu.sr)
    registers=[getattr(machine68k.Register,f'{prefix}{i}')for prefix in['D','A']for i in range(8)]
    for register,value in zip(registers,list(cpu.d)+list(cpu.a)):oracle.cpu.w_reg(register,value)
    oracle.cpu.w_pc(cpu.pc)
    for _ in range(limit):
        pc=oracle.cpu.r_pc()
        if pc in stops:break
        assert 0x1000<=pc<0x1000+len(image[0]),hex(pc)
        if stimulus:stimulus(pc)
        if observe:observe(pc,oracle.mem)
        oracle.cpu.execute(1)  # Musashi completes one instruction at this cycle budget.
    else:pytest.fail('Original BCD routine exceeded its bounded handoff')
    ctypes.memmove(ctypes.addressof(memory),oracle.mem.r_block(0,len(memory)),len(memory))
    cpu.d[:]=[oracle.cpu.r_reg(r)for r in registers[:8]]
    cpu.a[:]=[oracle.cpu.r_reg(r)for r in registers[8:]]
    cpu.pc=oracle.cpu.r_pc();cpu.sr=oracle.cpu.r_sr()


FONT,SCRATCH,SCORE,COUNTER,TIMER=0x16DE0,0xE000,APP+0x71C,APP+0x7AA,APP+0x7AC
SCORES={'amiga':(0xD620,0xD634,[0x70094]),'mode0':(0x3CAF2,0x3CB0A,[0x682F0,0x702F0,0x782F0]),'mode1':(0x3D384,0x3D39C,[0x68218,0x70218,0x78218])}
PERIODIC={'amiga':(0xD6A0,[0x702E2]),'mode0':(0x3CCFE,[0x68C28,0x70C28,0x78C28]),'mode1':(0x3CCFE,[0x68B64,0x70B64,0x78B64])}


def packed(number,digits):return int(f'{number:0{digits}d}',16)


def pixels(m,mode,anchors,number,digits,expected):
    for column,char in enumerate(f'{number:0{digits}d}'):
        glyph=bytes(m[FONT+8*int(char):FONT+8*(int(char)+1)])
        for anchor in anchors:
            for row,value in enumerate(glyph):
                if mode=='amiga':
                    for plane in[0x4000,0x6000]:expected[anchor+plane+40*row+column]=value
                elif mode=='mode0':
                    for plane in[4,6]:expected[anchor+160*row+8*(column//2)+column%2+plane]=value
                else:
                    doubled=sum(((value>>bit)&1)*3<<(2*bit)for bit in range(8))
                    for vertical in[0,80]:expected[anchor+160*row+vertical+2*column:anchor+160*row+vertical+2*column+2]=doubled.to_bytes(2,'big')


def saved_digit_helper_frame(expected):
    expected[STACK-12:STACK-8]=FONT.to_bytes(4,'big')
    expected[STACK-8:STACK-4]=(INPUT+0x280).to_bytes(4,'big')
    expected[STACK-4:STACK]=(0x3D3CC).to_bytes(4,'big')


@pytest.mark.parametrize('mode',SCORES)
@pytest.mark.parametrize('score',[0,1,9,10,99,999,9999,99999,999999,123456])
@pytest.mark.parametrize('addend',[0,1,9,99,555555])
@pytest.mark.parametrize('prefix',[0,0xA5])
def test_score_updates_low_three_bytes_and_draws_six_digits(original_image,memory,mode,score,addend,prefix):
    m=memory;entry,after_bcd,anchors=SCORES[mode];input_value=(prefix<<24)|packed(addend,6)
    put(m,SCORE,(prefix<<24)|packed(score,6));cpu=state(m,entry);cpu.d[0]=input_value;cpu.sr|=0x10
    expected=bytearray(m);answer=(score+addend)%1000000
    expected[SCRATCH:SCRATCH+4]=input_value.to_bytes(4,'big')
    expected[SCORE:SCORE+4]=((prefix<<24)|packed(answer,6)).to_bytes(4,'big')
    run(original_image,m,cpu,{after_bcd})
    assert get(m,SCORE)==(prefix<<24)|packed(answer,6)
    assert cpu.sr&0x15==((0x11 if score+addend>=1000000 else 0)|(4 if answer==0 else 0))
    assert cpu.a[1]==SCORE+1 and cpu.a[0]==SCRATCH+1
    pixels(m,mode,anchors,answer,6,expected)
    if mode=='mode1':saved_digit_helper_frame(expected)
    run(original_image,m,cpu,{RETURN});assert bytes(m)==expected
    assert cpu.a[7]==STACK+4


@pytest.mark.parametrize('mode',PERIODIC)
@pytest.mark.parametrize('counter',[0,9,9999])
@pytest.mark.parametrize('countdown',[0,1,65535])
@pytest.mark.parametrize('flags',[0,2,128,130])
def test_periodic_two_byte_increment_timer_policy_and_render_gate(original_image,memory,mode,counter,countdown,flags):
    m=memory;entry,anchors=PERIODIC[mode];m[APP+0x1F2]=2 if mode=='mode1'else 0
    m[APP+0x20A]=flags;put(m,COUNTER,packed(counter,4),2);put(m,TIMER,countdown,2)
    cpu=state(m,entry);cpu.sr|=0x10;expected=bytearray(m);answer=(counter+1)%10000
    expected[COUNTER:COUNTER+2]=packed(answer,4).to_bytes(2,'big')
    expected[TIMER:TIMER+2]=(((countdown+432)&65535)if mode=='mode1'else 432).to_bytes(2,'big')
    if flags&2:
        pixels(m,mode,anchors,answer,4,expected)
        if mode=='mode1':saved_digit_helper_frame(expected)
    run(original_image,m,cpu,{RETURN});assert bytes(m)==expected
    assert cpu.a[7]==STACK+4


@pytest.mark.parametrize('graphics',[0,1,2,3,128,130])
def test_alternate_periodic_dispatch_uses_bit_one_not_sign(original_image,memory,graphics):
    m=memory;m[APP+0x1F2]=graphics;m[APP+0x20A]=0
    put(m,COUNTER,0x0099,2);put(m,TIMER,65535,2);cpu=state(m,0x3CCFE)
    visited=[];run(original_image,m,cpu,{RETURN},visited.append)
    assert (0x3D3D2 in visited)==bool(graphics&2)
    assert get(m,COUNTER,2)==0x0100 and get(m,TIMER,2)==(431 if graphics&2 else 432)


@pytest.mark.parametrize('mode',PERIODIC)
@pytest.mark.parametrize('flags',[0,2,128])
@pytest.mark.parametrize('modal',[0,1,128])
@pytest.mark.parametrize('countdown',[0,1,2,65535])
def test_observed_caller_calls_only_on_word_zero_after_sign_and_modal_gates(original_image,memory,mode,flags,modal,countdown):
    m=memory;m[APP+0x1F2]=2 if mode=='mode1'else 0;m[APP+0x20A]=flags;m[APP+0x6DA]=modal
    put(m,COUNTER,0x0099,2);put(m,TIMER,countdown,2);put(m,APP+0x7C2,65535,2)
    if mode=='amiga':entry,stop,skip,callee=0xC738,0xC754,0xC876,0xD6A0
    else:entry,stop,skip,callee=0x3B1AC,0x3B1C8,0x3B28C,0x3CCFE
    cpu=state(m,entry);expected=bytearray(m);observed=[]
    def inspect(pc,ram):
        if pc==callee:observed.append(int.from_bytes(ram.r_block(TIMER,2),'big'))
    advances=bool(flags&128)and not modal;calls=advances and countdown==1
    if advances:
        expected[APP+0x7C2:APP+0x7C4]=b'\0\0'
        expected[TIMER:TIMER+2]=((countdown-1)&65535).to_bytes(2,'big')
    if calls:
        expected[COUNTER:COUNTER+2]=b'\x01\x00';expected[TIMER:TIMER+2]=(432).to_bytes(2,'big')
        expected[STACK-4:STACK]=stop.to_bytes(4,'big')
    run(original_image,m,cpu,{stop,skip},observe=inspect)
    assert observed==([0]if calls else[])
    assert bytes(m)==expected and cpu.a[7]==STACK
