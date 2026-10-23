"""Original NPC feedback and secondary playback in controlled RAM/MMIO shadows.

No DMA, audible output, ordinary call order or gameplay reachability is claimed.
Whole callback calls use real audio initialization/dispatch. Large initialization
writes can exceed bounded summaries; assertions inspect guest memory and returns.
"""
import itertools

import pytest

from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import resolve_project_paths
from tests.test_pandora_state_transitions import BASE, TARGET, cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_render_order import sequencer
from tests.test_pandora_message_queue import initialize, APP, HEAD, TAIL, CONTEXT

pytestmark = pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
CALLBACKS = {'wackobrain':(0x4D44A,0,8,5), 'menial':(0x4D496,2,19,1),
             'gardener':(0x4D4C4,2,23,2), 'sequence214':(0x4D4F2,2,20,3)}
STATES, DMA, CONFIGS = BASE+0x4E5F6, BASE+0x4E690, BASE+0x4E6C0
SERVICE, DISPATCH = 0x4E512, 0x4E4AE
NPC, FIXED_STATE, ENVELOPE = 0x82000, 0x85000, 0x88000


@pytest.fixture
def feedback(cpu_fixture,title_slots):
    cpu,memory,schemas,read,write,run = cpu_fixture
    m = effective_target_metadata(resolve_project_paths(TARGET).target_dir)
    names = {e.name:BASE+e.addr for e in m.seeded_entities if e.name}
    sizes = {s.name:s.size for s in m.custom_structs}
    constants = {e.name:e.value for e in m.target_equates}
    cpu.d[0] = 0
    assert sequencer(cpu,memory,write)(0x4D7DE,budget=4096).stop_reason == 1
    slots = title_slots
    p,d = schemas['audio_channel_playback_state'],schemas['audio_channel_dma_configuration']
    assert sizes['audio_channel_playback_state'] == 38
    assert sizes['audio_channel_dma_configuration'] == 12
    assert sizes['audio_sequence_channel_configuration'] == 22
    fixed_descriptor = names['wackobrain_actor_positions_49492_2']
    write(fixed_descriptor,FIXED_STATE)
    write(FIXED_STATE,0x11111111)
    milestones = [names['wackobrain_actor_frames_49492_1'+suffix] for suffix in ['',
                  '_bitplane_data_ptr_10','_bitplane_data_ptr_17','_bitplane_data_ptr_24']]
    headers = sorted({BASE+e.addr for e in m.seeded_entities if e.name and
                      e.name.startswith('wackobrain_actor_frames_49492_1') and
                      e.struct_name=='WorldPositionAnimationFrame' and e.field_name=='bitplane_data_ptr'})
    assert len(headers) == 43 and set(milestones) <= set(headers)

    def call(name):
        cpu.a[5],cpu.a[6] = NPC,APP
        trace = sequencer(cpu,memory,write)(CALLBACKS[name][0],budget=4096)
        assert trace.stop_reason == 1 and trace.steps < 4096
        assert cpu.a[5] == NPC and cpu.a[6] == APP and cpu.a[7] == 0x9004
        assert not cpu.sr & 1

    return cpu,memory,read,write,run,slots,p,d,constants,milestones,headers,call


def flag_slot(slots,name):
    return APP+slots['app_world_interaction_flags' if name=='wackobrain' else 'app_world_interaction_audio_flags']


def state_address(channel):return STATES+38*channel

def dma_address(channel):return DMA+12*channel


def arm_service(feedback,channel=2):
    cpu,memory,read,write,run,slots,p,d,*_ = feedback
    state, dma = state_address(channel),dma_address(channel)
    memory[state:state+38] = bytes(38)
    memory[dma:dma+12] = bytes(12)
    for field,value,width in [('active',255,1),('playback_ticks_remaining',10,1),
                              ('current_period',0x400,2),('sequence_countdown',2,1)]:
        write(state+p[field],value,width)
    write(BASE+0x4E93E,0x90000)
    cpu.a[0],cpu.a[1],cpu.a[4],cpu.d[2] = 0xDFF000+16*channel,state,dma,1<<channel
    return state,dma


