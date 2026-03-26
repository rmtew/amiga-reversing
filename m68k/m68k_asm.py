"""KB-driven M68K assembler - assembly text -> machine code bytes.

All M68K knowledge comes from the runtime KB and its canonical source data.
No instruction encodings, sizes, or field values are hardcoded.

Usage:
    from m68k_asm import assemble_instruction
    code = assemble_instruction("move.l d0,(a1)")
"""

import re
import struct
from collections.abc import Mapping
from typing import Literal, TypedDict, cast

from m68k_kb import runtime_m68k_asm, runtime_m68k_decode
from m68k_kb.runtime_types import AsmCcParam, AsmOpmodeEntry, DirectionVariant

_SIZE_BYTE = 0
_SIZE_WORD = 1
_SIZE_LONG = 2

type SizeChar = Literal["b", "w", "l", "s"]
type ParsedEa = tuple[int, int, bytes]
type FieldValue = int | list[int]
type FieldValues = dict[str, FieldValue]
type OperandClass = Literal["imm", "dn", "an", "sr", "ccr", "usp", "ea"]
type Operands = list[str]
type ResolvedSyntax = tuple[str, int]
type EaModeEncoding = dict[str, tuple[int, int]]


__all__ = ["assemble_instruction", "parse_ea", "runtime_m68k_asm"]


class Resolution(TypedDict):
    mnemonic: str
    cc_index: int | None
    direction: int | None
    direction_mnemonic: str | None
    size: SizeChar | None
    mnemonic_str: str


# -- EA mode encoding from KB ---------------------------------------------

# -- Bit field helpers -----------------------------------------------------

def _pack_field(word: int, value: int, bit_hi: int, bit_lo: int) -> int:
    """Set bits [bit_hi:bit_lo] of word to value."""
    width = bit_hi - bit_lo + 1
    mask = (1 << width) - 1
    return word | ((value & mask) << bit_lo)


def _to_bytes_16(val: int) -> bytes:
    """Pack a 16-bit value as big-endian bytes."""
    return struct.pack(">H", val & 0xFFFF)


def _to_bytes_32(val: int) -> bytes:
    """Pack a 32-bit value as big-endian bytes."""
    return struct.pack(">I", val & 0xFFFFFFFF)


# -- EA mode parser (the shared core) -------------------------------------

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
_RE_FULL_INDEX = re.compile(r'^([da])([0-7])\.(w|l)(?:\*(1|2|4|8))?$', re.I)


def _parse_imm_value(s: str) -> int:
    """Parse an immediate value string (hex $NN or decimal)."""
    s = s.strip()
    if s.startswith(("$", "0x")):
        return int(s.replace("$", ""), 16)
    return int(s)


