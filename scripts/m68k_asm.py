"""KB-driven M68K assembler — assembly text → machine code bytes.

All M68K knowledge comes from knowledge/m68k_instructions.json.
No instruction encodings, sizes, or field values are hardcoded.

Usage:
    from m68k_asm import assemble_instruction
    code = assemble_instruction("move.l d0,(a1)")
"""

import json
import re
import struct
from functools import lru_cache
from pathlib import Path

PROJ_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE = PROJ_ROOT / "knowledge" / "m68k_instructions.json"


# ── KB loader ─────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_kb():
    with open(KNOWLEDGE, encoding="utf-8") as f:
        data = json.load(f)
    instructions = data.get("instructions", [])
    meta = data.get("_meta", {})
    by_mnemonic = {}
    for inst in instructions:
        by_mnemonic[inst["mnemonic"]] = inst
    return by_mnemonic, instructions, meta

def _kb():
    return _load_kb()[0]

def _kb_list():
    return _load_kb()[1]

def _kb_meta():
    return _load_kb()[2]


# ── EA mode encoding from KB ─────────────────────────────────────────────

@lru_cache(maxsize=1)
def _ea_mode_encoding():
    """Return {mode_name: (mode_num, reg_or_none)} from KB _meta."""
    raw = _kb_meta()["ea_mode_encoding"]
    return {name: (vals[0], vals[1]) for name, vals in raw.items()}


@lru_cache(maxsize=1)
def _ea_brief_fields():
    """Return brief extension word field layout from KB _meta.

    Returns dict mapping field name to (bit_hi, bit_lo, width).
    """
    raw = _kb_meta()["ea_brief_ext_word"]
    return {f["name"]: (f["bit_hi"], f["bit_lo"], f["bit_hi"] - f["bit_lo"] + 1)
            for f in raw}


@lru_cache(maxsize=1)
def _size_byte_count():
    """Return {size_suffix: byte_count} from KB _meta."""
    return _kb_meta()["size_byte_count"]


# ── Bit field helpers ─────────────────────────────────────────────────────

def _pack_field(word, value, bit_hi, bit_lo):
    """Set bits [bit_hi:bit_lo] of word to value."""
    width = bit_hi - bit_lo + 1
    mask = (1 << width) - 1
    return word | ((value & mask) << bit_lo)


def _to_bytes_16(val):
    """Pack a 16-bit value as big-endian bytes."""
    return struct.pack(">H", val & 0xFFFF)


def _to_bytes_32(val):
    """Pack a 32-bit value as big-endian bytes."""
    return struct.pack(">I", val & 0xFFFFFFFF)


# ── EA mode parser (the shared core) ─────────────────────────────────────

# Regex patterns for operand syntax.
# These are Motorola assembly syntax conventions, not M68K instruction knowledge.
_RE_DN = re.compile(r'^d([0-7])$', re.I)
_RE_AN = re.compile(r'^a([0-7])$', re.I)
_RE_SP = re.compile(r'^sp$', re.I)
_RE_IND = re.compile(r'^\(a([0-7])\)$', re.I)
_RE_IND_SP = re.compile(r'^\(sp\)$', re.I)
_RE_POSTINC = re.compile(r'^\(a([0-7])\)\+$', re.I)
_RE_POSTINC_SP = re.compile(r'^\(sp\)\+$', re.I)
_RE_PREDEC = re.compile(r'^-\(a([0-7])\)$', re.I)
_RE_PREDEC_SP = re.compile(r'^-\(sp\)$', re.I)
_RE_DISP = re.compile(r'^(-?\d+)\(a([0-7])\)$', re.I)
_RE_DISP_SP = re.compile(r'^(-?\d+)\(sp\)$', re.I)
_RE_INDEX = re.compile(
    r'^(-?\d+)\(a([0-7]),([da])([0-7])\.(w|l)\)$', re.I)
_RE_INDEX_SP = re.compile(
    r'^(-?\d+)\(sp,([da])([0-7])\.(w|l)\)$', re.I)
_RE_PCDISP = re.compile(r'^(-?\d+)\(pc\)$', re.I)
_RE_PCINDEX = re.compile(
    r'^(-?\d+)\(pc,([da])([0-7])\.(w|l)\)$', re.I)
_RE_IMM = re.compile(r'^#(.+)$', re.I)
_RE_ABSW = re.compile(r'^\(?\$?([0-9a-f]+)\)?\.(w)$', re.I)
_RE_ABSL_HEX = re.compile(r'^\$([0-9a-f]+)$', re.I)
_RE_ABSL_DEC = re.compile(r'^(\d+)$')


def _parse_imm_value(s):
    """Parse an immediate value string (hex $NN or decimal)."""
    s = s.strip()
    if s.startswith("$") or s.startswith("0x"):
        return int(s.replace("$", ""), 16)
    return int(s)


def _build_brief_ext_word(xreg_num, is_addr, is_long, disp8):
    """Build brief extension word from KB field layout."""
    bf = _ea_brief_fields()
    word = 0
    word = _pack_field(word, 1 if is_addr else 0, *bf["D/A"][:2])
    word = _pack_field(word, xreg_num, *bf["REGISTER"][:2])
    word = _pack_field(word, 1 if is_long else 0, *bf["W/L"][:2])
    # SCALE = 0 (×1) for 68000 basic indexed mode
    word = _pack_field(word, disp8 & 0xFF, *bf["DISPLACEMENT"][:2])
    return word


def parse_ea(operand, op_size=None):
    """Parse an EA operand string into (mode_num, reg_num, extension_bytes).

    Args:
        operand: Assembly operand text (e.g. "d0", "(a1)+", "#$1234")
        op_size: Operation size as int bytes (1, 2, or 4) for immediate sizing.
                 Can be None if not immediate.

    Returns:
        (mode, reg, ext_bytes) where:
            mode: EA mode number (0-7)
            reg: register number (0-7) or sub-mode for mode 7
            ext_bytes: bytes object with extension word data (may be empty)
    """
    operand = operand.strip()
    enc = _ea_mode_encoding()

    # Dn
    m = _RE_DN.match(operand)
    if m:
        mode, _ = enc["dn"]
        return mode, int(m.group(1)), b""

    # An or SP
    m = _RE_AN.match(operand)
    if m:
        mode, _ = enc["an"]
        return mode, int(m.group(1)), b""
    if _RE_SP.match(operand):
        mode, _ = enc["an"]
        return mode, 7, b""

    # (An)+ / (SP)+
    m = _RE_POSTINC.match(operand)
    if m:
        mode, _ = enc["postinc"]
        return mode, int(m.group(1)), b""
    if _RE_POSTINC_SP.match(operand):
        mode, _ = enc["postinc"]
        return mode, 7, b""

    # -(An) / -(SP)
    m = _RE_PREDEC.match(operand)
    if m:
        mode, _ = enc["predec"]
        return mode, int(m.group(1)), b""
    if _RE_PREDEC_SP.match(operand):
        mode, _ = enc["predec"]
        return mode, 7, b""

    # d(An,Xn.s) — indexed (must check before disp because of overlapping patterns)
    m = _RE_INDEX.match(operand)
    if m:
        disp = int(m.group(1))
        areg = int(m.group(2))
        xtype = m.group(3).lower()
        xreg = int(m.group(4))
        xsize = m.group(5).lower()
        mode, _ = enc["index"]
        ext_word = _build_brief_ext_word(xreg, xtype == "a", xsize == "l", disp)
        return mode, areg, _to_bytes_16(ext_word)
    m = _RE_INDEX_SP.match(operand)
    if m:
        xtype = m.group(2).lower()
        xreg = int(m.group(3))
        xsize = m.group(4).lower()
        disp = int(m.group(1))
        mode, _ = enc["index"]
        ext_word = _build_brief_ext_word(xreg, xtype == "a", xsize == "l", disp)
        return mode, 7, _to_bytes_16(ext_word)

    # d(An) / d(SP) — displacement
    m = _RE_DISP.match(operand)
    if m:
        disp = int(m.group(1))
        areg = int(m.group(2))
        mode, _ = enc["disp"]
        return mode, areg, _to_bytes_16(disp)
    m = _RE_DISP_SP.match(operand)
    if m:
        disp = int(m.group(1))
        mode, _ = enc["disp"]
        return mode, 7, _to_bytes_16(disp)

    # (An) / (SP) — indirect (check after postinc/predec/disp/index)
    m = _RE_IND.match(operand)
    if m:
        mode, _ = enc["ind"]
        return mode, int(m.group(1)), b""
    if _RE_IND_SP.match(operand):
        mode, _ = enc["ind"]
        return mode, 7, b""

    # d(PC,Xn.s) — PC indexed
    m = _RE_PCINDEX.match(operand)
    if m:
        disp = int(m.group(1))
        xtype = m.group(2).lower()
        xreg = int(m.group(3))
        xsize = m.group(4).lower()
        mode, reg = enc["pcindex"]
        ext_word = _build_brief_ext_word(xreg, xtype == "a", xsize == "l", disp)
        return mode, reg, _to_bytes_16(ext_word)

    # d(PC) — PC displacement
    m = _RE_PCDISP.match(operand)
    if m:
        disp = int(m.group(1))
        mode, reg = enc["pcdisp"]
        return mode, reg, _to_bytes_16(disp)

    # #imm — immediate
    m = _RE_IMM.match(operand)
    if m:
        val = _parse_imm_value(m.group(1))
        mode, reg = enc["imm"]
        if op_size is not None and op_size >= 4:
            return mode, reg, _to_bytes_32(val)
        else:
            return mode, reg, _to_bytes_16(val)

    # ($xxxx).w — absolute word
    m = _RE_ABSW.match(operand)
    if m:
        addr = int(m.group(1), 16)
        mode, reg = enc["absw"]
        return mode, reg, _to_bytes_16(addr)

    # $xxxx — absolute long (hex)
    m = _RE_ABSL_HEX.match(operand)
    if m:
        addr = int(m.group(1), 16)
        mode, reg = enc["absl"]
        return mode, reg, _to_bytes_32(addr)

    # decimal number — absolute long
    m = _RE_ABSL_DEC.match(operand)
    if m:
        addr = int(m.group(1))
        mode, reg = enc["absl"]
        return mode, reg, _to_bytes_32(addr)

    raise ValueError(f"Cannot parse EA operand: {operand!r}")


