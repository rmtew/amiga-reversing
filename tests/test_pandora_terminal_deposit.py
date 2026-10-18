"""Original terminal deposit admission, storage and ID recheck in controlled RAM.

Real code and callees, explicit MMIO shadows, no DMA or ordinary route claim.
The 64-byte declaration is a physical prefix, not a runtime scan bound.
"""
import pytest

from tests.test_pandora_state_transitions import BASE,cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_message_queue import initialize,APP,HEAD,TAIL,CONTEXT
from tests.test_pandora_render_order import sequencer

pytestmark=pytest.mark.parametrize('cpu_fixture',[0x1000000],indirect=True)
PLAYER,DESCRIPTOR,STATE,GEOMETRY=0x5c322,0x591ee,0x591fa,0x591dc


@pytest.fixture
def deposit(cpu_fixture,title_slots):
    cpu,memory,schemas,read,write,run=cpu_fixture
    slots,obj=title_slots,schemas['world_object_shared_prefix']
    cpu.a[6]=APP;cpu.d[0]=0
    assert sequencer(cpu,memory,write)(0x4d7de,budget=4096).stop_reason==1
    def app(name,value,size=1):write(APP+slots['app_'+name],value,size)
    def value(name,size=1):return read(APP+slots['app_'+name],size)
    def prepare(item=54,occupancy=16):
        initialize(cpu_fixture,slots,occupancy)
        for index in range(occupancy):write(APP+HEAD+4*index,0x5ccf5)
        app('context_flags',32);app('game_event_flags',0);app('salvage_item_count',0)
        app('input_fire_pressed_ff',255);app('ranged_weapon_fire_latched',0)
        app('font_glyph_bitmap_table_ptr',BASE+0xa7e2,4)
        for field,bank in [('front_bitplane_base',0x78000),('back_bitplane_base',0x70000),('display_bitplane_base',0x78000)]:app(field,bank,4)
        memory[APP+slots['app_terminal_deposited_item_ids']:APP+slots['app_terminal_deposited_item_ids']+66]=bytes(66)
        memory[APP+slots['app_carried_item_ids']:APP+slots['app_carried_item_ids']+4]=bytes(4)
        memory[APP+slots['app_pocket_item_ids']:APP+slots['app_pocket_item_ids']+4]=bytes(4)
        write(PLAYER+obj['world_x'],148,2);write(PLAYER+obj['world_y'],964,2)
        write(PLAYER+obj['world_object_flags'],0,1);write(PLAYER+obj['selected_item_id'],item,1)
        write(PLAYER+obj['hit_points'],95,2);write(0xdff01e,0x40,2)
        cpu.a[4],cpu.a[5],cpu.a[6]=PLAYER,PLAYER,APP
    def call(source=0x8984,stop=None,budget=20000):
        t=sequencer(cpu,memory,write)(source,stop=stop,budget=budget)
        assert t.stop_reason==1 and t.steps<budget
        return t
    prepare()
    return cpu,memory,schemas,read,write,slots,obj,app,value,prepare,call


def test_original_marker_has_exact_frame_descriptor_and_26_byte_render_prefix(deposit):
    cpu,memory,schemas,read,write,slots,obj,app,v,prepare,call=deposit
    assert read(DESCRIPTOR)==STATE and read(STATE)==read(STATE+4)==GEOMETRY
    assert [read(DESCRIPTOR+i,2) for i in [4,6,8,10]]==[148,964,148,964]
    assert read(STATE+8)==read(STATE+12)==read(STATE+20)==0
    assert read(STATE+16)==DESCRIPTOR and read(STATE+24,2)==0
    assert [read(GEOMETRY+i,2) for i in [8,10,12,14,16]]==[2,32,32,0,0]
    assert GEOMETRY+18==DESCRIPTOR and DESCRIPTOR+12==STATE and STATE+26==0x59214


