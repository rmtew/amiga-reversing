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

from amiga_reversing.disasm.source_numbers import parse_source_int

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_OS_VERSION_ORDER = ("1.0", "1.1", "1.2", "1.3", "2.0", "2.04", "2.1", "3.0", "3.1", "3.5")
KNOWN_CORRECTION_REVIEW_STATUSES = {"seeded", "validated"}
KNOWN_SOURCE_INVENTORY_STATUSES = {
    "parsed",
    "parser_asserted",
    "seeded_correction",
    "validated_correction",
    "candidate",
    "deferred",
    "unsupported",
}


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
    target_gaps_parser = subparsers.add_parser("target-gaps", help="Report target-driven platform KB gaps.")
    target_gaps_parser.add_argument("target")
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
    if args.command == "target-gaps":
        print(format_target_gap_report(build_target_gap_report(PROJECT_ROOT, args.target)))
        return 0

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
        "source_inventory": _source_inventory_report(
            knowledge / "platform_source_inventory.json", knowledge / "adcd21_inventory.md"
        ),
        "ndk": _ndk_report(includes, other, generated / "amiga_os_runtime.c"),
        "hardware": _hardware_report(hw_registers, hw_symbols),
        "corrections": _corrections_report(corrections),
        "hunk": _hunk_report(hunk),
        "target_platform_summary": _target_platform_summary_report(project_root),
    }


def check_report(report: Mapping[str, object]) -> list[str]:
    violations: list[str] = []
    source = cast(Mapping[str, object], report["source_inventory"])
    violations.extend(cast(list[str], source["violations"]))
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
    target_summary = cast(Mapping[str, object], report["target_platform_summary"])
    malformed = cast(list[str], target_summary["malformed_summary_artifacts"])
    if malformed:
        violations.append(f"target platform summary artifacts are malformed: {', '.join(malformed)}")
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
        f"  status counts: {_format_counts(cast(Mapping[str, int], source['status_counts']))}",
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
        f"  artifact source counts: {_format_counts(cast(Mapping[str, int], target_summary['artifact_source_counts']))}",
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


def build_target_gap_report(project_root: Path, target: str) -> dict[str, object]:
    target_path = _resolve_target_path(project_root, target)
    gap_inputs = _load_json_if_exists(target_path / "platform_gap_inputs.json")
    source_analysis = _load_json_if_exists(target_path / "source_analysis.json")
    platform_summary = _target_platform_summary_payload(target_path, source_analysis)
    metadata = _load_json_if_exists(target_path / "target_metadata.json")
    constants_by_value = _constant_rows_by_value(
        _load_json_if_exists(project_root / "knowledge" / "amiga_ndk_includes_parsed.json")
    )
    groups: dict[str, dict[str, object]] = {}
    for value_row in _target_gap_absolute_values(gap_inputs, source_analysis):
        value = _parse_int(value_row.get("value"))
        if value is None:
            continue
        _target_gap_add_value_candidate(groups, value_row, value, constants_by_value)
    _target_gap_add_os_compatibility_candidates(groups, platform_summary, metadata, target_path)
    return {
        "target": str(target_path.relative_to(project_root)) if target_path.is_relative_to(project_root) else str(target_path),
        "candidate_count": sum(len(cast(list[object], group["candidates"])) for group in groups.values()),
        "groups": list(groups.values()),
    }


def format_target_gap_report(report: Mapping[str, object]) -> str:
    lines = [f"Target platform gap report: {report['target']}"]
    groups = cast(list[Mapping[str, object]], report["groups"])
    if not groups:
        lines.append("  no platform-looking gaps found")
        return "\n".join(lines)
    for group in groups:
        lines.append(f"{group['owner']}:")
        lines.append(f"  source family: {group['source_family']}")
        lines.append(f"  parser area: {group['parser_area']}")
        for candidate in cast(list[Mapping[str, object]], group["candidates"]):
            detail = _string(candidate.get("detail")) or "-"
            source = _string(candidate.get("source")) or "-"
            reason = _string(candidate.get("reason")) or "-"
            expectation = _string(candidate.get("expectation_source"))
            suffix = f" expectation={expectation}" if expectation else ""
            lines.append(f"  - {detail} source={source} reason={reason}{suffix}")
    return "\n".join(lines)


