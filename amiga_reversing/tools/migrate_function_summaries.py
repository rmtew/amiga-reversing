from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from amiga_reversing.disasm.target_metadata import FunctionSummaryMetadata

_LEGACY_CREATE_CALLBACK = "create_manual_callback_table_signature"
_LEGACY_REMOVE_CALLBACK = "remove_manual_callback_table_signature"
_LEGACY_CREATE_DIRECT = "create_manual_function_register_contract"
_LEGACY_REMOVE_DIRECT = "remove_manual_function_register_contract"
_LEGACY_KINDS = {
    _LEGACY_CREATE_CALLBACK,
    _LEGACY_REMOVE_CALLBACK,
    _LEGACY_CREATE_DIRECT,
    _LEGACY_REMOVE_DIRECT,
}
_FUNCTION_SUMMARY_CREATE = "create_manual_function_summary"


def _unknown_effects() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "registers": {"state": "unknown"},
        "memory": {"state": "unknown"},
        "escapes": {"state": "unknown"},
    }


def _migrate_legacy_effects(summary: dict[str, Any]) -> dict[str, Any]:
    """Replace exactly the retired all-unknown triple with the v1 object.

    A migrated record is deliberately rejected instead of being silently
    passed through: this command is an auditable one-shot conversion, not a
    compatibility reader.
    """
    if "effects" in summary:
        raise ValueError("function summary already uses the canonical effects schema")
    retired = ("return_contract", "register_effects", "memory_effects")
    if any(summary.get(name) != "unknown" for name in retired):
        raise ValueError("function summary has unsupported legacy effect payload")
    converted = dict(summary)
    for name in retired:
        del converted[name]
    converted["effects"] = _unknown_effects()
    inputs = converted.get("inputs")
    if not isinstance(inputs, list):
        raise ValueError("function summary inputs must be a list")
    converted_inputs: list[dict[str, Any]] = []
    for input_payload in inputs:
        if not isinstance(input_payload, dict):
            raise ValueError("function summary input must be an object")
        location = input_payload.get("location")
        if not isinstance(location, str) or len(location) != 2 or location[0].upper() not in {"D", "A"} or location[1] not in "01234567":
            raise ValueError("legacy function summary input location must be Dn or An")
        converted_input = dict(input_payload)
        converted_input["location"] = {"kind": "register", "register": location.upper(), "width": 4}
        converted_inputs.append(converted_input)
    converted["inputs"] = converted_inputs
    converted["results"] = []
    FunctionSummaryMetadata.from_dict(converted)
    return converted


@dataclass(frozen=True)
class _LegacyFact:
    action_id: str
    sequence: int
    created_at: str | None
    kind: str
    payload: dict[str, Any]


def _required_string(payload: dict[str, Any], name: str) -> str:
    value = payload.get(name)
    if not isinstance(value, str) or not value:
        raise ValueError(f"legacy summary migration requires non-empty {name}")
    return value


def _required_nonnegative_int(payload: dict[str, Any], name: str) -> int:
    value = payload.get(name)
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"legacy summary migration requires non-negative integer {name}")
    return value


def _input_from_legacy(payload: dict[str, Any]) -> dict[str, object]:
    return {
        "location": {"kind": "register", "register": _required_string(payload, "register").upper(), "width": 4},
        "value_kind": "struct_ptr",
        "struct_name": _required_string(payload, "struct_name"),
    }


def _direct_summary_key(payload: dict[str, Any]) -> tuple[str, int, int]:
    return ("direct", _required_nonnegative_int(payload, "hunk"), _required_nonnegative_int(payload, "entry_offset"))


def _callback_summary_key(payload: dict[str, Any]) -> tuple[str, int, int, int]:
    return (
        "callback_table",
        _required_nonnegative_int(payload, "hunk"),
        _required_nonnegative_int(payload, "table_offset"),
        _required_nonnegative_int(payload, "entry_count"),
    )


def _summary_id(key: tuple[object, ...]) -> str:
    if key[0] == "direct":
        _, hunk, entry_offset = key
        return f"function-summary-entry-h{hunk}-{entry_offset:08X}"
    _, hunk, table_offset, entry_count = key
    return f"function-summary-table-h{hunk}-{table_offset:08X}-{entry_count}"


