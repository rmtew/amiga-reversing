"""Shared KB utilities for M68K analysis tools.

Provides common helpers used across jump_tables, os_calls, name_entities,
subroutine_scan, and build_entities. Single source of truth for KB access
patterns and encoding field extraction.
"""

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from m68k_executor import (_load_kb, _find_kb_entry, _extract_mnemonic,
                          _decode_ea, _extract_size, Operand, _xf)


class KB:
    """Cached KB access with common lookups pre-resolved."""

    def __init__(self):
        self.by_name, _, self.meta = _load_kb()
        self.cc_defs = self.meta["cc_test_definitions"]
        self.cc_aliases = self.meta["cc_aliases"]
        self.opword_bytes = self.meta["opword_bytes"]
        self.ea_enc = self.meta["ea_mode_encoding"]
        self.size_bytes = self.meta["size_byte_count"]
        self.align_mask = self.opword_bytes - 1
        # EA modes that use an address register as base for memory access
        # without side effects.  Derived from ea_mode_encoding: modes that
        # encode a register in the EA field (mode < 7) and are not register-
        # direct (dn/an) or auto-modify (postinc/predec).
        _direct = {"dn", "an"}
        _automod = {"postinc", "predec"}
        self.reg_indirect_modes = frozenset(
            name for name, (mode_val, reg_val) in self.ea_enc.items()
            if reg_val is None  # uses register field from EA
            and name not in _direct
            and name not in _automod)

    def find(self, mnemonic: str) -> dict | None:
        """Look up KB entry for a mnemonic (handles CC families)."""
        return _find_kb_entry(self.by_name, mnemonic,
                              self.cc_defs, self.cc_aliases)

    def flow_type(self, inst) -> tuple[str | None, bool]:
        """Get (flow_type, conditional) for a decoded instruction.

        Returns (None, False) if instruction has no flow effect or is
        not in KB.
        """
        mn = _extract_mnemonic(inst.text)
        ikb = self.find(mn)
        if ikb is None:
            return None, False
        pc_effects = ikb.get("pc_effects")
        if pc_effects is None:
            return None, False
        flow = pc_effects["flow"]
        return flow["type"], flow.get("conditional", False)

    def ea_field_spec(self, inst_kb: dict) -> tuple | None:
        """Extract (mode_field, reg_field) from KB encoding for EA instructions.

        Returns ((hi, lo, width), (hi, lo, width)) for source MODE and
        REGISTER fields, or None.
        """
        encodings = inst_kb.get("encodings", [])
        if not encodings:
            return None
        fields = encodings[0].get("fields", [])
        mode_f = reg_f = None
        for f in fields:
            if f["name"] == "MODE":
                mode_f = (f["bit_hi"], f["bit_lo"],
                          f["bit_hi"] - f["bit_lo"] + 1)
            elif f["name"] == "REGISTER" and f["bit_hi"] <= 5:
                reg_f = (f["bit_hi"], f["bit_lo"],
                         f["bit_hi"] - f["bit_lo"] + 1)
        if mode_f and reg_f:
            return mode_f, reg_f
        return None

    def dst_reg_field(self, inst_kb: dict) -> tuple | None:
        """Extract destination REGISTER field (higher bits) for MOVEA etc.

        For instructions with two REGISTER fields, returns the one at
        higher bit positions.
        """
        encodings = inst_kb.get("encodings", [])
        if not encodings:
            return None
        fields = encodings[0].get("fields", [])
        reg_fields = [f for f in fields if f["name"] == "REGISTER"]
        if len(reg_fields) < 2:
            return None
        reg_fields.sort(key=lambda f: f["bit_lo"], reverse=True)
        dst = reg_fields[0]
        return (dst["bit_hi"], dst["bit_lo"],
                dst["bit_hi"] - dst["bit_lo"] + 1)


def xf(opcode: int, field: tuple) -> int:
    """Extract a bit field from an opcode. field = (bit_hi, bit_lo, width)."""
    return (opcode >> field[1]) & ((1 << field[2]) - 1)


