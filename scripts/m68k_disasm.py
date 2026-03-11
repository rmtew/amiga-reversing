"""M68K disassembler targeting vasm-compatible Motorola syntax.

Decodes 68000 instructions from raw bytes and emits assembly text.
"""

import json
import re
import struct
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass
class Instruction:
    offset: int       # byte offset within hunk
    size: int         # total instruction size in bytes
    opcode: int       # first word
    text: str         # disassembled text (mnemonic + operands)
    raw: bytes        # raw instruction bytes


class DecodeError(Exception):
    pass


SIZE_BYTE = 0
SIZE_WORD = 1
SIZE_LONG = 2

SIZE_SUFFIX = {SIZE_BYTE: ".b", SIZE_WORD: ".w", SIZE_LONG: ".l"}
SIZE_NAMES = {SIZE_BYTE: "byte", SIZE_WORD: "word", SIZE_LONG: "long"}
_SIZE_LETTER_TO_INT = {"b": SIZE_BYTE, "w": SIZE_WORD, "l": SIZE_LONG}
CC_CONDITION_TABLE = re.compile(r"\b([A-Za-z]{2})\s+[A-Za-z]\s+(?:set|clear)\b")


def _normalize_cpu(cpu_name: str | None) -> str:
    """Strip vasm -m prefix from cpu flag strings (e.g. '-m68000' -> '68000')."""
    if not cpu_name:
        return "68000"
    if cpu_name.startswith("-m"):
        cpu_name = cpu_name[2:]
    return cpu_name


def _load_kb_payload() -> tuple[list[dict], dict]:
    path = Path(__file__).resolve().parent.parent / "knowledge" / "m68k_instructions.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["instructions"], data["_meta"]


def _kb_encoding_masks(enc_idx: int) -> dict[str, tuple[int, int]]:
    """Return {mnemonic: (mask, val)} computed from KB encoding[enc_idx] fixed fields."""
    kb, _ = _load_kb_payload()
    result: dict[str, tuple[int, int]] = {}
    for inst in kb:
        encs = inst["encodings"]
        if len(encs) <= enc_idx:
            continue
        fields = encs[enc_idx]["fields"]
        mask = val = 0
        for f in fields:
            if f["name"] in ("0", "1"):
                bit = 1 if f["name"] == "1" else 0
                for b in range(f["bit_lo"], f["bit_hi"] + 1):
                    mask |= (1 << b)
                    val |= (bit << b)
        if mask:
            result[inst["mnemonic"]] = (mask, val)
    return result


@lru_cache(maxsize=1)
def _load_kb_encoding_masks() -> dict[str, tuple[int, int]]:
    """Return {mnemonic: (mask, val)} from opword (encoding[0]) fixed fields."""
    return _kb_encoding_masks(0)


@lru_cache(maxsize=1)
def _load_kb_ext_encoding_masks() -> dict[str, tuple[int, int]]:
    """Return {mnemonic: (mask, val)} from extension word (encoding[1]) fixed fields."""
    return _kb_encoding_masks(1)


@lru_cache(maxsize=4)
def _load_kb_encoding_masks_idx(enc_idx: int) -> dict[str, tuple[int, int]]:
    """Return {mnemonic: (mask, val)} from encoding[enc_idx] fixed fields."""
    return _kb_encoding_masks(enc_idx)


@lru_cache(maxsize=1)
def _load_kb_fixed_opcodes() -> dict[int, str]:
    """Return {opcode_value: mnemonic} for all instructions where mask=0xFFFF.

    These are zero-operand or fixed-format instructions (NOP, RESET, RTE, RTS, etc.)
    """
    masks = _load_kb_encoding_masks()
    return {val: mn for mn, (mask, val) in masks.items() if mask == 0xFFFF}


@lru_cache(maxsize=1)
def _load_kb_ext_field_names() -> dict[str, frozenset[str]]:
    """Return {mnemonic: frozenset(ext_word_field_names)} for instructions with
    extension words.  Uses encoding[1] field names (excluding fixed 0/1 bits)."""
    kb, _ = _load_kb_payload()
    result: dict[str, frozenset[str]] = {}
    for inst in kb:
        encs = inst["encodings"]
        if len(encs) < 2:
            continue
        names = frozenset(
            f["name"] for f in encs[1]["fields"]
            if f["name"] not in ("0", "1")
        )
        if names:
            result[inst["mnemonic"]] = names
    return result


def _kb_field_map(enc_idx: int) -> dict[str, dict[str, tuple[int, int, int]]]:
    """Return {mnemonic: {field_name: (bit_hi, bit_lo, width)}} for a given encoding index.

    Extracts named fields (excluding fixed 0/1 bits) from encoding[enc_idx].
    """
    kb, _ = _load_kb_payload()
    result: dict[str, dict[str, tuple[int, int, int]]] = {}
    for inst in kb:
        encs = inst["encodings"]
        if len(encs) <= enc_idx:
            continue
        fields = {}
        for f in encs[enc_idx]["fields"]:
            if f["name"] not in ("0", "1"):
                fields[f["name"]] = (f["bit_hi"], f["bit_lo"], f["width"])
        if fields:
            result[inst["mnemonic"]] = fields
    return result


@lru_cache(maxsize=1)
def _load_kb_opword_field_map() -> dict[str, dict[str, tuple[int, int, int]]]:
    """Return {mnemonic: {field_name: (bit_hi, bit_lo, width)}} for opwords (encoding[0])."""
    return _kb_field_map(0)


@lru_cache(maxsize=1)
def _load_kb_ext_field_map() -> dict[str, dict[str, tuple[int, int, int]]]:
    """Return {mnemonic: {field_name: (bit_hi, bit_lo, width)}} for extension words (encoding[1])."""
    return _kb_field_map(1)


@lru_cache(maxsize=1)
def _load_kb_ext2_field_map() -> dict[str, dict[str, tuple[int, int, int]]]:
    """Return {mnemonic: {field_name: (bit_hi, bit_lo, width)}} for encoding[2]."""
    return _kb_field_map(2)


@lru_cache(maxsize=4)
def _load_kb_raw_fields(enc_idx: int) -> dict[str, list[tuple[str, int, int, int]]]:
    """Return {mnemonic: [(name, bit_hi, bit_lo, width), ...]} preserving duplicate field names.

    Unlike _kb_field_map() which deduplicates by name, this preserves all fields
    in their original order — needed for instructions with duplicate REGISTER or MODE fields
    (MOVE, LEA, CHK, ADD, etc.).
    """
    kb, _ = _load_kb_payload()
    result: dict[str, list[tuple[str, int, int, int]]] = {}
    for inst in kb:
        encs = inst["encodings"]
        if len(encs) <= enc_idx:
            continue
        fields = []
        for f in encs[enc_idx]["fields"]:
            if f["name"] not in ("0", "1"):
                fields.append((f["name"], f["bit_hi"], f["bit_lo"], f["width"]))
        if fields:
            result[inst["mnemonic"]] = fields
    return result


@lru_cache(maxsize=1)
def _load_kb_ea_brief_fields() -> dict[str, tuple[int, int, int]]:
    """Return {field_name: (bit_hi, bit_lo, width)} for Brief Extension Word fields."""
    _, meta = _load_kb_payload()
    result: dict[str, tuple[int, int, int]] = {}
    for f in meta["ea_brief_ext_word"]:
        width = f["bit_hi"] - f["bit_lo"] + 1
        result[f["name"]] = (f["bit_hi"], f["bit_lo"], width)
    return result


@lru_cache(maxsize=1)
def _load_kb_movem_reg_masks() -> dict[str, list[str]]:
    """Return {"normal": [...], "predecrement": [...]} register mask tables from KB."""
    _, meta = _load_kb_payload()
    return meta["movem_reg_masks"]


def _derive_varying_bits(mask_val_pairs: list[tuple[int, int]]) -> tuple[int, int]:
    """XOR encoding vals to find the contiguous bit range that distinguishes related instructions.

    Returns (bit_hi, bit_lo).
    """
    if len(mask_val_pairs) < 2:
        raise RuntimeError("need at least 2 mask/val pairs to derive varying bits")
    # XOR all vals together to find bits that vary
    varying = 0
    base_val = mask_val_pairs[0][1]
    for _, v in mask_val_pairs[1:]:
        varying |= base_val ^ v
    # Also check all pairs against each other
    for i in range(len(mask_val_pairs)):
        for j in range(i + 1, len(mask_val_pairs)):
            varying |= mask_val_pairs[i][1] ^ mask_val_pairs[j][1]
    if varying == 0:
        raise RuntimeError("all vals are identical — cannot derive varying bits")
    bit_lo = (varying & -varying).bit_length() - 1
    bit_hi = varying.bit_length() - 1
    return bit_hi, bit_lo


@lru_cache(maxsize=1)
def _load_kb_dest_reg_field() -> dict[str, tuple[int, int, int]]:
    """Return {mnemonic: (bit_hi, bit_lo, width)} for the UPPER REGISTER field (bits 11:9).

    Scans _load_kb_raw_fields(0) for instructions with duplicate REGISTER fields
    and returns the one with higher bit position. For instructions with a single
    REGISTER field at bits 11:9, also includes those.
    """
    raw = _load_kb_raw_fields(0)
    result: dict[str, tuple[int, int, int]] = {}
    for mn, fields in raw.items():
        reg_fields = [(name, hi, lo, w) for name, hi, lo, w in fields if name == "REGISTER"]
        if len(reg_fields) >= 2:
            # Multiple REGISTER fields — take the highest one (destination reg at bits 11:9)
            upper = max(reg_fields, key=lambda f: f[1])
            result[mn] = (upper[1], upper[2], upper[3])
        elif len(reg_fields) == 1 and reg_fields[0][1] >= 9:
            # Single REGISTER at upper position (e.g., MOVEQ)
            result[mn] = (reg_fields[0][1], reg_fields[0][2], reg_fields[0][3])
    return result


@lru_cache(maxsize=1)
def _load_kb_bf_mnemonics() -> list[str]:
    """Return BFxxx mnemonics from KB (group E, size_bits=3 instructions)."""
    masks = _load_kb_encoding_masks()
    return [mn for mn in masks if mn.startswith("BF")]


@lru_cache(maxsize=1)
def _load_kb_bitop_names() -> tuple[dict[int, str], tuple[int, int, int]]:
    """Derive bit-op name table from KB: ({bit_index: mnemonic}, field_tuple).

    BTST/BCHG/BCLR/BSET are distinguished by varying bits in their encoding vals.
    Returns the name table and the (bit_hi, bit_lo, width) field for runtime extraction.
    """
    masks = _load_kb_encoding_masks()
    _mns = ("BTST", "BCHG", "BCLR", "BSET")
    pairs = [masks[mn] for mn in _mns]
    hi, lo = _derive_varying_bits(pairs)
    w = hi - lo + 1
    result: dict[int, str] = {}
    for mn in _mns:
        _, val = masks[mn]
        idx = (val >> lo) & ((1 << w) - 1)
        result[idx] = mn.lower()
    return result, (hi, lo, w)


@lru_cache(maxsize=1)
def _load_kb_imm_names() -> tuple[dict[int, str], tuple[int, int, int]]:
    """Derive immediate-op name table from KB: ({top_bits: mnemonic}, field_tuple).

    ORI/ANDI/SUBI/ADDI/EORI/CMPI are distinguished by varying bits in their encoding vals.
    Returns the name table and the (bit_hi, bit_lo, width) field for runtime extraction.
    """
    masks = _load_kb_encoding_masks()
    _mns = ("ORI", "ANDI", "SUBI", "ADDI", "EORI", "CMPI")
    pairs = [masks[mn] for mn in _mns]
    hi, lo = _derive_varying_bits(pairs)
    w = hi - lo + 1
    result: dict[int, str] = {}
    for mn in _mns:
        _, val = masks[mn]
        idx = (val >> lo) & ((1 << w) - 1)
        result[idx] = mn.lower()
    return result, (hi, lo, w)


