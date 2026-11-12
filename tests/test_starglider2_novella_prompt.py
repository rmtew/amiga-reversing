"""Decoded local CPU windows, not protection startup or normal-media proof.

Use the reversible canonical analysis view with explicit RAM/caller state.
The unknown external selector and palette/text/input services are not executed.
The original parent decimal formatter is executed without a stub.
"""
import ctypes
import hashlib
from pathlib import Path

import pytest

from amiga_reversing.tools.starglider2_protection import START, extract_view
from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP
from src.tests.test_m68k_simulator_abstract import _diag_has_errors, _diag_message
from tests.test_starglider2_palette_priority import rng


@pytest.fixture(scope='module')
def decoded_image(original_image):
    raw, _, step, *rest = original_image
    view, receipt = extract_view(raw)
    assert receipt['inverse_exact']
    image = bytearray(raw)
    image[START-0x1000:START-0x1000+len(view)] = view
    code = (ctypes.c_uint8*len(image)).from_buffer_copy(image)
    return bytes(image), code, step, *rest


def install_view(memory, decoded_image):
    memory[0x1000:0x1000+len(decoded_image[0])] = decoded_image[0]


@pytest.fixture(scope='module')
def imported_bootblock():
    path = Path(__file__).resolve().parents[1]/'bin/Starglider 2 (1988)(Rainbird)[cr UA - WOW].adf'
    if not path.exists():
        pytest.skip('Imported original disk required')
    disk = path.read_bytes()
    assert len(disk) == 901120
    assert hashlib.sha256(disk).hexdigest() == '77c633a9270f85361a30ba19175f5940155631ceb6c84b47b1efbb0bf2150ee3'
    return disk[:1024]


def step_memory(image, memory, cpu, stops):
    for _ in range(100):
        if cpu.pc in stops:
            return
        assert 0 <= cpu.pc < len(memory)
        code = ctypes.cast(ctypes.byref(memory, cpu.pc), ctypes.POINTER(ctypes.c_uint8))
        result = image[2](code, len(memory)-cpu.pc, 0, memory, len(memory), ctypes.byref(cpu))
        assert not _diag_has_errors(result.diagnostics), _diag_message(result.diagnostics)
    pytest.fail('Imported shim did not reach bounded handoff')


def test_imported_loader_copies_twenty_byte_selector_shim(original_image, memory, imported_bootblock):
    memory[0x70000:0x70400] = imported_bootblock
    memory[0x380:0x398] = b'\xCC'*24
    cpu = state(memory, 0x70024)
    step_memory(original_image, memory, cpu, {0x200})
    assert bytes(memory[0x380:0x394]) == imported_bootblock[0x38:0x4C]
    assert bytes(memory[0x394:0x398]) == b'\xCC'*4
    assert cpu.a[0] == 0x7004C and cpu.a[2] == 0x394


@pytest.mark.parametrize('return_address', [0x13C06, 0x13C05, 0x13C07, 0x12345678])
@pytest.mark.parametrize('seed_a,seed_b', [(0,0), (0xFFFFFFFF,0x12345678), (0x95901143,0x28731549)])
def test_imported_selector_shim_is_return_address_gated(original_image, memory, imported_bootblock,
                                                       return_address, seed_a, seed_b):
    memory[0x380:0x394] = imported_bootblock[0x38:0x4C]
    put(memory, APP+0x60, seed_a); put(memory, APP+0x64, seed_b)
    cpu = state(memory, 0x380); put(memory, cpu.a[7], return_address)
    old_d1 = cpu.d[1]
    step_memory(original_image, memory, cpu, {return_address})
    if return_address == 0x13C06:
        assert cpu.d[0] == 145
        assert (get(memory, APP+0x60), get(memory, APP+0x64)) == (seed_a,seed_b)
    else:
        next_a,next_b = rng(seed_a,seed_b)
        assert cpu.d[0] == next_b
        assert (get(memory, APP+0x60), get(memory, APP+0x64)) == (next_a,next_b)
    assert cpu.d[1] == old_d1


@pytest.mark.parametrize('low', [0, 1, 146, 147, 255, 32768, 65535])
@pytest.mark.parametrize('high', [0, 1, 65535])
def test_selector_rejects_unsigned_word_then_clears_upper_bits(decoded_image, memory, low, high):
    install_view(memory, decoded_image)
    cpu = state(memory, 0x13C06); cpu.d[0] = high << 16 | low
    run(decoded_image, memory, cpu, {0x13C02, 0x13C1C})
    if low >= 147:
        assert cpu.pc == 0x13C02
    else:
        assert cpu.pc == 0x13C1C
        assert cpu.d[0] == low*16 and cpu.a[0] == START+low*16


@pytest.mark.parametrize('record', range(147))
def test_three_record_numbers_use_parent_formatter_and_replace_terminators(decoded_image, memory, record):
    install_view(memory, decoded_image)
    pointer = START+record*16
    values = bytes(memory[pointer:pointer+3])
    put(memory, APP+0x68, pointer)
    cpu = state(memory, 0x13C24)
    run(decoded_image, memory, cpu, {0x13D2C})
    for address, value in zip([0x13BD2, 0x13BE2, 0x13BED], values):
        text = str(value).encode()
        assert bytes(memory[address:address+len(text)+1]) == text+b' '
    assert cpu.a[0] == pointer+3
    assert get(memory, APP+0x58) == 0x13BED+len(str(values[2]))+1
