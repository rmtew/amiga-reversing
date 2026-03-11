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


def _as_kb_payload(kb_data: list[dict], pmmu_cc: list[str]) -> dict:
    return {
        "_meta": {
            "condition_codes": _kb_condition_codes(),
            "pmmu_condition_codes": pmmu_cc,
            "cpu_hierarchy": CPU_HIERARCHY,
        },
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
        bit_15_x = None
        for cx, bn in x_to_bit.items():
            if bn == 15:
                bit_15_x = cx
                break
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

            if first_cluster_started:
                current_cluster.extend(enc_items)

        if current_cluster:
            all_clusters.append(current_cluster)

        for cluster in all_clusters:
            sorted_cluster = sorted(cluster,
                key=lambda e: (0 if e[2] in ("0", "1") else 1, e[5], e[1] - e[0]))
            fields = _map_values_to_bits(x_to_bit, sorted_cluster)
            if fields and sum(f.width for f in fields) >= 15:
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
                    best = max(candidates, key=lambda f: f.bbox_width)
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
        pattern = rf"{flag}\s*[\u2014\-\u2013]\s*(.+?)(?:\n|$)"
        fm = re.search(pattern, text)
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
    """Find a field description by name, case-insensitive."""
    fn_lower = field_name.lower()
    for fd_key, fd_val in fd.items():
        if fd_key.lower() == fn_lower:
            return fd_val
        if fd_key.lower().replace(" ", "").replace("/", "") == fn_lower.replace(" ", "").replace("/", ""):
            return fd_val
    return ""


    # Field names that represent structural parts of the encoding, not immediate data
_STRUCTURAL_FIELD_RE = re.compile(
    r"^(REGISTER|MODE|OPMODE|CONDITION|SIZE|CACHE|SCOPE|ID|FC|MASK|"
    r"LEVEL|NUM|OFFSET|WIDTH|A/D|D/A|R/?W|R/M|dr|i/r|D[couwqrhl]|"
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
                return {
                    "min": 0,
                    "max": (1 << bit_width) - 1,
                    "field": field_name,
                    "bits": bit_width,
                }
            dl = desc.lower()

            if "sign-extended" in dl or "sign extended" in dl:
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
    # Map processor model patterns to hierarchy entries.
    # Coprocessors (FPU 68881/68882, MMU 68851) imply 68020 as the minimum CPU.
    _COPROCESSOR_IMPLIES = "68020"
    best_idx = -1

    for proc_token in re.findall(r"MC?68\w+|CPU32", processors):
        token = proc_token.lstrip("MC")  # "MC68020" -> "68020"
        # Strip EC/LC variants: "68EC030" -> "68030", "68LC040" -> "68040"
        core = re.sub(r"^68[A-Z]{1,2}(\d)", r"68\1", token)

        if core in ("68881", "68882", "68851"):
            # Coprocessor — implies 68020
            idx = order.index(_COPROCESSOR_IMPLIES) if _COPROCESSOR_IMPLIES in order else -1
        elif core == "CPU32":
            return "cpu32"
        elif core in order:
            idx = order.index(core)
        else:
            # Try prefix match (68008 -> 68000)
            idx = next((order.index(o) for o in order if core.startswith(o[:4])), -1)

        if idx > best_idx:
            best_idx = idx

    return order[best_idx] if best_idx >= 0 else "68000"


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

        current_cpu = "68010"  # Default for MOVEC
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
                json.dump(_as_kb_payload(kb_data, pmmu_cc), f, indent=2, ensure_ascii=False)
            print(f"\nWrote {len(kb_data)} instructions to {outpath}")
        else:
            print(f"\n(dry run, {len(kb_data)} instructions would be written)")

    if args.output != "summary":
        output_summary(kb_data)


if __name__ == "__main__":
    main()
