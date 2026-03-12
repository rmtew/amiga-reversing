#!/usr/bin/env py.exe
"""Parse M68000 Programmer's Reference Manual PDF into structured instruction JSON.

Single pipeline that extracts all instruction data from the PDF:
  Phase 1: Bit encodings, metadata, syntax, condition codes
  Phase 2: Effective addressing mode tables
  Phase 3: Syntax pattern parsing into structured forms
  Phase 4: Constraint derivation (immediates, CC params, sizes, etc.)

Deletes and regenerates m68k_instructions.json from scratch each run.

Usage:
    python parse_m68k.py <pdf_path> [--output json|md|summary]
    python parse_m68k.py <pdf_path> --dump-page 107
    python parse_m68k.py <pdf_path> --sections 4,6
    python parse_m68k.py <pdf_path> --dry-run
"""

import fitz
import re, json, sys, argparse
from dataclasses import dataclass, field, asdict
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════════
# Shared constants
# ═══════════════════════════════════════════════════════════════════════════════

PROJ_ROOT = Path(__file__).resolve().parent.parent
KB_PATH = PROJ_ROOT / "knowledge" / "m68k_instructions.json"

# Page ranges for each section of the manual
SECTIONS = {
    4: (105, 302),   # Integer Instructions
    6: (455, 540),   # Supervisor (Privileged) Instructions
}

# Common PDF ligatures to normalize
LIGATURES = {"\ufb01": "fi", "\ufb02": "fl", "\ufb00": "ff", "\ufb03": "ffi", "\ufb04": "ffl"}

# Standard M68K EA mode encoding (Motorola-defined)
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

EA_ALL = list(dict.fromkeys(MODE_MAP[k] for k in sorted(MODE_MAP.keys())))
EA_ORDER = {m: i for i, m in enumerate(EA_ALL)}

# Populated at runtime by extract_standard_cc_table() from PDF Table 3-19
CC_TABLE: dict[int, str] = {}

# Processor family hierarchy (ordered by capability, ascending)
CPU_HIERARCHY = {
    "order": ["68000", "68010", "68020", "68030", "68040", "68060"],
    "aliases": {
        "68020up": "68020",
        "cf":      "68060",
        "cfpu":    "68060",
        "cpu32":   "68020",
    },
}


def _kb_condition_codes() -> list[str]:
    """Ordered architectural condition-code mnemonics."""
    return [CC_TABLE[i] for i in sorted(CC_TABLE.keys())]


def extract_ea_extension_formats(doc) -> list[dict]:
    """Extract Brief Extension Word field layout from PDF page 43.

    Page 43 has three encoding tables: single EA operation word, Brief Extension
    Word, and Full Extension Word.  We extract the second one (Brief) and return
    its named variable fields as [{name, bit_hi, bit_lo}, ...].
    """
    page = doc[42]  # page 43 (0-indexed)
    spans = extract_page_spans(page)
    rows = spans_to_rows(spans)
    encs = find_encoding_tables(rows, summary_mode=True)

    if len(encs) < 2:
        raise RuntimeError(
            f"Expected >=2 encoding tables on page 43, found {len(encs)}"
        )

    brief_fields = encs[1]  # second table = Brief Extension Word
    result = []
    for f in brief_fields:
        if f.name not in ("0", "1"):  # skip fixed bits
            result.append({
                "name": f.name,
                "bit_hi": f.bit_hi,
                "bit_lo": f.bit_lo,
            })
    return result


def extract_movem_regmask_tables(doc) -> dict[str, list[str]]:
    """Extract MOVEM register-to-bit-position mappings from PDF page 234.

    Page 234 has two 16-column tables mapping bit positions (15..0) to register
    names.  The first (normal) table is for postincrement/control modes, the
    second (predecrement) table has reversed bit order.

    Returns {"normal": [16 reg names], "predecrement": [16 reg names]} where
    index = bit position, value = lowercase register name.
    """
    page = doc[233]  # page 234 (0-indexed)
    spans = extract_page_spans(page)
    rows = spans_to_rows(spans)

    # Find rows that are bit number headers (contain "15" and "0" with 16 entries)
    bit_header_ys = []
    for y_key in sorted(rows.keys()):
        texts = [item[2] for item in rows[y_key]]
        if "15" in texts and "0" in texts and len(texts) == 16:
            bit_header_ys.append(y_key)

    if len(bit_header_ys) != 2:
        raise RuntimeError(
            f"Expected 2 bit header rows on page 234, found {len(bit_header_ys)}"
        )

    # Determine which is normal vs predecrement by checking preceding text
    # "postincrement" appears before the first table, "predecrement" before the second
    # We rely on ordering: first header = normal, second = predecrement
    tables = {}
    labels = ["normal", "predecrement"]

    for idx, header_y in enumerate(bit_header_ys):
        # Build x -> bit_number mapping from header row
        header_items = rows[header_y]
        x_to_bit = {}
        for x, x2, text, font, size in header_items:
            mid_x = (x + x2) / 2
            x_to_bit[mid_x] = int(text)

        # Find the next row after this header (register names)
        next_y = None
        for y_key in sorted(rows.keys()):
            if y_key > header_y:
                next_y = y_key
                break

        if next_y is None:
            raise RuntimeError(f"No register row found after bit header at y={header_y}")

        reg_items = rows[next_y]
        if len(reg_items) != 16:
            raise RuntimeError(
                f"Expected 16 register entries at y={next_y}, found {len(reg_items)}"
            )

        # Map each register to its bit position by x-coordinate proximity
        bit_to_reg = {}
        header_xs = sorted(x_to_bit.keys())
        for x, x2, text, font, size in reg_items:
            mid_x = (x + x2) / 2
            # Find closest header x
            closest_x = min(header_xs, key=lambda hx: abs(hx - mid_x))
            bit_pos = x_to_bit[closest_x]
            bit_to_reg[bit_pos] = text.lower()

        # Build list indexed by bit position (0..15)
        tables[labels[idx]] = [bit_to_reg[i] for i in range(16)]

    return tables


def _as_kb_payload(kb_data: list[dict], pmmu_cc: list[str],
                   ea_brief_ext_word: list[dict] | None = None,
                   movem_reg_masks: dict[str, list[str]] | None = None,
                   nop_opword: int | None = None) -> dict:
    meta = {
        "condition_codes": _kb_condition_codes(),
        "pmmu_condition_codes": pmmu_cc,
        "cpu_hierarchy": CPU_HIERARCHY,
    }
    if ea_brief_ext_word is not None:
        meta["ea_brief_ext_word"] = ea_brief_ext_word
    if movem_reg_masks is not None:
        meta["movem_reg_masks"] = movem_reg_masks
    if nop_opword is not None:
        meta["nop_opword"] = nop_opword
    return {
        "_meta": meta,
        "instructions": kb_data,
    }


def extract_pmmu_cc_table(doc, page_ranges) -> list[str]:
    """Extract MC68851 PMMU condition codes from the PBcc instruction page.

    The table appears in a two-column layout with 6-bit binary field values
    (e.g. '000000') mapped to 2-letter specifiers (e.g. 'BS').
    Returns an ordered list of 16 lowercase mnemonics indexed by field value.
    """
    for start_page, end_page in page_ranges:
        for pn in range(start_page, end_page + 1):
            page = doc[pn - 1]
            spans = extract_page_spans(page)
            rows = spans_to_rows(spans)
            result = _parse_pmmu_cc_table(rows)
            if result:
                return result
    return []


def _parse_pmmu_cc_table(rows) -> list[str]:
    """Find and parse the PMMU CC table on a page.

    Identifies the table by its header ('Specifier' + 'Condition Field'),
    then extracts (field_value, mnemonic) pairs from data rows containing
    6-digit binary strings.
    """
    sorted_ys = sorted(rows.keys())

    for idx, y_key in enumerate(sorted_ys):
        row_texts = " ".join(t for _, _, t, _, _ in rows[y_key])
        if "Specifier" not in row_texts or "Condition Field" not in row_texts:
            continue

        # Found the table header — parse subsequent data rows
        codes: dict[int, str] = {}

        for next_idx in range(idx + 1, min(idx + 25, len(sorted_ys))):
            next_y = sorted_ys[next_idx]
            next_row = rows[next_y]

            # Find all 6-digit binary strings in this row
            binary_entries = [
                (x, int(text, 2))
                for x, _, text, _, _ in next_row
                if len(text) == 6 and all(c in "01" for c in text)
            ]

            if not binary_entries:
                if codes:
                    break  # end of table
                continue

            # For each binary entry find the nearest 2-letter uppercase
            # specifier to its left (specifier precedes its field value)
            for bin_x, field_val in binary_entries:
                best_spec = None
                best_dist = float("inf")
                for x, _, text, _, _ in next_row:
                    if (len(text) == 2 and text.isupper() and text.isalpha()
                            and x < bin_x):
                        dist = bin_x - x
                        if dist < best_dist:
                            best_dist = dist
                            best_spec = text
                if best_spec and best_dist < 250:
                    codes[field_val] = best_spec.lower()

        if len(codes) >= 16:
            return [codes[i] for i in range(16)]

    return []


def extract_standard_cc_table(doc) -> dict[int, str]:
    """Extract standard M68K condition codes from PDF Table 3-19.

    Searches pages near the instruction set summary for 'Conditional Tests'
    table header, then parses rows with 4-bit binary encodings and mnemonic
    specifiers.  Returns {encoding_int: mnemonic_lowercase} for all 16 CCs.
    """
    # Table 3-19 is in Section 3 (Instruction Set Summary), typically page ~90
    for pn in range(70, 120):
        page = doc[pn]
        text = page.get_text()
        if "Conditional Tests" not in text:
            continue

        spans = extract_page_spans(page)
        rows = spans_to_rows(spans)
        sorted_ys = sorted(rows.keys())

        for idx, y_key in enumerate(sorted_ys):
            row_texts = " ".join(t for _, _, t, _, _ in rows[y_key])
            if "Mnemonic" not in row_texts or "Encoding" not in row_texts:
                continue

            # Found the table header — parse subsequent data rows
            codes: dict[int, str] = {}
            for next_idx in range(idx + 1, min(idx + 25, len(sorted_ys))):
                next_y = sorted_ys[next_idx]
                next_row = rows[next_y]

                # Find 4-digit binary encoding in this row
                binary_entries = [
                    (x, int(text, 2))
                    for x, _, text, _, _ in next_row
                    if len(text) == 4 and all(c in "01" for c in text)
                ]
                if not binary_entries:
                    # Stray formula symbols (Λ) can create rows without
                    # binary entries.  Only break when all 16 codes found,
                    # or when we encounter a long text row (next table/notes).
                    row_text = " ".join(t for _, _, t, _, _ in next_row)
                    if len(codes) >= 16 or (codes and len(row_text) > 40):
                        break
                    continue

                # Find the mnemonic — leftmost text in the row, stripping
                # asterisk markers and parenthetical aliases like "CC(HI)"
                mnemonic = None
                for _, _, text, _, _ in next_row:
                    if len(text) == 4 and all(c in "01" for c in text):
                        continue  # skip encoding
                    stripped = text.rstrip("*").split("(")[0].strip()
                    if stripped and stripped[0].isalpha():
                        mnemonic = stripped.lower()
                        break

                if mnemonic and binary_entries:
                    enc_val = binary_entries[0][1]
                    codes[enc_val] = mnemonic

            if len(codes) == 16:
                return codes

    return {}


def normalize_text(text):
    """Replace PDF ligatures with ASCII equivalents."""
    for lig, repl in LIGATURES.items():
        text = text.replace(lig, repl)
    return text


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 1: PDF text extraction and instruction parsing
# ═══════════════════════════════════════════════════════════════════════════════

