from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
KB_PATH = PROJECT_ROOT / "knowledge" / "platform_executable_formats.json"
SCHEMA_PATH = PROJECT_ROOT / "knowledge" / "platform_executable_formats.schema.json"

FACT_STATES = {"validated", "parser_asserted", "candidate", "deferred", "unsupported"}
ACCEPTED_FACT_STATES = {"validated", "parser_asserted"}
SOURCE_TYPES = {"old_out_of_print", "modern_compatible", "project_observed", "parser_asserted"}
ENTRYPOINT_TYPES = {
    "file_entrypoint",
    "segment_entrypoint",
    "runtime_entrypoint",
    "exported_entrypoint",
    "callback_entrypoint",
    "analysis_seed_entrypoint",
}
PARSER_USES = {"accepted_parser_output", "candidate_only", "deferred_only", "unsupported_only"}
REQUIRED_PARSER_BEHAVIORS = {"fail_closed", "emit_candidate", "emit_placeholder", "ignore_safely", "block_closeout"}
MODEL_LAYERS = {
    "file_structure",
    "loader_model",
    "runtime_entry_model",
    "analysis_model",
    "renderer_expectation",
    "archetype_identity",
}

RECORD_SECTIONS = (
    "identification",
    "containers",
    "regions",
    "relocations",
    "symbols",
    "bss",
    "loader_model",
    "runtime_model",
    "analysis_model",
    "renderer_expectations",
)
REVIEW_SECTIONS = ("unknowns", "conflicts", "deferred", "unsupported")
STATUS_DEFAULT_PARSER_USE = {
    "candidate": "candidate_only",
    "deferred": "deferred_only",
    "unsupported": "unsupported_only",
}


def load_kb(path: Path = KB_PATH) -> dict[str, Any]:
    return _load_json(path)


