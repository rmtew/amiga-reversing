#!/usr/bin/env py.exe
"""Verify the hardware register JSON output."""

import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

with open("knowledge/amiga_hw_registers.json", encoding="utf-8") as f:
    data = json.load(f)

regs = data["registers"]
with_bits = sum(1 for r in regs if r.get("bits"))
print(f"Registers: {len(regs)}")
print(f"With bits: {with_bits}")
print(f"Chapters: {len(data['chapters'])}")

# Show DMACON as example
for r in regs:
    if r["name"] == "DMACON":
        addr = int(r["address"], 16)
        print(f"\nExample - {r['name']} (${addr:03X}):")
        print(f"  68K addr: {r['address_68k']}")
        print(f"  Access: {r['access']}, Chip: {r['chip']}")
        print(f"  Function: {r['function']}")
        for b in r.get("bits", [])[:5]:
            print(f"  bit {b['bit']:2d}: {b['name']:<10s} {b['description'][:60]}")
        if len(r.get("bits", [])) > 5:
            print(f"  ... ({len(r['bits'])} total bits)")
        break

# Show INTENA
for r in regs:
    if r["name"] == "INTENA":
        print(f"\nINTENA (${int(r['address'], 16):03X}): {r['function']}")
        for b in r.get("bits", []):
            print(f"  bit {b['bit']:2d}: {b['name']:<10s} {b['description'][:60]}")
        break

# Count unique detail pages that have bits
pages_with_bits = set()
for r in regs:
    if r.get("bits"):
        pages_with_bits.add(r["name"])
print(f"\nRegisters with full bit defs: {sorted(pages_with_bits)}")