def test_all_ui_bytes_gate_four_callbacks_before_pending_or_audio_writes(feedback):
    cpu,memory,read,write,run,slots,p,d,constants,milestones,headers,call = feedback
    for name,(_,channel,config,bit) in CALLBACKS.items():
        state = state_address(channel)
        for ui in range(256):
            write(APP+slots['app_ui_flags'],ui,1)
            write(APP+slots['app_world_interaction_flags'],0,1)
            write(APP+slots['app_world_interaction_audio_flags'],0,1)
            memory[state:state+38] = b'\xA5'*38
            call(name)
            if ui & 2:
                assert memory[state:state+38] == b'\xA5'*38
                assert read(flag_slot(slots,name),1) == 0
            else:
                assert memory[state:state+22] == memory[CONFIGS+22*config:CONFIGS+22*(config+1)]
                assert read(state+p['active'],1) == 255
                assert read(flag_slot(slots,name),1) == 1<<bit


def test_all_pending_flag_bytes_keep_other_bits_and_first_start_ignores_old_ticks(feedback):
    cpu,memory,read,write,run,slots,p,d,constants,milestones,headers,call = feedback
    write(APP+slots['app_ui_flags'],0,1)
    for name,(_,channel,config,bit) in CALLBACKS.items():
        state, flags = state_address(channel),flag_slot(slots,name)
        for value in range(256):
            write(flags,value,1)
            write(state+p['playback_ticks_remaining'],73,1)
            write(state+p['active'],0,1)
            before = bytes(memory[state:state+38])
            call(name)
            if value & (1<<bit):
                assert bytes(memory[state:state+38]) == before
                assert read(flags,1) == value
            else:
                assert memory[state:state+22] == memory[CONFIGS+22*config:CONFIGS+22*(config+1)]
                assert read(flags,1) == ((value | (1<<bit)) if name=='wackobrain' else (value | (1<<bit)) & ~1)


def test_all_tick_bytes_rearm_pending_channel_two_callbacks_only_at_zero(feedback):
    cpu,memory,read,write,run,slots,p,d,constants,milestones,headers,call = feedback
    write(APP+slots['app_ui_flags'],0,1)
    state = state_address(2)
    for name in ['menial','gardener','sequence214']:
        _,_,config,bit = CALLBACKS[name]
        for active in [0,255]:
            for ticks in range(256):
                write(flag_slot(slots,name),1<<bit,1)
                write(state+p['playback_ticks_remaining'],ticks,1)
                write(state+p['active'],active,1)
                before = bytes(memory[state:state+38])
                call(name)
                if ticks:assert bytes(memory[state:state+38]) == before
                else:
                    assert memory[state:state+22] == memory[CONFIGS+22*config:CONFIGS+22*(config+1)]
                    assert read(state+p['active'],1) == 255
                assert read(flag_slot(slots,name),1) == 1<<bit


def test_wackobrain_uses_fixed_current_geometry_and_restarts_on_every_matching_visit(feedback):
    cpu,memory,read,write,run,slots,p,d,constants,milestones,headers,call = feedback
    write(APP+slots['app_ui_flags'],0,1)
    state = state_address(0)
    for geometry in [*headers,0,0xFFFFFFFF,*[v+1 for v in milestones]]:
        write(FIXED_STATE,geometry)
        write(flag_slot(slots,'wackobrain'),32,1)
        write(state+p['playback_ticks_remaining'],7,1)
        before = bytes(memory[state:state+38])
        call('wackobrain')
        if geometry in milestones:
            assert read(state+p['playback_ticks_remaining'],1) == 50
            write(state+p['playback_ticks_remaining'],3,1)
            call('wackobrain')
            assert read(state+p['playback_ticks_remaining'],1) == 50
        else:assert bytes(memory[state:state+38]) == before
        assert read(flag_slot(slots,'wackobrain'),1) == 32
    write(FIXED_STATE,0x11111111)
    write(flag_slot(slots,'wackobrain'),0,1)
    call('wackobrain')  # First visit starts without a geometry match.
    assert read(state+p['playback_ticks_remaining'],1) == 50


