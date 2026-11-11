"""Original RAM codecs; supplied packets/counts are not physical-media proof.

Invalid indexes exercise isolated wrappers, not the scanner's reachable domain.
"""
import ctypes
import struct
import subprocess
from pathlib import Path
import pytest
from tests.test_starglider2_text_editor import original_image, state, run, put, BASE, STACK, RETURN
from amiga_reversing.tools.starglider2_disk_audio import mfm_word

ENCODE, CRC, INIT, HEADER, SECTOR, DECODE = 0x10D8A, 0x10DC6, 0x10DEC, 0x10E16, 0x10E2C, 0x10E90
HIGH, LOW, POINTER, INDEX, COUNT = 0x12428, 0x12528, 0x121C0, 0x1219E, 0x121A0
SRC, ENCODED, SCRATCH, TRANSFER = 0x100000, 0x120000, 0x140000, 0x150000


@pytest.fixture(scope='module')
def codec_symbols(tmp_path_factory, original_image):
    target = Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    names = ['encode_mfm_bytes', 'update_crc16_1021_bytes', 'initialize_crc16_1021_tables',
             'decode_and_check_mfm_header', 'decode_and_check_mfm_sector_data', 'decode_mfm_bytes_and_crc',
             'crc16_1021_high_table', 'crc16_1021_low_table', 'disk_service_state_transfer_buffer_pointer',
             'disk_service_state_sector_work_index', 'disk_service_state_expected_sector_count',
             'scan_dma_buffer_for_mfm_sectors', 'seek_next_mfm_id_sync_word', 'decode_next_mfm_byte_and_update_crc',
             'SG2_DISK_CRC16_POLYNOMIAL', 'SG2_CRC16_SPLIT_TABLE_STRIDE_BYTES', 'SG2_MFM_ID_SECTOR_BYTE_OFFSET',
             'SG2_MFM_A1_SYNC_WORD', 'SG2_MFM_ID_ADDRESS_MARK_WORD', 'SG2_MFM_DATA_ADDRESS_MARK_WORD']
    folder = tmp_path_factory.mktemp('codec-symbols'); source, output = folder/'map.s', folder/'map.raw'
    source.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(names)+'\n')
    r = subprocess.run([str(target.parents[1]/'tools/vasmm68k_mot.exe'), '-quiet', '-Fbin', '-m68000',
        '-no-opt', '-I'+str(target/'includes'), '-o', str(output), str(source)], cwd=target, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout+r.stderr
    raw = output.read_bytes(); assert raw[:-4*len(names)] == original_image[0]
    assert struct.unpack('>'+'I'*len(names), raw[-4*len(names):]) == (
        ENCODE, CRC, INIT, HEADER, SECTOR, DECODE, HIGH, LOW, POINTER, INDEX, COUNT,
        0x10A70, 0x10A7E, 0x10E9E, 0x1021, 256, 6, 0x4489, 0x5554, 0x5545)


def crc16(data, initial=65535):
    crc = initial
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ (0x1021 if crc & 32768 else 0)) & 65535
    return crc


def encoded(data, noise=0):
    previous = 1
    words = []
    for byte in data:
        words.append((mfm_word(byte, previous) ^ noise).to_bytes(2, 'big'))
        previous = byte & 1
    return b''.join(words)


def cold(original_image):
    m = (ctypes.c_uint8 * 0x180000)()
    ctypes.memmove(ctypes.addressof(m)+BASE, original_image[0], len(original_image[0]))
    return m


@pytest.fixture(scope='module')
def crc_image(original_image, codec_symbols):
    m = cold(original_image)
    cpu = state(m, INIT)
    expected = bytearray(m)
    values = [crc16(bytes([i]), 0) for i in range(256)]
    expected[HIGH:HIGH+256] = bytes(v >> 8 for v in values)
    expected[LOW:LOW+256] = bytes(v & 255 for v in values)
    run(original_image, m, cpu, {RETURN}, limit=30000)
    assert bytes(m) == expected
    assert cpu.a[5] == HIGH+256 and cpu.d[7] & 255 == 0 and cpu.a[7] == STACK+4
    return bytes(m)


