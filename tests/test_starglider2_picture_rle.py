"""Original picture-format instructions with explicit fixture inputs, not gameplay.

Check both shipped compressed streams and boundary-crossing synthetic runs.
Preserve original underfill; the fixture does not certify malformed run bounds
or execute the outer frame/palette/protection handshake. The paired-bit path
stops before its final hardware write at $FFFF8240; it is not skipped/emulated.
"""
import ctypes
from pathlib import Path
import struct

import pytest

from tests.test_memory_frame_arithmetic import ConcreteState
from tests.test_starglider2_interleaved_color_kernels import kernels as original_image
from src.tests.test_m68k_simulator_abstract import _diag_has_errors, _diag_message

ROOT = Path(__file__).resolve().parents[1]
BASE, DEST, TEMP, APP, STREAM, STACK = 0x1000, 0x70000, 0x78000, 0x85000, 0x90000, 0xB0000
RETURN, PICTURE = 0xFFFFFF00, 0x87654


def decode_runs(stream):
    """Independent byte grammar; preserve output count and original terminators."""
    cursor, planes = 0, []
    for _ in range(4):
        values = bytearray()
        while True:
            control = stream[cursor]
            cursor += 1
            if control == 0:
                break
            count = control if control < 128 else ((-control)&127) or 65536
            if control < 128:
                values.extend([stream[cursor]]*count)
                cursor += 1
            else:
                values.extend(stream[cursor:cursor+count])
                cursor += count
        planes.append(values)
    assert cursor == len(stream)
    assert all(len(p) <= 8000 for p in planes)  # Only these bounded supplied inputs.
    return planes


def encoded_stream(which):
    if which == 'boundaries':
        return bytes([3, 0xA5, 0xFD, 0x11, 0x22, 0x33, 0,
                      127, 0x55, 74, 0xAA, 0,
                      100, 0xCC, 0x81, *range(127), 0, 0])
    return (ROOT/'targets/amiga_raw_starglider2_game/assets'/f'{which}_picture_rle_data.bin').read_bytes()


def expected_storage(planes, layout):
    expected = bytearray(b'\xA5'*0x10000)
    planar = [bytearray(b'\xA5'*8192) for _ in range(4)]
    for p, values in enumerate(planes):
        for i, value in enumerate(values):
            row, column = i%200, i//200
            planar[p][row*40+column] = value
            if layout == 'interleaved':
                expected[row*160+(column//2)*8+column%2+2*p] = value
            else:
                offset = (TEMP-DEST if layout == 'paired_bits' else 0)+p*8192+row*40+column
                expected[offset] = value
    if layout == 'paired_bits':
        cursor = 0
        for row in range(200):
            for p in [0, 2]:
                for column in range(20):
                    left = struct.unpack_from('>H', planar[p], row*40+2*column)[0]
                    right = struct.unpack_from('>H', planar[p+1], row*40+2*column)[0]
                    packed = 0
                    for bit in range(15, -1, -1):
                        packed = (packed<<2) | (((left>>bit)&1)<<1) | ((right>>bit)&1)
                    struct.pack_into('>I', expected, cursor, packed)
                    cursor += 4
    return expected


@pytest.mark.parametrize('which', ['cockpit', 'argonaut_splash', 'boundaries'])
@pytest.mark.parametrize('layout', ['planar', 'interleaved', 'paired_bits'])
def test_original_picture_layout_and_underfill(original_image, which, layout):
    raw, code, step, decode, cache = original_image
    stream = encoded_stream(which)
    planes = decode_runs(stream)
    if which == 'cockpit':
        assert list(map(len, planes)) == [7999, 8000, 7999, 7999]
    elif which == 'argonaut_splash':
        assert list(map(len, planes)) == [7999]*4
    memory = (ctypes.c_uint8 * 0xB1000)()
    ctypes.memmove(ctypes.addressof(memory)+BASE, raw, len(raw))
    ctypes.memmove(ctypes.addressof(memory)+STREAM, stream, len(stream))
    memory[DEST:DEST+0x10000] = b'\xA5'*0x10000
    state = ConcreteState()
    state.pc = BASE + (0x2A7E if layout == 'planar' else 0x2B80 if layout == 'interleaved' else 0x2AFC)
    state.sr = 0x2700
    state.a[0], state.a[1], state.a[4], state.a[6], state.a[7] = STREAM, DEST, DEST, APP, STACK
    state.d[0] = PICTURE
    if layout == 'planar':
        memory[STACK:STACK+4] = struct.pack('>I', RETURN)
    else:
        memory[STACK:STACK+8] = struct.pack('>II', PICTURE, RETURN)
    memory[APP+0x1F2] = 2 if layout == 'paired_bits' else 0
    consumed = None
    for _ in range(2_000_000):
        if state.pc == RETURN or (layout == 'paired_bits' and state.pc == BASE+0x2B76):
            break
        offset = state.pc-BASE
        assert 0 <= offset < len(raw), hex(state.pc)
        ptr = ctypes.cast(ctypes.byref(code, offset), ctypes.POINTER(ctypes.c_uint8))
        if offset not in cache:
            instruction = decode(ptr, len(raw)-offset, 0)
            assert not _diag_has_errors(instruction.diagnostics), _diag_message(instruction.diagnostics)
            cache[offset] = b''.join(instruction.text.lower().split()).decode()
        if cache[offset] == 'movea.l(a7)+,a0' and consumed is None:
            consumed = state.a[0]
        outcome = step(ptr, len(raw)-offset, 0, memory, len(memory), ctypes.byref(state))
        assert not _diag_has_errors(outcome.diagnostics), (hex(state.pc), _diag_message(outcome.diagnostics))
    else:
        pytest.fail('Bounded supplied picture failed to reach its image handoff')
    assert consumed == STREAM+len(stream)
    if layout == 'paired_bits':
        assert raw[0x2B76:0x2B7C] == bytes.fromhex('31fc00008240')
        assert state.pc == BASE+0x2B76 and state.a[0] == DEST+32000
        assert state.a[7] == STACK  # Palette write/pop/RTS are outside the fixture.
        assert bytes(memory[STACK:STACK+8]) == struct.pack('>II', PICTURE, RETURN)
    else:
        assert state.pc == RETURN and state.a[0] == PICTURE
        assert state.a[7] == STACK+(4 if layout == 'planar' else 8)
    assert bytes(memory[DEST:DEST+0x10000]) == bytes(expected_storage(planes, layout))
    assert bytes(memory[STREAM:STREAM+len(stream)]) == stream


@pytest.mark.parametrize('start,copy_start', [(0x2AC6, 0x2ACE), (0x2BD0, 0x2BD8)])
def test_original_negative_controls_prepare_exact_word_counters(original_image, start, copy_start):
    # Scope ends before any literal read/write. In particular, $80's 65536
    # writes are not executed or certified as a valid bounded picture stream.
    raw, code, step, _, _ = original_image
    memory = (ctypes.c_uint8 * 16)()
    for control in range(0x80, 0x100):
        state = ConcreteState()
        state.pc, state.sr, state.d[1] = BASE+start, 0x2700, 0xACED0000|control
        for _ in range(3):
            offset = state.pc-BASE
            ptr = ctypes.cast(ctypes.byref(code, offset), ctypes.POINTER(ctypes.c_uint8))
            result = step(ptr, len(raw)-offset, 0, memory, len(memory), ctypes.byref(state))
            assert not _diag_has_errors(result.diagnostics), _diag_message(result.diagnostics)
        assert state.pc == BASE+copy_start
        assert state.d[1] == 0xACED0000|((((-control)&127)-1)&0xFFFF)
