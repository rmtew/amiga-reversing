#!/usr/bin/env py.exe
"""Find register detail pages that have bit tables we're not parsing."""

import os
import re
import sys
from html import unescape

sys.stdout.reconfigure(encoding="utf-8")

guide_dir = "resources/Hardware_Manual_guide"

sys.path.insert(0, "scripts")
from parse_hw_manual import parse_register_detail, extract_body, strip_html

# Check ALL HTML files for bit-table-like patterns
files = sorted(f for f in os.listdir(guide_dir) if f.endswith(".html"))

parsed_ok = 0
has_bits_unparsed = 0

for fname in files:
    path = os.path.join(guide_dir, fname)
    with open(path, encoding="utf-8", errors="replace") as f:
        html = f.read()

    body = extract_body(html)
    if not body:
        continue

    text = strip_html(body)

    # Check if this page has a BIT# header
    has_bit_header = bool(re.search(r'BIT#?\s+', text))
    # Also check for patterns like "15    SETCLR" or "00    AUDOEN"
    has_bit_lines = len(re.findall(r'^\s+\d{1,2}\s+\w+', text, re.MULTILINE)) >= 5

    if not has_bit_header and not has_bit_lines:
        continue

    # Try parsing
    bits, _ = parse_register_detail(guide_dir, fname)

    # Get page title
    title_m = re.search(r'<title>(.*?)</title>', html)
    title = strip_html(title_m.group(1)) if title_m else fname

    if bits:
        parsed_ok += 1
    else:
        has_bits_unparsed += 1
        # Show what the bit table looks like
        print(f"\n=== {fname}: {title} ===")
        print(f"  has_bit_header={has_bit_header}, has_bit_lines={has_bit_lines}")
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if re.search(r'BIT#|^\s+\d{1,2}\s+\w{2,}', line):
                # Show context
                start = max(0, i - 1)
                end = min(len(lines), i + 8)
                for j in range(start, end):
                    print(f"  {j:3d}: {lines[j][:100]}")
                print("  ...")
                break

print(f"\n\nSummary: {parsed_ok} pages parsed OK, {has_bits_unparsed} pages with unparsed bit tables")

# Also check for CIA-related pages
print("\n=== CIA-related pages ===")
for fname in files:
    path = os.path.join(guide_dir, fname)
    with open(path, encoding="utf-8", errors="replace") as f:
        html = f.read()
    if "CIA" in html or "8520" in html:
        title_m = re.search(r'<title>(.*?)</title>', html)
        title = strip_html(title_m.group(1)) if title_m else fname
        if "8520" in title or "CIA" in title:
            print(f"  {fname}: {title}")
