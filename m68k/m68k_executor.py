"""KB-driven M68K symbolic executor - static analysis via abstract interpretation.

Walks disassembled code, maintaining an abstract register/memory state.
All instruction semantics are derived from the KB (m68k_instructions.json)
via the compute engine (m68k_compute.py). No hardcoded M68K knowledge.

Usage:
    from m68k_executor import Executor
    exe = Executor(code_bytes, base_addr=0x1000)
    blocks = exe.discover_blocks()
"""

from __future__ import annotations

import operator
import struct
import sys
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, TypeAlias, TypedDict, cast

from m68k_kb import runtime_m68k_analysis
from m68k_kb import runtime_m68k_executor
from m68k_kb.runtime_types import CcrState, ComputeFormula, KnownCcrState, MnemonicInstructionRecord

from .decode_errors import DecodeError
from .abstract_values import AbstractValue, _UNKNOWN, _concrete, _symbolic, _unknown
from .instruction_kb import instruction_kb
from .m68k_compute import _to_signed
from .m68k_compute import ComputeContext
from .m68k_disasm import disassemble, Instruction, _Decoder, _decode_one
from .instruction_primitives import (
    Operand,
    DecodedOps,
    decode_ea as _decode_ea,
    decode_instruction_ops,
    extract_branch_target as _extract_branch_target,
    xf as _xf,
)
from .operand_resolution import resolve_ea, _resolve_full_extension_ea
from .os_calls import (
    BaseRegisterCallEffect,
    LibraryBaseTag,
    MemoryAllocationCallEffect,
    OsResultTag,
    OutputRegisterCallEffect,
    PlatformState,
)

if TYPE_CHECKING:
    from .os_calls import CallEffect

__all__ = [
    "AbstractMemory",
    "AnalysisResult",
    "BasicBlock",
    "CPUState",
    "CallSummary",
    "Instruction",
    "XRef",
    "_concrete",
    "_resolve_operand",
    "_symbolic",
    "_unknown",
    "_write_operand",
    "analyze",
    "decode_instruction_ops",
    "propagate_states",
    "resolve_ea",
]


# -- KB loader -------------------------------------------------------------

_SIZE_BYTE_COUNT = runtime_m68k_analysis.SIZE_BYTE_COUNT
_OPWORD_BYTES = runtime_m68k_analysis.OPWORD_BYTES
_FLOW_BRANCH = runtime_m68k_analysis.FlowType.BRANCH
_FLOW_CALL = runtime_m68k_analysis.FlowType.CALL
_FLOW_JUMP = runtime_m68k_analysis.FlowType.JUMP
_FLOW_RETURN = runtime_m68k_analysis.FlowType.RETURN
_FLOW_SEQUENTIAL = runtime_m68k_analysis.FlowType.SEQUENTIAL
_FLOW_TRAP = runtime_m68k_analysis.FlowType.TRAP


# -- Module-level KB singletons (avoid per-call cache overhead) ------------



OperandMode: TypeAlias = str
StatePair: TypeAlias = tuple["CPUState", "AbstractMemory"]
IncomingStates: TypeAlias = dict[int, StatePair]
SymbolicKey: TypeAlias = tuple[str | None, int | None, int]
TagKey: TypeAlias = tuple[int, int]
TagMap: TypeAlias = object
class AnalysisResult(TypedDict, total=False):
    blocks: dict[int, BasicBlock]
    xrefs: list[XRef]
    call_targets: set[int]
    branch_targets: set[int]
    exit_states: dict[int, StatePair]


def _resolve_operand(
    operand: Operand,
    cpu: "CPUState",
    mem: "AbstractMemory",
    size: str,
    size_bytes: int,
) -> AbstractValue | None:
    """Read the value at a decoded EA operand.

    For postincrement/predecrement, also adjusts the register.
    Uses get_reg/set_reg for proper SP aliasing.
    Returns None if the operand can't be resolved.
    """
    if operand.mode == "dn":
        assert operand.reg is not None
        return cpu.get_reg("dn", operand.reg)
    if operand.mode == "an":
        assert operand.reg is not None
        return cpu.get_reg("an", operand.reg)
    if operand.mode == "imm":
        assert operand.value is not None
        return _concrete(operand.value)
    if operand.mode == "ind":
        assert operand.reg is not None
        addr = cpu.get_reg("an", operand.reg)
        if addr.is_known:
            return mem.read(addr.concrete, size)
        if addr.is_symbolic:
            return mem.read(addr, size)
        return None
    if operand.mode == "postinc":
        assert operand.reg is not None
        addr = cpu.get_reg("an", operand.reg)
        if addr.is_known:
            val = mem.read(addr.concrete, size)
            cpu.set_reg("an", operand.reg, _concrete(
                (addr.concrete + size_bytes) & 0xFFFFFFFF))
            return val
        if addr.is_symbolic:
            val = mem.read(addr, size)
            cpu.set_reg("an", operand.reg, addr.sym_add(size_bytes))
            return val
        return None
    if operand.mode == "predec":
        assert operand.reg is not None
        addr = cpu.get_reg("an", operand.reg)
        if addr.is_known:
            new_addr = (addr.concrete - size_bytes) & 0xFFFFFFFF
            cpu.set_reg("an", operand.reg, _concrete(new_addr))
            return mem.read(new_addr, size)
        if addr.is_symbolic:
            new_val = addr.sym_add(-size_bytes)
            cpu.set_reg("an", operand.reg, new_val)
            return mem.read(new_val, size)
        return None
    if operand.mode == "disp":
        assert operand.reg is not None
        assert operand.value is not None
        addr = cpu.get_reg("an", operand.reg)
        if addr.is_known:
            return mem.read(
                (addr.concrete + operand.value) & 0xFFFFFFFF, size)
        if addr.is_symbolic:
            return mem.read(addr.sym_add(operand.value), size)
        return None
    if operand.mode in ("absw", "absl", "pcdisp"):
        return None  # can't resolve without memory map
    if operand.mode == "index":
        if operand.full_extension:
            ea = _resolve_full_extension_ea(operand, cpu, mem)
            if ea is None:
                return None
            return mem.read(ea, size)
        assert operand.reg is not None
        base = cpu.get_reg("an", operand.reg)
        if not base.is_known:
            return None
        if operand.memory_indirect or operand.base_suppressed or operand.index_suppressed:
            return None
        idx_mode = "an" if operand.index_is_addr else "dn"
        assert operand.index_reg is not None
        assert operand.value is not None
        idx_val = cpu.get_reg(idx_mode, operand.index_reg)
        if not idx_val.is_known:
            return None
        nbits = _SIZE_BYTE_COUNT[operand.index_size] * 8
        mask = (1 << nbits) - 1
        idx_v = idx_val.concrete & mask
        if idx_v >= (1 << (nbits - 1)):
            idx_v -= (1 << nbits)
        ea = (base.concrete + operand.value + idx_v * operand.index_scale) & 0xFFFFFFFF
        return mem.read(ea, size)
    return None


def _write_operand(
    operand: Operand,
    cpu: "CPUState",
    mem: "AbstractMemory",
    value: AbstractValue,
    size: str,
    size_bytes: int,
) -> None:
    """Write a value to a decoded EA operand.

    For predecrement/postincrement, also adjusts the register.
    Uses get_reg/set_reg for proper SP aliasing.
    """
    if operand.mode == "dn":
        assert operand.reg is not None
        cpu.set_reg("dn", operand.reg, value)
    elif operand.mode == "an":
        assert operand.reg is not None
        cpu.set_reg("an", operand.reg, value)
    elif operand.mode == "ind":
        assert operand.reg is not None
        addr = cpu.get_reg("an", operand.reg)
        if addr.is_known:
            mem.write(addr.concrete, value, size)
        elif addr.is_symbolic:
            mem.write(addr, value, size)
    elif operand.mode == "predec":
        assert operand.reg is not None
        addr = cpu.get_reg("an", operand.reg)
        if addr.is_known:
            new_addr = (addr.concrete - size_bytes) & 0xFFFFFFFF
            cpu.set_reg("an", operand.reg, _concrete(new_addr))
            mem.write(new_addr, value, size)
        elif addr.is_symbolic:
            new_val = addr.sym_add(-size_bytes)
            cpu.set_reg("an", operand.reg, new_val)
            mem.write(new_val, value, size)
    elif operand.mode == "postinc":
        assert operand.reg is not None
        addr = cpu.get_reg("an", operand.reg)
        if addr.is_known:
            mem.write(addr.concrete, value, size)
            cpu.set_reg("an", operand.reg, _concrete(
                (addr.concrete + size_bytes) & 0xFFFFFFFF))
        elif addr.is_symbolic:
            mem.write(addr, value, size)
            cpu.set_reg("an", operand.reg, addr.sym_add(size_bytes))
    elif operand.mode == "disp":
        assert operand.reg is not None
        assert operand.value is not None
        addr = cpu.get_reg("an", operand.reg)
        if addr.is_known:
            mem.write(
                (addr.concrete + operand.value) & 0xFFFFFFFF,
                value, size)
        elif addr.is_symbolic:
            mem.write(addr.sym_add(operand.value), value, size)
    elif operand.mode in ("index", "pcindex") and operand.full_extension:
        ea = _resolve_full_extension_ea(operand, cpu, mem)
        if ea is not None:
            mem.write(ea, value, size)


# KB-derived register layout constants
_NUM_DATA_REGS = runtime_m68k_analysis.NUM_DATA_REGS
_NUM_ADDR_REGS = runtime_m68k_analysis.NUM_ADDR_REGS
_SP_REG_NUM = runtime_m68k_analysis.SP_REG_NUM
_CCR_FLAGS = list(runtime_m68k_analysis.CCR_FLAG_NAMES)
_DEFAULT_D = [_UNKNOWN] * _NUM_DATA_REGS
_DEFAULT_A = [_UNKNOWN] * _NUM_ADDR_REGS
_DEFAULT_CCR = {f: None for f in _CCR_FLAGS}


class _CPUState:
    """Abstract CPU state for symbolic execution.

    Register layout derived from KB movem_reg_masks and ccr_bit_positions.
    Uses __slots__ for performance (thousands of instances).
    """
    __slots__ = ("d", "a", "sp", "pc", "ccr")

    def __init__(self) -> None:
        self.d = list(_DEFAULT_D)
        self.a = list(_DEFAULT_A)
        self.sp = _UNKNOWN
        self.pc = 0
        self.ccr: dict[str, int | None] = dict(_DEFAULT_CCR)

    def get_reg(self, mode: str, reg: int) -> AbstractValue:
        if mode == "dn":
            return self.d[reg]
        if mode == "an":
            return self.sp if reg == _SP_REG_NUM else self.a[reg]
        raise ValueError(f"get_reg: unsupported mode '{mode}'")

    def set_reg(self, mode: str, reg: int, val: AbstractValue) -> None:
        if mode == "dn":
            self.d[reg] = val
        elif mode == "an":
            if reg == _SP_REG_NUM:
                self.sp = val
            else:
                self.a[reg] = val
        else:
            raise ValueError(f"set_reg: unsupported mode '{mode}'")

    def copy(self) -> _CPUState:
        s = _CPUState.__new__(_CPUState)
        s.d = list(self.d)
        s.a = list(self.a)
        s.sp = self.sp
        s.pc = self.pc
        s.ccr = dict(self.ccr)
        return s


CPUState = _CPUState


# -- EA resolution ---------------------------------------------------------

# -- PC prediction ---------------------------------------------------------

def predict_pc(
    inst_kb: str,
    pc: int,
    instr_size: int,
    displacement: int | None,
    ccr: CcrState,
    dn_val: int | None = None,
) -> list[int]:
    """Predict possible next-PC values from KB pc_effects.

    Returns a list of possible targets:
    - Sequential: [pc + instr_size]
    - Unconditional branch/jump: [target]
    - Conditional branch: [target, pc + instr_size] (taken, not-taken)
    - DBcc: up to [fallthrough, target] depending on condition

    Args:
        inst_kb: KB instruction dict
        pc: current instruction address
        instr_size: instruction size in bytes (from disassembler)
        displacement: branch displacement if applicable
        ccr: current CCR flags dict (may have None values for unknown flags)
        dn_val: Dn counter value for DBcc (None if unknown)
    """
    opword_bytes = _OPWORD_BYTES
    flow_type = runtime_m68k_analysis.FLOW_TYPES[inst_kb]
    conditional = runtime_m68k_analysis.FLOW_CONDITIONAL[inst_kb]
    next_seq = pc + instr_size

    if flow_type == _FLOW_SEQUENTIAL:
        return [next_seq]

    if flow_type in (_FLOW_BRANCH, _FLOW_JUMP, _FLOW_CALL):
        if displacement is not None:
            # Branches are relative to PC + opword_bytes (KB _meta.opword_bytes)
            target = pc + opword_bytes + displacement
        else:
            target = None  # jump through register - unknown target

        if not conditional:
            if target is not None:
                return [target]
            return []  # unknown target (JMP (An))

        # Conditional: both taken and not-taken paths
        targets = [next_seq]
        if target is not None:
            targets.append(target)
        return targets

    if flow_type == _FLOW_RETURN:
        return []  # unknown - return address on stack

    if flow_type == _FLOW_TRAP:
        return []  # exception vector

    print(f"WARNING: predict_pc: unhandled flow_type '{flow_type}' "
          f"for {inst_kb} at ${pc:06x}", file=sys.stderr)
    return [next_seq]


