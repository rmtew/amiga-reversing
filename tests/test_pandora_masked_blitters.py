"""Original masked-blit CPU packets and address math; no DMA or admission proof."""
import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_render_order import sequencer

pytestmark = pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
APP, CUSTOM, PIXELS, MASK, DEST = 0x39FC, 0xDFF000, 0x82000, 0x83000, 0x70000
PACKETS = {
    0x691E: (0x698E, 0x69B8, 0x69E2, 0x6A0C),
    0x6A1E: (0x6A90, 0x6ABA, 0x6AE4, 0x6B0E),
    0x6B18: (0x6B94, 0x6BC0, 0x6BEC, 0x6C18),
    0x6C60: (0x6CDE, 0x6D0A, 0x6D36, 0x6D62),
}
WAITS = {
    0x691E: (0x6944, 0x6994, 0x69BE, 0x69E8),
    0x6A1E: (0x6A48, 0x6A96, 0x6AC0, 0x6AEA),
    0x6B18: (0x6B4C, 0x6B9C, 0x6BC8, 0x6BF4, 0x6C18),
    0x6C60: (0x6C96, 0x6CE6, 0x6D12, 0x6D3E, 0x6D62),
}
SCRATCH, FIRST_FINAL_END, SECOND_FINAL_END = BASE+0xB3A8, 0x6C56, 0x6DA4


def initialize(cpu_fixture, entry, height=3, stride=16, phase=5):
    cpu, memory, schemas, read, write, run = cpu_fixture
    cpu.a[0], cpu.a[1], cpu.a[2], cpu.a[3], cpu.a[5], cpu.a[6] = PIXELS, MASK, DEST, 0x84000, 0x87654321, APP
    cpu.d[4], cpu.d[5], cpu.d[6], cpu.d[7] = 0xABCD8001, 0xBEEF0000|stride, 0xCAFE0000|phase, 0xDCBA0000|height
    write(CUSTOM+0x1E, 0x40, 2)
    write(CUSTOM+0x44, 0xA55A, 2)  # inherited first-word mask
    write(CUSTOM+0x58, 0x1234, 2)
    return cpu, memory, read, write


def test_each_plane_launch_retains_mask_pixels_background_and_scratch_relationships(cpu_fixture):
    for entry, stops in PACKETS.items():
        for height in (1, 48, 49):
            for stride in (8, 16, 65535):
                for phase in range(16):
                    cpu, memory, read, write = initialize(cpu_fixture, entry, height, stride, phase)
                    before = bytes(memory[DEST:DEST+0x10000])
                    source = bytes(memory[PIXELS:MASK+0x100])
                    scratch_before = bytes(memory[SCRATCH:SCRATCH+0x310])
                    advance = sequencer(cpu, memory, write)
                    scratch = entry in (0x6B18, 0x6C60)
                    words = 1 if entry==0x691E else 2
                    for plane, stop in enumerate(stops):
                        assert advance(entry if plane==0 else None, stop=stop).stop_reason == 1
                        assert read(CUSTOM+0x50) == MASK
                        assert read(CUSTOM+0x4C) == PIXELS+2*plane
                        assert read(CUSTOM+0x48) == DEST+40*plane-(2 if entry==0x6C60 else 0)
                        assert read(CUSTOM+0x54) == (SCRATCH+4*plane if scratch else DEST+40*plane)
                        packed_phase = 0 if entry==0x691E else phase<<12
                        assert read(CUSTOM+0x42, 2) == packed_phase
                        assert read(CUSTOM+0x40, 2) == packed_phase|0xFCA
                        assert read(CUSTOM+0x44, 2) == 0xA55A
                        assert read(CUSTOM+0x46, 2) == (65535 if words==1 else 0)
                        assert read(CUSTOM+0x64, 2) == ((stride>>2)-2*words)&65535
                        assert read(CUSTOM+0x62, 2) == (stride-2*words)&65535
                        assert read(CUSTOM+0x60, 2) == 160-2*words
                        assert read(CUSTOM+0x66, 2) == (16-2*words if scratch else 160-2*words)
                        assert read(CUSTOM+0x58, 2) == (height<<6)|words
                        assert read(CUSTOM+0x9C, 2) == 0x40
                    if scratch:
                        end = FIRST_FINAL_END if entry==0x6B18 else SECOND_FINAL_END
                        assert advance(stop=end).stop_reason == 1
                        assert read(CUSTOM+0x50) == SCRATCH+(2 if entry==0x6C60 else 0)
                        assert read(CUSTOM+0x54) == DEST and read(CUSTOM+0x40, 2) == 0x9F0
                        assert read(CUSTOM+0x64, 2) == 2 and read(CUSTOM+0x66, 2) == 38
                        assert read(CUSTOM+0x58, 2) == (height*4<<6)|1
                    assert advance().stop_reason == 1
                    assert memory[DEST:DEST+0x10000] == before
                    assert memory[PIXELS:MASK+0x100] == source and memory[SCRATCH:SCRATCH+0x310] == scratch_before


