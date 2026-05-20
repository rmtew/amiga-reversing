from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import cast

KNOWN_AVAILABILITY = {"committed", "optional_local", "required_local", "missing_external"}
KNOWN_EXTRACTION_STATUS = {"parsed", "parser_asserted", "candidate", "deferred", "unsupported"}
KNOWN_REVIEW_STATUS = {"not_applicable", "seeded", "validated"}
KNOWN_DECISION = {"parse", "cite_manually", "defer", "unsupported"}


def build_docs_inventory_report(project_root: Path, inventory_path: Path) -> dict[str, object]:
    payload = _load_json(inventory_path)
    sources = [source for source in cast(list[object], payload.get("sources", [])) if isinstance(source, dict)]
    rows = [_source_row(project_root, cast(Mapping[str, object], source)) for source in sources]
    return {
        "inventory_path": str(inventory_path),
        "source_count": len(rows),
        "availability_counts": dict(Counter(row["availability"] for row in rows)),
        "extraction_status_counts": dict(Counter(row["extraction_status"] for row in rows)),
        "review_status_counts": dict(Counter(row["review_status"] for row in rows)),
        "decision_counts": dict(Counter(row["decision"] for row in rows)),
        "sources": rows,
    }


def check_docs_inventory_report(report: Mapping[str, object]) -> list[str]:
    rows = cast(list[Mapping[str, object]], report["sources"])
    violations: list[str] = []
    violations.extend(_duplicate_violations(rows, "id"))
    violations.extend(_duplicate_violations(rows, "path"))
    for row in rows:
        source_id = cast(str, row["id"])
        if row["availability"] not in KNOWN_AVAILABILITY:
            violations.append(f"{source_id}: unknown availability {row['availability']}")
        if row["extraction_status"] not in KNOWN_EXTRACTION_STATUS:
            violations.append(f"{source_id}: unknown extraction_status {row['extraction_status']}")
        if row["review_status"] not in KNOWN_REVIEW_STATUS:
            violations.append(f"{source_id}: unknown review_status {row['review_status']}")
        if row["decision"] not in KNOWN_DECISION:
            violations.append(f"{source_id}: unknown decision {row['decision']}")
        if row["citation_quality"] != "page":
            violations.append(f"{source_id}: citation_quality must be page")
        if not row["path_exists"]:
            violations.append(f"{source_id}: source path missing: {row['path']}")
        if not row["metadata_exists"]:
            violations.append(f"{source_id}: metadata path missing: {row['metadata_path']}")
        if row["metadata_final_md"] and row["metadata_final_md"] != row["path"]:
            violations.append(f"{source_id}: metadata final_md does not match inventory path")
        expected = row["expected_markers"]
        actual = row["page_markers"]
        if expected is not None and actual != expected:
            violations.append(f"{source_id}: page marker count {actual} != expected {expected}")
    return violations


def format_docs_inventory_report(report: Mapping[str, object], *, title: str) -> str:
    lines = [
        title,
        "",
        "Source inventory:",
        f"  sources: {report['source_count']}",
        f"  availability: {_format_counts(cast(Mapping[str, int], report['availability_counts']))}",
        f"  extraction: {_format_counts(cast(Mapping[str, int], report['extraction_status_counts']))}",
        f"  review: {_format_counts(cast(Mapping[str, int], report['review_status_counts']))}",
        f"  decision: {_format_counts(cast(Mapping[str, int], report['decision_counts']))}",
        "",
        "Committed Markdown sources:",
    ]
    for row in cast(list[Mapping[str, object]], report["sources"]):
        lines.append(
            f"  {row['id']}: markers={row['page_markers']}/{row['expected_markers']} "
            f"quality={row['citation_quality']} path={row['path']}"
        )
    return "\n".join(lines)


def _source_row(project_root: Path, source: Mapping[str, object]) -> dict[str, object]:
    path = _string(source.get("path")) or ""
    metadata_path = _string(source.get("metadata_path")) or ""
    full_path = project_root / path
    full_metadata_path = project_root / metadata_path
    metadata = _load_json(full_metadata_path) if full_metadata_path.exists() else {}
    metadata_paths = cast(Mapping[str, object], metadata.get("paths", {}))
    probe = cast(Mapping[str, object], metadata.get("probe", {}))
    expected_markers = probe.get("final_markdown_page_markers", probe.get("text_pages"))
    return {
        "id": _string(source.get("id")) or "missing",
        "path": path,
        "metadata_path": metadata_path,
        "availability": _string(source.get("availability")) or "missing",
        "extraction_status": _string(source.get("extraction_status")) or "missing",
        "review_status": _string(source.get("review_status")) or "missing",
        "decision": _string(source.get("decision")) or "missing",
        "citation_quality": _string(source.get("citation_quality")) or "missing",
        "path_exists": full_path.exists(),
        "metadata_exists": full_metadata_path.exists(),
        "metadata_final_md": _string(metadata_paths.get("final_md")) or "",
        "page_markers": _page_marker_count(full_path),
        "expected_markers": int(expected_markers) if isinstance(expected_markers, int) else None,
    }


def _duplicate_violations(rows: list[Mapping[str, object]], key: str) -> list[str]:
    counts = Counter(cast(str, row[key]) for row in rows)
    duplicates = sorted(value for value, count in counts.items() if value and count > 1)
    return [f"duplicate {key}s: {', '.join(duplicates)}"] if duplicates else []


def _page_marker_count(path: Path) -> int:
    if not path.exists():
        return 0
    return path.read_text(encoding="utf-8", errors="replace").count("<!-- source-page:")


def _format_counts(counts: Mapping[str, int]) -> str:
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "none"


def _load_json(path: Path) -> dict[str, object]:
    return cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))


def _string(value: object) -> str | None:
    return value if isinstance(value, str) and value else None
