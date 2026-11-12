"""Original constructor prefixes expose partial WORD and phase-specific state.

Entries follow PRNG return; no allocation, heading helper, lifetime or complete
spawn-reachability claim. Independent assembly checks every temporary stop label.
"""
import re
import struct
import subprocess
from pathlib import Path
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,INPUT

READERS=[(0xA036,0xB43A,8,False),(0xA300,0xB442,4,True),
         (0xA924,0xB43A,8,False),(0xAA6C,0xB442,4,True)]


@pytest.fixture(scope='module')
def launch_labels(tmp_path_factory,original_image):
    target=Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    lines=[];n=0;ground_pending=False
    for line in (target/'starglider2_game.s').read_text().splitlines():
        # Raw and restored spellings denote the same encoded operand.
        low=bool(re.search(r'\bmove\.b #\$64,(?:\$0029|SG2(?:Airborne|Ground)LaunchState_proximity_evasion_countdown_low_byte)\(a2\)',line))
        if ground_pending and line.strip()=='bsr.w recompute_a2_horizontal_motion_from_heading':
            lines.append(f'fixture_launch_stop_{n}:');n+=1;ground_pending=False
        lines.append(line)
        if low:
            if n%2:ground_pending=True
            else:lines.append(f'fixture_launch_stop_{n}:');n+=1
    assert n==4 and not ground_pending
    names=[f'fixture_launch_stop_{i}'for i in range(4)]+[
        'primary_object_update_offsets','update_shared_flying_actor',
        'advance_large_transport_frame_then_update','update_saucer_motion_evasion_and_capsule',
        'model_default_scale_shifts','model_default_durability_bytes','object_default_motion_words',
        'SG2_OBJECT_TYPE_EGRON_SILO','SG2_OBJECT_TYPE_EGRON_DOME_SILO',
        'SG2AirborneLaunchState_proximity_response_countdown']
    folder=tmp_path_factory.mktemp('launch-state');asm,out=folder/'labels.s',folder/'labels.raw'
    asm.write_text('\n'.join(lines)+'\n dc.l '+','.join(names)+'\n')
    r=subprocess.run([str(target.parents[1]/'tools/vasmm68k_mot.exe'),'-quiet','-Fbin','-m68000','-no-opt',
        '-I'+str(target/'includes'),'-o',str(out),str(asm)],cwd=target,capture_output=True,text=True)
    assert r.returncode==0,r.stdout+r.stderr
    raw=out.read_bytes();size=4*len(names);assert raw[:-size]==original_image[0]
    values=dict(zip(names,struct.unpack('>'+'I'*len(names),raw[-size:])))
    assert values['SG2AirborneLaunchState_proximity_response_countdown']==38
    return values


@pytest.mark.parametrize('reader,index,high',[
    (j,i,h)for j,(_,_,count,_)in enumerate(READERS)for i in range(count)for h in [0,1,127,128,255]])
def test_constructor_keeps_partial_word_and_unused_record_bytes(original_image,memory,launch_labels,reader,index,high):
    entry,table,_,ground=READERS[reader];selected=memory[table+index]
    parent,child=INPUT,INPUT+0x100
    memory[parent:parent+68]=b'\x5A'*68;memory[child:child+68]=b'\xA5'*68
    memory[child+40]=high
    for o,v in [(4,123456),(8,0xFFFFA432),(12,987654)]:put(memory,parent+o,v)
    for o,v in [(16,345),(18,0xFEED),(20,2468)]:put(memory,parent+o,v,2)
    expected=bytearray(memory[child:child+68])
    put(expected,0,selected,2);expected[3]=0;expected[42]=launch_labels['SG2_OBJECT_TYPE_EGRON_DOME_SILO'if ground else'SG2_OBJECT_TYPE_EGRON_SILO']
    for off in [4,12]:expected[off:off+4]=bytes(memory[parent+off:parent+off+4])
    expected[32:34]=bytes(memory[launch_labels['object_default_motion_words']+selected*2:
                                           launch_labels['object_default_motion_words']+selected*2+2])
    expected[41]=100;expected[43]=1
    if ground:
        put(expected,8,0xFFFFFFFC if selected==9 and reader==1 else 0xFFFFFFFB)
        expected[16:18]=bytes(memory[parent+16:parent+18]);put(expected,18,(get(memory,parent+18,2)+1024)&65535,2)
        expected[20:22]=bytes(memory[parent+20:parent+22]);put(expected,60,parent)
        expected[2]=(expected[2]|128)&~16;expected[29]=3;expected[30]=255;expected[28]=6
        expected[40]=170
        if selected==9:put(expected,38,100,2);put(expected,36,3,2)
    else:
        expected[29]=memory[launch_labels['model_default_scale_shifts']+selected]
        expected[28]=memory[launch_labels['model_default_durability_bytes']+selected]
        put(expected,36,1022,2);put(expected,38,0,2);put(expected,46,65531,2);put(expected,20,1,2)
    cpu=state(memory,entry);cpu.a[0]=parent;cpu.a[1]=table;cpu.a[2]=child;cpu.d[0]=0xBEEF0000|index
    run(original_image,memory,cpu,{launch_labels[f'fixture_launch_stop_{reader}']},limit=70)
    assert bytes(memory[child:child+68])==expected, (hex(cpu.a[2]),[(i,memory[child+i],v)for i,v in enumerate(expected)if memory[child+i]!=v])
    assert get(memory,child+40,2)==(0xAA64 if ground else (high<<8)|100)


def test_airborne_choices_have_flying_or_saucer_consumers(original_image,memory,launch_labels):
    base=launch_labels['primary_object_update_offsets'];targets={
        launch_labels['update_shared_flying_actor'],launch_labels['advance_large_transport_frame_then_update'],
        launch_labels['update_saucer_motion_evasion_and_capsule']}
    for kind in memory[0xB43A:0xB442]:
        offset=get(memory,base+2*kind,2);offset=offset-65536 if offset&32768 else offset
        assert base+offset in targets
