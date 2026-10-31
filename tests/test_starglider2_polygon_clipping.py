"""Original five-plane XYZ clipping: bounded supplied polygons, not capacity proof.

The reference keeps WORD wrapping, Q15 rounding, edge order and consecutive-only
deduplication. These CPU cases do not establish normal-game reachability,
scratch capacity, framebuffer output, or the unentered raw point-tail slots.
"""
import pytest

from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, INPUT, RETURN, STACK
from tests.test_starglider2_control_normalization import signed
from tests.test_starglider2_point_field import fields

ENTRY, SCRATCH_A, SCRATCH_B = 0x5AF2, 0x5EEC, 0x5FAE


def word(m, p, value):
    put(m, p, value & 65535, 2)


def divide(n, d):
    assert d
    return (-1 if (n < 0) != (d < 0) else 1) * (abs(n) // abs(d))


def fraction(n, d):
    dividend = signed(n) << 15
    q = divide(dividend, signed(d))
    # Original DIVS overflow leaves the dividend unchanged; later MULS uses
    # its low WORD. Preserve that behavior rather than saturating the ratio.
    return signed(q if -32768 <= q <= 32767 else dividend)


def interpolate(a, b, ratio):
    return signed(a + ((signed(b - a) * ratio) >> 15))


def reference(points, mask):
    points = [(signed((signed(x) * 113) >> 8),
               signed((signed(y) * 334) >> 8), signed(z) >> 1)
              for x, y, z in points]
    address = SCRATCH_A
    if mask & 128:
        mask |= 15
    for plane, axis, sign in [(128, None, 1), (1, 0, -1),
                              (2, 0, 1), (4, 1, -1), (8, 1, 1)]:
        if not mask & plane:
            continue
        if not points:
            return [], address
        output = []
        for a, b in zip(points, points[1:] + points[:1]):
            a, b = list(a), list(b)
            if axis is None:
                outside_a, outside_b = a[2] < 128, b[2] < 128
            else:
                a[axis], b[axis] = signed(sign * a[axis]), signed(sign * b[axis])
                outside_a, outside_b = a[axis] > a[2], b[axis] > b[2]
            if outside_a and outside_b:
                continue
            if outside_a != outside_b:
                if axis is None:
                    ratio = fraction(128 - a[2], b[2] - a[2])
                else:
                    ratio = fraction(a[2] - a[axis],
                                     a[2] - b[2] + b[axis] - a[axis])
                cut = [interpolate(a[i], b[i], ratio) for i in range(2)]
                cut.append(128 if axis is None else cut[axis])
                if outside_a:
                    a = cut
                else:
                    b = cut
            if axis is not None:
                a[axis], b[axis] = signed(sign * a[axis]), signed(sign * b[axis])
            a, b = tuple(a), tuple(b)
            if not output or output[-1] != a:
                output.append(a)
            if b != a:
                output.append(b)
        points = output
        address = SCRATCH_B if address == SCRATCH_A else SCRATCH_A
    return points, address


POLYGONS = [
    [(0, 0, 1024)],
    [(0, 0, 1024), (100, 100, 1024)],
    [(-2000, 0, 1024), (100, 0, 1024)],
    [(100, 0, 1024), (2000, 0, 1024)],
    [(0, -1000, 1024), (0, 100, 1024)],
    [(0, 100, 1024), (0, 1000, 1024)],
    [(10, 20, 128), (100, 40, 1024)],
    [(10, 20, 256), (100, 40, 128)],  # Exact near endpoint: Q15 DIVS overflow.
    [(-100, -100, 1024), (100, -100, 1024), (0, 100, 1024)],
    [(-2000, -1000, 1024), (2000, -1000, 1024), (2000, 1000, 1024), (-2000, 1000, 1024)],
    [(0, 0, 64), (10, 10, 128)],
    [(2000, 0, 1024), (2200, 10, 1024)],
    [(0, 0, 1024), (0, 0, 1024), (100, 0, 1024)],
]


@pytest.mark.parametrize('mask', [0, 1, 2, 4, 8, 15, 128, 129, 255])
@pytest.mark.parametrize('points', POLYGONS)
def test_original_clipping_order_rounding_and_pingpong(original_image, memory, mask, points):
    m = memory
    for i, xyz in enumerate(points):
        for j, value in enumerate(xyz):
            word(m, INPUT + 6 * i + 2 * j, value)
    original_input = bytes(m[INPUT:INPUT + 6 * len(points)])
    # Guards are fixture backing, not an assertion about the original buffer's
    # maximum capacity. Check the entire written prefixes against the model.
    m[SCRATCH_A:SCRATCH_A + 194] = b'\xA5' * 194
    m[SCRATCH_B:SCRATCH_B + 192] = b'\x5A' * 192
    cpu = state(m, ENTRY)
    cpu.a[2], cpu.d[7], cpu.d[4] = INPUT, len(points), mask
    cpu.a[3] = 0  # MOVEA.W count overwrites all bits; no hidden high-WORD seed.
    expected, address = reference(points, mask)
    run(original_image, m, cpu, {RETURN})
    assert cpu.d[7] & 65535 == len(expected)
    assert cpu.a[2] == address
    actual = [tuple(signed(get(m, address + 6 * i + 2 * j, 2)) for j in range(3))
              for i in range(len(expected))]
    assert actual == expected
    assert bytes(m[INPUT:INPUT + 6 * len(points)]) == original_input
    assert cpu.a[6] == APP and cpu.a[7] == STACK + 4


@pytest.mark.parametrize('mask', [1, 2, 4, 8, 15, 128, 255])
def test_closed_edge_retains_first_vertex_again_but_collapses_adjacent_duplicates(original_image, memory, mask):
    points = [(0, 0, 1024), (100, 100, 1024)]
    expected, _ = reference(points, mask)
    assert expected == [(0, 0, 512), (44, 130, 512), (0, 0, 512)]
    for i, xyz in enumerate(points):
        for j, value in enumerate(xyz):
            word(memory, INPUT + 6 * i + 2 * j, value)
    cpu = state(memory, ENTRY)
    cpu.a[2], cpu.d[7], cpu.d[4] = INPUT, 2, mask
    run(original_image, memory, cpu, {RETURN})
    assert cpu.d[7] & 65535 == 3
    assert [tuple(signed(get(memory, cpu.a[2] + 6 * i + 2 * j, 2)) for j in range(3))
            for i in range(3)] == expected


def test_near_flag_enables_all_sides_and_suppresses_only_adjacent_duplicates(original_image, memory):
    points = [(-2000, -1000, 128), (2000, -1000, 1024), (2000, 1000, 1024), (-2000, 1000, 1024)]
    assert reference(points, 128) == reference(points, 143)
    assert fraction(-64, -64) == 0  # 32768 overflows DIVS.W; low dividend WORD is zero.
    results = []
    for mask in [128, 143]:
        for i, xyz in enumerate(points):
            for j, value in enumerate(xyz):
                word(memory, INPUT + 6 * i + 2 * j, value)
        cpu = state(memory, ENTRY)
        cpu.a[2], cpu.d[7], cpu.d[4] = INPUT, 4, mask
        run(original_image, memory, cpu, {RETURN})
        results.append((cpu.a[2], cpu.d[7] & 65535,
                        bytes(memory[cpu.a[2]:cpu.a[2] + 6 * (cpu.d[7] & 65535)])))
    assert results[0] == results[1]


@pytest.mark.parametrize('mask', [0, 128, 255])
def test_zero_count_underflows_before_the_first_copy_not_an_empty_input_guard(original_image, memory, mask):
    cpu = state(memory, ENTRY)
    cpu.a[2], cpu.d[7], cpu.d[4] = INPUT, 0, mask
    run(original_image, memory, cpu, {0x5B12})
    assert cpu.d[7] & 65535 == cpu.d[0] & 65535 == 65535
    assert cpu.a[3] == 0


def test_exact_near_endpoint_overflows_original_signed_division(original_image, memory):
    for i, xyz in enumerate([(10, 20, 256), (100, 40, 128)]):
        for j, value in enumerate(xyz):
            word(memory, INPUT + 6 * i + 2 * j, value)
    cpu = state(memory, ENTRY)
    cpu.a[2], cpu.d[7], cpu.d[4] = INPUT, 2, 128
    run(original_image, memory, cpu, {0x5B7C})
    dividend, divisor = cpu.d[0], signed(cpu.d[6])
    run(original_image, memory, cpu, {0x5B7E})
    assert dividend == 0 and divisor == -64
    # First edge's near endpoint has numerator zero and quotient zero. The
    # reverse edge reaches +32768, leaves DIVS dividend unchanged, and sets V.
    run(original_image, memory, cpu, {0x5B7C})
    dividend = cpu.d[0]
    assert signed(dividend, 32) == 64 << 15 and signed(cpu.d[6]) == 64
    run(original_image, memory, cpu, {0x5B7E})
    assert cpu.d[0] == dividend and cpu.sr & 2


@pytest.mark.parametrize('mask,current,previous', [
    (1, (-2000, 0, 1024), (100, 0, 1024)),
    (2, (100, 0, 1024), (2000, 0, 1024)),
    (4, (0, -1000, 1024), (0, 100, 1024)),
    (8, (0, 100, 1024), (0, 1000, 1024)),
    (128, (10, 20, 128), (100, 40, 1024)),
])
@pytest.mark.parametrize('bounds', [(0, 319, 0, 159), (16, 303, 30, 128)])
def test_real_point_trail_caller_clips_projects_or_recycles(original_image, memory, fields, mask, current, previous, bounds):
    m = memory
    for j, value in enumerate(current):
        word(m, INPUT + 2 * j, value)
    put(m, 0x4E5C0, INPUT + 6)
    for key, value in zip(['projection_screen_origin_x', 'projection_screen_origin_y',
                           'view_clip_min_x', 'view_clip_max_x', 'view_clip_min_y', 'view_clip_max_y'],
                          [159, 79, *bounds]):
        word(m, fields[key], value)
    cpu = state(m, 0x4E480)
    # state() installs an RTS target; this entry instead consumes three saved
    # WORDs before saving its own LONG register frame.
    for j, value in enumerate(previous):
        word(m, STACK + 2 * j, value)
    put(m, STACK + 6, RETURN)
    reference_cells, packet = INPUT + 0x1000, INPUT + 0x2000
    put(m, 0x3C2C, reference_cells)
    put(m, 0x3C30, packet)
    word(m, 0x49A8, 65535)
    word(m, fields['selected_celestial_body_index'], 0)
    cpu.d[3], cpu.d[7] = mask, 0
    clipped, _ = reference([current, previous], mask)
    assert len(clipped) >= 2
    projected = [(signed(divide(x * 288, z * 2) + 159),
                  signed(divide(y * 98, z * 2) + 79)) for x, y, z in clipped[:2]]
    accepted = all(signed(x - bounds[0]) >= 0 and signed(x - bounds[1]) < 0
                   and signed(y - bounds[2]) >= 0 and signed(y - bounds[3]) < 0
                   for x, y in projected)
    run(original_image, m, cpu, {0x4E22E, 0x4E350})
    assert cpu.pc == (0x4E22E if accepted else 0x4E350)
    assert cpu.a[7] == STACK + 6 and cpu.a[6] == APP and cpu.d[7] == 0
    assert [signed(get(m, 0x52C0 + 6 * i + 2 * j, 2))
            for i in range(2) for j in range(3)] == [*current, *previous]
    if accepted:
        assert tuple(signed(cpu.d[i]) for i in [1, 2, 4, 5]) == (*projected[0], *projected[1])
        assert cpu.d[3] & 65535 == 2 * clipped[0][2]
        assert cpu.d[6] & 65535 == 2 * clipped[1][2]
        depth = cpu.d[6] & 65535
        style = get(m, 0x4E5A4 + ((depth >> 11) & 14), 2)
        run(original_image, m, cpu, {RETURN})
        assert cpu.a[7] == STACK + 10
        assert get(m, reference_cells) == packet and get(m, 0x3C2C) == reference_cells + 4
        assert get(m, 0x3C30) == packet + 14 and get(m, 0x49A8, 2) == 0
        assert [get(m, packet + 2 * i, 2) for i in range(7)] == [
            depth, style, *projected[0], *projected[1], 65535]
    else:
        assert get(m, 0x3C2C) == reference_cells and get(m, 0x3C30) == packet
        assert get(m, 0x49A8, 2) == 65535
