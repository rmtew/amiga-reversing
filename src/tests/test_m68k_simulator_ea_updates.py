"""Scalar memory operand updates use generated widths and a single access address."""
from __future__ import annotations

import unittest

from src.tests import test_m68k_simulator_arithmetic as arithmetic

State = arithmetic.State


class ConcreteEAUpdateTests(unittest.TestCase):
    run_one = arithmetic.ConcreteArithmeticTests.run_one

    def check_access(self, text, register, width, mode, before_value, after_value, ccr=None):
        state = State()
        state.d[:] = [0xCAFE0000+i for i in range(8)]
        state.a[:] = [0xABC000+i for i in range(8)]
        delta = 2 if width == 1 and register == 7 else width
        state.a[register] = 32+delta if mode == 'pre' else 32
        state.sr = 0xA71F
        old_a, old_d = list(state.a), list(state.d)
        memory, before, trace = self.run_one(text, state, [(32, before_value.to_bytes(width, 'big'))])
        expected = bytearray(before)
        expected[32:32+width] = after_value.to_bytes(width, 'big')
        old_a[register] = 32+delta if mode == 'post' else 32
        self.assertEqual(list(state.a), old_a)
        self.assertEqual(list(state.d), old_d)
        self.assertEqual(memory, expected)
        self.assertEqual(trace.writes, 1)
        self.assertEqual(trace.range_count, 1)
        self.assertEqual((trace.ranges[0].start, trace.ranges[0].end), (32, 32+width))
        if ccr is not None:
            self.assertEqual(state.sr, 0xA700|ccr)

    def test_clear_all_sizes_registers_and_address_modes(self):
        for suffix, width in [('b', 1), ('w', 2), ('l', 4)]:
            for register in range(8):
                for mode, operand in [('pre', f'-(a{register})'), ('post', f'(a{register})+'), ('ind', f'(a{register})')]:
                    with self.subTest(suffix=suffix, register=register, mode=mode):
                        self.check_access(f'clr.{suffix} {operand}', register, width, mode,
                                          (1 << (width*8))-1, 0, 0x14)

    def test_write_only_condition_all_registers_and_address_modes(self):
        for register in range(8):
            for mode, operand in [('pre', f'-(a{register})'), ('post', f'(a{register})+'), ('ind', f'(a{register})')]:
                with self.subTest(register=register, mode=mode):
                    self.check_access(f'seq {operand}', register, 1, mode, 0x55, 0xFF, 0x1F)

    def test_read_modify_write_updates_once_and_reuses_read_address(self):
        for suffix, width in [('b', 1), ('w', 2), ('l', 4)]:
            for register in [0, 3, 7]:
                for mode, operand in [('pre', f'-(a{register})'), ('post', f'(a{register})+'), ('ind', f'(a{register})')]:
                    with self.subTest(suffix=suffix, register=register, mode=mode):
                        self.check_access(f'not.{suffix} {operand}', register, width, mode, 0, (1 << (width*8))-1, 0x18)

    def test_memory_rmw_siblings(self):
        for register in [0, 7]:
            for mode, operand in [('pre', f'-(a{register})'), ('post', f'(a{register})+'), ('ind', f'(a{register})')]:
                for instruction, width, before, after in [('neg.w', 2, 1, 0xFFFF), ('lsr.w', 2, 2, 1), ('andi.w #1,', 2, 3, 1), ('tas', 1, 1, 0x81)]:
                    text = f'{instruction}{operand}' if instruction.endswith(',') else f'{instruction} {operand}'
                    with self.subTest(text=text, mode=mode):
                        self.check_access(text, register, width, mode, before, after)

    def test_read_only_sources_use_the_same_update_boundary(self):
        for register in [0, 7]:
            for mode, operand in [('pre', f'-(a{register})'), ('post', f'(a{register})+'), ('ind', f'(a{register})')]:
                for instruction, cell, initial, result, ccr in [
                    ('tst.w', 0x8000, 4, 4, 0x18),
                    ('cmp.w', 4, 4, 4, 0x14),
                    ('mulu.w', 3, 4, 12, 0x10),
                    ('and.w', 1, 3, 1, 0x10),
                ]:
                    text = f'{instruction} {operand}'+('' if instruction == 'tst.w' else ',d0')
                    with self.subTest(text=text, mode=mode):
                        state = State()
                        state.a[register] = 34 if mode == 'pre' else 32
                        state.d[0], state.sr = initial, 0xA71F
                        memory, before, trace = self.run_one(text, state, [(32, cell.to_bytes(2, 'big'))])
                        self.assertEqual(state.a[register], 34 if mode == 'post' else 32)
                        self.assertEqual(state.d[0], result)
                        self.assertEqual(state.sr, 0xA700|ccr)
                        self.assertEqual(memory, before)
                        self.assertEqual(trace.writes, 0)

    def test_out_of_range_predecrement_does_not_write_the_old_address(self):
        import ctypes as C
        for suffix in ['b', 'w', 'l']:
            for register in [0, 7]:
                with self.subTest(suffix=suffix, register=register):
                    code = arithmetic.assemble('68000', f'clr.{suffix} -(a{register})')
                    memory = bytearray(code+b'\xA5'*(64-len(code)))
                    before = bytes(memory)
                    state = State()
                    buffer = (C.c_uint8*len(memory)).from_buffer(memory)
                    trace = arithmetic.Trace()
                    rc = arithmetic.engine()(0, buffer, len(memory), C.byref(state), 1, 0, 0, None, C.byref(trace))
                    self.assertEqual(rc, 0)
                    self.assertEqual(trace.stop_reason, 5)  # Simulation error, not a completed instruction.
                    self.assertEqual(trace.steps, 0)
                    self.assertEqual(memory, before)
                    self.assertEqual(trace.writes, 0)
                    self.assertTrue(any(d.severity >= 3 for d in trace.diagnostics.items[:trace.diagnostics.count]))
