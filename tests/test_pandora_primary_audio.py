"""Original primary sequencer arithmetic and CPU audio-register packets.

Explicit RAM/MMIO inputs, no patched instructions or DMA/audible-output claim.
Injected out-of-prefix selectors and stream bytes do not prove normal programs.
"""
import pytest

from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import resolve_project_paths
from tests.test_pandora_state_transitions import BASE,TARGET,cpu_fixture
from tests.test_pandora_render_order import sequencer

pytestmark=pytest.mark.parametrize('cpu_fixture',[0x1000000],indirect=True)
PLAYER,GLOBAL,CHANNEL,DMA,PROGRAM,META,VOLUME,PITCH,SAMPLE=0x5d7de,0x5dcfe,0x81000,0x82000,0x83000,0x84000,0x85000,0x86000,0x87000
SCALARS=0x5ddd4


@pytest.fixture
def primary(cpu_fixture):
    cpu,memory,schemas,read,write,run=cpu_fixture
    metadata=effective_target_metadata(resolve_project_paths(TARGET).target_dir)
    names={a.name:BASE+a.addr for a in metadata.seeded_entities if a.name}
    names.update({a.name:BASE+a.addr for a in metadata.seeded_code_labels if a.name})
    names.update({a.name:a.addr for a in metadata.absolute_code_labels if a.name})
    st,cfg,sm,g=(schemas[k] for k in ['audio_channel_runtime_state','audio_channel_dma_configuration','audio_sample_metadata','audio_player_global_state'])
    def field(base,layout,name,value,size):write(base+layout[name],value,size)
    def prepare(channel=2):
        memory[CHANNEL:CHANNEL+48]=bytes(48);memory[DMA:DMA+12]=bytes(12);memory[META:META+12]=bytes(12)
        memory[PROGRAM:PROGRAM+32]=bytes([36,0x82])+bytes(30)
        memory[VOLUME:VOLUME+4]=bytes([32,0xc0,0,0]);memory[PITCH:PITCH+4]=bytes([0,0x80,0,0])
        for name,value,size in [('program_cursor',PROGRAM,4),('sample_metadata_ptr',META,4),('sample_start_pending',255,1),('volume_sequence_start_ptr',VOLUME,4),('volume_sequence_cursor',VOLUME,4),('volume_sequence_interval',1,1),('volume_sequence_countdown',1,1),('pitch_sequence_start_ptr',PITCH,4),('pitch_sequence_cursor',PITCH,4),('current_note',36,1),('update_reload_countdown',5,2),('update_countdown',3,2)]:field(CHANNEL,st,name,value,size)
        for name,value,size in [('sample_ptr',SAMPLE,4),('sample_start_byte_offset',0,4),('sample_length',64,2),('sample_period',400,2)]:field(META,sm,name,value,size)
        for name,value,size in [('duration_multiplier',1,2),('master_volume',64,2),('global_note_offset',0,1)]:field(GLOBAL,g,name,value,size)
        field(GLOBAL,g,'silence_sample_ptr',SAMPLE+0x100,4)
        for i in range(4):memory[0xdff0a0+16*i:0xdff0aa+16*i]=bytes(10)
        cpu.a[0],cpu.a[1],cpu.a[3],cpu.a[4],cpu.a[5],cpu.a[6]=CHANNEL,PROGRAM,PLAYER,DMA,META,0xdff000+16*channel
        cpu.d[7]=channel
    def call(source,stop,budget=1024):
        trace=sequencer(cpu,memory,write)(source,stop=stop,budget=budget)
        assert trace.stop_reason==1 and trace.steps<budget
        return trace
    prepare()
    assert read(SCALARS,2)==0x2000 and read(SCALARS+72*2,2)!=0x2000
    return cpu,memory,read,write,st,cfg,sm,g,names,metadata,prepare,call


