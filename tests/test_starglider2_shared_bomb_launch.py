"""Shared bomb initialization, complete bouncing launch and BYTE/WORD alias.

Backed records, HUD banks and trig tables are supplied inputs. Contact checks
start at the type/ignore filter with supplied pairs; geometry and final awards
remain outside these windows.
"""
import struct
import subprocess
from pathlib import Path
import pytest
from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, FB, RETURN
from tests.test_starglider2_bounce_effects import install_motion
from tests.test_starglider2_homing_launch import prepare, expected_hud, OBJECT, POOL, TARGET
from tests.test_starglider2_scan_acquisition import signed16, project


@pytest.fixture(scope='module')
def bomb_fields(tmp_path_factory, original_image):
    target=Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    names=['bouncing_bomb_hud_icon_count','bouncing_bomb_hud_saved_backgrounds',
           'bouncing_bomb_hud_screen_origin','model_type_population_counts',
           'try_launch_bouncing_bomb']
    folder=tmp_path_factory.mktemp('bomb-launch');asm,out=folder/'map.s',folder/'map.raw'
    asm.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(names)+'\n')
    p=subprocess.run([str(target.parents[1]/'ext/vasm/vasmm68k_mot'),'-quiet','-Fbin','-m68000',
        '-no-opt','-I'+str(target/'includes'),'-o',str(out),str(asm)],cwd=target,capture_output=True,text=True)
    assert p.returncode==0,p.stdout+p.stderr
    raw=out.read_bytes();assert raw[:-20]==original_image[0]
    result=dict(zip(names,struct.unpack('>5I',raw[-20:])))
    for key in ['bouncing_bomb_hud_icon_count','model_type_population_counts']:result[key]+=APP
    return result


def expected_record(m,before,angles,speed,header):
    result=bytearray(before);scale=(speed+200)&65535
    def f(off,v,width=2):put(result,off,v&((1<<(8*width))-1),width)
    if header:
        for off,v in [(34,255),(29,5),(3,0),(30,255),(28,1)]:f(off,v,1)
    f(36,1000);f(38,0);f(32,scale)
    sine,cosine=get(m,APP+0x44),get(m,APP+0x48)
    s0,c0,s1,c1=[get(m,p+2*(angle&4095),2)for p,angle in [(sine,angles[0]),(cosine,angles[0]),(sine,angles[1]),(cosine,angles[1])]]
    velocity=[(-project(project(scale,s1),c0))&65535,(-project(scale,s0))&65535,project(project(scale,c1),c0)&65535]
    for off,v in zip([16,18,20],angles):f(off,v)
    for off,v in zip([44,46,48],velocity):f(off,v)
    for off,world,v in zip([4,8,12],[get(m,APP+x)for x in [0x704,0x708,0x70C]],velocity):
        value=(world+signed16(v))&0xFFFFFFFF
        f(off,value if off==8 else value&get(m,APP+0x6FC),4)
    return result


@pytest.mark.parametrize('kind,entry',[(91,0x7A98),(98,0x7A98),(98,0x7AB2)])
@pytest.mark.parametrize('dirty',[0,0xA5])
@pytest.mark.parametrize('speed',[0,200,32767,32768,65336,65535])
@pytest.mark.parametrize('angles',[(0,0,0),(1024,2048,3072),(65535,4097,32768)])
@pytest.mark.parametrize('world',[(0x12345,0xFFFFFC18,0x23456),(0x7FFFFFFF,0x80000000,0xFFFFFFFE)])
def test_shared_entries_preserve_neighbors_and_bounce_consumes_the_overlaid_phase(original_image,memory,kind,entry,dirty,speed,angles,world):
    m=memory;install_motion(original_image,m);m[OBJECT:OBJECT+68]=bytes([dirty])*68;put(m,OBJECT,kind,2)
    for off,value in zip([0x704,0x708,0x70C],world):put(m,APP+off,value)
    for off,value in zip([0x744,0x746,0x748],angles):put(m,APP+off,value,2)
    put(m,APP+0x75A,speed,2);put(m,APP+0x6FC,65535)
    expected=expected_record(m,m[OBJECT:OBJECT+68],angles,speed,entry==0x7A98)
    cpu=state(m,entry);cpu.a[2]=OBJECT
    run(original_image,m,cpu,{RETURN},limit=100)
    assert bytes(m[OBJECT:OBJECT+68])==expected
    if kind==91:
        # Before the first body update the common header wrote only the high byte.
        assert get(m,OBJECT+34,2)==0xFF00|dirty
        m[APP+0x77D]=128
        updated=bytearray(expected)
        for off,v in [(4,get(m,OBJECT+4)+signed16(get(m,OBJECT+44,2))),
                      (12,get(m,OBJECT+12)+signed16(get(m,OBJECT+48,2)))]:put(updated,off,v&65535)
        put(updated,36,999,2);put(updated,34,0,2);updated[3]=11
        c=state(m,0x368AE);c.a[0]=OBJECT;run(original_image,m,c,{RETURN},limit=60)
        assert bytes(m[OBJECT:OBJECT+68])==updated


