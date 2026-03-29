from __future__ import annotations

import json
from pathlib import Path
from typing import cast
from unittest.mock import Mock

import pytest

from disasm import server as disasm_server
from disasm.projects import ProjectRecord
from disasm.types import BlockRowContext, ListingRow


def _binary_project(project_name: str, *, ready: bool) -> ProjectRecord:
    return ProjectRecord(
        id=project_name,
        name=project_name,
        kind="binary",
        target_dir=f"targets/{project_name}",
        entities_path=f"targets/{project_name}/entities.jsonl",
        output_path=None,
        binary_path="bin/BLOODWYCH" if ready else None,
        ready=ready,
        last_opened=None,
        manifest_path=None,
        target_count=None,
        source_path=None,
        disk_type=None,
        parent_project_id=None,
        target_type="program",
        created_at="2026-03-25T00:00:00+00:00",
        updated_at="2026-03-25T01:00:00+00:00",
    )


def _disk_manifest_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "disk_id": "demo_disk",
        "source_path": "bin/demo.adf",
        "source_sha256": "deadbeef",
        "bootblock_target_name": "amiga_disk_demo_disk__amiga_raw_bootblock",
        "bootblock_target_path": "targets/amiga_disk_demo_disk/targets/amiga_raw_bootblock",
        "analysis": {
            "disk_info": {
                "path": "demo.adf",
                "size": 901120,
                "variant": "DD",
                "total_sectors": 1760,
                "sectors_per_track": 11,
                "is_dos": True,
            },
            "boot_block": {
                "magic_ascii": "DOS",
                "is_dos": True,
                "flags_byte": 1,
                "fs_type": "FFS",
                "fs_description": "DOS\\1 - Fast File System",
                "checksum": "0x00000000",
                "checksum_valid": True,
                "rootblock_ptr": 880,
                "bootcode_size": 1012,
                "bootcode_has_code": False,
                "bootcode_entropy": 0.0,
            },
        },
        "imported_targets": [
            {
                "target_name": "amiga_disk_demo_disk__amiga_hunk_run_12345678",
                "target_path": "targets/amiga_disk_demo_disk/targets/amiga_hunk_run_12345678",
                "entry_path": "c/Run",
                "binary_path": "bin/demo.adf::c/Run",
                "target_type": "program",
            }
        ],
    }


def test_route_projects_returns_project_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(disasm_server, "list_projects", lambda: [_binary_project("bloodwych", ready=True)])

    payload = disasm_server.route_request("GET", "/api/projects", {})

    assert payload["ok"] is True
    assert payload["data"] == [_binary_project("bloodwych", ready=True).to_dict()]


def test_route_create_project(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "create_project",
        lambda project_id: _binary_project(project_id, ready=False),
    )

    payload = disasm_server.route_request("POST", "/api/projects", {}, {"id": "demo"})
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["id"] == "demo"


def test_route_project_returns_project_and_session(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request("GET", "/api/projects/bloodwych", {})
    data = cast(dict[str, object], payload["data"])
    project = cast(dict[str, object], data["project"])

    assert payload["ok"] is True
    assert project["name"] == "bloodwych"
    assert "session" not in data
    assert "disk_manifest" not in data


def test_route_project_returns_disk_manifest_for_disk_project(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_disk_manifest_payload()))

    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: ProjectRecord(
            id=project_name,
            name="demo_disk",
            kind="disk",
            target_dir=str(tmp_path),
            entities_path=None,
            output_path=None,
            binary_path=None,
            ready=False,
            last_opened=None,
            manifest_path=str(manifest_path),
            target_count=0,
            source_path="bin/demo.adf",
            disk_type="DOS",
            parent_project_id=None,
            target_type=None,
            created_at="2026-03-25T00:00:00+00:00",
            updated_at="2026-03-25T01:00:00+00:00",
        ),
    )

    payload = disasm_server.route_request("GET", "/api/projects/amiga_disk_demo_disk", {})

    data = cast(dict[str, object], payload["data"])
    project = cast(dict[str, object], data["project"])
    disk_manifest = cast(dict[str, object], data["disk_manifest"])

    assert payload["ok"] is True
    assert project["kind"] == "disk"
    assert disk_manifest["disk_id"] == "demo_disk"


