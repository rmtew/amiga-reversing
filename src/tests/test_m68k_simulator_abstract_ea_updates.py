"""Abstract scalar accesses preserve order and capture one address per operand."""
from __future__ import annotations

import ctypes as C
import unittest

from src.tests import test_m68k_simulator_abstract as abstract
from src.tests import test_m68k_simulator_arithmetic as arithmetic


class AbstractEAUpdateTests(unittest.TestCase):
    def execute(self, instruction, state, cells=()):
        code = arithmetic.assemble('68000', instruction)
        memory = bytearray(128)
        memory[:len(code)] = code
        for address, data in cells:
            memory[address:address+len(data)] = data
        buffer = (C.c_uint8*len(memory)).from_buffer(memory)
        result = abstract._disasm_library().m68k_simulate_one_abstract_for_cpu(buffer, len(memory), 0, C.byref(state))
        self.assertFalse(abstract._diag_has_errors(result.diagnostics), abstract._diag_message(result.diagnostics))
        return result.step

    def test_clear_sizes_registers_and_modes(self):
        for suffix, width in [('b', 1), ('w', 2), ('l', 4)]:
            for reg in range(8):
                for mode, operand in [('pre', f'-(a{reg})'), ('post', f'(a{reg})+'), ('ind', f'(a{reg})')]:
                    with self.subTest(suffix=suffix, reg=reg, mode=mode):
                        delta = 2 if width == 1 and reg == 7 else width
                        state = abstract.M68kSimCpuState()
                        state.sr, state.sr_known = 0xA71F, 1
                        state.a[reg] = abstract._section_ptr(64+delta if mode == 'pre' else 64)
                        step = self.execute(f'clr.{suffix} {operand}', state)
                        self.assertEqual(step.next_state.a[reg].kind, 2)
                        self.assertEqual(step.next_state.a[reg].value, 64+delta if mode == 'post' else 64)
                        self.assertEqual(step.next_state.sr, 0xA714)
                        self.assertEqual(step.memory_write_count, 1)
                        cell = step.memory_writes[0]
                        self.assertEqual((cell.offset, cell.width, cell.value.kind, cell.value.value), (64, width, 1, 0))

    def test_rmw_and_condition_store_update_only_once(self):
        for instruction, width, initial, expected in [('not.b', 1, 1, 254), ('not.w', 2, 1, 65534),
                ('not.l', 4, 256, 0xFFFFFEFF), ('seq', 1, 1, 255), ('tas', 1, 1, 129)]:
            for reg in [0, 7]:
                for mode, operand in [('pre', f'-(a{reg})'), ('post', f'(a{reg})+')]:
                    with self.subTest(instruction=instruction, reg=reg, mode=mode):
                        delta = 2 if width == 1 and reg == 7 else width
                        state = abstract.M68kSimCpuState()
                        state.sr, state.sr_known = 0xA71F, 1
                        state.a[reg] = abstract._section_ptr(64+delta if mode == 'pre' else 64)
                        step = self.execute(f'{instruction} {operand}', state, [(64, initial.to_bytes(width, 'big'))])
                        self.assertEqual(step.next_state.a[reg].value, 64+delta if mode == 'post' else 64)
                        self.assertEqual(step.memory_write_count, 1)
                        cell = step.memory_writes[0]
                        self.assertEqual((cell.offset, cell.width, cell.value.value), (64, width, expected))

    def test_shared_register_memory_operands_are_sequential(self):
        for suffix, width in [('b', 1), ('w', 2), ('l', 4)]:
            for reg in [0, 7]:
                delta = 2 if width == 1 and reg == 7 else width
                with self.subTest(op='cmpm', suffix=suffix, reg=reg):
                    state = abstract.M68kSimCpuState()
                    state.sr, state.sr_known = 0xA710, 1
                    state.a[reg] = abstract._section_ptr(64)
                    # Long values exceed this section and remain scalar constants.
                    unit = 0x10000 if width == 4 else 1
                    step = self.execute(f'cmpm.{suffix} (a{reg})+,(a{reg})+', state,
                        [(64, unit.to_bytes(width, 'big')), (64+delta, (2*unit).to_bytes(width, 'big'))])
                    self.assertEqual(step.next_state.a[reg].value, 64+2*delta)
                    self.assertEqual(step.next_state.sr_known, 0)  # Mutable loads cannot prove branch flags.
                    self.assertEqual([step.accesses[i].offset for i in range(step.access_count)], [64, 64+delta])
                    self.assertEqual(step.memory_write_count, 0)
                for op, expected in [('addx', 4), ('subx', 2)]:
                    with self.subTest(op=op, suffix=suffix, reg=reg):
                        state = abstract.M68kSimCpuState()
                        state.sr, state.sr_known = 0xA704, 1
                        state.a[reg] = abstract._section_ptr(64+2*delta)
                        step = self.execute(f'{op}.{suffix} -(a{reg}),-(a{reg})', state,
                            [(64, (3*unit).to_bytes(width, 'big')), (64+delta, unit.to_bytes(width, 'big'))])
                        self.assertEqual(step.next_state.a[reg].value, 64)
                        self.assertEqual(step.memory_write_count, 1)
                        self.assertEqual((step.memory_writes[0].offset, step.memory_writes[0].value.value), (64, expected*unit))

    def test_move_source_update_and_pointer_identity(self):
        state = abstract.M68kSimCpuState()
        state.a[0] = abstract._section_ptr(64)
        step = self.execute('move.l (a0)+,(a0)+', state, [(64, (96).to_bytes(4, 'big'))])
        self.assertEqual(step.next_state.a[0].value, 72)
        self.assertEqual((step.memory_writes[0].offset, step.memory_writes[0].value.kind, step.memory_writes[0].value.value), (68, 2, 96))
        state.a[0] = abstract._section_ptr(64)
        step = self.execute('movea.l (a0)+,a0', state, [(64, (96).to_bytes(4, 'big'))])
        self.assertEqual((step.next_state.a[0].kind, step.next_state.a[0].value), (2, 96))

    def test_unknown_and_wrapped_addresses_do_not_create_memory_facts(self):
        for address in [None, 0]:
            with self.subTest(address=address):
                state = abstract.M68kSimCpuState()
                if address is not None:
                    state.a[7] = abstract._section_ptr(address)
                step = self.execute('clr.w -(a7)', state)
                self.assertEqual(step.memory_write_count, 0)
                self.assertEqual(step.next_state.a[7].kind, 0 if address is None else 2)
                if address is not None:
                    self.assertEqual(step.next_state.a[7].value, 0xFFFFFFFE)
