"""Conservative cleanup for OCR-derived, page-cited Markdown sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

PAGE_MARKER_RE = re.compile(r"<!-- source-page: (\d+) -->\n## Page \1\n\n")
EMPTY_TABLE_RE = re.compile(
    r"(?m)^\s*<table>(?:<thead><tr>(?:<th></th>)+</tr></thead>)?"
    r"<tbody>?<tr>(?:<td></td>)+</tr></tbody>?</table>\s*$"
)

MOJIBAKE = {
    "â€™": "'",
    "â€˜": "'",
    "â€œ": '"',
    "â€\u009d": '"',
    "â€”": "--",
    "â€“": "-",
    "Â©": "(c)",
    "Â®": "(r)",
    "Â«": "<<",
    "Â»": ">>",
    "Â¢": "c",
    "Â£": "GBP",
    "Â": "",
}


@dataclass
class CleanResult:
    text: str
    counts: Counter[str]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Clean OCR-derived page-cited Markdown conservatively.")
    parser.add_argument("source_json", nargs="+", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    for source_json in args.source_json:
        clean_source(source_json, dry_run=args.dry_run)
    return 0


def clean_source(source_json: Path, *, dry_run: bool = False) -> None:
    metadata = _load_json(source_json)
    final_md = Path(cast(str, cast(dict[str, object], metadata["paths"])["final_md"]))
    original = final_md.read_text(encoding="utf-8")
    result = clean_markdown(original)
    changed = original != result.text
    print(f"{final_md}: changed={changed} {_format_counts(result.counts)}")
    if dry_run or not changed:
        return

    final_md.write_text(result.text, encoding="utf-8", newline="\n")
    cleanup = {
        "tool": "src/scripts/kb/clean_pdf_md.py",
        "rules": sorted(rule for rule, count in result.counts.items() if count),
        "counts": dict(sorted(result.counts.items())),
        "final_md_sha256_after": _sha256(final_md),
    }
    metadata["cleanup"] = cleanup
    cast(dict[str, object], metadata["sha256"])["final_md"] = cleanup["final_md_sha256_after"]
    source_json.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def clean_markdown(text: str) -> CleanResult:
    parts = PAGE_MARKER_RE.split(text)
    if len(parts) == 1:
        return _clean_page_text(text)

    output = [parts[0].rstrip(), ""]
    counts: Counter[str] = Counter()
    for index in range(1, len(parts), 2):
        page = parts[index]
        body = parts[index + 1]
        cleaned = _clean_page_text(body)
        counts.update(cleaned.counts)
        output.append(f"<!-- source-page: {page} -->")
        output.append(f"## Page {page}")
        output.append("")
        output.append(cleaned.text.strip())
        output.append("")
    return CleanResult("\n".join(output).rstrip() + "\n", counts)


def _clean_page_text(text: str) -> CleanResult:
    counts: Counter[str] = Counter()
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    text = _replace_mojibake(text, counts)
    text = _drop_empty_tables(text, counts)
    text = _join_alpha_hyphen_breaks(text, counts)
    text = _normalize_blank_lines(text, counts)
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return CleanResult(text.strip(), counts)


def _replace_mojibake(text: str, counts: Counter[str]) -> str:
    for src, dst in MOJIBAKE.items():
        count = text.count(src)
        if count:
            counts["mojibake_common"] += count
            text = text.replace(src, dst)
    return text


def _drop_empty_tables(text: str, counts: Counter[str]) -> str:
    text, count = EMPTY_TABLE_RE.subn("", text)
    counts["empty_table_drop"] += count
    return text


def _join_alpha_hyphen_breaks(text: str, counts: Counter[str]) -> str:
    pattern = re.compile(r"\b([A-Za-z]{2,})-\n([a-z]{2,})\b")
    text, count = pattern.subn(r"\1\2", text)
    counts["alpha_hyphen_join"] += count
    return text


def _normalize_blank_lines(text: str, counts: Counter[str]) -> str:
    text, count = re.subn(r"\n{3,}", "\n\n", text)
    counts["blank_line_collapse"] += count
    return text


def _format_counts(counts: Counter[str]) -> str:
    active = {key: value for key, value in counts.items() if value}
    return ", ".join(f"{key}={value}" for key, value in sorted(active.items())) or "no changes"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    raise SystemExit(main())
