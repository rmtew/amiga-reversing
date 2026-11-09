"""Original inventory continuations with supplied RAM, lists and command states.

Stop before the display call; do not infer input-device delivery, complete UI
execution, capture eligibility, buffer capacity or normal-game reachability.
Deliberately dense/long supplied cases retain original shared-scratch aliases.
"""
import struct
import subprocess
from pathlib import Path
import pytest
from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, INPUT, STACK, RETURN

APP_FIELDS = ['shared_inventory_depot_message_pointers', 'inventory_list_quantity_prefix',
    'inventory_quantity_decimal_prefix', 'inventory_list_model_type_prefix', 'inventory_line_text_start',
    'depot_line_pointer_offset', 'inventory_list_item_index', 'model_type_population_counts',
    'icarus_power_reserve', 'weapon_energy_reserve', 'icarus_shield_strength']
GLOBALS = ['build_depot_inventory_status_lists', 'reset_shared_inventory_scratch_prefixes',
    'display_event_message_line', 'advance_projector_station_cycle_continuation',
    'object_name_pointers', 'depot_inventory_mode_flag', 'event_message_pointers']


@pytest.fixture(scope='module')
def symbols(tmp_path_factory, original_image):
    target = Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    temp = tmp_path_factory.mktemp('inventory-interface-symbols'); asm, out = temp/'fields.s', temp/'fields.raw'
    names = APP_FIELDS + GLOBALS
    asm.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(names)+'\n')
    r = subprocess.run([str(target.parents[1]/'tools/vasmm68k_mot.exe'), '-quiet', '-Fbin', '-m68000', '-no-opt',
        '-I'+str(target/'includes'), '-o', str(out), str(asm)], cwd=target, text=True, capture_output=True)
    assert r.returncode == 0, r.stdout+r.stderr
    data = out.read_bytes(); size = 4*len(names); assert data[:-size] == original_image[0]
    values = struct.unpack('>'+'I'*len(names), data[-size:])
    return {n: v+(APP if n in APP_FIELDS else 0)for n,v in zip(names,values)}


def name_pointer(memory, symbols, kind): return get(memory, symbols['object_name_pointers']+4*kind)


def cstring(memory, address):
    result = bytearray()
    for i in range(128):
        v = memory[address+i]
        if not v: return bytes(result)
        result.append(v)
    pytest.fail('Supplied text has no bounded NUL')


def selected(memory, symbols, kinds, quantities, index=0):
    pointers = symbols['shared_inventory_depot_message_pointers']; qty = symbols['inventory_list_quantity_prefix']
    tags = symbols['inventory_list_model_type_prefix']; line = symbols['inventory_line_text_start']
    memory[line-1:line+96] = b'\xCC'*97
    for i,(kind,count)in enumerate(zip(kinds,quantities)):
        put(memory,pointers+4*i,name_pointer(memory,symbols,kind));memory[qty+i]=count;memory[tags+i]=kind
    put(memory,pointers+4*len(kinds),0xFFFFFFFF)
    put(memory,symbols['depot_line_pointer_offset'],4*index,2);put(memory,symbols['inventory_list_item_index'],index,2)


def display(image,memory,symbols,entry=0x347D4,key=None):
    cpu = state(memory,entry)
    if key is not None:cpu.d[0]=key
    run(image,memory,cpu,{symbols['display_event_message_line'],symbols['advance_projector_station_cycle_continuation']})
    return cpu


def line_for(name,count,previous=ord('X')):
    plural = name if (name[-1]if name else previous)==ord('s')else name+b's'
    return plural+b': '+str(count).encode()+b'\0'


@pytest.mark.parametrize('kind',range(104))
def test_original_name_prefix_and_unsigned_quantity_execute_real_decimal_formatter(original_image,memory,symbols,kind):
    name = cstring(memory,name_pointer(memory,symbols,kind));selected(memory,symbols,[kind],[255])
    line = symbols['inventory_line_text_start'];expected = line_for(name,255)
    before, after = memory[line-1],memory[line+len(expected)]
    cpu=display(original_image,memory,symbols)
    assert cpu.pc==symbols['display_event_message_line'] and cpu.a[1]==line and cpu.a[7]==STACK-4
    assert bytes(memory[line:line+len(expected)])==expected
    assert memory[line-1]==before and memory[line+len(expected)]==after
    if kind==86:  # 25-byte name + plural/punctuation/quantity/NUL spans32 bytes.
        qty=symbols['inventory_list_quantity_prefix']
        assert qty-line==30 and memory[qty]==ord('5') and memory[qty+1]==0


