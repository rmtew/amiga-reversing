"""Isolated original colour kernels, not gameplay or caller/lifetime proof.

Build the committed export with vasm, then use the existing generated simulator.
All four interleaved WORD planes must receive the table-selected colour while
other pixel bits and every byte outside the requested cells are preserved.
"""
import ctypes
import hashlib
from pathlib import Path
import shutil
import struct
import subprocess

import pytest

from amiga_reversing.tools.direct_payload_adapter import VASM
from tests.test_memory_frame_arithmetic import ConcreteState, ConcreteResult
from src.tests.test_m68k_simulator_abstract import (
    M68kDiagList, _disasm_library, _diag_has_errors, _diag_message,
)

ROOT = Path(__file__).resolve().parents[1]
TABLES = {'regular': 0x3E112, 'single_cell': 0x3EF42}
ORIGINAL_SHA256 = '662976920689c38fd47271ed7e656a92caf20aa20ce0b8801db2bdc77ba864d9'


class DecodedText(ctypes.Structure):
    _fields_ = [('byte_count', ctypes.c_size_t), ('text', ctypes.c_char * 256),
                ('diagnostics', M68kDiagList)]


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    vasm = str(VASM) if VASM.exists() else shutil.which('vasmm68k_mot')
    if not vasm:
        pytest.skip('External vasm is required to build the committed original export')
    target = ROOT / 'targets/amiga_raw_starglider2_game'
    output = tmp_path_factory.mktemp('sg2-colour') / 'original.raw'
    result = subprocess.run([vasm, '-quiet', '-Fbin', '-m68000', '-no-opt',
        '-I' + str(target / 'includes'), '-o', str(output), str(target / 'starglider2_game.s')],
        cwd=target, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    raw = output.read_bytes()
    assert len(raw) == 412736 and hashlib.sha256(raw).hexdigest() == ORIGINAL_SHA256
    # These are original data values, not guessed pointer candidates.
    for i in range(16):
        assert struct.unpack_from('>I', raw, 0x3E172 + 4*i)[0] == (0xFFFF >> i) * 0x10001
        assert struct.unpack_from('>I', raw, 0x3E132 + 4*i)[0] == ((0xFFFF << (15-i)) & 0xFFFF) * 0x10001
    library = _disasm_library()
    step = library.m68k_simulate_one_concrete_for_cpu
    step.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.c_uint8,
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ConcreteState)]
    step.restype = ConcreteResult
    decode = library.m68k_disassemble_one_text_for_cpu
    decode.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.c_uint8]
    decode.restype = DecodedText
    return raw, (ctypes.c_uint8 * len(raw)).from_buffer_copy(raw), step, decode, {}