@lru_cache(maxsize=1)
def _load_kb_shift_names() -> dict[int, str]:
    """Derive shift/rotate name table from KB: {type_index: prefix}.

    ASL/ASR, LSL/LSR, ROXL/ROXR, ROL/ROR are distinguished by varying bits
    in their register-mode encoding[0] vals.
    """
    masks = _load_kb_encoding_masks()
    _mns = ("ASL, ASR", "LSL, LSR", "ROXL, ROXR", "ROL, ROR")
    _prefixes = ("as", "ls", "rox", "ro")
    pairs = [masks[mn] for mn in _mns]
    hi, lo = _derive_varying_bits(pairs)
    w = hi - lo + 1
    result: dict[int, str] = {}
    for mn, prefix in zip(_mns, _prefixes):
        _, val = masks[mn]
        idx = (val >> lo) & ((1 << w) - 1)
        result[idx] = prefix
    return result


@lru_cache(maxsize=1)
def _load_kb_shift_type_fields() -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    """Derive shift type extraction fields for register and memory modes.

    Returns (reg_type_field, mem_type_field) as (bit_hi, bit_lo, width) tuples.
    """
    _mns = ("ASL, ASR", "LSL, LSR", "ROXL, ROXR", "ROL, ROR")
    # Register mode: encoding[0] vals
    reg_pairs = [_kb_encoding_masks(0)[mn] for mn in _mns]
    rhi, rlo = _derive_varying_bits(reg_pairs)
    # Memory mode: encoding[1] vals
    mem_pairs = [_kb_encoding_masks(1)[mn] for mn in _mns]
    mhi, mlo = _derive_varying_bits(mem_pairs)
    return (rhi, rlo, rhi - rlo + 1), (mhi, mlo, mhi - mlo + 1)


@lru_cache(maxsize=1)
def _load_kb_shift_fields() -> dict:
    """Load shift/rotate field rules from KB.

    Returns dict with:
      dr_values:  {0: "r", 1: "l"} direction mapping
      zero_means: value to substitute when count field is 0 (e.g. 8)
    """
    kb, _ = _load_kb_payload()
    for inst in kb:
        if inst["mnemonic"].startswith("ASL"):
            dv = inst["constraints"]["direction_variants"]
            dr_values = {int(k): v for k, v in dv["values"].items()}
            imm_range = inst["constraints"]["immediate_range"]
            return {
                "dr_values": dr_values,
                "zero_means": imm_range["zero_means"],
            }
    raise RuntimeError("KB missing ASL/ASR — regenerate m68k_instructions.json")


_SIZE_NAME_MAP = {"byte": SIZE_BYTE, "word": SIZE_WORD, "long": SIZE_LONG}


def _xf(op: int, field: tuple[int, int, int]) -> int:
    """Extract named field from opword/extword. field is (bit_hi, bit_lo, width)."""
    return (op >> field[1]) & ((1 << field[2]) - 1)


@lru_cache(maxsize=1)
def _load_kb_rm_field() -> dict[str, tuple[int, dict[int, str]]]:
    """Load R/M field position and value mapping from KB operand_modes.

    Returns {mnemonic: (bit_lo, {0: 'dn,dn', 1: 'predec,predec'})}.
    """
    kb, _ = _load_kb_payload()
    result: dict[str, tuple[int, dict[int, str]]] = {}
    for inst in kb:
        om = inst.get("constraints", {}).get("operand_modes")
        if not om or om.get("field") != "R/M":
            continue
        # Get R/M field position from encoding
        fields = _load_kb_opword_field_map().get(inst["mnemonic"], {})
        rm_field = fields.get("R/M")
        if not rm_field:
            continue
        values = {int(k): v for k, v in om["values"].items()}
        result[inst["mnemonic"]] = (rm_field[0], values)  # (bit_pos, value_map)
    return result


@lru_cache(maxsize=1)
def _load_kb_addq_zero_means() -> int:
    """Load the zero_means value for ADDQ/SUBQ from KB immediate_range."""
    kb, _ = _load_kb_payload()
    for inst in kb:
        if inst["mnemonic"] == "ADDQ":
            return inst["constraints"]["immediate_range"]["zero_means"]
    raise RuntimeError("KB missing ADDQ — regenerate m68k_instructions.json")


@lru_cache(maxsize=1)
def _load_kb_control_registers() -> dict[int, str]:
    """Load MOVEC control register names from KB: {hex_code: abbreviation}."""
    kb, _ = _load_kb_payload()
    for inst in kb:
        if inst["mnemonic"] == "MOVEC":
            ctrl_regs = inst["constraints"]["control_registers"]
            result: dict[int, str] = {}
            for cr in ctrl_regs:
                hex_val = int(cr["hex"], 16)
                # First occurrence wins (avoids EC040 aliases overwriting)
                if hex_val not in result:
                    result[hex_val] = cr["abbrev"]
            return result
    raise RuntimeError("KB missing MOVEC — regenerate m68k_instructions.json")


@lru_cache(maxsize=1)
def _load_kb_size_encodings() -> dict[str, dict[int, int]]:
    """Parse size encoding mappings from KB field_descriptions.

    Returns {mnemonic: {binary_val: SIZE_xxx}} derived from the Size field
    description text, e.g. "01 — Byte operation 10 — Word operation 11 — Long".
    """
    kb, _ = _load_kb_payload()
    result: dict[str, dict[int, int]] = {}
    for inst in kb:
        fd = inst["field_descriptions"]
        size_desc = fd.get("Size", "")
        if not size_desc:
            continue
        mapping: dict[int, int] = {}
        for m in re.finditer(r"([01]{1,2})\s*[\u2014\u2013\-]\s*(Byte|Word|Long)", size_desc, re.IGNORECASE):
            bits = int(m.group(1), 2)
            mapping[bits] = _SIZE_NAME_MAP[m.group(2).lower()]
        if mapping:
            result[inst["mnemonic"]] = mapping
    return result


@lru_cache(maxsize=1)
def _load_kb_processor_mins() -> dict[str, str]:
    kb, _ = _load_kb_payload()

    mins: dict[str, str] = {}
    for inst in kb:
        min_cpu = _normalize_cpu(inst["processor_min"])
        mnemonic = inst["mnemonic"]
        for part in mnemonic.split(","):
            tokens = part.strip().split()
            if not tokens:
                continue
            # Keep full token and individual alias tokens like "ASL" and "ASR".
            for token in tokens:
                mins[token.lower()] = min_cpu
    return mins


@lru_cache(maxsize=1)
def _load_kb_opmode_tables() -> dict[str, dict[int, dict]]:
    """Return {mnemonic: {opmode_int: {size, operation/description}}} from KB."""
    kb, _ = _load_kb_payload()
    result: dict[str, dict[int, dict]] = {}
    for inst in kb:
        opm = inst.get("constraints", {}).get("opmode_table")
        if not opm:
            continue
        table: dict[int, dict] = {}
        for entry in opm:
            table[entry["opmode"]] = entry
        result[inst["mnemonic"]] = table
    return result


@lru_cache(maxsize=1)
def _load_disasm_meta() -> dict:
    kb, kb_meta = _load_kb_payload()

    condition_codes = list(kb_meta["condition_codes"])
    cpu_hierarchy = kb_meta["cpu_hierarchy"]
    pmmu_condition_codes = kb_meta["pmmu_condition_codes"]

    families = {}
    for inst in kb:
        constraints = inst.get("constraints", {})
        cc_param = constraints.get("cc_parameterized")

        for raw_name in inst["mnemonic"].split(","):
            name = raw_name.strip().lower().replace(" ", "")
            if not name or not name.endswith("cc"):
                continue

            prefix = name[:-2]
            if not prefix:
                continue

            entry = families.get(name)
            if entry is None:
                entry = {
                    "prefix": prefix,
                    "canonical": name,
                    "codes": condition_codes[:],
                    "excluded": set(),
                }
                families[name] = entry

            if cc_param:
                if cc_param.get("excluded"):
                    entry["excluded"].update(
                        code.lower() for code in cc_param.get("excluded", [])
                    )
                continue

            description = inst["description"]
            parsed_codes = [
                code.lower()
                for code in CC_CONDITION_TABLE.findall(description)
            ]
            if parsed_codes:
                entry["codes"] = parsed_codes

    canonical_families = []
    for entry in families.values():
        codes = entry["codes"]
        if not codes:
            continue
        canonical_families.append({
            "prefix": entry["prefix"],
            "canonical": entry["canonical"],
            "codes": codes,
            "exclude_from_family": sorted(entry["excluded"]),
        })

    # Ensure deterministic ordering.
    canonical_families = sorted(
        canonical_families,
        key=lambda item: item["canonical"]
    )

    return {
        "condition_codes": condition_codes,
        "condition_families": canonical_families,
        "cpu_hierarchy": cpu_hierarchy,
        "pmmu_condition_codes": pmmu_condition_codes,
    }


def _canonical_mnemonic(decoded: str) -> str:
    """Normalize a decoded token to a KB mnemonic key."""
    tok = decoded.split(".", 1)[0].lower()
    if tok in ("", "#"):
        return tok

    meta = _load_disasm_meta()
    families = meta["condition_families"]

    for fam in families:
        prefix = fam["prefix"]
        if not prefix:
            continue
        if not tok.startswith(prefix):
            continue
        suffix = tok[len(prefix):]
        if suffix not in fam["codes"]:
            continue
        if tok in fam["exclude_from_family"]:
            continue
        return fam["canonical"]

    return tok


def _ensure_cpu_supported(decoded_text: str, max_cpu: str | None) -> None:
    if not max_cpu:
        return

    max_cpu = _normalize_cpu(max_cpu)
    cpu_hier = _load_disasm_meta()["cpu_hierarchy"]
    cpu_order = cpu_hier["order"]
    cpu_aliases = cpu_hier["aliases"]

    max_cpu = cpu_aliases.get(max_cpu, max_cpu)
    if max_cpu not in cpu_order:
        return

    canonical = _canonical_mnemonic(decoded_text)
    required_cpu = _load_kb_processor_mins().get(canonical)
    if required_cpu is None:
        return

    required_cpu = cpu_aliases.get(required_cpu, required_cpu)
    if cpu_order.index(required_cpu) > cpu_order.index(max_cpu):
        raise DecodeError(
            f"unsupported instruction '{canonical}' for max_cpu={max_cpu}; "
            f"requires {required_cpu}"
        )


class _Decoder:
    """Stateful instruction decoder."""

    def __init__(self, data: bytes, base_offset: int = 0):
        self.data = data
        self.base = base_offset
        self.pos = 0

    def remaining(self) -> int:
        return len(self.data) - self.pos

    def peek_u16(self) -> int:
        return struct.unpack_from(">H", self.data, self.pos)[0]

    def read_u16(self) -> int:
        val = struct.unpack_from(">H", self.data, self.pos)[0]
        self.pos += 2
        return val

    def read_i16(self) -> int:
        val = struct.unpack_from(">h", self.data, self.pos)[0]
        self.pos += 2
        return val

    def read_u32(self) -> int:
        val = struct.unpack_from(">I", self.data, self.pos)[0]
        self.pos += 4
        return val

    def read_i32(self) -> int:
        val = struct.unpack_from(">i", self.data, self.pos)[0]
        self.pos += 4
        return val


