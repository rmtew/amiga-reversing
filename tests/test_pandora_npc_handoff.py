"""Original NPC handoff, UI/state consumers and script entry in controlled RAM."""
import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_framebuffer_lifetime import APP, fill_rows
from tests.test_pandora_render_order import sequencer

pytestmark = pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
GIVER,DESC,ACTIVE,SAVED,ACTIVE_NODE,SAVED_NODE,INVENTORY = (0x82000+256*i for i in range(7))
PLAYER,OFFICER,FIXED_NODE = BASE+0x4C322,BASE+0x4A40A,BASE+0x4A572
UI_QUEUE = BASE+0xA862


@pytest.fixture
def handoff(cpu_fixture,title_slots):
    cpu,memory,schemas,read,write,run=cpu_fixture
    fill_rows(cpu,memory,run)
    o,s,n=schemas['world_object_shared_prefix'],schemas['world_position_state_record'],schemas['WorldPositionStateNode']
    write(GIVER+o['position_descriptor_ptr'],DESC);write(DESC,ACTIVE)
    write(GIVER+o['saved_position_state_ptr'],SAVED)
    write(ACTIVE+s['state_node_ptr'],ACTIVE_NODE);write(SAVED+s['state_node_ptr'],SAVED_NODE)
    write(GIVER+o['inventory_slots_ptr'],INVENTORY)
    write(GIVER+o['selected_item_id'],54,1)
    memory[INVENTORY:INVENTORY+8]=bytes([7,13,54,29,54,31,9,42])
    write(SAVED_NODE+n['mode_flags'],0xA5,1);write(SAVED_NODE+n['frame_index_and_phase'],0xBEEF,2)
    write(ACTIVE_NODE+n['mode_flags'],0xA5,1);write(ACTIVE_NODE+n['frame_index_and_phase'],0xABCD,2)
    write(FIXED_NODE+n['mode_flags'],0xA5,1);write(FIXED_NODE+n['frame_index_and_phase'],0x1234,2)
    write(PLAYER+o['world_object_flags'],0,1);write(PLAYER+o['selected_item_id'],9,1)
    for key,value in [('app_font_glyph_bitmap_table_ptr',BASE+0xA7E2),
                      ('app_font_glyph_layout_table_ptr',BASE+0xAAFE),
                      ('app_ui_flags',0),('app_context_flags',32)]:
        write(APP+title_slots[key],value,1 if key in ['app_ui_flags','app_context_flags'] else 4)
    write(APP+0x1E0,0x70000);write(APP+0x1D4,0x78000)
    write(0xDFF01E,0x40,2)
    memory[APP+0x232:APP+0x276]=bytes(68);write(APP+title_slots['app_scrolling_message_queue_tail'],APP+0x232)
    memory[UI_QUEUE:UI_QUEUE+128]=bytes(128)
    cpu.a[5],cpu.a[6]=GIVER,APP
    return cpu,memory,schemas,read,write,run,title_slots


def init_audio(handoff):
    cpu,memory,schemas,read,write,run,slots=handoff
    cpu.d[0]=0
    assert sequencer(cpu,memory,write)(0x4D7DE,budget=4096).stop_reason==1
    cpu.a[5],cpu.a[6]=GIVER,APP


def test_all_player_flags_gate_only_inactive_before_message_and_effects(handoff):
    cpu,memory,schemas,read,write,run,slots=handoff
    flag=PLAYER+schemas['world_object_shared_prefix']['world_object_flags']
    for value in range(256):
        write(flag,value,1)
        run(0x4B11A,stop=0x4B184 if value&2 else 0x4B124,budget=8)
        assert read(GIVER+70,1)==54 and read(PLAYER+70,1)==9 and read(DESC)==ACTIVE
        assert read(APP+0x232)==0