def run_kernel(kernels, family, colour, groups, left, right, pattern):
    raw, code, step, decode, cache = kernels
    table = TABLES[family]
    state = ConcreteState()
    state.pc = table + struct.unpack_from('>h', raw, table + 2*colour)[0]
    state.sr = 0x2700
    start = 64
    state.a[1], state.a[3], state.a[5] = start, 0xFFFF0000, 160
    state.d[0], state.d[1], state.d[7] = 15, 0xFFFF, 0xFFFFFFFF
    state.d[3] = 8*(groups-1) + right//2
    state.d[4] = (0xFFFF >> left) * 0x10001
    state.d[6] = ((0xFFFF << (15-right)) & 0xFFFF) * 0x10001
    if family == 'single_cell':
        state.d[4] &= state.d[6]
        state.d[6] = 152
    old = [pattern if pattern is not None else ((0x5137 + i*0x3179) ^ 0xA55A) & 0xFFFF
           for i in range(groups*4)]
    memory = (ctypes.c_uint8 * 512).from_buffer_copy(b'\xA5' * 512)
    memory[start:start + groups*8] = struct.pack('>' + 'H'*len(old), *old)
    expected = bytearray(memory)
    words = []
    for group in range(groups):
        mask = (0xFFFF >> left if group == 0 else 0xFFFF)
        mask &= ((0xFFFF << (15-right)) & 0xFFFF) if group == groups-1 else 0xFFFF
        words.extend((old[4*group+p] & (~mask & 0xFFFF)) |
                     (mask if colour >> p & 1 else 0) for p in range(4))
    expected[start:start + groups*8] = struct.pack('>' + 'H'*len(words), *words)
    for _ in range(300):
        pc = state.pc
        assert 0 <= pc < len(raw)
        pointer = ctypes.cast(ctypes.byref(code, pc), ctypes.POINTER(ctypes.c_uint8))
        if pc not in cache:
            decoded = decode(pointer, len(raw)-pc, 0)
            assert not _diag_has_errors(decoded.diagnostics), _diag_message(decoded.diagnostics)
            cache[pc] = b''.join(decoded.text.lower().split()).decode()
        text = cache[pc]
        # The remaining row/reference machinery is deliberately outside this test.
        if (family == 'regular' and text.endswith('usp,a1')) or (
                family == 'single_cell' and text == 'adda.wd6,a1'):
            break
        outcome = step(pointer, len(raw)-pc, 0, memory, len(memory), ctypes.byref(state))
        assert not _diag_has_errors(outcome.diagnostics), (hex(pc), _diag_message(outcome.diagnostics))
    else:
        pytest.fail('Kernel failed to reach its row handoff within 300 instructions')
    assert bytes(memory) == bytes(expected), (family, colour, groups, left, right, pattern)
    if family == 'single_cell':
        assert state.a[1] == start + 8  # The later +152 completes the 160-byte row stride.


@pytest.mark.parametrize('family', ['regular', 'single_cell'])
@pytest.mark.parametrize('colour', range(16))
def test_original_interleaved_colour_truth_and_pixel_boundaries(kernels, family, colour):
    for groups in ([1, 2, 3, 20] if family == 'regular' else [1]):
        for left, right in [(0, 15), (2, 13), (7, 8), (15, 15)]:
            for pattern in [0, 0xFFFF, None]:
                run_kernel(kernels, family, colour, groups, left, right, pattern)


def test_original_interleaved_mask_producer_normalizes_all_endpoint_pairs(kernels):
    # Enter the already selected interleaved initializer branch. This is an
    # instruction-semantic fixture, not evidence that a live game took it.
    raw, code, step, decode, _ = kernels
    base = 0x1000
    memory = (ctypes.c_uint8 * (base + len(raw) + 16))()
    memory[base:base + len(raw)] = raw
    expected = bytearray(memory)
    masks = []
    for left in range(16):
        for right in range(16):
            low, high = sorted((left, right))
            inside = (0xFFFF >> low) & ((0xFFFF << (15-high)) & 0xFFFF)
            masks.append(inside * 0x10001)
    start = base + 0x3EFBA  # Canonical generated_outside_span_masks32 owner.
    expected[start:start+1024] = struct.pack('>256I', *masks)
    state = ConcreteState()
    state.pc, state.sr = base + 0x3DA00, 0x2700
    for _ in range(6000):
        offset = state.pc - base
        assert 0 <= offset < len(raw)
        pointer = ctypes.cast(ctypes.byref(code, offset), ctypes.POINTER(ctypes.c_uint8))
        decoded = decode(pointer, len(raw)-offset, 0)
        assert not _diag_has_errors(decoded.diagnostics), _diag_message(decoded.diagnostics)
        if decoded.text.decode().strip().lower() == 'rts':
            break
        outcome = step(pointer, len(raw)-offset, 0, memory, len(memory), ctypes.byref(state))
        assert not _diag_has_errors(outcome.diagnostics), _diag_message(outcome.diagnostics)
    else:
        pytest.fail('Mask producer failed to reach its return within 6000 instructions')
    assert bytes(memory) == bytes(expected)  # Includes the untouched remainder of the shared 32x32 allocation.
