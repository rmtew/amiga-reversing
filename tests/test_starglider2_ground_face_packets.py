"""Original ground-face gates, phase cache and finite packet production.

Supplied headers/caches/matrices are not universal model domains, arena bounds,
cache lifetime/exclusion, normal-game reachability, pixels or hardware proof.
"""
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, INPUT, STACK, RETURN
from tests.test_starglider2_control_normalization import signed

OUTPUT, REFS, COMMANDS, RECORDS, POOL, VARIANT = [INPUT + n for n in [0x4000, 0x200, 0, 0x1000, 0x2000, 0x2400]]
FIELDS = ['active_model_ground_face_count', 'active_model_ground_face_commands', 'active_model_type_index',
          'active_ground_face_world_y_word', 'active_model_scale_shift', 'model_origin_delta_x',
          'model_origin_delta_y', 'model_origin_delta_z', 'view_rotation_matrix', 'model_view_matrix',
          'model_view_vertex_scratch_prefix', 'active_model_vertex_reference_records',
          'active_model_coordinate_pool', 'active_model_vertex_variant_data', 'model_rotation_0',
          'model_rotation_2', 'space_environment_flag', 'inside_structure_flag']


@pytest.fixture(scope='module')
def slots(tmp_path_factory):
    target = Path(__file__).resolve().parents[1] / 'targets/amiga_raw_starglider2_game'
    temp = tmp_path_factory.mktemp('ground-fields')
    asm, out = temp / 'fields.s', temp / 'fields.bin'
    asm.write_text((target / 'starglider2_game.s').read_text().split('    SECTION code,code', 1)[0]
                   + '\n SECTION constants,data\n dc.l ' + ','.join(FIELDS) + '\n')
    result = subprocess.run([str(target.parents[1] / 'tools/vasmm68k_mot.exe'), '-quiet', '-Fbin', '-no-opt',
                             '-I' + str(target / 'includes'), '-o', str(out), str(asm)],
                            cwd=target, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    return dict(zip(FIELDS, struct.unpack('>' + str(len(FIELDS)) + 'I', out.read_bytes())))


def word(m, p, v):
    put(m, p, v & 65535, 2)


def field(m, slots, name, value, width=2):
    put(m, APP + slots[name], value & ((1 << (8 * width)) - 1), width)


def prepare(m, slots, faces=1, vertices=(0, 8)):
    for name, value, width in [('active_model_ground_face_count', faces, 2),
                              ('active_model_ground_face_commands', COMMANDS, 4),
                              ('active_model_vertex_reference_records', RECORDS, 4),
                              ('active_model_coordinate_pool', POOL, 4),
                              ('active_model_type_index', 0, 2), ('active_model_scale_shift', 0, 2),
                              ('active_ground_face_world_y_word', 0, 2), ('model_origin_delta_z', 1000, 2)]:
        field(m, slots, name, value, width)
    for off, value in [(0x194, 159), (0x196, 79), (0xE4, 16), (0xE6, 303), (0xE8, 30), (0xEA, 128)]:
        word(m, APP + off, value)
    word(m, 0x18B8, 1)
    word(m, 0x5918, 0)
    word(m, 0x49A8, 0)
    put(m, 0x3C30, OUTPUT)
    put(m, 0x3C2C, REFS)
    m[OUTPUT - 4:OUTPUT + 256] = b'\xCC' * 260
    m[REFS - 4:REFS + 40] = b'\xA5' * 44
    cache = APP + slots['model_view_vertex_scratch_prefix']
    for i in range(4):
        for j, value in enumerate([40 + i * 20, 50 + i * 10, 0, 0xFEDC]):
            word(m, cache + 8 * i + 2 * j, value)
    cursor = COMMANDS
    for _ in range(faces):
        word(m, cursor, (len(vertices) << 8) | 0xA7)
        cursor += 2
        for value in vertices:
            word(m, cursor, value)
            cursor += 2
    return state(m, 0x4FAC), cache, cursor


@pytest.mark.parametrize('reason', ['no_faces', 'disabled', 'space', 'inside', 'type72', 'type103',
                                     'low_world_y', 'count145', 'count32767', 'depth0', 'depth128',
                                     'left', 'right', 'top', 'bottom'])
def test_entry_gates_publish_unchanged_cursors_before_reading_commands(original_image, memory, slots, reason):
    cpu, cache, _ = prepare(memory, slots)
    if reason == 'no_faces': field(memory, slots, 'active_model_ground_face_count', 0)
    elif reason == 'disabled': word(memory, 0x18B8, 0)
    elif reason in ['space', 'inside']: field(memory, slots, 'space_environment_flag' if reason == 'space' else 'inside_structure_flag', 128, 1)
    elif reason.startswith('type'): field(memory, slots, 'active_model_type_index', int(reason[4:]))
    elif reason == 'low_world_y': field(memory, slots, 'active_ground_face_world_y_word', -12001)
    elif reason.startswith('count'): word(memory, 0x49A8, int(reason[5:]))
    elif reason.startswith('depth'): field(memory, slots, 'model_origin_delta_z', int(reason[5:]))
    else: field(memory, slots, 'model_origin_delta_x' if reason in ['left', 'right'] else 'model_origin_delta_y', -2000 if reason in ['left', 'top'] else 2000)
    before = bytes(memory[OUTPUT - 4:OUTPUT + 256]), bytes(memory[REFS - 4:REFS + 40]), bytes(memory[cache:cache + 32])
    run(original_image, memory, cpu, {RETURN})
    assert get(memory, 0x3C30) == OUTPUT and get(memory, 0x3C2C) == REFS
    assert (bytes(memory[OUTPUT - 4:OUTPUT + 256]), bytes(memory[REFS - 4:REFS + 40]), bytes(memory[cache:cache + 32])) == before
    assert cpu.a[7] == STACK + 4


@pytest.mark.parametrize('initial_count', [0, 143, 144])
@pytest.mark.parametrize('header_low', [0, 0xFF])
def test_real_cached_phase_can_advance_count_to146_and_ignores_low_header_byte(original_image, memory, slots, initial_count, header_low):
    cpu, cache, _ = prepare(memory, slots, faces=3)
    for i in range(3): word(memory, COMMANDS + 6 * i, 0xF200 | header_low)
    word(memory, 0x49A8, initial_count)
    before = bytes(memory[cache:cache + 32])
    run(original_image, memory, cpu, {RETURN})
    made = min(3, 146 - initial_count)
    assert get(memory, 0x49A8, 2) == initial_count + made
    assert get(memory, 0x3C30) == OUTPUT + made * 14 and get(memory, 0x3C2C) == REFS + made * 4
    for i in range(made):
        assert [get(memory, OUTPUT + 14 * i + 2 * j, 2) for j in range(7)] == [0x7FE0, 0, 40, 50, 60, 60, 65535]
        assert get(memory, REFS + 4 * i) == OUTPUT + 14 * i
    assert bytes(memory[cache:cache + 32]) == before


def test_cache_marker_bypasses_depth_and_clamp_checks(original_image, memory, slots):
    cpu, cache, _ = prepare(memory, slots)
    word(memory, cache, 500)
    word(memory, cache + 2, -10)
    word(memory, cache + 4, 0)
    run(original_image, memory, cpu, {RETURN})
    assert [get(memory, OUTPUT + 4 + 2 * i, 2) for i in range(2)] == [500, 65526]


def q14(product):
    return signed(((product << 2) & 0xFFFFFFFF) >> 16)


def transform_encoded(refs, pool, matrix, scale, origin):
    result = []
    for row, base in zip(matrix, origin):
        value = 0
        for coefficient, ref in zip(row, refs):
            term = q14(coefficient * pool[(ref & 32767) // 2])
            value = signed(value + (-term if ref & 32768 else term))
        result.append(signed((value >> scale) + base))
    return result


def project(point):
    x, y, z = point
    if z <= 128: return None
    if z >= 12000:
        x, y = int(x * 128 / z), int(y * 128 / z)
    else:
        z &= 65534
        coefficient = 0x4000 // (z - 1) if z <= 128 else 0x3FFF80 // (z - 2)
        # Original low-WORD extraction after doubling signed products.
        x = signed(((coefficient * point[0] * 2) & 0xFFFFFFFF) >> 16)
        y = signed(((coefficient * point[1] * 2) & 0xFFFFFFFF) >> 16)
    return max(16, min(303, signed(x + 159))), max(30, min(128, signed(y + 79))), z


@pytest.mark.parametrize('scale', [0, 1, 3, 7, 15])
@pytest.mark.parametrize('variant', ['none', 'negative_offset', 'selected'])
@pytest.mark.parametrize('rotated', [False, True])
@pytest.mark.parametrize('negative_x', [False, True])
@pytest.mark.parametrize('cache_byte', [0, 2, 255])
def test_actual_transform_variant_ground_drop_and_projected_cache_reuse(original_image, memory, slots, scale, variant, rotated, negative_x, cache_byte):
    cpu, cache, _ = prepare(memory, slots, vertices=(0, 0))
    view = [[16384, 8192, 0], [0, 16384, 0], [0, -8192, 16384]]
    model = [[-8192, 16384, 0], [-16384, 0, 0], [8192, 0, 16384]] if rotated else view
    built = [[0, 16384, 0], [-16384, 0, 0], [0, 0, 16384]]
    for name, matrix in [('view_rotation_matrix', view), ('model_view_matrix', model)]:
        for i, v in enumerate(sum(matrix, [])): word(memory, APP + slots[name] + 2 * i, v)
    for i, v in enumerate(sum(built, [])): word(memory, 0x2BFC + 2 * i, v)
    pool = [8, 21, 800, 35]
    for i, v in enumerate(pool): word(memory, POOL + 2 * i, v)
    normal = [32768 if negative_x else 0, 2, 4]
    selected = [normal[0], 0x8006, 4]
    for i, v in enumerate(normal): word(memory, RECORDS + 2 * i, v)
    word(memory, RECORDS + 6, 65535 if variant == 'negative_offset' else 0)
    for i, v in enumerate(selected): word(memory, VARIANT + 2 * i, v)
    field(memory, slots, 'active_model_vertex_variant_data', 0 if variant == 'none' else VARIANT, 4)
    field(memory, slots, 'active_model_scale_shift', scale)
    field(memory, slots, 'model_rotation_2', int(rotated))
    field(memory, slots, 'active_ground_face_world_y_word', -100)
    word(memory, cache + 6, (cache_byte << 8) | 0xA5)
    refs = selected if variant == 'selected' else normal
    decoded = [signed(-pool[(r & 32767) // 2] if r & 32768 else pool[r // 2]) for r in refs]
    vertical = q14(-16384 * decoded[0]) if rotated else decoded[1]
    drop = signed(-(vertical >> scale))
    base = transform_encoded(refs, pool, model, scale, [0, 0, 1000])
    point = [signed(v + q14(c * 100) + q14(c * drop)) for v, c in zip(base, [8192, 16384, -8192])]
    expected = project(point)
    run(original_image, memory, cpu, {RETURN})
    assert expected is not None
    assert [get(memory, cache + 2 * i, 2) for i in range(4)] == [*expected, 0xFEDC]
    assert [get(memory, OUTPUT + 2 * i, 2) for i in range(7)] == [0x7FE0, 0, *expected[:2], *expected[:2], 65535]
    assert get(memory, 0x49A8, 2) == 1 and get(memory, 0x3C30) == OUTPUT + 14


@pytest.mark.parametrize('depth', [0, 128, 129, 130, 11999, 12000, 12001, 32767, 32768, 65535])
def test_view_ready_byte_retains_base_xyz_until_depth_gate_and_projection(original_image, memory, slots, depth):
    cpu, cache, end = prepare(memory, slots)
    for j, value in enumerate([1000, -1000, depth, 0x01A5]): word(memory, cache + 2 * j, value)
    expected = project([1000, -1000, signed(depth)])
    run(original_image, memory, cpu, {RETURN})
    assert cpu.a[5] == end
    if expected is None:
        assert get(memory, 0x49A8, 2) == 0
        assert get(memory, 0x3C30) == OUTPUT and get(memory, 0x3C2C) == REFS
        assert get(memory, OUTPUT, 2) == 0x7FE0 and get(memory, OUTPUT + 4) == 0xCCCCCCCC
        assert get(memory, cache + 6, 2) == 0x01A5
    else:
        assert [get(memory, cache + 2 * j, 2) for j in range(4)] == [*expected, 0xFEDC]
        assert [get(memory, OUTPUT + 4 + 2 * j, 2) for j in range(2)] == list(expected[:2])
        assert get(memory, 0x49A8, 2) == 1


def test_rejection_skips_unread_offsets_and_keeps_prior_cache_and_scratch_writes(original_image, memory, slots):
    cpu, cache, _ = prepare(memory, slots, faces=2)
    for i, values in enumerate([(0, 0, 200, 0x01A5), (20, 30, 300, 0x01A5),
                                (5, 6, 128, 0x01A5), (7, 8, 500, 0x01A5), (40, 50, 400, 0x01A5)]):
        for j, value in enumerate(values): word(memory, cache + 8 * i + 2 * j, value)
    for j, value in enumerate([0x0400, 0, 8, 16, 24, 0x0100, 32]): word(memory, COMMANDS + 2 * j, value)
    run(original_image, memory, cpu, {RETURN})
    expected = project([40, 50, 400])
    assert [get(memory, OUTPUT + 2 * j, 2) for j in range(5)] == [0x7FE0, 0, *expected[:2], 65535]
    assert get(memory, OUTPUT + 10, 2) == project([20, 30, 300])[1]  # prior partial vertex survives
    assert get(memory, OUTPUT + 12) == 0xCCCCCCCC
    assert get(memory, REFS) == OUTPUT and get(memory, 0x3C2C) == REFS + 4
    assert get(memory, 0x3C30) == OUTPUT + 10 and get(memory, 0x49A8, 2) == 1
    assert [get(memory, cache + 8 * i + 6, 2) for i in range(5)] == [0xFEDC, 0xFEDC, 0x01A5, 0x01A5, 0xFEDC]
    assert cpu.a[5] == COMMANDS + 14 and cpu.a[7] == STACK + 4


def test_zero_vertex_nibble_is_not_rejected_before_original_dbf_setup(original_image, memory, slots):
    cpu, cache, _ = prepare(memory, slots)
    word(memory, COMMANDS, 0xF0FF)
    run(original_image, memory, cpu, {0x50F6})
    assert cpu.d[0] & 65535 == 65535 and get(memory, 0x49A8, 2) == 1
    assert get(memory, REFS) == OUTPUT and get(memory, OUTPUT) == 0x7FE00000


def test_signed_world_y_cutoff_equality_passes_the_original_gate(original_image, memory, slots):
    cpu, cache, _ = prepare(memory, slots)
    field(memory, slots, 'active_ground_face_world_y_word', -12000)
    run(original_image, memory, cpu, {RETURN})
    assert get(memory, 0x49A8, 2) == 1
