from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path

DECISION_JOURNAL_FILE_NAME = "decision_journal.jsonl"
DECISION_JOURNAL_SCHEMA = "evidence-decision/v1"
DECISION_JOURNAL_ACTIONS = frozenset(
    {
        "accept_fact",
        "defer_fact",
        "reject_fact",
        "supersede_decision",
    }
)
DECISION_JOURNAL_ACTOR_KINDS = frozenset({"human", "llm", "auto-analysis", "tool"})


def decision_journal_path(target_dir: Path) -> Path:
    return target_dir / DECISION_JOURNAL_FILE_NAME


def read_decision_journal(target_dir: Path) -> dict[str, object]:
    path = decision_journal_path(target_dir)
    if not path.exists():
        return _journal_read_result(path, [], [])
    records: list[dict[str, object]] = []
    diagnostics: list[dict[str, object]] = []
    try:
        with open(path, encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    raw = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    diagnostics.append(
                        {
                            "line": line_number,
                            "field": "$",
                            "message": f"malformed JSONL: {exc.msg}",
                        }
                    )
                    continue
                if not isinstance(raw, Mapping):
                    diagnostics.append(
                        {
                            "line": line_number,
                            "field": "$",
                            "message": "record must be an object",
                        }
                    )
                    continue
                records.append(dict(raw))
    except OSError as exc:
        diagnostics.append({"field": "$", "message": str(exc)})
    return _journal_read_result(path, records, diagnostics)


def append_decision_record(target_dir: Path, record: Mapping[str, object]) -> dict[str, object]:
    path = decision_journal_path(target_dir)
    current = read_decision_journal(target_dir)
    if not current["valid"]:
        return {
            "status": "rejected",
            "path": str(path),
            "record": dict(record),
            "validation": current["validation"],
            "diagnostics": current["diagnostics"],
        }
    records = [dict(existing) for existing in _record_sequence(current.get("records"))]
    next_records = [*records, dict(record)]
    validation = validate_decision_journal_records(next_records)
    if not validation["valid"]:
        return {
            "status": "rejected",
            "path": str(path),
            "record": dict(record),
            "validation": validation,
            "diagnostics": validation["diagnostics"],
        }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(record), sort_keys=True, separators=(",", ":")) + "\n")
    return {
        "status": "appended",
        "path": str(path),
        "record": dict(record),
        "validation": validation,
        "head_hash": decision_record_hash(record),
        "record_count": len(next_records),
    }


def decision_journal_report(
    target_dir: Path,
    *,
    dry_run_record: object | None = None,
) -> dict[str, object]:
    path = decision_journal_path(target_dir)
    readback = read_decision_journal(target_dir)
    records = _record_sequence(readback.get("records"))
    report: dict[str, object] = {
        "path": str(path),
        "exists": path.exists(),
        "valid": readback["valid"],
        "record_count": len(records),
        "diagnostics": readback["diagnostics"],
        "validation": readback["validation"],
        "next_prev": decision_journal_next_prev(records),
    }
    if dry_run_record is not None:
        report["dry_run_record"] = dry_run_decision_record(records, dry_run_record, current_valid=readback["valid"])
    return report


def dry_run_decision_record(
    records: Sequence[object],
    record: object,
    *,
    current_valid: object = True,
) -> dict[str, object]:
    if not isinstance(record, Mapping):
        validation = {
            "valid": False,
            "diagnostics": [{"index": len(records), "field": "$", "message": "record must be an object"}],
            "active_decision_ids": [],
            "superseded_decision_ids": [],
            "record_count": len(records) + 1,
        }
        return {"record": record, "status": "rejected", "validation": validation, "diagnostics": validation["diagnostics"]}
    if current_valid is not True:
        validation = validate_decision_journal_records(records)
        diagnostics = validation["diagnostics"] or [
            {"field": "$", "message": "current journal is invalid; proposed record was not evaluated"}
        ]
        return {"record": dict(record), "status": "rejected", "validation": validation, "diagnostics": diagnostics}
    validation = validate_decision_journal_records([*records, dict(record)])
    return {
        "record": dict(record),
        "status": "valid" if validation["valid"] else "rejected",
        "validation": validation,
        "diagnostics": validation["diagnostics"],
    }


