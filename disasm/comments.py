from __future__ import annotations

import re

from disasm.ascii import PRINTABLE_MAX, PRINTABLE_MIN
from disasm.validation import get_processor_min
from disasm.types import HunkDisassemblySession


def format_app_offset_comment(text: str, base_reg: int,
                              named_offsets: dict[str, str]) -> str | None:
    """Generate a hex offset comment for unnamed d(base_reg) references."""
    base_name = f"a{base_reg}"
    match = re.search(rf'(-?\d+)\({base_name}\)', text)
    if not match:
        return None
    if re.search(rf'[a-z_]+\({base_name}\)', text):
        return None
    offset = int(match.group(1))
    if offset < 0:
        return f"app-${-offset:X}"
    return f"app+${offset:X}"


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


def build_instruction_comment_parts(inst, rendered_text: str,
                                    hunk_session: HunkDisassemblySession,
                                    include_arg_subs: bool = True
                                    ) -> tuple[str, ...]:
    parts: list[str] = []
    pmin = get_processor_min(inst.text, hunk_session.kb)
    if pmin != "68000":
        parts.append(f"{pmin}+")

    arg_ann = hunk_session.arg_annotations.get(inst.offset)
    if include_arg_subs and arg_ann:
        parts.append(f"{arg_ann['function']}: {arg_ann['arg_name']}")

    base_info = hunk_session.platform.get("initial_base_reg")
    if not parts and base_info:
        app_comment = format_app_offset_comment(
            rendered_text, base_info[0], hunk_session.app_offsets)
        if app_comment:
            parts.append(app_comment)

    if not parts:
        imm_match = re.search(r'#\$([0-9a-fA-F]{8})\b', rendered_text)
        if imm_match:
            ascii_str = format_ascii_immediate(int(imm_match.group(1), 16))
            if ascii_str:
                parts.append(ascii_str)

    return tuple(parts)


def render_comment_parts(comment_parts: tuple[str, ...]) -> str:
    return "; ".join(part for part in comment_parts if part)