def test_every_selected_byte_overwrites_player_and_clears_only_first_slot(handoff):
    cpu,memory,schemas,read,write,run,slots=handoff
    o=schemas['world_object_shared_prefix']
    for item in range(256):
        write(GIVER+70,item,1);write(GIVER+72,0xA0,1)
        write(PLAYER+70,255-item,1)
        memory[INVENTORY:INVENTORY+8]=bytes([7,13,item,29,item,31,9,42])
        cpu.a[5]=GIVER
        run(0x4B12E,stop=0x4B148,budget=16)
        assert read(GIVER+70,1)==0 and read(PLAYER+70,1)==item
        assert read(GIVER+72,1)==0xA2
        assert memory[INVENTORY:INVENTORY+8]==bytes([0,13,item,29,item,31,9,42])


def test_every_giver_flag_is_accepted_and_other_bits_survive_transfer(handoff):
    cpu,memory,schemas,read,write,run,slots=handoff
    for flags in range(256):
        write(GIVER+72,flags,1);write(GIVER+70,54,1);cpu.a[5]=GIVER
        run(0x4B12E,stop=0x4B148,budget=16)
        assert read(GIVER+72,1)==flags|2 and read(PLAYER+70,1)==54


def test_fixed_pose_reset_uses_global_officer_node_not_generic_giver_nodes(handoff):
    cpu,memory,schemas,read,write,run,slots=handoff
    active=bytes(memory[ACTIVE_NODE:ACTIVE_NODE+18]);saved=bytes(memory[SAVED_NODE:SAVED_NODE+18])
    for flags in range(256):
        write(FIXED_NODE+10,flags,1);write(FIXED_NODE+16,0xBEEF,2)
        run(0x4B148,stop=0x4B156,budget=8)
        assert read(FIXED_NODE+10,1)==flags&~1 and read(FIXED_NODE+16,2)==0
    assert memory[ACTIVE_NODE:ACTIVE_NODE+18]==active and memory[SAVED_NODE:SAVED_NODE+18]==saved


@pytest.mark.parametrize('panel',[False,True])
@pytest.mark.parametrize('item',[0,1,54,100,108])
def test_full_handoff_runs_original_message_ui_exchange_and_audio(handoff,panel,item):
    cpu,memory,schemas,read,write,run,slots=handoff
    init_audio(handoff)
    write(GIVER+70,item,1);write(APP+slots['app_ui_flags'],4 if panel else 0,1)
    trace=sequencer(cpu,memory,write)(0x4B11A,budget=150000)
    assert trace.stop_reason==1 and trace.steps<150000
    assert read(GIVER+70,1)==0 and read(PLAYER+70,1)==item and read(GIVER+72,1)&2
    assert memory[INVENTORY:INVENTORY+8]==bytes([0,13,54,29,54,31,9,42])
    assert read(DESC)==SAVED and read(GIVER+schemas['world_object_shared_prefix']['saved_position_state_ptr'])==ACTIVE
    assert read(SAVED_NODE+10,1)==0xA4 and read(SAVED_NODE+16,2)==0
    assert read(ACTIVE_NODE+10,1)==0xA5 and read(ACTIVE_NODE+16,2)==0xABCD
    assert read(FIXED_NODE+10,1)==0xA4 and read(FIXED_NODE+16,2)==0
    assert read(APP+0x232)==BASE+0x4D2A1 and read(APP+0x236)==0
    assert read(APP+slots['app_status_message_service_ticks_remaining'],2)==80
    assert not read(APP+slots['app_ui_flags'],1)&4
    assert read(APP+slots['app_game_event_flags'],1)&128
    line0=schemas['ui_overlay_descriptor']['line_0_ptr']
    names,offsets=BASE+0xA25C,BASE+0xA6DC
    assert read(BASE+0x33B2+line0)==names+read(offsets,2)
    assert read(BASE+0x32AA+line0)==names+read(offsets+2*max(1,item),2)
    assert cpu.a[5]==GIVER and cpu.a[6]==APP and cpu.a[7]==0x9004


def test_direct_second_handoff_is_not_guarded_by_giver_inactive(handoff):
    cpu,memory,schemas,read,write,run,slots=handoff
    init_audio(handoff)
    for active,saved,item in [(SAVED,ACTIVE,54),(ACTIVE,SAVED,0)]:
        trace=sequencer(cpu,memory,write)(0x4B11A,budget=150000)
        assert trace.stop_reason==1 and trace.steps<150000
        assert read(DESC)==active and read(GIVER+schemas['world_object_shared_prefix']['saved_position_state_ptr'])==saved
        assert read(PLAYER+70,1)==item and read(GIVER+72,1)&2