# ── KB encoding helpers ───────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _kb_encoding_masks():
    """Return {mnemonic: (mask, val, fields)} from KB encoding fixed bits.

    fields is list of (name, bit_hi, bit_lo, width) for variable fields.
    """
    result = {}
    for inst in _kb_list():
        if not inst.get("encodings"):
            continue
        enc = inst["encodings"][0]
        mask = val = 0
        fields = []
        for f in enc["fields"]:
            if f["name"] in ("0", "1"):
                bit = 1 if f["name"] == "1" else 0
                for b in range(f["bit_lo"], f["bit_hi"] + 1):
                    mask |= (1 << b)
                    val |= (bit << b)
            else:
                fields.append((f["name"], f["bit_hi"], f["bit_lo"],
                               f["bit_hi"] - f["bit_lo"] + 1))
        result[inst["mnemonic"]] = (mask, val, fields)
    return result


@lru_cache(maxsize=1)
def _kb_size_encodings():
    """Return {mnemonic: {size_suffix: binary_val}} — reverse of disassembler's mapping.

    Parses size encoding from KB field_descriptions.Size text.
    """
    size_name_map = {"byte": "b", "word": "w", "long": "l"}
    result = {}
    for inst in _kb_list():
        fd = inst.get("field_descriptions", {})
        size_desc = fd.get("Size", "")
        if not size_desc:
            continue
        mapping = {}
        for m in re.finditer(
                r"([01]{1,2})\s*[\u2014\u2013\-]\s*(Byte|Word|Long)",
                size_desc, re.IGNORECASE):
            bits = int(m.group(1), 2)
            sz = size_name_map[m.group(2).lower()]
            mapping[sz] = bits
        if mapping:
            result[inst["mnemonic"]] = mapping
    return result


@lru_cache(maxsize=1)
def _kb_opmode_tables():
    """Return {mnemonic: [{opmode, size, operation}, ...]} from KB constraints."""
    result = {}
    for inst in _kb_list():
        opm = inst.get("constraints", {}).get("opmode_table")
        if opm:
            result[inst["mnemonic"]] = opm
    return result


@lru_cache(maxsize=1)
def _kb_cc_index():
    """Return {cc_name: index} from KB _meta.condition_codes."""
    return {name: i for i, name in enumerate(_kb_meta()["condition_codes"])}


@lru_cache(maxsize=1)
def _kb_cc_families():
    """Return {prefix: (mnemonic, cc_parameterized_info)} for cc-parameterized instructions."""
    result = {}
    for inst in _kb_list():
        cc_param = inst.get("constraints", {}).get("cc_parameterized")
        if cc_param:
            result[cc_param["prefix"]] = (inst["mnemonic"], cc_param)
    return result


@lru_cache(maxsize=1)
def _kb_immediate_ranges():
    """Return {mnemonic: immediate_range_info} from KB constraints."""
    result = {}
    for inst in _kb_list():
        ir = inst.get("constraints", {}).get("immediate_range")
        if ir:
            result[inst["mnemonic"]] = ir
    return result


# ── Mnemonic resolution ──────────────────────────────────────────────────

def _parse_mnemonic_size(text):
    """Parse 'move.l' → ('move', 'l') or 'nop' → ('nop', None)."""
    text = text.strip().lower()
    # Try splitting on last dot
    if "." in text:
        parts = text.rsplit(".", 1)
        if parts[1] in ("b", "w", "l", "s"):
            return parts[0], parts[1]
    return text, None


def _resolve_cc_mnemonic(mnemonic_lower):
    """Check if mnemonic is a cc-parameterized variant (e.g. 'beq' → Bcc, cc=1).

    Also handles CC aliases from KB _meta.cc_aliases (e.g. 'dbra' → DBcc with
    cc=F, 'blo' → Bcc with cc=CS).

    Returns (kb_inst, cc_index) or None.
    """
    families = _kb_cc_families()
    cc_idx = _kb_cc_index()
    cc_aliases = _kb_meta().get("cc_aliases", {})

    for prefix, (kb_mnemonic, cc_param) in families.items():
        if mnemonic_lower.startswith(prefix) and len(mnemonic_lower) > len(prefix):
            cc_suffix = mnemonic_lower[len(prefix):]
            # Direct CC match
            if cc_suffix in cc_idx:
                excluded = set(cc_param.get("excluded", []))
                if cc_suffix not in excluded:
                    return _kb()[kb_mnemonic], cc_idx[cc_suffix]
            # Alias CC match (e.g. "ra" → "f", "lo" → "cs")
            canonical = cc_aliases.get(cc_suffix)
            if canonical and canonical in cc_idx:
                excluded = set(cc_param.get("excluded", []))
                if canonical not in excluded:
                    return _kb()[kb_mnemonic], cc_idx[canonical]
    return None


def _resolve_direction_mnemonic(mnemonic_lower):
    """Check if mnemonic is a direction variant (e.g. 'asl' → 'ASL, ASR', direction=L).

    KB direction_variants has:
        field: "dr"
        values: {"0": "r", "1": "l"}  — bit_value → suffix
        base: "as"
        variants: ["asl", "asr"]  — string list of valid mnemonics

    Returns (kb_inst, direction_bit_value, individual_mnemonic) or None.
    """
    kb = _kb()
    for mnemonic, inst in kb.items():
        dv = inst.get("constraints", {}).get("direction_variants")
        if not dv:
            continue
        variants = dv.get("variants", [])
        # variants are strings like ["asl", "asr"]
        if mnemonic_lower not in [v.lower() for v in variants]:
            continue
        # Matched — derive direction bit value from suffix
        base = dv.get("base", "")
        suffix = mnemonic_lower[len(base):]
        for bit_val, dir_char in dv.get("values", {}).items():
            if dir_char == suffix:
                return inst, int(bit_val), mnemonic_lower
    return None


def resolve_instruction(mnemonic_str, size_char=None):
    """Resolve assembly mnemonic to KB instruction + context.

    Returns dict with keys:
        inst: KB instruction dict
        cc_index: condition code index (for Bcc/Scc/DBcc) or None
        direction: direction field value (for shifts/rotates) or None
        direction_mnemonic: individual mnemonic (for combined like ASL,ASR) or None
        size: size suffix character or None
    """
    mnemonic_lower = mnemonic_str.lower()

    # Direct match (case-insensitive, try upper)
    kb = _kb()
    for kb_mnemonic, inst in kb.items():
        # Match against the full mnemonic or any comma-separated part
        parts = [p.strip().lower() for p in kb_mnemonic.split(",")]
        if mnemonic_lower in parts:
            # If this instruction has direction variants, delegate to that path
            # so the direction field value gets resolved properly
            if inst.get("constraints", {}).get("direction_variants"):
                break  # fall through to direction variant check below
            # If this instruction is CC-parameterized (Scc, Bcc, etc.), delegate
            # to the CC resolution path so the condition index gets set
            if inst.get("constraints", {}).get("cc_parameterized"):
                break  # fall through to CC-parameterized check below
            return {
                "inst": inst,
                "cc_index": None,
                "direction": None,
                "direction_mnemonic": None,
                "size": size_char,
                "mnemonic_str": mnemonic_lower,
            }

    # CC-parameterized (beq, bne, scc, dbcc, etc.)
    cc_result = _resolve_cc_mnemonic(mnemonic_lower)
    if cc_result:
        return {
            "inst": cc_result[0],
            "cc_index": cc_result[1],
            "direction": None,
            "direction_mnemonic": None,
            "size": size_char,
            "mnemonic_str": mnemonic_lower,
        }

    # Direction variants (asl, asr, lsl, lsr, rol, ror, roxl, roxr)
    dir_result = _resolve_direction_mnemonic(mnemonic_lower)
    if dir_result:
        return {
            "inst": dir_result[0],
            "cc_index": None,
            "direction": dir_result[1],
            "direction_mnemonic": dir_result[2],
            "size": size_char,
            "mnemonic_str": mnemonic_lower,
        }

    raise ValueError(f"Unknown mnemonic: {mnemonic_str!r}")


