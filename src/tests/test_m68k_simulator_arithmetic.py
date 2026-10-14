"""Concrete arithmetic regressions using generated assembly and explicit vectors."""
from __future__ import annotations

import ctypes as C
from functools import lru_cache
from pathlib import Path
import unittest

from src.tests._build_helpers import prepare_test_dll
from src.tests.test_m68k_simulator_abstract import M68kDiagList, _assemble_line_hex

ROOT = Path(__file__).resolve().parents[2]


class State(C.Structure):
    _fields_ = [("d", C.c_uint32 * 8), ("a", C.c_uint32 * 8), ("c", C.c_uint32 * 32),
                ("pc", C.c_uint32), ("sr", C.c_uint16)]


class WriteRange(C.Structure):
    _fields_ = [("start", C.c_uint32), ("end", C.c_uint32)]


class Trace(C.Structure):
    _fields_ = [("steps", C.c_size_t), ("start_pc", C.c_uint32), ("stop_pc", C.c_uint32),
                ("write_start", C.c_uint32), ("write_end", C.c_uint32), ("writes", C.c_size_t),
                ("range_count", C.c_size_t), ("overflow", C.c_uint8), ("reserved", C.c_uint8 * 7),
                ("ranges", WriteRange * 32), ("stop_reason", C.c_int), ("diagnostics", M68kDiagList)]


@lru_cache(maxsize=1)
def engine():
    lib = C.CDLL(str(prepare_test_dll(ROOT / "src/build/m68k_disassembler_lib.dll")))
    run = lib.m68k_simulate_run_concrete
    run.argtypes = [C.c_uint8, C.POINTER(C.c_uint8), C.c_size_t, C.POINTER(State), C.c_size_t,
                    C.c_uint32, C.c_uint32, C.c_void_p, C.POINTER(Trace)]
    run.restype = C.c_int
    return run


assemble = lru_cache(maxsize=None)(_assemble_line_hex)


