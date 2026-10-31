"""Original Q16 line spans and two-chain polygon-edge interpolation.

Supplied RAM contours establish local arithmetic and register transport, not
normal-game coordinate domains, general polygon validity, capacity or scanout.
"""
import pytest

from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, INPUT, STACK
from tests.test_starglider2_scene_packets import CYCLE, HEADERS, OUTPUT, polygon, word
from tests.test_starglider2_control_normalization import signed

SPANS, RECIPROCAL, HANDOFF = 0x41848, 0x4B99E, 0x3DB30


def prepare(m, packets, sentinel=65535, d5_fraction=0x1234):
    for i, points in enumerate(packets):
        polygon(m, HEADERS + 0x100 * i, points, style=7 + i, sentinel=sentinel)
        put(m, INPUT + 4 * i, HEADERS + 0x100 * i)
    put(m, INPUT + 4 * len(packets), 0xFFFFFFFF)
    cpu = state(m, CYCLE)
    cpu.d[5] = (d5_fraction << 16) | (cpu.d[5] & 65535)
    cpu.a[1], cpu.a[2], cpu.a[6] = OUTPUT, INPUT, INPUT
    return cpu


def span_words(m, p, rows):
    return [get(m, p + 2 * i, 2) for i in range(3 + 2 * rows)]


def line_pairs(m, start_x, end_x, dy, descending_fraction=0x1234):
    step = ((abs(end_x - start_x) * get(m, RECIPROCAL + signed(2 * dy), 2)) * 2) & 0xFFFFFFFF
    acc = (start_x << 16) | (descending_fraction if end_x < start_x else 0)
    result = [(start_x, start_x)]
    for _ in range(dy):
        previous = (acc >> 16) & 65535
        acc = (acc + step if end_x > start_x else acc - step) & 0xFFFFFFFF
        current = acc >> 16
        if end_x > start_x:
            lower = (previous + 1) & 65535
            result.append((lower if current >= lower else previous, current))
        else:
            upper = (previous - 1) & 65535
            result.append((current, upper if upper >= current else previous))
    return result


@pytest.mark.parametrize('dy', [1, 2, 3, 7, 16, 31, 100, 299, 300])
@pytest.mark.parametrize('dx', [1, 3, 10, 64])
@pytest.mark.parametrize('direction', [-1, 1])
@pytest.mark.parametrize('reverse', [False, True])
def test_actual_cycle_to_sloped_line_spans(original_image, memory, dy, dx, direction, reverse):
    start_x, end_x = 100, 100 + direction * dx
    points = [(start_x, 4), (end_x, 4 + dy)]
    cpu = prepare(memory, [points[::-1] if reverse else points])
    expected = line_pairs(memory, start_x, end_x, dy)
    run(original_image, memory, cpu, {HANDOFF})
    assert get(memory, INPUT) == SPANS and get(memory, INPUT + 4) == 0xFFFFFFFF
    assert span_words(memory, SPANS, len(expected)) == [7, 4, *[v for pair in expected for v in pair], 65535]
    assert cpu.a[3] == SPANS + 6 + 4 * len(expected)
    assert cpu.a[2] == INPUT and cpu.a[7] == STACK


def test_shipped_unit_slope_and_first_word_outside_reciprocal_owner(original_image, memory):
    assert get(memory, RECIPROCAL + 2, 2) == 32767
    assert line_pairs(memory, 100, 101, 1) == [(100, 100), (100, 100)]
    assert line_pairs(memory, 100, 99, 1) == [(100, 100), (99, 99)]
    assert get(memory, RECIPROCAL + 598, 2) == 32768 // 299
    assert get(memory, RECIPROCAL + 600, 2) == 0
    cpu = prepare(memory, [[(100, 4), (164, 304)]])
    run(original_image, memory, cpu, {HANDOFF})
    assert span_words(memory, SPANS, 301) == [7, 4, *([100, 100] * 301), 65535]


@pytest.mark.parametrize('fraction', [0, 0x1234, 65535])
def test_descending_line_inherits_d5_high_word_through_the_real_cycle(original_image, memory, fraction):
    cpu = prepare(memory, [[(100, 4), (99, 20)]], d5_fraction=fraction)
    run(original_image, memory, cpu, {0x3DC98})
    assert cpu.d[5] >> 16 == fraction
    expected = line_pairs(memory, 100, 99, 16, fraction)
    run(original_image, memory, cpu, {HANDOFF})
    assert span_words(memory, SPANS, 17) == [7, 4, *[v for pair in expected for v in pair], 65535]