def test_all_token_bytes_partition_without_an_invented_control_bound(primary):
    cpu,memory,read,write,st,cfg,sm,g,names,metadata,prepare,call=primary
    for token in range(256):
        prepare();write(PROGRAM,token,1)
        trace=sequencer(cpu,memory,write)(0x4da1a,budget=3)
        assert trace.stop_reason==3 and cpu.pc==BASE+(0x4da22 if token<128 else 0x4dba8)
        assert cpu.a[1]==PROGRAM+1
        if token<128:continue
        if token<0xa0:
            call(0x4dba8,0x4dc20)
            # Only inspect the unchecked table index, never execute unknown targets.
            call(0x4dc20,0x4dc2a)
            assert cpu.d[0]&255==2*(token-0x80)
            table=names['audio_control_opcode_handler_offsets']
            expected=read(table+2*(token-0x80),2)
            assert cpu.a[2]&65535==expected
        else:
            call(0x4dba8,0x4da1a)
            if token>=0xe0:assert read(CHANNEL+st['update_reload_countdown'],2)==token-223
            elif token>=0xc0:
                expected=names['audio_sample_metadata']+12*(token-0xc0)
                assert cpu.a[5]==read(CHANNEL+st['sample_metadata_ptr'])==expected
            elif token>=0xb0:
                offset=read(names['audio_volume_sequence_offset_table']+2*(token-0xb0),2)
                expected=PLAYER+(offset if offset<32768 else offset-65536)
                assert read(CHANNEL+st['volume_sequence_start_ptr'])==expected
                assert read(CHANNEL+st['volume_sequence_cursor'])==VOLUME
                assert read(CHANNEL+st['volume_sequence_interval'],1)==read(expected-1,1)
            else:
                offset=read(names['audio_pitch_sequence_offset_table']+2*(token-0xa0),2)
                expected=PLAYER+(offset if offset<32768 else offset-65536)
                assert read(CHANNEL+st['pitch_sequence_start_ptr'])==read(CHANNEL+st['pitch_sequence_cursor'])==expected, (hex(token),hex(offset),hex(cpu.a[3]),hex(cpu.a[2]),hex(expected))


def test_signed_multiplier_operand_is_consumed_by_unsigned_word_duration_product(primary):
    cpu,memory,read,write,st,cfg,sm,g,names,metadata,prepare,call=primary
    handler=names['set_audio_duration_multiplier_from_signed_byte']-BASE
    for operand in range(256):
        prepare();write(PROGRAM,operand,1);call(handler,0x4da1a)
        multiplier=operand if operand<128 else operand+0xff00
        assert read(GLOBAL+g['duration_multiplier'],2)==multiplier
        for token in [0xe0,0xe1,0xef,0xfe,0xff]:
            cpu.d[0]=token;call(0x4dba8,0x4da1a)
            assert read(CHANNEL+st['update_reload_countdown'],2)==((token-223)*multiplier)&65535


def test_attack_note_offsets_wrap_as_byte_before_unchecked_scalar_lookup(primary):
    cpu,memory,read,write,st,cfg,sm,g,names,metadata,prepare,call=primary
    for global_offset in range(256):
        for channel_offset in [0,127,255]:
            prepare();write(GLOBAL+g['global_note_offset'],global_offset,1);write(CHANNEL+st['note_offset'],channel_offset,1)
            index=(36+global_offset+channel_offset)&255;expected=(read(SCALARS+2*index,2)*400)>>10
            call(0x4da1a,0x4daae)
            assert read(CHANNEL+st['current_note'],1)==36 and read(CHANNEL+st['program_cursor'])==PROGRAM+1
            assert read(DMA+cfg['sample_period'],2)==read(0xdff0c6,2)==expected&65535
            assert read(CHANNEL+st['sample_start_pending'],1)==0
    # Indices72..255 above are explicit injected offsets, beyond the72-word table.


def test_attack_and_later_volume_markers_have_different_byte_treatment(primary):
    cpu,memory,read,write,st,cfg,sm,g,names,metadata,prepare,call=primary
    for value in range(256):
        for master in [64,65535]:
            for pending in [0,1]:
                prepare();write(VOLUME,value,1);write(GLOBAL+g['master_volume'],master,2);write(DMA+cfg['start_pending'],pending,1)
                call(0x4da1a,0x4daae)
                extended=value if value<128 else value+0xff00
                expected=((extended*master)&65535)>>6
                assert read(DMA+cfg['sample_volume'],2)==expected
                assert read(0xdff0c8,2)==(0 if pending else expected)
                assert read(CHANNEL+st['volume_sequence_cursor'])==VOLUME+1
                write(CHANNEL+st['volume_sequence_cursor'],VOLUME);write(CHANNEL+st['volume_sequence_countdown'],0,1)
                call(0x4db72,0x4dba4)
                expected=(((value&127)*master)&65535)>>6
                assert read(DMA+cfg['sample_volume'],2)==expected
                assert read(CHANNEL+st['volume_sequence_cursor'])==(VOLUME if value&128 else VOLUME+1)
                assert read(0xdff0c8,2)==(0 if pending else expected)


