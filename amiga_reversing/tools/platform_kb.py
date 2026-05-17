from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import cast

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_OS_VERSION_ORDER = ("1.0", "1.1", "1.2", "1.3", "2.0", "2.04", "2.1", "3.0", "3.1", "3.5")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report committed Amiga platform KB coverage.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("report", help="Print current platform KB coverage.")
    subparsers.add_parser("check", help="Fail on enforced platform KB consistency issues.")
    args = parser.parse_args(argv)

    report = build_report(PROJECT_ROOT)
    if args.command == "report":
        print(format_report(report))
        return 0
    if args.command == "check":
        violations = check_report(report)
        if violations:
            print("Platform KB check failed:")
            for violation in violations:
                print(f"  - {violation}")
            return 1
        print("Platform KB check passed.")
        return 0
    raise SystemExit(f"Unsupported command: {args.command}")


def build_report(project_root: Path) -> dict[str, object]:
    knowledge = project_root / "knowledge"
    generated = project_root / "src" / "generated"
    includes = _load_json(knowledge / "amiga_ndk_includes_parsed.json")
    other = _load_json(knowledge / "amiga_ndk_other_parsed.json")
    hw_registers = _load_json(knowledge / "amiga_hw_registers.json")
    hw_symbols = _load_json(knowledge / "amiga_hw_symbols.json")
    corrections = _load_json(knowledge / "amiga_ndk_corrections.json")
    hunk = _load_json(knowledge / "amiga_hunk_file.json")
    return {
        "source_inventory": _source_inventory_report(knowledge / "adcd21_inventory.md"),
        "ndk": _ndk_report(includes, other, generated / "amiga_os_runtime.c"),
        "hardware": _hardware_report(hw_registers, hw_symbols),
        "corrections": _corrections_report(corrections),
        "hunk": _hunk_report(hunk),
        "target_platform_summary": _target_platform_summary_report(project_root),
    }


def check_report(report: Mapping[str, object]) -> list[str]:
    violations: list[str] = []
    corrections = cast(Mapping[str, object], report["corrections"])
    if corrections["unknown_review_status"]:
        violations.append(f"corrections have unknown review_status: {corrections['unknown_review_status']}")
    if corrections["missing_citation"]:
        violations.append(f"corrections are missing citations: {corrections['missing_citation']}")
    hunk = cast(Mapping[str, object], report["hunk"])
    half = cast(list[str], hunk["half_represented_record_types"])
    if half:
        violations.append(f"HUNK records are half-represented: {', '.join(half)}")
    ndk = cast(Mapping[str, object], report["ndk"])
    lost = cast(list[str], ndk["raw_availability_versions_not_represented_in_runtime"])
    if lost:
        violations.append(f"raw OS availability precision is not represented in runtime metadata: {', '.join(lost)}")
    return violations


def format_report(report: Mapping[str, object]) -> str:
    source = cast(Mapping[str, object], report["source_inventory"])
    ndk = cast(Mapping[str, object], report["ndk"])
    hardware = cast(Mapping[str, object], report["hardware"])
    corrections = cast(Mapping[str, object], report["corrections"])
    hunk = cast(Mapping[str, object], report["hunk"])
    target_summary = cast(Mapping[str, object], report["target_platform_summary"])
    lines = [
        "Platform KB coverage report",
        "",
        "Source inventory:",
        f"  inventory rows: {source['inventory_rows']}",
        f"  parsed: {source['parsed']}",
        f"  candidate/deferred: {source['candidate_or_deferred']}",
        "",
        "NDK:",
        f"  include paths: {ndk['include_paths']}",
        f"  libraries: {ndk['libraries']}",
        f"  functions: {ndk['functions']}",
        f"  structs: {ndk['structs']}",
        f"  constants: {ndk['constants']}",
        f"  value domains: {ndk['value_domains']}",
        f"  include min-version rows: {ndk['include_min_version_rows']}",
        f"  raw available_since counts: {_format_counts(cast(Mapping[str, int], ndk['raw_available_since_counts']))}",
        f"  normalized compatibility counts: {_format_counts(cast(Mapping[str, int], ndk['normalized_available_since_counts']))}",
        f"  FD/interface version counts: {_format_counts(cast(Mapping[str, int], ndk['fd_version_counts']))}",
        f"  raw OS version rank coverage: {_format_bool_map(cast(Mapping[str, bool], ndk['raw_os_version_rank_coverage']))}",
        "",
        "Hardware:",
        f"  HRM registers: {hardware['hrm_registers']}",
        f"  HRM registers with bit definitions: {hardware['hrm_registers_with_bits']}",
        f"  NDK hardware symbol rows: {hardware['ndk_hardware_symbol_rows']}",
        f"  joined by CPU address: {hardware['joined_cpu_address_rows']}",
        "",
        "Corrections:",
        f"  review status counts: {_format_counts(cast(Mapping[str, int], corrections['review_status_counts']))}",
        f"  missing citation: {corrections['missing_citation']}",
        f"  unknown review status: {corrections['unknown_review_status']}",
        "",
        "HUNK:",
        f"  enum ids: {hunk['enum_ids']}",
        f"  normalized record types: {hunk['record_types']}",
        f"  valid load-file record types: {hunk['valid_load_file_record_types']}",
        f"  half-represented record types: {', '.join(cast(list[str], hunk['half_represented_record_types'])) or 'none'}",
        "",
        "Target platform summary:",
        f"  schema present: {target_summary['schema_present']}",
        f"  os compatibility state coverage: {_format_counts(cast(Mapping[str, int], target_summary['os_compatibility_state_counts']))}",
    ]
    return "\n".join(lines)


