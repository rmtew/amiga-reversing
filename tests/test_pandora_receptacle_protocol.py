"""Original receptacle entry/exit and ordered attachment transfers in flat RAM."""
import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_framebuffer_lifetime import APP, fill_rows
from tests.test_pandora_render_order import sequencer

pytestmark = pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
PLAYER = BASE+0x4C322
STATE, DESCRIPTOR, DATA, NODE, ATTACHMENT, TABLE = (0x82000+i*0x100 for i in range(6))


@pytest.fixture
def receptacle(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    fill_rows(cpu, memory, run)
    obj, state = schemas['world_object_shared_prefix'], schemas['world_position_state_record']
    node, data = schemas['WorldPositionStateNode'], schemas['item_receptacle_interaction_data']
    memory[STATE:TABLE+16] = bytes(TABLE+16-STATE)
    write(DESCRIPTOR, STATE)
    write(DESCRIPTOR+4, 400, 2); write(DESCRIPTOR+6, 400, 2)
    write(STATE+state['interaction_data_ptr'], DATA)
    write(STATE+state['state_node_ptr'], NODE)
    write(STATE+state['attachment_state_ptr'], ATTACHMENT)
    write(STATE+state['world_object_flags'], 4, 1)
    write(DATA+data['required_item_definition_id'], 7, 1)
    write(TABLE, DESCRIPTOR)
    write(APP+title_slots['app_active_world_object_ptr_table'], TABLE)
    write(APP+title_slots['active_world_object_count'], 1, 2)
    write(APP+title_slots['app_ui_flags'], 4, 1)
    write(APP+title_slots['app_context_flags'], 0, 1)
    write(APP+title_slots['app_scrolling_message_queue_tail'], APP+0x232)
    memory[APP+0x232:APP+0x276] = bytes(68)
    write(APP+0x1E0, 0x70000); write(APP+0x1D4, 0x78000)
    write(0xDFF01E, 0x40, 2)
    write(PLAYER+obj['world_x'], 400, 2); write(PLAYER+obj['world_y'], 400, 2)
    write(PLAYER+obj['world_object_flags'], 0, 1)
    write(PLAYER+obj['selected_item_id'], 2, 1)
    cpu.a[1], cpu.a[2], cpu.a[3], cpu.a[4], cpu.a[6] = DESCRIPTOR, STATE, DATA, PLAYER, APP
    return cpu, memory, schemas, read, write, run, title_slots


def magnitude(word):
    return (-word) & 0xFFFF if word & 0x8000 else word


def test_every_axis_word_uses_wrapped_distance_and_exclusive_28(receptacle):
    cpu, memory, schemas, read, write, run, slots = receptacle
    for axis in [4, 6]:
        for value in range(65536):
            write(DESCRIPTOR+4, 400, 2); write(DESCRIPTOR+6, 400, 2)
            write(DESCRIPTOR+axis, value, 2)
            distance = magnitude((value-400) & 0xFFFF)
            run(0x8086, stop=0x80C2 if distance < 28 else 0x814E, budget=64)
            assert cpu.d[0] & 0xFFFF == distance


@pytest.mark.parametrize('dx,dy', [(27,0),(28,0),(14,13),(14,14),(-14,-13),
                                   (32768,32768),(32767,32768),(65535,1)])
def test_distance_sum_wraps_and_state_offsets_precede_center_bias(receptacle, dx, dy):
    cpu, memory, schemas, read, write, run, slots = receptacle
    s = schemas['world_position_state_record']
    write(DESCRIPTOR+4, 100, 2); write(DESCRIPTOR+6, 200, 2)
    write(STATE+s['world_x_offset'], (300+dx)&0xFFFF, 2)
    write(STATE+s['world_y_offset'], (200+dy)&0xFFFF, 2)
    distance = (magnitude(dx&0xFFFF)+magnitude(dy&0xFFFF))&0xFFFF
    run(0x8086, stop=0x80C2 if distance<28 else 0x814E, budget=64)
    assert cpu.d[0]&0xFFFF == distance


def test_every_state_flag_dispatch_prioritizes_checkpoint_over_receptacle(receptacle):
    cpu, memory, schemas, read, write, run, slots = receptacle
    s=schemas['world_position_state_record']
    for flags in range(256):
        write(STATE+s['world_object_flags'],flags,1)
        destination=0x7F08 if flags&16 else 0x807C if flags&4 else 0x7E38 if flags&1 else 0x7F02
        run(0x7DF0,stop=destination,budget=32)
        assert cpu.a[1]==DESCRIPTOR and cpu.a[2]==STATE
    write(STATE+s['interaction_flags'],1,1)
    run(0x7DF0,stop=0x7F02,budget=32)
    write(APP+slots['active_world_object_count'],0,2)
    run(0x7DF0,budget=16)


def test_all_flag_bytes_latch_first_attempt_even_with_a_busy_hand(receptacle):
    cpu, memory, schemas, read, write, run, slots = receptacle
    d=schemas['item_receptacle_interaction_data']
    inhibited=APP+slots['app_player_movement_commit_inhibited']
    for flags in range(256):
        write(DATA+d['flags'],flags,1); write(inhibited,0xA5,1)
        run(0x807C,stop=0x7F02,budget=64)
        assert read(DATA+d['flags'],1)==flags|1
        assert read(inhibited,1)==(0xA5 if flags&1 else 0)
        assert read(DATA)==0 and read(STATE+20)==ATTACHMENT


def test_every_player_flag_skips_inactive_before_any_nearby_latch(receptacle):
    cpu, memory, schemas, read, write, run, slots = receptacle
    o=schemas['world_object_shared_prefix']
    for flags in range(256):
        write(PLAYER+o['world_object_flags'],flags,1)
        run(0x807C,stop=0x7F02 if flags&2 else 0x8086,budget=8)
        assert read(DATA+5,1)==0


def test_all_required_and_held_item_bytes_compare_exactly_on_return(receptacle):
    cpu, memory, schemas, read, write, run, slots = receptacle
    o=schemas['world_object_shared_prefix']
    for required in range(256):
        write(DATA+4,required,1)
        for held in range(256):
            write(PLAYER+o['selected_item_id'],held,1)
            run(0x80D8,stop=0x80F6 if held==required else 0x80E2,budget=8)


def test_all_held_bytes_allow_pickup_only_for_zero_or_one(receptacle):
    cpu, memory, schemas, read, write, run, slots = receptacle
    o=schemas['world_object_shared_prefix']
    for held in range(256):
        write(PLAYER+o['selected_item_id'],held,1)
        run(0x8104,stop=0x8110 if held<2 else 0x7F02,budget=8)


@pytest.mark.parametrize('held',[0,1])
@pytest.mark.parametrize('attachment',[0,ATTACHMENT])
def test_full_pickup_stores_attachment_gives_item_and_returns_from_dispatch(receptacle, held, attachment):
    cpu, memory, schemas, read, write, run, slots = receptacle
    o,s=schemas['world_object_shared_prefix'],schemas['world_position_state_record']
    write(PLAYER+o['selected_item_id'],held,1)
    write(STATE+s['attachment_state_ptr'],attachment)
    # A second invalid entry proves successful transfer exits the whole service.
    write(APP+slots['active_world_object_count'],2,2);write(TABLE+4,0xFFFFFF)
    run(0x7DF0,budget=256)
    assert read(DATA)==attachment and read(STATE+s['attachment_state_ptr'])==0
    assert read(PLAYER+o['selected_item_id'],1)==7 and read(DATA+5,1)==1
    assert cpu.a[0]==TABLE+4 and cpu.a[7]==0x9004


def test_full_item_return_restores_attachment_clears_held_id_and_exits(receptacle):
    cpu, memory, schemas, read, write, run, slots = receptacle
    o,s=schemas['world_object_shared_prefix'],schemas['world_position_state_record']
    write(DATA,ATTACHMENT);write(STATE+s['attachment_state_ptr'],0)
    write(PLAYER+o['selected_item_id'],7,1)
    write(APP+slots['active_world_object_count'],2,2);write(TABLE+4,0xFFFFFF)
    run(0x7DF0,budget=256)
    assert read(DATA)==0 and read(STATE+s['attachment_state_ptr'])==ATTACHMENT
    assert read(PLAYER+o['selected_item_id'],1)==0 and read(DATA+5,1)==1
    assert cpu.a[0]==TABLE+4 and cpu.a[7]==0x9004


def test_wrong_return_enqueues_both_messages_and_continues_to_next_descriptor(receptacle):
    cpu, memory, schemas, read, write, run, slots = receptacle
    write(DATA,ATTACHMENT)
    write(TABLE+4,DESCRIPTOR+0x40)  # A second descriptor with NULL state.
    write(APP+slots['active_world_object_count'],2,2)
    run(0x7DF0,budget=1024)
    assert read(APP+0x232)==BASE+0x8162 and read(APP+0x236)!=0
    assert read(APP+0x23A)==0 and read(APP+0x276)==APP+0x23A
    assert read(DATA)==ATTACHMENT and read(DATA+5,1)==1
    assert cpu.d[7]&0xFFFF==0xFFFF and cpu.a[0]==TABLE+8 and cpu.a[1]==DESCRIPTOR+0x40


def test_far_visit_clears_only_nearby_bit_and_accepts_null_data(receptacle):
    cpu, memory, schemas, read, write, run, slots = receptacle
    for flags in range(256):
        write(DATA+5,flags,1)
        run(0x814E,stop=0x7F02,budget=16)
        assert read(DATA+5,1)==flags&~1
    write(STATE+schemas['world_position_state_record']['interaction_data_ptr'],0)
    before=bytes(memory[:16]);run(0x814E,stop=0x7F02,budget=8)
    assert memory[:16]==before


def test_reentry_rearms_transfer_but_latched_visits_preserve_all_state(receptacle):
    cpu, memory, schemas, read, write, run, slots = receptacle
    o=schemas['world_object_shared_prefix']
    write(PLAYER+o['selected_item_id'],0,1);run(0x7DF0,budget=256)
    snapshot=bytes(memory[STATE:DATA+6])
    run(0x7DF0,budget=256)
    assert memory[STATE:DATA+6]==snapshot and read(PLAYER+o['selected_item_id'],1)==7
    run(0x814E,stop=0x7F02,budget=16)
    run(0x7DF0,budget=256)
    assert read(DATA)==0 and read(PLAYER+o['selected_item_id'],1)==0


def test_all_event_flag_bytes_apply_brain_health_assignment_only_once(receptacle):
    cpu, memory, schemas, read, write, run, slots = receptacle
    hp=PLAYER+schemas['world_object_shared_prefix']['hit_points']
    flags=APP+slots['app_game_event_flags']
    for value in range(256):
        write(flags,value,1);write(hp,0xABCD,2)
        run(0x812C,stop=0x814C if value&1 else 0x813A,budget=8)
        assert read(flags,1)==value|1 and read(hp,2)==(0xABCD if value&1 else 95)


@pytest.mark.parametrize('hp',[0,94,95,96,255,65535])
def test_brain_pickup_assigns_full_hp_word_and_runs_original_ui_audio(receptacle, hp):
    cpu, memory, schemas, read, write, run, slots = receptacle
    o=schemas['world_object_shared_prefix']
    write(PLAYER+o['hit_points'],hp,2)
    write(PLAYER+o['selected_item_id'],0,1);write(DATA+4,104,1)
    write(APP+slots['app_game_event_flags'],0,1)
    cpu.d[0]=0
    advance=sequencer(cpu,memory,write)
    assert advance(0x4D7DE,budget=4096).stop_reason==1
    trace=sequencer(cpu,memory,write)(0x7DF0,budget=40000)
    assert trace.stop_reason==1 and trace.steps<40000
    assert read(PLAYER+o['hit_points'],2)==95
    assert read(PLAYER+o['selected_item_id'],1)==104 and read(DATA)==ATTACHMENT
    assert read(STATE+20)==0 and read(APP+slots['app_game_event_flags'],1)&1
    assert cpu.a[5]==PLAYER and cpu.a[4]!=PLAYER and cpu.a[7]==0x9004


def test_original_six_reset_records_restore_saved_attachments_for_all_presence_masks(receptacle):
    cpu, memory, schemas, read, write, run, slots = receptacle
    s=schemas['world_position_state_record']
    states=[read(BASE+0x488AA+4*i) for i in range(6)]
    data=[read(p+s['interaction_data_ptr']) for p in states]
    attachments=[read(p+s['attachment_state_ptr']) for p in states]
    ids=[read(p+4,1) for p in data]
    assert len(set(states))==6 and len(set(data))==6 and all(attachments)
    for mask in range(64):
        for i,(p,d,a) in enumerate(zip(states,data,attachments)):
            write(p+s['attachment_state_ptr'],0x86000+16*i)
            write(d,a if mask>>i&1 else 0);write(d+5,0xA4|i,1)
        run(0x9F66,stop=0x9F86,budget=128)
        for i,(p,d,a) in enumerate(zip(states,data,attachments)):
            assert read(p+s['attachment_state_ptr'])==(a if mask>>i&1 else 0x86000+16*i)
            assert read(d)==0 and read(d+5,1)==0 and read(d+4,1)==ids[i]
    assert cpu.d[7]&0xFFFF==0xFFFF


def test_pickup_transfer_copies_every_required_id_without_filtering(receptacle):
    cpu, memory, schemas, read, write, run, slots = receptacle
    selected=PLAYER+schemas['world_object_shared_prefix']['selected_item_id']
    for item in range(256):
        write(DATA,0);write(DATA+4,item,1);write(STATE+20,ATTACHMENT)
        run(0x8110,stop=0x811E,budget=8)
        assert read(DATA)==ATTACHMENT and read(STATE+20)==0 and read(selected,1)==item


def test_brain_already_latched_still_picks_up_without_health_or_feedback(receptacle):
    cpu, memory, schemas, read, write, run, slots = receptacle
    o=schemas['world_object_shared_prefix']
    write(PLAYER+o['selected_item_id'],0,1);write(DATA+4,104,1)
    write(PLAYER+o['hit_points'],0x1234,2)
    write(APP+slots['app_game_event_flags'],1,1)
    run(0x7DF0,budget=256)
    assert read(PLAYER+o['selected_item_id'],1)==104 and read(DATA)==ATTACHMENT
    assert read(PLAYER+o['hit_points'],2)==0x1234 and cpu.a[4]==PLAYER
    assert read(APP+slots['app_game_event_flags'],1)==1


def test_reset_shared_interaction_record_is_consumed_by_first_state_only(receptacle):
    cpu, memory, schemas, read, write, run, slots = receptacle
    s=schemas['world_position_state_record'];second=STATE+0x40
    for i,p in enumerate([STATE,second,second,second,second,second]):
        write(BASE+0x488AA+4*i,p)
        write(p+s['interaction_data_ptr'],DATA)
    write(STATE+20,0x11111111);write(second+20,0x22222222)
    write(DATA,ATTACHMENT);write(DATA+5,255,1)
    run(0x9F66,stop=0x9F86,budget=128)
    assert read(STATE+20)==ATTACHMENT and read(second+20)==0x22222222
    assert read(DATA)==0 and read(DATA+5,1)==0
