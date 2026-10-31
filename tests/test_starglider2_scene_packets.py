"""Original reference sorting, packet cycling and bounded caller preparation.

These are supplied-RAM CPU paths, not full rendering, queue capacity, lifetime,
arbitrary-coordinate validity or alternate-profile hardware certification.
"""
import itertools
import random
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, FB, INPUT, STACK, RETURN
from tests.test_starglider2_control_normalization import signed

SORT, CYCLE, HANDOFF, PREPARE = 0x41646, 0x3DAE2, 0x3DB28, 0x3D9DA
HEADERS, OUTPUT = INPUT + 0x1000, INPUT + 0x4000
GUARD = INPUT + 0xE00
FIELDS = ['draw_buffer_base', 'alternate_graphics_mode', 'player_rotation_2']


def word(m, p, value):
    put(m, p, value & 65535, 2)


@pytest.fixture(scope='module')
def fields(tmp_path_factory):
    root = Path(__file__).resolve().parents[1]
    target = root / 'targets/amiga_raw_starglider2_game'
    temp = tmp_path_factory.mktemp('scene-fields')
    asm, out = temp / 'fields.s', temp / 'fields.bin'
    asm.write_text((target / 'starglider2_game.s').read_text().split('    SECTION code,code', 1)[0]
                   + '\n SECTION constants,data\n dc.l ' + ','.join(FIELDS) + '\n')
    result = subprocess.run([str(root / 'tools/vasmm68k_mot.exe'), '-quiet', '-Fbin', '-no-opt',
                             '-I' + str(target / 'includes'), '-o', str(out), str(asm)],
                            cwd=target, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    return {name: APP + value for name, value in zip(FIELDS, struct.unpack('>3I', out.read_bytes()))}


RANDOM = random.Random(1988)
KEYS = (list(itertools.permutations([0, 1, 32768, 65535]))
        + [[0], [65535], [1, 1], [65535] * 7, [0] * 7,
           [3, 1, 3, 0, 65535, 1], [65535, 32768, 0, 1]]
        + [[RANDOM.randrange(65536) for _ in range(n)] for n in range(2, 18)])


def references(m, keys):
    word(m, GUARD, 65535)
    put(m, INPUT, GUARD)
    addresses = [HEADERS + 8 * i for i in range(len(keys))]
    for i, (address, key) in enumerate(zip(addresses, keys)):
        word(m, address, key)
        put(m, INPUT + 4 + 4 * i, address)
    return addresses


@pytest.mark.parametrize('keys', KEYS)
def test_descending_unsigned_sort_preserves_references_and_payloads(original_image, memory, keys):
    m = memory
    addresses = references(m, keys)
    payload = bytes(m[HEADERS:HEADERS + 8 * len(keys)])
    word(m, INPUT + 4 + 4 * len(keys), 0xA5A5)
    cpu = state(m, SORT)
    cpu.a[0], cpu.a[1] = INPUT + 4, INPUT + 4 * len(keys)
    preserved = cpu.a[4]
    run(original_image, m, cpu, {RETURN})
    actual = [get(m, INPUT + 4 + 4 * i) for i in range(len(keys))]
    assert sorted(actual) == sorted(addresses)
    assert [get(m, address, 2) for address in actual] == sorted(keys, reverse=True)
    assert get(m, INPUT) == GUARD and get(m, GUARD, 2) == 65535
    assert bytes(m[HEADERS:HEADERS + 8 * len(keys)]) == payload
    assert get(m, INPUT + 4 + 4 * len(keys), 2) == 0xA5A5
    assert cpu.a[4] == preserved and cpu.a[7] == STACK + 4


def test_empty_signed_address_range_returns_before_dereferencing(original_image, memory):
    cpu = state(memory, SORT)
    cpu.a[0], cpu.a[1] = INPUT + 4, INPUT
    before = bytes(memory[INPUT:INPUT + 8])
    run(original_image, memory, cpu, {RETURN})
    assert bytes(memory[INPUT:INPUT + 8]) == before and cpu.a[7] == STACK + 4


def test_missing_high_guard_allows_backward_scan_beyond_first_cell(original_image, memory):
    references(memory, [42])
    word(memory, GUARD, 0)
    cpu = state(memory, SORT)
    cpu.a[0] = cpu.a[1] = INPUT + 4
    run(original_image, memory, cpu, {0x41662})
    assert cpu.a[3] == INPUT
    run(original_image, memory, cpu, {0x4165E})
    assert cpu.a[3] == INPUT  # The next instruction predecrements past the guard.


POLYGONS = [
    [(10, 5)], [(10, 5), (20, 8)], [(10, 8), (20, 5)],
    [(10, 5), (20, 5)], [(10, 5), (20, 8), (30, 5)],
    [(10, 8), (20, 5), (30, 7), (40, 9)],
    [(10, 4095), (20, 4095)], [(10, 0), (20, 4095), (30, 0)],
]


def polygon(m, address, points, depth=123, style=7, sentinel=65535, following=0xA5A5):
    values = [depth, style, *[v for xy in points for v in xy], sentinel, following]
    for i, value in enumerate(values):
        word(m, address + 2 * i, value)
    return 2 * len(values)


@pytest.mark.parametrize('points', POLYGONS)
@pytest.mark.parametrize('sentinel', [0x8000, 0xA5A5, 0xFFFF])
@pytest.mark.parametrize('following', [0, 1234, 65535])
def test_cycle_uses_last_equal_unsigned_minimum_and_end_pointer_format(original_image, memory, points, sentinel, following):
    m = memory
    size = polygon(m, HEADERS, points, sentinel=sentinel, following=following)
    source = bytes(m[HEADERS:HEADERS + size])
    put(m, INPUT, HEADERS)
    put(m, INPUT + 4, 0xFFFFFFFF)
    m[OUTPUT - 4:OUTPUT + 128] = b'\xA5' * 132
    cpu = state(m, CYCLE)
    cpu.a[1], cpu.a[2], cpu.a[6] = OUTPUT, INPUT, INPUT
    run(original_image, m, cpu, {HANDOFF})
    index = max(i for i, xy in enumerate(points) if xy[1] == min(y for x, y in points))
    expected = points[index:] + points[:index]
    end = OUTPUT + 6 + 4 * len(points)
    assert get(m, OUTPUT) == end and get(m, OUTPUT + 4, 2) == 7
    assert [(get(m, OUTPUT + 6 + 4 * i, 2), get(m, OUTPUT + 8 + 4 * i, 2))
            for i in range(len(points))] == expected
    assert get(m, end) == 0 and get(m, end + 4) == 0xA5A5A5A5
    assert get(m, OUTPUT - 4) == 0xA5A5A5A5
    assert bytes(m[HEADERS:HEADERS + size]) == source
    assert get(m, INPUT) == OUTPUT and get(m, INPUT + 4) == 0xFFFFFFFF
    assert cpu.a[1] == end + 4 and cpu.a[2] == INPUT + 4 and cpu.a[6] == INPUT


def test_multiple_packets_replace_shared_reference_cells_without_merging_layouts(original_image, memory):
    packets = [[(10, 4), (20, 2), (30, 3)], [(11, 1), (22, 1)]]
    addresses = [HEADERS, HEADERS + 64]
    for i, (p, points) in enumerate(zip(addresses, packets)):
        polygon(memory, p, points, style=i + 5)
        put(memory, INPUT + 4 * i, p)
    put(memory, INPUT + 8, 0xFFFFFFFF)
    cpu = state(memory, CYCLE)
    cpu.a[1], cpu.a[2], cpu.a[6] = OUTPUT, INPUT, INPUT
    run(original_image, memory, cpu, {HANDOFF})
    p = OUTPUT
    for i, points in enumerate(packets):
        assert get(memory, INPUT + 4 * i) == p
        assert get(memory, p + 4, 2) == i + 5
        p = get(memory, p) + 4
    assert cpu.a[1] == p and get(memory, INPUT + 8) == 0xFFFFFFFF


@pytest.mark.parametrize('points', [
    [(7, 4), (40, 4)], [(40, 4), (7, 4)],
    [(10, 2), (10, 8)], [(10, 8), (10, 2)],
])
def test_actual_cycle_to_horizontal_or_vertical_span_consumer(original_image, memory, points):
    polygon(memory, HEADERS, points, style=7)
    put(memory, INPUT, HEADERS)
    put(memory, INPUT + 4, 0xFFFFFFFF)
    cpu = state(memory, CYCLE)
    cpu.a[1], cpu.a[2], cpu.a[6] = OUTPUT, INPUT, INPUT
    run(original_image, memory, cpu, {0x3DB30})
    span = 0x41848
    first_y, last_y = min(y for x, y in points), max(y for x, y in points)
    left, right = min(x for x, y in points), max(x for x, y in points)
    expected = [7, first_y, *[v for row in range(first_y, last_y + 1)
                              for v in (left, right)], 65535]
    assert get(memory, INPUT) == span and get(memory, INPUT + 4) == 0xFFFFFFFF
    assert [get(memory, span + 2 * i, 2) for i in range(len(expected))] == expected
    assert cpu.a[3] == span + 2 * len(expected)
    assert cpu.a[2] == INPUT and cpu.a[7] == STACK


@pytest.mark.parametrize('points', [[], [(10, 4096), (20, 65535)]])
def test_no_selected_y_retains_unestablished_start_cursor(original_image, memory, points):
    polygon(memory, HEADERS, points)
    put(memory, INPUT, HEADERS)
    cpu = state(memory, CYCLE)
    cpu.a[1], cpu.a[2] = OUTPUT, INPUT
    original_a3 = cpu.a[3]
    run(original_image, memory, cpu, {0x3DB0E})
    assert cpu.a[3] == original_a3 and cpu.d[0] & 65535 == 4095


def test_vertex_counter_is_a_byte_even_though_selected_count_is_copied_as_word(original_image, memory):
    points = [(i, 100 if i != 255 else 0) for i in range(256)]
    polygon(memory, HEADERS, points)
    put(memory, INPUT, HEADERS)
    cpu = state(memory, CYCLE)
    cpu.a[1], cpu.a[2] = OUTPUT, INPUT
    run(original_image, memory, cpu, {0x3DB0E})
    assert cpu.d[4] == 0 and cpu.d[5] & 65535 == 0
    assert cpu.a[3] == HEADERS + 4 + 4 * 256


@pytest.mark.parametrize('count', [1, 2, 8192, 8193, 16384, 16385, 65535])
def test_preparation_uses_wrapped_word_offset_not_unbounded_count_multiplication(original_image, memory, count):
    cpu = state(memory, 0x3DA10)
    cpu.a[2], cpu.d[0] = INPUT, count
    run(original_image, memory, cpu, {0x3DA2E, 0x3DA32})
    last = INPUT + 4 + signed(4 * (count - 1))
    assert cpu.a[0] == INPUT + 4 and cpu.a[1] == last and cpu.a[4] == last + 4


@pytest.mark.parametrize('profile', ['amiga', 'mode0', 'mode1'])
@pytest.mark.parametrize('count', [0, 1, 3])
@pytest.mark.parametrize('heading', [0x340, 0x341, 0xB40, 0xB41])
def test_real_preparation_sorts_then_appends_profile_hud_without_drawing(original_image, memory, fields, profile, count, heading):
    m = memory
    keys = [123, 65535, 0][:count]
    references(m, keys)
    put(m, INPUT + 4 + 4 * count, 0x3C36)
    put(m, fields['draw_buffer_base'], FB)
    m[fields['alternate_graphics_mode']] = 2 if profile == 'mode1' else 0
    word(m, fields['player_rotation_2'], heading | 0xF000)
    word(m, 0x1002, 0x8000 if profile == 'amiga' else 0)
    cpu = state(m, PREPARE)
    cpu.a[2], cpu.d[0] = INPUT, count
    run(original_image, m, cpu, {0x3DAD4, RETURN})
    expected_fb = bytearray(b'\xA5' * 0x8000)
    if profile == 'mode0':
        for row in range(34):
            start = 0x5B98 + 160 * row
            expected_fb[start:start + 16] = bytes(16)
    elif profile == 'mode1':
        for row in range(33):
            for column in [0, 80]:
                start = 0x5B6C + 160 * row + column
                expected_fb[start:start + 8] = bytes(8)
    assert bytes(m[FB:FB + 0x8000]) == expected_fb
    assert get(m, 0x416A8) == FB and get(m, 0x416A6, 2) == heading
    assert m[0x416A5] == (2 if profile == 'mode1' else 0)
    if count == 0 and profile == 'amiga':
        assert cpu.pc == RETURN and cpu.a[7] == STACK + 4
        assert get(m, INPUT + 4) == 0x3C36
        return
    assert cpu.pc == 0x3DAD4 and get(m, cpu.a[4]) == 0xFFFFFFFF
    first = INPUT + (4 if count else 0)
    assert [get(m, get(m, first + 4 * i), 2) for i in range(count)] == sorted(keys, reverse=True)
    tail = first + 4 * count
    if profile == 'amiga':
        assert cpu.a[4] == tail
    else:
        assert get(m, tail) == 0x3A0D2 and cpu.a[4] == tail + 4
        inside = 0x340 < heading <= 0xB40
        assert get(m, 0x3A0D4, 2) == ((7 if inside else 3) if profile == 'mode1' else (2 if inside else 1))