def test_sample_resume_uses_signed_byte_offset_but_word_length_arithmetic(primary):
    cpu,memory,read,write,st,cfg,sm,g,names,metadata,prepare,call=primary
    for offset in [0,1,2,3,127,128,0x7fffffff,0x80000000,0xffffffff]:
        for length in [0,1,64,65535]:
            for pending in [0,1]:
                for installed in [0,1,128,255]:
                    prepare();write(META+sm['sample_start_byte_offset'],offset);write(META+sm['sample_length'],length,2)
                    write(CHANNEL+st['sample_start_pending'],installed,1);write(DMA+cfg['start_pending'],pending,1)
                    call(0x4d990,0x4d9ec)
                    if installed:
                        assert read(DMA)==0 and read(DMA+cfg['sample_length'],2)==0
                    else:
                        pointer=SAMPLE+0x100 if offset&0x80000000 else (SAMPLE+offset)&0xffffffff
                        words=32 if offset&0x80000000 else (length-(offset>>1))&65535
                        assert read(DMA+cfg['sample_ptr'])==pointer and read(DMA+cfg['sample_length'],2)==words
                        assert read(0xdff0c0)==(0 if pending else pointer)
                        assert read(0xdff0c4,2)==(0 if pending else words)
                        assert read(CHANNEL+st['sample_start_pending'],1)==255


def test_countdown_expiry_clears_delta_flag_only_and_preexpiry_dma_has_two_gates(primary):
    cpu,memory,read,write,st,cfg,sm,g,names,metadata,prepare,call=primary
    for countdown in [0,1,2,3,65535]:
        prepare();write(CHANNEL+st['update_countdown'],countdown,2)
        write(CHANNEL+st['channel_flags'],255,1);write(CHANNEL+st['pitch_modulation_flags'],255,1)
        stop=0x4da1a if countdown==1 else 0x4daae if countdown==2 else 0x4dab6
        call(0x4d9ec,stop)
        assert read(CHANNEL+st['update_countdown'],2)==(countdown-1)&65535
        assert read(CHANNEL+st['channel_flags'],1)==(0 if countdown==1 else 255)
        assert read(CHANNEL+st['pitch_modulation_flags'],1)==255
    for pending,token in [(p,0) for p in range(256)]+[(0,t) for t in range(256)]:
        prepare();write(CHANNEL+st['update_countdown'],2,2);write(DMA+cfg['start_pending'],pending,1);write(PROGRAM,token,1)
        write(0xdff096,0xa55a,2);call(0x4d9ec,0x4daae)
        assert read(0xdff096,2)==(0xa55a if pending or token==0x83 else 4)
        assert read(CHANNEL+st['program_cursor'])==PROGRAM


def test_pitch_stream_terminal_byte_is_applied_before_cursor_loops(primary):
    cpu,memory,read,write,st,cfg,sm,g,names,metadata,prepare,call=primary
    for value in range(256):
        for pending in [0,1]:
            prepare();write(PITCH,value,1);write(CHANNEL+st['note_offset'],250,1);write(DMA+cfg['start_pending'],pending,1)
            expected=(read(SCALARS+2*((36+250+(value&127))&255),2)*400>>10)&65535
            call(0x4dab6,0x4db72)
            assert read(CHANNEL+st['pitch_sequence_cursor'])==(PITCH if value&128 else PITCH+1)
            assert read(DMA+cfg['sample_period'],2)==expected
            assert read(0xdff0c6,2)==(0 if pending else expected)