@pytest.mark.parametrize('mode',[0,1,2])
@pytest.mark.parametrize('icons',[0,1,2,9])
@pytest.mark.parametrize('inventory',[0,1,128,129,255])
@pytest.mark.parametrize('free',[0,2,3,65535])
def test_complete_bouncing_launch_preserves_gate_order_and_partial_record(original_image,memory,bomb_fields,mode,icons,inventory,free):
    m=memory;install_motion(original_image,m);f=bomb_fields
    prepare(m,mode,icons=icons,free=free);put(m,f['bouncing_bomb_hud_icon_count'],icons,2)
    inventory_addr=f['model_type_population_counts']+91;m[inventory_addr]=inventory
    backup=f['bouncing_bomb_hud_saved_backgrounds'];put(m,f['bouncing_bomb_hud_screen_origin'],FB+0x4800)
    for i in range(896):m[backup+i]=(i*19+3)&255
    put(m,APP+0x700,TARGET);m[TARGET:TARGET+68]=b'\x5A'*68;put(m,TARGET,30,2)
    angles=[1024,2048,3072];speed=65535
    for off,value in zip([0x744,0x746,0x748],angles):put(m,APP+off,value,2)
    put(m,APP+0x75A,speed,2);put(m,APP+0x6FC,65535)
    parent=bytearray(m[TARGET:TARGET+68]);before=bytes(m[OBJECT:OBJECT+68]);admitted=free>2 and inventory!=0 and icons!=0
    expected=expected_record(m,before,angles,speed,True)if admitted else bytearray(before)
    expected_pixels=expected_hud(m,mode,icons,backup)if admitted else bytes(m[FB:FB+0x18000])
    if admitted:
        put(expected,0,91,2);put(expected,46,30,2);put(expected,8,(get(expected,8)+20)&0xFFFFFFFF)
        expected[42]=91;parent[42]=91
    old_cooldown=get(m,APP+0x7C4,2)
    cpu=state(m,f['try_launch_bouncing_bomb']);run(original_image,m,cpu,{RETURN,0x7B22},limit=500)
    missing=free>2 and inventory==0
    assert cpu.pc==(0x7B22 if missing else RETURN)
    assert bytes(m[OBJECT:OBJECT+68])==expected and bytes(m[TARGET:TARGET+68])==parent
    assert bytes(m[FB:FB+0x18000])==expected_pixels
    assert get(m,f['bouncing_bomb_hud_icon_count'],2)==(icons-1 if admitted else icons)
    left=(inventory-1)&255
    assert m[inventory_addr]==(0 if admitted and left&128 else left if admitted else inventory)
    assert get(m,APP+0x772,2)==(free-1 if admitted else free)
    assert get(m,APP+0x6D4)==(POOL if admitted else POOL+4)
    assert get(m,APP+0x7C4,2)==(150 if admitted else old_cooldown)


