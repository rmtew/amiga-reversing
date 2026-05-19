from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from amiga_reversing.reversing_workspace import (
    TargetFileAction,
    TargetFileClass,
    clean_run_target_workspace,
    inspect_target_hygiene,
)


def _target(tmp_path: Path, name: str = "demo") -> Path:
    target_dir = tmp_path / "targets" / name
    target_dir.mkdir(parents=True)
    return target_dir


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x", encoding="utf-8")


def _entry(report: object, path: str) -> dict[str, object]:
    files = report.to_dict()["files"]
    assert isinstance(files, list)
    for entry in files:
        assert isinstance(entry, dict)
        if entry["path"] == path:
            return entry
    raise AssertionError(f"missing hygiene entry for {path}")


def test_hygiene_preserves_source_import_facts(tmp_path: Path) -> None:
    target_dir = _target(tmp_path)
    _touch(target_dir / "source_binary.json")
    _touch(target_dir / "target_seeded_metadata.json")

    report = inspect_target_hygiene("demo", project_root=tmp_path)

    assert _entry(report, "source_binary.json")["class"] == TargetFileClass.SOURCE_IMPORT_FACT
    assert _entry(report, "target_seeded_metadata.json")["action"] == TargetFileAction.PRESERVE
    assert report.safe_to_clean_run is True


def test_hygiene_classifies_disk_import_state_and_nested_targets(tmp_path: Path) -> None:
    target_dir = _target(tmp_path)
    _touch(target_dir / "manifest.json")
    _touch(target_dir / "target_state.json")
    _touch(target_dir / "targets" / "raw_payload" / "source_binary.json")
    _touch(target_dir / "targets" / "raw_payload" / "target_metadata.json")
    _touch(target_dir / "targets" / "raw_payload" / "binary.bin")
    _touch(target_dir / "targets" / "raw_payload" / "reproduction.json")
    _touch(target_dir / "targets" / "raw_payload" / "payload.s")
    _touch(target_dir / "targets" / "raw_payload" / "ui_preferences.json")

    report = inspect_target_hygiene("demo", project_root=tmp_path)

    assert _entry(report, "manifest.json")["class"] == TargetFileClass.SOURCE_IMPORT_FACT
    assert _entry(report, "target_state.json")["action"] == TargetFileAction.PRESERVE
    assert _entry(report, "targets/raw_payload/source_binary.json")["class"] == TargetFileClass.SOURCE_IMPORT_FACT
    assert _entry(report, "targets/raw_payload/binary.bin")["action"] == TargetFileAction.PRESERVE
    assert _entry(report, "targets/raw_payload/reproduction.json")["class"] == TargetFileClass.GENERATED_OUTPUT
    assert _entry(report, "targets/raw_payload/payload.s")["action"] == TargetFileAction.REGENERATE_ON_CLEAN_RUN
    assert _entry(report, "targets/raw_payload/ui_preferences.json")["class"] == TargetFileClass.OBSOLETE_UI_STATE
    assert report.unknown_files == ()
    assert report.safe_to_clean_run is True


def test_hygiene_classifies_obsolete_ui_and_manual_state(tmp_path: Path) -> None:
    target_dir = _target(tmp_path)
    _touch(target_dir / "target_ui_edits.json")
    _touch(target_dir / "ui_preferences.json")
    _touch(target_dir / "manual_actions.jsonl")

    report = inspect_target_hygiene("demo", project_root=tmp_path)

    assert _entry(report, "target_ui_edits.json")["class"] == TargetFileClass.OBSOLETE_UI_STATE
    assert _entry(report, "ui_preferences.json")["action"] == TargetFileAction.DELETE_ON_CLEAN_RUN
    assert _entry(report, "manual_actions.jsonl")["class"] == TargetFileClass.LOCAL_MANUAL_STATE


def test_hygiene_marks_unknown_files_unsafe(tmp_path: Path) -> None:
    target_dir = _target(tmp_path)
    _touch(target_dir / "notes.json")

    report = inspect_target_hygiene("demo", project_root=tmp_path)

    assert report.unknown_files == ("notes.json",)
    assert report.safe_to_clean_run is False
    assert _entry(report, "notes.json")["action"] == TargetFileAction.REVIEW_REQUIRED


