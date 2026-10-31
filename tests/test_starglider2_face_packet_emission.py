"""Original admitted-face to scene-polygon packet paths with supplied records.

These finite CPU cases do not establish model indices, queue/arena capacity,
shared lifetime, all clipper paths, normal-game reachability or pixel output.
"""
import pytest

from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, INPUT, STACK
from tests.test_starglider2_control_normalization import signed

PROJECTED, VIEW = 0x4B35E, APP + 0x21E
OUTPUT, REFS, COMMANDS = INPUT + 0x4000, INPUT + 0x200, INPUT
COUNT, REMAIN, START, STYLE = 0x49A8, 0x52BE, 0x52BA, 0x52C0


def word(m, p, v):
    put(m, p, v & 65535, 2)


def quotient(a, b):
    return (-1 if a < 0 else 1) * (abs(a) // b)


def classified_style(style, xs):
    low = min(xs) if xs else 32767
    high = max(xs) if xs else -32768
    delta = ((high & 0xFFF0) - (low & 0xFFF0)) & 65535
    if delta == 0:
        return (-style) & 65535
    if delta in (1, 65535):
        return (-(style + 16)) & 65535
    return style & 65535


def prepare(m, style, vertices):
    m[OUTPUT - 4:OUTPUT + 128] = b'\xCC' * 132
    m[REFS - 4:REFS + 32] = b'\xA5' * 36
    word(m, COMMANDS, style)
    for i, (x, y, depth) in enumerate(vertices):
        word(m, COMMANDS + 2 + 2 * i, 8 * i)
        for p, v in zip([PROJECTED + 8 * i, PROJECTED + 8 * i + 2, PROJECTED + 8 * i + 4], (x, y, depth)):
            word(m, p, v)
        m[VIEW + 8 * i + 6:VIEW + 8 * i + 8] = b'\xFF\0'
    word(m, COMMANDS + 2 + 2 * len(vertices), 65535)
    word(m, COUNT, 0)
    word(m, REMAIN, 1)
    cpu = state(m, 0x4D80)
    cpu.a[3], cpu.a[4], cpu.a[5] = REFS, OUTPUT, COMMANDS
    return cpu


VERTICES = [[], [(7, 3, 129)], [(15, 2, 150), (16, 4, 300)],
            [(1, 3, -20), (14, 8, 19)], [(1, 3, 100), (17, 8, 301), (9, 5, 202)],
            [(303, 128, 30000), (16, 30, 29999), (20, 35, -100)]]


@pytest.mark.parametrize('style', [0, 1, 7, 15, 16, 127, 32767, 32768, 65535])
@pytest.mark.parametrize('vertices', VERTICES)
def test_fast_path_writes_xy_average_signed_depth_and_width_classification(original_image, memory, style, vertices):
    cpu = prepare(memory, style, vertices)
    run(original_image, memory, cpu, {0x4F7C})
    depth = quotient(sum(signed(v[2]) for v in vertices), len(vertices)) if vertices else 0
    expected = [depth, classified_style(style, [signed(v[0]) for v in vertices]),
                *[value for x, y, z in vertices for value in (x, y)], 65535]
    assert [get(memory, OUTPUT + 2 * i, 2) for i in range(len(expected))] == [v & 65535 for v in expected]
    end = OUTPUT + 2 * len(expected)
    assert cpu.a[4] == end and cpu.a[3] == REFS + 4 and get(memory, REFS) == OUTPUT
    assert get(memory, COUNT, 2) == 1 and get(memory, REMAIN, 2) == 1
    assert get(memory, REFS + 4) == 0xA5A5A5A5
    assert bytes(memory[OUTPUT - 4:OUTPUT]) == bytes(memory[end:end + 4]) == b'\xCC' * 4
    assert cpu.a[7] == STACK


@pytest.mark.parametrize('flags', [(0, 1, 0), (1, 1, 1), (2, 2), (4, 4), (8, 8), (128, 128), (1, 2, 4), (129, 129)])
def test_outcodes_rewind_packet_and_gather_view_records_before_conditional_clipping(original_image, memory, flags):
    vertices = [(20 + i * 4, 40 + i, 200) for i in range(len(flags))]
    cpu = prepare(memory, 3, vertices)
    for i, flag in enumerate(flags):
        for j, value in enumerate((10 + i, 20 - i, 300 + i)):
            word(memory, VIEW + 8 * i + 2 * j, value)
        memory[VIEW + 8 * i + 7] = flag
    run(original_image, memory, cpu, {0x4E72, 0x4F7C})
    common = 15
    for f in flags:
        common &= f
    assert cpu.pc == (0x4F7C if common else 0x4E72)
    assert get(memory, STYLE, 2) == 3
    for i in range(len(flags)):
        assert bytes(memory[STYLE + 2 + 6 * i:STYLE + 8 + 6 * i]) == bytes(memory[VIEW + 8 * i:VIEW + 8 * i + 6])
    assert cpu.a[4] == OUTPUT and cpu.a[3] == REFS and cpu.a[7] == STACK
    assert get(memory, COUNT, 2) == 0
    # Original speculative header/XY stores remain in scratch after rewind.
    assert get(memory, OUTPUT, 2) == 0 and get(memory, OUTPUT + 2, 2) == 3


def prepare_clipped(m, points, style=3):
    m[OUTPUT - 4:OUTPUT + 128] = b'\xCC' * 132
    m[REFS - 4:REFS + 32] = b'\xA5' * 36
    for i, point in enumerate(points):
        for j, value in enumerate(point):
            word(m, COMMANDS + 6 * i + 2 * j, value)
    word(m, STYLE, style)
    word(m, COUNT, 10)
    word(m, REMAIN, 1)
    for off, value in [(0x194, 159), (0x196, 79), (0xE4, 16), (0xE6, 303), (0xE8, 30), (0xEA, 128)]:
        word(m, APP + off, value)
    cpu = state(m, 0x4E9C)
    cpu.a[2], cpu.a[3], cpu.a[4], cpu.d[7] = COMMANDS, REFS, OUTPUT, len(points)
    return cpu


def projected(point):
    x, y, z = map(signed, point)
    divisor = (2 * z) & 65535
    if divisor == 0 or divisor & 32768:
        return None
    x = quotient(x * 288, divisor) + 159
    y = quotient(y * 98, divisor) + 79
    return max(16, min(303, x)), max(30, min(128, y)), divisor


POINTS = [[(20, 30, 200)], [(20, 30, 200)] * 2,
          [(0, 0, 200), (100, -100, 201)],
          [(-1000, -1000, 128), (1000, 1000, 129), (0, 0, 16383)],
          [(0, 0, 200), (10, 20, 300), (0, 0, 200)],
          [(0, 0, 200), (10, 20, 300), (0, 0, 200), (0, 0, 200)]]


@pytest.mark.parametrize('points', POINTS)
@pytest.mark.parametrize('style', [0, 1, 7, 15, 65535])
def test_clipped_packet_removes_one_closing_xyz_and_averages_doubled_depth(original_image, memory, points, style):
    cpu = prepare_clipped(memory, points, style)
    unique = points[:-1] if points[-1] == points[0] else points
    run(original_image, memory, cpu, {0x4F7C})
    if not unique:
        assert bytes(memory[OUTPUT:OUTPUT + 128]) == b'\xCC' * 128
        assert cpu.a[3] == REFS and get(memory, COUNT, 2) == 10
        return
    values = [projected(p) for p in unique]
    expected = [sum(z for x, y, z in values) // len(values),
                classified_style(style, [x for x, y, z in values]),
                *[v for x, y, z in values for v in (x, y)], 65535]
    assert [get(memory, OUTPUT + 2 * i, 2) for i in range(len(expected))] == expected
    assert cpu.a[4] == OUTPUT + 2 * len(expected) and cpu.a[3] == REFS + 4
    assert get(memory, COUNT, 2) == 11 and get(memory, START) == OUTPUT


@pytest.mark.parametrize('invalid', [0, 16384, 32767, 32768, 65535])
@pytest.mark.parametrize('first_valid', [False, True])
def test_invalid_doubled_depth_withdraws_reference_without_erasing_partial_packet(original_image, memory, invalid, first_valid):
    points = ([(0, 0, 200)] if first_valid else []) + [(20, 30, invalid), (1, 1, 300)]
    cpu = prepare_clipped(memory, points)
    run(original_image, memory, cpu, {0x4F7C})
    assert cpu.a[3] == REFS and cpu.a[4] == OUTPUT and get(memory, COUNT, 2) == 10
    assert get(memory, REFS) == get(memory, START) == OUTPUT
    assert get(memory, OUTPUT, 2) == 0 and get(memory, OUTPUT + 2, 2) == 3
    if first_valid:
        assert (get(memory, OUTPUT + 4, 2), get(memory, OUTPUT + 6, 2)) == (159, 79)
    assert get(memory, OUTPUT + (8 if first_valid else 4)) == 0xCCCCCCCC


@pytest.mark.parametrize('count', [0, 143, 144, 145, 32766, 32767, 65535])
def test_post_emission_count_gate_preserves_remaining_counter_on_cap(original_image, memory, count):
    cpu = prepare(memory, 7, [(1, 2, 300), (20, 3, 400)])
    # Stop at the actual post-face count gate, avoiding a guessed second command.
    word(memory, COUNT, count)
    word(memory, REMAIN, 3)
    run(original_image, memory, cpu, {0x4F88, 0x4F92})
    actual = (count + 1) & 65535
    assert get(memory, COUNT, 2) == actual and get(memory, REMAIN, 2) == 3
    assert cpu.pc == (0x4F92 if signed(actual) >= 145 else 0x4F88)


@pytest.mark.parametrize('initial_count', [0, 143, 144, 145, 32767, 65535])
def test_actual_multi_face_loop_publishes_cursors_and_keeps_original_cap_order(original_image, memory, initial_count):
    cpu = prepare(memory, 7, [(1, 2, 300), (20, 3, 400)])
    for i in range(3):
        for j, value in enumerate([7, 0, 8, 65535]):
            word(memory, COMMANDS + 8 * i + 2 * j, value)
    word(memory, COUNT, initial_count)
    word(memory, REMAIN, 3)
    count, pending, processed = initial_count, 3, 0
    while True:
        count = (count + 1) & 65535
        processed += 1
        if signed(count) >= 145:
            break
        pending -= 1
        if not pending:
            break
    run(original_image, memory, cpu, {0xFFFFFF00})
    assert get(memory, COUNT, 2) == count and get(memory, REMAIN, 2) == pending
    assert get(memory, 0x3C30) == OUTPUT + 14 * processed
    assert get(memory, 0x3C2C) == REFS + 4 * processed
    for i in range(processed):
        assert get(memory, REFS + 4 * i) == OUTPUT + 14 * i
        assert [get(memory, OUTPUT + 14 * i + 2 * j, 2) for j in range(7)] == [350, 7, 1, 2, 20, 3, 65535]
    assert cpu.a[7] == STACK + 4
