from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from collections.abc import Iterable, Mapping, MutableMapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import cast

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_OS_VERSION_ORDER = ("1.0", "1.1", "1.2", "1.3", "2.0", "2.04", "2.1", "3.0", "3.1", "3.5")
KNOWN_CORRECTION_REVIEW_STATUSES = {"seeded", "validated"}


@dataclass(frozen=True)
class CorrectionRecord:
    id: str
    category: str
    path: tuple[str | int, ...]
    entry: MutableMapping[str, object]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report committed Amiga platform KB coverage.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("report", help="Print current platform KB coverage.")
    subparsers.add_parser("check", help="Fail on enforced platform KB consistency issues.")
    corrections_parser = subparsers.add_parser("corrections", help="Review Amiga NDK corrections.")
    correction_subparsers = corrections_parser.add_subparsers(dest="corrections_command", required=True)
    correction_subparsers.add_parser("list", help="List corrections and review state.")
    correction_subparsers.add_parser("check", help="Fail on corrections review consistency issues.")
    promote_parser = correction_subparsers.add_parser("promote", help="Promote one seeded correction.")
    promote_parser.add_argument("correction_id")
    promote_parser.add_argument("--reviewer", required=True)
    args = parser.parse_args(argv)

    if args.command == "corrections":
        corrections_path = PROJECT_ROOT / "knowledge" / "amiga_ndk_corrections.json"
        if args.corrections_command == "list":
            print(format_corrections_list(build_corrections_report(PROJECT_ROOT)))
            return 0
        if args.corrections_command == "check":
            violations = check_corrections_report(build_corrections_report(PROJECT_ROOT))
            if violations:
                print("Corrections check failed:")
                for violation in violations:
                    print(f"  - {violation}")
                return 1
            print("Corrections check passed.")
            return 0
        if args.corrections_command == "promote":
            try:
                promote_correction(corrections_path, args.correction_id, args.reviewer)
            except ValueError as exc:
                print(f"Corrections promote failed: {exc}")
                return 1
            print(f"Promoted correction: {args.correction_id}")
            return 0
        raise SystemExit(f"Unsupported corrections command: {args.corrections_command}")

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
    violations.extend(check_corrections_report(corrections))
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
        f"  unsupported record types: {', '.join(cast(list[str], hunk['unsupported_record_types'])) or 'none'}",
        f"  half-represented record types: {', '.join(cast(list[str], hunk['half_represented_record_types'])) or 'none'}",
        "",
        "Target platform summary:",
        f"  schema present: {target_summary['schema_present']}",
        f"  os compatibility state coverage: {_format_counts(cast(Mapping[str, int], target_summary['os_compatibility_state_counts']))}",
    ]
    return "\n".join(lines)


def build_corrections_report(project_root: Path) -> dict[str, object]:
    return _corrections_report(_load_json(project_root / "knowledge" / "amiga_ndk_corrections.json"))


def check_corrections_report(corrections: Mapping[str, object]) -> list[str]:
    violations: list[str] = []
    if corrections["unknown_review_status"]:
        violations.append(f"corrections have unknown review_status: {corrections['unknown_review_status']}")
    if corrections["missing_citation"]:
        violations.append(f"corrections are missing citations: {corrections['missing_citation']}")
    duplicate_ids = cast(list[str], corrections["duplicate_ids"])
    if duplicate_ids:
        violations.append(f"corrections have duplicate ids: {', '.join(duplicate_ids)}")
    missing_provenance = cast(list[str], corrections["validated_without_review_provenance"])
    if missing_provenance:
        violations.append(
            f"validated corrections are missing review provenance: {', '.join(missing_provenance)}"
        )
    return violations


def format_corrections_list(corrections: Mapping[str, object]) -> str:
    records = cast(list[Mapping[str, object]], corrections["records"])
    lines = ["id\tcategory\ttarget\tsource_file\tcitation\treason\treview_status"]
    for record in records:
        lines.append(
            "\t".join(
                [
                    _string(record.get("id")) or "-",
                    _string(record.get("category")) or "-",
                    _string(record.get("target")) or "-",
                    _string(record.get("source_file")) or "-",
                    _string(record.get("citation")) or "-",
                    _string(record.get("reason")) or "-",
                    _string(record.get("review_status")) or "-",
                ]
            )
        )
    return "\n".join(lines)


def promote_correction(corrections_path: Path, correction_id: str, reviewer: str, today: date | None = None) -> None:
    if not reviewer.strip():
        raise ValueError("reviewer is required")
    payload = _load_json(corrections_path)
    records = list(_correction_records(payload))
    matches = [record for record in records if record.id == correction_id]
    if not matches:
        raise ValueError(f"unknown correction id: {correction_id}")
    if len(matches) > 1:
        raise ValueError(f"duplicate correction id: {correction_id}")
    record = matches[0]
    status = _string(record.entry.get("review_status"))
    if status != "seeded":
        raise ValueError(f"correction {correction_id} is {status or 'missing'}, not seeded")
    if not _string(record.entry.get("citation")):
        raise ValueError(f"correction {correction_id} cannot be promoted without a citation")
    record.entry["review_status"] = "validated"
    record.entry["reviewed_by"] = reviewer.strip()
    record.entry["reviewed_at"] = (today or date.today()).isoformat()
    corrections_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


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
    records = list(_correction_records(cast(MutableMapping[str, object], corrections)))
    statuses = Counter(_string(record.entry.get("review_status")) or "missing" for record in records)
    duplicate_ids = sorted(id_ for id_, count in Counter(record.id for record in records).items() if count > 1)
    return {
        "entries": len(records),
        "records": [_correction_record_row(record) for record in records],
        "review_status_counts": dict(sorted(statuses.items())),
        "missing_citation": [
            record.id for record in records if not _string(record.entry.get("citation"))
        ],
        "unknown_review_status": [
            f"{record.id}={_string(record.entry.get('review_status')) or 'missing'}"
            for record in records
            if (_string(record.entry.get("review_status")) or "missing") not in KNOWN_CORRECTION_REVIEW_STATUSES
        ],
        "duplicate_ids": duplicate_ids,
        "validated_without_review_provenance": [
            record.id
            for record in records
            if _string(record.entry.get("review_status")) == "validated" and not _has_review_provenance(record.entry)
        ],
    }


