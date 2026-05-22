from __future__ import annotations

import json
from pathlib import Path

from amiga_reversing.disasm import decision_journal


def test_packet_reference_maps_rsset_packet_identity() -> None:
    packet = _rsset_packet()

    reference = decision_journal.decision_packet_reference(packet)

    assert reference == {
        "packet_id": "rsset-packet:rsset-raw-a6:022E:s0:000006E4:op1",
        "evidence_refs": ["rsset-packet:rsset-raw-a6:022E:s0:000006E4:op1"],
        "candidate_id": "rsset-raw-a6:022E",
        "selected_identity": packet["selected_identity"],
    }


def test_accept_fact_decision_record_validates_with_packet_reference() -> None:
    record = _decision_record("accept_fact")

    validation = decision_journal.validate_decision_record(record)

    assert validation == {"valid": True, "diagnostics": []}


def test_defer_reject_and_supersede_decision_records_validate() -> None:
    accept = _decision_record("accept_fact", decision_id="decision-accept")
    defer = _decision_record(
        "defer_fact",
        decision_id="decision-defer",
        prev=f"sha256:{decision_journal.decision_record_hash(accept)}",
    )
    reject = _decision_record(
        "reject_fact",
        decision_id="decision-reject",
        prev=f"sha256:{decision_journal.decision_record_hash(defer)}",
    )
    supersede = _supersede_record(
        "decision-supersede",
        supersedes="decision-accept",
        replacement="decision-defer",
        prev=f"sha256:{decision_journal.decision_record_hash(reject)}",
    )

    validation = decision_journal.validate_decision_journal_records([accept, defer, reject, supersede])

    assert validation["valid"] is True
    assert validation["diagnostics"] == []
    assert validation["superseded_decision_ids"] == ["decision-accept"]
    assert validation["record_count"] == 4


def test_invalid_accept_fact_reports_structured_diagnostics() -> None:
    record = _decision_record("accept_fact")
    del record["selected_identity"]["operand_index"]
    record["conflicts"] = [{"source": "ambiguous-a6-base"}]

    validation = decision_journal.validate_decision_record(record)

    assert validation["valid"] is False
    assert {"field": "selected_identity.operand_index", "message": "selected identity field is required"} in validation[
        "diagnostics"
    ]
    assert {
        "field": "conflicts",
        "message": "accept_fact conflicts must be explicit empty list",
    } in validation["diagnostics"]


def test_journal_chain_reports_bad_prev_duplicate_and_forward_supersession() -> None:
    accept = _decision_record("accept_fact", decision_id="decision-1")
    duplicate = _decision_record("reject_fact", decision_id="decision-1", prev="sha256:not-the-previous-record")
    supersede = _supersede_record(
        "decision-3",
        supersedes="decision-missing",
        replacement=None,
        prev=f"sha256:{decision_journal.decision_record_hash(duplicate)}",
    )

    validation = decision_journal.validate_decision_journal_records([accept, duplicate, supersede])

    assert validation["valid"] is False
    assert {"index": 1, "field": "decision_id", "message": "duplicate decision id: decision-1"} in validation[
        "diagnostics"
    ]
    assert {
        "index": 1,
        "field": "prev",
        "message": f"prev must be 'sha256:{decision_journal.decision_record_hash(accept)}' for append-only chain",
    } in validation["diagnostics"]
    assert {
        "index": 2,
        "field": "supersedes_decision_id",
        "message": "supersession target must refer to an earlier decision",
    } in validation["diagnostics"]


