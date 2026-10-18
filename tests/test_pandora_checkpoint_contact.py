"""Original contact authorization and attachment holds; controlled RAM, no DMA."""
import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_receptacle_protocol import receptacle, PLAYER, STATE, NODE, TABLE
from tests.test_pandora_framebuffer_lifetime import APP
from tests.test_pandora_render_order import sequencer

pytestmark = pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
# Native copied-view symbols and decoded absolute operands inspected at68eba33b.
DESCRIPTORS = [BASE+p for p in (0x48CD0,0x48CDC,0x48CE8,0x48CF4)]+[0x82600]
CARDS = [48,49,50,55,None]
DEFEAT, DEFEAT_GEOMETRY = BASE+0x4C6BA, BASE+0x4C5D0
STATES = [STATE+64*i for i in range(3)]
NODES = [NODE+32*i for i in range(3)]


@pytest.fixture
def contact(receptacle):
    cpu, memory, schemas, read, write, run, slots = receptacle
    o,s,n=schemas['world_object_shared_prefix'],schemas['world_position_state_record'],schemas['WorldPositionStateNode']
    for i,(p,node) in enumerate(zip(STATES,NODES)):
        write(p+s['state_node_ptr'],node)
        write(p+s['attachment_state_ptr'],STATES[i+1] if i<2 else 0)
        write(p+s['world_object_flags'],16,1)
        write(node+n['mode_flags'],0xA4+i,1)
        write(node+n['frame_index_and_phase'],0xBEEF,2)
    write(APP+slots['app_font_glyph_bitmap_table_ptr'],BASE+0xA7E2)
    write(APP+slots['app_authorized_checkpoint_seen_bits'],255,1)
    write(APP+slots['app_authorized_checkpoint_count'],0xA5,1)
    write(APP+slots['app_game_event_flags'],0,1)
    def configure(index=0,dx=0,dy=0):
        d=DESCRIPTORS[index]
        write(d,STATE);write(d+4,(400+dx)&65535,2)
        write(d+6,(400+dy-(16 if index in (2,3) else 0))&65535,2)
        write(TABLE,d)
        write(PLAYER+o['selected_item_id'],CARDS[index] or 2,1)
        write(APP+slots['app_player_movement_commit_inhibited'],0xA5,1)
        cpu.a[1],cpu.a[2],cpu.a[4],cpu.a[6]=d,STATE,PLAYER,APP
        return d
    configure()
    return cpu,memory,schemas,read,write,run,slots,configure


def magnitude(word):
    return (-word)&65535 if word&32768 else word


@pytest.mark.parametrize('index',[0,2])
def test_every_axis_word_at_both_vertical_biases(contact,index):
    cpu,memory,schemas,read,write,run,slots,configure=contact
    descriptor=configure(index)
    bias=16 if index==2 else 0
    for axis in [4,6]:
        for value in range(65536):
            write(descriptor+4,400,2);write(descriptor+6,400-bias,2)
            write(descriptor+axis,value,2)
            delta=(value-400+(bias if axis==6 else 0))&65535
            distance=magnitude(delta)
            near=distance < (18 if axis==4 else 32)
            run(0x7F18,stop=0x7F6C if near else 0x7FF4,budget=64)
            assert (cpu.d[0] if axis==4 else cpu.d[1])&65535==distance


@pytest.mark.parametrize('index',range(5))
def test_every_card_byte_at_each_identity_and_unknown_default(contact,index):
    cpu,memory,schemas,read,write,run,slots,configure=contact
    configure(index)
    for card in range(256):
        write(PLAYER+schemas['world_object_shared_prefix']['selected_item_id'],card,1)
        write(APP+slots['app_game_event_flags'],0xB5,1)
        run(0x7F6C,stop=0x7FC2 if CARDS[index] is None or card==CARDS[index] else 0x800A,budget=32)
        expected=0xB5 if index!=3 or card==55 else 0xA5
        assert read(APP+slots['app_game_event_flags'],1)==expected
        assert cpu.d[1]==(index if index<4 else 0)
        assert read(APP+slots['app_player_movement_commit_inhibited'],1)==0


def test_all_guard_bytes_skip_only_player_inactive_or_escape_triggered(contact):
    cpu,memory,schemas,read,write,run,slots,configure=contact
    flags=PLAYER+schemas['world_object_shared_prefix']['world_object_flags']
    for value in range(256):
        write(flags,value,1)
        run(0x7F08,stop=0x7F02 if value&2 else 0x7F18,budget=8)
    write(flags,0,1)
    for value in range(256):
        write(APP+slots['app_game_event_flags'],value,1)
        run(0x7F08,stop=0x7F02 if value&8 else 0x7F18,budget=8)
        assert read(APP+slots['app_game_event_flags'],1)==value
    assert read(APP+slots['app_player_movement_commit_inhibited'],1)==0xA5


