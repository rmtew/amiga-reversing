"""Original face admission, backface refresh and cached-vertex producers.

Finite supplied faces and frames are not universal model/index domains,
workspace capacity, lifetime, final visibility or normal-game reachability.
"""
import random
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, INPUT, STACK, RETURN
from tests.test_starglider2_control_normalization import signed
from tests.test_starglider2_palette_priority import rng

COMMANDS, SOURCE, POOL, OBJECT_CACHE, OUTPUT, REFS = [INPUT + n for n in [0, 0x1000, 0x2000, 0x3000, 0x5000, 0x6000]]
ADMITTED, FORCE, STYLES = 0x4B0A2, 0x58A4, 0x5894
FIELDS = ['active_model_type_index', 'active_model_face_commands', 'active_model_vertex_reference_records',
          'active_model_coordinate_pool', 'model_view_vertex_scratch_prefix', 'model_face_admission_bits_scratch',
          'model_face_vertex_count_scratch', 'drawing_fill_style_word', 'model_face_culling_disabled_flag',
          'frame_handoff_counter', 'model_view_matrix', 'active_model_scale_shift', 'model_last_vertex_index']


@pytest.fixture(scope='module')
def slots(tmp_path_factory):
    target = Path(__file__).resolve().parents[1] / 'targets/amiga_raw_starglider2_game'
    temp = tmp_path_factory.mktemp('face-admission-fields')
    asm, out = temp / 'fields.s', temp / 'fields.bin'
    asm.write_text((target / 'starglider2_game.s').read_text().split('    SECTION code,code', 1)[0]
                   + '\n SECTION constants,data\n dc.l ' + ','.join(FIELDS) + '\n')
    result = subprocess.run([str(target.parents[1] / 'tools/vasmm68k_mot.exe'), '-quiet', '-Fbin', '-no-opt',
                             '-I' + str(target / 'includes'), '-o', str(out), str(asm)],
                            cwd=target, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    return dict(zip(FIELDS, struct.unpack('>' + str(len(FIELDS)) + 'I', out.read_bytes())))


def word(m, p, v): put(m, p, v & 65535, 2)
def slot(m, slots, name): return APP + slots[name]
def long_signed(v): return (v + 0x80000000) % 0x100000000 - 0x80000000


def backface_value(points):
    p, q, r = points[:3]
    edge = [signed(b - a) for a, b in zip(p, q)]
    other = [signed(b - a) for a, b in zip(p, r)]
    a = long_signed(other[2] * edge[1] - other[1] * edge[2]) >> 6
    b = long_signed(other[0] * edge[2] - other[2] * edge[0]) >> 6
    c = long_signed(other[1] * edge[0] - other[0] * edge[1]) >> 6
    return long_signed(sum(signed(v) * (signed(coordinate) >> 5) for v, coordinate in zip([a, b, c], r)))


TRIANGLE = [(0, 0, 1000), (100, 0, 1000), (0, 100, 1000)]
ACCEPT = [TRIANGLE[0], TRIANGLE[2], TRIANGLE[1]]


def prepare(m, slots, points=TRIANGLE, header=0x0303, phase=0, cached=0, force=0, disabled=0, flag=1, index=0, kind=0):
    cache = slot(m, slots, 'model_view_vertex_scratch_prefix')
    for i, point in enumerate(points):
        for j, value in enumerate(point): word(m, cache + 8 * i + 2 * j, value)
        m[cache + 8 * i + 6] = flag
        m[cache + 8 * i + 7] = 0xA5
    for name, value, width in [('active_model_type_index', kind, 2), ('frame_handoff_counter', phase, 2),
                              ('model_face_culling_disabled_flag', disabled, 1),
                              ('model_face_admission_bits_scratch', cached, 4),
                              ('active_model_vertex_reference_records', SOURCE, 4),
                              ('active_model_coordinate_pool', POOL, 4)]:
        put(m, slot(m, slots, name), value, width)
    word(m, FORCE, force)
    word(m, 0x52BE, 0)
    m[ADMITTED - 4:ADMITTED + 512] = b'\xCC' * 516
    word(m, COMMANDS, header)
    count = (header >> 8) & 7
    for i in range(max(3, count)): word(m, COMMANDS + 2 + 2 * i, 8 * (i % len(points)))
    cpu = state(m, 0x4B54)
    cpu.d[0] = index
    cpu.a[0], cpu.a[1], cpu.a[4], cpu.a[5] = cache, SOURCE, COMMANDS, ADMITTED
    put(m, STACK, OBJECT_CACHE)
    put(m, STACK + 4, RETURN)
    put(m, OBJECT_CACHE, 0xDEADBEEF)
    return cpu, cache, count


def admitted(m): return get(m, 0x52BE, 2) == 1


@pytest.mark.parametrize('kind', list(range(104)) + [104, 32768, 65535])
def test_model_whitelist_sets_refresh_word_only(original_image, memory, slots, kind):
    word(memory, slot(memory, slots, 'active_model_type_index'), kind)
    word(memory, FORCE, 0x1234)
    cpu = state(memory, 0x4ADA)
    run(original_image, memory, cpu, {0x4B38})
    assert get(memory, FORCE, 2) == (65535 if kind in [49, 84, 30, 47, 91, 3] else 0)


@pytest.mark.parametrize('phase', [0, 1, 2, 3, 4, 65535])
@pytest.mark.parametrize('force', [0, 1, 32767, 32768, 65535])
@pytest.mark.parametrize('cached', [0, 1])
@pytest.mark.parametrize('points', [TRIANGLE, ACCEPT])
def test_forced_word_recomputes_backface_instead_of_admitting(original_image, memory, slots, phase, force, cached, points):
    cpu, cache, count = prepare(memory, slots, points, phase=phase, cached=cached, force=force)
    run(original_image, memory, cpu, {0x4C8A})
    expected = backface_value(points) < 0 if (phase & 3) == 0 or force & 32768 else bool(cached)
    assert admitted(memory) == expected
    assert get(memory, slot(memory, slots, 'model_face_admission_bits_scratch')) == int(expected)
    assert cpu.a[4] == COMMANDS + 2 + 2 * count and cpu.a[7] == STACK
    assert get(memory, STACK) == OBJECT_CACHE and get(memory, OBJECT_CACHE) == 0xDEADBEEF


RANDOM = random.Random(68000)
GEOMETRY = [TRIANGLE, ACCEPT, [(0, 0, 0)] * 3,
            [(0, 0, 1000), (1, 0, 1000), (0, 1, 1000)],
            [(-32768, 32767, 0), (32767, -32768, 1000), (0, 0, -32768)]]
GEOMETRY += [[tuple(RANDOM.randrange(-32768, 32768) for _ in range(3)) for _ in range(3)] for _ in range(40)]


@pytest.mark.parametrize('points', GEOMETRY)
@pytest.mark.parametrize('flag', [1, 2, 127])
def test_original_word_edges_cross_products_and_scaled_dot_match_integer_reference(original_image, memory, slots, points, flag):
    cpu, cache, _ = prepare(memory, slots, points, flag=flag)
    run(original_image, memory, cpu, {0x4C8A})
    assert admitted(memory) == (backface_value(points) < 0)
    assert [memory[cache + 8 * i + 6] for i in range(3)] == [flag] * 3


@pytest.mark.parametrize('disabled', [0, 1, 128, 255])
@pytest.mark.parametrize('negative_header', [False, True])
@pytest.mark.parametrize('style', [0, 127, 128, 255])
def test_explicit_bypasses_copy_signed_style_and_mark_only_zero_used_bytes(original_image, memory, slots, disabled, negative_header, style):
    header = (0x8300 if negative_header else 0x0300) | style
    cpu, cache, _ = prepare(memory, slots, header=header, phase=1, disabled=disabled, flag=0)
    for i, flag in enumerate([0, 1, 128]): memory[cache + 8 * i + 6] = flag
    run(original_image, memory, cpu, {0x4C8A})
    expected = bool(disabled or negative_header)
    assert admitted(memory) == expected
    assert [memory[cache + 8 * i + 6] for i in range(3)] == ([255, 1, 128] if expected else [0, 1, 128])
    if expected:
        assert [get(memory, ADMITTED + 2 * i, 2) for i in range(5)] == [style if style < 128 else style + 65280, 0, 8, 16, 65535]


@pytest.mark.parametrize('faces', [1, 31, 32, 33, 65])
def test_full_descending_face_loop_aliases_cache_bits_modulo32(original_image, memory, slots, faces):
    cpu, cache, _ = prepare(memory, slots)
    mask, output, accepted = 0xA5A55A5A, [], 0
    put(memory, slot(memory, slots, 'model_face_admission_bits_scratch'), mask)
    for i in range(faces):
        offsets = [0, 16, 8] if i % 3 == 0 else [0, 8, 16]
        for j, value in enumerate([0x0303, *offsets]): word(memory, COMMANDS + 8 * i + 2 * j, value)
        bit = 1 << ((faces - i - 1) % 32)
        if i % 3 == 0:
            mask |= bit
            output += [3, *offsets, 65535]
            accepted += 1
        else: mask &= ~bit
    cpu.d[0] = faces - 1
    run(original_image, memory, cpu, {0x4C8A})
    assert get(memory, slot(memory, slots, 'model_face_admission_bits_scratch')) == mask
    assert get(memory, 0x52BE, 2) == accepted and cpu.a[4] == COMMANDS + 8 * faces
    assert [get(memory, ADMITTED + 2 * i, 2) for i in range(len(output))] == output
    assert cpu.a[5] == ADMITTED + 2 * len(output) and cpu.a[7] == STACK


@pytest.mark.parametrize('seed', [(0, 0), (0x12345678, 0xABCDEF01), (0xFFFFFFFF, 1), (0x80000000, 0x12345678)])
def test_model47_uses_actual_rng_style_but_restores_face_index_for_cache_update(original_image, memory, slots, seed):
    cpu, cache, _ = prepare(memory, slots, ACCEPT, force=65535, phase=3, kind=47, index=32)
    put(memory, APP + 0x60, seed[0]); put(memory, APP + 0x64, seed[1])
    # Isolate one original iteration while retaining saved index32.
    run(original_image, memory, cpu, {0x4C7E})
    expected = rng(*seed)
    assert [get(memory, APP + off) for off in [0x60, 0x64]] == list(expected)
    assert get(memory, ADMITTED, 2) == get(memory, STYLES + (expected[1] & 14), 2)
    assert get(memory, slot(memory, slots, 'model_face_admission_bits_scratch')) == 1
    assert cpu.d[0] == 32 and admitted(memory)


def test_zero_count_reaches_original_copy_loop_without_a_positive_count_guard(original_image, memory, slots):
    cpu, cache, _ = prepare(memory, slots, header=0x8807)
    run(original_image, memory, cpu, {0x4C56})
    assert cpu.d[2] & 65535 == 0 and cpu.a[5] == ADMITTED + 2
    assert get(memory, ADMITTED, 2) == 7 and get(memory, 0x52BE, 2) == 0


def encoded_fixture(m, slots, points):
    for i in range(9): word(m, slot(m, slots, 'model_view_matrix') + 2 * i, 16384 if i in [0, 4, 8] else 0)
    values = sorted(set(v for point in points for v in point))
    for i, value in enumerate(values): word(m, POOL + 2 * i, value)
    for i, point in enumerate(points):
        for j, value in enumerate(point): word(m, SOURCE + 8 * i + 2 * j, 2 * values.index(value))
        word(m, SOURCE + 8 * i + 6, 65535)
    return values


@pytest.mark.parametrize('flag', [0, 128, 255])
@pytest.mark.parametrize('points', [TRIANGLE, ACCEPT])
def test_actual_cache_misses_feed_refresh_and_preserve_view_ready_results(original_image, memory, slots, flag, points):
    cpu, cache, _ = prepare(memory, slots, points, flag=flag)
    encoded_fixture(memory, slots, points)
    run(original_image, memory, cpu, {0x4C8A})
    assert admitted(memory) == (backface_value(points) < 0)
    for i, point in enumerate(points):
        assert [get(memory, cache + 8 * i + 2 * j, 2) for j in range(3)] == list(point)
        assert memory[cache + 8 * i + 6] == 1
        assert memory[cache + 8 * i + 7] == 0xA5


@pytest.mark.parametrize('points', [TRIANGLE, ACCEPT, ACCEPT + [(100, 100, 1000)]])
def test_actual_admission_to_transformation_projection_and_packet_handoff(original_image, memory, slots, points):
    from tests.test_starglider2_ground_face_packets import project
    cpu, cache, _ = prepare(memory, slots, points, header=(len(points) << 8) | 3, flag=0)
    encoded_fixture(memory, slots, points)
    word(memory, slot(memory, slots, 'model_last_vertex_index'), len(points) - 1)
    for off, value in [(0x194, 159), (0x196, 79), (0xE4, 16), (0xE6, 303), (0xE8, 30), (0xEA, 128)]:
        word(memory, APP + off, value)
    put(memory, 0x3C30, OUTPUT); put(memory, 0x3C2C, REFS)
    word(memory, 0x49A8, 0)
    memory[OUTPUT - 4:OUTPUT + 128] = b'\xCC' * 132
    memory[REFS - 4:REFS + 16] = b'\xA5' * 20
    expected = backface_value(points) < 0
    run(original_image, memory, cpu, {RETURN})
    assert get(memory, OBJECT_CACHE) == int(expected) and cpu.a[7] == STACK + 8
    assert get(memory, 0x49A8, 2) == int(expected)
    if expected:
        expected_packet = [1000, 3, *[v for point in points for v in project(point)[:2]], 65535]
        assert [get(memory, OUTPUT + 2 * i, 2) for i in range(len(expected_packet))] == expected_packet
        assert get(memory, REFS) == OUTPUT and get(memory, 0x3C2C) == REFS + 4
        assert get(memory, 0x3C30) == OUTPUT + 2 * len(expected_packet)
        assert get(memory, 0x52BE, 2) == 0
        if len(points) == 4:
            assert memory[cache + 3 * 8 + 6] == 255  # newly marked point uses the negative-byte transform path
    else:
        assert bytes(memory[OUTPUT:OUTPUT + 128]) == b'\xCC' * 128
        assert get(memory, 0x3C30) == OUTPUT and get(memory, 0x3C2C) == REFS


@pytest.mark.parametrize('count', [1, 2])
def test_refresh_reads_three_offsets_even_when_copy_count_is_smaller(original_image, memory, slots, count):
    cpu, cache, _ = prepare(memory, slots, ACCEPT, header=(count << 8) | 3, flag=0)
    encoded_fixture(memory, slots, ACCEPT)
    run(original_image, memory, cpu, {0x4C8A})
    assert admitted(memory) and cpu.a[4] == COMMANDS + 2 + 2 * count
    assert [memory[cache + 8 * i + 6] for i in range(3)] == [1, 1, 1]
