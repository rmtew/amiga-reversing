from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from amiga_reversing import reversing_loop
from amiga_reversing.disasm.manual_actions import (
    ReviewItemKind,
    ReviewItemScope,
    ReviewItemState,
)
from amiga_reversing.disasm.projects import ProjectKind, ProjectRecord


def _target(tmp_path: Path, name: str = "demo") -> Path:
    target_dir = tmp_path / "targets" / name
    target_dir.mkdir(parents=True)
    return target_dir


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


def test_inspect_report_generation_does_not_mutate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target_dir = _target(tmp_path)
    (target_dir / "source_binary.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(reversing_loop.projects, "get_project", lambda target_id, project_root: _project(()))

    report = reversing_loop.inspect_target("demo", project_root=tmp_path)

    assert report["target_id"] == "demo"
    assert report["safe_to_mutate"] is True
    assert sorted(path.name for path in target_dir.iterdir()) == ["source_binary.json"]


def test_inspect_candidates_include_durable_identity_or_locator(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _target(tmp_path)
    item = {
        "kind": ReviewItemKind.ORPHAN_CODE_CANDIDATE,
        "scope": ReviewItemScope.RANGE,
        "state": ReviewItemState.OPEN,
        "item_id": "orphan:h0:$00000010-$00000012",
        "hunk": 0,
        "start": 0x10,
        "end": 0x12,
        "ref_count": 2,
        "message": "orphan code",
        "suggested_actions": [{"action": "create_manual_seed"}],
    }
    monkeypatch.setattr(reversing_loop.projects, "get_project", lambda target_id, project_root: _project((item,)))

    report = reversing_loop.inspect_target("demo", project_root=tmp_path)
    candidate = report["candidate_work"][0]

    assert candidate["durable_id"] == "orphan:h0:$00000010-$00000012"
    assert candidate["locator"] == {"section_index": 0, "start_offset": 0x10, "end_offset": 0x12}
    assert candidate["evidence"]["has_xrefs"] is True


def test_inspect_unsafe_hygiene_blocks_mutation_readiness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target_dir = _target(tmp_path)
    (target_dir / "unknown.txt").write_text("x", encoding="utf-8")
    monkeypatch.setattr(reversing_loop.projects, "get_project", lambda target_id, project_root: _project(()))

    report = reversing_loop.inspect_target("demo", project_root=tmp_path)

    assert report["safe_to_mutate"] is False
    assert report["hygiene"]["unknown_files"] == ["unknown.txt"]


def test_inspect_cli_reports_json(tmp_path: Path) -> None:
    _target(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "amiga_reversing.reversing_loop",
            "--project-root",
            str(tmp_path),
            "inspect",
            "--target",
            "demo",
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    payload = json.loads(result.stdout)
    assert payload["target_id"] == "demo"
    assert payload["candidate_work"] == []
    assert payload["target_state"]["manual_action_log"]["count"] == 0