@pytest.mark.parametrize('name',[b'Whale',b'Glass',b'GAS',b'',b'X'])
@pytest.mark.parametrize('count',[0,1,10,127,255])
@pytest.mark.parametrize('previous',[ord('s'),ord('X')])
def test_plural_rule_ignores_quantity_and_empty_name_reads_previous_byte(original_image,memory,symbols,name,count,previous):
    selected(memory,symbols,[0],[count]);memory[INPUT:INPUT+len(name)+1]=name+b'\0'
    put(memory,symbols['shared_inventory_depot_message_pointers'],INPUT)
    line=symbols['inventory_line_text_start'];memory[line-1]=previous
    expected=line_for(name,count,previous);display(original_image,memory,symbols)
    assert bytes(memory[line:line+len(expected)])==expected


@pytest.mark.parametrize('kinds', [[],[12],[12,91,98,84],[3,24,86]])
def test_builder_descends_all_nonzero_types_and_keeps_model_tag_suffix(original_image,memory,symbols,kinds):
    counts=symbols['model_type_population_counts'];memory[counts:counts+104]=bytes(104)
    for i,k in enumerate(kinds):memory[counts+k]=[1,2,127,255][i%4]
    p,q,t=[symbols[n]for n in ['shared_inventory_depot_message_pointers','inventory_list_quantity_prefix','inventory_list_model_type_prefix']]
    memory[p:p+40]=b'\xCC'*40;memory[q:q+10]=b'\xCC'*10;memory[t:t+10]=b'\xCC'*10
    cpu=state(memory,symbols['build_depot_inventory_status_lists']);run(original_image,memory,cpu,{RETURN})
    order=sorted(kinds,reverse=True)
    assert [get(memory,p+4*i)for i in range(len(order))]==[name_pointer(memory,symbols,k)for k in order]
    assert bytes(memory[q:q+len(order)])==bytes(memory[counts+k]for k in order)
    assert bytes(memory[t:t+len(order)])==bytes(order)
    assert get(memory,p+4*len(order))==0xFFFFFFFF and memory[q+len(order)]==255
    assert memory[t+len(order)]==0xCC and cpu.a[7]==STACK+4


def test_dense_supplied_list_retains_real_cross_prefix_writes(original_image,memory,symbols):
    counts=symbols['model_type_population_counts'];memory[counts:counts+104]=bytes(104)
    for k in range(1,24):memory[counts+k]=1
    p=symbols['shared_inventory_depot_message_pointers'];line=symbols['inventory_line_text_start']
    assert p+23*4==line
    cpu=state(memory,symbols['build_depot_inventory_status_lists']);run(original_image,memory,cpu,{RETURN})
    assert [get(memory,p+4*i)for i in range(23)]==[name_pointer(memory,symbols,k)for k in range(23,0,-1)]
    assert get(memory,line)==0xFFFFFFFF
    assert bytes(memory[symbols['inventory_quantity_decimal_prefix']:symbols['inventory_quantity_decimal_prefix']+10])==b'\1'*10
    assert get(memory,symbols['inventory_list_item_index'],2)==0x0908


@pytest.mark.parametrize('enter',[False,True])
@pytest.mark.parametrize('size',[1,2,3])
def test_i_advances_before_display_and_wraps_on_pointer_sentinel(original_image,memory,symbols,enter,size):
    kinds=[12,11,3][:size];qty=[1,2,3][:size];selected(memory,symbols,kinds,qty)
    cpu=display(original_image,memory,symbols,0x3492C if enter else 0x3478C,ord('I'))
    index=1 if size>1 else 0
    assert get(memory,symbols['depot_line_pointer_offset'],2)==4*index
    assert get(memory,symbols['inventory_list_item_index'],2)==index
    expected=line_for(cstring(memory,name_pointer(memory,symbols,kinds[index])),qty[index])
    line=symbols['inventory_line_text_start'];assert bytes(memory[line:line+len(expected)])==expected
    if enter:assert memory[symbols['depot_inventory_mode_flag']]==255
    assert cpu.pc==symbols['display_event_message_line']


@pytest.mark.parametrize('kind',[12,91,98,84])
def test_give_refuses_the_four_special_inventory_types_without_recharging(original_image,memory,symbols,kind):
    selected(memory,symbols,[kind],[1]);counts=symbols['model_type_population_counts']
    memory[counts:counts+104]=bytes(104);memory[counts+kind]=1;memory[counts+3]=1
    for n in ['icarus_power_reserve','weapon_energy_reserve','icarus_shield_strength']:put(memory,symbols[n],123,2)
    display(original_image,memory,symbols,0x34866)
    assert memory[counts+kind]==1 and memory[symbols['inventory_list_quantity_prefix']]==1
    assert all(get(memory,symbols[n],2)==123 for n in ['icarus_power_reserve','weapon_energy_reserve','icarus_shield_strength'])


