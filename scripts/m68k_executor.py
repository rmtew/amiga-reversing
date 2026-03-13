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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from m68k_compute import (predict_cc, predict_sp, evaluate_cc_test,
                          _compute_result, _size_mask, _to_signed)
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
    if addr_regs:
        meta["_sp_reg_num"] = int(addr_regs[-1][1:])
    else:
        meta["_sp_reg_num"] = 7  # fallback

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
        brief = meta.get("ea_brief_ext_word", [])
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
        brief = meta.get("ea_brief_ext_word", [])
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


# ── Abstract state ────────────────────────────────────────────────────────

@dataclass
class AbstractValue:
    """A value that may be concrete or symbolic."""
    concrete: int | None = None     # known concrete value, or None if unknown
    label: str | None = None        # symbolic label (e.g., "A0_init", "mem[0x1234]")

    @property
    def is_known(self) -> bool:
        return self.concrete is not None

    def __repr__(self):
        if self.concrete is not None:
            return f"${self.concrete:08x}"
        return f"?{self.label or ''}"


def _concrete(val: int) -> AbstractValue:
    return AbstractValue(concrete=val & 0xFFFFFFFF)


def _unknown(label: str = "") -> AbstractValue:
    return AbstractValue(label=label)


def _make_cpu_state_class():
    """Build CPUState class with register layout derived from KB."""
    _, _, meta = _load_kb()
    num_d = meta["_num_data_regs"]
    num_a = meta["_num_addr_regs"]
    sp_reg = meta["_sp_reg_num"]
    ccr_flags = list(meta["ccr_bit_positions"].keys())

    @dataclass
    class CPUState:
        """Abstract CPU state for symbolic execution.

        Register layout derived from KB movem_reg_masks and ccr_bit_positions.
        """
        d: list[AbstractValue] = field(
            default_factory=lambda: [_unknown(f"D{i}") for i in range(num_d)])
        a: list[AbstractValue] = field(
            default_factory=lambda: [_unknown(f"A{i}") for i in range(num_a)])
        sp: AbstractValue = field(default_factory=lambda: _unknown("SP"))
        pc: int = 0
        ccr: dict[str, int | None] = field(
            default_factory=lambda: {f: None for f in ccr_flags})

        def get_reg(self, mode: str, reg: int) -> AbstractValue:
            """Read a register by EA mode name and register number."""
            if mode == "dn":
                return self.d[reg]
            elif mode == "an":
                if reg == sp_reg:
                    return self.sp
                return self.a[reg]
            raise ValueError(f"get_reg: unsupported mode '{mode}'")

        def set_reg(self, mode: str, reg: int, val: AbstractValue):
            """Write a register by EA mode name and register number."""
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
            """Create an independent copy of this state."""
            s = CPUState()
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
    # Build size suffixes from KB: ".b", ".w", ".l" from size_byte_count,
    # plus ".s" which is the short branch form (displacement_encoding uses
    # the 8-bit field for byte-sized branches)
    size_suffixes = ["." + s for s in meta["size_byte_count"]] + [".s"]
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

    print(f"WARNING: _find_kb_entry: no KB entry for '{mnemonic}'",
          file=sys.stderr)
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
    cc_families = meta["_cc_families"]

    text = inst.text.strip()
    raw = inst.raw
    mnemonic = _extract_mnemonic(text)
    mn_upper = mnemonic.upper()

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
        absw_enc = ea_enc.get("absw", [7, 0])
        absl_enc = ea_enc.get("absl", [7, 1])
        pcdisp_enc = ea_enc.get("pcdisp", [7, 2])

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


# ── Public API ────────────────────────────────────────────────────────────

def analyze(code: bytes, base_addr: int = 0,
            entry_points: list[int] | None = None) -> dict:
    """Analyze code and return structured results.

    Returns dict with:
        blocks: dict[int, BasicBlock] — basic blocks keyed by start address
        xrefs: list[XRef] — all cross-references
        call_targets: set[int] — addresses that are call targets (subroutines)
        branch_targets: set[int] — addresses that are branch targets
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

    return {
        "blocks": blocks,
        "xrefs": all_xrefs,
        "call_targets": call_targets,
        "branch_targets": branch_targets,
    }


# ── CLI ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from hunk_parser import parse_file, HunkType as HT

    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <hunk_file>")
        sys.exit(1)

    hf = parse_file(sys.argv[1])
    for hunk in hf.hunks:
        if hunk.hunk_type != HT.HUNK_CODE:
            continue
        print(f"; === Hunk #{hunk.index} CODE ({len(hunk.data)} bytes) ===")
        result = analyze(hunk.data)
        blocks = result["blocks"]

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
            print()