def test_all_seen_masks_set_only_selected_bit_and_gate_first_feedback(contact):
    cpu,memory,schemas,read,write,run,slots,configure=contact
    for index in range(4):
        for mask in range(256):
            cpu.d[1]=index
            write(APP+slots['app_authorized_checkpoint_seen_bits'],mask,1)
            run(0x7FC2,stop=0x7FDE if mask&(1<<index) else 0x7FC8,budget=8)
            assert read(APP+slots['app_authorized_checkpoint_seen_bits'],1)==mask|1<<index
            assert read(APP+slots['app_authorized_checkpoint_count'],1)==0xA5
    for count in range(256):
        write(APP+slots['app_authorized_checkpoint_count'],count,1)
        run(0x7FDA,stop=0x7FDE,budget=4)
        assert read(APP+slots['app_authorized_checkpoint_count'],1)==(count+1)&255


@pytest.mark.parametrize('start,held',[(0x7FDE,True),(0x7FF4,False)])
def test_every_node_mode_byte_preserves_clock_and_all_other_bytes(contact,start,held):
    cpu,memory,schemas,read,write,run,slots,configure=contact
    n=schemas['WorldPositionStateNode']
    for flags in range(256):
        expected=[]
        for i,p in enumerate(NODES):
            write(p+n['mode_flags'],(flags+17*i)&255,1)
            row=bytearray(memory[p:p+18]);row[n['mode_flags']]=row[n['mode_flags']]|1 if held else row[n['mode_flags']]&~1
            expected.append(row)
        cpu.a[2]=STATE
        run(start,stop=0x7F02,budget=64)
        assert all(memory[p:p+18]==row for p,row in zip(NODES,expected))
        assert cpu.a[2]==STATES[-1] and cpu.a[3]==NODES[-1]


@pytest.mark.parametrize('index',range(4))
@pytest.mark.parametrize('count',[0,255])
def test_full_first_authorization_runs_audio_counts_once_and_holds_chain(contact,index,count):
    cpu,memory,schemas,read,write,run,slots,configure=contact
    cpu.d[0]=0;assert sequencer(cpu,memory,write)(0x4D7DE,budget=4096).stop_reason==1
    descriptor=configure(index)
    write(APP+slots['app_authorized_checkpoint_seen_bits'],0xF0,1)
    write(APP+slots['app_authorized_checkpoint_count'],count,1)
    trace=sequencer(cpu,memory,write)(0x7DF0,budget=10000)
    assert trace.stop_reason==1 and trace.steps<10000
    assert read(APP+slots['app_authorized_checkpoint_seen_bits'],1)==0xF0|1<<index
    assert read(APP+slots['app_authorized_checkpoint_count'],1)==(count+1)&255
    assert read(APP+slots['app_game_event_flags'],1)==(128|16 if index==3 else 128)
    assert all(read(p+schemas['WorldPositionStateNode']['mode_flags'],1)&1 for p in NODES)
    assert all(read(p+16,2)==0xBEEF for p in NODES)
    assert cpu.a[0]==TABLE+4 and cpu.a[1]==descriptor and cpu.a[2]==STATES[-1]
    assert cpu.a[4]==PLAYER and cpu.a[7]==0x9004


def test_repeated_authorization_does_not_recount_or_request_feedback(contact):
    cpu,memory,schemas,read,write,run,slots,configure=contact
    write(APP+slots['app_authorized_checkpoint_seen_bits'],1,1)
    for _ in range(2):
        run(0x7DF0,budget=256)
        assert read(APP+slots['app_authorized_checkpoint_count'],1)==0xA5
        assert read(APP+slots['app_game_event_flags'],1)==0


@pytest.mark.parametrize('dx,dy',[(17,31),(18,0),(0,32),(-18,0),(0,-32),(-17,-31)])
def test_full_rectangle_holds_inside_and_far_only_releases_chain(contact,dx,dy):
    cpu,memory,schemas,read,write,run,slots,configure=contact
    configure(2,dx,dy)
    write(APP+slots['app_game_event_flags'],16,1)
    near=abs(dx)<18 and abs(dy)<32
    run(0x7DF0,budget=256)
    for i,p in enumerate(NODES):
        flags=0xA4+i
        assert read(p+10,1)==(flags|1 if near else flags&~1)
        assert read(p+16,2)==0xBEEF
    assert read(APP+slots['app_game_event_flags'],1)==16
    assert read(APP+slots['app_player_movement_commit_inhibited'],1)==(0 if near else 0xA5)
    assert read(APP+slots['app_authorized_checkpoint_count'],1)==0xA5