# -- Cross-reference tracking ---------------------------------------------

@dataclass
class XRef:
    """A cross-reference from one address to another."""
    src: int           # source instruction address
    dst: int           # target address
    type: str          # "branch", "jump", "call", "data_read", "data_write"
    conditional: bool = False


@dataclass(frozen=True, slots=True)
class CallSummary:
    preserved_d: frozenset[int] = frozenset()
    preserved_a: frozenset[int] = frozenset()
    produced_d: tuple[tuple[int, int], ...] = ()
    produced_d_tags: tuple[tuple[int, object], ...] = ()
    produced_a: tuple[tuple[int, int], ...] = ()
    produced_a_tags: tuple[tuple[int, object], ...] = ()
    sp_delta: int = 0


# -- Basic block -----------------------------------------------------------

@dataclass
class BasicBlock:
    """A sequence of instructions with single entry, single exit."""
    start: int         # address of first instruction
    end: int           # address after last instruction (exclusive)
    instructions: list[Instruction] = field(default_factory=list)
    successors: list[int] = field(default_factory=list)  # addresses of successor blocks
    predecessors: list[int] = field(default_factory=list)
    xrefs: list[XRef] = field(default_factory=list)
    is_entry: bool = False
    is_return: bool = False


# -- Block discovery -------------------------------------------------------

def discover_blocks(code: bytes, base_addr: int = 0,
                    entry_points: list[int] | None = None) -> dict[int, BasicBlock]:
    """Discover basic blocks by following control flow from entry points.

    Returns dict mapping block start address -> BasicBlock.
    Uses KB pc_effects to determine control flow at block boundaries.
    """
    if entry_points is None:
        entry_points = [base_addr]

    # Demand-driven disassembly: decode instructions as we follow flow,
    # rather than disassembling the entire code section upfront.
    # This handles mixed code/data sections where linear disassembly fails.
    instr_map: dict[int, Instruction] = {}  # addr -> Instruction (cache)

    def _disasm_at(addr: int) -> Instruction | None:
        """Disassemble one instruction at addr, caching the result."""
        if addr in instr_map:
            return instr_map[addr]
        offset = addr - base_addr
        if offset < 0 or offset + _OPWORD_BYTES > len(code):
            return None
        d = _Decoder(code, base_addr)
        d.pos = offset
        try:
            inst = _decode_one(d, None)
        except (DecodeError, struct.error):
            return None
        instr_map[addr] = inst
        return inst

    # Pass 1: Follow control flow to discover block boundary addresses.
    # We only record block_starts here - edges are derived in pass 2.
    block_starts: set[int] = set(entry_points)
    work = list(entry_points)
    visited: set[int] = set()

    while work:
        addr = work.pop()
        if addr in visited:
            continue
        visited.add(addr)

        pc = addr
        while True:
            inst = _disasm_at(pc)
            if inst is None:
                break
            next_seq = pc + inst.size
            inst_kb = instruction_kb(inst)

            flow_type = runtime_m68k_analysis.FLOW_TYPES[inst_kb]
            conditional = runtime_m68k_analysis.FLOW_CONDITIONAL[inst_kb]

            if flow_type == _FLOW_SEQUENTIAL:
                pc = next_seq
                if next_seq in block_starts and next_seq != addr:
                    break
                continue

            if flow_type in (_FLOW_BRANCH, _FLOW_JUMP, _FLOW_CALL):
                target = _extract_branch_target(inst, pc)
                if target is not None:
                    block_starts.add(target)
                    if target not in visited:
                        work.append(target)
                if conditional or flow_type == _FLOW_CALL:
                    block_starts.add(next_seq)
                    if next_seq not in visited:
                        work.append(next_seq)
                break

            break  # return, trap, etc.

    # Pass 2: Build blocks and derive edges from each block's last instruction.
    sorted_starts = sorted(block_starts)
    blocks: dict[int, BasicBlock] = {}

    for i, start in enumerate(sorted_starts):
        next_start = sorted_starts[i + 1] if i + 1 < len(sorted_starts) else base_addr + len(code)
        block_instrs = []
        pc = start
        while pc < next_start:
            inst = _disasm_at(pc)
            if inst is None:
                break
            block_instrs.append(inst)
            pc += inst.size
            inst_kb = instruction_kb(inst)
            ft = runtime_m68k_analysis.FLOW_TYPES[inst_kb]
            if ft != _FLOW_SEQUENTIAL:
                break

        if not block_instrs:
            continue

        last_inst = block_instrs[-1]
        end = last_inst.offset + last_inst.size
        block = BasicBlock(
            start=start,
            end=end,
            instructions=block_instrs,
            is_entry=(start in entry_points),
        )

        # Derive edges from the last instruction's KB flow type
        last_kb = instruction_kb(last_inst)
        flow_type = runtime_m68k_analysis.FLOW_TYPES[last_kb]
        conditional = runtime_m68k_analysis.FLOW_CONDITIONAL[last_kb]

        if flow_type == _FLOW_SEQUENTIAL:
            # Fallthrough to next block
            if end in block_starts:
                block.successors.append(end)
                block.xrefs.append(XRef(
                    src=last_inst.offset, dst=end,
                    type="fallthrough", conditional=False))

        elif flow_type in (_FLOW_BRANCH, _FLOW_JUMP, _FLOW_CALL):
            target = _extract_branch_target(last_inst, last_inst.offset)
            if target is not None:
                block.successors.append(target)
                block.xrefs.append(XRef(
                    src=last_inst.offset, dst=target,
                    type=flow_type, conditional=conditional))
            if conditional or flow_type == _FLOW_CALL:
                block.successors.append(end)
                block.xrefs.append(XRef(
                    src=last_inst.offset, dst=end,
                    type="fallthrough", conditional=False))

        elif flow_type == _FLOW_RETURN:
            block.is_return = True

        blocks[start] = block

    # Fill in predecessors
    for addr, block in blocks.items():
        for succ in block.successors:
            if succ in blocks:
                if addr not in blocks[succ].predecessors:
                    blocks[succ].predecessors.append(addr)

    return blocks


# -- Helpers ---------------------------------------------------------------

# -- Abstract memory ------------------------------------------------------


class AbstractMemory:
    """Sparse memory map tracking concrete and symbolic values.

    Two stores: concrete (addr: int -> byte values) and symbolic
    (base+offset keys -> full values).  Concrete store handles normal
    memory; symbolic store handles SP-relative push/pop where the
    actual address is unknown but the base+offset is tracked.

    Reads/writes at byte, word, and long sizes.  Byte order is
    big-endian (M68K native).
    """

    def __init__(self, code_section: bytes | None = None) -> None:
        self._bytes: dict[int, AbstractValue] = {}  # concrete addr -> byte
        self._tags: dict[TagKey, TagMap] = {}  # (addr, nbytes) -> tag dict
        # Symbolic store: (base_name, offset, nbytes) -> AbstractValue
        self._sym: dict[SymbolicKey, AbstractValue] = {}
        # Read-only fallback: code section bytes for resolving data reads.
        # When a concrete address is unmapped, falls back to code_section
        # if the address is within range.
        self._code_section: bytes | None = code_section

    def write(self, addr: int | AbstractValue, value: AbstractValue, size: str) -> None:
        """Write a value.  addr is int (concrete) or AbstractValue (symbolic)."""
        nbytes = _SIZE_BYTE_COUNT[size]

        if isinstance(addr, AbstractValue):
            if addr.is_symbolic:
                key = (addr.sym_base, addr.sym_offset, nbytes)
                self._sym[key] = value
                return
            if addr.is_known:
                addr = addr.concrete
            else:
                return  # unknown address - can't store

        if value.is_known:
            val = value.concrete
            for i in range(nbytes):
                shift = (nbytes - 1 - i) * 8
                self._bytes[addr + i] = _concrete((val >> shift) & 0xFF)
        else:
            for i in range(nbytes):
                self._bytes[addr + i] = _unknown()
        if value.tag:
            self._tags[(addr, nbytes)] = value.tag
        elif (addr, nbytes) in self._tags:
            del self._tags[(addr, nbytes)]

    def read(self, addr: int | AbstractValue, size: str) -> AbstractValue:
        """Read a value.  addr is int (concrete) or AbstractValue (symbolic)."""
        nbytes = _SIZE_BYTE_COUNT[size]

        if isinstance(addr, AbstractValue):
            if addr.is_symbolic:
                key = (addr.sym_base, addr.sym_offset, nbytes)
                return self._sym.get(key, _unknown())
            if addr.is_known:
                addr = addr.concrete
            else:
                return _unknown()

        result = 0
        for i in range(nbytes):
            bv = self._bytes.get(addr + i)
            if bv is None or not bv.is_known:
                # Fall back to code section for unmapped addresses
                if (bv is None and self._code_section is not None
                        and 0 <= addr + i < len(self._code_section)):
                    byte_val = self._code_section[addr + i]
                    result = (result << 8) | byte_val
                    continue
                tag = self._tags.get((addr, nbytes))
                return _unknown(tag=tag)
            result = (result << 8) | (bv.concrete & 0xFF)
        tag = self._tags.get((addr, nbytes))
        return _concrete(result, tag=tag)

    def copy(self) -> AbstractMemory:
        """Create an independent copy."""
        m = AbstractMemory(self._code_section)
        m._bytes = dict(self._bytes)
        m._tags = dict(self._tags)
        m._sym = dict(self._sym)
        return m

    def known_ranges(self) -> list[tuple[int, int]]:
        """Return sorted list of (start, end) ranges with known bytes."""
        if not self._bytes:
            return []
        addrs = sorted(self._bytes)
        ranges = []
        start = addrs[0]
        prev = start
        for a in addrs[1:]:
            if a != prev + 1:
                ranges.append((start, prev + 1))
                start = a
            prev = a
        ranges.append((start, prev + 1))
        return ranges


# -- State propagation ----------------------------------------------------

def _join_values(a: AbstractValue, b: AbstractValue) -> AbstractValue:
    """Join two abstract values at a merge point.

    Concrete: both concrete and equal -> keep.
    Symbolic: both symbolic with same base and offset -> keep.
    Otherwise: unknown.  Tag preserved if both agree.
    """
    # Fast path: identical objects (common when sharing references)
    if a is b:
        return a
    tag = a.tag if a.tag is not None and a.tag == b.tag else None
    if a.is_known and b.is_known and a.concrete == b.concrete:
        if tag is a.tag:
            return a
        return AbstractValue(concrete=a.concrete, tag=tag)
    if (a.sym_base is not None and a.sym_base == b.sym_base
            and a.sym_offset == b.sym_offset):
        if tag is a.tag:
            return a
        return AbstractValue(sym_base=a.sym_base,
                             sym_offset=a.sym_offset, tag=tag)
    if tag is None:
        return _UNKNOWN
    return _unknown(tag=tag)