def test_route_listing_rejects_disk_project(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_disk_manifest_payload()))
    disk_project = ProjectRecord(
        id="amiga_disk_demo_disk",
        name="demo_disk",
        kind="disk",
        target_dir=str(tmp_path),
        entities_path=None,
        output_path=None,
        binary_path=None,
        ready=False,
        last_opened=None,
        manifest_path=str(manifest_path),
        target_count=0,
        source_path="bin/demo.adf",
        disk_type="DOS",
        parent_project_id=None,
        target_type=None,
        created_at="2026-03-25T00:00:00+00:00",
        updated_at="2026-03-25T01:00:00+00:00",
    )
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: disk_project)

    with pytest.raises(ValueError, match="does not expose a disassembly listing"):
        disasm_server.route_request("GET", "/api/projects/amiga_disk_demo_disk/listing", {})


def test_route_listing_open_rejects_disk_project(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_disk_manifest_payload()))
    disk_project = ProjectRecord(
        id="amiga_disk_demo_disk",
        name="demo_disk",
        kind="disk",
        target_dir=str(tmp_path),
        entities_path=None,
        output_path=None,
        binary_path=None,
        ready=False,
        last_opened=None,
        manifest_path=str(manifest_path),
        target_count=0,
        source_path="bin/demo.adf",
        disk_type="DOS",
        parent_project_id=None,
        target_type=None,
        created_at="2026-03-25T00:00:00+00:00",
        updated_at="2026-03-25T01:00:00+00:00",
    )
    monkeypatch.setattr(disasm_server, "get_project", lambda project_name: disk_project)

    with pytest.raises(ValueError, match="does not expose a disassembly listing"):
        disasm_server.route_request("POST", "/api/projects/amiga_disk_demo_disk/listing/open", {}, {})


def test_route_create_project_from_adf_media(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "_start_project_create_job",
        lambda body: {"job_id": "job-adf", "job_kind": "project_create", "status": "queued"},
    )

    payload = disasm_server.route_request(
        "POST",
        "/api/projects",
        {},
        {"filename": "demo.adf", "media_base64": "ZGVtbw=="},
    )
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["job_id"] == "job-adf"
    assert data["job_kind"] == "project_create"


def test_route_create_project_from_executable_media(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "_start_project_create_job",
        lambda body: {"job_id": "job-exe", "job_kind": "project_create", "status": "queued"},
    )

    payload = disasm_server.route_request(
        "POST",
        "/api/projects",
        {},
        {"filename": "bloodwych", "media_base64": "ZGVtbw=="},
    )
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["job_id"] == "job-exe"
    assert data["job_kind"] == "project_create"


def test_route_project_create_status_returns_job(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "_job_payload",
        lambda job_id: {"job_id": job_id, "status": "building", "phase_id": "analyze_disk"},
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/create/status",
        {"job_id": ["job-1"]},
    )
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["phase_id"] == "analyze_disk"


def test_route_delete_project(monkeypatch: pytest.MonkeyPatch) -> None:
    deleted: list[str] = []
    monkeypatch.setattr(disasm_server, "delete_project", lambda project_id: deleted.append(project_id))

    payload = disasm_server.route_request("POST", "/api/projects/demo/delete", {})

    assert payload["ok"] is True
    assert deleted == ["demo"]


def test_create_project_from_media_creates_executable_project(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target_dir = tmp_path / "targets" / "amiga_hunk_bloodwych"

    def fake_create_project(project_id: str, project_root: Path) -> ProjectRecord:
        assert project_root == tmp_path
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "entities.jsonl").write_text("")
        (target_dir / ".project.json").write_text(json.dumps({
            "schema_version": 1,
            "created_at": "2026-03-25T00:00:00+00:00",
            "updated_at": "2026-03-25T00:00:00+00:00",
        }))
        return ProjectRecord(
            id=project_id,
            name=project_id,
            kind="binary",
            target_dir=str(target_dir),
            entities_path=str(target_dir / "entities.jsonl"),
            output_path=None,
            binary_path=None,
            ready=False,
            last_opened=None,
            manifest_path=None,
            target_count=None,
            source_path=None,
            disk_type=None,
            parent_project_id=None,
            target_type="program",
            created_at="2026-03-25T00:00:00+00:00",
            updated_at="2026-03-25T00:00:00+00:00",
        )

    monkeypatch.setattr(disasm_server, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        disasm_server,
        "parse",
        Mock(return_value=type("ParsedExecutable", (), {"is_executable": True})()),
    )
    monkeypatch.setattr(disasm_server, "create_project", fake_create_project)
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name, project_root: _binary_project(project_name, ready=True),
    )

    project = disasm_server._create_project_from_media({
        "filename": "Bloodwych",
        "media_base64": "ZGVtbw==",
    })

    assert project.id == "amiga_hunk_bloodwych"
    assert (tmp_path / "bin" / "uploads" / "Bloodwych").read_bytes() == b"demo"
    payload = json.loads((target_dir / "source_binary.json").read_text())
    assert payload == {
        "kind": "hunk_file",
        "path": "bin/uploads/Bloodwych",
    }


