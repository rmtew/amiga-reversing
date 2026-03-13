#!/usr/bin/env py.exe
"""Test state propagation and memory model in m68k_executor."""

import sys
import struct
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))

from m68k_executor import (analyze, CPUState, AbstractMemory,
                            _concrete, _unknown, _join_states)


def test_memory_basic():
    """Test basic memory read/write."""
    mem = AbstractMemory()
    mem.write(0x1000, _concrete(0xDEADBEEF), "l")
    val = mem.read(0x1000, "l")
    assert val.is_known and val.concrete == 0xDEADBEEF, f"got {val}"
    # Word read from same address
    val_w = mem.read(0x1000, "w")
    assert val_w.is_known and val_w.concrete == 0xDEAD, f"got {val_w}"
    # Byte read
    val_b = mem.read(0x1000, "b")
    assert val_b.is_known and val_b.concrete == 0xDE, f"got {val_b}"
    # Word read at +2
    val_w2 = mem.read(0x1002, "w")
    assert val_w2.is_known and val_w2.concrete == 0xBEEF, f"got {val_w2}"
    # Uninitialized read
    val_u = mem.read(0x2000, "l")
    assert not val_u.is_known
    print("  memory_basic: OK")


def test_memory_copy():
    """Test memory copy independence."""
    mem = AbstractMemory()
    mem.write(0x100, _concrete(42), "w")
    mem2 = mem.copy()
    mem2.write(0x100, _concrete(99), "w")
    assert mem.read(0x100, "w").concrete == 42
    assert mem2.read(0x100, "w").concrete == 99
    print("  memory_copy: OK")


def test_join_states():
    """Test state joining at merge points."""
    cpu1 = CPUState()
    cpu1.d[0] = _concrete(42)
    cpu1.d[1] = _concrete(100)
    mem1 = AbstractMemory()
    mem1.write(0x1000, _concrete(0xAA), "b")

    cpu2 = CPUState()
    cpu2.d[0] = _concrete(42)   # same
    cpu2.d[1] = _concrete(200)  # different
    mem2 = AbstractMemory()
    mem2.write(0x1000, _concrete(0xAA), "b")  # same

    cpu_j, mem_j = _join_states([(cpu1, mem1), (cpu2, mem2)])
    assert cpu_j.d[0].is_known and cpu_j.d[0].concrete == 42, "D0 should agree"
    assert not cpu_j.d[1].is_known, "D1 should be unknown (disagreement)"
    assert mem_j.read(0x1000, "b").concrete == 0xAA, "mem should agree"
    print("  join_states: OK")


def test_propagation_moveq_lea():
    """Test MOVEQ + LEA propagation across blocks."""
    code = b''
    # Block 0: LEA 14(pc),a0 -> a0 = 0+2+14 = 16 = 0x10
    code += struct.pack('>HH', 0x41FA, 0x000E)     # lea 14(pc),a0      [0]
    code += struct.pack('>H', 0x7000 | 42)          # moveq #42,d0       [4]
    code += struct.pack('>HH', 0x6700, 0x0006)      # beq.w $0E          [6]
    # Block 1 [0x000A]: fallthrough
    code += struct.pack('>H', 0x2080)               # move.l d0,(a0)     [A]
    code += struct.pack('>H', 0x2210)               # move.l (a0),d1     [C]
    # Block 2 [0x000E]: branch target + fallthrough
    code += struct.pack('>H', 0x4E75)               # rts                [E]

    result = analyze(code, propagate=True)
    exit_states = result.get("exit_states", {})

    # After block 0: D0=42, A0=0x10
    if 0x0000 in exit_states:
        cpu, _ = exit_states[0x0000]
        assert cpu.d[0].is_known and cpu.d[0].concrete == 42, \
            f"D0={cpu.d[0]} (expect 42)"
        assert cpu.a[0].is_known and cpu.a[0].concrete == 0x10, \
            f"A0={cpu.a[0]} (expect 0x10)"
    else:
        assert False, "No exit state for block 0"

    # After block 1: D1 should be 42 (read from memory written by MOVE.L d0,(a0))
    if 0x000A in exit_states:
        cpu, mem = exit_states[0x000A]
        assert cpu.d[0].is_known and cpu.d[0].concrete == 42
        assert cpu.d[1].is_known and cpu.d[1].concrete == 42, \
            f"D1={cpu.d[1]} (expect 42 from memory propagation)"
        # Memory at 0x10 should have 42
        mem_val = mem.read(0x10, "l")
        assert mem_val.is_known and mem_val.concrete == 42
    else:
        assert False, "No exit state for block 1"

    print("  propagation_moveq_lea: OK")


