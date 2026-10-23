"""Original restart dataflow and bounded PRNG arithmetic, without DMA emulation."""
import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_render_order import sequencer

pytestmark = pytest.mark.parametrize("cpu_fixture", [0x1000000], indirect=True)

APP = 0x39FC


def step_random(history, shift):
    for _ in range(32):
        feedback = ((shift >> 3) ^ history) & 1
        history = (history & 0xFFFFFF00) | (0xFF if shift & 0x80000000 else 0)
        shift = ((shift << 1) | feedback) & 0xFFFFFFFF
    return history, shift


def test_random_recurrence_retains_high_history_bytes_and_preserved_registers(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    states = [0, 1, 2, 8, 0x80000000, 0xFFFFFFFF, 0x12345678, 0xDA0597A3]
    for history in states:
        for shift in states:
            write(0x7E8, history)
            write(0x7EC, shift)
            for i in range(8):
                cpu.d[i] = 0xCAFE0000+i
                if i < 7:cpu.a[i] = 0xBEEF0000+i
            before_d, before_a = list(cpu.d), list(cpu.a[:7])
            expected = step_random(history, shift)
            run(0x2FD8, budget=512)
            assert (read(0x7E8), read(0x7EC)) == expected
            assert cpu.d[0] == cpu.d[1] == expected[1] and cpu.a[0] == 0x7E8
            assert list(cpu.d[2:]) == before_d[2:] and list(cpu.a[1:7]) == before_a[1:]
            assert cpu.a[7] == 0x9004
            assert read(0x7E8) & 0xFFFFFF00 == history & 0xFFFFFF00
            assert read(0x7EB,1) == (0xFF if shift & 1 else 0)


def test_random_stream_repeats_exactly_from_same_two_longwords(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    for initial in [(0,0), (0,1), (1,0), (0x67FD67FD,0xE432A55A)]:
        expected = initial
        for _ in range(64):
            write(0x7E8,expected[0]);write(0x7EC,expected[1])
            expected = step_random(*expected)
            run(0x2FD8,budget=512)
            assert (read(0x7E8),read(0x7EC)) == expected
        if initial==(0,0):assert expected==(0,0)


@pytest.mark.parametrize('old_tail',[0,1,0x55AA,0xFFFF])
def test_beam_seed_writes_six_bytes_then_falls_through_one_random_step(cpu_fixture,old_tail):
    cpu, memory, schemas, read, write, run = cpu_fixture
    seeds=[0x67FDE432,0x95429168,0xDA0597A3,0x54FFA672]
    for beam in [*range(16),0x1234,0xABCD,0xFFFF]:
        write(0xDFF006,beam,2)
        write(0x7E8,0xDEADBEEF);write(0x7EC,0xAA550000|old_tail)
        write(0x7E7,0x5A,1);write(0x7F0,0xA5,1)
        seed=seeds[(beam&12)>>2]
        run(0x2FC2,stop=0x2FD8)
        seeded=bytes(memory[0x7E8:0x7F0])
        assert seeded==seed.to_bytes(4,'big')[:2]+seed.to_bytes(4,'big')+old_tail.to_bytes(2,'big')
        initial=(read(0x7E8),read(0x7EC))
        run(0x2FD8,budget=512)
        assert (read(0x7E8),read(0x7EC)) == step_random(*initial)
        assert read(0x7E7,1)==0x5A and read(0x7F0,1)==0xA5
        # Entering the seed entry normally includes the same advance, not a return at +$16.
        write(0x7E8,0xDEADBEEF);write(0x7EC,0xAA550000|old_tail)
        run(0x2FC2,budget=512)
        assert (read(0x7E8),read(0x7EC)) == step_random(*initial)


def test_full_original_world_reset_restores_all_35_objects_but_not_random_state(cpu_fixture,title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    obj=schemas['world_object_shared_prefix']
    objects=[]
    for i in range(36):
        pointer=read(BASE+0x300A+4*i)
        if not pointer:break
        objects.append(pointer)
    assert len(objects)==35
    sources=set()
    for p in objects:
        sources.update(range(read(p+obj['initial_inventory_slots_ptr']),read(p+obj['initial_inventory_slots_ptr'])+8))
        sources.update(range(read(p+obj['initial_trade_offer_table_ptr']),read(p+obj['initial_trade_offer_table_ptr'])+8))
    expected=[]
    for i,p in enumerate(objects):
        write(p+obj['world_object_flags'],read(p+obj['initial_world_object_flags'],1),1)
        record={}
        for coordinate,value in [('world_x',0x5000+i),('world_y',0x6000+i)]:
            write(p+obj[coordinate],value,2)
            record[coordinate]=((241 if coordinate=='world_x' else 866) if p==BASE+0x4C322 else value,2)
        for current,initial,size in [('selected_item_id','initial_selected_item_id',1),('item_state','initial_item_state',1),('hit_points','initial_hit_points',2),('behavior_script_ptr','initial_behavior_script_ptr',4)]:
            record[current]=(read(p+obj[initial],size),size)
            write(p+obj[current],(1<<(size*8))-1,size)
        write(p+obj['behavior_script_delay_ticks'],0x1234,2)
        for current,initial in [('inventory_slots_ptr','initial_inventory_slots_ptr'),('trade_offer_table_ptr','initial_trade_offer_table_ptr')]:
            dest,source=read(p+obj[current]),read(p+obj[initial])
            record[current]=(dest,bytes(memory[source:source+8]))
            if not any(a in sources for a in range(dest,dest+8)):memory[dest:dest+8]=bytes([0xA5])*8
        expected.append(record)
    random_before=bytes.fromhex('0123456789ABCDEF');memory[0x7E8:0x7F0]=random_before
    cpu.a[6]=APP;cpu.a[5]=0xABCDEF
    assert sequencer(cpu,memory,write)(0x9F26,budget=50000).stop_reason == 1
    assert cpu.a[5]==0xABCDEF and cpu.a[7]==0x9004
    assert memory[0x7E8:0x7F0]==random_before
    for p,record in zip(objects,expected,strict=True):
        for current,(value,size) in record.items():
            if current.endswith('_ptr') and isinstance(size,bytes):assert bytes(memory[value:value+8])==size
            else:assert read(p+obj[current],size)==value
        assert read(p+obj['behavior_script_delay_ticks'],2)==0
        assert read(p+obj['world_object_flags'],1)==read(p+obj['initial_world_object_flags'],1)
    assert read(APP+title_slots['app_self_destruct_service_ticks_remaining'],2)==3000
    assert read(APP+title_slots['app_earth_orbit_countdown_bcd'],2)==0x9999
    assert read(APP+title_slots['app_earth_orbit_countdown_divider'],1)==1
    assert read(APP+title_slots['active_world_object_count'],2)==67
    assert read(APP+title_slots['app_tilemap_scroll_y'],2)==51*16
    assert read(BASE+0x4C322+obj['world_x'],2)==241
    assert read(BASE+0x4C322+obj['world_y'],2)==866


def test_restart_object_copies_are_forward_bytes_even_for_overlapping_inputs(cpu_fixture):
    cpu,memory,schemas,read,write,run=cpu_fixture
    obj=schemas['world_object_shared_prefix'];p=0x81000
    write(0x80000,p);write(0x80004,0)
    for field,value in [('item_definition_id',7),('initial_selected_item_id',13),('initial_item_state',39)]:write(p+obj[field],value,1)
    write(p+obj['initial_hit_points'],95,2)
    write(p+obj['initial_behavior_script_ptr'],0x12345678)
    for field,value in [('initial_inventory_slots_ptr',0x82000),('inventory_slots_ptr',0x82001),('initial_trade_offer_table_ptr',0x83001),('trade_offer_table_ptr',0x83000)]:write(p+obj[field],value)
    memory[0x82000:0x8200A]=bytes(range(1,11));memory[0x83000:0x8300A]=bytes(range(11,21))
    cpu.a[1]=0x80000;cpu.a[6]=APP
    run(0xA0B8,stop=0xA12E,budget=512)
    assert memory[0x82000:0x82009]==bytes([1])*9 and read(0x82009,1)==10
    assert memory[0x83000:0x83008]==bytes(range(12,20)) and read(0x83008,1)==19
    assert cpu.a[1]==0x80008
    for field,value,size in [('selected_item_id',13,1),('item_state',39,1),('hit_points',95,2),('behavior_script_ptr',0x12345678,4),('behavior_script_delay_ticks',0,2)]:assert read(p+obj[field],size)==value


def test_empty_restart_object_table_stops_after_one_null_read(cpu_fixture):
    cpu,memory,schemas,read,write,run=cpu_fixture
    write(0x80000,0);memory[0x81000:0x81054]=bytes([0xA5])*84
    cpu.a[1]=0x80000;cpu.a[5]=0x81000
    assert run(0xA0B8,stop=0xA12E)==2
    assert cpu.a[1]==0x80004 and cpu.a[5]==0x81000
    assert memory[0x81000:0x81054]==bytes([0xA5])*84


def test_cursor_seed_rows_deinterleave_first_eight_bytes_of_each_sixteen_byte_group(cpu_fixture):
    cpu,memory,schemas,read,write,run=cpu_fixture
    cpu.a[6]=APP
    run(0x9EF2,stop=0x9F06)
    source=cpu.a[0]
    memory[source:source+256]=bytes(range(256))
    write(0x65370,0xA55A1234);write(0x653B4,0x9876ABCD)
    run(0x9F06,stop=0x9F18,budget=512)
    assert bytes(memory[0x65374:0x653B4])==b''.join(bytes(range(i,i+4)) for i in range(0,256,16))
    assert bytes(memory[0x653B8:0x653F8])==b''.join(bytes(range(i+4,i+8)) for i in range(0,256,16))
    assert read(0x65370)==0xA55A1234 and read(0x653B4)==0x9876ABCD
    assert (cpu.a[0],cpu.a[1],cpu.a[2])==(source+256,0x653B4,0x653F8)


def test_random_output_ignores_all_history_bits_except_bit_zero(cpu_fixture):
    cpu,memory,schemas,read,write,run=cpu_fixture
    for low_bit in [0,1]:
        outputs=[]
        for high_bits in [0,2,0xFE,0x12345600,0xFFFFFFFE]:
            write(0x7E8,high_bits|low_bit);write(0x7EC,0x13579BDF)
            run(0x2FD8,budget=512);outputs.append(cpu.d[0])
        assert len(set(outputs))==1