# ── Opword construction ──────────────────────────────────────────────────

def _build_opword(inst, field_values, enc_idx=0):
    """Build opword from KB encoding fixed bits + variable field values.

    Args:
        inst: KB instruction dict
        field_values: dict mapping field name to value.
            For duplicate fields (e.g. MOVE has two MODE), use
            field_values with list values — first element is highest bit position.
            For named fields (e.g. "REGISTER Rx"), use exact names.
        enc_idx: which encoding to use (default 0, the primary encoding).

    Returns:
        16-bit opword integer.
    """
    enc = inst["encodings"][enc_idx]
    word = 0

    # Set fixed bits
    for f in enc["fields"]:
        if f["name"] in ("0", "1"):
            bit = 1 if f["name"] == "1" else 0
            word = _pack_field(word, bit, f["bit_hi"], f["bit_lo"])

    # Set variable fields
    # Support two styles:
    #   1. Exact named fields: {"REGISTER Rx": 3, "REGISTER Ry": 5}
    #   2. List-based duplicates: {"REGISTER": [3, 5]} (indexed by occurrence order)
    field_counts = {}
    for f in enc["fields"]:
        name = f["name"]
        if name in ("0", "1"):
            continue

        # Try exact field name match first
        exact_val = field_values.get(name)
        if exact_val is not None and not isinstance(exact_val, list):
            word = _pack_field(word, exact_val, f["bit_hi"], f["bit_lo"])
            continue

        # Fallback: base name (before space) with index tracking for list values
        base_name = name.split(" ")[0] if " " in name else name
        idx = field_counts.get(base_name, 0)
        field_counts[base_name] = idx + 1

        val = exact_val if exact_val is not None else field_values.get(base_name)
        if val is None:
            continue
        if isinstance(val, list):
            if idx < len(val):
                word = _pack_field(word, val[idx], f["bit_hi"], f["bit_lo"])
        else:
            if idx == 0:
                word = _pack_field(word, val, f["bit_hi"], f["bit_lo"])

    return word


def _get_size_encoding(inst, size_char):
    """Get binary size field value for an instruction.

    Returns the binary value to pack into the SIZE field, or None if no size field.
    """
    mnemonic = inst["mnemonic"]
    size_encs = _kb_size_encodings()
    if mnemonic in size_encs:
        enc = size_encs[mnemonic]
        if size_char in enc:
            return enc[size_char]
    # Default encoding: b=0, w=1, l=2 (most instructions use this)
    # This default is derived from the most common pattern in KB field_descriptions
    default = {"b": 0, "w": 1, "l": 2}
    return default.get(size_char)


# ── Instruction assemblers ────────────────────────────────────────────────

def _assemble_no_operands(inst, resolution):
    """Assemble instructions with no operands (NOP, RTS, RTE, etc.)."""
    word = _build_opword(inst, {})
    return _to_bytes_16(word)


def _assemble_ea_single(inst, resolution, operand, enc_idx=0):
    """Assemble instructions with a single EA operand (CLR, NEG, NOT, TST, etc.)."""
    size_char = resolution["size"]
    size_enc = _get_size_encoding(inst, size_char)
    sz_bytes = _size_byte_count().get(size_char, 2) if size_char else 2

    mode, reg, ext = parse_ea(operand, sz_bytes)

    fields = {"SIZE": size_enc, "MODE": mode, "REGISTER": reg}

    # CC-parameterized single EA (Scc)
    if resolution["cc_index"] is not None:
        fields["CONDITION"] = resolution["cc_index"]

    word = _build_opword(inst, fields)
    return _to_bytes_16(word) + ext


def _assemble_two_ea(inst, resolution, src_str, dst_str):
    """Assemble instructions with source and destination EA (MOVE, etc.)."""
    size_char = resolution["size"]
    size_enc = _get_size_encoding(inst, size_char)
    sz_bytes = _size_byte_count().get(size_char, 2) if size_char else 2

    src_mode, src_reg, src_ext = parse_ea(src_str, sz_bytes)
    dst_mode, dst_reg, dst_ext = parse_ea(dst_str, sz_bytes)

    # For MOVE, encoding has: dst_reg[11:9], dst_mode[8:6], src_mode[5:3], src_reg[2:0]
    # KB encoding lists fields in bit order (high to low), so:
    # First REGISTER = dst (bits 11:9), second REGISTER = src (bits 2:0)
    # First MODE = dst (bits 8:6), second MODE = src (bits 5:3)
    # Use list values for duplicate fields — first = highest bit position = destination.

    # Check if this instruction has duplicate MODE/REGISTER fields
    enc = inst["encodings"][0]
    mode_count = sum(1 for f in enc["fields"] if f["name"] == "MODE")

    if mode_count >= 2:
        # Dual EA (MOVE-style): higher bits = destination
        fields = {
            "MODE": [dst_mode, src_mode],
            "REGISTER": [dst_reg, src_reg],
        }
    else:
        # Single EA + register (ADD-style): handled by _assemble_opmode instead
        raise ValueError(f"_assemble_two_ea called for non-dual-EA instruction {inst['mnemonic']}")

    if size_enc is not None:
        fields["SIZE"] = size_enc

    word = _build_opword(inst, fields)
    return _to_bytes_16(word) + src_ext + dst_ext


def _assemble_opmode(inst, resolution, src_str, dst_str):
    """Assemble instructions with OPMODE field (ADD, SUB, AND, OR, CMP, etc.).

    OPMODE determines both size and direction (ea→Dn or Dn→ea).
    """
    size_char = resolution["size"]
    sz_bytes = _size_byte_count().get(size_char, 2) if size_char else 2

    opm_table = inst.get("constraints", {}).get("opmode_table", [])
    if not opm_table:
        raise ValueError(f"{inst['mnemonic']}: no opmode_table in KB")

    src_mode, src_reg, src_ext = parse_ea(src_str, sz_bytes)
    dst_mode, dst_reg, dst_ext = parse_ea(dst_str, sz_bytes)

    # Determine direction from operands:
    # If dst is Dn (mode 0), direction is ea→Dn: look for matching opmode with "→ Dn" operation
    # If src is Dn (mode 0) and dst is EA, direction is Dn→ea: look for "→ <ea>" operation
    enc = _ea_mode_encoding()
    dn_mode = enc["dn"][0]

    selected_opmode = None
    if dst_mode == dn_mode:
        # Destination is Dn — find opmode for ea→Dn at this size
        for entry in opm_table:
            if entry["size"] == size_char and "Dn" in entry.get("operation", "").split("→")[-1]:
                selected_opmode = entry["opmode"]
                break
    if selected_opmode is None and src_mode == dn_mode:
        # Source is Dn — find opmode for Dn→ea at this size
        for entry in opm_table:
            op = entry.get("operation", "")
            if entry["size"] == size_char and "ea" in op.split("→")[-1].lower():
                selected_opmode = entry["opmode"]
                break
    if selected_opmode is None:
        # Fallback: just match size (e.g. CMP only has ea→Dn direction)
        for entry in opm_table:
            if entry["size"] == size_char:
                selected_opmode = entry["opmode"]
                break

    if selected_opmode is None:
        raise ValueError(
            f"{inst['mnemonic']}.{size_char}: no matching opmode for "
            f"src_mode={src_mode} dst_mode={dst_mode}")

    # For opmode instructions: REGISTER field = Dn register, MODE/REGISTER(EA) = the EA operand
    if dst_mode == dn_mode:
        # ea→Dn: REGISTER=dst_reg(Dn), MODE=src_mode, EA_REGISTER=src_reg
        fields = {"REGISTER": dst_reg, "OPMODE": selected_opmode,
                  "MODE": src_mode}
        # Find the EA register field (might be named REGISTER too — it's the lower one)
        enc_fields = inst["encodings"][0]["fields"]
        reg_fields = [f for f in enc_fields if f["name"] == "REGISTER"]
        if len(reg_fields) >= 2:
            # Two REGISTER fields: higher = Dn, lower = EA reg
            fields["REGISTER"] = [dst_reg, src_reg]
        else:
            # Single REGISTER field — EA reg is separate
            fields["REGISTER"] = dst_reg
            # Hmm, need to figure out which field holds the EA register
            # For ADD etc., the encoding is: REGISTER[11:9]=Dn, OPMODE[8:6], MODE[5:3], REGISTER[2:0]=EA
            fields["REGISTER"] = [dst_reg, src_reg]
        word = _build_opword(inst, fields)
        return _to_bytes_16(word) + src_ext
    else:
        # Dn→ea: REGISTER=src_reg(Dn), MODE=dst_mode, EA_REGISTER=dst_reg
        fields = {"REGISTER": [src_reg, dst_reg], "OPMODE": selected_opmode,
                  "MODE": dst_mode}
        word = _build_opword(inst, fields)
        return _to_bytes_16(word) + dst_ext