def _split_top_level(text: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for ch in text:
        if ch == ',' and depth == 0:
            parts.append("".join(current).strip())
            current = []
            continue
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth < 0:
                raise ValueError(f"Unbalanced brackets in EA operand: {text!r}")
        current.append(ch)
    if depth != 0:
        raise ValueError(f"Unbalanced brackets in EA operand: {text!r}")
    parts.append("".join(current).strip())
    return parts


def _parse_num(text: str) -> int:
    text = text.strip()
    if not text:
        raise ValueError("Expected numeric value")
    return _parse_imm_value(text)


def _parse_full_index(text: str) -> tuple[bool, int, bool, int]:
    match = _RE_FULL_INDEX.match(text.strip())
    if match is None:
        raise ValueError(f"Invalid full-extension index operand: {text!r}")
    reg_kind = match.group(1).lower()
    reg_num = int(match.group(2))
    is_long = match.group(3).lower() == "l"
    scale = 1 if match.group(4) is None else int(match.group(4))
    return reg_kind == "a", reg_num, is_long, scale


def _build_full_ext_word(*, index_is_addr: bool, index_reg: int, index_is_long: bool, index_scale: int,
                         base_suppressed: bool, index_suppressed: bool, base_disp_kind: str, iis: int) -> int:
    fields = runtime_m68k_decode.EA_FULL_FIELDS
    bd_value = {name: int(key) for key, name in runtime_m68k_decode.EA_FULL_BD_SIZE.items()}
    scale_value = {1: 0, 2: 1, 4: 2, 8: 3}
    if base_disp_kind not in bd_value:
        raise ValueError(f"Unsupported base displacement kind {base_disp_kind!r}")
    if index_scale not in scale_value:
        raise ValueError(f"Unsupported index scale {index_scale}")

    word = 0x0100
    if index_suppressed:
        index_is_addr = False
        index_reg = 0
        index_is_long = False
        index_scale = 1
    word = _pack_field(word, 1 if index_is_addr else 0, *fields["D/A"][:2])
    word = _pack_field(word, index_reg, *fields["REGISTER"][:2])
    word = _pack_field(word, 1 if index_is_long else 0, *fields["W/L"][:2])
    word = _pack_field(word, scale_value[index_scale], *fields["SCALE"][:2])
    word = _pack_field(word, 1 if base_suppressed else 0, *fields["BS"][:2])
    word = _pack_field(word, 1 if index_suppressed else 0, *fields["IS"][:2])
    word = _pack_field(word, bd_value[base_disp_kind], *fields["BD SIZE"][:2])
    return _pack_field(word, iis, *fields["I/IS"][:2])


def _full_ext_disp_kind(value: int | None) -> str:
    if value is None:
        return "null"
    if -0x8000 <= value <= 0x7FFF:
        return "word"
    return "long"


def _full_ext_disp_bytes(value: int | None) -> bytes:
    if value is None:
        return b""
    if -0x8000 <= value <= 0x7FFF:
        return _to_bytes_16(value)
    return struct.pack(">i", value)


def _parse_full_extension_ea(operand: str, enc: dict[str, tuple[int, int]]) -> ParsedEa | None:
    if not (operand.startswith("(") and operand.endswith(")")):
        return None
    if "[" not in operand or "]" not in operand:
        return None
    inner = operand[1:-1]
    parts = _split_top_level(inner)
    if not parts:
        raise ValueError(f"Invalid full-extension EA operand: {operand!r}")
    leading_outer_disp = None
    if parts[0].startswith("[") and parts[0].endswith("]"):
        bracket_text = parts[0][1:-1]
        outer_parts = parts[1:]
    elif (
        len(parts) == 2
        and parts[1].startswith("[")
        and parts[1].endswith("]")
    ):
        leading_outer_disp = _parse_num(parts[0])
        bracket_text = parts[1][1:-1]
        outer_parts = []
    else:
        raise ValueError(f"Invalid full-extension EA operand: {operand!r}")

    bracket_parts = _split_top_level(bracket_text)
    if not bracket_parts:
        raise ValueError(f"Invalid full-extension EA operand: {operand!r}")

    base_disp = None
    base_register = None
    index_is_addr = False
    index_reg = 0
    index_is_long = False
    index_scale = 1
    bracket_index = None

    for item in bracket_parts:
        low = item.lower()
        if low == "pc":
            if base_register is not None:
                raise ValueError(f"Duplicate base register in EA operand: {operand!r}")
            base_register = "pc"
            continue
        if _RE_AN.match(low) or _RE_SP.match(low):
            if base_register is not None:
                raise ValueError(f"Duplicate base register in EA operand: {operand!r}")
            base_register = "sp" if low == "sp" else low
            continue
        if _RE_FULL_INDEX.match(item):
            if bracket_index is not None:
                raise ValueError(f"Duplicate index register in EA operand: {operand!r}")
            bracket_index = item
            continue
        if base_disp is not None:
            raise ValueError(f"Duplicate base displacement in EA operand: {operand!r}")
        base_disp = _parse_num(item)

    outer_disp = leading_outer_disp
    trailing_index = None
    for item in outer_parts:
        if _RE_FULL_INDEX.match(item):
            if trailing_index is not None:
                raise ValueError(f"Duplicate trailing index in EA operand: {operand!r}")
            trailing_index = item
            continue
        if outer_disp is not None:
            raise ValueError(f"Duplicate outer displacement in EA operand: {operand!r}")
        outer_disp = _parse_num(item)

    preindexed = bracket_index is not None
    postindexed = trailing_index is not None
    if preindexed and postindexed:
        raise ValueError(f"EA operand cannot be both preindexed and postindexed: {operand!r}")

    index_text = bracket_index if preindexed else trailing_index
    if index_text is not None:
        index_is_addr, index_reg, index_is_long, index_scale = _parse_full_index(index_text)
        index_suppressed = False
    else:
        index_suppressed = True

    if base_register is None:
        raise ValueError(f"Full-extension EA missing base register: {operand!r}")

    outer_kind = "null" if outer_disp is None else _full_ext_disp_kind(outer_disp)
    if preindexed:
        iis = {"null": 1, "word": 2, "long": 3}[outer_kind]
    else:
        iis = {"null": 5, "word": 6, "long": 7}[outer_kind]

    base_disp_kind = _full_ext_disp_kind(base_disp)
    ext_word = _build_full_ext_word(
        index_is_addr=index_is_addr,
        index_reg=index_reg,
        index_is_long=index_is_long,
        index_scale=index_scale,
        base_suppressed=False,
        index_suppressed=index_suppressed,
        base_disp_kind=base_disp_kind,
        iis=iis,
    )
    ext = _to_bytes_16(ext_word) + _full_ext_disp_bytes(base_disp) + _full_ext_disp_bytes(outer_disp)

    if base_register == "pc":
        mode, reg = enc["pcindex"]
        return mode, reg, ext
    mode, _ = enc["index"]
    reg = 7 if base_register == "sp" else int(base_register[1])
    return mode, reg, ext


def _build_brief_ext_word(xreg_num: int, is_addr: bool, is_long: bool, disp8: int) -> int:
    """Build brief extension word from KB field layout."""
    bf = runtime_m68k_asm.EA_BRIEF_FIELDS
    word = 0
    word = _pack_field(word, 1 if is_addr else 0, *bf["D/A"][:2])
    word = _pack_field(word, xreg_num, *bf["REGISTER"][:2])
    word = _pack_field(word, 1 if is_long else 0, *bf["W/L"][:2])
    # SCALE = 0 (x1) for 68000 basic indexed mode
    return _pack_field(word, disp8 & 0xFF, *bf["DISPLACEMENT"][:2])


def parse_ea(operand: str, op_size: int | None = None) -> ParsedEa:
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
    enc = cast(EaModeEncoding, runtime_m68k_asm.EA_MODE_ENCODING)

    full_ext = _parse_full_extension_ea(operand, enc)
    if full_ext is not None:
        return full_ext

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

    # d(An,Xn.s) - indexed (must check before disp because of overlapping patterns)
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

    # d(An) / d(SP) - displacement
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

    # (An) / (SP) - indirect (check after postinc/predec/disp/index)
    m = _RE_IND.match(operand)
    if m:
        mode, _ = enc["ind"]
        return mode, int(m.group(1)), b""
    if _RE_IND_SP.match(operand):
        mode, _ = enc["ind"]
        return mode, 7, b""

    # d(PC,Xn.s) - PC indexed
    m = _RE_PCINDEX.match(operand)
    if m:
        disp = int(m.group(1))
        xtype = m.group(2).lower()
        xreg = int(m.group(3))
        xsize = m.group(4).lower()
        mode, reg = enc["pcindex"]
        ext_word = _build_brief_ext_word(xreg, xtype == "a", xsize == "l", disp)
        return mode, reg, _to_bytes_16(ext_word)

    # d(PC) - PC displacement
    m = _RE_PCDISP.match(operand)
    if m:
        disp = int(m.group(1))
        mode, reg = enc["pcdisp"]
        return mode, reg, _to_bytes_16(disp)

    # #imm - immediate
    m = _RE_IMM.match(operand)
    if m:
        val = _parse_imm_value(m.group(1))
        mode, reg = enc["imm"]
        if op_size is not None and op_size >= 4:
            return mode, reg, _to_bytes_32(val)
        return mode, reg, _to_bytes_16(val)

    # ($xxxx).w - absolute word
    m = _RE_ABSW.match(operand)
    if m:
        addr = int(m.group(1), 16)
        mode, reg = enc["absw"]
        return mode, reg, _to_bytes_16(addr)

    # $xxxx - absolute long (hex)
    m = _RE_ABSL_HEX.match(operand)
    if m:
        addr = int(m.group(1), 16)
        mode, reg = enc["absl"]
        return mode, reg, _to_bytes_32(addr)

    # decimal number - absolute long
    m = _RE_ABSL_DEC.match(operand)
    if m:
        addr = int(m.group(1))
        mode, reg = enc["absl"]
        return mode, reg, _to_bytes_32(addr)

    raise ValueError(f"Cannot parse EA operand: {operand!r}")


# -- KB encoding helpers ---------------------------------------------------


# -- Mnemonic resolution --------------------------------------------------

def _parse_mnemonic_size(text: str) -> tuple[str, SizeChar | None]:
    """Parse 'move.l' -> ('move', 'l') or 'nop' -> ('nop', None)."""
    text = text.strip().lower()
    # Try splitting on last dot
    if "." in text:
        parts = text.rsplit(".", 1)
        if parts[1] in ("b", "w", "l", "s"):
            return parts[0], cast(SizeChar, parts[1])
    return text, None


def _resolve_cc_mnemonic(mnemonic_lower: str) -> tuple[str, int] | None:
    """Check if mnemonic is a cc-parameterized variant (e.g. 'beq' -> Bcc, cc=1).

    Also handles CC aliases from KB _meta.cc_aliases (e.g. 'dbra' -> DBcc with
    cc=F, 'blo' -> Bcc with cc=CS).

    Returns (kb_inst, cc_index) or None.
    """
    families = cast(dict[str, tuple[str, AsmCcParam]], runtime_m68k_asm.CC_FAMILIES)
    condition_codes = cast(tuple[str, ...], runtime_m68k_asm.CONDITION_CODES)
    cc_idx = {name: i for i, name in enumerate(condition_codes)}
    cc_aliases = runtime_m68k_asm.CC_ALIASES

    for prefix, (kb_mnemonic, cc_param) in families.items():
        if mnemonic_lower.startswith(prefix) and len(mnemonic_lower) > len(prefix):
            cc_suffix = mnemonic_lower[len(prefix):]
            # Direct CC match
            if cc_suffix in cc_idx:
                excluded = set(cc_param.get("excluded", []))
                if cc_suffix not in excluded:
                    return kb_mnemonic, cc_idx[cc_suffix]
            # Alias CC match (e.g. "ra" -> "f", "lo" -> "cs")
            canonical = cc_aliases.get(cc_suffix)
            if canonical and canonical in cc_idx:
                excluded = set(cc_param.get("excluded", []))
                if canonical not in excluded:
                    return kb_mnemonic, cc_idx[canonical]
    return None


def _resolve_direction_mnemonic(mnemonic_lower: str) -> tuple[str, int, str] | None:
    """Check if mnemonic is a direction variant (e.g. 'asl' -> 'ASL, ASR', direction=L).

    Returns (kb_inst, direction_bit_value, individual_mnemonic) or None.
    """
    direction_variants = cast(dict[str, DirectionVariant], runtime_m68k_asm.DIRECTION_VARIANTS)
    for mnemonic, dv in direction_variants.items():
        _, base, variant_names, values = dv
        variants = [variant.lower() for variant in variant_names]
        if mnemonic_lower not in variants:
            continue
        suffix = mnemonic_lower[len(base):]
        for bit_val, dir_char in values.items():
            if dir_char == suffix:
                return mnemonic, int(bit_val), mnemonic_lower
    return None


def resolve_instruction(mnemonic_str: str, size_char: SizeChar | None = None) -> Resolution:
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
    kb_mnemonic = runtime_m68k_asm.LOOKUP_UPPER.get(mnemonic_lower.upper())
    if kb_mnemonic is not None:
        direction_variants = cast(dict[str, DirectionVariant], runtime_m68k_asm.DIRECTION_VARIANTS)
        cc_families = cast(dict[str, tuple[str, AsmCcParam]], runtime_m68k_asm.CC_FAMILIES)
        if (kb_mnemonic not in direction_variants
                and kb_mnemonic not in {family[0] for family in cc_families.values()}):
            return {
                "mnemonic": kb_mnemonic,
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
            "mnemonic": cc_result[0],
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
            "mnemonic": dir_result[0],
            "cc_index": None,
            "direction": dir_result[1],
            "direction_mnemonic": dir_result[2],
            "size": size_char,
            "mnemonic_str": mnemonic_lower,
        }

    raise ValueError(f"Unknown mnemonic: {mnemonic_str!r}")


# -- Opword construction --------------------------------------------------

def _build_opword(inst: str, field_values: Mapping[str, FieldValue], enc_idx: int = 0) -> int:
    """Build opword from KB encoding fixed bits + variable field values.

    Args:
        inst: KB instruction dict
        field_values: dict mapping field name to value.
            For duplicate fields (e.g. MOVE has two MODE), use
            field_values with list values - first element is highest bit position.
            For named fields (e.g. "REGISTER Rx"), use exact names.
        enc_idx: which encoding to use (default 0, the primary encoding).

    Returns:
        16-bit opword integer.
    """
    word = 0
    fields = runtime_m68k_asm.RAW_FIELDS[enc_idx][inst]

    # Set fixed bits
    mask, value = runtime_m68k_asm.ENCODING_MASKS[enc_idx][inst]
    word |= value & mask

    # Set variable fields
    # Support two styles:
    #   1. Exact named fields: {"REGISTER Rx": 3, "REGISTER Ry": 5}
    #   2. List-based duplicates: {"REGISTER": [3, 5]} (indexed by occurrence order)
    field_counts: dict[str, int] = {}
    for name, bit_hi, bit_lo, _width in fields:
        if name in ("0", "1"):
            continue

        # Try exact field name match first
        exact_val = field_values.get(name)
        if exact_val is not None and not isinstance(exact_val, list):
            word = _pack_field(word, exact_val, bit_hi, bit_lo)
            continue

        # List-based duplicate packing is only valid when the KB reuses the
        # exact same raw field name more than once.
        base_name = name.split(" ")[0] if " " in name else name
        idx = field_counts.get(base_name, 0)
        field_counts[base_name] = idx + 1

        val = exact_val if exact_val is not None else field_values.get(base_name)
        if val is None:
            raise KeyError(f"{inst}: missing value for field {name}")
        if " " in name and base_name != name:
            raise KeyError(f"{inst}: missing exact value for field {name}")
        if isinstance(val, list):
            if idx >= len(val):
                raise KeyError(f"{inst}: missing value for field {name}")
            word = _pack_field(word, val[idx], bit_hi, bit_lo)
        else:
            if idx != 0:
                raise KeyError(f"{inst}: missing value for field {name}")
            word = _pack_field(word, val, bit_hi, bit_lo)

    return word


def _get_size_encoding(inst: str, size_char: SizeChar | None) -> int | None:
    """Get binary size field value for an instruction.

    Returns the binary value to pack into the SIZE field.
    """
    if size_char is None:
        return None
    has_size_field = any(
        any(name == "SIZE" for name, _, _, _ in runtime_m68k_asm.RAW_FIELDS[enc_idx][inst])
        for enc_idx in range(runtime_m68k_asm.ENCODING_COUNTS[inst])
    )
    if not has_size_field:
        return None
    mnemonic = inst
    size_encs = runtime_m68k_asm.SIZE_ENCODINGS_ASM
    if mnemonic not in size_encs:
        raise KeyError(f"KB missing size encoding for {mnemonic!r}")
    enc = size_encs[mnemonic]
    idx = {"b": _SIZE_BYTE, "w": _SIZE_WORD, "l": _SIZE_LONG}.get(size_char)
    if idx is None:
        raise KeyError(f"unsupported size {size_char!r}")
    value = enc[idx]
    if value is None:
        raise KeyError(
            f"KB size encoding for {mnemonic!r} missing size {size_char!r}"
        )
    return int(value)


def _defaulted_size_char(inst: str, size_char: SizeChar | None) -> SizeChar | None:
    """Resolve omitted size suffixes from KB metadata when the instruction allows it."""
    if size_char is not None:
        return size_char
    if runtime_m68k_asm.USES_LABELS[inst]:
        return None
    sizes = runtime_m68k_asm.INSTRUCTION_SIZES.get(inst, ())
    if not sizes:
        return None
    if len(sizes) == 1:
        return cast(SizeChar, sizes[0])
    default_size = runtime_m68k_asm.DEFAULT_OPERAND_SIZE
    if default_size in sizes:
        return cast(SizeChar, default_size)
    return None


# -- Instruction assemblers ------------------------------------------------

def _assemble_no_operands(inst: str, resolution: Resolution) -> bytes:
    """Assemble instructions with no operands (NOP, RTS, RTE, etc.)."""
    word = _build_opword(inst, {})
    return _to_bytes_16(word)


def _assemble_ea_single(inst: str, resolution: Resolution, operand: str, enc_idx: int = 0) -> bytes:
    """Assemble instructions with a single EA operand (CLR, NEG, NOT, TST, etc.)."""
    size_char = resolution["size"]
    size_enc = _get_size_encoding(inst, size_char)
    sz_bytes = runtime_m68k_asm.SIZE_BYTE_COUNT.get(size_char, 2) if size_char else 2

    mode, reg, ext = parse_ea(operand, sz_bytes)
    _require_allowed_target_ea_mode(inst, mode, reg)

    fields: FieldValues = {"MODE": mode, "REGISTER": reg}
    if size_enc is not None:
        fields["SIZE"] = size_enc

    # CC-parameterized single EA (Scc)
    if resolution["cc_index"] is not None:
        fields["CONDITION"] = resolution["cc_index"]

    word = _build_opword(inst, fields)
    return _to_bytes_16(word) + ext


def _assemble_two_ea(inst: str, resolution: Resolution, src_str: str, dst_str: str) -> bytes:
    """Assemble instructions with source and destination EA (MOVE, etc.)."""
    size_char = resolution["size"]
    size_enc = _get_size_encoding(inst, size_char)
    sz_bytes = runtime_m68k_asm.SIZE_BYTE_COUNT.get(size_char, 2) if size_char else 2

    src_mode, src_reg, src_ext = parse_ea(src_str, sz_bytes)
    dst_mode, dst_reg, dst_ext = parse_ea(dst_str, sz_bytes)

    # For MOVE, encoding has: dst_reg[11:9], dst_mode[8:6], src_mode[5:3], src_reg[2:0]
    # KB encoding lists fields in bit order (high to low), so:
    # First REGISTER = dst (bits 11:9), second REGISTER = src (bits 2:0)
    # First MODE = dst (bits 8:6), second MODE = src (bits 5:3)
    # Use list values for duplicate fields - first = highest bit position = destination.

    # Check if this instruction has duplicate MODE/REGISTER fields
    fields0 = runtime_m68k_asm.RAW_FIELDS[0][inst]
    mode_count = sum(1 for name, _, _, _ in fields0 if name == "MODE")

    if mode_count >= 2:
        # Dual EA (MOVE-style): higher bits = destination
        fields: FieldValues = {
            "MODE": [dst_mode, src_mode],
            "REGISTER": [dst_reg, src_reg],
        }
    else:
        # Single EA + register (ADD-style): handled by _assemble_opmode instead
        raise ValueError(f"_assemble_two_ea called for non-dual-EA instruction {inst}")

    if size_enc is not None:
        fields["SIZE"] = size_enc

    word = _build_opword(inst, fields)
    return _to_bytes_16(word) + src_ext + dst_ext


def _assemble_opmode(inst: str, resolution: Resolution, src_str: str, dst_str: str) -> bytes:
    """Assemble instructions with OPMODE field (ADD, SUB, AND, OR, CMP, etc.).

    OPMODE determines both size and direction (ea->Dn or Dn->ea).
    """
    size_char = resolution["size"]
    sz_bytes = runtime_m68k_asm.SIZE_BYTE_COUNT.get(size_char, 2) if size_char else 2

    mnemonic = inst
    opm_table = cast(list[AsmOpmodeEntry] | None, runtime_m68k_asm.OPMODE_TABLES_LIST.get(mnemonic))
    if not opm_table:
        raise KeyError(f"{mnemonic}: runtime KB missing opmode_table")

    src_mode, src_reg, src_ext = parse_ea(src_str, sz_bytes)
    dst_mode, dst_reg, dst_ext = parse_ea(dst_str, sz_bytes)

    # Determine direction from operands:
    # If dst is Dn (mode 0), direction is ea->Dn: look for matching opmode with "-> Dn" operation
    # If src is Dn (mode 0) and dst is EA, direction is Dn->ea: look for "-> <ea>" operation
    enc = cast(EaModeEncoding, runtime_m68k_asm.EA_MODE_ENCODING)
    dn_mode = enc["dn"][0]

    selected_opmode: int | None = None
    if dst_mode == dn_mode:
        # Destination is Dn - find KB entry where EA is the source.
        for entry in opm_table:
            if entry["size"] == size_char and entry["ea_is_source"]:
                selected_opmode = entry["opmode"]
                break
    elif src_mode == dn_mode:
        # Source is Dn - find KB entry where EA is the destination.
        for entry in opm_table:
            if entry["size"] == size_char and not entry["ea_is_source"]:
                selected_opmode = entry["opmode"]
                break

    if selected_opmode is None:
        raise ValueError(
                f"{inst}.{size_char}: no matching opmode for "
                f"src_mode={src_mode} dst_mode={dst_mode}")

    # For opmode instructions: REGISTER field = Dn register, MODE/REGISTER(EA) = the EA operand
    if dst_mode == dn_mode:
        # ea->Dn: REGISTER=dst_reg(Dn), MODE=src_mode, EA_REGISTER=src_reg
        ea_fields: FieldValues = {"REGISTER": dst_reg, "OPMODE": selected_opmode,
                  "MODE": src_mode}
        # Find the EA register field (might be named REGISTER too - it's the lower one)
        enc_fields = runtime_m68k_asm.RAW_FIELDS[0][inst]
        reg_fields = [field for field in enc_fields if field[0] == "REGISTER"]
        if len(reg_fields) >= 2:
            # Two REGISTER fields: higher = Dn, lower = EA reg
            ea_fields["REGISTER"] = [dst_reg, src_reg]
        else:
            # Single REGISTER field - EA reg is separate
            ea_fields["REGISTER"] = dst_reg
            # Hmm, need to figure out which field holds the EA register
            # For ADD etc., the encoding is: REGISTER[11:9]=Dn, OPMODE[8:6], MODE[5:3], REGISTER[2:0]=EA
            ea_fields["REGISTER"] = [dst_reg, src_reg]
        word = _build_opword(inst, ea_fields)
        return _to_bytes_16(word) + src_ext
    # Dn->ea: REGISTER=src_reg(Dn), MODE=dst_mode, EA_REGISTER=dst_reg
    dst_fields: FieldValues = {"REGISTER": [src_reg, dst_reg], "OPMODE": selected_opmode,
              "MODE": dst_mode}
    word = _build_opword(inst, dst_fields)
    return _to_bytes_16(word) + dst_ext


def _assemble_immediate(inst: str, resolution: Resolution, imm_str: str, dst_str: str) -> bytes:
    """Assemble immediate instructions (ADDI, SUBI, ORI, ANDI, EORI, CMPI)."""
    size_char = resolution["size"]
    size_enc = _get_size_encoding(inst, size_char)
    sz_bytes = runtime_m68k_asm.SIZE_BYTE_COUNT.get(size_char, 2) if size_char else 2

    imm_val = _parse_imm_value(imm_str.lstrip("#"))
    dst_mode, dst_reg, dst_ext = parse_ea(dst_str, sz_bytes)
    _require_allowed_target_ea_mode(inst, dst_mode, dst_reg)

    fields: FieldValues = {"MODE": dst_mode, "REGISTER": dst_reg}
    if size_enc is not None:
        fields["SIZE"] = size_enc
    word = _build_opword(inst, fields)

    # Immediate data extension word(s)
    imm_bytes = _to_bytes_32(imm_val) if sz_bytes >= 4 else _to_bytes_16(imm_val)

    return _to_bytes_16(word) + imm_bytes + dst_ext


def _assemble_quick(inst: str, resolution: Resolution, imm_str: str, dst_str: str) -> bytes:
    """Assemble ADDQ/SUBQ - inline 3-bit immediate with zero_means."""
    size_char = resolution["size"]
    size_enc = _get_size_encoding(inst, size_char)
    sz_bytes = runtime_m68k_asm.SIZE_BYTE_COUNT.get(size_char, 2) if size_char else 2

    imm_val = _parse_imm_value(imm_str.lstrip("#"))
    dst_mode, dst_reg, dst_ext = parse_ea(dst_str, sz_bytes)
    _require_allowed_target_ea_mode(inst, dst_mode, dst_reg)

    # Handle zero_means: if imm_val equals zero_means value, encode as 0
    mnemonic = inst
    ir = runtime_m68k_asm.IMMEDIATE_RANGES.get(mnemonic)
    if ir is None:
        raise KeyError(f"{mnemonic}: runtime KB missing immediate_range")
    zero_means = ir[5]
    data_val = imm_val
    if zero_means is not None and imm_val == zero_means:
        data_val = 0

    fields: FieldValues = {"MODE": dst_mode, "REGISTER": dst_reg, "DATA": data_val}
    if size_enc is not None:
        fields["SIZE"] = size_enc
    word = _build_opword(inst, fields)
    return _to_bytes_16(word) + dst_ext


def _assemble_moveq(inst: str, resolution: Resolution, imm_str: str, dst_str: str) -> bytes:
    """Assemble MOVEQ - 8-bit immediate in opword."""
    imm_val = _parse_imm_value(imm_str.lstrip("#"))

    # Destination must be Dn
    m = _RE_DN.match(dst_str.strip())
    if not m:
        raise ValueError(f"MOVEQ destination must be Dn, got {dst_str!r}")
    dreg = int(m.group(1))

    fields: FieldValues = {"REGISTER": dreg, "DATA": imm_val & 0xFF}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word)


