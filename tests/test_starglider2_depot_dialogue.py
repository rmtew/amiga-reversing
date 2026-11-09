"""Original depot-status continuations with supplied RAM and cursor values.

Stop before display or station handoff. No complete UI, physical cadence,
arbitrary-cursor validity, mission reachability or runtime-state proof.
"""
import itertools
import struct
import subprocess
from pathlib import Path
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,STACK

APP_FIELDS=['current_structure_service_id','professor_taymar_aboard_flag',
    'professor_taymar_delivered_flag','neutron_bomb_order_requested_flag','depot_line_pointer_offset']
GLOBALS=['depot_dialogue_tick','display_event_message_line','display_blank_event_message_line',
    'advance_projector_station_cycle_continuation','service_depot_inventory_or_help_page']
TABLES={0x38E38:5,0x38E50:6,0x38E6C:9,0x38E94:4}


@pytest.fixture(scope='module')
def symbols(tmp_path_factory,original_image):
    target=Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    folder=tmp_path_factory.mktemp('depot-dialogue');asm,out=folder/'symbols.s',folder/'symbols.raw'
    names=APP_FIELDS+GLOBALS;asm.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(names)+'\n')
    result=subprocess.run([str(target.parents[1]/'tools/vasmm68k_mot.exe'),'-quiet','-Fbin','-m68000','-no-opt',
        '-I'+str(target/'includes'),'-o',str(out),str(asm)],cwd=target,text=True,capture_output=True)
    assert result.returncode==0,result.stdout+result.stderr
    data=out.read_bytes();size=4*len(names);assert data[:-size]==original_image[0]
    values=struct.unpack('>'+'I'*len(names),data[-size:])
    return{n:v+(APP if n in APP_FIELDS else 0)for n,v in zip(names,values)}


def enter(memory,symbols,service=2,tick=31):
    put(memory,symbols['current_structure_service_id'],service,2)
    put(memory,symbols['depot_dialogue_tick'],tick,2)
    return state(memory,0x346F2)


@pytest.mark.parametrize('aboard,delivered,order',itertools.product([0,1,127,128,255],repeat=3))
def test_negative_byte_flags_choose_page_with_aboard_then_delivery_priority(original_image,memory,symbols,aboard,delivered,order):
    m=memory
    for name,value in zip(APP_FIELDS[1:4],[aboard,delivered,order]):m[symbols[name]]=value
    put(m,symbols['depot_line_pointer_offset'],0x8877,2)
    cpu=enter(m,symbols);run(original_image,m,cpu,{0x3473C})
    expected=0x38E94 if aboard&128 else 0x38E38 if delivered&128 else 0x38E50 if order&128 else 0x38E6C
    assert cpu.a[1]==expected and get(m,symbols['depot_dialogue_tick'],2)==0
    assert get(m,symbols['depot_line_pointer_offset'],2)==0x8877 and cpu.a[7]==STACK
    assert [m[symbols[n]]for n in APP_FIELDS[1:4]]==[aboard,delivered,order]


@pytest.mark.parametrize('service',[0,1,3,10,65535])
def test_other_service_delegates_before_touching_dialogue_tick(original_image,memory,symbols,service):
    m=memory;cpu=enter(m,symbols,service,0x1234)
    run(original_image,m,cpu,{symbols['service_depot_inventory_or_help_page']})
    assert get(m,symbols['depot_dialogue_tick'],2)==0x1234 and cpu.a[7]==STACK


@pytest.mark.parametrize('tick',[0,1,30,31,32,32767,32768,65535])
def test_word_tick_increments_then_masks_without_a_physical_time_claim(original_image,memory,symbols,tick):
    m=memory;cpu=enter(m,symbols,tick=tick);put(m,symbols['depot_dialogue_tick']+2,0xBEEF,2)
    run(original_image,m,cpu,{0x3473C,symbols['advance_projector_station_cycle_continuation']})
    expected=(tick+1)&31
    assert get(m,symbols['depot_dialogue_tick'],2)==expected
    assert get(m,symbols['depot_dialogue_tick']+2,2)==0xBEEF
    assert cpu.pc==(0x3473C if not expected else symbols['advance_projector_station_cycle_continuation'])


@pytest.mark.parametrize('table,offset',[(t,4*i)for t,n in TABLES.items()for i in range(n+1)]+[(t,i)for t in TABLES for i in [-4,1,65535]])
def test_reader_uses_signed_word_cursor_and_only_ffffffff_resets_it(original_image,memory,symbols,table,offset):
    m=memory;offset &= 65535
    # Odd and negative supplied offsets are aliases, not valid-entry claims.
    signed=offset if offset<32768 else offset-65536;value=get(m,table+signed)
    put(m,symbols['depot_line_pointer_offset'],offset,2);cpu=state(m,0x3473C);cpu.a[1]=table
    run(original_image,m,cpu,{symbols['display_event_message_line'],symbols['display_blank_event_message_line']})
    sentinel=value==0xFFFFFFFF
    assert cpu.pc==symbols['display_blank_event_message_line'if sentinel else'display_event_message_line']
    assert cpu.a[1]==value and cpu.a[7]==STACK-4
    assert get(m,symbols['depot_line_pointer_offset'],2)==(0 if sentinel else offset)


@pytest.mark.parametrize('offset',[0,1,32767,65531,65532,65535])
def test_after_display_continuation_advances_word_by_four(original_image,memory,symbols,offset):
    m=memory;put(m,symbols['depot_line_pointer_offset'],offset,2)
    put(m,symbols['depot_line_pointer_offset']+2,0xBEEF,2)
    cpu=state(m,0x3475C);run(original_image,m,cpu,{symbols['advance_projector_station_cycle_continuation']})
    assert get(m,symbols['depot_line_pointer_offset'],2)==(offset+4)&65535
    assert get(m,symbols['depot_line_pointer_offset']+2,2)==0xBEEF and cpu.a[7]==STACK
