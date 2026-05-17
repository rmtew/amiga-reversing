from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import cast

import pytest

from amiga_reversing.disasm import project_paths, projects
from amiga_reversing.disasm import server as disasm_server
from amiga_reversing.disasm.binary_source import write_source_descriptor
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
from tests.listing_row_fixtures import serialize_row
from tests.listing_types_fixtures import ListingRow
from tests.workflow_harness import (
    ManualWorkflowExpectation,
    PreferenceWorkflowExpectation,
    assert_manual_workflow_snapshot,
    assert_preference_workflow_snapshot,
)


class _RowsArtifact:
    def __init__(self, rows: list[ListingRow]) -> None:
        self.rows = rows
        self.closed = False

    def close(self) -> None:
        self.closed = True

    def window_payload(self, *, start: int, count: int) -> tuple[dict[str, object], dict[str, object]]:
        safe_start = max(0, min(start, len(self.rows)))
        safe_end = min(len(self.rows), safe_start + max(0, count))
        return (
            {
                "anchor_addr": self.rows[safe_start].addr if safe_start < len(self.rows) else None,
                "start": safe_start,
                "end": safe_end,
                "has_more_before": safe_start > 0,
                "has_more_after": safe_end < len(self.rows),
                "total_rows": len(self.rows),
                "rows": [dict(serialize_row(row)) for row in self.rows[safe_start:safe_end]],
            },
            {},
        )

    def summary_payload(self) -> tuple[dict[str, object], dict[str, object]]:
        return {"total_rows": len(self.rows)}, {}


@pytest.fixture(autouse=True)
def _reset_listing_projection_service() -> Iterator[None]:
    disasm_server._LISTING_PROJECTION_SERVICE.reset()
    yield
    disasm_server._LISTING_PROJECTION_SERVICE.reset()


