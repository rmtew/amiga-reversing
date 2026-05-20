#!/usr/bin/env python3
"""Build a conservative symbol index for extracted Classic Mac OS includes."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


IDENT = r"[A-Za-z_][A-Za-z0-9_]*"


def read_text(path: Path) -> str:
    return path.read_text(encoding="mac_roman", errors="replace")


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def strip_c_comments_keep_lines(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        return "\n" * match.group(0).count("\n")

    text = re.sub(r"/\*.*?\*/", repl, text, flags=re.S)
    text = re.sub(r"//.*", "", text)
    return text


def compact(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def add(items: list[dict[str, object]], seen: set[tuple[str, str, str, int]], **entry: object) -> None:
    key = (str(entry["kind"]), str(entry["name"]), str(entry["source"]), int(entry["line"]))
    if key in seen:
        return
    seen.add(key)
    items.append(entry)


def c_line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def index_c_header(path: Path, root: Path, items: list[dict[str, object]], seen: set[tuple[str, str, str, int]]) -> None:
    original = read_text(path)
    source = rel(path, root)
    text = strip_c_comments_keep_lines(original)

    for match in re.finditer(r"^\s*#\s*define\s+(" + IDENT + r")\b(.*)$", text, flags=re.M):
        name = match.group(1)
        value = compact(match.group(2))
        if name.startswith("__") and name.endswith("__"):
            continue
        add(items, seen, kind="c_macro", name=name, source=source, line=c_line_number(text, match.start()), value=value)

    for match in re.finditer(r"\bstruct\s+(" + IDENT + r")\s*\{", text):
        add(items, seen, kind="c_struct", name=match.group(1), source=source, line=c_line_number(text, match.start()))

    for match in re.finditer(r"\b(?:typedef\s+)?enum\s+(" + IDENT + r")?\s*\{(?P<body>.*?)\}\s*(?P<alias>" + IDENT + r")?", text, flags=re.S):
        name = match.group("alias") or match.group(1)
        if name:
            add(items, seen, kind="c_enum", name=name, source=source, line=c_line_number(text, match.start()))
        body = match.group("body")
        body_offset = match.start("body")
        for enum_match in re.finditer(r"\b(" + IDENT + r")\s*(?:=\s*([^,\n]+))?\s*,?", body):
            enum_name = enum_match.group(1)
            if enum_name in {"enum", "typedef"}:
                continue
            add(
                items,
                seen,
                kind="c_enum_constant",
                name=enum_name,
                source=source,
                line=c_line_number(text, body_offset + enum_match.start()),
                value=compact(enum_match.group(2) or ""),
            )

    for match in re.finditer(r"\btypedef\s+(?!struct\b|enum\b)(?P<decl>[^;{]+?)\s+(?P<name>" + IDENT + r")\s*;", text, flags=re.S):
        add(
            items,
            seen,
            kind="c_typedef",
            name=match.group("name"),
            source=source,
            line=c_line_number(text, match.start()),
            declaration=compact(match.group(0)),
        )

    lines = text.splitlines()
    pending: list[str] = []
    start_line = 0
    for line_no, line in enumerate(lines, 1):
        stripped = line.strip()
        starts_decl = stripped.startswith(("EXTERN_API", "CALLBACK_API", "pascal "))
        if starts_decl and not pending:
            pending = [stripped]
            start_line = line_no
        elif pending:
            pending.append(stripped)
        if pending and ";" in stripped:
            declaration = compact(" ".join(pending).split(";", 1)[0] + ";")
            pending = []
            name_match = re.search(r"\)\s*(" + IDENT + r")\s*\(", declaration)
            if name_match is None and declaration.startswith("pascal "):
                name_match = re.search(r"\b(" + IDENT + r")\s*\(", declaration)
            if name_match is None:
                continue
            add(
                items,
                seen,
                kind="c_function",
                name=name_match.group(1),
                source=source,
                line=start_line,
                declaration=declaration,
            )


def index_asm(path: Path, root: Path, items: list[dict[str, object]], seen: set[tuple[str, str, str, int]]) -> None:
    source = rel(path, root)
    for line_no, line in enumerate(read_text(path).splitlines(), 1):
        stripped = line.split(";", 1)[0].strip()
        match = re.match(r"^(" + IDENT + r")\s+EQU\s+(.+)$", stripped, flags=re.I)
        if match:
            add(items, seen, kind="asm_equ", name=match.group(1), source=source, line=line_no, value=compact(match.group(2)))
            continue
        match = re.match(r"^(" + IDENT + r")\s+RECORD\b", stripped, flags=re.I)
        if match:
            add(items, seen, kind="asm_record", name=match.group(1), source=source, line=line_no)


def index_rez(path: Path, root: Path, items: list[dict[str, object]], seen: set[tuple[str, str, str, int]]) -> None:
    source = rel(path, root)
    text = strip_c_comments_keep_lines(read_text(path))
    for match in re.finditer(r"^\s*#\s*define\s+(" + IDENT + r")\b(.*)$", text, flags=re.M):
        add(items, seen, kind="rez_macro", name=match.group(1), source=source, line=c_line_number(text, match.start()), value=compact(match.group(2)))
    for match in re.finditer(r"\btype\s+'(.{4})'", text):
        add(items, seen, kind="rez_type", name=match.group(1), source=source, line=c_line_number(text, match.start()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("ext/macos_includes/mpw_gm/Interfaces"))
    parser.add_argument("--output", type=Path, default=Path("ext/macos_includes/mpw_gm/index.json"))
    args = parser.parse_args()

    root = args.root
    items: list[dict[str, object]] = []
    seen: set[tuple[str, str, str, int]] = set()

    for path in sorted((root / "CIncludes").glob("*.h")):
        index_c_header(path, root, items, seen)
    for path in sorted((root / "AIncludes").glob("*.a")):
        index_asm(path, root, items, seen)
    for path in sorted((root / "RIncludes").glob("*.r")):
        index_rez(path, root, items, seen)

    by_kind: dict[str, int] = {}
    for item in items:
        by_kind[str(item["kind"])] = by_kind.get(str(item["kind"]), 0) + 1

    document = {
        "schema": "macos_include_index.v1",
        "source": "ext/macos_includes/mpw_gm/Interfaces",
        "indexed_sets": ["CIncludes/*.h", "AIncludes/*.a", "RIncludes/*.r"],
        "item_count": len(items),
        "counts_by_kind": dict(sorted(by_kind.items())),
        "items": sorted(items, key=lambda entry: (str(entry["name"]).lower(), str(entry["kind"]), str(entry["source"]), int(entry["line"]))),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