@pytest.mark.parametrize('low_phase',[0,1,2,3,165,255])
@pytest.mark.parametrize('speed',[0,65336,65356,32767,65535])
def test_constructor_to_first_surface_bounce_distinguishes_phase_mask_and_rest(original_image,memory,bomb_fields,low_phase,speed):
    m=memory;install_motion(original_image,m);f=bomb_fields
    prepare(m,0,icons=1,free=3);put(m,f['bouncing_bomb_hud_icon_count'],1,2)
    m[f['model_type_population_counts']+91]=1
    put(m,f['bouncing_bomb_hud_screen_origin'],FB+0x4800)
    put(m,APP+0x700,TARGET);put(m,TARGET,30,2)
    m[OBJECT:OBJECT+68]=bytes(68);m[OBJECT+35]=low_phase
    for off,value in [(0x704,1000),(0x708,0xFFFFFFD8),(0x70C,2000),(0x6FC,65535)]:put(m,APP+off,value)
    for off in [0x744,0x746,0x748]:put(m,APP+off,0,2)
    put(m,APP+0x75A,speed,2)
    c=state(m,f['try_launch_bouncing_bomb']);run(original_image,m,c,{RETURN},limit=500)
    initial=bytearray(m[OBJECT:OBJECT+68]);scale=get(m,OBJECT+32,2)
    # Zero-angle launch copies Y=-40, adds20, then replaces vector VY with30.
    assert get(m,OBJECT+8)==0xFFFFFFEC and get(m,OBJECT+46,2)==30
    next_scale=(scale-20)&65535;nonnegative=not(next_scale&32768)
    if not nonnegative:next_scale=0
    resting=next_scale==0
    expected=bytearray(initial);put(expected,32,next_scale,2);put(expected,38,3,2)
    put(expected,46,65512,2);put(expected,8,0xFFFFFFE7 if resting else 0xFFFFFFF6)
    sine,cosine=get(m,APP+0x44),get(m,APP+0x48)
    vx=(-project(project(next_scale,get(m,sine,2)),get(m,cosine,2)))&65535
    vz=project(project(next_scale,get(m,cosine,2)),get(m,cosine,2))&65535
    for off,value in [(44,vx),(48,vz)]:put(expected,off,value,2)
    for off,v in [(4,vx),(12,vz)]:put(expected,off,(get(initial,off)+signed16(v))&65535)
    if resting:expected[30]=0
    else:
        put(expected,36,999,2);phase=(get(initial,34,2)+1)&3;put(expected,34,phase,2)
        if phase==0:expected[3]=11
    m[APP+0x77D]=0;m[APP+0xAE1]=0
    c=state(m,0x368AE);c.a[0]=OBJECT;run(original_image,m,c,{RETURN},limit=110)
    assert bytes(m[OBJECT:OBJECT+68])==expected
    assert m[APP+0xAE1]==(255 if nonnegative else 0)
    assert m[OBJECT+34]==(255 if resting else 0)


@pytest.mark.parametrize('kind',[12,84,91,98,103])
@pytest.mark.parametrize('marker',[0,1,255])
@pytest.mark.parametrize('inner',[False,True])
def test_complete_contact_type_filter_bypasses_generic_byte_for_bomb_types(original_image,memory,kind,marker,inner):
    m=memory;victim=TARGET;peer=OBJECT
    m[victim:victim+68]=bytes(68);m[peer:peer+68]=bytes(68)
    put(m,victim,1,2);put(m,peer,kind,2)
    m[victim+28]=2;m[victim+30]=255;m[peer+28]=1;m[peer+30]=255;m[peer+34]=marker
    entry=0xB7D6 if inner else 0xB6A0
    filter_pc=0xB894 if inner else 0xB772
    award_pc=0xB8A6 if inner else 0xB784
    credit_pc=0xB868 if inner else 0xB744
    clear_pc=0xB8F4 if inner else 0xB7D2
    retire_pc=0xB8E8 if inner else 0xB7C6
    c=state(m,entry);c.a[0],c.a[2]=(peer,victim)if inner else(victim,peer)
    run(original_image,m,c,{filter_pc,award_pc,credit_pc,clear_pc,retire_pc},limit=45)
    expected=filter_pc if kind==91 else award_pc if kind==98 else (filter_pc if marker else retire_pc)if kind in [12,84] else credit_pc if marker else clear_pc
    assert c.pc==expected
    assert m[victim+28]==(0 if kind==84 else 1 if kind==103 else 2)
