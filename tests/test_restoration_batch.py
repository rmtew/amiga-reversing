"""Atomic catalog interpretation batches use real histories and native rebuilds."""

import json
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace

import pytest

from amiga_reversing.disasm import c_backend, restoration, server
from amiga_reversing.disasm.binary_source import resolve_target_binary_source
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.manual_actions import load_manual_projection
from src.tests._platform_backend_test_utils import make_synthetic_hunkexe
from tests.listing_types_fixtures import ListingRow
from tests.test_disasm_server import (
    _binary_project,
    _element_command_context,
    _row_command_context,
    _RowsCListingArtifact,
    _seed_c_listing_artifact,
)


@pytest.fixture
def batch_target(tmp_path, monkeypatch):
    binary = tmp_path / "source.hunk"
    original = make_synthetic_hunkexe()
    binary.write_bytes(original)
    (tmp_path / "source_binary.json").write_text(
        json.dumps({"kind": "hunk_file", "path": str(binary)})
    )
    source = resolve_target_binary_source(tmp_path)
    paths = SimpleNamespace(target_dir=tmp_path, binary_source=source)
    monkeypatch.setattr(server, "resolve_project_paths", lambda *a, **kw: paths)
    monkeypatch.setattr(
        server,
        "get_project",
        lambda name: replace(
            _binary_project(name, ready=True), target_dir=str(tmp_path)
        ),
    )
    monkeypatch.setattr(server, "mark_project_updated", lambda _: None)
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="rts\n",
            addr=0,
            section_index=0,
            start_offset=0,
            end_offset=2,
            stable_key="s0:00000000:instruction",
        ),
        ListingRow(
            row_id="r1",
            kind="label",
            text="loc_0_00000000:\n",
            addr=0,
            section_index=0,
            start_offset=0,
            end_offset=0,
            label="loc_0_00000000",
            stable_key="s0:00000000:label",
        ),
    ]
    _seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
    entries = [
        {
            "command_id": "label.rename",
            "context": _element_command_context(
                rows[1], "s0:00000000:label:label:loc_0_00000000"
            ),
            "parameters": {"name": "entry_returns"},
        },
        {
            "command_id": "comment.edit",
            "context": _row_command_context(rows[0]),
            "parameters": {"text": "Synthetic entry returns to its caller."},
        },
    ]
    for entry in entries:
        entry["evidence"] = {
            "reason": "Inspected return instruction at section entry.",
            "source_evidence_refs": ["s0:00000000:instruction"],
        }
    yield SimpleNamespace(
        directory=tmp_path, source=source, original=original, entries=entries
    )
    server._LISTING_PROJECTION_SERVICE.reset()


def invoke(target, entries=None, revision=None):
    return restoration.execute(
        "bloodwych",
        {
            "operation": "interpret_batch",
            "expected_revision": revision
            or restoration.revisions("bloodwych")["revision"],
            "entries": target.entries if entries is None else entries,
        },
    )


def test_mixed_batch_one_append_invalidation_and_exact_rebuild(
    batch_target, monkeypatch
):
    calls = []
    original_append = server.append_manual_actions
    monkeypatch.setattr(
        server,
        "append_manual_actions",
        lambda *a, **kw: (calls.append(kw["actions"]), original_append(*a, **kw))[1],
    )
    result = invoke(batch_target)
    assert len(calls) == 1 and len(calls[0]) == 2
    assert len(result["actions"]) == 2
    assert [c["command_id"] for c in result["commands"]] == [
        "label.rename",
        "comment.edit",
    ]
    spans = result["workflow_profile"]["spans"]
    assert sum(s["name"] == "listing_cache_invalidation" for s in spans) == 1
    projection = load_manual_projection(
        batch_target.directory, binary_source=batch_target.source
    )
    assert projection.labels[0]["name"] == "entry_returns"
    assert all(
        a["interpretation"]["subject_revision"]
        == result["actions"][0]["interpretation"]["subject_revision"]
        for a in result["actions"]
    )
    with effective_metadata_file(batch_target.directory) as metadata:
        text = c_backend.render_project_source_with_c_backend(
            batch_target.source, metadata_path=metadata
        )
        assert "entry_returns:" in text
        assert "Synthetic entry returns to its caller." in text
        rebuilt, _, _ = (
            c_backend.facts_v2_direct_rebuild_project_source_with_c_backend_profile(
                batch_target.source, metadata_path=metadata, compare_original=True
            )
        )
    assert rebuilt == batch_target.original