def _join_states(
    states: list[StatePair],
    init_mem: AbstractMemory | None = None,
) -> StatePair:
    """Join multiple CPU states at a block merge point.

    Returns (joined_cpu_state, joined_memory).
    For each register/flag/memory cell: if all incoming states agree on
    a concrete value, keep it; otherwise mark unknown.

    init_mem, when provided, supplies default values for memory bytes
    that a predecessor never wrote to.  This makes the join aware of
    program-init state without post-hoc restoration.  If a predecessor
    explicitly overwrote an init byte (even with unknown), its value is
    used in the join -- init_mem only fills genuinely missing bytes.
    """
    if not states:
        return CPUState(), AbstractMemory()
    if len(states) == 1:
        cpu, mem = states[0]
        return cpu.copy(), mem.copy()
    first_cpu, first_mem = states[0]
    if all(cpu is first_cpu and mem is first_mem for cpu, mem in states[1:]):
        return first_cpu.copy(), first_mem.copy()
    if all(cpu is first_cpu for cpu, _ in states[1:]):
        _, result_mem = _join_states([(CPUState(), mem) for _, mem in states], init_mem=init_mem)
        return first_cpu.copy(), result_mem
    if all(mem is first_mem for _, mem in states[1:]):
        result_cpu, _ = _join_states([(cpu, AbstractMemory()) for cpu, _ in states])
        return result_cpu, first_mem.copy()

    _UNK = _UNKNOWN

    # Fast path for 2 predecessors (most common merge case).
    # Inline the join logic to avoid 16+ function calls per merge.
    if len(states) == 2:
        other_cpu, other_mem = states[1]

        # If both CPU states are the same object, skip register comparison
        if first_cpu is other_cpu:
            result_cpu = first_cpu.copy()
        else:
            cls = _CPUState
            result_cpu = cls.__new__(cls)
            # Inline join for data registers
            rd: list[AbstractValue] = [_UNK for _ in range(len(first_cpu.d))]
            fd, od = first_cpu.d, other_cpu.d
            for i in range(len(fd)):
                a = fd[i]
                b = od[i]
                if a is b:
                    rd[i] = a
                elif (a.is_known and b.is_known and a.concrete == b.concrete
                      and a.tag == b.tag):
                    rd[i] = a
                elif (a.sym_base is not None and a.sym_base == b.sym_base
                      and a.sym_offset == b.sym_offset and a.tag == b.tag):
                    rd[i] = a
                else:
                    rd[i] = _UNK
            result_cpu.d = rd

            # Inline join for address registers
            ra: list[AbstractValue] = [_UNK for _ in range(len(first_cpu.a))]
            fa, oa = first_cpu.a, other_cpu.a
            for i in range(len(fa)):
                a = fa[i]
                b = oa[i]
                if a is b:
                    ra[i] = a
                elif (a.is_known and b.is_known and a.concrete == b.concrete
                      and a.tag == b.tag):
                    ra[i] = a
                elif (a.sym_base is not None and a.sym_base == b.sym_base
                      and a.sym_offset == b.sym_offset and a.tag == b.tag):
                    ra[i] = a
                else:
                    ra[i] = _UNK
            result_cpu.a = ra

            # SP
            a, b = first_cpu.sp, other_cpu.sp
            if a is b:
                result_cpu.sp = a
            elif (a.is_known and b.is_known and a.concrete == b.concrete
                  and a.tag == b.tag):
                result_cpu.sp = a
            elif (a.sym_base is not None and a.sym_base == b.sym_base
                  and a.sym_offset == b.sym_offset and a.tag == b.tag):
                result_cpu.sp = a
            else:
                result_cpu.sp = _UNK

            result_cpu.pc = 0
            # CCR
            ccr = {}
            for flag in first_cpu.ccr:
                v0 = first_cpu.ccr.get(flag)
                ccr[flag] = v0 if v0 is not None and other_cpu.ccr.get(flag) == v0 else None
            result_cpu.ccr = ccr
    else:
        # General N-way join
        result_cpu = CPUState()
        n_d = len(result_cpu.d)
        n_a = len(result_cpu.a)
        _jv = _join_values

        for i in range(n_d):
            r = first_cpu.d[i]
            for s in states[1:]:
                r = _jv(r, s[0].d[i])
            result_cpu.d[i] = r
        for i in range(n_a):
            r = first_cpu.a[i]
            for s in states[1:]:
                r = _jv(r, s[0].a[i])
            result_cpu.a[i] = r
        r = first_cpu.sp
        for s in states[1:]:
            r = _jv(r, s[0].sp)
        result_cpu.sp = r
        for flag in result_cpu.ccr:
            v0 = first_cpu.ccr.get(flag)
            if v0 is not None and all(
                    s[0].ccr.get(flag) == v0 for s in states[1:]):
                result_cpu.ccr[flag] = v0
            else:
                result_cpu.ccr[flag] = None

    # Join memory
    code_sec = first_mem._code_section
    if code_sec is None:
        for _, mem in states[1:]:
            if mem._code_section is not None:
                code_sec = mem._code_section
                break
    if all(s[1] is first_mem for s in states[1:]):
        result_mem = first_mem.copy()
    else:
        result_mem = AbstractMemory(code_sec)
        _jv = _join_values
        init_bytes = init_mem._bytes if init_mem is not None else {}

        # Compute address sets: intersection for non-init bytes,
        # union for init-mem bytes (using init value as default).
        common_addrs = set(states[0][1]._bytes.keys())
        for _, mem in states[1:]:
            common_addrs &= mem._bytes.keys()
        # Add init-mem addresses present in at least one predecessor
        if init_bytes:
            all_addrs = set(states[0][1]._bytes.keys())
            for _, mem in states[1:]:
                all_addrs |= mem._bytes.keys()
            common_addrs |= (all_addrs & init_bytes.keys())

        for addr in common_addrs:
            init_default = init_bytes.get(addr)
            joined_val: AbstractValue | None = states[0][1]._bytes.get(addr, init_default)
            if joined_val is None:
                continue
            for _, mem in states[1:]:
                v = mem._bytes.get(addr, init_default)
                if v is None:
                    joined_val = _UNKNOWN
                    break
                joined_val = _jv(joined_val, v)
            assert joined_val is not None
            if joined_val.is_known:
                result_mem._bytes[addr] = joined_val

        # Tags: intersection semantics (init_mem tags included)
        init_tags = init_mem._tags if init_mem is not None else {}
        common_tags = set(states[0][1]._tags.keys())
        for _, mem in states[1:]:
            common_tags &= mem._tags.keys()
        if init_tags:
            all_tag_keys = set(states[0][1]._tags.keys())
            for _, mem in states[1:]:
                all_tag_keys |= mem._tags.keys()
            common_tags |= (all_tag_keys & init_tags.keys())
        for key in common_tags:
            init_t = init_tags.get(key)
            t0 = states[0][1]._tags.get(key, init_t)
            if t0 is not None and all(
                    s[1]._tags.get(key, init_t) == t0 for s in states[1:]):
                result_mem._tags[key] = t0

        common_sym: set[SymbolicKey] = set(states[0][1]._sym.keys())
        for _, mem in states[1:]:
            common_sym &= mem._sym.keys()
        for sym_key in common_sym:
            r = states[0][1]._sym[sym_key]
            for _, mem in states[1:]:
                r = _jv(r, mem._sym[sym_key])
            if r.is_known or r.sym_base is not None or r.tag:
                result_mem._sym[sym_key] = r

    return result_cpu, result_mem


def _incoming_state_signature(pred_dict: IncomingStates) -> frozenset[tuple[int, int, int]]:
    return frozenset((src, id(cpu), id(mem)) for src, (cpu, mem) in pred_dict.items())


def _parse_reg_from_text(reg_text: str) -> tuple[str, int] | None:
    """Parse a register name into (mode, reg_num).

    Returns ('dn', N) or ('an', N) or None.
    """
    reg_text = reg_text.strip().lower()
    # Check register aliases from KB (e.g. "sp" -> "a7")
    aliases = runtime_m68k_analysis.REGISTER_ALIASES
    if reg_text in aliases:
        reg_text = aliases[reg_text]
    if len(reg_text) == 2 and reg_text[0] in ('d', 'a') and reg_text[1].isdigit():
        num = int(reg_text[1])
        mode = "dn" if reg_text[0] == 'd' else "an"
        return (mode, num)
    return None


# -- Binary operation table ------------------------------------------------

_BINARY_OPS = {
    "add": operator.add,
    "subtract": operator.sub,
    "bitwise_and": operator.and_,
    "bitwise_or": operator.or_,
    "bitwise_xor": operator.xor,
}


def _sign_ext_src(val: AbstractValue | None, src_sign_ext: bool, size: str) -> AbstractValue | None:
    """Sign-extend source value per KB source_sign_extend."""
    if src_sign_ext and size == "w" and val and val.is_known:
        w_bits = _SIZE_BYTE_COUNT["w"] * 8
        w_mask = (1 << w_bits) - 1
        v = val.concrete & w_mask
        if v >= (1 << (w_bits - 1)):
            v |= ~w_mask
        return _concrete(v & 0xFFFFFFFF)
    return val


def _apply_binary_op(
    op_fn: Callable[[int, int], int],
    d: DecodedOps,
    inst_kb: str,
    cpu: _CPUState,
    mem: AbstractMemory,
    size: str,
    size_bytes: int,
    op_type: object,
) -> None:
    """Apply a binary arithmetic/logic operation to the abstract state.

    Handles three patterns from KB:
    1. OPMODE-directed: ea_is_source determines direction (ADD/SUB/AND/OR/EOR)
    2. Immediate + EA: ADDI/SUBI/ANDI/ORI/EORI
    3. Error if neither pattern matches

    For subtract with compare (operation_type=="compare"): no write (CMP/CMPI/CMPA).
    Source sign-extension applied per KB source_sign_extend.
    """
    src_sign_ext = inst_kb in runtime_m68k_executor.SOURCE_SIGN_EXTEND
    is_compare = (op_type == runtime_m68k_executor.OperationType.COMPARE)
    # For bitwise ops, the destination is always Dn (no source_sign_extend).
    # For add/subtract, source_sign_extend distinguishes ADDA/SUBA (An dest)
    # from ADD/SUB (Dn dest).
    is_bitwise = (op_fn in (operator.and_, operator.or_, operator.xor))

    if d.ea_is_source is not None and d.ea_op and d.reg_num is not None:
        # OPMODE-directed
        if is_bitwise:
            dst_mode = "dn"
        else:
            dst_mode = "an" if src_sign_ext else "dn"
        ea_val = _resolve_operand(d.ea_op, cpu, mem, size, size_bytes)
        reg_val = cpu.get_reg(dst_mode, d.reg_num)
        if d.ea_is_source:
            src_val = _sign_ext_src(ea_val, src_sign_ext, size)
            op_dst_val: AbstractValue | None = reg_val
        else:
            src_val = _sign_ext_src(reg_val, src_sign_ext, size)
            op_dst_val = ea_val
        assert d.reg_num is not None
        if not is_compare:
            if src_val and op_dst_val and src_val.is_known and op_dst_val.is_known:
                r = op_fn(op_dst_val.concrete, src_val.concrete) & 0xFFFFFFFF
                if d.ea_is_source:
                    cpu.set_reg(dst_mode, d.reg_num, _concrete(r))
                else:
                    _write_operand(d.ea_op, cpu, mem, _concrete(r),
                                   size, size_bytes)
            else:
                if d.ea_is_source:
                    cpu.set_reg(dst_mode, d.reg_num, _unknown())
                else:
                    _write_operand(d.ea_op, cpu, mem, _unknown(),
                                   size, size_bytes)
        # CMP/CMPA: no register/memory write (CC flags only)
    elif d.imm_val is not None and d.ea_op:
        # Immediate + EA destination (ADDQ/ADDI/SUBI/ANDI/ORI/EORI)
        if not is_compare:
            imm_dst_val: AbstractValue | None = _resolve_operand(d.ea_op, cpu, mem, size, size_bytes)
            src_val = _sign_ext_src(_concrete(d.imm_val),
                                    src_sign_ext, size)
            if src_val and imm_dst_val and src_val.is_known and imm_dst_val.is_known:
                r = op_fn(imm_dst_val.concrete, src_val.concrete) & 0xFFFFFFFF
                _write_operand(d.ea_op, cpu, mem, _concrete(r),
                               size, size_bytes)
            else:
                _write_operand(d.ea_op, cpu, mem, _unknown(),
                               size, size_bytes)
        # CMPI: no write
    elif is_compare:
        pass  # compare: no register/memory write (CC flags only)
    elif inst_kb in runtime_m68k_executor.OPERAND_MODE_TABLES:
        # Register-pair encoding: ADDX/SUBX/ABCD/SBCD
        mnemonic = inst_kb
        reg_fields = runtime_m68k_executor.REGISTER_FIELDS.get(mnemonic)
        assert reg_fields is not None, f"runtime KB missing paired register fields for {mnemonic}"
        assert len(reg_fields) >= 2, f"runtime KB missing paired register fields for {mnemonic}"
        rx = _xf(d.opcode, reg_fields[0])
        ry = _xf(d.opcode, reg_fields[1])
        rm_info = runtime_m68k_executor.RM_FIELD.get(mnemonic)
        assert rm_info is not None, f"runtime KB missing R/M field for {mnemonic}"
        rm_bit_lo, rm_values = rm_info
        rm = (d.opcode >> rm_bit_lo) & 1
        assert 0 <= rm < len(rm_values) and rm_values[rm] is not None, (
            f"runtime KB missing R/M value {rm} for {mnemonic}"
        )
        if rm == 0:
            # Register-to-register: src=Dy, dst=Dx
            src_val = cpu.d[ry]
            dst_val = cpu.d[rx]
            if src_val.is_known and dst_val.is_known:
                r = op_fn(dst_val.concrete, src_val.concrete) & 0xFFFFFFFF
                cpu.set_reg("dn", rx, _concrete(r))
            else:
                cpu.set_reg("dn", rx, _unknown())
        else:
            # Predecrement: src=-(Ay), dst=-(Ax) - memory operation
            # Decrement both address registers, read, compute, write
            for an in (ry, rx):
                if cpu.a[an].is_known:
                    cpu.set_reg("an", an, _concrete(
                        (cpu.a[an].concrete - size_bytes) & 0xFFFFFFFF))
            src_val = mem.read(cpu.a[ry], size)
            dst_val = mem.read(cpu.a[rx], size)
            if src_val and dst_val and src_val.is_known and dst_val.is_known:
                r = op_fn(dst_val.concrete, src_val.concrete) & 0xFFFFFFFF
                mem.write(cpu.a[rx], _concrete(r), size)
            elif cpu.a[rx].is_known:
                mem.write(cpu.a[rx], _unknown(), size)
    else:
        assert False, f"{op_fn.__name__}: no structured decode for {inst_kb}"