def extract_page_spans(page) -> list[tuple[float, float, float, str, str, float]]:
    """Extract (x, y, x2, text, font, size) from a page using PyMuPDF dict mode."""
    spans = []
    for block in page.get_text("dict")["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text = normalize_text(span["text"].strip())
                if text:
                    spans.append((
                        span["bbox"][0],   # x (left)
                        span["bbox"][1],   # y (top)
                        span["bbox"][2],   # x2 (right)
                        text,
                        span["font"],
                        span["size"],
                    ))
    return spans


def spans_to_rows(spans, y_tolerance=3):
    """Group spans into rows by approximate y-coordinate."""
    rows: dict[int, list[tuple[float, float, str, str, float]]] = {}
    for x, y, x2, text, font, size in spans:
        y_key = round(y / y_tolerance) * y_tolerance
        rows.setdefault(y_key, []).append((x, x2, text, font, size))
    for y_key in rows:
        rows[y_key].sort(key=lambda e: e[0])
    return rows


def rows_to_plain_text(rows):
    """Convert rows dict to plain text string."""
    lines = []
    for y_key in sorted(rows.keys()):
        parts = [text for _, _, text, _, _ in rows[y_key]]
        lines.append(" ".join(parts))
    return "\n".join(lines)


# --- Encoding table extraction ---

@dataclass
class BitField:
    name: str
    bit_hi: int
    bit_lo: int
    width: int
    bbox_width: float = 0.0  # original text bbox width for tie-breaking


def find_encoding_tables(rows, summary_mode=False) -> list[list[BitField]]:
    """Find bit encoding tables using positioned text rows.

    Only accepts encoding tables preceded by "Instruction Format:" or a
    sub-format label (e.g. "Register Rotate:"), filtering out false positives
    from addressing mode tables and explanatory diagrams.

    In summary_mode, the "Instruction Format:" filter is bypassed — the summary
    section (Section 8) uses bare instruction names before encoding tables.
    """
    encodings = []
    sorted_ys = sorted(rows.keys())

    for idx, y_key in enumerate(sorted_ys):
        row = rows[y_key]
        texts = [t for _, _, t, _, _ in row]

        # Check for bit number header: must have "15" and "0" and most in between
        bit_numbers = set()
        for t in texts:
            try:
                n = int(t)
                if 0 <= n <= 15:
                    bit_numbers.add(n)
            except ValueError:
                pass

        # Handle split "15" — some pages render it as separate "1" and "5" spans
        has_15 = 15 in bit_numbers
        if not has_15 and 5 in bit_numbers and 0 in bit_numbers and len(bit_numbers) >= 14:
            row_by_x = sorted(row, key=lambda e: e[0])
            leftmost = row_by_x[0]
            if leftmost[2].strip() == "5" and 14 in bit_numbers:
                bit_numbers.add(15)
                has_15 = True

        if not has_15 or 0 not in bit_numbers or len(bit_numbers) < 14:
            continue

        # === False-positive filter ===
        if summary_mode:
            # Summary section only has encoding tables — no EA tables or
            # explanatory diagrams, so skip the filter entirely.
            is_real_encoding = True
        else:
            is_real_encoding = False
            for prev_idx in range(idx - 1, max(idx - 8, -1), -1):
                prev_y = sorted_ys[prev_idx]
                if y_key - prev_y > 80:
                    break
                prev_texts = " ".join(t for _, _, t, _, _ in rows[prev_y])
                if "Instruction Format" in prev_texts:
                    is_real_encoding = True
                    break
                if re.search(r"^(Register|Memory)\s+\w+:?$", prev_texts.strip()):
                    is_real_encoding = True
                    break
                if any(kw in prev_texts for kw in
                       ("Source:", "Destination:", "Resulting", "Concatenated",
                        "Add Adjustment", "Addressing Mode", "Effective Address field")):
                    break

        if not is_real_encoding:
            continue

        # Build x -> bit number mapping
        x_to_bit: dict[float, int] = {}
        leftmost_5_x = None
        for x, x2, t, _, _ in row:
            try:
                n = int(t)
                if 0 <= n <= 15:
                    x_to_bit[x] = n
                    if n == 5 and leftmost_5_x is None:
                        leftmost_5_x = x
            except ValueError:
                pass

        # If "15" was split, remap the leftmost "5" to be bit 15
        if has_15 and 15 not in x_to_bit.values() and leftmost_5_x is not None:
            min_x = min(x_to_bit.keys())
            if leftmost_5_x == min_x:
                x_to_bit[leftmost_5_x] = 15

        # Collect value rows below the header, splitting each 16-bit word into its
        # own cluster.  A new cluster begins whenever a row places a "0" or "1"
        # near the bit-15 column — that signals the start of a fresh encoding word
        # (opword, extension word, etc.).
        min_col_x = min(x_to_bit.keys()) - 15
        header_y = y_key

        col_xs = sorted(x_to_bit.keys())
        bit_x = {bn: cx for cx, bn in x_to_bit.items()}
        bit_15_x = bit_x.get(15)
        half_col = ((col_xs[-1] - col_xs[0]) / (len(col_xs) - 1) / 2
                    if len(col_xs) >= 2 else 15.0)

        current_cluster: list = []
        all_clusters: list[list] = []
        first_cluster_started = False

        for next_idx in range(idx + 1, min(idx + 6, len(sorted_ys))):
            next_y = sorted_ys[next_idx]
            if next_y - header_y > 45:
                break

            row_items = rows[next_y]
            row_text = " ".join(t for _, _, t, _, _ in row_items)
            if "Instruction Fields" in row_text:
                break

            enc_items = [(x, x2, t, f, s, next_y) for x, x2, t, f, s in row_items
                        if x >= min_col_x]
            enc_items = [e for e in enc_items
                        if e[2] in ("0", "1") or len(e[2].split()) <= 2]
            if not enc_items:
                continue

            # Start a new cluster when the leftmost item in the row is near the
            # bit-15 column.  This detects both opword rows (fixed 0/1 at bit 15)
            # and extension word rows that start with a named field at bit 15 (e.g.
            # MOVES: A/D at bit 15, CAS: 0 at bit 15).
            # Label-only rows (e.g. "MODE  REGISTER") have their leftmost item far
            # to the right and are therefore excluded.
            min_item_x = min(e[0] for e in enc_items)
            starts_new_word = (
                bit_15_x is not None
                and min_item_x < bit_15_x + half_col * 2.0
            )
            if starts_new_word:
                if first_cluster_started and current_cluster:
                    all_clusters.append(current_cluster)
                current_cluster = []
                first_cluster_started = True

            # Detect extension word label rows: a single centered label spanning
            # most of the encoding width (e.g. "WORD DISPLACEMENT", "16-BIT
            # DISPLACEMENT").  These are full 16-bit extension word fields that
            # don't align with bit-15 because the text is centered.
            non_bit_items = [e for e in enc_items if e[2] not in ("0", "1")]
            if (first_cluster_started and len(non_bit_items) == len(enc_items)
                    and 1 <= len(non_bit_items) <= 2
                    and not starts_new_word):
                label = " ".join(e[2] for e in sorted(non_bit_items, key=lambda e: e[0]))
                if label.upper() not in ("MODE", "REGISTER", "MODE REGISTER"):
                    # Flush current cluster and emit extension word as its own cluster
                    if current_cluster:
                        all_clusters.append(current_cluster)
                        current_cluster = []
                    all_clusters.append([
                        (bit_x[15], bit_x[0], label, non_bit_items[0][3],
                         non_bit_items[0][4], non_bit_items[0][5])
                    ])
                    continue

            if first_cluster_started:
                current_cluster.extend(enc_items)

        if current_cluster:
            all_clusters.append(current_cluster)

        for cluster in all_clusters:
            sorted_cluster = sorted(cluster,
                key=lambda e: (0 if e[2] in ("0", "1") else 1, e[5], e[1] - e[0]))
            fields = _map_values_to_bits(x_to_bit, sorted_cluster)
            if fields and sum(f.width for f in fields) >= 15:
                # Skip spurious single-field entries from PDF section labels
                if (len(fields) == 1
                        and fields[0].name.startswith("Instruction F")):
                    continue
                encodings.append(fields)

    return encodings


def _map_values_to_bits(x_to_bit, value_row):
    """Map value row to bit positions using x-coordinate proximity to header columns."""
    sorted_cols = sorted(x_to_bit.items(), key=lambda e: e[0])
    bit_x = {bit: x for x, bit in sorted_cols}

    col_xs = sorted(bit_x.values())
    if len(col_xs) < 2:
        return []
    avg_spacing = (col_xs[-1] - col_xs[0]) / (len(col_xs) - 1)
    half_col = avg_spacing / 2

    fields = []
    used_bits = set()

    for item in value_row:
        vx, vx2, vtext = item[0], item[1], item[2]
        vtext = vtext.strip()
        if not vtext:
            continue

        text_width = vx2 - vx

        if vtext in ("0", "1"):
            best_bit = None
            best_dist = float("inf")
            for bit_num, col_x in bit_x.items():
                dist = abs(vx - col_x)
                if dist < best_dist and bit_num not in used_bits:
                    best_dist = dist
                    best_bit = bit_num
            if best_bit is not None and best_dist < half_col * 1.5:
                fields.append(BitField(name=vtext, bit_hi=best_bit, bit_lo=best_bit, width=1))
                used_bits.add(best_bit)
        else:
            # Narrow labels (e.g. "R/M", "SIZE") use tighter tolerance
            # to avoid overclaiming adjacent bit columns
            if text_width < avg_spacing * 0.7:
                tolerance = half_col
            else:
                tolerance = half_col * 1.5
            matching_bits = []
            for bit_num, col_x in bit_x.items():
                if bit_num not in used_bits:
                    if col_x >= vx - tolerance and col_x <= vx2 + tolerance:
                        matching_bits.append(bit_num)

            if matching_bits:
                matching_bits.sort(reverse=True)
                actual = set(matching_bits) - used_bits
                if actual:
                    hi = max(actual)
                    lo = min(actual)
                    fields.append(BitField(name=vtext, bit_hi=hi, bit_lo=lo,
                                          width=hi - lo + 1, bbox_width=text_width))
                    for b in range(lo, hi + 1):
                        used_bits.add(b)

    # Expand fields to cover adjacent orphan bits
    all_bits = set(range(16))
    assigned = set()
    for f in fields:
        for b in range(f.bit_lo, f.bit_hi + 1):
            assigned.add(b)
    orphans = all_bits - assigned

    if orphans:
        changed = True
        while changed:
            changed = False
            for orphan in sorted(orphans):
                candidates = []
                for f in fields:
                    if f.name in ("0", "1"):
                        continue
                    if orphan == f.bit_hi + 1 or orphan == f.bit_lo - 1:
                        candidates.append(f)
                if len(candidates) == 1:
                    best = candidates[0]
                elif len(candidates) > 1:
                    best = max(candidates, key=lambda f: (f.width, f.bbox_width))
                else:
                    continue
                best.bit_hi = max(best.bit_hi, orphan)
                best.bit_lo = min(best.bit_lo, orphan)
                best.width = best.bit_hi - best.bit_lo + 1
                orphans.discard(orphan)
                assigned.add(orphan)
                changed = True

    fields.sort(key=lambda f: -f.bit_hi)

    total = sum(f.width for f in fields)
    if total < 12:
        return []

    return fields


# --- Instruction detection and text parsing ---

@dataclass
class Instruction:
    mnemonic: str
    title: str
    processors: str
    operation: str
    syntax: list[str]
    attributes: str
    description: str
    condition_codes: dict[str, str]
    encodings: list[dict]
    field_descriptions: dict[str, str]
    page: int
    pages: list[int]


_SECTION_HEADERS = {
    "Integer Instructions", "Floating Point Instructions",
    "Supervisor (Privileged) Instructions", "Supervisor Instructions",
    "CPU32 Instructions",
}


def is_instruction_start(rows):
    """Check if these rows represent the start of an instruction entry."""
    lines = []
    for y_key in sorted(rows.keys()):
        parts = [text for x, x2, text, font, size in rows[y_key] if x < 370]
        if parts:
            lines.append(" ".join(parts))

    content = []
    for l in lines:
        l = l.strip()
        if not l:
            continue
        if "MOTOROLA" in l or "REFERENCE MANUAL" in l:
            continue
        if re.match(r"^\d+-\d+$", l):
            continue
        if l in _SECTION_HEADERS:
            continue
        content.append(l)

    if len(content) < 3:
        return None

    first = content[0]

    if not re.match(r"^[A-Za-z][A-Za-z0-9/]{1,10}(?:,\s*[A-Za-z0-9/]+)?$", first):
        return None

    text_block = "\n".join(content[:15])
    if "Operation:" not in text_block:
        return None

    mnemonic = first
    title = content[1] if len(content) > 1 else ""

    if len(content) > 1:
        second = content[1]
        if re.match(r"^(to |from |USP)", second) or re.match(r"^[A-Z0-9]{2,8}$", second):
            mnemonic = f"{first} {second}"
            title = content[2] if len(content) > 2 else second

    processors = "M68000 Family"
    for l in content[1:8]:
        m = re.match(r"^\((.+)\)\s*$", l)
        if m:
            processors = m.group(1)
            break

    return {"mnemonic": mnemonic, "title": title, "processors": processors}


def parse_text_sections(text):
    """Parse operation, syntax, attributes, description, CCs, field descriptions."""
    operation = ""
    m = re.search(r"Operation:\s*(.+?)(?:Assembler|$)", text, re.DOTALL)
    if m:
        operation = m.group(1).strip().split("\n")[0].strip()

    syntax = []
    m_asm = re.search(r"Assembler\s+(.+?)(?:\n|$)", text)
    if m_asm:
        asm_line = m_asm.group(1).strip()
        if not asm_line.startswith("Syntax"):
            syntax.append(asm_line)
    m = re.search(r"Syntax:\s*(.+?)(?:Attributes:|$)", text, re.DOTALL)
    if m:
        for line in m.group(1).strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("Assembler") and not line.startswith("Syntax"):
                syntax.append(line)

    attributes = ""
    m = re.search(r"Attributes:\s*(.+?)(?:Description:|$)", text, re.DOTALL)
    if m:
        attributes = m.group(1).strip().split("\n")[0].strip()

    description = ""
    m = re.search(r"Description:\s*(.+?)(?:Condition Codes:|Instruction Format:|$)", text, re.DOTALL)
    if m:
        description = re.sub(r"\s+", " ", m.group(1).strip())

    cc = {"X": "\u2014", "N": "\u2014", "Z": "\u2014", "V": "\u2014", "C": "\u2014"}
    for flag in cc:
        # Match "X — description" at start of line; [^\S\n]* avoids crossing newlines
        pattern = rf"^{flag}[^\S\n]*[\u2014\-\u2013][^\S\n]*(.+?)$"
        fm = re.search(pattern, text, re.MULTILINE)
        if fm:
            val = fm.group(1).strip().rstrip(".")
            if val and val != flag:
                cc[flag] = val

    field_descs = {}
    field_section = re.search(r"Instruction Fields:\s*\n(.+?)(?:\n\s*\n\s*\n|$)", text, re.DOTALL)
    if field_section:
        content = field_section.group(1)
        # Truncate at any subsequent Instruction Fields/Format boundary
        # (e.g. CAS page has both CAS and CAS2 Instruction Fields sections)
        for boundary in ("Instruction Fields:", "Instruction Format:"):
            idx = content.find(boundary)
            if idx >= 0:
                content = content[:idx]
        current_name = None
        current_desc = []
        for line in content.split("\n"):
            line = line.strip()
            fm = re.match(r"^(.+?)\s*[Ff]ields?\s*[\u2014\u2013\-]\s*(.+)", line)
            if fm:
                if current_name:
                    field_descs[current_name] = " ".join(current_desc)
                current_name = fm.group(1).strip()
                current_desc = [fm.group(2).strip()]
            elif current_name and line:
                # Capture value descriptions: "0 —", "1 —", "01 —", "10 —", "11 —", etc.
                if (line.startswith("If ") or
                    re.match(r"^[01]{1,2}\s*[\u2014\u2013\-]", line)):
                    current_desc.append(line)
        if current_name:
            field_descs[current_name] = " ".join(current_desc)

    return operation, syntax, attributes, description, cc, field_descs


def parse_all_instructions(doc, page_ranges):
    """Parse instructions from given page ranges."""
    page_data = []
    for start_page, end_page in page_ranges:
        for pn in range(start_page, end_page + 1):
            page = doc[pn - 1]
            spans = extract_page_spans(page)
            rows = spans_to_rows(spans)
            header = is_instruction_start(rows)
            page_data.append((pn, rows, header))

    instructions = []
    current = None

    for pn, rows, header in page_data:
        if header:
            if current:
                if header["mnemonic"] == current[0]["mnemonic"]:
                    current[1].append((pn, rows))
                    continue
                else:
                    instructions.append(current)
            current = (header, [(pn, rows)])
        elif current:
            current[1].append((pn, rows))

    if current:
        instructions.append(current)

    parsed = []
    for header, page_list in instructions:
        all_text = ""
        all_encodings = []
        page_nums = []

        for pn, rows in page_list:
            page_nums.append(pn)
            all_text += rows_to_plain_text(rows) + "\n"
            encs = find_encoding_tables(rows)
            all_encodings.extend(encs)

        operation, syntax, attributes, description, cc, field_descs = parse_text_sections(all_text)

        enc_data = []
        for enc_fields in all_encodings:
            fields_out = []
            for f in enc_fields:
                d = asdict(f)
                d.pop("bbox_width", None)
                fields_out.append(d)
            enc_data.append({"fields": fields_out})

        parsed.append(Instruction(
            mnemonic=header["mnemonic"],
            title=header["title"],
            processors=header["processors"],
            operation=operation,
            syntax=syntax,
            attributes=attributes,
            description=description,
            condition_codes=cc,
            encodings=enc_data,
            field_descriptions=field_descs,
            page=page_nums[0],
            pages=page_nums,
        ))

    _cross_check_with_summary(parsed, doc)
    return parsed


# --- Cross-check detail encodings against Section 8 summary ---

# Page range for Section 8: Instruction Format Summary
SUMMARY_PAGES = (561, 596)


def _encoding_mask_val(enc_fields):
    """Compute (mask, val) from encoding fields — only fixed 0/1 bits contribute."""
    mask = 0
    val = 0
    for f in enc_fields:
        name = f["name"] if isinstance(f, dict) else f.name
        bit_hi = f["bit_hi"] if isinstance(f, dict) else f.bit_hi
        bit_lo = f["bit_lo"] if isinstance(f, dict) else f.bit_lo
        if name in ("0", "1"):
            for b in range(bit_lo, bit_hi + 1):
                mask |= (1 << b)
                if name == "1":
                    val |= (1 << b)
    return mask, val


def parse_summary_encodings(doc):
    """Parse opword encodings from Section 8 (Instruction Format Summary).

    Returns dict mapping instruction_name -> list of (mask, val, fields).
    Each instruction may have multiple encoding forms in the summary.
    """
    summary: dict[str, list] = {}
    start, end = SUMMARY_PAGES

    for pn in range(start, end + 1):
        page = doc[pn - 1]
        spans = extract_page_spans(page)
        rows = spans_to_rows(spans)
        sorted_ys = sorted(rows.keys())

        # Find all bit header positions
        bit_headers = []  # list of (idx, y_key)
        for idx, y_key in enumerate(sorted_ys):
            row = rows[y_key]
            texts = [t for _, _, t, _, _ in row]
            bit_numbers = set()
            for t in texts:
                try:
                    n = int(t)
                    if 0 <= n <= 15:
                        bit_numbers.add(n)
                except ValueError:
                    pass
            if 15 in bit_numbers and 0 in bit_numbers and len(bit_numbers) >= 14:
                bit_headers.append((idx, y_key))

        # For each bit header, extract just the rows belonging to it and parse
        for hdr_pos, (h_idx, h_y) in enumerate(bit_headers):
            # Find instruction name by scanning backwards from the header
            name = None
            for prev_idx in range(h_idx - 1, max(h_idx - 5, -1), -1):
                prev_y = sorted_ys[prev_idx]
                prev_texts = " ".join(t for _, _, t, _, _ in rows[prev_y])
                prev_texts = prev_texts.strip()
                if not prev_texts or "MOTOROLA" in prev_texts or \
                   "REFERENCE MANUAL" in prev_texts or \
                   re.match(r"^\d+-\d+$", prev_texts) or \
                   prev_texts == "Instruction Format Summary":
                    continue
                if len(prev_texts) > 30:
                    continue
                name = prev_texts
                break

            if not name:
                continue

            # Determine y-range: from header to next header (or end of page)
            next_hdr_y = (bit_headers[hdr_pos + 1][1]
                          if hdr_pos + 1 < len(bit_headers) else 9999)

            # Extract just the rows for this header's region
            region_rows = {y: rows[y] for y in sorted_ys
                          if y >= h_y and y < next_hdr_y}

            # Parse the encoding table for this region
            encs = find_encoding_tables(region_rows, summary_mode=True)
            if not encs:
                continue

            # First encoding is the opword
            opword_fields = encs[0]
            enc_mask, enc_val = _encoding_mask_val(opword_fields)
            summary.setdefault(name, []).append((enc_mask, enc_val, opword_fields))

    return summary


def _cross_check_with_summary(instructions, doc):
    """Cross-check detail page opword encodings against the Section 8 summary.

    When detail and summary disagree on a fixed bit, resolve using collision
    detection: the correct encoding must be unique — it must not collide with
    any other instruction's opword.  If one source creates a collision and the
    other doesn't, the non-colliding one is preferred.

    This catches typos in either the detail pages (e.g. BFFFO bit 10) or the
    summary (e.g. ANDI bit 9) without hardcoding which source is correct.
    """
    summary = parse_summary_encodings(doc)
    if not summary:
        return

    # Build lookup of all detail opword (mask, val) by mnemonic for collision checks
    all_opwords = {}  # mnemonic -> (mask, val)
    for inst in instructions:
        if inst.encodings:
            m, v = _encoding_mask_val(inst.encodings[0]["fields"])
            all_opwords[inst.mnemonic] = (m, v)

    fixes = 0
    for inst in instructions:
        if not inst.encodings:
            continue

        mnemonic = inst.mnemonic
        entries = summary.get(mnemonic)
        if not entries:
            continue

        opword = inst.encodings[0]
        detail_mask, detail_val = _encoding_mask_val(opword["fields"])

        for smask, sval, sfields in entries:
            if smask != detail_mask:
                continue
            if sval == detail_val:
                continue  # no discrepancy

            diff_bits = detail_val ^ sval
            diff_positions = [b for b in range(16) if diff_bits & (1 << b)]

            # Collision check: does either value create an exact collision with
            # another instruction that has the same mask?  An exact collision
            # means two instructions are truly indistinguishable by their
            # opword fixed bits.
            detail_collides = False
            summary_collides = False
            for other_mn, (om, ov) in all_opwords.items():
                if other_mn == mnemonic:
                    continue
                # Only check instructions with the same mask (same field layout)
                if om != detail_mask:
                    continue
                if ov == detail_val:
                    detail_collides = True
                if ov == sval:
                    summary_collides = True

            if detail_collides and not summary_collides:
                # Detail collides, summary doesn't — use summary
                print(f"  SUMMARY FIX: {mnemonic} bits {diff_positions} "
                      f"(detail=0x{detail_val:04X} collides, "
                      f"summary=0x{sval:04X} unique) — using summary")

                fields_out = []
                for f in sfields:
                    if isinstance(f, BitField):
                        d = {"name": f.name, "bit_hi": f.bit_hi, "bit_lo": f.bit_lo,
                             "width": f.width}
                    else:
                        d = dict(f)
                        d.pop("bbox_width", None)
                    fields_out.append(d)
                inst.encodings[0] = {"fields": fields_out}
                # Update the lookup so subsequent checks see the corrected value
                all_opwords[mnemonic] = (smask, sval)
                fixes += 1
            elif not detail_collides and summary_collides:
                # Summary collides — detail is correct, keep it
                print(f"  SUMMARY WARN: {mnemonic} bits {diff_positions} "
                      f"(detail=0x{detail_val:04X} unique, "
                      f"summary=0x{sval:04X} collides) — keeping detail")
            else:
                # Both collide or neither collides — flag but don't auto-fix
                print(f"  SUMMARY WARN: {mnemonic} bits {diff_positions} "
                      f"(detail=0x{detail_val:04X}, summary=0x{sval:04X}) "
                      f"— ambiguous, keeping detail")
            break

    if fixes:
        print(f"  Applied {fixes} summary cross-check fix(es)")


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 2: EA mode table extraction from PDF
# ═══════════════════════════════════════════════════════════════════════════════

def _ea_sort_key(m):
    return EA_ORDER.get(m, 99)


def _parse_3bit(text):
    """Parse a 3-digit binary string to int, or return None."""
    text = text.strip()
    if len(text) == 3 and all(c in '01' for c in text):
        return int(text, 2)
    return None


def find_ea_tables_on_page(rows):
    """Find EA mode tables on a page.

    Returns list of (label, valid_modes, modes_020) tuples.
    """
    tables = []
    sorted_ys = sorted(rows.keys())

    for idx, y_key in enumerate(sorted_ys):
        row = rows[y_key]
        texts = [t for _, _, t, _, _ in row]
        row_text = " ".join(texts)

        if "Addressing Mode" not in row_text:
            continue
        if "Mode" not in row_text or "Register" not in row_text:
            continue

        mode_col_xs = []
        for x, x2, text, _, _ in row:
            if text.strip() == "Mode":
                mode_col_xs.append((x + x2) / 2)

        if not mode_col_xs:
            continue

        reg_col_xs = []
        for x, x2, text, _, _ in row:
            if text.strip() == "Register":
                reg_col_xs.append((x + x2) / 2)

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

        valid_modes = set()
        modes_020 = set()

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

            if any(kw in next_text for kw in (
                "MC68020", "MC68030", "MC68040",
                "NOTE", "Instruction Format", "Instruction Fields",
            )):
                break
            if any(kw in next_text for kw in (
                "Can be used", "Word and long", "word and long",
            )):
                continue

            col_has_footnote = [False] * len(mode_col_xs)
            for span_x, span_x2, span_text, _, _ in next_row:
                if "*" not in span_text:
                    continue
                span_mid = (span_x + span_x2) / 2
                for ci, (nm_min, nm_max) in enumerate(col_name_ranges):
                    if nm_min <= span_mid < nm_max:
                        col_has_footnote[ci] = True
                        break

            for span_x, span_x2, span_text, _, _ in next_row:
                span_center = (span_x + span_x2) / 2
                span_text_s = span_text.strip()

                for col_idx, mode_col_x in enumerate(mode_col_xs):
                    if abs(span_center - mode_col_x) < 25:
                        mode_val = _parse_3bit(span_text_s)
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
                                            reg_val = _parse_3bit(rtext.strip())
                                            if reg_val is not None:
                                                canonical = MODE_MAP.get((7, reg_val))
                            if canonical:
                                valid_modes.add(canonical)
                                if col_has_footnote[col_idx]:
                                    modes_020.add(canonical)
                        break

        if valid_modes:
            sorted_modes = sorted(valid_modes, key=_ea_sort_key)
            sorted_020 = sorted(modes_020, key=_ea_sort_key)
            tables.append((label, sorted_modes, sorted_020))

    return tables


def _merge_ea_tables(tables_by_page, pages):
    """Merge EA tables from all pages of an instruction."""
    all_tables = []
    for pg in pages:
        if pg in tables_by_page:
            all_tables.extend(tables_by_page[pg])

    if not all_tables:
        return {}, {}

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

    result = {}
    result_020 = {}
    for key, modes in by_label.items():
        result[key] = sorted(modes, key=_ea_sort_key)
    for key, modes in by_label_020.items():
        if modes:
            result_020[key] = sorted(modes, key=_ea_sort_key)

    return result, result_020


def apply_ea_modes(kb_data, doc, page_ranges):
    """Phase 2: Extract EA tables from PDF and merge into instruction dicts."""
    tables_by_page = {}
    for start_page, end_page in page_ranges:
        for pn in range(start_page, end_page + 1):
            page = doc[pn - 1]
            spans = extract_page_spans(page)
            rows = spans_to_rows(spans)
            tables = find_ea_tables_on_page(rows)
            if tables:
                tables_by_page[pn] = tables

    for inst in kb_data:
        pages = inst.get("pages", [inst.get("page", 0)])
        ea_modes, ea_modes_020 = _merge_ea_tables(tables_by_page, pages)
        inst["ea_modes"] = ea_modes
        if ea_modes_020:
            inst["ea_modes_020"] = ea_modes_020
        elif "ea_modes_020" in inst:
            del inst["ea_modes_020"]
        # Stash raw per-page tables for post-processing after constraints
        inst["_ea_tables_by_page"] = {
            pg: tables_by_page[pg] for pg in pages if pg in tables_by_page
        }

    with_ea = sum(1 for inst in kb_data if inst.get("ea_modes"))
    with_020 = sum(1 for inst in kb_data if inst.get("ea_modes_020"))
    print(f"  EA modes: {with_ea}/{len(kb_data)} instructions, {with_020} with 020+ modes")


def apply_ea_direction_split(kb_data):
    """Post-process: for instructions with movem_direction, split EA modes by direction.

    Uses stashed per-page EA tables from Phase 2 plus direction constraints from Phase 4.
    The PDF lists separate EA tables for each direction (e.g. MOVEM has one table for
    reg-to-mem and another for mem-to-reg on consecutive pages).
    """
    count = 0
    for inst in kb_data:
        movem_dir = inst.get("constraints", {}).get("movem_direction")
        raw_tables = inst.pop("_ea_tables_by_page", {})

        if not movem_dir or not raw_tables:
            continue

        dir_values = movem_dir.get("values", {})
        if len(dir_values) != 2:
            continue

        # Direction order matches page order in the PDF
        dir_labels = list(dir_values.values())  # e.g. ["reg-to-mem", "mem-to-reg"]
        ea_per_dir = {}
        dir_idx = 0
        for pg in sorted(raw_tables.keys()):
            for label, modes, modes_020 in raw_tables[pg]:
                if dir_idx < len(dir_labels):
                    ea_per_dir[dir_labels[dir_idx]] = modes
                    dir_idx += 1

        if ea_per_dir:
            inst["ea_modes_by_direction"] = ea_per_dir
            count += 1

    if count:
        print(f"  EA direction splits: {count} instructions")


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 3: Syntax pattern parsing
# ═══════════════════════════════════════════════════════════════════════════════

def _normalize_syntax(raw):
    """Normalize a raw PDF syntax string."""
    s = raw.strip()
    s = s.lstrip("*").strip()
    s = re.sub(r"<\s*(\w+)\s*>", r"<\1>", s)
    s = re.sub(r"\s*,\s*", ",", s)
    s = re.sub(r"–\s*\(", "-(", s)
    s = re.sub(r"\)\s*\+", ")+", s)
    s = re.sub(r"\s+", " ", s)
    return s


def _parse_operand(token):
    """Parse a single operand token into a type descriptor."""
    t = token.strip()

    if t in ("<ea>",):
        return {"type": "ea"}
    if t in ("<label>",):
        return {"type": "label"}
    if re.match(r"^#\s*<?\s*(data|vector|displacement)\s*>?$", t):
        return {"type": "imm"}
    if t.startswith("#"):
        return {"type": "imm"}
    if t in ("CCR", "ccr"):
        return {"type": "ccr"}
    if t in ("SR", "sr"):
        return {"type": "sr"}
    if t in ("USP", "usp"):
        return {"type": "usp"}
    if re.match(r"^[Dd][0-7nxylhqr]?$", t):
        return {"type": "dn"}
    if re.match(r"^[Aa][0-7nxy]$", t):
        return {"type": "an"}
    if re.match(r"^-\([Aa][0-7xy]\)$", t):
        return {"type": "predec"}
    if re.match(r"^\([Aa][0-7xy]\)\+$", t):
        return {"type": "postinc"}
    if re.match(r"^\(d?\d+,[Aa][0-7xy]\)$", t):
        return {"type": "disp"}
    if re.match(r"^[Dd]\w+\s*[–-]\s*[Dd]\w+$", t):
        return {"type": "dn_pair"}
    if t == "<list>":
        return {"type": "reglist"}
    if re.match(r"^[Dd]\w+:[Dd]\w+$", t):
        return {"type": "dn_pair"}

    # CAS: Dc/Du data register operands (e.g. Dc, Du, Dc1, Dc2, Du1, Du2)
    if re.match(r"^[Dd][cu]\d*$", t, re.IGNORECASE):
        return {"type": "dn"}

    # Control register operand (MOVEC Rc)
    if re.match(r"^[Rr]c$", t):
        return {"type": "ctrl_reg"}

    # Generic register Rn (MOVEC Rn, MOVES Rn, RTM Rn, CMP2/CHK2 Rn)
    if re.match(r"^[Rr]n\d*$", t):
        return {"type": "rn"}

    # Bit-field EA: "<ea> {offset:width}" forms (BFTST, BFCHG, BFINS, etc.)
    if re.match(r"^<ea>\s*\{", t):
        return {"type": "bf_ea"}

    return {"type": "unknown", "raw": t}


def _split_operands(s):
    """Split operand string by commas, respecting parentheses."""
    parts = []
    depth = 0
    current = []
    for ch in s:
        if ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current).strip())
    return parts