def decision_journal_next_prev(records: Sequence[object]) -> str | None:
    if not records:
        return None
    last = records[-1]
    if not isinstance(last, Mapping):
        return None
    return f"sha256:{decision_record_hash(last)}"


def decision_packet_reference(packet: Mapping[str, object]) -> dict[str, object]:
    packet_id = _text(packet.get("packet_id"))
    candidate_id = _text(packet.get("candidate_id"))
    selected_identity = packet.get("selected_identity")
    reference: dict[str, object] = {}
    if packet_id is not None:
        reference["packet_id"] = packet_id
        reference["evidence_refs"] = [packet_id]
    if candidate_id is not None:
        reference["candidate_id"] = candidate_id
    if isinstance(selected_identity, Mapping):
        reference["selected_identity"] = dict(selected_identity)
    return reference


def decision_record_hash(record: Mapping[str, object]) -> str:
    payload = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_decision_record(record: Mapping[str, object]) -> dict[str, object]:
    diagnostics = _decision_record_diagnostics(record)
    return {
        "valid": not diagnostics,
        "diagnostics": diagnostics,
    }


def validate_decision_journal_records(records: Sequence[object]) -> dict[str, object]:
    diagnostics: list[dict[str, object]] = []
    decision_ids: set[str] = set()
    superseded_ids: set[str] = set()
    previous_record: Mapping[str, object] | None = None

    for index, raw_record in enumerate(records):
        if not isinstance(raw_record, Mapping):
            diagnostics.append(_diagnostic(index, "$", "record must be an object"))
            previous_record = None
            continue
        record = raw_record
        for diagnostic in _decision_record_diagnostics(record):
            diagnostics.append({**diagnostic, "index": index})

        decision_id = _text(record.get("decision_id"))
        if decision_id is not None:
            if decision_id in decision_ids:
                diagnostics.append(_diagnostic(index, "decision_id", f"duplicate decision id: {decision_id}"))
            decision_ids.add(decision_id)

        expected_prev = None if previous_record is None else f"sha256:{decision_record_hash(previous_record)}"
        actual_prev = record.get("prev")
        if actual_prev != expected_prev:
            diagnostics.append(
                _diagnostic(
                    index,
                    "prev",
                    f"prev must be {expected_prev!r} for append-only chain",
                )
            )

        if record.get("action") == "supersede_decision":
            superseded = _text(record.get("supersedes_decision_id"))
            if superseded is not None:
                superseded_ids.add(superseded)
                if superseded not in decision_ids:
                    diagnostics.append(
                        _diagnostic(
                            index,
                            "supersedes_decision_id",
                            "supersession target must refer to an earlier decision",
                        )
                    )

        previous_record = record

    active_ids = sorted(decision_ids - superseded_ids)
    return {
        "valid": not diagnostics,
        "diagnostics": diagnostics,
        "active_decision_ids": active_ids,
        "superseded_decision_ids": sorted(superseded_ids),
        "record_count": len(records),
    }


def _journal_read_result(
    path: Path,
    records: list[dict[str, object]],
    read_diagnostics: list[dict[str, object]],
) -> dict[str, object]:
    validation = validate_decision_journal_records(records)
    diagnostics = [*read_diagnostics, *validation["diagnostics"]]
    return {
        "path": str(path),
        "valid": not diagnostics,
        "records": records,
        "diagnostics": diagnostics,
        "validation": {**validation, "valid": not diagnostics, "diagnostics": diagnostics},
    }