def _extract_size_bits(op: int, size_field: tuple, sz_enc: dict[int, int]) -> int:
    """Extract size bits from opword using KB field position and encoding values.

    The KB field width may be inflated by orphan expansion (e.g., 2 bits when only
    1 is needed).  Derive the effective width from the encoding's max value.
    """
    bit_hi = size_field[0]
    max_val = max(sz_enc.keys()) if sz_enc else 0
    eff_w = max(max_val.bit_length(), 1)
    return (op >> (bit_hi - eff_w + 1)) & ((1 << eff_w) - 1)


def _reg_name(reg: int, is_addr: bool = False) -> str:
    if is_addr:
        return f"a{reg}" if reg < 7 else "sp"
    return f"d{reg}"


def _ea_str(d: _Decoder, mode: int, reg: int, size: int, pc_offset: int) -> str:
    """Decode effective address and return string representation.

    pc_offset: byte offset of the instruction start (for PC-relative).
    """
    if mode == 0:  # Dn
        return _reg_name(reg)
    elif mode == 1:  # An
        return _reg_name(reg, True)
    elif mode == 2:  # (An)
        return f"({_reg_name(reg, True)})"
    elif mode == 3:  # (An)+
        return f"({_reg_name(reg, True)})+"
    elif mode == 4:  # -(An)
        return f"-({_reg_name(reg, True)})"
    elif mode == 5:  # d16(An)
        disp = d.read_i16()
        return f"{disp}({_reg_name(reg, True)})"
    elif mode == 6:  # d8(An,Xn)
        ext = d.read_u16()
        bf = _load_kb_ea_brief_fields()
        xreg = _xf(ext, bf["REGISTER"])
        xtype = "a" if _xf(ext, bf["D/A"]) == 1 else "d"
        xsize = ".l" if _xf(ext, bf["W/L"]) == 1 else ".w"
        disp = _xf(ext, bf["DISPLACEMENT"])
        disp_width = bf["DISPLACEMENT"][2]
        if disp & (1 << (disp_width - 1)):
            disp -= (1 << disp_width)
        return f"{disp}({_reg_name(reg, True)},{xtype}{xreg}{xsize})"
    elif mode == 7:
        if reg == 0:  # abs.w
            addr = d.read_i16()
            if addr < 0:
                return f"(${''.join(f'{b:02x}' for b in struct.pack('>h', addr))}).w"
            return f"(${addr:04x}).w"
        elif reg == 1:  # abs.l
            addr = d.read_u32()
            return f"${addr:08x}"
        elif reg == 2:  # d16(PC)
            disp = d.read_i16()
            return f"{disp}(pc)"
        elif reg == 3:  # d8(PC,Xn)
            ext = d.read_u16()
            bf = _load_kb_ea_brief_fields()
            xreg = _xf(ext, bf["REGISTER"])
            xtype = "a" if _xf(ext, bf["D/A"]) == 1 else "d"
            xsize = ".l" if _xf(ext, bf["W/L"]) == 1 else ".w"
            disp = _xf(ext, bf["DISPLACEMENT"])
            disp_width = bf["DISPLACEMENT"][2]
            if disp & (1 << (disp_width - 1)):
                disp -= (1 << disp_width)
            return f"{disp}(pc,{xtype}{xreg}{xsize})"
        elif reg == 4:  # #imm
            if size == SIZE_BYTE or size == SIZE_WORD:
                imm = d.read_u16()
                if size == SIZE_BYTE:
                    imm &= 0xFF
                return f"#${imm:x}"
            elif size == SIZE_LONG:
                imm = d.read_u32()
                return f"#${imm:x}"
    raise DecodeError(f"unknown EA mode={mode} reg={reg}")


def _movem_reglist(mask: int, direction: int) -> str:
    """Convert MOVEM register mask to register list string.

    direction: 0 = register-to-memory (reversed bit order for predecrement)
               1 = memory-to-register (normal bit order)
    """
    masks = _load_kb_movem_reg_masks()
    table = masks["predecrement"] if direction == 0 else masks["normal"]
    regs = [table[i] for i in range(16) if mask & (1 << i)]
    return _compress_reglist(regs)


def _compress_reglist(regs: list[str]) -> str:
    """Compress register list into range notation."""
    if not regs:
        return ""
    # Group by type (d/a) and find ranges
    groups = []
    dregs = sorted([int(r[1]) for r in regs if r[0] == 'd'])
    aregs = sorted([int(r[1]) for r in regs if r[0] == 'a'])

    def ranges(nums, prefix):
        if not nums:
            return
        start = nums[0]
        end = start
        for n in nums[1:]:
            if n == end + 1:
                end = n
            else:
                if start == end:
                    groups.append(f"{prefix}{start}")
                else:
                    groups.append(f"{prefix}{start}-{prefix}{end}")
                start = end = n
        if start == end:
            groups.append(f"{prefix}{start}")
        else:
            groups.append(f"{prefix}{start}-{prefix}{end}")

    ranges(dregs, "d")
    ranges(aregs, "a")
    return "/".join(groups)


def _branch_target(offset: int, disp: int) -> str:
    """Format branch target address."""
    target = offset + 2 + disp
    return f"${target:x}"


def _decode_one(d: _Decoder, max_cpu: str | None) -> Instruction:
    """Decode a single instruction at current position."""
    start = d.pos
    pc_offset = d.base + start
    opcode = d.read_u16()

    # Decode based on upper nibble and bit patterns
    group = (opcode >> 12) & 0xF
    try:
        text = _decode_opcode(d, opcode, group, pc_offset)
    except struct.error as e:
        raise DecodeError(
            f"truncated instruction at offset=${pc_offset:06x} opcode=${opcode:04x}"
        ) from e
    _ensure_cpu_supported(text, max_cpu)

    size = d.pos - start
    raw = d.data[start:d.pos]
    return Instruction(offset=pc_offset, size=size, opcode=opcode,
                       text=text, raw=raw)


def _decode_opcode(d: _Decoder, op: int, group: int, pc: int) -> str:
    """Main opcode decoder."""

    if group == 0:
        return _decode_group0(d, op, pc)
    elif group == 1:
        return _decode_move_byte(d, op, pc)
    elif group == 2:
        return _decode_move_long(d, op, pc)
    elif group == 3:
        return _decode_move_word(d, op, pc)
    elif group == 4:
        return _decode_group4(d, op, pc)
    elif group == 5:
        return _decode_group5(d, op, pc)
    elif group == 6:
        return _decode_group6(d, op, pc)
    elif group == 7:
        return _decode_moveq(d, op, pc)
    elif group == 8:
        return _decode_group8(d, op, pc)
    elif group == 9:
        return _decode_sub(d, op, pc)
    elif group == 0xA:
        raise DecodeError(f"unsupported line-A op=${op:04x}")
    elif group == 0xB:
        return _decode_cmp_eor(d, op, pc)
    elif group == 0xC:
        return _decode_group_c(d, op, pc)
    elif group == 0xD:
        return _decode_add(d, op, pc)
    elif group == 0xE:
        return _decode_shift(d, op, pc)
    elif group == 0xF:
        return _decode_line_f(d, op, pc)

    raise DecodeError(f"unhandled group {group}")


def _opmode_ea_to_dn(entry: dict) -> bool:
    """Return True if opmode table entry indicates ea→Dn direction, False for Dn→ea."""
    op_text = entry.get("operation", "")
    # Multi-column format: "< ea > OP Dn → Dn" vs "Dn OP < ea > → < ea >"
    if "→" in op_text:
        dest = op_text.split("→")[-1].strip()
        return "Dn" in dest and "ea" not in dest.lower()
    # Arrow may be missing from PDF extraction; determine from operand order
    if op_text:
        return op_text.lstrip().startswith("<")
    # Value-description format: "memory to register" vs "register to memory"
    desc = entry.get("description", "").lower()
    return "to register" in desc


# --- Group decoders ---

