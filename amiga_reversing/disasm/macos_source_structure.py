"""MPW assembly source-structure parser for Classic Mac OS fixtures."""

from __future__ import annotations

import re
from pathlib import Path

_DIRECTIVES = frozenset(
    {
        "INCLUDE",
        "IMPORT",
        "EXPORT",
        "SEG",
        "MAIN",
        "PROC",
        "FUNC",
        "ENDP",
        "ENDF",
        "ENDPROC",
        "RECORD",
        "ENDR",
        "WITH",
    }
)

_ROUTINE_STARTS = frozenset({"MAIN", "PROC", "FUNC"})
_ROUTINE_ENDS = frozenset({"ENDP", "ENDF", "ENDPROC"})


def parse_mpw_source_files(paths: list[Path]) -> dict[str, object]:
    files = [parse_mpw_source_file(path) for path in paths]
    return {
        "schema_version": 1,
        "kind": "mpw_assembly_source_structure",
        "source_segment_mapping": {
            "kind": "source_membership_only",
            "maps_to_observed_code_resources": False,
            "reason": "source SEG facts are not linked to MPW/Tools/Asm CODE resources by name alone",
        },
        "files": files,
    }


def parse_mpw_source_file(path: Path) -> dict[str, object]:
    text = path.read_bytes().decode("mac_roman")
    return parse_mpw_source_text(text, path=str(path))


def parse_mpw_source_text(text: str, *, path: str) -> dict[str, object]:
    includes: list[dict[str, object]] = []
    imports: list[dict[str, object]] = []
    exports: list[dict[str, object]] = []
    segments: list[dict[str, object]] = []
    routines: list[dict[str, object]] = []
    records: list[dict[str, object]] = []
    with_scopes: list[dict[str, object]] = []
    entry_markers: list[dict[str, object]] = []

    current_segment: str | None = None
    active_routine: dict[str, object] | None = None
    active_records: list[dict[str, object]] = []

    logical_lines = list(_logical_lines(text.splitlines()))
    for logical in logical_lines:
        parsed = _parse_directive(logical["text"])
        if parsed is None:
            continue
        label, directive, operand_text = parsed
        raw_start_line = logical["start_line"]
        raw_end_line = logical["end_line"]
        if not isinstance(raw_start_line, int) or not isinstance(raw_end_line, int):
            continue
        start_line = raw_start_line
        end_line = raw_end_line

        if directive == "INCLUDE":
            includes.append(
                {
                    "path": _first_quoted_or_token(operand_text),
                    "line": start_line,
                    "line_end": end_line,
                }
            )
            continue
        if directive == "SEG":
            name = _first_quoted_or_token(operand_text)
            current_segment = name
            segments.append(
                {
                    "name": name,
                    "line": start_line,
                    "line_end": end_line,
                    "source_fact_kind": "source_segment",
                    "maps_to_observed_code_resource": False,
                }
            )
            continue
        if directive in {"IMPORT", "EXPORT"}:
            facts = imports if directive == "IMPORT" else exports
            for symbol in _symbol_refs(operand_text):
                facts.append(
                    {
                        **symbol,
                        "line": start_line,
                        "line_end": end_line,
                        "routine": active_routine.get("name") if active_routine else None,
                        "segment": current_segment,
                    }
                )
            continue
        if directive in _ROUTINE_STARTS:
            if active_routine is not None and "line_end" not in active_routine:
                active_routine["line_end"] = start_line - 1
            name = label or _first_quoted_or_token(operand_text) or directive
            routine = {
                "name": name,
                "kind": directive.lower(),
                "line": start_line,
                "line_end": end_line,
                "segment": current_segment,
                "source_fact_kind": "source_entry_marker" if directive == "MAIN" else "source_routine",
                "exported": "EXPORT" in _operand_words(operand_text),
                "maps_to_observed_code_resource": False,
            }
            routines.append(routine)
            active_routine = routine
            if directive == "MAIN":
                entry_markers.append(
                    {
                        "name": name,
                        "kind": "source_main_entry",
                        "line": start_line,
                        "line_end": end_line,
                        "segment": current_segment,
                        "program_kind_claim": None,
                        "maps_to_observed_code_resource": False,
                    }
                )
            continue
        if directive in _ROUTINE_ENDS:
            if active_routine is not None:
                active_routine["line_end"] = end_line
                active_routine = None
            continue
        if directive == "RECORD":
            name = label or _first_quoted_or_token(operand_text) or "anonymous"
            record = {
                "name": name,
                "line": start_line,
                "line_end": end_line,
                "routine": active_routine.get("name") if active_routine else None,
                "segment": current_segment,
            }
            records.append(record)
            active_records.append(record)
            continue
        if directive == "ENDR":
            if active_records:
                active_records.pop()["line_end"] = end_line
            continue
        if directive == "WITH":
            with_scopes.append(
                {
                    "targets": [symbol["symbol"] for symbol in _symbol_refs(operand_text)],
                    "line": start_line,
                    "line_end": end_line,
                    "routine": active_routine.get("name") if active_routine else None,
                    "segment": current_segment,
                }
            )

    last_line = len(text.splitlines())
    if active_routine is not None and "line_end" not in active_routine:
        active_routine["line_end"] = last_line
    for record in active_records:
        if "line_end" not in record:
            record["line_end"] = last_line

    return {
        "path": path,
        "file_name": Path(path).name,
        "encoding": "mac_roman",
        "line_count": last_line,
        "includes": includes,
        "imports": imports,
        "exports": exports,
        "segments": segments,
        "routines": routines,
        "records": records,
        "with_scopes": with_scopes,
        "entry_markers": entry_markers,
        "source_segment_mapping": {
            "kind": "source_membership_only",
            "maps_to_observed_code_resources": False,
        },
    }


