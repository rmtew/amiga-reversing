from __future__ import annotations

from disasm.ascii import PRINTABLE_MAX, PRINTABLE_MIN
from disasm.types import HunkDisassemblySession, SemanticOperand
from disasm.validation import get_instruction_processor_min
from m68k.m68k_disasm import Instruction


def _has_resolved_library_call(
    hunk_session: HunkDisassemblySession,
    inst: Instruction,
) -> bool:
    return any(
        call.addr == inst.offset and call.library != "unknown"
        for call in hunk_session.lib_calls
    )


def format_app_offset_comment(operand_parts: tuple[SemanticOperand, ...], base_reg: int) -> str | None:
    """Generate a hex offset comment for unnamed d(base_reg) references."""
    base_name = f"a{base_reg}"
    for operand in operand_parts:
        if operand.base_register != base_name:
            continue
        if operand.kind != "base_displacement":
            continue
        if operand.displacement is None:
            raise ValueError(
                f"Base displacement operand {operand.text!r} missing displacement")
        offset = operand.displacement
        if offset < 0:
            return f"app-${-offset:X}"
        return f"app+${offset:X}"
    return None


def format_ascii_immediate(value: int) -> str | None:
    """Format a printable longword immediate as a quoted ASCII string."""
    lo4 = PRINTABLE_MIN | (PRINTABLE_MIN << 8) | (PRINTABLE_MIN << 16) | (PRINTABLE_MIN << 24)
    hi4 = PRINTABLE_MAX | (PRINTABLE_MAX << 8) | (PRINTABLE_MAX << 16) | (PRINTABLE_MAX << 24)
    if value < lo4 or value > hi4:
        return None
    chars = []
    for index in range(4):
        byte = (value >> (24 - index * 8)) & 0xFF
        if byte < PRINTABLE_MIN or byte > PRINTABLE_MAX:
            return None
        chars.append(chr(byte))
    return "'" + "".join(chars) + "'"


def build_instruction_comment_parts(inst: Instruction,
                                    hunk_session: HunkDisassemblySession,
                                    operand_parts: tuple[SemanticOperand, ...] | None,
                                    include_arg_subs: bool = True
                                    ) -> tuple[str, ...]:
    parts: list[str] = []
    pmin = get_instruction_processor_min(inst)
    if pmin != "68000":
        parts.append(f"{pmin}+")

    arg_ann = hunk_session.arg_annotations.get(inst.offset)
    if include_arg_subs and arg_ann:
        parts.append(f"{arg_ann.function}: {arg_ann.arg_name}")

    base_info = hunk_session.platform.app_base
    if not parts and base_info and operand_parts is not None:
        app_comment = format_app_offset_comment(operand_parts, base_info.reg_num)
        if app_comment:
            parts.append(app_comment)

    if not parts and operand_parts is not None:
        for operand in operand_parts:
            if operand.kind != "immediate" or operand.value is None:
                continue
            if inst.operand_size != "l":
                continue
            ascii_str = format_ascii_immediate(operand.value & 0xFFFFFFFF)
            if ascii_str:
                parts.append(ascii_str)
                break

    unresolved = hunk_session.unresolved_indirects.get(inst.offset)
    if unresolved is not None and not _has_resolved_library_call(hunk_session, inst):
        parts.append(
            f"unresolved_indirect_{unresolved.region}:{unresolved.shape}")

    return tuple(parts)


def render_comment_parts(comment_parts: tuple[str, ...]) -> str:
    return "; ".join(part for part in comment_parts if part)

