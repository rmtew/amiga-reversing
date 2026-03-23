"""M68K disassembler targeting vasm-compatible Motorola syntax.

Decodes 68000 instructions from raw bytes and emits assembly text.
"""

import struct
from dataclasses import dataclass
from typing import TYPE_CHECKING

from m68k_kb import runtime_m68k_disasm
from m68k_kb.runtime_types import ConditionFamily, CpuHierarchy, OpmodeEntry

from .decode_errors import DecodeError
from .ea_extension import FullExtensionInfo, parse_full_extension

if TYPE_CHECKING:
    from disasm.decode import DecodedInstructionForEmit


CONDITION_FAMILIES: tuple[ConditionFamily, ...] = runtime_m68k_disasm.CONDITION_FAMILIES
DEFAULT_OPERAND_SIZE: str | None = runtime_m68k_disasm.DEFAULT_OPERAND_SIZE
CC_NAMES: tuple[str, ...] = runtime_m68k_disasm.CONDITION_CODES
CPU_HIERARCHY: CpuHierarchy = runtime_m68k_disasm.CPU_HIERARCHY
PROCESSOR_MINS: dict[str, str] = runtime_m68k_disasm.PROCESSOR_MINS
OPMODE_TABLES_BY_VALUE: dict[str, dict[int, OpmodeEntry]] = runtime_m68k_disasm.OPMODE_TABLES_BY_VALUE
FORM_OPERAND_TYPES: dict[str, tuple[tuple[str, ...], ...]] = runtime_m68k_disasm.FORM_OPERAND_TYPES
PMMU_CONDITION_CODES: tuple[str, ...] = runtime_m68k_disasm.PMMU_CONDITION_CODES


@dataclass
class Instruction:
    offset: int       # byte offset within hunk
    size: int         # total instruction size in bytes
    opcode: int       # first word
    text: str         # disassembled text (mnemonic + operands)
    raw: bytes        # raw instruction bytes
    opcode_text: str | None = None
    kb_mnemonic: str | None = None  # canonical KB mnemonic family
    decoded_operands: DecodedInstructionForEmit | None = None
    operand_size: str | None = None
    operand_texts: tuple[str, ...] | None = None
    operand_nodes: tuple[DecodedOperandNode, ...] | None = None


@dataclass(frozen=True)
class DecodedOperandNode:
    kind: str
    text: str
    value: int | None = None
    register: str | None = None
    target: int | None = None
    metadata: (
        DecodedBitfieldNodeMetadata
        | DecodedRegisterListNodeMetadata
        | DecodedRegisterPairNodeMetadata
        | DecodedBaseRegisterNodeMetadata
        | DecodedBaseDisplacementNodeMetadata
        | DecodedIndexedNodeMetadata
        | DecodedFullExtensionNodeMetadata
        | None
    ) = None


@dataclass(frozen=True, slots=True)
class DecodedBitfieldNodeMetadata:
    base_node: DecodedOperandNode
    offset_is_register: bool
    offset_value: int
    width_is_register: bool
    width_value: int


@dataclass(frozen=True, slots=True)
class DecodedRegisterListNodeMetadata:
    registers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DecodedRegisterPairNodeMetadata:
    registers: tuple[str, str]


@dataclass(frozen=True, slots=True)
class DecodedBaseRegisterNodeMetadata:
    base_register: str


@dataclass(frozen=True, slots=True)
class DecodedBaseDisplacementNodeMetadata:
    base_register: str
    displacement: int


@dataclass(frozen=True, slots=True)
class DecodedIndexedNodeMetadata:
    displacement: int
    index_register: str
    index_size: str
    index_is_addr: bool
    base_register: str | None = None


@dataclass(frozen=True, slots=True)
class DecodedFullExtensionNodeMetadata:
    base_register: str | None
    base_displacement: int | None
    index_register: str | None
    index_size: str | None
    index_scale: int | None
    memory_indirect: bool
    preindexed: bool
    postindexed: bool
    outer_displacement: int | None
    base_suppressed: bool
    index_suppressed: bool


@dataclass(frozen=True)
class DecodedInstructionText:
    text: str
    opcode_text: str
    operand_text: str | None
    operand_texts: tuple[str, ...]
    operand_size: str | None
    operand_nodes: tuple[DecodedOperandNode, ...]


def _register_node(register: str) -> DecodedOperandNode:
    return DecodedOperandNode(kind="register", text=register, register=register)


def _special_register_node(register: str) -> DecodedOperandNode:
    return DecodedOperandNode(kind="special_register", text=register, register=register)


def _predecrement_node(register: str) -> DecodedOperandNode:
    return DecodedOperandNode(
        kind="predecrement",
        text=f"-({register})",
        metadata=DecodedBaseRegisterNodeMetadata(base_register=register),
    )


def _postincrement_node(register: str) -> DecodedOperandNode:
    return DecodedOperandNode(
        kind="postincrement",
        text=f"({register})+",
        metadata=DecodedBaseRegisterNodeMetadata(base_register=register),
    )


def _base_displacement_node(register: str, displacement: int) -> DecodedOperandNode:
    return DecodedOperandNode(
        kind="base_displacement",
        text=f"{displacement}({register})",
        value=displacement,
        metadata=DecodedBaseDisplacementNodeMetadata(
            base_register=register,
            displacement=displacement,
        ),
    )


def _immediate_node(value: int, text: str) -> DecodedOperandNode:
    return DecodedOperandNode(kind="immediate", text=text, value=value)


def _branch_target_node(target: str) -> DecodedOperandNode:
    return DecodedOperandNode(kind="branch_target", text=target, target=int(target[1:], 16))


def _register_list_node(text: str, registers: list[str]) -> DecodedOperandNode:
    return DecodedOperandNode(
        kind="register_list",
        text=text,
        metadata=DecodedRegisterListNodeMetadata(registers=tuple(registers)),
    )


def _register_pair_node(text: str, registers: tuple[str, str]) -> DecodedOperandNode:
    return DecodedOperandNode(
        kind="register_pair",
        text=text,
        metadata=DecodedRegisterPairNodeMetadata(registers=registers),
    )


def _absolute_target_node(text: str, target: int) -> DecodedOperandNode:
    return DecodedOperandNode(kind="absolute_target", text=text, target=target)


def _bitfield_node(base_node: DecodedOperandNode, bitfield: DecodedBitfieldNodeMetadata,
                   text: str) -> DecodedOperandNode:
    return DecodedOperandNode(kind="bitfield_ea", text=text, metadata=bitfield)


def _brief_index_metadata(ext: int) -> tuple[int, str, str, bool]:
    bf = runtime_m68k_disasm.EA_BRIEF_FIELDS
    index_reg = _xf(ext, bf["REGISTER"])
    index_is_addr = _xf(ext, bf["D/A"]) == 1
    index_size = "l" if _xf(ext, bf["W/L"]) == 1 else "w"
    disp = _xf(ext, bf["DISPLACEMENT"])
    disp_width = bf["DISPLACEMENT"][2]
    if disp & (1 << (disp_width - 1)):
        disp -= (1 << disp_width)
    return disp, f"{'a' if index_is_addr else 'd'}{index_reg}", index_size, index_is_addr


def _full_extension_text(info: FullExtensionInfo) -> str:
    base_parts = []
    if info.base_displacement is not None:
        base_parts.append(str(info.base_displacement))
    if info.base_register is not None:
        base_parts.append(str(info.base_register))

    index_text = None
    if info.index_register is not None:
        index_text = f"{info.index_register}.{info.index_size}"
        if info.index_scale not in (None, 1):
            index_text = f"{index_text}*{info.index_scale}"

    if not info.memory_indirect:
        parts = list(base_parts)
        if index_text is not None:
            parts.append(index_text)
        if not parts:
            return "0"
        return f"({','.join(parts)})"

    if info.preindexed:
        parts = list(base_parts)
        if index_text is not None:
            parts.append(index_text)
        text = f"([{','.join(parts)}]"
    elif info.postindexed:
        text = f"([{','.join(base_parts)}]"
        if index_text is not None:
            text = f"{text},{index_text}"
    else:
        text = f"([{','.join(base_parts)}]"

    if info.outer_displacement is not None:
        text = f"{text},{info.outer_displacement}"
    return f"{text})"


def _full_extension_node(info: FullExtensionInfo, *, pc_relative: bool) -> DecodedOperandNode:
    kind = "pc_relative_indexed" if pc_relative else "indexed"
    if info.memory_indirect:
        kind = "pc_memory_indirect_indexed" if pc_relative else "memory_indirect_indexed"
    metadata = DecodedFullExtensionNodeMetadata(
        base_register=info.base_register,
        base_displacement=info.base_displacement,
        index_register=info.index_register,
        index_size=info.index_size,
        index_scale=info.index_scale,
        memory_indirect=info.memory_indirect,
        preindexed=info.preindexed,
        postindexed=info.postindexed,
        outer_displacement=info.outer_displacement,
        base_suppressed=info.base_suppressed,
        index_suppressed=info.index_suppressed,
    )
    return DecodedOperandNode(
        kind=kind,
        text=_full_extension_text(info),
        value=info.base_target if pc_relative else info.base_displacement,
        target=info.base_target if pc_relative else None,
        metadata=metadata,
    )


def _build_decoded_instruction_text(opcode_text: str,
                                    operand_texts: tuple[DecodedOperandNode, ...] = ()
                                    ) -> DecodedInstructionText:
    operand_size = _decode_operand_size(opcode_text)
    operand_nodes = operand_texts
    rendered_operand_texts = tuple(op.text for op in operand_nodes)
    operand_text = ",".join(rendered_operand_texts) if rendered_operand_texts else None
    if operand_text:
        if len(opcode_text) >= 8:
            text = f"{opcode_text} {operand_text}"
        else:
            text = f"{opcode_text:8s}{operand_text}"
    else:
        text = f"{opcode_text:8s}".rstrip()
    return DecodedInstructionText(
        text=text,
        opcode_text=opcode_text,
        operand_text=operand_text,
        operand_texts=rendered_operand_texts,
        operand_size=operand_size,
        operand_nodes=operand_nodes,
    )


SIZE_BYTE = 0
SIZE_WORD = 1
SIZE_LONG = 2

SIZE_SUFFIX = {SIZE_BYTE: ".b", SIZE_WORD: ".w", SIZE_LONG: ".l"}
SIZE_NAMES = {SIZE_BYTE: "byte", SIZE_WORD: "word", SIZE_LONG: "long"}
_SIZE_LETTER_TO_INT = {"b": SIZE_BYTE, "w": SIZE_WORD, "l": SIZE_LONG}

_SIZE_ENC_0 = 0
_SIZE_ENC_1 = 1
_SIZE_ENC_2 = 2
_SIZE_ENC_3 = 3


def _normalize_cpu(cpu_name: str | None) -> str:
    """Strip vasm -m prefix from cpu flag strings (e.g. '-m68000' -> '68000')."""
    if not cpu_name:
        return "68000"
    if cpu_name.startswith("-m"):
        cpu_name = cpu_name[2:]
    return cpu_name






















_SIZE_NAME_MAP = {"byte": SIZE_BYTE, "word": SIZE_WORD, "long": SIZE_LONG}


def _xf(op: int, field: tuple[int, int, int]) -> int:
    """Extract named field from opword/extword. field is (bit_hi, bit_lo, width)."""
    return (op >> field[1]) & ((1 << field[2]) - 1)









