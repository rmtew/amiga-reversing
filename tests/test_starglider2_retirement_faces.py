"""Original retirement-face displacement, clipping score and packet withdrawal.

Finite supplied frames are not model/phase domains, queue capacity, lifetime,
normal-game reachability or hardware visibility. Original arithmetic is retained.
"""
import random
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, INPUT, STACK, RETURN
from tests.test_starglider2_control_normalization import signed
from tests.test_starglider2_face_admission import long_signed
from tests.test_starglider2_face_packet_emission import classified_style, quotient

COMMANDS, OUTPUT, REFS = INPUT, INPUT + 0x4000, INPUT + 0x200
FIELDS = ['model_view_vertex_scratch_prefix', 'active_model_retirement_phase_word',
          'retirement_face_displacement_x', 'retirement_face_displacement_y',
          'retirement_face_displacement_z', 'space_environment_flag', 'model_origin_delta_y',
          'model_face_vertex_count_scratch', 'drawing_fill_style_word', 'saved_model_face_loop_index',
          'projection_screen_origin_x', 'projection_screen_origin_y',
          'view_clip_min_x', 'view_clip_max_x', 'view_clip_min_y', 'view_clip_max_y',
          'active_model_header_counts', 'model_last_vertex_index', 'model_view_matrix',
          'active_model_vertex_reference_records', 'active_model_coordinate_pool',
          'active_model_vertex_variant_data', 'active_model_face_commands']


