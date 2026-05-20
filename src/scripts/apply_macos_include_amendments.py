#!/usr/bin/env python3
"""Apply high-confidence Mac doc identifier fixes from the include audit."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


CONFUSABLES = str.maketrans(
    {
        "0": "O",
        "1": "l",
        "I": "l",
        "3": "s",
        "5": "S",
    }
)


def normalized(value: str) -> str:
    return value.translate(CONFUSABLES).lower()


def acceptance_reason(unknown: str, replacement: str) -> str | None:
    if unknown == replacement:
        return None
    if unknown.lower() == replacement.lower():
        return "case-only include match"
    if normalized(unknown) == normalized(replacement):
        return "OCR-confusable include match"
    return None


def word_pattern(token: str) -> re.Pattern[str]:
    return re.compile(rf"\b{re.escape(token)}\b")


def build_amendments(audit: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for finding in audit["findings"]:
        suggestions = finding["suggestions"]
        if len(suggestions) != 1:
            continue
        unknown = finding["unknown"]
        replacement = suggestions[0]["name"]
        reason = acceptance_reason(unknown, replacement)
        if reason is None:
            continue
        key = (finding["document"], unknown, replacement, reason)
        item = grouped.setdefault(
            key,
            {
                "document": finding["document"],
                "unknown": unknown,
                "replacement": replacement,
                "reason": reason,
                "pages": [],
                "audit_lines": [],
                "include_entries": suggestions[0]["entries"],
            },
        )
        page = finding.get("page")
        if page is not None and page not in item["pages"]:
            item["pages"].append(page)
        line = finding.get("line")
        if line is not None:
            item["audit_lines"].append(line)

    amendments = list(grouped.values())
    amendments.sort(key=lambda item: (item["document"], item["unknown"], item["replacement"]))
    for item in amendments:
        item["pages"].sort()
        item["audit_lines"].sort()
    return amendments


def apply_amendments(docs_dir: Path, amendments: list[dict[str, Any]], dry_run: bool) -> None:
    by_doc: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in amendments:
        by_doc[item["document"]].append(item)

    for document, items in sorted(by_doc.items()):
        path = docs_dir / document
        text = path.read_text(encoding="utf-8")
        for item in items:
            pattern = word_pattern(item["unknown"])
            matches = list(pattern.finditer(text))
            item["occurrences_before"] = len(matches)
            if matches:
                text = pattern.sub(item["replacement"], text)
            item["occurrences_replaced"] = len(matches)
        if not dry_run:
            path.write_text(text, encoding="utf-8", newline="\n")


def merge_amendments(existing: list[dict[str, Any]], new: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for item in [*existing, *new]:
        key = (item["document"], item["unknown"], item["replacement"], item["reason"])
        if key not in merged:
            merged[key] = item
            continue
        current = merged[key]
        current["pages"] = sorted(set(current.get("pages", [])) | set(item.get("pages", [])))
        current["audit_lines"] = sorted(set(current.get("audit_lines", [])) | set(item.get("audit_lines", [])))
        current["occurrences_before"] = current.get("occurrences_before", 0) + item.get("occurrences_before", 0)
        current["occurrences_replaced"] = current.get("occurrences_replaced", 0) + item.get("occurrences_replaced", 0)
    return sorted(merged.values(), key=lambda item: (item["document"], item["unknown"], item["replacement"]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", type=Path, default=Path("ext/docs_macos/macos_include_audit.json"))
    parser.add_argument("--docs", type=Path, default=Path("ext/docs_macos"))
    parser.add_argument("--output", type=Path, default=Path("ext/docs_macos/macos_include_amendments.json"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    new_amendments = build_amendments(audit)
    apply_amendments(args.docs, new_amendments, args.dry_run)
    existing_amendments: list[dict[str, Any]] = []
    if args.output.exists():
        existing = json.loads(args.output.read_text(encoding="utf-8"))
        existing_amendments = existing.get("amendments", [])
    amendments = merge_amendments(existing_amendments, new_amendments)

    report = {
        "schema": "macos_doc_include_amendments.v1",
        "audit": str(args.audit).replace("\\", "/"),
        "docs": str(args.docs).replace("\\", "/"),
        "selection": (
            "Auto-accepted only when an audit finding has exactly one MPW include-index "
            "suggestion and the unknown token differs from it only by case or OCR-confusable "
            "characters: 0/O, 1/l, I/l, 3/s, 5/S."
        ),
        "dry_run": args.dry_run,
        "new_amendment_count": len(new_amendments),
        "new_replacement_count": sum(item.get("occurrences_replaced", 0) for item in new_amendments),
        "amendment_count": len(amendments),
        "replacement_count": sum(item.get("occurrences_replaced", 0) for item in amendments),
        "amendments": amendments,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"{'would write' if args.dry_run else 'wrote'} {args.output} with "
        f"{report['new_amendment_count']} new amendment(s), "
        f"{report['new_replacement_count']} new replacement(s), "
        f"{len(amendments)} total amendment(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