def test_create_project_from_media_creates_disk_project(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(disasm_server, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        disasm_server,
        "create_disk_project",
        lambda media_path, *, disk_id, project_root, progress_fn=None: type("Manifest", (), {"disk_id": disk_id})(),
    )
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name, project_root: ProjectRecord(
            id=project_name,
            name="bloodwych",
            kind="disk",
            target_dir="targets/amiga_disk_bloodwych",
            entities_path=None,
            output_path=None,
            binary_path=None,
            ready=False,
            last_opened=None,
            manifest_path="targets/amiga_disk_bloodwych/manifest.json",
            target_count=0,
            source_path="bin/uploads/Bloodwych.adf",
            disk_type="DOS",
            parent_project_id=None,
            target_type=None,
            created_at="2026-03-25T00:00:00+00:00",
            updated_at="2026-03-25T01:00:00+00:00",
        ),
    )

    project = disasm_server._create_project_from_media({
        "filename": "Bloodwych.adf",
        "media_base64": "ZGVtbw==",
    })

    assert project.id == "amiga_disk_bloodwych"
    assert (tmp_path / "bin" / "uploads" / "Bloodwych.adf").read_bytes() == b"demo"


def test_route_listing_returns_empty_payload_for_unready_project(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=False),
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/demo/listing",
        {"addr": ["0x10"], "before": ["5"], "after": ["7"]},
    )
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["rows"] == []


def test_route_listing_raises_if_rows_not_loaded(monkeypatch: pytest.MonkeyPatch) -> None:
    disasm_server._PROJECT_ROW_CACHE.clear()
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )
    with pytest.raises(ValueError, match="Canonical rows not loaded"):
        disasm_server.route_request("GET", "/api/projects/bloodwych/listing", {})


def test_route_listing_returns_cached_window(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [ListingRow(row_id="r0", kind="instruction", text="moveq #0,d0\n", addr=0x10)]
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE["bloodwych"] = rows
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing",
        {"addr": ["0x10"], "before": ["5"], "after": ["7"]},
    )
    data = cast(dict[str, object], payload["data"])
    rows_data = cast(list[dict[str, object]], data["rows"])

    assert payload["ok"] is True
    assert data["anchor_addr"] == 0x10
    assert rows_data[0]["row_id"] == "r0"
    assert rows_data[0]["view_annotations"] == []


def test_route_listing_keeps_view_annotations_empty_for_monam(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        ListingRow(row_id="r0", kind="label", text="setpointer_pointer:\n", addr=0x0008),
        ListingRow(row_id="r1", kind="instruction", text="movea.l #memtask,a0\n", addr=0x0298),
        ListingRow(row_id="r2", kind="label", text="call_setpointer:\n", addr=0x8146),
    ]
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE["amiga_hunk_monam302"] = rows
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/amiga_hunk_monam302/listing",
        {"before": ["5"], "after": ["7"]},
    )
    data = cast(dict[str, object], payload["data"])
    rows_data = cast(list[dict[str, object]], data["rows"])

    assert payload["ok"] is True
    assert rows_data[0]["view_annotations"] == []
    assert rows_data[1]["view_annotations"] == []
    assert rows_data[2]["view_annotations"] == []


def test_route_listing_adds_api_call_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="jsr _LVOSetPointer(a6)\n",
            addr=0x814E,
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
        )
    ]
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE["bloodwych"] = rows
    disasm_server._PROJECT_API_CALL_CACHE["bloodwych"] = {
        (0, 0x814E): {
            "library": "intuition.library",
            "function": "SetPointer",
            "inputs": [
                {
                    "name": "pointer",
                    "regs": ["A1"],
                    "type": "UWORD *",
                    "i_struct": None,
                    "source": "parsed NDK",
                }
            ],
        }
    }
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request("GET", "/api/projects/bloodwych/listing", {})
    data = cast(dict[str, object], payload["data"])
    rows_data = cast(list[dict[str, object]], data["rows"])

    assert rows_data[0]["api_call"] == {
        "library": "intuition.library",
        "function": "SetPointer",
        "inputs": [
            {
                "name": "pointer",
                "regs": ["A1"],
                "type": "UWORD *",
                "i_struct": None,
                "source": "parsed NDK",
            }
        ],
    }