@pytest.mark.parametrize('dy', [16383, 16384, 32768])
def test_doubled_word_index_and_counter_boundary_stop_before_large_span_loop(original_image, memory, dy):
    cpu = prepare(memory, [[(100, 4), (110, 4 + dy)]])
    run(original_image, memory, cpu, {0x3DCD6})
    offset = signed(2 * dy)
    assert signed(cpu.d[3]) == offset
    value = get(memory, cpu.a[4] + offset, 2)
    run(original_image, memory, cpu, {0x3DCE8})
    assert cpu.d[2] == (10 * value * 2) & 0xFFFFFFFF
    assert cpu.d[3] & 65535 == ((dy & 32767) - 1) & 65535
    assert get(memory, SPANS + 4, 2) == get(memory, SPANS + 6, 2) == 100


def polygon_pairs(m, points, reverse_fraction):
    index = max(i for i, (x, y) in enumerate(points) if y == min(p[1] for p in points))
    vertices = points[index:] + points[:index]
    reverse_state = {'fraction': reverse_fraction}

    def edge_chain(sequence, forward, fractional):
        x, y = vertices[0]
        first = True
        for end_x, end_y in sequence:
            dy = signed(end_y - y)
            if dy < 0:
                return
            if dy == 0:
                x, y = end_x, end_y
                continue
            # Initial edges use the NEXT reciprocal entry. Later edges use dy.
            bias = 2 if first else 0
            reciprocal = signed(get(m, RECIPROCAL + signed(2 * dy) + bias, 2))
            step = signed(signed(end_x - x) * reciprocal * 2, 32)
            for _ in range(dy + int(first)):
                total = fractional + step
                x = (x + (total >> 16)) & 65535
                fractional = total & 65535
                if not forward:
                    reverse_state['fraction'] = fractional
                yield x
            x, y = end_x, end_y
            if forward:
                fractional = 0
            first = False

    forward = edge_chain(vertices[1:] + vertices[:1], True, 0)
    reverse = edge_chain(vertices[:0:-1] + vertices[:1], False, reverse_fraction)
    result = list(zip(forward, reverse))
    return result, reverse_state['fraction']


CONTOURS = [
    [(10, 2), (30, 8), (0, 8)],
    [(10, 2), (30, 2), (30, 8), (10, 8)],
    [(10, 2), (30, 5), (40, 10), (0, 10), (5, 6)],
    [(20, 1), (25, 3), (24, 3), (30, 9), (0, 9), (15, 5)],
    [(20, 2), (40, 5), (25, 4), (30, 9), (0, 9)],  # Local descending edge ends this chain early.
    [(20, 2), (100, 300), (0, 300)],
    [(20, 2), (100, 301), (0, 301)],  # Initial dy+1 reads just beyond the 300-WORD owner.
]


@pytest.mark.parametrize('points', CONTOURS)
@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('sentinel', [0x8000, 0xFFFF])
def test_actual_multi_edge_pipeline_preserves_lane_order_and_fraction_seed(original_image, memory, points, reverse, sentinel):
    points = points[::-1] if reverse else points
    cpu = prepare(memory, [points], sentinel)
    pairs, fraction = polygon_pairs(memory, points, sentinel)
    run(original_image, memory, cpu, {HANDOFF})
    expected = [7, min(y for x, y in points), *[v for pair in pairs for v in pair], 65535]
    assert span_words(memory, SPANS, len(pairs)) == expected
    assert cpu.a[3] == SPANS + 2 * len(expected)
    assert cpu.d[2] & 65535 == fraction
    assert cpu.a[2] == INPUT and cpu.a[7] == STACK


def test_reverse_fraction_survives_into_next_polygon_packet(original_image, memory):
    packets = [CONTOURS[2], CONTOURS[0]]
    cpu = prepare(memory, packets)
    fraction, expected = 65535, []
    for points in packets:
        pairs, fraction = polygon_pairs(memory, points, fraction)
        expected.append((points, pairs))
    run(original_image, memory, cpu, {HANDOFF})
    p = SPANS
    for i, (points, pairs) in enumerate(expected):
        words = [7 + i, min(y for x, y in points), *[v for pair in pairs for v in pair], 65535]
        assert get(memory, INPUT + 4 * i) == p
        assert span_words(memory, p, len(pairs)) == words
        p += 2 * len(words)
    assert cpu.a[3] == p and cpu.d[2] & 65535 == fraction


def test_negative_x_terminator_is_not_a_general_fraction_independence_contract(original_image, memory):
    results = []
    for sentinel in [0x8000, 0xFFFF]:
        cpu = prepare(memory, [CONTOURS[0]], sentinel)
        run(original_image, memory, cpu, {HANDOFF})
        results.append(bytes(memory[SPANS:cpu.a[3]]))
    assert results[0] != results[1]
