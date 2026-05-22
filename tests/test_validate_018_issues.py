from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from amiga_reversing.tools.validate_018_issues import (
    validate_issue_path,
    validate_issue_text,
)

VALID_COMPLETED = """# 018-099: Fixture

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`

## Knowledge Delta

Done.

## Default Behavior

Unchanged.

## Evidence Standard

Checked.

## Implementation Slice

Implemented.

## Research Completion Standard

Recorded.

## Completion Evidence

- `pytest tests/test_validate_018_issues.py`

## Research Coverage

- [x] Checked.

## Research Review

- [x] Reviewed.

## Required Sign-Off

- [x] Signed.
"""


def test_validate_018_issue_accepts_completed_protocol_issue() -> None:
    report = validate_issue_text(VALID_COMPLETED, path=Path("018-099-fixture.md"))

    assert report["valid"] is True
    assert report["diagnostics"] == []


def test_validate_018_issue_rejects_completed_unchecked_boxes() -> None:
    report = validate_issue_text(
        VALID_COMPLETED.replace("- [x] Checked.", "- [ ] Checked."),
        path=Path("018-099-fixture.md"),
    )

    assert report["valid"] is False
    assert any("unchecked completed checkbox" in item["message"] for item in report["diagnostics"])


def test_validate_018_issue_allows_open_unchecked_boxes() -> None:
    report = validate_issue_text(
        VALID_COMPLETED.replace("Status: completed", "Status: open").replace("- [x] Checked.", "- [ ] Checked."),
        path=Path("018-099-fixture.md"),
    )

    assert report["valid"] is True


def test_validate_018_issue_rejects_missing_section_and_bad_superseded() -> None:
    missing_section = VALID_COMPLETED.replace("## Knowledge Delta\n\nDone.\n\n", "")
    superseded = VALID_COMPLETED.replace("Status: completed", "Status: superseded")

    assert validate_issue_text(missing_section, path=Path("018-099-fixture.md"))["valid"] is False
    report = validate_issue_text(superseded, path=Path("018-099-fixture.md"))
    assert report["valid"] is False
    assert any("superseded issue" in item["message"] for item in report["diagnostics"])


def test_validate_018_issue_rejects_deleted_without_reason() -> None:
    report = validate_issue_text(
        VALID_COMPLETED.replace("Status: completed", "Status: deleted"),
        path=Path("018-099-fixture.md"),
    )

    assert report["valid"] is False
    assert any("deleted issue" in item["message"] for item in report["diagnostics"])


def test_validate_018_issue_script_does_not_rewrite(tmp_path: Path) -> None:
    path = tmp_path / "018-099-fixture.md"
    path.write_text(VALID_COMPLETED, encoding="utf-8")
    before = path.read_text(encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "amiga_reversing.tools.validate_018_issues", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout == ""
    assert path.read_text(encoding="utf-8") == before


def test_validate_real_018_issues_pass() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    for issue in sorted((repo_root / "docs/issues").glob("018-*.md")):
        report = validate_issue_path(issue)
        assert report["valid"] is True, (issue, report["diagnostics"])