def _ndk_report(includes: Mapping[str, object], other: Mapping[str, object], runtime_header: Path) -> dict[str, object]:
    meta = _mapping(includes.get("_meta"))
    libraries = _mapping(includes.get("libraries"))
    functions = [(library_name, function_name, function) for library_name, library in libraries.items() for function_name, function in _mapping(_mapping(library).get("functions")).items()]
    other_functions = _mapping(other.get("functions"))
    raw_available_since = Counter[str]()
    for library in other_functions.values():
        for function in _mapping(library).values():
            version = _string(_mapping(function).get("available_since"))
            if version:
                raw_available_since[version] += 1
    fd_versions = Counter[str]()
    for _library_name, _function_name, function in functions:
        version = _string(_mapping(function).get("fd_version"))
        if version:
            fd_versions[version] += 1
    runtime_text = runtime_header.read_text(encoding="utf-8", errors="ignore") if runtime_header.exists() else ""
    raw_versions = set(raw_available_since)
    runtime_preserves_raw = "available_since_raw" in runtime_text or "available_since_text" in runtime_text
    return {
        "include_paths": len(cast(list[object], meta.get("parsed_include_paths", []))),
        "libraries": len(libraries),
        "functions": len(functions),
        "structs": len(_mapping(includes.get("structs"))),
        "constants": len(_mapping(includes.get("constants"))),
        "value_domains": len(_mapping(meta.get("value_domains"))),
        "include_min_version_rows": len(_mapping(meta.get("include_min_versions"))),
        "raw_available_since_counts": dict(sorted(raw_available_since.items(), key=lambda item: _version_sort_key(item[0]))),
        "normalized_available_since_counts": dict(_normalized_counts(raw_available_since)),
        "fd_version_counts": dict(sorted(fd_versions.items(), key=lambda item: item[0])),
        "raw_os_version_rank_coverage": {version: version in raw_versions for version in RAW_OS_VERSION_ORDER},
        "raw_availability_versions_not_represented_in_runtime": sorted(
            raw_versions - set(_runtime_compatibility_versions(runtime_text)),
            key=_version_sort_key,
        )
        if not runtime_preserves_raw
        else [],
    }


def _hardware_report(hw_registers: Mapping[str, object], hw_symbols: Mapping[str, object]) -> dict[str, object]:
    registers = [item for item in cast(list[object], hw_registers.get("registers", [])) if isinstance(item, dict)]
    symbol_rows = [item for item in cast(list[object], hw_symbols.get("registers", [])) if isinstance(item, dict)]
    hrm_addresses = {_string(item.get("address_68k")) for item in registers}
    symbol_addresses = {_string(item.get("cpu_address")) for item in symbol_rows}
    return {
        "hrm_registers": len(registers),
        "hrm_registers_with_bits": sum(1 for item in registers if isinstance(item.get("bits"), list) and item["bits"]),
        "ndk_hardware_symbol_rows": len(symbol_rows),
        "joined_cpu_address_rows": len((hrm_addresses - {None}) & (symbol_addresses - {None})),
    }