def _apply_neg(d: DecodedOps, inst_kb: str, cpu: _CPUState, mem: AbstractMemory, size: str, size_bytes: int, mask: int) -> None:
    """Apply NEG: implicit(0) - destination (single operand)."""
    mnemonic = inst_kb
    implicit_val = runtime_m68k_executor.IMPLICIT_OPERANDS.get(mnemonic)
    assert implicit_val is not None, f"implicit_operand missing for {mnemonic}"
    assert d.ea_op is not None, f"subtract/implicit: no EA for {mnemonic}"
    dst_val = _resolve_operand(d.ea_op, cpu, mem, size, size_bytes)
    if dst_val and dst_val.is_known:
        result = (implicit_val - dst_val.concrete) & mask
        if size != "l":
            result = (dst_val.concrete & ~mask) | result
        _write_operand(d.ea_op, cpu, mem,
                       _concrete(result & 0xFFFFFFFF),
                       size, size_bytes)
    else:
        _write_operand(d.ea_op, cpu, mem, _unknown(),
                       size, size_bytes)


def _apply_complement(d: DecodedOps, cpu: _CPUState, mem: AbstractMemory, size: str, size_bytes: int, mask: int) -> None:
    """Apply NOT: ~destination (single operand = ea_op)."""
    assert d.ea_op is not None, "bitwise_complement: no EA"
    dst_val = _resolve_operand(d.ea_op, cpu, mem, size, size_bytes)
    if dst_val and dst_val.is_known:
        result = dst_val.concrete ^ mask
        if size != "l":
            result = (dst_val.concrete & ~mask) | result
        _write_operand(d.ea_op, cpu, mem,
                       _concrete(result & 0xFFFFFFFF),
                       size, size_bytes)
    else:
        _write_operand(d.ea_op, cpu, mem, _unknown(),
                       size, size_bytes)


def _apply_swap(
    d: DecodedOps,
    inst_kb: str,
    formula: ComputeFormula,
    cpu: _CPUState,
) -> None:
    """Apply SWAP: exchange bit ranges within Dn."""
    range_a = formula[2]
    range_b = formula[3]
    if not (range_a and range_b):
        return
    # Get Dn register: from ea_op if decoded, else from REGISTER field
    if d.ea_op and d.ea_op.mode == "dn":
        dn = d.ea_op.reg
    else:
        mnemonic = inst_kb
        reg_fields = runtime_m68k_executor.REGISTER_FIELDS.get(mnemonic)
        assert reg_fields is not None and len(reg_fields) == 1, (
            f"runtime KB missing single register field for {mnemonic}"
        )
        dn = _xf(d.opcode, reg_fields[0])
    assert dn is not None
    val = cpu.get_reg("dn", dn)
    if val.is_known:
        v = val.concrete
        a_hi, a_lo = range_a
        b_hi, b_lo = range_b
        a_width = a_hi - a_lo + 1
        b_width = b_hi - b_lo + 1
        a_mask = ((1 << a_width) - 1) << a_lo
        b_mask = ((1 << b_width) - 1) << b_lo
        a_bits = (v & a_mask) >> a_lo
        b_bits = (v & b_mask) >> b_lo
        v = (v & ~(a_mask | b_mask)) | (b_bits << a_lo) | (a_bits << b_lo)
        cpu.set_reg("dn", dn, _concrete(v & 0xFFFFFFFF))
    else:
        cpu.set_reg("dn", dn, _unknown())


def _apply_sign_extend(
    d: DecodedOps,
    inst_kb: str,
    formula: ComputeFormula,
    cpu: _CPUState,
    mnemonic: str,
    size: str,
) -> None:
    """Apply EXT/EXTB: sign-extend Dn from source_bits_by_size."""
    source_bits = formula[4]
    assert source_bits is not None, f"source_bits_by_size missing for {mnemonic}"
    src_bits_by_size = dict(source_bits)
    assert src_bits_by_size, f"source_bits_by_size missing for {mnemonic}"
    # EXT has Dn in REGISTER field (no MODE field, so ea_op may
    # be None).  Fall back to first REGISTER field from encoding.
    if d.ea_op and d.ea_op.mode == "dn":
        dn = d.ea_op.reg
    else:
        reg_fields = runtime_m68k_executor.REGISTER_FIELDS.get(mnemonic)
        assert reg_fields is not None and len(reg_fields) == 1, (
            f"runtime KB missing single register field for {mnemonic}"
        )
        dn = _xf(d.opcode, reg_fields[0])
    assert dn is not None
    val = cpu.get_reg("dn", dn)
    if val.is_known:
        v = val.concrete
        mnemonic_key = mnemonic.lower() + "_" + size
        src_bits = src_bits_by_size.get(mnemonic_key,
                                        src_bits_by_size.get(size))
        assert src_bits is not None, f"No source_bits for size={size} in {mnemonic}"
        src_mask = (1 << src_bits) - 1
        src_val = v & src_mask
        w_bits = _SIZE_BYTE_COUNT["w"] * 8
        w_mask = (1 << w_bits) - 1
        if src_val >= (1 << (src_bits - 1)):
            if size == "w":
                extended = src_val | (~src_mask & w_mask)
                v = (v & ~w_mask) | (extended & w_mask)
            else:
                v = src_val | ~src_mask
        else:
            if size == "w":
                v = (v & ~w_mask) | (src_val & w_mask)
            else:
                v = src_val
        cpu.set_reg("dn", dn, _concrete(v & 0xFFFFFFFF))
    else:
        cpu.set_reg("dn", dn, _unknown())


def _apply_exg(d: DecodedOps, inst_kb: str, cpu: _CPUState) -> None:
    """Apply EXG: exchange two registers (KB operation_type == 'swap',
    no compute_formula)."""
    mnemonic = inst_kb
    opmode_table = runtime_m68k_executor.OPMODE_TABLES_BY_VALUE.get(mnemonic)
    assert opmode_table is not None, f"runtime KB missing opmode table for {mnemonic}"
    opword_fields = runtime_m68k_executor.FIELD_MAPS[0].get(mnemonic)
    assert opword_fields is not None, f"runtime KB missing opword field map for {mnemonic}"
    assert "OPMODE" in opword_fields, f"runtime KB missing OPMODE field for {mnemonic}"
    opmode = _xf(d.opcode, opword_fields["OPMODE"])
    entry = opmode_table.get(opmode)
    assert entry is not None, f"Unknown OPMODE {opmode} for {mnemonic}"
    reg_fields = runtime_m68k_executor.REGISTER_FIELDS.get(mnemonic)
    assert reg_fields is not None and len(reg_fields) >= 2, (
        f"runtime KB missing paired register fields for {mnemonic}"
    )
    rx = _xf(d.opcode, reg_fields[0])
    ry = _xf(d.opcode, reg_fields[1])
    rx_mode = entry.rx_mode
    ry_mode = entry.ry_mode
    assert rx_mode is not None and ry_mode is not None, (
        f"runtime KB missing EXG register modes for {mnemonic}"
    )
    sv = cpu.get_reg(rx_mode, rx)
    dv = cpu.get_reg(ry_mode, ry)
    cpu.set_reg(rx_mode, rx, dv)
    cpu.set_reg(ry_mode, ry, sv)


def _apply_movem(inst: Instruction, inst_kb: str, d: DecodedOps, cpu: _CPUState, mem: AbstractMemory) -> None:
    """Apply MOVEM: move multiple registers to/from memory."""
    opword_bytes = _OPWORD_BYTES
    if len(inst.raw) < opword_bytes + 2:
        return  # truncated
    opcode = struct.unpack_from(">H", inst.raw, 0)[0]
    reg_mask = struct.unpack_from(">H", inst.raw, opword_bytes)[0]
    direction = _xf(opcode, runtime_m68k_executor.MOVEM_FIELDS["dr"])  # 0=reg-to-mem, 1=mem-to-reg
    ea_mode = _xf(opcode, runtime_m68k_executor.MOVEM_FIELDS["mode"])
    ea_reg = _xf(opcode, runtime_m68k_executor.MOVEM_FIELDS["register"])

    # EA mode name from KB
    ea_enc = runtime_m68k_analysis.EA_MODE_ENCODING
    predec_enc = ea_enc["predec"]
    postinc_enc = ea_enc["postinc"]
    is_predec = (ea_mode == predec_enc[0])
    is_postinc = (ea_mode == postinc_enc[0])

    # Register order from KB movem_reg_masks
    masks = runtime_m68k_analysis.MOVEM_REG_MASKS
    reg_order = masks["predecrement"] if is_predec else masks["normal"]

    # Collect registers to transfer (bit N set -> reg_order[N])
    regs = []
    for bit in range(16):
        if reg_mask & (1 << bit):
            regs.append(reg_order[bit])

    if not regs:
        return

    size_bit = _xf(opcode, runtime_m68k_executor.MOVEM_FIELDS["size"])
    xfer_size = "l" if size_bit == 1 else "w"
    xfer_bytes = _SIZE_BYTE_COUNT[xfer_size]

    sp_reg = _SP_REG_NUM

    if direction == 0 and is_predec and ea_reg == sp_reg:
        # Register-to-memory via -(SP): push registers onto stack.
        # SP decrements BEFORE each transfer (predecrement mode).
        total_bytes = len(regs) * xfer_bytes
        for reg_name in regs:
            reg_info = _parse_reg_from_text(reg_name)
            if reg_info is None:
                continue
            # Decrement SP
            if cpu.sp.is_known:
                cpu.sp = _concrete(
                    (cpu.sp.concrete - xfer_bytes) & 0xFFFFFFFF)
            elif cpu.sp.is_symbolic:
                cpu.sp = cpu.sp.sym_add(-xfer_bytes)
            else:
                break
            # Write register value to memory at new SP
            val = cpu.get_reg(reg_info[0], reg_info[1])
            mem.write(cpu.sp, val, xfer_size)

    elif direction == 1 and is_postinc and ea_reg == sp_reg:
        # Memory-to-register via (SP)+: pop registers from stack.
        # SP increments AFTER each transfer (postincrement mode).
        for reg_name in regs:
            reg_info = _parse_reg_from_text(reg_name)
            if reg_info is None:
                continue
            # Read from current SP
            if cpu.sp.is_known:
                val = mem.read(cpu.sp.concrete, xfer_size)
            elif cpu.sp.is_symbolic:
                val = mem.read(cpu.sp, xfer_size)
            else:
                val = _unknown()
            cpu.set_reg(reg_info[0], reg_info[1], val)
            # Increment SP
            if cpu.sp.is_known:
                cpu.sp = _concrete(
                    (cpu.sp.concrete + xfer_bytes) & 0xFFFFFFFF)
            elif cpu.sp.is_symbolic:
                cpu.sp = cpu.sp.sym_add(xfer_bytes)

    else:
        # Non-stack MOVEM (e.g. to/from absolute address):
        # no SP effect, registers become unknown for loads.
        if direction == 1:
            for reg_name in regs:
                reg_info = _parse_reg_from_text(reg_name)
                if reg_info:
                    cpu.set_reg(reg_info[0], reg_info[1], _unknown())


def _apply_lea(d: DecodedOps, cpu: _CPUState) -> None:
    """Apply LEA: load effective address into An register."""
    src_op = d.ea_op
    addr_val: AbstractValue | None = None
    if src_op:
        # Compute the EA address from the decoded operand
        if src_op.mode == "pcdisp":
            assert src_op.value is not None
            addr_val = _concrete(src_op.value)
        elif src_op.mode == "pcindex":
            base_addr_val = src_op.value
            assert base_addr_val is not None
            idx_mode = "an" if src_op.index_is_addr else "dn"
            assert src_op.index_reg is not None
            idx_val = cpu.get_reg(idx_mode, src_op.index_reg)
            if idx_val.is_known:
                nbits = _SIZE_BYTE_COUNT[src_op.index_size] * 8
                mask = (1 << nbits) - 1
                iv = idx_val.concrete & mask
                if iv >= (1 << (nbits - 1)):
                    iv -= (1 << nbits)
                addr_val = _concrete(
                    (base_addr_val + iv) & 0xFFFFFFFF)
        elif src_op.mode == "disp":
            assert src_op.reg is not None
            assert src_op.value is not None
            base = cpu.a[src_op.reg]
            if base.is_known:
                addr_val = _concrete(
                    (base.concrete + src_op.value) & 0xFFFFFFFF)
            elif base.is_symbolic:
                addr_val = base.sym_add(src_op.value)
        elif src_op.mode == "ind":
            assert src_op.reg is not None
            addr_val = cpu.get_reg("an", src_op.reg)
        elif src_op.mode in ("absw", "absl"):
            assert src_op.value is not None
            addr_val = _concrete(src_op.value)
    # Write to destination An (from KB encoding)
    if d.reg_num is not None:
        cpu.set_reg("an", d.reg_num,
                    addr_val if addr_val else _unknown())