def _resolve_target_path(project_root: Path, target: str) -> Path:
    candidate = Path(target)
    if candidate.exists():
        return candidate
    direct = project_root / "targets" / target
    if direct.exists():
        return direct
    matches = [path for path in (project_root / "targets").glob(f"**/{target}") if path.is_dir()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise SystemExit(f"Ambiguous target: {target}")
    raise SystemExit(f"Unknown target: {target}")


def _target_platform_summary_payload(
    target_path: Path, source_analysis: Mapping[str, object]
) -> Mapping[str, object]:
    summary = _target_platform_summary_artifact(target_path, source_analysis)
    return cast(Mapping[str, object], summary["payload"])


def _target_gap_absolute_values(
    gap_inputs: Mapping[str, object], source_analysis: Mapping[str, object]
) -> Iterable[Mapping[str, object]]:
    for row in cast(list[object], gap_inputs.get("absolute_values", [])):
        if isinstance(row, dict):
            yield cast(Mapping[str, object], row)
    for row in cast(list[object], gap_inputs.get("constants", [])):
        if isinstance(row, dict):
            yield cast(Mapping[str, object], row)
    for row in cast(list[object], gap_inputs.get("lvo_offsets", [])):
        if isinstance(row, dict):
            yield cast(Mapping[str, object], row)
    for section in cast(list[object], source_analysis.get("sections", [])):
        if not isinstance(section, dict):
            continue
        for access in cast(list[object], section.get("recovered_platform_unresolved_typed_accesses", [])):
            if not isinstance(access, dict):
                continue
            displacement = _parse_int(access.get("displacement"))
            if displacement is None:
                continue
            yield {
                "value": displacement,
                "source": f"section {section.get('section_index', '?')} offset {access.get('offset', '?')}",
                "reason": _string(access.get("classification")) or "unresolved typed access",
            }


def _target_gap_add_value_candidate(
    groups: dict[str, dict[str, object]],
    row: Mapping[str, object],
    value: int,
    constants_by_value: Mapping[int, list[Mapping[str, object]]],
) -> None:
    source = _string(row.get("source")) or "-"
    reason = _string(row.get("reason")) or "platform-looking absolute value"
    signed_value = _signed_platform_value(value)
    if 0xDFF000 <= value <= 0xDFFFFF:
        _target_gap_add_candidate(
            groups,
            "custom_chip_registers",
            "hardware/custom",
            "knowledge/amiga_hw_registers.json; knowledge/amiga_hw_symbols.json",
            {"detail": _hex_value(value), "source": source, "reason": reason},
        )
        return
    if 0xBFD000 <= value <= 0xBFEFFF:
        _target_gap_add_candidate(
            groups,
            "cia_registers",
            "hardware/cia",
            "knowledge/amiga_hw_symbols.json",
            {"detail": _hex_value(value), "source": source, "reason": reason},
        )
        return
    if signed_value < 0 and signed_value % 6 == 0 and abs(signed_value) <= 4096:
        _target_gap_add_candidate(
            groups,
            "amiga_os_lvo",
            "ndk/fd-autodoc",
            "src/scripts/kb/ndk_parser.py; knowledge/amiga_ndk_includes_parsed.json",
            {"detail": str(signed_value), "source": source, "reason": "LVO-shaped negative offset"},
        )
        return
    constant_matches = constants_by_value.get(value, [])
    if constant_matches:
        first = constant_matches[0]
        include_path = _string(first.get("include_path")) or "unknown include"
        names = ", ".join(_string(match.get("name")) or "?" for match in constant_matches[:3])
        _target_gap_add_candidate(
            groups,
            f"known_include_family:{include_path}",
            include_path,
            "knowledge/amiga_ndk_includes_parsed.json",
            {"detail": f"{_hex_value(value)} matches {names}", "source": source, "reason": reason},
        )
        return
    if value >= 0x1000:
        _target_gap_add_candidate(
            groups,
            "unknown_absolute_platform_value",
            "unknown",
            "target gap triage; source inventory",
            {"detail": _hex_value(value), "source": source, "reason": reason},
        )


def _target_gap_add_os_compatibility_candidates(
    groups: dict[str, dict[str, object]],
    platform_summary: Mapping[str, object],
    metadata: Mapping[str, object],
    target_path: Path,
) -> None:
    os_summary = _mapping(platform_summary.get("os_compatibility"))
    minimum = _string(os_summary.get("minimum_required"))
    if not minimum:
        return
    expected, expectation_source = _target_expected_os(metadata, target_path)
    if expected is None or _version_sort_key(minimum) <= _version_sort_key(expected):
        return
    drivers = cast(list[object], os_summary.get("max_requirement_drivers", []))
    if drivers:
        for driver in drivers:
            if not isinstance(driver, dict):
                continue
            call = _string(driver.get("call")) or _string(driver.get("function")) or "unknown call"
            available = _string(driver.get("available_since")) or minimum
            _target_gap_add_candidate(
                groups,
                "unexpected_new_api",
                "ndk/os-compatibility",
                "target platform summary; knowledge/amiga_ndk_other_parsed.json",
                {
                    "detail": f"{call} available_since={available} expected={expected}",
                    "source": _target_gap_driver_source(driver),
                    "reason": "observed API is newer than target expectation",
                    "expectation_source": expectation_source,
                },
            )
    else:
        _target_gap_add_candidate(
            groups,
            "unexpected_new_api",
            "ndk/os-compatibility",
            "target platform summary; knowledge/amiga_ndk_other_parsed.json",
            {
                "detail": f"minimum_required={minimum} expected={expected}",
                "source": "platform_summary",
                "reason": "observed API is newer than target expectation",
                "expectation_source": expectation_source,
            },
        )


def _target_gap_add_candidate(
    groups: dict[str, dict[str, object]],
    owner: str,
    source_family: str,
    parser_area: str,
    candidate: Mapping[str, object],
) -> None:
    group = groups.setdefault(
        owner,
        {"owner": owner, "source_family": source_family, "parser_area": parser_area, "candidates": []},
    )
    cast(list[object], group["candidates"]).append(dict(candidate))


def _target_expected_os(metadata: Mapping[str, object], target_path: Path) -> tuple[str | None, str | None]:
    for key in ("expected_os_version", "expected_min_os_version", "target_os_version"):
        version = _string(metadata.get(key))
        if version:
            return version, "explicit_target_metadata"
    platform = _mapping(metadata.get("platform"))
    for key in ("expected_os_version", "expected_min_os_version", "target_os_version"):
        version = _string(platform.get(key))
        if version:
            return version, "explicit_target_metadata"
    year = _target_year_hint(target_path)
    if year is None:
        return None, None
    if year <= 1990:
        return "1.3", "inferred_year"
    if year <= 1992:
        return "2.0", "inferred_year"
    return "3.1", "inferred_year"


def _target_year_hint(target_path: Path) -> int | None:
    for part in reversed(target_path.parts):
        match = re.search(r"\b(19[8-9][0-9]|20[0-2][0-9])\b", part)
        if match:
            return int(match.group(1))
    return None


def _target_gap_driver_source(driver: Mapping[str, object]) -> str:
    section = driver.get("section_index")
    offset = driver.get("offset")
    if section is not None and offset is not None:
        return f"section {section} offset {offset}"
    return _string(driver.get("source")) or "platform_summary"


def _constant_rows_by_value(includes: Mapping[str, object]) -> dict[int, list[Mapping[str, object]]]:
    rows: dict[int, list[Mapping[str, object]]] = {}
    for name, payload in _mapping(includes.get("constants")).items():
        constant = _mapping(payload)
        value = _parse_int(constant.get("value"))
        if value is None:
            continue
        owner = _mapping(constant.get("owner"))
        rows.setdefault(value, []).append(
            {
                "name": name,
                "include_path": _string(owner.get("canonical_include_path"))
                or _string(owner.get("assembler_include_path"))
                or _string(owner.get("source_file"))
                or "unknown include",
            }
        )
    return rows


def _parse_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return parse_source_int(text)
        except ValueError:
            return None
    return None


def _signed_platform_value(value: int) -> int:
    if value >= 0x80000000:
        return value - 0x100000000
    if value >= 0x8000:
        return value - 0x10000
    return value


def _hex_value(value: int) -> str:
    return f"0x{value:X}"


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
    source_counts = Counter[str]()
    malformed: list[str] = []
    summary_count = 0
    standalone_count = 0
    embedded_count = 0
    targets = project_root / "targets"
    target_dirs = sorted(path for path in targets.glob("*") if path.is_dir()) if targets.exists() else []
    for target_path in target_dirs:
        artifact = _target_platform_summary_artifact(target_path)
        payload = cast(Mapping[str, object], artifact["payload"])
        source = _string(artifact.get("source")) or "missing"
        errors = cast(list[str], artifact["errors"])
        if errors:
            malformed.extend(f"{target_path.name}:{error}" for error in errors)
            continue
        if not payload:
            continue
        summary_count += 1
        source_counts[source] += 1
        if source == "standalone_platform_summary":
            standalone_count += 1
        if source == "embedded_source_analysis":
            embedded_count += 1
        os_summary = _mapping(payload.get("os_compatibility"))
        status = _string(os_summary.get("status"))
        if status in state_counts:
            state_counts[status] += 1
    return {
        "schema_present": summary_count > 0,
        "summary_files": summary_count,
        "standalone_summary_files": standalone_count,
        "embedded_summary_files": embedded_count,
        "artifact_source_counts": dict(sorted(source_counts.items())),
        "os_compatibility_state_counts": state_counts,
        "malformed_summary_artifacts": malformed,
    }


def _target_platform_summary_artifact(
    target_path: Path, source_analysis: Mapping[str, object] | None = None
) -> dict[str, object]:
    standalone_path = target_path / "platform_summary.json"
    if standalone_path.exists():
        payload = _load_json(standalone_path)
        return {
            "source": "standalone_platform_summary",
            "path": str(standalone_path),
            "payload": payload,
            "errors": _target_platform_summary_artifact_errors(payload),
        }
    analysis = source_analysis if source_analysis is not None else _load_json_if_exists(target_path / "source_analysis.json")
    if "platform_summary" not in analysis:
        return {"source": "missing", "path": "", "payload": {}, "errors": []}
    embedded_payload = analysis.get("platform_summary")
    if not isinstance(embedded_payload, dict):
        return {
            "source": "embedded_source_analysis",
            "path": str(target_path / "source_analysis.json"),
            "payload": {},
            "errors": ["platform_summary is not an object"],
        }
    payload = embedded_payload
    return {
        "source": "embedded_source_analysis",
        "path": str(target_path / "source_analysis.json"),
        "payload": payload,
        "errors": _target_platform_summary_artifact_errors(payload),
    }


def _target_platform_summary_artifact_errors(payload: Mapping[str, object]) -> list[str]:
    errors: list[str] = []
    if not payload:
        errors.append("summary is empty")
        return errors
    os_summary = payload.get("os_compatibility")
    if not isinstance(os_summary, dict):
        errors.append("os_compatibility is missing or not an object")
        return errors
    status = _string(os_summary.get("status"))
    if status not in {"observed", "no_os_calls", "unknown"}:
        errors.append(f"os_compatibility.status is invalid: {status or 'missing'}")
    return errors


def _source_inventory_report(inventory_path: Path, markdown_path: Path) -> dict[str, object]:
    payload = _load_json(inventory_path)
    entries = [entry for entry in cast(list[object], payload.get("entries", [])) if isinstance(entry, dict)]
    statuses = Counter(_string(entry.get("status")) or "missing" for entry in entries)
    paths = [_string(entry.get("path")) or "" for entry in entries]
    duplicate_ids = sorted(
        id_ for id_, count in Counter(_string(entry.get("id")) or "missing" for entry in entries).items() if count > 1
    )
    duplicate_paths = sorted(path for path, count in Counter(paths).items() if path and count > 1)
    unknown_status = sorted(
        f"{_string(entry.get('id')) or _string(entry.get('path')) or 'missing'}={_string(entry.get('status')) or 'missing'}"
        for entry in entries
        if (_string(entry.get("status")) or "missing") not in KNOWN_SOURCE_INVENTORY_STATUSES
    )
    markdown_paths = _source_inventory_markdown_paths(markdown_path)
    inventory_paths = {path for path in paths if path}
    missing_from_inventory = sorted(markdown_paths - inventory_paths)
    missing_from_markdown = sorted(inventory_paths - markdown_paths)
    violations = []
    if duplicate_ids:
        violations.append(f"source inventory has duplicate ids: {', '.join(duplicate_ids)}")
    if duplicate_paths:
        violations.append(f"source inventory has duplicate paths: {', '.join(duplicate_paths)}")
    if unknown_status:
        violations.append(f"source inventory has unknown statuses: {', '.join(unknown_status)}")
    if missing_from_inventory:
        violations.append(f"source inventory missing markdown paths: {', '.join(missing_from_inventory)}")
    if missing_from_markdown:
        violations.append(f"source inventory has paths absent from markdown: {', '.join(missing_from_markdown)}")
    return {
        "inventory_rows": len(entries),
        "status_counts": dict(sorted(statuses.items())),
        "parsed": statuses["parsed"] + statuses["parser_asserted"],
        "candidate_or_deferred": statuses["candidate"] + statuses["deferred"],
        "candidate": statuses["candidate"],
        "deferred": statuses["deferred"],
        "unsupported": statuses["unsupported"],
        "unknown_status": unknown_status,
        "duplicate_ids": duplicate_ids,
        "duplicate_paths": duplicate_paths,
        "markdown_missing_from_inventory": missing_from_inventory,
        "inventory_missing_from_markdown": missing_from_markdown,
        "violations": violations,
    }


def _source_inventory_markdown_paths(path: Path) -> set[str]:
    rows: set[str] = set()
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if cells:
            rows.add(cells[0].strip("`"))
    return rows


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


def _load_json_if_exists(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return _load_json(path)


def _mapping(value: object) -> Mapping[str, object]:
    return cast(Mapping[str, object], value) if isinstance(value, dict) else {}


def _string(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


if __name__ == "__main__":
    raise SystemExit(main())
