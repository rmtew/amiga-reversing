from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from amiga_reversing import reversing_loop
from amiga_reversing.disasm import project_paths, projects
from amiga_reversing.disasm import server as disasm_server
from amiga_reversing.disasm.binary_source import write_source_descriptor
from amiga_reversing.disasm.manual_actions import (
    ReviewItemKind,
    ReviewItemScope,
    ReviewItemState,
)
from amiga_reversing.disasm.projects import ProjectKind, ProjectRecord
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
from tests.listing_row_fixtures import serialize_row
from tests.listing_types_fixtures import ListingRow


@pytest.fixture(autouse=True)
def _reset_listing_projection_service() -> Iterator[None]:
    disasm_server._LISTING_PROJECTION_SERVICE.reset()
    disasm_server._ASYNC_JOBS.clear()
    yield
    disasm_server._LISTING_PROJECTION_SERVICE.reset()
    disasm_server._ASYNC_JOBS.clear()


def test_agent_reversing_loop_smoke(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    (target_dir / "source_binary.json").write_text("{}", encoding="utf-8")
    locator = {
        "target_id": "demo",
        "projection_hash": "projection-1",
        "row_key": "row-1",
        "section_index": 0,
        "start_offset": 0,
        "end_offset": 2,
        "kind": "instruction",
    }
    item = {
        "kind": ReviewItemKind.REVIEW_NOTE,
        "scope": ReviewItemScope.RANGE,
        "state": ReviewItemState.OPEN,
        "item_id": "review-note:h0:$00000000-$00000002",
        "locator": locator,
        "ref_count": 1,
        "message": "candidate with xrefs",
        "suggested_actions": [{"action": "comment.edit"}],
    }
    monkeypatch.setattr(reversing_loop.projects, "get_project", lambda target_id, project_root: _project((item,)))
    calls: list[tuple[str, str]] = []

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        calls.append((method, path))
        if method == "GET":
            assert query["context"] == ["row"]
            return {"data": {"commands": [{"command_id": "comment.edit"}]}}
        assert isinstance(body, dict)
        assert body["context"]["locator"]["row_key"] == "row-1"
        _write_manual_log(target_dir)
        return {
            "data": {
                "action": {"action_id": "manual-1"},
                "mutation": {
                    "durable_action_id": "manual-1",
                    "manual_action_log_count": 1,
                    "affected_locators": [locator],
                },
                "workflow_profile": {
                    "workflow_id": "manual_command_execution",
                    "spans": [{"name": "manual_action_append", "seconds": 0.01, "module": "manual_action_log"}],
                },
            }
        }

    monkeypatch.setattr(reversing_loop.server, "route_request", route_request)

    hygiene = reversing_loop.inspect_target_hygiene("demo", project_root=tmp_path)
    read_only = reversing_loop.inspect_target("demo", project_root=tmp_path)
    dry_run = reversing_loop.run_one_iteration("demo", mode="clean-run", dry_run=True, project_root=tmp_path)
    report = reversing_loop.run_one_iteration("demo", mode="continue", project_root=tmp_path)

    assert hygiene.safe_to_continue is True
    assert read_only["candidate_work"][0]["locator"]["row_key"] == "row-1"
    assert dry_run["action_result"]["status"] == "dry_run"
    assert report["verification"]["status"] == "passed"
    assert report["workflow_profile"]["workflow_id"] == "manual_command_execution"
    assert report["next"]["recommendation"] == "continue"
    assert calls == [
        ("GET", "/api/projects/demo/commands"),
        ("POST", "/api/projects/demo/commands/execute"),
    ]
    latest_path = target_dir / "agent" / "latest-reversing-loop.json"
    assert latest_path.exists()


def test_agent_listing_backed_comment_smoke_uses_harness_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_id = "listing_demo"
    target_dir = _install_durable_listing_project(monkeypatch, tmp_path, project_id)
    rows = [
        ListingRow(
            row_id="r0",
            stable_key="row-0",
            kind="instruction",
            text="rts\n",
            addr=0,
            section_index=0,
            start_offset=0,
            end_offset=2,
            opcode_or_directive="rts",
        )
    ]
    artifact = _RowsArtifact(rows)
    monkeypatch.setattr(
        disasm_server,
        "build_project_listing_artifact_profile",
        lambda project_name: (len(rows), {}, artifact),
    )
    monkeypatch.setattr(
        disasm_server,
        "_start_listing_worker",
        lambda job_id, project_name: disasm_server._build_rows_job(job_id, project_name),
    )

    report = reversing_loop.run_listing_backed_comment_iteration(
        project_id,
        mode="clean-run",
        comment_text="LLM smoke comment",
        project_root=tmp_path,
    )

    assert report["selected_work_item"]["locator"]["row_key"] == "row-0"
    assert report["action"]["command_id"] == "comment.edit"
    assert report["durable_result"]["mutation"]["manual_action_log_count"] == 1
    assert report["verification"]["status"] == "passed"
    assert report["workflow_profile"]["workflow_id"] == "manual_command_execution"
    projection = next(layer for layer in report["verification"]["layers"] if layer["layer"] == "projection")
    assert projection["actual_comment_text"] == "LLM smoke comment"
    assert report["next"]["recommendation"] == "continue"
    assert (target_dir / "agent" / "latest-reversing-loop.json").exists()


def _project(review_items: tuple[dict[str, object], ...]) -> ProjectRecord:
    return ProjectRecord(
        id="demo",
        name="demo",
        kind=ProjectKind.BINARY,
        target_dir="targets/demo",
        output_path=None,
        binary_path="bin/demo.bin",
        ready=True,
        last_opened=None,
        manifest_path=None,
        target_count=None,
        source_path=None,
        disk_type=None,
        parent_project_id=None,
        target_type="program",
        created_at="2026-05-18T00:00:00+00:00",
        updated_at="2026-05-18T00:00:00+00:00",
        manual_action_log_path="targets/demo/manual_actions.jsonl",
        review_state=None,
        review_items=review_items,
        manual_state={"review_state": "needs_review"},
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


def _install_durable_listing_project(
    monkeypatch: pytest.MonkeyPatch,
    project_root: Path,
    project_id: str,
) -> Path:
    target_dir = project_root / "targets" / project_id
    target_dir.mkdir(parents=True)
    binary_path = project_root / "bin" / f"{project_id}.bin"
    binary_path.parent.mkdir()
    binary_path.write_bytes(b"\x4e\x75\x4e\x75")
    projects.initialize_project_metadata(target_dir, origin={"kind": "agent_listing_smoke_test"})
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
        lambda name: projects.get_project(name, project_root=project_root),
    )
    monkeypatch.setattr(
        disasm_server,
        "resolve_project_paths",
        lambda name, project_root=None, root=project_root: project_paths.resolve_project_paths(name, project_root=root),
    )
    monkeypatch.setattr(disasm_server, "_project_listing_cache_key", lambda name: "cache")
    return target_dir


def _write_manual_log(target_dir: Path) -> None:
    (target_dir / "manual_actions.jsonl").write_text(
        '{"record": "manual_action_log_header"}\n{"record": "manual_action", "action_id": "manual-1"}\n',
        encoding="utf-8",
    )