def _split_concatenated_forms(syntax_list, mnemonic):
    """Split concatenated syntax entries into separate forms.

    Returns list of (syntax_str, is_020plus) tuples.
    """
    result = []
    base = mnemonic.split(",")[0].split()[0]

    for raw_s in syntax_list:
        is_020 = raw_s.strip().startswith("*")
        s = _normalize_syntax(raw_s)
        if s.lower().startswith("where ") or s.lower().startswith("applies to"):
            continue
        if s.strip() in ("→", "->"):
            continue

        parts_to_add = [s]
        words = s.split()
        if len(words) > 2:
            splits = []
            for i, w in enumerate(words):
                w_base = w.split(".")[0].upper()
                if i > 0 and (w_base == base.upper() or
                              w_base.rstrip("DLRS") == base.upper().rstrip("DLRS")):
                    splits.append(i)

            if splits:
                parts_to_add = []
                prev = 0
                for split_idx in splits:
                    chunk = " ".join(words[prev:split_idx]).strip()
                    if chunk:
                        parts_to_add.append(chunk)
                    prev = split_idx
                chunk = " ".join(words[prev:]).strip()
                if chunk:
                    parts_to_add.append(chunk)

        result.extend((p, is_020) for p in parts_to_add)

    return result


def _parse_syntax_to_form(mnemonic, syntax_str):
    """Parse a single syntax string into a structured form."""
    s = _normalize_syntax(syntax_str)

    if s.lower().startswith("where ") or s.startswith("Applies to"):
        return None
    if s.strip() in ("→", "->"):
        return None

    parts = s.split(None, 1)
    if not parts:
        return None

    inst_name = parts[0]
    base_mnemonic = mnemonic.split(",")[0].split()[0]
    inst_base = inst_name.split(".")[0].upper().lstrip("*")
    known_variants = {base_mnemonic.upper()}
    for part in mnemonic.split(","):
        for word in part.strip().split():
            known_variants.add(word.upper())
    if inst_base not in known_variants:
        if not (inst_base.endswith("D") and any(
            v.startswith(inst_base[:-1]) and len(v) == len(inst_base)
            for v in known_variants
        )):
            return None

    operand_str = parts[1] if len(parts) > 1 else ""
    operand_str = re.sub(r"\s+where\s+.*$", "", operand_str, flags=re.IGNORECASE)
    operand_str = re.sub(r"\s*(?:→|->).*$", "", operand_str)

    if not operand_str:
        return {"syntax": s, "operands": []}

    tokens = _split_operands(operand_str)
    operands = []
    for tok in tokens:
        tok = re.sub(r"\s*\d+\s*[/x]\s*\d+.*$", "", tok)
        tok = re.sub(r"\s*(?:→|->).*$", "", tok)
        tok = re.sub(r"\s*extend\s+.*$", "", tok, flags=re.IGNORECASE)
        tok = re.sub(r"\s*\(MC68.*$", "", tok)
        tok = re.sub(r"\s*MC68.*$", "", tok)
        tok = re.sub(r"\s*where\s+.*$", "", tok, flags=re.IGNORECASE)
        tok = tok.strip()
        if not tok:
            continue
        op = _parse_operand(tok)
        operands.append(op)

    return {"syntax": s, "operands": operands}


def _parse_operation_effects(operation, condition_codes, mnemonic):
    """Parse the operation field into structured read/write effects."""
    effects = {
        "reads_pc": False,
        "writes_pc": False,
        "reads_sp": False,
        "writes_sp": False,
        "privileged": False,
    }

    op = operation

    if "→ PC" in op or "-> PC" in op:
        effects["writes_pc"] = True
    if "PC +" in op or "PC →" in op or "PC ->" in op:
        effects["reads_pc"] = True

    if "SP –" in op or "SP -" in op or "SP +" in op:
        effects["reads_sp"] = True
        effects["writes_sp"] = True
    if "→ SP" in op or "-> SP" in op:
        effects["writes_sp"] = True
    if "(SP)" in op or "(SSP)" in op:
        effects["reads_sp"] = True
    if "SSP" in op:
        effects["reads_sp"] = True
        effects["writes_sp"] = True

    if "Supervisor State" in op or "S-Bit" in op:
        effects["privileged"] = True

    dash = "\u2014"
    cc_write = []
    for flag in ("X", "N", "Z", "V", "C"):
        val = condition_codes.get(flag, dash)
        if val == dash or val == "Not affected" or val == "Undefined":
            continue
        if "same as" in val.lower():
            cc_write.append(flag)
        elif "unchanged" in val.lower():
            pass
        else:
            cc_write.append(flag)

    effects["cc_write"] = cc_write
    return effects


def apply_syntax_forms(kb_data):
    """Phase 3: Parse syntax patterns into structured forms."""
    for inst in kb_data:
        mnemonic = inst["mnemonic"]
        syntax_list = inst.get("syntax", [])

        split_syntaxes = _split_concatenated_forms(syntax_list, mnemonic)
        forms = []
        for syn, is_020 in split_syntaxes:
            form = _parse_syntax_to_form(mnemonic, syn)
            if form:
                if is_020:
                    form["processor_020"] = True
                forms.append(form)
        inst["forms"] = forms

        effects = _parse_operation_effects(
            inst.get("operation", ""),
            inst.get("condition_codes", {}),
            mnemonic,
        )
        inst["effects"] = effects

    with_forms = sum(1 for i in kb_data if i["forms"])
    total_forms = sum(len(i["forms"]) for i in kb_data)
    print(f"  Syntax forms: {with_forms}/{len(kb_data)} instructions, {total_forms} total forms")


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 4: Constraint derivation
# ═══════════════════════════════════════════════════════════════════════════════

def _find_encoding_field(encodings, target_name):
    """Find a named field in the encodings list, return (name, width) or None."""
    target_upper = target_name.upper()
    for enc in encodings:
        fields = enc.get("fields", [])
        for f in fields:
            if f["name"].upper() == target_upper:
                return f["name"], f["width"]
    return None


