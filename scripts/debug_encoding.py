#!/usr/bin/env py.exe
"""Debug encoding extraction on a specific page."""

import fitz, sys
from parse_m68k import extract_page_spans, spans_to_rows, BitField

sys.stdout.reconfigure(encoding="utf-8")
doc = fitz.open("resources/M68000PM_AD_Rev_1_Programmers_Reference_Manual_1992.pdf")
page_num = int(sys.argv[1]) if len(sys.argv) > 1 else 220

page = doc[page_num - 1]
spans = extract_page_spans(page)
rows = spans_to_rows(spans)
sorted_ys = sorted(rows.keys())

# Find the bit header row
for idx, y_key in enumerate(sorted_ys):
    row = rows[y_key]
    texts = [t for _, _, t, _, _ in row]
    if "15" not in texts or "0" not in texts:
        continue
    bit_numbers = set()
    for t in texts:
        try:
            n = int(t)
            if 0 <= n <= 15:
                bit_numbers.add(n)
        except ValueError:
            pass
    if len(bit_numbers) < 14:
        continue

    print(f"Bit header at y={y_key}")

    # Build x->bit mapping
    x_to_bit = {}
    for x, x2, t, _, _ in row:
        try:
            n = int(t)
            if 0 <= n <= 15:
                x_to_bit[x] = n
        except ValueError:
            pass

    bit_x = {bit: x for x, bit in x_to_bit.items()}
    col_xs = sorted(bit_x.values())
    avg_spacing = (col_xs[-1] - col_xs[0]) / (len(col_xs) - 1)
    half_col = avg_spacing / 2

    print(f"  avg_spacing={avg_spacing:.1f}, half_col={half_col:.1f}")
    print(f"  Bit positions: {dict(sorted(bit_x.items(), reverse=True))}")

    # Collect value rows
    min_col_x = min(x_to_bit.keys()) - 15
    merged = []
    for ni in range(idx + 1, min(idx + 6, len(sorted_ys))):
        ny = sorted_ys[ni]
        if ny - y_key > 45:
            break
        items = [(x, x2, t, f, s) for x, x2, t, f, s in rows[ny] if x >= min_col_x]
        if items:
            merged.extend(items)
            print(f"\n  Row y={ny}:")
            for x, x2, t, f, s in items:
                print(f"    x={x:6.1f}-{x2:6.1f} {t!r}")

    # Sort: fixed bits first, then narrow spans first
    sorted_merged = sorted(merged, key=lambda e: (0 if e[2] in ("0","1") else 1, e[1]-e[0]))

    print(f"\n  Processing order:")
    used_bits = set()
    fields = []
    for vx, vx2, vtext, _, _ in sorted_merged:
        if vtext in ("0", "1"):
            best_bit = None
            best_dist = float("inf")
            for bn, cx in bit_x.items():
                dist = abs(vx - cx)
                if dist < best_dist and bn not in used_bits:
                    best_dist = dist
                    best_bit = bn
            if best_bit is not None and best_dist < half_col * 1.5:
                fields.append(BitField(name=vtext, bit_hi=best_bit, bit_lo=best_bit, width=1))
                used_bits.add(best_bit)
                print(f"    '{vtext}' x={vx:.1f} -> bit {best_bit} (dist={best_dist:.1f})")
            else:
                print(f"    '{vtext}' x={vx:.1f} -> FAILED (best_bit={best_bit}, dist={best_dist:.1f})")
        else:
            matching = []
            for bn, cx in bit_x.items():
                if bn not in used_bits and cx >= vx - half_col and cx <= vx2 + half_col * 0.5:
                    matching.append(bn)
            if matching:
                hi, lo = max(matching), min(matching)
                actual = set(matching) - used_bits
                if actual:
                    hi, lo = max(actual), min(actual)
                    w = hi - lo + 1
                    fields.append(BitField(name=vtext, bit_hi=hi, bit_lo=lo, width=w))
                    for b in range(lo, hi + 1):
                        used_bits.add(b)
                    print(f"    '{vtext}' x={vx:.1f}-{vx2:.1f} -> bits {hi}-{lo} ({w}b) matching={sorted(matching, reverse=True)}")
                else:
                    print(f"    '{vtext}' x={vx:.1f}-{vx2:.1f} -> FAILED (all matching bits used)")
            else:
                print(f"    '{vtext}' x={vx:.1f}-{vx2:.1f} -> NO MATCH (checked range {vx-half_col:.1f} to {vx2+half_col*0.5:.1f})")

    total = sum(f.width for f in fields)
    print(f"\n  Result: {len(fields)} fields, {total} bits, unused: {set(range(16)) - used_bits}")
    for f in sorted(fields, key=lambda f: -f.bit_hi):
        print(f"    bits {f.bit_hi:2d}-{f.bit_lo:2d} ({f.width:2d}b): {f.name}")
