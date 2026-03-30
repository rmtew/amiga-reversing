from __future__ import annotations

import struct
from collections.abc import Mapping
from typing import Protocol, TextIO

from disasm.ascii import is_printable_ascii
from disasm.assembler_profiles import VASM_PROFILE, AssemblerProfile
from disasm.os_value_domains import resolve_value_domain_expression
from disasm.types import TypedDataFieldInfo
from m68k.os_structs import OsStructFieldLike, OsStructLike

_MIN_STRING_LEN = 4


class _TypedFieldValueKb(Protocol):
    STRUCT_FIELD_VALUE_DOMAINS: dict[str, dict[str | None, str]]
    STRUCTS: Mapping[str, OsStructLike]


def _resolve_typed_field_value(
    *,
    os_kb: _TypedFieldValueKb | None,
    field_info: TypedDataFieldInfo | None,
    value: int,
) -> str | None:
    if field_info is None or os_kb is None:
        return None
    field_domains = os_kb.STRUCT_FIELD_VALUE_DOMAINS.get(
        f"{field_info.owner_struct}.{field_info.field_symbol}"
    )
    if field_domains is None:
        return None
    domain_names: list[str] = []
    if field_info.context_name is not None:
        context_domain = field_domains.get(field_info.context_name)
        if context_domain is not None:
            domain_names.append(context_domain)
    base_domain = field_domains.get(None)
    if base_domain is not None:
        domain_names.append(base_domain)
    for domain_name in domain_names:
        resolved = resolve_value_domain_expression(os_kb, domain_name, value)
        if resolved is not None:
            return str(resolved.text)
    return None


def _typed_field_def(
    os_kb: _TypedFieldValueKb | None, field_info: TypedDataFieldInfo | None
) -> OsStructFieldLike | None:
    if os_kb is None or field_info is None:
        return None
    struct_name: str | None = field_info.owner_struct
    seen: set[str] = set()
    while struct_name is not None and struct_name not in seen:
        seen.add(struct_name)
        struct_def = os_kb.STRUCTS.get(struct_name)
        if struct_def is None:
            return None
        for field in struct_def.fields:
            if field.name == field_info.field_symbol:
                return field
        struct_name = struct_def.base_struct
    return None


def _typed_field_is_pointer_like(
    os_kb: _TypedFieldValueKb | None, field_info: TypedDataFieldInfo | None
) -> bool:
    field = _typed_field_def(os_kb, field_info)
    if field is None or field.size != 4:
        return False
    field_type = str(field.type)
    return (
        "*" in field_type
        or "PTR" in field_type
        or field.struct is not None
        or field.pointer_struct is not None
    )


def _try_read_string(code: bytes, pos: int, end: int) -> str | None:
    chars: list[str] = []
    i = pos
    while i < end:
        b = code[i]
        if b == 0:
            if len(chars) >= 4:
                return "".join(chars)
            return None
        if is_printable_ascii(b) or b in (0x09, 0x0A):
            chars.append(chr(b))
        else:
            return None
        i += 1
    return None


def _string_line(text: str, indent: str, *, assembler_profile: AssemblerProfile) -> str:
    return render_string_data_line(
        text,
        indent=indent,
        assembler_profile=assembler_profile,
        null_terminated=True,
    )


def _quoted_string_token(text: str, delimiter: str) -> str:
    return f"{delimiter}{text}{delimiter}"


def _string_tokens(
    text: str,
    *,
    assembler_profile: AssemblerProfile,
    null_terminated: bool,
) -> list[str]:
    tokens: list[str] = []
    current: list[str] = []
    delimiters = assembler_profile.render.string_delimiters

    def flush_current() -> None:
        if not current:
            return
        chunk = "".join(current)
        delimiter = next(
            (candidate for candidate in delimiters if candidate not in chunk),
            delimiters[0],
        )
        escaped_chunk = chunk.replace(delimiter, delimiter * 2)
        tokens.append(_quoted_string_token(escaped_chunk, delimiter))
        current.clear()

    for ch in text:
        if not is_printable_ascii(ord(ch)):
            flush_current()
            tokens.append(f"${ord(ch):02x}")
            continue
        if ch in delimiters:
            flush_current()
            delimiter = next(
                candidate for candidate in delimiters if candidate != ch
            )
            tokens.append(_quoted_string_token(ch, delimiter))
            continue
        current.append(ch)

    flush_current()
    if null_terminated:
        tokens.append("0")
    return tokens


