"""Extract valid EA mode tables from M68K PDF for each instruction.

Finds the "Addressing Mode / Mode / Register" tables in the PDF,
determines which modes are valid (have mode bits) vs invalid (have em-dash),
and updates m68k_instructions.json with structured ea_modes data.

Usage:
    python parse_ea_modes.py [--dump-page N] [--dry-run]
"""

import fitz
import json
import re
import sys
from pathlib import Path

PROJ_ROOT = Path(__file__).resolve().parent.parent
PDF_PATH = PROJ_ROOT / "tmp" / "M68000PM_AD_Rev_1_Programmers_Reference_Manual_1992.pdf"
KB_PATH = PROJ_ROOT / "knowledge" / "m68k_instructions.json"

sys.path.insert(0, str(PROJ_ROOT / "scripts"))
from parse_m68k_instructions import (
    extract_page_spans, spans_to_rows, SECTIONS
)

# Standard M68K EA mode encoding
MODE_MAP = {
    (0, None): "dn",
    (1, None): "an",
    (2, None): "ind",
    (3, None): "postinc",
    (4, None): "predec",
    (5, None): "disp",
    (6, None): "index",
    (7, 0): "absw",
    (7, 1): "absl",
    (7, 2): "pcdisp",
    (7, 3): "pcindex",
    (7, 4): "imm",
}

EA_ALL = ["dn", "an", "ind", "postinc", "predec", "disp", "index",
          "absw", "absl", "pcdisp", "pcindex", "imm"]

EA_ORDER = {m: i for i, m in enumerate(EA_ALL)}


def _ea_sort_key(m):
    return EA_ORDER.get(m, 99)


def parse_3bit(text):
    """Parse a 3-digit binary string to int, or return None."""
    text = text.strip()
    if len(text) == 3 and all(c in '01' for c in text):
        return int(text, 2)
    return None


def find_ea_tables_on_page(rows):
    """Find EA mode tables on a page.

    Returns list of (label, valid_modes) tuples.
    label is the preceding descriptive text (e.g. "source operand",
    "destination operand") or empty string.
    valid_modes is a sorted list of canonical mode names.
    """
    tables = []
    sorted_ys = sorted(rows.keys())

    for idx, y_key in enumerate(sorted_ys):
        row = rows[y_key]
        texts = [t for _, _, t, _, _ in row]
        row_text = " ".join(texts)

        # Detect header row: must have "Addressing Mode" and "Mode" and "Register"
        if "Addressing Mode" not in row_text:
            continue
        if "Mode" not in row_text or "Register" not in row_text:
            continue

        # Find x-positions of "Mode" columns (not the "Addressing Mode" text)
        mode_col_xs = []
        for x, x2, text, _, _ in row:
            if text.strip() == "Mode":
                mode_col_xs.append((x + x2) / 2)

        if not mode_col_xs:
            continue

        # Find x-positions of "Register" columns
        reg_col_xs = []
        for x, x2, text, _, _ in row:
            if text.strip() == "Register":
                reg_col_xs.append((x + x2) / 2)

        # Scan backwards to find the preceding label text
        label = ""
        for prev_idx in range(idx - 1, max(idx - 6, -1), -1):
            prev_y = sorted_ys[prev_idx]
            if y_key - prev_y > 80:
                break
            prev_texts = " ".join(t for _, _, t, _, _ in rows[prev_y]).lower()
            if "source" in prev_texts:
                label = "src"
                break
            if "destination" in prev_texts:
                label = "dst"
                break
            if "effective address" in prev_texts:
                label = "ea"
                break

        # Parse subsequent rows until we hit something non-tabular
        valid_modes = set()
        modes_020 = set()  # modes marked with footnote as 020+ only

        # Define per-column name boundaries for footnote detection.
        # Each EA table has left and (optionally) right side-by-side columns.
        # A footnote * on the addressing mode name applies only to that column.
        # col_name_range[i] = (x_min, x_max) for addressing mode name area
        col_name_ranges = []
        sorted_mcxs = sorted(mode_col_xs)
        for ci, mcx in enumerate(sorted_mcxs):
            x_min = sorted_mcxs[ci - 1] + 50 if ci > 0 else 0
            x_max = mcx
            col_name_ranges.append((x_min, x_max))

        for next_idx in range(idx + 1, min(idx + 25, len(sorted_ys))):
            next_y = sorted_ys[next_idx]
            if next_y - y_key > 300:
                break

            next_row = rows[next_y]
            next_text = " ".join(t for _, _, t, _, _ in next_row)

            # Stop conditions
            if any(kw in next_text for kw in (
                "MC68020", "MC68030", "MC68040",
                "NOTE", "Instruction Format", "Instruction Fields",
            )):
                break
            # Skip footnotes
            if any(kw in next_text for kw in (
                "Can be used", "Word and long", "word and long",
            )):
                continue

            # Check for footnote markers per column
            col_has_footnote = [False] * len(mode_col_xs)
            for span_x, span_x2, span_text, _, _ in next_row:
                if "*" not in span_text:
                    continue
                span_mid = (span_x + span_x2) / 2
                for ci, (nm_min, nm_max) in enumerate(col_name_ranges):
                    if nm_min <= span_mid < nm_max:
                        col_has_footnote[ci] = True
                        break

            # Check for mode values near each Mode column x-position
            for span_x, span_x2, span_text, _, _ in next_row:
                span_center = (span_x + span_x2) / 2
                span_text_s = span_text.strip()

                for col_idx, mode_col_x in enumerate(mode_col_xs):
                    if abs(span_center - mode_col_x) < 25:
                        mode_val = parse_3bit(span_text_s)
                        if mode_val is not None:
                            canonical = None
                            if mode_val < 7:
                                canonical = MODE_MAP.get((mode_val, None))
                            elif mode_val == 7:
                                if col_idx < len(reg_col_xs):
                                    reg_col_x = reg_col_xs[col_idx]
                                    for rx, rx2, rtext, _, _ in next_row:
                                        rc = (rx + rx2) / 2
                                        if abs(rc - reg_col_x) < 25:
                                            reg_val = parse_3bit(rtext.strip())
                                            if reg_val is not None:
                                                canonical = MODE_MAP.get((7, reg_val))
                            if canonical:
                                valid_modes.add(canonical)
                                if col_has_footnote[col_idx]:
                                    modes_020.add(canonical)
                        break

        if valid_modes:
            sorted_modes = sorted(valid_modes,
                                  key=_ea_sort_key)
            sorted_020 = sorted(modes_020,
                                key=_ea_sort_key)
            tables.append((label, sorted_modes, sorted_020))

    return tables


