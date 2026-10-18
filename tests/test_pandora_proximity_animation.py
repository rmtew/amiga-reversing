"""Original proximity selection, real feedback and animation consumption in RAM."""
import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_render_order import sequencer

pytestmark = pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
APP, PLAYER = 0x39FC, BASE+0x4C322
TABLE, DESCRIPTOR, STATE, NODE = 0x82000,0x82100,0x82200,0x82300
SEQUENCES = {(True,0):BASE+0x49134,(False,0):BASE+0x49150,
             (True,1):BASE+0x4916C,(False,1):BASE+0x49188}


@pytest.fixture
def proximity(cpu_fixture,title_slots):
    cpu,memory,schemas,read,write,run=cpu_fixture
    o,s,n=schemas['world_object_shared_prefix'],schemas['world_position_state_record'],schemas['WorldPositionStateNode']
    write(TABLE,DESCRIPTOR);write(DESCRIPTOR,STATE)
    write(STATE+s['state_node_ptr'],NODE)
    write(NODE+n['position_descriptor_ptr'],DESCRIPTOR)
    write(NODE+n['frame_count'],6,1);write(NODE+n['phase_step'],64,1)
    write(NODE+n['frame_sequence_ptr'],SEQUENCES[(False,0)])
    write(NODE+n['mode_flags'],1,1);write(NODE+n['frame_index_and_phase'],0xBEEF,2)
    write(APP+title_slots['app_active_world_object_ptr_table'],TABLE)
    write(APP+title_slots['active_world_object_count'],1,2)
    write(PLAYER+o['world_x'],400,2);write(PLAYER+o['world_y'],400,2)
    def configure(variant=0,near=True):
        write(STATE+s['world_object_flags'],1|variant<<5,1)
        write(DESCRIPTOR+4,(408 if variant else 400)+(0 if near else 1000),2)
        write(DESCRIPTOR+6,400,2)
        cpu.a[0],cpu.a[1],cpu.a[2],cpu.a[4],cpu.a[6]=TABLE,DESCRIPTOR,STATE,PLAYER,APP
    configure()
    return cpu,memory,schemas,read,write,run,title_slots,configure


def magnitude(word):
    return (-word)&65535 if word&32768 else word


@pytest.mark.parametrize('variant',[0,1])
def test_every_axis_word_at_both_x_biases(proximity,variant):
    cpu,memory,schemas,read,write,run,slots,configure=proximity
    configure(variant)
    center=408 if variant else 400
    for axis in [4,6]:
        for value in range(65536):
            write(DESCRIPTOR+4,center,2);write(DESCRIPTOR+6,400,2)
            write(DESCRIPTOR+axis,value,2)
            distance=magnitude((value-(center if axis==4 else 400))&65535)
            run(0x7E38,stop=0x7E7C if distance<44 else 0x7EC2,budget=64)
            assert cpu.d[0]&65535==distance


@pytest.mark.parametrize('dx,dy',[(43,0),(44,0),(22,21),(22,22),(-22,-21),
                                   (32768,32768),(32767,32768),(65535,1)])
def test_state_offsets_and_distance_sum_wrap_before_unsigned_threshold(proximity,dx,dy):
    cpu,memory,schemas,read,write,run,slots,configure=proximity
    s=schemas['world_position_state_record']
    write(DESCRIPTOR+4,100,2);write(DESCRIPTOR+6,200,2)
    write(STATE+s['world_x_offset'],(300+dx)&65535,2)
    write(STATE+s['world_y_offset'],(200+dy)&65535,2)
    distance=(magnitude(dx&65535)+magnitude(dy&65535))&65535
    run(0x7E38,stop=0x7E7C if distance<44 else 0x7EC2,budget=64)
    assert cpu.d[0]&65535==distance


def test_isolated_selector_uses_only_variant_bit_five_of_all_state_flag_bytes(proximity):
    cpu,memory,schemas,read,write,run,slots,configure=proximity
    for flags in range(256):
        variant=bool(flags&32);configure(int(variant))
        write(STATE+schemas['world_position_state_record']['world_object_flags'],flags,1)
        run(0x7E38,stop=0x7E90,budget=64)
        assert cpu.a[3]==SEQUENCES[(True,int(variant))]


def test_player_event_and_ui_flags_do_not_gate_the_proximity_role(proximity):
    cpu,memory,schemas,read,write,run,slots,configure=proximity
    for address in [PLAYER+schemas['world_object_shared_prefix']['world_object_flags'],
                    APP+slots['app_game_event_flags'],APP+slots['app_ui_flags']]:
        for flags in range(256):
            write(address,flags,1)
            run(0x7DF0,stop=0x7E90,budget=64)
            assert cpu.a[3]==SEQUENCES[(True,0)]
        write(address,0,1)


