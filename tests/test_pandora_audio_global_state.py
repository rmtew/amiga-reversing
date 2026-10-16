"""Original audio global-state transitions; CPU stores, not DMA bus timing."""
import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture

PLAYER = BASE+0x4D7DE


@pytest.mark.parametrize('increment', [0, 1, 15, 16, 127, 128, 255])
def test_phase_carry_precedes_six_visit_skip_gate(cpu_fixture, increment):
    cpu, memory, schemas, read, write, run = cpu_fixture
    for phase in range(256):
        for countdown in (0, 1, 2, 6):
            cpu.a[3] = PLAYER
            for off, value in ((0x529,255),(0x524,increment),(0x526,phase),(0x52C,1),(0x52B,countdown)):
                write(PLAYER+off,value,1)
            total = phase + ((increment*16)&255)
            carry = total > 255
            skip = not carry and countdown == 1
            stop = 0x4D8F6 if carry else 0x4D8FA if skip else 0x4D92A
            run(0x4D900,stop=stop,budget=32)
            assert read(PLAYER+0x526,1) == total&255
            assert read(PLAYER+0x52B,1) == (countdown if carry else 6 if skip else (countdown-1)&255)
            assert cpu.a[3] == PLAYER


@pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
def test_reset_clears_primary_gate_and_four_secondary_dma_pairs(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    locations=[(0x529,1)]+[(0xE30+38*i,1) for i in range(4)]+[(0xEBC+12*i,2) for i in range(4)]
    for off,size in locations:write(PLAYER+off,(1<<(8*size))-1,size)
    write(PLAYER+0x527,255,1);write(PLAYER+0x528,255,1)
    run(0x4D872)
    assert cpu.a[3] == PLAYER
    assert all(read(PLAYER+off,size)==0 for off,size in locations)
    assert read(PLAYER+0x527,1)==read(PLAYER+0x528,1)==255


def test_sample_initializer_sets_guard_and_both_sample_bases(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cursor=BASE+0x4EAD8;expected=[]
    for _ in range(11):
        length,divisor=read(cursor),read(cursor+4,2)
        expected.append((cursor+6,length//2,0x369E99//divisor))
        cursor+=6+length
    cpu.a[3]=PLAYER;write(PLAYER+0x528,0,1)
    run(0x4E378,budget=1024)
    assert cpu.a[3]==PLAYER and read(PLAYER+0x528,1)==255
    assert read(PLAYER+0x52E)==cursor and read(PLAYER+0x1160)==cursor+64
    for i,(ptr,length,period) in enumerate(expected):
        record=BASE+0x4DEB0+12*i
        assert read(record)==ptr and read(record+10,2)==period
        assert read(record+8,2)==(32 if i==7 else length)
    sample7=expected[7][0]
    assert memory[sample7:sample7+64]==bytes([0xC0])*32+bytes([0x3F])*32
    assert read(PLAYER+0x532,2)==0 and read(PLAYER+0x534,2)==32
    # Guarded reentry must retain later waveform and cursor changes.
    write(PLAYER+0x534,40,2);write(sample7,0x55,1)
    run(0x4E378)
    assert read(PLAYER+0x534,2)==40 and read(sample7,1)==0x55


def test_all_new_program_parameter_records_match_original_handlers(cpu_fixture):
    from amiga_reversing.disasm.effective_metadata import effective_target_metadata
    from amiga_reversing.disasm.project_paths import resolve_project_paths
    from tests.test_pandora_state_transitions import TARGET
    cpu,memory,schemas,read,write,run=cpu_fixture
    metadata=effective_target_metadata(resolve_project_paths(TARGET).target_dir)
    records=[]
    for layout in metadata.data_block_layouts:
        for element in layout.elements:
            typ=(element.type_binding or {}).get('bound_type_id')
            if typ in ('audio_pitch_modulation_command','audio_note_offset_operand'):
                records.append((BASE+layout.source_start+element.offset,element.width,typ))
    assert len(records)==25
    assert sum(typ=='audio_pitch_modulation_command' for _,_,typ in records)==16
    for address,width,typ in records:
        cpu.a[0],cpu.a[1],cpu.a[3]=0x81000,address+1,PLAYER
        opcode=read(address,1)
        assert opcode==(0x86 if typ=='audio_pitch_modulation_command' else 0x88)
        run(0x4DCA6 if opcode==0x86 else 0x4DCC2,stop=0x4DA1A,budget=16)
        assert cpu.a[1]==address+width
        if opcode==0x86:
            assert [read(0x81000+i,1) for i in (1,44,45,46)]==[255,read(address+1,1),0,read(address+2,1)]
        else:
            assert read(0x81003,1)==read(address+1,1)
