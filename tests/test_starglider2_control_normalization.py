"""Original control continuations in supplied RAM contexts, not a gameplay trace."""
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,RETURN

YAW,PITCH,SPEED,ROT2,STEP,TARGET=0x7A2,0x7A4,0x7A8,0x748,0x1C8,0x758
FIRE,DIRECTIONS,AUTOCENTRE,DOCK,PHASE,BIAS,CLAMP=0x1FD,0x15C,0x7F0,0x7EC,0x796,0x786,0x7E4
HOLD=0x39CC6

def signed(v,bits=16):
    v&=(1<<bits)-1
    return v-(1<<bits) if v&(1<<(bits-1)) else v

def word(m,offset,value):put(m,APP+offset,value&65535,2)

def guard(m,before,allowed):
    after=bytearray(m[APP:APP+0x1000])
    for off,width in allowed:
        after[off:off+width]=before[off:off+width]
    assert bytes(after)==before

def centre(v):
    # Actual BMI/BPL test subtraction N alone, rather than N xor V.
    if signed(v-32)>=0:return(v-32)&65535
    if signed(v-0xFFE1)<0:return(v+32)&65535
    return v&65535

@pytest.mark.parametrize('directions',list(range(16))+[0x10,0xFFFF])
@pytest.mark.parametrize('fire',[0,255])
@pytest.mark.parametrize('mode',[0,1,2,3])
def test_joystick_fire_modifier_and_per_axis_autocentre(original_image,memory,directions,fire,mode):
    m=memory;word(m,YAW,64);word(m,PITCH,-64);word(m,SPEED,0)
    word(m,DIRECTIONS,directions);m[APP+FIRE]=fire;m[APP+AUTOCENTRE]=mode
    before=bytes(m[APP:APP+0x1000]);yaw,pitch,speed=64,-64,0
    if fire and directions&3:speed=-16 if directions&1 else 16
    else:
        yaw+=32*bool(directions&8)-32*bool(directions&4)
        pitch+=32*bool(directions&2)-32*bool(directions&1)
        if directions==0:
            if mode&1:yaw=centre(yaw)
            if mode&2:pitch=centre(pitch)
    cpu=state(m,0x19B4);run(original_image,m,cpu,{RETURN})
    assert [get(m,APP+o,2)for o in [YAW,PITCH,SPEED]]==[x&65535 for x in [yaw,pitch,speed]]
    guard(m,before,[(YAW,2),(PITCH,2),(SPEED,2)])

@pytest.mark.parametrize('value',[-32768,-32767,-32737,-32736,-33,-32,-31,-1,0,31,32,33,32767])
@pytest.mark.parametrize('mode',[1,2,3,128])
def test_autocentre_retains_n_only_overflow_and_dead_band(original_image,memory,value,mode):
    m=memory;word(m,YAW,value);word(m,PITCH,value);m[APP+AUTOCENTRE]=mode
    cpu=state(m,0x1A18);run(original_image,m,cpu,{RETURN})
    assert get(m,APP+YAW,2)==(centre(value) if mode&1 else value&65535)
    assert get(m,APP+PITCH,2)==(centre(value) if mode&2 else value&65535)


def normalize(image,m,pitch,speed,yaw=0,dock=0,phase=0,bias=0,clamp=0,hold=0):
    for off,v in [(PITCH,pitch),(SPEED,speed),(YAW,yaw),(PHASE,phase)]:word(m,off,v)
    for off,v in [(DOCK,dock),(BIAS,bias),(CLAMP,clamp)]:m[APP+off]=v
    put(m,HOLD,hold,2);before=bytes(m[APP:APP+0x1000])
    p=max(-1600,min(1600,signed(pitch)));step=0 if -48<=p<=48 else -(p>>4)
    s=max(-479,min(0,signed(speed)))
    if dock:s=0 if phase==30 else -10
    target=-s;new_bias=bias
    if bias:
        if p<0:new_bias=0
        else:new_bias=(bias-1)&255;p-=10
    if clamp or hold:target=max(0,target-4);s=min(0,s+2)
    cpu=state(m,0x2F71C);run(image,m,cpu,{0x2F7EA})
    assert [get(m,APP+o,2)for o in [PITCH,SPEED,ROT2,STEP,TARGET]]==[x&65535 for x in [p,s,(-yaw)&4095,step,target]]
    assert m[APP+BIAS]==new_bias
    guard(m,before,[(PITCH,2),(SPEED,2),(ROT2,2),(STEP,2),(TARGET,2),(BIAS,1)])
    return cpu