def _assemble_branch(inst: str, resolution: Resolution, target_str: str, pc: int = 0) -> bytes:
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
    mnemonic = inst
    ir = runtime_m68k_asm.IMMEDIATE_RANGES.get(mnemonic)
    if ir is None:
        raise KeyError(f"{mnemonic}: runtime KB missing immediate_range")
    disp_enc = runtime_m68k_asm.BRANCH_INLINE_DISPLACEMENTS.get(mnemonic)
    if disp_enc is None:
        raise KeyError(f"{mnemonic}: runtime KB missing branch displacement table")

    # KB-driven displacement field name, reserved values, and extension sizes
    disp_field, _disp_spec, word_signal, long_signal, word_bytes, long_bytes = disp_enc
    word_bits = word_bytes * 8

    # KB-driven byte displacement range
    byte_min = ir[3] if ir[3] is not None else -128
    byte_max = ir[4] if ir[4] is not None else 127

    target = _parse_imm_value(target_str)
    disp = target - (pc + 2)

    fields: FieldValues = {}
    if cc_index is not None:
        fields["CONDITION"] = cc_index

    # Reserved values in the byte displacement field (signal word/long extension)
    reserved = set()
    if word_signal is not None:
        reserved.add(word_signal)            # 0x00 -> word extension
    if long_signal is not None:
        reserved.add(long_signal - 256)      # 0xFF as signed -> -1

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
    if size_char == "w":
        word_max = (1 << (word_bits - 1)) - 1
        word_min = -(1 << (word_bits - 1))
        if not (word_min <= disp <= word_max):
            raise ValueError(
                f"Branch displacement {disp} out of .w range "
                f"({word_min}..{word_max})")
        fields[disp_field] = word_signal if word_signal is not None else 0x00
        word = _build_opword(inst, fields)
        return _to_bytes_16(word) + _to_bytes_16(disp & 0xFFFF)
    # Long branch (020+)
    fields[disp_field] = long_signal if long_signal is not None else 0xFF
    word = _build_opword(inst, fields)
    return _to_bytes_16(word) + _to_bytes_32(disp & 0xFFFFFFFF)