def _apply_pea(
    inst_kb: str,
    d: DecodedOps,
    cpu: _CPUState,
    mem: AbstractMemory,
) -> None:
    """Apply PEA: push effective address to stack."""
    assert d.ea_op is not None, f"{inst_kb}: missing EA operand for PEA"
    # Validate EA mode against KB-allowed modes (catches internal bugs)
    pea_ea_modes = runtime_m68k_analysis.EA_MODE_TABLES.get(inst_kb, ((), (), ()))[2]
    assert not pea_ea_modes or d.ea_op.mode in pea_ea_modes, (
        f"PEA: EA mode {d.ea_op.mode!r} not in allowed modes "
        f"{pea_ea_modes} (internal bug)"
    )
    # Compute the effective address (not the value at it)
    addr_val = resolve_ea(d.ea_op, cpu, "l")
    if addr_val is not None and (cpu.sp.is_known or cpu.sp.is_symbolic):
        # Write size from KB sp_effects decrement
        push_bytes = sum(
            nbytes
            for action, nbytes, _ in runtime_m68k_analysis.SP_EFFECTS[inst_kb]
            if action == runtime_m68k_analysis.SpEffectAction.DECREMENT and nbytes is not None
        )
        write_size = next(
            k for k, v in _SIZE_BYTE_COUNT.items()
            if v == push_bytes)
        mem.write(cpu.sp, addr_val, write_size)


def _apply_assign(
    d: DecodedOps,
    inst_kb: str,
    cpu: _CPUState,
    mem: AbstractMemory,
    size: str,
    size_bytes: int,
    platform: PlatformState | None,
) -> None:
    """Apply MOVE/MOVEA/MOVEQ/CLR family."""
    formula = runtime_m68k_analysis.COMPUTE_FORMULAS.get(inst_kb)
    terms = formula[1] if formula is not None else ()
    src_sign_ext = inst_kb in runtime_m68k_executor.SOURCE_SIGN_EXTEND
    mnemonic = inst_kb
    src_op = d.ea_op  # alias for assign handler

    if runtime_m68k_analysis.FormulaTerm.IMPLICIT in terms:
        # CLR: assign implicit_operand (0) to destination.
        implicit_val = runtime_m68k_executor.IMPLICIT_OPERANDS.get(mnemonic)
        assert implicit_val is not None, f"implicit_operand missing for {mnemonic}"
        write_op = d.dst_op if d.dst_op else src_op
        if write_op:
            _write_operand(write_op, cpu, mem,
                           _concrete(implicit_val), size, size_bytes)
        return

    # Source-assign: MOVE, MOVEA, MOVEQ.
    # Source from structured EA decode, or from decoded immediate
    # (MOVEQ has immediate in DATA field, not EA).
    if src_op:
        src_val = _resolve_operand(src_op, cpu, mem, size, size_bytes)
    elif d.imm_val is not None:
        src_val = _concrete(d.imm_val)
    else:
        src_val = None

    # Sign-extend immediate from KB constraints.immediate_range
    imm_range = runtime_m68k_executor.IMMEDIATE_RANGES.get(mnemonic)
    assert not (src_val and src_val.is_known and mnemonic == "MOVEQ" and imm_range is None), (
        "runtime KB missing immediate range for MOVEQ"
    )
    if imm_range and imm_range[2] and src_val and src_val.is_known:
        bits = imm_range[1]
        assert bits is not None, f"runtime KB immediate range for {mnemonic} missing bit width"
        val = src_val.concrete & ((1 << bits) - 1)
        if val >= (1 << (bits - 1)):
            val |= ~((1 << bits) - 1)
        val &= 0xFFFFFFFF
        src_val = _concrete(val)

    # Source sign-extension from KB source_sign_extend
    if src_sign_ext and size == "w" and src_val and src_val.is_known:
        w_bits = _SIZE_BYTE_COUNT["w"] * 8
        w_mask = (1 << w_bits) - 1
        val = src_val.concrete & w_mask
        if val >= (1 << (w_bits - 1)):
            val |= ~w_mask
        src_val = _concrete(val & 0xFFFFFFFF)

    # ExecBase load: MOVEA.L ($N).W,An -- source is absw
    # matching platform exec_base_addr.
    if (src_val is None and platform and src_op
            and src_op.mode == "absw"
            and src_op.value == platform.exec_base_addr):
        src_val = _unknown(tag=platform.exec_base_tag)

    # Write to destination.
    result = src_val if src_val is not None else _unknown()
    if d.dst_op:
        _write_operand(d.dst_op, cpu, mem, result, size, size_bytes)
    elif d.reg_num is not None:
        if src_sign_ext:
            cpu.set_reg("an", d.reg_num, result)
        else:
            cpu.set_reg("dn", d.reg_num, result)
    else:
        # Single REGISTER field (MOVEQ: Dn from bits 11-9).
        # The EA is the source (imm_val), the register is the dest.
        mnemonic = inst_kb
        try:
            rn = _xf(d.opcode, runtime_m68k_executor.DEST_REG_FIELD[mnemonic])
        except KeyError:
            if not d.ea_op:
                raise
        else:
            cpu.set_reg("dn", rn, result)
            return
        if d.ea_op:
            _write_operand(d.ea_op, cpu, mem, result,
                           size, size_bytes)


def _resolve_os_call(
    inst: Instruction,
    inst_kb: str,
    cpu: _CPUState,
    platform: PlatformState,
    code: bytes,
) -> CallEffect | None:
    """Resolve OS library call from instruction EA.

    Returns call_effect dict or None.
    """
    call_effect = None
    resolver = platform.os_call_resolver
    if resolver and len(inst.raw) >= _OPWORD_BYTES:
        lvo = None
        base_reg_num = platform.base_reg_num
        opcode = struct.unpack_from(">H", inst.raw, 0)[0]
        mnemonic = inst_kb
        opword_fields = runtime_m68k_executor.FIELD_MAPS[0].get(mnemonic)
        assert opword_fields is not None, f"runtime KB missing opword field map for {mnemonic}"
        if "MODE" not in opword_fields or "REGISTER" not in opword_fields:
            return None
        ea_mode = _xf(opcode, opword_fields["MODE"])
        ea_reg = _xf(opcode, opword_fields["REGISTER"])
        try:
            operand, _ = _decode_ea(
                inst.raw, _OPWORD_BYTES,
                ea_mode, ea_reg, "l", inst.offset)
        except ValueError:
            operand = None
        if operand:
            if (operand.mode == "disp"
                    and operand.reg == base_reg_num):
                lvo = operand.value
            elif (operand.mode == "index"
                  and operand.reg == base_reg_num):
                # LVO = displacement + index reg value
                idx_mode = ("an" if operand.index_is_addr
                            else "dn")
                assert operand.index_reg is not None
                idx_val = cpu.get_reg(
                    idx_mode, operand.index_reg)
                if idx_val.is_known:
                    assert operand.value is not None
                    idx_v = idx_val.concrete
                    if operand.index_size == "w":
                        idx_v = _to_signed(
                            idx_v & 0xFFFF, "w")
                    else:
                        idx_v = _to_signed(
                            idx_v & 0xFFFFFFFF, "l")
                    lvo = operand.value + idx_v
        a6_tag = cpu.a[base_reg_num].tag
        a6_lib = a6_tag.library_base if isinstance(a6_tag, LibraryBaseTag) else None
        if lvo is not None and a6_lib:
            call_effect = resolver(
                inst.offset, lvo, a6_lib, cpu, code,
                platform=platform)
    return call_effect


def _apply_sp_effects(
    inst: Instruction,
    inst_kb: str,
    d: DecodedOps,
    cpu: _CPUState,
    mem: AbstractMemory,
    mnemonic: str,
    platform: PlatformState | None,
    code: bytes,
) -> None:
    """Apply SP effects and OS call resolution (orthogonal to compute).

    Handles SP decrement/increment, displacement_adjust (LINK),
    call return address write, scratch reg invalidation, and OS
    call resolution.
    """
    flow_type = runtime_m68k_analysis.FLOW_TYPES[inst_kb]
    sp_effects = runtime_m68k_analysis.SP_EFFECTS.get(mnemonic)
    if not sp_effects:
        return

    def _address_effect_reg(aux: str | None) -> int:
        assert aux == "An", f"{mnemonic}: unsupported SP effect register target {aux!r}"
        assert d.reg_num is not None, f"{mnemonic}: missing decoded An register for SP effect"
        reg_num: int = d.reg_num
        return reg_num

    for effect in sp_effects:
        action, nbytes, _aux = effect
        if nbytes is None and action in (
            runtime_m68k_analysis.SpEffectAction.DECREMENT,
            runtime_m68k_analysis.SpEffectAction.INCREMENT,
        ):
            assert False, f"sp_effects.bytes missing for {mnemonic} action={action}"
        if action == runtime_m68k_analysis.SpEffectAction.DECREMENT:
            assert nbytes is not None
            if cpu.sp.is_known:
                cpu.sp = _concrete(cpu.sp.concrete - nbytes)
            elif cpu.sp.is_symbolic:
                cpu.sp = cpu.sp.sym_add(-nbytes)
        elif action == runtime_m68k_analysis.SpEffectAction.INCREMENT:
            assert nbytes is not None
            if cpu.sp.is_known:
                cpu.sp = _concrete(cpu.sp.concrete + nbytes)
            elif cpu.sp.is_symbolic:
                cpu.sp = cpu.sp.sym_add(nbytes)
        elif action == runtime_m68k_analysis.SpEffectAction.ADJUST:
            # LINK-style: SP += displacement (negative = allocate).
            # Displacement from extension word (KB immediate_range).
            disp_val = d.imm_val
            if disp_val is None and len(inst.raw) >= 4:
                disp_val = struct.unpack_from(
                    ">h", inst.raw, _OPWORD_BYTES)[0]
            if disp_val is not None:
                disp = _to_signed(disp_val & 0xFFFF, "w")
                if cpu.sp.is_known:
                    cpu.sp = _concrete(cpu.sp.concrete + disp)
                elif cpu.sp.is_symbolic:
                    cpu.sp = cpu.sp.sym_add(disp)
        elif action == runtime_m68k_analysis.SpEffectAction.STORE_REG_TO_STACK:
            reg_num = _address_effect_reg(_aux)
            assert nbytes is not None, f"sp_effects.bytes missing for {mnemonic} action={action}"
            if nbytes == 1:
                stack_size = "b"
            elif nbytes == 2:
                stack_size = "w"
            elif nbytes == 4:
                stack_size = "l"
            else:
                assert False, f"{mnemonic}: unsupported stack size {nbytes} for {action}"
            mem.write(cpu.sp, cpu.get_reg("an", reg_num), stack_size)
        elif action == runtime_m68k_analysis.SpEffectAction.SAVE_TO_REG:
            reg_num = _address_effect_reg(_aux)
            cpu.set_reg("an", reg_num, cpu.sp)
        elif action == runtime_m68k_analysis.SpEffectAction.LOAD_FROM_REG:
            reg_num = _address_effect_reg(_aux)
            cpu.sp = cpu.get_reg("an", reg_num)
        elif action == runtime_m68k_analysis.SpEffectAction.LOAD_FROM_STACK_TO_REG:
            reg_num = _address_effect_reg(_aux)
            assert nbytes is not None, f"sp_effects.bytes missing for {mnemonic} action={action}"
            if nbytes == 1:
                stack_size = "b"
            elif nbytes == 2:
                stack_size = "w"
            elif nbytes == 4:
                stack_size = "l"
            else:
                assert False, f"{mnemonic}: unsupported stack size {nbytes} for {action}"
            stack_val = mem.read(cpu.sp, stack_size)
            cpu.set_reg("an", reg_num, stack_val)

    # For call instructions (JSR/BSR), write the return address to
    # the stack.  The return address is the instruction immediately
    # after the call.  This enables RTS resolution and push/pop
    # patterns to work through abstract memory.
    if cpu.sp.is_known or cpu.sp.is_symbolic:
        if flow_type == _FLOW_CALL:
            return_addr = inst.offset + inst.size
            mem.write(cpu.sp, _concrete(return_addr), "l")

    # After call instructions, invalidate scratch registers per
    # platform calling convention.  Detect calls by KB pc_effects
    # flow type, not by SP decrement (PEA also decrements SP but
    # isn't a call).
    if platform and platform.scratch_regs:
        if flow_type == _FLOW_CALL:
            # Resolve call effects before invalidation (needs pre-call
            # register state for input registers like A1 name string).
            call_effect = _resolve_os_call(inst, inst_kb, cpu, platform,
                                           code)

            # Store call effect for propagate_states to apply
            # after scratch reg invalidation on the fallthrough.
            # Don't invalidate here -- the callee needs the
            # pre-call register state (e.g. D0 = LVO offset).
            if call_effect:
                platform.pending_call_effect = call_effect


