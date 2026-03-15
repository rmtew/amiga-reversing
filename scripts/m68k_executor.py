"""KB-driven M68K symbolic executor — static analysis via abstract interpretation.

Walks disassembled code, maintaining an abstract register/memory state.
All instruction semantics are derived from the KB (m68k_instructions.json)
via the compute engine (m68k_compute.py). No hardcoded M68K knowledge.

Usage:
    from m68k_executor import Executor
    exe = Executor(code_bytes, base_addr=0x1000)
    blocks = exe.discover_blocks()
"""

import json
import struct
import sys
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from m68k_compute import _to_signed
from m68k_disasm import disassemble, Instruction, DecodeError, _Decoder, _decode_one


# ── KB loader ─────────────────────────────────────────────────────────────

_KB_CACHE = {}

def _load_kb():
    if _KB_CACHE:
        return _KB_CACHE["by_name"], _KB_CACHE["list"], _KB_CACHE["meta"]
    path = Path(__file__).resolve().parent.parent / "knowledge" / "m68k_instructions.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    instructions = data.get("instructions", [])
    meta = data.get("_meta", {})
    by_name = {inst["mnemonic"]: inst for inst in instructions}

    # Build CC family lookup from KB cc_parameterized fields.
    # Each cc-parameterized instruction (Bcc, Scc, DBcc, etc.) has
    # constraints.cc_parameterized.prefix that maps mnemonic prefixes
    # to the KB entry name.
    cc_families = {}  # prefix -> kb_mnemonic
    for inst in instructions:
        cc_param = inst.get("constraints", {}).get("cc_parameterized")
        if cc_param:
            cc_families[cc_param["prefix"].lower()] = inst["mnemonic"]
    meta["_cc_families"] = cc_families

    # Derive register layout from movem_reg_masks: count of data and address
    # registers, and which address register number maps to SP.
    reg_masks = meta.get("movem_reg_masks", {}).get("normal", [])
    data_regs = [r for r in reg_masks if r.startswith("d")]
    addr_regs = [r for r in reg_masks if r.startswith("a")]
    meta["_num_data_regs"] = len(data_regs)
    meta["_num_addr_regs"] = len(addr_regs)
    # SP register number: highest address register (a7 -> 7)
    if not addr_regs:
        raise KeyError("KB movem_reg_masks has no address registers")
    meta["_sp_reg_num"] = int(addr_regs[-1][1:])

    _KB_CACHE["by_name"] = by_name
    _KB_CACHE["list"] = instructions
    _KB_CACHE["meta"] = meta
    return by_name, instructions, meta


# ── Structured operand representation ─────────────────────────────────────

@dataclass
class Operand:
    """Structured operand decoded from opcode bits."""
    mode: str          # EA mode name from KB: "dn", "an", "ind", "postinc", etc.
    reg: int | None    # register number (0-7) for modes that use one
    value: int | None  # immediate value, displacement, or absolute address
    index_reg: int | None = None      # index register number
    index_is_addr: bool = False       # True if index is An, False if Dn
    index_size: str = "w"             # "w" or "l" for index register
    size: str | None = None           # operand size for immediates


# ── Operand decoder ───────────────────────────────────────────────────────

def _decode_ea(data: bytes, pos: int, mode: int, reg: int,
               op_size: str, pc_offset: int) -> tuple[Operand, int]:
    """Decode an effective address from opcode bits + extension words.

    Returns (Operand, new_pos) where new_pos accounts for consumed extension words.
    Uses KB ea_mode_encoding to map (mode, reg) to mode name.
    """
    _, _, meta = _load_kb()
    ea_enc = meta["ea_mode_encoding"]
    # Reverse lookup: find mode name from (mode, reg) in KB ea_mode_encoding.
    # KB entries have [mode, null] for modes that don't use register sub-select,
    # and [mode, reg] for those that do. Try specific (mode, reg) first, then
    # (mode, null) — this matches the KB structure without hardcoding the
    # mode-7 boundary.
    mode_name = None
    for name, (m, r) in ea_enc.items():
        if m == mode and r == reg:
            mode_name = name
            break
    if mode_name is None:
        for name, (m, r) in ea_enc.items():
            if m == mode and r is None:
                mode_name = name
                break
    if mode_name is None:
        raise ValueError(f"Unknown EA mode={mode} reg={reg}")

    if mode_name == "dn":
        return Operand(mode="dn", reg=reg, value=None), pos
    elif mode_name == "an":
        return Operand(mode="an", reg=reg, value=None), pos
    elif mode_name == "ind":
        return Operand(mode="ind", reg=reg, value=None), pos
    elif mode_name == "postinc":
        return Operand(mode="postinc", reg=reg, value=None), pos
    elif mode_name == "predec":
        return Operand(mode="predec", reg=reg, value=None), pos
    elif mode_name == "disp":
        if pos + 2 > len(data):
            raise ValueError("Truncated displacement extension word")
        disp = struct.unpack_from(">h", data, pos)[0]
        return Operand(mode="disp", reg=reg, value=disp), pos + 2
    elif mode_name == "index":
        if pos + 2 > len(data):
            raise ValueError("Truncated index extension word")
        ext = struct.unpack_from(">H", data, pos)[0]
        # Brief extension word layout from KB ea_brief_ext_word
        brief = meta["ea_brief_ext_word"]
        bf = {f["name"]: (f["bit_hi"], f["bit_lo"], f["bit_hi"] - f["bit_lo"] + 1)
              for f in brief}
        xreg = _xf(ext, bf["REGISTER"])
        xtype_bit = _xf(ext, bf["D/A"])
        xsize_bit = _xf(ext, bf["W/L"])
        disp_raw = _xf(ext, bf["DISPLACEMENT"])
        disp_width = bf["DISPLACEMENT"][2]
        if disp_raw & (1 << (disp_width - 1)):
            disp_raw -= (1 << disp_width)
        return Operand(
            mode="index", reg=reg, value=disp_raw,
            index_reg=xreg, index_is_addr=(xtype_bit == 1),
            index_size="l" if xsize_bit == 1 else "w"
        ), pos + 2
    elif mode_name == "absw":
        if pos + 2 > len(data):
            raise ValueError("Truncated abs.w extension word")
        addr = struct.unpack_from(">h", data, pos)[0]
        # Sign-extend to 32 bits (abs.w is sign-extended)
        addr &= 0xFFFFFFFF
        return Operand(mode="absw", reg=None, value=addr), pos + 2
    elif mode_name == "absl":
        if pos + 4 > len(data):
            raise ValueError("Truncated abs.l extension words")
        addr = struct.unpack_from(">I", data, pos)[0]
        return Operand(mode="absl", reg=None, value=addr), pos + 4
    elif mode_name == "pcdisp":
        if pos + 2 > len(data):
            raise ValueError("Truncated PC displacement")
        disp = struct.unpack_from(">h", data, pos)[0]
        # PC-relative: target = PC + displacement (PC = instruction addr + opword)
        opword_bytes = meta["opword_bytes"]
        target = pc_offset + opword_bytes + disp
        return Operand(mode="pcdisp", reg=None, value=target), pos + 2
    elif mode_name == "pcindex":
        if pos + 2 > len(data):
            raise ValueError("Truncated PC index extension word")
        ext = struct.unpack_from(">H", data, pos)[0]
        brief = meta["ea_brief_ext_word"]
        bf = {f["name"]: (f["bit_hi"], f["bit_lo"], f["bit_hi"] - f["bit_lo"] + 1)
              for f in brief}
        xreg = _xf(ext, bf["REGISTER"])
        xtype_bit = _xf(ext, bf["D/A"])
        xsize_bit = _xf(ext, bf["W/L"])
        disp_raw = _xf(ext, bf["DISPLACEMENT"])
        disp_width = bf["DISPLACEMENT"][2]
        if disp_raw & (1 << (disp_width - 1)):
            disp_raw -= (1 << disp_width)
        # Value stores PC-relative base (instruction addr + opword + displacement)
        opword_bytes = meta["opword_bytes"]
        target = pc_offset + opword_bytes + disp_raw
        return Operand(
            mode="pcindex", reg=None, value=target,
            index_reg=xreg, index_is_addr=(xtype_bit == 1),
            index_size="l" if xsize_bit == 1 else "w"
        ), pos + 2
    elif mode_name == "imm":
        size_bytes = meta["size_byte_count"]
        nbytes = size_bytes.get(op_size, 2)
        if nbytes <= 2:
            if pos + 2 > len(data):
                raise ValueError("Truncated immediate extension word")
            imm = struct.unpack_from(">H", data, pos)[0]
            if op_size == "b":
                imm &= 0xFF
            return Operand(mode="imm", reg=None, value=imm, size=op_size), pos + 2
        else:
            if pos + 4 > len(data):
                raise ValueError("Truncated immediate long extension")
            imm = struct.unpack_from(">I", data, pos)[0]
            return Operand(mode="imm", reg=None, value=imm, size=op_size), pos + 4
    else:
        raise ValueError(f"Unhandled EA mode name '{mode_name}'")


def _xf(word: int, field_spec: tuple) -> int:
    """Extract field from word given (bit_hi, bit_lo, width)."""
    bit_hi, bit_lo, width = field_spec
    return (word >> bit_lo) & ((1 << width) - 1)


def _resolve_operand(operand: Operand, cpu, mem, size: str,
                     size_bytes: int) -> "AbstractValue | None":
    """Read the value at a decoded EA operand.

    For postincrement/predecrement, also adjusts the register.
    Uses get_reg/set_reg for proper SP aliasing.
    Returns None if the operand can't be resolved.
    """
    if operand.mode == "dn":
        return cpu.get_reg("dn", operand.reg)
    if operand.mode == "an":
        return cpu.get_reg("an", operand.reg)
    if operand.mode == "imm":
        return _concrete(operand.value)
    if operand.mode == "ind":
        addr = cpu.get_reg("an", operand.reg)
        if addr.is_known:
            return mem.read(addr.concrete, size)
        if addr.is_symbolic:
            return mem.read(addr, size)
        return None
    if operand.mode == "postinc":
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
        base = cpu.get_reg("an", operand.reg)
        if not base.is_known:
            return None
        idx_mode = "an" if operand.index_is_addr else "dn"
        idx_val = cpu.get_reg(idx_mode, operand.index_reg)
        if not idx_val.is_known:
            return None
        _, _, meta = _load_kb()
        nbits = meta["size_byte_count"][operand.index_size] * 8
        mask = (1 << nbits) - 1
        idx_v = idx_val.concrete & mask
        if idx_v >= (1 << (nbits - 1)):
            idx_v -= (1 << nbits)
        ea = (base.concrete + operand.value + idx_v) & 0xFFFFFFFF
        return mem.read(ea, size)
    return None


