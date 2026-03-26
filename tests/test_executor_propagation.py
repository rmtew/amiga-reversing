"""Test state propagation and memory model in m68k_executor."""

import struct

from _pytest.monkeypatch import MonkeyPatch

from m68k.instruction_primitives import DecodedOps, Operand
from m68k.m68k_disasm import Instruction
from m68k.m68k_executor import (
    AbstractMemory,
    CPUState,
    _apply_instruction,
    _apply_pea,
    _concrete,
    _join_states,
    analyze,
    collect_instruction_traces,
    discover_blocks,
)


def test_memory_basic() -> None:
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


def test_memory_copy() -> None:
    """Test memory copy independence."""
    mem = AbstractMemory()
    mem.write(0x100, _concrete(42), "w")
    mem2 = mem.copy()
    mem2.write(0x100, _concrete(99), "w")
    assert mem.read(0x100, "w").concrete == 42
    assert mem2.read(0x100, "w").concrete == 99


def test_apply_pea_ignores_invalid_ea_mode() -> None:
    cpu = CPUState()
    cpu.sp = _concrete(0x1000)
    mem = AbstractMemory()

    _apply_pea(
        "PEA",
        DecodedOps(ea_op=Operand(mode="predec", reg=0, value=None)),
        cpu,
        mem,
    )

    assert cpu.sp.is_known and cpu.sp.concrete == 0x1000
    assert not mem.read(0x1000, "l").is_known


def test_apply_instruction_ignores_unsupported_compute_mnemonic(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "m68k.m68k_executor.decode_instruction_ops",
        lambda inst, mnemonic, size: DecodedOps(),
    )
    inst = Instruction(
        offset=0,
        size=2,
        opcode=0,
        text="bfchg d0{0:1}",
        raw=b"\x00\x00",
        kb_mnemonic="BFCHG",
        operand_size="l",
    )

    _apply_instruction(inst, "BFCHG", CPUState(), AbstractMemory(), b"\x00\x00", 0)


def test_join_states() -> None:
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


def test_join_states_fast_path_for_identical_inputs() -> None:
    cpu = CPUState()
    cpu.d[0] = _concrete(42)
    mem = AbstractMemory()
    mem.write(0x1000, _concrete(0xAA), "b")

    cpu_j, mem_j = _join_states([(cpu, mem), (cpu, mem), (cpu, mem)])

    assert cpu_j is not cpu
    assert mem_j is not mem
    assert cpu_j.d[0].is_known and cpu_j.d[0].concrete == 42
    assert mem_j.read(0x1000, "b").concrete == 0xAA


def test_join_states_fast_path_for_identical_cpu_objects() -> None:
    cpu = CPUState()
    cpu.d[0] = _concrete(42)
    mem1 = AbstractMemory()
    mem1.write(0x1000, _concrete(0xAA), "b")
    mem2 = AbstractMemory()
    mem2.write(0x1000, _concrete(0xAA), "b")

    cpu_j, mem_j = _join_states([(cpu, mem1), (cpu, mem2)])

    assert cpu_j.d[0].is_known and cpu_j.d[0].concrete == 42
    assert mem_j.read(0x1000, "b").concrete == 0xAA


def test_join_states_fast_path_for_identical_memory_objects() -> None:
    cpu1 = CPUState()
    cpu1.d[0] = _concrete(42)
    cpu2 = CPUState()
    cpu2.d[0] = _concrete(42)
    mem = AbstractMemory()
    mem.write(0x1000, _concrete(0xAA), "b")

    cpu_j, mem_j = _join_states([(cpu1, mem), (cpu2, mem)])

    assert cpu_j.d[0].is_known and cpu_j.d[0].concrete == 42
    assert mem_j.read(0x1000, "b").concrete == 0xAA


def test_propagation_moveq_lea() -> None:
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


def test_propagation_add_sub() -> None:
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


def test_propagation_clr() -> None:
    """Test CLR propagation."""
    code = b''
    code += struct.pack('>H', 0x7000 | 99)          # moveq #99,d0
    code += struct.pack('>H', 0x4240)               # clr.w d0
    code += struct.pack('>H', 0x4E75)               # rts

    result = analyze(code, propagate=True)
    cpu, _ = result["exit_states"][0x0000]
    assert cpu.d[0].is_known and cpu.d[0].concrete == 0


