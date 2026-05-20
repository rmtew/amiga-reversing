#!/usr/bin/env python3
"""Find general OCR/readability issues in Classic Mac OS Markdown docs."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


PAGE_RE = re.compile(r"<!--\s*source-page:\s*(\d+)\s*-->")

RULES: list[dict[str, Any]] = [
    {
        "id": "mojibake_latin1",
        "pattern": r"[ÃÂ]",
        "description": "Likely UTF-8/Latin-1 mojibake marker.",
        "auto_replacement": None,
    },
    {
        "id": "boolean_split",
        "pattern": r"\b(?:F ALSE|T RUE|N IL)\b",
        "description": "Split Pascal boolean/nil token.",
        "auto_replacement": {"F ALSE": "FALSE", "T RUE": "TRUE", "N IL": "NIL"},
    },
    {
        "id": "param_ocr",
        "pattern": r"\b(?:pararn|Pararn|ioPararn|filePararn|cntrlPararn|csPararn|pararnBlock|PararnBlock|PararnBlk|ParrnBlk|PannBlk|PannBlkPtr|ParrnBlkPtr|HParrnBlkPtr)\b",
        "description": "Common OCR damage in parameter-block identifiers.",
        "auto_replacement": {
            "pararn": "param",
            "Pararn": "Param",
            "ioPararn": "ioParam",
            "filePararn": "fileParam",
            "cntrlPararn": "cntrlParam",
            "csPararn": "csParam",
            "pararnBlock": "paramBlock",
            "PararnBlock": "ParamBlock",
            "PararnBlk": "ParmBlk",
            "ParrnBlk": "ParmBlk",
            "PannBlk": "ParmBlk",
            "PannBlkPtr": "ParmBlkPtr",
            "ParrnBlkPtr": "ParmBlkPtr",
            "HParrnBlkPtr": "HParmBlkPtr",
        },
    },
    {
        "id": "volume_ocr",
        "pattern": r"\b(?:volurne|Volurne|volurnePararn|volumePararn)\b",
        "description": "Common rn/m OCR damage in volume identifiers.",
        "auto_replacement": {
            "volurne": "volume",
            "Volurne": "Volume",
            "volurnePararn": "volumeParam",
            "volumePararn": "volumeParam",
        },
    },
    {
        "id": "appletalk_ocr",
        "pattern": r"\b(?:AppleTelk|App leTelk)\b",
        "description": "Common OCR damage in AppleTalk.",
        "auto_replacement": {"AppleTelk": "AppleTalk", "App leTelk": "AppleTalk"},
    },
    {
        "id": "routine_page_ref_roman",
        "pattern": r"\bIl-\d+\b",
        "description": "Likely OCR damage for Roman numeral II page references.",
        "auto_replacement": None,
    },
    {
        "id": "split_pascal_assignment",
        "pattern": r":\s+=",
        "description": "Split Pascal assignment operator.",
        "auto_replacement": None,
    },
]


def page_for_offset(offset: int, page_markers: list[tuple[int, int]]) -> int | None:
    current: int | None = None
    for marker_offset, page in page_markers:
        if marker_offset > offset:
            break
        current = page
    return current


def line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def context_line(text: str, offset: int) -> str:
    start = text.rfind("\n", 0, offset) + 1
    end = text.find("\n", offset)
    if end == -1:
        end = len(text)
    return text[start:end].strip()


def audit_doc(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    markers = [(match.start(), int(match.group(1))) for match in PAGE_RE.finditer(text)]
    findings: list[dict[str, Any]] = []
    seen: set[tuple[str, str, int | None, str]] = set()

    for rule in RULES:
        pattern = re.compile(rule["pattern"])
        for match in pattern.finditer(text):
            page = page_for_offset(match.start(), markers)
            token = match.group(0)
            key = (rule["id"], token, page, context_line(text, match.start()))
            if key in seen:
                continue
            seen.add(key)
            replacement = None
            if rule["auto_replacement"]:
                replacement = rule["auto_replacement"].get(token)
            findings.append(
                {
                    "document": path.name,
                    "page": page,
                    "line": line_for_offset(text, match.start()),
                    "rule": rule["id"],
                    "match": token,
                    "auto_replacement": replacement,
                    "description": rule["description"],
                    "context": context_line(text, match.start()),
                }
            )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs", type=Path, default=Path("ext/docs_macos"))
    parser.add_argument("--output", type=Path, default=Path("ext/docs_macos/macos_text_audit.json"))
    args = parser.parse_args()

    findings: list[dict[str, Any]] = []
    for doc in sorted(args.docs.glob("*.md")):
        if doc.name == "README.md":
            continue
        findings.extend(audit_doc(doc))

    report = {
        "schema": "macos_doc_text_audit.v1",
        "docs": str(args.docs).replace("\\", "/"),
        "finding_count": len(findings),
        "counts_by_rule": dict(sorted(Counter(finding["rule"] for finding in findings).items())),
        "counts_by_document": dict(sorted(Counter(finding["document"] for finding in findings).items())),
        "findings": findings,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output} with {len(findings)} finding(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
