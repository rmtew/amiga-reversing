#!/usr/bin/env python3
"""Test instruction header detection on specific pages."""

import fitz, sys
sys.path.insert(0, "scripts")
from parse_m68k_instructions import extract_page_spans, spans_to_rows, is_instruction_start, rows_to_plain_text

sys.stdout.reconfigure(encoding="utf-8")
doc = fitz.open("tmp/M68000PM_AD_Rev_1_Programmers_Reference_Manual_1992.pdf")

for pn in [106, 107, 108, 109, 110, 220]:
    page = doc[pn - 1]
    spans = extract_page_spans(page)
    rows = spans_to_rows(spans)
    text = rows_to_plain_text(rows)

    # Show first few content lines
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    content = []
    for l in lines:
        if "MOTOROLA" in l or "REFERENCE MANUAL" in l:
            continue
        if l in ("Integer Instructions", "Floating Point Instructions"):
            continue
        import re
        if re.match(r"^\d+-\d+$", l):
            continue
        content.append(l)

    header = is_instruction_start(rows)
    print(f"Page {pn}: header={header}")
    print(f"  First 3 content lines: {content[:3]}")
    if content:
        import re
        print(f"  Regex test on '{content[0]}': {bool(re.match(r'^[A-Z][A-Z0-9/]{1,10}$', content[0]))}")
    print()