def render_string_data_line(
    text: str,
    *,
    indent: str,
    assembler_profile: AssemblerProfile,
    null_terminated: bool,
) -> str:
    tokens = _string_tokens(
        text,
        assembler_profile=assembler_profile,
        null_terminated=null_terminated,
    )
    return (
        f"{indent}{assembler_profile.render.directives.dc_b}    "
        f"{','.join(tokens)}\n"
    )


def _hex_byte_lines(
    data: bytes, indent: str, *, assembler_profile: AssemblerProfile
) -> list[str]:
    lines: list[str] = []
    for i in range(0, len(data), 16):
        row = data[i : i + 16]
        hex_vals = ",".join(f"${b:02x}" for b in row)
        lines.append(f"{indent}{assembler_profile.render.directives.dc_b}    {hex_vals}\n")
    return lines


def _safe_string_span(
    *, start: int, text: str, labels: dict[int, str], reloc_map: dict[int, int]
) -> int | None:
    string_end = start + len(text) + 1
    for addr in range(start + 1, string_end):
        if addr in labels or addr in reloc_map:
            return None
    return string_end


def _chunk_with_strings_lines(
    code: bytes,
    start: int,
    end: int,
    indent: str,
    *,
    assembler_profile: AssemblerProfile = VASM_PROFILE,
) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    pos = start
    hex_start = start
    while pos < end:
        if not is_printable_ascii(code[pos]):
            pos += 1
            continue

        run_start = pos
        while pos < end and is_printable_ascii(code[pos]):
            pos += 1

        run_end = pos
        run_len = run_end - run_start
        null_term = run_end < end and code[run_end] == 0
        min_len = _MIN_STRING_LEN if null_term else 6
        if run_len < min_len:
            continue

        if hex_start < run_start:
            for offset, line in enumerate(
                _hex_byte_lines(
                    code[hex_start:run_start],
                    indent,
                    assembler_profile=assembler_profile,
                )
            ):
                lines.append((hex_start + offset * 16, line))

        text = code[run_start:run_end].decode("ascii")
        if null_term:
            lines.append((
                run_start,
                _string_line(text, indent, assembler_profile=assembler_profile),
            ))
            pos += 1
        else:
            lines.append((
                run_start,
                render_string_data_line(
                    text,
                    indent=indent,
                    assembler_profile=assembler_profile,
                    null_terminated=False,
                ),
            ))
        hex_start = pos

    if hex_start < end:
        for offset, line in enumerate(
            _hex_byte_lines(code[hex_start:end], indent, assembler_profile=assembler_profile)
        ):
            lines.append((hex_start + offset * 16, line))
    return lines


def _byte_line_for_range(
    code: bytes,
    start: int,
    end: int,
    indent: str,
    *,
    assembler_profile: AssemblerProfile = VASM_PROFILE,
) -> tuple[int, str]:
    vals = ",".join(f"${byte:02x}" for byte in code[start:end])
    return start, f"{indent}{assembler_profile.render.directives.dc_b}    {vals}\n"


