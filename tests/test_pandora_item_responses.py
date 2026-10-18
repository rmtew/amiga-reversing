"""Original item-response callbacks and their real carry-controlled message path.

Controlled flat RAM, typed object records and a busy FIFO avoid UI/hardware.
Calls do not establish ordinary gameplay reachability or exclusive ownership.
"""
from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_message_queue import initialize, APP, HEAD, LIMIT, TAIL, CONTEXT
from tests.test_pandora_restart_random import step_random

NPC, PLAYER = 0x82000, BASE+0x4C322
CALLBACKS = {'musician':0x4D37E, 'officer':0x4D3AE, 'chemist':0x4D3BE,
             'bank':0x4D3FC, 'priest':0x4D426, 'technician':0x4D432,
             'squash':0x4D520, 'driffid':0x4D538}
INVOKE = 0x83F6


def setup(cpu_fixture, slots, *, player_item=0, npc_item=0, flags=0, defeats=0, cooldown=77):
    cpu, memory, schemas, read, write, run = cpu_fixture
    o = schemas['world_object_shared_prefix']
    memory[NPC:NPC+84] = bytes(84)
    write(NPC+o['selected_item_id'], npc_item, 1)
    write(NPC+o['context_prompt_cooldown'], cooldown, 2)
    write(NPC+o['interaction_message_ptr'], 0x80000)
    write(NPC+o['context_message_ptr'], 0x80100)
    memory[0x80000:0x8000C] = b'INTERACTION\0'
    memory[0x80100:0x80108] = b'CONTEXT\0'
    for owner in [NPC, PLAYER]:
        write(owner+o['world_x'], 0, 2);write(owner+o['world_y'], 0, 2)
    write(PLAYER+o['selected_item_id'], player_item, 1)
    write(PLAYER+o['world_object_flags'], 0, 1)
    write(APP+slots['app_nearest_object_ptr'], NPC)
    write(APP+slots['app_world_interaction_flags'], flags, 1)
    write(APP+slots['app_defeated_object_count'], defeats, 1)
    initialize(cpu_fixture, slots)
    write(APP+CONTEXT, 32, 1)
    write(APP+slots['app_nearby_object_prompt_countdown'], 0, 1)
    cpu.a[5], cpu.a[6] = NPC, APP
    return o


def invoke(cpu_fixture, name):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[5], cpu.a[6] = NPC, APP
    run(CALLBACKS[name], budget=2048)
    assert cpu.a[5] == NPC and cpu.a[7] == 0x9004
    return bool(cpu.sr & 1)


def assert_record_effects(memory, o, before_npc, before_player):
    # Only response pointer and cooldown are writable in this callback family.
    actual = bytearray(memory[NPC:NPC+84])
    for field, size in [('interaction_message_ptr',4), ('context_prompt_cooldown',2)]:
        off = o[field];actual[off:off+size] = before_npc[off:off+size]
    assert actual == before_npc
    assert memory[PLAYER:PLAYER+84] == before_player