@pytest.mark.parametrize('near,variant',[(True,0),(True,1),(False,0),(False,1)])
def test_same_sequence_keeps_every_node_byte_and_skips_audio(proximity,near,variant):
    cpu,memory,schemas,read,write,run,slots,configure=proximity
    n=schemas['WorldPositionStateNode'];configure(variant,near)
    write(NODE+n['frame_sequence_ptr'],SEQUENCES[(near,variant)])
    for flags in range(256):
        write(NODE+n['mode_flags'],flags,1);write(NODE+n['frame_count'],flags,1)
        write(NODE+n['frame_index_and_phase'],0xAB00|flags,2)
        write(APP+slots['app_game_event_flags'],0,1)
        write(APP+slots['app_world_interaction_audio_flags'],255,1)
        before=bytes(memory[NODE:NODE+18])
        cpu.d[0],cpu.d[1]=(0 if near else 44),0
        run(0x7E74,stop=0x7F02,budget=32)
        assert memory[NODE:NODE+18]==before
        assert read(APP+slots['app_game_event_flags'],1)==0
        assert read(APP+slots['app_world_interaction_audio_flags'],1)==255


@pytest.mark.parametrize('start,near',[(0x7EA8,True),(0x7EEE,False)])
def test_transition_store_preserves_count_step_xy_and_unrelated_mode_bits(proximity,start,near):
    cpu,memory,schemas,read,write,run,slots,configure=proximity
    n=schemas['WorldPositionStateNode'];target=SEQUENCES[(near,0)]
    for flags in range(256):
        write(NODE+n['mode_flags'],flags,1);write(NODE+n['frame_count'],flags,1)
        write(NODE+n['phase_step'],255-flags,1);write(NODE+n['xy_sequence_ptr'],0x88776654)
        write(NODE+n['frame_index_and_phase'],0xBEEF,2)
        expected=bytearray(memory[NODE:NODE+18]);expected[6:10]=target.to_bytes(4,'big')
        expected[10]=(flags&~1)|4;expected[16:18]=bytes(2)
        cpu.a[0],cpu.a[3],cpu.a[5]=TABLE,target,NODE
        run(start,stop=0x7F02,budget=16)
        assert memory[NODE:NODE+18]==expected and cpu.a[0]==TABLE and cpu.a[7]==0x9000


@pytest.mark.parametrize('near,variant',[(True,0),(True,1),(False,0),(False,1)])
def test_full_transition_runs_original_audio_and_balances_iteration_stack(proximity,near,variant):
    cpu,memory,schemas,read,write,run,slots,configure=proximity
    cpu.d[0]=0;assert sequencer(cpu,memory,write)(0x4D7DE,budget=4096).stop_reason==1
    configure(variant,near);n=schemas['WorldPositionStateNode']
    write(NODE+n['frame_sequence_ptr'],SEQUENCES[(not near,variant)])
    write(APP+slots['app_world_interaction_audio_flags'],0xA5,1)
    write(APP+slots['app_game_event_flags'],0x16,1)
    expected=bytearray(memory[NODE:NODE+18]);expected[6:10]=SEQUENCES[(near,variant)].to_bytes(4,'big')
    expected[10]=(expected[10]&~1)|4;expected[16:18]=bytes(2)
    trace=sequencer(cpu,memory,write)(0x7DF0,budget=10000)
    assert trace.stop_reason==1 and trace.steps<10000
    assert memory[NODE:NODE+18]==expected
    assert read(APP+slots['app_world_interaction_audio_flags'],1)==0xA4
    assert read(APP+slots['app_game_event_flags'],1)==0x96
    assert cpu.a[0]==TABLE+4 and cpu.a[3]==SEQUENCES[(near,variant)]
    assert cpu.a[4]==PLAYER and cpu.a[5]==NODE and cpu.a[6]==APP and cpu.a[7]==0x9004
    assert cpu.d[7]&65535==65535