def test_hygiene_report_is_json_serializable_and_separates_agent_audit(tmp_path: Path) -> None:
    target_dir = _target(tmp_path)
    _touch(target_dir / "agent" / "reversing-loop.jsonl")
    _touch(target_dir / "reproduction.json")

    report = inspect_target_hygiene("demo", project_root=tmp_path)
    payload = report.to_dict()

    assert _entry(report, "agent/reversing-loop.jsonl")["class"] == TargetFileClass.AGENT_AUDIT
    assert _entry(report, "reproduction.json")["class"] == TargetFileClass.GENERATED_OUTPUT
    assert json.loads(json.dumps(payload))["recommended_modes"] == ["continue", "clean-run", "reimport"]


def test_hygiene_cli_reports_json(tmp_path: Path) -> None:
    target_dir = _target(tmp_path)
    _touch(target_dir / "source_binary.json")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "amiga_reversing.reversing_loop",
            "--project-root",
            str(tmp_path),
            "hygiene",
            "--target",
            "demo",
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    payload = json.loads(result.stdout)
    assert payload["target_id"] == "demo"
    assert payload["files"][0]["class"] == TargetFileClass.SOURCE_IMPORT_FACT


def test_clean_run_preserves_source_import_facts(tmp_path: Path) -> None:
    target_dir = _target(tmp_path)
    _touch(target_dir / "source_binary.json")

    report = clean_run_target_workspace("demo", project_root=tmp_path)

    assert report.status == "completed"
    assert (target_dir / "source_binary.json").exists()


def test_clean_run_deletes_obsolete_ui_and_manual_state(tmp_path: Path) -> None:
    target_dir = _target(tmp_path)
    _touch(target_dir / "target_ui_edits.json")
    _touch(target_dir / "ui_preferences.json")
    _touch(target_dir / "manual_actions.jsonl")

    report = clean_run_target_workspace("demo", project_root=tmp_path)

    assert sorted(report.deleted_files) == ["manual_actions.jsonl", "target_ui_edits.json", "ui_preferences.json"]
    assert not (target_dir / "target_ui_edits.json").exists()
    assert not (target_dir / "ui_preferences.json").exists()
    assert not (target_dir / "manual_actions.jsonl").exists()


def test_clean_run_deletes_generated_state(tmp_path: Path) -> None:
    target_dir = _target(tmp_path)
    _touch(target_dir / "reproduction.json")
    _touch(target_dir / "demo.s")

    report = clean_run_target_workspace("demo", project_root=tmp_path)

    assert sorted(report.deleted_files) == ["demo.s", "reproduction.json"]
    assert not (target_dir / "reproduction.json").exists()
    assert not (target_dir / "demo.s").exists()


def test_clean_run_stops_on_unknown_without_deletion(tmp_path: Path) -> None:
    target_dir = _target(tmp_path)
    _touch(target_dir / "notes.json")
    _touch(target_dir / "reproduction.json")

    report = clean_run_target_workspace("demo", project_root=tmp_path)

    assert report.status == "blocked"
    assert report.blocked_reason == "unknown target-local files require review before clean-run"
    assert report.deleted_files == ()
    assert (target_dir / "notes.json").exists()
    assert (target_dir / "reproduction.json").exists()


def test_clean_run_writes_before_after_report(tmp_path: Path) -> None:
    target_dir = _target(tmp_path)
    _touch(target_dir / "reproduction.json")

    report = clean_run_target_workspace("demo", project_root=tmp_path)

    before_path = Path(report.report_paths["before"])
    latest_path = Path(report.report_paths["latest"])
    assert before_path.exists()
    assert latest_path.exists()
    payload = json.loads(latest_path.read_text(encoding="utf-8"))
    assert payload["before"]["files"][0]["path"] == "reproduction.json"
    assert payload["after"]["target_id"] == "demo"
    assert payload["deleted_files"] == ["reproduction.json"]


def test_clean_run_cli_reports_json(tmp_path: Path) -> None:
    target_dir = _target(tmp_path)
    _touch(target_dir / "reproduction.json")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "amiga_reversing.reversing_loop",
            "--project-root",
            str(tmp_path),
            "clean-run",
            "--target",
            "demo",
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    payload = json.loads(result.stdout)
    assert payload["status"] == "completed"
    assert payload["deleted_files"] == ["reproduction.json"]