def _canonical_mnemonic(opcode_text: str) -> str:
    """Normalize a decoded opcode token to a KB mnemonic key."""
    if not opcode_text or any(ch.isspace() for ch in opcode_text) or "," in opcode_text:
        raise ValueError(f"Expected opcode token, got {opcode_text!r}")
    tok = opcode_text.lower()
    tok = tok.split(".", 1)[0]
    if tok in ("", "#"):
        return tok

    families = CONDITION_FAMILIES

    for fam in families:
        prefix, canonical_name, codes, match_numeric_suffix, excluded = fam
        canonical_name = str(canonical_name)
        if not prefix:
            continue
        if not tok.startswith(prefix):
            continue
        suffix = tok[len(prefix):]
        if suffix not in codes and not (match_numeric_suffix and suffix.startswith("#")):
            continue
        if tok in excluded:
            continue
        return canonical_name

    return tok


def _decode_operand_size(opcode_text: str) -> str | None:
    if not opcode_text:
        raise DecodeError("Instruction text is empty")
    if any(ch.isspace() for ch in opcode_text) or "," in opcode_text:
        raise DecodeError(f"Expected opcode token, got {opcode_text!r}")
    mnemonic = opcode_text.lower()
    _, sep, suffix = mnemonic.rpartition(".")
    if not sep:
        return DEFAULT_OPERAND_SIZE
    if suffix not in {"b", "w", "l", "s"}:
        raise DecodeError(f"Unsupported size suffix in instruction opcode {opcode_text!r}")
    return suffix


def _kb_mnemonic_matches(inst_name: str, canonical: str) -> bool:
    lowered = inst_name.lower()
    if lowered == canonical:
        return True
    if lowered.startswith(canonical + " "):
        return True
    return canonical in lowered.replace(",", " ").split()


def _encoding_match_literal_count(opcode: int, mnemonic: str, enc_idx: int) -> int | None:
    masks = runtime_m68k_disasm.ENCODING_MASKS[enc_idx]
    if mnemonic not in masks:
        return 0
    mask, value = masks[mnemonic]
    if (opcode & mask) != value:
        return None
    return int(mask.bit_count())


def _resolve_kb_mnemonic(opcode: int, opcode_text: str) -> str:
    canonical = _canonical_mnemonic(opcode_text)
    kb_index = runtime_m68k_disasm.MNEMONIC_INDEX
    matches: list[tuple[int, str]] = []
    for mnemonic in kb_index.get(canonical, ()):
        best_specificity = None
        for enc_idx in range(runtime_m68k_disasm.ENCODING_COUNTS[mnemonic]):
            literal_count = _encoding_match_literal_count(opcode, mnemonic, enc_idx)
            if literal_count is None:
                continue
            if best_specificity is None or literal_count > best_specificity:
                best_specificity = literal_count
        if best_specificity is not None:
            matches.append((best_specificity, mnemonic))
    if not matches:
        raise DecodeError(
            f"KB entry match count 0 for opcode ${opcode:04x} "
            f"and decoded opcode {opcode_text!r}")
    max_specificity = max(specificity for specificity, _ in matches)
    narrowed = []
    for specificity, name in matches:
        if specificity != max_specificity or name in narrowed:
            continue
        narrowed.append(name)
    exact = [name for name in narrowed if name.lower() == canonical]
    if len(exact) == 1:
        return exact[0]
    if len(narrowed) != 1:
        raise DecodeError(
            f"KB entry match count {len(narrowed)} for opcode ${opcode:04x} "
            f"and decoded opcode {opcode_text!r}")
    return narrowed[0]


def _ensure_cpu_supported(opcode_text: str, max_cpu: str | None) -> None:
    if not max_cpu:
        return

    max_cpu = _normalize_cpu(max_cpu)
    cpu_hier = CPU_HIERARCHY
    cpu_order = cpu_hier["order"]
    cpu_aliases = cpu_hier["aliases"]

    max_cpu = cpu_aliases.get(max_cpu, max_cpu)
    if max_cpu not in cpu_order:
        return

    canonical = _canonical_mnemonic(opcode_text)
    required_cpu = PROCESSOR_MINS.get(canonical)
    if required_cpu is None:
        return

    required_cpu = cpu_aliases.get(str(required_cpu), str(required_cpu))
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
        value = struct.unpack_from(">H", self.data, self.pos)[0]
        return int(value)

    def read_u16(self) -> int:
        val = struct.unpack_from(">H", self.data, self.pos)[0]
        self.pos += 2
        return int(val)

    def read_i16(self) -> int:
        val = struct.unpack_from(">h", self.data, self.pos)[0]
        self.pos += 2
        return int(val)

    def read_u32(self) -> int:
        val = struct.unpack_from(">I", self.data, self.pos)[0]
        self.pos += 4
        return int(val)

    def read_i32(self) -> int:
        val = struct.unpack_from(">i", self.data, self.pos)[0]
        self.pos += 4
        return int(val)


def _extract_size_bits(op: int, size_field: tuple[int, int, int],
                       sz_enc: tuple[int | None, int | None, int | None, int | None]) -> int:
    """Extract size bits from opword using KB field position and encoding values.

    The KB field width may be inflated by orphan expansion (e.g., 2 bits when only
    1 is needed).  Derive the effective width from the encoding's max value.
    """
    bit_hi = size_field[0]
    present = [idx for idx, size_val in enumerate(sz_enc) if size_val is not None]
    max_val = max(present) if present else 0
    eff_w = max(max_val.bit_length(), 1)
    return int((op >> (bit_hi - eff_w + 1)) & ((1 << eff_w) - 1))


def _reg_name(reg: int, is_addr: bool = False) -> str:
    if is_addr:
        return f"a{reg}" if reg < 7 else "sp"
    return f"d{reg}"


def _maybe_simple_ea_node(d: _Decoder, mode: int, reg: int, size: int,
                          pc_offset: int) -> DecodedOperandNode | None:
    if mode == 0:
        name = _reg_name(reg)
        return _register_node(name)
    if mode == 1:
        name = _reg_name(reg, True)
        return _register_node(name)
    if mode == 2:
        name = _reg_name(reg, True)
        return DecodedOperandNode(
            kind="indirect",
            text=f"({name})",
            metadata=DecodedBaseRegisterNodeMetadata(base_register=name),
        )
    if mode == 3:
        name = _reg_name(reg, True)
        return DecodedOperandNode(
            kind="postincrement",
            text=f"({name})+",
            metadata=DecodedBaseRegisterNodeMetadata(base_register=name),
        )
    if mode == 4:
        name = _reg_name(reg, True)
        return DecodedOperandNode(
            kind="predecrement",
            text=f"-({name})",
            metadata=DecodedBaseRegisterNodeMetadata(base_register=name),
        )
    if mode == 5:
        disp = d.read_i16()
        name = _reg_name(reg, True)
        return DecodedOperandNode(
            kind="base_displacement",
            text=f"{disp}({name})",
            value=disp,
            metadata=DecodedBaseDisplacementNodeMetadata(
                base_register=name,
                displacement=disp,
            ),
        )
    if mode == 6:
        ext = d.read_u16()
        if ext & 0x0100:
            info, d.pos = parse_full_extension(
                ext, d.data, d.pos,
                base_register=_reg_name(reg, True),
                pc_offset=None,
            )
            return _full_extension_node(info, pc_relative=False)
        disp, index_register, index_size, index_is_addr = _brief_index_metadata(ext)
        name = _reg_name(reg, True)
        return DecodedOperandNode(
            kind="indexed",
            text=f"{disp}({name},{index_register}.{index_size})",
            value=disp,
            metadata=DecodedIndexedNodeMetadata(
                base_register=name,
                displacement=disp,
                index_register=index_register,
                index_size=index_size,
                index_is_addr=index_is_addr,
            ),
        )
    if mode == 7 and reg == 0:
        addr = d.read_i16()
        text = (f"(${''.join(f'{b:02x}' for b in struct.pack('>h', addr))}).w"
                if addr < 0 else f"(${addr:04x}).w")
        return DecodedOperandNode(
            kind="absolute_target",
            text=text,
            target=addr & 0xFFFF,
        )
    if mode == 7 and reg == 1:
        addr = d.read_u32()
        return DecodedOperandNode(
            kind="absolute_target",
            text=f"${addr:08x}",
            target=addr,
        )
    if mode == 7 and reg == 2:
        disp = d.read_i16()
        target = pc_offset + 2 + disp
        return DecodedOperandNode(
            kind="pc_relative_target",
            text=f"{disp}(pc)",
            value=target,
            target=target,
        )
    if mode == 7 and reg == 3:
        ext = d.read_u16()
        if ext & 0x0100:
            info, d.pos = parse_full_extension(
                ext, d.data, d.pos,
                base_register="pc",
                pc_offset=pc_offset,
            )
            return _full_extension_node(info, pc_relative=True)
        disp, index_register, index_size, index_is_addr = _brief_index_metadata(ext)
        target = pc_offset + 2 + disp
        return DecodedOperandNode(
            kind="pc_relative_indexed",
            text=f"{disp}(pc,{index_register}.{index_size})",
            value=target,
            target=target,
            metadata=DecodedIndexedNodeMetadata(
                displacement=disp,
                index_register=index_register,
                index_size=index_size,
                index_is_addr=index_is_addr,
            ),
        )
    if mode == 7 and reg == 4:
        if size in (SIZE_BYTE, SIZE_WORD):
            imm = d.read_u16()
            if size == SIZE_BYTE:
                imm &= 0xFF
            return _immediate_node(imm, f"#${imm:x}")
        if size == SIZE_LONG:
            imm = d.read_u32()
            return _immediate_node(imm, f"#${imm:x}")
    return None


def _must_decode_ea_node(d: _Decoder, mode: int, reg: int, size: int,
                         pc_offset: int) -> DecodedOperandNode:
    node = _maybe_simple_ea_node(d, mode, reg, size, pc_offset)
    if node is None:
        raise DecodeError(f"unknown EA mode={mode} reg={reg}")
    return node


def _movem_registers(mask: int, direction: int) -> list[str]:
    """Convert MOVEM register mask to ordered register names.

    direction: 0 = register-to-memory (reversed bit order for predecrement)
               1 = memory-to-register (normal bit order)
    """
    masks = runtime_m68k_disasm.MOVEM_REG_MASKS
    table = masks["predecrement"] if direction == 0 else masks["normal"]
    regs = [table[i] for i in range(16) if mask & (1 << i)]
    dregs = sorted(int(r[1:]) for r in regs if r.startswith("d"))
    aregs = sorted(int(r[1:]) for r in regs if r.startswith("a"))
    return [f"d{reg}" for reg in dregs] + [f"a{reg}" for reg in aregs]


def _movem_reglist(mask: int, direction: int) -> str:
    return _compress_reglist(_movem_registers(mask, direction))