def _decode_group0(d: _Decoder, op: int, pc: int) -> str:
    """Bit operations and immediate ops (ORI, ANDI, SUBI, ADDI, EORI, CMPI, BTST, etc.)"""
    _masks = _load_kb_encoding_masks()

    # Derive bit-op name table from KB: extract bits 7:6 from each instruction's val
    _bitop_names, _bitop_field = _load_kb_bitop_names()

    _fields = _load_kb_opword_field_map()

    # MOVEP — detect via KB mask/val + opmode validation
    _movep_m, _movep_v = _masks["MOVEP"]
    _movep_opm = _load_kb_opmode_tables()["MOVEP"]
    if (op & _movep_m) == _movep_v:
        _movep_f = _fields["MOVEP"]
        opmode = _xf(op, _movep_f["OPMODE"])
        if opmode in _movep_opm:
            dreg = _xf(op, _movep_f["DATA REGISTER"])
            areg = _xf(op, _movep_f["ADDRESS REGISTER"])
            disp = d.read_i16()
            entry = _movep_opm[opmode]
            sfx = f".{entry['size']}"
            desc = entry.get("description", "").lower()
            if "memory to register" in desc:
                return f"movep{sfx} {disp}(a{areg}),d{dreg}"
            else:
                return f"movep{sfx} d{dreg},{disp}(a{areg})"

    if op & 0x0100:
        # Dynamic bit operations: BTST/BCHG/BCLR/BSET Dn,<ea>
        _dest_reg = _load_kb_dest_reg_field()
        _btst_f = _fields["BTST"]
        reg = _xf(op, _dest_reg["BTST"])
        mode = _xf(op, _btst_f["MODE"])
        ea_reg = _xf(op, _btst_f["REGISTER"])
        bit_op = _xf(op, _bitop_field)
        sz = SIZE_LONG if mode == 0 else SIZE_BYTE
        ea = _ea_str(d, mode, ea_reg, sz, pc)
        return f"{_bitop_names[bit_op]}    d{reg},{ea}"
    else:
        # Static bit ops or immediate ops
        # Use ORI SIZE field for size_bits; imm_names returns field for top_bits
        imm_names, _imm_field = _load_kb_imm_names()
        _ori_f = _fields["ORI"]
        top_bits = _xf(op, _imm_field)
        size_bits = _xf(op, _ori_f["SIZE"])

        if top_bits == 4:
            # Static bit operations — MODE/REGISTER same positions as dynamic BTST
            _btst_f = _fields["BTST"]
            mode = _xf(op, _btst_f["MODE"])
            ea_reg = _xf(op, _btst_f["REGISTER"])
            bit_op = _xf(op, _bitop_field)
            bit_num = d.read_u16() & 0xFF
            sz = SIZE_LONG if mode == 0 else SIZE_BYTE
            ea = _ea_str(d, mode, ea_reg, sz, pc)
            return f"{_bitop_names[bit_op]}    #{bit_num},{ea}"

        # CMP2/CHK2/CAS (68020+): size_bits==3 distinguishes from immediate ops
        # Note: CAS.L also has top_bits==7, so CAS must be checked before MOVES.
        if size_bits == 3:
            _m_cmp, _v_cmp = _masks["CMP2"]    # KeyError → regenerate KB JSON
            _m_cas, _v_cas = _masks["CAS CAS2"]
            if (op & _m_cmp) == _v_cmp:
                # CMP2/CHK2: SIZE from KB field map (valid: 0,1,2 only)
                # ss==3 means this is RTM, not CMP2 — fall through
                _cmp2_f = _fields["CMP2"]
                ss = _xf(op, _cmp2_f["SIZE"])
                if ss <= 2:
                    sfx = SIZE_SUFFIX[ss]
                    mode = _xf(op, _cmp2_f["MODE"])
                    reg = _xf(op, _cmp2_f["REGISTER"])
                    ext = d.read_u16()
                    # Extension word fields from KB (D/A + REGISTER combined span)
                    _ef = _load_kb_ext_field_map()["CMP2"]
                    ad_hi = _ef["D/A"][0]
                    reg_lo = _ef["REGISTER"][1]
                    reg_span = _ef["D/A"][1] - reg_lo + 1
                    is_an = (ext >> ad_hi) & 1
                    gpreg = (ext >> reg_lo) & ((1 << reg_span) - 1)
                    # CHK2 vs CMP2: compute ext mask/val from fixed bits in
                    # CHK2's encoding[1] to find the distinguishing bit
                    chk2_ext_mask, chk2_ext_val = _load_kb_ext_encoding_masks()["CHK2"]
                    chk2 = (ext & chk2_ext_mask) == chk2_ext_val
                    name = "chk2" if chk2 else "cmp2"
                    gp_name = f"{'a' if is_an else 'd'}{gpreg}"
                    ea = _ea_str(d, mode, reg, ss, pc)
                    return f"{name}{sfx}  {ea},{gp_name}"
            if (op & _m_cas) == _v_cas:
                # Size encoding parsed from KB field description
                _cas_f = _fields["CAS CAS2"]
                cas_sz = _load_kb_size_encodings()["CAS CAS2"]
                ss_raw = _xf(op, _cas_f["SIZE"])
                if ss_raw not in cas_sz:
                    raise DecodeError(f"unknown CAS size={ss_raw}")
                sz = cas_sz[ss_raw]
                sfx = SIZE_SUFFIX[sz]
                mode = _xf(op, _cas_f["MODE"])
                reg = _xf(op, _cas_f["REGISTER"])
                ext = d.read_u16()
                # Extension word field positions from KB
                _cas_ef = _load_kb_ext_field_map()["CAS CAS2"]
                du_lo = _cas_ef["Du"][1]
                du_w = _cas_ef["Du"][2]
                dc_lo = _cas_ef["Dc"][1]
                dc_w = _cas_ef["Dc"][2]
                dc = (ext >> dc_lo) & ((1 << dc_w) - 1)
                du = (ext >> du_lo) & ((1 << du_w) - 1)
                ea = _ea_str(d, mode, reg, sz, pc)
                return f"cas{sfx}   d{dc},d{du},{ea}"

        # MOVES (68010+): top_bits=7, size_bits in 0-2 (CAS.L already caught above)
        if top_bits == 7:
            _m, _v = _masks["MOVES"]  # KeyError → regenerate m68k_instructions.json
            if (op & _m) == _v:
                sz = size_bits
                if sz > 2:
                    raise DecodeError(f"unknown group0 moves sz={sz}")
                sfx = SIZE_SUFFIX[sz]
                _moves_f = _fields["MOVES"]
                mode = _xf(op, _moves_f["MODE"])
                reg = _xf(op, _moves_f["REGISTER"])
                ext = d.read_u16()
                _ef = _load_kb_ext_field_map()["MOVES"]
                # A/D flag at A/D.bit_hi; register spans A/D.bit_lo..REGISTER.bit_lo
                _ad_hi = _ef["A/D"][0]
                _reg_lo = _ef["REGISTER"][1]
                _reg_span = _ef["A/D"][1] - _reg_lo + 1
                _dr_hi = _ef["dr"][0]
                is_an = (ext >> _ad_hi) & 1
                gpreg = (ext >> _reg_lo) & ((1 << _reg_span) - 1)
                rw = (ext >> _dr_hi) & 1   # 1 = Rn→EA (write), 0 = EA→Rn (read)
                gp_name = f"{'a' if is_an else 'd'}{gpreg}"
                ea = _ea_str(d, mode, reg, sz, pc)
                if rw:
                    return f"moves{sfx} {gp_name},{ea}"
                else:
                    return f"moves{sfx} {ea},{gp_name}"
            raise DecodeError(f"unknown group0 top={top_bits}")

        # CALLM / RTM (68020) — detect via KB mask/val
        _m_rtm, _v_rtm = _masks["RTM"]
        if (op & _m_rtm) == _v_rtm:
            _rtm_f = _fields["RTM"]
            da = _xf(op, _rtm_f["D/A"])
            ea_reg = _xf(op, _rtm_f["REGISTER"])
            if da == 0:
                return f"rtm     d{ea_reg}"
            else:
                return f"rtm     a{ea_reg}"
        _m_callm, _v_callm = _masks["CALLM"]
        if (op & _m_callm) == _v_callm:
            _callm_f = _fields["CALLM"]
            mode = _xf(op, _callm_f["MODE"])
            ea_reg = _xf(op, _callm_f["REGISTER"])
            ext = d.read_u16()
            _callm_ef = _load_kb_ext_field_map()["CALLM"]
            _ac = _callm_ef["ARGUMENT COUNT"]
            arg_count = (ext >> _ac[1]) & ((1 << _ac[2]) - 1)
            ea = _ea_str(d, mode, ea_reg, SIZE_LONG, pc)
            return f"callm   #{arg_count},{ea}"

        # Immediate operations — name table derived from KB encoding vals
        if top_bits not in imm_names:
            raise DecodeError(f"unknown group0 top={top_bits}")

        name = imm_names[top_bits]
        # Use ORI fields as representative — all imm ops share MODE/REGISTER positions
        _imm_f = _fields["ORI"]
        mode = _xf(op, _imm_f["MODE"])
        ea_reg = _xf(op, _imm_f["REGISTER"])

        # Special cases: ORI/ANDI/EORI to CCR/SR — detect via KB mask/val
        for _sr_suffix, _sr_name, _sr_size in (("CCR", "ccr", "b"), ("SR", "sr", "w")):
            _sr_key = f"{name.upper()} to {_sr_suffix}"
            _sr_mv = _masks.get(_sr_key)
            if _sr_mv is not None and (op & _sr_mv[0]) == _sr_mv[1]:
                imm = d.read_u16()
                if _sr_size == "b":
                    imm &= 0xFF
                return f"{name}.{_sr_size}  #${imm:x},{_sr_name}"

        sz = size_bits
        sfx = SIZE_SUFFIX[sz]
        if sz == SIZE_BYTE:
            imm = d.read_u16() & 0xFF
            imm_s = f"#${imm:x}"
        elif sz == SIZE_WORD:
            imm = d.read_u16()
            imm_s = f"#${imm:x}"
        else:
            imm = d.read_u32()
            imm_s = f"#${imm:x}"

        ea = _ea_str(d, mode, ea_reg, sz, pc)
        return f"{name}{sfx}  {imm_s},{ea}"


@lru_cache(maxsize=1)
def _load_kb_move_fields() -> tuple[tuple[int, int, int], tuple[int, int, int],
                                     tuple[int, int, int], tuple[int, int, int]]:
    """Return (dst_reg, dst_mode, src_mode, src_reg) field tuples for MOVE.

    MOVE has duplicate MODE and REGISTER fields; disambiguate by positional order
    in raw field list (higher bits first in the encoding).
    """
    raw = _load_kb_raw_fields(0)["MOVE"]
    modes = [(hi, lo, w) for name, hi, lo, w in raw if name == "MODE"]
    regs = [(hi, lo, w) for name, hi, lo, w in raw if name == "REGISTER"]
    # Higher-bit fields are destination, lower-bit fields are source
    modes.sort(key=lambda f: f[0], reverse=True)
    regs.sort(key=lambda f: f[0], reverse=True)
    return regs[0], modes[0], modes[1], regs[1]  # dst_reg, dst_mode, src_mode, src_reg


def _decode_move(d: _Decoder, op: int, pc: int, size: int) -> str:
    """Decode MOVE/MOVEA instruction."""
    dst_reg_f, dst_mode_f, src_mode_f, src_reg_f = _load_kb_move_fields()
    src_mode = _xf(op, src_mode_f)
    src_reg = _xf(op, src_reg_f)
    dst_reg = _xf(op, dst_reg_f)
    dst_mode = _xf(op, dst_mode_f)
    sfx = SIZE_SUFFIX[size]

    src = _ea_str(d, src_mode, src_reg, size, pc)

    if dst_mode == 1:
        # MOVEA
        dst = _reg_name(dst_reg, True)
        return f"movea{sfx} {src},{dst}"

    dst = _ea_str(d, dst_mode, dst_reg, size, pc)
    return f"move{sfx}  {src},{dst}"


def _decode_move_byte(d: _Decoder, op: int, pc: int) -> str:
    return _decode_move(d, op, pc, SIZE_BYTE)

def _decode_move_long(d: _Decoder, op: int, pc: int) -> str:
    return _decode_move(d, op, pc, SIZE_LONG)

def _decode_move_word(d: _Decoder, op: int, pc: int) -> str:
    return _decode_move(d, op, pc, SIZE_WORD)