def _legacy_identity(kind: str, payload: dict[str, Any]) -> str:
    if kind == _LEGACY_CREATE_CALLBACK:
        return _required_string(payload, "callback_table_signature_id")
    return _required_string(payload, "function_register_contract_id")


def _remove_identity(kind: str, record: dict[str, Any]) -> str:
    field = "callback_table_signature_id" if kind == _LEGACY_REMOVE_CALLBACK else "function_register_contract_id"
    return _required_string(record, field)


def _load_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            raise ValueError(f"manual action log contains blank line {line_number}")
        record = json.loads(line)
        if not isinstance(record, dict):
            raise ValueError(f"manual action log record {line_number} is not an object")
        records.append(record)
    return records


def migrate_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Convert retired callable facts into canonical summary facts.

    The output intentionally carries only the new schema.  The report, rather
    than a legacy runtime projection, preserves the retired history and its
    mapping to canonical callable summaries.
    """
    active: OrderedDict[str, _LegacyFact] = OrderedDict()
    legacy_history: list[dict[str, Any]] = []
    summary_schema_migrations: list[dict[str, Any]] = []
    retained: list[dict[str, Any]] = []
    max_sequence = -1
    previous_sequence = -1
    seen_action_ids: set[str] = set()
    legacy_action_ids = {
        action_id
        for record in records
        if record.get("record") == "manual_action"
        if record.get("kind") in _LEGACY_KINDS
        if isinstance(action_id := record.get("action_id"), str) and action_id
    }
    legacy_summary_action_ids = {
        action_id
        for record in records
        if record.get("record") == "manual_action"
        if record.get("kind") == _FUNCTION_SUMMARY_CREATE
        if isinstance(action_id := record.get("action_id"), str) and action_id
    }
    active_summary_action_ids: OrderedDict[str, str] = OrderedDict()
    for record in records:
        if record.get("record") != "manual_action":
            retained.append(record)
            continue
        action_id = record.get("action_id")
        sequence = record.get("sequence")
        kind = record.get("kind")
        if not isinstance(action_id, str) or not action_id:
            raise ValueError("manual action log record lacks action_id")
        if action_id in seen_action_ids:
            raise ValueError(f"manual action log repeats action_id {action_id}")
        seen_action_ids.add(action_id)
        if not isinstance(sequence, int) or sequence < 0:
            raise ValueError(f"manual action {action_id} lacks non-negative sequence")
        if sequence <= previous_sequence:
            raise ValueError("manual action log sequences must be strictly increasing")
        previous_sequence = sequence
        max_sequence = max(max_sequence, sequence)
        if kind == _FUNCTION_SUMMARY_CREATE:
            summary = record.get("function_summary")
            if not isinstance(summary, dict):
                raise ValueError(f"manual action {action_id} lacks function_summary")
            converted_record = dict(record)
            converted_summary = _migrate_legacy_effects(summary)
            converted_record["function_summary"] = converted_summary
            summary_id = _required_string(converted_summary, "function_summary_id")
            if summary_id in active_summary_action_ids:
                raise ValueError(f"function summary {summary_id} is created more than once without removal")
            active_summary_action_ids[summary_id] = action_id
            retained.append(converted_record)
            summary_schema_migrations.append({
                "action_id": action_id,
                "sequence": sequence,
                "function_summary_id": summary_id,
            })
            continue
        if kind == "remove_manual_function_summary":
            summary_id = _required_string(record, "function_summary_id")
            if active_summary_action_ids.pop(summary_id, None) is None:
                raise ValueError(f"manual action {action_id} removes unknown function summary {summary_id}")
            retained.append(record)
            continue
        if kind not in _LEGACY_KINDS:
            if kind in {"undo_action", "redo_action"}:
                reference_name = "undoes_action_id" if kind == "undo_action" else "redoes_action_id"
                reference = record.get(reference_name)
                if reference in legacy_action_ids or reference in legacy_summary_action_ids:
                    raise ValueError("migrated callable actions referenced by undo/redo require explicit resolution")
            retained.append(record)
            continue
        if kind in {_LEGACY_CREATE_CALLBACK, _LEGACY_CREATE_DIRECT}:
            payload_name = "callback_table_signature" if kind == _LEGACY_CREATE_CALLBACK else "function_register_contract"
            payload = record.get(payload_name)
            if not isinstance(payload, dict):
                raise ValueError(f"manual action {action_id} lacks {payload_name}")
            identity = _legacy_identity(kind, payload)
            if identity in active:
                raise ValueError(f"legacy callable fact {identity} is created more than once without removal")
            active[identity] = _LegacyFact(
                action_id=action_id,
                sequence=sequence,
                created_at=record.get("created_at") if isinstance(record.get("created_at"), str) else None,
                kind=kind,
                payload=payload,
            )
            legacy_history.append({"action_id": action_id, "sequence": sequence, "kind": kind, "state": "created"})
            continue
        identity = _remove_identity(kind, record)
        removed = active.pop(identity, None)
        if removed is None:
            raise ValueError(f"manual action {action_id} removes unknown legacy callable fact {identity}")
        legacy_history.append({
            "action_id": action_id,
            "sequence": sequence,
            "kind": kind,
            "state": "removed",
            "retired_action_id": removed.action_id,
        })

    grouped: OrderedDict[tuple[object, ...], list[_LegacyFact]] = OrderedDict()
    for fact in active.values():
        key = _callback_summary_key(fact.payload) if fact.kind == _LEGACY_CREATE_CALLBACK else _direct_summary_key(fact.payload)
        grouped.setdefault(key, []).append(fact)

    summaries: list[dict[str, Any]] = []
    for key, facts in grouped.items():
        inputs: list[dict[str, object]] = []
        input_locations: set[str] = set()
        for fact in facts:
            item = _input_from_legacy(fact.payload)
            location = item["location"]
            assert isinstance(location, dict)
            location_identity = str(location)
            if location_identity in input_locations:
                raise ValueError(f"callable {_summary_id(key)} has duplicate input location {item['location']}")
            input_locations.add(location_identity)
            inputs.append(item)
        first = facts[0]
        summary: dict[str, Any] = {
            "function_summary_id": _summary_id(key),
            "hunk": key[1],
            "callable_kind": key[0],
            "inputs": inputs,
            "results": [],
            "effects": _unknown_effects(),
            "note": first.payload.get("note", "Migrated function summary"),
            "context_name": first.payload.get("context_name", ""),
        }
        if key[0] == "direct":
            summary["entry_offset"] = key[2]
        else:
            summary["table_offset"] = key[2]
            summary["entry_count"] = key[3]
        summaries.append({
            "summary": summary,
            "source_action_ids": [fact.action_id for fact in facts],
            "source_fact_ids": [_legacy_identity(fact.kind, fact.payload) for fact in facts],
            "created_at": first.created_at,
        })

    converted = list(retained)
    for summary_index, item in enumerate(summaries, start=1):
        summary = item["summary"]
        if summary["function_summary_id"] in active_summary_action_ids:
            raise ValueError(f"legacy callable migration conflicts with active function summary {summary['function_summary_id']}")
        converted.append({
            "record": "manual_action",
            "action_id": f"migration-{summary['function_summary_id']}",
            "sequence": max_sequence + summary_index,
            "created_at": item["created_at"],
            "kind": "create_manual_function_summary",
            "function_summary": summary,
        })
    report = {
        "schema_version": 2,
        "retired_action_history": legacy_history,
        "active_summary_mappings": [
            {
                "function_summary_id": item["summary"]["function_summary_id"],
                "source_action_ids": item["source_action_ids"],
                "source_fact_ids": item["source_fact_ids"],
            }
            for item in summaries
        ],
        "summary_schema_migrations": summary_schema_migrations,
    }
    return converted, report


def migrate_canonical_location_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Convert the retired register-string location form in canonical summaries.

    This is deliberately separate from the retired-fact/effect-schema migration
    above. It accepts only fully canonical v1 effects and refuses an input log
    that has already been converted or mixes object and string locations.
    """
    converted: list[dict[str, Any]] = []
    migrations: list[dict[str, Any]] = []
    seen_action_ids: set[str] = set()
    previous_sequence = -1
    for record in records:
        if record.get("record") != "manual_action":
            converted.append(record)
            continue
        action_id = record.get("action_id")
        sequence = record.get("sequence")
        if not isinstance(action_id, str) or not action_id or action_id in seen_action_ids:
            raise ValueError("manual action log has missing or duplicate action_id")
        if not isinstance(sequence, int) or sequence < 0 or sequence <= previous_sequence:
            raise ValueError("manual action log sequences must be strictly increasing")
        seen_action_ids.add(action_id)
        previous_sequence = sequence
        if record.get("kind") != _FUNCTION_SUMMARY_CREATE:
            converted.append(record)
            continue
        summary = record.get("function_summary")
        if not isinstance(summary, dict):
            raise ValueError(f"manual action {action_id} lacks function_summary")
        effects = summary.get("effects")
        if effects != _unknown_effects():
            raise ValueError("location migration accepts only canonical all-unknown effects")
        inputs = summary.get("inputs")
        if not isinstance(inputs, list) or not inputs:
            raise ValueError("function summary inputs must be a non-empty list")
        converted_inputs: list[dict[str, Any]] = []
        for input_payload in inputs:
            if not isinstance(input_payload, dict):
                raise ValueError("function summary input must be an object")
            location = input_payload.get("location")
            if not isinstance(location, str) or len(location) != 2 or location[0].upper() not in {"D", "A"} or location[1] not in "01234567":
                raise ValueError("location migration requires every input to use a Dn/An register string")
            converted_input = dict(input_payload)
            converted_input["location"] = {"kind": "register", "register": location.upper(), "width": 4}
            converted_inputs.append(converted_input)
        converted_summary = dict(summary)
        converted_summary["inputs"] = converted_inputs
        converted_summary["results"] = []
        FunctionSummaryMetadata.from_dict(converted_summary)
        converted_record = dict(record)
        converted_record["function_summary"] = converted_summary
        converted.append(converted_record)
        migrations.append({
            "action_id": action_id,
            "sequence": sequence,
            "function_summary_id": _required_string(converted_summary, "function_summary_id"),
        })
    if not migrations:
        raise ValueError("location migration found no retired register-string summary inputs")
    return converted, {"schema_version": 1, "function_summary_location_migrations": migrations}