def _find_field_description(fd, field_name):
    """Find a field description by name, case-insensitive.

    Also matches extension word field names like "WORD DISPLACEMENT" or
    "16-BIT DISPLACEMENT" to a base description key like "Displacement".
    """
    fn_lower = field_name.lower()
    for fd_key, fd_val in fd.items():
        if fd_key.lower() == fn_lower:
            return fd_val
        if fd_key.lower().replace(" ", "").replace("/", "") == fn_lower.replace(" ", "").replace("/", ""):
            return fd_val
    # Fallback: check if the last word of the field name matches an fd_key
    # (handles "WORD DISPLACEMENT" → "Displacement", "16-BIT DISPLACEMENT" → "Displacement")
    last_word = fn_lower.rsplit(None, 1)[-1] if fn_lower else ""
    if last_word:
        for fd_key, fd_val in fd.items():
            if fd_key.lower() == last_word:
                return fd_val
    return ""


    # Field names that represent structural parts of the encoding, not immediate data
_STRUCTURAL_FIELD_RE = re.compile(
    r"^(REGISTER|MODE|OPMODE|CONDITION|SIZE|CACHE|SCOPE|ID|FC|MASK|"
    r"LEVEL|NUM|OFFSET|WIDTH|A/D|D/A|R/?\s*W|R/M|dr|i/r|D[couwqrhl]|"
    r"Rn\d|Instruction|FD|A$|COPROCESSOR|MC68851)"
    r"|REGISTER\b"  # also match fields containing REGISTER
    , re.IGNORECASE
)


def _extract_immediate_range(inst):
    """Extract immediate value range from encoding field width and field_descriptions."""
    fd = inst.get("field_descriptions", {})
    encodings = inst.get("encodings", [])

    if not encodings:
        return None

    # Iterate over all named encoding fields; let descriptions drive extraction
    for enc in encodings:
        for f in enc.get("fields", []):
            field_name = f["name"]
            if field_name in ("0", "1"):
                continue
            if _STRUCTURAL_FIELD_RE.search(field_name):
                continue

            bit_width = f["width"]
            desc = _find_field_description(fd, field_name)
            # Non-structural fields without a description — assume unsigned immediate
            if not desc:
                print(f"WARNING: {inst.get('mnemonic','?')}: field '{field_name}' "
                      f"has no description — assuming unsigned {bit_width}-bit immediate",
                      file=sys.stderr)
                return {
                    "min": 0,
                    "max": (1 << bit_width) - 1,
                    "field": field_name,
                    "bits": bit_width,
                }
            dl = desc.lower()

            if ("sign-extended" in dl or "sign extended" in dl
                    or "twos complement" in dl or "two\u2019s complement" in dl):
                return {
                    "min": -(1 << (bit_width - 1)),
                    "max": (1 << (bit_width - 1)) - 1,
                    "field": field_name,
                    "bits": bit_width,
                    "signed": True,
                }

            if "represent" in dl:
                return {
                    "min": 1,
                    "max": (1 << bit_width),
                    "field": field_name,
                    "bits": bit_width,
                    "zero_means": (1 << bit_width),
                }

            # Fields with explicit numeric ranges in description
            if bit_width <= 8:
                range_match = re.search(r"(\d+)\s*-\s*(\d+)", desc)
                if range_match:
                    lo, hi = int(range_match.group(1)), int(range_match.group(2))
                    if lo == 0 and "represent" in dl:
                        return {
                            "min": 1,
                            "max": hi + 1,
                            "field": field_name,
                            "bits": bit_width,
                            "zero_means": hi + 1,
                        }

            # Non-DATA immediate fields (vector, count, etc.) — unsigned range
            fn_upper = field_name.upper()
            if fn_upper != "DATA" and ("immediate" in dl or "vector" in dl
                                       or "count" in dl or "number" in dl):
                return {
                    "min": 0,
                    "max": (1 << bit_width) - 1,
                    "field": field_name,
                    "bits": bit_width,
                }

    return None


def _extract_cc_parameterization(inst):
    """Extract condition code parameterization from encoding and mnemonic."""
    mnemonic = inst["mnemonic"]

    if "cc" not in mnemonic:
        return None

    encodings = inst.get("encodings", [])
    if not encodings:
        return None

    result = _find_encoding_field(encodings, "CONDITION")
    condition_bits = result[1] if result else None

    if condition_bits is None:
        return None

    prefix = mnemonic.lower().replace("cc", "")

    # Derive excluded CCs: if a cc value (e.g. "t","f") forms a separately-parsed
    # instruction (e.g. Bcc with cc=t → BRA, Bcc with cc=f → BSR), exclude it.
    # This is checked by the caller after all instructions are parsed.
    return {
        "prefix": prefix,
        "field_bits": condition_bits,
        "excluded": [],  # populated by _derive_cc_exclusions()
    }


def _extract_direction_variants(inst):
    """Extract direction variant info from dr field description."""
    fd = inst.get("field_descriptions", {})
    mnemonic = inst["mnemonic"]

    dr_desc = fd.get("dr", "")
    if not dr_desc:
        return None

    values = {}
    for match in re.finditer(r"(\d)\s*(?:--|—|–)\s*(\w+)\s+(\w+)", dr_desc):
        bit_val = match.group(1)
        direction = match.group(3).lower()
        if direction in ("right", "left"):
            values[bit_val] = "r" if direction == "right" else "l"

    if not values:
        return None

    parts = [p.strip() for p in mnemonic.split(",")]
    if len(parts) == 2:
        a, b = parts[0], parts[1]
        common = ""
        for i in range(min(len(a), len(b))):
            if a[i] == b[i]:
                common += a[i]
            else:
                break
        if common:
            variants = [p.lower() for p in parts]
            return {
                "field": "dr",
                "values": values,
                "base": common.lower(),
                "variants": variants,
            }

    return None


def _extract_operand_modes(inst):
    """Extract R/M operand mode variants from field description."""
    fd = inst.get("field_descriptions", {})

    rm_desc = fd.get("R/M", "")
    if not rm_desc:
        return None

    modes = {}
    if "data register" in rm_desc.lower() and "memory" in rm_desc.lower():
        for match in re.finditer(r"(\d)\s*(?:--|—|–)\s*(?:The operation is\s+)?(.+?)(?:\.|$|\d\s*(?:--|—|–))", rm_desc):
            bit_val = match.group(1)
            mode_desc = match.group(2).strip().lower()
            if "data register" in mode_desc:
                modes[bit_val] = "dn,dn"
            elif "memory" in mode_desc:
                modes[bit_val] = "predec,predec"

    if not modes:
        if "0" in rm_desc and "data register" in rm_desc.lower():
            modes["0"] = "dn,dn"
        if "1" in rm_desc and "memory" in rm_desc.lower():
            modes["1"] = "predec,predec"

    if modes:
        return {"field": "R/M", "values": modes}
    return None


def _extract_movem_direction(inst):
    """Extract register-to-memory/memory-to-register direction from dr field description."""
    fd = inst.get("field_descriptions", {})
    dr_desc = fd.get("dr", "")
    if not dr_desc:
        return None

    values = {}
    if "register to memory" in dr_desc.lower():
        match = re.search(r"(\d)\s*(?:--|—|–)\s*[Rr]egister to memory", dr_desc)
        if match:
            values[match.group(1)] = "reg-to-mem"
    if "memory to register" in dr_desc.lower():
        match = re.search(r"(\d)\s*(?:--|—|–)\s*[Mm]emory to register", dr_desc)
        if match:
            values[match.group(1)] = "mem-to-reg"

    if values:
        return {"field": "dr", "values": values}
    return None


def _extract_shift_count_range(inst):
    """Extract shift/rotate count range from encoding structure."""
    fd = inst.get("field_descriptions", {})
    encodings = inst.get("encodings", [])

    cr_desc = _find_field_description(fd, "Count/Register")
    if cr_desc:
        range_match = re.search(r"values?\s+(\d+)\s*[-\u2013\u2014]\s*(\d+)", cr_desc)
        zero_match = re.search(r"(?:value of|value\s+)(?:zero|0)\s+represents\s+(?:a\s+)?(?:count of\s+)?(\d+)", cr_desc, re.IGNORECASE)
        if range_match:
            lo = int(range_match.group(1))
            hi = int(range_match.group(2))
            zero_means = int(zero_match.group(1)) if zero_match else hi + 1
            # Bit width from the encoding field
            cr_field = _find_encoding_field(encodings, "Count/Register")
            bits = cr_field[2] if cr_field else (hi.bit_length())
            return {
                "min": lo, "max": zero_means if zero_means > hi else hi,
                "field": "Count/Register", "bits": bits,
                "zero_means": zero_means,
            }

    has_dr = _find_encoding_field(encodings, "dr") is not None
    if not has_dr:
        return None

    # Fallback: detect shift/rotate structure from encoding fields
    for enc in encodings:
        fields = enc.get("fields", [])
        has_ir = any(f["name"] == "i/r" for f in fields)
        count_field = next((f for f in fields if f["name"] == "REGISTER"
                           and f["width"] == 3 and f["bit_hi"] >= 9), None)
        if has_ir and count_field:
            bits = count_field["width"]
            return {
                "min": 1, "max": 1 << bits,
                "field": "Count/Register", "bits": bits,
                "zero_means": 1 << bits,
            }

    return None


def _extract_sizes_68000(inst):
    """Filter sizes to 68000-only by checking asterisk in attributes."""
    attrs = inst.get("attributes", "")
    sizes = inst.get("sizes", [])

    if "*" not in attrs or not sizes:
        return None

    filtered = []
    for sz in sizes:
        sz_word = {"b": "Byte", "w": "Word", "l": "Long"}.get(sz, "")
        if sz_word and f"{sz_word}*" in attrs:
            continue
        filtered.append(sz)

    if filtered != sizes:
        return filtered
    return None


def _extract_memory_size_restriction(inst):
    """Detect if memory EA form has a fixed size (shift/rotate memory = word only).

    Derives size field position from the register-form encoding's SIZE field,
    then checks if those bits are all-fixed in the memory-form encoding.
    """
    encodings = inst.get("encodings", [])
    if len(encodings) < 2:
        return None

    has_dr = _find_encoding_field(encodings, "dr") is not None
    if not has_dr:
        return None

    # Find SIZE field position from register-form encoding (has i/r field)
    size_hi = size_lo = None
    for enc in encodings:
        fields = enc.get("fields", [])
        if any(f["name"] == "i/r" for f in fields):
            for f in fields:
                if f["name"] == "SIZE":
                    size_hi, size_lo = f["bit_hi"], f["bit_lo"]
                    break
            if size_hi is not None:
                break
    if size_hi is None:
        return None

    SIZE_MAP = {0: "b", 1: "w", 2: "l"}

    # Check memory-form encoding (has MODE but not i/r)
    for enc in encodings:
        fields = enc.get("fields", [])
        has_mode = any(f["name"] == "MODE" for f in fields)
        has_ir = any(f["name"] == "i/r" for f in fields)
        has_dr_field = any(f["name"] == "dr" for f in fields)

        if has_mode and not has_ir and has_dr_field:
            # Check if all bits at the SIZE field position are fixed
            fixed_val = 0
            all_fixed = True
            for bit in range(size_lo, size_hi + 1):
                bf = next((f for f in fields if f["bit_hi"] == bit and f["bit_lo"] == bit), None)
                if bf and bf["name"] in ("0", "1"):
                    fixed_val |= int(bf["name"]) << (bit - size_lo)
                else:
                    all_fixed = False
                    break
            if all_fixed:
                if fixed_val in SIZE_MAP:
                    return SIZE_MAP[fixed_val]
                # Non-standard SIZE value — memory-form discriminator;
                # derive actual size from instruction attributes
                attrs = inst.get("attributes", "").lower()
                for sz_name, sz_letter in [("word", "w"), ("byte", "b"), ("long", "l")]:
                    if sz_name in attrs:
                        return sz_letter

    return None


def _extract_bit_op_size_restriction(inst):
    """Detect bit operation size behavior from description."""
    desc = inst.get("description", "")
    has_reg_32 = "modulo 32" in desc
    has_mem_byte = "byte operation" in desc.lower() or "modulo 8" in desc

    if has_reg_32 or has_mem_byte:
        return {"dn": "l", "memory": "b"}
    return None


def _derive_processor_min(processors):
    """Derive processor_min from the processors field using CPU_HIERARCHY."""
    if not processors or "M68000 Family" in processors:
        return "68000"

    order = CPU_HIERARCHY["order"]
    aliases = CPU_HIERARCHY["aliases"]
    # Coprocessors (FPU 68881/68882, MMU 68851) imply 68020 as the minimum CPU.
    _COPROCESSOR_IMPLIES = "68020"
    min_idx = len(order)
    has_cpu32 = False

    for proc_token in re.findall(r"MC?68\w+|CPU32", processors):
        if proc_token == "CPU32":
            has_cpu32 = True
            continue
        token = proc_token.removeprefix("MC")  # "MC68020" -> "68020"
        # Strip EC/LC variants: "68EC030" -> "68030", "68LC040" -> "68040"
        core = re.sub(r"^68[A-Z]{1,2}(\d)", r"68\1", token)

        if core in ("68881", "68882", "68851"):
            # Coprocessor — implies 68020
            idx = order.index(_COPROCESSOR_IMPLIES) if _COPROCESSOR_IMPLIES in order else len(order)
        elif core in order:
            idx = order.index(core)
        else:
            # Try prefix match (68008 -> 68000)
            idx = next((order.index(o) for o in order if core.startswith(o[:4])), len(order))

        if idx < min_idx:
            min_idx = idx

    if min_idx < len(order):
        return order[min_idx]
    if has_cpu32:
        return "cpu32"
    return "68000"