def _decode_group4(d: _Decoder, op: int, pc: int) -> str:
    """Miscellaneous: LEA, PEA, CLR, NEG, NOT, TST, MOVEM, JMP, JSR, etc."""
    _masks = _load_kb_encoding_masks()
    _fields = _load_kb_opword_field_map()
    _dest_reg = _load_kb_dest_reg_field()

    # --- Fixed-opword instructions (mask=0xFFFF in KB) ---
    # Build lookup from all KB instructions whose mask covers all 16 bits
    _fixed = _load_kb_fixed_opcodes()
    if op in _fixed:
        mn = _fixed[op]
        mn_l = mn.lower()
        if mn in ("STOP",):
            imm = d.read_u16()
            return f"{mn_l}    #${imm:04x}"
        if mn in ("RTD",):
            disp = d.read_i16()
            return f"{mn_l}     #{disp}"
        return f"{mn_l:8s}".rstrip()

    # TRAP
    _m, _v = _masks["TRAP"]
    if (op & _m) == _v:
        vec = _xf(op, _fields["TRAP"]["VECTOR"])
        return f"trap    #{vec}"

    # LINK.L (68020+) — encoding[2] in KB; must check before LINK.W
    _m2, _v2 = _load_kb_encoding_masks_idx(2)["LINK"]
    if (op & _m2) == _v2:
        areg = _xf(op, _fields["LINK"]["REGISTER"])
        disp = d.read_i32()
        return f"link.l  {_reg_name(areg, True)},#{disp}"

    # MULU.L/MULS.L (68020+) — enc[1] opword, enc[2] ext word
    _enc1 = _load_kb_encoding_masks_idx(1)
    _enc2 = _load_kb_encoding_masks_idx(2)
    _ef1 = _load_kb_ext_field_map()
    _ef2 = _load_kb_ext2_field_map()

    _m1_mul, _v1_mul = _enc1["MULS"]  # MULS/MULU share enc[1] opword
    if (op & _m1_mul) == _v1_mul:
        _mul_f1 = _ef1["MULS"]
        mode = _xf(op, _mul_f1["MODE"])
        ea_reg = _xf(op, _mul_f1["REGISTER"])
        ext = d.read_u16()
        for _mn in ("MULS", "MULU"):
            _m2e, _v2e = _enc2[_mn]
            if (ext & _m2e) == _v2e:
                ef = _ef2[_mn]
                reg_fields = sorted(
                    [(k, v) for k, v in ef.items() if k.startswith("REGISTER")],
                    key=lambda x: x[1][0], reverse=True,
                )
                dl_f = reg_fields[0][1]  # higher bit pos (14:12) = Dl/DI
                dh_f = reg_fields[1][1]  # lower bit pos (2:0) = Dh
                sz_f = ef["SIZE"]
                dl = _xf(ext, dl_f)
                dh = _xf(ext, dh_f)
                size_bit = _xf(ext, sz_f)
                ea = _ea_str(d, mode, ea_reg, SIZE_LONG, pc)
                name = _mn.lower()
                if size_bit:
                    return f"{name}.l  {ea},d{dh}:d{dl}"
                else:
                    return f"{name}.l  {ea},d{dl}"
        raise DecodeError(f"MUL.L ext word ${ext:04x} matches neither MULS nor MULU")

    # DIVU.L/DIVS.L/DIVUL.L/DIVSL.L (68020+)
    _m1_div, _v1_div = _enc1["DIVS, DIVSL"]  # DIVS/DIVU share enc[1] opword
    if (op & _m1_div) == _v1_div:
        _div_f1 = _ef1["DIVS, DIVSL"]
        mode = _xf(op, _div_f1["MODE"])
        ea_reg = _xf(op, _div_f1["REGISTER"])
        ext = d.read_u16()
        for _mn, _name_s, _name_l in (
            ("DIVS, DIVSL", "divs", "divsl"),
            ("DIVU, DIVUL", "divu", "divul"),
        ):
            _m2e, _v2e = _enc2[_mn]
            if (ext & _m2e) == _v2e:
                ef = _ef2[_mn]
                reg_fields = sorted(
                    [(k, v) for k, v in ef.items() if k.startswith("REGISTER")],
                    key=lambda x: x[1][0], reverse=True,
                )
                dq_f = reg_fields[0][1]  # higher bit pos (14:12) = Dq
                dr_f = reg_fields[1][1]  # lower bit pos (2:0) = Dr
                sz_f = ef["SIZE"]
                dq = _xf(ext, dq_f)
                dr = _xf(ext, dr_f)
                size_bit = _xf(ext, sz_f)
                ea = _ea_str(d, mode, ea_reg, SIZE_LONG, pc)
                if size_bit:
                    return f"{_name_s}.l  {ea},d{dr}:d{dq}"
                elif dq != dr:
                    return f"{_name_l}.l  {ea},d{dr}:d{dq}"
                else:
                    return f"{_name_s}.l  {ea},d{dq}"
        raise DecodeError(f"DIV.L ext word ${ext:04x} matches neither DIVS nor DIVU")

    # LINK.W
    _m, _v = _masks["LINK"]
    if (op & _m) == _v:
        areg = _xf(op, _fields["LINK"]["REGISTER"])
        disp = d.read_i16()
        return f"link    {_reg_name(areg, True)},#{disp}"

    # UNLK
    _m, _v = _masks["UNLK"]
    if (op & _m) == _v:
        areg = _xf(op, _fields["UNLK"]["REGISTER"])
        return f"unlk    {_reg_name(areg, True)}"

    # MOVE USP — dr field from KB
    _m, _v = _masks["MOVE USP"]
    if (op & _m) == _v:
        _usp_f = _fields["MOVE USP"]
        areg = _xf(op, _usp_f["REGISTER"])
        dr = _xf(op, _usp_f["dr"])
        if dr:
            return f"move.l  usp,{_reg_name(areg, True)}"
        else:
            return f"move.l  {_reg_name(areg, True)},usp"

    # JSR
    _m, _v = _masks["JSR"]
    if (op & _m) == _v:
        _jsr_f = _fields["JSR"]
        mode = _xf(op, _jsr_f["MODE"])
        reg = _xf(op, _jsr_f["REGISTER"])
        ea = _ea_str(d, mode, reg, SIZE_LONG, pc)
        return f"jsr     {ea}"

    # JMP
    _m, _v = _masks["JMP"]
    if (op & _m) == _v:
        _jmp_f = _fields["JMP"]
        mode = _xf(op, _jmp_f["MODE"])
        reg = _xf(op, _jmp_f["REGISTER"])
        ea = _ea_str(d, mode, reg, SIZE_LONG, pc)
        return f"jmp     {ea}"

    # LEA
    _m, _v = _masks["LEA"]
    if (op & _m) == _v:
        areg = _xf(op, _dest_reg["LEA"])
        _lea_f = _fields["LEA"]
        mode = _xf(op, _lea_f["MODE"])
        reg = _xf(op, _lea_f["REGISTER"])
        ea = _ea_str(d, mode, reg, SIZE_LONG, pc)
        return f"lea     {ea},{_reg_name(areg, True)}"

    # BKPT (68010+)
    _m, _v = _masks["BKPT"]
    if (op & _m) == _v:
        vec = _xf(op, _fields["BKPT"]["VECTOR"])
        return f"bkpt    #{vec}"

    # SWAP (must be before PEA — both match similar patterns but SWAP has mode=0)
    _m, _v = _masks["SWAP"]
    if (op & _m) == _v:
        return f"swap    d{_xf(op, _fields['SWAP']['REGISTER'])}"

    # EXT, EXTB (must be before MOVEM — EXT has mode=0)
    _m, _v = _masks["EXT, EXTB"]
    if (op & _m) == _v:
        _ext_f = _fields["EXT, EXTB"]
        opmode = _xf(op, _ext_f["OPMODE"])
        dreg = _xf(op, _ext_f["REGISTER"])
        _ext_opm = _load_kb_opmode_tables()["EXT, EXTB"]
        if opmode in _ext_opm:
            entry = _ext_opm[opmode]
            # Description tells us the output: byte→word = ext.w, word→long = ext.l, byte→long = extb.l
            desc = entry.get("description", "").lower()
            if "byte" in desc and "to long" in desc:
                return f"extb.l  d{dreg}"
            elif "to long" in desc:
                return f"ext.l   d{dreg}"
            else:
                return f"ext.w   d{dreg}"

    # PEA
    _m, _v = _masks["PEA"]
    if (op & _m) == _v:
        _pea_f = _fields["PEA"]
        mode = _xf(op, _pea_f["MODE"])
        reg = _xf(op, _pea_f["REGISTER"])
        ea = _ea_str(d, mode, reg, SIZE_LONG, pc)
        return f"pea     {ea}"

    # MOVEM (mode >= 2 guaranteed now since EXT caught mode=0)
    _m, _v = _masks["MOVEM"]
    if (op & _m) == _v:
        _of = _fields["MOVEM"]
        direction = _xf(op, _of["dr"])  # 0=reg-to-mem, 1=mem-to-reg
        sz_enc = _load_kb_size_encodings()["MOVEM"]
        sz_bits = _extract_size_bits(op, _of["SIZE"], sz_enc)
        sz = sz_enc[sz_bits]
        sfx = SIZE_SUFFIX[sz]
        mode = _xf(op, _of["MODE"])
        reg = _xf(op, _of["REGISTER"])
        mask = d.read_u16()

        is_predec = (mode == 4)
        reglist = _movem_reglist(mask, 0 if is_predec else 1)
        ea = _ea_str(d, mode, reg, sz, pc)

        if direction == 0:
            return f"movem{sfx} {reglist},{ea}"
        else:
            return f"movem{sfx} {ea},{reglist}"

    # CLR, NEG, NEGX, NOT — mask/val from KB
    for _mn in ("CLR", "NEG", "NEGX", "NOT"):
        _m, _v = _masks[_mn]
        if (op & _m) == _v:
            _mn_f = _fields[_mn]
            sz = _xf(op, _mn_f["SIZE"])
            if sz == 3:
                continue  # not this instruction
            sfx = SIZE_SUFFIX[sz]
            mode = _xf(op, _mn_f["MODE"])
            reg = _xf(op, _mn_f["REGISTER"])
            ea = _ea_str(d, mode, reg, sz, pc)
            return f"{_mn.lower()}{sfx}  {ea}"

    # TST
    _m, _v = _masks["TST"]
    if (op & _m) == _v:
        _tst_f = _fields["TST"]
        sz = _xf(op, _tst_f["SIZE"])
        if sz < 3:
            sfx = SIZE_SUFFIX[sz]
            mode = _xf(op, _tst_f["MODE"])
            reg = _xf(op, _tst_f["REGISTER"])
            ea = _ea_str(d, mode, reg, sz, pc)
            return f"tst{sfx}   {ea}"

    # TAS
    _m, _v = _masks["TAS"]
    if (op & _m) == _v:
        _tas_f = _fields["TAS"]
        mode = _xf(op, _tas_f["MODE"])
        reg = _xf(op, _tas_f["REGISTER"])
        ea = _ea_str(d, mode, reg, SIZE_BYTE, pc)
        return f"tas     {ea}"

    # NBCD
    _m, _v = _masks["NBCD"]
    if (op & _m) == _v:
        _nbcd_f = _fields["NBCD"]
        mode = _xf(op, _nbcd_f["MODE"])
        reg = _xf(op, _nbcd_f["REGISTER"])
        ea = _ea_str(d, mode, reg, SIZE_BYTE, pc)
        return f"nbcd    {ea}"

    # MOVE from SR
    _m, _v = _masks["MOVE from SR"]
    if (op & _m) == _v:
        _msr_f = _fields["MOVE from SR"]
        mode = _xf(op, _msr_f["MODE"])
        reg = _xf(op, _msr_f["REGISTER"])
        ea = _ea_str(d, mode, reg, SIZE_WORD, pc)
        return f"move.w  sr,{ea}"

    # MOVE from CCR (68010+)
    _m, _v = _masks["MOVE from CCR"]
    if (op & _m) == _v:
        _mccr_f = _fields["MOVE from CCR"]
        mode = _xf(op, _mccr_f["MODE"])
        reg = _xf(op, _mccr_f["REGISTER"])
        ea = _ea_str(d, mode, reg, SIZE_WORD, pc)
        return f"move.w  ccr,{ea}"

    # MOVE to CCR
    _m, _v = _masks["MOVE to CCR"]
    if (op & _m) == _v:
        _mtccr_f = _fields["MOVE to CCR"]
        mode = _xf(op, _mtccr_f["MODE"])
        reg = _xf(op, _mtccr_f["REGISTER"])
        ea = _ea_str(d, mode, reg, SIZE_WORD, pc)
        return f"move.w  {ea},ccr"

    # MOVE to SR
    _m, _v = _masks["MOVE to SR"]
    if (op & _m) == _v:
        _mtsr_f = _fields["MOVE to SR"]
        mode = _xf(op, _mtsr_f["MODE"])
        reg = _xf(op, _mtsr_f["REGISTER"])
        ea = _ea_str(d, mode, reg, SIZE_WORD, pc)
        return f"move.w  {ea},sr"

    # CHK (word and long) — broad mask, must be checked after specific instructions
    _m, _v = _masks["CHK"]
    if (op & _m) == _v:
        dreg = _xf(op, _dest_reg["CHK"])
        _of = _fields["CHK"]
        mode = _xf(op, _of["MODE"])
        reg = _xf(op, _of["REGISTER"])
        sz_lo = _of["SIZE"][1]
        sz_w = _of["SIZE"][2]
        sz_bits = (op >> sz_lo) & ((1 << sz_w) - 1)
        chk_sz = _load_kb_size_encodings()["CHK"]
        if sz_bits in chk_sz:
            sz = chk_sz[sz_bits]
            sfx = SIZE_SUFFIX[sz]
            ea = _ea_str(d, mode, reg, sz, pc)
            return f"chk{sfx}   {ea},d{dreg}"

    # MOVEC (68010+) — extension word fields from KB
    _m, _v = _masks["MOVEC"]
    if (op & _m) == _v:
        ext = d.read_u16()
        _movec_f = _fields["MOVEC"]
        dr = _xf(op, _movec_f["dr"])  # 0 = Rc→Rn, 1 = Rn→Rc
        _ef = _load_kb_ext_field_map()["MOVEC"]
        # A/D flag at A/D.bit_hi; register spans A/D.bit_lo..REGISTER.bit_lo
        ad_hi = _ef["A/D"][0]
        reg_lo = _ef["REGISTER"][1]
        reg_span = _ef["A/D"][1] - reg_lo + 1
        ctrl_lo = _ef["CONTROL REGISTER"][1]
        ctrl_w = _ef["CONTROL REGISTER"][2]
        is_an = (ext >> ad_hi) & 1
        gpreg = (ext >> reg_lo) & ((1 << reg_span) - 1)
        ctrl = (ext >> ctrl_lo) & ((1 << ctrl_w) - 1)
        _ctrl_regs = _load_kb_control_registers()
        if ctrl not in _ctrl_regs:
            raise DecodeError(f"unknown MOVEC control register ${ctrl:03x}")
        ctrl_name = _ctrl_regs[ctrl]
        gp_name = f"{'a' if is_an else 'd'}{gpreg}"
        if dr == 0:
            return f"movec   {ctrl_name},{gp_name}"
        else:
            return f"movec   {gp_name},{ctrl_name}"

    raise DecodeError(f"unknown group4 op=${op:04x}")


