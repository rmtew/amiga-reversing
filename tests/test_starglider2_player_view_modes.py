"""Original view routing and pre-offset state, not gameplay/caller closure.

Run unchanged image instructions with explicit fixture inputs. External cases
stop at the existing matrix-offset helper; this does not certify that helper's
trigonometry or claim arbitrary pointer inputs are valid player records.
"""
import ctypes
import itertools
import struct

import pytest

from tests.test_starglider2_interleaved_color_kernels import kernels as original_image
from src.tests.test_m68k_simulator_abstract import _diag_has_errors, _diag_message
from tests.test_memory_frame_arithmetic import ConcreteState

BASE, APP, PLAYER, STACK, RETURN = 0x1000, 0x90000, 0x92000, 0x98000, 0xFFFFFF00
ENTRY, TABLE, OFFSET_HELPER = 0x2C40, 0x2C5A, 0x2D34
FIELDS = dict(player_object_reference=0x700, view_mode=0x7EB,
              view_origin_x=0x710, view_origin_y=0x714, view_origin_z=0x718,
              view_rotation_0=0x7B6, view_rotation_1=0x7B8, view_rotation_2=0x7BA,
              view_rotation_offset_0=0x7BC, view_rotation_offset_1=0x7BE,
              view_offset_distance=0x7C0, inside_structure_flag=0x77C,
              space_environment_flag=0x77D, display_and_frame_service_flags=0x20A)


def fixture_state(image, mode, *, inside=False, space=False, special=False, y=300):
    raw, code, step, decode, cache = image
    memory = (ctypes.c_uint8 * 0xA0000)()
    memory[BASE:BASE+len(raw)] = raw
    def put(name, fmt, value):
        pos = APP + FIELDS[name]
        memory[pos:pos+struct.calcsize(fmt)] = struct.pack(fmt, value)
    put('player_object_reference', '>I', PLAYER)
    for name, value in [('view_mode', mode), ('inside_structure_flag', 0xFF if inside else 0),
                        ('space_environment_flag', 0xFF if space else 0),
                        ('display_and_frame_service_flags', 0xA5)]:
        put(name, '>B', value)
    for name, value in [('view_rotation_offset_0', 0x180),
                        ('view_rotation_offset_1', 0x800 if special else 0x900),
                        ('view_offset_distance', 0x345)]:
        put(name, '>H', value)
    memory[PLAYER:PLAYER+0x44] = b'\xA7'*0x44
    memory[PLAYER+2] = 0xBD
    memory[PLAYER+4:PLAYER+16] = struct.pack('>iii', 0x12345678, y, -400)
    memory[PLAYER+16:PLAYER+22] = struct.pack('>HHH', 0xF90, 0x780, 0xD10)
    memory[STACK:STACK+4] = struct.pack('>I', RETURN)
    state = ConcreteState()
    state.pc, state.sr, state.a[6], state.a[7] = BASE+ENTRY, 0x2700, APP, STACK
    state.d[0] = 0xFFFFFFFF  # Original MOVEQ must zero-extend the BYTE selector.
    return memory, state


def run_until(image, memory, state, stops):
    raw, code, step, _, _ = image
    for _ in range(100):
        if state.pc in stops:
            return
        offset = state.pc - BASE
        assert 0 <= offset < len(raw), hex(state.pc)
        ptr = ctypes.cast(ctypes.byref(code, offset), ctypes.POINTER(ctypes.c_uint8))
        outcome = step(ptr, len(raw)-offset, 0, memory, len(memory), ctypes.byref(state))
        assert not _diag_has_errors(outcome.diagnostics), (hex(state.pc), _diag_message(outcome.diagnostics))
    pytest.fail('Original view path failed to reach its handoff')


def test_all_byte_selectors_take_only_the_guarded_eight_slots(original_image):
    raw = original_image[0]
    targets = [BASE+TABLE+struct.unpack_from('>h', raw, TABLE+2*i)[0] for i in range(13)]
    assert len(set(targets[:8])) == 8
    assert targets[8:] == [targets[0]]*5  # Stored extent is not the dispatch domain.
    for mode in range(256):
        memory, state = fixture_state(original_image, mode)
        run_until(original_image, memory, state, set(targets))
        assert state.pc == targets[mode if mode < 8 else 0]
        assert bytes(memory[PLAYER:PLAYER+0x44])[2] == 0xBD  # Stop before mode effects.


@pytest.mark.parametrize('mode', range(9))
def test_view_mode_effects_before_optional_matrix_offset(original_image, mode):
    for inside, space, special, y in itertools.product([False, True], [False, True],
                                                      [False, True], [-121, -120, 300]):
        memory, state = fixture_state(original_image, mode, inside=inside, space=space,
                                      special=special, y=y)
        expected = bytearray(memory[APP:APP+0x1000])
        player = bytearray(memory[PLAYER:PLAYER+0x44])
        external = 4 <= mode <= 7
        offset0, offset1, distance = 0x180, 0x800 if special else 0x900, 0x345
        if external and inside:
            offset0 = 0
            if not special:
                offset1, distance = 0, 800
        rotation0, rotation1, rotation2 = (0xF90+offset0)&4095, (0x780+offset1)&4095, 0xD10
        if mode in [2, 3, 7]:
            rotation0 = 0
        if mode in [1, 3, 5, 6, 7]:
            rotation2 = 0
        for name, value in [('view_rotation_0', rotation0), ('view_rotation_1', rotation1),
                            ('view_rotation_2', rotation2), ('view_rotation_offset_0', offset0),
                            ('view_rotation_offset_1', offset1), ('view_offset_distance', distance)]:
            struct.pack_into('>H', expected, FIELDS[name], value)
        expected[FIELDS['display_and_frame_service_flags']] = 0xA4 if external else 0xA5
        player[2] = 0xBD if external else 0xBF
        # Cockpit clamps here; external paths clamp only after the offset helper.
        struct.pack_into('>iii', expected, FIELDS['view_origin_x'], 0x12345678,
                         y if external or space else min(y, -120), -400)
        run_until(original_image, memory, state, {RETURN, BASE+OFFSET_HELPER})
        assert bytes(memory[APP:APP+0x1000]) == bytes(expected)
        assert bytes(memory[PLAYER:PLAYER+0x44]) == bytes(player)
        assert state.a[6] == APP
        if external:
            assert state.pc == BASE+OFFSET_HELPER and state.a[7] == STACK
            assert state.d[1]&0xFFFF == (0 if mode in [6, 7] else rotation0)
            assert state.d[2]&0xFFFF == rotation1
        else:
            assert state.pc == RETURN and state.a[7] == STACK+4