def _assemble_immediate(inst, resolution, imm_str, dst_str):
    """Assemble immediate instructions (ADDI, SUBI, ORI, ANDI, EORI, CMPI)."""
    size_char = resolution["size"]
    size_enc = _get_size_encoding(inst, size_char)
    sz_bytes = _size_byte_count().get(size_char, 2) if size_char else 2

    imm_val = _parse_imm_value(imm_str.lstrip("#"))
    dst_mode, dst_reg, dst_ext = parse_ea(dst_str, sz_bytes)

    fields = {"SIZE": size_enc, "MODE": dst_mode, "REGISTER": dst_reg}
    word = _build_opword(inst, fields)

    # Immediate data extension word(s)
    if sz_bytes >= 4:
        imm_bytes = _to_bytes_32(imm_val)
    else:
        imm_bytes = _to_bytes_16(imm_val)

    return _to_bytes_16(word) + imm_bytes + dst_ext


def _assemble_quick(inst, resolution, imm_str, dst_str):
    """Assemble ADDQ/SUBQ — inline 3-bit immediate with zero_means."""
    size_char = resolution["size"]
    size_enc = _get_size_encoding(inst, size_char)
    sz_bytes = _size_byte_count().get(size_char, 2) if size_char else 2

    imm_val = _parse_imm_value(imm_str.lstrip("#"))
    dst_mode, dst_reg, dst_ext = parse_ea(dst_str, sz_bytes)

    # Handle zero_means: if imm_val equals zero_means value, encode as 0
    ir = inst.get("constraints", {}).get("immediate_range", {})
    zero_means = ir.get("zero_means")
    data_val = imm_val
    if zero_means is not None and imm_val == zero_means:
        data_val = 0

    fields = {"SIZE": size_enc, "MODE": dst_mode, "REGISTER": dst_reg,
              "DATA": data_val}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word) + dst_ext


def _assemble_moveq(inst, resolution, imm_str, dst_str):
    """Assemble MOVEQ — 8-bit immediate in opword."""
    imm_val = _parse_imm_value(imm_str.lstrip("#"))

    # Destination must be Dn
    m = _RE_DN.match(dst_str.strip())
    if not m:
        raise ValueError(f"MOVEQ destination must be Dn, got {dst_str!r}")
    dreg = int(m.group(1))

    fields = {"REGISTER": dreg, "DATA": imm_val & 0xFF}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word)


def _assemble_branch(inst, resolution, target_str, pc=0):
    """Assemble branch instructions (Bcc, BRA, BSR).

    target_str is a target address (absolute or label).
    Displacement is computed as target - (pc + 2), per M68K semantics:
    the PC used for displacement calculation points to the extension word
    (or the byte after the opword for .b branches), i.e. pc_of_opword + 2.

    Displacement encoding rules (reserved values, extension sizes) are read
    from KB constraints.displacement_encoding.
    When no size specified: auto-select .b if displacement fits, else .w.
    """
    size_char = resolution["size"]
    cc_index = resolution["cc_index"]
    ir = inst.get("constraints", {}).get("immediate_range", {})
    disp_enc = inst.get("constraints", {}).get("displacement_encoding", {})

    # KB-driven displacement field name, reserved values, and extension sizes
    disp_field = disp_enc.get("field", ir.get("field", "8-BIT DISPLACEMENT"))
    word_signal = disp_enc.get("word_signal")
    long_signal = disp_enc.get("long_signal")
    word_bits = disp_enc.get("word_bits", 16)
    long_bits = disp_enc.get("long_bits", 32)

    # KB-driven byte displacement range
    byte_min = ir.get("min", -128)
    byte_max = ir.get("max", 127)

    target = _parse_imm_value(target_str)
    disp = target - (pc + 2)

    fields = {}
    if cc_index is not None:
        fields["CONDITION"] = cc_index

    # Reserved values in the byte displacement field (signal word/long extension)
    reserved = set()
    if word_signal is not None:
        reserved.add(word_signal)            # 0x00 → word extension
    if long_signal is not None:
        reserved.add(long_signal - 256)      # 0xFF as signed → -1

    # Auto-select size if none specified
    if size_char is None:
        if byte_min <= disp <= byte_max and (disp & 0xFF) not in {
                v & 0xFF for v in reserved | {word_signal or 0,
                                              long_signal or 255}}:
            size_char = "b"
        else:
            size_char = "w"

    if size_char == "s" or size_char == "b":
        disp_unsigned = disp & 0xFF
        if not (byte_min <= disp <= byte_max) or disp_unsigned in {
                word_signal, long_signal}:
            raise ValueError(
                f"Branch displacement {disp} out of .b range "
                f"({byte_min}..{byte_max}, "
                f"excluding reserved values {sorted(reserved)})")
        fields[disp_field] = disp_unsigned
        word = _build_opword(inst, fields)
        return _to_bytes_16(word)
    elif size_char == "w":
        word_max = (1 << (word_bits - 1)) - 1
        word_min = -(1 << (word_bits - 1))
        if not (word_min <= disp <= word_max):
            raise ValueError(
                f"Branch displacement {disp} out of .w range "
                f"({word_min}..{word_max})")
        fields[disp_field] = word_signal if word_signal is not None else 0x00
        word = _build_opword(inst, fields)
        return _to_bytes_16(word) + _to_bytes_16(disp & 0xFFFF)
    else:
        # Long branch (020+)
        fields[disp_field] = long_signal if long_signal is not None else 0xFF
        word = _build_opword(inst, fields)
        return _to_bytes_16(word) + _to_bytes_32(disp & 0xFFFFFFFF)


def _assemble_dbcc(inst, resolution, reg_str, target_str, pc=0):
    """Assemble DBcc — decrement and branch.

    Displacement is computed as target - (pc + 2), same as Bcc.
    DBcc always uses 16-bit displacement.
    """
    cc_index = resolution["cc_index"]
    m = _RE_DN.match(reg_str.strip())
    if not m:
        raise ValueError(f"DBcc register must be Dn, got {reg_str!r}")
    dreg = int(m.group(1))

    target = _parse_imm_value(target_str)
    disp = target - (pc + 2)

    if not (-32768 <= disp <= 32767):
        raise ValueError(
            f"DBcc displacement {disp} out of range (-32768..+32767)")

    fields = {"CONDITION": cc_index, "REGISTER": dreg}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word) + _to_bytes_16(disp & 0xFFFF)


def _assemble_shift_reg(inst, resolution, operands):
    """Assemble shift/rotate register form: ASL Dx,Dy or ASL #n,Dy.

    KB encoding has two REGISTER fields:
        REGISTER(11:9) = count/register (immediate count or source Dn number)
        REGISTER(2:0)  = destination Dn
    The type bits (distinguishing ASL/LSL/ROL/ROXL) are fixed in each
    instruction's encoding — no variable type field needed.
    """
    size_char = resolution["size"]
    size_enc = _get_size_encoding(inst, size_char)
    direction = resolution["direction"]

    src_str, dst_str = operands

    # Destination must be Dn
    m = _RE_DN.match(dst_str.strip())
    if not m:
        raise ValueError(f"Shift destination must be Dn, got {dst_str!r}")
    dst_reg = int(m.group(1))

    fields = {"SIZE": size_enc}
    if direction is not None:
        fields["dr"] = direction

    # Determine i/r and count/register from source
    src_stripped = src_str.strip()
    m_imm = _RE_IMM.match(src_stripped)
    m_dn = _RE_DN.match(src_stripped)

    if m_imm:
        count = _parse_imm_value(m_imm.group(1))
        ir = inst.get("constraints", {}).get("immediate_range", {})
        zero_means = ir.get("zero_means")
        if zero_means is not None and count == zero_means:
            count = 0
        # REGISTER(11:9) = count, REGISTER(2:0) = dst
        fields["REGISTER"] = [count, dst_reg]
        fields["i/r"] = 0  # immediate
    elif m_dn:
        # REGISTER(11:9) = source Dn, REGISTER(2:0) = dst
        fields["REGISTER"] = [int(m_dn.group(1)), dst_reg]
        fields["i/r"] = 1  # register

    word = _build_opword(inst, fields)
    return _to_bytes_16(word)


def _assemble_shift_mem(inst, resolution, operand):
    """Assemble shift/rotate memory form: ASL <ea> (single-operand, word-only).

    Uses encoding[1] which has dr + MODE/REGISTER for the EA.
    The shift count is always 1 (implicit).
    """
    direction = resolution["direction"]
    mode, reg, ext = parse_ea(operand)

    fields = {"MODE": mode, "REGISTER": reg}
    if direction is not None:
        fields["dr"] = direction
    word = _build_opword(inst, fields, enc_idx=1)
    return _to_bytes_16(word) + ext