def test_shared_channel_preemption_and_zero_tick_replay_depend_on_callback_order(feedback):
    cpu,memory,read,write,run,slots,p,d,constants,milestones,headers,call = feedback
    state = state_address(2)
    write(APP+slots['app_ui_flags'],0,1)
    for order in itertools.permutations(['menial','gardener','sequence214']):
        write(APP+slots['app_world_interaction_audio_flags'],0,1)
        for name in order:call(name)
        last = CALLBACKS[order[-1]][2]
        assert memory[state:state+22] == memory[CONFIGS+22*last:CONFIGS+22*(last+1)]
        assert read(APP+slots['app_world_interaction_audio_flags'],1) == 14
        # The real four-channel dispatcher expires the selected secondary voice.
        for channel in range(4):write(state_address(channel)+p['active'],int(channel==2),1)
        write(state+p['playback_ticks_remaining'],1,1)
        write(dma_address(2)+d['enabled'],0,1)
        run(DISPATCH,budget=512)
        assert read(state+p['playback_ticks_remaining'],1) == 0 and read(state+p['active'],1) == 0
        for name in order:call(name)
        first = CALLBACKS[order[0]][2]
        assert memory[state:state+22] == memory[CONFIGS+22*first:CONFIGS+22*(first+1)]
        assert read(APP+slots['app_world_interaction_audio_flags'],1) == 14


def test_real_reset_retains_pending_ticks_and_inactive_dispatch_cannot_drain_them(feedback):
    cpu,memory,read,write,run,slots,p,d,constants,milestones,headers,call = feedback
    write(APP+slots['app_ui_flags'],0,1)
    write(APP+slots['app_world_interaction_audio_flags'],0,1)
    call('menial')
    state = state_address(2)
    ticks = read(state+p['playback_ticks_remaining'],1)
    cpu.a[6] = APP
    run(0x4D368,budget=256)
    assert read(state+p['active'],1) == 0
    for _ in range(3):
        run(DISPATCH,budget=128)
        call('menial')
        assert read(state+p['playback_ticks_remaining'],1) == ticks == 20
        assert read(state+p['active'],1) == 0
        assert read(APP+slots['app_world_interaction_audio_flags'],1) & 2
    call('gardener')  # Its clear pending bit can replace the inactive voice.
    assert read(state+p['playback_ticks_remaining'],1) == 30 and read(state+p['active'],1) == 255


def test_real_nearby_dispatcher_skips_all_four_feedback_messages_and_keeps_object_state(feedback):
    cpu,memory,read,write,run,slots,p,d,constants,milestones,headers,call = feedback
    o = effective_target_metadata(resolve_project_paths(TARGET).target_dir)
    fields = next(s for s in o.custom_structs if s.name=='world_object_shared_prefix')
    f = {a.name:a.offset for a in fields.fields}
    for name,(entry,_,_,_) in CALLBACKS.items():
        initialize((cpu,memory,{},read,write,run),slots)
        write(APP+CONTEXT,32,1);write(APP+slots['app_nearby_object_prompt_countdown'],0,1)
        write(APP+slots['app_ui_flags'],0,1)
        write(APP+slots['app_world_interaction_flags'],0,1)
        write(APP+slots['app_world_interaction_audio_flags'],0,1)
        memory[NPC:NPC+84] = bytes(84)
        write(NPC+f['interaction_callback'],BASE+entry)
        write(NPC+f['interaction_message_ptr'],0x80000)
        write(NPC+f['context_prompt_cooldown'],77,2)
        memory[0x80000:0x80008] = b'MESSAGE\0'
        before = bytes(memory[NPC:NPC+84])
        cpu.a[5],cpu.a[6] = NPC,APP
        trace = sequencer(cpu,memory,write)(0x83F6,budget=8192)
        assert trace.stop_reason == 1 and cpu.a[7] == 0x9004
        assert read(APP+HEAD) == 0 and read(APP+TAIL) == APP+HEAD
        assert bytes(memory[NPC:NPC+84]) == before


