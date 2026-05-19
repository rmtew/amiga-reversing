from __future__ import annotations

import shutil
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest

from amiga_reversing import reversing_loop
from amiga_reversing.disasm import c_backend, project_paths, projects
from amiga_reversing.disasm import server as disasm_server
from amiga_reversing.disasm.binary_source import write_source_descriptor
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.manual_actions import (
    ReviewItemKind,
    ReviewItemScope,
    ReviewItemState,
)
from amiga_reversing.disasm.projects import ProjectKind, ProjectRecord
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
from tests.listing_row_fixtures import serialize_row
from tests.listing_types_fixtures import ListingRow

PROJECT_ROOT = Path(__file__).resolve().parents[1]


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
        "suggested_comment_text": "xref-backed smoke comment",
    }
    monkeypatch.setattr(reversing_loop.projects, "get_project", lambda target_id, project_root: _project((item,)))
    calls: list[tuple[str, str]] = []

    def route_request(method: str, path: str, query: dict[str, list[str]], body: object = None) -> dict[str, object]:
        calls.append((method, path))
        if method == "GET" and path == "/api/projects/demo":
            return {"data": {"project": {"manual_state": {}}}}
        if method == "GET" and path.endswith("/listing"):
            return {"data": {"rows": [{**locator, "row_key": "row-1", "comment_text": "xref-backed smoke comment"}]}}
        if method == "GET" and path.endswith("/commands"):
            assert query["context"] == ["row"]
            return {"data": {"commands": [{"command_id": "comment.edit"}]}}
        assert isinstance(body, dict)
        assert body["context"]["locator"]["row_key"] == "row-1"
        _write_manual_log(target_dir)
        log_state = reversing_loop._manual_action_log_state(target_dir)
        return {
            "data": {
                "action": {"action_id": "manual-1"},
                "mutation": {
                    "durable_action_id": "manual-1",
                    "manual_action_log_count": log_state["count"],
                    "manual_action_log_head_hash": log_state["head_hash"],
                    "effective_metadata_hash": "f" * 64,
                    "affected_locators": [locator],
                    "projection_hash": "projection-1",
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
    assert read_only["candidate_work"][0]["confidence"] == "high"
    assert read_only["candidate_work"][0]["default_verifier"] == "projection_metadata"
    assert dry_run["action_result"]["status"] == "dry_run"
    assert report["verification"]["status"] == "passed"
    assert report["workflow_profile"]["workflow_id"] == "manual_command_execution"
    assert report["next"]["recommendation"] == "continue"
    assert calls == [
        ("GET", "/api/projects/demo/commands"),
        ("POST", "/api/projects/demo/commands/execute"),
        ("GET", "/api/projects/demo"),
        ("GET", "/api/projects/demo/listing"),
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

    assert report["selected_work_item"]["kind"] == "source_entrypoint_row"
    assert report["selected_work_item"]["locator"]["row_key"] == "row-0"
    assert report["selected_work_item"]["confidence"] == "high"
    assert report["selected_work_item"]["rationale"] == "source descriptor entrypoint maps to this listing row"
    assert report["action"]["command_id"] == "comment.edit"
    assert report["durable_result"]["mutation"]["manual_action_log_count"] == 1
    assert report["verification"]["status"] == "passed"
    assert report["workflow_profile"]["workflow_id"] == "manual_command_execution"
    projection = next(layer for layer in report["verification"]["layers"] if layer["layer"] == "projection")
    assert projection["actual_comment_text"] == "LLM smoke comment"
    assert report["next"]["recommendation"] == "continue"
    assert (target_dir / "agent" / "latest-reversing-loop.json").exists()


def test_agent_real_genam_autonomous_rsset_candidate_converges_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _skip_without_c_backend()
    project_id = "amiga_hunk_genam"
    project_root = tmp_path / "project_root"
    shutil.copytree(PROJECT_ROOT / "targets" / project_id, project_root / "targets" / project_id)
    (project_root / "bin").mkdir(parents=True)
    shutil.copy2(PROJECT_ROOT / "bin" / "GenAm", project_root / "bin" / "GenAm")

    original_get_project = projects.get_project

    def get_temp_project(name: str, project_root: Path | None = None, root: Path = project_root) -> ProjectRecord:
        project = original_get_project(name, project_root=root)
        return replace(project, review_items=())

    def resolve_temp_paths(name: str, project_root: Path | None = None, root: Path = project_root) -> project_paths.ProjectPaths:
        return project_paths.resolve_project_paths(name, project_root=root)

    monkeypatch.setattr(reversing_loop.projects, "get_project", get_temp_project)
    monkeypatch.setattr(disasm_server, "get_project", lambda name: get_temp_project(name))
    monkeypatch.setattr(disasm_server, "resolve_project_paths", resolve_temp_paths)
    monkeypatch.setattr(c_backend, "resolve_project_paths", resolve_temp_paths)
    monkeypatch.setattr(reversing_loop, "_listing_entrypoint_label_candidates", lambda *args, **kwargs: [])
    monkeypatch.setattr(reversing_loop, "_listing_data_symbol_candidates", lambda *args, **kwargs: [])
    monkeypatch.setattr(reversing_loop, "_listing_data_role_candidates", lambda *args, **kwargs: [])

    report = reversing_loop.run_one_iteration(project_id, mode="clean-run", project_root=project_root)

    assert report["selected_work_item"]["kind"] == "rsset_layout_region"
    assert report["selected_work_item"]["evidence"]["navigation_group"] == "app-slot-suggestions"
    assert report["action"]["command_id"] == "target.rsset_region.add"
    assert report["verification"]["status"] == "passed"
    expected_region = cast(dict[str, object], report["selected_work_item"]["parameters"])
    semantic_reload = next(layer for layer in report["verification"]["layers"] if layer["layer"] == "semantic_reload")
    matching_regions = cast(list[dict[str, object]], semantic_reload["matching_rsset_layout_regions"])
    assert matching_regions[0]["symbol"] == expected_region["symbol"]
    assert matching_regions[0]["offset"] == expected_region["offset"]

    paths = resolve_temp_paths(project_id)
    with effective_metadata_file(paths.target_dir) as metadata_path:
        rendered, _profile = c_backend.listing_artifact_source_text_with_c_backend_profile(
            paths.binary_source,
            metadata_path=metadata_path,
            project_root=PROJECT_ROOT,
    )
    assert expected_region["symbol"] in rendered
    assert f"{expected_region['symbol']} RS." in rendered


def test_agent_real_genam_autonomous_lvo_library_base_candidate_converges(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _skip_without_c_backend()
    project_id = "amiga_hunk_genam"
    project_root = tmp_path / "project_root"
    shutil.copytree(PROJECT_ROOT / "targets" / project_id, project_root / "targets" / project_id)
    (project_root / "bin").mkdir(parents=True)
    shutil.copy2(PROJECT_ROOT / "bin" / "GenAm", project_root / "bin" / "GenAm")

    original_get_project = projects.get_project

    def get_temp_project(name: str, project_root: Path | None = None, root: Path = project_root) -> ProjectRecord:
        project = original_get_project(name, project_root=root)
        return replace(project, review_items=())

    def resolve_temp_paths(name: str, project_root: Path | None = None, root: Path = project_root) -> project_paths.ProjectPaths:
        return project_paths.resolve_project_paths(name, project_root=root)

    monkeypatch.setattr(reversing_loop.projects, "get_project", get_temp_project)
    monkeypatch.setattr(disasm_server, "get_project", lambda name: get_temp_project(name))
    monkeypatch.setattr(disasm_server, "resolve_project_paths", resolve_temp_paths)
    monkeypatch.setattr(c_backend, "resolve_project_paths", resolve_temp_paths)
    monkeypatch.setattr(reversing_loop, "_listing_entrypoint_label_candidates", lambda *args, **kwargs: [])
    monkeypatch.setattr(reversing_loop, "_listing_representation_candidates", lambda *args, **kwargs: [])
    monkeypatch.setattr(reversing_loop, "_listing_data_symbol_candidates", lambda *args, **kwargs: [])
    monkeypatch.setattr(reversing_loop, "_listing_data_role_candidates", lambda *args, **kwargs: [])
    monkeypatch.setattr(reversing_loop, "_listing_struct_pointer_candidates", lambda *args, **kwargs: [])
    monkeypatch.setattr(reversing_loop, "_listing_rsset_region_candidates", lambda *args, **kwargs: [])

    report = reversing_loop.run_one_iteration(project_id, mode="clean-run", project_root=project_root)

    assert report["selected_work_item"]["kind"] == "api_register_semantic"
    assert report["selected_work_item"]["base_register"] == "A6"
    assert report["selected_work_item"]["api_library"] == "exec.library"
    assert report["action"]["command_id"] == "semantic.library_base.exec.library"
    assert report["verification"]["status"] == "passed"
    semantic_reload = next(layer for layer in report["verification"]["layers"] if layer["layer"] == "semantic_reload")
    assert semantic_reload["expected_register"] == "A6"
    assert semantic_reload["expected_library_name"] == "exec.library"
    matching_seeds = cast(list[dict[str, object]], semantic_reload["matching_register_seeds"])
    assert matching_seeds[0]["kind"] == "library_base"
    assert matching_seeds[0]["library_name"] == "exec.library"


def test_agent_real_genam_autonomous_data_symbol_candidate_converges(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _skip_without_c_backend()
    project_id = "amiga_hunk_genam"
    project_root = tmp_path / "project_root"
    shutil.copytree(PROJECT_ROOT / "targets" / project_id, project_root / "targets" / project_id)
    (project_root / "bin").mkdir(parents=True)
    shutil.copy2(PROJECT_ROOT / "bin" / "GenAm", project_root / "bin" / "GenAm")

    original_get_project = projects.get_project

    def get_temp_project(name: str, project_root: Path | None = None, root: Path = project_root) -> ProjectRecord:
        project = original_get_project(name, project_root=root)
        return replace(project, review_items=())

    def resolve_temp_paths(name: str, project_root: Path | None = None, root: Path = project_root) -> project_paths.ProjectPaths:
        return project_paths.resolve_project_paths(name, project_root=root)

    monkeypatch.setattr(reversing_loop.projects, "get_project", get_temp_project)
    monkeypatch.setattr(disasm_server, "get_project", lambda name: get_temp_project(name))
    monkeypatch.setattr(disasm_server, "resolve_project_paths", resolve_temp_paths)
    monkeypatch.setattr(c_backend, "resolve_project_paths", resolve_temp_paths)
    monkeypatch.setattr(reversing_loop, "_listing_entrypoint_label_candidates", lambda *args, **kwargs: [])
    monkeypatch.setattr(reversing_loop, "_listing_representation_candidates", lambda *args, **kwargs: [])
    monkeypatch.setattr(reversing_loop, "_listing_data_role_candidates", lambda *args, **kwargs: [])
    monkeypatch.setattr(reversing_loop, "_listing_struct_pointer_candidates", lambda *args, **kwargs: [])
    monkeypatch.setattr(reversing_loop, "_listing_library_base_candidates", lambda *args, **kwargs: [])
    monkeypatch.setattr(reversing_loop, "_listing_rsset_region_candidates", lambda *args, **kwargs: [])

    report = reversing_loop.run_one_iteration(project_id, mode="clean-run", project_root=project_root)

    assert report["selected_work_item"]["kind"] == "data_symbol_name"
    assert report["action"]["command_id"] in {"data_symbol.rename", "data_symbol.rename_existing"}
    assert report["verification"]["status"] == "passed"
    expected_name = report["selected_work_item"]["new_name"]
    projection = next(layer for layer in report["verification"]["layers"] if layer["layer"] == "projection")
    assert projection["expected_data_symbol_name"] == expected_name


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


def _skip_without_c_backend() -> None:
    build_dir = PROJECT_ROOT / "src" / "build"
    if not (build_dir / "platform_file_lib.dll").exists() or not (build_dir / "platform_disk_lib.dll").exists():
        pytest.skip("C backend DLLs are missing; run cmd /c src\\build.bat")