def _decode_group5(d: _Decoder, op: int, pc: int) -> str:
    """ADDQ, SUBQ, Scc, DBcc"""
    _fields = _load_kb_opword_field_map()
    _addq_f = _fields["ADDQ"]
    size_bits = _xf(op, _addq_f["SIZE"])

    if size_bits == 3:
        # Scc, DBcc, or TRAPcc
        _scc_f = _fields["Scc"]
        condition = _xf(op, _scc_f["CONDITION"])
        mode = _xf(op, _scc_f["MODE"])
        reg = _xf(op, _scc_f["REGISTER"])

        if mode == 1:
            # DBcc
            disp = d.read_i16()
            target = _branch_target(pc, disp)
            cc = _cc_name(condition)
            _dbcc_f = _fields["DBcc"]
            reg = _xf(op, _dbcc_f["REGISTER"])
            return f"db{cc}    d{reg},{target}"

        # TRAPcc (68020+) — mode=7, reg from KB opmode_table
        if mode == 7:
            _trapcc_opm = _load_kb_opmode_tables()["TRAPcc"]
            if reg in _trapcc_opm:
                cc = _cc_name(condition)
                entry = _trapcc_opm[reg]
                sz = entry["size"]
                if sz == "w":
                    imm = d.read_u16()
                    return f"trap{cc}.w #${imm:04x}"
                elif sz == "l":
                    imm = d.read_u32()
                    return f"trap{cc}.l #${imm:08x}"
                else:
                    return f"trap{cc}"

        # Scc (all other mode/reg combos including mode=7 absolute addressing)
        ea = _ea_str(d, mode, reg, SIZE_BYTE, pc)
        cc = _cc_name(condition)
        return f"s{cc}     {ea}"
    else:
        # ADDQ / SUBQ — discriminate via KB mask/val
        _masks = _load_kb_encoding_masks()
        _subq_m, _subq_v = _masks["SUBQ"]
        data = _xf(op, _addq_f["DATA"])
        if data == 0:
            data = _load_kb_addq_zero_means()
        is_sub = (op & _subq_m) == _subq_v
        name = "subq" if is_sub else "addq"
        sfx = SIZE_SUFFIX[size_bits]
        mode = _xf(op, _addq_f["MODE"])
        reg = _xf(op, _addq_f["REGISTER"])
        ea = _ea_str(d, mode, reg, size_bits, pc)
        return f"{name}{sfx} #{data},{ea}"


CC_NAMES = _load_disasm_meta()["condition_codes"]

def _cc_name(cc: int) -> str:
    return CC_NAMES[cc]


def _decode_group6(d: _Decoder, op: int, pc: int) -> str:
    """Bcc, BSR, BRA"""
    _masks = _load_kb_encoding_masks()
    _fields = _load_kb_opword_field_map()
    _bcc_f = _fields["Bcc"]
    condition = _xf(op, _bcc_f["CONDITION"])
    _bra_f = _fields["BRA"]
    disp8 = _xf(op, _bra_f["8-BIT DISPLACEMENT"])

    if disp8 == 0:
        disp = d.read_i16()
        sfx = ".w"
    elif disp8 == 0xFF:
        # 68020+ long branch
        disp = d.read_i32()
        sfx = ".l"
    else:
        disp = disp8 if disp8 < 128 else disp8 - 256
        sfx = ".s"

    target = _branch_target(pc, disp)

    # Detect BRA/BSR via KB mask/val instead of hardcoded condition indices
    _bra_m, _bra_v = _masks["BRA"]
    _bsr_m, _bsr_v = _masks["BSR"]
    if (op & _bra_m) == _bra_v:
        return f"bra{sfx}   {target}"
    elif (op & _bsr_m) == _bsr_v:
        return f"bsr{sfx}   {target}"
    else:
        cc = _cc_name(condition)
        return f"b{cc}{sfx}    {target}"


def _decode_moveq(d: _Decoder, op: int, pc: int) -> str:
    """MOVEQ"""
    _m, _v = _load_kb_encoding_masks()["MOVEQ"]
    if (op & _m) != _v:
        raise DecodeError(f"invalid moveq ${op:04x}")
    _moveq_f = _load_kb_opword_field_map()["MOVEQ"]
    reg = _xf(op, _moveq_f["REGISTER"])
    data = _xf(op, _moveq_f["DATA"])
    if data & 0x80:
        data -= 256
    return f"moveq   #{data},d{reg}"


def _decode_group8(d: _Decoder, op: int, pc: int) -> str:
    """OR, DIV, SBCD"""
    _masks = _load_kb_encoding_masks()
    _fields = _load_kb_opword_field_map()
    _dest_reg = _load_kb_dest_reg_field()
    _or_f = _fields["OR"]
    reg = _xf(op, _dest_reg["OR"])
    opmode = _xf(op, _or_f["OPMODE"])
    mode = _xf(op, _or_f["MODE"])
    ea_reg = _xf(op, _or_f["REGISTER"])

    # DIVU.W / DIVS.W — detect via KB masks
    for _divmn in ("DIVU, DIVUL", "DIVS, DIVSL"):
        _dm, _dv = _masks[_divmn]
        if (op & _dm) == _dv:
            ea = _ea_str(d, mode, ea_reg, SIZE_WORD, pc)
            name = _divmn.split(",")[0].lower()
            return f"{name}.w  {ea},d{reg}"

    # SBCD — R/M field from KB operand_modes
    _m, _v = _masks["SBCD"]
    if (op & _m) == _v:
        _sbcd_f = _fields["SBCD"]
        ry = _xf(op, _sbcd_f["REGISTER Dx/Ax"])
        rx = _xf(op, _sbcd_f["REGISTER Dy/Ay"])
        _rm_lo, _rm_vals = _load_kb_rm_field()["SBCD"]
        rm = (op >> _rm_lo) & 1
        if _rm_vals[rm] == "predec,predec":
            return f"sbcd    -(a{ry}),-(a{rx})"
        return f"sbcd    d{ry},d{rx}"

    # PACK / UNPK (68020+): identified by KB mask/val, field positions from KB
    _masks = _load_kb_encoding_masks()
    _m_pack, _v_pack = _masks["PACK"]   # KeyError → regenerate KB JSON
    _m_unpk, _v_unpk = _masks["UNPK"]
    _opfields = _load_kb_opword_field_map()
    for _mn_upper, _m, _v in (("PACK", _m_pack, _v_pack), ("UNPK", _m_unpk, _v_unpk)):
        if (op & _m) == _v:
            _of = _opfields[_mn_upper]
            dx = _xf(op, _of["REGISTER Dy/Ay"])
            rm = _xf(op, _of["R/M"])
            dy = _xf(op, _of["REGISTER Dx/Ax"])
            adj = d.read_u16()
            _mn = _mn_upper.lower()
            if rm:
                return f"{_mn}    -(a{dy}),-(a{dx}),#${adj:x}"
            return f"{_mn}    d{dy},d{dx},#${adj:x}"

    # OR — size/direction from KB opmode_table
    _or_opm = _load_kb_opmode_tables()["OR"]
    entry = _or_opm[opmode]
    sz = _SIZE_LETTER_TO_INT[entry["size"]]
    sfx = SIZE_SUFFIX[sz]
    ea = _ea_str(d, mode, ea_reg, sz, pc)
    if _opmode_ea_to_dn(entry):
        return f"or{sfx}    {ea},d{reg}"
    else:
        return f"or{sfx}    d{reg},{ea}"


def _decode_sub(d: _Decoder, op: int, pc: int) -> str:
    """SUB, SUBA, SUBX"""
    _masks = _load_kb_encoding_masks()
    _opm_tables = _load_kb_opmode_tables()
    _fields = _load_kb_opword_field_map()
    _dest_reg = _load_kb_dest_reg_field()
    _sub_f = _fields["SUB"]
    reg = _xf(op, _dest_reg["SUB"])
    opmode = _xf(op, _sub_f["OPMODE"])
    mode = _xf(op, _sub_f["MODE"])
    ea_reg = _xf(op, _sub_f["REGISTER"])

    # SUBA — opmode 3/7 from KB opmode_table
    _suba_opm = _opm_tables["SUBA"]
    if opmode in _suba_opm:
        sz = _SIZE_LETTER_TO_INT[_suba_opm[opmode]["size"]]
        ea = _ea_str(d, mode, ea_reg, sz, pc)
        sfx = SIZE_SUFFIX[sz]
        return f"suba{sfx} {ea},a{reg}"

    # SUBX — R/M field from KB operand_modes
    _m, _v = _masks["SUBX"]
    if (op & _m) == _v and (mode == 0 or mode == 1):
        _subx_f = _fields["SUBX"]
        ry = _xf(op, _subx_f["REGISTER Dx/Ax"])
        rx = _xf(op, _subx_f["REGISTER Dy/Ay"])
        sz = _xf(op, _subx_f["SIZE"])
        sfx = SIZE_SUFFIX[sz]
        _rm_lo, _rm_vals = _load_kb_rm_field()["SUBX"]
        rm = (op >> _rm_lo) & 1
        if _rm_vals[rm] == "predec,predec":
            return f"subx{sfx} -(a{ry}),-(a{rx})"
        return f"subx{sfx} d{ry},d{rx}"

    # SUB — size/direction from KB opmode_table
    _sub_opm = _opm_tables["SUB"]
    entry = _sub_opm[opmode]
    sz = _SIZE_LETTER_TO_INT[entry["size"]]
    sfx = SIZE_SUFFIX[sz]
    ea = _ea_str(d, mode, ea_reg, sz, pc)
    if _opmode_ea_to_dn(entry):
        return f"sub{sfx}   {ea},d{reg}"
    else:
        return f"sub{sfx}   d{reg},{ea}"