def decode_instruction_operands(inst_raw: bytes, inst_kb: dict,
                                meta: dict, size: str,
                                inst_offset: int) -> dict:
    """Decode source and destination operands from raw instruction bytes.

    Extracts structured operand info using KB encoding fields, without
    executing the instruction.  This is the same decode logic used in the
    executor's _apply_instruction, extracted for use by downstream tools.

    Returns dict with:
        ea_op: Operand from MODE/REGISTER (bits 5-0), or None
        dst_op: Operand from upper MODE/REGISTER (MOVE only), or None
        reg_num: register number from upper REGISTER field, or None
        imm_val: decoded immediate (from DATA field or extension words), or None
        ea_is_source: bool from OPMODE (None if no OPMODE)
    """
    result = {"ea_op": None, "dst_op": None, "reg_num": None,
              "imm_val": None, "ea_is_source": None}

    if len(inst_raw) < meta["opword_bytes"]:
        return result

    opcode = struct.unpack_from(">H", inst_raw, 0)[0]
    enc_fields = inst_kb.get("encodings", [{}])[0].get("fields", [])

    mode_fields = sorted(
        [f for f in enc_fields if f["name"] == "MODE"],
        key=lambda f: f["bit_lo"])
    reg_fields = sorted(
        [f for f in enc_fields if f["name"] == "REGISTER"],
        key=lambda f: f["bit_lo"])

    ext_pos = meta["opword_bytes"]

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
                inst_raw, meta["opword_bytes"],
                ea_mode, ea_reg, size, inst_offset)
            result["ea_op"] = ea_op
        except ValueError:
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
                    inst_raw, ext_pos,
                    d_mode, d_reg, size, inst_offset)
                result["dst_op"] = dst_op
            except ValueError:
                pass

    # Register number from REGISTER field.
    # With 2+ REGISTER fields: upper field is the "other" register (bits 11-9).
    # With exactly 1 REGISTER and no MODE: the sole REGISTER is the
    # destination (e.g. MOVEQ where DATA has the immediate).
    if len(reg_fields) >= 2:
        rf = reg_fields[-1]
        result["reg_num"] = _xf(opcode, (rf["bit_hi"], rf["bit_lo"],
                                         rf["bit_hi"] - rf["bit_lo"] + 1))
    elif len(reg_fields) == 1 and not mode_fields:
        rf = reg_fields[0]
        result["reg_num"] = _xf(opcode, (rf["bit_hi"], rf["bit_lo"],
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
                    result["ea_is_source"] = entry.get("ea_is_source")
                    break

    # Decode immediate value from opcode (KB-driven).
    # Pattern 1: DATA field in opcode (ADDQ/SUBQ/MOVEQ)
    # Pattern 2: extension word immediate (ADDI/SUBI/etc.)
    imm_range = inst_kb.get("constraints", {}).get("immediate_range")
    data_field_name = imm_range.get("field") if imm_range else None
    if data_field_name:
        df = next((f for f in enc_fields
                   if f["name"] == data_field_name), None)
        if df:
            raw_val = _xf(opcode, (df["bit_hi"], df["bit_lo"],
                                   df["bit_hi"] - df["bit_lo"] + 1))
            if imm_range.get("zero_means") and raw_val == 0:
                raw_val = imm_range["zero_means"]
            if imm_range.get("signed"):
                bits = imm_range["bits"]
                if raw_val >= (1 << (bits - 1)):
                    raw_val -= (1 << bits)
                raw_val &= 0xFFFFFFFF
            result["imm_val"] = raw_val

    elif (not opmode_table and not data_field_name
          and mode_fields and not imm_range):
        # Pattern 2: extension word immediate (ADDI etc.)
        imm_bytes = meta["size_byte_count"].get(
            size, meta["size_byte_count"]["w"])
        pos = meta["opword_bytes"]
        if pos + imm_bytes <= len(inst_raw):
            if imm_bytes <= 2:
                imm_val = struct.unpack_from(">H", inst_raw, pos)[0]
                if size == "b":
                    imm_val &= 0xFF
            else:
                imm_val = struct.unpack_from(">I", inst_raw, pos)[0]
            result["imm_val"] = imm_val
            # Re-decode EA after the immediate
            if mode_fields and reg_fields:
                mf = mode_fields[0]
                rf = reg_fields[0]
                ea_m = _xf(opcode, (mf["bit_hi"], mf["bit_lo"],
                                    mf["bit_hi"] - mf["bit_lo"] + 1))
                ea_r = _xf(opcode, (rf["bit_hi"], rf["bit_lo"],
                                    rf["bit_hi"] - rf["bit_lo"] + 1))
                try:
                    ea_op, _ = _decode_ea(
                        inst_raw, pos + max(imm_bytes, 2),
                        ea_m, ea_r, size, inst_offset)
                    result["ea_op"] = ea_op
                except ValueError:
                    pass

    return result


def decode_destination(inst_raw: bytes, inst_kb: dict,
                       meta: dict, size: str,
                       inst_offset: int) -> tuple[str, int] | None:
    """Determine the destination register of an instruction.

    Returns (mode, reg_num) where mode is "dn" or "an", or None if the
    destination cannot be determined from opcode bits.

    Handles:
    - MOVE/MOVEA: dst_op from upper MODE/REGISTER fields
    - OPMODE instructions: ea_is_source=False means EA is dst, else reg_num
    - Single-EA + reg_num: destination is the upper REGISTER (e.g. LEA)
    """
    decoded = decode_instruction_operands(
        inst_raw, inst_kb, meta, size, inst_offset)

    # MOVE/MOVEA: has dst_op with explicit mode
    dst_op = decoded["dst_op"]
    if dst_op is not None:
        if dst_op.mode in ("dn", "an"):
            return (dst_op.mode, dst_op.reg)
        return None  # destination is memory, not a register

    # OPMODE instructions (ADD, SUB, AND, OR, etc.)
    ea_is_source = decoded["ea_is_source"]
    ea_op = decoded["ea_op"]
    reg_num = decoded["reg_num"]
    if ea_is_source is not None:
        if ea_is_source:
            # EA is source -> destination is the upper register (Dn)
            if reg_num is not None:
                return ("dn", reg_num)
        else:
            # EA is destination
            if ea_op and ea_op.mode in ("dn", "an"):
                return (ea_op.mode, ea_op.reg)
        return None

    # Single-EA with upper register: LEA, MOVEA-like, etc.
    # Check if instruction writes to An via source_sign_extend (MOVEA pattern)
    if inst_kb.get("source_sign_extend") and reg_num is not None:
        return ("an", reg_num)

    # Default: reg_num is destination Dn (MOVEQ, ADDQ to Dn, etc.)
    if reg_num is not None:
        # If ea_op is a register and no OPMODE, check operation_type
        op_type = inst_kb.get("operation_type")
        if op_type == "move":
            return ("dn", reg_num)
        # For ALU ops without OPMODE (ADDQ/SUBQ), EA is the destination
        if ea_op and ea_op.mode in ("dn", "an"):
            return (ea_op.mode, ea_op.reg)

    return None


def parse_reg_name(name: str) -> tuple[str, int]:
    """Parse a register name like "D0"/"A1" to ("dn", 0)/("an", 1).

    Raises ValueError on unrecognized format.
    """
    name = name.strip().upper()
    if len(name) == 2 and name[1].isdigit():
        if name[0] == "D":
            return ("dn", int(name[1]))
        if name[0] == "A":
            return ("an", int(name[1]))
    raise ValueError(f"Cannot parse register name: {name}")


def read_string_at(data: bytes, addr: int, max_len: int = 64) -> str | None:
    """Read a null-terminated ASCII string from data bytes.

    Returns None if addr is out of range or string is empty/non-ASCII.
    """
    if addr >= len(data):
        return None
    end = min(addr + max_len, len(data))
    result = []
    for i in range(addr, end):
        b = data[i]
        if b == 0:
            break
        result.append(b)
    if not result:
        return None
    try:
        return bytes(result).decode("ascii")
    except UnicodeDecodeError:
        return None


def find_containing_sub(addr: int, sorted_subs: list[dict]) -> int | None:
    """Binary search for the subroutine containing addr.

    sorted_subs: list of dicts with int "addr" and "end" keys, sorted by addr.
    Returns the subroutine's start address, or None.
    """
    lo, hi = 0, len(sorted_subs) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        s = sorted_subs[mid]
        if addr < s["addr"]:
            hi = mid - 1
        elif addr >= s["end"]:
            lo = mid + 1
        else:
            return s["addr"]
    return None