def migrate_canonical_result_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Add the mandatory canonical result collection to fully canonical summaries.

    This accepts only the pre-result summary schema and rejects a mixed or
    already-converted log. It is conversion tooling, not a runtime default for
    a missing member.
    """
    converted: list[dict[str, Any]] = []
    migrations: list[dict[str, Any]] = []
    seen_action_ids: set[str] = set()
    previous_sequence = -1
    for record in records:
        if record.get("record") != "manual_action":
            converted.append(record)
            continue
        action_id = record.get("action_id")
        sequence = record.get("sequence")
        if not isinstance(action_id, str) or not action_id or action_id in seen_action_ids:
            raise ValueError("manual action log has missing or duplicate action_id")
        if not isinstance(sequence, int) or sequence < 0 or sequence <= previous_sequence:
            raise ValueError("manual action log sequences must be strictly increasing")
        seen_action_ids.add(action_id)
        previous_sequence = sequence
        if record.get("kind") != _FUNCTION_SUMMARY_CREATE:
            converted.append(record)
            continue
        summary = record.get("function_summary")
        if not isinstance(summary, dict):
            raise ValueError(f"manual action {action_id} lacks function_summary")
        if "results" in summary:
            raise ValueError("result migration rejects an already-migrated or mixed summary")
        converted_summary = dict(summary)
        converted_summary["results"] = []
        FunctionSummaryMetadata.from_dict(converted_summary)
        converted_record = dict(record)
        converted_record["function_summary"] = converted_summary
        converted.append(converted_record)
        migrations.append({
            "action_id": action_id,
            "sequence": sequence,
            "function_summary_id": _required_string(converted_summary, "function_summary_id"),
        })
    if not migrations:
        raise ValueError("result migration found no pre-result function summaries")
    return converted, {"schema_version": 1, "function_summary_result_migrations": migrations}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migrate retired callable facts to function summaries.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    migration_group = parser.add_mutually_exclusive_group()
    migration_group.add_argument("--migrate-locations", action="store_true",
        help="migrate canonical function-summary register-string inputs to ABI location objects")
    migration_group.add_argument("--migrate-results", action="store_true",
        help="migrate canonical summaries to the required explicit results collection")
    args = parser.parse_args(argv)
    if args.output.exists() or args.report.exists():
        raise SystemExit("refusing to overwrite migration output or report")
    records = _load_records(args.input)
    if args.migrate_locations:
        converted, report = migrate_canonical_location_records(records)
    elif args.migrate_results:
        converted, report = migrate_canonical_result_records(records)
    else:
        converted, report = migrate_records(records)
    args.output.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in converted), encoding="utf-8")
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