def test_original_officer_script_reaches_handoff_with_real_callees(handoff):
    cpu,memory,schemas,read,write,run,slots=handoff
    init_audio(handoff);o=schemas['world_object_shared_prefix']
    cpu.a[5]=OFFICER
    previous=read(read(OFFICER+o['position_descriptor_ptr']))
    incoming=read(OFFICER+o['saved_position_state_ptr'])
    inventory=read(OFFICER+o['inventory_slots_ptr']);item=read(OFFICER+o['selected_item_id'],1)
    assert item==54 and not read(OFFICER+o['world_object_flags'],1)&2
    visits=0
    for visits in range(1,501):
        trace=sequencer(cpu,memory,write)(0x13F4,budget=150000)
        assert trace.stop_reason==1 and trace.steps<150000 and cpu.a[5]==OFFICER
        if read(OFFICER+o['world_object_flags'],1)&2:break
    else:pytest.fail('handoff not reached within 500 explicit interpreter services')
    assert read(PLAYER+70,1)==54 and read(OFFICER+70,1)==0 and read(inventory,1)==0
    assert read(read(OFFICER+o['position_descriptor_ptr']))==incoming
    assert read(OFFICER+o['saved_position_state_ptr'])==previous
    assert read(APP+0x232)==BASE+0x4D2A1 and cpu.a[7]==0x9004
    cursor=read(OFFICER+o['behavior_script_ptr']);delay=read(OFFICER+o['behavior_script_delay_ticks'],2)
    assert visits==95 and cursor==BASE+0x23D0 and delay==10000
    for _ in range(3):
        run(0x13F4,budget=128)
        delay=max(0,delay-1)
        assert read(OFFICER+o['behavior_script_ptr'])==cursor
        assert read(OFFICER+o['behavior_script_delay_ticks'],2)==delay


def test_close_panel_recomputes_kriptonite_from_all_eight_slots_and_held_id(handoff):
    cpu,memory,schemas,read,write,run,slots=handoff
    carried,pocket=APP+slots['app_carried_item_ids'],APP+slots['app_pocket_item_ids']
    addresses=[carried+i for i in range(4)]+[pocket+i for i in range(4)]+[PLAYER+70]
    for selected in range(-1,9):
        for address in addresses:write(address,0,1)
        if selected>=0:write(addresses[selected],108,1)
        write(APP+slots['app_game_event_flags'],0xFE,1)
        run(0x2780,stop=0x27AE,budget=40)
        assert read(APP+slots['app_game_event_flags'],1)==(0xFE if selected>=0 else 0xFC)


def test_holding_name_panel_gate_accepts_every_other_flag(handoff):
    cpu,memory,schemas,read,write,run,slots=handoff
    for flags in range(256):
        write(APP+slots['app_ui_flags'],flags,1);cpu.a[5]=GIVER
        run(0x29BC,stop=0x29E8 if flags&4 else 0x29C4,budget=4)
        assert cpu.a[5]==GIVER


@pytest.mark.parametrize('context,ticker',[(0,False),(0,True),(32,True)])
def test_handoff_preserves_giver_across_immediate_message_and_ticker_clear(handoff,context,ticker):
    cpu,memory,schemas,read,write,run,slots=handoff
    init_audio(handoff)
    write(APP+slots['app_context_flags'],context,1)
    write(APP+slots['app_ui_flags'],64 if ticker else 0,1)
    trace=sequencer(cpu,memory,write)(0x4B11A,budget=150000)
    assert trace.stop_reason==1 and trace.steps<150000
    assert cpu.a[5]==GIVER and cpu.a[6]==APP and cpu.a[7]==0x9004
    assert read(GIVER+70,1)==0 and read(PLAYER+70,1)==54 and read(DESC)==SAVED
    assert read(APP+0x232)==BASE+0x4D2A1