def test_pitch_delta_wait_suppresses_accumulator_application_then_runs_every_visit(primary):
    cpu,memory,read,write,st,cfg,sm,g,names,metadata,prepare,call=primary
    for step in range(256):
        for accumulator in [0,0x7fff,0x8000,0xffff]:
            for countdown in [0,1,255]:
                prepare();write(CHANNEL+st['channel_flags'],2,1);write(CHANNEL+st['pitch_delta_step'],step,1)
                write(CHANNEL+st['pitch_delta_accumulator'],accumulator,2);write(CHANNEL+st['pitch_delta_countdown'],countdown,1)
                call(0x4dab6,0x4db72)
                updated=accumulator if countdown else (accumulator+(step if step<128 else step-256))&65535
                assert read(CHANNEL+st['pitch_delta_accumulator'],2)==updated
                assert read(CHANNEL+st['pitch_delta_countdown'],1)==max(0,countdown-1)
                assert read(DMA+cfg['sample_period'],2)==(400 if countdown else (400-updated)&65535)
                if not countdown:
                    call(0x4dab6,0x4db72)
                    assert read(CHANNEL+st['pitch_delta_countdown'],1)==0
                    assert read(CHANNEL+st['pitch_delta_accumulator'],2)==(updated+(step if step<128 else step-256))&65535


def test_modulation_uses_byte_equality_turns_and_signed_value_with_word_period_wrap(primary):
    cpu,memory,read,write,st,cfg,sm,g,names,metadata,prepare,call=primary
    for flags in range(256):
        for step,old,limit in [(2,0,4),(2,2,4),(2,2,3),(2,0,0),(1,127,128),(255,1,0),(0,0,0),(0,5,5)]:
            for period in [0,65535]:
                prepare();write(CHANNEL+st['pitch_modulation_flags'],flags,1)
                for field,value in [('step',step),('value',old),('limit',limit)]:write(CHANNEL+st['pitch_modulation_'+field],value,1)
                cpu.d[0]=period;call(0x4db12,0x4db64)
                updated_flags=flags;value=old;expected=period
                if flags:
                    value=(old+step if flags&128 else old-step)&255
                    if (flags&128 and value==limit) or (not flags&128 and value==0):updated_flags^=128
                    if value==0:updated_flags^=1
                    signed=value if value<128 else value-256
                    expected=(period+signed if updated_flags&1 else period-signed)&65535
                assert read(CHANNEL+st['pitch_modulation_flags'],1)==updated_flags
                assert read(CHANNEL+st['pitch_modulation_value'],1)==value
                assert cpu.d[0]&65535==expected


def test_volume_header_counts_underflow_visits_and_terminal_marker_remains(primary):
    cpu,memory,read,write,st,cfg,sm,g,names,metadata,prepare,call=primary
    for interval in [0,1,2,127,255]:
        prepare();write(CHANNEL+st['volume_sequence_interval'],interval,1);write(CHANNEL+st['volume_sequence_countdown'],interval,1)
        for left in range(interval-1,-1,-1):
            call(0x4db72,0x4dba4)
            assert read(CHANNEL+st['volume_sequence_countdown'],1)==left
            assert read(CHANNEL+st['volume_sequence_cursor'])==VOLUME
        call(0x4db72,0x4dba4)
        assert read(CHANNEL+st['volume_sequence_cursor'])==VOLUME+1
        for _ in range(2*(interval+1)):call(0x4db72,0x4dba4)
        assert read(CHANNEL+st['volume_sequence_cursor'])==VOLUME+1
        assert read(DMA+cfg['sample_volume'],2)==64