def _assemble_dbcc(inst: str, resolution: Resolution, reg_str: str, target_str: str, pc: int = 0) -> bytes:
    """Assemble DBcc - decrement and branch.

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

    if cc_index is None:
        raise ValueError(f"{inst}: DBcc requires condition code")
    fields: FieldValues = {"CONDITION": cc_index, "REGISTER": dreg}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word) + _to_bytes_16(disp & 0xFFFF)


def _assemble_shift_reg(inst: str, resolution: Resolution, operands: Operands) -> bytes:
    """Assemble shift/rotate register form: ASL Dx,Dy or ASL #n,Dy.

    KB encoding has two REGISTER fields:
        REGISTER(11:9) = count/register (immediate count or source Dn number)
        REGISTER(2:0)  = destination Dn
    The type bits (distinguishing ASL/LSL/ROL/ROXL) are fixed in each
    instruction's encoding - no variable type field needed.
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

    fields: FieldValues = {}
    if size_enc is not None:
        fields["SIZE"] = size_enc
    if direction is not None:
        fields["dr"] = direction

    # Determine i/r and count/register from source
    src_stripped = src_str.strip()
    m_imm = _RE_IMM.match(src_stripped)
    m_dn = _RE_DN.match(src_stripped)

    if m_imm:
        count = _parse_imm_value(m_imm.group(1))
        mnemonic = inst
        ir = runtime_m68k_asm.IMMEDIATE_RANGES.get(mnemonic)
        if ir is None:
            raise KeyError(f"{mnemonic}: runtime KB missing immediate_range")
        zero_means = ir[5]
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