def _compress_reglist(regs: list[str]) -> str:
    """Compress register list into range notation."""
    if not regs:
        return ""
    # Group by type (d/a) and find ranges
    groups = []
    dregs = sorted([int(r[1]) for r in regs if r[0] == 'd'])
    aregs = sorted([int(r[1]) for r in regs if r[0] == 'a'])

    def ranges(nums: list[int], prefix: str) -> None:
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
        decoded_text = _decode_opcode(d, opcode, group, pc_offset)
    except struct.error as e:
        raise DecodeError(
            f"truncated instruction at offset=${pc_offset:06x} opcode=${opcode:04x}"
        ) from e
    _ensure_cpu_supported(decoded_text.opcode_text, max_cpu)

    size = d.pos - start
    raw = d.data[start:d.pos]
    kb_mnemonic = _resolve_kb_mnemonic(opcode, decoded_text.opcode_text)
    return Instruction(offset=pc_offset, size=size, opcode=opcode,
                       text=decoded_text.text, raw=raw,
                       opcode_text=decoded_text.opcode_text,
                       kb_mnemonic=kb_mnemonic,
                       operand_size=decoded_text.operand_size,
                       operand_texts=decoded_text.operand_texts,
                       operand_nodes=decoded_text.operand_nodes)


def _decode_opcode(d: _Decoder, op: int, group: int, pc: int) -> DecodedInstructionText:
    """Main opcode decoder."""

    if group == 0:
        return _decode_group0(d, op, pc)
    if group == 1:
        return _decode_move_byte(d, op, pc)
    if group == 2:
        return _decode_move_long(d, op, pc)
    if group == 3:
        return _decode_move_word(d, op, pc)
    if group == 4:
        return _decode_group4(d, op, pc)
    if group == 5:
        return _decode_group5(d, op, pc)
    if group == 6:
        return _decode_group6(d, op, pc)
    if group == 7:
        return _decode_moveq(d, op, pc)
    if group == 8:
        return _decode_group8(d, op, pc)
    if group == 9:
        return _decode_sub(d, op, pc)
    if group == 0xA:
        raise DecodeError(f"unsupported line-A op=${op:04x}")
    if group == 0xB:
        return _decode_cmp_eor(d, op, pc)
    if group == 0xC:
        return _decode_group_c(d, op, pc)
    if group == 0xD:
        return _decode_add(d, op, pc)
    if group == 0xE:
        return _decode_shift(d, op, pc)
    if group == 0xF:
        return _decode_line_f(d, op, pc)

    raise DecodeError(f"unhandled group {group}")


def _opmode_ea_to_dn(entry: OpmodeEntry) -> bool:
    """Return True if opmode table entry indicates ea->Dn direction, False for Dn->ea."""
    if entry.ea_is_source is not None:
        return bool(entry.ea_is_source)
    op_text_raw = entry.description
    op_text = "" if op_text_raw is None else op_text_raw
    # Multi-column format: "< ea > OP Dn -> Dn" vs "Dn OP < ea > -> < ea >"
    if "->" in op_text:
        dest = op_text.split("->")[-1].strip()
        return "Dn" in dest and "ea" not in dest.lower()
    # Arrow may be missing from PDF extraction; determine from operand order
    if op_text:
        return op_text.lstrip().startswith("<")
    # Value-description format: "memory to register" vs "register to memory"
    desc = op_text.lower()
    return "to register" in desc


# --- Group decoders ---

def _decode_group0(d: _Decoder, op: int, pc: int) -> DecodedInstructionText:
    """Bit operations and immediate ops (ORI, ANDI, SUBI, ADDI, EORI, CMPI, BTST, etc.)"""
    _masks = runtime_m68k_disasm.ENCODING_MASKS[0]

    # Derive bit-op name table from KB: extract bits 7:6 from each instruction's val
    _bitop_names, _bitop_field = runtime_m68k_disasm.BITOP_NAMES

    _fields = runtime_m68k_disasm.FIELD_MAPS[0]

    # MOVEP - detect via KB mask/val + opmode validation
    _movep_m, _movep_v = _masks["MOVEP"]
    _movep_opm = OPMODE_TABLES_BY_VALUE["MOVEP"]
    if (op & _movep_m) == _movep_v:
        _movep_f = _fields["MOVEP"]
        opmode = _xf(op, _movep_f["OPMODE"])
        if opmode in _movep_opm:
            dreg = _xf(op, _movep_f["DATA REGISTER"])
            areg = _xf(op, _movep_f["ADDRESS REGISTER"])
            disp = d.read_i16()
            entry = _movep_opm[opmode]
            size_name = entry.size
            assert size_name is not None
            sfx = f".{size_name}"
            desc = (entry.description or "").lower()
            disp_node = _base_displacement_node(f"a{areg}", disp)
            if "memory to register" in desc:
                return _build_decoded_instruction_text(
                    f"movep{sfx}", (disp_node, _register_node(f"d{dreg}")))
            return _build_decoded_instruction_text(
                f"movep{sfx}", (_register_node(f"d{dreg}"), disp_node))

    if op & 0x0100:
        # Dynamic bit operations: BTST/BCHG/BCLR/BSET Dn,<ea>
        _dest_reg = runtime_m68k_disasm.DEST_REG_FIELD
        _btst_f = _fields["BTST"]
        reg = _xf(op, _dest_reg["BTST"])
        mode = _xf(op, _btst_f["MODE"])
        ea_reg = _xf(op, _btst_f["REGISTER"])
        bit_op = _xf(op, _bitop_field)
        sz = SIZE_LONG if mode == 0 else SIZE_BYTE
        ea_node = _must_decode_ea_node(d, mode, ea_reg, sz, pc)
        return _build_decoded_instruction_text(
            _bitop_names[bit_op], (_register_node(f"d{reg}"), ea_node))
    # Static bit ops or immediate ops
    # Use ORI SIZE field for size_bits; imm_names returns field for top_bits
    imm_names, _imm_field = runtime_m68k_disasm.IMM_NAMES
    _ori_f = _fields["ORI"]
    top_bits = _xf(op, _imm_field)
    size_bits = _xf(op, _ori_f["SIZE"])

    if top_bits == 4:
        # Static bit operations - MODE/REGISTER same positions as dynamic BTST
        _btst_f = _fields["BTST"]
        mode = _xf(op, _btst_f["MODE"])
        ea_reg = _xf(op, _btst_f["REGISTER"])
        bit_op = _xf(op, _bitop_field)
        bit_num = d.read_u16() & 0xFF
        sz = SIZE_LONG if mode == 0 else SIZE_BYTE
        ea_node = _must_decode_ea_node(d, mode, ea_reg, sz, pc)
        return _build_decoded_instruction_text(
            _bitop_names[bit_op], (_immediate_node(bit_num, f"#{bit_num}"), ea_node))

    # CMP2/CHK2/CAS (68020+): size_bits==3 distinguishes from immediate ops
    # Note: CAS.L also has top_bits==7, so CAS must be checked before MOVES.
    if size_bits == 3:
        _m_cmp, _v_cmp = _masks["CMP2"]    # KeyError -> regenerate KB JSON
        _m_cas, _v_cas = _masks["CAS CAS2"]
        if (op & _m_cmp) == _v_cmp:
            # CMP2/CHK2: SIZE from KB field map (valid: 0,1,2 only)
            # ss==3 means this is RTM, not CMP2 - fall through
            _cmp2_f = _fields["CMP2"]
            ss = _xf(op, _cmp2_f["SIZE"])
            if ss <= 2:
                sfx = SIZE_SUFFIX[ss]
                mode = _xf(op, _cmp2_f["MODE"])
                reg = _xf(op, _cmp2_f["REGISTER"])
                ext = d.read_u16()
                # Extension word fields from KB (D/A + REGISTER combined span)
                _ef = runtime_m68k_disasm.FIELD_MAPS[1]["CMP2"]
                ad_hi = _ef["D/A"][0]
                reg_lo = _ef["REGISTER"][1]
                reg_span = _ef["D/A"][1] - reg_lo + 1
                is_an = (ext >> ad_hi) & 1
                gpreg = (ext >> reg_lo) & ((1 << reg_span) - 1)
                # CHK2 vs CMP2: compute ext mask/val from fixed bits in
                # CHK2's encoding[1] to find the distinguishing bit
                chk2_ext_mask, chk2_ext_val = runtime_m68k_disasm.ENCODING_MASKS[1]["CHK2"]
                chk2 = (ext & chk2_ext_mask) == chk2_ext_val
                name = "chk2" if chk2 else "cmp2"
                gp_name = f"{'a' if is_an else 'd'}{gpreg}"
                ea_node = _must_decode_ea_node(d, mode, reg, ss, pc)
                return _build_decoded_instruction_text(
                    f"{name}{sfx}", (ea_node, _register_node(gp_name)))
        if (op & _m_cas) == _v_cas:
            # Size encoding parsed from KB field description
            _cas_f = _fields["CAS CAS2"]
            cas_sz = runtime_m68k_disasm.SIZE_ENCODINGS_DISASM["CAS CAS2"]
            ss_raw = _xf(op, _cas_f["SIZE"])
            if not (0 <= ss_raw < len(cas_sz)) or cas_sz[ss_raw] is None:
                raise DecodeError(f"unknown CAS size={ss_raw}")
            sz_entry = cas_sz[ss_raw]
            assert sz_entry is not None
            sz = sz_entry
            sfx = SIZE_SUFFIX[sz]
            mode = _xf(op, _cas_f["MODE"])
            reg = _xf(op, _cas_f["REGISTER"])
            ext = d.read_u16()
            # Extension word field positions from KB
            _cas_ef = runtime_m68k_disasm.FIELD_MAPS[1]["CAS CAS2"]
            du_lo = _cas_ef["Du"][1]
            du_w = _cas_ef["Du"][2]
            dc_lo = _cas_ef["Dc"][1]
            dc_w = _cas_ef["Dc"][2]
            dc = (ext >> dc_lo) & ((1 << dc_w) - 1)
            du = (ext >> du_lo) & ((1 << du_w) - 1)
            ea_node = _must_decode_ea_node(d, mode, reg, sz, pc)
            return _build_decoded_instruction_text(
                f"cas{sfx}", (_register_node(f"d{dc}"), _register_node(f"d{du}"), ea_node))

    # MOVES (68010+): top_bits=7, size_bits in 0-2 (CAS.L already caught above)
    if top_bits == 7:
        _m, _v = _masks["MOVES"]  # KeyError -> regenerate m68k_instructions.json
        if (op & _m) == _v:
            sz = size_bits
            if sz > 2:
                raise DecodeError(f"unknown group0 moves sz={sz}")
            sfx = SIZE_SUFFIX[sz]
            _moves_f = _fields["MOVES"]
            mode = _xf(op, _moves_f["MODE"])
            reg = _xf(op, _moves_f["REGISTER"])
            ext = d.read_u16()
            _ef = runtime_m68k_disasm.FIELD_MAPS[1]["MOVES"]
            # A/D flag at A/D.bit_hi; register spans A/D.bit_lo..REGISTER.bit_lo
            _ad_hi = _ef["A/D"][0]
            _reg_lo = _ef["REGISTER"][1]
            _reg_span = _ef["A/D"][1] - _reg_lo + 1
            _dr_hi = _ef["dr"][0]
            is_an = (ext >> _ad_hi) & 1
            gpreg = (ext >> _reg_lo) & ((1 << _reg_span) - 1)
            rw = (ext >> _dr_hi) & 1   # 1 = Rn->EA (write), 0 = EA->Rn (read)
            gp_name = f"{'a' if is_an else 'd'}{gpreg}"
            ea_node = _must_decode_ea_node(d, mode, reg, sz, pc)
            if rw:
                return _build_decoded_instruction_text(
                    f"moves{sfx}", (_register_node(gp_name), ea_node))
            return _build_decoded_instruction_text(
                f"moves{sfx}", (ea_node, _register_node(gp_name)))
        raise DecodeError(f"unknown group0 top={top_bits}")

    # CALLM / RTM (68020) - detect via KB mask/val
    _m_rtm, _v_rtm = _masks["RTM"]
    if (op & _m_rtm) == _v_rtm:
        _rtm_f = _fields["RTM"]
        da = _xf(op, _rtm_f["D/A"])
        ea_reg = _xf(op, _rtm_f["REGISTER"])
        if da == 0:
            return _build_decoded_instruction_text("rtm", (_register_node(f"d{ea_reg}"),))
        return _build_decoded_instruction_text("rtm", (_register_node(f"a{ea_reg}"),))
    _m_callm, _v_callm = _masks["CALLM"]
    if (op & _m_callm) == _v_callm:
        _callm_f = _fields["CALLM"]
        mode = _xf(op, _callm_f["MODE"])
        ea_reg = _xf(op, _callm_f["REGISTER"])
        ext = d.read_u16()
        _callm_ef = runtime_m68k_disasm.FIELD_MAPS[1]["CALLM"]
        _ac = _callm_ef["ARGUMENT COUNT"]
        arg_count = (ext >> _ac[1]) & ((1 << _ac[2]) - 1)
        ea_node = _must_decode_ea_node(d, mode, ea_reg, SIZE_LONG, pc)
        return _build_decoded_instruction_text(
            "callm", (_immediate_node(arg_count, f"#{arg_count}"), ea_node))

    # Immediate operations - name table derived from KB encoding vals
    if top_bits not in imm_names:
        raise DecodeError(f"unknown group0 top={top_bits}")

    name = imm_names[top_bits]
    # Use ORI fields as representative - all imm ops share MODE/REGISTER positions
    _imm_f = _fields["ORI"]
    mode = _xf(op, _imm_f["MODE"])
    ea_reg = _xf(op, _imm_f["REGISTER"])

    # Special cases: ORI/ANDI/EORI to CCR/SR - detect via KB mask/val
    for _sr_suffix, _sr_name, _sr_size in (("CCR", "ccr", "b"), ("SR", "sr", "w")):
        _sr_key = f"{name.upper()} to {_sr_suffix}"
        _sr_mv = _masks.get(_sr_key)
        if _sr_mv is not None and (op & _sr_mv[0]) == _sr_mv[1]:
            imm = d.read_u16()
            if _sr_size == "b":
                imm &= 0xFF
            return _build_decoded_instruction_text(
                f"{name}.{_sr_size}",
                (_immediate_node(imm, f"#${imm:x}"), _special_register_node(_sr_name)))

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

    ea_node = _must_decode_ea_node(d, mode, ea_reg, sz, pc)
    return _build_decoded_instruction_text(
        f"{name}{sfx}", (_immediate_node(imm, imm_s), ea_node))