def test_real_command_chain_keeps_modulation_across_note_and_zero_duration_wrap(primary):
    cpu,memory,read,write,st,cfg,sm,g,names,metadata,prepare,call=primary
    write(GLOBAL+g['samples_initialized'],0,1);cpu.a[3]=PLAYER
    assert sequencer(cpu,memory,write)(0x4e378,budget=1024).stop_reason==1
    prepare();program=bytes.fromhex('81ff008602048a00e0b0a0c024')
    memory[PROGRAM:PROGRAM+len(program)]=program
    call(0x4da16,0x4daae)
    sample=names['audio_sample_metadata'];scalar=read(SCALARS+72,2)
    period=(scalar*read(sample+sm['sample_period'],2)>>10)&65535
    assert read(CHANNEL+st['sample_metadata_ptr'])==sample
    assert read(CHANNEL+st['program_cursor'])==PROGRAM+13
    assert read(CHANNEL+st['channel_flags'],1)==2
    assert read(CHANNEL+st['pitch_modulation_flags'],1)==255
    assert read(CHANNEL+st['update_countdown'],2)==read(CHANNEL+st['update_reload_countdown'],2)==0
    assert read(DMA+cfg['sample_period'],2)==period
    call(0x4d9ec,0x4daae)
    assert read(CHANNEL+st['update_countdown'],2)==65535
    assert read(CHANNEL+st['pitch_delta_accumulator'],2)==65535
    assert read(CHANNEL+st['pitch_modulation_value'],1)==2
    assert read(DMA+cfg['sample_period'],2)==read(0xdff0c6,2)==(period+3)&65535
    assert read(CHANNEL+st['program_cursor'])==PROGRAM+13


def test_complete_four_channel_service_uses_distinct_typed_records_and_register_banks(primary):
    cpu,memory,read,write,st,cfg,sm,g,names,metadata,prepare,call=primary
    write(GLOBAL+g['samples_initialized'],0,1);cpu.a[3]=PLAYER
    assert sequencer(cpu,memory,write)(0x4e378,budget=1024).stop_reason==1
    assert sequencer(cpu,memory,write)(0x4d872,budget=1024).stop_reason==1
    prepare();template=bytes(memory[CHANNEL:CHANNEL+48]);samples=names['audio_sample_metadata']
    states=names['audio_channel_state_records'];configs=names['audio_channel_dma_configurations']
    for channel in range(4):
        state=states+48*channel;program=PROGRAM+32*channel
        memory[state:state+48]=template;memory[program:program+2]=bytes([36+channel,0x82])
        write(state+st['program_cursor'],program);write(state+st['sample_metadata_ptr'],samples)
        write(state+st['update_countdown'],1,2);write(state+st['pitch_modulation_flags'],255,1)
        write(state+st['pitch_modulation_step'],2,1);write(state+st['pitch_modulation_limit'],4,1)
    write(GLOBAL+g['primary_updates_enabled'],255,1);write(GLOBAL+g['update_phase_increment'],0,1);write(GLOBAL+g['skip_gate_enabled'],0,1)
    sample7=read(samples+7*12);write(PLAYER+0x532,0,2);write(PLAYER+0x534,32,2)
    assert sequencer(cpu,memory,write)(0x4d8fc,budget=2048).stop_reason==1
    for channel in range(4):
        state,config,audio=states+48*channel,configs+12*channel,0xdff0a0+16*channel
        period=(read(SCALARS+2*(36+channel),2)*read(samples+sm['sample_period'],2)>>10)&65535
        assert read(config+cfg['enabled'],1)==255
        assert read(config+cfg['sample_ptr'])==read(audio)==read(samples)
        assert read(config+cfg['sample_length'],2)==read(audio+4,2)==read(samples+sm['sample_length'],2)
        assert read(config+cfg['sample_period'],2)==read(audio+6,2)==period
        assert read(config+cfg['sample_volume'],2)==read(audio+8,2)==32
        assert read(state+st['program_cursor'])==PROGRAM+32*channel+1
        assert read(state+st['sample_start_pending'],1)==0
        assert read(state+st['update_countdown'],2)==5
        assert read(state+st['pitch_modulation_value'],1)==0
    assert read(0xdff096,2)==0x8201
    assert read(sample7+32,2)==0xc0c0 and read(PLAYER+0x534,2)==34
    assert sequencer(cpu,memory,write)(0x4d8fc,budget=2048).stop_reason==1
    for channel in range(4):
        state,config,audio=states+48*channel,configs+12*channel,0xdff0a0+16*channel
        period=(read(SCALARS+2*(36+channel),2)*read(samples+sm['sample_period'],2)>>10)&65535
        assert read(config+cfg['sample_period'],2)==read(audio+6,2)==(period+2)&65535
        assert read(state+st['sample_start_pending'],1)==255
        assert read(state+st['update_countdown'],2)==4
        assert read(state+st['pitch_modulation_value'],1)==2
        assert read(state+st['program_cursor'])==PROGRAM+32*channel+1
