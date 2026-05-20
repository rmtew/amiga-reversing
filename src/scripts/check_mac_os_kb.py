#!/usr/bin/env python3
"""Check the seeded Classic Mac OS knowledge file against local sources."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kb", type=Path, default=Path("knowledge/mac_os.json"))
    args = parser.parse_args()

    kb_path = resolve(args.kb)
    data = json.loads(kb_path.read_text(encoding="utf-8"))
    errors: list[str] = []

    if data.get("_meta", {}).get("name") != "mac_os":
        errors.append("_meta.name must be mac_os")

    file_manager = data.get("api_families", {}).get("file_manager")
    if not isinstance(file_manager, dict):
        errors.append("api_families.file_manager missing")
    else:
        errors.extend(check_paths(data))
        errors.extend(check_line_refs(data))
        errors.extend(check_file_manager(file_manager))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"checked {rel(kb_path)}")
    print(f"file_manager records={len(file_manager['record_types'])} routines={len(file_manager['routines'])}")
    return 0


def resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def iter_source_refs(value: Any) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if isinstance(value, dict):
        if "path" in value and ("line" in value or "lines" in value or "page" in value):
            refs.append(value)
        for child in value.values():
            refs.extend(iter_source_refs(child))
    elif isinstance(value, list):
        for child in value:
            refs.extend(iter_source_refs(child))
    return refs


def iter_paths(value: Any) -> set[str]:
    paths: set[str] = set()
    if isinstance(value, dict):
        path = value.get("path")
        if isinstance(path, str):
            paths.add(path)
        for child in value.values():
            paths.update(iter_paths(child))
    elif isinstance(value, list):
        for child in value:
            paths.update(iter_paths(child))
    return paths


def read_lines(path: str) -> list[str]:
    return resolve(path).read_text(encoding="utf-8", errors="replace").splitlines()


def line_window(path: str, start: int, end: int) -> str:
    lines = read_lines(path)
    return "\n".join(lines[start - 1 : end])


def check_paths(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for path in sorted(iter_paths(data)):
        if not resolve(path).exists():
            errors.append(f"missing source path {path}")
    return errors


def check_line_refs(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for ref in iter_source_refs(data):
        path = ref.get("path")
        if not isinstance(path, str) or not resolve(path).exists():
            continue
        line_count = len(read_lines(path))
        if "line" in ref:
            line = ref["line"]
            if not isinstance(line, int) or line < 1 or line > line_count:
                errors.append(f"{path}: bad line {line}")
        if "lines" in ref:
            lines = ref["lines"]
            if (
                not isinstance(lines, list)
                or len(lines) != 2
                or not all(isinstance(item, int) for item in lines)
                or lines[0] < 1
                or lines[1] < lines[0]
                or lines[1] > line_count
            ):
                errors.append(f"{path}: bad line range {lines}")
    return errors


def check_file_manager(file_manager: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(check_calling_convention(file_manager))
    errors.extend(check_record_offsets(file_manager))
    errors.extend(check_routines(file_manager))
    errors.extend(check_macro_aliases(file_manager))
    return errors


def check_calling_convention(file_manager: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    convention = file_manager["calling_conventions"]["pb_trap_68k"]
    if convention.get("parameter_registers", {}).get("paramBlock") != "A0":
        errors.append("pb_trap_68k paramBlock must be A0")
    if convention.get("return_registers", {}).get("OSErr") != "D0":
        errors.append("pb_trap_68k OSErr must be D0")
    source = convention["source"]
    text = line_window(source["path"], source["lines"][0], source["lines"][1])
    if "paramBlock" not in text or "A0" not in text:
        errors.append("pb_trap_68k source does not show paramBlock => A0")
    if "OSErr" not in text or "D0" not in text:
        errors.append("pb_trap_68k source does not show OSErr <= D0")
    return errors


def check_record_offsets(file_manager: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    header = file_manager["common_parameter_block_header"]
    source = header["asm_source"]
    text = line_window(source["path"], source["lines"][0], source["lines"][1])
    for field in header["fields"]:
        name = field["name"]
        offset = int(field["offset"])
        storage = field["asm_storage"]
        storage_pattern = r"\s+".join(re.escape(part) for part in storage.split())
        pattern = rf"\b{re.escape(name)}\b.*{storage_pattern}.*offset:\s+\$[0-9A-Fa-f]+\s+\({offset}\)"
        if not re.search(pattern, text):
            errors.append(f"common_parameter_block_header.{name}: asm offset/storage mismatch")
    return errors


def check_routines(file_manager: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    conventions = file_manager["calling_conventions"]
    for routine in file_manager["routines"]:
        name = routine["name"]
        if routine.get("calling_convention") not in conventions:
            errors.append(f"{name}: unknown calling convention {routine.get('calling_convention')}")
        c_source = routine["c_source"]
        c_text = line_window(c_source["path"], c_source["lines"][0], c_source["lines"][1])
        if name not in c_text:
            errors.append(f"{name}: C source range does not contain routine name")
        for word in routine["trap_words"]:
            if word not in c_text:
                errors.append(f"{name}: C source range missing trap word {word}")
        asm_source = routine["asm_source"]
        asm_text = line_window(asm_source["path"], asm_source["lines"][0], asm_source["lines"][1])
        if name not in asm_text:
            errors.append(f"{name}: asm source range does not contain routine name")
        for word in routine["trap_words"]:
            if not asm_contains_trap_word(asm_text, word):
                errors.append(f"{name}: asm source range missing trap word {asm_word_label(word)}")
        if "paramBlock" not in asm_text or "A0" not in asm_text:
            errors.append(f"{name}: asm source range missing paramBlock/A0 protocol")
        if "OSErr" not in asm_text or "D0" not in asm_text:
            errors.append(f"{name}: asm source range missing OSErr/D0 protocol")
    return errors


def asm_word_label(word: str) -> str:
    return "$" + word.removeprefix("0x").upper()


def asm_contains_trap_word(text: str, word: str) -> bool:
    if asm_word_label(word) in text:
        return True
    value = int(word, 16)
    if value & 0xFF00 == 0x7000:
        immediate = value & 0xFF
        return re.search(rf"\bmoveq\b\s+#\s*{immediate}\s*,\s*D0\b", text, re.IGNORECASE) is not None
    return False


def check_macro_aliases(file_manager: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    routines = {routine["name"] for routine in file_manager["routines"]}
    for alias, spec in file_manager["macro_aliases"].items():
        sync = spec.get("sync")
        if sync not in routines:
            errors.append(f"{alias}: sync routine {sync} not present in seeded routines")
        source = spec["source"]
        text = line_window(source["path"], source["line"], source["line"])
        if alias not in text or spec["sync"] not in text or spec["async"] not in text:
            errors.append(f"{alias}: macro source line does not match sync/async mapping")
    return errors


if __name__ == "__main__":
    raise SystemExit(main())