def test_all_gate_bytes_and_selected_ids_stop_before_storage_or_enter_scan(deposit):
    cpu,memory,schemas,read,write,slots,obj,app,v,prepare,call=deposit
    for domain in ['fire','ui','flags','item']:
        for value in range(256):
            prepare(value if domain=='item' else 54)
            if domain=='flags':write(PLAYER+obj['world_object_flags'],value,1)
            elif domain!='item':app('input_fire_pressed_ff' if domain=='fire' else 'ui_flags',value)
            admitted=bool(value) if domain=='fire' else not value&6 if domain=='ui' else not value&2 if domain=='flags' else value>=2
            call(stop=0x89da if admitted else None,budget=128)
            assert read(PLAYER+obj['selected_item_id'],1)==(value if domain=='item' else 54)
            assert v('salvage_item_count')==0
            assert read(APP+slots['app_terminal_deposited_item_ids'],1)==0


def test_word_distance_boundaries_and_wrapped_sum_are_not_geometric_clamps(deposit):
    cpu,memory,schemas,read,write,slots,obj,app,v,prepare,call=deposit
    for axis,center in [('world_x',148),('world_y',964)]:
        for delta in [-32768,-32767,-25,-24,-23,-1,0,1,23,24,25,32767]:
            prepare();write(PLAYER+obj[axis],(center+delta)&65535,2)
            call(stop=0x89da if abs(delta)<24 else None,budget=128)
    for dx,dy in [(12,11),(12,12),(32768,32768),(32767,32768),(32768,32767)]:
        prepare();write(PLAYER+obj['world_x'],(148+dx)&65535,2);write(PLAYER+obj['world_y'],(964+dy)&65535,2)
        magnitude=lambda n: min(n&65535,(-n)&65535)
        admitted=(magnitude(dx)+magnitude(dy))&65535<24
        call(stop=0x89da if admitted else None,budget=128)