def test_api_harness_proves_manual_workflow_reload_projection_and_stale_locator(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project_id = "workflow_demo"
    _install_durable_project(monkeypatch, tmp_path, project_id)
    rows = [
        ListingRow(
            row_id="r0",
            stable_key="row-0",
            kind="instruction",
            text="rts\n",
            addr=4,
            section_index=0,
            start_offset=4,
            end_offset=6,
            opcode_or_directive="rts",
        )
    ]
    _seed_listing(project_id, rows)
    listing = cast(dict[str, object], disasm_server.route_request(
        "GET",
        f"/api/projects/{project_id}/listing",
        {"start": ["0"], "count": ["20"]},
    )["data"])
    locator = cast(dict[str, object], cast(dict[str, object], cast(list[object], listing["rows"])[0])["locator"])
    stale_locator = {**locator, "projection_hash": "old-cache"}

    stale_result = cast(dict[str, object], disasm_server.route_request(
        "POST",
        f"/api/projects/{project_id}/commands/execute",
        {},
        {
            "command_id": "review_note.add",
            "context": {"kind": "row", "locator": stale_locator},
            "parameters": {"title": "Check RTS", "body": "Verify return path", "tracking": "needs_review"},
        },
    )["data"])
    comment_result = cast(dict[str, object], disasm_server.route_request(
        "POST",
        f"/api/projects/{project_id}/commands/execute",
        {},
        {
            "command_id": "comment.edit",
            "context": {"kind": "row", "locator": locator},
            "parameters": {"text": "manual return"},
        },
    )["data"])

    reloaded_project = cast(dict[str, object], disasm_server.route_request("GET", f"/api/projects/{project_id}", {})["data"])
    projected_listing = cast(dict[str, object], disasm_server.route_request(
        "GET",
        f"/api/projects/{project_id}/listing",
        {"start": ["0"], "count": ["20"]},
    )["data"])
    mutation = cast(dict[str, object], comment_result["mutation"])
    assert_manual_workflow_snapshot(
        {
            "mutation": mutation,
            "project": reloaded_project,
            "listing": projected_listing,
            "server_debug_state": disasm_server._LISTING_PROJECTION_SERVICE.debug_state(),
            "browser_debug_state": {
                "project_id": project_id,
                "selected_row_key": "row-0",
                "listing_projection_hash": "cache",
            },
            "locator_recovery": {
                "ok": True,
                "row_key": "row-0",
                "projection_hash": cast(dict[str, object], stale_result["mutation"])["projection_hash"],
            },
        },
        ManualWorkflowExpectation(
            project_id=project_id,
            manual_action_log_count=2,
            durable_action_id=cast(str, mutation["durable_action_id"]),
            row_key="row-0",
            projection_hash="cache",
            comment_text="manual return",
            review_title="Check RTS",
            review_state="needs_review",
            presentation_dirty=True,
            locator_recovered=True,
        ),
    )


def test_api_harness_proves_preference_workflow_reload(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    project_id = "workflow_prefs"
    _install_durable_project(monkeypatch, tmp_path, project_id)
    saved = cast(dict[str, object], disasm_server.route_request(
        "PUT",
        f"/api/projects/{project_id}/ui-preferences",
        {},
        {
            "source_export_assembler": "vasm",
            "listing_location": {"stable_key": "row-0", "row_index": 0, "scroll_top": 12},
        },
    )["data"])
    reloaded = cast(dict[str, object], disasm_server.route_request(
        "GET",
        f"/api/projects/{project_id}/ui-preferences",
        {},
    )["data"])

    assert saved["preferences"] == reloaded["preferences"]
    assert_preference_workflow_snapshot(
        {
            "preferences": reloaded,
            "browser_debug_state": {
                "project_id": project_id,
                "listing_stable_key": "row-0",
            },
        },
        PreferenceWorkflowExpectation(
            project_id=project_id,
            source_export_assembler="vasm",
            listing_stable_key="row-0",
        ),
    )


def test_workflow_assertions_accept_debug_state_shape() -> None:
    snapshot: dict[str, object] = {
        "mutation": {
            "durable_action_id": "a1",
            "manual_action_log_count": 1,
            "manual_action_log_head_hash": "1" * 64,
            "effective_metadata_hash": "2" * 64,
            "projection_hash": "cache",
            "affected_locators": [{"row_key": "row-0"}],
        },
        "project": {
            "project": {
                "review_state": "needs_review",
                "manual_state": {
                    "comments": [{"text": "manual return"}],
                    "review_notes": [{"title": "Check RTS"}],
                },
            }
        },
        "listing": {
            "rows": [{"row_key": "row-0", "comment_text": "manual return", "view_annotations": ["REVIEW: Check RTS"]}]
        },
        "server_debug_state": {
            "artifact_projects": ["debug_demo"],
            "cache_keys": {"debug_demo": "cache"},
            "presentation_dirty_projects": ["debug_demo"],
        },
        "browser_debug_state": {
            "project_id": "debug_demo",
            "selected_row_key": "row-0",
            "listing_projection_hash": "cache",
        },
        "locator_recovery": {"ok": True, "row_key": "row-0", "projection_hash": "cache"},
    }

    assert_manual_workflow_snapshot(
        snapshot,
        ManualWorkflowExpectation(
            project_id="debug_demo",
            manual_action_log_count=1,
            durable_action_id="a1",
            row_key="row-0",
            projection_hash="cache",
            comment_text="manual return",
            review_title="Check RTS",
            review_state="needs_review",
            presentation_dirty=True,
            locator_recovered=True,
        ),
    )
    cast(dict[str, object], cast(list[object], cast(dict[str, object], snapshot["listing"])["rows"])[0])["comment_text"] = "wrong"
    with pytest.raises(AssertionError, match="projection:"):
        assert_manual_workflow_snapshot(
            snapshot,
            ManualWorkflowExpectation(
                project_id="debug_demo",
                manual_action_log_count=1,
                row_key="row-0",
                projection_hash="cache",
                comment_text="manual return",
            ),
        )


def _install_durable_project(
    monkeypatch: pytest.MonkeyPatch,
    project_root: Path,
    project_id: str,
) -> Path:
    root = project_root
    target_dir = project_root / "targets" / project_id
    target_dir.mkdir(parents=True)
    binary_path = project_root / "bin" / f"{project_id}.bin"
    binary_path.parent.mkdir()
    binary_path.write_bytes(b"\x4e\x75\x4e\x75")
    projects.initialize_project_metadata(target_dir, origin={"kind": "api_workflow_test"})
    write_source_descriptor(
        target_dir,
        {
            "kind": "raw_binary",
            "path": str(binary_path),
            "address_model": "local_offset",
            "load_address": 0,
            "entrypoint": 0,
            "code_start_offset": 0,
        },
    )
    write_target_metadata(target_dir, TargetMetadata(target_type="program", entry_register_seeds=()))
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda name: projects.get_project(name, project_root=root),
    )
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda name, project_root=None: project_paths.resolve_project_paths(name, project_root=root),
    )
    monkeypatch.setattr(
        disasm_server,
        "_project_listing_cache_key",
        lambda name: "cache",
    )
    return target_dir


def _seed_listing(project_id: str, rows: list[ListingRow]) -> None:
    disasm_server._LISTING_PROJECTION_SERVICE.reset()
    disasm_server._LISTING_PROJECTION_SERVICE.seed_artifact_for_test(
        project_id,
        _RowsArtifact(rows),
        cache_key="cache",
    )
