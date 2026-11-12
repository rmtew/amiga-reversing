"""Original pirate raid stages; local inputs are not ordinary-play/save proofs.

Start after PRNG return where stated. No random-state reachability, free-slot
ownership, complete actor update or immutable source-table invariant follows.
"""
import struct
import subprocess
from pathlib import Path
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,INPUT

PARENT,CHILD,FREE=INPUT,INPUT+0x100,INPUT+0x300


@pytest.fixture(scope='module')
def fields(tmp_path_factory,original_image):
    target=Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    names=['free_object_count','free_object_stack_cursor','model_type_population_counts',
           'neutron_bomb_ingredient_model_types','projector_rebuild_part_types',
           'pirate_destruction_drop_choices','SG2PirateShip_raid_attempt_mod8_index']
    folder=tmp_path_factory.mktemp('pirate');asm,out=folder/'map.s',folder/'map.raw'
    asm.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(names)+'\n')
    result=subprocess.run([str(target.parents[1]/'tools/vasmm68k_mot.exe'),'-quiet','-Fbin','-m68000','-no-opt',
        '-I'+str(target/'includes'),'-o',str(out),str(asm)],cwd=target,capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    raw=out.read_bytes();tail=4*len(names);assert raw[:-tail]==original_image[0]
    return dict(zip(names,struct.unpack('>'+'I'*len(names),raw[-tail:])))


def prepare(memory,fields,free=21):
    put(memory,APP+fields['free_object_count'],free,2)
    put(memory,APP+fields['free_object_stack_cursor'],FREE+4);put(memory,FREE,CHILD)
    memory[PARENT:PARENT+68]=b'\x5A'*68;memory[CHILD:CHILD+68]=b'\xA5'*68


@pytest.mark.parametrize('x',[0,999,1000,0x7fffffff,0x80000000,0xffffffff])
@pytest.mark.parametrize('y',[0,999,1000,0x7fffffff,0x80000000,0xffffffff])
@pytest.mark.parametrize('z',[0,999,1000,0x7fffffff,0x80000000,0xffffffff])
def test_raid_distance_gates_use_result_sign_not_signed_order(original_image,memory,x,y,z):
    cpu=state(memory,0x36E58);cpu.d[0],cpu.d[1],cpu.d[2]=x,y,z
    run(original_image,memory,cpu,{0x36E70,0x37042})
    negative=lambda v:bool(((v-1000)&0xffffffff)&0x80000000)
    expected=not negative(x)and negative(y)and negative(z)
    assert cpu.pc==(0x36E70 if expected else 0x37042)


@pytest.mark.parametrize('phase',list(range(16))+[32767,65535])
def test_raid_attempt_counter_masks_before_random_gate(original_image,memory,fields,phase):
    prepare(memory,fields);address=PARENT+fields['SG2PirateShip_raid_attempt_mod8_index'];put(memory,address,phase,2)
    cpu=state(memory,0x36E70);cpu.a[0]=PARENT
    run(original_image,memory,cpu,{0x36E7E,0x3703E})
    expected=(phase+1)&7
    assert get(memory,address,2)==expected and cpu.pc==(0x36E7E if expected==0 else 0x3703E)


@pytest.mark.parametrize('result',[0,1,7,8,255,256,0x12340000,0xffffffff])
@pytest.mark.parametrize('free',[0,20,21,65535])
def test_first_random_gate_and_unsigned_free_threshold_precede_selection(original_image,memory,fields,result,free):
    prepare(memory,fields,free);cpu=state(memory,0x36E82);cpu.d[0]=result
    run(original_image,memory,cpu,{0x36E94,0x36F84})
    assert cpu.pc==(0x36E94 if(result&7)==0 and free>20 else 0x36F84)
    assert get(memory,APP+fields['free_object_count'],2)==free
    assert get(memory,APP+fields['free_object_stack_cursor'])==FREE+4


@pytest.mark.parametrize('choice',range(8))
@pytest.mark.parametrize('quantity',[0,1,128,255])
def test_doubled_byte_selector_crosses_into_next_owner_and_can_publish_zero_tag(original_image,memory,fields,choice,quantity):
    prepare(memory,fields);base=fields['neutron_bomb_ingredient_model_types']
    assert fields['projector_rebuild_part_types']==base+8
    selected=memory[base+2*choice]
    assert selected==([102,100,29,38,0,0,0,0][choice])
    inventory=APP+fields['model_type_population_counts'];memory[inventory:inventory+104]=bytes(104);memory[inventory+selected]=quantity
    cpu=state(memory,0x36EA2);cpu.a[0],cpu.a[1]=PARENT,inventory;cpu.d[0]=0xABCDFFF8|choice
    before=bytes(memory[CHILD:CHILD+68])
    run(original_image,memory,cpu,{0x36F84,0x36ECE})
    expected=bytearray(before)
    if quantity:expected[:2]=selected.to_bytes(2,'big')
    assert bytes(memory[CHILD:CHILD+68])==expected
    assert cpu.pc==(0x36ECE if quantity else 0x36F84)
    assert get(memory,APP+fields['free_object_count'],2)==(20 if quantity else 21)
    assert get(memory,APP+fields['free_object_stack_cursor'])==(FREE if quantity else FREE+4)
    assert memory[inventory+selected]==quantity  # Decrement belongs to a later stage.


@pytest.mark.parametrize('choice',range(16))
@pytest.mark.parametrize('free',[20,21])
@pytest.mark.parametrize('velocity',[(16,0xffeb,40),(0x8000,0x7fff,0xffff)])
def test_loot_prefix_keeps_three_stores_to_x_and_other_child_bytes(original_image,memory,fields,choice,free,velocity):
    prepare(memory,fields,free)
    for off,value in [(4,123456),(8,0xffffa123),(12,654321)]:put(memory,PARENT+off,value)
    for off,value in zip([44,46,48],velocity):put(memory,PARENT+off,value,2)
    parent=bytes(memory[PARENT:PARENT+68]);expected=bytearray(memory[CHILD:CHILD+68])
    selected=memory[fields['pirate_destruction_drop_choices']+choice]
    admitted=selected!=0 and free>20
    if admitted:
        expected[:2]=selected.to_bytes(2,'big');expected[60:64]=b'\xff'*4;expected[4:16]=parent[4:16]
        signed_z=velocity[2]-(65536 if velocity[2]&32768 else 0)
        expected[44:46]=((signed_z>>2)&65535).to_bytes(2,'big')
    cpu=state(memory,0x37056);cpu.a[0],cpu.a[1]=PARENT,fields['pirate_destruction_drop_choices'];cpu.d[0]=choice
    run(original_image,memory,cpu,{0x37114,0x370B8})
    assert bytes(memory[CHILD:CHILD+68])==expected
    assert bytes(memory[PARENT:PARENT+68])==parent
    assert get(memory,APP+fields['free_object_count'],2)==(free-1 if admitted else free)
    assert get(memory,APP+fields['free_object_stack_cursor'])==(FREE if admitted else FREE+4)
