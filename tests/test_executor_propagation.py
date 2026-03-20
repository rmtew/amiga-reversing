"""Test state propagation and memory model in m68k_executor."""

import struct

from m68k.m68k_executor import (analyze, CPUState, AbstractMemory,
                                _concrete, _unknown, _join_states)


def test_memory_basic():
    """Test basic memory read/write."""
    mem = AbstractMemory()
    mem.write(0x1000, _concrete(0xDEADBEEF), "l")
    val = mem.read(0x1000, "l")
    assert val.is_known and val.concrete == 0xDEADBEEF, f"got {val}"
    val_w = mem.read(0x1000, "w")
    assert val_w.is_known and val_w.concrete == 0xDEAD, f"got {val_w}"
    val_b = mem.read(0x1000, "b")
    assert val_b.is_known and val_b.concrete == 0xDE, f"got {val_b}"
    val_w2 = mem.read(0x1002, "w")
    assert val_w2.is_known and val_w2.concrete == 0xBEEF, f"got {val_w2}"
    val_u = mem.read(0x2000, "l")
    assert not val_u.is_known


def test_memory_copy():
    """Test memory copy independence."""
    mem = AbstractMemory()
    mem.write(0x100, _concrete(42), "w")
    mem2 = mem.copy()
    mem2.write(0x100, _concrete(99), "w")
    assert mem.read(0x100, "w").concrete == 42
    assert mem2.read(0x100, "w").concrete == 99


def test_join_states():
    """Test state joining at merge points."""
    cpu1 = CPUState()
    cpu1.d[0] = _concrete(42)
    cpu1.d[1] = _concrete(100)
    mem1 = AbstractMemory()
    mem1.write(0x1000, _concrete(0xAA), "b")

    cpu2 = CPUState()
    cpu2.d[0] = _concrete(42)
    cpu2.d[1] = _concrete(200)
    mem2 = AbstractMemory()
    mem2.write(0x1000, _concrete(0xAA), "b")

    cpu_j, mem_j = _join_states([(cpu1, mem1), (cpu2, mem2)])
    assert cpu_j.d[0].is_known and cpu_j.d[0].concrete == 42
    assert not cpu_j.d[1].is_known
    assert mem_j.read(0x1000, "b").concrete == 0xAA


def test_join_states_fast_path_for_identical_inputs():
    cpu = CPUState()
    cpu.d[0] = _concrete(42)
    mem = AbstractMemory()
    mem.write(0x1000, _concrete(0xAA), "b")

    cpu_j, mem_j = _join_states([(cpu, mem), (cpu, mem), (cpu, mem)])

    assert cpu_j is not cpu
    assert mem_j is not mem
    assert cpu_j.d[0].is_known and cpu_j.d[0].concrete == 42
    assert mem_j.read(0x1000, "b").concrete == 0xAA


def test_join_states_fast_path_for_identical_cpu_objects():
    cpu = CPUState()
    cpu.d[0] = _concrete(42)
    mem1 = AbstractMemory()
    mem1.write(0x1000, _concrete(0xAA), "b")
    mem2 = AbstractMemory()
    mem2.write(0x1000, _concrete(0xAA), "b")

    cpu_j, mem_j = _join_states([(cpu, mem1), (cpu, mem2)])

    assert cpu_j.d[0].is_known and cpu_j.d[0].concrete == 42
    assert mem_j.read(0x1000, "b").concrete == 0xAA


def test_join_states_fast_path_for_identical_memory_objects():
    cpu1 = CPUState()
    cpu1.d[0] = _concrete(42)
    cpu2 = CPUState()
    cpu2.d[0] = _concrete(42)
    mem = AbstractMemory()
    mem.write(0x1000, _concrete(0xAA), "b")

    cpu_j, mem_j = _join_states([(cpu1, mem), (cpu2, mem)])

    assert cpu_j.d[0].is_known and cpu_j.d[0].concrete == 42
    assert mem_j.read(0x1000, "b").concrete == 0xAA


def test_propagation_moveq_lea():
    """Test MOVEQ + LEA propagation across blocks."""
    code = b''
    code += struct.pack('>HH', 0x41FA, 0x000E)     # lea 14(pc),a0      [0]
    code += struct.pack('>H', 0x7000 | 42)          # moveq #42,d0       [4]
    code += struct.pack('>HH', 0x6700, 0x0006)      # beq.w $0E          [6]
    code += struct.pack('>H', 0x2080)               # move.l d0,(a0)     [A]
    code += struct.pack('>H', 0x2210)               # move.l (a0),d1     [C]
    code += struct.pack('>H', 0x4E75)               # rts                [E]

    result = analyze(code, propagate=True)
    exit_states = result.get("exit_states", {})

    cpu, _ = exit_states[0x0000]
    assert cpu.d[0].is_known and cpu.d[0].concrete == 42
    assert cpu.a[0].is_known and cpu.a[0].concrete == 0x10

    cpu, mem = exit_states[0x000A]
    assert cpu.d[1].is_known and cpu.d[1].concrete == 42
    assert mem.read(0x10, "l").concrete == 42


def test_propagation_add_sub():
    """Test ADD/SUB propagation."""
    code = b''
    code += struct.pack('>H', 0x7000 | 10)          # moveq #10,d0
    code += struct.pack('>H', 0x7200 | 20)          # moveq #20,d1
    code += struct.pack('>H', 0xD041)               # add.w d1,d0
    code += struct.pack('>H', 0x4E75)               # rts

    result = analyze(code, propagate=True)
    cpu, _ = result["exit_states"][0x0000]
    assert cpu.d[0].is_known and cpu.d[0].concrete == 30
    assert cpu.d[1].is_known and cpu.d[1].concrete == 20


def test_propagation_clr():
    """Test CLR propagation."""
    code = b''
    code += struct.pack('>H', 0x7000 | 99)          # moveq #99,d0
    code += struct.pack('>H', 0x4240)               # clr.w d0
    code += struct.pack('>H', 0x4E75)               # rts

    result = analyze(code, propagate=True)
    cpu, _ = result["exit_states"][0x0000]
    assert cpu.d[0].is_known and cpu.d[0].concrete == 0


def test_merge_point():
    """Test state merging at a merge point."""
    code = b''
    code += struct.pack('>H', 0x7000 | 10)          # moveq #10,d0
    code += struct.pack('>H', 0x7200 | 5)           # moveq #5,d1
    code += struct.pack('>HH', 0x6700, 0x0006)      # beq.w $0C
    code += struct.pack('>H', 0x7200 | 99)          # moveq #99,d1
    code += struct.pack('>H', 0x4E71)               # nop
    code += struct.pack('>H', 0x4E75)               # rts

    result = analyze(code, propagate=True)
    cpu, _ = result["exit_states"][0x000C]
    assert cpu.d[0].is_known and cpu.d[0].concrete == 10
    assert not cpu.d[1].is_known


def test_propagation_exg_swap():
    """Test EXG and SWAP propagation."""
    code = b''
    code += struct.pack('>H', 0x7000 | 0x12)        # moveq #$12,d0
    code += struct.pack('>H', 0x7200 | 0x34)        # moveq #$34,d1
    code += struct.pack('>H', 0xC141)               # exg d0,d1
    code += struct.pack('>H', 0x4E75)               # rts

    result = analyze(code, propagate=True)
    cpu, _ = result["exit_states"][0x0000]
    assert cpu.d[0].is_known and cpu.d[0].concrete == 0x34
    assert cpu.d[1].is_known and cpu.d[1].concrete == 0x12
