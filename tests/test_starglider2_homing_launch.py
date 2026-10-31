"""Original homing-input, inventory, HUD restore and record-allocation CPU paths.

Supplied valid pool/HUD state is not a normal-game target lifetime or hardware
proof. Calls and original motion arithmetic execute without guest opcode patches.
"""
import pytest
from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, FB, INPUT, STACK, RETURN
from tests.test_starglider2_scan_acquisition import signed16, project

POOL, OBJECT, TARGET = INPUT+0x100, INPUT+0x200, INPUT+0x400
BACKUP, ORIGIN, KEYS = 0x7B40, 0x7920, 0xDE8C
ICONS, FREE, COUNTER = 0x78A, 0x772, 0xAE5+12


def prepare(memory,mode=0,icons=2,free=3,counter=2):
    put(memory,0x1002,0x8000 if mode==0 else 0,2)
    memory[APP+0x1F2]=255 if mode==2 else 0
    put(memory,APP+ICONS,icons,2);put(memory,APP+FREE,free,2);memory[APP+COUNTER]=counter
    put(memory,ORIGIN,FB+0x4800);put(memory,APP+0x6D4,POOL+4);put(memory,POOL,OBJECT)
    put(memory,APP+0x6B0,TARGET);put(memory,APP+0x7C4,0,2)
    put(memory,APP+0x760,1,2);put(memory,APP+0x750,1,2)
    for i in range(896):memory[BACKUP+i]=(13*i+7)&255
    memory[OBJECT:OBJECT+68]=b'\xCC'*68
    # Original pointer installer executes in each full launch case.
    put(memory,APP+0x704,0x12345);put(memory,APP+0x708,0xFFFFFFF0);put(memory,APP+0x70C,0x23456)
    put(memory,APP+0x6FC,0xFFFF,4)


def expected_hud(memory,mode,icons):
    result=bytearray(memory[FB:FB+0x18000]);source=BACKUP+((icons-1)&7)*112
    destination=FB+0x4800-signed16(icons*(480 if mode==0 else 1920))
    for row in range(14):
        data=bytes(memory[source+8*row:source+8*row+8]);base=destination+(40 if mode==0 else 160)*row
        writes=[(base+8192*p,data[2*p:2*p+2])for p in range(4)]if mode==0 else [
            (base+32768*p+off,data[start:start+4])for p in range(3)
            for off,start in [(0,0),(80 if mode==2 else 4,4)]]
        for addr,b in writes:result[addr-FB:addr-FB+len(b)]=b
    return bytes(result)


@pytest.mark.parametrize('cooldown',[0,1])
@pytest.mark.parametrize('one_hand',[0,1])
@pytest.mark.parametrize('direction',[0,1,2,3,4])
@pytest.mark.parametrize('button',['none','mouse','primary','key'])
def test_existing_lock_input_precedence(original_image,memory,cooldown,one_hand,direction,button):
    prepare(memory);put(memory,APP+0x7C4,cooldown,2);memory[APP+0x7F1]=one_hand
    put(memory,APP+0x15C,direction,2);memory[APP+0x7F2]=255
    memory[APP+0x201]=button=='mouse';memory[APP+0x1FD]=button=='primary'
    memory[KEYS+255]=button=='key'
    cpu=state(memory,0x757E);run(original_image,memory,cpu,{0x75EA,0x76D4})
    launch=not cooldown and(not one_hand or not(direction&3))and button!='none'
    assert cpu.pc==(0x75EA if launch else 0x76D4)
    assert get(memory,APP+ICONS,2)==2 and get(memory,APP+FREE,2)==3


@pytest.mark.parametrize('icons',[0,1,2,9])
@pytest.mark.parametrize('free',[0,1,2,3,65535])
def test_icon_decrement_precedes_free_slot_guard(original_image,memory,icons,free):
    prepare(memory,icons=icons,free=free);before=bytes(memory[FB:FB+0x18000])
    cpu=state(memory,0x75EA);run(original_image,memory,cpu,{RETURN,0x760C})
    assert cpu.pc==(0x760C if icons and free>2 else RETURN)
    assert get(memory,APP+ICONS,2)==max(0,icons-1)
    assert get(memory,APP+FREE,2)==free and get(memory,APP+0x6D4)==POOL+4
    assert memory[APP+COUNTER]==2 and bytes(memory[FB:FB+0x18000])==before


