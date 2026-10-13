"""Atomic canonical review batches preserve the single-review decision semantics."""

import json

import pytest

from amiga_reversing.disasm import restoration, restoration_verification
from amiga_reversing.disasm.decision_journal import read_decision_journal
from tests.test_restoration_operations import current, invoke
from tests.test_restoration_operations import target as target


def actions(target, count=3):
    return [target.add(interpretation=True, name=f"entry_{i}")["action_id"] for i in range(count)]


def review(ids, **parameters):
    return invoke("review_batch", expected_revision=current(), action_ids=ids,
                  decision="defer", reason="Bounded caller evidence", **parameters)


def test_batch_accept_loads_proof_and_history_once_and_returns_fresh_revision(target, monkeypatch):
    ids = actions(target)
    before = current()
    subject = restoration.revisions("test")["subject_revision"]
    calls = []
    proof = {"receipt_id": "proof", "kind": "verification", "subject_revision": subject,
             "exact": True, "large_detail": "x" * 100000}
    monkeypatch.setattr(restoration_verification, "load_receipt", lambda *args: calls.append(args) or proof)
    history = restoration._history
    history_calls = []
    monkeypatch.setattr(restoration, "_history", lambda *args, **kw: history_calls.append(kw) or history(*args, **kw))
    result = invoke("review_batch", expected_revision=before, action_ids=ids, decision="accept",
                    reason="Exact source and grounded consumers", verification_id="proof")
    assert len(calls) == len(history_calls) == 1
    assert history_calls[0]["journal"]["valid"]
    assert result["revision"] != before
    assert result["revision"] == current()
    assert result["verification"] == {key: proof[key] for key in ("receipt_id", "kind", "subject_revision", "exact")}
    assert [item["action_id"] for item in result["decisions"]] == ids
    assert len(json.dumps(result)) < 65536
    assert read_decision_journal(target.directory)["valid"]


@pytest.mark.parametrize("invalid", [[], ["missing"], ["same", "same"], ["a"] * 101, [None], ["x" * 257]])
def test_batch_identity_guards_leave_histories_unchanged(target, invalid):
    actions(target)
    manual = (target.directory / "manual_actions.jsonl").read_bytes()
    with pytest.raises(ValueError, match="review_batch|current active manual action"):
        review(invalid)
    assert (target.directory / "manual_actions.jsonl").read_bytes() == manual
    assert not (target.directory / "decision_journal.jsonl").exists()


@pytest.mark.parametrize("failure", ["inactive", "no_evidence", "stale_proof", "stale_probe", "stale_revision"])
def test_invalid_middle_action_or_proof_is_atomic(target, monkeypatch, failure):
    ids = actions(target)
    old = current()
    if failure == "inactive":
        invoke("rollback", expected_revision=current(), action_id=ids[1])
    elif failure == "no_evidence":
        ids[1] = target.add(name="legacy")["action_id"]
    elif failure == "stale_revision":
        target.add(name="changed")
    monkeypatch.setattr(restoration_verification, "load_receipt",
                        lambda *_: {"kind": "probe" if failure == "stale_probe" else "verification",
                                    "subject_revision": "old", "exact": True})
    body = {"expected_revision": old if failure == "stale_revision" else current(),
            "action_ids": ids, "decision": "accept" if failure == "stale_proof" else "defer",
            "reason": "Consumers inspected", "verification_id": "proof"}
    if failure == "stale_probe":
        body["probe_id"] = "probe"
    manual = (target.directory / "manual_actions.jsonl").read_bytes()
    with pytest.raises(ValueError, match="current active|no evidence|exact rebuild|stale source subject|stale_revision"):
        invoke("review_batch", **body)
    assert (target.directory / "manual_actions.jsonl").read_bytes() == manual
    assert not (target.directory / "decision_journal.jsonl").exists()


def test_invalid_generated_middle_record_preserves_existing_journal(target, monkeypatch):
    ids = actions(target)
    review(ids)
    path = target.directory / "decision_journal.jsonl"
    before = path.read_bytes()
    prepare = restoration._prepare_review_records
    def invalid(*args):
        records, decision = prepare(*args)
        if args[3]["action_id"] == ids[1]:
            decision["prev"] = "sha256:" + "0" * 64
        return records, decision
    monkeypatch.setattr(restoration, "_prepare_review_records", invalid)
    with pytest.raises(ValueError, match="decision rejected"):
        review(ids)
    assert path.read_bytes() == before


def test_batch_matches_single_reviews_and_sequential_supersessions(target):
    ids = actions(target)
    path = target.directory / "decision_journal.jsonl"
    for decision in ("defer", "reject"):
        for identity in ids:
            invoke("review", expected_revision=current(), action_id=identity,
                   decision=decision, reason="Consumers inspected")
    singles = read_decision_journal(target.directory)
    path.unlink()
    for decision in ("defer", "reject"):
        invoke("review_batch", expected_revision=current(), action_ids=ids,
               decision=decision, reason="Consumers inspected")
    batched = read_decision_journal(target.directory)
    assert singles["valid"] and batched["valid"]
    def semantic(records):
        return [{key: value for key, value in record.items()
                 if key not in {"decision_id", "created_at", "prev", "supersedes_decision_id", "replacement_decision_id"}}
                for record in records]
    assert semantic(singles["records"]) == semantic(batched["records"])
    assert len(batched["records"]) == 9
    assert [item["status"] for item in invoke("history")["items"] if item["action_id"] in ids] == ["rejected"] * 3
