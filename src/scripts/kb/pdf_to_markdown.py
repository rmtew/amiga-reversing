"""Prepare PDF source material as Markdown-like text for KB extraction.

This is a source-prep tool, not a formal KB parser.  It preserves page
provenance and fails clearly when a PDF needs OCR before text extraction.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

import fitz  # type: ignore[import-untyped]

LIGATURES = {"\ufb01": "fi", "\ufb02": "fl", "\ufb00": "ff", "\ufb03": "ffi", "\ufb04": "ffl"}


@dataclass(frozen=True)
class PdfProbe:
    path: str
    page_count: int
    text_pages: int
    empty_text_pages: int
    low_text_pages: list[int]
    image_blocks: int
    needs_ocr: bool


class OcrRequiredError(RuntimeError):
    pass


def probe_pdf(path: Path, *, min_page_chars: int = 40) -> PdfProbe:
    doc = fitz.open(path)
    text_pages = 0
    empty_text_pages = 0
    low_text_pages: list[int] = []
    image_blocks = 0

    for page_index, page in enumerate(doc):
        text_len = len(page.get_text("text").strip())
        if text_len > 0:
            text_pages += 1
        else:
            empty_text_pages += 1
        if text_len < min_page_chars:
            low_text_pages.append(page_index + 1)
        blocks = cast(list[dict[str, object]], page.get_text("dict").get("blocks", []))
        image_blocks += sum(1 for block in blocks if block.get("type") == 1)

    return PdfProbe(
        path=path.as_posix(),
        page_count=doc.page_count,
        text_pages=text_pages,
        empty_text_pages=empty_text_pages,
        low_text_pages=low_text_pages,
        image_blocks=image_blocks,
        needs_ocr=text_pages == 0,
    )


def pdf_to_markdown(path: Path, *, min_page_chars: int = 40, pages: list[int] | None = None) -> str:
    probe = probe_pdf(path, min_page_chars=min_page_chars)
    if probe.needs_ocr:
        raise OcrRequiredError(
            f"{path} has no extractable text pages; OCR it first, then convert the OCR PDF to Markdown."
        )

    doc = fitz.open(path)
    page_numbers = pages or list(range(1, doc.page_count + 1))
    lines = [
        f"<!-- source-pdf: {path.as_posix()} -->",
        f"<!-- source-pages: {doc.page_count} -->",
        "",
    ]
    for page_number in page_numbers:
        if page_number < 1 or page_number > doc.page_count:
            raise ValueError(f"page out of range: {page_number}")
        text = _normalize_text(doc[page_number - 1].get_text("text"))
        if not text:
            continue
        lines.extend(
            [
                f"<!-- source-page: {page_number} -->",
                f"## Page {page_number}",
                "",
                text,
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def parse_pages(value: str) -> list[int]:
    pages: list[int] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            start = int(start_text)
            end = int(end_text)
            if end < start:
                raise ValueError(f"invalid page range: {part}")
            pages.extend(range(start, end + 1))
        else:
            pages.append(int(part))
    return list(dict.fromkeys(pages))


def _normalize_text(text: str) -> str:
    for src, dst in LIGATURES.items():
        text = text.replace(src, dst)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert text-layer PDFs to page-cited Markdown.")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output", "-o", type=Path)
    parser.add_argument("--probe", action="store_true", help="Print text/OCR suitability report as JSON.")
    parser.add_argument("--min-page-chars", type=int, default=40)
    parser.add_argument("--pages", help="Comma-separated pages/ranges, e.g. 1,3-5.")
    args = parser.parse_args(argv)

    try:
        if args.probe:
            print(json.dumps(asdict(probe_pdf(args.pdf, min_page_chars=args.min_page_chars)), indent=2))
            return 0
        markdown = pdf_to_markdown(
            args.pdf,
            min_page_chars=args.min_page_chars,
            pages=parse_pages(args.pages) if args.pages else None,
        )
    except OcrRequiredError as exc:
        print(f"OCR required: {exc}", file=sys.stderr)
        print("Suggested first pass: ocrmypdf --deskew --rotate-pages input.pdf output.ocr.pdf", file=sys.stderr)
        return 2

    if args.output:
        args.output.write_text(markdown, encoding="utf-8", newline="\n")
    else:
        print(markdown, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