def _record_sequence(value: object) -> list[dict[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        return []
    return [dict(record) for record in value if isinstance(record, Mapping)]


def _decision_record_diagnostics(record: Mapping[str, object]) -> list[dict[str, object]]:
    diagnostics: list[dict[str, object]] = []
    schema = record.get("schema")
    if schema != DECISION_JOURNAL_SCHEMA:
        diagnostics.append(_diagnostic(None, "schema", f"schema must be {DECISION_JOURNAL_SCHEMA!r}"))
    action = _text(record.get("action"))
    if action not in DECISION_JOURNAL_ACTIONS:
        diagnostics.append(_diagnostic(None, "action", "action must be a supported decision action"))
        return diagnostics

    _require_text(record, "decision_id", diagnostics)
    _require_text(record, "created_at", diagnostics)
    _validate_actor(record.get("actor"), diagnostics)

    if action == "supersede_decision":
        _require_text(record, "supersedes_decision_id", diagnostics)
        _require_text(record, "reason", diagnostics)
        replacement = record.get("replacement_decision_id")
        if replacement is not None and _text(replacement) is None:
            diagnostics.append(_diagnostic(None, "replacement_decision_id", "replacement_decision_id must be a string"))
        return diagnostics

    _require_text(record, "candidate_id", diagnostics)
    _validate_selected_identity(record.get("selected_identity"), diagnostics)
    _validate_evidence_refs(record.get("evidence_refs"), diagnostics)
    _validate_conflict_state(record.get("conflicts"), diagnostics)

    if action == "accept_fact":
        _require_text(record, "fact_type", diagnostics)
        _validate_scope(record.get("scope"), diagnostics)
        if record.get("conflicts") != []:
            diagnostics.append(_diagnostic(None, "conflicts", "accept_fact conflicts must be explicit empty list"))
    elif action == "defer_fact":
        _require_text(record, "defer_reason", diagnostics)
    elif action == "reject_fact":
        _require_text(record, "reject_reason", diagnostics)
    return diagnostics


def _validate_actor(value: object, diagnostics: list[dict[str, object]]) -> None:
    if not isinstance(value, Mapping):
        diagnostics.append(_diagnostic(None, "actor", "actor must be an object"))
        return
    kind = value.get("kind")
    if kind not in DECISION_JOURNAL_ACTOR_KINDS:
        diagnostics.append(_diagnostic(None, "actor.kind", "actor.kind must be a supported actor kind"))


def _validate_selected_identity(value: object, diagnostics: list[dict[str, object]]) -> None:
    if not isinstance(value, Mapping):
        diagnostics.append(_diagnostic(None, "selected_identity", "selected_identity must be an object"))
        return
    for key in ("target_id", "segment_id", "hunk", "addr", "operand_index"):
        if key not in value:
            diagnostics.append(_diagnostic(None, f"selected_identity.{key}", "selected identity field is required"))
    for key in ("target_id", "segment_id"):
        if key in value and _text(value.get(key)) is None:
            diagnostics.append(_diagnostic(None, f"selected_identity.{key}", "selected identity field must be a string"))
    for key in ("hunk", "addr", "operand_index"):
        if key in value and _int(value.get(key)) is None:
            diagnostics.append(_diagnostic(None, f"selected_identity.{key}", "selected identity field must be an integer"))


def _validate_evidence_refs(value: object, diagnostics: list[dict[str, object]]) -> None:
    if isinstance(value, str) or not isinstance(value, Sequence) or not value:
        diagnostics.append(_diagnostic(None, "evidence_refs", "evidence_refs must be a non-empty sequence"))
        return
    for index, item in enumerate(value):
        if _text(item) is None:
            diagnostics.append(_diagnostic(None, f"evidence_refs[{index}]", "evidence ref must be a string"))


def _validate_conflict_state(value: object, diagnostics: list[dict[str, object]]) -> None:
    if isinstance(value, str) or not isinstance(value, Sequence):
        diagnostics.append(_diagnostic(None, "conflicts", "conflicts must be an explicit sequence"))
        return
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            diagnostics.append(_diagnostic(None, f"conflicts[{index}]", "conflict entry must be an object"))


def _validate_scope(value: object, diagnostics: list[dict[str, object]]) -> None:
    if not isinstance(value, Mapping):
        diagnostics.append(_diagnostic(None, "scope", "scope must be an object"))
        return
    if _text(value.get("kind")) is None:
        diagnostics.append(_diagnostic(None, "scope.kind", "scope.kind must be a string"))


def _require_text(record: Mapping[str, object], key: str, diagnostics: list[dict[str, object]]) -> None:
    if _text(record.get(key)) is None:
        diagnostics.append(_diagnostic(None, key, f"{key} must be a non-empty string"))


def _diagnostic(index: int | None, field: str, message: str) -> dict[str, object]:
    diagnostic: dict[str, object] = {
        "field": field,
        "message": message,
    }
    if index is not None:
        diagnostic["index"] = index
    return diagnostic


def _text(value: object) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def _int(value: object) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None
