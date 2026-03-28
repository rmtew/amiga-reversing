from __future__ import annotations

import struct
from typing import TextIO

from disasm.ascii import is_printable_ascii

_MIN_STRING_LEN = 4


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


def _emit_string(handle: TextIO, text: str, indent: str) -> None:
    parts: list[str] = []
    current: list[str] = []
    for ch in text:
        if is_printable_ascii(ord(ch)) and ch != '"':
            current.append(ch)
        else:
            if current:
                parts.append('"' + "".join(current) + '"')
                current = []
            parts.append(f"${ord(ch):02x}")
    if current:
        parts.append('"' + "".join(current) + '"')
    parts.append("0")
    handle.write(f"{indent}dc.b    {','.join(parts)}\n")


def _emit_hex_bytes(handle: TextIO, data: bytes, indent: str) -> None:
    for i in range(0, len(data), 16):
        row = data[i:i + 16]
        hex_vals = ",".join(f"${b:02x}" for b in row)
        handle.write(f"{indent}dc.b    {hex_vals}\n")


def _safe_string_span(*, start: int, text: str,
                      labels: dict[int, str], reloc_map: dict[int, int]) -> int | None:
    string_end = start + len(text) + 1
    for addr in range(start + 1, string_end):
        if addr in labels or addr in reloc_map:
            return None
    return string_end


def _emit_chunk_with_strings(handle: TextIO, code: bytes, start: int, end: int,
                             indent: str) -> None:
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
        null_term = (run_end < end and code[run_end] == 0)
        min_len = _MIN_STRING_LEN if null_term else 6
        if run_len < min_len:
            continue

        if hex_start < run_start:
            _emit_hex_bytes(handle, code[hex_start:run_start], indent)

        text = code[run_start:run_end].decode("ascii")
        if null_term:
            _emit_string(handle, text, indent)
            pos += 1
        else:
            handle.write(f'{indent}dc.b    "{text}"\n')
        hex_start = pos

    if hex_start < end:
        _emit_hex_bytes(handle, code[hex_start:end], indent)


def emit_data_region(handle: TextIO, code: bytes, start: int, end: int,
                     labels: dict[int, str], reloc_map: dict[int, int],
                     string_addrs: set[int], indent: str = "    ",
                     access_sizes: dict[int, int] | None = None,
                     addr_comments: dict[int, str] | None = None) -> None:
    if addr_comments is None:
        addr_comments = {}
    pos = start
    while pos < end:
        if pos != start and pos in labels:
            comment = addr_comments.get(pos)
            if comment is not None:
                handle.write(f"; {comment}\n")
            handle.write(f"{labels[pos]}:\n")

        if pos in reloc_map and pos + 4 <= end:
            target = reloc_map[pos]
            if target in labels:
                handle.write(f"{indent}dc.l    {labels[target]}\n")
            else:
                val = struct.unpack_from(">I", code, pos)[0]
                handle.write(f"{indent}dc.l    ${val:08x}\n")
            pos += 4
            continue

        if pos in string_addrs:
            text = _try_read_string(code, pos, end)
            if text:
                _emit_string(handle, text, indent)
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
                _emit_string(handle, text, indent)
                pos = string_end
                continue

        if access_sizes and pos in access_sizes:
            asize = access_sizes[pos]
            if asize == 4 and pos + 4 <= end:
                val = struct.unpack_from(">I", code, pos)[0]
                if val in labels:
                    handle.write(f"{indent}dc.l    {labels[val]}\n")
                else:
                    handle.write(f"{indent}dc.l    ${val:08x}\n")
                pos += 4
                continue
            if asize == 2 and pos + 2 <= end:
                word_end = pos + 2
                while access_sizes.get(word_end) == asize and word_end + 2 <= end:
                    if (word_end in labels or word_end in reloc_map
                            or word_end in string_addrs):
                        break
                    word_end += 2
                for row_start in range(pos, word_end, 16):
                    row_end = min(row_start + 16, word_end)
                    vals: list[str] = []
                    for wp in range(row_start, row_end, 2):
                        vals.append(f"${struct.unpack_from('>H', code, wp)[0]:04x}")
                    handle.write(f"{indent}dc.w    {','.join(vals)}\n")
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
                handle.write(f"{indent}dcb.b   {count},0\n")
                pos = zero_end
                continue

        chunk_end = pos + 1
        while chunk_end < end:
            if (chunk_end in labels or chunk_end in reloc_map
                    or chunk_end in string_addrs
                    or (access_sizes and chunk_end in access_sizes)):
                break
            if (code[chunk_end] == 0 and chunk_end + 3 < end
                    and all(code[chunk_end + i] == 0 for i in range(4))):
                break
            chunk_end += 1

        _emit_chunk_with_strings(handle, code, pos, chunk_end, indent)
        pos = chunk_end
