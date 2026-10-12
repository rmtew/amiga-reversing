from __future__ import annotations

import json
import multiprocessing
from pathlib import Path

import pytest

from amiga_reversing.disasm.binary_source import resolve_target_binary_source
from amiga_reversing.disasm.manual_actions import (
    ManualActionKind,
    append_manual_action,
    append_manual_actions,
    build_target_identity,
    load_manual_projection,
    manual_action_interpretation,
)
from amiga_reversing.disasm.target_history import history_revision, target_lock


def _source(path):
    return resolve_target_binary_source(path)


@pytest.fixture
def target(tmp_path):
    (tmp_path / "binary.bin").write_bytes(b"\x4e\x75")
    (tmp_path / "source_binary.json").write_text(
        json.dumps(
            {
                "kind": "raw_binary",
                "address_model": "local_offset",
                "path": str(tmp_path / "binary.bin"),
                "load_address": 0,
                "entrypoint": 0,
                "code_start_offset": 0,
            }
        )
    )
    return tmp_path


def _comment(text):
    return {"comment": {"comment_id": text, "hunk": 0, "addr": 0, "text": text}}


def _append_worker(path, number):
    target = Path(path)
    append_manual_action(
        target,
        kind=ManualActionKind.CREATE_MANUAL_COMMENT,
        payload=_comment(str(number)),
        binary_source=_source(target),
    )


def test_legacy_bytes_unknown_fields_and_identity_preserved(target):
    source = _source(target)
    header = {
        "record": "manual_action_log_header",
        "version": 1,
        "target_identity": build_target_identity(source),
        "unknown_header": ["preserve"],
    }
    record = {
        "record": "manual_action",
        "sequence": 1,
        "action_id": "old",
        "created_at": "old",
        "kind": "create_manual_comment",
        **_comment("original"),
        "unknown_extension": {"future": True},
    }
    raw = ("  " + json.dumps(header) + "\r\n" + json.dumps(record)).encode()
    path = target / "manual_actions.jsonl"
    path.write_bytes(raw)
    before = history_revision(target)
    with target_lock(target):
        append_manual_action(
            target,
            kind=ManualActionKind.CREATE_MANUAL_COMMENT,
            payload=_comment("next"),
            binary_source=source,
        )
    assert path.read_bytes().startswith(raw + b"\n")
    assert history_revision(target) != before
    assert {item["text"] for item in load_manual_projection(target).comments} == {
        "original",
        "next",
    }
    assert manual_action_interpretation(record) == {
        "source_evidence_status": "legacy_unassessed"
    }


def test_batch_failure_writes_nothing(target):
    append_manual_action(
        target,
        kind=ManualActionKind.CREATE_MANUAL_COMMENT,
        payload=_comment("old"),
        binary_source=_source(target),
    )
    path = target / "manual_actions.jsonl"
    before = path.read_bytes()
    with pytest.raises(ValueError, match="comment"):
        append_manual_actions(
            target,
            actions=[
                (ManualActionKind.CREATE_MANUAL_COMMENT, _comment("valid")),
                (ManualActionKind.CREATE_MANUAL_COMMENT, {"comment": None}),
            ],
            binary_source=_source(target),
        )
    assert path.read_bytes() == before


@pytest.mark.parametrize("corruption", [b"{bad json", b"{}\n", b"\xff"])
def test_malformed_log_refuses_append(target, corruption):
    path = target / "manual_actions.jsonl"
    path.write_bytes(corruption)
    with pytest.raises((ValueError, UnicodeError)):
        append_manual_action(
            target,
            kind=ManualActionKind.CREATE_MANUAL_COMMENT,
            payload=_comment("new"),
            binary_source=_source(target),
        )
    assert path.read_bytes() == corruption


def test_atomic_replace_failure_preserves_log(target, monkeypatch):
    import amiga_reversing.disasm.target_history as history

    append_manual_action(
        target,
        kind=ManualActionKind.CREATE_MANUAL_COMMENT,
        payload=_comment("old"),
        binary_source=_source(target),
    )
    path = target / "manual_actions.jsonl"
    before = path.read_bytes()

    def fail(*args):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(history.os, "replace", fail)
    with pytest.raises(OSError, match="simulated"):
        append_manual_action(
            target,
            kind=ManualActionKind.CREATE_MANUAL_COMMENT,
            payload=_comment("new"),
            binary_source=_source(target),
        )
    assert path.read_bytes() == before
    assert not list(target.glob(".manual_actions.jsonl.*"))


def test_concurrent_process_appends_keep_all_actions(target):
    context = multiprocessing.get_context("spawn")
    processes = [
        context.Process(target=_append_worker, args=(str(target), n)) for n in range(8)
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join(15)
        assert process.exitcode == 0
    records = [
        json.loads(line)
        for line in (target / "manual_actions.jsonl").read_text().splitlines()
    ]
    assert [record["sequence"] for record in records[1:]] == list(range(1, 9))
    assert len(load_manual_projection(target).comments) == 8


def test_metadata_is_optional_validated_and_preserved(target):
    metadata = {
        "source_evidence_status": "hypothesis",
        "confidence": "low",
        "reason": "Read accesses only",
        "evidence_refs": ["native:source:0"],
        "future_extension": {"keep": True},
    }
    record = append_manual_action(
        target,
        kind=ManualActionKind.CREATE_MANUAL_COMMENT,
        payload={**_comment("meaning"), "interpretation": metadata},
        binary_source=_source(target),
    )
    assert manual_action_interpretation(record) == metadata
    assert (
        json.loads((target / "manual_actions.jsonl").read_text().splitlines()[-1])[
            "interpretation"
        ]
        == metadata
    )
    with pytest.raises(ValueError, match="confidence"):
        append_manual_action(
            target,
            kind=ManualActionKind.CREATE_MANUAL_COMMENT,
            payload={
                **_comment("bad"),
                "interpretation": {**metadata, "confidence": "certain"},
            },
            binary_source=_source(target),
        )
