"""Original track preparation up to the first hardware setup instruction.

RAM codecs and the RAM scanner execute unchanged. Supplied input/profile state
is not a disk-write, complete save/load, or normal-game reachability proof.
"""
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_mfm_codec import (
    original_image, codec_symbols, crc_image, memory, crc16, encoded, HEADER, ENCODED, SCRATCH,
    TRACK, TRACK_SCRATCH, FLAGS, ERRORS, FIRST, TRANSFER, POINTER, COUNT, INDEX,
)
from tests.test_starglider2_text_editor import state, run, put, STACK, RETURN

PREPARE, HARDWARE = 0x1080A, 0x108E0
TEMPLATE, BODY, GAP = 0x121D4, 0x1220E, 0x12410
ORDER, SECTOR_ID, CYLINDER, HEADER_CRC = 0x121C8, 0x12197, 0x1219A, 0x121B0
SOURCE, SCANNER = 0x7E000, 0x10A70


@pytest.fixture(scope='module', autouse=True)
def writer_symbols(tmp_path_factory, original_image):
    target = Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    bindings = {
        'encode_next_interleaved_mfm_sector': 0x10818,
        'calculate_mfm_id_header_crc': 0x10850,
        'emit_mfm_data_sync_and_select_payload': 0x10882,
        'copy_sector_payload_to_mfm_crc_scratch': 0x108AC,
        'calculate_mfm_data_marker_and_payload_crc': 0x108B2,
        'begin_prepared_mfm_track_dma_setup': HARDWARE,
        'return_master_media_signature_match': 0x10D82,
        'return_master_media_signature_mismatch': 0x10D86,
        'SG2_MFM_WRITE_SECTOR_COUNT': 10, 'SG2_MFM_SYNC_ZERO_BYTES': 12,
        'SG2_MFM_A1_SYNC_PAIR': 0x44894489, 'SG2_MFM_ID_CYLINDER_BYTE_OFFSET': 4,
        'SG2_MFM_HEADER_CRC_DBF_LAST': 7, 'SG2_MFM_SYNC_MARK_BYTES': 3,
        'SG2_MFM_HEADER_AFTER_SYNC_BYTES': 5, 'SG2_MFM_CRC_BYTES': 2,
        'SG2_MFM_POST_ID_GAP_AND_ZERO_BYTES': 34, 'SG2_MFM_PAYLOAD_LONGS_DBF_LAST': 127,
        'SG2_MFM_DATA_CRC_DBF_LAST': 515, 'SG2_MFM_DATA_CRC_HIGH_OFFSET': 516,
        'SG2_MFM_DATA_CRC_LOW_OFFSET': 517, 'SG2_MFM_DATA_AFTER_SYNC_BYTES': 515,
        'SG2_MFM_POST_DATA_GAP_BYTES': 22, 'SG2_MASTER_MEDIA_SIGNATURE_OFFSET': 30,
    }
    folder = tmp_path_factory.mktemp('track-writer-symbols')
    source, output = folder/'map.s', folder/'map.raw'
    source.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(bindings)+'\n')
    result = subprocess.run([str(target.parents[1]/'tools/vasmm68k_mot.exe'), '-quiet', '-Fbin', '-m68000',
        '-no-opt', '-I'+str(target/'includes'), '-o', str(output), str(source)], cwd=target, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout+result.stderr
    raw = output.read_bytes(); size = 4*len(bindings)
    assert raw[:-size] == original_image[0]
    assert struct.unpack('>'+'I'*len(bindings), raw[-size:]) == tuple(bindings.values())


def modeled_track(before, source, cylinder):
    """Independent byte/CRC oracle, retaining original encoder call boundaries."""
    model = bytearray(before)
    output, headers = [], []
    for selector in range(10, 0, -1):
        sector_id = before[ORDER+selector]
        header = bytearray(before[TEMPLATE+12:TEMPLATE+20])
        header[4], header[6] = cylinder & 255, sector_id
        check = crc16(header).to_bytes(2, 'big')
        block = source[512*(sector_id-1):512*sector_id]
        assert len(block) == 512
        body = before[BODY-4:BODY]+block
        body_check = crc16(body).to_bytes(2, 'big')
        output.extend((encoded(before[TEMPLATE:TEMPLATE+12]), b'\x44\x89'*3,
                       encoded(header[3:]), encoded(check),
                       encoded(before[TEMPLATE+20:TEMPLATE+54]), b'\x44\x89'*3,
                       encoded(body[3:]+body_check), encoded(before[GAP:GAP+22])))
        model[TEMPLATE+16], model[TEMPLATE+18] = cylinder & 255, sector_id
        model[HEADER_CRC:HEADER_CRC+2] = check
        model[BODY:BODY+514] = block+body_check
        headers.append(sector_id)
    model[SECTOR_ID] = headers[-1]
    model[INDEX:INDEX+2] = b'\0\0'
    track = b''.join(output)
    model[TRACK:TRACK+len(track)] = track
    return model, track, headers


@pytest.mark.parametrize('cylinder,pattern', [(0, 'zero'), (79, 'ramp'), (256, 'ones'), (65535, 'ramp')])
def test_original_track_preparation_and_independent_scanner_roundtrip(original_image, memory, cylinder, pattern):
    source = bytes(5120) if pattern == 'zero' else bytes([255])*5120 if pattern == 'ones' else bytes((i*31+i//512) & 255 for i in range(5120))
    memory[SOURCE:SOURCE+5120] = source
    memory[TRACK:TRACK+0x3000] = b'\xCC'*0x3000
    put(memory, CYLINDER, cylinder, 2)
    before = bytes(memory)
    expected, track, order = modeled_track(before, source, cylinder)
    assert order == [5, 9, 2, 6, 10, 3, 7, 1, 4, 8]
    assert len(track) == 11920
    cpu = state(memory, PREPARE)
    calls = []
    def observe(pc):
        if pc == 0x10D8A: calls.append(('encode', cpu.d[1] & 65535))
        if pc == 0x10DC6: calls.append(('crc', cpu.d[2] & 65535))
    run(original_image, memory, cpu, {HARDWARE}, observe, limit=250000)
    assert calls == [('encode', 12), ('crc', 7), ('encode', 5), ('encode', 2),
                     ('encode', 34), ('crc', 515), ('encode', 515), ('encode', 22)]*10
    # Codec calls leave saved return/temporary pointers in these stack slots.
    expected[STACK-8:STACK] = bytes(memory[STACK-8:STACK])
    assert bytes(memory) == expected
    assert cpu.a[0] == TRACK+11920 and cpu.a[7] == STACK
    assert bytes(memory[TRACK+11920:TRACK+0x3000]) == b'\xCC'*368
    assert cpu.a[1] == GAP+22

    # Actual generated stream is consumed by the original post-DMA scanner.
    # FIRST=1 is supplied explicitly; original static state contains zero.
    memory[TRACK_SCRATCH:TRACK_SCRATCH+128] = b'\xCC'*128
    memory[FLAGS:FLAGS+12] = bytes(12)
    memory[TRANSFER:TRANSFER+5120] = b'\xCC'*5120
    put(memory, POINTER, TRANSFER); put(memory, COUNT, 10, 2); put(memory, FIRST, 1, 2)
    put(memory, ERRORS, 9, 2)
    cpu = state(memory, SCANNER)
    run(original_image, memory, cpu, {RETURN}, limit=250000)
    assert cpu.d[0] == 0 and cpu.sr & 4 and cpu.a[7] == STACK+4
    assert bytes(memory[TRANSFER:TRANSFER+5120]) == source
    assert bytes(memory[FLAGS:FLAGS+12]) == b'\xFF'*10+b'\0\0'
    assert bytes(memory[ERRORS:ERRORS+2]) == b'\0\x09'
    assert cpu.a[4] == TRACK_SCRATCH+80


@pytest.mark.parametrize('difference', [None, *range(14)])
def test_master_media_signature_is_a_fourteen_byte_test_at_offset_thirty(original_image, memory, difference):
    signature = b'StarGlider II,'
    assert struct.pack('>IIIH', 1400136050, 1198287204, 1701978185, 18732) == signature
    memory[TRANSFER:TRANSFER+96] = b'\xCC'*96
    memory[TRANSFER+30:TRANSFER+44] = signature
    if difference is not None: memory[TRANSFER+30+difference] ^= 1
    put(memory, POINTER, TRANSFER)
    cpu = state(memory, 0x10D58); before = bytes(memory)
    run(original_image, memory, cpu, {RETURN})
    assert cpu.d[0] == (0xFFFFFFFF if difference is None else 0)
    assert bool(cpu.sr & 4) == (difference is not None)
    expected_advance = 14 if difference is None or difference >= 12 else 4*(difference//4+1)
    assert cpu.a[0] == TRANSFER+30+expected_advance
    assert bytes(memory) == before and cpu.a[7] == STACK+4


@pytest.mark.parametrize('part', ['header', 'data'])
def test_preparation_preserves_shared_template_mutations_without_reinitializing_marks(original_image, memory, part):
    from tests.test_starglider2_mfm_codec import SECTOR
    source = bytes((i*13) & 255 for i in range(5120))
    memory[SOURCE:SOURCE+5120] = source
    marks = TEMPLATE+12 if part == 'header' else BODY-4
    memory[marks:marks+3] = b'\xF5'*3
    before = bytes(memory)
    expected, track, _ = modeled_track(before, source, 0)
    cpu = state(memory, PREPARE)
    run(original_image, memory, cpu, {HARDWARE}, limit=250000)
    expected[STACK-8:STACK] = bytes(memory[STACK-8:STACK])
    assert bytes(memory) == expected
    assert bytes(memory[marks:marks+3]) == b'\xF5'*3
    # Encoder emits hard-coded A1 sync while CRC uses mutated template bytes.
    # Decode the first record to demonstrate the mismatch, without asserting
    # that a normal platform switch reaches this supplied mutation state.
    memory[ENCODED:ENCODED+len(track)] = track
    put(memory, POINTER, TRANSFER); put(memory, COUNT, 10, 2); put(memory, INDEX, 4, 2)
    cpu = state(memory, HEADER if part == 'header' else SECTOR)
    cpu.a[0] = ENCODED+(24 if part == 'header' else 112)
    cpu.a[4] = SCRATCH; cpu.d[1] = 9
    run(original_image, memory, cpu, {RETURN}, limit=50000)
    assert not cpu.sr & 4
    if part == 'header': assert bytes(memory[SCRATCH:SCRATCH+3]) == b'\xA1'*3
    else: assert bytes(memory[TRANSFER+4*512:TRANSFER+5*512]) == source[4*512:5*512]