def load_schema(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    return _load_json(path)


def validate_kb(kb: Mapping[str, Any], schema: Mapping[str, Any] | None = None) -> list[str]:
    diagnostics: list[str] = []
    if kb.get("schema_version") != 1:
        diagnostics.append("schema_version must be 1")

    vocabularies = _mapping(kb.get("vocabularies"))
    _check_vocabulary(diagnostics, vocabularies, "fact_states", FACT_STATES)
    _check_vocabulary(diagnostics, vocabularies, "source_types", SOURCE_TYPES)
    _check_vocabulary(diagnostics, vocabularies, "entrypoint_types", ENTRYPOINT_TYPES)
    _check_vocabulary(diagnostics, vocabularies, "parser_uses", PARSER_USES)
    _check_vocabulary(diagnostics, vocabularies, "required_parser_behaviors", REQUIRED_PARSER_BEHAVIORS)
    _check_vocabulary(diagnostics, vocabularies, "model_layers", MODEL_LAYERS)

    if schema is not None:
        schema_id = schema.get("$id")
        if schema_id != "knowledge/platform_executable_formats.schema.json":
            diagnostics.append("schema $id must be knowledge/platform_executable_formats.schema.json")

    sources = _sequence(kb.get("sources"))
    source_ids: set[str] = set()
    for index, source_value in enumerate(sources):
        source = _mapping(source_value)
        source_id = _string(source.get("id"))
        if not source_id:
            diagnostics.append(f"sources[{index}] missing id")
        elif source_id in source_ids:
            diagnostics.append(f"duplicate source id: {source_id}")
        else:
            source_ids.add(source_id)
        _check_enum(diagnostics, source.get("source_type"), SOURCE_TYPES, f"sources[{index}].source_type")
        for key in ("license_status", "path", "role"):
            if not _string(source.get(key)):
                diagnostics.append(f"sources[{index}] missing {key}")

    records = _sequence(kb.get("records"))
    if not records:
        diagnostics.append("records must not be empty")
    for index, record_value in enumerate(records):
        _validate_record(diagnostics, _mapping(record_value), index, source_ids)

    packet_ids: set[str] = set()
    for index, packet_value in enumerate(_sequence(kb.get("citation_packets"))):
        _validate_citation_packet(diagnostics, _mapping(packet_value), index, source_ids, packet_ids)
    return diagnostics


def record_by_id(kb: Mapping[str, Any], record_id: str) -> dict[str, Any]:
    for record_value in _sequence(kb.get("records")):
        record = _mapping(record_value)
        if record.get("id") == record_id:
            return dict(record)
    raise KeyError(record_id)


def fact_by_id(record: Mapping[str, Any], fact_id: str) -> dict[str, Any]:
    for fact_value in _sequence(record.get("facts")):
        fact = _mapping(fact_value)
        if fact.get("id") == fact_id:
            return dict(fact)
    raise KeyError(fact_id)


def record_item_by_id(record: Mapping[str, Any], item_id: str) -> dict[str, Any]:
    for item in _iter_record_items(record):
        if item.get("id") == item_id:
            return dict(item)
    raise KeyError(item_id)


def citation_packet_by_id(kb: Mapping[str, Any], packet_id: str) -> dict[str, Any]:
    for packet_value in _sequence(kb.get("citation_packets")):
        packet = _mapping(packet_value)
        if packet.get("id") == packet_id:
            return dict(packet)
    raise KeyError(packet_id)


def validate_parser_fact_references(payload: object, kb: Mapping[str, Any] | None = None) -> list[str]:
    knowledge = load_kb() if kb is None else kb
    citation_fact_ids = {
        _string(_mapping(packet).get("fact_candidate_id")) for packet in _sequence(knowledge.get("citation_packets"))
    }
    citation_fact_ids.discard("")
    diagnostics: list[str] = []
    _validate_parser_fact_node(
        diagnostics,
        payload,
        knowledge,
        citation_fact_ids,
        inherited_record_id=None,
        path="$",
    )
    return diagnostics


def build_parser_fact_coverage_report(
    payloads: Sequence[object],
    kb: Mapping[str, Any] | None = None,
    *,
    labels: Sequence[str] | None = None,
) -> dict[str, Any]:
    knowledge = load_kb() if kb is None else kb
    emitted: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    emitted_record_ids: set[str] = set()
    counts = {"accepted": 0, "candidate": 0, "deferred": 0, "unsupported": 0, "invalid": 0}

    for payload_index, payload in enumerate(payloads):
        label = labels[payload_index] if labels is not None and payload_index < len(labels) else f"parser_output[{payload_index}]"
        for ref in _collect_parser_fact_refs(payload, inherited_record_id=None, path="$"):
            item = _classify_parser_fact_ref(ref, knowledge)
            item["source"] = label
            if item["record_id"]:
                emitted_record_ids.add(item["record_id"])
            emitted.append(item)
            classification = _string(item.get("classification"))
            if classification in counts:
                counts[classification] += 1
            if classification == "invalid":
                invalid.append(item)

    all_records = [_mapping(record) for record in _sequence(knowledge.get("records"))]
    unreported_records = [
        {
            "record_id": _string(record.get("id")),
            "platform_id": _string(record.get("platform_id")),
            "archetype_id": _string(record.get("archetype_id")),
        }
        for record in all_records
        if _string(record.get("id")) not in emitted_record_ids
    ]
    emitted_platform_ids = {
        _string(record.get("platform_id"))
        for record in all_records
        if _string(record.get("id")) in emitted_record_ids
    }
    all_platform_ids = sorted({_string(record.get("platform_id")) for record in all_records if _string(record.get("platform_id"))})
    unreported_platforms = [platform_id for platform_id in all_platform_ids if platform_id not in emitted_platform_ids]

    return {
        "summary": {
            "parser_outputs": len(payloads),
            "emitted_fact_refs": len(emitted),
            "accepted": counts["accepted"],
            "candidate": counts["candidate"],
            "deferred": counts["deferred"],
            "unsupported": counts["unsupported"],
            "invalid": counts["invalid"],
        },
        "emitted_fact_refs": emitted,
        "invalid_fact_refs": invalid,
        "unreported_records": unreported_records,
        "unreported_platforms": unreported_platforms,
        "generated_fact_table": {
            "source": "knowledge/platform_executable_formats.json",
            "record_count": len(all_records),
            "fact_ref_count": sum(1 for record in all_records for _item in _iter_record_items(record)),
        },
    }


def build_guardrail_report(kb: Mapping[str, Any]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for record_value in _sequence(kb.get("records")):
        record = _mapping(record_value)
        record_id = _string(record.get("id"))
        required = _mapping(record.get("required_parser_behavior"))
        accepted_fact_ids: list[str] = []
        candidate_fact_ids: list[str] = []
        deferred_fact_ids: list[str] = []
        unsupported_fact_ids: list[str] = []
        for item in _iter_fact_like_items(record):
            item_id = _string(item.get("id"))
            status = item.get("status")
            parser_use = item.get("parser_use")
            if parser_use == "accepted_parser_output":
                accepted_fact_ids.append(item_id)
            elif status == "candidate":
                candidate_fact_ids.append(item_id)
            elif status == "deferred":
                deferred_fact_ids.append(item_id)
            elif status == "unsupported":
                unsupported_fact_ids.append(item_id)
        records.append(
            {
                "id": record_id,
                "platform_id": record.get("platform_id"),
                "kb_backed": required.get("kb_backed") is True,
                "accepted_parser_fact_ids": accepted_fact_ids,
                "candidate_only_fact_ids": candidate_fact_ids,
                "deferred_fact_ids": deferred_fact_ids,
                "unsupported_fact_ids": unsupported_fact_ids,
                "missing_fact_behavior": required.get("missing_fact_behavior"),
            }
        )
    return {
        "records": records,
        "kb_backed_records": [record["id"] for record in records if record["kb_backed"]],
        "report_only_records": [record["id"] for record in records if not record["kb_backed"]],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate platform executable-format KB files.")
    parser.add_argument("command", nargs="?", choices=("validate", "guardrails", "coverage"), default="validate")
    parser.add_argument("--kb", type=Path, default=KB_PATH)
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH)
    parser.add_argument("--parser-output", action="append", type=Path, default=[])
    parser.add_argument("--allow-empty", action="store_true", help="Allow report-only coverage with no parser output.")
    parser.add_argument(
        "--current-macos-c-backend",
        action="store_true",
        help="Include current Mac C backend output from the committed MPW fixture.",
    )
    parser.add_argument(
        "--current-amiga-hunk",
        action="store_true",
        help="Include current Amiga HUNK parser output from a synthetic parser fixture.",
    )
    parser.add_argument(
        "--current-atari-prg",
        action="store_true",
        help="Include current Atari ST PRG parser output from a synthetic parser fixture.",
    )
    parser.add_argument(
        "--macos-image",
        type=Path,
        default=PROJECT_ROOT / "resources/platform_macos/MPW-GM.img.bin",
        help="Mac HFS image used with --current-macos-c-backend.",
    )
    parser.add_argument(
        "--macos-hfs-path",
        default="MPW-GM/MPW/Tools/Asm",
        help="HFS path used with --current-macos-c-backend.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    kb = load_kb(args.kb)
    diagnostics = validate_kb(kb, load_schema(args.schema))
    for diagnostic in diagnostics:
        print(diagnostic)
    if diagnostics:
        return 1
    if args.command == "guardrails":
        print(json.dumps(build_guardrail_report(kb), indent=2))
    if args.command == "coverage":
        payloads = [_load_json(path) for path in args.parser_output]
        labels = [str(path) for path in args.parser_output]
        if args.current_macos_c_backend:
            try:
                payloads.append(_load_current_macos_c_backend_output(args.macos_image, args.macos_hfs_path))
            except Exception as exc:
                print(f"coverage current Mac C backend output failed: {exc}", file=sys.stderr)
                return 1
            labels.append(f"current-macos-c-backend:{args.macos_image}:{args.macos_hfs_path}")
        if args.current_amiga_hunk:
            try:
                payloads.append(_load_current_amiga_hunk_output())
            except Exception as exc:
                print(f"coverage current Amiga HUNK output failed: {exc}", file=sys.stderr)
                return 1
            labels.append("current-amiga-hunk:synthetic-parser-fixture")
        if args.current_atari_prg:
            try:
                payloads.append(_load_current_atari_prg_output())
            except Exception as exc:
                print(f"coverage current Atari PRG output failed: {exc}", file=sys.stderr)
                return 1
            labels.append("current-atari-prg:synthetic-parser-fixture")
        if not payloads and not args.allow_empty:
            print(
                "coverage requires --parser-output, --current-macos-c-backend, "
                "--current-amiga-hunk, or --current-atari-prg; "
                "use --allow-empty only for inventory/report-only output",
                file=sys.stderr,
            )
            return 2
        report = build_parser_fact_coverage_report(payloads, kb, labels=labels)
        print(json.dumps(report, indent=2, sort_keys=True))
        if report["summary"]["invalid"]:
            return 1
    return 0


def _validate_record(diagnostics: list[str], record: Mapping[str, Any], index: int, source_ids: set[str]) -> None:
    prefix = f"records[{index}]"
    for key in ("id", "platform_id", "format_id", "archetype_id"):
        if not _string(record.get(key)):
            diagnostics.append(f"{prefix} missing {key}")
    _check_enum(diagnostics, record.get("fact_state"), FACT_STATES, f"{prefix}.fact_state")

    source_policy = _mapping(record.get("source_policy"))
    accepted = set(_sequence(source_policy.get("accepted_fact_states")))
    if accepted != ACCEPTED_FACT_STATES:
        diagnostics.append(f"{prefix}.source_policy.accepted_fact_states must be validated/parser_asserted")

    for section in RECORD_SECTIONS:
        items = _sequence(record.get(section))
        if section not in {"conflicts"} and record.get(section) is None:
            diagnostics.append(f"{prefix} missing {section}")
        for item_index, item_value in enumerate(items):
            _validate_format_item(diagnostics, _mapping(item_value), f"{prefix}.{section}[{item_index}]", source_ids)

    for entry_index, entry_value in enumerate(_sequence(record.get("entrypoints"))):
        entry = _mapping(entry_value)
        _check_enum(diagnostics, entry.get("type"), ENTRYPOINT_TYPES, f"{prefix}.entrypoints[{entry_index}].type")
        _validate_format_item(diagnostics, entry, f"{prefix}.entrypoints[{entry_index}]", source_ids)

    fact_ids: set[str] = set()
    for fact_index, fact_value in enumerate(_sequence(record.get("facts"))):
        fact = _mapping(fact_value)
        fact_id = _string(fact.get("id"))
        if fact_id in fact_ids:
            diagnostics.append(f"{prefix}.facts duplicate id: {fact_id}")
        fact_ids.add(fact_id)
        _check_enum(diagnostics, fact.get("layer"), MODEL_LAYERS, f"{prefix}.facts[{fact_index}].layer")
        _validate_format_item(diagnostics, fact, f"{prefix}.facts[{fact_index}]", source_ids)
        if fact.get("status") == "parser_asserted" and not _mapping(fact.get("parser_assertion")):
            diagnostics.append(f"{prefix}.facts[{fact_index}] parser_asserted fact lacks parser_assertion")
        assertion = _mapping(fact.get("parser_assertion"))
        if assertion:
            for key in ("reason", "citation_context", "standard_interpretation", "review_status"):
                if not _string(assertion.get(key)):
                    diagnostics.append(f"{prefix}.facts[{fact_index}].parser_assertion missing {key}")

    for section in ("unknowns", "conflicts", "deferred", "unsupported"):
        for item_index, item_value in enumerate(_sequence(record.get(section))):
            item = _mapping(item_value)
            for key in ("id", "scope", "summary"):
                if not _string(item.get(key)):
                    diagnostics.append(f"{prefix}.{section}[{item_index}] missing {key}")
            _check_enum(diagnostics, item.get("status"), FACT_STATES, f"{prefix}.{section}[{item_index}].status")
            _check_enum(
                diagnostics,
                item.get("required_parser_behavior"),
                REQUIRED_PARSER_BEHAVIORS,
                f"{prefix}.{section}[{item_index}].required_parser_behavior",
            )
            _validate_citations(diagnostics, _sequence(item.get("citations")), f"{prefix}.{section}[{item_index}]", source_ids)

    required = _mapping(record.get("required_parser_behavior"))
    accepted_states = set(_sequence(required.get("accepted_output_requires_fact_states")))
    if accepted_states != ACCEPTED_FACT_STATES:
        diagnostics.append(f"{prefix}.required_parser_behavior accepted output must require accepted fact states")


def _iter_fact_like_items(record: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    items: list[Mapping[str, Any]] = []
    for section in (*RECORD_SECTIONS, "entrypoints", "facts"):
        items.extend(_mapping(item) for item in _sequence(record.get(section)))
    return items


def _iter_record_items(record: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    items = _iter_fact_like_items(record)
    for section in REVIEW_SECTIONS:
        items.extend(_mapping(item) for item in _sequence(record.get(section)))
    return items


def _collect_parser_fact_refs(
    value: object,
    *,
    inherited_record_id: str | None,
    path: str,
) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    if isinstance(value, Mapping):
        node = _mapping(value)
        record_id = _string(node.get("kb_record_id")) or inherited_record_id
        if any(key in node for key in ("fact_id", "fact_status", "parser_use")):
            refs.append(
                {
                    "path": path,
                    "record_id": record_id or "",
                    "fact_id": _string(node.get("fact_id")),
                    "fact_status": _string(node.get("fact_status")),
                    "parser_use": _string(node.get("parser_use")),
                }
            )
        for key, child in node.items():
            refs.extend(_collect_parser_fact_refs(child, inherited_record_id=record_id, path=f"{path}.{key}"))
    elif isinstance(value, Sequence) and not isinstance(value, str):
        for index, child in enumerate(value):
            refs.extend(
                _collect_parser_fact_refs(child, inherited_record_id=inherited_record_id, path=f"{path}[{index}]")
            )
    return refs


def _classify_parser_fact_ref(ref: Mapping[str, str], kb: Mapping[str, Any]) -> dict[str, Any]:
    record_id = _string(ref.get("record_id"))
    fact_id = _string(ref.get("fact_id"))
    emitted_status = _string(ref.get("fact_status"))
    emitted_parser_use = _string(ref.get("parser_use"))
    output: dict[str, Any] = {
        "path": _string(ref.get("path")),
        "record_id": record_id,
        "fact_id": fact_id,
        "emitted_status": emitted_status,
        "emitted_parser_use": emitted_parser_use,
        "classification": "invalid",
        "reason": "",
    }
    if not record_id:
        output["reason"] = "missing_kb_record_id"
        return output
    if not fact_id:
        output["reason"] = "missing_fact_id"
        return output
    try:
        record = record_by_id(kb, record_id)
    except KeyError:
        output["reason"] = "unknown_kb_record_id"
        return output
    try:
        item = record_item_by_id(record, fact_id)
    except KeyError:
        output["reason"] = "unknown_fact_id"
        return output

    kb_status = _string(item.get("status") or record.get("fact_state"))
    kb_parser_use = _string(item.get("parser_use")) or STATUS_DEFAULT_PARSER_USE.get(kb_status, "")
    output["kb_status"] = kb_status
    output["kb_parser_use"] = kb_parser_use
    if emitted_status and emitted_status != kb_status:
        output["reason"] = "status_mismatch"
        return output
    if emitted_parser_use and emitted_parser_use != kb_parser_use:
        output["reason"] = "parser_use_mismatch"
        return output
    if emitted_parser_use == "accepted_parser_output" and kb_parser_use != "accepted_parser_output":
        output["reason"] = "accepted_claim_not_authorized"
        return output
    if kb_parser_use == "accepted_parser_output":
        output["classification"] = "accepted"
    elif kb_status == "candidate":
        output["classification"] = "candidate"
    elif kb_status == "deferred":
        output["classification"] = "deferred"
    elif kb_status == "unsupported":
        output["classification"] = "unsupported"
    else:
        output["reason"] = "unknown_kb_status"
        return output
    output["reason"] = ""
    return output


def _load_current_macos_c_backend_output(image_path: Path, hfs_path: str) -> dict[str, Any]:
    from amiga_reversing.disasm.c_backend import (
        inspect_macos_hfs_code_summary_with_c_backend,
    )
    from amiga_reversing.disasm.macos_asm_container import read_macos_hfs_image_bytes

    if not image_path.exists():
        raise FileNotFoundError(image_path)
    image_data = read_macos_hfs_image_bytes(image_path)
    return inspect_macos_hfs_code_summary_with_c_backend(image_data, hfs_path)


def _load_current_amiga_hunk_output() -> dict[str, Any]:
    summary = _inspect_platform_fixture("amiga-hunk", _synthetic_amiga_hunk_fixture(), ".hunk")
    sections = _sequence(summary.get("sections"))
    if summary.get("file_kind") != "executable" or not sections:
        raise ValueError("synthetic Amiga HUNK fixture did not parse as an executable with sections")
    _require_parser_owned_fact_refs(summary, "amiga.hunk.load_file.basic_backfill", "current Amiga HUNK")
    _require_amiga_hunk_shared_executable_ranges(summary)
    return summary


def _load_current_atari_prg_output() -> dict[str, Any]:
    summary = _inspect_platform_fixture("atari-st", _synthetic_atari_prg_fixture(), ".prg")
    sections = _sequence(summary.get("sections"))
    if summary.get("file_kind") != "executable" or not sections:
        raise ValueError("synthetic Atari PRG fixture did not parse as an executable with sections")
    _require_parser_owned_fact_refs(summary, "atari_st.prg.gemdos_basic_backfill", "current Atari PRG")
    _require_atari_prg_shared_executable_ranges(summary)
    return summary


def _require_parser_owned_fact_refs(payload: Mapping[str, Any], record_id: str, label: str) -> None:
    if _string(payload.get("kb_record_id")) != record_id:
        raise ValueError(f"{label} parser summary did not emit kb_record_id {record_id}")
    refs = [_mapping(item) for item in _sequence(payload.get("fact_refs"))]
    if not refs:
        raise ValueError(f"{label} parser summary emitted no parser-owned fact refs")
    for index, ref in enumerate(refs):
        for key in ("fact_id", "fact_status", "parser_use"):
            if not _string(ref.get(key)):
                raise ValueError(f"{label} parser summary fact_refs[{index}] missing {key}")
    diagnostics = validate_parser_fact_references(payload)
    if diagnostics:
        raise ValueError(f"{label} parser summary emitted invalid fact refs: {diagnostics}")


def _require_amiga_hunk_shared_executable_ranges(payload: Mapping[str, Any]) -> None:
    label = "current Amiga HUNK"
    if payload.get("executable_model") != "platform_executable_summary_v1":
        raise ValueError(f"{label} parser summary did not emit shared executable model")
    ranges = {_string(item.get("role")): item for item in map(_mapping, _sequence(payload.get("executable_ranges")))}
    for role in ("code", "data", "bss"):
        if role not in ranges:
            raise ValueError(f"{label} parser summary missing executable {role} range")
    for role in ("code", "data"):
        item = ranges[role]
        if not isinstance(item.get("load_offset"), int) or not isinstance(item.get("stored_offset"), int):
            raise ValueError(f"{label} executable {role} range missing load/stored offsets")
        if item.get("fact_id") != "amiga.hunk.code_data_bss.sections.accepted":
            raise ValueError(f"{label} executable {role} range has unexpected fact_id")
        if item.get("fact_status") != "parser_asserted" or item.get("parser_use") != "accepted_parser_output":
            raise ValueError(f"{label} executable {role} range has unexpected fact authority")
    bss = ranges["bss"]
    if not isinstance(bss.get("load_offset"), int) or bss.get("stored_offset") is not None or bss.get("stored_size") != 0:
        raise ValueError(f"{label} executable bss range must be size-only with no stored offset")
    if bss.get("fact_id") != "amiga.hunk.bss.size_only.accepted":
        raise ValueError(f"{label} executable bss range has unexpected fact_id")
    deferred = {
        _string(item.get("kind")): item
        for item in map(_mapping, _sequence(payload.get("executable_deferred")))
    }
    runtime_entry = deferred.get("runtime_entry")
    if runtime_entry is None:
        raise ValueError(f"{label} parser summary missing deferred runtime entry")
    if (
        runtime_entry.get("fact_id") != "amiga.hunk.runtime_entry.deferred"
        or runtime_entry.get("fact_status") != "deferred"
        or runtime_entry.get("parser_use") != "deferred_only"
    ):
        raise ValueError(f"{label} deferred runtime entry has unexpected fact authority")


def _require_atari_prg_shared_executable_ranges(payload: Mapping[str, Any]) -> None:
    label = "current Atari PRG"
    if payload.get("executable_model") != "platform_executable_summary_v1":
        raise ValueError(f"{label} parser summary did not emit shared executable model")
    ranges = {_string(item.get("role")): item for item in map(_mapping, _sequence(payload.get("executable_ranges")))}
    for role in ("code", "data", "bss"):
        if role not in ranges:
            raise ValueError(f"{label} parser summary missing executable {role} range")
    for role in ("code", "data"):
        item = ranges[role]
        if not isinstance(item.get("load_offset"), int) or not isinstance(item.get("stored_offset"), int):
            raise ValueError(f"{label} executable {role} range missing load/stored offsets")
        if item.get("fact_id") != "atari_st.prg.text_data_loaded_image.accepted":
            raise ValueError(f"{label} executable {role} range has unexpected fact_id")
        if item.get("fact_status") != "parser_asserted" or item.get("parser_use") != "accepted_parser_output":
            raise ValueError(f"{label} executable {role} range has unexpected fact authority")
    bss = ranges["bss"]
    if not isinstance(bss.get("load_offset"), int) or bss.get("stored_offset") is not None or bss.get("stored_size") != 0:
        raise ValueError(f"{label} executable bss range must be size-only with no stored offset")
    if (
        bss.get("fact_id") != "atari_st.prg.bss.header_only.candidate"
        or bss.get("fact_status") != "candidate"
        or bss.get("parser_use") != "candidate_only"
    ):
        raise ValueError(f"{label} executable bss range must remain candidate-only")
    deferred = {
        _string(item.get("kind")): item
        for item in map(_mapping, _sequence(payload.get("executable_deferred")))
    }
    relocation = deferred.get("relocation_breadth")
    if relocation is None:
        raise ValueError(f"{label} parser summary missing deferred relocation breadth")
    if (
        relocation.get("fact_id") != "atari_st.prg.relocation_terminator_variants.deferred"
        or relocation.get("fact_status") != "deferred"
        or relocation.get("parser_use") != "deferred_only"
    ):
        raise ValueError(f"{label} deferred relocation breadth has unexpected fact authority")


def _inspect_platform_fixture(backend: str, fixture_bytes: bytes, suffix: str) -> dict[str, Any]:
    from amiga_reversing.disasm.c_backend import _platform_file_text

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as fixture:
            fixture.write(fixture_bytes)
            temp_path = Path(fixture.name)
        summary_text = _platform_file_text(
            "platform_file_inspect_path_json_alloc",
            backend,
            str(temp_path),
            project_root=PROJECT_ROOT,
        )
        summary = json.loads(summary_text)
        if not isinstance(summary, dict):
            raise ValueError(f"{backend} parser summary was not a JSON object")
        return summary
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _synthetic_amiga_hunk_fixture() -> bytes:
    def u32(value: int) -> bytes:
        return value.to_bytes(4, "big")

    return b"".join(
        [
            u32(1011),  # HUNK_HEADER
            u32(0),  # no resident library names
            u32(3),
            u32(0),
            u32(2),
            u32(1),
            u32(1),
            u32(2),
            u32(1001),  # HUNK_CODE
            u32(1),
            b"\x4e\x75\x00\x00",
            u32(1010),
            u32(1002),  # HUNK_DATA
            u32(1),
            b"\x12\x34\x56\x78",
            u32(1010),
            u32(1003),  # HUNK_BSS
            u32(2),
            u32(1010),
        ]
    )


def _synthetic_atari_prg_fixture() -> bytes:
    def u16(value: int) -> bytes:
        return value.to_bytes(2, "big")

    def u32(value: int) -> bytes:
        return value.to_bytes(4, "big")

    text = b"\x4e\x75\x00\x00"
    data = b"\x12\x34\x56\x78"
    return b"".join(
        [
            u16(0x601A),
            u32(len(text)),
            u32(len(data)),
            u32(8),
            u32(0),
            u32(0),
            u32(0),
            u16(0),
            text,
            data,
            u32(0),
        ]
    )


def _validate_parser_fact_node(
    diagnostics: list[str],
    value: object,
    kb: Mapping[str, Any],
    citation_fact_ids: set[str],
    *,
    inherited_record_id: str | None,
    path: str,
) -> None:
    if isinstance(value, Mapping):
        node = _mapping(value)
        record_id = _string(node.get("kb_record_id")) or inherited_record_id
        if "kb_record_id" in node and not _string(node.get("kb_record_id")):
            diagnostics.append(f"{path}.kb_record_id must be a non-empty string")
        if _string(node.get("kb_record_id")):
            try:
                record_by_id(kb, _string(node.get("kb_record_id")))
            except KeyError:
                diagnostics.append(f"{path}.kb_record_id unknown record: {node.get('kb_record_id')}")
        if any(key in node for key in ("fact_id", "fact_status", "parser_use")):
            _validate_parser_fact_mapping(diagnostics, node, kb, citation_fact_ids, record_id, path)
        for key, child in node.items():
            _validate_parser_fact_node(
                diagnostics,
                child,
                kb,
                citation_fact_ids,
                inherited_record_id=record_id,
                path=f"{path}.{key}",
            )
    elif isinstance(value, Sequence) and not isinstance(value, str):
        for index, child in enumerate(value):
            _validate_parser_fact_node(
                diagnostics,
                child,
                kb,
                citation_fact_ids,
                inherited_record_id=inherited_record_id,
                path=f"{path}[{index}]",
            )


def _validate_parser_fact_mapping(
    diagnostics: list[str],
    node: Mapping[str, Any],
    kb: Mapping[str, Any],
    citation_fact_ids: set[str],
    record_id: str | None,
    path: str,
) -> None:
    fact_id = _string(node.get("fact_id"))
    if not fact_id:
        diagnostics.append(f"{path}.fact_id must be present when fact_status/parser_use is emitted")
        return
    if record_id is None:
        diagnostics.append(f"{path}.fact_id {fact_id} has no kb_record_id context")
        return
    try:
        record = record_by_id(kb, record_id)
    except KeyError:
        diagnostics.append(f"{path}.kb_record_id unknown record: {record_id}")
        return
    try:
        item = record_item_by_id(record, fact_id)
    except KeyError:
        if fact_id in citation_fact_ids:
            diagnostics.append(f"{path}.fact_id {fact_id} is a citation packet fact_candidate_id, not a KB record item")
        else:
            diagnostics.append(f"{path}.fact_id unknown KB record item: {fact_id}")
        return
    expected_status = _string(item.get("status"))
    expected_parser_use = _expected_parser_use(item)
    fact_status = _string(node.get("fact_status"))
    parser_use = _string(node.get("parser_use"))
    if fact_status != expected_status:
        diagnostics.append(f"{path}.fact_status {fact_status!r} does not match KB status {expected_status!r}")
    if parser_use != expected_parser_use:
        diagnostics.append(f"{path}.parser_use {parser_use!r} does not match KB parser_use {expected_parser_use!r}")
    if parser_use == "accepted_parser_output" and expected_status not in ACCEPTED_FACT_STATES:
        diagnostics.append(f"{path}.parser_use accepted_parser_output requires validated/parser_asserted status")


def _expected_parser_use(item: Mapping[str, Any]) -> str:
    parser_use = _string(item.get("parser_use"))
    if parser_use:
        return parser_use
    return STATUS_DEFAULT_PARSER_USE.get(_string(item.get("status")), "")


def _validate_citation_packet(
    diagnostics: list[str],
    packet: Mapping[str, Any],
    index: int,
    source_ids: set[str],
    packet_ids: set[str],
) -> None:
    prefix = f"citation_packets[{index}]"
    packet_id = _string(packet.get("id"))
    if not packet_id:
        diagnostics.append(f"{prefix} missing id")
    elif packet_id in packet_ids:
        diagnostics.append(f"duplicate citation packet id: {packet_id}")
    else:
        packet_ids.add(packet_id)
    for key in ("platform_id", "fact_candidate_id", "wording", "license_status"):
        if not _string(packet.get(key)):
            diagnostics.append(f"{prefix} missing {key}")
    _check_enum(diagnostics, packet.get("status"), FACT_STATES, f"{prefix}.status")
    _check_enum(diagnostics, packet.get("source_type"), SOURCE_TYPES, f"{prefix}.source_type")
    for layer in _sequence(packet.get("affects")):
        _check_enum(diagnostics, layer, MODEL_LAYERS, f"{prefix}.affects")
    _validate_citations(diagnostics, _sequence(packet.get("citations")), prefix, source_ids)
    _check_enum(
        diagnostics,
        packet.get("parser_behavior_before_kb_migration"),
        REQUIRED_PARSER_BEHAVIORS,
        f"{prefix}.parser_behavior_before_kb_migration",
    )
    if packet.get("source_type") == "project_observed" and packet.get("status") == "validated":
        diagnostics.append(f"{prefix} project_observed packet must not validate a general platform rule")


def _validate_format_item(
    diagnostics: list[str],
    item: Mapping[str, Any],
    prefix: str,
    source_ids: set[str],
) -> None:
    for key in ("id", "summary"):
        if not _string(item.get(key)):
            diagnostics.append(f"{prefix} missing {key}")
    status = item.get("status")
    parser_use = item.get("parser_use")
    _check_enum(diagnostics, status, FACT_STATES, f"{prefix}.status")
    _check_enum(diagnostics, item.get("source_type"), SOURCE_TYPES, f"{prefix}.source_type")
    _check_enum(diagnostics, parser_use, PARSER_USES, f"{prefix}.parser_use")
    _validate_citations(diagnostics, _sequence(item.get("citations")), prefix, source_ids)
    if parser_use == "accepted_parser_output" and status not in ACCEPTED_FACT_STATES:
        diagnostics.append(f"{prefix} cannot use {status} as accepted parser output")
    if status == "candidate" and parser_use != "candidate_only":
        diagnostics.append(f"{prefix} candidate fact must be candidate_only")
    if status == "deferred" and parser_use != "deferred_only":
        diagnostics.append(f"{prefix} deferred fact must be deferred_only")
    if status == "unsupported" and parser_use != "unsupported_only":
        diagnostics.append(f"{prefix} unsupported fact must be unsupported_only")


def _validate_citations(
    diagnostics: list[str],
    citations: Sequence[object],
    prefix: str,
    source_ids: set[str],
) -> None:
    if not citations:
        diagnostics.append(f"{prefix} missing citations")
    for index, citation_value in enumerate(citations):
        citation = _mapping(citation_value)
        source_id = _string(citation.get("source_id"))
        if source_id not in source_ids:
            diagnostics.append(f"{prefix}.citations[{index}] unknown source_id: {source_id}")
        _check_enum(diagnostics, citation.get("source_type"), SOURCE_TYPES, f"{prefix}.citations[{index}].source_type")
        for key in ("target", "context"):
            if not _string(citation.get(key)):
                diagnostics.append(f"{prefix}.citations[{index}] missing {key}")


def _check_vocabulary(diagnostics: list[str], vocabularies: Mapping[str, Any], key: str, expected: set[str]) -> None:
    observed = set(_sequence(vocabularies.get(key)))
    if observed != expected:
        diagnostics.append(f"vocabularies.{key} mismatch")


def _check_enum(diagnostics: list[str], value: object, choices: set[str], field: str) -> None:
    if value not in choices:
        diagnostics.append(f"{field} has unknown value: {value}")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> Sequence[object]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        return []
    return value


def _string(value: object) -> str:
    return value if isinstance(value, str) else ""


if __name__ == "__main__":
    sys.exit(main())
