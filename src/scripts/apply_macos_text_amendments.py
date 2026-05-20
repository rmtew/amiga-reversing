#!/usr/bin/env python3
"""Apply conservative text-quality fixes from the Mac docs OCR audit."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


def whole_token_pattern(token: str) -> re.Pattern[str]:
    if re.match(r"^[A-Za-z0-9_ ]+$", token):
        return re.compile(rf"\b{re.escape(token)}\b")
    return re.compile(re.escape(token))


def build_amendments(audit: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for finding in audit["findings"]:
        replacement = finding.get("auto_replacement")
        if not replacement:
            continue
        key = (finding["document"], finding["match"], replacement, finding["rule"])
        item = grouped.setdefault(
            key,
            {
                "document": finding["document"],
                "match": finding["match"],
                "replacement": replacement,
                "rule": finding["rule"],
                "pages": [],
                "audit_lines": [],
            },
        )
        page = finding.get("page")
        if page is not None and page not in item["pages"]:
            item["pages"].append(page)
        line = finding.get("line")
        if line is not None:
            item["audit_lines"].append(line)

    amendments = list(grouped.values())
    amendments.sort(key=lambda item: (item["document"], item["rule"], item["match"]))
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
            pattern = whole_token_pattern(item["match"])
            matches = list(pattern.finditer(text))
            item["occurrences_before"] = len(matches)
            if matches:
                text = pattern.sub(item["replacement"], text)
            item["occurrences_replaced"] = len(matches)
        if not dry_run:
            path.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", type=Path, default=Path("ext/docs_macos/macos_text_audit.json"))
    parser.add_argument("--docs", type=Path, default=Path("ext/docs_macos"))
    parser.add_argument("--output", type=Path, default=Path("ext/docs_macos/macos_text_amendments.json"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    amendments = build_amendments(audit)
    apply_amendments(args.docs, amendments, args.dry_run)

    report = {
        "schema": "macos_doc_text_amendments.v1",
        "audit": str(args.audit).replace("\\", "/"),
        "docs": str(args.docs).replace("\\", "/"),
        "selection": (
            "Auto-applied only fixed text substitutions listed by the text audit rules. "
            "Mojibake and ambiguous Roman numeral/page-reference findings stay review-only."
        ),
        "dry_run": args.dry_run,
        "amendment_count": len(amendments),
        "replacement_count": sum(item.get("occurrences_replaced", 0) for item in amendments),
        "amendments": amendments,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"{'would write' if args.dry_run else 'wrote'} {args.output} with "
        f"{len(amendments)} amendment(s), {report['replacement_count']} replacement(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