def _extract_opmode_table(doc, inst):
    """Extract OPMODE value table from PDF instruction pages.

    Handles three formats found in the M68000 reference:
    1. Multi-column: "Byte Word Long Operation" header with binary columns
       (used by ADD, OR, SUB, AND, CMP, EOR)
    2. Value-description: "binary—Description" lines under Opmode field heading
       (used by MOVEP, EXG, ADDA, SUBA, CMPA)
    3. Source/Destination: "Opmode Source Destination Assembler Syntax" header
       with space-separated binary digits (used by MOVE16)

    Returns list of dicts with {opmode, size, operation} entries, or None.
    """
    pages = inst.get("pages", [inst.get("page", 0)])
    if not pages:
        return None

    # Check if this instruction has an OPMODE encoding field
    has_opmode = False
    for enc in inst.get("encodings", []):
        for f in enc.get("fields", []):
            if f["name"].upper() == "OPMODE":
                has_opmode = True
                break
    if not has_opmode:
        return None

    SIZE_NAMES = {"b": "byte", "w": "word", "l": "long"}
    SIZE_MAP = {"byte": "b", "word": "w", "long": "l"}
    entries = []

    for pg in pages:
        page = doc[pg - 1]
        spans = extract_page_spans(page)
        rows = spans_to_rows(spans)
        sorted_ys = sorted(rows.keys())

        in_opmode = False
        header_cols = {}  # "Byte"->x, "Word"->x, "Long"->x, "Operation"->x
        src_dst_cols = {}  # "source"->x, "destination"->x, "syntax"->x (Format 3)

        for idx, y_key in enumerate(sorted_ys):
            row_items = rows[y_key]
            row_text = " ".join(t for _, _, t, _, _ in row_items)

            # Detect Opmode field section start
            if re.search(r"Opmode\s+\S*eld\b", row_text, re.IGNORECASE):
                in_opmode = True
                continue

            if not in_opmode:
                continue

            # Stop at next field description or encoding diagram
            if re.match(r"^.+\s+\S*eld[s—\u2014\u2013\-]", row_text) and "opmode" not in row_text.lower():
                in_opmode = False
                continue
            if re.match(r"^Effective Address", row_text):
                in_opmode = False
                continue
            # Stop at encoding bit numbers (15 14 13 12 ...)
            if re.match(r"^15\s+14\s+13", row_text):
                in_opmode = False
                continue

            # Detect Byte/Word/Long/Operation header (Format 1)
            texts = {t.lower(): x for x, _, t, _, _ in row_items}
            if "Byte" in [t for _, _, t, _, _ in row_items] or "byte" in texts:
                if "word" in texts or "Word" in [t for _, _, t, _, _ in row_items]:
                    for x, _, t, _, _ in row_items:
                        tl = t.lower()
                        if tl in ("byte", "word", "long", "operation"):
                            header_cols[tl] = x
                    continue

            # Detect Source/Destination header (Format 3: MOVE16-style)
            raw_texts = [t for _, _, t, _, _ in row_items]
            if "Source" in raw_texts and any("Destinati" in t or "Destination" in t for t in raw_texts):
                for x, _, t, _, _ in row_items:
                    tl = t.lower().replace(" ", "")
                    if tl == "source":
                        src_dst_cols["source"] = x
                    elif tl.startswith("destinati"):
                        src_dst_cols["destination"] = x
                    elif "assembler" in tl or "syntax" in tl:
                        src_dst_cols["syntax"] = x
                continue

            # Format 1: Multi-column (Byte/Word/Long rows)
            if header_cols:
                # Collect binary spans from this row
                bin_spans = [(x, t) for x, _, t, _, _ in row_items
                             if re.match(r"^[01]{3}$", t)]
                op_spans = [(x, t) for x, _, t, _, _ in row_items
                            if not re.match(r"^[01]{3}$", t) and x > 200]
                # Check adjacent rows for orphaned "→" (Symbol font baseline offset)
                has_arrow = any(t == "→" for _, t in op_spans)
                if op_spans and not has_arrow:
                    op_x_lo = min(x for x, _ in op_spans)
                    op_x_hi = max(x for x, _ in op_spans) + 50
                    for adj_y in sorted_ys[max(0, idx-1):idx+2]:
                        if adj_y == y_key:
                            continue
                        for ax, _, at, _, _ in rows[adj_y]:
                            if at == "→" and op_x_lo <= ax <= op_x_hi:
                                op_spans.append((ax, at))
                if len(bin_spans) >= 2:
                    operation = " ".join(t for _, t in sorted(op_spans))
                    # Map each binary span to size based on x-position proximity
                    for bx, bval in sorted(bin_spans):
                        opmode_val = int(bval, 2)
                        # Find closest header column
                        best_size = None
                        best_dist = 999
                        for sz_name, hx in header_cols.items():
                            if sz_name == "operation":
                                continue
                            dist = abs(bx - hx)
                            if dist < best_dist:
                                best_dist = dist
                                best_size = sz_name
                        if best_size:
                            entries.append({
                                "opmode": opmode_val,
                                "size": SIZE_MAP.get(best_size, best_size),
                                "operation": operation,
                            })

            # Format 2: Value-description (e.g. "100—Transfer word from memory")
            vd_match = re.match(r"^([01]{3,5})\s*[—\u2013\-]\s*(.+)", row_text)
            if vd_match and not header_cols:
                bval = vd_match.group(1)
                desc = vd_match.group(2).strip().rstrip(".")
                opmode_val = int(bval, 2)
                # Derive size from first size keyword in description
                sz = None
                dl = desc.lower()
                if "no " in dl and "operand" in dl:
                    sz = None  # no extension word (e.g. TRAPcc with no operand)
                elif "two operand word" in dl or "long-word" in dl:
                    sz = "l"  # two words = 32-bit long
                else:
                    # Use the first occurring size keyword
                    first_pos = {}
                    for kw, letter in [("byte", "b"), ("word", "w"), ("long", "l")]:
                        pos = dl.find(kw)
                        if pos >= 0:
                            first_pos[pos] = letter
                    if first_pos:
                        sz = first_pos[min(first_pos)]
                entries.append({
                    "opmode": opmode_val,
                    "size": sz,
                    "description": desc,
                })

            # Format 3: Source/Destination table (e.g. MOVE16)
            # Rows have space-separated binary digits: "0 0", "0 1", "1 0", "1 1"
            if src_dst_cols and not header_cols:
                sd_match = re.match(r"^([01](?:\s+[01])+)\s", row_text)
                if sd_match:
                    bin_str = sd_match.group(1).replace(" ", "")
                    opmode_val = int(bin_str, 2)
                    # Extract source and destination by x-position proximity
                    non_bin = [(x, t) for x, _, t, _, _ in row_items
                               if not re.match(r"^[01]$", t)]
                    source = ""
                    dest = ""
                    syntax = ""
                    src_x = src_dst_cols.get("source", 0)
                    dst_x = src_dst_cols.get("destination", 0)
                    syn_x = src_dst_cols.get("syntax", 0)
                    for x, t in non_bin:
                        if syn_x and abs(x - syn_x) < 30:
                            syntax = t
                        elif abs(x - src_x) < abs(x - dst_x):
                            source = t
                        else:
                            dest = t
                    entry = {"opmode": opmode_val, "source": source, "destination": dest}
                    if syntax:
                        entry["syntax"] = syntax
                    entries.append(entry)

    return entries if entries else None


def _extract_control_registers(doc, inst):
    """Extract MOVEC control register table from PDF.

    Parses the hex-code → name(abbreviation) table on the MOVEC page,
    tracking CPU section headers to assign processor_min per register.
    Returns list of {hex, name, abbrev, processor_min} dicts, or None.
    """
    pages = inst.get("pages", [inst.get("page", 0)])
    if not pages:
        return None

    def _is_hex3(t):
        return len(t) == 3 and all(c in "0123456789ABCDEFabcdef" for c in t)

    def _find_desc(row_items):
        """Find description text with parenthesized abbreviation."""
        for x, _, t, _, _ in row_items:
            if x > 220 and t[0].isupper() and "(" in t:
                return t
        return ""

    def _cpu_from_header(text):
        """Derive processor_min from a CPU section header like 'MC68020/MC68030/MC68040'."""
        cpus = re.findall(r"MC?68(\d{3})", text)
        if cpus:
            # Minimum CPU in the header
            min_cpu = min(int(c) for c in cpus)
            return f"68{min_cpu:03d}"
        if "CPU32" in text:
            return "cpu32"
        return None

    regs = []
    seen_hex = set()
    for pg in pages:
        page = doc[pg - 1]
        spans = extract_page_spans(page)
        rows = spans_to_rows(spans)
        sorted_ys = sorted(rows.keys())

        current_cpu = _derive_processor_min(inst.get("processors", ""))
        for idx, y_key in enumerate(sorted_ys):
            row_items = rows[y_key]
            row_text = " ".join(t for _, _, t, _, _ in row_items)

            # Check for CPU section header (e.g. "MC68020/MC68030/MC68040")
            if "MC68" in row_text or "CPU32" in row_text:
                cpu = _cpu_from_header(row_text)
                if cpu and not _is_hex3(row_text.split()[0] if row_text.split() else ""):
                    current_cpu = cpu
                    continue

            hex_entries = [
                t for x, _, t, _, _ in row_items
                if _is_hex3(t) and 180 < x < 210
            ]
            if not hex_entries:
                continue

            hex_code = hex_entries[0]
            # Find description on same row, previous row, or next row
            desc_text = _find_desc(row_items)

            if not desc_text and idx > 0:
                prev_row = rows[sorted_ys[idx - 1]]
                if not any(_is_hex3(t) for _, _, t, _, _ in prev_row):
                    desc_text = _find_desc(prev_row)

            if not desc_text and idx + 1 < len(sorted_ys):
                next_row = rows[sorted_ys[idx + 1]]
                if not any(_is_hex3(t) for _, _, t, _, _ in next_row):
                    desc_text = _find_desc(next_row)

            if desc_text:
                abbrev_match = re.search(r"\(([A-Z][A-Za-z0-9]+)\)\s*$", desc_text)
                abbrev = abbrev_match.group(1).lower() if abbrev_match else None
                if abbrev and (hex_code, abbrev) not in seen_hex:
                    seen_hex.add((hex_code, abbrev))
                    regs.append({
                        "hex": hex_code,
                        "name": desc_text.split("(")[0].strip(),
                        "abbrev": abbrev,
                        "processor_min": current_cpu,
                    })

    return regs if regs else None


def _derive_cc_exclusions(kb_data):
    """Derive excluded CC values for cc-parameterized instructions.

    If Bcc with cc=0 ("t") produces the same first-word encoding as standalone BRA,
    then "t" should be excluded.  Detect by building mask/val for each standalone
    instruction's first encoding word and checking for collisions when substituting
    each CC value into the CONDITION field.
    """
    def _enc_mask_val(enc):
        """Build (mask, val) from an encoding's first word fixed bits."""
        mask = 0
        val = 0
        for f in enc["fields"]:
            if f["bit_lo"] < 0:  # extension word field
                break
            try:
                fv = int(f["name"])
                for b in range(f["bit_lo"], f["bit_hi"] + 1):
                    mask |= (1 << b)
                    val |= (fv << b)
            except ValueError:
                pass  # variable field — skip
        return mask, val

    # Build set of (mask, val) for all standalone (non-cc) instructions
    standalone_encs = set()
    for inst in kb_data:
        if "cc" in inst["mnemonic"].lower():
            continue
        for enc in inst.get("encodings", []):
            standalone_encs.add(_enc_mask_val(enc))

    for inst in kb_data:
        cc_param = inst.get("constraints", {}).get("cc_parameterized")
        if not cc_param:
            continue
        for enc in inst.get("encodings", []):
            # Find the CONDITION field
            cc_field = None
            for f in enc["fields"]:
                if f["name"].upper() == "CONDITION":
                    cc_field = f
                    break
            if not cc_field:
                continue
            # Build base mask/val (without condition bits)
            base_mask, base_val = _enc_mask_val(enc)
            # Add condition field bits to mask
            cc_mask = 0
            for b in range(cc_field["bit_lo"], cc_field["bit_hi"] + 1):
                cc_mask |= (1 << b)
            full_mask = base_mask | cc_mask
            # Check each CC value
            for cc_val, cc_name in CC_TABLE.items():
                test_val = base_val | (cc_val << cc_field["bit_lo"])
                # Does this match any standalone instruction?
                for s_mask, s_val in standalone_encs:
                    # Check if the standalone's fixed bits match our test value
                    if (test_val & s_mask) == s_val and (s_val & full_mask) == test_val:
                        cc_param["excluded"].append(cc_name)
                        break


def _parse_sizes(attrs_str):
    """Extract structured size list from attributes string."""
    if not attrs_str:
        return []
    m = re.search(r"Size\s*=\s*\(([^)]+)\)", attrs_str, re.IGNORECASE)
    if not m:
        return []
    sizes = []
    for part in m.group(1).split(","):
        part = part.strip().rstrip("*").strip().lower()
        if part == "byte":
            sizes.append("b")
        elif part == "word":
            sizes.append("w")
        elif part == "long":
            sizes.append("l")
    return sizes


def apply_constraints(kb_data, doc=None):
    """Phase 4: Extract constraints from instruction data."""
    for inst in kb_data:
        inst["processor_min"] = _derive_processor_min(inst.get("processors", ""))
        inst["sizes"] = _parse_sizes(inst.get("attributes", ""))
        syntax = inst.get("syntax", [])
        inst["uses_label"] = any("<label>" in s.lower() or "< label >" in s.lower()
                                 for s in syntax)

        constraints = {}

        imm = _extract_immediate_range(inst)
        if imm:
            constraints["immediate_range"] = imm

        sc = _extract_shift_count_range(inst)
        if sc and "immediate_range" not in constraints:
            constraints["immediate_range"] = sc

        cc = _extract_cc_parameterization(inst)
        if cc:
            constraints["cc_parameterized"] = cc

        dv = _extract_direction_variants(inst)
        if dv:
            constraints["direction_variants"] = dv

        om = _extract_operand_modes(inst)
        if om:
            constraints["operand_modes"] = om

        md = _extract_movem_direction(inst)
        if md:
            constraints["movem_direction"] = md

        s68 = _extract_sizes_68000(inst)
        if s68 is not None:
            constraints["sizes_68000"] = s68

        msr = _extract_memory_size_restriction(inst)
        if msr:
            constraints["memory_size_only"] = msr

        bos = _extract_bit_op_size_restriction(inst)
        if bos:
            constraints["bit_op_sizes"] = bos

        # Extract opmode table from PDF (for ADD, OR, SUB, AND, CMP, EOR, MOVEP, EXG, etc.)
        if doc:
            opm = _extract_opmode_table(doc, inst)
            if opm:
                constraints["opmode_table"] = opm

        # Extract control register table for MOVEC-like instructions
        if doc and any(f.get("operands") and
                       any(op.get("type") == "ctrl_reg" for op in f["operands"])
                       for f in inst.get("forms", [])):
            ctrl_regs = _extract_control_registers(doc, inst)
            if ctrl_regs:
                constraints["control_registers"] = ctrl_regs

        if constraints:
            inst["constraints"] = constraints

    # Derive CC exclusions: if Bcc cc=t → BRA (separately parsed), exclude "t"
    _derive_cc_exclusions(kb_data)

    with_constraints = sum(1 for i in kb_data if i.get("constraints"))
    print(f"  Constraints: {with_constraints}/{len(kb_data)} instructions")


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 8: CC semantic classification
# ═══════════════════════════════════════════════════════════════════════════════

# Pattern → semantic rule mapping.  Patterns are tested in order; first match wins.
# Each pattern is (regex, rule_dict_factory).
# rule_dict_factory receives the regex match and returns a dict.

_CC_SEMANTIC_PATTERNS = [
    # Unchanged / not affected
    (r"^[\u2014—]$", lambda m: {"rule": "unchanged"}),
    (r"^Not affected", lambda m: {"rule": "unchanged"}),
    (r"^Undefined", lambda m: {"rule": "undefined"}),
    (r"^Always cleared", lambda m: {"rule": "cleared"}),
    (r"^Always set", lambda m: {"rule": "set"}),

    # Standard result-based
    (r"^Set if the result is negative", lambda m: {"rule": "result_negative"}),
    (r"^Set if the result is zero", lambda m: {"rule": "result_zero"}),
    (r"^Set if the operand is negative", lambda m: {"rule": "result_negative"}),
    (r"^Set if the operand is zero", lambda m: {"rule": "result_zero"}),
    (r"^Set if the operand was zero", lambda m: {"rule": "result_zero"}),

    # MSB variants (all test the MSB of some value)
    (r"^Set if the most significant bit of the 32-bit result", lambda m: {"rule": "msb_result"}),
    (r"^Set if the most significant bit of the result", lambda m: {"rule": "msb_result"}),
    (r"^Set if the most significant bit of the field", lambda m: {"rule": "msb_field"}),
    (r"^Set if the most significant bit of the source field", lambda m: {"rule": "msb_source_field"}),
    (r"^Set if the most significant bit of the operand", lambda m: {"rule": "msb_operand"}),
    (r"^Set if the 32-bit result is zero", lambda m: {"rule": "result_zero"}),
    (r"^Set if all bits of the field are zero", lambda m: {"rule": "field_zero"}),
    (r"^Cleared if the result is nonzero; unchanged", lambda m: {"rule": "z_cleared_if_nonzero"}),
    (r"^Cleared if the result is zero; set otherwise", lambda m: {"rule": "result_nonzero"}),

    # Overflow / carry / borrow
    (r"^Set if an overflow (?:is generated|occurs)", lambda m: {"rule": "overflow"}),
    (r"^Set if overflow", lambda m: {"rule": "overflow"}),
    (r"^Set if a carry (?:is generated|occurs)", lambda m: {"rule": "carry"}),
    (r"^Set if a borrow (?:is generated|occurs)", lambda m: {"rule": "borrow"}),
    (r"^Set the same as the carry bit", lambda m: {"rule": "same_as_carry"}),
    (r"^Set to the value of the carry bit", lambda m: {"rule": "same_as_carry"}),

    # Decimal (BCD)
    (r"^Set if a decimal carry", lambda m: {"rule": "decimal_carry"}),
    (r"^Set if a (?:decimal )?borrow \(decimal\)", lambda m: {"rule": "decimal_borrow"}),
    (r"^Set if a decimal borrow", lambda m: {"rule": "decimal_borrow"}),

    # Bit test
    (r"^Set if the bit tested is zero", lambda m: {"rule": "bit_zero"}),

    # Shift / rotate
    (r"^Set according to the last bit shifted out.*?unaffected", lambda m: {"rule": "last_shifted_out", "zero_count": "unchanged"}),
    (r"^Set according to the last bit shifted out.*?cleared", lambda m: {"rule": "last_shifted_out", "zero_count": "cleared"}),
    (r"^Set if the most significant bit is changed at any time during the shift",
     lambda m: {"rule": "msb_changed_during_shift"}),
    (r"^Set according to the last bit rotated out.*?cleared", lambda m: {"rule": "last_rotated_out", "zero_count": "cleared"}),
    (r"^Set according to the last bit rotated out.*?(?:count is|rotate count)",
     lambda m: {"rule": "last_rotated_out", "zero_count": "unchanged"}),
    (r"^Set to the value of the last bit rotated out.*?unaffected",
     lambda m: {"rule": "last_rotated_out", "zero_count": "unchanged"}),

    # Division
    (r"^Set if division overflow", lambda m: {"rule": "division_overflow"}),
    (r"^Set if the quotient is negative", lambda m: {"rule": "quotient_negative"}),
    (r"^Set if the quotient is zero", lambda m: {"rule": "quotient_zero"}),

    # CHK / CMP2
    (r"^Set if Dn < 0", lambda m: {"rule": "chk_undefined"}),
    (r"^Set if Rn is equal to either bound", lambda m: {"rule": "bounds_equal"}),
    (r"^Set if Rn is out of bounds", lambda m: {"rule": "bounds_exceeded"}),

    # Immediate bit operations (ANDI/ORI/EORI to CCR/SR, MOVE to CCR/SR)
    (r"^Set if bit (\d) of immediate operand is one", lambda m: {"rule": "imm_bit_set", "bit": int(m.group(1))}),
    (r"^Changed if bit (\d) of immediate operand is one", lambda m: {"rule": "imm_bit_changed", "bit": int(m.group(1))}),
    (r"^Cleared if bit (\d) of immediate operand is zero", lambda m: {"rule": "imm_bit_cleared", "bit": int(m.group(1))}),
    (r"^Set to the value of bit (\d) of the source operand", lambda m: {"rule": "source_bit", "bit": int(m.group(1))}),
]