def _assemble_shift_mem(inst: str, resolution: Resolution, operand: str) -> bytes:
    """Assemble shift/rotate memory form: ASL <ea> (single-operand, word-only).

    Uses encoding[1] which has dr + MODE/REGISTER for the EA.
    The shift count is always 1 (implicit).
    """
    direction = resolution["direction"]
    mode, reg, ext = parse_ea(operand)
    _require_allowed_target_ea_mode(inst, mode, reg)

    fields: FieldValues = {"MODE": mode, "REGISTER": reg}
    if direction is not None:
        fields["dr"] = direction
    word = _build_opword(inst, fields, enc_idx=1)
    return _to_bytes_16(word) + ext


def _assemble_ea_dn(inst: str, resolution: Resolution, src_str: str, dst_str: str) -> bytes:
    """Assemble <ea>,Dn form - CHK, DIVS, DIVU, MULS, MULU.

    Encoding: REGISTER(11:9)=Dn, MODE(5:3)+REGISTER(2:0)=EA source.
    CHK also has a SIZE field.
    """
    size_char = resolution["size"]
    size_enc = _get_size_encoding(inst, size_char)
    sz_bytes = runtime_m68k_asm.SIZE_BYTE_COUNT.get(size_char, 2) if size_char else 2

    src_mode, src_reg, src_ext = parse_ea(src_str, sz_bytes)
    _require_allowed_ea_mode(inst, src_mode, src_reg, source=True)

    m = _RE_DN.match(dst_str.strip())
    if not m:
        raise ValueError(f"{inst}: destination must be Dn, got {dst_str!r}")
    dn_reg = int(m.group(1))

    fields: FieldValues = {"REGISTER": [dn_reg, src_reg], "MODE": src_mode}
    if size_enc is not None:
        fields["SIZE"] = size_enc
    word = _build_opword(inst, fields)
    return _to_bytes_16(word) + src_ext


def _assemble_movep(inst: str, resolution: Resolution, src_str: str, dst_str: str) -> bytes:
    """Assemble MOVEP - data register to/from memory displacement.

    KB encoding uses named fields: DATA REGISTER (11:9), ADDRESS REGISTER (2:0).
    Direction and size determined from opmode_table.
    """
    size_char = resolution["size"]

    # Determine direction from operands
    ms_dn = _RE_DN.match(src_str.strip())
    md_dn = _RE_DN.match(dst_str.strip())

    mnemonic = inst
    opm_table = cast(list[AsmOpmodeEntry] | None, runtime_m68k_asm.OPMODE_TABLES_LIST.get(mnemonic))
    if not opm_table:
        raise KeyError(f"{mnemonic}: runtime KB missing opmode_table")
    selected: int | None = None

    if ms_dn and not md_dn:
        # Dn,d(An) -> register to memory
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
        # d(An),Dn -> memory to register
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
        raise ValueError("MOVEP: need Dn,d(An) or d(An),Dn")

    if selected is None:
        raise ValueError(f"MOVEP.{size_char}: no matching opmode")

    fields: FieldValues = {"DATA REGISTER": data_reg, "OPMODE": selected,
              "ADDRESS REGISTER": addr_reg}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word) + _to_bytes_16(disp)


def _assemble_movem(inst: str, resolution: Resolution, operands: Operands) -> bytes:
    """Assemble MOVEM - register list to/from memory."""
    size_char = resolution["size"]
    size_enc = _get_size_encoding(inst, size_char)
    sz_bytes = runtime_m68k_asm.SIZE_BYTE_COUNT.get(size_char, 2) if size_char else 2

    src_str, dst_str = operands

    # Determine direction: reg-to-mem or mem-to-reg
    # If source looks like a register list, it's reg-to-mem
    # If destination looks like a register list, it's mem-to-reg
    reg_masks = runtime_m68k_asm.MOVEM_REG_MASKS

    def _parse_reglist(s: str) -> set[str]:
        """Parse register list string like 'd0-d2/a0' -> bitmask."""
        s = s.strip().lower()
        regs: set[str] = set()
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

    def _reglist_to_mask(regs: set[str], order: list[str]) -> int:
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
        _require_allowed_target_ea_mode(inst, ea_mode, ea_reg)
        direction = 0  # reg-to-mem

        # Use predecrement order if destination is predecrement
        predec_mode = cast(EaModeEncoding, runtime_m68k_asm.EA_MODE_ENCODING)["predec"][0]
        if ea_mode == predec_mode:
            mask = _reglist_to_mask(regs, reg_masks["predecrement"])
        else:
            mask = _reglist_to_mask(regs, reg_masks["normal"])
    else:
        # Memory-to-register: MOVEM <ea>,reglist
        regs = _parse_reglist(dst_str)
        ea_mode, ea_reg, ea_ext = parse_ea(src_str, sz_bytes)
        _require_allowed_target_ea_mode(inst, ea_mode, ea_reg)
        direction = 1  # mem-to-reg
        mask = _reglist_to_mask(regs, reg_masks["normal"])

    fields: FieldValues = {"dr": direction, "MODE": ea_mode, "REGISTER": ea_reg}
    if size_enc is not None:
        fields["SIZE"] = size_enc
    word = _build_opword(inst, fields)
    return _to_bytes_16(word) + _to_bytes_16(mask) + ea_ext


def _assemble_link(inst: str, resolution: Resolution, reg_str: str, imm_str: str) -> bytes:
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
    fields: FieldValues = {"REGISTER": areg}
    size_char = resolution["size"] or "w"
    if size_char == "l":
        word = _build_opword(inst, fields, enc_idx=2)
        return _to_bytes_16(word) + _to_bytes_32(disp)
    word = _build_opword(inst, fields)
    return _to_bytes_16(word) + _to_bytes_16(disp)


def _assemble_unlk(inst: str, resolution: Resolution, reg_str: str) -> bytes:
    """Assemble UNLK An."""
    m = _RE_AN.match(reg_str.strip())
    if not m:
        raise ValueError(f"UNLK register must be An, got {reg_str!r}")
    areg = int(m.group(1))
    fields: FieldValues = {"REGISTER": areg}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word)


def _assemble_exg(inst: str, resolution: Resolution, src_str: str, dst_str: str) -> bytes:
    """Assemble EXG - exchange registers.

    KB encoding uses named fields: REGISTER Rx (11:9), REGISTER Ry (3:0).
    KB opmode_table uses "description" (not "operation") for form descriptions.
    """
    ms = _RE_DN.match(src_str.strip())
    md = _RE_DN.match(dst_str.strip())
    mas = _RE_AN.match(src_str.strip()) or _RE_SP.match(src_str.strip())
    mad = _RE_AN.match(dst_str.strip()) or _RE_SP.match(dst_str.strip())

    opmode: int | None = None
    rx = ry = 0
    mnemonic = inst
    opm_table = cast(list[AsmOpmodeEntry] | None, runtime_m68k_asm.OPMODE_TABLES_LIST.get(mnemonic))
    if not opm_table:
        raise KeyError(f"{mnemonic}: runtime KB missing opmode_table")

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
        # Ax,Dy - swap to canonical Dy,Ax
        rx = int(md.group(1))
        ry = 7 if _RE_SP.match(src_str.strip()) else int(mas.group(1))
        for entry in opm_table:
            desc = entry.get("description", "").lower()
            if "data" in desc and "address" in desc:
                opmode = entry["opmode"]
                break

    if opmode is None:
        raise ValueError(f"EXG: cannot determine opmode for {src_str},{dst_str}")

    fields: FieldValues = {
        "REGISTER Rx": rx,
        "REGISTER Ry": ry,
        "OPMODE": opmode,
    }
    word = _build_opword(inst, fields)
    return _to_bytes_16(word)


def _assemble_swap(inst: str, resolution: Resolution, reg_str: str) -> bytes:
    """Assemble SWAP Dn."""
    m = _RE_DN.match(reg_str.strip())
    if not m:
        raise ValueError(f"SWAP register must be Dn, got {reg_str!r}")
    fields: FieldValues = {"REGISTER": int(m.group(1))}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word)