def _apply_computed(
    d: DecodedOps,
    inst_kb: str,
    formula: ComputeFormula | None,
    cpu: _CPUState,
    mem: AbstractMemory,
    size: str,
    size_bytes: int,
    mask: int,
) -> None:
    """Apply any remaining compute_formula op via m68k_compute.

    Uses _compute_result to evaluate the KB formula with concrete operand
    values. Handles shift, rotate, multiply, divide, bit ops, BCD -- any
    op that _compute_result supports. If operands are unknown, invalidates
    the destination (conservative).

    The compute engine needs src (source operand value) and dst (destination
    operand value). For OPMODE instructions, ea_is_source determines which
    is which. For immediate+EA, imm is src and EA is dst.
    """
    from .m68k_compute import _compute_result

    bits = size_bytes * 8
    op = formula[0] if formula else None
    mnemonic = inst_kb
    op_type = runtime_m68k_executor.OPERATION_TYPES[mnemonic]
    src_sign_ext = mnemonic in runtime_m68k_executor.SOURCE_SIGN_EXTEND
    opword_fields = runtime_m68k_executor.FIELD_MAPS[0].get(mnemonic)
    assert opword_fields is not None, f"runtime KB missing opword field map for {mnemonic}"
    mode_fields_exist = "MODE" in opword_fields

    # Resolve source and destination values
    src_val = dst_val = None
    write_to_ea = True  # default: write result to EA operand

    if d.ea_op and d.reg_num is not None and d.ea_is_source is None and d.imm_val is None:
        # EA + Dn without OPMODE. Direction depends on instruction type:
        # - bit_test ops (BTST/BCHG/BCLR/BSET): Dn=bit_number(src), EA=data(dst)
        # - multiply (MULU/MULS): EA=multiplicand(src), Dn=multiplier(dst)
        if op_type == "bit_test":
            src_val = cpu.get_reg("dn", d.reg_num)
            dst_val = _resolve_operand(d.ea_op, cpu, mem, size, size_bytes)
            write_to_ea = True  # result writes back to EA
        else:
            src_val = _resolve_operand(d.ea_op, cpu, mem, size, size_bytes)
            dst_val = cpu.get_reg("dn", d.reg_num)
            write_to_ea = False  # result goes to reg
    elif d.ea_is_source is not None and d.ea_op and d.reg_num is not None:
        # OPMODE-directed (e.g. ADD <ea>,Dn or ADD Dn,<ea>)
        ea_val = _resolve_operand(d.ea_op, cpu, mem, size, size_bytes)
        reg_val = cpu.get_reg("dn", d.reg_num)
        if d.ea_is_source:
            src_val = ea_val
            dst_val = reg_val
            write_to_ea = False
        else:
            src_val = reg_val
            dst_val = ea_val
    elif d.imm_val is not None and d.ea_op:
        # Immediate + EA (e.g. BTST #n,Dn)
        src_val = _concrete(d.imm_val)
        dst_val = _resolve_operand(d.ea_op, cpu, mem, size, size_bytes)
    elif d.ea_op is None and d.reg_num is not None and not mode_fields_exist:
        # Two-REGISTER form (shift/rotate): upper REGISTER = count or
        # count register, lower REGISTER = destination Dn.
        # The i/r field distinguishes immediate count from register count.
        reg_fields = runtime_m68k_executor.REGISTER_FIELDS.get(mnemonic)
        if reg_fields and len(reg_fields) >= 2:
            dn = _xf(d.opcode, reg_fields[-1])
            if d.imm_val is not None:
                # Immediate count form (#count,Dn)
                src_val = _concrete(d.imm_val)
            else:
                # Register count form (Dm,Dn) -- count comes from Dm
                count_reg = d.reg_num  # upper REGISTER = count register
                src_val = cpu.get_reg("dn", count_reg)
            dst_val = cpu.get_reg("dn", dn)
            write_to_ea = False
            d.reg_num = dn  # result writes to destination Dn
    elif d.ea_op:
        # Single operand (e.g. memory shift ASL.W <ea>)
        if d.imm_val is not None:
            src_val = _concrete(d.imm_val)
        dst_val = _resolve_operand(d.ea_op, cpu, mem, size, size_bytes)

    # Need concrete values to compute
    src_concrete = src_val.concrete if src_val and src_val.is_known else None
    dst_concrete = dst_val.concrete if dst_val and dst_val.is_known else None

    # Some ops only need dst (single-operand: memory shifts, TAS)
    # Some ops need both src and dst (shift by count, multiply, bit ops)
    can_compute = False
    if op in ("bit_test", "bit_change", "bit_clear", "bit_set",
              "shift", "rotate", "rotate_extend",
              "multiply", "divide"):
        can_compute = (src_concrete is not None and dst_concrete is not None)
    elif op in ("add_decimal", "subtract_decimal"):
        can_compute = (src_concrete is not None and dst_concrete is not None)
    elif dst_concrete is not None:
        can_compute = True

    if can_compute and formula:
        src_c = src_concrete if src_concrete is not None else 0
        dst_c = dst_concrete if dst_concrete is not None else 0

        # Build context for the compute engine
        ctx: ComputeContext = {}

        # Bit modulus from KB (BTST/BCHG/BCLR/BSET)
        bit_mod = runtime_m68k_executor.BIT_MODULI.get(mnemonic)
        if bit_mod:
            # For register-direct EA: use "register" modulus
            if d.ea_op and d.ea_op.mode == "dn":
                ctx["bit_modulus"] = bit_mod[0]
            else:
                ctx["bit_modulus"] = bit_mod[1]

        # Shift/rotate count modulus from KB
        count_mod = runtime_m68k_executor.SHIFT_COUNT_MODULI.get(mnemonic)
        if count_mod:
            ctx["count_modulus"] = count_mod

        # Rotate extra bits from KB
        rotate_extra = runtime_m68k_executor.ROTATE_EXTRA_BITS.get(mnemonic)
        if rotate_extra:
            ctx["extra_bits"] = rotate_extra

        # Direction + fill from KB variants, selected by opcode dr field
        dir_variants = runtime_m68k_executor.DIRECTION_VARIANTS.get(mnemonic)
        if dir_variants:
            dr_val = _xf(d.opcode, runtime_m68k_executor.SHIFT_FIELDS[0])
            dr_values = runtime_m68k_executor.SHIFT_FIELDS[1]
            dr_char = dr_values[dr_val] if 0 <= dr_val < len(dr_values) else None
            for _variant, direction, fill, _arithmetic in runtime_m68k_executor.SHIFT_VARIANT_BEHAVIORS.get(mnemonic, ()):
                if direction.value[0] == dr_char:
                    direction_char = direction.value[0].upper()
                    assert direction_char in ("L", "R"), (
                        f"Unexpected shift direction {direction_char!r} for {mnemonic}"
                    )
                    ctx["direction"] = cast(Literal["L", "R"], direction_char)
                    ctx["fill"] = fill.value
                    break

        # Multiply/divide: data_sizes + signed from KB forms
        if op in ("multiply", "divide"):
            ds = runtime_m68k_executor.PRIMARY_DATA_SIZES.get(inst_kb)
            if ds:
                ctx["data_sizes"] = ds
            if mnemonic in runtime_m68k_executor.SIGNED_RESULTS:
                ctx["signed"] = runtime_m68k_executor.SIGNED_RESULTS[mnemonic]

        # CCR for extend operations
        initial_ccr: KnownCcrState = {}

        try:
            result_full, result = _compute_result(
                inst_kb, src_c, dst_c, mask, bits, initial_ccr, ctx)
        except (RuntimeError, KeyError, ZeroDivisionError):
            # Compute failed (e.g. division by zero) -- invalidate
            result = None

        if result is not None:
            # For bit_test: no write (only CC flags affected)
            if op == "bit_test":
                return
            # Apply size masking: preserve upper bits for sub-long ops
            if size != "l" and dst_concrete is not None:
                result = (dst_c & ~mask) | (result & mask)
            result_val = _concrete(result & 0xFFFFFFFF)
            if write_to_ea and d.ea_op:
                _write_operand(d.ea_op, cpu, mem, result_val,
                               size, size_bytes)
            elif d.reg_num is not None:
                cpu.set_reg("dn", d.reg_num, result_val)
            return

    # Could not compute -- invalidate destination
    if write_to_ea and d.ea_op:
        _write_operand(d.ea_op, cpu, mem, _unknown(), size, size_bytes)
    elif d.reg_num is not None:
        cpu.set_reg("dn", d.reg_num, _unknown())
    elif d.ea_op:
        _write_operand(d.ea_op, cpu, mem, _unknown(), size, size_bytes)


def _apply_instruction(inst: Instruction, inst_kb: str,
                       cpu: _CPUState, mem: AbstractMemory,
                       code: bytes, base_addr: int,
                       platform: PlatformState | None = None) -> None:
    """Apply one instruction's effects to the abstract state.

    Dispatches on KB compute_formula.op and operation_type -- not mnemonics.
    Sign-extension widths, bit ranges, and implicit operands all come from KB.
    LEA is the one exception: it resolves the EA address (not value) and has
    no KB field to distinguish this from MOVE, so it is detected by its unique
    operation text signature.

    If platform is provided (from OS KB calling_convention), scratch registers
    are invalidated after call instructions.
    """
    assert inst.kb_mnemonic, f"Instruction at ${inst.offset:06x} is missing kb_mnemonic"
    mnemonic = inst.kb_mnemonic
    flow_type = runtime_m68k_analysis.FLOW_TYPES[mnemonic]
    size = inst.operand_size
    assert size is not None or flow_type in (_FLOW_BRANCH, _FLOW_JUMP, _FLOW_RETURN, _FLOW_CALL, _FLOW_TRAP), (
        f"Instruction at ${inst.offset:06x} is missing operand_size"
    )
    if size in _SIZE_BYTE_COUNT:
        size_bytes = _SIZE_BYTE_COUNT[size]
    elif flow_type in (_FLOW_BRANCH, _FLOW_JUMP, _FLOW_RETURN, _FLOW_CALL, _FLOW_TRAP):
        size_bytes = _SIZE_BYTE_COUNT["w"]
    else:
        assert False, f"runtime KB missing size byte count for {size!r}"
    assert size is not None
    mask = (1 << (size_bytes * 8)) - 1

    formula = runtime_m68k_analysis.COMPUTE_FORMULAS.get(mnemonic)
    op = formula[0] if formula else None
    op_type = runtime_m68k_executor.OPERATION_TYPES[mnemonic]

    d = decode_instruction_ops(inst, mnemonic, size)

    # SP effects (orthogonal to compute)
    _apply_sp_effects(inst, mnemonic, d, cpu, mem, mnemonic, platform,
                      code)

    # Flow-control stops here
    if flow_type in (_FLOW_BRANCH, _FLOW_JUMP, _FLOW_RETURN, _FLOW_CALL, _FLOW_TRAP):
        return
    if (
        op_type is not None
        and op_type not in (
            runtime_m68k_executor.OperationType.BOUNDS_CHECK,
            runtime_m68k_executor.OperationType.SWAP,
            runtime_m68k_executor.OperationType.CCR_OP,
            runtime_m68k_executor.OperationType.SR_OP,
        )
        and formula is None
    ):
        if mnemonic in runtime_m68k_analysis.SP_EFFECTS_COMPLETE:
            return
        formula = runtime_m68k_analysis.COMPUTE_FORMULAS[mnemonic]
        op = formula[0]
    if op_type == runtime_m68k_executor.OperationType.BOUNDS_CHECK:
        runtime_m68k_executor.BOUNDS_CHECKS[mnemonic]
        return
    if op is None and op_type != runtime_m68k_executor.OperationType.SWAP:
        return

    # Special handlers by operation_class
    op_class = runtime_m68k_executor.OPERATION_CLASSES[mnemonic]
    if op_class == runtime_m68k_executor.OperationClass.MULTI_REGISTER_TRANSFER:
        _apply_movem(inst, mnemonic, d, cpu, mem)
        return
    if op_class == runtime_m68k_executor.OperationClass.LOAD_EFFECTIVE_ADDRESS and op == runtime_m68k_analysis.ComputeOp.ASSIGN:
        _apply_lea(d, cpu)
        return

    # PEA detection
    if runtime_m68k_analysis.SP_EFFECTS.get(mnemonic) and op_type == runtime_m68k_executor.OperationType.SUB and d.ea_op:
        _apply_pea(mnemonic, d, cpu, mem)
        return

    # NEG: subtract with implicit operand (0 - dst), separate from table
    if op == runtime_m68k_analysis.ComputeOp.SUBTRACT and runtime_m68k_analysis.FormulaTerm.IMPLICIT in (formula[1] if formula else ()):
        _apply_neg(d, mnemonic, cpu, mem, size, size_bytes, mask)
        return

    # Binary ops (add, subtract, and, or, xor)
    if op in _BINARY_OPS:
        _apply_binary_op(_BINARY_OPS[op], d, mnemonic, cpu, mem, size,
                         size_bytes, op_type)
        return

    # Remaining handlers
    if op == runtime_m68k_analysis.ComputeOp.ASSIGN:
        _apply_assign(d, mnemonic, cpu, mem, size, size_bytes, platform)
        return
    if op == runtime_m68k_analysis.ComputeOp.BITWISE_COMPLEMENT:
        _apply_complement(d, cpu, mem, size, size_bytes, mask)
        return
    if op == runtime_m68k_analysis.ComputeOp.EXCHANGE:
        _apply_swap(d, mnemonic, cast(ComputeFormula, formula), cpu)
        return
    if op == runtime_m68k_analysis.ComputeOp.SIGN_EXTEND:
        _apply_sign_extend(d, mnemonic, cast(ComputeFormula, formula), cpu, mnemonic, size)
        return
    if op == runtime_m68k_analysis.ComputeOp.TEST:
        return  # CC only, no state change
    if op_type == runtime_m68k_executor.OperationType.SWAP and op is None:
        _apply_exg(d, mnemonic, cpu)
        return

    # KB-driven compute fallback: use m68k_compute._compute_result for
    # all remaining ops (shift, rotate, multiply, divide, bit ops, BCD).
    # If both operands are concrete, compute the result; otherwise invalidate.
    _apply_computed(d, mnemonic, cast(ComputeFormula | None, formula), cpu, mem, size, size_bytes, mask)