def _write_operand(operand: Operand, cpu, mem, value,
                   size: str, size_bytes: int):
    """Write a value to a decoded EA operand.

    For predecrement/postincrement, also adjusts the register.
    Uses get_reg/set_reg for proper SP aliasing.
    """
    if operand.mode == "dn":
        cpu.set_reg("dn", operand.reg, value)
    elif operand.mode == "an":
        cpu.set_reg("an", operand.reg, value)
    elif operand.mode == "ind":
        addr = cpu.get_reg("an", operand.reg)
        if addr.is_known:
            mem.write(addr.concrete, value, size)
        elif addr.is_symbolic:
            mem.write(addr, value, size)
    elif operand.mode == "predec":
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
        addr = cpu.get_reg("an", operand.reg)
        if addr.is_known:
            mem.write(addr.concrete, value, size)
            cpu.set_reg("an", operand.reg, _concrete(
                (addr.concrete + size_bytes) & 0xFFFFFFFF))
        elif addr.is_symbolic:
            mem.write(addr, value, size)
            cpu.set_reg("an", operand.reg, addr.sym_add(size_bytes))
    elif operand.mode == "disp":
        addr = cpu.get_reg("an", operand.reg)
        if addr.is_known:
            mem.write(
                (addr.concrete + operand.value) & 0xFFFFFFFF,
                value, size)
        elif addr.is_symbolic:
            mem.write(addr.sym_add(operand.value), value, size)


# ── Abstract state ────────────────────────────────────────────────────────

class AbstractValue:
    """A value that may be concrete, symbolic (base+offset), or unknown.

    Concrete: known 32-bit value.
    Symbolic: base name + integer offset (e.g., SP_entry-4).
    Unknown: neither concrete nor symbolic.

    Uses __slots__ for performance (millions of instances).
    """
    __slots__ = ("concrete", "sym_base", "sym_offset", "label", "tag")

    def __init__(self, concrete=None, sym_base=None, sym_offset=None,
                 label=None, tag=None):
        self.concrete = concrete
        self.sym_base = sym_base
        self.sym_offset = sym_offset
        self.label = label
        self.tag = tag

    @property
    def is_known(self) -> bool:
        return self.concrete is not None

    @property
    def is_symbolic(self) -> bool:
        return self.sym_base is not None

    def sym_add(self, delta: int) -> "AbstractValue":
        """Return a new symbolic value with adjusted offset."""
        return AbstractValue(sym_base=self.sym_base,
                             sym_offset=self.sym_offset + delta,
                             tag=self.tag)

    def __repr__(self):
        if self.concrete is not None:
            return f"${self.concrete:08x}"
        if self.sym_base is not None:
            off = self.sym_offset
            if off == 0:
                return self.sym_base
            return f"{self.sym_base}{off:+d}"
        return f"?{self.label or ''}"

    def __eq__(self, other):
        if not isinstance(other, AbstractValue):
            return NotImplemented
        return (self.concrete == other.concrete
                and self.sym_base == other.sym_base
                and self.sym_offset == other.sym_offset
                and self.tag == other.tag)

    def __hash__(self):
        return hash((self.concrete, self.sym_base, self.sym_offset))


# Pre-allocated singleton for the common case
_UNKNOWN = AbstractValue()


def _concrete(val: int, tag: dict | None = None) -> AbstractValue:
    return AbstractValue(concrete=val & 0xFFFFFFFF, tag=tag)


def _symbolic(base: str, offset: int = 0,
              tag: dict | None = None) -> AbstractValue:
    return AbstractValue(sym_base=base, sym_offset=offset, tag=tag)


def _unknown(label: str = "", tag: dict | None = None) -> AbstractValue:
    if not label and tag is None:
        return _UNKNOWN
    return AbstractValue(label=label, tag=tag)


def _make_cpu_state_class():
    """Build CPUState class with register layout derived from KB."""
    _, _, meta = _load_kb()
    num_d = meta["_num_data_regs"]
    num_a = meta["_num_addr_regs"]
    sp_reg = meta["_sp_reg_num"]
    ccr_flags = list(meta["ccr_bit_positions"].keys())

    _default_d = [_UNKNOWN] * num_d
    _default_a = [_UNKNOWN] * num_a
    _default_ccr = {f: None for f in ccr_flags}

    class CPUState:
        """Abstract CPU state for symbolic execution.

        Register layout derived from KB movem_reg_masks and ccr_bit_positions.
        Uses __slots__ for performance (thousands of instances).
        """
        __slots__ = ("d", "a", "sp", "pc", "ccr")

        def __init__(self):
            self.d = list(_default_d)
            self.a = list(_default_a)
            self.sp = _UNKNOWN
            self.pc = 0
            self.ccr = dict(_default_ccr)

        def get_reg(self, mode: str, reg: int) -> AbstractValue:
            if mode == "dn":
                return self.d[reg]
            if mode == "an":
                return self.sp if reg == sp_reg else self.a[reg]
            raise ValueError(f"get_reg: unsupported mode '{mode}'")

        def set_reg(self, mode: str, reg: int, val: AbstractValue):
            if mode == "dn":
                self.d[reg] = val
            elif mode == "an":
                if reg == sp_reg:
                    self.sp = val
                else:
                    self.a[reg] = val
            else:
                raise ValueError(f"set_reg: unsupported mode '{mode}'")

        def copy(self) -> "CPUState":
            s = CPUState.__new__(CPUState)
            s.d = list(self.d)
            s.a = list(self.a)
            s.sp = self.sp
            s.pc = self.pc
            s.ccr = dict(self.ccr)
            return s

    return CPUState

# Defer construction until first use (KB must be loaded first)
_CPUState = None

def _get_cpu_state_class():
    global _CPUState
    if _CPUState is None:
        _CPUState = _make_cpu_state_class()
    return _CPUState

def CPUState(*args, **kwargs):
    """Create a CPUState instance (register layout from KB)."""
    cls = _get_cpu_state_class()
    return cls(*args, **kwargs)


# ── EA resolution ─────────────────────────────────────────────────────────

def resolve_ea(operand: Operand, state: CPUState,
               size: str) -> AbstractValue | None:
    """Resolve an EA operand to its effective address or value.

    For register-direct modes, returns the register value.
    For memory modes, returns the memory address (not the value at that address).
    For immediate mode, returns the immediate value.
    Returns None if the address cannot be determined.
    """
    if operand.mode == "dn":
        return state.get_reg("dn", operand.reg)
    elif operand.mode == "an":
        return state.get_reg("an", operand.reg)
    elif operand.mode == "ind":
        return state.get_reg("an", operand.reg)
    elif operand.mode in ("postinc", "predec"):
        base = state.get_reg("an", operand.reg)
        return base  # address before inc/dec adjustment
    elif operand.mode == "disp":
        base = state.get_reg("an", operand.reg)
        if base.is_known:
            return _concrete(base.concrete + operand.value)
        return None
    elif operand.mode == "index":
        base = state.get_reg("an", operand.reg)
        idx = state.get_reg("an" if operand.index_is_addr else "dn", operand.index_reg)
        if base.is_known and idx.is_known:
            idx_val = idx.concrete
            if operand.index_size == "w":
                idx_val = _to_signed(idx_val & 0xFFFF, "w")
                idx_val &= 0xFFFFFFFF
            return _concrete(base.concrete + idx_val + operand.value)
        return None
    elif operand.mode == "absw":
        return _concrete(operand.value)
    elif operand.mode == "absl":
        return _concrete(operand.value)
    elif operand.mode == "pcdisp":
        return _concrete(operand.value)  # already resolved to absolute target
    elif operand.mode == "pcindex":
        # Base target is resolved, but index register adds to it
        idx = state.get_reg("an" if operand.index_is_addr else "dn", operand.index_reg)
        if idx.is_known:
            idx_val = idx.concrete
            if operand.index_size == "w":
                idx_val = _to_signed(idx_val & 0xFFFF, "w")
                idx_val &= 0xFFFFFFFF
            return _concrete(operand.value + idx_val)
        return None
    elif operand.mode == "imm":
        return _concrete(operand.value)
    return None


# ── PC prediction ─────────────────────────────────────────────────────────

def predict_pc(inst_kb: dict, pc: int, instr_size: int,
               displacement: int | None, ccr: dict,
               dn_val: int | None = None) -> list[int]:
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
    _, _, meta = _load_kb()
    opword_bytes = meta["opword_bytes"]
    pc_effects = inst_kb.get("pc_effects", {})
    flow = pc_effects.get("flow", {})
    flow_type = flow.get("type", "sequential")
    conditional = flow.get("conditional", False)
    next_seq = pc + instr_size

    if flow_type == "sequential":
        return [next_seq]

    if flow_type in ("branch", "jump", "call"):
        if displacement is not None:
            # Branches are relative to PC + opword_bytes (KB _meta.opword_bytes)
            target = pc + opword_bytes + displacement
        else:
            target = None  # jump through register — unknown target

        if not conditional:
            if target is not None:
                return [target]
            return []  # unknown target (JMP (An))

        # Conditional: both taken and not-taken paths
        targets = [next_seq]
        if target is not None:
            targets.append(target)
        return targets

    if flow_type == "return":
        return []  # unknown — return address on stack

    if flow_type == "trap":
        return []  # exception vector

    print(f"WARNING: predict_pc: unhandled flow_type '{flow_type}' "
          f"for {inst_kb['mnemonic']} at ${pc:06x}", file=sys.stderr)
    return [next_seq]


# ── Cross-reference tracking ─────────────────────────────────────────────

@dataclass
class XRef:
    """A cross-reference from one address to another."""
    src: int           # source instruction address
    dst: int           # target address
    type: str          # "branch", "jump", "call", "data_read", "data_write"
    conditional: bool = False


# ── Basic block ───────────────────────────────────────────────────────────

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


# ── Block discovery ───────────────────────────────────────────────────────

def discover_blocks(code: bytes, base_addr: int = 0,
                    entry_points: list[int] | None = None) -> dict[int, BasicBlock]:
    """Discover basic blocks by following control flow from entry points.

    Returns dict mapping block start address -> BasicBlock.
    Uses KB pc_effects to determine control flow at block boundaries.
    """
    kb_by_name, _, meta = _load_kb()
    cc_test_defs = meta.get("cc_test_definitions", {})
    cc_aliases = meta.get("cc_aliases", {})

    if entry_points is None:
        entry_points = [base_addr]

    # Demand-driven disassembly: decode instructions as we follow flow,
    # rather than disassembling the entire code section upfront.
    # This handles mixed code/data sections where linear disassembly fails.
    instr_map = {}  # addr -> Instruction (cache)

    def _disasm_at(addr):
        """Disassemble one instruction at addr, caching the result."""
        if addr in instr_map:
            return instr_map[addr]
        offset = addr - base_addr
        _, _, m = _load_kb()
        if offset < 0 or offset + m["opword_bytes"] > len(code):
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
    # We only record block_starts here — edges are derived in pass 2.
    block_starts = set(entry_points)
    work = list(entry_points)
    visited = set()

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
            mnemonic = _extract_mnemonic(inst.text)
            inst_kb = _find_kb_entry(kb_by_name, mnemonic, cc_test_defs, cc_aliases)

            if inst_kb is None:
                break

            flow = inst_kb.get("pc_effects", {}).get("flow", {})
            flow_type = flow.get("type", "sequential")
            conditional = flow.get("conditional", False)

            if flow_type == "sequential":
                pc = next_seq
                if next_seq in block_starts and next_seq != addr:
                    break
                continue

            if flow_type in ("branch", "jump", "call"):
                target = _extract_branch_target(inst, pc)
                if target is not None:
                    block_starts.add(target)
                    if target not in visited:
                        work.append(target)
                if conditional or flow_type == "call":
                    block_starts.add(next_seq)
                    if next_seq not in visited:
                        work.append(next_seq)
                break

            break  # return, trap, etc.

    # Pass 2: Build blocks and derive edges from each block's last instruction.
    sorted_starts = sorted(block_starts)
    blocks = {}

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
            mnemonic = _extract_mnemonic(inst.text)
            inst_kb = _find_kb_entry(kb_by_name, mnemonic, cc_test_defs, cc_aliases)
            if inst_kb:
                ft = inst_kb.get("pc_effects", {}).get("flow", {}).get("type", "sequential")
                if ft != "sequential":
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
        last_mn = _extract_mnemonic(last_inst.text)
        last_kb = _find_kb_entry(kb_by_name, last_mn, cc_test_defs, cc_aliases)
        if last_kb:
            flow = last_kb.get("pc_effects", {}).get("flow", {})
            flow_type = flow.get("type", "sequential")
            conditional = flow.get("conditional", False)

            if flow_type == "sequential":
                # Fallthrough to next block
                if end in block_starts:
                    block.successors.append(end)
                    block.xrefs.append(XRef(
                        src=last_inst.offset, dst=end,
                        type="fallthrough", conditional=False))

            elif flow_type in ("branch", "jump", "call"):
                target = _extract_branch_target(last_inst, last_inst.offset)
                if target is not None:
                    block.successors.append(target)
                    block.xrefs.append(XRef(
                        src=last_inst.offset, dst=target,
                        type=flow_type, conditional=conditional))
                if conditional or flow_type == "call":
                    block.successors.append(end)
                    block.xrefs.append(XRef(
                        src=last_inst.offset, dst=end,
                        type="fallthrough", conditional=False))

            elif flow_type == "return":
                block.is_return = True

        blocks[start] = block

    # Fill in predecessors
    for addr, block in blocks.items():
        for succ in block.successors:
            if succ in blocks:
                if addr not in blocks[succ].predecessors:
                    blocks[succ].predecessors.append(addr)

    return blocks