def _decode_cmp_eor(d: _Decoder, op: int, pc: int) -> str:
    """CMP, CMPA, CMPM, EOR"""
    _masks = _load_kb_encoding_masks()
    _opm_tables = _load_kb_opmode_tables()
    _fields = _load_kb_opword_field_map()
    _dest_reg = _load_kb_dest_reg_field()
    _cmp_f = _fields["CMP"]
    reg = _xf(op, _dest_reg["CMP"])
    opmode = _xf(op, _cmp_f["OPMODE"])
    mode = _xf(op, _cmp_f["MODE"])
    ea_reg = _xf(op, _cmp_f["REGISTER"])

    # CMPA — opmode 3/7 from KB opmode_table
    _cmpa_opm = _opm_tables["CMPA"]
    if opmode in _cmpa_opm:
        sz = _SIZE_LETTER_TO_INT[_cmpa_opm[opmode]["size"]]
        ea = _ea_str(d, mode, ea_reg, sz, pc)
        sfx = SIZE_SUFFIX[sz]
        return f"cmpa{sfx} {ea},a{reg}"

    # CMPM — SIZE field from KB (not ad-hoc opmode - 4)
    _m, _v = _masks["CMPM"]
    if (op & _m) == _v:
        _cmpm_f = _fields["CMPM"]
        sz = _xf(op, _cmpm_f["SIZE"])
        sfx = SIZE_SUFFIX[sz]
        return f"cmpm{sfx} (a{ea_reg})+,(a{reg})+"

    # EOR — opmode 4/5/6 from KB opmode_table
    _eor_opm = _opm_tables["EOR"]
    if opmode in _eor_opm:
        entry = _eor_opm[opmode]
        sz = _SIZE_LETTER_TO_INT[entry["size"]]
        sfx = SIZE_SUFFIX[sz]
        ea = _ea_str(d, mode, ea_reg, sz, pc)
        return f"eor{sfx}   d{reg},{ea}"

    # CMP — opmode 0/1/2 from KB opmode_table
    _cmp_opm = _opm_tables["CMP"]
    entry = _cmp_opm[opmode]
    sz = _SIZE_LETTER_TO_INT[entry["size"]]
    sfx = SIZE_SUFFIX[sz]
    ea = _ea_str(d, mode, ea_reg, sz, pc)
    return f"cmp{sfx}   {ea},d{reg}"


def _decode_group_c(d: _Decoder, op: int, pc: int) -> str:
    """AND, MUL, ABCD, EXG"""
    _masks = _load_kb_encoding_masks()
    _opm_tables = _load_kb_opmode_tables()
    _fields = _load_kb_opword_field_map()
    _dest_reg = _load_kb_dest_reg_field()
    _and_f = _fields["AND"]
    reg = _xf(op, _dest_reg["AND"])
    opmode = _xf(op, _and_f["OPMODE"])
    mode = _xf(op, _and_f["MODE"])
    ea_reg = _xf(op, _and_f["REGISTER"])

    # MULU.W / MULS.W — detect via KB masks
    for _mulmn in ("MULU", "MULS"):
        _mm, _mv = _masks[_mulmn]
        if (op & _mm) == _mv:
            ea = _ea_str(d, mode, ea_reg, SIZE_WORD, pc)
            return f"{_mulmn.lower()}.w  {ea},d{reg}"

    # ABCD — R/M field from KB operand_modes
    _m, _v = _masks["ABCD"]
    if (op & _m) == _v:
        _abcd_f = _fields["ABCD"]
        ry = _xf(op, _abcd_f["REGISTER Ry"])
        rx = _xf(op, _abcd_f["REGISTER Rx"])
        _rm_lo, _rm_vals = _load_kb_rm_field()["ABCD"]
        rm = (op >> _rm_lo) & 1
        if _rm_vals[rm] == "predec,predec":
            return f"abcd    -(a{ry}),-(a{rx})"
        return f"abcd    d{ry},d{rx}"

    # EXG — check KB encoding mask first, then opmode table
    _exg_m, _exg_v = _masks["EXG"]
    if (op & _exg_m) == _exg_v:
        _exg_opm = _opm_tables["EXG"]
        # Derive extraction width from KB opmode table values
        _opfields = _fields["EXG"]
        opm_hi = _opfields["OPMODE"][0]
        max_opm_val = max(_exg_opm.keys())
        opm_bits = max_opm_val.bit_length()
        opm_lo = opm_hi - opm_bits + 1
        exg_mode = (op >> opm_lo) & ((1 << opm_bits) - 1)
        if exg_mode in _exg_opm:
            rx_hi, rx_lo, rx_w = _opfields["REGISTER Rx"]
            rx = (op >> rx_lo) & ((1 << rx_w) - 1)
            # Ry occupies bits below the corrected OPMODE boundary
            ry = op & ((1 << opm_lo) - 1)
            entry = _exg_opm[exg_mode]
            desc = entry.get("description", "").lower()
            if "data register" in desc and "address register" in desc:
                return f"exg     d{rx},a{ry}"
            elif "address" in desc:
                return f"exg     a{rx},a{ry}"
            else:
                return f"exg     d{rx},d{ry}"

    # AND — size/direction from KB opmode_table
    _and_opm = _opm_tables["AND"]
    entry = _and_opm[opmode]
    sz = _SIZE_LETTER_TO_INT[entry["size"]]
    sfx = SIZE_SUFFIX[sz]
    ea = _ea_str(d, mode, ea_reg, sz, pc)
    if _opmode_ea_to_dn(entry):
        return f"and{sfx}   {ea},d{reg}"
    else:
        return f"and{sfx}   d{reg},{ea}"


def _decode_add(d: _Decoder, op: int, pc: int) -> str:
    """ADD, ADDA, ADDX"""
    _masks = _load_kb_encoding_masks()
    _opm_tables = _load_kb_opmode_tables()
    _fields = _load_kb_opword_field_map()
    _dest_reg = _load_kb_dest_reg_field()
    _add_f = _fields["ADD"]
    reg = _xf(op, _dest_reg["ADD"])
    opmode = _xf(op, _add_f["OPMODE"])
    mode = _xf(op, _add_f["MODE"])
    ea_reg = _xf(op, _add_f["REGISTER"])

    # ADDA — opmode 3/7 from KB opmode_table
    _adda_opm = _opm_tables["ADDA"]
    if opmode in _adda_opm:
        sz = _SIZE_LETTER_TO_INT[_adda_opm[opmode]["size"]]
        ea = _ea_str(d, mode, ea_reg, sz, pc)
        sfx = SIZE_SUFFIX[sz]
        return f"adda{sfx} {ea},a{reg}"

    # ADDX — R/M field from KB operand_modes
    _m, _v = _masks["ADDX"]
    if (op & _m) == _v and (mode == 0 or mode == 1):
        _addx_f = _fields["ADDX"]
        ry = _xf(op, _addx_f["REGISTER Ry"])
        rx = _xf(op, _addx_f["REGISTER Rx"])
        sz = _xf(op, _addx_f["SIZE"])
        sfx = SIZE_SUFFIX[sz]
        _rm_lo, _rm_vals = _load_kb_rm_field()["ADDX"]
        rm = (op >> _rm_lo) & 1
        if _rm_vals[rm] == "predec,predec":
            return f"addx{sfx} -(a{ry}),-(a{rx})"
        return f"addx{sfx} d{ry},d{rx}"

    # ADD — size/direction from KB opmode_table
    _add_opm = _opm_tables["ADD"]
    entry = _add_opm[opmode]
    sz = _SIZE_LETTER_TO_INT[entry["size"]]
    sfx = SIZE_SUFFIX[sz]
    ea = _ea_str(d, mode, ea_reg, sz, pc)
    if _opmode_ea_to_dn(entry):
        return f"add{sfx}   {ea},d{reg}"
    else:
        return f"add{sfx}   d{reg},{ea}"


def _decode_bfxxx(d: _Decoder, op: int, pc: int, mn: str, ext_names: frozenset[str]) -> str:
    """Decode a BFxxx bit-field instruction.

    Field positions are derived from KB extension word (encoding[1]):
      Do:       flag bit at Do.bit_hi; offset spans Do.bit_lo..OFFSET.bit_lo
      Dw:       flag bit at Dw.bit_hi; width spans Dw.bit_lo..WIDTH.bit_lo
      REGISTER: destination/source Dn (only present in BFEXTU/BFEXTS/BFFFO/BFINS)
    """
    ext_fields = _load_kb_ext_field_map()[mn]  # hard-fail if missing

    # Do flag and offset field (from KB positions)
    do_hi, do_lo, _ = ext_fields["Do"]
    off_hi, off_lo, _ = ext_fields["OFFSET"]
    off_total_lo = off_lo  # lowest bit of the combined offset field
    off_total_hi = do_lo   # Do.bit_lo is the top bit of the offset value

    # Dw flag and width field (from KB positions)
    dw_hi, dw_lo, _ = ext_fields["Dw"]
    w_hi, w_lo, _ = ext_fields["WIDTH"]
    w_total_lo = w_lo
    w_total_hi = dw_lo

    ext = d.read_u16()

    do = (ext >> do_hi) & 1
    off_bits = off_total_hi - off_total_lo + 1
    off_val = (ext >> off_total_lo) & ((1 << off_bits) - 1)
    off_str = f"d{off_val & 7}" if do else str(off_val)

    dw = (ext >> dw_hi) & 1
    w_bits = w_total_hi - w_total_lo + 1
    w_val = (ext >> w_total_lo) & ((1 << w_bits) - 1)
    w_str = f"d{w_val & 7}" if dw else ("32" if w_val == 0 else str(w_val))

    _bf_opf = _load_kb_opword_field_map()[mn]
    mode = _xf(op, _bf_opf["MODE"])
    reg = _xf(op, _bf_opf["REGISTER"])
    ea = _ea_str(d, mode, reg, SIZE_LONG, pc)
    bf = f"{{{off_str}:{w_str}}}"
    pad = "  " if len(mn) >= 6 else "   "

    # REGISTER field (Dn) — only present in BFEXTU/BFEXTS/BFFFO/BFINS
    if "REGISTER" not in ext_fields:
        return f"{mn.lower()}{pad} {ea}{bf}"
    reg_hi, reg_lo, reg_w = ext_fields["REGISTER"]
    dn = (ext >> reg_lo) & ((1 << reg_w) - 1)
    # Operand order from KB forms: BFINS has Dn before <ea>, others have <ea> before Dn
    kb, _ = _load_kb_payload()
    bf_inst = next(i for i in kb if i["mnemonic"] == mn)
    bf_ops = bf_inst["forms"][0]["operands"]
    dn_first = bf_ops and bf_ops[0]["type"] == "dn"
    if dn_first:
        return f"{mn.lower()}{pad} d{dn},{ea}{bf}"
    return f"{mn.lower()}{pad} {ea}{bf},d{dn}"


def _decode_shift(d: _Decoder, op: int, pc: int) -> str:
    """ASd, LSd, ROd, ROXd, BFxxx"""
    _shift_reg_f = _load_kb_opword_field_map()["ASL, ASR"]
    size_bits = _xf(op, _shift_reg_f["SIZE"])

    if size_bits == 3:
        # BFxxx instructions (68020+) live in group E with size_bits=3.
        # Mnemonic list and mask/val derived from KB.
        _masks = _load_kb_encoding_masks()
        _ext_names = _load_kb_ext_field_names()
        for mn in _load_kb_bf_mnemonics():
            _m, _v = _masks[mn]
            if (op & _m) == _v:
                return _decode_bfxxx(d, op, pc, mn, _ext_names[mn])

        # Memory shift (word only, shift by 1)
        # Field positions from KB — memory shift uses encoding[1]
        _sf = _load_kb_shift_fields()
        _mem_shift_f = _kb_field_map(1)["ASL, ASR"]
        dr_val = _xf(op, _mem_shift_f["dr"])
        direction = _sf["dr_values"][dr_val]
        _, _mem_type_f = _load_kb_shift_type_fields()
        shift_type = _xf(op, _mem_type_f)
        _shift_names = _load_kb_shift_names()
        mode = _xf(op, _mem_shift_f["MODE"])
        reg = _xf(op, _mem_shift_f["REGISTER"])
        ea = _ea_str(d, mode, reg, SIZE_WORD, pc)
        return f"{_shift_names[shift_type]}{direction}.w  {ea}"

    # Register shift — field positions from KB
    _sf = _load_kb_shift_fields()
    _shift_f = _load_kb_opword_field_map()["ASL, ASR"]
    dr_val = _xf(op, _shift_f["dr"])
    direction = _sf["dr_values"][dr_val]
    _reg_type_f, _ = _load_kb_shift_type_fields()
    shift_type = _xf(op, _reg_type_f)
    _shift_names = _load_kb_shift_names()
    sfx = SIZE_SUFFIX[size_bits]
    dreg = _xf(op, _shift_f["REGISTER"])
    _shift_dest = _load_kb_dest_reg_field()
    count_or_reg = _xf(op, _shift_dest["ASL, ASR"])

    ir_val = _xf(op, _shift_f["i/r"])
    if ir_val:
        # Shift by register (i/r = 1)
        return f"{_shift_names[shift_type]}{direction}{sfx}  d{count_or_reg},d{dreg}"
    else:
        # Shift by immediate (i/r = 0); count 0 → zero_means from KB
        count = count_or_reg if count_or_reg != 0 else _sf["zero_means"]
        return f"{_shift_names[shift_type]}{direction}{sfx}  #{count},d{dreg}"