def propagate_states(blocks: dict[int, BasicBlock],
                     code: bytes, base_addr: int = 0,
                     initial_state: _CPUState | None = None,
                     initial_mem: AbstractMemory | None = None,
                     platform: PlatformState | None = None,
                     summaries: Mapping[int, CallSummary | None] | None = None,
                     ) -> dict[int, StatePair]:
    """Propagate abstract state through basic blocks.

    Seeds all entry points (base_addr + blocks marked is_entry) with
    initial state, then walks forward via BFS.  At merge points, joins
    states conservatively.

    Call fallthroughs use subroutine summaries (SP delta + register
    preservation) when available.  Caller state is also propagated into
    callees for concrete execution (resolves memory reads like library
    base loads).  If a summary clobbers the app base register and the
    platform has a discovered base value, the base register is restored
    (the init routine sets it - its summary reports it as clobbered).

    Returns dict mapping block_start -> (exit_cpu_state, exit_memory).
    """
    if initial_state is None:
        initial_state = CPUState()
        if platform:
            # Set initial SP as symbolic base for abstract stack tracking.
            # SP_entry+0 at entry; push gives SP_entry-4, pop gives SP_entry+0.
            # Symbolic SP survives joins (same base+offset -> keep).
            initial_state.sp = _symbolic("SP_entry", 0)
            # Set initial base register if discovered from prior pass
            base_info = platform.app_base
            if base_info:
                initial_state.set_reg(
                    "an", base_info.reg_num, _concrete(base_info.concrete))
    if initial_mem is None:
        # Use init-discovered memory if available (base-region contents
        # from the init routine, e.g. library bases stored at d(An))
        if platform and platform.initial_mem is not None:
            initial_mem = platform.initial_mem.copy()
        else:
            initial_mem = AbstractMemory()
    # Enable code-section reads: when a concrete address within the code
    # range is read but not in tracked memory, fall back to the code bytes.
    # This resolves indirect calls through data pointers, function tables,
    # and dispatch structures without format-specific parsers.
    initial_mem._code_section = code

    # Map block_start -> {source_key: (cpu_state, memory)}
    # Keyed by source so each predecessor overwrites its previous
    # contribution instead of accumulating across fixpoint iterations.
    incoming: dict[int, IncomingStates] = {}
    # Map block_start -> (exit_cpu_state, exit_memory) after execution
    exit_states: dict[int, StatePair] = {}
    last_incoming_sig: dict[int, frozenset[tuple[object, int, int]]] = {}

    # Seed all entry points with initial state.  The primary entry
    # (base_addr) always gets seeded.  Additional entry points (from
    # jump table targets, resolved indirect jumps, etc.) are also
    # seeded so they produce exit states even when the control flow
    # path from base_addr to them is unresolved.
    seed_addrs = []
    if base_addr in blocks:
        seed_addrs.append(base_addr)
    # Additional entry points from the blocks' is_entry flag
    for addr, blk in blocks.items():
        if blk.is_entry and addr != base_addr and addr in blocks:
            seed_addrs.append(addr)
    for addr in seed_addrs:
        if addr not in incoming:
            incoming[addr] = {-1: (initial_state.copy(),
                                  initial_mem.copy())}

    work = deque(seed_addrs)
    visited = set()
    iterations = 0
    max_iterations = len(blocks) * 10  # convergence guard

    while work and iterations < max_iterations:
        iterations += 1
        addr = work.popleft()
        if addr not in blocks:
            continue

        block = blocks[addr]
        pred_dict = incoming.get(addr)
        if not pred_dict:
            continue
        incoming_sig = _incoming_state_signature(pred_dict)
        if addr in visited and last_incoming_sig.get(addr) == incoming_sig:
            continue
        pred_states = list(pred_dict.values())

        # Join incoming states.  Pass init_mem so the join uses init
        # values as defaults for bytes a predecessor never touched,
        # without overriding explicit writes (even unknown ones).
        p_init_mem = platform.initial_mem if platform else None
        cpu, mem = _join_states(pred_states, init_mem=p_init_mem)
        cpu.pc = addr

        # Restore app base register if merge killed it.
        # The base register is set once in init and never legitimately
        # changes to a different value. A conservative join may lose it
        # when one predecessor clobbered it (e.g. after a call that
        # used it for ExecBase). Restoring it here is safe and enables
        # library call resolution downstream.
        if platform:
            base_info = platform.app_base
            if base_info:
                if not cpu.a[base_info.reg_num].is_known:
                    cpu.set_reg("an", base_info.reg_num, _concrete(base_info.concrete))

        # Fixpoint check: skip if state unchanged from last visit.
        if addr in visited and addr in exit_states:
            prev_cpu, _ = exit_states[addr]
            if (cpu.d == prev_cpu.d and cpu.a == prev_cpu.a
                    and cpu.sp == prev_cpu.sp):
                last_incoming_sig[addr] = incoming_sig
                continue

        visited.add(addr)

        # Execute all instructions in the block
        for inst in block.instructions:
            ikb = instruction_kb(inst)
            _apply_instruction(inst, ikb, cpu, mem, code, base_addr,
                               platform)
            cpu.pc = inst.offset + inst.size

        exit_cpu = cpu.copy()
        exit_mem = mem.copy()
        exit_states[addr] = (exit_cpu, exit_mem)
        last_incoming_sig[addr] = incoming_sig

        # Propagate to successors.
        # For call fallthroughs, adjust SP to account for the callee's
        # return popping the return address that JSR/BSR pushed.
        call_sp_push = 0
        if block.instructions:
            last = block.instructions[-1]
            last_ikb = instruction_kb(last)
            if runtime_m68k_analysis.FLOW_TYPES[last_ikb] == _FLOW_CALL:
                for action, nbytes, _ in runtime_m68k_analysis.SP_EFFECTS.get(last_ikb, ()):
                    if action == runtime_m68k_analysis.SpEffectAction.DECREMENT:
                        if nbytes is not None:
                            call_sp_push += nbytes

        # Classify xrefs
        call_dst = ft_dst = None
        other_xrefs = []
        for xref in block.xrefs:
            if xref.type == "call":
                call_dst = xref.dst
            elif xref.type == "fallthrough":
                ft_dst = xref.dst
            else:
                other_xrefs.append(xref)

        if call_sp_push and ft_dst:
            summary = summaries.get(call_dst) if summaries and call_dst is not None else None
            ft_cpu = _call_fallthrough_state(
                exit_cpu, call_sp_push, summary, platform)
            incoming.setdefault(ft_dst, {})[addr] = \
                (ft_cpu, exit_mem)
            work.append(ft_dst)
            # Propagate into callee with pre-call state (callee
            # receives the caller's registers as input).
            if call_dst:
                incoming.setdefault(call_dst, {})[addr] = \
                    (exit_cpu, exit_mem)
                work.append(call_dst)
        elif ft_dst:
            incoming.setdefault(ft_dst, {})[addr] = \
                (exit_cpu, exit_mem)
            work.append(ft_dst)

        for xref in other_xrefs:
            incoming.setdefault(xref.dst, {})[addr] = \
                (exit_cpu, exit_mem)
            work.append(xref.dst)

    return exit_states


# -- Subroutine summaries -------------------------------------------------

def _compute_sub_blocks(blocks: dict[int, BasicBlock],
                        call_targets: set[int]) -> dict[int, set[int]]:
    """Map each subroutine entry to the set of block addresses it owns.

    A block belongs to a subroutine if reachable from its entry via
    successors without crossing another subroutine's entry.
    """
    result = {}
    for entry in call_targets:
        if entry not in blocks:
            continue
        owned = set()
        work = [entry]
        while work:
            a = work.pop()
            if a in owned or a not in blocks:
                continue
            if a != entry and a in call_targets:
                continue
            owned.add(a)
            for s in blocks[a].successors:
                work.append(s)
        result[entry] = owned
    return result


def _compute_summary(entry: int, owned: set[int],
                     blocks: dict[int, BasicBlock],
                     summaries: dict[int, CallSummary | None],
                     code: bytes, base_addr: int,
                     platform: PlatformState | None = None,
                     global_exit_states: dict[int, StatePair] | None = None,
                     ) -> CallSummary | None:
    """Compute a subroutine summary by analyzing with symbolic inputs.

    Each register gets a unique symbolic value (D0_entry, A0_entry,
    SP_entry).  At RTS, registers whose symbolic value survived are
    preserved; others are clobbered.  No platform config - summaries
    track register preservation, not concrete OS call effects.

    Returns a typed call summary or None.
    """
    entry_cpu = CPUState()
    for i in range(len(entry_cpu.d)):
        entry_cpu.d[i] = _symbolic(f"D{i}_entry", 0)
    for i in range(len(entry_cpu.a)):
        entry_cpu.a[i] = _symbolic(f"A{i}_entry", 0)
    entry_cpu.sp = _symbolic("SP_entry", 0)

    incoming: dict[int, IncomingStates] = {entry: {-1: (entry_cpu.copy(), AbstractMemory())}}
    exit_states: dict[int, StatePair] = {}
    last_incoming_sig: dict[int, frozenset[tuple[int, int, int]]] = {}
    work = deque([entry])
    visited = set()

    for _ in range(len(owned) * 3):
        if not work:
            break
        addr = work.popleft()
        if addr not in owned or addr not in blocks:
            continue
        pred_dict = incoming.get(addr)
        if not pred_dict:
            continue
        incoming_sig = _incoming_state_signature(pred_dict)
        if addr in visited and last_incoming_sig.get(addr) == incoming_sig:
            continue

        cpu, mem = _join_states(list(pred_dict.values()))
        cpu.pc = addr

        if addr in visited and addr in exit_states:
            prev_cpu, _ = exit_states[addr]
            if (cpu.d == prev_cpu.d and cpu.a == prev_cpu.a
                    and cpu.sp == prev_cpu.sp):
                last_incoming_sig[addr] = incoming_sig
                continue
        visited.add(addr)

        block = blocks[addr]
        for inst in block.instructions:
            ikb = instruction_kb(inst)
            _apply_instruction(inst, ikb, cpu, mem, code, base_addr,
                               platform)
            cpu.pc = inst.offset + inst.size
        exit_cpu = cpu.copy()
        exit_mem = mem.copy()
        exit_states[addr] = (exit_cpu, exit_mem)
        last_incoming_sig[addr] = incoming_sig
        if global_exit_states is not None:
            global_exit_states[addr] = exit_states[addr]

        # Propagate to successors within the subroutine
        call_sp_push = 0
        if block.instructions:
            last = block.instructions[-1]
            last_ikb = instruction_kb(last)
            if runtime_m68k_analysis.FLOW_TYPES[last_ikb] == _FLOW_CALL:
                for action, nbytes, _ in runtime_m68k_analysis.SP_EFFECTS.get(last_ikb, ()):
                    if action == runtime_m68k_analysis.SpEffectAction.DECREMENT:
                        if nbytes is not None:
                            call_sp_push += nbytes

        call_dst = ft_dst = None
        other_xrefs = []
        for xref in block.xrefs:
            if xref.type == "call":
                call_dst = xref.dst
            elif xref.type == "fallthrough":
                ft_dst = xref.dst
            else:
                other_xrefs.append(xref)

        if call_sp_push and ft_dst and ft_dst in owned:
            nested = summaries.get(call_dst) if call_dst is not None else None
            ft_cpu = _call_fallthrough_state(
                exit_cpu, call_sp_push, nested, platform)
            incoming.setdefault(ft_dst, {})[addr] = \
                (ft_cpu, exit_mem)
            work.append(ft_dst)
        elif ft_dst and ft_dst in owned:
            incoming.setdefault(ft_dst, {})[addr] = \
                (exit_cpu, exit_mem)
            work.append(ft_dst)

        for xref in other_xrefs:
            if xref.dst in owned:
                incoming.setdefault(xref.dst, {})[addr] = \
                    (exit_cpu, exit_mem)
                work.append(xref.dst)

    # Collect RTS exit states
    rts_states = []
    for addr in owned:
        blk = blocks.get(addr)
        if not blk or not blk.instructions:
            continue
        last = blk.instructions[-1]
        ikb = instruction_kb(last)
        if runtime_m68k_analysis.FLOW_TYPES[ikb] == _FLOW_RETURN and addr in exit_states:
            rts_states.append(exit_states[addr])

    if not rts_states:
        return None

    rts_cpu, _ = _join_states(rts_states)

    preserved_d = frozenset(
        i for i in range(len(rts_cpu.d))
        if rts_cpu.d[i].sym_base == f"D{i}_entry"
        and rts_cpu.d[i].sym_offset == 0
    )
    preserved_a = frozenset(
        i for i in range(len(rts_cpu.a))
        if rts_cpu.a[i].sym_base == f"A{i}_entry"
        and rts_cpu.a[i].sym_offset == 0
    )
    # Produced values: registers that are concrete at all RTS exits
    # regardless of input.  These are constants the sub always computes
    # (e.g. LEA target(pc),a0 - always returns the same address).
    # Input-dependent results show as symbolic (Dn_entry + offset) or
    # unknown, not concrete - so this is sound.
    produced_d = []
    produced_d_tags = []
    for i in range(len(rts_cpu.d)):
        if i not in preserved_d and rts_cpu.d[i].is_known:
            produced_d.append((i, rts_cpu.d[i].concrete))
        if i not in preserved_d and rts_cpu.d[i].tag is not None:
            produced_d_tags.append((i, rts_cpu.d[i].tag))
    produced_a = []
    produced_a_tags = []
    for i in range(len(rts_cpu.a)):
        if i not in preserved_a and rts_cpu.a[i].is_known:
            produced_a.append((i, rts_cpu.a[i].concrete))
        if i not in preserved_a and rts_cpu.a[i].tag is not None:
            produced_a_tags.append((i, rts_cpu.a[i].tag))
    sp_delta = 0
    if rts_cpu.sp.is_symbolic and rts_cpu.sp.sym_base == "SP_entry":
        assert rts_cpu.sp.sym_offset is not None
        sp_delta = rts_cpu.sp.sym_offset

    return CallSummary(
        preserved_d=preserved_d,
        preserved_a=preserved_a,
        produced_d=tuple(produced_d),
        produced_d_tags=tuple(produced_d_tags),
        produced_a=tuple(produced_a),
        produced_a_tags=tuple(produced_a_tags),
        sp_delta=sp_delta,
    )