def test_propagation_add_sub():
    """Test ADD/SUB propagation."""
    code = b''
    code += struct.pack('>H', 0x7000 | 10)          # moveq #10,d0       [0]
    code += struct.pack('>H', 0x7200 | 20)          # moveq #20,d1       [2]
    code += struct.pack('>H', 0xD041)               # add.w d1,d0        [4]
    code += struct.pack('>H', 0x4E75)               # rts                [6]

    result = analyze(code, propagate=True)
    exit_states = result.get("exit_states", {})

    if 0x0000 in exit_states:
        cpu, _ = exit_states[0x0000]
        assert cpu.d[0].is_known and cpu.d[0].concrete == 30, \
            f"D0={cpu.d[0]} (expect 30 = 10+20)"
        assert cpu.d[1].is_known and cpu.d[1].concrete == 20
    else:
        assert False, "No exit state for block 0"

    print("  propagation_add_sub: OK")


def test_propagation_clr():
    """Test CLR propagation."""
    code = b''
    code += struct.pack('>H', 0x7000 | 99)          # moveq #99,d0       [0]
    code += struct.pack('>H', 0x4240)               # clr.w d0           [2]
    code += struct.pack('>H', 0x4E75)               # rts                [4]

    result = analyze(code, propagate=True)
    exit_states = result.get("exit_states", {})

    if 0x0000 in exit_states:
        cpu, _ = exit_states[0x0000]
        assert cpu.d[0].is_known and cpu.d[0].concrete == 0, \
            f"D0={cpu.d[0]} (expect 0 after CLR)"
    print("  propagation_clr: OK")


def test_merge_point():
    """Test state merging at a merge point."""
    code = b''
    # Block 0: MOVEQ #10,d0 ; BEQ block2
    code += struct.pack('>H', 0x7000 | 10)          # moveq #10,d0       [0]
    code += struct.pack('>H', 0x7200 | 5)           # moveq #5,d1        [2]
    code += struct.pack('>HH', 0x6700, 0x0006)      # beq.w $0C          [4]
    # Block 1 [0x08]: fallthrough — changes d1
    code += struct.pack('>H', 0x7200 | 99)          # moveq #99,d1       [8]
    code += struct.pack('>H', 0x4E71)               # nop                [A]
    # Block 2 [0x0C]: merge — d0 should be 10, d1 should be unknown
    code += struct.pack('>H', 0x4E75)               # rts                [C]

    result = analyze(code, propagate=True)
    exit_states = result.get("exit_states", {})

    if 0x000C in exit_states:
        cpu, _ = exit_states[0x000C]
        assert cpu.d[0].is_known and cpu.d[0].concrete == 10, \
            f"D0={cpu.d[0]} (expect 10 — same on both paths)"
        assert not cpu.d[1].is_known, \
            f"D1={cpu.d[1]} (expect unknown — 5 vs 99 on different paths)"
    else:
        assert False, "No exit state for merge block"

    print("  merge_point: OK")


def test_propagation_exg_swap():
    """Test EXG and SWAP propagation."""
    code = b''
    code += struct.pack('>H', 0x7000 | 0x12)        # moveq #$12,d0      [0]
    code += struct.pack('>H', 0x7200 | 0x34)        # moveq #$34,d1      [2]
    code += struct.pack('>H', 0xC141)               # exg d0,d1          [4]
    code += struct.pack('>H', 0x4E75)               # rts                [6]

    result = analyze(code, propagate=True)
    exit_states = result.get("exit_states", {})

    if 0x0000 in exit_states:
        cpu, _ = exit_states[0x0000]
        assert cpu.d[0].is_known and cpu.d[0].concrete == 0x34, \
            f"D0={cpu.d[0]} (expect $34 after EXG)"
        assert cpu.d[1].is_known and cpu.d[1].concrete == 0x12, \
            f"D1={cpu.d[1]} (expect $12 after EXG)"
    print("  propagation_exg_swap: OK")


if __name__ == "__main__":
    print("Testing m68k_executor state propagation...")
    test_memory_basic()
    test_memory_copy()
    test_join_states()
    test_propagation_moveq_lea()
    test_propagation_add_sub()
    test_propagation_clr()
    test_merge_point()
    test_propagation_exg_swap()
    print(f"\nAll tests passed.")
