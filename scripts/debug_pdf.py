#!/usr/bin/env python3
"""Debug PDF text extraction - show positioned text elements per page.

Usage:
    python debug_pdf.py [pdf_path] [page_num]
    python debug_pdf.py                          # defaults: M68K manual, page 107
    python debug_pdf.py resources/foo.pdf 42
"""

import fitz
import sys


def dump_page_positioned(doc, page_num):
    """Show all text elements with their (x, y) positions."""
    page = doc[page_num - 1]
    blocks = page.get_text("dict")["blocks"]

    print(f"=== PAGE {page_num} ===\n")

    # Extract individual text spans with positions
    spans = []
    for block in blocks:
        if block["type"] != 0:  # text block
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                x = span["bbox"][0]
                y = span["bbox"][1]
                text = span["text"].strip()
                font = span["font"]
                size = span["size"]
                if text:
                    spans.append((x, y, text, font, size))

    # Group by approximate y (within 3 units)
    rows: dict[int, list] = {}
    for x, y, text, font, size in spans:
        y_key = round(y / 3) * 3
        rows.setdefault(y_key, []).append((x, text, font, size))

    for y_key in sorted(rows.keys()):
        parts = sorted(rows[y_key], key=lambda e: e[0])
        print(f"  y={y_key:6.0f}:", end="")
        for x, text, font, size in parts:
            print(f"  [x={x:6.1f} {text!r}]", end="")
        print()


def dump_page_rawdict(doc, page_num):
    """Show raw dict output for a page."""
    page = doc[page_num - 1]
    blocks = page.get_text("rawdict")["blocks"]

    print(f"\n=== PAGE {page_num} RAW BLOCKS ===\n")
    for bi, block in enumerate(blocks):
        if block["type"] != 0:
            continue
        for li, line in enumerate(block["lines"]):
            for si, span in enumerate(line["spans"]):
                text = span["text"].strip()
                if text:
                    bbox = span["bbox"]
                    print(f"  b{bi} l{li} s{si}  ({bbox[0]:6.1f}, {bbox[1]:6.1f}) - ({bbox[2]:6.1f}, {bbox[3]:6.1f})  {text!r}")


def main():
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "resources/M68000PM_AD_Rev_1_Programmers_Reference_Manual_1992.pdf"
    page_num = int(sys.argv[2]) if len(sys.argv) > 2 else 107

    sys.stdout.reconfigure(encoding="utf-8")
    doc = fitz.open(pdf_path)
    print(f"PDF: {pdf_path} ({len(doc)} pages)")

    dump_page_positioned(doc, page_num)
    dump_page_rawdict(doc, page_num)


if __name__ == "__main__":
    main()