def _decode_move(d: _Decoder, op: int, pc: int, size: int) -> DecodedInstructionText:
    """Decode MOVE/MOVEA instruction."""
    dst_reg_f, dst_mode_f, src_mode_f, src_reg_f = runtime_m68k_disasm.MOVE_FIELDS
    src_mode = _xf(op, src_mode_f)
    src_reg = _xf(op, src_reg_f)
    dst_reg = _xf(op, dst_reg_f)
    dst_mode = _xf(op, dst_mode_f)
    sfx = SIZE_SUFFIX[size]

    src_node = _must_decode_ea_node(d, src_mode, src_reg, size, pc)

    if dst_mode == 1:
        # MOVEA
        dst = _reg_name(dst_reg, True)
        return _build_decoded_instruction_text(
            f"movea{sfx}", (src_node, _register_node(dst)))

    dst_node = _must_decode_ea_node(d, dst_mode, dst_reg, size, pc)
    return _build_decoded_instruction_text(f"move{sfx}", (src_node, dst_node))


def _decode_move_byte(d: _Decoder, op: int, pc: int) -> DecodedInstructionText:
    return _decode_move(d, op, pc, SIZE_BYTE)

def _decode_move_long(d: _Decoder, op: int, pc: int) -> DecodedInstructionText:
    return _decode_move(d, op, pc, SIZE_LONG)

def _decode_move_word(d: _Decoder, op: int, pc: int) -> DecodedInstructionText:
    return _decode_move(d, op, pc, SIZE_WORD)