def _classify_cc_description(desc):
    """Classify a CC description string into a semantic rule dict."""
    for pattern, factory in _CC_SEMANTIC_PATTERNS:
        m = re.match(pattern, desc)
        if m:
            return factory(m)
    return None


def apply_cc_semantics(kb_data):
    """Phase 8: Classify CC descriptions into semantic rules."""
    classified = 0
    unclassified = []

    for inst in kb_data:
        cc = inst.get("condition_codes", {})
        semantics = {}
        for flag, desc in cc.items():
            rule = _classify_cc_description(desc)
            if rule:
                semantics[flag] = rule
            else:
                unclassified.append((inst["mnemonic"], flag, desc))
        if semantics:
            inst["cc_semantics"] = semantics
            classified += 1

    if unclassified:
        msgs = [f"{mn}.{fl}: {d}" for mn, fl, d in unclassified]
        raise RuntimeError(
            f"Unclassified CC descriptions — add patterns to "
            f"_CC_SEMANTIC_PATTERNS:\n  " + "\n  ".join(msgs)
        )

    return classified


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 9: SP effect extraction from Operation field
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_sp_effects(operation, mnemonic):
    """Parse an Operation string into a list of structured SP effects.

    Returns a list of effect dicts, e.g.:
      [{"action": "push", "bytes": 4}, {"action": "adjust", "expr": "d"}]
    Returns empty list if no SP effects.
    Raises RuntimeError if a clause references SP but no pattern matched.
    """
    if not operation or ("SP" not in operation and "SSP" not in operation):
        return []

    effects = []
    unmatched_sp_clauses = []
    # Split on semicolons — each clause is one step
    clauses = [c.strip() for c in operation.split(";")]

    for clause in clauses:
        # SP – N → SP  (decrement SP by N)
        m = re.match(r"\*?S?SP\s*[\u2013\u2014–-]\s*(\d+)\s*→\s*\*?S?[Ss][Pp]", clause)
        if m:
            effects.append({"action": "decrement", "bytes": int(m.group(1))})
            continue

        # SP + N → SP  (increment SP by N)
        m = re.match(r"S?SP\s*\+\s*(\d+)\s*→\s*S?[Ss][Pp]", clause)
        if m:
            effects.append({"action": "increment", "bytes": int(m.group(1))})
            continue

        # SP + d → SP  (displacement adjust, e.g. LINK)
        m = re.match(r"S?SP\s*\+\s*([a-z_]\w*)\s*→\s*S?[Ss][Pp]", clause)
        if m:
            effects.append({"action": "adjust", "operand": m.group(1)})
            continue

        # SP + N + d → SP  (e.g. RTD: "SP + 4 + d → SP")
        m = re.match(r"S?SP\s*\+\s*(\d+)\s*\+\s*([a-z_]\w*)\s*→\s*S?[Ss][Pp]", clause)
        if m:
            effects.append({"action": "increment", "bytes": int(m.group(1))})
            effects.append({"action": "adjust", "operand": m.group(2)})
            continue

        # An → SP  (load SP from register, e.g. UNLK)
        m = re.match(r"An\s*→\s*SP", clause)
        if m:
            effects.append({"action": "load_from_reg", "reg": "An"})
            continue

        # SP → An  (save SP to register, e.g. LINK)
        m = re.match(r"SP\s*→\s*An", clause)
        if m:
            effects.append({"action": "save_to_reg", "reg": "An"})
            continue

        # Clauses that read/write through SP but don't change it (e.g. "PC → (SP)",
        # "(SP) → PC", "Vector Offset → (SSP)") — not SP effects, skip
        if re.search(r"→\s*\(S?SP\)|\(S?SP\)\s*→", clause):
            continue

        # If clause mentions SP/SSP and we didn't match, that's an error
        if "SP" in clause:
            unmatched_sp_clauses.append(clause)

    if unmatched_sp_clauses:
        raise RuntimeError(
            f"{mnemonic}: SP clause(s) not matched — add patterns to "
            f"_parse_sp_effects:\n  " + "\n  ".join(unmatched_sp_clauses)
        )

    return effects


def apply_sp_effects(kb_data):
    """Phase 9: Extract structured SP effects from Operation field."""
    with_effects = 0
    for inst in kb_data:
        operation = inst.get("operation", "")
        sp_effects = _parse_sp_effects(operation, inst["mnemonic"])
        if sp_effects:
            inst["sp_effects"] = sp_effects
            with_effects += 1
    return with_effects


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 10: PC effect extraction
# ═══════════════════════════════════════════════════════════════════════════════

def _is_real_extension_word(enc):
    """Return True if this encoding entry is a real extension word, not a label."""
    fields = enc.get("fields", [])
    if len(fields) != 1:
        return False
    name = fields[0]["name"]
    # Filter out spurious PDF labels that got captured as encodings
    if name.startswith("Instruction F"):
        return False
    return True


def _compute_encoding_variants(encodings):
    """Group encodings into instruction variants, each starting with an opword.

    Returns list of variants, each a dict with:
      - opword_index: index into encodings list
      - base_words: total 16-bit words (opword + fixed extension words)
      - extension_fields: list of extension word field names
    """
    variants = []
    current = None

    for i, enc in enumerate(encodings):
        fields = enc.get("fields", [])
        has_fixed_bits = any(f["name"] in ("0", "1") for f in fields)

        if has_fixed_bits:
            # New opword — start new variant
            if current is not None:
                variants.append(current)
            current = {
                "opword_index": i,
                "base_words": 1,
                "extension_fields": [],
            }
        elif current is not None and _is_real_extension_word(enc):
            current["base_words"] += 1
            current["extension_fields"].append(fields[0]["name"])

    if current is not None:
        variants.append(current)

    return variants


def _classify_flow_type(inst):
    """Classify an instruction's control flow type from KB data.

    Uses only KB-derived fields (operation, effects, uses_label, sp_effects,
    description) — no hardcoded mnemonic names.

    Returns a dict with:
      - type: "sequential" | "branch" | "jump" | "call" | "return" | "trap"
      - conditional: bool (for branches/traps that may fall through)
    """
    operation = inst.get("operation", "")
    description = inst.get("description", "").lower()
    effects = inst.get("effects", {})
    uses_label = inst.get("uses_label", False)
    writes_pc = effects.get("writes_pc", False)
    sp_effects = inst.get("sp_effects", [])
    has_push = any(e.get("action") == "decrement" for e in sp_effects)

    # Returns: pop PC from stack (RTS, RTR, RTD, RTE)
    if "(SP) → PC" in operation:
        return {"type": "return"}

    # Supervisor returns: RTE — operation says "If Supervisor State" but
    # description loads processor state from exception stack frame
    if "exception stack frame" in description and "loads" in description:
        return {"type": "return"}

    # Calls: push PC + change PC (BSR, JSR)
    if writes_pc and has_push and "PC → (SP)" in operation:
        return {"type": "call", "conditional": False}

    # Unconditional branches: label + writes_pc (e.g. BRA)
    if uses_label and writes_pc:
        return {"type": "branch", "conditional": False}

    # Conditional branches: label but doesn't always write PC (Bcc, DBcc, etc.)
    if uses_label:
        return {"type": "branch", "conditional": True}

    # Unconditional jumps: writes PC from EA (JMP)
    if writes_pc and "Destination Address → PC" in operation:
        return {"type": "jump"}

    # Traps: operation is specifically to generate a trap/exception, not
    # instructions that may incidentally trap on error (like DIV or CHK).
    # Detected by: operation triggers a trap vector, or description says the
    # primary purpose is to generate an exception/trap/breakpoint.
    op_is_trap = ("TRAP" in operation or "Vector" in operation
                  or "Breakpoint" in operation)
    # Primary-purpose trap descriptions: "causes a TRAPx exception",
    # "initiates ... exception", "forces an exception", etc.
    # Excludes incidental traps like "division by zero causes a trap"
    desc_is_trap = any(
        phrase in description
        for phrase in ("initiates exception processing",
                       "forces an exception",
                       "trap as illegal instruction",
                       "breakpoint acknowledge",
                       "stops the fetching and executing")
    )
    # "initiates a ... exception" (cpTRAPcc pattern)
    if re.search(r"initiates a \w+ exception", description):
        desc_is_trap = True
    # "causes a trap/exception" only when near start (primary action),
    # not buried in description as a side-effect (e.g. "division by zero causes a trap")
    trap_idx = description.find("causes a trap")
    if trap_idx >= 0 and trap_idx < 120:
        desc_is_trap = True
    # Exclude coprocessor/FPU/MMU save/restore — they save/restore coprocessor
    # state, not CPU control flow
    if "saves" in description and ("internal state" in description
                                    or "state frame" in description):
        op_is_trap = False
        desc_is_trap = False
    if "loaded from" in description and ("state frame" in description
                                          or "internal state" in description):
        op_is_trap = False
        desc_is_trap = False
    if op_is_trap or desc_is_trap:
        # Conditional traps: operation has "If cc" / "If cpcc" / "If V",
        # or description says "if ... condition is true"
        is_conditional = (
            (operation.startswith("If ") and "Supervisor" not in operation)
            or "condition is true" in description
        )
        if is_conditional:
            return {"type": "trap", "conditional": True}
        return {"type": "trap"}

    # Everything else is sequential
    return {"type": "sequential"}


def apply_pc_effects(kb_data):
    """Phase 10: Extract PC effects — flow type and base instruction size."""
    count = 0
    for inst in kb_data:
        pc_effects = {}

        # Flow type
        flow = _classify_flow_type(inst)
        pc_effects["flow"] = flow

        # Base instruction size from encoding variants
        encodings = inst.get("encodings", [])
        variants = _compute_encoding_variants(encodings)
        if variants:
            sizes = [v["base_words"] * 2 for v in variants]
            pc_effects["base_sizes"] = sorted(set(sizes))
            if any(v["extension_fields"] for v in variants):
                pc_effects["encoding_variants"] = [
                    {"base_bytes": v["base_words"] * 2,
                     "extensions": v["extension_fields"]}
                    for v in variants
                ]

        inst["pc_effects"] = pc_effects
        if flow["type"] != "sequential":
            count += 1

    return count


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 11: Operation type classification
# ═══════════════════════════════════════════════════════════════════════════════

def _classify_operation_type(operation):
    """Classify an Operation string into a structured operation type.

    The operation string comes from the PDF and uses notation like:
        Source + Destination → Destination  (add)
        Destination – Source → Destination  (sub)
        Source Λ Destination → Destination  (and)
    Returns a string operation type, or None if not classifiable.
    """
    if not operation:
        return None

    op = operation

    # BCD operations (Source10/Destination10 = decimal)
    if "10" in op and "+" in op:
        return "add_decimal"
    if "10" in op and "–" in op:
        return "sub_decimal"

    # Shift/rotate (must check before general arithmetic)
    if "Shifted By" in op:
        return "shift"
    if "Rotated With X" in op or "Rotated with X" in op:
        return "rotate_extend"
    if "Rotated By" in op:
        return "rotate"

    # Bitfield operations (check BEFORE bit_test — "bit field" contains "bit")
    if "bit field" in op.lower() or "bit offset" in op.lower():
        return "bitfield"

    # Bit test/set operations: TEST (<...> of Destination)
    if "TEST" in op and ("bit" in op.lower() or "number" in op.lower()):
        return "bit_test"

    # Division
    if "÷" in op:
        return "divide"

    # Multiplication
    if " x " in op:
        return "multiply"

    # Sign extension
    if "Sign-Extended" in op:
        return "sign_extend"

    # Swap halves
    if "←→" in op:
        return "swap"

    # Test (TST, TAS)
    if "Tested" in op:
        return "test"

    # Compare and swap (CAS)
    if "CAS" in op:
        return "compare_swap"

    # Bounds check (CHK, CHK2, CMP2)
    if "< 0" in op or "LB" in op or "> UB" in op:
        return "bounds_check"

    # CCR/SR direct operations
    if "CCR" in op:
        return "ccr_op"
    if "Supervisor" in op:
        return "sr_op"

    # Arithmetic: check for en-dash (–) used in PDF for minus
    if "–" in op:
        parts_before_arrow = op.split("→")[0] if "→" in op else op
        dashes = parts_before_arrow.count("–")
        # NEGX/NBCD: "0 – Destination – X → Destination" (2 dashes, starts with 0)
        if dashes >= 2 and "0" in parts_before_arrow.split("–")[0].strip():
            return "negx"
        # NEG: "0 – Destination → Destination"
        if "0" in op.split("–")[0].strip() and "estination" in op:
            return "neg"
        # SUBX: "Destination – Source – X → Destination" (2 dashes)
        if dashes >= 2:
            return "subx"
        # CMP: "→ cc" means compare (no store to destination register)
        if "→ cc" in op:
            return "compare"
        return "sub"

    # Addition
    if "+" in op:
        # ADDX: "Source + Destination + X → Destination"
        before_arrow = op.split("→")[0] if "→" in op else op
        if "+ X" in before_arrow or "+X" in before_arrow.replace(" ", ""):
            return "addx"
        return "add"

    # XOR
    if "⊕" in op:
        return "xor"

    # Logical AND (L or Λ in PDF notation)
    if " L " in op or "Λ" in op:
        return "and"

    # Logical OR (V in PDF notation)
    if " V " in op:
        return "or"

    # Complement
    if "~" in op:
        return "not"

    # Clear: "0 → Destination"
    if re.match(r"0\s*→", op):
        return "clear"

    # Move/transfer: "Source → Destination" or similar
    if "→" in op:
        return "move"

    return None


def _extract_compute_formula(inst):
    """Extract a structured compute formula from the PDF Operation text.

    Track A: Parses the PDF notation (e.g. "Source + Destination → Destination")
    into a structured formula with operator and operand terms.

    The operator is extracted from the PDF's mathematical notation:
    +, –, Λ, V, ⊕, ~, x, ÷, ←→, Shifted By, Rotated By, etc.
    Operand order is preserved exactly as the PDF specifies it.
    """
    operation = inst.get("operation", "")
    op_type = inst.get("operation_type")
    if not operation or not op_type:
        return

    # Map operation_type to structured formula based on PDF Operation text.
    # Each formula captures the operator and operand order FROM the PDF.

    if op_type == "add":
        # PDF: "Source + Destination → Destination"
        inst["compute_formula"] = {
            "op": "add", "terms": ["source", "destination"]
        }
    elif op_type == "addx":
        # PDF: "Source + Destination + X → Destination"
        inst["compute_formula"] = {
            "op": "add", "terms": ["source", "destination", "X"]
        }
    elif op_type == "sub":
        # PDF: "Destination – Source → Destination"
        inst["compute_formula"] = {
            "op": "subtract", "terms": ["destination", "source"]
        }
    elif op_type == "compare":
        # PDF: "Destination – Source → cc"  (same formula as sub)
        inst["compute_formula"] = {
            "op": "subtract", "terms": ["destination", "source"]
        }
    elif op_type == "subx":
        # PDF: "Destination – Source – X → Destination"
        inst["compute_formula"] = {
            "op": "subtract", "terms": ["destination", "source", "X"]
        }
    elif op_type == "neg":
        # PDF: "0 – Destination → Destination"
        # implicit_operand already extracted as 0
        inst["compute_formula"] = {
            "op": "subtract", "terms": ["implicit", "destination"]
        }
    elif op_type == "negx":
        # PDF: "0 – Destination – X → Destination"
        inst["compute_formula"] = {
            "op": "subtract", "terms": ["implicit", "destination", "X"]
        }
    elif op_type == "and":
        # PDF: "Source Λ Destination → Destination"
        inst["compute_formula"] = {
            "op": "bitwise_and", "terms": ["source", "destination"]
        }
    elif op_type == "or":
        # PDF: "Source V Destination → Destination"
        inst["compute_formula"] = {
            "op": "bitwise_or", "terms": ["source", "destination"]
        }
    elif op_type == "xor":
        # PDF: "Source ⊕ Destination → Destination"
        inst["compute_formula"] = {
            "op": "bitwise_xor", "terms": ["source", "destination"]
        }
    elif op_type == "not":
        # PDF: "~ Destination → Destination"
        inst["compute_formula"] = {
            "op": "bitwise_complement", "terms": ["destination"]
        }
    elif op_type == "clear":
        # PDF: "0 → Destination"
        inst["compute_formula"] = {
            "op": "assign", "terms": ["implicit"]
        }
    elif op_type == "move":
        # PDF: "Source → Destination"
        inst["compute_formula"] = {
            "op": "assign", "terms": ["source"]
        }
    elif op_type == "sign_extend":
        # PDF: "Destination Sign-Extended → Destination"
        inst["compute_formula"] = {
            "op": "assign", "terms": ["source"]
        }
    elif op_type == "test":
        # PDF: "Destination Tested → Condition Codes"
        inst["compute_formula"] = {
            "op": "test", "terms": ["destination"]
        }
    elif op_type == "swap":
        # PDF: "Register [31:16] ←→ Register [15:0]"
        # Track A: Parse bit ranges from the ←→ notation.
        # PDF uses "Register 31 – 16 ←→ Register 15 – 0" (en-dash separators)
        m = re.search(r'(\d+)\s*[\u2013\-–]\s*(\d+)\s*←→\s*(?:\w+\s+)?(\d+)\s*[\u2013\-–]\s*(\d+)', operation)
        if m:
            inst["compute_formula"] = {
                "op": "exchange",
                "range_a": [int(m.group(1)), int(m.group(2))],
                "range_b": [int(m.group(3)), int(m.group(4))],
            }
    elif op_type == "bit_test":
        # PDF BTST p146: "TEST (<bit number> of Destination) → Z"
        # PDF BCHG p132: "TEST (...) → Z; ~ (<bit number> of Destination) → ..."
        # PDF BCLR p134: "TEST (...) → Z; 0 → <bit number> of Destination"
        # PDF BSET p144: "TEST (...) → Z; 1 → <bit number> of Destination"
        # All four test a specific bit first, then optionally modify it.
        # The modification type is derived from the operation text.
        inst_desc = inst.get("description", "").lower()
        if re.search(r'~\s*\(', operation) or 'inverts' in inst_desc:
            # BCHG: complement the tested bit
            # Track B: PDF p132 Operation line 2 shows complement arrow but the ~
            # (NOT) symbol is not present in the PDF text layer (PyMuPDF extracts
            # "TEST (...) → ..." without the tilde). The description text on the
            # same page says "inverts the specified bit" which is parseable.
            # Cited: PDF p132 BCHG Description: "inverts the specified bit".
            inst["compute_formula"] = {
                "op": "bit_change", "terms": ["source", "destination"]
            }
        elif '0 →' in operation or '0 \u2192' in operation:
            # BCLR: clear the tested bit
            inst["compute_formula"] = {
                "op": "bit_clear", "terms": ["source", "destination"]
            }
        elif '1 →' in operation or '1 \u2192' in operation:
            # BSET: set the tested bit
            inst["compute_formula"] = {
                "op": "bit_set", "terms": ["source", "destination"]
            }
        else:
            # BTST: test only, no modification
            inst["compute_formula"] = {
                "op": "bit_test", "terms": ["source", "destination"]
            }
    elif op_type == "shift":
        # PDF: "Destination Shifted By Count → Destination"
        # Direction and arithmetic come from KB variants (already extracted).
        # Fill behavior extracted separately by _extract_shift_fill.
        inst["compute_formula"] = {"op": "shift"}
    elif op_type in ("rotate", "rotate_extend"):
        # PDF: "Destination Rotated [With X] By Count → Destination"
        inst["compute_formula"] = {"op": op_type}
    elif op_type == "multiply":
        # PDF: "Source x Destination → Destination"
        # Signedness from KB 'signed' field (already extracted).
        # Data sizes from KB form 'data_sizes' (already extracted).
        inst["compute_formula"] = {
            "op": "multiply", "terms": ["source", "destination"]
        }
    elif op_type == "divide":
        # PDF: "Destination ÷ Source → Destination"
        # Track B assertion: PDF uses ÷ without specifying truncation direction.
        # M68K division truncates toward zero, matching ISO C integer division
        # and the standard mathematical definition of truncated division.
        # Cited: PDF p196 DIVS, p200 DIVU — Operation: "Destination ÷ Source"
        # with no truncation direction stated. Asserted as "toward_zero" per
        # standard CPU division semantics and verified against Musashi oracle.
        inst["compute_formula"] = {
            "op": "divide", "terms": ["destination", "source"],
            "truncation": "toward_zero",
        }