def _hunk_report(hunk: Mapping[str, object]) -> dict[str, object]:
    hunk_type = _mapping(_mapping(hunk.get("enums")).get("hunk_type"))
    record_types = _mapping(hunk.get("record_types"))
    unsupported = _mapping(hunk.get("unsupported_record_types"))
    groups = _mapping(hunk.get("groups"))
    section_block = _mapping(groups.get("section_block"))
    valid_load = {
        "HUNK_HEADER",
        *cast(list[str], section_block.get("section_start_types", [])),
        *cast(list[str], section_block.get("aux_types", [])),
        *cast(list[str], section_block.get("terminator_types", [])),
    }
    half_represented = sorted(set(hunk_type) - set(record_types) - set(unsupported))
    return {
        "enum_ids": len(hunk_type),
        "record_types": len(record_types),
        "valid_load_file_record_types": len(valid_load),
        "unsupported_record_types": sorted(unsupported),
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


def _correction_records(
    value: object, path: tuple[str | int, ...] = (), category: str | None = None
) -> Iterable[CorrectionRecord]:
    if isinstance(value, dict):
        if "review_status" in value:
            entry = cast(MutableMapping[str, object], value)
            record_category = category or _category_from_path(path)
            yield CorrectionRecord(
                id=_correction_id(record_category, entry, path),
                category=record_category,
                path=path,
                entry=entry,
            )
        for key, child in value.items():
            child_category = key if key != "_meta" else category
            yield from _correction_records(child, (*path, key), child_category)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _correction_records(child, (*path, index), category)


def _correction_record_row(record: CorrectionRecord) -> dict[str, object]:
    return {
        "id": record.id,
        "category": record.category,
        "target": _correction_target(record.entry),
        "source_file": _correction_source_file(record.entry),
        "citation": _string(record.entry.get("citation")) or "",
        "reason": _correction_reason(record.entry),
        "review_status": _string(record.entry.get("review_status")) or "missing",
    }


def _category_from_path(path: tuple[str | int, ...]) -> str:
    for segment in reversed(path):
        if isinstance(segment, str) and segment != "_meta":
            return segment
    return "correction"


def _correction_id(category: str, entry: Mapping[str, object], path: tuple[str | int, ...]) -> str:
    explicit = _string(entry.get("id"))
    if explicit:
        return explicit
    parts = [category]
    for key in (
        "library",
        "function",
        "input",
        "struct",
        "i_struct",
        "field",
        "domain",
        "name",
        "address",
        "reg",
    ):
        value = entry.get(key)
        if value is not None:
            parts.append(str(value))
    if len(parts) == 1:
        parts.extend(str(segment) for segment in path)
    return _slug("-".join(parts))


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()


def _correction_target(entry: Mapping[str, object]) -> str:
    library = _string(entry.get("library"))
    function = _string(entry.get("function"))
    input_name = _string(entry.get("input"))
    if library and function and input_name:
        return f"{library}/{function}/{input_name}"
    if library and function:
        return f"{library}/{function}"
    struct = _string(entry.get("struct")) or _string(entry.get("i_struct"))
    field = _string(entry.get("field")) or _string(entry.get("name")) or _string(entry.get("input"))
    if struct and field:
        return f"{struct}.{field}"
    for key in ("name", "domain", "address", "type", "semantic_kind"):
        value = entry.get(key)
        if value is not None:
            return str(value)
    return "-"


def _correction_source_file(entry: Mapping[str, object]) -> str:
    for key in ("source_file", "source_path", "include_file", "include", "file", "path"):
        value = _string(entry.get(key))
        if value:
            return value
    citation = _string(entry.get("citation"))
    if citation:
        words = citation.split()
        if len(words) >= 2 and words[1] == "autodoc":
            return f"{words[0]} autodoc"
        if citation.startswith("ROM Kernel Reference Manual"):
            return "ROM Kernel Reference Manual"
        return words[0] if words else "-"
    value = _string(entry.get("seed_origin"))
    if value:
        return value
    return "-"


def _correction_reason(entry: Mapping[str, object]) -> str:
    for key in ("reason", "semantic_note", "note", "semantic_kind", "type"):
        value = _string(entry.get(key))
        if value:
            return value
    return "-"


def _has_review_provenance(entry: Mapping[str, object]) -> bool:
    reviewer = _string(entry.get("reviewed_by")) or _string(entry.get("reviewer"))
    reviewed_at = _string(entry.get("reviewed_at")) or _string(entry.get("reviewed_on")) or _string(
        entry.get("review_date")
    )
    return bool(reviewer and reviewed_at)


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
