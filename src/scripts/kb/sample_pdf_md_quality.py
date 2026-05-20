"""Sample page-cited Markdown quality against source PDF text extraction."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, cast

import fitz  # type: ignore[import-untyped]

KEYWORDS = (
    "contents",
    "index",
    "trap",
    "toolbox",
    "resource",
    "quickdraw",
    "mpw",
    "assembly",
    "procedure",
    "function",
    "pascal",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sample final Markdown pages for PDF conversion quality.")
    parser.add_argument("source_json", nargs="+", type=Path)
    parser.add_argument("--chars", type=int, default=500)
    args = parser.parse_args(argv)

    for path in args.source_json:
        report_source(path, chars=args.chars)
    return 0


def report_source(source_json: Path, *, chars: int) -> None:
    metadata = _load_json(source_json)
    title = metadata.get("title") or metadata.get("source_id") or source_json.stem
    source_pdf = Path(cast(str, cast(dict[str, object], metadata["paths"])["source_pdf"]))
    final_md = Path(cast(str, cast(dict[str, object], metadata["paths"])["final_md"]))
    weak_pages = [int(page) for page in cast(dict[str, list[int]], metadata["remaining_review"])["weak_pages"]]
    pages = _sample_pages(final_md, weak_pages)
    pdf = fitz.open(source_pdf)
    md_pages = _markdown_pages(final_md)

    print(f"# {title}")
    print(f"source={source_json.as_posix()}")
    for label, page in pages:
        md = md_pages.get(page, "")
        pdf_text = pdf[page - 1].get_text("text") if 1 <= page <= pdf.page_count else ""
        print(f"\n## {label}: page {page}")
        print(f"md_chars={len(md.strip())} pdf_text_chars={len(pdf_text.strip())}")
        print(f"md_flags={','.join(_flags(md)) or 'none'}")
        print("md:")
        print(_excerpt(md, chars))
        if _normalize(md)[:200] != _normalize(pdf_text)[:200]:
            print("pdf_text:")
            print(_excerpt(pdf_text, chars))
    print()


def _sample_pages(final_md: Path, weak_pages: list[int]) -> list[tuple[str, int]]:
    md_pages = _markdown_pages(final_md)
    ordered_pages = sorted(md_pages)
    samples: list[tuple[str, int]] = []
    if ordered_pages:
        samples.append(("first_text", ordered_pages[0]))
    keyword_page = _first_keyword_page(md_pages)
    if keyword_page is not None:
        samples.append(("keyword", keyword_page))
    dense_page = max(ordered_pages, key=lambda page: len(md_pages[page])) if ordered_pages else None
    if dense_page is not None:
        samples.append(("dense", dense_page))
    for page in weak_pages[:2]:
        if page in md_pages:
            samples.append(("weak", page))
    deduped: list[tuple[str, int]] = []
    seen: set[int] = set()
    for label, page in samples:
        if page not in seen:
            deduped.append((label, page))
            seen.add(page)
    return deduped


def _first_keyword_page(md_pages: dict[int, str]) -> int | None:
    for page in sorted(md_pages):
        lowered = md_pages[page].lower()
        if any(keyword in lowered for keyword in KEYWORDS):
            return page
    return None


def _markdown_pages(path: Path) -> dict[int, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    pattern = re.compile(r"<!-- source-page: (\d+) -->\n## Page \1\n\n")
    matches = list(pattern.finditer(text))
    pages: dict[int, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        pages[int(match.group(1))] = text[start:end].strip()
    return pages


def _flags(text: str) -> list[str]:
    flags: list[str] = []
    if "�" in text:
        flags.append("replacement_char")
    if re.search(r"[âÂ]", text):
        flags.append("mojibake")
    if "<table><tr><td></td>" in text:
        flags.append("empty_table")
    if re.search(r"[A-Za-z]{2,}-\n[a-z]{2,}", text):
        flags.append("hyphen_break")
    return flags


def _excerpt(text: str, chars: int) -> str:
    compact = re.sub(r"\n{3,}", "\n\n", text.strip())
    return compact[:chars].rstrip()


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    raise SystemExit(main())