def test_every_hp_low_byte_and_high_byte_reaches_signed_result_branch(contact):
    cpu,memory,schemas,read,write,run,slots,configure=contact
    hp=PLAYER+schemas['world_object_shared_prefix']['hit_points']
    for high in [0,1,127,255]:
        for low in range(256):
            write(hp,high*256+low,2);cpu.d[0]=0xCAFE0000
            difference=(low-10)&255;survives=0<difference<128
            run(0x800A,stop=0x801E if survives else 0x8032,budget=12)
            assert read(hp,2)==high*256+(difference if survives else low)
            assert cpu.d[0]==0xCAFE0000|difference
            assert read(APP+slots['app_player_movement_commit_inhibited'],1)==255


@pytest.mark.parametrize('low',[11,95,137])
def test_full_rejected_card_survives_updates_only_low_hp_and_returns_early(contact,low):
    cpu,memory,schemas,read,write,run,slots,configure=contact
    cpu.d[0]=0;assert sequencer(cpu,memory,write)(0x4D7DE,budget=4096).stop_reason==1
    configure();o=schemas['world_object_shared_prefix']
    write(PLAYER+o['selected_item_id'],2,1);write(PLAYER+o['hit_points'],0xA500+low,2)
    write(APP+slots['active_world_object_count'],2,2);write(TABLE+4,0xFFFFFF)
    write(APP+slots['app_game_exit_service_ticks_remaining'],0x5A,1)
    trace=sequencer(cpu,memory,write)(0x7DF0,budget=40000)
    assert trace.stop_reason==1 and trace.steps<40000
    assert read(PLAYER+o['hit_points'],2)==0xA500+low-10
    assert not read(PLAYER+o['world_object_flags'],1)&2
    assert read(APP+slots['app_player_movement_commit_inhibited'],1)==255
    assert read(APP+slots['app_game_exit_service_ticks_remaining'],1)==0x5A
    assert read(APP+slots['app_game_event_flags'],1)==128 and cpu.a[7]==0x9004


@pytest.mark.parametrize('low',[0,10,138,255])
def test_full_rejected_card_defeat_installs_animation_exchanges_state_and_queues_outcome(contact,low):
    cpu,memory,schemas,read,write,run,slots,configure=contact
    o,s,n=schemas['world_object_shared_prefix'],schemas['world_position_state_record'],schemas['WorldPositionStateNode']
    write(PLAYER+o['selected_item_id'],2,1);write(PLAYER+o['hit_points'],0xA500+low,2)
    player_descriptor=read(PLAYER+o['position_descriptor_ptr']);previous=read(player_descriptor)
    node=read(DEFEAT+s['state_node_ptr']);assert node
    write(node+n['mode_flags'],0xA5,1);write(node+n['frame_index_and_phase'],0xBEEF,2)
    write(APP+slots['app_context_flags'],32,1)
    write(APP+slots['active_world_object_count'],2,2);write(TABLE+4,0xFFFFFF)
    trace=sequencer(cpu,memory,write)(0x7DF0,budget=60000)
    assert trace.stop_reason==1 and trace.steps<60000
    assert read(player_descriptor)==DEFEAT and read(PLAYER+o['saved_position_state_ptr'])==previous
    assert read(DEFEAT)==DEFEAT_GEOMETRY
    assert read(node+n['mode_flags'],1)==0xA4 and read(node+n['frame_index_and_phase'],2)==0
    assert read(PLAYER+o['hit_points'],2)==0 and read(PLAYER+o['world_object_flags'],1)&2
    assert read(APP+slots['app_game_exit_service_ticks_remaining'],1)==70
    assert read(APP+slots['app_player_movement_commit_inhibited'],1)==255
    assert read(APP+slots['app_game_event_flags'],1)==64
    queue=APP+slots['app_scrolling_message_queue_head']
    assert all(read(queue+4*i) for i in range(3)) and read(queue+12)==0
    assert cpu.a[7]==0x9004


