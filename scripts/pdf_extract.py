#!/usr/bin/env python3
"""
PDF text extraction tool.

Usage:
    python pdf_extract.py <pdf_path> toc                    # Show table of contents
    python pdf_extract.py <pdf_path> pages <start> [end]    # Extract page range
    python pdf_extract.py <pdf_path> search <term>          # Search for text, show matching pages
    python pdf_extract.py <pdf_path> info                   # Basic PDF info
"""

import fitz
import sys
import argparse


def cmd_info(doc, args):
    print(f"Pages: {len(doc)}")
    print(f"TOC entries: {len(doc.get_toc())}")
    meta = doc.metadata
    for k, v in meta.items():
        if v:
            print(f"{k}: {v}")


def cmd_toc(doc, args):
    toc = doc.get_toc()
    if not toc:
        print("No table of contents found.")
        return
    for level, title, page in toc:
        indent = "  " * (level - 1)
        print(f"{indent}{title} (p{page})")
    print(f"\n{len(toc)} entries")


def cmd_pages(doc, args):
    start = args.start
    end = args.end or start
    for pn in range(start, end + 1):
        if pn < 1 or pn > len(doc):
            print(f"Page {pn} out of range (1-{len(doc)})")
            continue
        page = doc[pn - 1]
        text = page.get_text()
        print(f"=== PAGE {pn} ===")
        print(text)
        print()


def cmd_search(doc, args):
    term = args.term.lower()
    matches = []
    for pn in range(len(doc)):
        page = doc[pn]
        text = page.get_text()
        if term in text.lower():
            # Show first matching line for context
            for line in text.split("\n"):
                if term in line.lower():
                    context = line.strip()[:120]
                    matches.append((pn + 1, context))
                    break
    for page, context in matches:
        print(f"  p{page}: {context}")
    print(f"\n{len(matches)} pages match '{args.term}'")


def main():
    parser = argparse.ArgumentParser(description="PDF text extraction tool")
    parser.add_argument("pdf", help="Path to PDF file")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("info", help="Show PDF info")
    sub.add_parser("toc", help="Show table of contents")

    p_pages = sub.add_parser("pages", help="Extract page range")
    p_pages.add_argument("start", type=int, help="Start page number")
    p_pages.add_argument("end", type=int, nargs="?", help="End page number (default: same as start)")

    p_search = sub.add_parser("search", help="Search for text")
    p_search.add_argument("term", help="Search term")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    sys.stdout.reconfigure(encoding="utf-8")
    doc = fitz.open(args.pdf)

    cmds = {"info": cmd_info, "toc": cmd_toc, "pages": cmd_pages, "search": cmd_search}
    cmds[args.command](doc, args)


if __name__ == "__main__":
    main()