def _assemble_ea_dn(inst, resolution, src_str, dst_str):
    """Assemble <ea>,Dn form — CHK, DIVS, DIVU, MULS, MULU.

    Encoding: REGISTER(11:9)=Dn, MODE(5:3)+REGISTER(2:0)=EA source.
    CHK also has a SIZE field.
    """
    size_char = resolution["size"]
    size_enc = _get_size_encoding(inst, size_char)
    sz_bytes = _size_byte_count().get(size_char, 2) if size_char else 2

    src_mode, src_reg, src_ext = parse_ea(src_str, sz_bytes)

    m = _RE_DN.match(dst_str.strip())
    if not m:
        raise ValueError(f"{inst['mnemonic']}: destination must be Dn, got {dst_str!r}")
    dn_reg = int(m.group(1))

    fields = {"REGISTER": [dn_reg, src_reg], "MODE": src_mode}
    if size_enc is not None:
        fields["SIZE"] = size_enc
    word = _build_opword(inst, fields)
    return _to_bytes_16(word) + src_ext


def _assemble_movep(inst, resolution, src_str, dst_str):
    """Assemble MOVEP — data register to/from memory displacement.

    KB encoding uses named fields: DATA REGISTER (11:9), ADDRESS REGISTER (2:0).
    Direction and size determined from opmode_table.
    """
    size_char = resolution["size"]

    # Determine direction from operands
    ms_dn = _RE_DN.match(src_str.strip())
    md_dn = _RE_DN.match(dst_str.strip())

    opm_table = inst.get("constraints", {}).get("opmode_table", [])
    selected = None

    if ms_dn and not md_dn:
        # Dn,d(An) → register to memory
        data_reg = int(ms_dn.group(1))
        m = _RE_DISP.match(dst_str.strip()) or _RE_DISP_SP.match(dst_str.strip())
        if not m:
            raise ValueError(f"MOVEP: destination must be d(An), got {dst_str!r}")
        disp = int(m.group(1))
        addr_reg = 7 if _RE_DISP_SP.match(dst_str.strip()) else int(m.group(2))
        for entry in opm_table:
            desc = entry.get("description", "").lower()
            if entry["size"] == size_char and "to memory" in desc:
                selected = entry["opmode"]
                break
    elif md_dn and not ms_dn:
        # d(An),Dn → memory to register
        data_reg = int(md_dn.group(1))
        m = _RE_DISP.match(src_str.strip()) or _RE_DISP_SP.match(src_str.strip())
        if not m:
            raise ValueError(f"MOVEP: source must be d(An), got {src_str!r}")
        disp = int(m.group(1))
        addr_reg = 7 if _RE_DISP_SP.match(src_str.strip()) else int(m.group(2))
        for entry in opm_table:
            desc = entry.get("description", "").lower()
            if entry["size"] == size_char and "to register" in desc:
                selected = entry["opmode"]
                break
    else:
        raise ValueError(f"MOVEP: need Dn,d(An) or d(An),Dn")

    if selected is None:
        raise ValueError(f"MOVEP.{size_char}: no matching opmode")

    fields = {"DATA REGISTER": data_reg, "OPMODE": selected,
              "ADDRESS REGISTER": addr_reg}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word) + _to_bytes_16(disp)


def _assemble_movem(inst, resolution, operands):
    """Assemble MOVEM — register list to/from memory."""
    size_char = resolution["size"]
    size_enc = _get_size_encoding(inst, size_char)
    sz_bytes = _size_byte_count().get(size_char, 2) if size_char else 2

    src_str, dst_str = operands

    # Determine direction: reg-to-mem or mem-to-reg
    # If source looks like a register list, it's reg-to-mem
    # If destination looks like a register list, it's mem-to-reg
    reg_masks = _kb_meta()["movem_reg_masks"]

    def _parse_reglist(s):
        """Parse register list string like 'd0-d2/a0' → bitmask."""
        s = s.strip().lower()
        regs = set()
        for part in s.split("/"):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-")
                start_name = start.strip()
                end_name = end.strip()
                # Find indices in normal order
                normal = reg_masks["normal"]
                si = normal.index(start_name)
                ei = normal.index(end_name)
                for i in range(si, ei + 1):
                    regs.add(normal[i])
            else:
                regs.add(part)
        return regs

    def _reglist_to_mask(regs, order):
        """Convert register set to 16-bit mask using given bit ordering."""
        mask = 0
        for i, name in enumerate(order):
            if name in regs:
                mask |= (1 << i)
        return mask

    # Detect direction by checking which operand is a register list
    src_is_reglist = bool(re.match(r'^[da]', src_str.strip(), re.I) and
                          not _RE_DN.match(src_str.strip()) and
                          not _RE_AN.match(src_str.strip()) and
                          not _RE_SP.match(src_str.strip()))
    # Also check for parenthesized EA patterns
    if src_str.strip().startswith("(") or src_str.strip().startswith("-"):
        src_is_reglist = False

    if src_is_reglist:
        # Register-to-memory: MOVEM reglist,<ea>
        regs = _parse_reglist(src_str)
        ea_mode, ea_reg, ea_ext = parse_ea(dst_str, sz_bytes)
        direction = 0  # reg-to-mem

        # Use predecrement order if destination is predecrement
        predec_mode = _ea_mode_encoding()["predec"][0]
        if ea_mode == predec_mode:
            mask = _reglist_to_mask(regs, reg_masks["predecrement"])
        else:
            mask = _reglist_to_mask(regs, reg_masks["normal"])
    else:
        # Memory-to-register: MOVEM <ea>,reglist
        regs = _parse_reglist(dst_str)
        ea_mode, ea_reg, ea_ext = parse_ea(src_str, sz_bytes)
        direction = 1  # mem-to-reg
        mask = _reglist_to_mask(regs, reg_masks["normal"])

    fields = {"dr": direction, "SIZE": size_enc,
              "MODE": ea_mode, "REGISTER": ea_reg}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word) + _to_bytes_16(mask) + ea_ext


def _assemble_link(inst, resolution, reg_str, imm_str):
    """Assemble LINK An,#displacement."""
    m = _RE_AN.match(reg_str.strip())
    if not m:
        if _RE_SP.match(reg_str.strip()):
            areg = 7
        else:
            raise ValueError(f"LINK register must be An, got {reg_str!r}")
    else:
        areg = int(m.group(1))

    disp = _parse_imm_value(imm_str.strip().lstrip("#"))
    fields = {"REGISTER": areg}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word) + _to_bytes_16(disp)


def _assemble_unlk(inst, resolution, reg_str):
    """Assemble UNLK An."""
    m = _RE_AN.match(reg_str.strip())
    if not m:
        raise ValueError(f"UNLK register must be An, got {reg_str!r}")
    areg = int(m.group(1))
    fields = {"REGISTER": areg}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word)


def _assemble_exg(inst, resolution, src_str, dst_str):
    """Assemble EXG — exchange registers.

    KB encoding uses named fields: REGISTER Rx (11:9), REGISTER Ry (3:0).
    KB opmode_table uses "description" (not "operation") for form descriptions.
    """
    ms = _RE_DN.match(src_str.strip())
    md = _RE_DN.match(dst_str.strip())
    mas = _RE_AN.match(src_str.strip()) or _RE_SP.match(src_str.strip())
    mad = _RE_AN.match(dst_str.strip()) or _RE_SP.match(dst_str.strip())

    opmode = None
    rx = ry = 0
    opm_table = inst.get("constraints", {}).get("opmode_table", [])

    if ms and md:
        # Dx,Dy
        rx = int(ms.group(1))
        ry = int(md.group(1))
        for entry in opm_table:
            desc = entry.get("description", "").lower()
            if "data" in desc and "address" not in desc:
                opmode = entry["opmode"]
                break
    elif mas and mad:
        # Ax,Ay
        rx = 7 if _RE_SP.match(src_str.strip()) else int(mas.group(1))
        ry = 7 if _RE_SP.match(dst_str.strip()) else int(mad.group(1))
        for entry in opm_table:
            desc = entry.get("description", "").lower()
            if "address" in desc and "data" not in desc:
                opmode = entry["opmode"]
                break
    elif ms and mad:
        # Dx,Ay
        rx = int(ms.group(1))
        ry = 7 if _RE_SP.match(dst_str.strip()) else int(mad.group(1))
        for entry in opm_table:
            desc = entry.get("description", "").lower()
            if "data" in desc and "address" in desc:
                opmode = entry["opmode"]
                break
    elif mas and md:
        # Ax,Dy — swap to canonical Dy,Ax
        rx = int(md.group(1))
        ry = 7 if _RE_SP.match(src_str.strip()) else int(mas.group(1))
        for entry in opm_table:
            desc = entry.get("description", "").lower()
            if "data" in desc and "address" in desc:
                opmode = entry["opmode"]
                break

    if opmode is None:
        raise ValueError(f"EXG: cannot determine opmode for {src_str},{dst_str}")

    fields = {"REGISTER": [rx, ry], "OPMODE": opmode}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word)


def _assemble_swap(inst, resolution, reg_str):
    """Assemble SWAP Dn."""
    m = _RE_DN.match(reg_str.strip())
    if not m:
        raise ValueError(f"SWAP register must be Dn, got {reg_str!r}")
    fields = {"REGISTER": int(m.group(1))}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word)


