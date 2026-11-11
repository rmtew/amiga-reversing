"""Original post-game planar smear with supplied profile tables and RAM.

The mask producers execute original instructions. Alternate X/row maps are
explicit inputs, not a full startup/mode-switch or visible-frame qualification.
No instruction bytes, helper returns or guest CPU state are patched mid-run.
"""
import ctypes
import struct
import subprocess
from pathlib import Path

import pytest

from tests.test_starglider2_text_editor import original_image, memory, state, run, put, get, APP, FB, STACK, RETURN
from tests.test_starglider2_planar_span_reader import initialized, ROWS, MASK32, MASK16
from tests.test_starglider2_palette_priority import rng

ENTRY, CHOOSE, KERNEL, FINISH = 0x365C, 0x367E, 0x373A, 0x38A0
XOFFSETS = 0x16760
PROFILES = {'amiga': (40, 8192, 0), 'mode0': (160, 2, 0), 'mode1': (160, 2, 76)}


@pytest.fixture(scope='module')
def layout_symbols(tmp_path_factory, original_image):
    target = Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    names = ['screen_x_word_byte_offsets', 'raster_row_byte_offsets', 'alternate_graphics_mode',
             'vblank_tick_counter', 'pending_key_scancode', 'mouse_secondary_button_flag',
             'smear_random_planar_screen_regions', 'choose_next_random_smear_region',
             'snapshot_smear_source_and_destination_rows', 'copy_smear_words_with_complementary_plane_masks',
             'shift_smear_words_left_one_bit', 'shift_smear_words_right_one_bit',
             'SG2_SMEAR_REGION_DBF_LAST', 'SG2_POSTGAME_SMEAR_FRAME_DBF_LAST']
    folder = tmp_path_factory.mktemp('smear-symbols'); source, output = folder/'map.s', folder/'map.raw'
    source.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(names)+'\n')
    r = subprocess.run([str(target.parents[1]/'tools/vasmm68k_mot.exe'), '-quiet', '-Fbin', '-m68000',
        '-no-opt', '-I'+str(target/'includes'), '-o', str(output), str(source)], cwd=target, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout+r.stderr
    raw = output.read_bytes(); assert raw[:-4*len(names)] == original_image[0]
    symbols = dict(zip(names, struct.unpack('>'+'I'*len(names), raw[-4*len(names):])))
    assert symbols['screen_x_word_byte_offsets'] == XOFFSETS and symbols['raster_row_byte_offsets'] == ROWS
    assert symbols['alternate_graphics_mode'] == 0x1F2
    assert {k: symbols[k] for k in names[6:]} == dict(zip(names[6:],
        [ENTRY, CHOOSE, KERNEL, 0x3742, 0x37AE, 0x3828, 256, 750]))
    return symbols


def inside(left, right):
    lo, hi = sorted((left, right))
    return ((1 << (hi-lo+1))-1) << (15-hi)


@pytest.fixture(scope='module')
def layouts(original_image, initialized, layout_symbols):
    result = {}
    for mode, (row, _, _) in PROFILES.items():
        m = (ctypes.c_uint8 * len(initialized)).from_buffer_copy(initialized)
        put(m, 0x1002, 0x8000 if mode == 'amiga' else 0, 2)
        m[APP+0x1F2] = 255 if mode == 'mode1' else 0
        if mode != 'amiga':
            cpu = state(m, 0x3E96E)
            run(original_image, m, cpu, {RETURN}, limit=50000)
        for y in range(200):
            put(m, ROWS+2*y, row*y, 2)
        for x in range(320):
            offset = (x//16)*2 if mode == 'amiga' else (x//16)*8 if mode == 'mode0' else (x//8)*2
            put(m, XOFFSETS+2*x, offset, 2)
        for a in range(16):
            for b in range(16):
                mask = inside(a, b)
                if mode == 'amiga':
                    assert get(m, MASK16+2*(16*a+b), 2) == mask ^ 65535
                else:
                    assert get(m, MASK32+4*(16*a+b)) == mask * 0x10001
        m[FB:FB+0x8000] = bytes(((i*73+(i>>5)) ^ 0xA7) & 255 for i in range(0x8000))
        result[mode] = bytes(m)
    return result


def smear(expected, source, destination, height, mask, variant, mode):
    row, plane, gap = PROFILES[mode]
    # The snapshots remain fixed: after the first row, each further iteration
    # revisits the preceding row rather than walking through height+1 rows.
    for repeat in range(height+1):
        s = source if repeat == 0 else source-row
        d = destination if repeat == 0 else destination-row
        for number, offset in enumerate((0, plane, 2*plane+gap, 3*plane+gap)):
            source_word = int.from_bytes(expected[s+offset:s+offset+2], 'big')
            old = int.from_bytes(expected[d+offset:d+offset+2], 'big')
            if variant == 'copy':
                selection = mask ^ (65535 if number & 1 else 0)
                bits, destination_mask = source_word & selection, selection
            elif variant == 'left':
                bits, destination_mask = ((source_word & mask) << 1) & 65535, (mask << 1) & 65535
            else:
                bits, destination_mask = (source_word & mask) >> 1, mask >> 1
            word = bits | (old & (destination_mask ^ 65535))
            expected[d+offset:d+offset+2] = word.to_bytes(2, 'big')


@pytest.mark.parametrize('mode', PROFILES)
@pytest.mark.parametrize('variant', ['copy', 'left', 'right'])
@pytest.mark.parametrize('height', range(4))
@pytest.mark.parametrize('mask', [0, 0x8000, 0x3C1F])
def test_original_kernel_masks_shift_edges_aliasing_and_repeated_row(original_image, memory, layouts, mode, variant, height, mask):
    ctypes.memmove(ctypes.addressof(memory), layouts[mode], len(memory))
    row, plane, _ = PROFILES[mode]
    source = FB+20*row+8
    destination = source+height*row
    cpu = state(memory, KERNEL)
    cpu.a[0], cpu.a[1], cpu.a[2] = row, source, destination
    cpu.d[2], cpu.d[3], cpu.d[4] = 0xABCD0000+height, plane, 0xBEEF0000+mask
    cpu.d[5] = {'copy': 0x8000, 'left': 0, 'right': 0x4000}[variant]
    expected = bytearray(memory)
    smear(expected, source, destination, height, mask, variant, mode)
    run(original_image, memory, cpu, {FINISH})
    assert bytes(memory) == expected
    assert cpu.d[2] == 0xABCDFFFF
    assert (cpu.a[1], cpu.a[2]) == (source-row, destination-row)
    assert (cpu.a[3], cpu.a[4]) == (source, destination)
    assert cpu.a[7] == STACK


@pytest.mark.parametrize('mode', PROFILES)
@pytest.mark.parametrize('seed', [(0, 0), (0x12345678, 0x90ABCDEF)])
def test_original_full_effect_257_regions_four_rng_advances_and_ram_boundary(original_image, memory, layouts, mode, seed):
    ctypes.memmove(ctypes.addressof(memory), layouts[mode], len(memory))
    put(memory, APP+0x60, seed[0]); put(memory, APP+0x64, seed[1])
    cpu = state(memory, ENTRY)
    expected = bytearray(memory)
    a, b = seed
    predicted = []
    for _ in range(257):
        a, b = rng(a, b); height = b & 3
        a, b = rng(a, b); y = (b & 65535) % 196
        a, b = rng(a, b); x = ((b & 65535) % 320) & 0xFFF0
        a, b = rng(a, b); selector = b & 65535
        index = (selector & (510 if mode == 'amiga' else 1022)) // (2 if mode == 'amiga' else 4)
        mask = inside(index//16, index % 16)
        row, plane, _ = PROFILES[mode]
        xoff = (x//16)*2 if mode == 'amiga' else (x//16)*8 if mode == 'mode0' else (x//8)*2
        source = FB+(y+height)*row+xoff
        destination = source+height*row
        variant = 'copy' if selector & 32768 else 'right' if selector & 16384 else 'left'
        predicted.append((height, source, destination, mask, selector, plane, row))
        smear(expected, source, destination, height, mask, variant, mode)
    expected[APP+0x60:APP+0x68] = a.to_bytes(4, 'big')+b.to_bytes(4, 'big')
    expected[STACK-6:STACK] = FB.to_bytes(4, 'big')+b'\0\0'
    observed, counters = [], []
    def observe(pc):
        if pc == CHOOSE:
            counters.append(cpu.d[0] & 65535)
        if pc == KERNEL:
            observed.append((cpu.d[2] & 65535, cpu.a[1], cpu.a[2], cpu.d[4] & 65535,
                             cpu.d[5] & 65535, cpu.d[3] & 65535, cpu.a[0]))
    run(original_image, memory, cpu, {RETURN}, observe, limit=200000)
    assert counters == list(range(256, -1, -1))
    assert observed == predicted
    assert bytes(memory) == expected
    assert (cpu.d[6], cpu.d[7]) == (a, b)
    assert cpu.a[0] == FB and cpu.a[7] == STACK+4


@pytest.mark.parametrize('mode', PROFILES)
def test_original_region_can_target_row201_with_supplied_seed(original_image, memory, layouts, mode):
    ctypes.memmove(ctypes.addressof(memory), layouts[mode], len(memory))
    # A supplied local-loop entry state, not proof of normal-game seed reachability.
    a, b = 0x32, 0x60000002
    put(memory, APP+0x60, a); put(memory, APP+0x64, b)
    cpu = state(memory, CHOOSE)
    cpu.a[0], cpu.d[0], cpu.d[6], cpu.d[7] = FB, 0, a, b
    for _ in range(4): a, b = rng(a, b)
    selector = b & 65535
    index = (selector & (510 if mode == 'amiga' else 1022)) // (2 if mode == 'amiga' else 4)
    mask = inside(index//16, index % 16)
    row, _, _ = PROFILES[mode]
    xoff = 2 if mode == 'amiga' else 8 if mode == 'mode0' else 4
    source, destination = FB+198*row+xoff, FB+201*row+xoff
    expected = bytearray(memory)
    smear(expected, source, destination, 3, mask, 'left', mode)
    expected[APP+0x60:APP+0x68] = a.to_bytes(4, 'big')+b.to_bytes(4, 'big')
    expected[STACK-6:STACK] = FB.to_bytes(4, 'big')+b'\0\0'
    regions = []
    def observe(pc):
        if pc == KERNEL:
            regions.append((cpu.d[2] & 65535, cpu.a[1], cpu.a[2], cpu.d[5] & 65535))
    run(original_image, memory, cpu, {RETURN}, observe)
    assert regions == [(3, source, destination, selector)]
    assert bytes(memory) == expected and cpu.a[7] == STACK+4


@pytest.mark.parametrize('counter', [0, 750])
@pytest.mark.parametrize('tick', [0, 65535])
@pytest.mark.parametrize('skip', ['none', 'key', 'secondary_mouse'])
def test_caller_continuation_restores_word_counter_and_polls_exact_tick(original_image, memory, layouts, layout_symbols, counter, tick, skip):
    ctypes.memmove(ctypes.addressof(memory), layouts['amiga'], len(memory))
    f = layout_symbols
    put(memory, APP+f['vblank_tick_counter'], tick, 2)
    memory[APP+f['pending_key_scancode']] = int(skip == 'key')
    memory[APP+f['mouse_secondary_button_flag']] = int(skip == 'secondary_mouse')
    # Enter immediately after the effect's return, with its saved WORD counter.
    cpu = state(memory, 0x153A); cpu.a[7] = STACK-2
    cpu.d[1] = 0xBEEF1234; put(memory, STACK-2, counter, 2)
    run(original_image, memory, cpu, {0x1542})
    assert cpu.d[1] == 0xBEEF0000+counter and cpu.a[7] == STACK
    assert cpu.d[0] & 65535 == (tick+1) & 65535
    # A supplied RAM tick stimulus, not proof of physical IRQ cadence/delivery.
    put(memory, APP+f['vblank_tick_counter'], (tick+1) & 65535, 2)
    run(original_image, memory, cpu, {0x1534, 0x16B0})
    assert cpu.pc == (0x1534 if skip == 'none' and counter else 0x16B0)
    assert cpu.d[1] == 0xBEEF0000+(counter if skip != 'none' else (counter-1) & 65535)


def test_one_original_caller_iteration_executes_effect_then_exits_on_word_count(original_image, memory, layouts, layout_symbols):
    ctypes.memmove(ctypes.addressof(memory), layouts['amiga'], len(memory))
    f = layout_symbols
    memory[APP+f['pending_key_scancode']] = memory[APP+f['mouse_secondary_button_flag']] = 0
    put(memory, APP+f['vblank_tick_counter'], 65535, 2)
    put(memory, APP+0x60, 0); put(memory, APP+0x64, 0)
    cpu = state(memory, 0x1534); cpu.d[1] = 0
    calls = []
    def tick(pc):
        if pc == ENTRY: calls.append(pc)
        if pc == 0x1542: put(memory, APP+f['vblank_tick_counter'], 0, 2)
    run(original_image, memory, cpu, {0x16B0}, tick, limit=200000)
    a, b = 0, 0
    for _ in range(1028): a, b = rng(a, b)
    assert calls == [ENTRY] and cpu.d[1] & 65535 == 65535 and cpu.a[7] == STACK
    assert (get(memory, APP+0x60), get(memory, APP+0x64)) == (a, b)
