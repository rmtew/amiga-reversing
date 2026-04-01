from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LINE_LENGTH = 140
DECLARATION_RE = re.compile(
    r"^\s*(?:const\s+)?(?:u?int(?:8|16|32|64)_t|size_t|ptrdiff_t|char|float|double|FILE)\s+\*?[A-Za-z_]\w*\s*(?:=\s*[^;]+)?;$"
)
FUNCTION_START_RE = re.compile(r"^\s*(?:static\s+)?(?:[A-Za-z_]\w*[\s\*]+)+[A-Za-z_]\w*\(\s*$")
BANNED_INTEGER_TYPE_RE = re.compile(
    r"\b(?:unsigned\s+long|signed\s+long|unsigned\s+short|signed\s+short|long|short)\b"
)
CONTROL_HEADS = {"if", "for", "while", "switch"}
SINGLE_CLAUSE_BODY_RE = re.compile(r"^\s*(?:return\b.*|break;|continue;)\s*$")


@dataclass(frozen=True)
class LineInfo:
    number: int
    raw: str
    code: str
    stripped: str
    indent: int
    paren_delta: int


def _scan_lines(text: str) -> list[LineInfo]:
    lines: list[LineInfo] = []
    in_block_comment = False
    in_string = False
    in_char = False
    escape = False
    for number, raw in enumerate(text.splitlines(), start=1):
        chars: list[str] = []
        i = 0
        while i < len(raw):
            ch = raw[i]
            nxt = raw[i + 1] if i + 1 < len(raw) else ""
            if in_block_comment:
                chars.append(" ")
                if ch == "*" and nxt == "/":
                    chars.append(" ")
                    in_block_comment = False
                    i += 2
                    continue
                i += 1
                continue
            if in_string:
                chars.append(" ")
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                i += 1
                continue
            if in_char:
                chars.append(" ")
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == "'":
                    in_char = False
                i += 1
                continue
            if ch == "/" and nxt == "*":
                chars.append(" ")
                chars.append(" ")
                in_block_comment = True
                i += 2
                continue
            if ch == "/" and nxt == "/":
                chars.extend(" " for _ in raw[i:])
                break
            if ch == '"':
                chars.append(" ")
                in_string = True
                i += 1
                continue
            if ch == "'":
                chars.append(" ")
                in_char = True
                i += 1
                continue
            chars.append(ch)
            i += 1
        code = "".join(chars)
        stripped = code.strip()
        indent = len(raw) - len(raw.lstrip(" "))
        lines.append(LineInfo(number, raw, code, stripped, indent, code.count("(") - code.count(")")))
    return lines


def _is_simple_declaration(line: LineInfo) -> bool:
    return DECLARATION_RE.match(line.code.strip()) is not None


def _is_function_signature_start(line: LineInfo) -> bool:
    if not FUNCTION_START_RE.match(line.code):
        return False
    match = re.match(r"^\s*([A-Za-z_]\w*)\b", line.code)
    head = match.group(1) if match else None
    if head in CONTROL_HEADS:
        return False
    if "=" in line.code:
        return False
    return True


def _is_call_start(line: LineInfo) -> bool:
    if not line.stripped.endswith("("):
        return False
    if _is_function_signature_start(line):
        return False
    return bool(re.search(r"[A-Za-z_]\w*\(\s*$", line.code))


def _collect_multiline_span(lines: list[LineInfo], start_index: int) -> tuple[list[LineInfo], int] | None:
    parts = [lines[start_index]]
    depth = lines[start_index].paren_delta
    index = start_index + 1
    while index < len(lines) and depth > 0:
        parts.append(lines[index])
        depth += lines[index].paren_delta
        index += 1
    if depth != 0 or len(parts) <= 1:
        return None
    return parts, index