def _assemble_ext(inst: str, resolution: Resolution, reg_str: str) -> bytes:
    """Assemble EXT/EXTB Dn.

    EXT has no SIZE field - size is encoded in OPMODE from KB opmode_table.
    User's size suffix is the result size (.w = byte->word, .l = word->long).
    """
    size_char = resolution["size"]
    user_mnemonic = resolution.get("mnemonic_str", "ext")
    m = _RE_DN.match(reg_str.strip())
    if not m:
        raise ValueError(f"EXT register must be Dn, got {reg_str!r}")

    mnemonic = inst
    opm_table = cast(list[AsmOpmodeEntry] | None, runtime_m68k_asm.OPMODE_TABLES_LIST.get(mnemonic))
    if not opm_table:
        raise KeyError(f"{mnemonic}: runtime KB missing opmode_table")
    selected: int | None = None
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
            if user_mnemonic == "ext" and "word" in desc:
                selected = entry["opmode"]
                break
    if selected is None:
        raise ValueError(f"EXT: no opmode for {user_mnemonic}.{size_char}")

    fields: FieldValues = {"REGISTER": int(m.group(1)), "OPMODE": selected}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word)


def _assemble_rn(inst: str, resolution: Resolution, reg_str: str) -> bytes:
    """Assemble single rn register forms such as RTM."""
    stripped = reg_str.strip()
    m = _RE_DN.match(stripped)
    if m:
        fields: FieldValues = {"D/A": 0, "REGISTER": int(m.group(1))}
    else:
        m = _RE_AN.match(stripped)
        if m:
            fields = {"D/A": 1, "REGISTER": int(m.group(1))}
        elif _RE_SP.match(stripped):
            fields = {"D/A": 1, "REGISTER": 7}
        else:
            raise ValueError(f"{inst} register must be Dn or An, got {reg_str!r}")
    word = _build_opword(inst, fields)
    return _to_bytes_16(word)


def _assemble_opword_immediate(inst: str, resolution: Resolution, imm_str: str) -> bytes:
    """Assemble instructions where immediate goes into an opword field.

    Used for TRAP, BKPT, and any instruction whose immediate_range.field
    names an encoding field in the opword (e.g. VECTOR, DATA).
    """
    mnemonic = inst
    ir = runtime_m68k_asm.IMMEDIATE_RANGES.get(mnemonic)
    if ir is None:
        raise KeyError(f"{mnemonic}: runtime KB missing immediate_range")
    field_name = ir[0]
    if not field_name:
        raise ValueError(f"{inst}: no immediate_range.field in KB")
    imm_val = _parse_imm_value(imm_str.strip().lstrip("#"))
    bits = ir[1] if ir[1] is not None else 16
    ir_min = ir[3] if ir[3] is not None else 0
    ir_max = ir[4] if ir[4] is not None else (1 << bits) - 1
    if not (ir_min <= imm_val <= ir_max):
        raise ValueError(
            f"{inst}: immediate {imm_val} out of range "
            f"[{ir_min}..{ir_max}]")
    fields: FieldValues = {field_name: imm_val}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word)


def _assemble_lea_pea(inst: str, resolution: Resolution, src_str: str, dst_str: str | None = None) -> bytes:
    """Assemble LEA <ea>,An or PEA <ea>."""
    sz_bytes = 4  # LEA/PEA always long

    src_mode, src_reg, src_ext = parse_ea(src_str, sz_bytes)
    _require_allowed_target_ea_mode(inst, src_mode, src_reg)

    fields: FieldValues = {"MODE": src_mode}

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


def _assemble_bcd(inst: str, resolution: Resolution, src_str: str, dst_str: str) -> bytes:
    """Assemble ABCD/SBCD - data register or predecrement form.

    KB encoding has two named REGISTER fields (highest bits = dst, lowest = src).
    """
    ms = _RE_DN.match(src_str.strip())
    md = _RE_DN.match(dst_str.strip())

    reg_fields = runtime_m68k_asm.RAW_FIELDS[0][inst]
    dst_field = next(name for name, bit_hi, *_ in reg_fields if name.startswith("REGISTER") and bit_hi == 11)
    src_field = next(name for name, bit_hi, *_ in reg_fields if name.startswith("REGISTER") and bit_hi == 2)

    if ms and md:
        # Dn,Dn: syntax is src,dst; encoding high bits = dst, low bits = src
        fields: FieldValues = {
            dst_field: int(md.group(1)),
            src_field: int(ms.group(1)),
            "R/M": 0,
        }
    else:
        # -(An),-(An)
        ms = _RE_PREDEC.match(src_str.strip())
        md = _RE_PREDEC.match(dst_str.strip())
        if not (ms and md):
            raise ValueError("ABCD/SBCD operands must be Dn,Dn or -(An),-(An)")
        fields = {
            dst_field: int(md.group(1)),
            src_field: int(ms.group(1)),
            "R/M": 1,
        }

    word = _build_opword(inst, fields)
    return _to_bytes_16(word)


def _assemble_pack_unpk(inst: str, resolution: Resolution, src_str: str, dst_str: str, imm_str: str) -> bytes:
    """Assemble PACK/UNPK KB-backed forms.

    PACK supports register and predecrement forms.
    UNPK support follows the current KB/runtime forms exactly.
    """
    imm = _parse_imm_value(imm_str.strip().lstrip("#"))

    ms = _RE_DN.match(src_str.strip())
    md = _RE_DN.match(dst_str.strip())
    if ms and md:
        fields = {
            "REGISTER Dy/Ay": int(md.group(1)),
            "R/M": 0,
            "REGISTER Dx/Ax": int(ms.group(1)),
        }
        word = _build_opword(inst, fields)
        return _to_bytes_16(word) + _to_bytes_16(imm)

    if inst != "PACK":
        raise ValueError(f"{inst}: unsupported operands {(src_str, dst_str, imm_str)!r}")

    ms = _RE_PREDEC.match(src_str.strip())
    md = _RE_PREDEC.match(dst_str.strip())
    if not (ms and md):
        raise ValueError(f"{inst}: operands must be Dn,Dn,#imm or -(An),-(An),#imm")

    fields = {
        "REGISTER Dy/Ay": int(md.group(1)),
        "R/M": 1,
        "REGISTER Dx/Ax": int(ms.group(1)),
    }
    word = _build_opword(inst, fields)
    return _to_bytes_16(word) + _to_bytes_16(imm)


def _assemble_addx_subx(inst: str, resolution: Resolution, src_str: str, dst_str: str) -> bytes:
    """Assemble ADDX/SUBX - data register or predecrement form.

    KB encoding has two named REGISTER fields (highest bits = dst, lowest = src).
    """
    size_char = resolution["size"]
    size_enc = _get_size_encoding(inst, size_char)

    ms = _RE_DN.match(src_str.strip())
    md = _RE_DN.match(dst_str.strip())

    if ms and md:
        reg_fields = runtime_m68k_asm.RAW_FIELDS[0][inst]
        dst_field = next(name for name, bit_hi, *_ in reg_fields if name.startswith("REGISTER") and bit_hi == 11)
        src_field = next(name for name, bit_hi, *_ in reg_fields if name.startswith("REGISTER") and bit_hi == 2)
        fields: FieldValues = {
            dst_field: int(md.group(1)),
            src_field: int(ms.group(1)),
            "R/M": 0,
        }
    else:
        ms = _RE_PREDEC.match(src_str.strip())
        md = _RE_PREDEC.match(dst_str.strip())
        if not (ms and md):
            raise ValueError("ADDX/SUBX operands must be Dn,Dn or -(An),-(An)")
        reg_fields = runtime_m68k_asm.RAW_FIELDS[0][inst]
        dst_field = next(name for name, bit_hi, *_ in reg_fields if name.startswith("REGISTER") and bit_hi == 11)
        src_field = next(name for name, bit_hi, *_ in reg_fields if name.startswith("REGISTER") and bit_hi == 2)
        fields = {
            dst_field: int(md.group(1)),
            src_field: int(ms.group(1)),
            "R/M": 1,
        }
    if size_enc is not None:
        fields["SIZE"] = size_enc

    word = _build_opword(inst, fields)
    return _to_bytes_16(word)