def test_every_player_item_byte_selects_officer_bank_driffid_and_bible_responses(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    driffid = {0x2A:0x5D0DC, 0x2D:0x5D104, 0x67:0x5D11D}
    for item in range(256):
        for name in ['officer','bank','driffid','chemist']:
            o = setup(cpu_fixture,title_slots,player_item=item)
            before_npc, before_player = bytes(memory[NPC:NPC+84]), bytes(memory[PLAYER:PLAYER+84])
            requested = invoke(cpu_fixture,name)
            expected = name == 'bank' or item == {'officer':0x12,'chemist':0x2C}.get(name) or (name == 'driffid' and item in driffid)
            assert requested == expected
            assert read(NPC+o['context_prompt_cooldown'],2) == (250 if expected else 77)
            pointer = read(NPC+o['interaction_message_ptr'])
            if name == 'bank':assert pointer == (0x5D24B if item == 0x64 else 0x5D275)
            elif name == 'driffid':assert pointer == driffid.get(item,0x80000)
            elif name == 'chemist':assert pointer == (0x5CF4C if item == 0x2C else 0x80000)
            assert read(PLAYER+o['selected_item_id'],1) == item
            assert_record_effects(memory,o,before_npc,before_player)


def test_every_npc_held_byte_drives_technician_and_squash_without_player_item_or_range_gate(cpu_fixture,title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    for item in range(256):
        for name,required,bit in [('technician',0x2E,2),('squash',0x2F,3)]:
            o = setup(cpu_fixture,title_slots,npc_item=item,player_item=0xFF)
            write(PLAYER+o['world_x'],0x4000,2);write(PLAYER+o['world_y'],0x4000,2)
            assert invoke(cpu_fixture,name) == (item == required)
            assert read(APP+title_slots['app_world_interaction_flags'],1) == ((1<<bit) if item == required else 0)
            assert read(NPC+o['selected_item_id'],1) == item
            assert read(PLAYER+o['selected_item_id'],1) == 255
            assert read(NPC+o['context_prompt_cooldown'],2) == (250 if item == required else 77)


def test_priest_uses_nonzero_defeat_byte_without_latch_or_item_gate(cpu_fixture,title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    for defeats in range(256):
        o = setup(cpu_fixture,title_slots,defeats=defeats,flags=255,player_item=255,npc_item=255)
        assert invoke(cpu_fixture,'priest') == bool(defeats)
        assert read(NPC+o['context_prompt_cooldown'],2) == (250 if defeats else 77)
        assert read(APP+title_slots['app_world_interaction_flags'],1) == 255


def test_all_latch_bytes_preserve_other_bits_and_musician_does_not_set_cooldown(cpu_fixture,title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    for flags in range(256):
        for name,item,npc_item,bit in [('musician',0x27,0,1),('chemist',0x2C,0,7),
                                      ('technician',0,0x2E,2),('squash',0,0x2F,3)]:
            o = setup(cpu_fixture,title_slots,flags=flags,player_item=item,npc_item=npc_item)
            assert invoke(cpu_fixture,name) == (not flags & (1<<bit))
            assert read(APP+title_slots['app_world_interaction_flags'],1) == flags | (1<<bit)
            expected = 250 if name != 'musician' and not flags & (1<<bit) else 77
            assert read(NPC+o['context_prompt_cooldown'],2) == expected
            assert not invoke(cpu_fixture,name)
            assert read(PLAYER+o['selected_item_id'],1) == item
            assert read(NPC+o['selected_item_id'],1) == npc_item


def test_musician_gin_and_strict_wrapped_range_are_both_required(cpu_fixture,title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    for item in range(256):
        setup(cpu_fixture,title_slots,player_item=item)
        assert invoke(cpu_fixture,'musician') == (item == 0x27)
    cases = [(0,0,True),(23,15,True),(-23,-15,True),(24,0,False),
             (-24,0,False),(0,16,False),(0,-16,False),(0x8000,0,False),(0,0x8000,False)]
    for dx,dy,near in cases:
        o = setup(cpu_fixture,title_slots,player_item=0x27)
        write(PLAYER+o['world_x'],dx & 65535,2);write(PLAYER+o['world_y'],dy & 65535,2)
        assert invoke(cpu_fixture,'musician') == near
        assert read(APP+title_slots['app_world_interaction_flags'],1) == (2 if near else 0)
        assert read(NPC+o['context_prompt_cooldown'],2) == 77
        assert cpu.a[4] == PLAYER
    o = setup(cpu_fixture,title_slots,player_item=0x27)
    write(NPC+o['world_x'],65530,2);write(PLAYER+o['world_x'],10,2)
    assert invoke(cpu_fixture,'musician')  # Wrapped WORD delta16.


def test_chemist_advances_real_prng_and_uses_only_four_aligned_quote_entries(cpu_fixture,title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    expected_ptrs = [0x5CEB3,0x5CEDC,0x5CEFC,0x5CF27]
    seen = set()
    for shift in range(64):
        o = setup(cpu_fixture,title_slots,npc_item=0x2B)
        initial = (0x12345678,shift)
        write(0x7E8,initial[0]);write(0x7EC,initial[1])
        expected = step_random(*initial)
        assert invoke(cpu_fixture,'chemist')
        index = (expected[1] & 12)//4;seen.add(index)
        assert read(NPC+o['interaction_message_ptr']) == expected_ptrs[index]
        assert (read(0x7E8),read(0x7EC)) == expected
        assert read(NPC+o['context_prompt_cooldown'],2) == 250
    assert seen == set(range(4))


def test_chemist_new_bible_latch_has_priority_then_falls_through_to_held_shakespeare(cpu_fixture,title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    o = setup(cpu_fixture,title_slots,player_item=0x2C,npc_item=0x2B)
    write(0x7E8,0x12345678);write(0x7EC,0xABCDEF01)
    original = bytes(memory[0x7E8:0x7F0])
    assert invoke(cpu_fixture,'chemist')
    assert read(NPC+o['interaction_message_ptr']) == 0x5CF4C
    assert bytes(memory[0x7E8:0x7F0]) == original
    assert invoke(cpu_fixture,'chemist')  # Latched Bible now falls through.
    expected = step_random(0x12345678,0xABCDEF01)
    assert read(NPC+o['interaction_message_ptr']) == [0x5CEB3,0x5CEDC,0x5CEFC,0x5CF27][(expected[1]&12)//4]
    assert (read(0x7E8),read(0x7EC)) == expected
    write(NPC+o['selected_item_id'],0,1)
    assert not invoke(cpu_fixture,'chemist')


def test_real_dispatcher_queues_interaction_pointer_and_respects_clear_carry_or_null_pointer(cpu_fixture,title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cases = [('musician',0x27,0,0),('officer',0x12,0,0),('chemist',0x2C,0,0),
             ('bank',0,0,0),('priest',0,0,1),('technician',0,0x2E,0),
             ('squash',0,0x2F,0),('driffid',0x2A,0,0)]
    for name,item,npc_item,defeats in cases:
        o = setup(cpu_fixture,title_slots,player_item=item,npc_item=npc_item,defeats=defeats)
        write(NPC+o['interaction_callback'],BASE+CALLBACKS[name])
        run(INVOKE,budget=4096)
        assert read(APP+HEAD) == read(NPC+o['interaction_message_ptr'])
        assert read(APP+HEAD) != read(NPC+o['context_message_ptr'])
        assert read(APP+TAIL) == APP+HEAD+4 and read(APP+HEAD+4) == 0
        assert cpu.a[5] == NPC and cpu.a[7] == 0x9004
    for callback,pointer in [(0,0x80000),(BASE+CALLBACKS['officer'],0x80000),(BASE+CALLBACKS['priest'],0)]:
        o = setup(cpu_fixture,title_slots,defeats=1)
        write(NPC+o['interaction_callback'],callback);write(NPC+o['interaction_message_ptr'],pointer)
        run(INVOKE,budget=4096)
        assert read(APP+TAIL) == APP+HEAD and read(APP+HEAD) == 0


def test_full_fifo_does_not_undo_chemist_message_latch_or_cooldown(cpu_fixture,title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    o = setup(cpu_fixture,title_slots,player_item=0x2C)
    write(NPC+o['interaction_callback'],BASE+CALLBACKS['chemist'])
    for i in range(16):write(APP+HEAD+4*i,0x80100)
    write(APP+TAIL,APP+LIMIT)
    before = bytes(memory[APP+HEAD:APP+LIMIT+4])
    run(INVOKE,budget=4096)
    assert bytes(memory[APP+HEAD:APP+LIMIT+4]) == before and read(APP+TAIL) == APP+LIMIT
    assert read(NPC+o['interaction_message_ptr']) == 0x5CF4C
    assert read(NPC+o['context_prompt_cooldown'],2) == 250
    assert read(APP+title_slots['app_world_interaction_flags'],1) == 128
    assert read(PLAYER+o['selected_item_id'],1) == 0x2C


def test_selected_service_tests_inactive_bits_then_decrements_cooldown_before_later_dispatch(cpu_fixture,title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    for owner in [NPC,PLAYER]:
        for flags in range(256):
            o = setup(cpu_fixture,title_slots,player_item=0x12,cooldown=0)
            write(owner+o['world_object_flags'],flags,1)
            write(NPC+o['interaction_callback'],BASE+CALLBACKS['officer'])
            run(0x83D2,budget=4096)
            assert read(APP+TAIL) == APP+HEAD+(0 if flags & 2 else 4)
            assert read(NPC+o['context_prompt_cooldown'],2) == (0 if flags & 2 else 250)
    for cooldown in [*range(256),32767,32768,65535]:
        o = setup(cpu_fixture,title_slots,player_item=0x12,cooldown=cooldown)
        write(NPC+o['interaction_callback'],BASE+CALLBACKS['officer'])
        run(0x83D2,budget=4096)
        assert read(NPC+o['context_prompt_cooldown'],2) == (cooldown-1 if cooldown else 250)
        assert read(APP+TAIL) == APP+HEAD+(0 if cooldown else 4)
        if cooldown == 1:
            run(0x83D2,budget=4096)
            assert read(NPC+o['context_prompt_cooldown'],2) == 250
            assert read(APP+TAIL) == APP+HEAD+4


def test_inventory_panel_gate_precedes_selected_callback_service(cpu_fixture,title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    for ui in range(256):
        o = setup(cpu_fixture,title_slots,player_item=0x12,cooldown=0)
        write(APP+title_slots['app_ui_flags'],ui,1)
        write(NPC+o['interaction_callback'],BASE+CALLBACKS['officer'])
        run(0x83B6,budget=8192)
        assert read(APP+TAIL) == APP+HEAD+(0 if ui & 4 else 4)
        assert read(NPC+o['context_prompt_cooldown'],2) == (0 if ui & 4 else 250)