def test_all_deposit_bytes_use_the_original_adjacent_bit_lookup_and_count_wrap(deposit):
    cpu,memory,schemas,read,write,slots,obj,app,v,prepare,call=deposit
    bits=bytes(memory[BASE+0xa813:BASE+0xa833])
    assert len(bits)==32  # Only the first15 bytes belong to the salvage bitset.
    start=APP+slots['app_terminal_deposited_item_ids']
    for item in range(2,256):
        prepare(item);app('salvage_item_count',255)
        call(stop=0x89fa,budget=256)
        eligible=bool(bits[item//8]&(128>>(item%8)))
        assert read(start,1)==item and read(start+1,1)==0
        assert read(PLAYER+obj['selected_item_id'],1)==0
        assert v('salvage_item_count')==(0 if eligible else 255)
        assert v('context_flags')==48
    # IDs120..255 are explicit injected values, not normal item acquisition.


def test_scan_crosses_declared_prefix_into_cache_and_fire_latch_when_supplied_full(deposit):
    cpu,memory,schemas,read,write,slots,obj,app,v,prepare,call=deposit
    start=APP+slots['app_terminal_deposited_item_ids']
    assert start+64==APP+slots['app_modal_last_selected_item_id']
    assert start+65==APP+slots['app_ranged_weapon_fire_latched']
    for occupied in [0,1,63,64,65]:
        prepare(23);memory[start:start+occupied]=bytes([7])*occupied
        call(stop=0x89fa,budget=512)
        assert memory[start:start+occupied]==bytes([7])*occupied and read(start+occupied,1)==23
        assert read(start+occupied+1,1)==0
    prepare();memory[start:start+400]=bytes([7])*400
    cpu.a[0],cpu.d[0]=start,23
    trace=sequencer(cpu,memory,write)(0x89da,budget=512)
    assert trace.stop_reason==3 and cpu.pc in [BASE+0x89da,BASE+0x89dc]
    assert start+64<cpu.a[0]<start+400
    assert read(PLAYER+obj['selected_item_id'],1)==54


def test_full_calls_keep_held_fire_accept_duplicates_and_do_not_roll_back_when_fifo_full(deposit):
    cpu,memory,schemas,read,write,slots,obj,app,v,prepare,call=deposit
    prepare(23);start=APP+slots['app_terminal_deposited_item_ids']
    queue_before=bytes(memory[APP+HEAD:APP+HEAD+68]);tail_before=read(APP+TAIL)
    for count in range(1,4):
        write(PLAYER+obj['selected_item_id'],23,1)
        call()
        assert memory[start:start+count]==bytes([23])*count and read(start+count,1)==0
        assert read(PLAYER+obj['selected_item_id'],1)==0
        assert v('salvage_item_count')==count and v('input_fire_pressed_ff')==255
        assert v('context_flags')&16 and v('ranged_weapon_fire_latched')==0
        assert read(APP+TAIL)==tail_before and memory[APP+HEAD:APP+HEAD+68]==queue_before
    # Fresh held IDs are explicit inputs; no ordinary replenishment is asserted.


def test_full_deposit_removes_id_from_possession_and_real_recheck_stages_defeat(deposit):
    cpu,memory,schemas,read,write,slots,obj,app,v,prepare,call=deposit
    prepare(54);call()
    assert read(APP+slots['app_terminal_deposited_item_ids'],1)==54
    assert read(PLAYER+obj['selected_item_id'],1)==0 and v('context_flags')&16
    before_d,before_a=list(cpu.d),list(cpu.a[:6])
    call(0x86ca,budget=20000)
    assert list(cpu.d)==before_d and list(cpu.a[:6])==before_a
    assert read(PLAYER+obj['hit_points'],2)==0 and read(PLAYER+obj['world_object_flags'],1)&2
    assert v('game_exit_service_ticks_remaining')==70 and not v('context_flags')&16
    assert read(read(PLAYER+obj['position_descriptor_ptr']))==BASE+0x4c6ba
    # The real non-escape outcome sets bit1 in holding, independently of flags.
    assert read(PLAYER+obj['selected_item_id'],1)==2


def test_spare_pocket_id_satisfies_recheck_but_empty_holding_fails_selected_clearance(deposit):
    cpu,memory,schemas,read,write,slots,obj,app,v,prepare,call=deposit
    prepare(54);write(APP+slots['app_pocket_item_ids']+3,48,1);call()
    call(0x86ca)
    assert read(PLAYER+obj['hit_points'],2)==95 and not read(PLAYER+obj['world_object_flags'],1)&2
    assert not v('context_flags')&16 and read(PLAYER+obj['selected_item_id'],1)==0
    app('player_security_zone_tier',0);call(0x87e2)
    assert cpu.sr&1


def test_beyond_prefix_store_can_inhibit_rifle_until_release_in_explicit_full_buffer_state(deposit):
    cpu,memory,schemas,read,write,slots,obj,app,v,prepare,call=deposit
    prepare(23);start=APP+slots['app_terminal_deposited_item_ids']
    memory[start:start+65]=bytes([7])*65
    call(stop=0x89fa,budget=512)
    assert v('ranged_weapon_fire_latched')==23
    memory[BASE+0x924e:BASE+0x9250]=bytes([5,1])
    write(PLAYER+obj['selected_item_id'],18,1)
    call(0x9250)
    assert read(BASE+0x924e,2)==0x0501
    app('input_fire_pressed_ff',0);call(0x9250)
    assert v('ranged_weapon_fire_latched')==0
    app('input_fire_pressed_ff',255);call(0x9250,stop=0x92ba,budget=128)
    assert read(BASE+0x924e,2)==0x0401


@pytest.mark.parametrize('outside',[False,True])
def test_admitted_original_table_ray_can_relocate_the_offscreen_deposit_marker(deposit,outside):
    cpu,memory,schemas,read,write,slots,obj,app,v,prepare,call=deposit
    app('active_world_object_ptr_table',BASE+0x309a,4)
    write(APP+slots['active_world_object_count'],67,2);app('defeated_object_count',0)
    # Preserve all67 original descriptors and all35 original object pointers.
    descriptors=bytes(memory[BASE+0x309a:BASE+0x31aa])
    objects=bytes(memory[BASE+0x300a:BASE+0x309a])
    assert DESCRIPTOR in [read(BASE+0x309a+4*i) for i in range(67)]
    assert DESCRIPTOR not in [read(read(BASE+0x300a+4*i)+obj['position_descriptor_ptr']) for i in range(35)]
    write(STATE+24,int(outside),1)
    cpu.d[0],cpu.d[1]=170,970
    advance=sequencer(cpu,memory,write)
    assert advance(0x931c,stop=0x9380,budget=10000).stop_reason==1
    assert cpu.a[1]==DESCRIPTOR and cpu.a[2]==STATE
    assert advance(stop=0x944a,budget=10000).stop_reason==1
    assert read(DESCRIPTOR+4)==(0x00aa03ca if outside else 0x009403c4)
    assert v('defeated_object_count')==0 and read(PLAYER+obj['hit_points'],2)==95
    assert memory[BASE+0x309a:BASE+0x31aa]==descriptors and memory[BASE+0x300a:BASE+0x309a]==objects
    # At the original center, the rewritten marker is now28 pixels away.
    call(stop=None if outside else 0x89da,budget=128)
    assert read(PLAYER+obj['selected_item_id'],1)==54
    if outside:
        write(PLAYER+obj['world_x'],170,2);write(PLAYER+obj['world_y'],970,2)
        call(stop=0x89da,budget=128)
    # This is an explicitly admitted per-point CPU path, not ordinary aim/play.


def test_original_world_reset_clears_deposit_prefix_and_fire_latch_but_keeps_marker_and_cache(deposit):
    cpu,memory,schemas,read,write,slots,obj,app,v,prepare,call=deposit
    start=APP+slots['app_terminal_deposited_item_ids']
    memory[start:start+64]=bytes([23])*64
    app('salvage_item_count',31);app('modal_last_selected_item_id',0xad);app('ranged_weapon_fire_latched',0xbc)
    write(DESCRIPTOR+4,0x00aa03ca)
    call(0x9f26,budget=50000)
    assert memory[start:start+64]==bytes(64) and v('salvage_item_count')==0
    assert v('ranged_weapon_fire_latched')==0 and v('modal_last_selected_item_id')==0xad
    assert read(DESCRIPTOR+4)==0x00aa03ca
    assert read(DESCRIPTOR)==STATE and read(STATE)==GEOMETRY
    # This initializer is bounded; later title/modal/camera calls are separate.


def test_six_explicit_eligible_deposits_feed_real_escape_rank_without_uniqueness_check(deposit):
    cpu,memory,schemas,read,write,slots,obj,app,v,prepare,call=deposit
    prepare(23)
    for _ in range(6):
        write(PLAYER+obj['selected_item_id'],23,1);call()
    assert v('salvage_item_count')==6
    initialize((cpu,memory,schemas,read,write,None),slots,0)
    app('context_flags',32);app('game_event_flags',8);app('self_destruct_state',0)
    app('earth_orbit_countdown_bcd',1,2)
    call(0x4c9ae,budget=20000)
    assert read(APP+HEAD+8)==0x5ccf5
    pointer=read(APP+HEAD+8)
    assert bytes(memory[pointer:memory.index(0,pointer)])==b'. . QUITE  USEFUL . .'
    assert v('salvage_item_count')==6 and v('game_event_flags')==72
    assert read(PLAYER+obj['selected_item_id'],1)==0
    before=bytes(memory[APP+HEAD:APP+HEAD+68]);call(0x4c9ae)
    assert memory[APP+HEAD:APP+HEAD+68]==before and v('salvage_item_count')==6
