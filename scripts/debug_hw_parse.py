#!/usr/bin/env py.exe
"""Debug hardware manual bit field parsing."""

import sys
sys.path.insert(0, "scripts")
sys.stdout.reconfigure(encoding="utf-8")

from parse_hw_manual import parse_full_manual, parse_register_detail

# Check what detail pages get assigned
import os
from parse_hw_manual import parse_address_order_summary

guide_dir = "resources/Hardware_Manual_guide"
registers = parse_address_order_summary(guide_dir)

# Show first 20 registers with their detail pages
print("=== Register -> Detail Page mapping (first 30) ===")
for reg in registers[:30]:
    exists = os.path.exists(os.path.join(guide_dir, reg.detail_page)) if reg.detail_page else False
    print(f"  {reg.name:<12} -> {reg.detail_page!r:<25} exists={exists}")

# Check a specific detail page
print("\n=== Direct parse of node002F.html ===")
bits, notes = parse_register_detail(guide_dir, "node002F.html")
print(f"  Got {len(bits)} bits")

# Check what pages have bits
detail_pages = {}
for reg in registers:
    if reg.detail_page and reg.detail_page not in detail_pages:
        detail_pages[reg.detail_page] = None

total_with_bits = 0
for page in detail_pages:
    bits, notes = parse_register_detail(guide_dir, page)
    detail_pages[page] = len(bits)
    if bits:
        total_with_bits += 1

print(f"\n=== {total_with_bits}/{len(detail_pages)} detail pages have bit defs ===")
for page, count in sorted(detail_pages.items()):
    if count:
        print(f"  {page}: {count} bits")