def test_decision_journal_appends_and_reads_jsonl_chain(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    first = _decision_record("defer_fact", decision_id="decision-1")
    second = _decision_record(
        "reject_fact",
        decision_id="decision-2",
        prev=f"sha256:{decision_journal.decision_record_hash(first)}",
    )

    first_append = decision_journal.append_decision_record(target_dir, first)
    second_append = decision_journal.append_decision_record(target_dir, second)
    readback = decision_journal.read_decision_journal(target_dir)

    assert first_append["status"] == "appended"
    assert first_append["record_count"] == 1
    assert second_append["status"] == "appended"
    assert second_append["record_count"] == 2
    assert readback["valid"] is True
    assert readback["records"] == [first, second]
    assert readback["validation"]["active_decision_ids"] == ["decision-1", "decision-2"]
    assert decision_journal.decision_journal_next_prev(readback["records"]) == (
        f"sha256:{decision_journal.decision_record_hash(second)}"
    )


def test_decision_journal_rejects_invalid_append_without_writing(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    invalid = _decision_record("accept_fact")
    del invalid["candidate_id"]

    result = decision_journal.append_decision_record(target_dir, invalid)

    assert result["status"] == "rejected"
    assert {"index": 0, "field": "candidate_id", "message": "candidate_id must be a non-empty string"} in result[
        "diagnostics"
    ]
    assert not decision_journal.decision_journal_path(target_dir).exists()


def test_decision_journal_reports_malformed_jsonl_and_blocks_append(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    path = decision_journal.decision_journal_path(target_dir)
    target_dir.mkdir(parents=True)
    path.write_text('{"schema":"evidence-decision/v1"}\nnot json\n', encoding="utf-8")

    readback = decision_journal.read_decision_journal(target_dir)
    append = decision_journal.append_decision_record(target_dir, _decision_record("defer_fact"))

    assert readback["valid"] is False
    assert {"line": 2, "field": "$", "message": "malformed JSONL: Expecting value"} in readback["diagnostics"]
    assert append["status"] == "rejected"
    assert path.read_text(encoding="utf-8") == '{"schema":"evidence-decision/v1"}\nnot json\n'


def test_decision_journal_read_detects_bad_prev_duplicate_and_supersession(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    path = decision_journal.decision_journal_path(target_dir)
    first = _decision_record("defer_fact", decision_id="decision-1")
    duplicate = _decision_record("reject_fact", decision_id="decision-1", prev="sha256:bad")
    supersede = _supersede_record(
        "decision-3",
        supersedes="decision-missing",
        replacement=None,
        prev=f"sha256:{decision_journal.decision_record_hash(duplicate)}",
    )
    target_dir.mkdir(parents=True)
    path.write_text(
        "".join(
            f"{json.dumps(record, sort_keys=True, separators=(',', ':'))}\n"
            for record in [first, duplicate, supersede]
        ),
        encoding="utf-8",
    )

    readback = decision_journal.read_decision_journal(target_dir)

    assert readback["valid"] is False
    assert {"index": 1, "field": "decision_id", "message": "duplicate decision id: decision-1"} in readback[
        "diagnostics"
    ]
    assert {
        "index": 1,
        "field": "prev",
        "message": f"prev must be 'sha256:{decision_journal.decision_record_hash(first)}' for append-only chain",
    } in readback["diagnostics"]
    assert {
        "index": 2,
        "field": "supersedes_decision_id",
        "message": "supersession target must refer to an earlier decision",
    } in readback["diagnostics"]


def test_decision_journal_validation_is_side_effect_free(tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    packet = _rsset_packet()
    record = _decision_record("defer_fact")

    before_gate = dict(packet["command_gate"])
    validation = decision_journal.validate_decision_record(record)

    assert validation["valid"] is True
    assert packet["command_gate"] == before_gate
    assert packet["command_gate"]["state"] == "blocked"
    assert packet["command_gate"]["enabled"] is False
    assert not decision_journal.decision_journal_path(target_dir).exists()
    assert not (target_dir / "manual_actions.jsonl").exists()


def _decision_record(
    action: str,
    *,
    decision_id: str = "decision-rsset-022e",
    prev: str | None = None,
) -> dict[str, object]:
    packet_ref = decision_journal.decision_packet_reference(_rsset_packet())
    record: dict[str, object] = {
        "schema": decision_journal.DECISION_JOURNAL_SCHEMA,
        "decision_id": decision_id,
        "prev": prev,
        "created_at": "2026-05-22T00:00:00+00:00",
        "actor": {"kind": "llm", "name": "codex"},
        "action": action,
        **packet_ref,
        "conflicts": [],
    }
    if action == "accept_fact":
        record.update(
            {
                "fact_type": "rsset_app_base",
                "scope": {"kind": "selected_use", "hunk": 0, "addr": 0x6E4, "operand_index": 1},
            }
        )
    elif action == "defer_fact":
        record["defer_reason"] = "missing selected A6 base identity"
    elif action == "reject_fact":
        record["reject_reason"] = "not accepted under current evidence model"
    else:
        raise ValueError(action)
    return record


def _supersede_record(
    decision_id: str,
    *,
    supersedes: str,
    replacement: str | None,
    prev: str | None,
) -> dict[str, object]:
    record: dict[str, object] = {
        "schema": decision_journal.DECISION_JOURNAL_SCHEMA,
        "decision_id": decision_id,
        "prev": prev,
        "created_at": "2026-05-22T00:01:00+00:00",
        "actor": {"kind": "llm", "name": "codex"},
        "action": "supersede_decision",
        "supersedes_decision_id": supersedes,
        "reason": "new packet evidence replaces the earlier decision",
    }
    if replacement is not None:
        record["replacement_decision_id"] = replacement
    return record


def _rsset_packet() -> dict[str, object]:
    return {
        "packet_kind": "rsset_selected_use_evidence_packet",
        "schema_version": 1,
        "packet_id": "rsset-packet:rsset-raw-a6:022E:s0:000006E4:op1",
        "candidate_id": "rsset-raw-a6:022E",
        "candidate_family": "rsset_app_base",
        "selected_identity": {
            "target_id": "pandora",
            "segment_id": "s0",
            "hunk": 0,
            "addr": 0x6E4,
            "operand_index": 1,
            "base_register": "A6",
            "displacement": 0x22E,
        },
        "command_gate": {
            "command_id": "rsset.binding.bind",
            "state": "blocked",
            "enabled": False,
            "safe_to_mutate": False,
        },
    }