def _logical_lines(lines: list[str]) -> list[dict[str, object]]:
    logical: list[dict[str, object]] = []
    buffer = ""
    start_line = 1
    for index, line in enumerate(lines, start=1):
        stripped = line.rstrip()
        if not buffer:
            start_line = index
        if stripped.endswith("\\"):
            buffer += stripped[:-1] + " "
            continue
        buffer += stripped
        logical.append({"start_line": start_line, "end_line": index, "text": buffer})
        buffer = ""
    if buffer:
        logical.append({"start_line": start_line, "end_line": len(lines), "text": buffer})
    return logical


def _parse_directive(text: object) -> tuple[str | None, str, str] | None:
    if not isinstance(text, str):
        return None
    code = _strip_inline_comment(text).rstrip()
    if not code.strip() or code.lstrip().startswith("*"):
        return None
    starts_with_space = bool(code[:1].isspace())
    tokens = code.split(None, 2)
    if not tokens:
        return None
    first = tokens[0].upper()
    if starts_with_space or first in _DIRECTIVES:
        if first not in _DIRECTIVES:
            return None
        return None, first, _operand_from_tokens(tokens, 1)
    if len(tokens) < 2:
        return None
    second = tokens[1].upper()
    if second not in _DIRECTIVES:
        return None
    return tokens[0], second, _operand_from_tokens(tokens, 2)


def _operand_from_tokens(tokens: list[str], start_index: int) -> str:
    if len(tokens) <= start_index:
        return ""
    if len(tokens) == start_index + 1:
        return tokens[start_index]
    return f"{tokens[start_index]} {tokens[start_index + 1]}"


def _strip_inline_comment(text: str) -> str:
    quote: str | None = None
    for index, char in enumerate(text):
        if char in {"'", '"'}:
            quote = None if quote == char else char if quote is None else quote
        elif char == ";" and quote is None:
            return text[:index]
    return text


def _first_quoted_or_token(text: str) -> str:
    quoted = re.search(r"""['"]([^'"]+)['"]""", text)
    if quoted:
        return quoted.group(1)
    tokens = _operand_words(text)
    return tokens[0] if tokens else ""


def _operand_words(text: str) -> list[str]:
    return [word for word in re.split(r"[\s,]+", text.strip()) if word]


def _symbol_refs(text: str) -> list[dict[str, str]]:
    payload = text.strip()
    refs: list[dict[str, str]] = []
    parenthesized = re.match(r"^\(([^)]*)\)(?::([^,\s]+))?", payload)
    if parenthesized:
        type_name = parenthesized.group(2)
        for name in _split_symbols(parenthesized.group(1)):
            ref = {"symbol": name}
            if type_name:
                ref["type"] = type_name
            refs.append(ref)
        payload = payload[parenthesized.end() :].lstrip(" ,")
    for item in _split_symbols(payload):
        if ":" in item:
            symbol, type_name = item.split(":", 1)
            refs.append({"symbol": symbol.strip(), "type": type_name.strip()})
        else:
            refs.append({"symbol": item})
    return [ref for ref in refs if ref["symbol"]]


def _split_symbols(text: str) -> list[str]:
    symbols: list[str] = []
    for part in text.replace("\\", " ").split(","):
        symbols.extend(word.strip() for word in part.split() if word.strip())
    return symbols