def _decode_group4(d: _Decoder, op: int, pc: int) -> DecodedInstructionText:
    """Miscellaneous: LEA, PEA, CLR, NEG, NOT, TST, MOVEM, JMP, JSR, etc."""
    _masks = runtime_m68k_disasm.ENCODING_MASKS[0]
    _fields = runtime_m68k_disasm.FIELD_MAPS[0]
    _dest_reg = runtime_m68k_disasm.DEST_REG_FIELD

    # --- Fixed-opword instructions (mask=0xFFFF in KB) ---
    # Build lookup from all KB instructions whose mask covers all 16 bits
    _fixed = runtime_m68k_disasm.FIXED_OPCODES
    if op in _fixed:
        mn = _fixed[op]
        mn_l = mn.lower()
        if mn in ("STOP",):
            imm = d.read_u16()
            return _build_decoded_instruction_text(mn_l, (_immediate_node(imm, f"#${imm:04x}"),))
        if mn in ("RTD",):
            disp = d.read_i16()
            return _build_decoded_instruction_text(mn_l, (_immediate_node(disp, f"#{disp}"),))
        return _build_decoded_instruction_text(mn_l)

    # TRAP
    _m, _v = _masks["TRAP"]
    if (op & _m) == _v:
        vec = _xf(op, _fields["TRAP"]["VECTOR"])
        return _build_decoded_instruction_text("trap", (_immediate_node(vec, f"#{vec}"),))

    # LINK.L (68020+) - encoding[2] in KB; must check before LINK.W
    _m2, _v2 = runtime_m68k_disasm.ENCODING_MASKS[2]["LINK"]
    if (op & _m2) == _v2:
        areg = _xf(op, _fields["LINK"]["REGISTER"])
        disp = d.read_i32()
        return _build_decoded_instruction_text(
            "link.l",
            (_register_node(_reg_name(areg, True)), _immediate_node(disp & 0xFFFFFFFF, f"#{disp}")))

    # MULU.L/MULS.L (68020+) - enc[1] opword, enc[2] ext word
    _enc1 = runtime_m68k_disasm.ENCODING_MASKS[1]
    _enc2 = runtime_m68k_disasm.ENCODING_MASKS[2]
    _ef1 = runtime_m68k_disasm.FIELD_MAPS[1]
    _ef2 = runtime_m68k_disasm.FIELD_MAPS[2]

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
                ea_node = _must_decode_ea_node(d, mode, ea_reg, SIZE_LONG, pc)
                name = _mn.lower()
                if size_bit:
                    return _build_decoded_instruction_text(
                        f"{name}.l",
                        (ea_node, _register_pair_node(f"d{dh}:d{dl}", (f"d{dh}", f"d{dl}"))),
                    )
                return _build_decoded_instruction_text(
                    f"{name}.l",
                    (ea_node, _register_node(f"d{dl}")),
                )
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
                ea_node = _must_decode_ea_node(d, mode, ea_reg, SIZE_LONG, pc)
                if size_bit:
                    return _build_decoded_instruction_text(
                        f"{_name_s}.l",
                        (ea_node, _register_pair_node(f"d{dr}:d{dq}", (f"d{dq}", f"d{dr}"))),
                    )
                if dq != dr:
                    return _build_decoded_instruction_text(
                        f"{_name_l}.l",
                        (ea_node, _register_pair_node(f"d{dr}:d{dq}", (f"d{dq}", f"d{dr}"))),
                    )
                return _build_decoded_instruction_text(
                    f"{_name_s}.l",
                    (ea_node, _register_node(f"d{dq}")),
                )
        raise DecodeError(f"DIV.L ext word ${ext:04x} matches neither DIVS nor DIVU")

    # LINK.W
    _m, _v = _masks["LINK"]
    if (op & _m) == _v:
        areg = _xf(op, _fields["LINK"]["REGISTER"])
        disp = d.read_i16()
        return _build_decoded_instruction_text(
            "link", (_register_node(_reg_name(areg, True)), _immediate_node(disp & 0xFFFFFFFF, f"#{disp}")))

    # UNLK
    _m, _v = _masks["UNLK"]
    if (op & _m) == _v:
        areg = _xf(op, _fields["UNLK"]["REGISTER"])
        return _build_decoded_instruction_text("unlk", (_register_node(_reg_name(areg, True)),))

    # MOVE USP - dr field from KB
    _m, _v = _masks["MOVE USP"]
    if (op & _m) == _v:
        _usp_f = _fields["MOVE USP"]
        areg = _xf(op, _usp_f["REGISTER"])
        dr = _xf(op, _usp_f["dr"])
        if dr:
            return _build_decoded_instruction_text(
                "move.l", (_special_register_node("usp"), _register_node(_reg_name(areg, True))))
        return _build_decoded_instruction_text(
            "move.l", (_register_node(_reg_name(areg, True)), _special_register_node("usp")))

    # JSR
    _m, _v = _masks["JSR"]
    if (op & _m) == _v:
        _jsr_f = _fields["JSR"]
        mode = _xf(op, _jsr_f["MODE"])
        reg = _xf(op, _jsr_f["REGISTER"])
        ea_node = _must_decode_ea_node(d, mode, reg, SIZE_LONG, pc)
        return _build_decoded_instruction_text("jsr", (ea_node,))

    # JMP
    _m, _v = _masks["JMP"]
    if (op & _m) == _v:
        _jmp_f = _fields["JMP"]
        mode = _xf(op, _jmp_f["MODE"])
        reg = _xf(op, _jmp_f["REGISTER"])
        ea_node = _must_decode_ea_node(d, mode, reg, SIZE_LONG, pc)
        return _build_decoded_instruction_text("jmp", (ea_node,))

    # LEA
    _m, _v = _masks["LEA"]
    if (op & _m) == _v:
        areg = _xf(op, _dest_reg["LEA"])
        _lea_f = _fields["LEA"]
        mode = _xf(op, _lea_f["MODE"])
        reg = _xf(op, _lea_f["REGISTER"])
        ea_node = _must_decode_ea_node(d, mode, reg, SIZE_LONG, pc)
        return _build_decoded_instruction_text(
            "lea", (ea_node, _register_node(_reg_name(areg, True))))

    # BKPT (68010+)
    _m, _v = _masks["BKPT"]
    if (op & _m) == _v:
        vec = _xf(op, _fields["BKPT"]["VECTOR"])
        return _build_decoded_instruction_text("bkpt", (_immediate_node(vec, f"#{vec}"),))

    # SWAP (must be before PEA - both match similar patterns but SWAP has mode=0)
    _m, _v = _masks["SWAP"]
    if (op & _m) == _v:
        return _build_decoded_instruction_text(
            "swap", (_register_node(f"d{_xf(op, _fields['SWAP']['REGISTER'])}"),))

    # EXT, EXTB (must be before MOVEM - EXT has mode=0)
    _m, _v = _masks["EXT, EXTB"]
    if (op & _m) == _v:
        _ext_f = _fields["EXT, EXTB"]
        opmode = _xf(op, _ext_f["OPMODE"])
        dreg = _xf(op, _ext_f["REGISTER"])
        _ext_opm = OPMODE_TABLES_BY_VALUE["EXT, EXTB"]
        if opmode in _ext_opm:
            entry = _ext_opm[opmode]
    # Description tells us the output: byte->word = ext.w, word->long = ext.l, byte->long = extb.l
            desc = (entry.description or "").lower()
            if "byte" in desc and "to long" in desc:
                return _build_decoded_instruction_text("extb.l", (_register_node(f"d{dreg}"),))
            if "to long" in desc:
                return _build_decoded_instruction_text("ext.l", (_register_node(f"d{dreg}"),))
            return _build_decoded_instruction_text("ext.w", (_register_node(f"d{dreg}"),))

    # PEA
    _m, _v = _masks["PEA"]
    if (op & _m) == _v:
        _pea_f = _fields["PEA"]
        mode = _xf(op, _pea_f["MODE"])
        reg = _xf(op, _pea_f["REGISTER"])
        ea_node = _must_decode_ea_node(d, mode, reg, SIZE_LONG, pc)
        return _build_decoded_instruction_text("pea", (ea_node,))

    # MOVEM (mode >= 2 guaranteed now since EXT caught mode=0)
    _m, _v = _masks["MOVEM"]
    if (op & _m) == _v:
        _of = _fields["MOVEM"]
        direction = _xf(op, _of["dr"])  # 0=reg-to-mem, 1=mem-to-reg
        sz_enc = runtime_m68k_disasm.SIZE_ENCODINGS_DISASM["MOVEM"]
        sz_bits = _extract_size_bits(op, _of["SIZE"], sz_enc)
        sz = sz_enc[sz_bits]
        assert sz is not None
        sfx = SIZE_SUFFIX[sz]
        mode = _xf(op, _of["MODE"])
        reg = _xf(op, _of["REGISTER"])
        mask = d.read_u16()

        is_predec = (mode == 4)
        reg_direction = 0 if is_predec else 1
        reglist_registers = _movem_registers(mask, reg_direction)
        reglist = _movem_reglist(mask, reg_direction)
        reglist_node = _register_list_node(reglist, reglist_registers)
        ea_node = _must_decode_ea_node(d, mode, reg, sz, pc)

        if direction == 0:
            return _build_decoded_instruction_text(f"movem{sfx}", (reglist_node, ea_node))
        return _build_decoded_instruction_text(f"movem{sfx}", (ea_node, reglist_node))

    # CLR, NEG, NEGX, NOT - mask/val from KB
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
            ea_node = _must_decode_ea_node(d, mode, reg, sz, pc)
            return _build_decoded_instruction_text(f"{_mn.lower()}{sfx}", (ea_node,))

    # TST
    _m, _v = _masks["TST"]
    if (op & _m) == _v:
        _tst_f = _fields["TST"]
        sz = _xf(op, _tst_f["SIZE"])
        if sz < 3:
            sfx = SIZE_SUFFIX[sz]
            mode = _xf(op, _tst_f["MODE"])
            reg = _xf(op, _tst_f["REGISTER"])
            ea_node = _must_decode_ea_node(d, mode, reg, sz, pc)
            return _build_decoded_instruction_text(f"tst{sfx}", (ea_node,))

    # TAS
    _m, _v = _masks["TAS"]
    if (op & _m) == _v:
        _tas_f = _fields["TAS"]
        mode = _xf(op, _tas_f["MODE"])
        reg = _xf(op, _tas_f["REGISTER"])
        ea_node = _must_decode_ea_node(d, mode, reg, SIZE_BYTE, pc)
        return _build_decoded_instruction_text("tas", (ea_node,))

    # NBCD
    _m, _v = _masks["NBCD"]
    if (op & _m) == _v:
        _nbcd_f = _fields["NBCD"]
        mode = _xf(op, _nbcd_f["MODE"])
        reg = _xf(op, _nbcd_f["REGISTER"])
        ea_node = _must_decode_ea_node(d, mode, reg, SIZE_BYTE, pc)
        return _build_decoded_instruction_text("nbcd", (ea_node,))

    # MOVE from SR
    _m, _v = _masks["MOVE from SR"]
    if (op & _m) == _v:
        _msr_f = _fields["MOVE from SR"]
        mode = _xf(op, _msr_f["MODE"])
        reg = _xf(op, _msr_f["REGISTER"])
        ea_node = _must_decode_ea_node(d, mode, reg, SIZE_WORD, pc)
        return _build_decoded_instruction_text("move.w", (_special_register_node("sr"), ea_node))

    # MOVE from CCR (68010+)
    _m, _v = _masks["MOVE from CCR"]
    if (op & _m) == _v:
        _mccr_f = _fields["MOVE from CCR"]
        mode = _xf(op, _mccr_f["MODE"])
        reg = _xf(op, _mccr_f["REGISTER"])
        ea_node = _must_decode_ea_node(d, mode, reg, SIZE_WORD, pc)
        return _build_decoded_instruction_text("move.w", (_special_register_node("ccr"), ea_node))

    # MOVE to CCR
    _m, _v = _masks["MOVE to CCR"]
    if (op & _m) == _v:
        _mtccr_f = _fields["MOVE to CCR"]
        mode = _xf(op, _mtccr_f["MODE"])
        reg = _xf(op, _mtccr_f["REGISTER"])
        ea_node = _must_decode_ea_node(d, mode, reg, SIZE_WORD, pc)
        return _build_decoded_instruction_text("move.w", (ea_node, _special_register_node("ccr")))

    # MOVE to SR
    _m, _v = _masks["MOVE to SR"]
    if (op & _m) == _v:
        _mtsr_f = _fields["MOVE to SR"]
        mode = _xf(op, _mtsr_f["MODE"])
        reg = _xf(op, _mtsr_f["REGISTER"])
        ea_node = _must_decode_ea_node(d, mode, reg, SIZE_WORD, pc)
        return _build_decoded_instruction_text("move.w", (ea_node, _special_register_node("sr")))

    # CHK (word and long) - broad mask, must be checked after specific instructions
    _m, _v = _masks["CHK"]
    if (op & _m) == _v:
        dreg = _xf(op, _dest_reg["CHK"])
        _of = _fields["CHK"]
        mode = _xf(op, _of["MODE"])
        reg = _xf(op, _of["REGISTER"])
        sz_lo = _of["SIZE"][1]
        sz_w = _of["SIZE"][2]
        sz_bits = (op >> sz_lo) & ((1 << sz_w) - 1)
        chk_sz = runtime_m68k_disasm.SIZE_ENCODINGS_DISASM["CHK"]
        if 0 <= sz_bits < len(chk_sz) and chk_sz[sz_bits] is not None:
            sz = chk_sz[sz_bits]
            assert sz is not None
            sfx = SIZE_SUFFIX[sz]
            ea_node = _must_decode_ea_node(d, mode, reg, sz, pc)
            return _build_decoded_instruction_text(
                f"chk{sfx}", (ea_node, _register_node(f"d{dreg}")))

    # MOVEC (68010+) - extension word fields from KB
    _m, _v = _masks["MOVEC"]
    if (op & _m) == _v:
        ext = d.read_u16()
        _movec_f = _fields["MOVEC"]
        dr = _xf(op, _movec_f["dr"])  # 0 = Rc->Rn, 1 = Rn->Rc
        _ef = runtime_m68k_disasm.FIELD_MAPS[1]["MOVEC"]
        # A/D flag at A/D.bit_hi; register spans A/D.bit_lo..REGISTER.bit_lo
        ad_hi = _ef["A/D"][0]
        reg_lo = _ef["REGISTER"][1]
        reg_span = _ef["A/D"][1] - reg_lo + 1
        ctrl_lo = _ef["CONTROL REGISTER"][1]
        ctrl_w = _ef["CONTROL REGISTER"][2]
        is_an = (ext >> ad_hi) & 1
        gpreg = (ext >> reg_lo) & ((1 << reg_span) - 1)
        ctrl = (ext >> ctrl_lo) & ((1 << ctrl_w) - 1)
        _ctrl_regs = runtime_m68k_disasm.CONTROL_REGISTERS
        if ctrl not in _ctrl_regs:
            raise DecodeError(f"unknown MOVEC control register ${ctrl:03x}")
        ctrl_name = _ctrl_regs[ctrl]
        gp_name = f"{'a' if is_an else 'd'}{gpreg}"
        if dr == 0:
            return _build_decoded_instruction_text(
                "movec", (_special_register_node(ctrl_name), _register_node(gp_name)))
        return _build_decoded_instruction_text(
            "movec", (_register_node(gp_name), _special_register_node(ctrl_name)))

    raise DecodeError(f"unknown group4 op=${op:04x}")


def _decode_group5(d: _Decoder, op: int, pc: int) -> DecodedInstructionText:
    """ADDQ, SUBQ, Scc, DBcc"""
    _fields = runtime_m68k_disasm.FIELD_MAPS[0]
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
            cc = CC_NAMES[condition]
            _dbcc_f = _fields["DBcc"]
            reg = _xf(op, _dbcc_f["REGISTER"])
            return _build_decoded_instruction_text(
                f"db{cc}", (_register_node(f"d{reg}"), _branch_target_node(target)))

    # TRAPcc (68020+) - mode=7, reg from KB opmode_table
        if mode == 7:
            _trapcc_opm = OPMODE_TABLES_BY_VALUE["TRAPcc"]
            if reg in _trapcc_opm:
                cc = CC_NAMES[condition]
                entry = _trapcc_opm[reg]
                sz = entry.size
                if sz == "w":
                    imm = d.read_u16()
                    return _build_decoded_instruction_text(
                        f"trap{cc}.w", (_immediate_node(imm, f"#${imm:04x}"),))
                if sz == "l":
                    imm = d.read_u32()
                    return _build_decoded_instruction_text(
                        f"trap{cc}.l", (_immediate_node(imm, f"#${imm:08x}"),))
                return _build_decoded_instruction_text(f"trap{cc}")

        # Scc (all other mode/reg combos including mode=7 absolute addressing)
        ea_node = _must_decode_ea_node(d, mode, reg, SIZE_BYTE, pc)
        cc = CC_NAMES[condition]
        return _build_decoded_instruction_text(f"s{cc}", (ea_node,))
    # ADDQ / SUBQ - discriminate via KB mask/val
    _masks = runtime_m68k_disasm.ENCODING_MASKS[0]
    _subq_m, _subq_v = _masks["SUBQ"]
    data = _xf(op, _addq_f["DATA"])
    if data == 0:
        zero_means = runtime_m68k_disasm.ADDQ_ZERO_MEANS
        assert zero_means is not None, "KB missing ADDQ zero_means value"
        data = zero_means
    is_sub = (op & _subq_m) == _subq_v
    name = "subq" if is_sub else "addq"
    sfx = SIZE_SUFFIX[size_bits]
    mode = _xf(op, _addq_f["MODE"])
    reg = _xf(op, _addq_f["REGISTER"])
    ea_node = _must_decode_ea_node(d, mode, reg, size_bits, pc)
    return _build_decoded_instruction_text(
        f"{name}{sfx}", (_immediate_node(data, f"#{data}"), ea_node))