def merge_ea_tables(tables_by_page, pages):
    """Merge EA tables from all pages of an instruction.

    Returns (ea_modes, ea_modes_020) tuple where:
      ea_modes: {"src": [...modes...], "dst": [...modes...]} or {"ea": [...]}
      ea_modes_020: {"src": [...020_modes...], ...} — subset marked as 020+ only

    Handles deduplication when the same operand has tables for
    multiple encoding forms (e.g. DIVS WORD and LONG forms).
    """
    all_tables = []
    for pg in pages:
        if pg in tables_by_page:
            all_tables.extend(tables_by_page[pg])

    if not all_tables:
        return {}, {}

    # Group by label
    by_label = {}
    by_label_020 = {}
    for label, modes, modes_020 in all_tables:
        key = label or "ea"
        if key not in by_label:
            by_label[key] = set(modes)
            by_label_020[key] = set(modes_020)
        else:
            by_label[key] |= set(modes)
            by_label_020[key] |= set(modes_020)

    # Sort modes in canonical order
    result = {}
    result_020 = {}
    for key, modes in by_label.items():
        result[key] = sorted(modes, key=_ea_sort_key)
    for key, modes in by_label_020.items():
        if modes:
            result_020[key] = sorted(modes, key=_ea_sort_key)

    return result, result_020


def dump_page_ea(doc, page_num):
    """Debug: show EA tables found on a specific page."""
    page = doc[page_num - 1]
    spans = extract_page_spans(page)
    rows = spans_to_rows(spans)

    print(f"=== PAGE {page_num} ===")
    tables = find_ea_tables_on_page(rows)
    if not tables:
        print("  No EA tables found.")
    else:
        for i, (label, modes, modes_020) in enumerate(tables):
            print(f"  Table {i+1} [{label or '?'}]: {modes}")
            if modes_020:
                print(f"           020+ only: {modes_020}")
    print()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dump-page", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    doc = fitz.open(str(PDF_PATH))

    if args.dump_page:
        dump_page_ea(doc, args.dump_page)
        return

    # Extract EA tables from all instruction pages
    tables_by_page = {}
    for section_start, section_end in SECTIONS.values():
        for pn in range(section_start, section_end + 1):
            page = doc[pn - 1]
            spans = extract_page_spans(page)
            rows = spans_to_rows(spans)
            tables = find_ea_tables_on_page(rows)
            if tables:
                tables_by_page[pn] = tables

    if args.verbose:
        print("EA tables found by page:")
        for pg in sorted(tables_by_page):
            for i, (label, modes) in enumerate(tables_by_page[pg]):
                print(f"  p{pg} [{label or '?'}]: {modes}")
        print()

    # Load knowledge base
    with open(KB_PATH, encoding="utf-8") as f:
        kb_data = json.load(f)

    # Assign tables to instructions
    for inst in kb_data:
        pages = inst.get("pages", [inst.get("page", 0)])
        ea_modes, ea_modes_020 = merge_ea_tables(tables_by_page, pages)
        inst["ea_modes"] = ea_modes
        if ea_modes_020:
            inst["ea_modes_020"] = ea_modes_020
        elif "ea_modes_020" in inst:
            del inst["ea_modes_020"]

    # Report
    with_ea = sum(1 for inst in kb_data if inst.get("ea_modes"))
    with_020 = sum(1 for inst in kb_data if inst.get("ea_modes_020"))
    print(f"Instructions with EA modes: {with_ea}/{len(kb_data)}")
    print(f"Instructions with 020+ EA modes: {with_020}")

    for inst in kb_data:
        ea = inst.get("ea_modes", {})
        ea020 = inst.get("ea_modes_020", {})
        if ea:
            parts = []
            for role, modes in ea.items():
                extra = ""
                if role in ea020:
                    extra = f" ({len(ea020[role])} are 020+)"
                parts.append(f"{role}={len(modes)} modes{extra}")
            print(f"  {inst['mnemonic']:25s} {', '.join(parts)}")

    if not args.dry_run:
        with open(KB_PATH, "w", encoding="utf-8") as f:
            json.dump(kb_data, f, indent=2, ensure_ascii=False)
        print(f"\nUpdated {KB_PATH}")
    else:
        print("\n(dry run, no changes written)")


if __name__ == "__main__":
    main()