def _apply_summary(caller_cpu: _CPUState,
                   summary: CallSummary) -> _CPUState:
    """Apply a subroutine summary to a caller's state.

    Preserved registers keep the caller's value.
    Produced registers get the callee's concrete return value.
    Everything else becomes unknown.  SP adjusted by delta.
    """
    result = CPUState()
    produced_d = dict(summary.produced_d)
    produced_d_tags = dict(summary.produced_d_tags)
    produced_a = dict(summary.produced_a)
    produced_a_tags = dict(summary.produced_a_tags)
    for i in range(len(result.d)):
        if i in summary.preserved_d:
            result.d[i] = caller_cpu.d[i]
        elif i in produced_d:
            result.d[i] = _concrete(produced_d[i], tag=produced_d_tags.get(i))
        elif i in produced_d_tags:
            result.d[i] = _unknown(tag=produced_d_tags[i])
        else:
            result.d[i] = _unknown()
    for i in range(len(result.a)):
        if i in summary.preserved_a:
            result.a[i] = caller_cpu.a[i]
        elif i in produced_a:
            result.a[i] = _concrete(produced_a[i], tag=produced_a_tags.get(i))
        elif i in produced_a_tags:
            result.a[i] = _unknown(tag=produced_a_tags[i])
        else:
            result.a[i] = _unknown()
    delta = summary.sp_delta
    if caller_cpu.sp.is_symbolic:
        result.sp = caller_cpu.sp.sym_add(delta)
    elif caller_cpu.sp.is_known:
        result.sp = _concrete(
            (caller_cpu.sp.concrete + delta) & 0xFFFFFFFF)
    return result


def _summary_known_regs(summary: CallSummary | None) -> tuple[set[int], set[int]]:
    if summary is None:
        return set(), set()
    known_d = set(summary.preserved_d)
    known_d.update(reg_num for reg_num, _ in summary.produced_d)
    known_d.update(reg_num for reg_num, _ in summary.produced_d_tags)
    known_a = set(summary.preserved_a)
    known_a.update(reg_num for reg_num, _ in summary.produced_a)
    known_a.update(reg_num for reg_num, _ in summary.produced_a_tags)
    return known_d, known_a


def _apply_pending_call_effect(ft_cpu: _CPUState, platform: PlatformState | None) -> None:
    if platform is None:
        return
    call_effect = platform.pending_call_effect
    platform.pending_call_effect = None
    if call_effect is None:
        return
    if isinstance(call_effect, BaseRegisterCallEffect):
        reg = _parse_reg_from_text(call_effect.base_reg)
        if reg is None:
            return
        mode, num = reg
        ft_cpu.set_reg(mode, num, _unknown(tag=call_effect.tag))
    elif isinstance(call_effect, MemoryAllocationCallEffect):
        reg = _parse_reg_from_text(call_effect.result_reg)
        if reg is None:
            return
        mode, num = reg
        ft_cpu.set_reg(mode, num, _concrete(call_effect.concrete))
    elif isinstance(call_effect, OutputRegisterCallEffect):
        reg = _parse_reg_from_text(call_effect.output_reg)
        if reg is None:
            return
        mode, num = reg
        ft_cpu.set_reg(
            mode,
            num,
            _unknown(tag=OsResultTag(
                os_type=call_effect.output_type.os_type,
                os_result=call_effect.output_type.os_result,
                call=call_effect.output_type.call,
                library=call_effect.output_type.library,
            )),
        )


def _call_fallthrough_state(exit_cpu: _CPUState,
                            call_sp_push: int,
                            summary: CallSummary | None,
                            platform: PlatformState | None) -> _CPUState:
    if summary:
        ft_cpu = _apply_summary(exit_cpu, summary)
        base_info = platform.app_base if platform else None
        if base_info:
            if not ft_cpu.a[base_info.reg_num].is_known:
                ft_cpu.set_reg("an", base_info.reg_num, _concrete(base_info.concrete))
    else:
        ft_cpu = exit_cpu.copy()
        if exit_cpu.sp.is_known:
            ft_cpu.sp = _concrete(
                (exit_cpu.sp.concrete + call_sp_push) & 0xFFFFFFFF)
        elif exit_cpu.sp.is_symbolic:
            ft_cpu.sp = exit_cpu.sp.sym_add(call_sp_push)

    if platform and platform.scratch_regs:
        known_d, known_a = _summary_known_regs(summary)
        for reg_mode, reg_num in platform.scratch_regs:
            if reg_mode == "dn" and reg_num in known_d:
                continue
            if reg_mode == "an" and reg_num in known_a:
                continue
            ft_cpu.set_reg(reg_mode, reg_num, _unknown())

    _apply_pending_call_effect(ft_cpu, platform)
    return ft_cpu


def compute_all_summaries(blocks: dict[int, BasicBlock],
                          code: bytes, base_addr: int,
                          existing: dict[int, CallSummary | None] | None = None,
                          platform: PlatformState | None = None,
                          global_exit_states: dict[int, StatePair] | None = None,
                          ) -> dict[int, CallSummary | None]:
    """Pre-compute summaries for all subroutines in topological order.

    Leaf subroutines (no calls) are computed first, then their callers
    can use the leaf summaries for nested call handling.

    If existing cache is provided, only computes summaries for entries
    not already in the cache.
    """
    call_targets = set()
    for blk in blocks.values():
        for xref in blk.xrefs:
            if xref.type == "call":
                call_targets.add(xref.dst)

    sub_map = _compute_sub_blocks(blocks, call_targets)
    summaries = dict(existing) if existing else {}

    # Skip entries already cached
    needed = {e for e in sub_map if e not in summaries}
    if not needed:
        return summaries

    # Build call graph for topological ordering (only needed entries)
    callees: dict[int, set[int]] = {}
    for entry in needed:
        calls = set()
        for addr in sub_map[entry]:
            block = blocks.get(addr)
            if block is None:
                continue
            for xref in block.xrefs:
                if xref.type == "call" and xref.dst in sub_map:
                    calls.add(xref.dst)
        callees[entry] = calls

    # Topological sort - count only UN-summarized callees
    in_degree = {}
    callers: dict[int, set[int]] = {e: set() for e in needed}
    for entry in needed:
        deg = sum(1 for c in callees[entry]
                  if c in needed and c not in summaries)
        in_degree[entry] = deg
        for c in callees[entry]:
            if c in callers:
                callers[c].add(entry)

    ready = [e for e, d in in_degree.items() if d == 0]

    while ready:
        entry = ready.pop()
        summaries[entry] = _compute_summary(
            entry, sub_map[entry], blocks, summaries, code,
            base_addr, platform, global_exit_states)
        for caller in callers.get(entry, set()):
            if caller in in_degree:
                in_degree[caller] -= 1
                if in_degree[caller] == 0:
                    ready.append(caller)

    # Cycles: compute with partial summaries
    for entry in needed:
        if entry not in summaries:
            summaries[entry] = _compute_summary(
                entry, sub_map[entry], blocks, summaries, code,
                base_addr, platform, global_exit_states)

    return summaries


# -- Public API ------------------------------------------------------------

def analyze(code: bytes, base_addr: int = 0,
            entry_points: list[int] | None = None,
            propagate: bool = False,
            platform: PlatformState | None = None) -> AnalysisResult:
    """Analyze code and return structured results.

    Args:
        code: raw code bytes
        base_addr: base address of the code section
        entry_points: list of entry point addresses (default: [base_addr])
        propagate: if True, run state propagation to track register values
        platform: optional platform config from OS KB (calling convention)

    Returns dict with:
        blocks: dict[int, BasicBlock] -- basic blocks keyed by start address
        xrefs: list[XRef] -- all cross-references
        call_targets: set[int] -- addresses that are call targets (subroutines)
        branch_targets: set[int] -- addresses that are branch targets
        exit_states: dict[int, (CPUState, AbstractMemory)] -- per-block exit
            states (only if propagate=True)
    """
    blocks = discover_blocks(code, base_addr, entry_points)

    all_xrefs = []
    call_targets = set()
    branch_targets = set()

    for block in blocks.values():
        for xref in block.xrefs:
            all_xrefs.append(xref)
            if xref.type == "call":
                call_targets.add(xref.dst)
            elif xref.type in ("branch", "jump"):
                branch_targets.add(xref.dst)

    result: AnalysisResult = {
        "blocks": blocks,
        "xrefs": all_xrefs,
        "call_targets": call_targets,
        "branch_targets": branch_targets,
    }

    if propagate:
        # Pre-compute subroutine summaries for SP delta + register
        # preservation on call fallthroughs.
        sums = None
        if platform:
            existing = platform.summary_cache
            platform.summary_cache = compute_all_summaries(
                blocks, code, base_addr, existing=existing, platform=platform)
            sums = platform.summary_cache
        result["exit_states"] = propagate_states(
            blocks, code, base_addr, platform=platform,
            summaries=sums)

    return result


# -- CLI -------------------------------------------------------------------

if __name__ == "__main__":
    from .hunk_parser import parse_file, HunkType as HT

    do_propagate = "--propagate" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if len(args) < 1:
        print(f"Usage: {sys.argv[0]} [--propagate] <hunk_file>")
        sys.exit(1)

    hf = parse_file(args[0])
    for hunk in hf.hunks:
        if hunk.hunk_type != HT.HUNK_CODE:
            continue
        print(f"; === Hunk #{hunk.index} CODE ({len(hunk.data)} bytes) ===")
        result = analyze(hunk.data, propagate=do_propagate)
        blocks = result["blocks"]
        exit_states = result.get("exit_states", {})

        print(f"; {len(blocks)} basic blocks, "
              f"{len(result['call_targets'])} call targets, "
              f"{len(result['branch_targets'])} branch targets")
        print()

        for addr in sorted(blocks):
            block = blocks[addr]
            flags = []
            if block.is_entry:
                flags.append("ENTRY")
            if block.is_return:
                flags.append("RETURN")
            pred_str = ", ".join(f"${p:06x}" for p in block.predecessors)
            succ_str = ", ".join(f"${s:06x}" for s in block.successors)
            print(f"; --- Block ${addr:06x} [{' '.join(flags)}] "
                  f"pred=[{pred_str}] succ=[{succ_str}] ---")
            for inst in block.instructions:
                hex_bytes = " ".join(f"{b:02x}" for b in inst.raw[:8])
                print(f"  {inst.offset:06x}: {hex_bytes:24s} {inst.text}")
            for xref in block.xrefs:
                cond = " (cond)" if xref.conditional else ""
                print(f"  ; xref: {xref.type}{cond} -> ${xref.dst:06x}")
            if addr in exit_states:
                cpu, mem = exit_states[addr]
                known_regs = []
                for i, v in enumerate(cpu.d):
                    if v.is_known:
                        known_regs.append(f"D{i}=${v.concrete:08x}")
                for i, v in enumerate(cpu.a):
                    if v.is_known:
                        known_regs.append(f"A{i}=${v.concrete:08x}")
                if cpu.sp.is_known:
                    known_regs.append(f"SP=${cpu.sp.concrete:08x}")
                if known_regs:
                    print(f"  ; state: {', '.join(known_regs)}")
                mem_ranges = mem.known_ranges()
                if mem_ranges:
                    print(f"  ; mem: {len(mem_ranges)} known ranges")
            print()