def test_route_listing_does_not_attach_api_call_metadata_to_label_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="label",
            text="loc_0010:\n",
            addr=0x10,
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
        ),
        ListingRow(
            row_id="r1",
            kind="instruction",
            text="jsr _LVOSetPointer(a6)\n",
            addr=0x10,
            source_context=BlockRowContext(kind="core-block", hunk_index=0),
        ),
    ]
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE["bloodwych"] = rows
    disasm_server._PROJECT_API_CALL_CACHE["bloodwych"] = {
        (0, 0x10): {
            "library": "intuition.library",
            "function": "SetPointer",
            "inputs": [],
        }
    }
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request("GET", "/api/projects/bloodwych/listing", {})
    data = cast(dict[str, object], payload["data"])
    rows_data = cast(list[dict[str, object]], data["rows"])

    assert rows_data[0]["api_call"] is None
    assert rows_data[1]["api_call"] == {
        "library": "intuition.library",
        "function": "SetPointer",
        "inputs": [],
    }


def test_route_listing_does_not_cross_apply_api_call_metadata_between_hunks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        ListingRow(
            row_id="r0",
            kind="instruction",
            text="moveq #1,d0\n",
            addr=0x10,
            source_context=BlockRowContext(kind="core-block", hunk_index=1),
        ),
        ListingRow(
            row_id="r1",
            kind="instruction",
            text="jsr _LVOOpenLibrary(a6)\n",
            addr=0x10,
            source_context=BlockRowContext(kind="core-block", hunk_index=3),
        ),
    ]
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._PROJECT_API_CALL_CACHE.clear()
    disasm_server._PROJECT_ROW_CACHE["bloodwych"] = rows
    disasm_server._PROJECT_API_CALL_CACHE["bloodwych"] = {
        (3, 0x10): {
            "library": "exec.library",
            "function": "OpenLibrary",
            "inputs": [],
        }
    }
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )

    payload = disasm_server.route_request("GET", "/api/projects/bloodwych/listing", {})
    data = cast(dict[str, object], payload["data"])
    rows_data = cast(list[dict[str, object]], data["rows"])

    assert rows_data[0]["api_call"] is None
    assert rows_data[1]["api_call"] == {
        "library": "exec.library",
        "function": "OpenLibrary",
        "inputs": [],
    }


def test_route_type_catalog_returns_known_structs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "load_live_os_reference_payload",
        lambda: {
            "_meta": {"api_input_type_overrides": []},
            "libraries": {},
            "constants": {},
            "structs": {
                "SimpleSprite": {"source": "GRAPHICS/SPRITE.I", "size": 12, "fields": []},
                "Window": {"source": "INTUITION/INTUITION.I", "size": 34, "fields": []},
            },
        },
    )

    payload = disasm_server.route_request("GET", "/api/projects/bloodwych/api/type-catalog", {})
    data = cast(list[dict[str, object]], payload["data"])

    assert payload["ok"] is True
    assert data[0]["name"] == "SimpleSprite"
    assert data[0]["source"] == "GRAPHICS/SPRITE.I"


def test_route_patch_api_input_struct_writes_global_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    corrections_path = tmp_path / "amiga_ndk_corrections.json"
    corrections_path.write_text(json.dumps({
        "_meta": {
            "absolute_symbols": [],
            "api_input_semantic_assertions": [],
            "api_input_type_overrides": [],
            "api_input_value_bindings": [],
            "struct_field_value_bindings": [],
            "value_domains": {},
        },
        "libraries": {},
        "structs": {},
        "constants": {},
    }))
    monkeypatch.setattr(disasm_server, "_OS_CORRECTIONS_PATH", corrections_path)
    monkeypatch.setattr(disasm_server, "install_live_runtime_os_kb", lambda: None)
    monkeypatch.setattr(
        disasm_server,
        "load_live_os_reference_payload",
        lambda: {
            "_meta": {"api_input_type_overrides": []},
            "constants": {},
            "structs": {
                "SimpleSprite": {"source": "GRAPHICS/SPRITE.I", "size": 12, "fields": []},
            },
            "libraries": {
                "intuition.library": {
                    "functions": {
                        "SetPointer": {
                            "inputs": [
                                {"name": "pointer", "type": "UWORD *"},
                            ]
                        }
                    }
                }
            },
        },
    )

    payload = disasm_server.route_request(
        "PATCH",
        "/api/projects/bloodwych/api/functions/intuition.library/SetPointer/inputs/pointer/struct",
        {},
        {"struct_name": "SimpleSprite"},
    )
    data = cast(dict[str, object], payload["data"])
    persisted = json.loads(corrections_path.read_text())

    assert payload["ok"] is True
    assert data["type"] == "struct SimpleSprite *"
    overrides = persisted["_meta"]["api_input_type_overrides"]
    assert overrides == [{
        "citation": "User-edited via disasm UI",
        "function": "SetPointer",
        "i_struct": "SimpleSprite",
        "input": "pointer",
        "library": "intuition.library",
        "review_status": "validated",
        "seed_origin": "manual",
        "type": "struct SimpleSprite *",
    }]