def iter_data_region_lines(
    code: bytes,
    start: int,
    end: int,
    labels: dict[int, str],
    reloc_map: dict[int, int],
    string_addrs: set[int],
    reloc_labels: dict[int, str] | None = None,
    indent: str = "    ",
    access_sizes: dict[int, int] | None = None,
    typed_sizes: dict[int, int] | None = None,
    typed_fields: dict[int, TypedDataFieldInfo] | None = None,
    os_kb: _TypedFieldValueKb | None = None,
    addr_comments: dict[int, str] | None = None,
    assembler_profile: AssemblerProfile = VASM_PROFILE,
) -> list[tuple[int, str]]:
    if reloc_labels is None:
        reloc_labels = {}
    if addr_comments is None:
        addr_comments = {}
    if typed_sizes is None:
        typed_sizes = {}
    if typed_fields is None:
        typed_fields = {}
    lines: list[tuple[int, str]] = []
    pos = start
    while pos < end:
        if pos != start and pos in labels:
            comment = addr_comments.get(pos)
            if comment is not None and pos not in typed_sizes:
                lines.append((pos, f"; {comment}\n"))
            lines.append((pos, f"{labels[pos]}:\n"))

        typed_size = typed_sizes.get(pos)

        if pos in reloc_map and pos + 4 <= end:
            if assembler_profile.render.auto_align_dc_l and pos % 2 != 0:
                lines.append(
                    _byte_line_for_range(
                        code,
                        pos,
                        pos + 4,
                        indent,
                        assembler_profile=assembler_profile,
                    )
                )
                pos += 4
                continue
            target = reloc_map[pos]
            is_pointer_like = _typed_field_is_pointer_like(os_kb, typed_fields.get(pos))
            if target == 0 and is_pointer_like:
                rendered = "0"
            elif pos in reloc_labels:
                rendered = reloc_labels[pos]
            elif target in labels:
                rendered = labels[target]
            else:
                val = struct.unpack_from(">I", code, pos)[0]
                rendered = f"${val:08x}"
                resolved_text = _resolve_typed_field_value(
                    os_kb=os_kb,
                    field_info=typed_fields.get(pos),
                    value=val,
                )
                if resolved_text is not None:
                    rendered = resolved_text
            comment = addr_comments.get(pos)
            suffix = f" ; {comment}" if comment else ""
            lines.append((
                pos,
                f"{indent}{assembler_profile.render.directives.dc_l}    {rendered}{suffix}\n",
            ))
            pos += 4
            continue

        if pos in string_addrs:
            text = _try_read_string(code, pos, end)
            if text:
                lines.append((
                    pos,
                    _string_line(text, indent, assembler_profile=assembler_profile),
                ))
                pos += len(text) + 1
                continue

        text = _try_read_string(code, pos, end)
        if text:
            string_end = _safe_string_span(
                start=pos,
                text=text,
                labels=labels,
                reloc_map=reloc_map,
            )
            if string_end is not None:
                lines.append((
                    pos,
                    _string_line(text, indent, assembler_profile=assembler_profile),
                ))
                pos = string_end
                continue

        asize = (
            typed_size
            if typed_size is not None
            else (access_sizes[pos] if access_sizes and pos in access_sizes else None)
        )
        if asize is not None:
            if asize == 4 and pos + 4 <= end:
                if assembler_profile.render.auto_align_dc_l and pos % 2 != 0:
                    lines.append(
                        _byte_line_for_range(
                            code,
                            pos,
                            pos + 4,
                            indent,
                            assembler_profile=assembler_profile,
                        )
                    )
                    pos += 4
                    continue
                val = struct.unpack_from(">I", code, pos)[0]
                is_pointer_like = _typed_field_is_pointer_like(
                    os_kb, typed_fields.get(pos)
                )
                if val == 0 and is_pointer_like:
                    rendered = "0"
                elif pos in reloc_labels:
                    rendered = reloc_labels[pos]
                elif val in labels and is_pointer_like:
                    rendered = labels[val]
                else:
                    rendered = f"${val:08x}"
                    resolved_text = _resolve_typed_field_value(
                        os_kb=os_kb,
                        field_info=typed_fields.get(pos),
                        value=val,
                    )
                    if resolved_text is not None:
                        rendered = resolved_text
                comment = addr_comments.get(pos)
                suffix = f" ; {comment}" if comment else ""
                lines.append((
                    pos,
                    f"{indent}{assembler_profile.render.directives.dc_l}    {rendered}{suffix}\n",
                ))
                pos += 4
                continue
            if asize == 2 and pos + 2 <= end:
                if assembler_profile.render.auto_align_dc_w and pos % 2 != 0:
                    lines.append(
                        _byte_line_for_range(
                            code,
                            pos,
                            pos + 2,
                            indent,
                            assembler_profile=assembler_profile,
                        )
                    )
                    pos += 2
                    continue
                word_end = pos + 2
                while (
                    typed_sizes.get(word_end) is None
                    and access_sizes is not None
                    and access_sizes.get(word_end) == asize
                    and word_end + 2 <= end
                ):
                    if (
                        word_end in labels
                        or word_end in reloc_map
                        or word_end in string_addrs
                    ):
                        break
                    if word_end in addr_comments:
                        break
                    word_end += 2
                for row_start in range(pos, word_end, 16):
                    row_end = min(row_start + 16, word_end)
                    vals: list[str] = []
                    for wp in range(row_start, row_end, 2):
                        value = struct.unpack_from(">H", code, wp)[0]
                        rendered = f"${value:04x}"
                        resolved_text = _resolve_typed_field_value(
                            os_kb=os_kb,
                            field_info=typed_fields.get(wp),
                            value=value,
                        )
                        if resolved_text is not None:
                            rendered = resolved_text
                        vals.append(rendered)
                    comment = addr_comments.get(row_start) if row_start == pos else None
                    suffix = f" ; {comment}" if comment else ""
                    lines.append(
                        (
                            row_start,
                            f"{indent}{assembler_profile.render.directives.dc_w}    {','.join(vals)}{suffix}\n",
                        )
                    )
                pos = word_end
                continue

        if code[pos] == 0:
            zero_end = pos + 1
            while zero_end < end and code[zero_end] == 0:
                if zero_end in labels or zero_end in reloc_map:
                    break
                zero_end += 1
            count = zero_end - pos
            if count >= 4:
                lines.append((
                    pos,
                    f"{indent}{assembler_profile.render.directives.dcb_b}   {count},0\n",
                ))
                pos = zero_end
                continue

        chunk_end = pos + 1
        while chunk_end < end:
            if (
                chunk_end in labels
                or chunk_end in reloc_map
                or chunk_end in string_addrs
                or (access_sizes and chunk_end in access_sizes)
                or chunk_end in typed_sizes
            ):
                break
            if (
                code[chunk_end] == 0
                and chunk_end + 3 < end
                and all(code[chunk_end + i] == 0 for i in range(4))
            ):
                break
            chunk_end += 1

        lines.extend(
            _chunk_with_strings_lines(
                code,
                pos,
                chunk_end,
                indent,
                assembler_profile=assembler_profile,
            )
        )
        pos = chunk_end
    return lines


def emit_data_region(
    handle: TextIO,
    code: bytes,
    start: int,
    end: int,
    labels: dict[int, str],
    reloc_map: dict[int, int],
    string_addrs: set[int],
    reloc_labels: dict[int, str] | None = None,
    indent: str = "    ",
    access_sizes: dict[int, int] | None = None,
    typed_sizes: dict[int, int] | None = None,
    typed_fields: dict[int, TypedDataFieldInfo] | None = None,
    os_kb: _TypedFieldValueKb | None = None,
    addr_comments: dict[int, str] | None = None,
    assembler_profile: AssemblerProfile = VASM_PROFILE,
) -> None:
    for _addr, line in iter_data_region_lines(
        code,
        start,
        end,
        labels,
        reloc_map,
        string_addrs,
        reloc_labels,
        indent=indent,
        access_sizes=access_sizes,
        typed_sizes=typed_sizes,
        typed_fields=typed_fields,
        os_kb=os_kb,
        addr_comments=addr_comments,
        assembler_profile=assembler_profile,
    ):
        handle.write(line)