def _check_multiline_signature(lines: list[LineInfo], path: Path, issues: list[str], line_length: int) -> None:
    i = 0
    while i < len(lines):
        line = lines[i]
        if not _is_function_signature_start(line):
            i += 1
            continue
        span = _collect_multiline_span(lines, i)
        if span is None:
            issues.append(f"{path}:{line.number}: unterminated multiline function signature")
            return
        args, next_index = span
        args = args[1:]
        if not args or not (args[-1].stripped.endswith(") {") or args[-1].stripped.endswith(");")):
            issues.append(f"{path}:{line.number}: unterminated multiline function signature")
            return
        for k, arg_line in enumerate(args):
            if arg_line.stripped and arg_line.indent < 4:
                issues.append(f"{path}:{line.number}: multiline signature args must use 4-space indent")
                break
            if k != len(args) - 1:
                if not arg_line.stripped.endswith(","):
                    issues.append(f"{path}:{line.number}: multiline signature continuation must preserve comma placement")
                    break
            else:
                if not (arg_line.stripped.endswith(") {") or arg_line.stripped.endswith(");")):
                    issues.append(f"{path}:{line.number}: closing ')' must stay on the last signature line")
                    break
        else:
            first_suffix = "," if len(args) > 1 else ""
            if len(line.raw.rstrip() + args[0].stripped + first_suffix) <= line_length:
                issues.append(f"{path}:{line.number}: opening signature line is too sparse; keep leading arguments on it")
            comma_counts = [arg.raw.rstrip().count(",") for arg in args[:-1]]
            if len(args) >= 3 and comma_counts and max(comma_counts) <= 1:
                issues.append(f"{path}:{line.number}: multiline signature wrap is too sparse; combine arguments more concisely")
        i = next_index


def _check_multiline_calls(lines: list[LineInfo], path: Path, issues: list[str], line_length: int) -> None:
    i = 0
    while i < len(lines):
        line = lines[i]
        if not _is_call_start(line):
            i += 1
            continue
        if line.paren_delta <= 0:
            i += 1
            continue
        span = _collect_multiline_span(lines, i)
        if span is None:
            i += 1
            continue
        parts, next_index = span
        for part in parts[1:]:
            if part.stripped and part.indent < 4:
                issues.append(f"{path}:{line.number}: multiline call continuation must stay indented")
                break
        if parts[-1].stripped.startswith(")") or parts[-1].stripped.startswith(");") or parts[-1].stripped.startswith(") "):
            issues.append(f"{path}:{line.number}: closing ')' must stay on the last call line")
        first_suffix = "," if len(parts) > 2 else ""
        string_literal_wrap = parts[1].raw.strip().startswith('"')
        if not string_literal_wrap and len(line.raw.rstrip() + parts[1].stripped + first_suffix) <= line_length:
            issues.append(f"{path}:{line.number}: opening call line is too sparse; keep leading arguments on it")
        comma_counts = [part.raw.rstrip().count(",") for part in parts[1:-1]]
        if not string_literal_wrap and len(parts) >= 4 and comma_counts and max(comma_counts) <= 1:
            issues.append(f"{path}:{line.number}: multiline call wrap is too sparse; combine arguments more concisely")
        flattened = " ".join(part.stripped for part in parts)
        if not string_literal_wrap and len(flattened) <= line_length:
            issues.append(f"{path}:{line.number}: multiline call wrap is unnecessary; keep it on one line")
        i = next_index


def _check_wrapped_boolean_continuations(lines: list[LineInfo], path: Path, issues: list[str]) -> None:
    for line in lines:
        if line.stripped.startswith("||") or line.stripped.startswith("&&"):
            if line.indent < 4:
                issues.append(f"{path}:{line.number}: wrapped boolean continuation must stay indented")


def _check_unindented_wrapped_call_starts(lines: list[LineInfo], path: Path, issues: list[str]) -> None:
    for index, line in enumerate(lines):
        if _is_function_signature_start(line):
            continue
        if line.raw.startswith("if (") and not line.stripped.endswith("{") and line.paren_delta > 0:
            prev = lines[index - 1].stripped if index > 0 else ""
            if prev.endswith("{") or prev.endswith("}") or prev.endswith(";") or prev == "":
                issues.append(f"{path}:{line.number}: multiline call continuation must stay indented")