def _decode_group6(d: _Decoder, op: int, pc: int) -> DecodedInstructionText:
    """Bcc, BSR, BRA"""
    _masks = runtime_m68k_disasm.ENCODING_MASKS[0]
    _fields = runtime_m68k_disasm.FIELD_MAPS[0]
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
        return _build_decoded_instruction_text(f"bra{sfx}", (_branch_target_node(target),))
    if (op & _bsr_m) == _bsr_v:
        return _build_decoded_instruction_text(f"bsr{sfx}", (_branch_target_node(target),))
    cc = CC_NAMES[condition]
    return _build_decoded_instruction_text(f"b{cc}{sfx}", (_branch_target_node(target),))


def _decode_moveq(d: _Decoder, op: int, pc: int) -> DecodedInstructionText:
    """MOVEQ"""
    _m, _v = runtime_m68k_disasm.ENCODING_MASKS[0]["MOVEQ"]
    if (op & _m) != _v:
        raise DecodeError(f"invalid moveq ${op:04x}")
    _moveq_f = runtime_m68k_disasm.FIELD_MAPS[0]["MOVEQ"]
    reg = _xf(op, _moveq_f["REGISTER"])
    data = _xf(op, _moveq_f["DATA"])
    if data & 0x80:
        data -= 256
    return _build_decoded_instruction_text(
        "moveq", (_immediate_node(data, f"#{data}"), _register_node(f"d{reg}")))


def _decode_group8(d: _Decoder, op: int, pc: int) -> DecodedInstructionText:
    """OR, DIV, SBCD"""
    _masks = runtime_m68k_disasm.ENCODING_MASKS[0]
    _fields = runtime_m68k_disasm.FIELD_MAPS[0]
    _dest_reg = runtime_m68k_disasm.DEST_REG_FIELD
    _or_f = _fields["OR"]
    reg = _xf(op, _dest_reg["OR"])
    opmode = _xf(op, _or_f["OPMODE"])
    mode = _xf(op, _or_f["MODE"])
    ea_reg = _xf(op, _or_f["REGISTER"])

    # DIVU.W / DIVS.W - detect via KB masks
    for _divmn in ("DIVU, DIVUL", "DIVS, DIVSL"):
        _dm, _dv = _masks[_divmn]
        if (op & _dm) == _dv:
            ea_node = _must_decode_ea_node(d, mode, ea_reg, SIZE_WORD, pc)
            name = _divmn.split(",")[0].lower()
            return _build_decoded_instruction_text(
                f"{name}.w", (ea_node, _register_node(f"d{reg}")))

    # SBCD - R/M field from KB operand_modes
    _m, _v = _masks["SBCD"]
    if (op & _m) == _v:
        _sbcd_f = _fields["SBCD"]
        ry = _xf(op, _sbcd_f["REGISTER Dx/Ax"])
        rx = _xf(op, _sbcd_f["REGISTER Dy/Ay"])
        _rm_lo, _rm_vals = runtime_m68k_disasm.RM_FIELD["SBCD"]
        rm = (op >> _rm_lo) & 1
        if _rm_vals[rm] == "predec,predec":
            return _build_decoded_instruction_text(
                "sbcd", (_predecrement_node(f"a{ry}"), _predecrement_node(f"a{rx}")))
        return _build_decoded_instruction_text(
            "sbcd", (_register_node(f"d{ry}"), _register_node(f"d{rx}")))

    # PACK / UNPK (68020+): identified by KB mask/val, field positions from KB
    _masks = runtime_m68k_disasm.ENCODING_MASKS[0]
    _m_pack, _v_pack = _masks["PACK"]   # KeyError -> regenerate KB JSON
    _m_unpk, _v_unpk = _masks["UNPK"]
    _opfields = runtime_m68k_disasm.FIELD_MAPS[0]
    for _mn_upper, _m, _v in (("PACK", _m_pack, _v_pack), ("UNPK", _m_unpk, _v_unpk)):
        if (op & _m) == _v:
            _of = _opfields[_mn_upper]
            dx = _xf(op, _of["REGISTER Dy/Ay"])
            rm = _xf(op, _of["R/M"])
            dy = _xf(op, _of["REGISTER Dx/Ax"])
            adj = d.read_u16()
            _mn = _mn_upper.lower()
            if rm:
                return _build_decoded_instruction_text(
                    _mn,
                    (_predecrement_node(f"a{dy}"), _predecrement_node(f"a{dx}"), _immediate_node(adj, f"#${adj:x}")),
                )
            return _build_decoded_instruction_text(
                _mn,
                (_register_node(f"d{dy}"), _register_node(f"d{dx}"), _immediate_node(adj, f"#${adj:x}")),
            )

    # OR - size/direction from KB opmode_table
    _or_opm = OPMODE_TABLES_BY_VALUE["OR"]
    entry = _or_opm[opmode]
    size_name = entry.size
    assert size_name is not None
    sz = _SIZE_LETTER_TO_INT[size_name]
    sfx = SIZE_SUFFIX[sz]
    ea_node = _must_decode_ea_node(d, mode, ea_reg, sz, pc)
    if _opmode_ea_to_dn(entry):
        return _build_decoded_instruction_text(f"or{sfx}", (ea_node, _register_node(f"d{reg}")))
    return _build_decoded_instruction_text(f"or{sfx}", (_register_node(f"d{reg}"), ea_node))


def _decode_sub(d: _Decoder, op: int, pc: int) -> DecodedInstructionText:
    """SUB, SUBA, SUBX"""
    _masks = runtime_m68k_disasm.ENCODING_MASKS[0]
    _opm_tables = OPMODE_TABLES_BY_VALUE
    _fields = runtime_m68k_disasm.FIELD_MAPS[0]
    _dest_reg = runtime_m68k_disasm.DEST_REG_FIELD
    _sub_f = _fields["SUB"]
    reg = _xf(op, _dest_reg["SUB"])
    opmode = _xf(op, _sub_f["OPMODE"])
    mode = _xf(op, _sub_f["MODE"])
    ea_reg = _xf(op, _sub_f["REGISTER"])

    # SUBA - opmode 3/7 from KB opmode_table
    _suba_opm = _opm_tables["SUBA"]
    if opmode in _suba_opm:
        entry = _suba_opm[opmode]
        size_name = entry.size
        assert size_name is not None
        sz = _SIZE_LETTER_TO_INT[size_name]
        ea_node = _must_decode_ea_node(d, mode, ea_reg, sz, pc)
        sfx = SIZE_SUFFIX[sz]
        return _build_decoded_instruction_text(f"suba{sfx}", (ea_node, _register_node(f"a{reg}")))

    # SUBX - R/M field from KB operand_modes
    _m, _v = _masks["SUBX"]
    if (op & _m) == _v and (mode == 0 or mode == 1):
        _subx_f = _fields["SUBX"]
        ry = _xf(op, _subx_f["REGISTER Dx/Ax"])
        rx = _xf(op, _subx_f["REGISTER Dy/Ay"])
        sz = _xf(op, _subx_f["SIZE"])
        sfx = SIZE_SUFFIX[sz]
        _rm_lo, _rm_vals = runtime_m68k_disasm.RM_FIELD["SUBX"]
        rm = (op >> _rm_lo) & 1
        if _rm_vals[rm] == "predec,predec":
            return _build_decoded_instruction_text(
                f"subx{sfx}", (_predecrement_node(f"a{ry}"), _predecrement_node(f"a{rx}")))
        return _build_decoded_instruction_text(
            f"subx{sfx}", (_register_node(f"d{ry}"), _register_node(f"d{rx}")))

    # SUB - size/direction from KB opmode_table
    _sub_opm = _opm_tables["SUB"]
    entry = _sub_opm[opmode]
    size_name = entry.size
    assert size_name is not None
    sz = _SIZE_LETTER_TO_INT[size_name]
    sfx = SIZE_SUFFIX[sz]
    ea_node = _must_decode_ea_node(d, mode, ea_reg, sz, pc)
    if _opmode_ea_to_dn(entry):
        return _build_decoded_instruction_text(f"sub{sfx}", (ea_node, _register_node(f"d{reg}")))
    return _build_decoded_instruction_text(f"sub{sfx}", (_register_node(f"d{reg}"), ea_node))


def _decode_cmp_eor(d: _Decoder, op: int, pc: int) -> DecodedInstructionText:
    """CMP, CMPA, CMPM, EOR"""
    _masks = runtime_m68k_disasm.ENCODING_MASKS[0]
    _opm_tables = OPMODE_TABLES_BY_VALUE
    _fields = runtime_m68k_disasm.FIELD_MAPS[0]
    _dest_reg = runtime_m68k_disasm.DEST_REG_FIELD
    _cmp_f = _fields["CMP"]
    reg = _xf(op, _dest_reg["CMP"])
    opmode = _xf(op, _cmp_f["OPMODE"])
    mode = _xf(op, _cmp_f["MODE"])
    ea_reg = _xf(op, _cmp_f["REGISTER"])

    # CMPA - opmode 3/7 from KB opmode_table
    _cmpa_opm = _opm_tables["CMPA"]
    if opmode in _cmpa_opm:
        entry = _cmpa_opm[opmode]
        size_name = entry.size
        assert size_name is not None
        sz = _SIZE_LETTER_TO_INT[size_name]
        ea_node = _must_decode_ea_node(d, mode, ea_reg, sz, pc)
        sfx = SIZE_SUFFIX[sz]
        return _build_decoded_instruction_text(f"cmpa{sfx}", (ea_node, _register_node(f"a{reg}")))

    # CMPM - SIZE field from KB (not ad hoc opmode 4)
    _m, _v = _masks["CMPM"]
    if (op & _m) == _v:
        _cmpm_f = _fields["CMPM"]
        sz = _xf(op, _cmpm_f["SIZE"])
        sfx = SIZE_SUFFIX[sz]
        return _build_decoded_instruction_text(
            f"cmpm{sfx}", (_postincrement_node(f"a{ea_reg}"), _postincrement_node(f"a{reg}")))

    # EOR - opmode 4/5/6 from KB opmode_table
    _eor_opm = _opm_tables["EOR"]
    if opmode in _eor_opm:
        entry = _eor_opm[opmode]
        size_name = entry.size
        assert size_name is not None
        sz = _SIZE_LETTER_TO_INT[size_name]
        sfx = SIZE_SUFFIX[sz]
        ea_node = _must_decode_ea_node(d, mode, ea_reg, sz, pc)
        return _build_decoded_instruction_text(f"eor{sfx}", (_register_node(f"d{reg}"), ea_node))

    # CMP - opmode 0/1/2 from KB opmode_table
    _cmp_opm = _opm_tables["CMP"]
    entry = _cmp_opm[opmode]
    size_name = entry.size
    assert size_name is not None
    sz = _SIZE_LETTER_TO_INT[size_name]
    sfx = SIZE_SUFFIX[sz]
    ea_node = _must_decode_ea_node(d, mode, ea_reg, sz, pc)
    return _build_decoded_instruction_text(f"cmp{sfx}", (ea_node, _register_node(f"d{reg}")))


