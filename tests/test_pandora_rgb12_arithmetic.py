"""Original RGB12 WORD arithmetic, including unchecked wrap and packing."""
import pytest

from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_render_order import sequencer
from tests.test_pandora_title_data import title_slots


def packed_accumulators(values):
    red, green, blue = (v >> 4 for v in values)
    return ((red << 8) & 0xFF00) | ((blue & 255) | ((green << 4) & 255))


def test_component_add_subtract_wrap_and_preserve_inputs_even_for_non_rgb12_values(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    record = 0x80000
    vectors = [(0, 0, 0), (15, 16, 31), (255, 4095, 65535),
               (0xFFF0, 0xFFF1, 0xFFF2), (0x1234, 0xABCD, 0x80F0)]
    for source, sign in [(0x255E, 1), (0x259E, -1)]:
        for initial in vectors:
            for delta in [0, 0xFFF, 0x123, 0xF00, 0x0F0, 0x00F, 0xFFFF, 0xFEDC]:
                expected = [(v+sign*((delta >> shift) & 15)) & 65535
                            for v, shift in zip(initial, (8, 4, 0))]
                for ignored in (0, 0x12345678):
                    memory[record-2:record+8] = bytes([0xC7])*10
                    for i, value in enumerate(initial): write(record+2*i, value, 2)
                    for i in range(8): cpu.d[i] = 0xABCD0000+i
                    cpu.d[0], cpu.d[1], cpu.a[2] = ignored, 0xCAFE0000|delta, record
                    saved = list(cpu.d)[1:]
                    run(source)
                    assert [read(record+2*i, 2) for i in range(3)] == expected
                    assert cpu.d[0] == packed_accumulators(expected)
                    assert list(cpu.d)[1:] == saved and cpu.a[2] == record
                    assert memory[record-2:record] == bytes([0xC7])*2
                    assert memory[record+6:record+8] == bytes([0xC7])*2


def test_unpack_all_4096_rgb12_colors_keeps_source_upper_bits_only_in_palette(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    source, palette, components = 0x68000, 0x70000, 0x74000
    colors = [i | (0xF000 if i & 1 else 0) for i in range(4096)]
    original = b''.join(c.to_bytes(2, 'big') for c in colors)
    memory[source:source+len(original)] = original
    memory[palette-2:palette+len(original)+2] = bytes([0xC7])*(len(original)+4)
    memory[components-2:components+4096*6+2] = bytes([0xC7])*(4096*6+4)
    cpu.a[0], cpu.a[1], cpu.a[2], cpu.d[7] = palette, source, components, 4095
    cpu.d[2] = 0x12345678
    advance = sequencer(cpu, memory, write)
    assert advance(0x2614, budget=100000).stop_reason == 1
    assert memory[palette:palette+len(original)] == original
    assert memory[source:source+len(original)] == original
    assert [read(components+6*i+2*j, 2) for i in range(4096) for j in range(3)] == [
        ((c >> shift) & 15) << 4 for c in colors for shift in (8, 4, 0)]
    assert (cpu.a[0], cpu.a[1], cpu.a[2], cpu.d[7], cpu.d[2]) == (palette, source, components, 4095, 0x12345678)
    for start, size in [(palette, len(original)), (components, 4096*6)]:
        assert memory[start-2:start] == bytes([0xC7])*2
        assert memory[start+size:start+size+2] == bytes([0xC7])*2


def test_palette_add_subtract_counted_spans_and_full_loop_register_preservation(cpu_fixture):
    cpu, memory, schemas, read, write, run = cpu_fixture
    palette, increments, components = 0x80000, 0x81000, 0x82000
    for count in (1, 3, 16):
        for source, sign in [(0x25DE, 1), (0x25FA, -1)]:
            memory[palette-2:palette+2*count+2] = bytes([0xC7])*(2*count+4)
            memory[components-2:components+6*count+2] = bytes([0xC7])*(6*count+4)
            expected = []
            for i in range(count):
                delta = (0xFEDC+i*0x137) & 65535
                write(increments+2*i, delta, 2)
                initial = [(i*0x1234+j*0x7FF) & 65535 for j in range(3)]
                values = [(v+sign*((delta >> shift) & 15)) & 65535
                          for v, shift in zip(initial, (8, 4, 0))]
                expected.append(values)
                for j, value in enumerate(initial): write(components+6*i+2*j, value, 2)
            cpu.a[0], cpu.a[1], cpu.a[2], cpu.d[7] = palette, increments, components, count-1
            for i in range(7): cpu.d[i] = 0x12340000+i
            before_d, before_a = list(cpu.d), list(cpu.a)[:7]
            run(source, budget=2048)
            assert list(cpu.d) == before_d and list(cpu.a)[:7] == before_a
            assert [read(palette+2*i, 2) for i in range(count)] == list(map(packed_accumulators, expected))
            assert [read(components+6*i+2*j, 2) for i in range(count) for j in range(3)] == [v for values in expected for v in values]
            for start, size in [(palette, 2*count), (components, 6*count)]:
                assert memory[start-2:start] == bytes([0xC7])*2
                assert memory[start+size:start+size+2] == bytes([0xC7])*2


def test_gameplay_fade_count_gate_updates_17_steps_and_latches_health_once(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    app = 0x39FC
    remaining = app+title_slots['app_palette_transition_steps_remaining']
    events = app+title_slots['app_game_event_flags']
    cpu.a[6] = app
    increments = [read(0x10000+0x34E2+2*i, 2) for i in range(16)]
    for value in range(256):
        memory[0x10000+0x3462:0x10000+0x34E2] = bytes(128)
        write(remaining, value, 1)
        write(events, 4, 1)  # Existing latch prevents the health renderer call.
        run(0x7DA6, budget=2048)
        expected_remaining = max(value-1, 0)
        active = 1 <= value <= 17
        assert read(remaining, 1) == expected_remaining
        assert [read(0x10000+0x3462+6*i+2*j, 2) for i in range(16) for j in range(3)] == [
            ((color >> shift) & 15) if active else 0
            for color in increments for shift in (8, 4, 0)]
        assert read(events, 1) == 4
    memory[0x10000+0x3462:0x10000+0x34E2] = bytes(128)
    write(remaining, 25, 1)
    for _ in range(25): run(0x7DA6, budget=2048)
    assert read(remaining, 1) == 0
    assert [read(0x10000+0x3462+6*i+2*j, 2) for i in range(16) for j in range(3)] == [
        17*((color >> shift) & 15) for color in increments for shift in (8, 4, 0)]
    write(remaining, 2, 1); write(events, 0x80, 1)
    run(0x7DA6, stop=0x7DCC)
    assert read(remaining, 1) == 1 and read(events, 1) == 0x84


@pytest.mark.parametrize('cpu_fixture', [0x1000000], indirect=True)
def test_initial_palette_writer_and_color_two_restart_consumer(cpu_fixture, title_slots):
    cpu, memory, schemas, read, write, run = cpu_fixture
    colors = bytes(memory[BASE+0x76E:BASE+0x78E])
    assert len(colors) == 32 and all(read(BASE+0x76E+2*i, 2) < 4096 for i in range(16))
    cpu.a[6] = 0x39FC
    write(0x39FC+title_slots['app_current_palette'], BASE+0x76E)
    memory[0xDFF17E:0xDFF1A2] = bytes([0xC7])*36
    before_d = list(cpu.d)
    run(0x752)
    assert memory[0xDFF180:0xDFF1A0] == colors
    assert memory[0xDFF17E:0xDFF180] == bytes([0xC7])*2
    assert memory[0xDFF1A0:0xDFF1A2] == bytes([0xC7])*2
    assert (cpu.a[0], cpu.a[1], list(cpu.d)) == (BASE+0x78E, 0xDFF1A0, before_d)
    write(BASE+0x772, 0x123, 2)
    run(0x9F50, stop=0x9F58)
    assert memory[BASE+0x76E:BASE+0x78E] == colors
