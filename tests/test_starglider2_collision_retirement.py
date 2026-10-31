"""Original post-filter collision responses and near/distant retirement CPU paths.

Supplied readable records/list/pool capacity are fixture preconditions. This is
not complete contact geometry, global alias invalidation or gameplay evidence.
"""
import pytest
from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, INPUT, STACK, RETURN

OUTER,INNER,POOL,ALIAS=INPUT+0x200,INPUT+0x300,INPUT+0x500,INPUT+0x600
LIMITS,AWARDS=0x17588,0x177B4
VARIANTS={'near':(0x817C,0x8196,0x81D2,255),'distant':(0x8344,0x835C,0x839C,0)}


def prepare(memory,kind=12,phase=255):
    memory[OUTER-4:OUTER+72]=b'\xCC'*76
    put(memory,OUTER,kind,2);memory[OUTER+30]=phase
    put(memory,APP+0x6D4,POOL);put(memory,APP+0x772,0,2)
    put(memory,ALIAS+60,OUTER);put(memory,APP+0x6B0,OUTER)


def execute(image,memory,entry,stop):
    cpu=state(memory,entry);cpu.a[0]=OUTER;run(image,memory,cpu,{stop});return cpu


@pytest.mark.parametrize('variant',VARIANTS)
@pytest.mark.parametrize('kind',[0,12,25,147])
@pytest.mark.parametrize('phase',[0,1,127,128,255])
def test_retirement_limit_uses_byte_equality_not_saturation(original_image,memory,variant,kind,phase):
    prepare(memory,kind,phase);limit=get(memory,LIMITS+kind,1);before=bytes(memory[OUTER:OUTER+68])
    age,_,end,final_phase=VARIANTS[variant];cpu=execute(original_image,memory,age,end)
    if phase==limit:
        expected=bytearray(68);expected[30]=final_phase
        assert bytes(memory[OUTER:OUTER+68])==expected
        assert get(memory,APP+0x772,2)==1 and get(memory,POOL)==OUTER
    else:
        expected=bytearray(before);expected[30]=(phase+1)&255
        assert bytes(memory[OUTER:OUTER+68])==expected and get(memory,APP+0x772,2)==0
    assert cpu.a[0]==OUTER and cpu.a[7]==STACK
    assert bytes(memory[OUTER-4:OUTER])==b'\xCC'*4 and bytes(memory[OUTER+68:OUTER+72])==b'\xCC'*4


@pytest.mark.parametrize('variant',VARIANTS)
@pytest.mark.parametrize('free',[0,1,65535])
def test_recycle_clears_68_bytes_but_retains_external_references(original_image,memory,variant,free):
    prepare(memory);put(memory,APP+0x772,free,2)
    _,release,end,final_phase=VARIANTS[variant];cpu=execute(original_image,memory,release,end)
    expected=bytearray(68);expected[30]=final_phase
    assert bytes(memory[OUTER:OUTER+68])==expected
    assert get(memory,APP+0x772,2)==(free+1)&65535 and get(memory,APP+0x6D4)==POOL+4
    assert get(memory,POOL)==OUTER and get(memory,ALIAS+60)==OUTER and get(memory,APP+0x6B0)==OUTER
    assert cpu.a[7]==STACK


@pytest.mark.parametrize('next_slot_index',[0,1,249,250])
def test_initial_free_stack_uses_one_based_inclusive_last_index(original_image,memory,next_slot_index):
    # Index zero is an out-of-contract local probe with explicit extra backing.
    start=INPUT;count=251-next_slot_index;pool=APP+0xEA4
    memory[pool-4:pool+1008]=b'\xCC'*1012
    cpu=state(memory,0x17EC2);cpu.a[0]=start;cpu.d[2]=68;cpu.d[7]=next_slot_index
    run(original_image,memory,cpu,{RETURN})
    assert get(memory,APP+0x772,2)==count and get(memory,APP+0x6D4)==pool+4*count
    assert [get(memory,pool+4*i)for i in range(count)]==[start+68*i for i in range(count)]
    assert get(memory,APP+0x172,2)==250 and memory[APP+0x7EE]==0
    assert bytes(memory[pool-4:pool])==b'\xCC'*4 and bytes(memory[pool+4*count:pool+4*count+4])==b'\xCC'*4


def contact(memory,side,kind=2,durability=1,phase=255,tracking=255,mini=1):
    target,projectile=(OUTER,INNER)if side=='outer'else(INNER,OUTER)
    for a in [OUTER,INNER]:memory[a:a+68]=b'\0'*68
    put(memory,target,kind,2);memory[target+28]=durability;memory[target+30]=phase;memory[target+2]=0x28
    put(memory,projectile,12,2);memory[projectile+34]=tracking
    put(memory,0x27A8,APP);put(memory,APP+0x5C,0xFFF0,2);put(memory,APP+0x6E4,0xFFFFFFFF);put(memory,APP+0xA7A,mini,2)
    return target,projectile