def _decode_group_c(d: _Decoder, op: int, pc: int) -> DecodedInstructionText:
    """AND, MUL, ABCD, EXG"""
    _masks = runtime_m68k_disasm.ENCODING_MASKS[0]
    _opm_tables = OPMODE_TABLES_BY_VALUE
    _fields = runtime_m68k_disasm.FIELD_MAPS[0]
    _dest_reg = runtime_m68k_disasm.DEST_REG_FIELD
    _and_f = _fields["AND"]
    reg = _xf(op, _dest_reg["AND"])
    opmode = _xf(op, _and_f["OPMODE"])
    mode = _xf(op, _and_f["MODE"])
    ea_reg = _xf(op, _and_f["REGISTER"])

    # MULU.W / MULS.W - detect via KB masks
    for _mulmn in ("MULU", "MULS"):
        _mm, _mv = _masks[_mulmn]
        if (op & _mm) == _mv:
            ea_node = _must_decode_ea_node(d, mode, ea_reg, SIZE_WORD, pc)
            return _build_decoded_instruction_text(
                f"{_mulmn.lower()}.w", (ea_node, _register_node(f"d{reg}")))

    # ABCD - R/M field from KB operand_modes
    _m, _v = _masks["ABCD"]
    if (op & _m) == _v:
        _abcd_f = _fields["ABCD"]
        ry = _xf(op, _abcd_f["REGISTER Ry"])
        rx = _xf(op, _abcd_f["REGISTER Rx"])
        _rm_lo, _rm_vals = runtime_m68k_disasm.RM_FIELD["ABCD"]
        rm = (op >> _rm_lo) & 1
        if _rm_vals[rm] == "predec,predec":
            return _build_decoded_instruction_text(
                "abcd", (_predecrement_node(f"a{ry}"), _predecrement_node(f"a{rx}")))
        return _build_decoded_instruction_text(
            "abcd", (_register_node(f"d{ry}"), _register_node(f"d{rx}")))

    # EXG - check KB encoding mask first, then opmode table
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
            desc = (entry.description or "").lower()
            if "data register" in desc and "address register" in desc:
                return _build_decoded_instruction_text(
                    "exg", (_register_node(f"d{rx}"), _register_node(f"a{ry}")))
            if "address" in desc:
                return _build_decoded_instruction_text(
                    "exg", (_register_node(f"a{rx}"), _register_node(f"a{ry}")))
            return _build_decoded_instruction_text(
                "exg", (_register_node(f"d{rx}"), _register_node(f"d{ry}")))

    # AND - size/direction from KB opmode_table
    _and_opm = _opm_tables["AND"]
    entry = _and_opm[opmode]
    size_name = entry.size
    assert size_name is not None
    sz = _SIZE_LETTER_TO_INT[size_name]
    sfx = SIZE_SUFFIX[sz]
    ea_node = _must_decode_ea_node(d, mode, ea_reg, sz, pc)
    if _opmode_ea_to_dn(entry):
        return _build_decoded_instruction_text(f"and{sfx}", (ea_node, _register_node(f"d{reg}")))
    return _build_decoded_instruction_text(f"and{sfx}", (_register_node(f"d{reg}"), ea_node))


def _decode_add(d: _Decoder, op: int, pc: int) -> DecodedInstructionText:
    """ADD, ADDA, ADDX"""
    _masks = runtime_m68k_disasm.ENCODING_MASKS[0]
    _opm_tables = OPMODE_TABLES_BY_VALUE
    _fields = runtime_m68k_disasm.FIELD_MAPS[0]
    _dest_reg = runtime_m68k_disasm.DEST_REG_FIELD
    _add_f = _fields["ADD"]
    reg = _xf(op, _dest_reg["ADD"])
    opmode = _xf(op, _add_f["OPMODE"])
    mode = _xf(op, _add_f["MODE"])
    ea_reg = _xf(op, _add_f["REGISTER"])

    # ADDA - opmode 3/7 from KB opmode_table
    _adda_opm = _opm_tables["ADDA"]
    if opmode in _adda_opm:
        entry = _adda_opm[opmode]
        size_name = entry.size
        assert size_name is not None
        sz = _SIZE_LETTER_TO_INT[size_name]
        ea_node = _must_decode_ea_node(d, mode, ea_reg, sz, pc)
        sfx = SIZE_SUFFIX[sz]
        return _build_decoded_instruction_text(f"adda{sfx}", (ea_node, _register_node(f"a{reg}")))

    # ADDX - R/M field from KB operand_modes
    _m, _v = _masks["ADDX"]
    if (op & _m) == _v and (mode == 0 or mode == 1):
        _addx_f = _fields["ADDX"]
        ry = _xf(op, _addx_f["REGISTER Ry"])
        rx = _xf(op, _addx_f["REGISTER Rx"])
        sz = _xf(op, _addx_f["SIZE"])
        sfx = SIZE_SUFFIX[sz]
        _rm_lo, _rm_vals = runtime_m68k_disasm.RM_FIELD["ADDX"]
        rm = (op >> _rm_lo) & 1
        if _rm_vals[rm] == "predec,predec":
            return _build_decoded_instruction_text(
                f"addx{sfx}", (_predecrement_node(f"a{ry}"), _predecrement_node(f"a{rx}")))
        return _build_decoded_instruction_text(
            f"addx{sfx}", (_register_node(f"d{ry}"), _register_node(f"d{rx}")))

    # ADD - size/direction from KB opmode_table
    _add_opm = _opm_tables["ADD"]
    entry = _add_opm[opmode]
    size_name = entry.size
    assert size_name is not None
    sz = _SIZE_LETTER_TO_INT[size_name]
    sfx = SIZE_SUFFIX[sz]
    ea_node = _must_decode_ea_node(d, mode, ea_reg, sz, pc)
    if _opmode_ea_to_dn(entry):
        return _build_decoded_instruction_text(f"add{sfx}", (ea_node, _register_node(f"d{reg}")))
    return _build_decoded_instruction_text(f"add{sfx}", (_register_node(f"d{reg}"), ea_node))


def _decode_bfxxx(d: _Decoder, op: int, pc: int, mn: str) -> DecodedInstructionText:
    """Decode a BFxxx bit-field instruction.

    Field positions are derived from KB extension word (encoding[1]):
      Do:       flag bit at Do.bit_hi; offset spans Do.bit_lo..OFFSET.bit_lo
      Dw:       flag bit at Dw.bit_hi; width spans Dw.bit_lo..WIDTH.bit_lo
      REGISTER: destination/source Dn (only present in BFEXTU/BFEXTS/BFFFO/BFINS)
    """
    ext_fields = runtime_m68k_disasm.FIELD_MAPS[1][mn]  # hard-fail if missing

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

    _bf_opf = runtime_m68k_disasm.FIELD_MAPS[0][mn]
    mode = _xf(op, _bf_opf["MODE"])
    reg = _xf(op, _bf_opf["REGISTER"])
    ea_node = _must_decode_ea_node(d, mode, reg, SIZE_LONG, pc)
    bitfield = f"{ea_node.text}{{{off_str}:{w_str}}}"
    bitfield_meta = DecodedBitfieldNodeMetadata(
        base_node=ea_node,
        offset_is_register=bool(do),
        offset_value=off_val & 7 if do else off_val,
        width_is_register=bool(dw),
        width_value=w_val & 7 if dw else (32 if w_val == 0 else w_val),
    )
    bitfield_node = _bitfield_node(ea_node, bitfield_meta, bitfield)

    # REGISTER field (Dn) - only present in BFEXTU/BFEXTS/BFFFO/BFINS
    if "REGISTER" not in ext_fields:
        return _build_decoded_instruction_text(mn.lower(), (bitfield_node,))
    _, reg_lo, reg_w = ext_fields["REGISTER"]
    dn = (ext >> reg_lo) & ((1 << reg_w) - 1)
    # Operand order from KB forms: BFINS has Dn before <ea>, others have <ea> before Dn
    forms = FORM_OPERAND_TYPES[mn]
    assert forms and forms[0]
    dn_first = forms[0][0] == "dn"
    if dn_first:
        return _build_decoded_instruction_text(mn.lower(), (_register_node(f"d{dn}"), bitfield_node))
    return _build_decoded_instruction_text(mn.lower(), (bitfield_node, _register_node(f"d{dn}")))


def _decode_shift(d: _Decoder, op: int, pc: int) -> DecodedInstructionText:
    """ASd, LSd, ROd, ROXd, BFxxx"""
    _shift_reg_f = runtime_m68k_disasm.FIELD_MAPS[0]["ASL, ASR"]
    size_bits = _xf(op, _shift_reg_f["SIZE"])

    if size_bits == 3:
        # BFxxx instructions (68020+) live in group E with size_bits=3.
        # Mnemonic list and mask/val derived from KB.
        _masks = runtime_m68k_disasm.ENCODING_MASKS[0]
        for mn in runtime_m68k_disasm.BF_MNEMONICS:
            _m, _v = _masks[mn]
            if (op & _m) == _v:
                return _decode_bfxxx(d, op, pc, mn)

        # Memory shift (word only, shift by 1)
    # Field positions from KB - memory shift uses encoding[1]
        _shift_dr_field, _shift_directions, _shift_zero_means = runtime_m68k_disasm.SHIFT_FIELDS
        _mem_shift_f = runtime_m68k_disasm.FIELD_MAPS[1]["ASL, ASR"]
        dr_val = _xf(op, _mem_shift_f["dr"])
        direction = _shift_directions[dr_val]
        _, _mem_type_f = runtime_m68k_disasm.SHIFT_TYPE_FIELDS
        shift_type = _xf(op, _mem_type_f)
        _shift_names = runtime_m68k_disasm.SHIFT_NAMES
        mode = _xf(op, _mem_shift_f["MODE"])
        reg = _xf(op, _mem_shift_f["REGISTER"])
        ea_node = _must_decode_ea_node(d, mode, reg, SIZE_WORD, pc)
        return _build_decoded_instruction_text(
            f"{_shift_names[shift_type]}{direction}.w", (ea_node,))

    # Register shift - field positions from KB
    _shift_direction_field, _shift_directions, _shift_zero_means = runtime_m68k_disasm.SHIFT_FIELDS
    _shift_f = runtime_m68k_disasm.FIELD_MAPS[0]["ASL, ASR"]
    dr_val = _xf(op, _shift_f["dr"])
    direction = _shift_directions[dr_val]
    _reg_type_f, _ = runtime_m68k_disasm.SHIFT_TYPE_FIELDS
    shift_type = _xf(op, _reg_type_f)
    _shift_names = runtime_m68k_disasm.SHIFT_NAMES
    sfx = SIZE_SUFFIX[size_bits]
    dreg = _xf(op, _shift_f["REGISTER"])
    _shift_dest = runtime_m68k_disasm.DEST_REG_FIELD
    count_or_reg = _xf(op, _shift_dest["ASL, ASR"])

    ir_val = _xf(op, _shift_f["i/r"])
    if ir_val:
        # Shift by register (i/r = 1)
        return _build_decoded_instruction_text(
            f"{_shift_names[shift_type]}{direction}{sfx}",
            (_register_node(f"d{count_or_reg}"), _register_node(f"d{dreg}")))
    # Shift by immediate (i/r = 0); count 0 -> zero_means from KB
    if count_or_reg != 0:
        count = count_or_reg
    else:
        assert _shift_zero_means is not None, "KB missing shift zero_means value"
        count = _shift_zero_means
    return _build_decoded_instruction_text(
        f"{_shift_names[shift_type]}{direction}{sfx}",
        (_immediate_node(count, f"#{count}"), _register_node(f"d{dreg}")))



# --- Line-F (coprocessor / 68040) ---