def _corrections_report(corrections: Mapping[str, object]) -> dict[str, object]:
    entries = list(_correction_entries(corrections))
    statuses = Counter(_string(entry.get("review_status")) or "missing" for entry in entries)
    known = {"seeded", "validated"}
    return {
        "entries": len(entries),
        "review_status_counts": dict(sorted(statuses.items())),
        "missing_citation": sum(1 for entry in entries if not _string(entry.get("citation"))),
        "unknown_review_status": sum(1 for entry in entries if (_string(entry.get("review_status")) or "missing") not in known),
    }


def _hunk_report(hunk: Mapping[str, object]) -> dict[str, object]:
    hunk_type = _mapping(_mapping(hunk.get("enums")).get("hunk_type"))
    record_types = _mapping(hunk.get("record_types"))
    groups = _mapping(hunk.get("groups"))
    section_block = _mapping(groups.get("section_block"))
    valid_load = {
        "HUNK_HEADER",
        *cast(list[str], section_block.get("section_start_types", [])),
        *cast(list[str], section_block.get("aux_types", [])),
        *cast(list[str], section_block.get("terminator_types", [])),
    }
    half_represented = sorted(set(hunk_type) - set(record_types))
    return {
        "enum_ids": len(hunk_type),
        "record_types": len(record_types),
        "valid_load_file_record_types": len(valid_load),
        "half_represented_record_types": half_represented,
    }


def _target_platform_summary_report(project_root: Path) -> dict[str, object]:
    state_counts = {"observed": 0, "no_os_calls": 0, "unknown": 0}
    summary_files = list((project_root / "targets").glob("*/platform_summary.json"))
    for path in summary_files:
        payload = _load_json(path)
        os_summary = _mapping(payload.get("os_compatibility"))
        status = _string(os_summary.get("status"))
        if status in state_counts:
            state_counts[status] += 1
    return {
        "schema_present": bool(summary_files),
        "summary_files": len(summary_files),
        "os_compatibility_state_counts": state_counts,
    }


def _source_inventory_report(path: Path) -> dict[str, object]:
    rows = []
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.startswith("| `"):
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) >= 3:
                rows.append(cells[2].lower())
    return {
        "inventory_rows": len(rows),
        "parsed": sum("parsed" in row for row in rows),
        "candidate_or_deferred": sum(any(marker in row for marker in ("not explored", "low priority", "deferred")) for row in rows),
    }


def _correction_entries(value: object) -> Iterable[Mapping[str, object]]:
    if isinstance(value, dict):
        if "review_status" in value:
            yield cast(Mapping[str, object], value)
        for child in value.values():
            yield from _correction_entries(child)
    elif isinstance(value, list):
        for child in value:
            yield from _correction_entries(child)


def _normalized_counts(raw: Mapping[str, int]) -> dict[str, int]:
    counts = Counter[str]()
    for version, count in raw.items():
        counts[_normalize_version(version)] += count
    return dict(sorted(counts.items(), key=lambda item: _version_sort_key(item[0])))


def _normalize_version(version: str) -> str:
    rank = _version_sort_key(version)
    for candidate in ("1.3", "2.0", "3.1", "3.5"):
        if rank <= _version_sort_key(candidate):
            return candidate
    return version


def _runtime_compatibility_versions(runtime_text: str) -> set[str]:
    return set(re.findall(r'"(\d+(?:\.\d+)?)"', runtime_text))


def _format_counts(counts: Mapping[str, int]) -> str:
    return ", ".join(f"{key}={value}" for key, value in counts.items()) or "none"


def _format_bool_map(values: Mapping[str, bool]) -> str:
    return ", ".join(f"{key}={'yes' if value else 'no'}" for key, value in values.items())


def _version_sort_key(version: str) -> int:
    version = "3.0" if version == "3" else version
    try:
        return RAW_OS_VERSION_ORDER.index(version)
    except ValueError:
        return len(RAW_OS_VERSION_ORDER)


def _load_json(path: Path) -> dict[str, object]:
    return cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))


def _mapping(value: object) -> Mapping[str, object]:
    return cast(Mapping[str, object], value) if isinstance(value, dict) else {}


def _string(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


if __name__ == "__main__":
    raise SystemExit(main())