def test_route_listing_open_starts_job(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "get_project",
        lambda project_name: _binary_project(project_name, ready=True),
    )
    monkeypatch.setattr(
        disasm_server,
        "_start_listing_job",
        lambda project_name: {"job_id": "job-1", "project_id": project_name, "status": "queued"},
    )

    payload = disasm_server.route_request(
        "POST",
        "/api/projects/bloodwych/listing/open",
        {},
    )
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["job_id"] == "job-1"


def test_start_listing_job_ignores_stale_ready_job_without_rows() -> None:
    disasm_server._PROJECT_ROW_CACHE.clear()
    disasm_server._ASYNC_JOBS.clear()
    disasm_server._ASYNC_JOBS["stale-job"] = {
        "job_id": "stale-job",
        "job_kind": "listing",
        "project_id": "bloodwych",
        "result_project_id": "bloodwych",
        "status": "ready",
        "phase_id": "done",
        "phase_index": 2,
        "phase_count": 2,
        "progress_mode": "determinate",
        "progress_current": 2,
        "progress_total": 2,
        "progress_percent": 100,
        "total_rows": 10,
        "error": None,
        "created_at": 1.0,
        "finished_at": 1.0,
    }

    payload = disasm_server._start_listing_job("bloodwych")

    assert payload["job_id"] != "stale-job"
    assert payload["status"] in {"queued", "building"}


def test_route_listing_status_returns_job(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server,
        "_job_payload",
        lambda job_id: {"job_id": job_id, "status": "building", "phase_id": "emit_rows"},
    )

    payload = disasm_server.route_request(
        "GET",
        "/api/projects/bloodwych/listing/status",
        {"job_id": ["job-1"]},
    )
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["status"] == "building"
    assert data["phase_id"] == "emit_rows"


def test_json_bytes_returns_valid_json() -> None:
    body = disasm_server._json_bytes({"ok": True, "data": {"x": 1}})

    assert json.loads(body.decode("utf-8")) == {"ok": True, "data": {"x": 1}}


def test_resolve_static_response_serves_index() -> None:
    response = disasm_server.resolve_static_response("/")

    assert response["content_type"] == "text/html; charset=utf-8"
    assert response["headers"]["Cache-Control"] == "no-store"
    assert b"Disassembly Projects" in response["body"]


def test_resolve_static_response_serves_project_route() -> None:
    response = disasm_server.resolve_static_response("/bloodwych")

    assert response["content_type"] == "text/html; charset=utf-8"
    assert response["headers"]["Cache-Control"] == "no-store"
    assert b"Disassembly Projects" in response["body"]


def test_resolve_static_response_serves_dotted_project_route() -> None:
    response = disasm_server.resolve_static_response("/amiga_disk_search-for-the-king")

    assert response["content_type"] == "text/html; charset=utf-8"
    assert response["headers"]["Cache-Control"] == "no-store"
    assert b"Disassembly Projects" in response["body"]


def test_resolve_static_response_serves_app_js_with_no_store() -> None:
    response = disasm_server.resolve_static_response("/app.js")

    assert response["content_type"] == "application/javascript; charset=utf-8"
    assert response["headers"]["Cache-Control"] == "no-store"
    assert b"function renderDiskTargets(manifest)" in response["body"]


def test_resolve_static_response_rejects_missing_file() -> None:
    with pytest.raises(FileNotFoundError, match="Unknown route"):
        disasm_server.resolve_static_response("/assets/missing.txt")


def test_route_get_entity_returns_annotation_view(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(disasm_server, "get_entity",
                        lambda project_name, addr: {"addr": addr, "name": "main"})

    payload = disasm_server.route_request(
        "GET", "/api/projects/bloodwych/entities/0x0000", {})
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["name"] == "main"


def test_route_patch_entity_updates_annotations(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        disasm_server, "patch_entity",
        lambda project_name, addr, body: {"addr": addr, "name": body["name"]},
    )

    payload = disasm_server.route_request(
        "PATCH", "/api/projects/bloodwych/entities/0x0000", {},
        {"name": "main"})
    data = cast(dict[str, object], payload["data"])

    assert payload["ok"] is True
    assert data["name"] == "main"