@pytest.fixture
def memory(crc_image):
    return (ctypes.c_uint8 * len(crc_image)).from_buffer_copy(crc_image)


@pytest.mark.parametrize('size,pattern', [(size, pattern) for size in [1, 2, 3, 256, 513]
                                       for pattern in ['zero', 'ones', 'ramp']]+[(1024, 'pairs')])
def test_encoder_clock_carry_word_sum_and_preserved_registers(original_image, memory, size, pattern):
    data = bytes(size) if pattern == 'zero' else bytes([255])*size if pattern == 'ones' else bytes((71*i+i//16) & 255 for i in range(size))
    if pattern == 'pairs':
        data = b''.join(bytes([previous, value]) for previous in [0, 1] for value in range(256))
    memory[SRC:SRC+size] = data
    cpu = state(memory, ENCODE); cpu.a[0], cpu.a[1], cpu.d[1] = ENCODED, SRC, 0xBEEF0000+size
    saved_d, saved_a = list(cpu.d), list(cpu.a)
    expected = bytearray(memory); result = encoded(data)
    expected[ENCODED:ENCODED+2*size] = result
    run(original_image, memory, cpu, {RETURN})
    assert bytes(memory) == expected
    assert (cpu.a[0], cpu.a[1], cpu.a[7]) == (ENCODED+2*size, SRC+size, STACK+4)
    assert cpu.d[1] == 0xBEEFFFFF
    assert cpu.d[5] == 0xFFFF0000+((sum(data)-1) & 65535)
    assert cpu.d[2] == (0 if data[-1] & 1 else 32768)
    assert cpu.d[3] == (saved_d[3] & 0xFFFF0000) | 0x1021
    assert [cpu.d[i] for i in [4, 6, 7]] == [saved_d[i] for i in [4, 6, 7]]
    assert list(cpu.a[3:7]) == saved_a[3:7]


def test_zero_encoder_count_wraps_and_executes_65536_bytes(original_image, memory):
    data = bytes(range(256))*256
    memory[SRC:SRC+len(data)] = data
    cpu = state(memory, ENCODE); cpu.a[0], cpu.a[1], cpu.d[1] = ENCODED, SRC, 0xBEEF0000
    result = encoded(data)
    expected = bytearray(memory); expected[ENCODED:ENCODED+len(result)] = result
    run(original_image, memory, cpu, {RETURN}, limit=1500000)
    assert bytes(memory) == expected
    assert (cpu.a[0], cpu.a[1], cpu.d[1]) == (ENCODED+131072, SRC+65536, 0xBEEFFFFF)


@pytest.mark.parametrize('data', [b'\0', b'\xFF', b'123456789', bytes(range(256))])
def test_crc_helper_uses_dbf_last_and_does_not_write_ram(original_image, memory, data):
    memory[SRC:SRC+len(data)] = data
    cpu = state(memory, CRC); cpu.a[1], cpu.d[2] = SRC, 0xBEEF0000+len(data)-1
    before = bytes(memory); result = crc16(data)
    run(original_image, memory, cpu, {RETURN})
    assert bytes(memory) == before and cpu.a[1] == SRC+len(data)
    assert (cpu.d[6] & 255, cpu.d[7] & 255) == (result >> 8, result & 255)
    assert cpu.d[2] == 0xBEEFFFFF


@pytest.mark.parametrize('noise', [0, 0xAAAA, 0x8080])
@pytest.mark.parametrize('data', [b'\0', b'\xFF', b'123456789', bytes(range(256))])
def test_decoder_discards_clock_bits_and_keeps_crc_state_in_low_bytes(original_image, memory, data, noise):
    packet = encoded(data, noise); memory[ENCODED:ENCODED+len(packet)] = packet
    cpu = state(memory, DECODE)
    cpu.a[0], cpu.a[4], cpu.d[1], cpu.d[3] = ENCODED, SRC, 0xBEEF0000+len(data)-1, 127
    cpu.d[6], cpu.d[7] = 0x123400FF, 0xBEEF00FF
    expected = bytearray(memory); expected[SRC:SRC+len(data)] = data
    run(original_image, memory, cpu, {RETURN})
    crc = crc16(data)
    assert bytes(memory) == expected
    assert (cpu.a[0], cpu.a[4], cpu.d[1]) == (ENCODED+len(packet), SRC+len(data), 0xBEEFFFFF)
    assert cpu.d[6] == 0x12340000+(crc >> 8) and cpu.d[7] == 0xBEEF0000+(crc & 255)
    assert cpu.d[0] == packet[-1] & 127


def protected(data, corrupt):
    result = data+crc16(data).to_bytes(2, 'big')
    assert crc16(result) == 0
    if corrupt is True or corrupt == 'crc': result = result[:-1]+bytes([result[-1] ^ 1])
    elif corrupt == 'payload': result = result[:5]+bytes([result[5] ^ 1])+result[6:]
    return result


def wrapper(memory, entry, packet, count):
    memory[ENCODED:ENCODED+len(packet)] = packet
    memory[SCRATCH-8:SCRATCH+32] = b'\xCC'*40
    cpu = state(memory, entry)
    cpu.a[0], cpu.a[4], cpu.d[1] = ENCODED, SCRATCH, 0xBEEF0000+count
    return cpu


@pytest.mark.parametrize('noise', [0, 0xAAAA])
@pytest.mark.parametrize('corrupt', [False, True])
@pytest.mark.parametrize('size_code', [0, 2, 255])
def test_header_reports_crc_by_z_after_writing_ten_bytes(original_image, memory, noise, corrupt, size_code):
    data = protected(bytes([0xA1, 0xA1, 0xA1, 0xFE, 17, 1, 245, size_code]), corrupt)
    packet = encoded(data, noise); cpu = wrapper(memory, HEADER, packet, 9)
    saved = list(cpu.a); expected = bytearray(memory); expected[SCRATCH:SCRATCH+10] = data
    run(original_image, memory, cpu, {RETURN})
    expected[STACK-16:STACK] = bytes(memory[STACK-16:STACK])  # Local register-save/call frame only.
    assert bytes(memory) == expected
    crc = crc16(data)
    assert bool(cpu.sr & 4) == (crc == 0)
    assert cpu.d[7] & 255 == (crc >> 8) | (crc & 255)
    assert cpu.d[0] == packet[-1] & 127  # Not a success/error return value.
    assert list(cpu.a[2:5]) == saved[2:5] and cpu.a[0] == ENCODED+20 and cpu.a[7] == STACK+4


def test_cold_zero_crc_tables_do_not_establish_crc_validation(original_image):
    memory = cold(original_image)
    data = protected(bytes([0xA1, 0xA1, 0xA1, 0xFE, 0, 0, 1, 2]), True)
    assert crc16(data) != 0 and bytes(memory[HIGH:LOW+256]) == bytes(512)
    cpu = wrapper(memory, HEADER, encoded(data), 9)
    run(original_image, memory, cpu, {RETURN})
    assert cpu.sr & 4 and cpu.d[6] & 255 == 0 and cpu.d[7] & 255 == 0
    assert bytes(memory[SCRATCH:SCRATCH+10]) == data


@pytest.mark.parametrize('count,index', [(10, 0), (10, 9), (6, 0), (6, 4), (6, 5), (7, 2),
                                       (10, 64), (10, 65), (10, -1), (6, 32), (6, 6), (6, -1)])
@pytest.mark.parametrize('corrupt', ['none', 'crc', 'payload'])
def test_sector_uses_count_selected_size_signed_word_offset_and_keeps_failed_output(original_image, memory, count, index, corrupt):
    length = 1024 if count == 6 and index != 5 else 512
    payload = bytes((i*37+i//7) & 255 for i in range(length))
    data = protected(b'\xA1\xA1\xA1\xFB'+payload, corrupt)
    packet = encoded(data, 0xAAAA)
    put(memory, POINTER, TRANSFER); put(memory, COUNT, count, 2); put(memory, INDEX, index & 65535, 2)
    cpu = wrapper(memory, SECTOR, packet, 123)
    saved = list(cpu.a); expected = bytearray(memory)
    offset = (index*(1024 if count == 6 else 512)) & 65535
    if offset & 32768: offset -= 65536
    expected[TRANSFER+offset:TRANSFER+offset+length] = data[4:-2]
    expected[SCRATCH:SCRATCH+6] = data[:4]+data[-2:]
    run(original_image, memory, cpu, {RETURN}, limit=50000)
    expected[STACK-20:STACK] = bytes(memory[STACK-20:STACK])
    assert bytes(memory) == expected
    assert bool(cpu.sr & 4) == (corrupt == 'none')
    assert cpu.d[0] == packet[-1] & 127
    assert list(cpu.a[2:5]) == saved[2:5] and cpu.a[0] == ENCODED+len(packet) and cpu.a[7] == STACK+4


TRACK, TRACK_SCRATCH, FLAGS, ERRORS, FIRST = 0x78000, 0x7D000, 0x12630, 0x121A6, 0x121AC


def track_packet(index, count, first, *, alternate=False, bad_header=False, bad_payload=False):
    length = 1024 if count == 6 and index != 5 else 512
    # Avoid accidental FE data marks while testing rejected-header rescan paths.
    value = (index*9+17+(51 if alternate else 0)) & 127
    while True:
        payload = bytes([value])*length
        body = protected(b'\xA1\xA1\xA1\xFB'+payload, bad_payload)
        if 254 not in body[4:]: break
        value = (value+1) & 127
    header = protected(bytes([0xA1, 0xA1, 0xA1, 0xFE, 77, 1, (first+index) & 255, 7]), bad_header)
    def marks(data):
        result = bytearray(encoded(data)); result[:6] = b'\x44\x89'*3
        return bytes(result)
    return encoded(b'\x4E'*8)+marks(header)+encoded(b'\x4E'*12)+marks(body), body[4:-2]


@pytest.mark.parametrize('count,first', [(10, 1), (6, 245)])
@pytest.mark.parametrize('scenario', ['clean', 'duplicate', 'bad_header', 'bad_payload', 'below_first', 'after_last'])
def test_post_dma_scanner_filters_ids_and_duplicates_and_retries_crc_failures(original_image, memory, count, first, scenario):
    prefix, expected_blocks = [], {}
    if scenario == 'duplicate':
        p, data = track_packet(0, count, first); prefix.append(p); expected_blocks[0] = data
        prefix.append(track_packet(0, count, first, alternate=True)[0])
        order = list(range(count-1, 0, -1))
    else:
        order = list(range(count-1, -1, -1))
        if scenario == 'bad_header': prefix.append(track_packet(0, count, first, bad_header=True)[0])
        elif scenario == 'bad_payload': prefix.append(track_packet(0, count, first, alternate=True, bad_payload=True)[0])
        elif scenario == 'below_first': prefix.append(track_packet(-1, count, first)[0])
        elif scenario == 'after_last': prefix.append(track_packet(count, count, first)[0])
    for index in order:
        p, data = track_packet(index, count, first); prefix.append(p); expected_blocks[index] = data
    stream = b''.join(prefix)
    assert len(stream) < 0x3800
    memory[TRACK:TRACK+0x3802] = bytes(0x3802)
    memory[TRACK:TRACK+len(stream)] = stream
    memory[TRACK_SCRATCH:TRACK_SCRATCH+144] = b'\xCC'*144
    memory[FLAGS:FLAGS+20] = bytes(12)+b'\xCC'*8
    put(memory, POINTER, TRANSFER); put(memory, COUNT, count, 2); put(memory, FIRST, first, 2)
    put(memory, ERRORS, 9, 2)
    cpu = state(memory, 0x10A70)
    expected = bytearray(memory)
    stride = 1024 if count == 6 else 512
    for index, data in expected_blocks.items():
        expected[TRANSFER+stride*index:TRANSFER+stride*index+len(data)] = data
    expected[FLAGS:FLAGS+count] = b'\xFF'*count
    expected[INDEX:INDEX+2] = order[-1].to_bytes(2, 'big')
    crc_results = []
    def observe(pc):
        if pc == 0x10AD8:
            crc_results.append(bool(cpu.sr & 4))
            if not cpu.sr & 4:
                assert bytes(memory[TRANSFER:TRANSFER+16]) != expected_blocks[0][:16]
                assert memory[FLAGS] == 0
    run(original_image, memory, cpu, {RETURN}, observe, limit=250000)
    assert crc_results == ([False] if scenario == 'bad_payload' else [])+[True]*count
    # Header scratch is phase-reused; codec tests separately check each write.
    expected[TRACK_SCRATCH:TRACK_SCRATCH+128] = bytes(memory[TRACK_SCRATCH:TRACK_SCRATCH+128])
    expected[STACK-24:STACK] = bytes(memory[STACK-24:STACK])
    assert bytes(memory) == expected
    assert cpu.d[0] == 0 and cpu.sr & 4 and cpu.a[7] == STACK+4
    assert cpu.a[4] == TRACK_SCRATCH+8*(count+int(scenario == 'bad_payload'))


@pytest.mark.parametrize('beyond', [0, 2])
def test_outer_sync_scan_uses_strict_greater_bound_and_wrapping_error_word(original_image, memory, beyond):
    end = TRACK+0x100
    put(memory, end, 0, 2); put(memory, ERRORS, 65535, 2)
    cpu = state(memory, 0x10A7E); cpu.a[0], cpu.a[3] = end+beyond, end
    run(original_image, memory, cpu, {RETURN})
    assert cpu.d[0] == 0xFFFFFFFF and not cpu.sr & 4
    assert bytes(memory[ERRORS:ERRORS+2]) == b'\0\0'
    assert cpu.a[0] == end+2


@pytest.mark.parametrize('kind', ['id', 'data'])
def test_inner_marker_search_does_not_repeat_outer_bound_check(original_image, memory, kind):
    end = TRACK+0x100
    memory[end:end+10] = bytes.fromhex('4489000000000000')+(b'\x55\x54' if kind == 'id' else b'\x55\x45')
    put(memory, ERRORS, 9, 2)
    cpu = state(memory, 0x10A7E if kind == 'id' else 0x10AC6)
    cpu.a[0], cpu.a[3], cpu.a[4] = end, end, TRACK_SCRATCH
    run(original_image, memory, cpu, {HEADER if kind == 'id' else SECTOR})
    assert cpu.a[0] == end+2
    if kind == 'id': assert cpu.d[1] == 9
    else: assert cpu.a[4] == TRACK_SCRATCH+8
    assert bytes(memory[end+2:end+4]) == b'\x44\x89'
    assert bytes(memory[ERRORS:ERRORS+2]) == b'\0\x09'


@pytest.mark.parametrize('sector_id,first,count', [(0, 0, 10), (9, 0, 10), (10, 0, 10), (0, 1, 10),
                                                 (0, 65535, 10), (1, 65535, 2),
                                                 (0, 32768, 32767), (0, 32769, 32767)])
def test_id_filter_keeps_wrapped_word_delta_without_inventing_an_index_domain(original_image, memory, sector_id, first, count):
    memory[SCRATCH+6] = sector_id
    put(memory, FIRST, first, 2); put(memory, COUNT, count, 2)
    cpu = state(memory, 0x10A9E); cpu.a[4] = SCRATCH
    # Stop before the indexed flag access: passing these guards is not a proof
    # that an arbitrary expected-count field bounds the twelve-byte backing.
    run(original_image, memory, cpu, {0x10ABA, 0x10A7E})
    delta = (sector_id-first) & 65535
    signed_count = count-65536 if count & 32768 else count
    accepted = not delta & 32768 and delta < signed_count
    assert cpu.pc == (0x10ABA if accepted else 0x10A7E)
    assert cpu.d[0] == delta