def _assemble_cmpm(inst: str, resolution: Resolution, src_str: str, dst_str: str) -> bytes:
    """Assemble CMPM (Ay)+,(Ax)+.

    KB encoding uses named fields: REGISTER Ax (11:9) = dst, REGISTER Ay (2:0) = src.
    Syntax: CMPM (Ay)+,(Ax)+ - source is first operand, destination is second.
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
        raise ValueError("CMPM operands must be (An)+,(An)+")

    fields: FieldValues = {
        "REGISTER Ax": dst_reg,
        "REGISTER Ay": src_reg,
    }
    if size_enc is not None:
        fields["SIZE"] = size_enc
    word = _build_opword(inst, fields)
    return _to_bytes_16(word)


def _assemble_movea(inst: str, resolution: Resolution, src_str: str, dst_str: str) -> bytes:
    """Assemble MOVEA <ea>,An."""
    size_char = resolution["size"]
    sz_bytes = runtime_m68k_asm.SIZE_BYTE_COUNT.get(size_char, 2) if size_char else 2

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
    move_inst = "MOVE"

    an_mode = cast(EaModeEncoding, runtime_m68k_asm.EA_MODE_ENCODING)["an"][0]  # mode 1

    size_enc = _get_size_encoding(move_inst, size_char)

    fields: FieldValues = {
        "MODE": [an_mode, src_mode],
        "REGISTER": [dst_areg, src_reg],
    }
    if size_enc is not None:
        fields["SIZE"] = size_enc

    word = _build_opword(move_inst, fields)
    return _to_bytes_16(word) + src_ext


def _assemble_bit_reg(inst: str, resolution: Resolution, src_str: str, dst_str: str) -> bytes:
    """Assemble BTST/BCHG/BCLR/BSET Dn,<ea> - dynamic (register) form.

    Uses encoding[0]: REGISTER(11:9)=Dn, MODE(5:3), REGISTER(2:0)=EA.
    """
    ms = _RE_DN.match(src_str.strip())
    if not ms:
        raise ValueError(f"{inst}: source must be Dn, got {src_str!r}")
    src_reg = int(ms.group(1))

    dst_mode, dst_reg, dst_ext = parse_ea(dst_str)
    _require_allowed_target_ea_mode(inst, dst_mode, dst_reg)
    fields: FieldValues = {"REGISTER": [src_reg, dst_reg], "MODE": dst_mode}
    word = _build_opword(inst, fields, enc_idx=0)
    return _to_bytes_16(word) + dst_ext


def _assemble_bit_imm(inst: str, resolution: Resolution, src_str: str, dst_str: str) -> bytes:
    """Assemble BTST/BCHG/BCLR/BSET #n,<ea> - static (immediate) form.

    Uses encoding[1] for the opword (fixed bits 15:8 + MODE/REGISTER for EA)
    and a 16-bit extension word containing the bit number.
    """
    bit_num = _parse_imm_value(src_str.strip().lstrip("#"))
    dst_mode, dst_reg, dst_ext = parse_ea(dst_str)
    _require_allowed_target_ea_mode(inst, dst_mode, dst_reg)

    fields: FieldValues = {"MODE": dst_mode, "REGISTER": dst_reg}
    word = _build_opword(inst, fields, enc_idx=1)
    return _to_bytes_16(word) + _to_bytes_16(bit_num) + dst_ext


def _assemble_adda_suba_cmpa(inst: str, resolution: Resolution, src_str: str, dst_str: str) -> bytes:
    """Assemble ADDA/SUBA/CMPA <ea>,An.

    These instructions have their own KB entry with encoding and opmode_table.
    The opmode_table uses "description" (not "operation") for entries.
    """
    size_char = resolution["size"]
    sz_bytes = runtime_m68k_asm.SIZE_BYTE_COUNT.get(size_char, 2) if size_char else 2

    src_mode, src_reg, src_ext = parse_ea(src_str, sz_bytes)

    m = _RE_AN.match(dst_str.strip())
    if m:
        dst_areg = int(m.group(1))
    elif _RE_SP.match(dst_str.strip()):
        dst_areg = 7
    else:
        raise ValueError(f"{inst} destination must be An, got {dst_str!r}")

    mnemonic = inst
    opm_table = cast(list[AsmOpmodeEntry] | None, runtime_m68k_asm.OPMODE_TABLES_LIST.get(mnemonic))
    if opm_table is None:
        raise KeyError(f"{mnemonic}: runtime KB missing opmode_table")
    selected_opmode = None
    for entry in opm_table:
        if entry["size"] == size_char:
            selected_opmode = entry["opmode"]
            break

    if selected_opmode is None:
        raise ValueError(f"{inst}.{size_char}: no opmode")

    fields: FieldValues = {"REGISTER": [dst_areg, src_reg], "OPMODE": selected_opmode, "MODE": src_mode}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word) + src_ext


def _classify_asm_operand(text: str) -> OperandClass:
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


def _resolve_by_syntax_index(mnemonic_lower: str, operands: Operands) -> ResolvedSyntax | None:
    """Resolve (mnemonic, operand types) to KB instruction via asm_syntax_index.

    Returns (kb_inst, matched_form_index) or None.
    """
    op_types = tuple(_classify_asm_operand(op) for op in operands)
    index = runtime_m68k_asm.ASM_SYNTAX_INDEX

    key = (mnemonic_lower, op_types)
    resolved = index.get(key)
    if resolved is None:
        return None
    kb_mnemonic, canonical_op_types = resolved
    for form_idx, form_ops in enumerate(runtime_m68k_asm.FORM_OPERAND_TYPES[kb_mnemonic]):
        if form_ops == canonical_op_types:
            return kb_mnemonic, form_idx
    raise KeyError(
        f"{kb_mnemonic}: ASM_SYNTAX_INDEX resolved {mnemonic_lower!r} {canonical_op_types!r} "
        f"but no FORM_OPERAND_TYPES entry matched"
    )


# -- SR/CCR/USP instruction handlers --------------------------------------

def _inst_size_bytes(inst: str) -> int:
    """Get operand size in bytes from the instruction's KB sizes field."""
    sizes = runtime_m68k_asm.INSTRUCTION_SIZES[inst]
    return int(runtime_m68k_asm.SIZE_BYTE_COUNT[sizes[0]])


def _ea_mode_name(mode: int, reg: int) -> str:
    for name, (mode_val, reg_val) in cast(EaModeEncoding, runtime_m68k_asm.EA_MODE_ENCODING).items():
        if mode_val != mode:
            continue
        if reg_val is None or reg_val == reg:
            return name
    raise KeyError(f"No EA mode name for mode={mode} reg={reg}")


def _require_allowed_ea_mode(inst: str, mode: int, reg: int, *, source: bool) -> None:
    ea_mode_tables = runtime_m68k_asm.EA_MODE_TABLES
    if inst not in ea_mode_tables:
        raise KeyError(f"{inst}: runtime KB missing ea_mode_table")
    source_modes, dest_modes, alterable_modes = ea_mode_tables[inst]
    allowed_modes = source_modes if source else dest_modes
    if not allowed_modes:
        allowed_modes = alterable_modes
    mode_name = _ea_mode_name(mode, reg)
    if mode_name not in allowed_modes:
        side = "source" if source else "destination"
        raise ValueError(f"{inst}: invalid {side} EA mode {mode_name}")


def _require_allowed_target_ea_mode(inst: str, mode: int, reg: int) -> None:
    ea_mode_tables = runtime_m68k_asm.EA_MODE_TABLES
    if inst not in ea_mode_tables:
        raise KeyError(f"{inst}: runtime KB missing ea_mode_table")
    _source_modes, dest_modes, alterable_modes = ea_mode_tables[inst]
    allowed_modes = dest_modes if dest_modes else alterable_modes
    mode_name = _ea_mode_name(mode, reg)
    if mode_name not in allowed_modes:
        raise ValueError(f"{inst}: invalid target EA mode {mode_name}")


def _assemble_imm_to_sr_ccr(inst: str, imm_str: str) -> bytes:
    """Assemble ANDI/EORI/ORI to CCR/SR - all-fixed opword + immediate extension.

    Extension word size derived from KB sizes field via size_byte_count.
    """
    sz_bytes = _inst_size_bytes(inst)
    imm_val = _parse_imm_value(imm_str.strip().lstrip("#"))
    word = _build_opword(inst, {})
    imm_bytes = _to_bytes_32(imm_val) if sz_bytes >= 4 else _to_bytes_16(imm_val)
    return _to_bytes_16(word) + imm_bytes


def _assemble_ea_to_sr_ccr(inst: str, src_str: str) -> bytes:
    """Assemble MOVE <ea>,CCR or MOVE <ea>,SR - source EA in encoding.

    Operand size derived from KB sizes field.
    """
    sz_bytes = _inst_size_bytes(inst)
    mode, reg, ext = parse_ea(src_str, sz_bytes)
    _require_allowed_ea_mode(inst, mode, reg, source=True)
    fields: FieldValues = {"MODE": mode, "REGISTER": reg}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word) + ext