# --- Line-F (coprocessor / 68040) ---

@lru_cache(maxsize=1)
def _load_kb_cpid_field() -> tuple[int, int]:
    """Derive coprocessor ID field position from KB FPU instruction encoding."""
    kb, _ = _load_kb_payload()
    inst = next(i for i in kb if i["mnemonic"] == "FRESTORE")
    id_field = next(f for f in inst["encodings"][0]["fields"] if f["name"] == "ID")
    return id_field["bit_lo"], id_field["width"]


def _decode_line_f(d: _Decoder, op: int, pc: int) -> str:
    """Line-F: coprocessor (FPU/MMU), MOVE16, etc."""
    _masks = _load_kb_encoding_masks()
    _cpid_lo, _cpid_w = _load_kb_cpid_field()
    cpid = (op >> _cpid_lo) & ((1 << _cpid_w) - 1)

    # MOVE16 (68040) — separate encoding masks for postincrement vs absolute forms
    _m16_pi_m, _m16_pi_v = _load_kb_encoding_masks_idx(0)["MOVE16"]  # enc[0] postincrement
    if (op & _m16_pi_m) == _m16_pi_v:
        _m16f0 = _kb_field_map(0)["MOVE16"]
        ax = _xf(op, _m16f0["REGISTER Ax"])
        ext = d.read_u16()
        _m16f1 = _kb_field_map(1)["MOVE16"]
        ay = _xf(ext, _m16f1["REGISTER Ay"])
        return f"move16  (a{ax})+,(a{ay})+"
    _m16_abs_masks = _load_kb_encoding_masks_idx(2)
    if "MOVE16" in _m16_abs_masks:
        _m16a_m, _m16a_v = _m16_abs_masks["MOVE16"]
        if (op & _m16a_m) == _m16a_v:
            # OPMODE and REGISTER from KB encoding[2]
            _fmap = _kb_field_map(2)["MOVE16"]
            opmode = _xf(op, _fmap["OPMODE"])
            an = _xf(op, _fmap["REGISTER Ay"])
            addr = d.read_u32()
            # Operand order from KB opmode_table
            _m16_opm = _load_kb_opmode_tables()["MOVE16"]
            entry = _m16_opm[opmode]
            # Source field tells us which operand is first
            src = entry["source"]
            postinc = "+" in src
            abs_first = "(xxx)" in src
            if abs_first:
                reg_postinc = "+" in entry["destination"]
                return f"move16  ${addr:08x}.l,(a{an}){'+'if reg_postinc else ''}"
            else:
                return f"move16  (a{an}){'+'if postinc else ''},${addr:08x}.l"

    # MMU (cpid=0): PRESTORE/PSAVE/PBcc/PDBcc/PScc/PTRAPcc/PFLUSH/PFLUSHR
    if cpid == 0:
        _opf = _load_kb_opword_field_map()
        pmmu_cc = _load_disasm_meta()["pmmu_condition_codes"]

        # PRESTORE
        _m, _v = _masks["PRESTORE"]
        if (op & _m) == _v:
            _pr_f = _opf["PRESTORE"]
            mode = _xf(op, _pr_f["MODE"])
            reg = _xf(op, _pr_f["REGISTER"])
            ea = _ea_str(d, mode, reg, SIZE_LONG, pc)
            return f"prestore {ea}"

        # PSAVE
        _m, _v = _masks["PSAVE"]
        if (op & _m) == _v:
            _ps_f = _opf["PSAVE"]
            mode = _xf(op, _ps_f["MODE"])
            reg = _xf(op, _ps_f["REGISTER"])
            ea = _ea_str(d, mode, reg, SIZE_LONG, pc)
            return f"psave   {ea}"

        # PBcc — KB mask/val and fields
        _pbcc_m, _pbcc_v = _masks["PBcc"]
        if (op & _pbcc_m) == _pbcc_v:
            _pbcc_f = _opf["PBcc"]
            cond = _xf(op, _pbcc_f["MC68851 CONDITION"])
            cc = pmmu_cc[cond] if cond < len(pmmu_cc) else f"#{cond}"
            sz_val = _xf(op, _pbcc_f["SIZE"])
            if sz_val == 0:
                disp = d.read_i16()
                target = _branch_target(pc, disp)
                return f"pb{cc}.w  {target}"
            else:
                disp = d.read_i32()
                target = _branch_target(pc, disp)
                return f"pb{cc}.l  {target}"

        # PDBcc (more specific mask, check before PScc)
        _pdbcc_m, _pdbcc_v = _masks["PDBcc"]
        if (op & _pdbcc_m) == _pdbcc_v:
            _pdbcc_f = _opf["PDBcc"]
            reg = _xf(op, _pdbcc_f["COUNT REGISTER"])
            ext = d.read_u16()
            _pdbcc_ef = _load_kb_ext_field_map()["PDBcc"]
            cond = _xf(ext, _pdbcc_ef["MC68851 CONDITION"])
            cc = pmmu_cc[cond] if cond < len(pmmu_cc) else f"#{cond}"
            disp = d.read_i16()
            target = _branch_target(pc, disp)
            return f"pdb{cc}   d{reg},{target}"

        # PTRAPcc (more specific mask, check before PScc; validate opmode)
        _ptrap_m, _ptrap_v = _masks["PTRAPcc"]
        _ptrap_opm = _load_kb_opmode_tables()["PTRAPcc"]
        if (op & _ptrap_m) == _ptrap_v:
            _ptrap_f = _opf["PTRAPcc"]
            opmode = _xf(op, _ptrap_f["OPMODE"])
            if opmode in _ptrap_opm:
                ext = d.read_u16()
                _ptrap_ef = _load_kb_ext_field_map()["PTRAPcc"]
                cond = _xf(ext, _ptrap_ef["MC68851 CONDITION"])
                cc = pmmu_cc[cond] if cond < len(pmmu_cc) else f"#{cond}"
                entry = _ptrap_opm[opmode]
                sz = entry["size"]
                if sz == "w":
                    imm = d.read_u16()
                    return f"ptrap{cc}.w #{imm}"
                elif sz == "l":
                    imm = d.read_u32()
                    return f"ptrap{cc}.l #{imm}"
                else:
                    return f"ptrap{cc}"

        # PScc (broader mask, check last)
        _pscc_m, _pscc_v = _masks["PScc"]
        if (op & _pscc_m) == _pscc_v:
            _pscc_f = _opf["PScc"]
            mode = _xf(op, _pscc_f["MODE"])
            reg = _xf(op, _pscc_f["REGISTER"])
            ext = d.read_u16()
            _pscc_ef = _load_kb_ext_field_map()["PScc"]
            cond = _xf(ext, _pscc_ef["MC68851 CONDITION"])
            cc = pmmu_cc[cond] if cond < len(pmmu_cc) else f"#{cond}"
            ea = _ea_str(d, mode, reg, SIZE_BYTE, pc)
            return f"ps{cc}    {ea}"

        # PFLUSH/PFLUSHA/PFLUSHR or PMMU general (type_bits == 0)
        _pfl_f = _opf["PFLUSH"]
        mode = _xf(op, _pfl_f["MODE"])
        reg = _xf(op, _pfl_f["REGISTER"])
        ext = d.read_u16()
        _ext_masks = _load_kb_ext_encoding_masks()
        _pf_m, _pf_v = _ext_masks["PFLUSH"]
        if (ext & _pf_m) == _pf_v:
            _ext_fields = _load_kb_ext_field_map()["PFLUSH"]
            pflush_mode = _xf(ext, _ext_fields["MODE"])
            pflush_mask = _xf(ext, _ext_fields["MASK"])
            fc = _xf(ext, _ext_fields["FC"])
            if pflush_mode == 1:
                return "pflusha"
            ea = _ea_str(d, mode, reg, SIZE_LONG, pc)
            return f"pflush  #{fc},#{pflush_mask},{ea}"
        _pfr_m, _pfr_v = _ext_masks["PFLUSHR"]
        if (ext & _pfr_m) == _pfr_v:
            ea = _ea_str(d, mode, reg, SIZE_LONG, pc)
            return f"pflushr {ea}"
        # Other PMMU general commands (PMOVE, PLOAD, PTEST, PVALID)
        raise DecodeError(f"unsupported PMMU command: op=${op:04x} ext=${ext:04x}")

    # FPU (cpid=1): FRESTORE/FSAVE
    if cpid == 1:
        _opf = _load_kb_opword_field_map()

        _m, _v = _masks["FRESTORE"]
        if (op & _m) == _v:
            _fr_f = _opf["FRESTORE"]
            mode = _xf(op, _fr_f["MODE"])
            reg = _xf(op, _fr_f["REGISTER"])
            ea = _ea_str(d, mode, reg, SIZE_LONG, pc)
            return f"frestore {ea}"

        _m, _v = _masks["FSAVE"]
        if (op & _m) == _v:
            _fs_f = _opf["FSAVE"]
            mode = _xf(op, _fs_f["MODE"])
            reg = _xf(op, _fs_f["REGISTER"])
            ea = _ea_str(d, mode, reg, SIZE_LONG, pc)
            return f"fsave   {ea}"

        # Other FPU instructions (cpGEN etc.) — not yet decoded
        raise DecodeError(f"unsupported FPU command: op=${op:04x}")

    raise DecodeError(f"unsupported line-F op=${op:04x}")


# --- Public API ---

def disassemble(data: bytes, base_offset: int = 0, max_cpu: str | None = None) -> list[Instruction]:
    """Disassemble M68K code from raw bytes."""
    d = _Decoder(data, base_offset)
    instructions = []
    while d.remaining() >= 2:
        inst = _decode_one(d, max_cpu)
        instructions.append(inst)
    return instructions


def format_instruction(inst: Instruction, labels: dict[int, str] | None = None) -> str:
    """Format instruction for vasm-compatible output."""
    hex_bytes = " ".join(f"{b:02x}" for b in inst.raw[:8])
    if labels and inst.offset in labels:
        label = f"{labels[inst.offset]}:"
    else:
        label = ""
    return f"{label:20s}    {inst.text:40s} ; {inst.offset:06x}: {hex_bytes}"


if __name__ == "__main__":
    import sys
    from hunk_parser import parse_file, HunkType as HT

    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <hunk_file>")
        sys.exit(1)

    hf = parse_file(sys.argv[1])
    for hunk in hf.hunks:
        if hunk.hunk_type != HT.HUNK_CODE:
            continue
        print(f"; === Hunk #{hunk.index} CODE ({len(hunk.data)} bytes) ===")
        # Build label map from symbols
        labels = {s.value: s.name for s in hunk.symbols}
        instructions = disassemble(hunk.data)
        for inst in instructions:
            print(format_instruction(inst, labels))
        print()