def _assemble_ext(inst, resolution, reg_str):
    """Assemble EXT/EXTB Dn.

    EXT has no SIZE field — size is encoded in OPMODE from KB opmode_table.
    User's size suffix is the result size (.w = byte→word, .l = word→long).
    """
    size_char = resolution["size"]
    user_mnemonic = resolution.get("mnemonic_str", "ext")
    m = _RE_DN.match(reg_str.strip())
    if not m:
        raise ValueError(f"EXT register must be Dn, got {reg_str!r}")

    opm_table = inst.get("constraints", {}).get("opmode_table", [])
    selected = None
    for entry in opm_table:
        desc = entry.get("description", "").lower()
        if size_char == "w" and "to word" in desc:
            selected = entry["opmode"]
            break
        if size_char == "l" and "to long" in desc:
            # For EXTB: "byte...to long"; for EXT: "word...to long"
            if user_mnemonic == "extb" and "byte" in desc:
                selected = entry["opmode"]
                break
            elif user_mnemonic == "ext" and "word" in desc:
                selected = entry["opmode"]
                break
    if selected is None:
        raise ValueError(f"EXT: no opmode for {user_mnemonic}.{size_char}")

    fields = {"REGISTER": int(m.group(1)), "OPMODE": selected}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word)


def _assemble_opword_immediate(inst, resolution, imm_str):
    """Assemble instructions where immediate goes into an opword field.

    Used for TRAP, BKPT, and any instruction whose immediate_range.field
    names an encoding field in the opword (e.g. VECTOR, DATA).
    """
    ir = inst.get("constraints", {}).get("immediate_range", {})
    field_name = ir.get("field")
    if not field_name:
        raise ValueError(f"{inst['mnemonic']}: no immediate_range.field in KB")
    imm_val = _parse_imm_value(imm_str.strip().lstrip("#"))
    ir_min = ir.get("min", 0)
    ir_max = ir.get("max", (1 << ir.get("bits", 16)) - 1)
    if not (ir_min <= imm_val <= ir_max):
        raise ValueError(
            f"{inst['mnemonic']}: immediate {imm_val} out of range "
            f"[{ir_min}..{ir_max}]")
    fields = {field_name: imm_val}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word)


def _assemble_lea_pea(inst, resolution, src_str, dst_str=None):
    """Assemble LEA <ea>,An or PEA <ea>."""
    sz_bytes = 4  # LEA/PEA always long

    src_mode, src_reg, src_ext = parse_ea(src_str, sz_bytes)

    fields = {"MODE": src_mode}

    # Find the EA register field name
    enc_fields = inst["encodings"][0]["fields"]
    reg_fields = [(f["name"], f["bit_hi"]) for f in enc_fields
                  if f["name"] not in ("0", "1") and "REGISTER" in f["name"].upper()]

    if dst_str is not None:
        # LEA: destination is An
        m = _RE_AN.match(dst_str.strip())
        if m:
            dst_areg = int(m.group(1))
        elif _RE_SP.match(dst_str.strip()):
            dst_areg = 7
        else:
            raise ValueError(f"LEA destination must be An, got {dst_str!r}")

        # LEA has two REGISTER fields: higher bits = An, lower bits = EA reg
        fields["REGISTER"] = [dst_areg, src_reg]
    else:
        # PEA: single EA operand
        fields["REGISTER"] = src_reg

    word = _build_opword(inst, fields)
    return _to_bytes_16(word) + src_ext


def _assemble_bcd(inst, resolution, src_str, dst_str):
    """Assemble ABCD/SBCD — data register or predecrement form.

    KB encoding has two named REGISTER fields (highest bits = dst, lowest = src).
    Base-name fallback in _build_opword handles varying suffixes (Rx/Ry, Dy/Dx).
    """
    ms = _RE_DN.match(src_str.strip())
    md = _RE_DN.match(dst_str.strip())

    if ms and md:
        # Dn,Dn: syntax is src,dst; encoding high bits = dst, low bits = src
        fields = {"REGISTER": [int(md.group(1)), int(ms.group(1))], "R/M": 0}
    else:
        # -(An),-(An)
        ms = _RE_PREDEC.match(src_str.strip())
        md = _RE_PREDEC.match(dst_str.strip())
        if not (ms and md):
            raise ValueError(f"ABCD/SBCD operands must be Dn,Dn or -(An),-(An)")
        fields = {"REGISTER": [int(md.group(1)), int(ms.group(1))], "R/M": 1}

    word = _build_opword(inst, fields)
    return _to_bytes_16(word)


def _assemble_addx_subx(inst, resolution, src_str, dst_str):
    """Assemble ADDX/SUBX — data register or predecrement form.

    KB encoding has two named REGISTER fields (highest bits = dst, lowest = src).
    Base-name fallback in _build_opword handles varying suffixes (Rx/Ry, Dy/Ax).
    """
    size_char = resolution["size"]
    size_enc = _get_size_encoding(inst, size_char)

    ms = _RE_DN.match(src_str.strip())
    md = _RE_DN.match(dst_str.strip())

    if ms and md:
        fields = {"REGISTER": [int(md.group(1)), int(ms.group(1))],
                  "SIZE": size_enc, "R/M": 0}
    else:
        ms = _RE_PREDEC.match(src_str.strip())
        md = _RE_PREDEC.match(dst_str.strip())
        if not (ms and md):
            raise ValueError(f"ADDX/SUBX operands must be Dn,Dn or -(An),-(An)")
        fields = {"REGISTER": [int(md.group(1)), int(ms.group(1))],
                  "SIZE": size_enc, "R/M": 1}

    word = _build_opword(inst, fields)
    return _to_bytes_16(word)


def _assemble_cmpm(inst, resolution, src_str, dst_str):
    """Assemble CMPM (Ay)+,(Ax)+.

    KB encoding uses named fields: REGISTER Ax (11:9) = dst, REGISTER Ay (2:0) = src.
    Syntax: CMPM (Ay)+,(Ax)+ — source is first operand, destination is second.
    """
    size_char = resolution["size"]
    size_enc = _get_size_encoding(inst, size_char)

    ms = _RE_POSTINC.match(src_str.strip())
    md = _RE_POSTINC.match(dst_str.strip())
    if not ms:
        ms = _RE_POSTINC_SP.match(src_str.strip())
        src_reg = 7
    else:
        src_reg = int(ms.group(1))
    if not md:
        md = _RE_POSTINC_SP.match(dst_str.strip())
        dst_reg = 7
    else:
        dst_reg = int(md.group(1))

    if not (ms and md):
        raise ValueError(f"CMPM operands must be (An)+,(An)+")

    fields = {"REGISTER": [dst_reg, src_reg], "SIZE": size_enc}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word)


def _assemble_movea(inst, resolution, src_str, dst_str):
    """Assemble MOVEA <ea>,An."""
    size_char = resolution["size"]
    sz_bytes = _size_byte_count().get(size_char, 2) if size_char else 2

    src_mode, src_reg, src_ext = parse_ea(src_str, sz_bytes)

    # MOVEA uses the MOVE encoding with destination mode=001 (An)
    m = _RE_AN.match(dst_str.strip())
    if m:
        dst_areg = int(m.group(1))
    elif _RE_SP.match(dst_str.strip()):
        dst_areg = 7
    else:
        raise ValueError(f"MOVEA destination must be An, got {dst_str!r}")

    # Get MOVE instruction from KB for encoding
    move_inst = _kb().get("MOVE")
    if move_inst is None:
        raise ValueError("MOVE instruction not found in KB")

    an_mode = _ea_mode_encoding()["an"][0]  # mode 1

    size_enc = _get_size_encoding(move_inst, size_char)

    fields = {
        "MODE": [an_mode, src_mode],
        "REGISTER": [dst_areg, src_reg],
    }
    if size_enc is not None:
        fields["SIZE"] = size_enc

    word = _build_opword(move_inst, fields)
    return _to_bytes_16(word) + src_ext


def _assemble_bit_reg(inst, resolution, src_str, dst_str):
    """Assemble BTST/BCHG/BCLR/BSET Dn,<ea> — dynamic (register) form.

    Uses encoding[0]: REGISTER(11:9)=Dn, MODE(5:3), REGISTER(2:0)=EA.
    """
    ms = _RE_DN.match(src_str.strip())
    if not ms:
        raise ValueError(f"{inst['mnemonic']}: source must be Dn, got {src_str!r}")
    src_reg = int(ms.group(1))

    dst_mode, dst_reg, dst_ext = parse_ea(dst_str)
    fields = {"REGISTER": [src_reg, dst_reg], "MODE": dst_mode}
    word = _build_opword(inst, fields, enc_idx=0)
    return _to_bytes_16(word) + dst_ext