@pytest.mark.parametrize("failure", ["catalog", "context", "evidence", "comment_codec"])
def test_invalid_last_entry_preserves_both_histories(batch_target, failure):
    invoke(batch_target, entries=[batch_target.entries[0]])
    history = batch_target.directory / "manual_actions.jsonl"
    journal = batch_target.directory / "decision_journal.jsonl"
    journal.write_bytes(b"preserve unrelated journal bytes\n")
    before = history.read_bytes()
    entries = deepcopy(batch_target.entries)
    if failure == "catalog":
        entries[-1]["command_id"] = "not.available"
    elif failure == "context":
        entries[-1]["context"]["locator"]["row_key"] = "s0:00000002:instruction"
    elif failure == "evidence":
        entries[-1]["evidence"]["source_evidence_refs"] = ["s0:00000002:instruction"]
    else:
        entries[-1]["parameters"]["text"] = "line\nnext"
    with pytest.raises(
        ValueError, match="available|locator|reference|codec|losslessly|capacity|batch"
    ):
        invoke(batch_target, entries=entries)
    assert history.read_bytes() == before
    assert journal.read_bytes() == b"preserve unrelated journal bytes\n"


def test_stale_batch_refused_before_any_append(batch_target):
    revision = restoration.revisions("bloodwych")["revision"]
    invoke(batch_target, entries=[batch_target.entries[0]])
    path = batch_target.directory / "manual_actions.jsonl"
    before = path.read_bytes()
    with pytest.raises(ValueError, match="stale_revision"):
        invoke(batch_target, revision=revision)
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "entries",
    [
        [],
        [None],
        [{}] * 101,
        [{"expected_revision": "extra"}],
        [{"operation": "command"}],
    ],
)
def test_batch_shape_refused_without_history(batch_target, entries):
    with pytest.raises(
        ValueError, match="available|locator|reference|codec|losslessly|capacity|batch"
    ):
        invoke(batch_target, entries=entries)
    assert not (batch_target.directory / "manual_actions.jsonl").exists()


@pytest.mark.parametrize("invalid_last", [None, "parameters", "codec"])
def test_repeated_context_resolves_once_but_validates_each_parameters(
    batch_target, monkeypatch, invalid_last
):
    entries = [deepcopy(batch_target.entries[1]) for _ in range(3)]
    for index, entry in enumerate(entries):
        entry["parameters"]["text"] = f"Caller evidence interpretation {index}."
    if invalid_last:
        entries[-1]["parameters"]["text"] = (
            None if invalid_last == "parameters" else "line\nnext"
        )
    calls = {"context": 0, "catalog": 0, "append": 0}
    for label, name in (
        ("context", "_command_context_from_body"),
        ("catalog", "_command_catalog_payload"),
        ("append", "append_manual_actions"),
    ):
        original = getattr(server, name)

        def counted(*args, _original=original, _label=label, **kwargs):
            calls[_label] += 1
            return _original(*args, **kwargs)

        monkeypatch.setattr(server, name, counted)
    if invalid_last:
        journal = batch_target.directory / "decision_journal.jsonl"
        journal.write_bytes(b"preserve journal bytes\n")
        with pytest.raises(ValueError, match="text|codec|losslessly|capacity"):
            invoke(batch_target, entries=entries)
        assert not (batch_target.directory / "manual_actions.jsonl").exists()
        assert journal.read_bytes() == b"preserve journal bytes\n"
    else:
        result = invoke(batch_target, entries=entries)
        assert [action["comment"]["text"] for action in result["actions"]] == [
            entry["parameters"]["text"] for entry in entries
        ]
    assert calls == {
        "context": 1,
        "catalog": 1,
        "append": 0 if invalid_last == "parameters" else 1,
    }


def test_preparation_context_memo_is_not_reused_between_requests(
    batch_target, monkeypatch
):
    calls = []
    original = server._command_catalog_payload

    def counted(*args, **kwargs):
        calls.append(args)
        return original(*args, **kwargs)

    monkeypatch.setattr(server, "_command_catalog_payload", counted)
    invoke(batch_target, entries=[batch_target.entries[1]])
    invoke(batch_target, entries=[batch_target.entries[1]])
    assert len(calls) == 2


