from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from amiga_reversing.tools.validate_017_issues import (
    validate_issue_path,
    validate_issue_text,
)

VALID_COMPLETED = """# 017-099: Fixture

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`

## Protocol Delta

Done.

## Default Behavior

Unchanged.

## Research Coverage

- [x] Checked.

## Research Review

- [x] Reviewed.

## Required Sign-Off

- [x] Signed.

## Completion Evidence

- `pytest tests/test_validate_017_issues.py`
"""


def test_validate_017_issue_accepts_completed_protocol_issue() -> None:
    report = validate_issue_text(VALID_COMPLETED, path=Path("017-099-fixture.md"))

    assert report["valid"] is True
    assert report["diagnostics"] == []


def test_validate_017_issue_rejects_completed_unchecked_boxes() -> None:
    report = validate_issue_text(
        VALID_COMPLETED.replace("- [x] Checked.", "- [ ] Checked."),
        path=Path("017-099-fixture.md"),
    )

    assert report["valid"] is False
    assert any("unchecked completed checkbox" in item["message"] for item in report["diagnostics"])


def test_validate_017_issue_allows_active_unchecked_boxes() -> None:
    report = validate_issue_text(
        VALID_COMPLETED.replace("Status: completed", "Status: active").replace("- [x] Checked.", "- [ ] Checked."),
        path=Path("017-099-fixture.md"),
    )

    assert report["valid"] is True


def test_validate_017_issue_keeps_pre_validator_history_out_of_scope() -> None:
    report = validate_issue_text(
        "# 017-038: Old Shape\n\nStatus: completed\n",
        path=Path("017-038-old-shape.md"),
    )

    assert report["valid"] is True


def test_validate_017_issue_rejects_missing_section_and_bad_superseded() -> None:
    missing_section = VALID_COMPLETED.replace("## Protocol Delta\n\nDone.\n\n", "")
    superseded = VALID_COMPLETED.replace("Status: completed", "Status: superseded")

    assert validate_issue_text(missing_section, path=Path("017-099-fixture.md"))["valid"] is False
    report = validate_issue_text(superseded, path=Path("017-099-fixture.md"))
    assert report["valid"] is False
    assert any("superseded issue" in item["message"] for item in report["diagnostics"])


def test_validate_017_issue_script_does_not_rewrite(tmp_path: Path) -> None:
    path = tmp_path / "017-099-fixture.md"
    path.write_text(VALID_COMPLETED, encoding="utf-8")
    before = path.read_text(encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "amiga_reversing.tools.validate_017_issues", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout == ""
    assert path.read_text(encoding="utf-8") == before


def test_validate_017_issue_path_accepts_current_completed_fixture(tmp_path: Path) -> None:
    issue = tmp_path / "017-099-fixture.md"
    issue.write_text(VALID_COMPLETED, encoding="utf-8")

    report = validate_issue_path(issue)

    assert report["valid"] is True, report["diagnostics"]