def _assemble_bit_imm(inst, resolution, src_str, dst_str):
    """Assemble BTST/BCHG/BCLR/BSET #n,<ea> — static (immediate) form.

    Uses encoding[1] for the opword (fixed bits 15:8 + MODE/REGISTER for EA)
    and a 16-bit extension word containing the bit number.
    """
    bit_num = _parse_imm_value(src_str.strip().lstrip("#"))
    dst_mode, dst_reg, dst_ext = parse_ea(dst_str)

    fields = {"MODE": dst_mode, "REGISTER": dst_reg}
    word = _build_opword(inst, fields, enc_idx=1)
    return _to_bytes_16(word) + _to_bytes_16(bit_num) + dst_ext


def _assemble_adda_suba_cmpa(inst, resolution, src_str, dst_str):
    """Assemble ADDA/SUBA/CMPA <ea>,An.

    These instructions have their own KB entry with encoding and opmode_table.
    The opmode_table uses "description" (not "operation") for entries.
    """
    size_char = resolution["size"]
    sz_bytes = _size_byte_count().get(size_char, 2) if size_char else 2

    src_mode, src_reg, src_ext = parse_ea(src_str, sz_bytes)

    m = _RE_AN.match(dst_str.strip())
    if m:
        dst_areg = int(m.group(1))
    elif _RE_SP.match(dst_str.strip()):
        dst_areg = 7
    else:
        raise ValueError(f"{inst['mnemonic']} destination must be An, got {dst_str!r}")

    # Use the instruction's own opmode_table
    opm_table = inst.get("constraints", {}).get("opmode_table", [])
    selected_opmode = None
    for entry in opm_table:
        if entry["size"] == size_char:
            selected_opmode = entry["opmode"]
            break

    if selected_opmode is None:
        raise ValueError(f"{inst['mnemonic']}.{size_char}: no opmode")

    fields = {"REGISTER": [dst_areg, src_reg],
              "OPMODE": selected_opmode, "MODE": src_mode}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word) + src_ext


# ── KB-driven operand type classification ────────────────────────────────

@lru_cache(maxsize=1)
def _special_operand_types():
    """Derive special register operand types from KB asm_syntax_index.

    Returns the set of operand types that appear in the syntax index but are
    not standard EA modes. These require special resolution because they map
    to separate KB instructions (e.g. 'ccr' in 'andi:imm,ccr' → 'ANDI to CCR').
    """
    ea_modes = set(_ea_mode_encoding().keys())  # dn, an, ind, postinc, etc.
    # Types that are parameters, not named registers
    generic_types = ea_modes | {"ea", "imm", "label", "reglist", "ctrl_reg",
                                "rn", "bf_ea", "unknown", "dn_pair",
                                "disp", "postinc", "predec"}
    all_types = set()
    for key in _kb_meta()["asm_syntax_index"]:
        parts = key.split(":", 1)
        if len(parts) > 1 and parts[1]:
            for t in parts[1].split(","):
                all_types.add(t)
    return all_types - generic_types


@lru_cache(maxsize=1)
def _asm_syntax_index():
    """Return {(asm_mnemonic, op_type_tuple): kb_mnemonic} from KB _meta."""
    raw = _kb_meta()["asm_syntax_index"]
    result = {}
    for key, kb_mnemonic in raw.items():
        parts = key.split(":", 1)
        asm_mn = parts[0]
        op_types = tuple(parts[1].split(",")) if len(parts) > 1 and parts[1] else ()
        result[(asm_mn, op_types)] = kb_mnemonic
    return result


def _classify_asm_operand(text):
    """Classify an assembly operand text into a KB operand type string.

    Returns one of: 'imm', 'dn', 'an', 'sr', 'ccr', 'usp', 'ea', etc.
    Uses the same type categories as the KB forms parser (_parse_operand in
    parse_m68k.py) so that lookups into asm_syntax_index match.
    """
    t = text.strip().lower()
    if t.startswith("#"):
        return "imm"
    if t == "sr":
        return "sr"
    if t == "ccr":
        return "ccr"
    if t == "usp":
        return "usp"
    if _RE_AN.match(t) or _RE_SP.match(t):
        return "an"
    if _RE_DN.match(t):
        return "dn"
    # Default: 'ea' covers all other addressing modes
    return "ea"


def _resolve_by_syntax_index(mnemonic_lower, operands):
    """Resolve (mnemonic, operand types) to KB instruction via asm_syntax_index.

    Tries exact operand type match first, then promotes specific register types
    (dn, an) to 'ea' since the KB forms use 'ea' for operands that accept any
    effective addressing mode.

    Returns (kb_inst, matched_form_index) or None.
    """
    op_types = tuple(_classify_asm_operand(op) for op in operands)
    index = _asm_syntax_index()

    # Try exact match first
    key = (mnemonic_lower, op_types)
    kb_mnemonic = index.get(key)

    # If no exact match, try promoting dn/an to ea (they're EA subsets)
    if kb_mnemonic is None:
        ea_promotable = {"dn", "an"}
        promoted = tuple("ea" if t in ea_promotable else t for t in op_types)
        if promoted != op_types:
            key = (mnemonic_lower, promoted)
            kb_mnemonic = index.get(key)

    if kb_mnemonic is None:
        return None
    inst = _kb().get(kb_mnemonic)
    if inst is None:
        raise ValueError(
            f"asm_syntax_index maps {key} to {kb_mnemonic!r} "
            f"but that instruction is not in the KB")
    # Find matching form index by operand types (try exact then promoted)
    for form_idx, form in enumerate(inst.get("forms", [])):
        form_ops = tuple(o["type"] for o in form.get("operands", []))
        if form_ops == op_types or form_ops == key[1]:
            return inst, form_idx
    return inst, 0


# ── SR/CCR/USP instruction handlers ──────────────────────────────────────

def _inst_size_bytes(inst):
    """Get operand size in bytes from the instruction's KB sizes field."""
    sizes = inst.get("sizes", [])
    if not sizes:
        raise ValueError(f"{inst['mnemonic']}: no sizes in KB")
    sbc = _size_byte_count()
    return sbc[sizes[0]]


def _assemble_imm_to_sr_ccr(inst, imm_str):
    """Assemble ANDI/EORI/ORI to CCR/SR — all-fixed opword + immediate extension.

    Extension word size derived from KB sizes field via size_byte_count.
    """
    sz_bytes = _inst_size_bytes(inst)
    imm_val = _parse_imm_value(imm_str.strip().lstrip("#"))
    word = _build_opword(inst, {})
    if sz_bytes >= 4:
        imm_bytes = _to_bytes_32(imm_val)
    else:
        imm_bytes = _to_bytes_16(imm_val)
    return _to_bytes_16(word) + imm_bytes


def _assemble_ea_to_sr_ccr(inst, src_str):
    """Assemble MOVE <ea>,CCR or MOVE <ea>,SR — source EA in encoding.

    Operand size derived from KB sizes field.
    """
    sz_bytes = _inst_size_bytes(inst)
    mode, reg, ext = parse_ea(src_str, sz_bytes)
    fields = {"MODE": mode, "REGISTER": reg}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word) + ext


def _assemble_sr_ccr_to_ea(inst, dst_str):
    """Assemble MOVE SR,<ea> or MOVE CCR,<ea> — destination EA in encoding.

    Operand size derived from KB sizes field.
    """
    sz_bytes = _inst_size_bytes(inst)
    mode, reg, ext = parse_ea(dst_str, sz_bytes)
    fields = {"MODE": mode, "REGISTER": reg}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word) + ext


def _assemble_direction_field(inst, form_idx, operands):
    """Assemble instruction with direction field (MOVE USP, MOVEM, MOVEC).

    Uses KB direction_field_values to determine the dr bit value from form index.
    """
    dfv = inst.get("direction_field_values")
    if dfv is None:
        raise ValueError(
            f"{inst['mnemonic']}: no direction_field_values in KB")

    field_name = dfv["field"]
    # JSON serializes int keys as strings
    dr_value = dfv["form_field_value"].get(str(form_idx))
    if dr_value is None:
        raise ValueError(
            f"{inst['mnemonic']}: form index {form_idx} not in "
            f"direction_field_values.form_field_value")

    # Determine which operand is the An register
    forms = inst.get("forms", [])
    form_ops = [o["type"] for o in forms[form_idx].get("operands", [])]

    # Find the non-special operand (the An register)
    an_str = None
    for i, op_type in enumerate(form_ops):
        if op_type == "an":
            an_str = operands[i]
            break
    if an_str is None:
        raise ValueError(
            f"{inst['mnemonic']}: no 'an' operand in form {form_idx}")

    m = _RE_AN.match(an_str.strip())
    if m:
        an_reg = int(m.group(1))
    elif _RE_SP.match(an_str.strip()):
        an_reg = 7
    else:
        raise ValueError(
            f"{inst['mnemonic']}: operand must be An, got {an_str!r}")

    fields = {field_name: dr_value, "REGISTER": an_reg}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word)


# ── Main assembler entry point ───────────────────────────────────────────

def _split_operands(operand_str):
    """Split operand string on comma, respecting parentheses."""
    depth = 0
    parts = []
    current = []
    for ch in operand_str:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current).strip())
    return parts