@pytest.mark.parametrize('owned,quantity',[(0,0),(1,1),(2,255),(128,128),(129,129),(255,255)])
def test_give_debits_with_n_only_clamps_then_refills_even_a_stale_selected_zero(original_image,memory,symbols,owned,quantity):
    selected(memory,symbols,[24],[quantity]);counts=symbols['model_type_population_counts']
    memory[counts:counts+104]=bytes(104);memory[counts+24]=owned;memory[counts+3]=1
    for n,v in zip(['icarus_power_reserve','weapon_energy_reserve','icarus_shield_strength'],[10,65000,65535]):put(memory,symbols[n],v,2)
    display(original_image,memory,symbols,0x34866)
    dec=lambda v:0 if((v-1)&255)&128 else(v-1)&255
    assert memory[counts+24]==dec(owned) and memory[symbols['inventory_list_quantity_prefix']]==dec(quantity)
    assert [get(memory,symbols[n],2)for n in ['icarus_power_reserve','weapon_energy_reserve','icarus_shield_strength']]==[2058,65535,65535]


@pytest.mark.parametrize('amount',[0,1,2048,32768,65535])
@pytest.mark.parametrize('old',[0,1,32768,65534,65535])
def test_shared_reserve_helper_adds_unsigned_word_with_independent_saturation(original_image,memory,symbols,amount,old):
    names=['icarus_power_reserve','weapon_energy_reserve','icarus_shield_strength'];values=[old,old^65535,(old+1)&65535]
    for n,v in zip(names,values):put(memory,symbols[n],v,2)
    cpu=state(memory,0x33D80);cpu.d[3]=0xCAFE0000|amount;before_d,before_a=list(cpu.d),list(cpu.a)
    run(original_image,memory,cpu,{RETURN})
    assert [get(memory,symbols[n],2)for n in names]==[min(65535,v+amount)for v in values]
    assert list(cpu.d)[1:]==before_d[1:] and list(cpu.a)[:7]==before_a[:7] and cpu.a[7]==STACK+4


def test_i_word_wrap_and_independent_pointer_quantity_indices(original_image,memory,symbols):
    selected(memory,symbols,[12,11],[1,2])
    put(memory,symbols['depot_line_pointer_offset'],65532,2);put(memory,symbols['inventory_list_item_index'],65535,2)
    display(original_image,memory,symbols,0x3478C,ord('I'))
    assert get(memory,symbols['depot_line_pointer_offset'],2)==0 and get(memory,symbols['inventory_list_item_index'],2)==0
    selected(memory,symbols,[12,11],[1,2])
    put(memory,symbols['depot_line_pointer_offset'],4,2)
    display(original_image,memory,symbols)
    expected=line_for(cstring(memory,name_pointer(memory,symbols,11)),1)
    line=symbols['inventory_line_text_start'];assert bytes(memory[line:line+len(expected)])==expected


def test_scratch_reset_touches_only_its_four_observed_prefixes(original_image,memory,symbols):
    regions=[(symbols['shared_inventory_depot_message_pointers'],40)]+[(symbols[n],10)for n in
        ['inventory_quantity_decimal_prefix','inventory_list_quantity_prefix','inventory_list_model_type_prefix']]
    for p,n in regions:memory[p-1:p+n+1]=b'\xCC'*(n+2)
    cpu=state(memory,symbols['reset_shared_inventory_scratch_prefixes']);run(original_image,memory,cpu,{RETURN})
    for p,n in regions:
        assert bytes(memory[p:p+n])==b'\xFF'*n and memory[p-1]==memory[p+n]==0xCC
    assert cpu.a[7]==STACK+4


@pytest.mark.parametrize('pointer_index,item_index',[(0,0),(4,1),(65532,65535)])
def test_exit_inventory_clears_mode_and_both_cursors(original_image,memory,symbols,pointer_index,item_index):
    memory[symbols['depot_inventory_mode_flag']]=255
    put(memory,symbols['depot_line_pointer_offset'],pointer_index,2);put(memory,symbols['inventory_list_item_index'],item_index,2)
    cpu=display(original_image,memory,symbols,0x3478C,ord('E'))
    assert cpu.pc==symbols['advance_projector_station_cycle_continuation'] and cpu.a[7]==STACK
    assert memory[symbols['depot_inventory_mode_flag']]==0
    assert get(memory,symbols['depot_line_pointer_offset'],2)==get(memory,symbols['inventory_list_item_index'],2)==0