def test_merge_point() -> None:
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


def test_collect_instruction_traces_preserves_first_arrival_loop_state() -> None:
    code = bytes.fromhex(
        "41FA0018"
        "43F900006000"
        "303C0004"
        "22D8"
        "51C8FFFC"
        "4EF900006000"
        "33FC448900DFF07E"
        "33FC801000DFF024"
        "4E75"
        "4E71"
    )
    blocks = discover_blocks(code, 0x40000, [0x40000])

    traces = collect_instruction_traces(blocks, code, base_addr=0x40000)

    copy_traces = [
        trace for trace in traces
        if trace.instruction.offset == 0x4000E and trace.incoming_source == 0x40000
    ]
    assert len(copy_traces) == 1
    trace = copy_traces[0]
    assert trace.pre_cpu.get_reg("an", 0).is_known
    assert trace.pre_cpu.get_reg("an", 0).concrete == 0x4001A
    assert trace.pre_cpu.get_reg("an", 1).is_known
    assert trace.pre_cpu.get_reg("an", 1).concrete == 0x6000
    assert trace.pre_cpu.get_reg("dn", 0).is_known
    assert trace.pre_cpu.get_reg("dn", 0).concrete == 4


def test_collect_instruction_traces_capture_post_memory_write() -> None:
    code = bytes.fromhex(
        "41F900001000"
        "7001"
        "2080"
        "4E75"
    )
    blocks = discover_blocks(code, 0, [0])

    traces = collect_instruction_traces(blocks, code, base_addr=0)

    write_trace = next(trace for trace in traces if trace.instruction.offset == 0x0008)
    assert not write_trace.pre_mem.read(0x1000, "l").is_known
    assert write_trace.post_mem.read(0x1000, "l").is_known
    assert write_trace.post_mem.read(0x1000, "l").concrete == 1


def test_collect_instruction_traces_watch_ranges_capture_only_watched_memory() -> None:
    code = bytes.fromhex(
        "41F900001000"
        "43F900002000"
        "7001"
        "2280"
        "4E75"
    )
    blocks = discover_blocks(code, 0, [0])

    traces = collect_instruction_traces(blocks, code, base_addr=0, watch_ranges=[(0x2000, 0x2004)])

    write_trace = next(trace for trace in traces if trace.instruction.offset == 0x000E)
    assert not write_trace.post_mem.read(0x1000, "l").is_known
    assert write_trace.post_mem.read(0x2000, "l").is_known
    assert write_trace.post_mem.read(0x2000, "l").concrete == 1


def test_collect_instruction_traces_replay_loop_iterations_until_state_repeats() -> None:
    code = bytes.fromhex(
        "45F900001000"
        "43F900002000"
        "7003"
        "22DA"
        "51C8FFFC"
        "4E75"
    )
    mem = AbstractMemory()
    mem.write(0x1000, _concrete(0x01020304), "l")
    mem.write(0x1004, _concrete(0x05060708), "l")
    mem.write(0x1008, _concrete(0x090A0B0C), "l")
    mem.write(0x100C, _concrete(0x0D0E0F10), "l")
    blocks = discover_blocks(code, 0x7000, [0x7000])

    traces = collect_instruction_traces(blocks, code, base_addr=0x7000, initial_mem=mem)

    move_traces = [trace for trace in traces if trace.instruction.offset == 0x700E]
    assert move_traces
    assert any(trace.post_mem.read(0x200C, "l").is_known for trace in move_traces)
    final_trace = next(trace for trace in reversed(move_traces) if trace.post_mem.read(0x200C, "l").is_known)
    assert final_trace.post_mem.read(0x2000, "l").concrete == 0x01020304
    assert final_trace.post_mem.read(0x2004, "l").concrete == 0x05060708
    assert final_trace.post_mem.read(0x2008, "l").concrete == 0x090A0B0C
    assert final_trace.post_mem.read(0x200C, "l").concrete == 0x0D0E0F10


def test_abstract_memory_code_section_respects_base_addr() -> None:
    mem = AbstractMemory(b"\x12\x34\x56\x78", code_base_addr=0x6000)

    value = mem.read(0x6000, "l")

    assert value.is_known
    assert value.concrete == 0x12345678
    assert not mem.read(0x2000, "l").is_known


def test_propagation_exg_swap() -> None:
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