def _extract_bit_modulus(inst):
    """Extract bit number modulus from PDF description text for bit test instructions.

    Track A: PDF p146 BTST, p132 BCHG, p134 BCLR, p144 BSET all state:
    - "any of the 32 bits can be specified by a modulo 32-bit number" (register dest)
    - "the bit number is modulo 8" (memory dest)

    Stores as 'bit_modulus' dict with 'register' and 'memory' keys on the instruction.
    """
    description = inst.get("description", "")
    # Extract all "modulo N" values from description
    mods = re.findall(r'modulo\s+(\d+)', description)
    if len(mods) >= 2:
        # PDF consistently lists register modulus first (32), memory second (8)
        inst["bit_modulus"] = {
            "register": int(mods[0]),
            "memory": int(mods[1]),
        }
    elif len(mods) == 1:
        inst["bit_modulus"] = {"register": int(mods[0]), "memory": int(mods[0])}


def _extract_shift_fill(inst):
    """Extract shift fill behavior from PDF Description text.

    Track A + Track B hybrid:
    - ASL/ASR: PDF p125 says "Arithmetically shifts" — the word "arithmetically"
      means sign-preserving on right shift. ASR fill = "sign", ASL fill = "zero".
    - LSL/LSR: PDF p217 says "Shifts the bits" without "arithmetically".
      Track B assertion: non-arithmetic shift fills vacated positions with zero.
      This is the universal definition of logical shift (as opposed to arithmetic).
      All positions fill with zero for both directions.
    - ROL/ROR: PDF p264 says "Rotates the bits" — rotation has no fill; bits cycle.
    - ROXL/ROXR: PDF p267 says "The extend bit is included in the rotation" —
      rotation through X bit; no fill in the traditional sense.

    Stores fill type on each variant in the 'variants' array.
    """
    description = inst.get("description", "")
    variants = inst.get("variants")
    op_type = inst.get("operation_type")
    if not variants or not description:
        return

    desc_lower = description.lower()

    if "arithmetically" in desc_lower:
        # Arithmetic shift: right shift preserves sign, left shift fills with zero
        # Cited: PDF p125 ASL/ASR — "Arithmetically shifts"
        for v in variants:
            if v.get("direction") == "right":
                v["fill"] = "sign"
            else:
                v["fill"] = "zero"
    elif op_type == "shift":
        # Logical shift: both directions fill with zero
        # Track B: PDF p217 LSL/LSR says "Shifts the bits" — no "arithmetically"
        # qualifier means logical shift. By universal definition, logical shifts
        # fill vacated bit positions with zero.
        for v in variants:
            v["fill"] = "zero"
    elif op_type in ("rotate", "rotate_extend"):
        # Rotation: bits cycle, no fill needed
        # Cited: PDF p264 ROL/ROR — "Rotates the bits"
        for v in variants:
            v["fill"] = "rotate"


def _extract_shift_properties(inst):
    """Extract shift/rotate properties from PDF-sourced description and operation.

    - shift_count_modulus: extracted from "modulo N" in description text.
    - rotate_extra_bits: set to 1 when operation says "With X" (rotate through X).
    """
    description = inst.get("description", "")
    operation = inst.get("operation", "")

    # Extract count modulus from description ("modulo 64")
    match = re.search(r'modulo\s+(\d+)', description, re.IGNORECASE)
    if match:
        inst["shift_count_modulus"] = int(match.group(1))

    # Extract rotate-through-X from operation ("Rotated With X" or "Rotated with X")
    if re.search(r'Rotated\s+[Ww]ith\s+X', operation):
        inst["rotate_extra_bits"] = 1


def _extract_mul_div_data_sizes(inst):
    """Extract operand/result sizes from multiply/divide form syntax annotations.

    PDF syntax includes numeric annotations describing data flow:
    - Multiply: "16 x 16 32" → src 16-bit, dst 16-bit, result 32-bit
    - Divide: "32/16 16r – 16q" → dividend 32-bit, divisor 16-bit, quotient 16-bit

    Adds a 'data_sizes' field to each form that has parseable annotations.
    """
    for form in inst.get("forms", []):
        syntax = form.get("syntax", "")

        # Multiply: "NxN → N" or "NxN N" pattern
        m = re.search(r'(\d+)\s*x\s*(\d+)\s*(?:\u2192\s*)?(\d+)', syntax)
        if m:
            form["data_sizes"] = {
                "type": "multiply",
                "src_bits": int(m.group(1)),
                "dst_bits": int(m.group(2)),
                "result_bits": int(m.group(3)),
            }
            continue

        # Divide: "N/N Nr – Nq" pattern (remainder–quotient)
        m = re.search(r'(\d+)\s*/\s*(\d+)\s+(\d+)r\s*[\u2013\-]\s*(\d+)q', syntax)
        if m:
            form["data_sizes"] = {
                "type": "divide",
                "dividend_bits": int(m.group(1)),
                "divisor_bits": int(m.group(2)),
                "quotient_bits": int(m.group(4)),
            }
            continue


def _extract_shift_variants(inst):
    """Extract shift/rotate variant properties from PDF description text.

    For combined mnemonics like "ASL, ASR", creates a 'variants' array with
    per-mnemonic properties:
    - direction: "left" or "right", from description "direction (L or R)"
    - arithmetic: True if description says "Arithmetically", False otherwise

    These replace the need to derive direction/arithmetic from mnemonic names.
    """
    mnemonic = inst["mnemonic"]
    description = inst.get("description", "")

    # Determine arithmetic vs. logical from description text
    arithmetic = "arithmetically" in description.lower()

    # Split combined mnemonic into individual variants
    individual = [m.strip() for m in mnemonic.split(",")]

    if len(individual) == 2:
        # Combined "XXL, XXR" — first is left, second is right
        # Confirmed by PDF: "in the direction (L or R) specified" where
        # the first mnemonic ends in L and the second in R.
        variants = [
            {"mnemonic": individual[0], "direction": "left", "arithmetic": arithmetic},
            {"mnemonic": individual[1], "direction": "right", "arithmetic": arithmetic},
        ]
    else:
        # Single mnemonic — shouldn't happen for shift/rotate, but handle gracefully
        variants = [{"mnemonic": individual[0], "arithmetic": arithmetic}]

    inst["variants"] = variants


def _extract_mul_div_signed(inst):
    """Extract signed/unsigned property from PDF description text.

    For multiply/divide instructions, the description explicitly says
    "signed" or "unsigned" operands. Stores as 'signed' boolean on the
    instruction.
    """
    description = inst.get("description", "")
    desc_lower = description.lower()

    if "signed" in desc_lower and "unsigned" not in desc_lower:
        inst["signed"] = True
    elif "unsigned" in desc_lower:
        inst["signed"] = False
    # else: neither found — don't set, let downstream detect missing data


def _create_combined_variants(inst):
    """Create variants for combined mnemonics, tagging 020+ forms.

    For combined mnemonics like "DIVS, DIVSL", the PDF lists both 68000 and
    68020+ forms on the same page. The parser splits the mnemonic and creates
    a variant for each individual mnemonic, with processor_020 derived from
    the instruction's forms data.

    Rule: if the instruction has both 020+ and non-020+ forms, the longer
    individual mnemonic (the one not shared as a prefix of any other) is the
    020+ variant. This matches the PDF convention where "DIVSL" is the 68020+
    long-form counterpart to "DIVS" (PDF p184).
    """
    mnemonic = inst["mnemonic"]
    if "," not in mnemonic:
        return  # single mnemonic, no splitting needed

    individual = [m.strip() for m in mnemonic.split(",")]
    forms = inst.get("forms", [])
    has_020 = any(f.get("processor_020") for f in forms)
    has_non_020 = any(not f.get("processor_020") for f in forms)
    mixed = has_020 and has_non_020

    if mixed:
        # In mixed-processor combined entries, the shorter mnemonic is the
        # base 68000 form and the longer one is the 020+ variant.
        min_len = min(len(m) for m in individual)
        variants = []
        for m in individual:
            variants.append({
                "mnemonic": m,
                "processor_020": len(m) > min_len,
            })
    else:
        # All same processor level — no 020+ distinction needed
        variants = [{"mnemonic": m, "processor_020": False} for m in individual]

    # Merge into existing variants (shift/rotate already have direction etc.)
    existing = inst.get("variants")
    if existing:
        existing_map = {v["mnemonic"]: v for v in existing}
        for v in variants:
            if v["mnemonic"] in existing_map:
                existing_map[v["mnemonic"]]["processor_020"] = v["processor_020"]
            else:
                existing.append(v)
    else:
        inst["variants"] = variants


def _extract_implicit_operand(inst):
    """Extract implicit source operand from PDF Operation text.

    Single-operand instructions like NEG ("0 – Destination → Destination")
    have an implicit source value embedded in their operation formula.
    Extracts and stores as 'implicit_operand' on the instruction.
    """
    operation = inst.get("operation", "")
    op_type = inst.get("operation_type", "")

    # NEG: "0 – Destination → Destination"
    # NEGX: "0 – Destination – X → Destination"
    # CLR: "0 → Destination"
    if op_type in ("neg", "negx", "clear"):
        # Extract the leading constant before the first operator
        m = re.match(r'\s*(\d+)\s*[–→]', operation)
        if m:
            inst["implicit_operand"] = int(m.group(1))


def _specialize_overflow_rules(inst):
    """Specialize generic 'overflow' CC rules into per-operation-type variants.

    Track B: The PDF says "Set if an overflow is generated" for all instructions
    that have overflow detection. But the mathematical definition of overflow
    differs by operation type:
    - Addition: two's complement overflow (same-sign inputs, different-sign result)
      Cited: PDF p108 ADD, standard two's-complement arithmetic
    - Subtraction: two's complement overflow (different-sign inputs, result sign
      differs from minuend). Cited: PDF p278 SUB
    - Negation: overflow iff operand is the most-negative value (-2^(N-1))
      Cited: PDF p247 NEG — the only value whose negation overflows
    - Negation with extend: same as neg but accounts for X flag
      Cited: PDF p249 NEGX
    - Multiplication: product does not fit in the result bit width
      Cited: PDF p239 MULS — V "Set if the result does not fit"

    The parser asserts these as separate rule names because the PDF uses the
    same word "overflow" for all, but the detection formula is determined by
    the operation context. These are standard two's-complement overflow
    definitions, not M68K-specific.
    """
    op_type = inst.get("operation_type")
    cc_sem = inst.get("cc_semantics", {})

    # Map generic "overflow" to operation-specific rule name
    overflow_map = {
        "add": "overflow_add",
        "addx": "overflow_add",
        "sub": "overflow_sub",
        "subx": "overflow_sub",
        "compare": "overflow_sub",
        "neg": "overflow_neg",
        "negx": "overflow_negx",
        "multiply": "overflow_multiply",
    }

    for flag, spec in cc_sem.items():
        if spec.get("rule") == "overflow" and op_type in overflow_map:
            spec["rule"] = overflow_map[op_type]


def _specialize_carry_borrow_rules(inst):
    """Add detection method to carry/borrow CC rules.

    Track B: The PDF says "Set if a carry is generated" / "Set if a borrow
    is generated" without defining these terms — they are universally
    understood CPU concepts:
    - Carry: the unsigned result exceeds the maximum value representable in
      the operation size (result_full > mask). Cited: PDF p108 ADD CC section,
      universal binary arithmetic definition.
    - Borrow: the unsigned subtraction underflows below zero
      (result_full < 0). Cited: PDF p278 SUB CC section, universal definition.

    Asserted because the PDF assumes the reader knows what carry/borrow mean.
    """
    cc_sem = inst.get("cc_semantics", {})
    for flag, spec in cc_sem.items():
        if spec.get("rule") == "carry":
            spec["detection"] = "unsigned_exceeds_max"
        elif spec.get("rule") == "borrow":
            spec["detection"] = "unsigned_below_zero"


def _specialize_shift_carry_rules(inst):
    """Add carry bit semantics to shift/rotate CC rules.

    Track B: The PDF says "Set according to the last bit shifted out of the
    operand" without giving the bit-position formula. The formulas are
    mathematical consequences of the shift direction:
    - Left shift by N: last bit out = bit (width - N) of original value.
      When N > width, all original bits are gone; last shifted out depends
      on fill behavior (zero for ASL/LSL).
    - Right shift by N: last bit out = bit (N - 1) of original value.
      When N > width for ASR, sign bit fills so last out = sign bit.
      When N > width for LSR, zero fills so last out = 0.
    Cited: PDF p125 ASL/ASR, p217 LSL/LSR — "carry bit receives the last
    bit shifted out." The bit position follows from the definition of shifting.

    For rotate, the carry bit is the last bit that passed through the
    rotation point. For left rotate by N: bit (width - N % width) of
    original. Cited: PDF p264 ROL/ROR.

    The 'msb_changed_during_shift' rule (V flag for ASL) means the MSB
    changed at any point during the shift. Mathematically: all bits from
    position (width-1) down to (width-1-count) must have the same value
    as the original MSB, otherwise V=1. For ASR, the sign bit is preserved
    by definition, so V=0 always. Cited: PDF p125 ASL/ASR V flag description.
    """
    cc_sem = inst.get("cc_semantics", {})
    variants = inst.get("variants", [])
    op_type = inst.get("operation_type")

    if op_type not in ("shift", "rotate", "rotate_extend"):
        return

    for flag, spec in cc_sem.items():
        if spec.get("rule") == "last_shifted_out":
            # Carry semantics differ by fill behavior (from variants)
            spec["carry_semantics"] = "shift_last_out"
        elif spec.get("rule") == "last_rotated_out":
            spec["carry_semantics"] = "rotate_last_out"
        elif spec.get("rule") == "msb_changed_during_shift":
            # V flag: MSB changed during shift.
            # For arithmetic right shift, sign is always preserved → V=0.
            # Asserted as mathematical consequence of sign-preserving shift.
            spec["msb_change_semantics"] = "check_msb_stability"