def test_secondary_expiry_precedes_update_disable_and_restarts_fallback_on_all_channels(feedback):
    cpu,memory,read,write,run,slots,p,d,*_ = feedback
    for channel in range(4):
        for ticks in range(256):
            state,dma = arm_service(feedback,channel)
            write(state+p['playback_ticks_remaining'],ticks,1)
            write(state+p['update_disabled'],255,1)
            write(dma+d['start_pending'],255,1)
            write(0xDFF096,0x1234,2)
            run(SERVICE,budget=128)
            assert read(state+p['playback_ticks_remaining'],1) == (ticks-1)&255
            assert read(state+p['active'],1) == (0 if ticks==1 else 255)
            assert read(dma+d['start_pending'],1) == (0 if ticks==1 else 255)
            assert read(0xDFF096,2) == (1<<channel if ticks==1 else 0x1234)
        state,dma = arm_service(feedback,channel)
        write(state+p['playback_ticks_remaining'],1,1);write(state+p['update_disabled'],255,1)
        for field,value,width in [('sample_ptr',0x91234,4),('sample_length',0x123,2),
                                  ('sample_period',0x321,2),('sample_volume',0x2A,2),('enabled',255,1)]:
            write(dma+d[field],value,width)
        run(SERVICE,budget=128)
        hw = 0xDFF0A0+16*channel
        assert [read(hw),read(hw+4,2),read(hw+6,2),read(hw+8,2)] == [0x91234,0x123,0x321,0x2A]
        assert read(0xDFF096,2) == 0x8200|(1<<channel)


def test_outer_secondary_dispatch_uses_nonzero_active_bytes_and_preserves_inactive_ticks(feedback):
    cpu,memory,read,write,run,slots,p,d,*_ = feedback
    for channel in range(4):
        for active in range(256):
            for other in range(4):
                write(state_address(other)+p['active'],0,1)
                write(state_address(other)+p['playback_ticks_remaining'],99,1)
            state,dma = arm_service(feedback,channel)
            write(state+p['active'],active,1);write(state+p['playback_ticks_remaining'],1,1)
            run(DISPATCH,budget=512)
            assert read(state+p['playback_ticks_remaining'],1) == (0 if active else 1)
            assert read(state+p['active'],1) == 0
            for other in range(4):
                if other!=channel:assert read(state_address(other)+p['playback_ticks_remaining'],1) == 99


def test_all_pair_selector_bytes_rotate_independently_and_sample_offsets_sign_extend(feedback):
    cpu,memory,read,write,run,slots,p,d,*_ = feedback
    for channel in range(4):
        for select in range(256):
            state,dma = arm_service(feedback,channel)
            sample_select = (select*73+17)&255
            for field,value,width in [('period_delta_interval',3,1),('period_delta_countdown',1,1),
                ('period_delta_step_pair',0x1234FFFE,4),('period_delta_select',select,1),
                ('current_period',0x100,2),('period_delta',0xFFFF,2),
                ('sample_address_offset_pair',0x80017FFF,4),('sample_address_offset_select',sample_select,1)]:
                write(state+p[field],value,width)
            run(SERVICE,budget=256)
            expected = (0x100+(0xFFFE if select&1 else 0x1234)-1)&65535
            assert read(state+p['current_period'],2) == expected
            assert read(state+p['period_delta_select'],1) == (select>>1)|((select&1)<<7)
            assert read(state+p['sample_address_offset_select'],1) == (sample_select>>1)|((sample_select&1)<<7)
            offset = 32767 if sample_select&1 else -32767
            assert read(0xDFF0A0+16*channel) == 0x90000+offset
            assert read(0xDFF0A6+16*channel,2) == expected