@pytest.mark.parametrize('pitch',[-32768,-1601,-1600,-49,-48,-1,0,1,48,49,1600,1601,32767])
@pytest.mark.parametrize('speed',[-32768,-480,-479,-1,0,1,32767])
@pytest.mark.parametrize('yaw',[-32768,-1,0,4095,32767])
def test_normalization_clamps_dead_band_and_numbered_rotation(original_image,memory,pitch,speed,yaw):
    normalize(original_image,memory,pitch,speed,yaw)

@pytest.mark.parametrize('dock,phase,clamp,hold',[(0,0,0,0),(1,29,0,0),(255,30,0,0),(1,31,1,0),(0,0,1,0),(0,0,0,65535)])
@pytest.mark.parametrize('pitch,bias',[(-1,2),(0,1),(9,255),(1601,2)])
@pytest.mark.parametrize('speed',[-479,-1,1])
def test_bias_runs_after_step_and_braking_uses_pre_increment_speed(original_image,memory,dock,phase,clamp,hold,pitch,bias,speed):
    normalize(original_image,memory,pitch,speed,dock=dock,phase=phase,bias=bias,clamp=clamp,hold=hold)

@pytest.mark.parametrize('world_y',[-0x80000000,-121,-120,-119,0,0x7FFFFFFF])
@pytest.mark.parametrize('space',[0,127,128,255])
@pytest.mark.parametrize('dock',[0,1])
def test_height_consumer_uses_pre_bias_step_and_n_only_world_guard(original_image,memory,world_y,space,dock):
    m=memory;cpu=normalize(original_image,m,1601,-100,dock=dock,bias=2)
    # STEP was computed from1600 before the bias changed the stored pitch to1590.
    assert get(m,APP+STEP,2)==(-100)&65535
    put(m,APP+0x708,world_y&0xFFFFFFFF);m[APP+0x77D]=space
    word(m,0x16C,-257);word(m,0x746,4090)
    before=bytes(m[APP:APP+0x1000]);run(original_image,m,cpu,{0x2F82E})
    drift=(-257)>>(6 if space&128 else 8)
    expected_rot=4090 if dock else(4090+drift)&4095
    can_move=not dock and not(space&128) and signed(world_y+120,32)>=0
    expected_y=(world_y-100 if can_move else world_y)&0xFFFFFFFF
    assert get(m,APP+0x746,2)==expected_rot and get(m,APP+0x708)==expected_y
    guard(m,before,[(0x746,2),(0x708,4)])

@pytest.mark.parametrize('current',[-32768,-1,0,1,5,6,15,16,23,24,25,100,479,32767])
@pytest.mark.parametrize('target',[-32768,-1,0,1,5,6,16,100,479,32767])
@pytest.mark.parametrize('space',[0,128])
def test_speed_update_preserves_n_only_target_comparisons_and_original_steps(original_image,memory,current,target,space):
    m=memory;word(m,0x75A,current);word(m,TARGET,target);m[APP+0x77D]=space
    before=bytes(m[APP:APP+0x1000]);expected=current&65535
    if (target&65535)!=(current&65535):
        if signed(target-current)>=0:
            expected=(current+6)&65535
            if signed(target-expected)>=0:expected=target&65535
        else:
            if space&128:expected=(current-16)&65535
            else:
                expected=(current-24)&65535
                if signed(expected)<0:expected=(expected-16)&65535
            if signed(expected)<0:expected=0
    cpu=state(m,0x2F6CA);run(original_image,m,cpu,{0x2F700})
    assert get(m,APP+0x75A,2)==expected
    guard(m,before,[(0x75A,2)])