def _assemble_sr_ccr_to_ea(inst: str, dst_str: str) -> bytes:
    """Assemble MOVE SR,<ea> or MOVE CCR,<ea> - destination EA in encoding.

    Operand size derived from KB sizes field.
    """
    sz_bytes = _inst_size_bytes(inst)
    mode, reg, ext = parse_ea(dst_str, sz_bytes)
    _require_allowed_ea_mode(inst, mode, reg, source=False)
    fields: FieldValues = {"MODE": mode, "REGISTER": reg}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word) + ext


def _assemble_direction_field(inst: str, form_idx: int, operands: Operands) -> bytes:
    """Assemble instruction with direction field (MOVE USP, MOVEM, MOVEC).

    Uses KB direction_field_values to determine the dr bit value from form index.
    """
    direction_form = runtime_m68k_asm.DIRECTION_FORM_VALUES.get(inst)
    if direction_form is None:
        raise ValueError(
            f"{inst}: no direction_field_values in KB")

    field_name, form_values = direction_form
    if form_idx >= len(form_values):
        raise ValueError(
            f"{inst}: form index {form_idx} not in "
            f"direction_field_values.form_field_value")
    dr_value = form_values[form_idx]

    # Determine which operand is the An register
    form_ops = runtime_m68k_asm.FORM_OPERAND_TYPES[inst][form_idx]

    # Find the non-special operand (the An register)
    an_str = None
    for i, op_type in enumerate(form_ops):
        if op_type == "an":
            an_str = operands[i]
            break
    if an_str is None:
        raise ValueError(
            f"{inst}: no 'an' operand in form {form_idx}")

    m = _RE_AN.match(an_str.strip())
    if m:
        an_reg = int(m.group(1))
    elif _RE_SP.match(an_str.strip()):
        an_reg = 7
    else:
        raise ValueError(
            f"{inst}: operand must be An, got {an_str!r}")

    fields: FieldValues = {field_name: dr_value, "REGISTER": an_reg}
    word = _build_opword(inst, fields)
    return _to_bytes_16(word)


# -- Main assembler entry point -------------------------------------------

def _split_operands(operand_str: str) -> Operands:
    """Split operand string on comma, respecting parentheses."""
    depth = 0
    parts: Operands = []
    current: list[str] = []
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


def _assemble_special_operand_form(mnemonic_str: str, operands: Operands) -> bytes | None:
    op_types = tuple(_classify_asm_operand(op) for op in operands)
    if not any(t in runtime_m68k_asm.SPECIAL_OPERAND_TYPES for t in op_types):
        return None

    resolved = _resolve_by_syntax_index(mnemonic_str.lower(), operands)
    if resolved is None:
        raise ValueError(
            f"No KB instruction for {mnemonic_str} with operand types {op_types}")
    sr_inst, form_idx = resolved
    form_ops = runtime_m68k_asm.FORM_OPERAND_TYPES[sr_inst][form_idx]

    if form_ops in (("imm", "ccr"), ("imm", "sr")):
        return _assemble_imm_to_sr_ccr(sr_inst, operands[0])
    if form_ops in (("ea", "ccr"), ("ea", "sr")):
        return _assemble_ea_to_sr_ccr(sr_inst, operands[0])
    if form_ops in (("sr", "ea"), ("ccr", "ea")):
        return _assemble_sr_ccr_to_ea(sr_inst, operands[1])
    if form_ops in (("usp", "an"), ("an", "usp")):
        return _assemble_direction_field(sr_inst, form_idx, operands)
    raise ValueError(f"Unhandled special operand form: {form_ops} for {sr_inst}")


def _assemble_special_mnemonic(inst: str, resolution: Resolution, operands: Operands) -> bytes | None:
    mnemonic = inst
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
    if mnemonic == "RTM":
        return _assemble_rn(inst, resolution, operands[0])
    if mnemonic in ("ABCD", "SBCD"):
        return _assemble_bcd(inst, resolution, operands[0], operands[1])
    if mnemonic in ("PACK", "UNPK"):
        return _assemble_pack_unpk(inst, resolution, operands[0], operands[1], operands[2])
    if mnemonic in ("ADDX", "SUBX"):
        return _assemble_addx_subx(inst, resolution, operands[0], operands[1])
    if mnemonic == "CMPM":
        return _assemble_cmpm(inst, resolution, operands[0], operands[1])
    return None


def _has_dual_ea_form(inst: str) -> bool:
    fields0 = runtime_m68k_asm.RAW_FIELDS[0][inst]
    return sum(1 for name, _, _, _ in fields0 if name == "MODE") >= 2


def _is_generic_ea_dn_form(inst: str) -> bool:
    fields0 = runtime_m68k_asm.RAW_FIELDS[0][inst]
    mode_count = sum(1 for name, _, _, _ in fields0 if name == "MODE")
    reg_count = sum(
        1
        for name, _, _, _ in fields0
        if name not in ("0", "1") and "REGISTER" in name.upper()
    )
    return mode_count == 1 and reg_count >= 2


def _assemble_single_operand(inst: str, resolution: Resolution, operands: Operands, pc: int) -> bytes:
    mnemonic = inst
    operand = operands[0]
    if operand.strip().startswith("#"):
        ir = runtime_m68k_asm.IMMEDIATE_RANGES.get(mnemonic)
        ir_field = ir[0] if ir is not None else ""
        enc_fields = {name for name, _, _, _ in runtime_m68k_asm.RAW_FIELDS[0][inst]}
        if ir_field and ir_field in enc_fields:
            return _assemble_opword_immediate(inst, resolution, operand)

    if runtime_m68k_asm.USES_LABELS[mnemonic]:
        return _assemble_branch(inst, resolution, operand, pc)
    if resolution["direction"] is not None:
        return _assemble_shift_mem(inst, resolution, operand)
    return _assemble_ea_single(inst, resolution, operand)


def _assemble_two_operands(inst: str, resolution: Resolution, operands: Operands, pc: int) -> bytes | None:
    mnemonic = inst
    src, dst = operands

    if mnemonic in ("BTST", "BCHG", "BCLR", "BSET"):
        if src.strip().startswith("#"):
            return _assemble_bit_imm(inst, resolution, src, dst)
        return _assemble_bit_reg(inst, resolution, src, dst)

    if runtime_m68k_asm.USES_LABELS[mnemonic]:
        if _RE_DN.match(src.strip()):
            return _assemble_dbcc(inst, resolution, src, dst, pc)
        return _assemble_branch(inst, resolution, src, pc)

    if resolution["direction"] is not None:
        return _assemble_shift_reg(inst, resolution, operands)

    if mnemonic == "LEA":
        return _assemble_lea_pea(inst, resolution, src, dst)

    if _has_dual_ea_form(inst):
        return _assemble_two_ea(inst, resolution, src, dst)

    if src.strip().startswith("#") and mnemonic in runtime_m68k_asm.OPMODE_TABLES_LIST:
        imm_mnemonic = runtime_m68k_asm.IMMEDIATE_ROUTING.get(mnemonic)
        if imm_mnemonic:
            imm_resolution: Resolution = {**resolution, "mnemonic": imm_mnemonic}
            return _assemble_immediate(imm_mnemonic, imm_resolution, src, dst)

    if mnemonic in runtime_m68k_asm.OPMODE_TABLES_LIST:
        return _assemble_opmode(inst, resolution, src, dst)

    if _is_generic_ea_dn_form(inst) and _RE_DN.match(dst.strip()):
        return _assemble_ea_dn(inst, resolution, src, dst)

    if src.strip().startswith("#"):
        ir = runtime_m68k_asm.IMMEDIATE_RANGES.get(mnemonic)
        if ir is not None and ir[0] == "DATA":
            return _assemble_quick(inst, resolution, src, dst)
        return _assemble_immediate(inst, resolution, src, dst)

    return None


def assemble_instruction(text: str, pc: int = 0) -> bytes:
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
    inst = resolution["mnemonic"]
    resolution["size"] = _defaulted_size_char(inst, resolution["size"])
    operands = _split_operands(operand_part) if operand_part else []

    if operands:
        result = _assemble_special_operand_form(mnemonic_str, operands)
        if result is not None:
            return result

    if not operands:
        return _assemble_no_operands(inst, resolution)

    result = _assemble_special_mnemonic(inst, resolution, operands)
    if result is not None:
        return result

    if inst == "PEA":
        return _assemble_lea_pea(inst, resolution, operands[0])

    if len(operands) == 1:
        return _assemble_single_operand(inst, resolution, operands, pc)

    if len(operands) == 2:
        result = _assemble_two_operands(inst, resolution, operands, pc)
        if result is not None:
            return result

    raise ValueError(f"Cannot assemble: {text!r}")


# -- CLI ------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
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