@pytest.mark.parametrize('mode',range(3))
@pytest.mark.parametrize('counter',[0,1,2,128,129,255])
def test_hud_restore_precedes_counter_signed_result_guard(original_image,memory,mode,counter):
    prepare(memory,mode,counter=counter);expected=expected_hud(memory,mode,2)
    cpu=state(memory,0x75EA);run(original_image,memory,cpu,{0x7626,0x7B22})
    decremented=(counter-1)&255;accepted=not(decremented&128)
    assert cpu.pc==(0x7626 if accepted else 0x7B22)
    assert memory[APP+COUNTER]==(decremented if accepted else 0)
    assert bytes(memory[FB:FB+0x18000])==expected
    assert get(memory,APP+ICONS,2)==1 and get(memory,APP+FREE,2)==3
    assert get(memory,APP+0x6D4)==POOL+4 and bytes(memory[OBJECT:OBJECT+68])==b'\xCC'*68
    if not accepted:assert cpu.d[0]&65535==0x114


@pytest.mark.parametrize('mode',range(3))
@pytest.mark.parametrize('icons',[1,2,9])
@pytest.mark.parametrize('speed',[0,32767,32768,65535])
@pytest.mark.parametrize('angles',[(0,0,0),(1024,2048,3072),(65535,4097,32768)])
def test_complete_launch_uses_original_motion_and_preserves_unwritten_record_bytes(original_image,memory,mode,icons,speed,angles):
    prepare(memory,mode,icons=icons);put(memory,APP+0x75A,speed,2)
    for off,v in zip([0x744,0x746,0x748],angles):put(memory,APP+off,v,2)
    cpu=state(memory,0x1F0E);run(original_image,memory,cpu,{RETURN})
    sine,cosine=get(memory,APP+0x44),get(memory,APP+0x48)
    s0,c0,s1,c1=[get(memory,base+2*(angle&4095),2)for base,angle in [(sine,angles[0]),(cosine,angles[0]),(sine,angles[1]),(cosine,angles[1])]]
    scale=(speed+500)&65535
    velocity=[(-project(project(scale,s1),c0))&65535,(-project(scale,s0))&65535,project(project(scale,c1),c0)&65535]
    expected_record=bytearray(memory[OBJECT:OBJECT+68])
    def field(off,value,width=2):expected_record[off:off+width]=value.to_bytes(width,'big')
    field(0,12);field(29,3,1);field(3,0,1);field(28,0xCC|128,1);field(30,255,1)
    field(34,255,1);field(36,400);field(60,TARGET,4);field(32,scale)
    for off,value in zip([16,18,20],[angles[0]|1,angles[1],angles[2]]):field(off,value)
    for off,value in zip([44,46,48],velocity):field(off,value)
    for off,base,v in zip([4,8,12],[0x12345,0xFFFFFFF0,0x23456],velocity):
        value=(base+signed16(2*v))&0xFFFFFFFF
        field(off,value if off==8 else value&0xFFFF,4)
    expected=expected_hud(memory,mode,icons);before_aim=bytes(memory[APP+0x766:APP+0x772])
    cpu=state(memory,0x75EA);run(original_image,memory,cpu,{RETURN})
    assert bytes(memory[OBJECT:OBJECT+68])==expected_record
    assert bytes(memory[FB:FB+0x18000])==expected
    assert get(memory,APP+FREE,2)==2 and get(memory,APP+0x6D4)==POOL and memory[APP+COUNTER]==1
    assert get(memory,APP+ICONS,2)==icons-1 and get(memory,APP+0x7C4,2)==100
    assert bytes(memory[APP+0x766:APP+0x772])==before_aim and get(memory,APP+0x750,2)==1
    assert cpu.a[2]==OBJECT and cpu.a[7]==STACK+4


@pytest.mark.parametrize('target',[0,0xFFFFFFFF,TARGET])
def test_launch_copies_target_without_dereferencing_or_validating_it(original_image,memory,target):
    prepare(memory);put(memory,APP+0x6B0,target)
    cpu=state(memory,0x1F0E);run(original_image,memory,cpu,{RETURN})
    cpu=state(memory,0x75EA);run(original_image,memory,cpu,{RETURN})
    assert get(memory,OBJECT+60)==target and get(memory,APP+0x6B0)==target