def _decode_line_f(d: _Decoder, op: int, pc: int) -> DecodedInstructionText:
    """Line-F: coprocessor (FPU/MMU), MOVE16, etc."""
    _masks = runtime_m68k_disasm.ENCODING_MASKS[0]
    _cpid_lo, _cpid_w = runtime_m68k_disasm.CPID_FIELD
    cpid = (op >> _cpid_lo) & ((1 << _cpid_w) - 1)

    # MOVE16 (68040) - separate encoding masks for postincrement vs absolute forms
    _m16_pi_m, _m16_pi_v = runtime_m68k_disasm.ENCODING_MASKS[0]["MOVE16"]  # enc[0] postincrement
    if (op & _m16_pi_m) == _m16_pi_v:
        _m16f0 = runtime_m68k_disasm.FIELD_MAPS[0]["MOVE16"]
        ax = _xf(op, _m16f0["REGISTER Ax"])
        ext = d.read_u16()
        _m16f1 = runtime_m68k_disasm.FIELD_MAPS[1]["MOVE16"]
        ay = _xf(ext, _m16f1["REGISTER Ay"])
        return _build_decoded_instruction_text(
            "move16",
            (
                DecodedOperandNode(
                    kind="postincrement",
                    text=f"(a{ax})+",
                    metadata=DecodedBaseRegisterNodeMetadata(base_register=f"a{ax}"),
                ),
                DecodedOperandNode(
                    kind="postincrement",
                    text=f"(a{ay})+",
                    metadata=DecodedBaseRegisterNodeMetadata(base_register=f"a{ay}"),
                ),
            ),
        )
    _m16_abs_masks = runtime_m68k_disasm.ENCODING_MASKS[2]
    if "MOVE16" in _m16_abs_masks:
        _m16a_m, _m16a_v = _m16_abs_masks["MOVE16"]
        if (op & _m16a_m) == _m16a_v:
            # OPMODE and REGISTER from KB encoding[2]
            _fmap = runtime_m68k_disasm.FIELD_MAPS[2]["MOVE16"]
            opmode = _xf(op, _fmap["OPMODE"])
            an = _xf(op, _fmap["REGISTER Ay"])
            addr = d.read_u32()
            # Operand order from KB opmode_table
            _m16_opm = OPMODE_TABLES_BY_VALUE["MOVE16"]
            entry = _m16_opm[opmode]
            # Source field tells us which operand is first
            src = entry.source
            assert src is not None
            postinc = "+" in src
            abs_first = "(xxx)" in src
            if abs_first:
                dest = entry.destination
                assert dest is not None
                reg_postinc = "+" in dest
                reg_node = (
                    DecodedOperandNode(
                        kind="postincrement",
                        text=f"(a{an})+",
                        metadata=DecodedBaseRegisterNodeMetadata(base_register=f"a{an}"),
                    )
                    if reg_postinc else
                    DecodedOperandNode(
                        kind="indirect",
                        text=f"(a{an})",
                        metadata=DecodedBaseRegisterNodeMetadata(base_register=f"a{an}"),
                    )
                )
                abs_node = _absolute_target_node(f"${addr:08x}.l", addr)
                return _build_decoded_instruction_text(
                    "move16", (abs_node, reg_node))
            reg_node = (
                DecodedOperandNode(
                    kind="postincrement",
                    text=f"(a{an})+",
                    metadata=DecodedBaseRegisterNodeMetadata(base_register=f"a{an}"),
                )
                if postinc else
                DecodedOperandNode(
                    kind="indirect",
                    text=f"(a{an})",
                    metadata=DecodedBaseRegisterNodeMetadata(base_register=f"a{an}"),
                )
            )
            abs_node = _absolute_target_node(f"${addr:08x}.l", addr)
            return _build_decoded_instruction_text(
                "move16", (reg_node, abs_node))

    # MMU (cpid=0): PRESTORE/PSAVE/PBcc/PDBcc/PScc/PTRAPcc/PFLUSH/PFLUSHR
    if cpid == 0:
        _opf = runtime_m68k_disasm.FIELD_MAPS[0]
        pmmu_cc = PMMU_CONDITION_CODES

        # PRESTORE
        _m, _v = _masks["PRESTORE"]
        if (op & _m) == _v:
            _pr_f = _opf["PRESTORE"]
            mode = _xf(op, _pr_f["MODE"])
            reg = _xf(op, _pr_f["REGISTER"])
            ea_node = _must_decode_ea_node(d, mode, reg, SIZE_LONG, pc)
            return _build_decoded_instruction_text("prestore", (ea_node,))

        # PSAVE
        _m, _v = _masks["PSAVE"]
        if (op & _m) == _v:
            _ps_f = _opf["PSAVE"]
            mode = _xf(op, _ps_f["MODE"])
            reg = _xf(op, _ps_f["REGISTER"])
            ea_node = _must_decode_ea_node(d, mode, reg, SIZE_LONG, pc)
            return _build_decoded_instruction_text("psave", (ea_node,))

            # PBcc - KB mask/val and fields
        _pbcc_m, _pbcc_v = _masks["PBcc"]
        if (op & _pbcc_m) == _pbcc_v:
            _pbcc_f = _opf["PBcc"]
            cond = _xf(op, _pbcc_f["MC68851 CONDITION"])
            cc = pmmu_cc[cond] if cond < len(pmmu_cc) else f"#{cond}"
            sz_val = _xf(op, _pbcc_f["SIZE"])
            if sz_val == 0:
                disp = d.read_i16()
                target = _branch_target(pc, disp)
                return _build_decoded_instruction_text(f"pb{cc}.w", (_branch_target_node(target),))
            disp = d.read_i32()
            target = _branch_target(pc, disp)
            return _build_decoded_instruction_text(f"pb{cc}.l", (_branch_target_node(target),))

        # PDBcc (more specific mask, check before PScc)
        _pdbcc_m, _pdbcc_v = _masks["PDBcc"]
        if (op & _pdbcc_m) == _pdbcc_v:
            _pdbcc_f = _opf["PDBcc"]
            reg = _xf(op, _pdbcc_f["COUNT REGISTER"])
            ext = d.read_u16()
            _pdbcc_ef = runtime_m68k_disasm.FIELD_MAPS[1]["PDBcc"]
            cond = _xf(ext, _pdbcc_ef["MC68851 CONDITION"])
            cc = pmmu_cc[cond] if cond < len(pmmu_cc) else f"#{cond}"
            disp = d.read_i16()
            target = _branch_target(pc, disp)
            return _build_decoded_instruction_text(f"pdb{cc}", (_register_node(f"d{reg}"), _branch_target_node(target)))

        # PTRAPcc (more specific mask, check before PScc; validate opmode)
        _ptrap_m, _ptrap_v = _masks["PTRAPcc"]
        _ptrap_opm = OPMODE_TABLES_BY_VALUE["PTRAPcc"]
        if (op & _ptrap_m) == _ptrap_v:
            _ptrap_f = _opf["PTRAPcc"]
            opmode = _xf(op, _ptrap_f["OPMODE"])
            if opmode in _ptrap_opm:
                ext = d.read_u16()
                _ptrap_ef = runtime_m68k_disasm.FIELD_MAPS[1]["PTRAPcc"]
                cond = _xf(ext, _ptrap_ef["MC68851 CONDITION"])
                cc = pmmu_cc[cond] if cond < len(pmmu_cc) else f"#{cond}"
                entry = _ptrap_opm[opmode]
                sz = entry.size
                if sz == "w":
                    imm = d.read_u16()
                    return _build_decoded_instruction_text(
                        f"ptrap{cc}.w", (_immediate_node(imm, f"#{imm}"),))
                if sz == "l":
                    imm = d.read_u32()
                    return _build_decoded_instruction_text(
                        f"ptrap{cc}.l", (_immediate_node(imm, f"#{imm}"),))
                return _build_decoded_instruction_text(f"ptrap{cc}")

        # PScc (broader mask, check last)
        _pscc_m, _pscc_v = _masks["PScc"]
        if (op & _pscc_m) == _pscc_v:
            _pscc_f = _opf["PScc"]
            mode = _xf(op, _pscc_f["MODE"])
            reg = _xf(op, _pscc_f["REGISTER"])
            ext = d.read_u16()
            _pscc_ef = runtime_m68k_disasm.FIELD_MAPS[1]["PScc"]
            cond = _xf(ext, _pscc_ef["MC68851 CONDITION"])
            cc = pmmu_cc[cond] if cond < len(pmmu_cc) else f"#{cond}"
            ea_node = _must_decode_ea_node(d, mode, reg, SIZE_BYTE, pc)
            return _build_decoded_instruction_text(f"ps{cc}", (ea_node,))

        # PFLUSH/PFLUSHA/PFLUSHR or PMMU general (type_bits == 0)
        _pfl_f = _opf["PFLUSH"]
        mode = _xf(op, _pfl_f["MODE"])
        reg = _xf(op, _pfl_f["REGISTER"])
        ext = d.read_u16()
        _ext_masks = runtime_m68k_disasm.ENCODING_MASKS[1]
        _pf_m, _pf_v = _ext_masks["PFLUSH PFLUSHA"]
        if (ext & _pf_m) == _pf_v:
            _ext_fields = runtime_m68k_disasm.FIELD_MAPS[1]["PFLUSH PFLUSHA"]
            pflush_mode = _xf(ext, _ext_fields["MODE"])
            pflush_mask = _xf(ext, _ext_fields["MASK"])
            fc = _xf(ext, _ext_fields["FC"])
            if pflush_mode == 1:
                return _build_decoded_instruction_text("pflusha")
            ea_node = _must_decode_ea_node(d, mode, reg, SIZE_LONG, pc)
            return _build_decoded_instruction_text(
                "pflush",
                (_immediate_node(fc, f"#{fc}"), _immediate_node(pflush_mask, f"#{pflush_mask}"), ea_node))
        _pfr_m, _pfr_v = _ext_masks["PFLUSHR"]
        if (ext & _pfr_m) == _pfr_v:
            ea_node = _must_decode_ea_node(d, mode, reg, SIZE_LONG, pc)
            return _build_decoded_instruction_text("pflushr", (ea_node,))
        # Other PMMU general commands (PMOVE, PLOAD, PTEST, PVALID)
        raise DecodeError(f"unsupported PMMU command: op=${op:04x} ext=${ext:04x}")

    # FPU (cpid=1): FRESTORE/FSAVE
    if cpid == 1:
        _opf = runtime_m68k_disasm.FIELD_MAPS[0]

        _m, _v = _masks["FRESTORE"]
        if (op & _m) == _v:
            _fr_f = _opf["FRESTORE"]
            mode = _xf(op, _fr_f["MODE"])
            reg = _xf(op, _fr_f["REGISTER"])
            ea_node = _must_decode_ea_node(d, mode, reg, SIZE_LONG, pc)
            return _build_decoded_instruction_text("frestore", (ea_node,))

        _m, _v = _masks["FSAVE"]
        if (op & _m) == _v:
            _fs_f = _opf["FSAVE"]
            mode = _xf(op, _fs_f["MODE"])
            reg = _xf(op, _fs_f["REGISTER"])
            ea_node = _must_decode_ea_node(d, mode, reg, SIZE_LONG, pc)
            return _build_decoded_instruction_text("fsave", (ea_node,))

        # Other FPU instructions (cpGEN etc.) - not yet decoded
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
    label = f"{labels[inst.offset]}:" if labels and inst.offset in labels else ""
    return f"{label:20s}    {inst.text:40s} ; {inst.offset:06x}: {hex_bytes}"


if __name__ == "__main__":
    import sys

    from .hunk_parser import HunkType as HT
    from .hunk_parser import parse_file

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