def test_two_unknown_descriptors_share_bit_zero_and_continue_after_audio(contact):
    cpu,memory,schemas,read,write,run,slots,configure=contact
    cpu.d[0]=0;assert sequencer(cpu,memory,write)(0x4D7DE,budget=4096).stop_reason==1
    configure(4)
    second=DESCRIPTORS[4]+64
    write(second,STATE);write(second+4,400,2);write(second+6,400,2)
    write(TABLE+4,second);write(APP+slots['active_world_object_count'],2,2)
    write(PLAYER+schemas['world_object_shared_prefix']['selected_item_id'],255,1)
    write(APP+slots['app_authorized_checkpoint_seen_bits'],0xA0,1)
    write(APP+slots['app_authorized_checkpoint_count'],255,1)
    trace=sequencer(cpu,memory,write)(0x7DF0,budget=10000)
    assert trace.stop_reason==1 and trace.steps<10000
    assert read(APP+slots['app_authorized_checkpoint_seen_bits'],1)==0xA1
    assert read(APP+slots['app_authorized_checkpoint_count'],1)==0
    assert read(APP+slots['app_game_event_flags'],1)==128
    assert cpu.a[0]==TABLE+8 and cpu.a[1]==second and cpu.d[7]&65535==65535
    assert cpu.a[7]==0x9004


def test_four_original_checkpoint_chains_cover_six_nodes_and_keep_clock_bytes(cpu_fixture):
    cpu,memory,schemas,read,write,run=cpu_fixture
    s,n=schemas['world_position_state_record'],schemas['WorldPositionStateNode']
    sizes=[];all_nodes=set()
    for i,descriptor in enumerate(DESCRIPTORS[:4]):
        root=read(descriptor);p=root;states=[];nodes=[]
        assert read(root+s['world_object_flags'],1)&16
        while p:
            assert p not in states and len(states)<4
            states.append(p);node=read(p+s['state_node_ptr']);assert node
            nodes.append(node);all_nodes.add(node)
            write(node+n['mode_flags'],0xA4+i,1);write(node+n['frame_index_and_phase'],0xBEEF,2)
            p=read(p+s['attachment_state_ptr'])
        sizes.append(len(states))
        cpu.a[2]=root;run(0x7FDE,stop=0x7F02,budget=128)
        assert all(read(p+n['mode_flags'],1)==(0xA4+i)|1 for p in nodes)
        cpu.a[2]=root;run(0x7FF4,stop=0x7F02,budget=128)
        assert all(read(p+n['mode_flags'],1)==(0xA4+i)&~1 for p in nodes)
        assert all(read(p+n['frame_index_and_phase'],2)==0xBEEF for p in nodes)
    assert sizes==[1,1,2,2] and len(all_nodes)==6


def test_escape_consumer_uses_card_latch_and_decoded_tile_low_word_only(contact):
    cpu,memory,schemas,read,write,run,slots,configure=contact
    for flags in range(256):
        for tile in [0,235,236,237,0x100EC,65535]:
            cpu.d[0]=tile;write(APP+slots['app_game_event_flags'],flags,1)
            allowed=bool(flags&16) and tile&65535==236
            run(0x977E,stop=0x978C if allowed else 0x97D0,budget=8)
            assert read(APP+slots['app_game_event_flags'],1)==flags


@pytest.mark.parametrize('delay',[0,70,255])
def test_full_escape_consumer_preserves_inherited_exit_delay_and_runs_original_audio(contact,delay):
    cpu,memory,schemas,read,write,run,slots,configure=contact
    write(APP+slots['app_game_event_flags'],0x90,1)
    write(APP+slots['app_authorized_checkpoint_count'],0,1)
    write(APP+slots['app_authorized_checkpoint_seen_bits'],0,1)
    write(APP+slots['app_game_exit_service_ticks_remaining'],delay,1)
    write(APP+slots['app_context_flags'],32,1)
    cpu.d[0]=236
    trace=sequencer(cpu,memory,write)(0x977E,budget=80000)
    assert trace.stop_reason==1 and trace.steps<80000
    s=schemas['world_position_state_record'];player_state=BASE+0x4C72A
    assert read(player_state+s['current_geometry_ptr'])==BASE+0x4C5A4
    assert read(player_state+s['state_node_ptr'])==0
    assert read(APP+slots['app_game_event_flags'],1)==0x58
    assert read(APP+slots['app_game_exit_service_ticks_remaining'],1)==delay
    assert read(APP+slots['app_player_movement_commit_inhibited'],1)==255
    assert read(APP+slots['app_authorized_checkpoint_count'],1)==0
    assert read(APP+slots['app_scrolling_message_queue_head'])
    assert cpu.a[6]==APP and cpu.a[7]==0x9004