def test_secondary_envelope_sign_pointer_hold_and_countdown_underflow(feedback):
    cpu,memory,read,write,run,slots,p,d,*_ = feedback
    for value in range(256):
        state,dma = arm_service(feedback)
        write(state+p['sequence_countdown'],1,1);write(state+p['sequence_interval'],5,1)
        write(state+p['volume_sequence_cursor'],ENVELOPE)
        memory[ENVELOPE:ENVELOPE+2] = bytes([value,0xA5])
        write(0xDFF0C8,0xBEEF,2)
        run(SERVICE,budget=256)
        assert read(state+p['sequence_countdown'],1) == 5
        assert read(state+p['volume_sequence_cursor']) == ENVELOPE+(value<128)
        assert read(0xDFF0C8,2) == (value if value<128 else 0xBEEF)
    for countdown in [0,1,2,255]:
        for interval in [0,1,7,255]:
            state,dma = arm_service(feedback)
            write(state+p['sequence_countdown'],countdown,1);write(state+p['sequence_interval'],interval,1)
            write(state+p['volume_sequence_cursor'],ENVELOPE);write(ENVELOPE,0x7F,1)
            run(SERVICE,budget=256)
            assert read(state+p['sequence_countdown'],1) == (interval if countdown==1 else (countdown-1)&255)
            assert read(state+p['volume_sequence_cursor']) == ENVELOPE+(countdown==1)


def test_period_reset_precedes_signed_minimum_clamp_and_word_addition_wraps(feedback):
    cpu,memory,read,write,run,slots,p,d,*_ = feedback
    for period in [0,1,123,124,125,32767,32768,65534,65535]:
        state,dma = arm_service(feedback)
        write(state+p['current_period'],0xFFFF,2);write(state+p['period_delta'],2,2)
        write(state+p['period_reset_interval'],7,1);write(state+p['period_reset_countdown'],1,1)
        write(state+p['period_reset_value'],period,2)
        run(SERVICE,budget=256)
        assert read(state+p['current_period'],2) == period
        assert read(state+p['period_reset_countdown'],1) == 7
        assert read(0xDFF0C6,2) == (period if 124<=period<32768 else 124)
    state,dma = arm_service(feedback)
    write(state+p['current_period'],0xFFFF,2);write(state+p['period_delta'],2,2)
    run(SERVICE,budget=256)
    assert read(state+p['current_period'],2) == 1 and read(0xDFF0C6,2) == 124


def test_secondary_start_copies_interval_byte_pair_into_both_countdowns(feedback):
    cpu,memory,read,write,run,slots,p,d,*_ = feedback
    for channel,config in [(0,8),(2,19),(2,20),(2,23)]:
        for reset_interval,delta_interval in [(0x12,0x34),(0,255),(255,0)]:
            source = CONFIGS+22*config
            write(source+p['period_reset_interval'],reset_interval,1)
            write(source+p['period_delta_interval'],delta_interval,1)
            cpu.d[0] = (channel<<8)|config
            trace = sequencer(cpu,memory,write)(0x4E3EC,budget=4096)
            assert trace.stop_reason == 1 and cpu.a[7] == 0x9004
            target = state_address(channel)
            assert memory[target:target+22] == memory[source:source+22]
            assert read(target+p['period_reset_countdown'],1) == reset_interval
            assert read(target+p['period_delta_countdown'],1) == delta_interval
            assert read(target+p['sequence_countdown'],1) == 1
            assert read(target+p['active'],1) == 255
            assert read(dma_address(channel)+d['start_pending'],1) == 255
