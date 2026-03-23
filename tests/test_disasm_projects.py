from __future__ import annotations

import json
from pathlib import Path

from disasm.project_paths import resolve_project_paths
from disasm.projects import create_project, list_projects, mark_project_opened


def test_resolve_project_paths_uses_recorded_binary_path(tmp_path: Path) -> None:
    project_root = tmp_path
    target_dir = project_root / "targets" / "demo"
    bin_dir = project_root / "bin"
    target_dir.mkdir(parents=True)
    bin_dir.mkdir(parents=True)

    entities_path = target_dir / "entities.jsonl"
    entities_path.write_text("")
    binary_path = bin_dir / "DemoGame"
    binary_path.write_bytes(b"\x4e\x75")
    (target_dir / "binary_path.txt").write_text(str(binary_path))
    (target_dir / "DemoGame.s").write_text("; output\n")

    resolved = resolve_project_paths("demo", project_root=project_root)

    assert resolved.binary_path == binary_path
    assert resolved.output_path == target_dir / "DemoGame.s"
    assert resolved.provenance == "recorded"


def test_list_projects_includes_unready_project(tmp_path: Path) -> None:
    project_root = tmp_path
    target_dir = project_root / "targets" / "demo"
    target_dir.mkdir(parents=True)
    (target_dir / "entities.jsonl").write_text("")

    projects = list_projects(project_root=project_root)

    assert len(projects) == 1
    assert projects[0]["id"] == "demo"
    assert projects[0]["ready"] is False
    assert projects[0]["binary_path"] is None


def test_create_project_creates_entities_file(tmp_path: Path) -> None:
    project = create_project("demo", project_root=tmp_path)

    assert project["id"] == "demo"
    assert (tmp_path / "targets" / "demo" / "entities.jsonl").exists()


def test_mark_project_opened_records_recent_timestamp(tmp_path: Path) -> None:
    create_project("demo", project_root=tmp_path)

    project = mark_project_opened("demo", project_root=tmp_path)
    state = json.loads((tmp_path / "targets" / ".browser_state.json").read_text())

    assert project["last_opened"] == state["recent_projects"]["demo"]


def test_list_projects_orders_by_most_recently_opened(tmp_path: Path) -> None:
    create_project("older", project_root=tmp_path)
    create_project("newer", project_root=tmp_path)
    mark_project_opened("older", project_root=tmp_path)
    mark_project_opened("newer", project_root=tmp_path)

    projects = list_projects(project_root=tmp_path)

    assert [project["id"] for project in projects] == ["newer", "older"]