@pytest.fixture(scope='module')
def slots(tmp_path_factory):
    target = Path(__file__).resolve().parents[1] / 'targets/amiga_raw_starglider2_game'
    temp = tmp_path_factory.mktemp('retirement-fields')
    asm, out = temp / 'fields.s', temp / 'fields.bin'
    asm.write_text((target / 'starglider2_game.s').read_text().split('    SECTION code,code', 1)[0]
                   + '\n SECTION constants,data\n dc.l ' + ','.join(FIELDS) + '\n')
    result = subprocess.run([str(target.parents[1] / 'tools/vasmm68k_mot.exe'), '-quiet', '-Fbin', '-no-opt',
                             '-I' + str(target / 'includes'), '-o', str(out), str(asm)],
                            cwd=target, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    return dict(zip(FIELDS, struct.unpack('>' + str(len(FIELDS)) + 'I', out.read_bytes())))


def word(m, p, value): put(m, p, value & 65535, 2)
def field(m, slots, name): return APP + slots[name]


def prepare(m, slots, points, phase=0, space=True, count=0, style=3):
    cache = field(m, slots, 'model_view_vertex_scratch_prefix')
    for i, point in enumerate(points):
        for j, v in enumerate(point): word(m, cache + 8 * i + 2 * j, v)
        word(m, COMMANDS + 2 + 2 * i, 8 * i)
    word(m, COMMANDS, (len(points) << 8) | style)
    word(m, field(m, slots, 'active_model_retirement_phase_word'), phase)
    m[field(m, slots, 'space_environment_flag')] = 255 if space else 0
    for axis in 'xyz': put(m, field(m, slots, 'retirement_face_displacement_' + axis), 0xA5A5B6B6)
    for name, value in [('view_clip_min_x', -300), ('view_clip_max_x', 300),
                        ('view_clip_min_y', -200), ('view_clip_max_y', 200)]:
        word(m, field(m, slots, name), value)
    put(m, 0x3C30, OUTPUT); put(m, 0x3C2C, REFS); word(m, 0x49A8, count)
    m[OUTPUT - 4:OUTPUT + 128] = b'\xCC' * 132
    m[REFS - 4:REFS + 16] = b'\xA5' * 20
    cpu = state(m, 0x5460); cpu.a[4] = COMMANDS; cpu.d[0] = 0
    return cpu


def displacements(points, phase, bias=None):
    p, q, r = points[:3]
    e = [signed(b - a) for a, b in zip(p, q)]
    f = [signed(b - a) for a, b in zip(p, r)]
    cross = [f[2] * e[1] - f[1] * e[2], f[0] * e[2] - f[2] * e[0],
             f[1] * e[0] - f[0] * e[1]]
    result = []
    for axis, (value, shift) in enumerate(zip(cross, [5, 6, 5])):
        value = signed(long_signed(value) >> shift) * signed(phase)
        if axis == 1 and bias is not None:
            value = long_signed((value & 0xFFFF0000) | ((value + bias) & 65535))
        result.append(signed(value >> 3))
    return result


RNG = random.Random(68000)
GEOMETRY = [[(0, 0, 1000), (100, 0, 1000), (0, 100, 1000)]]
GEOMETRY += [[tuple(RNG.randrange(-32768, 32768) for _ in range(3)) for _ in range(3)] for _ in range(12)]


@pytest.mark.parametrize('points', GEOMETRY)
@pytest.mark.parametrize('phase', [0, 1, 15, 32768, 65535])
def test_original_cross_products_truncate_before_phase_multiply(original_image, memory, slots, points, phase):
    cpu = prepare(memory, slots, points, phase)
    run(original_image, memory, cpu, {0x558A})
    expected = displacements(points, phase)
    for axis, v in zip('xyz', expected):
        p = field(memory, slots, 'retirement_face_displacement_' + axis)
        assert get(memory, p, 2) == v & 65535
        assert get(memory, p + 2, 2) == 0xB6B6  # WORD write into declared LONG slot


@pytest.mark.parametrize('phase', [0, 1, 2, 15, 16, 30, 31, 62, 63])
def test_original_surface_bias_adds_only_low_word_before_long_shift(original_image, memory, slots, phase):
    points = [(31000, -30000, 29000), (-20000, 17000, 13000), (15000, 27000, -31000)]
    cpu = prepare(memory, slots, points, phase, space=False)
    run(original_image, memory, cpu, {0x5508})
    bias = signed(get(memory, 0x567C + (phase & 65534), 2))
    expected = displacements(points, phase, bias)[1]
    run(original_image, memory, cpu, {0x550E})
    assert signed(get(memory, field(memory, slots, 'retirement_face_displacement_y'), 2)) == expected


@pytest.mark.parametrize('depths', [(1000, 1001, 1003), (12000, 14000, 16000), (129, 130, 131)])
def test_full_face_packet_uses_last_projected_depth_not_average(original_image, memory, slots, depths):
    points = [(0, 0, depths[0]), (80, 0, depths[1]), (0, 60, depths[2])]
    cpu = prepare(memory, slots, points)
    run(original_image, memory, cpu, {RETURN})
    projected = []
    for x, y, depth in points:
        if depth >= 12000: xy = [quotient(x * 128, depth), quotient(y * 128, depth)]
        else:
            depth &= 65534
            coefficient = get(memory, 0x2ADF8 + depth, 2)
            xy = [signed(((signed(coefficient) * v * 2) & 0xFFFFFFFF) >> 16) for v in [x, y]]
        projected.append((*xy, depth))
    words = [projected[-1][2], classified_style(3, [p[0] for p in projected])]
    words += [v & 65535 for p in projected for v in p[:2]] + [65535]
    assert [get(memory, OUTPUT + 2 * i, 2) for i in range(len(words))] == words
    assert get(memory, 0x3C30) == OUTPUT + 2 * len(words)
    assert get(memory, 0x3C2C) == REFS + 4 and get(memory, REFS) == OUTPUT
    assert get(memory, 0x49A8, 2) == 1 and cpu.a[4] == COMMANDS + 8
    assert cpu.a[7] == STACK + 4


@pytest.mark.parametrize('failed_vertex', [0, 1, 2])
def test_depth_rejection_skips_unread_offsets_and_withdraws_early_reference(original_image, memory, slots, failed_vertex):
    points = [(0, 0, 1000), (10, 0, 1000), (0, 10, 1000)]
    points[failed_vertex] = (0, 0, 128)
    cpu = prepare(memory, slots, points, count=12)
    run(original_image, memory, cpu, {RETURN})
    assert cpu.a[4] == COMMANDS + 8
    assert get(memory, 0x3C30) == OUTPUT and get(memory, 0x3C2C) == REFS
    assert get(memory, 0x49A8, 2) == 12
    assert get(memory, REFS) == OUTPUT  # withdrawn slot is not erased
    assert get(memory, OUTPUT, 2) == 0 and get(memory, OUTPUT + 2, 2) == 3


def test_next_face_reuses_withdrawn_packet_and_reference_positions(original_image, memory, slots):
    points = [(0, 0, 1000), (10, 0, 128), (0, 10, 1000), (10, 10, 1000)]
    cpu = prepare(memory, slots, points)
    for i, v in enumerate([0x0303, 0, 8, 16, 0x0304, 0, 16, 24]): word(memory, COMMANDS + 2 * i, v)
    cpu.d[0] = 1
    run(original_image, memory, cpu, {RETURN})
    assert cpu.a[4] == COMMANDS + 16 and get(memory, 0x49A8, 2) == 1
    assert get(memory, 0x3C2C) == REFS + 4 and get(memory, REFS) == OUTPUT
    assert get(memory, 0x3C30) == OUTPUT + 18
    assert get(memory, OUTPUT, 2) == 1000 and get(memory, OUTPUT + 2, 2) == 65532
    assert get(memory, OUTPUT + 16, 2) == 65535


@pytest.mark.parametrize('coordinate,accepted', [(299, True), (300, False), (301, False), (-300, True), (-301, False)])
def test_maximum_equality_decrements_per_axis_score(original_image, memory, slots, coordinate, accepted):
    cpu = prepare(memory, slots, [(0, 0, 12000)] * 3)
    cpu.pc = 0x558A; cpu.a[1] = OUTPUT + 4; cpu.a[2] = OUTPUT + 2
    cpu.a[3] = field(memory, slots, 'model_view_vertex_scratch_prefix'); cpu.a[4] = COMMANDS + 2
    cpu.a[5] = 0x2ADF8; cpu.d[7] = cpu.d[4] = 3; cpu.d[6] = 32767; cpu.d[5] = 32768
    for axis in 'xyz': word(memory, field(memory, slots, 'retirement_face_displacement_' + axis), 0)
    word(memory, field(memory, slots, 'projection_screen_origin_x'), coordinate)
    word(memory, field(memory, slots, 'saved_model_face_loop_index'), 0)
    word(memory, OUTPUT, 0); word(memory, OUTPUT + 2, 3)
    put(memory, REFS, OUTPUT); put(memory, 0x3C2C, REFS + 4); word(memory, 0x49A8, 1)
    run(original_image, memory, cpu, {RETURN})
    assert get(memory, 0x49A8, 2) == int(accepted)
    assert get(memory, 0x3C30) == (OUTPUT + 18 if accepted else OUTPUT)


def test_two_vertex_command_skips_before_reading_geometry(original_image, memory, slots):
    cpu = prepare(memory, slots, [(1, 2, 1000), (3, 4, 1000)], count=145)
    run(original_image, memory, cpu, {RETURN})
    assert cpu.a[4] == COMMANDS + 6 and get(memory, 0x49A8, 2) == 145
    assert bytes(memory[OUTPUT:OUTPUT + 128]) == b'\xCC' * 128
    assert get(memory, 0x3C2C) == REFS


@pytest.mark.parametrize('coordinate_count', [0, 1, 7])
def test_zero_last_vertex_returns_after_inclusive_axis_flag_clear(original_image, memory, slots, coordinate_count):
    cpu = state(memory, 0x53E8)
    word(memory, 0x49A8, 0)
    word(memory, field(memory, slots, 'active_model_header_counts') + 2, coordinate_count)
    word(memory, field(memory, slots, 'model_last_vertex_index'), 0)
    base = 0x47862
    for axis in [0, 0x12C0, 0x2580]:
        memory[base + axis:base + axis + 8 * (coordinate_count + 2)] = b'\xA5' * (8 * (coordinate_count + 2))
    run(original_image, memory, cpu, {RETURN})
    for axis in [0, 0x12C0, 0x2580]:
        for i in range(coordinate_count + 1):
            assert get(memory, base + axis + 8 * i, 2) == 0
            assert bytes(memory[base + axis + 8 * i + 2:base + axis + 8 * i + 8]) == b'\xA5' * 6
        assert get(memory, base + axis + 8 * (coordinate_count + 1), 2) == 0xA5A5


@pytest.mark.parametrize('count', [144, 145])
def test_post_face_limit_allows_one_packet_at_threshold(original_image, memory, slots, count):
    cpu = prepare(memory, slots, [(0, 0, 1000), (10, 0, 1000), (0, 10, 1000)], count=count)
    run(original_image, memory, cpu, {RETURN})
    assert get(memory, 0x49A8, 2) == count + 1  # entry into face body, not the outer threshold gate


@pytest.mark.parametrize('count', [144, 145, 146, 32767, 32768, 65535])
def test_outer_count_guard_is_signed_greater_than_threshold(original_image, memory, slots, count):
    cpu = state(memory, 0x53E8)
    word(memory, 0x49A8, count)
    word(memory, field(memory, slots, 'active_model_header_counts') + 2, 0)
    word(memory, field(memory, slots, 'model_last_vertex_index'), 0)
    word(memory, 0x47862, 0xA5A5)
    run(original_image, memory, cpu, {RETURN})
    assert get(memory, 0x47862, 2) == (0xA5A5 if signed(count) > 145 else 0)
    assert get(memory, 0x49A8, 2) == count


@pytest.mark.parametrize('variant_offset', [-1, 0, 8])
@pytest.mark.parametrize('has_variant', [False, True])
def test_full_vertex_pass_selects_only_nonnegative_available_variants(original_image, memory, slots, variant_offset, has_variant):
    records, pool, variants = INPUT + 0x1000, INPUT + 0x2000, INPUT + 0x2400
    points = [(12, 24, 1000), (-12, 24, 1000)]
    values = [12, 24, 1000, 80, 96, 1200, 160, 192, 1400]
    for i, v in enumerate(values): word(memory, pool + 2 * i, v)
    for i in range(9): word(memory, field(memory, slots, 'model_view_matrix') + 2 * i, 16384 if i in [0, 4, 8] else 0)
    for i in range(2):
        for j, ref in enumerate([0x8000 if i else 0, 2, 4]): word(memory, records + 8 * i + 2 * j, ref)
        word(memory, records + 8 * i + 6, variant_offset)
    for offset, refs in [(0, [6, 8, 10]), (8, [12, 14, 16])]:
        for j, ref in enumerate(refs): word(memory, variants + offset + 2 * j, ref)
    for name, value in [('active_model_vertex_reference_records', records),
                        ('active_model_coordinate_pool', pool), ('active_model_face_commands', COMMANDS),
                        ('active_model_vertex_variant_data', variants if has_variant else 0)]:
        put(memory, field(memory, slots, name), value)
    word(memory, field(memory, slots, 'active_model_header_counts'), 0)  # no faces after actual vertex transform
    word(memory, field(memory, slots, 'active_model_header_counts') + 2, len(values) - 1)
    word(memory, field(memory, slots, 'model_last_vertex_index'), 1)
    word(memory, 0x49A8, 0)
    cache = field(memory, slots, 'model_view_vertex_scratch_prefix')
    for i in range(2): word(memory, cache + 8 * i + 6, 0xA5B6)
    cpu = state(memory, 0x53E8)
    run(original_image, memory, cpu, {RETURN})
    if has_variant and variant_offset >= 0:
        points = [tuple(values[j:j + 3]) for j in [3 if variant_offset == 0 else 6] * 2]
    for i, point in enumerate(points):
        assert [signed(get(memory, cache + 8 * i + 2 * j, 2)) for j in range(3)] == list(point)
        assert get(memory, cache + 8 * i + 6, 2) == 0xA5B6
    assert cpu.a[7] == STACK + 4 and get(memory, 0x49A8, 2) == 0
