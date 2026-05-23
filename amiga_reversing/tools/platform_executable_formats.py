from __future__ import annotations

import argparse
import json
import sys
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
    parser.add_argument("command", nargs="?", choices=("validate", "guardrails"), default="validate")
    parser.add_argument("--kb", type=Path, default=KB_PATH)
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH)
    args = parser.parse_args(list(argv) if argv is not None else None)

    kb = load_kb(args.kb)
    diagnostics = validate_kb(kb, load_schema(args.schema))
    for diagnostic in diagnostics:
        print(diagnostic)
    if diagnostics:
        return 1
    if args.command == "guardrails":
        print(json.dumps(build_guardrail_report(kb), indent=2))
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