def assemble_instruction(text, pc=0):
    """Assemble a single M68K instruction into bytes.

    Args:
        text: Assembly text like "move.l d0,(a1)"
        pc: Current program counter (for PC-relative addressing)

    Returns:
        bytes object with the assembled instruction (big-endian).
    """
    text = text.strip()
    if not text:
        raise ValueError("Empty instruction")

    # Split mnemonic from operands
    parts = text.split(None, 1)
    mnemonic_part = parts[0]
    operand_part = parts[1] if len(parts) > 1 else ""

    mnemonic_str, size_char = _parse_mnemonic_size(mnemonic_part)
    resolution = resolve_instruction(mnemonic_str, size_char)
    inst = resolution["inst"]
    mnemonic = inst["mnemonic"]

    operands = _split_operands(operand_part) if operand_part else []

    # Check for special operands (SR/CCR/USP) — resolve via KB asm_syntax_index
    if operands:
        op_types = tuple(_classify_asm_operand(op) for op in operands)
        if any(t in _special_operand_types() for t in op_types):
            resolved = _resolve_by_syntax_index(mnemonic_str.lower(), operands)
            if resolved is None:
                raise ValueError(
                    f"No KB instruction for {mnemonic_str} with operand types {op_types}")
            sr_inst, form_idx = resolved
            form_ops = tuple(
                o["type"] for o in sr_inst["forms"][form_idx].get("operands", []))

            # Route by form operand pattern
            if form_ops in (("imm", "ccr"), ("imm", "sr")):
                return _assemble_imm_to_sr_ccr(sr_inst, operands[0])
            elif form_ops in (("ea", "ccr"), ("ea", "sr")):
                return _assemble_ea_to_sr_ccr(sr_inst, operands[0])
            elif form_ops in (("sr", "ea"), ("ccr", "ea")):
                return _assemble_sr_ccr_to_ea(sr_inst, operands[1])
            elif form_ops in (("usp", "an"), ("an", "usp")):
                return _assemble_direction_field(sr_inst, form_idx, operands)
            else:
                raise ValueError(
                    f"Unhandled special operand form: {form_ops} "
                    f"for {sr_inst['mnemonic']}")

    # Route to specific assembler based on instruction characteristics
    forms = inst.get("forms", [])
    op_types = [tuple(o["type"] for o in f.get("operands", [])) for f in forms]

    # No operands
    if not operands:
        return _assemble_no_operands(inst, resolution)

    # Special instruction routing by mnemonic
    if mnemonic == "MOVEQ":
        return _assemble_moveq(inst, resolution, operands[0], operands[1])

    if mnemonic == "MOVEA":
        return _assemble_movea(inst, resolution, operands[0], operands[1])

    if mnemonic in ("ADDA", "SUBA", "CMPA"):
        return _assemble_adda_suba_cmpa(inst, resolution, operands[0], operands[1])

    if mnemonic == "MOVEM":
        return _assemble_movem(inst, resolution, operands)

    if mnemonic == "MOVEP":
        return _assemble_movep(inst, resolution, operands[0], operands[1])

    if mnemonic == "LINK":
        return _assemble_link(inst, resolution, operands[0], operands[1])

    if mnemonic == "UNLK":
        return _assemble_unlk(inst, resolution, operands[0])

    if mnemonic == "EXG":
        return _assemble_exg(inst, resolution, operands[0], operands[1])

    if mnemonic == "SWAP":
        return _assemble_swap(inst, resolution, operands[0])

    if mnemonic in ("EXT", "EXT, EXTB"):
        return _assemble_ext(inst, resolution, operands[0])

    # Instructions with immediate embedded in opword field (TRAP, BKPT, etc.)
    # Detected by: single #imm operand, immediate_range.field names an opword field
    if len(operands) == 1 and operands[0].strip().startswith("#"):
        ir = inst.get("constraints", {}).get("immediate_range", {})
        ir_field = ir.get("field", "")
        enc_fields = {f["name"] for f in inst["encodings"][0]["fields"]}
        if ir_field and ir_field in enc_fields:
            return _assemble_opword_immediate(inst, resolution, operands[0])

    if mnemonic in ("ABCD", "SBCD"):
        return _assemble_bcd(inst, resolution, operands[0], operands[1])

    if mnemonic in ("ADDX", "SUBX"):
        return _assemble_addx_subx(inst, resolution, operands[0], operands[1])

    if mnemonic == "CMPM":
        return _assemble_cmpm(inst, resolution, operands[0], operands[1])

    # Bit operations: BTST/BCHG/BCLR/BSET — two forms (register and immediate)
    if mnemonic in ("BTST", "BCHG", "BCLR", "BSET") and len(operands) == 2:
        if operands[0].strip().startswith("#"):
            return _assemble_bit_imm(inst, resolution, operands[0], operands[1])
        else:
            return _assemble_bit_reg(inst, resolution, operands[0], operands[1])

    # Branch instructions
    if inst.get("uses_label"):
        if len(operands) == 2 and _RE_DN.match(operands[0].strip()):
            return _assemble_dbcc(inst, resolution, operands[0], operands[1], pc)
        return _assemble_branch(inst, resolution, operands[0], pc)

    # Shift/rotate: register form (2 operands) or memory form (1 operand)
    if resolution["direction"] is not None:
        if len(operands) == 2:
            return _assemble_shift_reg(inst, resolution, operands)
        if len(operands) == 1:
            return _assemble_shift_mem(inst, resolution, operands[0])

    # LEA <ea>,An
    if mnemonic == "LEA":
        return _assemble_lea_pea(inst, resolution, operands[0], operands[1])

    # PEA <ea>
    if mnemonic == "PEA":
        return _assemble_lea_pea(inst, resolution, operands[0])

    # Two-operand MOVE-style (dual EA) — BEFORE opmode/immediate checks
    # so that MOVE #imm,<ea> uses the dual-EA path, not the immediate path
    if len(operands) == 2:
        enc = inst["encodings"][0]
        mode_count = sum(1 for f in enc["fields"] if f["name"] == "MODE")
        if mode_count >= 2:
            return _assemble_two_ea(inst, resolution, operands[0], operands[1])

    # Immediate routing: ADD #imm,<ea> → ADDI #imm,<ea> (canonical encoding)
    # Driven by KB _meta.immediate_routing, which maps general-purpose
    # mnemonics to their immediate-specific variants.
    if (len(operands) == 2 and operands[0].strip().startswith("#")
            and inst.get("constraints", {}).get("opmode_table")):
        imm_routing = _kb_meta().get("immediate_routing", {})
        imm_mnemonic = imm_routing.get(mnemonic)
        if imm_mnemonic and imm_mnemonic in _kb():
            imm_inst = _kb()[imm_mnemonic]
            imm_resolution = {**resolution, "inst": imm_inst}
            return _assemble_immediate(imm_inst, imm_resolution,
                                       operands[0], operands[1])

    # Instructions with opmode table (ADD, SUB, AND, OR, CMP)
    if inst.get("constraints", {}).get("opmode_table") and len(operands) == 2:
        return _assemble_opmode(inst, resolution, operands[0], operands[1])

    # Generic <ea>,Dn form (CHK, DIVS, DIVU, MULS, MULU, etc.)
    # Detected by: 2 operands, 1 MODE field, 2+ REGISTER fields, no opmode table
    if len(operands) == 2 and not inst.get("constraints", {}).get("opmode_table"):
        enc = inst["encodings"][0]
        mode_count = sum(1 for f in enc["fields"] if f["name"] == "MODE")
        reg_count = sum(1 for f in enc["fields"]
                        if f["name"] not in ("0", "1") and "REGISTER" in f["name"].upper())
        if mode_count == 1 and reg_count >= 2:
            # Determine direction: if dst is Dn, it's <ea>,Dn
            if _RE_DN.match(operands[1].strip()):
                return _assemble_ea_dn(inst, resolution, operands[0], operands[1])

    # Immediate instructions (#imm,<ea>)
    if len(operands) == 2 and operands[0].strip().startswith("#"):
        # Check if this is ADDQ/SUBQ (quick immediate)
        ir = inst.get("constraints", {}).get("immediate_range", {})
        if ir.get("field") == "DATA":
            return _assemble_quick(inst, resolution, operands[0], operands[1])
        return _assemble_immediate(inst, resolution, operands[0], operands[1])

    # Single EA operand
    if len(operands) == 1:
        return _assemble_ea_single(inst, resolution, operands[0])

    raise ValueError(f"Cannot assemble: {text!r}")


# ── CLI ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    import argparse
    ap = argparse.ArgumentParser(description="M68K assembler")
    ap.add_argument("instruction", nargs="+", help="Instruction text")
    ap.add_argument("--pc", type=lambda x: int(x, 0), default=0,
                    help="PC value (default 0)")
    cli_args = ap.parse_args()

    text = " ".join(cli_args.instruction)
    try:
        result = assemble_instruction(text, pc=cli_args.pc)
        print(f"  {text}")
        print(f"  -> {result.hex()}")
        print(f"  -> {' '.join(f'{b:02x}' for b in result)}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