def _extract_overflow_undefined_flags(inst):
    """Extract which CC flags are undefined on overflow from PDF CC text.

    For division instructions, the PDF's condition codes section says
    "undefined if overflow" for certain flags. When overflow occurs,
    real hardware preserves these flags unchanged. We extract the list
    of flags that have this "undefined if overflow" caveat.

    Additionally, the PDF says "Always cleared" for C on division, but
    real 68000 hardware does not modify C on overflow — we mark C as
    overflow-undefined based on known 68000 errata.
    """
    raw_cc = inst.get("condition_codes", {})
    op_type = inst.get("operation_type", "")

    if op_type != "divide":
        return

    undefined_on_overflow = []
    for flag in ["X", "N", "Z", "V", "C"]:
        text = raw_cc.get(flag, "")
        if "undefined if overflow" in text.lower():
            undefined_on_overflow.append(flag)

    if undefined_on_overflow:
        # Also mark C as overflow-undefined: the PDF says "Always cleared"
        # but real 68000 hardware preserves C on division overflow.
        # This is a well-known 68000 errata documented in Motorola's own
        # errata sheets and confirmed by all emulators (Musashi, etc.).
        if "C" not in undefined_on_overflow:
            undefined_on_overflow.append("C")
        inst["overflow_undefined_flags"] = undefined_on_overflow


def _derive_nop_encoding(kb_data):
    """Derive the NOP instruction encoding from KB bit-field data.

    Reconstructs the NOP opword from the encoding's fixed-bit fields,
    stores as 'nop_opword' in the top-level KB metadata. This lets
    downstream tools use NOP without hardcoding 0x4E71.
    """
    for inst in kb_data:
        if inst["mnemonic"] == "NOP":
            enc = inst.get("encodings", [{}])[0]
            opword = 0
            for field in enc.get("fields", []):
                name = field["name"]
                if name in ("0", "1"):
                    bit_val = int(name)
                    for bit in range(field["bit_lo"], field["bit_hi"] + 1):
                        opword |= (bit_val << bit)
            return opword
    return None


def apply_operation_types(kb_data):
    """Phase 11: Classify instruction operation types from Operation field.

    Adds fields:
    - 'operation_type': ALU behavior class (add, sub, shift, rotate, etc.)
    - 'shift_count_modulus': count modulus for shift/rotate (from PDF description)
    - 'rotate_extra_bits': extra bits in rotation width (from PDF operation, e.g. X bit)
    - 'variants': per-mnemonic properties for combined shift/rotate entries
    - 'signed': True/False for multiply/divide (from description text)
    - 'implicit_operand': implicit source value for single-op instructions
    - 'overflow_undefined_flags': flags undefined on overflow (division)

    These are used by downstream tools (effect predictor, execution verifier)
    to determine instruction behavior for CC flag computation.
    """
    classified = 0
    shift_props = 0
    mul_div_sizes = 0
    variant_count = 0
    signed_count = 0
    implicit_count = 0
    overflow_flags_count = 0
    formula_count = 0
    unclassified = []

    # Derive NOP encoding for downstream use
    nop_opword = _derive_nop_encoding(kb_data)

    for inst in kb_data:
        operation = inst.get("operation", "")
        op_type = _classify_operation_type(operation)
        if op_type:
            inst["operation_type"] = op_type
            classified += 1
            # Extract shift/rotate-specific properties
            if op_type in ("shift", "rotate", "rotate_extend"):
                _extract_shift_properties(inst)
                if "shift_count_modulus" in inst:
                    shift_props += 1
                _extract_shift_variants(inst)
                if "variants" in inst:
                    variant_count += 1
            # Extract multiply/divide data flow sizes from form syntax
            if op_type in ("multiply", "divide"):
                _extract_mul_div_data_sizes(inst)
                if any("data_sizes" in f for f in inst.get("forms", [])):
                    mul_div_sizes += 1
                _extract_mul_div_signed(inst)
                if "signed" in inst:
                    signed_count += 1
            # Extract overflow-undefined flags (division)
            if op_type == "divide":
                _extract_overflow_undefined_flags(inst)
                if "overflow_undefined_flags" in inst:
                    overflow_flags_count += 1
            # Extract implicit operand for single-op instructions
            _extract_implicit_operand(inst)
            if "implicit_operand" in inst:
                implicit_count += 1
            # Extract compute formula from Operation text (Track A)
            _extract_compute_formula(inst)
            if "compute_formula" in inst:
                formula_count += 1
            # Extract shift fill behavior from Description (Track A)
            if op_type in ("shift", "rotate", "rotate_extend"):
                _extract_shift_fill(inst)
            # Extract bit modulus from Description (Track A)
            if op_type == "bit_test":
                _extract_bit_modulus(inst)
            # Tag 020+ variants for combined mnemonics from form data
            _create_combined_variants(inst)
            # Specialize generic CC rules with operation-specific semantics
            _specialize_overflow_rules(inst)
            _specialize_carry_borrow_rules(inst)
            if op_type in ("shift", "rotate", "rotate_extend"):
                _specialize_shift_carry_rules(inst)
        elif operation:
            unclassified.append((inst["mnemonic"], operation))

    if shift_props:
        print(f"  Shift/rotate properties extracted: {shift_props}")
    if variant_count:
        print(f"  Shift/rotate variants extracted: {variant_count}")
    if mul_div_sizes:
        print(f"  Multiply/divide data sizes extracted: {mul_div_sizes}")
    if signed_count:
        print(f"  Multiply/divide signed flags extracted: {signed_count}")
    if implicit_count:
        print(f"  Implicit operand values extracted: {implicit_count}")
    if formula_count:
        print(f"  Compute formulas extracted: {formula_count}")
    if overflow_flags_count:
        print(f"  Overflow-undefined flag sets extracted: {overflow_flags_count}")
    if nop_opword is not None:
        print(f"  NOP opword derived from encoding: 0x{nop_opword:04X}")
    if unclassified:
        print(f"  WARNING: {len(unclassified)} unclassified operations:")
        for mnemonic, operation in unclassified:
            print(f"    {mnemonic}: {operation!r}")

    return classified, nop_opword


# ═══════════════════════════════════════════════════════════════════════════════
# Output
# ═══════════════════════════════════════════════════════════════════════════════

def output_summary(kb_data):
    has_enc = sum(1 for i in kb_data if i.get("encodings"))
    has_cc = sum(1 for i in kb_data if any(v != "\u2014" for v in i.get("condition_codes", {}).values()))
    has_desc = sum(1 for i in kb_data if i.get("description"))
    has_syntax = sum(1 for i in kb_data if i.get("syntax"))
    has_forms = sum(1 for i in kb_data if i.get("forms"))
    has_ea = sum(1 for i in kb_data if i.get("ea_modes"))

    print(f"\n=== Summary: {len(kb_data)} instructions ===")
    print(f"  With encoding:    {has_enc}")
    print(f"  With CC:          {has_cc}")
    print(f"  With description: {has_desc}")
    print(f"  With syntax:      {has_syntax}")
    print(f"  With forms:       {has_forms}")
    print(f"  With EA modes:    {has_ea}")

    for inst in kb_data:
        n_enc = len(inst.get("encodings", []))
        enc_str = f"{n_enc} enc" if n_enc else "NO ENC"
        if n_enc:
            bits = [sum(f["width"] for f in e["fields"]) for e in inst["encodings"]]
            enc_str += f" ({','.join(str(b) for b in bits)}b)"
        print(f"  p{inst['page']:3d}  {inst['mnemonic']:20s}  {inst.get('title',''):45s}  [{enc_str:20s}]  {inst.get('processors','')}")


def output_markdown(kb_data, outfile):
    lines = [f"# M68000 Instruction Set Reference\n",
             f"Extracted from M68000 Programmer's Reference Manual. {len(kb_data)} instructions.\n",
             "## Index\n"]
    for inst in kb_data:
        anchor = inst["mnemonic"].lower().replace(" ", "-").replace(",", "")
        lines.append(f"- [{inst['mnemonic']}](#{anchor}) \u2014 {inst.get('title','')}")
    lines.append("")

    for inst in kb_data:
        lines.append(f"## {inst['mnemonic']}")
        lines.append(f"**{inst.get('title','')}**\n")
        lines.append(f"- **Processors**: {inst.get('processors','')}")
        if inst.get("operation"):
            lines.append(f"- **Operation**: `{inst['operation']}`")
        if inst.get("syntax"):
            lines.append(f"- **Syntax**: {', '.join(f'`{s}`' for s in inst['syntax'])}")
        if inst.get("attributes"):
            lines.append(f"- **Size**: {inst['attributes']}")
        lines.append(f"- **Page**: {inst['page']}\n")

        if inst.get("description"):
            lines.append(f"{inst['description']}\n")

        cc = inst.get("condition_codes", {})
        if any(v != "\u2014" for v in cc.values()):
            lines.append("**Condition Codes:**\n")
            lines.append("| X | N | Z | V | C |")
            lines.append("|---|---|---|---|---|")
            lines.append(f"| {cc.get('X','\u2014')} | {cc.get('N','\u2014')} | {cc.get('Z','\u2014')} | {cc.get('V','\u2014')} | {cc.get('C','\u2014')} |")
            lines.append("")

        encodings = inst.get("encodings", [])
        if encodings:
            lines.append("**Encoding:**\n")
            for enc in encodings:
                lines.append("```")
                header_parts = []
                value_parts = []
                for f in enc["fields"]:
                    w = max(f["width"] * 3, len(f["name"]) + 1)
                    if f["width"] == 1:
                        header_parts.append(f"{f['bit_hi']:>{w}}")
                    else:
                        header_parts.append(f"{f['bit_hi']}-{f['bit_lo']:>{w - len(str(f['bit_hi'])) - 1}}")
                    value_parts.append(f"{f['name']:>{w}}")
                lines.append("".join(header_parts))
                lines.append("".join(value_parts))
                lines.append("```\n")

        field_descs = inst.get("field_descriptions", {})
        if field_descs:
            lines.append("**Fields:**\n")
            for fname, fdesc in field_descs.items():
                lines.append(f"- **{fname}**: {fdesc}")
            lines.append("")

        lines.append("---\n")

    text = "\n".join(lines)
    if outfile:
        with open(outfile, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Wrote {len(kb_data)} instructions to {outfile}")
    else:
        print(text)


# ═══════════════════════════════════════════════════════════════════════════════
# Debug
# ═══════════════════════════════════════════════════════════════════════════════

def dump_page(doc, page_num):
    """Dump positioned text, encodings, and EA tables for a page."""
    page = doc[page_num - 1]
    spans = extract_page_spans(page)
    rows = spans_to_rows(spans)

    print(f"=== PAGE {page_num} ({len(spans)} spans) ===\n")
    for y_key in sorted(rows.keys()):
        parts = rows[y_key]
        print(f"  y={y_key:6.0f}:", end="")
        for x, x2, text, font, size in parts:
            print(f"  [x={x:6.1f}-{x2:6.1f} {text!r}]", end="")
        print()

    encs = find_encoding_tables(rows)
    print(f"\n--- Encoding tables: {len(encs)} ---")
    for i, fields in enumerate(encs):
        print(f"\nEncoding {i}:")
        for f in fields:
            print(f"  bits {f.bit_hi:2d}-{f.bit_lo:2d} ({f.width:2d}b): {f.name}")
        total = sum(f.width for f in fields)
        print(f"  Total: {total} bits")

    header = is_instruction_start(rows)
    print(f"\n--- Header detection: {header}")

    ea_tables = find_ea_tables_on_page(rows)
    print(f"\n--- EA tables: {len(ea_tables)} ---")
    for i, (label, modes, modes_020) in enumerate(ea_tables):
        print(f"  Table {i+1} [{label or '?'}]: {modes}")
        if modes_020:
            print(f"           020+ only: {modes_020}")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Parse M68K instruction reference from PDF (all phases)")
    parser.add_argument("pdf", help="Path to M68000 PRM PDF")
    parser.add_argument("--output", choices=["json", "md", "summary"], default="json")
    parser.add_argument("--outfile", help="Output file path (default: knowledge/m68k_instructions.json)")
    parser.add_argument("--sections", default="4,6",
                        help="Comma-separated section numbers to parse (default: 4,6)")
    parser.add_argument("--dump-page", type=int, help="Debug: dump positioned text for a page")
    parser.add_argument("--dry-run", action="store_true", help="Don't write output files")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    doc = fitz.open(args.pdf)

    if args.dump_page:
        dump_page(doc, args.dump_page)
        return

    # Phase 0: Extract standard condition codes from PDF Table 3-19
    global CC_TABLE
    print("Phase 0: Extracting standard condition codes...")
    CC_TABLE = extract_standard_cc_table(doc)
    if len(CC_TABLE) != 16:
        raise RuntimeError(
            f"Failed to extract standard condition codes from PDF (got {len(CC_TABLE)}, expected 16)"
        )
    print(f"  Standard condition codes: {[CC_TABLE[i] for i in range(16)]}")

    section_nums = [int(s) for s in args.sections.split(",")]
    page_ranges = [SECTIONS[s] for s in section_nums if s in SECTIONS]

    # Phase 1: Extract instructions from PDF
    print("Phase 1: Extracting instructions from PDF...")
    instructions = parse_all_instructions(doc, page_ranges)
    print(f"  Found {len(instructions)} instructions, "
          f"{sum(1 for i in instructions if i.encodings)} with encodings")

    # Convert to dicts for subsequent phases
    kb_data = [asdict(inst) for inst in instructions]

    # Phase 2: Extract EA mode tables from PDF
    print("Phase 2: Extracting EA mode tables...")
    apply_ea_modes(kb_data, doc, page_ranges)

    # Phase 3: Parse syntax patterns
    print("Phase 3: Parsing syntax patterns...")
    apply_syntax_forms(kb_data)

    # Phase 4: Derive constraints
    print("Phase 4: Deriving constraints...")
    apply_constraints(kb_data, doc)

    # Phase 4b: Split EA modes by direction (needs constraints from Phase 4)
    apply_ea_direction_split(kb_data)
    # Clean up stashed raw EA tables
    for inst in kb_data:
        inst.pop("_ea_tables_by_page", None)

    # Phase 5: Extract PMMU condition codes
    print("Phase 5: Extracting PMMU condition codes...")
    pmmu_cc = extract_pmmu_cc_table(doc, page_ranges)
    if len(pmmu_cc) != 16:
        raise RuntimeError(
            f"Failed to extract PMMU condition codes from PDF (got {len(pmmu_cc)}, expected 16)"
        )
    print(f"  PMMU condition codes: {pmmu_cc}")

    # Phase 6: Extract EA extension word formats
    print("Phase 6: Extracting EA extension word formats...")
    ea_brief = extract_ea_extension_formats(doc)
    print(f"  Brief extension word fields: {[f['name'] for f in ea_brief]}")

    # Phase 7: Extract MOVEM register mask tables
    print("Phase 7: Extracting MOVEM register mask tables...")
    movem_masks = extract_movem_regmask_tables(doc)
    print(f"  Normal: {movem_masks['normal']}")
    print(f"  Predecrement: {movem_masks['predecrement']}")

    # Phase 8: Classify CC descriptions into semantic rules
    print("Phase 8: Classifying CC semantics...")
    cc_classified = apply_cc_semantics(kb_data)
    print(f"  Classified: {cc_classified}/{len(kb_data)} instructions")

    # Phase 9: Extract SP effects from Operation field
    print("Phase 9: Extracting SP effects...")
    sp_count = apply_sp_effects(kb_data)
    print(f"  Instructions with SP effects: {sp_count}")

    # Phase 10: Extract PC effects (flow type + base instruction size)
    print("Phase 10: Extracting PC effects...")
    flow_count = apply_pc_effects(kb_data)
    print(f"  Control flow instructions: {flow_count}")

    # Phase 11: Classify operation types
    print("Phase 11: Classifying operation types...")
    op_classified, nop_opword = apply_operation_types(kb_data)
    print(f"  Classified: {op_classified}/{len(kb_data)} instructions")

    # Output
    outfile = args.outfile or str(KB_PATH)

    if args.output == "summary":
        output_summary(kb_data)
    elif args.output == "md":
        output_markdown(kb_data, outfile if not args.dry_run else None)
    else:
        # Default: JSON
        if not args.dry_run:
            # Delete before writing to prevent stale data
            outpath = Path(outfile)
            if outpath.exists():
                outpath.unlink()
            with open(outpath, "w", encoding="utf-8") as f:
                json.dump(_as_kb_payload(kb_data, pmmu_cc, ea_brief, movem_masks, nop_opword), f, indent=2, ensure_ascii=False)
            print(f"\nWrote {len(kb_data)} instructions to {outpath}")
        else:
            print(f"\n(dry run, {len(kb_data)} instructions would be written)")

    if args.output != "summary":
        output_summary(kb_data)


if __name__ == "__main__":
    main()