# ── Helpers ───────────────────────────────────────────────────────────────

def _extract_mnemonic(text: str) -> str:
    """Extract mnemonic from disassembled instruction text.

    Handles: 'add.l d0,d1' -> 'add'
             'moveq #$0,d0' -> 'moveq'
             'bra.w $1234' -> 'bra'
    Size suffixes derived from KB size_byte_count keys + short branch "s".
    """
    _, _, meta = _load_kb()
    # Size suffixes from KB (includes short branch ".s")
    size_suffixes = ["." + s for s in meta["size_suffixes"]]
    # Split on first space to get mnemonic+suffix
    parts = text.strip().split(None, 1)
    if not parts:
        return ""
    mn_part = parts[0]
    # Strip size suffix
    for suffix in size_suffixes:
        if mn_part.endswith(suffix):
            return mn_part[:-len(suffix)]
    return mn_part


def _find_kb_entry(kb_by_name: dict, mnemonic: str,
                   cc_test_defs: dict, cc_aliases: dict) -> dict | None:
    """Find KB entry for a mnemonic, handling condition code families.

    CC families (Bcc, Scc, DBcc, etc.) are discovered from KB
    cc_parameterized fields, not hardcoded.
    """
    _, _, meta = _load_kb()
    cc_families = meta["_cc_families"]  # {prefix: kb_mnemonic}
    mn_upper = mnemonic.upper()

    # Direct lookup
    if mn_upper in kb_by_name:
        return kb_by_name[mn_upper]

    # Check condition code families from KB cc_parameterized.
    # Sort by prefix length descending so "db" matches before "b".
    for prefix in sorted(cc_families, key=len, reverse=True):
        prefix_upper = prefix.upper()
        if mn_upper.startswith(prefix_upper) and len(mn_upper) > len(prefix_upper):
            cc_part = mn_upper[len(prefix_upper):].lower()
            kb_name = cc_families[prefix]
            # Check if it's a known condition code or alias
            if cc_part in cc_test_defs or cc_part in cc_aliases:
                return kb_by_name.get(kb_name)

    # Combined mnemonics: "ASL, ASR" -> match on "ASL" or "ASR"
    for kb_mn, inst in kb_by_name.items():
        if "," in kb_mn:
            parts = [p.strip() for p in kb_mn.split(",")]
            if mn_upper in parts:
                return inst

    # KB entries with spaces: try prefix matching for MOVE variants
    for kb_mn in kb_by_name:
        if kb_mn.startswith(mn_upper + " ") or kb_mn.startswith(mn_upper + ","):
            return kb_by_name[kb_mn]

    return None


