from pathlib import Path

from disasm.project_paths import resolve_project_paths
from disasm.projects import list_projects


def test_resolve_project_paths_uses_recorded_binary_path(tmp_path):
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


def test_resolve_project_paths_requires_recorded_binary_path(tmp_path):
    project_root = tmp_path
    target_dir = project_root / "targets" / "demo"
    bin_dir = project_root / "bin"
    target_dir.mkdir(parents=True)
    bin_dir.mkdir(parents=True)

    (target_dir / "entities.jsonl").write_text("")
    (target_dir / "DemoGame.s").write_text("; output\n")
    binary_path = bin_dir / "DemoGame"
    binary_path.write_bytes(b"\x4e\x75")

    try:
        resolve_project_paths("demo", project_root=project_root)
    except FileNotFoundError as exc:
        assert "binary_path.txt" in str(exc)
    else:
        raise AssertionError("expected missing binary_path.txt failure")


def test_list_projects_reports_resolved_paths(tmp_path):
    project_root = tmp_path
    target_dir = project_root / "targets" / "demo"
    bin_dir = project_root / "bin"
    target_dir.mkdir(parents=True)
    bin_dir.mkdir(parents=True)

    (target_dir / "entities.jsonl").write_text("")
    (target_dir / "DemoGame.s").write_text("; output\n")
    binary_path = bin_dir / "DemoGame"
    binary_path.write_bytes(b"\x4e\x75")
    (target_dir / "binary_path.txt").write_text(str(binary_path))

    projects = list_projects(project_root=project_root)

    assert len(projects) == 1
    assert projects[0]["name"] == "demo"
    assert projects[0]["binary_path"] == str(binary_path)
    assert projects[0]["output_path"] == str(target_dir / "DemoGame.s")


def test_list_projects_raises_for_unresolvable_target(tmp_path):
    project_root = tmp_path
    target_dir = project_root / "targets" / "demo"
    target_dir.mkdir(parents=True)
    (target_dir / "entities.jsonl").write_text("")

    try:
        list_projects(project_root=project_root)
    except FileNotFoundError as exc:
        assert "binary_path.txt" in str(exc)
    else:
        raise AssertionError("expected missing binary_path.txt failure")
