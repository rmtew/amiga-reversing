#!/usr/bin/env python3
"""Find likely OCR mistakes in Classic Mac docs using the MPW include index."""

from __future__ import annotations

import argparse
import difflib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


IDENT_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]{5,}\b")
PAGE_RE = re.compile(r"<!--\s*source-page:\s*(\d+)\s*-->")

STOP_WORDS = {
    "Addison",
    "Apple",
    "Computer",
    "Copyright",
    "Inside",
    "Macintosh",
    "MacintoshÂ",
    "Volume",
}


def normalized(value: str) -> str:
    return (
        value.replace("0", "O")
        .replace("1", "l")
        .replace("I", "l")
        .replace("3", "s")
        .replace("5", "S")
    )


def is_code_like(value: str) -> bool:
    if value in STOP_WORDS:
        return False
    if "_" in value:
        return True
    if re.search(r"[a-z][A-Z]", value):
        return True
    if re.match(r"(PB|FM|FS|HFS|Mac|Quick|New|Get|Set|Open|Close|Read|Write|Dispose|Handle|Ptr)[A-Z]", value):
        return True
    if value.startswith(("k", "gestalt", "fs", "io")) and re.search(r"[A-Z]", value):
        return True
    return False


def load_symbols(index_path: Path) -> tuple[set[str], dict[tuple[str, int], list[str]], dict[str, list[dict[str, object]]]]:
    data = json.loads(index_path.read_text(encoding="utf-8"))
    by_name: dict[str, list[dict[str, object]]] = defaultdict(list)
    for item in data["items"]:
        by_name[str(item["name"])].append(item)
    names = set(by_name)
    buckets: dict[tuple[str, int], list[str]] = defaultdict(list)
    for name in names:
        norm = normalized(name).lower()
        if len(norm) < 3:
            continue
        buckets[(norm[:2], len(norm))].append(name)
    for bucket in buckets.values():
        bucket.sort()
    return names, buckets, by_name


def page_for_offset(text: str, offset: int, page_markers: list[tuple[int, int]]) -> int | None:
    current: int | None = None
    for marker_offset, page in page_markers:
        if marker_offset > offset:
            break
        current = page
    return current


def line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def best_matches(token: str, buckets: dict[tuple[str, int], list[str]], limit: int) -> list[str]:
    norm_token = normalized(token).lower()
    candidates: list[str] = []
    for size in range(len(norm_token) - 2, len(norm_token) + 3):
        if size > 0:
            candidates.extend(buckets.get((norm_token[:2], size), []))
    if not candidates:
        return []
    close = difflib.get_close_matches(token, candidates, n=limit * 3, cutoff=0.86)
    scored: list[tuple[float, str]] = []
    for candidate in close:
        if token.lower() != candidate.lower() and normalized(token).lower() != normalized(candidate).lower():
            continue
        if token[1:] == candidate[1:] and token[:1].lower() == candidate[:1].lower():
            continue
        score = difflib.SequenceMatcher(None, norm_token, normalized(candidate).lower()).ratio()
        if score >= 0.88:
            scored.append((score, candidate))
    scored.sort(key=lambda item: (-item[0], item[1].lower()))
    return [candidate for _, candidate in scored[:limit]]


def context_line(text: str, offset: int) -> str:
    start = text.rfind("\n", 0, offset) + 1
    end = text.find("\n", offset)
    if end == -1:
        end = len(text)
    return text[start:end].strip()


def audit_doc(path: Path, symbol_names: set[str], buckets: dict[tuple[str, int], list[str]], by_name: dict[str, list[dict[str, object]]], limit: int) -> list[dict[str, object]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    markers = [(match.start(), int(match.group(1))) for match in PAGE_RE.finditer(text)]
    seen: set[tuple[str, int | None]] = set()
    findings: list[dict[str, object]] = []

    for match in IDENT_RE.finditer(text):
        token = match.group(0)
        if not is_code_like(token) or token in symbol_names:
            continue
        page = page_for_offset(text, match.start(), markers)
        key = (token, page)
        if key in seen:
            continue
        seen.add(key)
        suggestions = best_matches(token, buckets, limit=3)
        if not suggestions:
            continue
        suggestion_items = []
        for suggestion in suggestions:
            entries = by_name[suggestion][:3]
            suggestion_items.append(
                {
                    "name": suggestion,
                    "entries": [
                        {
                            "kind": entry["kind"],
                            "source": entry["source"],
                            "line": entry["line"],
                            **({"value": entry["value"]} if "value" in entry else {}),
                        }
                        for entry in entries
                    ],
                }
            )
        findings.append(
            {
                "document": path.name,
                "page": page,
                "line": line_for_offset(text, match.start()),
                "unknown": token,
                "suggestions": suggestion_items,
                "context": context_line(text, match.start()),
            }
        )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=Path, default=Path("ext/macos_includes/mpw_gm/index.json"))
    parser.add_argument("--docs", type=Path, default=Path("ext/docs_macos"))
    parser.add_argument("--output", type=Path, default=Path("ext/docs_macos/macos_include_audit.json"))
    parser.add_argument("--limit-per-doc", type=int, default=80)
    args = parser.parse_args()

    symbol_names, buckets, by_name = load_symbols(args.index)
    findings: list[dict[str, object]] = []
    for doc in sorted(args.docs.glob("*.md")):
        if doc.name == "README.md":
            continue
        findings.extend(audit_doc(doc, symbol_names, buckets, by_name, limit=3)[: args.limit_per_doc])

    counts = Counter(finding["document"] for finding in findings)
    report = {
        "schema": "macos_doc_include_audit.v1",
        "index": str(args.index).replace("\\", "/"),
        "docs": str(args.docs).replace("\\", "/"),
        "finding_count": len(findings),
        "counts_by_document": dict(sorted(counts.items())),
        "findings": findings,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output} with {len(findings)} finding(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