def _extract_branch_target(inst: Instruction, pc: int) -> int | None:
    """Extract branch/jump target address from instruction.

    For PC-relative branches: target = PC + opword_bytes + displacement.
    For JMP/JSR with absolute address: extract from extension words.
    For JMP/JSR (An): target is unknown (returns None).

    Displacement encoding rules (word_signal, long_signal) from KB.
    EA field positions (MODE, REGISTER) from KB encoding fields.
    """
    kb_by_name, _, meta = _load_kb()
    opword_bytes = meta["opword_bytes"]
    ea_enc = meta["ea_mode_encoding"]

    text = inst.text.strip()
    raw = inst.raw
    mnemonic = _extract_mnemonic(text)

    # Look up KB entry to get flow type and displacement_encoding
    cc_test_defs = meta.get("cc_test_definitions", {})
    cc_aliases = meta.get("cc_aliases", {})
    inst_kb = _find_kb_entry(kb_by_name, mnemonic, cc_test_defs, cc_aliases)
    if inst_kb is None:
        return None

    flow = inst_kb.get("pc_effects", {}).get("flow", {})
    flow_type = flow.get("type", "sequential")

    # Check if this instruction uses displacement encoding (Bcc, BRA, BSR, DBcc).
    # The KB distinguishes branch vs call vs jump at the flow level, but the
    # displacement mechanics are shared — determined by displacement_encoding
    # and multi-word encoding presence in the KB.
    disp_enc = inst_kb.get("constraints", {}).get("displacement_encoding")
    encodings = inst_kb.get("encodings", [])
    has_multiword_disp = len(encodings) > 1

    if disp_enc or has_multiword_disp:
        opcode = struct.unpack_from(">H", raw, 0)[0]

        if has_multiword_disp:
            # Multi-word encoding: displacement is in the second word
            # (e.g. DBcc has 16-bit displacement in word 2)
            disp_field = encodings[1].get("fields", [{}])[0]
            disp_width = disp_field.get("width", 16)
            if len(raw) >= opword_bytes + (disp_width // 8):
                if disp_width == 16:
                    disp = struct.unpack_from(">h", raw, opword_bytes)[0]
                else:
                    disp = struct.unpack_from(">i", raw, opword_bytes)[0]
                return pc + opword_bytes + disp
            return None

        if disp_enc:
            # Single-word branch with 8-bit displacement or extension
            disp_field_name = disp_enc["field"]
            # Find the field in the encoding
            for f in encodings[0].get("fields", []):
                if f["name"] == disp_field_name:
                    disp8 = _xf(opcode, (f["bit_hi"], f["bit_lo"],
                                         f["bit_hi"] - f["bit_lo"] + 1))
                    break
            else:
                return None

            word_signal = disp_enc["word_signal"]
            long_signal = disp_enc["long_signal"]
            word_bits = disp_enc["word_bits"]
            long_bits = disp_enc["long_bits"]

            if disp8 == word_signal:
                # Word displacement in extension
                ext_bytes = word_bits // 8
                if len(raw) >= opword_bytes + ext_bytes:
                    disp = struct.unpack_from(">h", raw, opword_bytes)[0]
                    return pc + opword_bytes + disp
            elif disp8 == long_signal:
                # Long displacement in extension (020+)
                ext_bytes = long_bits // 8
                if len(raw) >= opword_bytes + ext_bytes:
                    disp = struct.unpack_from(">i", raw, opword_bytes)[0]
                    return pc + opword_bytes + disp
            else:
                # 8-bit displacement (sign-extend from displacement field width)
                disp_bits = encodings[0]["fields"][-1]["width"]  # last field = displacement
                if disp8 >= (1 << (disp_bits - 1)):
                    disp8 -= (1 << disp_bits)
                return pc + opword_bytes + disp8

    elif flow_type in ("jump", "call"):
        # Extract MODE and REGISTER from KB encoding fields
        encodings = inst_kb.get("encodings", [])
        if not encodings:
            return None
        fields = encodings[0].get("fields", [])
        mode_field = None
        reg_field = None
        for f in fields:
            if f["name"] == "MODE":
                mode_field = f
            elif f["name"] == "REGISTER":
                reg_field = f
        if mode_field is None or reg_field is None:
            return None

        opcode = struct.unpack_from(">H", raw, 0)[0]
        mode = _xf(opcode, (mode_field["bit_hi"], mode_field["bit_lo"],
                            mode_field["bit_hi"] - mode_field["bit_lo"] + 1))
        reg = _xf(opcode, (reg_field["bit_hi"], reg_field["bit_lo"],
                           reg_field["bit_hi"] - reg_field["bit_lo"] + 1))

        # Use EA mode encoding from KB to determine addressing mode
        absw_enc = ea_enc["absw"]
        absl_enc = ea_enc["absl"]
        pcdisp_enc = ea_enc["pcdisp"]

        if mode == absw_enc[0] and reg == absw_enc[1]:
            if len(raw) >= opword_bytes + 2:
                addr = struct.unpack_from(">h", raw, opword_bytes)[0]
                return addr & 0xFFFFFFFF
        elif mode == absl_enc[0] and reg == absl_enc[1]:
            if len(raw) >= opword_bytes + 4:
                return struct.unpack_from(">I", raw, opword_bytes)[0]
        elif mode == pcdisp_enc[0] and reg == pcdisp_enc[1]:
            if len(raw) >= opword_bytes + 2:
                disp = struct.unpack_from(">h", raw, opword_bytes)[0]
                return pc + opword_bytes + disp
        # (An), d(An), etc. — target depends on register value
        return None

    return None


# ── Abstract memory ──────────────────────────────────────────────────────

class AbstractMemory:
    """Sparse memory map tracking concrete and symbolic values.

    Two stores: concrete (addr: int → byte values) and symbolic
    (base+offset keys → full values).  Concrete store handles normal
    memory; symbolic store handles SP-relative push/pop where the
    actual address is unknown but the base+offset is tracked.

    Reads/writes at byte, word, and long sizes.  Byte order is
    big-endian (M68K native).
    """

    def __init__(self):
        self._bytes: dict[int, AbstractValue] = {}  # concrete addr -> byte
        self._tags: dict[tuple, dict] = {}  # (addr, nbytes) -> tag dict
        # Symbolic store: (base_name, offset, nbytes) -> AbstractValue
        self._sym: dict[tuple, AbstractValue] = {}

    def write(self, addr, value: AbstractValue, size: str):
        """Write a value.  addr is int (concrete) or AbstractValue (symbolic)."""
        _, _, meta = _load_kb()
        nbytes = meta["size_byte_count"][size]

        if isinstance(addr, AbstractValue):
            if addr.is_symbolic:
                key = (addr.sym_base, addr.sym_offset, nbytes)
                self._sym[key] = value
                return
            if addr.is_known:
                addr = addr.concrete
            else:
                return  # unknown address — can't store

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

    def read(self, addr, size: str) -> AbstractValue:
        """Read a value.  addr is int (concrete) or AbstractValue (symbolic)."""
        _, _, meta = _load_kb()
        nbytes = meta["size_byte_count"][size]

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
                tag = self._tags.get((addr, nbytes))
                return _unknown(tag=tag)
            result = (result << 8) | (bv.concrete & 0xFF)
        tag = self._tags.get((addr, nbytes))
        return _concrete(result, tag=tag)

    def copy(self) -> "AbstractMemory":
        """Create an independent copy."""
        m = AbstractMemory()
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


# ── State propagation ────────────────────────────────────────────────────

def _join_values(a: AbstractValue, b: AbstractValue) -> AbstractValue:
    """Join two abstract values at a merge point.

    Concrete: both concrete and equal → keep.
    Symbolic: both symbolic with same base and offset → keep.
    Otherwise: unknown.  Tag preserved if both agree.
    """
    # Fast path: identical objects (common when sharing references)
    if a is b:
        return a
    tag = a.tag if a.tag is not None and a.tag == b.tag else None
    if a.concrete is not None and a.concrete == b.concrete:
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


def _join_states(states: list) -> tuple:
    """Join multiple CPU states at a block merge point.

    Returns (joined_cpu_state, joined_memory).
    For each register/flag/memory cell: if all incoming states agree on
    a concrete value, keep it; otherwise mark unknown.
    """
    if not states:
        return CPUState(), AbstractMemory()
    if len(states) == 1:
        cpu, mem = states[0]
        return cpu.copy(), mem.copy()

    result_cpu = CPUState()
    first_cpu = states[0][0]
    n_d = len(result_cpu.d)
    n_a = len(result_cpu.a)
    _jv = _join_values  # local ref for speed

    # Join data registers
    for i in range(n_d):
        r = first_cpu.d[i]
        for s in states[1:]:
            r = _jv(r, s[0].d[i])
        result_cpu.d[i] = r

    # Join address registers
    for i in range(n_a):
        r = first_cpu.a[i]
        for s in states[1:]:
            r = _jv(r, s[0].a[i])
        result_cpu.a[i] = r

    # Join SP
    r = first_cpu.sp
    for s in states[1:]:
        r = _jv(r, s[0].sp)
    result_cpu.sp = r

    # Join CCR flags
    for flag in result_cpu.ccr:
        v0 = first_cpu.ccr.get(flag)
        if v0 is not None and all(
                s[0].ccr.get(flag) == v0 for s in states[1:]):
            result_cpu.ccr[flag] = v0
        else:
            result_cpu.ccr[flag] = None

    # Join memory: skip if all states share the same memory object
    first_mem = states[0][1]
    if all(s[1] is first_mem for s in states[1:]):
        result_mem = first_mem.copy()
    else:
        result_mem = AbstractMemory()
        # Concrete bytes — intersect keys (only addresses in ALL states)
        common_addrs = set(states[0][1]._bytes.keys())
        for _, mem in states[1:]:
            common_addrs &= mem._bytes.keys()
        for addr in common_addrs:
            r = states[0][1]._bytes[addr]
            for _, mem in states[1:]:
                r = _jv(r, mem._bytes[addr])
            if r.concrete is not None:
                result_mem._bytes[addr] = r

        # Concrete memory tags — intersect
        common_tags = set(states[0][1]._tags.keys())
        for _, mem in states[1:]:
            common_tags &= mem._tags.keys()
        for key in common_tags:
            t0 = states[0][1]._tags[key]
            if all(s[1]._tags[key] == t0 for s in states[1:]):
                result_mem._tags[key] = t0

        # Symbolic slots — intersect
        common_sym = set(states[0][1]._sym.keys())
        for _, mem in states[1:]:
            common_sym &= mem._sym.keys()
        for key in common_sym:
            r = states[0][1]._sym[key]
            for _, mem in states[1:]:
                r = _jv(r, mem._sym[key])
            if r.concrete is not None or r.sym_base is not None or r.tag:
                result_mem._sym[key] = r

    return result_cpu, result_mem


def _extract_size(text: str) -> str:
    """Extract size suffix from disassembled instruction text.

    Returns the size letter, or the KB default_operand_size if unsized.
    """
    _, _, meta = _load_kb()
    parts = text.strip().split(None, 1)
    if not parts:
        return meta["default_operand_size"]
    mn_part = parts[0]
    for sz in meta["size_suffixes"]:
        if mn_part.endswith("." + sz):
            return sz
    return meta["default_operand_size"]


def _parse_operand_text(text: str) -> tuple[str | None, str | None]:
    """Extract source and destination operand strings from instruction text.

    Returns (src_text, dst_text). Either may be None.
    Handles: 'move.l d0,d1' -> ('d0', 'd1')
             'clr.l d0' -> (None, 'd0')
             'rts' -> (None, None)
    """
    parts = text.strip().split(None, 1)
    if len(parts) < 2:
        return None, None
    operand_str = parts[1].strip()
    # Split on comma, but not inside parentheses
    depth = 0
    split_pos = -1
    for i, ch in enumerate(operand_str):
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        elif ch == ',' and depth == 0:
            split_pos = i
            break
    if split_pos >= 0:
        return operand_str[:split_pos].strip(), operand_str[split_pos + 1:].strip()
    return operand_str, None


def _parse_reg_from_text(reg_text: str) -> tuple[str, int] | None:
    """Parse a register name into (mode, reg_num).

    Returns ('dn', N) or ('an', N) or None.
    """
    _, _, meta = _load_kb()
    reg_text = reg_text.strip().lower()
    # Check register aliases from KB (e.g. "sp" -> "a7")
    aliases = meta.get("register_aliases", {})
    if reg_text in aliases:
        reg_text = aliases[reg_text]
    if len(reg_text) == 2 and reg_text[0] in ('d', 'a') and reg_text[1].isdigit():
        num = int(reg_text[1])
        mode = "dn" if reg_text[0] == 'd' else "an"
        return (mode, num)
    return None


def _parse_disp(s: str) -> int | None:
    """Parse a displacement string: -$hex, $hex, or decimal."""
    s = s.strip()
    try:
        if s.startswith('-$'):
            return -int(s[2:], 16)
        if s.startswith('$'):
            return int(s[1:], 16)
        return int(s)
    except ValueError:
        return None


def _resolve_ea_address(src_text: str, cpu, inst: Instruction,
                        meta: dict) -> "AbstractValue | None":
    """Resolve an EA text operand to its effective address (not the value at it).

    Used by LEA — computes the address that the EA refers to.
    """
    src = src_text.strip()
    # d(An) or d(pc) — displacement from register/PC
    if '(' in src and src.endswith(')'):
        paren_idx = src.index('(')
        disp_str = src[:paren_idx].strip()
        inner = src[paren_idx + 1:-1].strip().lower()
        if inner == 'pc':
            opword_bytes = meta["opword_bytes"]
            try:
                if disp_str.startswith('$'):
                    disp = int(disp_str[1:], 16)
                else:
                    disp = int(disp_str)
            except ValueError:
                return None
            return _concrete(inst.offset + opword_bytes + disp)
        # (An) without displacement
        if not disp_str:
            reg_info = _parse_reg_from_text(inner)
            if reg_info:
                return cpu.get_reg(reg_info[0], reg_info[1])
            return None
        # d(An)
        reg_info = _parse_reg_from_text(inner)
        if reg_info:
            base = cpu.get_reg(reg_info[0], reg_info[1])
            if base.is_known:
                disp = _parse_disp(disp_str)
                if disp is None:
                    return None
                return _concrete(base.concrete + disp)
        return None
    # Absolute address
    if src.startswith('($') or src.startswith('$'):
        try:
            clean = src.strip('()').lstrip('$')
            if clean.endswith('.w') or clean.endswith('.l'):
                clean = clean[:-2]
            return _concrete(int(clean, 16))
        except ValueError:
            return None
    return None


def _apply_instruction(inst: Instruction, inst_kb: dict,
                       cpu: "CPUState_inner", mem: AbstractMemory,
                       code: bytes, base_addr: int,
                       platform: dict | None = None):
    """Apply one instruction's effects to the abstract state.

    Dispatches on KB compute_formula.op and operation_type — not mnemonics.
    Sign-extension widths, bit ranges, and implicit operands all come from KB.
    LEA is the one exception: it resolves the EA address (not value) and has
    no KB field to distinguish this from MOVE, so it is detected by its unique
    operation text signature.

    If platform is provided (from OS KB calling_convention), scratch registers
    are invalidated after call instructions.
    """
    _, _, meta = _load_kb()
    text = inst.text.strip()
    mnemonic = _extract_mnemonic(text)
    size = _extract_size(text)
    if size not in meta["size_byte_count"]:
        # Unsized instructions (e.g. JMP, LEA) default to word
        # for extension word parsing — not an error.
        size_bytes = meta["size_byte_count"]["w"]
    else:
        size_bytes = meta["size_byte_count"][size]
    mask = (1 << (size_bytes * 8)) - 1

    # KB fields that drive dispatch
    formula = inst_kb.get("compute_formula")
    op = formula.get("op") if formula else None
    op_type = inst_kb.get("operation_type")
    src_sign_ext = inst_kb.get("source_sign_extend", False)

    src_text, dst_text = _parse_operand_text(text)

    # Decode structured operands from opcode bytes (KB-driven).
    # ea_op: the EA operand from MODE/REGISTER in bits 5-0
    # dst_op: the destination EA from upper MODE/REGISTER (MOVE only)
    # reg_num: the register number from REGISTER in bits 11-9
    # For OPMODE instructions: ea_is_source from KB opmode_table
    ea_op = dst_op = None
    opcode = 0
    reg_num = None  # register from upper REGISTER field
    ea_is_source = None  # from OPMODE: True=EA is src, False=EA is dst
    if len(inst.raw) >= meta["opword_bytes"]:
        opcode = struct.unpack_from(">H", inst.raw, 0)[0]
        enc_fields = inst_kb.get("encodings", [{}])[0].get("fields", [])

        mode_fields = sorted(
            [f for f in enc_fields if f["name"] == "MODE"],
            key=lambda f: f["bit_lo"])
        reg_fields = sorted(
            [f for f in enc_fields if f["name"] == "REGISTER"],
            key=lambda f: f["bit_lo"])

        # Decode EA from lowest MODE + lowest REGISTER
        if mode_fields and reg_fields:
            mf = mode_fields[0]
            rf = reg_fields[0]
            ea_mode = _xf(opcode, (mf["bit_hi"], mf["bit_lo"],
                                   mf["bit_hi"] - mf["bit_lo"] + 1))
            ea_reg = _xf(opcode, (rf["bit_hi"], rf["bit_lo"],
                                  rf["bit_hi"] - rf["bit_lo"] + 1))
            try:
                ea_op, ext_pos = _decode_ea(
                    inst.raw, meta["opword_bytes"],
                    ea_mode, ea_reg, size, inst.offset)
            except ValueError:
                ea_op = None
                ext_pos = meta["opword_bytes"]

            # Destination EA from upper MODE + upper REGISTER (MOVE)
            if len(mode_fields) >= 2 and len(reg_fields) >= 2:
                dmf = mode_fields[1]
                drf = reg_fields[1]
                d_mode = _xf(opcode, (dmf["bit_hi"], dmf["bit_lo"],
                                      dmf["bit_hi"] - dmf["bit_lo"] + 1))
                d_reg = _xf(opcode, (drf["bit_hi"], drf["bit_lo"],
                                     drf["bit_hi"] - drf["bit_lo"] + 1))
                try:
                    dst_op, _ = _decode_ea(
                        inst.raw, ext_pos,
                        d_mode, d_reg, size, inst.offset)
                except ValueError:
                    dst_op = None

        # Upper register number (bits 11-9 typically)
        if len(reg_fields) >= 2:
            rf = reg_fields[-1]
            reg_num = _xf(opcode, (rf["bit_hi"], rf["bit_lo"],
                                   rf["bit_hi"] - rf["bit_lo"] + 1))

        # OPMODE direction from KB opmode_table
        opmode_table = inst_kb.get("constraints", {}).get("opmode_table")
        if opmode_table:
            opmode_f = next(
                (f for f in enc_fields if f["name"] == "OPMODE"), None)
            if opmode_f:
                opmode_val = _xf(opcode, (
                    opmode_f["bit_hi"], opmode_f["bit_lo"],
                    opmode_f["bit_hi"] - opmode_f["bit_lo"] + 1))
                for entry in opmode_table:
                    if entry["opmode"] == opmode_val:
                        ea_is_source = entry.get("ea_is_source")
                        break

    # Convenience aliases for backward compatibility
    src_op = ea_op  # for instructions where EA is the source

    # Helper: resolve a text operand to an AbstractValue.
    # For postincrement/predecrement modes, also adjusts the register.
    def _resolve_text_operand(op_text: str) -> AbstractValue | None:
        if op_text is None:
            return None
        op_text = op_text.strip()
        # Immediate
        if op_text.startswith('#'):
            imm_str = op_text[1:].strip()
            try:
                if imm_str.startswith('$'):
                    return _concrete(int(imm_str[1:], 16))
                elif imm_str.startswith('%'):
                    return _concrete(int(imm_str[1:], 2))
                else:
                    return _concrete(int(imm_str))
            except ValueError:
                return None
        # Register direct
        reg_info = _parse_reg_from_text(op_text)
        if reg_info:
            return cpu.get_reg(reg_info[0], reg_info[1])
        # Postincrement: (An)+ — read from An, then An += size_bytes
        if op_text.startswith('(') and op_text.endswith(')+'):
            inner = op_text[1:-2]
            reg_info = _parse_reg_from_text(inner)
            if reg_info:
                mode, num = reg_info
                addr_val = cpu.get_reg(mode, num)
                if addr_val.is_known:
                    val = mem.read(addr_val.concrete, size)
                    cpu.set_reg(mode, num, _concrete(
                        (addr_val.concrete + size_bytes) & 0xFFFFFFFF))
                    return val
                if addr_val.is_symbolic:
                    val = mem.read(addr_val, size)
                    cpu.set_reg(mode, num, addr_val.sym_add(size_bytes))
                    return val
                return None
        # Predecrement: -(An) — An -= size_bytes, then read from new An
        if op_text.startswith('-(') and op_text.endswith(')'):
            inner = op_text[2:-1]
            reg_info = _parse_reg_from_text(inner)
            if reg_info:
                mode, num = reg_info
                addr_val = cpu.get_reg(mode, num)
                if addr_val.is_known:
                    new_addr = (addr_val.concrete - size_bytes) & 0xFFFFFFFF
                    cpu.set_reg(mode, num, _concrete(new_addr))
                    return mem.read(new_addr, size)
                if addr_val.is_symbolic:
                    new_val = addr_val.sym_add(-size_bytes)
                    cpu.set_reg(mode, num, new_val)
                    return mem.read(new_val, size)
                return None
        # (An) indirect
        if op_text.startswith('(') and op_text.endswith(')'):
            inner = op_text[1:-1]
            reg_info = _parse_reg_from_text(inner)
            if reg_info:
                addr_val = cpu.get_reg(reg_info[0], reg_info[1])
                if addr_val.is_known:
                    return mem.read(addr_val.concrete, size)
                if addr_val.is_symbolic:
                    return mem.read(addr_val, size)
                return None
        # d(An) displacement
        if '(' in op_text and op_text.endswith(')'):
            paren_idx = op_text.index('(')
            disp_str = op_text[:paren_idx].strip()
            inner = op_text[paren_idx + 1:-1]
            reg_info = _parse_reg_from_text(inner)
            if reg_info:
                addr_val = cpu.get_reg(reg_info[0], reg_info[1])
                disp = _parse_disp(disp_str)
                if disp is None:
                    return None
                if addr_val.is_known:
                    return mem.read(
                        (addr_val.concrete + disp) & 0xFFFFFFFF, size)
                if addr_val.is_symbolic:
                    return mem.read(addr_val.sym_add(disp), size)
                return None
        # Absolute address
        if op_text.startswith('$') or op_text.startswith('('):
            return None  # can't resolve without more context
        return None

    # Helper: write to a destination.
    # For predecrement/postincrement modes, also adjusts the register.
    def _write_dst(op_text: str, value: AbstractValue):
        if op_text is None:
            return
        op_text = op_text.strip()
        # Register direct
        reg_info = _parse_reg_from_text(op_text)
        if reg_info:
            cpu.set_reg(reg_info[0], reg_info[1], value)
            return
        # Predecrement: -(An) — An -= size_bytes, then write to new An
        if op_text.startswith('-(') and op_text.endswith(')'):
            inner = op_text[2:-1]
            reg_info = _parse_reg_from_text(inner)
            if reg_info:
                mode, num = reg_info
                addr_val = cpu.get_reg(mode, num)
                if addr_val.is_known:
                    new_addr = (addr_val.concrete - size_bytes) & 0xFFFFFFFF
                    cpu.set_reg(mode, num, _concrete(new_addr))
                    mem.write(new_addr, value, size)
                elif addr_val.is_symbolic:
                    new_val = addr_val.sym_add(-size_bytes)
                    cpu.set_reg(mode, num, new_val)
                    mem.write(new_val, value, size)
            return
        # Postincrement: (An)+ — write to An, then An += size_bytes
        if op_text.startswith('(') and op_text.endswith(')+'):
            inner = op_text[1:-2]
            reg_info = _parse_reg_from_text(inner)
            if reg_info:
                mode, num = reg_info
                addr_val = cpu.get_reg(mode, num)
                if addr_val.is_known:
                    mem.write(addr_val.concrete, value, size)
                    cpu.set_reg(mode, num, _concrete(
                        (addr_val.concrete + size_bytes) & 0xFFFFFFFF))
                elif addr_val.is_symbolic:
                    mem.write(addr_val, value, size)
                    cpu.set_reg(mode, num,
                                addr_val.sym_add(size_bytes))
            return
        # (An) indirect write
        if op_text.startswith('(') and op_text.endswith(')'):
            inner = op_text[1:-1]
            reg_info = _parse_reg_from_text(inner)
            if reg_info:
                addr_val = cpu.get_reg(reg_info[0], reg_info[1])
                if addr_val.is_known:
                    mem.write(addr_val.concrete, value, size)
                elif addr_val.is_symbolic:
                    mem.write(addr_val, value, size)
            return
        # d(An) displacement write
        if '(' in op_text and op_text.endswith(')'):
            paren_idx = op_text.index('(')
            disp_str = op_text[:paren_idx].strip()
            inner = op_text[paren_idx + 1:-1]
            reg_info = _parse_reg_from_text(inner)
            if reg_info:
                addr_val = cpu.get_reg(reg_info[0], reg_info[1])
                disp = _parse_disp(disp_str)
                if disp is not None:
                    if addr_val.is_known:
                        mem.write((addr_val.concrete + disp) & 0xFFFFFFFF,
                                  value, size)
                    elif addr_val.is_symbolic:
                        mem.write(addr_val.sym_add(disp), value, size)

    # --- Apply per-instruction effects ---
    # Dispatch on KB compute_formula.op and operation_type.
    # No mnemonic-string dispatch — all semantics from KB fields.

    # SP-modifying instructions: track stack pointer (check first, these
    # are orthogonal to compute effects and may return early)
    sp_effects = inst_kb.get("sp_effects", [])
    if sp_effects:
        for effect in sp_effects:
            action = effect.get("action")
            if "bytes" not in effect and action in ("decrement", "increment"):
                raise KeyError(
                    f"sp_effects.bytes missing for {mnemonic} action={action}")
            if action == "decrement":
                if cpu.sp.is_known:
                    cpu.sp = _concrete(cpu.sp.concrete - effect["bytes"])
                elif cpu.sp.is_symbolic:
                    cpu.sp = cpu.sp.sym_add(-effect["bytes"])
            elif action == "increment":
                if cpu.sp.is_known:
                    cpu.sp = _concrete(cpu.sp.concrete + effect["bytes"])
                elif cpu.sp.is_symbolic:
                    cpu.sp = cpu.sp.sym_add(effect["bytes"])
            elif action == "displacement_adjust":
                # LINK-style: SP += displacement (negative = allocate)
                if src_text:
                    src_val = _resolve_text_operand(src_text)
                    if src_val and src_val.is_known:
                        disp = _to_signed(src_val.concrete & 0xFFFF, "w")
                        if cpu.sp.is_known:
                            cpu.sp = _concrete(cpu.sp.concrete + disp)
                        elif cpu.sp.is_symbolic:
                            cpu.sp = cpu.sp.sym_add(disp)
        # For call instructions (JSR/BSR), write the return address to
        # the stack.  The return address is the instruction immediately
        # after the call.  This enables RTS resolution and push/pop
        # patterns to work through abstract memory.
        if cpu.sp.is_known or cpu.sp.is_symbolic:
            flow = inst_kb.get("pc_effects", {}).get("flow", {})
            if flow.get("type") == "call":
                return_addr = inst.offset + inst.size
                mem.write(cpu.sp, _concrete(return_addr), "l")

        # After call instructions, invalidate scratch registers per
        # platform calling convention.  Detect calls by KB pc_effects
        # flow type, not by SP decrement (PEA also decrements SP but
        # isn't a call).
        if platform and platform.get("scratch_regs"):
            flow_type = inst_kb.get("pc_effects", {}).get(
                "flow", {}).get("type")
            if flow_type == "call":
                # Resolve call effects before invalidation (needs pre-call
                # register state for input registers like A1 name string).
                # Decode EA from opcode bits (KB-driven, not text parsing).
                call_effect = None
                resolver = platform.get("_os_call_resolver")
                if resolver and len(inst.raw) >= meta["opword_bytes"]:
                    lvo = None
                    base_reg_num = platform["_base_reg_num"]
                    opcode = struct.unpack_from(">H", inst.raw, 0)[0]
                    # Extract EA fields from KB encoding
                    enc_fields = inst_kb.get("encodings", [{}])[0].get(
                        "fields", [])
                    ea_mode_f = ea_reg_f = None
                    for f in enc_fields:
                        if f["name"] == "MODE":
                            ea_mode_f = (f["bit_hi"], f["bit_lo"],
                                         f["bit_hi"] - f["bit_lo"] + 1)
                        elif (f["name"] == "REGISTER"
                              and f["bit_hi"] <= 5):
                            ea_reg_f = (f["bit_hi"], f["bit_lo"],
                                        f["bit_hi"] - f["bit_lo"] + 1)
                    if ea_mode_f and ea_reg_f:
                        ea_mode = _xf(opcode, ea_mode_f)
                        ea_reg = _xf(opcode, ea_reg_f)
                        try:
                            operand, _ = _decode_ea(
                                inst.raw, meta["opword_bytes"],
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
                                idx_val = cpu.get_reg(
                                    idx_mode, operand.index_reg)
                                if idx_val.is_known:
                                    idx_v = idx_val.concrete
                                    if operand.index_size == "w":
                                        idx_v = _to_signed(
                                            idx_v & 0xFFFF, "w")
                                    else:
                                        idx_v = _to_signed(
                                            idx_v & 0xFFFFFFFF, "l")
                                    lvo = operand.value + idx_v
                    a6_tag = cpu.a[base_reg_num].tag
                    a6_lib = (a6_tag.get("library_base")
                              if a6_tag else None)
                    if lvo is not None and a6_lib:
                        call_effect = resolver(
                            inst.offset, lvo, a6_lib, cpu, code,
                            platform=platform)

                # Store call effect for propagate_states to apply
                # after scratch reg invalidation on the fallthrough.
                # Don't invalidate here — the callee needs the
                # pre-call register state (e.g. D0 = LVO offset).
                if call_effect:
                    platform["_pending_call_effect"] = call_effect

        # SP-only instructions (no compute_formula) stop here
        if op is None:
            return

    # MOVEM: Move Multiple Registers.  Transfers a set of registers
    # to/from memory via a 16-bit mask in the extension word.
    # Detected by KB operation_class (set by parser from form syntax).
    # Register order from KB movem_reg_masks (normal vs predecrement).
    if inst_kb.get("operation_class") == "multi_register_transfer":
        opword_bytes = meta["opword_bytes"]
        if len(inst.raw) < opword_bytes + 2:
            return  # truncated
        opcode = struct.unpack_from(">H", inst.raw, 0)[0]
        reg_mask = struct.unpack_from(">H", inst.raw, opword_bytes)[0]

        # Direction from KB encoding "dr" field
        dr_field = None
        for f in inst_kb["encodings"][0]["fields"]:
            if f["name"] == "dr":
                dr_field = (f["bit_hi"], f["bit_lo"],
                            f["bit_hi"] - f["bit_lo"] + 1)
                break
        if dr_field is None:
            raise KeyError("MOVEM encoding lacks 'dr' field")
        direction = _xf(opcode, dr_field)  # 0=reg-to-mem, 1=mem-to-reg

        # EA mode from encoding
        ea_mode_f = ea_reg_f = None
        for f in inst_kb["encodings"][0]["fields"]:
            if f["name"] == "MODE":
                ea_mode_f = (f["bit_hi"], f["bit_lo"],
                             f["bit_hi"] - f["bit_lo"] + 1)
            elif f["name"] == "REGISTER" and f["bit_hi"] <= 5:
                ea_reg_f = (f["bit_hi"], f["bit_lo"],
                            f["bit_hi"] - f["bit_lo"] + 1)
        if ea_mode_f is None or ea_reg_f is None:
            raise KeyError("MOVEM encoding lacks MODE/REGISTER fields")
        ea_mode = _xf(opcode, ea_mode_f)
        ea_reg = _xf(opcode, ea_reg_f)

        # EA mode name from KB
        ea_enc = meta["ea_mode_encoding"]
        predec_enc = ea_enc["predec"]
        postinc_enc = ea_enc["postinc"]
        is_predec = (ea_mode == predec_enc[0])
        is_postinc = (ea_mode == postinc_enc[0])

        # Register order from KB movem_reg_masks
        masks = meta["movem_reg_masks"]
        reg_order = masks["predecrement"] if is_predec else masks["normal"]

        # Collect registers to transfer (bit N set → reg_order[N])
        regs = []
        for bit in range(16):
            if reg_mask & (1 << bit):
                regs.append(reg_order[bit])

        if not regs:
            return

        # Size from KB encoding "SIZE" field
        size_field = None
        for f in inst_kb["encodings"][0]["fields"]:
            if f["name"] == "SIZE":
                size_field = (f["bit_hi"], f["bit_lo"],
                              f["bit_hi"] - f["bit_lo"] + 1)
                break
        if size_field is None:
            raise KeyError("MOVEM encoding lacks 'SIZE' field")
        size_bit = _xf(opcode, size_field)
        xfer_size = "l" if size_bit == 1 else "w"
        xfer_bytes = meta["size_byte_count"][xfer_size]

        sp_reg = meta["_sp_reg_num"]

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
        return

    # LEA: loads the effective address itself (not the value at EA).
    # Detected by KB operation_class. Resolves the source EA to its
    # address (not the value at the address), then writes to the
    # destination An register decoded from the opcode.
    if inst_kb.get("operation_class") == "load_effective_address" and op == "assign":
        addr_val = None
        if src_op:
            # Compute the EA address from the decoded operand
            if src_op.mode == "pcdisp":
                addr_val = _concrete(src_op.value)
            elif src_op.mode == "pcindex":
                base_addr_val = src_op.value
                idx_mode = "an" if src_op.index_is_addr else "dn"
                idx_val = cpu.get_reg(idx_mode, src_op.index_reg)
                if idx_val.is_known:
                    nbits = meta["size_byte_count"][
                        src_op.index_size] * 8
                    mask = (1 << nbits) - 1
                    iv = idx_val.concrete & mask
                    if iv >= (1 << (nbits - 1)):
                        iv -= (1 << nbits)
                    addr_val = _concrete(
                        (base_addr_val + iv) & 0xFFFFFFFF)
            elif src_op.mode == "disp":
                base = cpu.a[src_op.reg]
                if base.is_known:
                    addr_val = _concrete(
                        (base.concrete + src_op.value) & 0xFFFFFFFF)
                elif base.is_symbolic:
                    addr_val = base.sym_add(src_op.value)
            elif src_op.mode == "ind":
                addr_val = cpu.get_reg("an", src_op.reg)
            elif src_op.mode in ("absw", "absl"):
                addr_val = _concrete(src_op.value)
        # Write to destination An (from KB encoding)
        if reg_num is not None:
            cpu.set_reg("an", reg_num,
                        addr_val if addr_val else _unknown())
        return

    # --- Formula-driven dispatch ---

    if op == "assign":
        # MOVE/MOVEA/MOVEQ/CLR family.
        terms = formula.get("terms", [])

        if "implicit" in terms:
            # CLR: assign implicit_operand (0) to destination.
            implicit_val = inst_kb.get("implicit_operand")
            if implicit_val is None:
                raise KeyError(f"implicit_operand missing for {mnemonic}")
            write_op = dst_op if dst_op else src_op
            if write_op:
                _write_operand(write_op, cpu, mem,
                               _concrete(implicit_val), size, size_bytes)
            return

        # Source-assign: MOVE, MOVEA, MOVEQ.
        # Read source from structured operand, falling back to text
        # for instructions without EA fields (e.g. MOVEQ has the
        # immediate in a DATA field, not in a MODE/REGISTER EA).
        src_val = (_resolve_operand(src_op, cpu, mem, size, size_bytes)
                   if src_op else _resolve_text_operand(src_text))

        # Sign-extend immediate from KB constraints.immediate_range
        imm_range = inst_kb.get("constraints", {}).get("immediate_range")
        if imm_range and imm_range.get("signed") and src_val and src_val.is_known:
            bits = imm_range["bits"]
            val = src_val.concrete & ((1 << bits) - 1)
            if val >= (1 << (bits - 1)):
                val |= ~((1 << bits) - 1)
            val &= 0xFFFFFFFF
            src_val = _concrete(val)

        # Source sign-extension from KB source_sign_extend
        if src_sign_ext and size == "w" and src_val and src_val.is_known:
            w_bits = meta["size_byte_count"]["w"] * 8
            w_mask = (1 << w_bits) - 1
            val = src_val.concrete & w_mask
            if val >= (1 << (w_bits - 1)):
                val |= ~w_mask
            src_val = _concrete(val & 0xFFFFFFFF)

        # ExecBase load: MOVEA.L ($N).W,An — source is absw
        # matching platform exec_base_addr.
        if (src_val is None and platform and src_op
                and src_op.mode == "absw"
                and src_op.value == platform.get("exec_base_addr")):
            src_val = _unknown(tag=platform.get("exec_base_tag"))

        # Write to destination.
        result = src_val if src_val is not None else _unknown()
        if dst_op:
            _write_operand(dst_op, cpu, mem, result, size, size_bytes)
        elif reg_num is not None:
            if src_sign_ext:
                cpu.set_reg("an", reg_num, result)
            else:
                cpu.set_reg("dn", reg_num, result)
        else:
            # Fallback: text-based write for instructions whose
            # destination encoding isn't a standard EA (MOVEQ,
            # single-operand, etc.)
            _write_dst(dst_text or src_text, result)
        return

    # Helper: sign-extend source value per KB source_sign_extend
    def _sign_ext_src(val):
        if src_sign_ext and size == "w" and val and val.is_known:
            w_bits = meta["size_byte_count"]["w"] * 8
            w_mask = (1 << w_bits) - 1
            v = val.concrete & w_mask
            if v >= (1 << (w_bits - 1)):
                v |= ~w_mask
            return _concrete(v & 0xFFFFFFFF)
        return val

    if op == "add":
        if ea_is_source is not None and ea_op and reg_num is not None:
            # OPMODE-directed: ADD <ea>,Dn or ADD Dn,<ea>
            ea_val = _resolve_operand(ea_op, cpu, mem, size, size_bytes)
            dn_val = cpu.get_reg("dn", reg_num)
            src_val = _sign_ext_src(ea_val if ea_is_source else dn_val)
            dst_val = dn_val if ea_is_source else ea_val
            if src_val and dst_val and src_val.is_known and dst_val.is_known:
                result = (dst_val.concrete + src_val.concrete) & 0xFFFFFFFF
                if ea_is_source:
                    cpu.set_reg("dn", reg_num, _concrete(result))
                else:
                    _write_operand(ea_op, cpu, mem, _concrete(result),
                                   size, size_bytes)
            else:
                if ea_is_source:
                    cpu.set_reg("dn", reg_num, _unknown())
                else:
                    _write_operand(ea_op, cpu, mem, _unknown(),
                                   size, size_bytes)
        else:
            # ADDQ/ADDI/ADDA: text-based (immediate source not in EA)
            src_val = _sign_ext_src(_resolve_text_operand(src_text))
            dst_val = _resolve_text_operand(dst_text)
            if src_val and dst_val and src_val.is_known and dst_val.is_known:
                _write_dst(dst_text, _concrete(
                    (dst_val.concrete + src_val.concrete) & 0xFFFFFFFF))
            else:
                _write_dst(dst_text, _unknown())
        return

    if op == "subtract":
        terms = formula.get("terms", [])
        if "implicit" in terms:
            # NEG: implicit(0) - destination
            implicit_val = inst_kb.get("implicit_operand")
            if implicit_val is None:
                raise KeyError(f"implicit_operand missing for {mnemonic}")
            dst_val = _resolve_text_operand(dst_text or src_text)
            if dst_val and dst_val.is_known:
                result = (implicit_val - dst_val.concrete) & mask
                if size != "l":
                    upper = dst_val.concrete & ~mask
                    result = upper | result
                _write_dst(dst_text or src_text,
                           _concrete(result & 0xFFFFFFFF))
            else:
                _write_dst(dst_text or src_text, _unknown())
            return
        if ea_is_source is not None and ea_op and reg_num is not None:
            ea_val = _resolve_operand(ea_op, cpu, mem, size, size_bytes)
            dn_val = cpu.get_reg("dn", reg_num)
            src_val = _sign_ext_src(ea_val if ea_is_source else dn_val)
            dst_val = dn_val if ea_is_source else ea_val
            if src_val and dst_val and src_val.is_known and dst_val.is_known:
                result = (dst_val.concrete - src_val.concrete) & 0xFFFFFFFF
                if ea_is_source:
                    cpu.set_reg("dn", reg_num, _concrete(result))
                else:
                    _write_operand(ea_op, cpu, mem, _concrete(result),
                                   size, size_bytes)
            else:
                if ea_is_source:
                    cpu.set_reg("dn", reg_num, _unknown())
                else:
                    _write_operand(ea_op, cpu, mem, _unknown(),
                                   size, size_bytes)
        else:
            src_val = _sign_ext_src(_resolve_text_operand(src_text))
            dst_val = _resolve_text_operand(dst_text)
            if src_val and dst_val and src_val.is_known and dst_val.is_known:
                _write_dst(dst_text, _concrete(
                    (dst_val.concrete - src_val.concrete) & 0xFFFFFFFF))
            else:
                _write_dst(dst_text, _unknown())
        return

    if op == "bitwise_and":
        if ea_is_source is not None and ea_op and reg_num is not None:
            ea_val = _resolve_operand(ea_op, cpu, mem, size, size_bytes)
            dn_val = cpu.get_reg("dn", reg_num)
            s, d = (ea_val, dn_val) if ea_is_source else (dn_val, ea_val)
            if s and d and s.is_known and d.is_known:
                r = d.concrete & s.concrete
                if ea_is_source:
                    cpu.set_reg("dn", reg_num, _concrete(r))
                else:
                    _write_operand(ea_op, cpu, mem, _concrete(r),
                                   size, size_bytes)
            else:
                if ea_is_source:
                    cpu.set_reg("dn", reg_num, _unknown())
                else:
                    _write_operand(ea_op, cpu, mem, _unknown(),
                                   size, size_bytes)
        else:
            src_val = _resolve_text_operand(src_text)
            dst_val = _resolve_text_operand(dst_text)
            if src_val and dst_val and src_val.is_known and dst_val.is_known:
                _write_dst(dst_text, _concrete(
                    dst_val.concrete & src_val.concrete))
            else:
                _write_dst(dst_text, _unknown())
        return

    if op == "bitwise_or":
        if ea_is_source is not None and ea_op and reg_num is not None:
            ea_val = _resolve_operand(ea_op, cpu, mem, size, size_bytes)
            dn_val = cpu.get_reg("dn", reg_num)
            s, d = (ea_val, dn_val) if ea_is_source else (dn_val, ea_val)
            if s and d and s.is_known and d.is_known:
                r = d.concrete | s.concrete
                if ea_is_source:
                    cpu.set_reg("dn", reg_num, _concrete(r))
                else:
                    _write_operand(ea_op, cpu, mem, _concrete(r),
                                   size, size_bytes)
            else:
                if ea_is_source:
                    cpu.set_reg("dn", reg_num, _unknown())
                else:
                    _write_operand(ea_op, cpu, mem, _unknown(),
                                   size, size_bytes)
        else:
            src_val = _resolve_text_operand(src_text)
            dst_val = _resolve_text_operand(dst_text)
            if src_val and dst_val and src_val.is_known and dst_val.is_known:
                _write_dst(dst_text, _concrete(
                    dst_val.concrete | src_val.concrete))
            else:
                _write_dst(dst_text, _unknown())
        return

    if op == "bitwise_xor":
        if ea_is_source is not None and ea_op and reg_num is not None:
            ea_val = _resolve_operand(ea_op, cpu, mem, size, size_bytes)
            dn_val = cpu.get_reg("dn", reg_num)
            s, d = (ea_val, dn_val) if ea_is_source else (dn_val, ea_val)
            if s and d and s.is_known and d.is_known:
                r = d.concrete ^ s.concrete
                if ea_is_source:
                    cpu.set_reg("dn", reg_num, _concrete(r))
                else:
                    _write_operand(ea_op, cpu, mem, _concrete(r),
                                   size, size_bytes)
            else:
                if ea_is_source:
                    cpu.set_reg("dn", reg_num, _unknown())
                else:
                    _write_operand(ea_op, cpu, mem, _unknown(),
                                   size, size_bytes)
        else:
            src_val = _resolve_text_operand(src_text)
            dst_val = _resolve_text_operand(dst_text)
            if src_val and dst_val and src_val.is_known and dst_val.is_known:
                _write_dst(dst_text, _concrete(
                    dst_val.concrete ^ src_val.concrete))
            else:
                _write_dst(dst_text, _unknown())
        return

    if op == "bitwise_complement":
        # NOT: ~destination (single operand)
        dst_val = _resolve_text_operand(dst_text or src_text)
        if dst_val and dst_val.is_known:
            result = dst_val.concrete ^ mask
            if size != "l":
                upper = dst_val.concrete & ~mask
                result = upper | result
            _write_dst(dst_text or src_text, _concrete(result & 0xFFFFFFFF))
        else:
            _write_dst(dst_text or src_text, _unknown())
        return

    if op == "exchange":
        # SWAP: exchange bit ranges within register
        range_a = formula.get("range_a")
        range_b = formula.get("range_b")
        reg_info = _parse_reg_from_text(src_text or dst_text or "")
        if range_a and range_b and reg_info and reg_info[0] == "dn":
            val = cpu.get_reg("dn", reg_info[1])
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
                cpu.set_reg("dn", reg_info[1], _concrete(v & 0xFFFFFFFF))
            else:
                cpu.set_reg("dn", reg_info[1], _unknown())
            return

    if op == "sign_extend":
        # EXT/EXTB: sign-extend from source_bits_by_size
        src_bits_by_size = formula.get("source_bits_by_size")
        if src_bits_by_size is None:
            raise KeyError(f"source_bits_by_size missing for {mnemonic}")
        reg_info = _parse_reg_from_text(src_text or dst_text or "")
        if reg_info and reg_info[0] == "dn":
            val = cpu.get_reg("dn", reg_info[1])
            if val.is_known:
                v = val.concrete
                # Determine source bits: check for mnemonic-specific key first
                # (e.g. "extb_l" for EXTB.L), then fall back to size key
                mnemonic_key = mnemonic.lower() + "_" + size
                src_bits = src_bits_by_size.get(mnemonic_key,
                                                src_bits_by_size.get(size))
                if src_bits is None:
                    raise KeyError(
                        f"No source_bits for size={size} in {mnemonic}")
                src_mask = (1 << src_bits) - 1
                src_val = v & src_mask
                if src_val >= (1 << (src_bits - 1)):
                    # Sign-extend: fill upper bits
                    if size == "w":
                        # Extend within word, preserve upper 16 bits
                        extended = src_val | (~src_mask & 0xFFFF)
                        v = (v & 0xFFFF0000) | (extended & 0xFFFF)
                    else:
                        # Extend to full long
                        v = src_val | ~src_mask
                else:
                    if size == "w":
                        v = (v & 0xFFFF0000) | (src_val & 0xFFFF)
                    else:
                        v = src_val
                cpu.set_reg("dn", reg_info[1], _concrete(v & 0xFFFFFFFF))
            else:
                cpu.set_reg("dn", reg_info[1], _unknown())
        return

    if op == "test":
        # TST: reads destination but doesn't write (only sets CC flags).
        # No state change needed for abstract propagation.
        return

    # EXG: KB operation_type == "swap" with no compute_formula.
    # Swaps two registers.  Operand types from text (Dn/An).
    if op_type == "swap" and op is None:
        src_reg = _parse_reg_from_text(src_text) if src_text else None
        dst_reg = _parse_reg_from_text(dst_text) if dst_text else None
        if src_reg and dst_reg:
            sv = cpu.get_reg(src_reg[0], src_reg[1])
            dv = cpu.get_reg(dst_reg[0], dst_reg[1])
            cpu.set_reg(src_reg[0], src_reg[1], dv)
            cpu.set_reg(dst_reg[0], dst_reg[1], sv)
        return

    # Unhandled compute formulas (multiply, divide, shift, rotate, etc.):
    # invalidate the destination register.
    if dst_text:
        dst_reg = _parse_reg_from_text(dst_text)
        if dst_reg:
            cpu.set_reg(dst_reg[0], dst_reg[1], _unknown())


def propagate_states(blocks: dict[int, BasicBlock],
                     code: bytes, base_addr: int = 0,
                     initial_state: "CPUState_inner | None" = None,
                     initial_mem: AbstractMemory | None = None,
                     platform: dict | None = None,
                     summaries: dict[int, dict | None] | None = None,
                     ) -> dict[int, tuple]:
    """Propagate abstract state through basic blocks from the program entry.

    Seeds the block at base_addr with initial state, then walks forward
    via BFS.  At merge points, joins states conservatively.

    Call fallthroughs use subroutine summaries (SP delta + register
    preservation) when available.  Caller state is also propagated into
    callees for concrete execution (resolves memory reads like library
    base loads).  If a summary clobbers the app base register and the
    platform has a discovered base value, the base register is restored
    (the init routine sets it — its summary reports it as clobbered).

    Only blocks reachable from base_addr through control flow have exit
    states.  Blocks discovered from other entry points (reloc targets,
    heuristic scan) are not analyzed — they are discovery hints.

    Returns dict mapping block_start -> (exit_cpu_state, exit_memory).
    """
    kb_by_name, _, meta = _load_kb()
    cc_test_defs = meta.get("cc_test_definitions", {})
    cc_aliases = meta.get("cc_aliases", {})

    if initial_state is None:
        initial_state = CPUState()
        if platform:
            # Set initial SP as symbolic base for abstract stack tracking.
            # SP_entry+0 at entry; push gives SP_entry-4, pop gives SP_entry+0.
            # Symbolic SP survives joins (same base+offset → keep).
            initial_state.sp = _symbolic("SP_entry", 0)
            # Set initial base register if discovered from prior pass
            base_info = platform.get("initial_base_reg")
            if base_info:
                reg_num, concrete_val = base_info
                initial_state.set_reg("an", reg_num,
                                      _concrete(concrete_val))
    if initial_mem is None:
        # Use init-discovered memory if available (base-region contents
        # from the init routine, e.g. library bases stored at d(An))
        if platform and "_initial_mem" in platform:
            initial_mem = platform["_initial_mem"].copy()
        else:
            initial_mem = AbstractMemory()

    # Map block_start -> {source_key: (cpu_state, memory)}
    # Keyed by source so each predecessor overwrites its previous
    # contribution instead of accumulating across fixpoint iterations.
    incoming: dict[int, dict] = {}
    # Map block_start -> (exit_cpu_state, exit_memory) after execution
    exit_states: dict[int, tuple] = {}

    # Seed ONLY the program entry point (base_addr) with initial state.
    # All other blocks derive state through control flow: callee
    # propagation enters subroutines with the caller's concrete state.
    # Blocks not reachable from the program entry have no exit states
    # — they are discovery hints, not concrete analysis targets.
    if base_addr in blocks:
        incoming[base_addr] = {"_init": (initial_state.copy(),
                                         initial_mem.copy())}

    work = deque([base_addr] if base_addr in blocks else [])
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
        pred_states = list(pred_dict.values())

        # Join incoming states
        cpu, mem = _join_states(pred_states)
        cpu.pc = addr

        # Fixpoint check: skip if state unchanged from last visit.
        if addr in visited and addr in exit_states:
            prev_cpu, _ = exit_states[addr]
            if (cpu.d == prev_cpu.d and cpu.a == prev_cpu.a
                    and cpu.sp == prev_cpu.sp):
                continue

        visited.add(addr)

        # Execute all instructions in the block
        for inst in block.instructions:
            mn = _extract_mnemonic(inst.text)
            ikb = _find_kb_entry(kb_by_name, mn, cc_test_defs, cc_aliases)
            if ikb:
                _apply_instruction(inst, ikb, cpu, mem, code, base_addr,
                                   platform)
            cpu.pc = inst.offset + inst.size

        exit_cpu = cpu.copy()
        exit_mem = mem.copy()
        exit_states[addr] = (exit_cpu, exit_mem)

        # Propagate to successors.
        # For call fallthroughs, adjust SP to account for the callee's
        # return popping the return address that JSR/BSR pushed.
        call_sp_push = 0
        if block.instructions:
            last = block.instructions[-1]
            last_mn = _extract_mnemonic(last.text)
            last_ikb = _find_kb_entry(kb_by_name, last_mn,
                                      cc_test_defs, cc_aliases)
            if last_ikb:
                flow = last_ikb.get("pc_effects", {}).get("flow", {})
                if flow.get("type") == "call":
                    for eff in last_ikb.get("sp_effects", []):
                        if eff.get("action") == "decrement":
                            call_sp_push += eff["bytes"]

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
            # Call with fallthrough.  Apply summary to fallthrough
            # (SP delta + register preservation).  Also propagate
            # caller state into callee for concrete execution.
            # Build fallthrough state: summary provides SP delta +
            # register preservation.  Then apply scratch reg
            # invalidation + call effects (OS call return tags).
            summary = summaries.get(call_dst) if summaries else None
            if summary:
                ft_cpu = _apply_summary(exit_cpu, summary)
                # If the summary clobbered the app base register,
                # restore it.  Only the init routine does this —
                # its summary reports A6 as clobbered since
                # output != input, but we know the actual value.
                base_info = (platform.get("initial_base_reg")
                             if platform else None)
                if base_info:
                    breg_num, breg_val = base_info
                    if not ft_cpu.a[breg_num].is_known:
                        ft_cpu.set_reg("an", breg_num,
                                       _concrete(breg_val))
            else:
                ft_cpu = exit_cpu.copy()
                if exit_cpu.sp.is_known:
                    ft_cpu.sp = _concrete(
                        (exit_cpu.sp.concrete + call_sp_push)
                        & 0xFFFFFFFF)
                elif exit_cpu.sp.is_symbolic:
                    ft_cpu.sp = exit_cpu.sp.sym_add(call_sp_push)

            # Scratch reg invalidation on fallthrough (not on
            # callee — the callee receives pre-call register
            # state as input, e.g. D0 = LVO offset).
            if platform and platform.get("scratch_regs"):
                for reg_mode, reg_num in platform["scratch_regs"]:
                    ft_cpu.set_reg(reg_mode, reg_num, _unknown())

            # Apply pending call effect (from _apply_instruction's
            # OS call resolver) to post-invalidation state.
            if platform:
                call_effect = platform.pop("_pending_call_effect",
                                           None)
                if call_effect:
                    if "tag" in call_effect:
                        mode, num = _parse_reg_from_text(
                            call_effect["base_reg"])
                        ft_cpu.set_reg(mode, num,
                                       _unknown(tag=call_effect["tag"]))
                    elif "concrete" in call_effect:
                        mode, num = _parse_reg_from_text(
                            call_effect["result_reg"])
                        ft_cpu.set_reg(mode, num,
                                       _concrete(call_effect["concrete"]))
                    elif "output_type" in call_effect:
                        mode, num = _parse_reg_from_text(
                            call_effect["output_reg"])
                        ft_cpu.set_reg(mode, num,
                                       _unknown(tag=call_effect["output_type"]))

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


# ── Subroutine summaries ─────────────────────────────────────────────────

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
                     summaries: dict[int, dict | None],
                     code: bytes, base_addr: int,
                     kb_by_name: dict, cc_test_defs: dict,
                     cc_aliases: dict,
                     global_exit_states: dict | None = None,
                     ) -> dict | None:
    """Compute a subroutine summary by analyzing with symbolic inputs.

    Each register gets a unique symbolic value (D0_entry, A0_entry,
    SP_entry).  At RTS, registers whose symbolic value survived are
    preserved; others are clobbered.  No platform config — summaries
    track register preservation, not concrete OS call effects.

    Returns {"preserved_d": set, "preserved_a": set, "sp_delta": int}
    or None.
    """
    entry_cpu = CPUState()
    for i in range(len(entry_cpu.d)):
        entry_cpu.d[i] = _symbolic(f"D{i}_entry", 0)
    for i in range(len(entry_cpu.a)):
        entry_cpu.a[i] = _symbolic(f"A{i}_entry", 0)
    entry_cpu.sp = _symbolic("SP_entry", 0)

    incoming = {entry: {"_init": (entry_cpu.copy(), AbstractMemory())}}
    exit_states = {}
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

        cpu, mem = _join_states(list(pred_dict.values()))
        cpu.pc = addr

        if addr in visited and addr in exit_states:
            prev_cpu, _ = exit_states[addr]
            if (cpu.d == prev_cpu.d and cpu.a == prev_cpu.a
                    and cpu.sp == prev_cpu.sp):
                continue
        visited.add(addr)

        block = blocks[addr]
        for inst in block.instructions:
            mn = _extract_mnemonic(inst.text)
            ikb = _find_kb_entry(kb_by_name, mn, cc_test_defs, cc_aliases)
            if ikb:
                _apply_instruction(inst, ikb, cpu, mem, code, base_addr,
                                   None)  # no platform
            cpu.pc = inst.offset + inst.size
        exit_cpu = cpu.copy()
        exit_mem = mem.copy()
        exit_states[addr] = (exit_cpu, exit_mem)
        if global_exit_states is not None:
            global_exit_states[addr] = exit_states[addr]

        # Propagate to successors within the subroutine
        call_sp_push = 0
        if block.instructions:
            last = block.instructions[-1]
            last_mn = _extract_mnemonic(last.text)
            last_ikb = _find_kb_entry(kb_by_name, last_mn,
                                      cc_test_defs, cc_aliases)
            if last_ikb:
                flow = last_ikb.get("pc_effects", {}).get("flow", {})
                if flow.get("type") == "call":
                    for eff in last_ikb.get("sp_effects", []):
                        if eff.get("action") == "decrement":
                            call_sp_push += eff["bytes"]

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
            nested = summaries.get(call_dst)
            if nested:
                ft_cpu = _apply_summary(exit_cpu, nested)
                incoming.setdefault(ft_dst, {})[addr] = \
                    (ft_cpu, exit_mem)
            else:
                adj_cpu = exit_cpu.copy()
                if exit_cpu.sp.is_symbolic:
                    adj_cpu.sp = exit_cpu.sp.sym_add(call_sp_push)
                elif exit_cpu.sp.is_known:
                    adj_cpu.sp = _concrete(
                        (exit_cpu.sp.concrete + call_sp_push)
                        & 0xFFFFFFFF)
                incoming.setdefault(ft_dst, {})[addr] = \
                    (adj_cpu, exit_mem)
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
        mn = _extract_mnemonic(last.text)
        ikb = _find_kb_entry(kb_by_name, mn, cc_test_defs, cc_aliases)
        if ikb:
            flow = ikb.get("pc_effects", {}).get("flow", {})
            if flow.get("type") == "return" and addr in exit_states:
                rts_states.append(exit_states[addr])

    if not rts_states:
        return None

    rts_cpu, _ = _join_states(rts_states)

    preserved_d = {i for i in range(len(rts_cpu.d))
                   if rts_cpu.d[i].sym_base == f"D{i}_entry"
                   and rts_cpu.d[i].sym_offset == 0}
    preserved_a = {i for i in range(len(rts_cpu.a))
                   if rts_cpu.a[i].sym_base == f"A{i}_entry"
                   and rts_cpu.a[i].sym_offset == 0}
    sp_delta = 0
    if rts_cpu.sp.is_symbolic and rts_cpu.sp.sym_base == "SP_entry":
        sp_delta = rts_cpu.sp.sym_offset

    return {"preserved_d": preserved_d, "preserved_a": preserved_a,
            "sp_delta": sp_delta}


def _apply_summary(caller_cpu: "CPUState",
                   summary: dict) -> "CPUState":
    """Apply a subroutine summary to a caller's state.

    Preserved registers keep the caller's value.
    Clobbered registers become unknown.  SP adjusted by delta.
    """
    result = CPUState()
    for i in range(len(result.d)):
        result.d[i] = (caller_cpu.d[i] if i in summary["preserved_d"]
                       else _unknown())
    for i in range(len(result.a)):
        result.a[i] = (caller_cpu.a[i] if i in summary["preserved_a"]
                       else _unknown())
    delta = summary["sp_delta"]
    if caller_cpu.sp.is_symbolic:
        result.sp = caller_cpu.sp.sym_add(delta)
    elif caller_cpu.sp.is_known:
        result.sp = _concrete(
            (caller_cpu.sp.concrete + delta) & 0xFFFFFFFF)
    return result


def compute_all_summaries(blocks: dict[int, BasicBlock],
                          code: bytes, base_addr: int,
                          kb_by_name: dict, cc_test_defs: dict,
                          cc_aliases: dict,
                          existing: dict[int, dict | None] | None = None,
                          global_exit_states: dict | None = None,
                          ) -> dict[int, dict | None]:
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
            blk = blocks.get(addr)
            if blk:
                for xref in blk.xrefs:
                    if xref.type == "call" and xref.dst in sub_map:
                        calls.add(xref.dst)
        callees[entry] = calls

    # Topological sort — count only UN-summarized callees
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
            base_addr, kb_by_name, cc_test_defs, cc_aliases,
            global_exit_states)
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
                base_addr, kb_by_name, cc_test_defs, cc_aliases,
                global_exit_states)

    return summaries


# ── Public API ────────────────────────────────────────────────────────────

def analyze(code: bytes, base_addr: int = 0,
            entry_points: list[int] | None = None,
            propagate: bool = False,
            platform: dict | None = None) -> dict:
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

    result = {
        "blocks": blocks,
        "xrefs": all_xrefs,
        "call_targets": call_targets,
        "branch_targets": branch_targets,
    }

    if propagate:
        # Pre-compute subroutine summaries for SP delta + register
        # preservation on call fallthroughs.
        sums = None
        if platform and platform.get("initial_base_reg"):
            kb_by_name, _, meta = _load_kb()
            cc_test_defs = meta["cc_test_definitions"]
            cc_aliases = meta["cc_aliases"]
            existing = platform.get("_summary_cache")
            platform["_summary_cache"] = compute_all_summaries(
                blocks, code, base_addr,
                kb_by_name, cc_test_defs, cc_aliases,
                existing=existing)
            sums = platform["_summary_cache"]
        prop_states = propagate_states(
            blocks, code, base_addr, platform=platform,
            summaries=sums)
        result["exit_states"] = prop_states

    return result


# ── CLI ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from hunk_parser import parse_file, HunkType as HT

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