def test_word_inputs_wrap_packet_height_and_modulos_but_movem_restores_sign_extended_words(cpu_fixture):
    heights = (0, 1, 48, 255, 256, 511, 512, 1023, 1024, 65535)
    for entry in PACKETS:
        for height in heights:
            for stride in (0, 1, 2, 3, 4, 7, 8, 16, 65535):
                for phase in (0, 1, 15, 16, 255, 0x8000, 65535):
                    cpu, memory, read, write = initialize(cpu_fixture, entry, height, stride, phase)
                    before_a = list(cpu.a[:7])
                    assert sequencer(cpu, memory, write)(entry, budget=512).stop_reason == 1
                    sign = lambda value: value if value<0x8000 else value|0xFFFF0000
                    assert list(cpu.d[4:]) == [0xFFFF8001, sign(stride), 0 if entry==0x691E else sign(phase), sign(height)]
                    assert list(cpu.a[:7]) == before_a and cpu.a[7] == 0x9004
                    assert read(CUSTOM+0x44, 2) == 0xA55A
                    if not height:
                        assert read(CUSTOM+0x58, 2) == 0x1234
                        continue
                    assert read(CUSTOM+0x42, 2) == (0 if entry==0x691E else (phase&15)<<12)
                    if entry in (0x691E, 0x6A1E):
                        words = 1 if entry==0x691E else 2
                        assert read(CUSTOM+0x58, 2) == ((height<<6)|words)&65535
                        assert read(CUSTOM+0x64, 2) == ((stride>>2)-2*words)&65535
                        assert read(CUSTOM+0x62, 2) == (stride-2*words)&65535
                    else:assert read(CUSTOM+0x58, 2) == ((height<<8)|1)&65535


@pytest.mark.parametrize('entry', list(PACKETS))
def test_every_plane_and_scratch_read_waits_before_launch_but_no_wait_follows_final_copy(cpu_fixture, entry):
    cpu, memory, read, write = initialize(cpu_fixture, entry)
    write(CUSTOM+0x1E, 0, 2)
    advance = sequencer(cpu, memory, write)
    stops = list(PACKETS[entry])
    if entry in (0x6B18, 0x6C60):stops.append(FIRST_FINAL_END if entry==0x6B18 else SECOND_FINAL_END)
    for i, (wait, stop) in enumerate(zip(WAITS[entry], stops)):
        assert advance(entry if i==0 else None, stop=wait).stop_reason == 1
        previous_size = read(CUSTOM+0x58, 2)
        assert advance(stop=stop, budget=9).stop_reason == 3
        assert cpu.pc == BASE+wait and read(CUSTOM+0x58, 2) == previous_size
        write(CUSTOM+0x1E, 0x40, 2)
        assert advance(stop=stop).stop_reason == 1
        write(CUSTOM+0x1E, 0, 2)
    assert advance().stop_reason == 1 and cpu.a[7] == 0x9004


def test_address_helpers_use_word_index_offset_and_signed_destination_without_clipping(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    # Remap the caller-supplied workspace so signed row indices on either side
    # remain backed RAM. This is an arithmetic witness, not a game workspace claim.
    workspace = 0x40000
    cpu.a[6] = workspace
    write(workspace+title_slots['app_back_bitplane_base'], 0x78000)
    for y in (0, 1, 199, 200, 248, 0x3FFF, 0x4000, 0x7FFF, 0x8000, 65535):
        row_index = (y*2)&65535
        if row_index&0x8000:row_index -= 65536
        for row in (0, 0x7FFF, 0x8000, 65535):
            write(workspace+row_index, row, 2)
            for x in (0, 15, 16, 319, 65535):
                cpu.d[0], cpu.d[1], cpu.d[2] = 0xABCD0000|x, 0xDCBA0000|y, 0xF00D1234
                saved = list(cpu.d[:3])
                run(0x6DAE)
                offset = (((x>>3)&~1)+row)&65535
                assert cpu.a[1] == 0x78000+offset-(65536 if offset&0x8000 else 0)
                assert list(cpu.d[:3]) == saved
                run(0x6DCA)
                assert list(cpu.d[:2]) == saved[:2] and cpu.d[2] == 0xF00D0000|offset