@pytest.mark.parametrize('variant',[0,1])
def test_near_and_far_cycles_reach_held_geometry_and_do_not_restart(proximity,variant):
    cpu,memory,schemas,read,write,run,slots,configure=proximity
    cpu.d[0]=0;assert sequencer(cpu,memory,write)(0x4D7DE,budget=4096).stop_reason==1
    for near in [True,False]:
        configure(variant,near)
        trace=sequencer(cpu,memory,write)(0x7DF0,budget=10000);assert trace.stop_reason==1
        sequence=SEQUENCES[(near,variant)]
        for tick in range(1,13):
            cpu.a[4]=STATE;run(0x951A,budget=64)
            if tick%2==0:
                expected=read(sequence if tick==12 else sequence+4+4*(tick//2))
                assert read(STATE)==expected
        assert read(NODE+10,1)==5 and read(NODE+16,2)==0x0500
        assert read(STATE)==read(sequence)
        for _ in range(2):
            cpu.a[4]=STATE;run(0x951A,budget=64)
            assert read(NODE+16,2)==0x0500 and read(STATE)==read(sequence)
        before=bytes(memory[NODE:NODE+18]);write(APP+slots['app_game_event_flags'],0,1)
        run(0x7DF0,budget=256)
        assert memory[NODE:NODE+18]==before and read(APP+slots['app_game_event_flags'],1)==0


def test_all_phase_step_bytes_use_wrapped_negative_result_not_addition_carry(proximity):
    cpu,memory,schemas,read,write,run,slots,configure=proximity
    for phase in range(256):
        for step in range(256):
            write(NODE+17,phase,1);write(NODE+5,step,1)
            cpu.a[0]=NODE;result=(phase+step)&255
            run(0x9556,stop=0x9568 if result&128 else 0x95E0,budget=8)
            if not result&128:assert read(NODE+17,1)==result


@pytest.mark.parametrize('changed_first',[False,True])
def test_multiple_descriptors_preserve_cursor_after_audio_and_skip_null_state(proximity,changed_first):
    cpu,memory,schemas,read,write,run,slots,configure=proximity
    cpu.d[0]=0;assert sequencer(cpu,memory,write)(0x4D7DE,budget=4096).stop_reason==1
    configure();s,n=schemas['world_position_state_record'],schemas['WorldPositionStateNode']
    second_d,second_s,second_n=DESCRIPTOR+64,STATE+64,NODE+32
    write(TABLE+4,second_d);write(TABLE+8,DESCRIPTOR+128)
    write(second_d,second_s);write(second_d+4,1408,2);write(second_d+6,400,2)
    write(second_s+s['world_object_flags'],33,1);write(second_s+s['state_node_ptr'],second_n)
    write(second_n+n['frame_count'],3,1);write(second_n+n['phase_step'],64,1)
    write(second_n+n['mode_flags'],1,1);write(second_n+n['frame_index_and_phase'],0xABCD,2)
    for p,current in [(NODE,SEQUENCES[(not changed_first,0)]),(second_n,SEQUENCES[(not changed_first,1)])]:write(p+6,current)
    write(APP+slots['active_world_object_count'],3,2)
    trace=sequencer(cpu,memory,write)(0x7DF0,budget=10000)
    assert trace.stop_reason==1 and trace.steps<10000
    assert read(NODE+6)==SEQUENCES[(True,0)] and read(second_n+6)==SEQUENCES[(False,1)]
    assert read(NODE+16,2)==(0 if changed_first else 0xBEEF)
    assert read(second_n+16,2)==(0xABCD if changed_first else 0)
    assert read(second_n+4,1)==3
    assert cpu.a[0]==TABLE+12 and cpu.a[1]==DESCRIPTOR+128 and cpu.d[7]&65535==65535
    assert cpu.a[7]==0x9004


def test_all_eighteen_original_proximity_nodes_switch_with_real_feedback(cpu_fixture,title_slots):
    cpu,memory,schemas,read,write,run=cpu_fixture
    s,n,o=schemas['world_position_state_record'],schemas['WorldPositionStateNode'],schemas['world_object_shared_prefix']
    cpu.a[6]=APP;cpu.d[0]=0
    assert sequencer(cpu,memory,write)(0x4D7DE,budget=4096).stop_reason==1
    write(APP+title_slots['app_active_world_object_ptr_table'],TABLE)
    write(APP+title_slots['active_world_object_count'],1,2)
    nodes=set();variants=set()
    for i in range(18):
        descriptor=BASE+0x48BF8+12*i;state=read(descriptor)
        flags=read(state+s['world_object_flags'],1);variant=(flags>>5)&1
        assert flags&21==1 and not read(state+s['interaction_flags'],1)&1
        node=read(state+s['state_node_ptr']);assert node and node not in nodes
        nodes.add(node);variants.add(variant)
        assert read(node+n['frame_count'],1)==6 and read(node+n['phase_step'],1)==64
        initial=read(node+n['frame_sequence_ptr']);assert initial in SEQUENCES.values()
        near=initial not in [SEQUENCES[(True,0)],SEQUENCES[(True,1)]]
        assert read(node+n['xy_sequence_ptr'])==0
        write(node+n['frame_index_and_phase'],0xBEEF,2)
        expected=bytearray(memory[node:node+18]);expected[6:10]=SEQUENCES[(near,variant)].to_bytes(4,'big')
        expected[10]=(expected[10]&~1)|4;expected[16:18]=bytes(2)
        x=(read(descriptor+4,2)+read(state+s['world_x_offset'],2)-(8 if variant else 0)+(0 if near else 1000))&65535
        y=(read(descriptor+6,2)+read(state+s['world_y_offset'],2))&65535
        write(PLAYER+o['world_x'],x,2);write(PLAYER+o['world_y'],y,2)
        write(TABLE,descriptor);cpu.a[6]=APP
        trace=sequencer(cpu,memory,write)(0x7DF0,budget=10000)
        assert trace.stop_reason==1 and trace.steps<10000
        assert memory[node:node+18]==expected and cpu.a[7]==0x9004
    assert len(nodes)==18 and variants=={0,1}