class ConcreteArithmeticTests(unittest.TestCase):
    def run_one(self, text, state, cells=(), *, memory_size=64):
        code = assemble("68000", text)
        memory = bytearray(b"\xa5" * memory_size)
        memory[:len(code)] = code
        for offset, data in cells:
            memory[offset:offset + len(data)] = data
        before = bytes(memory)
        buf = (C.c_uint8 * len(memory)).from_buffer(memory)
        trace = Trace()
        self.assertEqual(engine()(0, buf, len(memory), C.byref(state), 1, 0, 0, None, C.byref(trace)), 0)
        messages = [bytes(d.message).split(b"\0")[0].decode() for d in trace.diagnostics.items[:trace.diagnostics.count]]
        self.assertFalse(any(d.severity >= 3 for d in trace.diagnostics.items[:trace.diagnostics.count]), messages)
        self.assertEqual(trace.steps, 1)
        self.assertEqual(state.pc, len(code))
        return memory, before, trace

    def test_minimal_subi_word_regression(self):
        state = State()
        state.d[0] = 0x00070328
        state.sr = 0x2000
        memory, before, trace = self.run_one("subi.w #840,d0", state)
        self.assertEqual(memory[:4], bytes.fromhex("04400348"))
        self.assertEqual(state.d[0], 0x0007FFE0)
        self.assertEqual(state.sr, 0x2019)
        self.assertEqual(memory, before)
        self.assertEqual(trace.writes, 0)

    def test_data_boundaries_flags_widths_and_neighbours(self):
        for suffix, width in (("b", 1), ("w", 2), ("l", 4)):
            mask = (1 << (width * 8)) - 1
            sign = (mask + 1) >> 1
            add = [(0, 0, 0, 4), (mask, 1, 0, 0x15), (sign-1, 1, sign, 0x0A),
                   (sign, sign, 0, 0x17), (sign, 0, sign, 8), (1, 1, 2, 0),
                   (mask, mask, mask-1, 0x19), (sign, mask, sign-1, 0x13)]
            sub = [(0, 0, 0, 4), (0, 1, mask, 0x19), (sign-1, mask, sign, 0x1B),
                   (sign, 1, sign-1, 2), (sign, sign, 0, 4), (mask, mask, 0, 4),
                   (mask, 1, mask-1, 8), (1, mask, 2, 0x11)]
            for op, vectors in (("add", add), ("sub", sub)):
                for lhs, rhs, output, ccr in vectors:
                    forms = [(f"{op}i.{suffix} #${rhs:X},d0", None, None),
                             (f"{op}.{suffix} d1,d0", None, None),
                             (f"{op}i.{suffix} #${rhs:X},(a0)", "write", None),
                             (f"{op}.{suffix} d1,(a0)", "write", None),
                             (f"{op}.{suffix} (a0),d0", "read", None),
                             (f"{op}.{suffix} (a0)+,d0", "read", "post"),
                             (f"{op}.{suffix} -(a0),d0", "read", "pre"),
                             (f"{op}i.{suffix} #${rhs:X},(a0)+", "write", "post"),
                             (f"{op}i.{suffix} #${rhs:X},-(a0)", "write", "pre")]
                    for text, access, update in forms:
                        for old_ccr in (0, 31):
                            with self.subTest(text=text, lhs=lhs, rhs=rhs, old_ccr=old_ccr):
                                state = State()
                                state.d[:] = [0xC0FFEE00 + i for i in range(8)]
                                state.a[:] = [0xABC000 + i for i in range(8)]
                                state.d[0] = (0xA57E9300 & ~mask) | lhs
                                state.d[1] = (0xCAFE9600 & ~mask) | rhs
                                state.a[0] = 32 + (width if update == "pre" else 0)
                                state.sr = 0xA700 | old_ccr
                                old_d, old_a = list(state.d), list(state.a)
                                cells = [] if access is None else [(32, (lhs if access == "write" else rhs).to_bytes(width, "big"))]
                                memory, before, trace = self.run_one(text, state, cells)
                                expected_memory = bytearray(before)
                                if access == "write":
                                    expected_memory[32:32+width] = output.to_bytes(width, "big")
                                else:
                                    old_d[0] = (old_d[0] & ~mask) | output
                                old_a[0] = 32 + (width if update == "post" else 0)
                                self.assertEqual(list(state.d), old_d)
                                self.assertEqual(list(state.a), old_a)
                                self.assertEqual(state.sr, 0xA700 | ccr)
                                self.assertEqual(memory, expected_memory)
                                self.assertEqual(trace.writes, int(access == "write"))
                                if trace.writes:
                                    self.assertEqual(trace.range_count, 1)
                                    self.assertEqual((trace.ranges[0].start, trace.ranges[0].end), (32, 32+width))

    def test_quick_data_and_address_destinations(self):
        for op in ("add", "sub"):
            for suffix, width in (("b", 1), ("w", 2), ("l", 4)):
                mask = (1 << (width * 8)) - 1
                for amount in (1, 8):
                    for dest in ("d0", "(a0)", "a1"):
                        if dest == "a1" and width == 1:
                            continue
                        with self.subTest(op=op, suffix=suffix, amount=amount, dest=dest):
                            state = State()
                            state.sr = 0xA71F
                            state.d[0] = (0xCAFE0000 & ~mask) | (mask if op == "add" else 0)
                            state.a[0] = 32
                            state.a[1] = 0xFFFF if op == "add" else 0x10000
                            lhs = mask if op == "add" else 0
                            cells = [(32, lhs.to_bytes(width, "big"))] if dest == "(a0)" else []
                            old_d0 = state.d[0]
                            memory, before, trace = self.run_one(f"{op}q.{suffix} #{amount},{dest}", state, cells)
                            expected = bytearray(before)
                            if dest == "a1":
                                self.assertEqual(state.a[1], 0xFFFF+amount if op == "add" else 0x10000-amount)
                                self.assertEqual(state.sr, 0xA71F)
                                self.assertEqual(state.d[0], old_d0)
                            else:
                                value = amount-1 if op == "add" else (mask+1-amount)
                                if dest == "d0":
                                    self.assertEqual(state.d[0], (old_d0 & ~mask) | value)
                                else:
                                    expected[32:32+width] = value.to_bytes(width, "big")
                                self.assertEqual(state.sr, 0xA700 | (0x15 if op == "add" and amount == 1 else 0x11 if op == "add" else 0x19))
                            self.assertEqual(memory, expected)
                            self.assertEqual(trace.writes, int(dest == "(a0)"))

    def test_address_arithmetic_source_extension_and_preserved_sr(self):
        for op in ("add", "sub"):
            for suffix, width in (("w", 2), ("l", 4)):
                for source in (0x7FFF, 0x8000, 0xFFFF, 0xFFFF8000):
                    raw = source & ((1 << (width * 8)) - 1)
                    scalar = raw - (1 << (width * 8)) if raw & (1 << (width * 8 - 1)) else raw
                    for operand in (f"#${raw:X}", "d1", "(a0)+", "-(a0)"):
                        with self.subTest(op=op, suffix=suffix, source=source, operand=operand):
                            state = State()
                            state.d[1] = source
                            state.a[0] = 32 + (width if operand == "-(a0)" else 0)
                            state.a[1] = 0x12340000
                            state.sr = 0xA71F
                            memory, before, trace = self.run_one(f"{op}a.{suffix} {operand},a1", state, [(32, raw.to_bytes(width, "big"))])
                            self.assertEqual(state.a[1], (0x12340000 + (scalar if op == "add" else -scalar)) & 0xFFFFFFFF)
                            self.assertEqual(state.a[0], 32 + (width if operand == "(a0)+" else 0))
                            self.assertEqual(state.sr, 0xA71F)
                            self.assertEqual(state.d[1], source)
                            self.assertEqual(memory, before)
                            self.assertEqual(trace.writes, 0)

    def test_address_wrap_preserves_sr(self):
        cases = [("adda.w #$FFFF,a1", 0, 0xFFFFFFFF),
                 ("suba.w #$FFFF,a1", 0xFFFFFFFF, 0),
                 ("addq.w #1,a1", 0xFFFFFFFF, 0),
                 ("subq.w #8,a1", 0, 0xFFFFFFF8)]
        for text, initial, expected in cases:
            for sr in (0x2000, 0xA71F):
                with self.subTest(text=text, sr=sr):
                    state = State()
                    state.a[1] = initial
                    state.sr = sr
                    memory, before, trace = self.run_one(text, state)
                    self.assertEqual(state.a[1], expected)
                    self.assertEqual(state.sr, sr)
                    self.assertEqual(memory, before)
                    self.assertEqual(trace.writes, 0)

    def test_byte_at_memory_end_and_unmapped_arithmetic_refusal(self):
        state = State()
        state.a[0] = 63
        memory, before, trace = self.run_one("subi.b #1,(a0)", state, [(63, b"\x00")])
        self.assertEqual(memory[:-1], before[:-1])
        self.assertEqual(memory[-1], 255)
        self.assertEqual(state.sr, 0x19)
        self.assertEqual((trace.ranges[0].start, trace.ranges[0].end), (63, 64))
        for text, address in (("subi.w #1,(a0)", 63), ("subi.b #1,-(a0)", 0)):
            with self.subTest(text=text, address=address):
                state = State()
                state.a[0] = address
                state.sr = 0xA71F
                code = assemble("68000", text)
                memory = bytearray(b"\xa5" * 64)
                memory[:len(code)] = code
                before = bytes(memory)
                buf = (C.c_uint8 * len(memory)).from_buffer(memory)
                trace = Trace()
                self.assertEqual(engine()(0, buf, len(memory), C.byref(state), 1, 0, 0, None, C.byref(trace)), 0)
                self.assertEqual(trace.stop_reason, 5)
                self.assertEqual((trace.steps, trace.writes, state.pc), (0, 0, 0))
                # Refused execution may retain a prepared EA update; the API
                # does not promise register rollback. No instruction/write
                # completes and the arithmetic flags remain untouched.
                self.assertEqual(state.sr, 0xA71F)
                self.assertEqual(memory, before)

    def test_reversed_logical_form_memory_bindings(self):
        for text, expected in (("and.w d1,(a0)", b"\x00\x02"), ("or.w d1,(a0)", b"\x12\xff")):
            with self.subTest(text=text):
                state = State()
                state.a[0] = 32
                state.d[1] = 0xABCD00F2
                memory, before, trace = self.run_one(text, state, [(32, b"\x12\x0f")])
                wanted = bytearray(before)
                wanted[32:34] = expected
                self.assertEqual(memory, wanted)
                self.assertEqual(state.d[1], 0xABCD00F2)
                self.assertEqual(trace.writes, 1)
                self.assertEqual((trace.ranges[0].start, trace.ranges[0].end), (32, 34))