def _check_single_clause_if_compaction(lines: list[LineInfo], path: Path, issues: list[str]) -> None:
    for index in range(len(lines) - 2):
        first = lines[index].stripped
        second = lines[index + 1].stripped
        third = lines[index + 2].stripped
        if not (first.startswith("if (") and first.endswith("{")):
            continue
        if not SINGLE_CLAUSE_BODY_RE.match(second):
            continue
        if third != "}":
            continue
        compact = f"{first[:-1].rstrip()} {second}"
        if len(compact) > DEFAULT_LINE_LENGTH:
            continue
        issues.append(f"{path}:{lines[index].number}: single-clause if with return/break/continue should stay on one line")
    for index in range(len(lines) - 4):
        first = lines[index].stripped
        third = lines[index + 2].stripped
        fourth = lines[index + 3].stripped
        fifth = lines[index + 4].stripped
        if not (first.startswith("if (") and first.endswith("{")):
            continue
        if third != "} else {":
            continue
        if fourth == "" or not fourth.endswith(";"):
            continue
        if fifth != "}":
            continue
        compact = f"{first[:-1].rstrip()} {lines[index + 1].stripped} else {fourth}"
        if len(compact) > DEFAULT_LINE_LENGTH:
            continue
        issues.append(f"{path}:{lines[index].number}: single-clause if/else should stay compact")


def _check_compact_local_declarations(lines: list[LineInfo], path: Path, issues: list[str]) -> None:
    brace_depth = 0
    function_depth: int | None = None
    run_start: int | None = None
    run_indent: int | None = None
    run_count = 0
    for line in lines:
        stripped = line.stripped
        if function_depth is None and (stripped.endswith(") {") or stripped == "{"):
            if stripped.endswith(") {"):
                function_depth = brace_depth + 1
        if _is_simple_declaration(line) and function_depth is not None:
            if run_start is None or line.indent != run_indent:
                run_start = line.number
                run_indent = line.indent
                run_count = 1
            else:
                run_count += 1
        else:
            if run_start is not None and run_count >= 6:
                issues.append(f"{path}:{run_start}: local declaration block is too tall; combine related entries more concisely")
            run_start = None
            run_indent = None
            run_count = 0
        brace_depth += line.code.count("{")
        brace_depth -= line.code.count("}")
        if function_depth is not None and brace_depth < function_depth:
            function_depth = None
    if run_start is not None and run_count >= 6:
        issues.append(f"{path}:{run_start}: local declaration block is too tall; combine related entries more concisely")


def check_file(path: Path, line_length: int) -> list[str]:
    issues: list[str] = []
    lines = _scan_lines(path.read_text(encoding="utf-8"))
    for line in lines:
        if "\t" in line.raw:
            issues.append(f"{path}:{line.number}: tabs are not allowed")
        if line.raw.rstrip() != line.raw:
            issues.append(f"{path}:{line.number}: trailing whitespace")
        if len(line.raw) > line_length:
            issues.append(f"{path}:{line.number}: line exceeds {line_length} columns")
        if BANNED_INTEGER_TYPE_RE.search(line.code):
            issues.append(f"{path}:{line.number}: use stdint.h fixed-width types instead of plain short/long")
    _check_multiline_signature(lines, path, issues, line_length)
    _check_multiline_calls(lines, path, issues, line_length)
    _check_wrapped_boolean_continuations(lines, path, issues)
    _check_unindented_wrapped_call_starts(lines, path, issues)
    _check_single_clause_if_compaction(lines, path, issues)
    _check_compact_local_declarations(lines, path, issues)
    return issues


def _iter_default_paths() -> list[Path]:
    excluded = {"m68k_asm_tables.c", "m68k_asm_tables.h"}
    return [
        path
        for path in sorted((ROOT / "src").glob("*.c")) + sorted((ROOT / "src").glob("*.h"))
        if path.name not in excluded
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check local C style rules.")
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--line-length", type=int, default=DEFAULT_LINE_LENGTH)
    args = parser.parse_args(argv)
    paths = [path if path.is_absolute() else (ROOT / path) for path in args.paths] if args.paths else _iter_default_paths()
    issues: list[str] = []
    for path in paths:
        if path.suffix not in {".c", ".h"} or not path.is_file():
            continue
        issues.extend(check_file(path, args.line_length))
    if issues:
        sys.stdout.write("\n".join(issues) + "\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
