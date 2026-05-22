from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

PROPOSAL_PATH = "docs/proposals/018-platform-executable-format-knowledge.md"
KNOWN_STATUSES = {"open", "active", "implemented", "completed", "complete", "deferred", "superseded", "deleted"}
COMPLETED_STATUSES = {"implemented", "completed", "complete"}
REQUIRED_SECTIONS = {
    "Proposal Context",
    "Knowledge Delta",
    "Default Behavior",
    "Evidence Standard",
    "Implementation Slice",
    "Research Completion Standard",
    "Research Coverage",
    "Research Review",
    "Required Sign-Off",
}
CHECKED_SECTIONS = {"Research Coverage", "Research Review", "Required Sign-Off"}


def validate_issue_path(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    return validate_issue_text(text, path=path)


def validate_issue_text(text: str, *, path: Path | None = None) -> dict[str, object]:
    diagnostics: list[dict[str, object]] = []
    status = _issue_status(text)
    sections = _sections(text)

    if status is None:
        diagnostics.append(_diagnostic("status", "Status: line is missing"))
    elif status not in KNOWN_STATUSES:
        diagnostics.append(_diagnostic("status", f"unknown status: {status}"))

    missing = sorted(REQUIRED_SECTIONS - set(sections))
    for section in missing:
        diagnostics.append(_diagnostic("section", f"missing required section: {section}"))
    if PROPOSAL_PATH not in text:
        diagnostics.append(_diagnostic("proposal", f"missing proposal reference: {PROPOSAL_PATH}"))

    if status in COMPLETED_STATUSES:
        if "Completion Evidence" not in sections:
            diagnostics.append(_diagnostic("completion_evidence", "completed issue lacks Completion Evidence section"))
        for section in sorted(CHECKED_SECTIONS):
            for line_number, line in _section_lines(sections, section):
                if re.match(r"\s*- \[ \]", line):
                    diagnostics.append(
                        _diagnostic("checkbox", f"unchecked completed checkbox in {section}", line=line_number)
                    )

    if status in {"superseded", "deleted"} and not re.search(
        r"\b(superseded by|replacement|replaced by|reason|deleted because)\b",
        text,
        re.I,
    ):
        diagnostics.append(_diagnostic(status, f"{status} issue must identify replacement or reason"))

    return {
        "path": str(path) if path is not None else None,
        "valid": not diagnostics,
        "status": status,
        "diagnostics": diagnostics,
    }


def validate_issue_paths(paths: Sequence[Path]) -> dict[str, object]:
    reports = [validate_issue_path(path) for path in paths]
    diagnostics = [
        {**diagnostic, "path": report["path"]}
        for report in reports
        for diagnostic in _diagnostic_sequence(report.get("diagnostics"))
    ]
    return {"valid": not diagnostics, "issue_count": len(reports), "issues": reports, "diagnostics": diagnostics}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate 018 issue protocol sign-off.")
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--issues-dir", type=Path, default=Path("docs/issues"))
    args = parser.parse_args(list(argv) if argv is not None else None)
    paths = args.paths or sorted(args.issues_dir.glob("018-*.md"))
    report = validate_issue_paths(paths)
    for diagnostic in report["diagnostics"]:
        path = diagnostic.get("path") or "<issue>"
        line = f":{diagnostic['line']}" if isinstance(diagnostic.get("line"), int) else ""
        print(f"{path}{line}: {diagnostic['message']}")
    return 0 if report["valid"] else 1


def _issue_status(text: str) -> str | None:
    match = re.search(r"^Status:\s*([A-Za-z_-]+)\s*$", text, re.M)
    return match.group(1).lower() if match else None


def _sections(text: str) -> dict[str, tuple[int, list[str]]]:
    result: dict[str, tuple[int, list[str]]] = {}
    current: str | None = None
    current_line = 0
    for index, line in enumerate(text.splitlines(), start=1):
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            current = match.group(1)
            current_line = index
            result[current] = (current_line, [])
            continue
        if current is not None:
            result[current][1].append(line)
    return result


def _section_lines(sections: Mapping[str, tuple[int, list[str]]], name: str) -> list[tuple[int, str]]:
    section = sections.get(name)
    if section is None:
        return []
    start, lines = section
    return [(start + index, line) for index, line in enumerate(lines, start=1)]


def _diagnostic(field: str, message: str, *, line: int | None = None) -> dict[str, object]:
    diagnostic: dict[str, object] = {"field": field, "message": message}
    if line is not None:
        diagnostic["line"] = line
    return diagnostic


def _diagnostic_sequence(value: object) -> list[dict[str, object]]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


if __name__ == "__main__":
    sys.exit(main())