def test_distinct_contexts_share_navigation_only_during_preparation(
    batch_target, monkeypatch
):
    calls = []
    original_navigation = _RowsCListingArtifact.navigation_payload

    def navigation(artifact):
        calls.append(artifact)
        return original_navigation(artifact)

    monkeypatch.setattr(_RowsCListingArtifact, "navigation_payload", navigation)
    original_apply = server._apply_manual_action_commands

    def apply(*args, **kwargs):
        assert len(calls) == 1
        assert server._COMMAND_NAVIGATION_SNAPSHOTS.get() is None
        return original_apply(*args, **kwargs)

    monkeypatch.setattr(server, "_apply_manual_action_commands", apply)
    invoke(batch_target)
    # Application invalidated the listing; inspection gets a fresh snapshot.
    artifact = calls[0]
    artifact.app_slot_analysis = {"new_snapshot": True}
    row, _ = server._resolve_command_locator(
        "bloodwych", batch_target.entries[1]["context"]["locator"]
    )
    assert row["app_slot_analysis"] == {"new_snapshot": True}
    assert len(calls) == 2
    monkeypatch.setattr(server, "_apply_manual_action_commands", original_apply)
    invoke(batch_target, entries=[batch_target.entries[1]])
    assert len(calls) == 3


@pytest.mark.parametrize(
    ("key", "value"),
    [("row_key", "s0:00000002:instruction"),
     ("projection_hash", "obsolete-projection"), ("target_id", "other-target")],
)
def test_invalid_distinct_locator_does_not_bypass_validation_or_leak_snapshot(
    batch_target, monkeypatch, key, value
):
    calls = []
    original_navigation = _RowsCListingArtifact.navigation_payload

    def navigation(artifact):
        calls.append(artifact)
        return original_navigation(artifact)

    monkeypatch.setattr(_RowsCListingArtifact, "navigation_payload", navigation)
    entries = deepcopy(batch_target.entries)
    entries[-1]["context"]["locator"][key] = value
    if key == "projection_hash":
        # Existing stale-locator recovery accepts an unchanged source identity.
        # This stale identity has no match in the current projection.
        entries[-1]["context"]["locator"]["end_offset"] = 999
    journal = batch_target.directory / "decision_journal.jsonl"
    journal.write_bytes(b"preserve journal bytes\n")
    with pytest.raises(ValueError, match="locator"):
        invoke(batch_target, entries=entries)
    assert len(calls) == 1
    assert server._COMMAND_NAVIGATION_SNAPSHOTS.get() is None
    assert not (batch_target.directory / "manual_actions.jsonl").exists()
    assert journal.read_bytes() == b"preserve journal bytes\n"
    # The immutable navigation payload survives a rejected request, but the
    # separate lookup must still validate the current source identity.
    hashes = []
    original_key = server._project_listing_cache_key
    def fresh_key(name):
        hashes.append(name)
        return original_key(name)
    monkeypatch.setattr(server, "_project_listing_cache_key", fresh_key)
    server._resolve_command_locator(
        "bloodwych", batch_target.entries[1]["context"]["locator"]
    )
    assert hashes and set(hashes) == {"bloodwych"}
    assert len(calls) == 1
    assert server._COMMAND_NAVIGATION_SNAPSHOTS.get() is None


def test_navigation_exception_restores_request_scope(batch_target, monkeypatch):
    calls = []
    original_navigation = _RowsCListingArtifact.navigation_payload

    def navigation(artifact):
        calls.append(artifact)
        if len(calls) == 1:
            raise RuntimeError("synthetic navigation failure")
        return original_navigation(artifact)

    monkeypatch.setattr(_RowsCListingArtifact, "navigation_payload", navigation)
    with pytest.raises(RuntimeError, match="navigation failure"):
        invoke(batch_target)
    assert server._COMMAND_NAVIGATION_SNAPSHOTS.get() is None
    assert not (batch_target.directory / "manual_actions.jsonl").exists()
    invoke(batch_target)
    assert len(calls) == 2