@pytest.mark.parametrize('side',['outer','inner'])
@pytest.mark.parametrize('kind',[2,37,98,99])
@pytest.mark.parametrize('tracking',[0,255])
@pytest.mark.parametrize('durability',[0,1,128,255])
def test_homing_contact_retirement_awards_and_ignored_types(original_image,memory,side,kind,tracking,durability):
    target,_=contact(memory,side,kind,durability,tracking=tracking)
    entry,end=(0xB714,0xB7D6)if side=='outer'else(0xB836,0xB8F8)
    cpu=state(memory,entry);cpu.a[0]=OUTER;cpu.a[2]=INNER
    run(original_image,memory,cpu,{end})
    eligible=kind==37 or not(durability&128)
    award=eligible and bool(tracking)and kind not in [98,99]
    retire=eligible and(not tracking or award)
    assert memory[target+30]==(0 if retire else 255) and memory[target+28]==durability
    assert memory[target+2]==(0x20 if retire else 0x28)
    assert get(memory,APP+0x6E4)==(0 if award else 0xFFFFFFFF)
    assert get(memory,APP+0x5C,2)==((0xFFF0+get(memory,AWARDS+2*kind,2))&65535 if award else 0xFFF0)
    assert get(memory,APP+0xA7A,2)==(0 if award and kind==37 else 1)
    assert get(memory,target,2)==kind and cpu.a[7]==STACK


@pytest.mark.parametrize('side',['outer','inner'])
@pytest.mark.parametrize('mini',[0,1,32768,65535])
def test_mini_sentinel_counter_preserves_n_only_saturation(original_image,memory,side,mini):
    contact(memory,side,kind=37,mini=mini)
    entry,end=(0xB714,0xB7D6)if side=='outer'else(0xB836,0xB8F8)
    cpu=state(memory,entry);cpu.a[0]=OUTER;cpu.a[2]=INNER;run(original_image,memory,cpu,{end})
    result=(mini-1)&65535
    assert get(memory,APP+0xA7A,2)==(0 if result&32768 else result)


@pytest.mark.parametrize('side',['outer','inner'])
@pytest.mark.parametrize('tracking',[0,255])
@pytest.mark.parametrize('tag',[0,254,255])
@pytest.mark.parametrize('durability',[2,3,127])
def test_surviving_damage_tags_skip_zero_and_keep_distinct_retirement_shortcut(original_image,memory,side,tracking,tag,durability):
    target,projectile=contact(memory,side,durability=durability,tracking=tracking)
    put(memory,projectile,103,2);memory[APP+0xDA6+2]=tag
    entry,end=(0xB72E,0xB7D6)if side=='outer'else(0xB852,0xB8F8)
    cpu=state(memory,entry);cpu.a[0]=OUTER;cpu.a[2]=INNER;run(original_image,memory,cpu,{end})
    assert memory[target+28]==durability-1 and memory[target+2]==0x2C
    assert memory[target+30]==(255 if tracking else 0)
    assert memory[APP+0xDA6+2]==((tag+1)&255 or 1)if tracking else memory[APP+0xDA6+2]==tag
    assert get(memory,APP+0x6E4)==(0 if tracking else 0xFFFFFFFF) and get(memory,APP+0x5C,2)==0xFFF0


@pytest.mark.parametrize('variant',VARIANTS)
@pytest.mark.parametrize('limit',[0,1,3])
def test_contact_phase_change_then_retirement_ticks_and_recycle_are_separate(original_image,memory,variant,limit):
    target,_=contact(memory,'outer',tracking=0);put(memory,APP+0x6D4,POOL);put(memory,APP+0x772,0,2)
    memory[LIMITS+2]=limit
    cpu=state(memory,0xB714);cpu.a[0]=OUTER;cpu.a[2]=INNER;run(original_image,memory,cpu,{0xB7D6})
    assert target==OUTER and memory[OUTER+30]==0 and get(memory,APP+0x772,2)==0
    age,_,end,final_phase=VARIANTS[variant]
    for phase in range(limit):
        execute(original_image,memory,age,end);assert memory[OUTER+30]==phase+1 and get(memory,APP+0x772,2)==0
    execute(original_image,memory,age,end)
    assert get(memory,OUTER,2)==0 and memory[OUTER+30]==final_phase and get(memory,APP+0x772,2)==1


def test_player_prefix_advances_one_based_index_before_empty_world_free_fill(original_image,memory):
    # Supplied zero-terminated empty placement stream, original player initializer.
    put(memory,0x2F9FC,INPUT);put(memory,INPUT,0,2);put(memory,APP+0x798,0,2)
    pool,free=APP+0x2330,APP+0xEA4
    memory[free:free+1008]=b'\xCC'*1008
    cpu=state(memory,0x17DBA);run(original_image,memory,cpu,{RETURN})
    assert get(memory,pool,2)==30 and get(memory,APP+0x700)==pool
    assert get(memory,APP+0x172,2)==250 and get(memory,APP+0x772,2)==249
    assert [get(memory,free+4*i)for i in range(249)]==[pool+68*(i+1)for i in range(249)]
    assert bytes(memory[free+996:free+1008])==b'\xCC'*12


@pytest.mark.parametrize('side',['outer','inner'])
@pytest.mark.parametrize('phase',[0,4,127,128,255])
def test_contact_start_preserves_existing_nonnegative_phase(original_image,memory,side,phase):
    target,_=contact(memory,side,phase=phase,tracking=0)
    entry,end=(0xB714,0xB7D6)if side=='outer'else(0xB836,0xB8F8)
    cpu=state(memory,entry);cpu.a[0]=OUTER;cpu.a[2]=INNER;run(original_image,memory,cpu,{end})
    assert memory[target+30]==(phase if phase<128 else 0)
    assert memory[target+2]==0x20 and get(memory,target,2)==2
