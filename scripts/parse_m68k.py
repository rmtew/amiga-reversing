#!/usr/bin/env python3
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

EA_ALL = ["dn", "an", "ind", "postinc", "predec", "disp", "index",
          "absw", "absl", "pcdisp", "pcindex", "imm"]
EA_ORDER = {m: i for i, m in enumerate(EA_ALL)}

# Standard M68K condition code encoding (architectural)
CC_TABLE = {
    0:  "t",   1:  "f",   2:  "hi",  3:  "ls",
    4:  "cc",  5:  "cs",  6:  "ne",  7:  "eq",
    8:  "vc",  9:  "vs",  10: "pl",  11: "mi",
    12: "ge",  13: "lt",  14: "gt",  15: "le",
}


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


def find_encoding_tables(rows) -> list[list[BitField]]:
    """Find bit encoding tables using positioned text rows.

    Only accepts encoding tables preceded by "Instruction Format:" or a
    sub-format label (e.g. "Register Rotate:"), filtering out false positives
    from addressing mode tables and explanatory diagrams.
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
        is_real_encoding = False
        for prev_idx in range(idx - 1, max(idx - 8, -1), -1):
            prev_y = sorted_ys[prev_idx]
            if y_key - prev_y > 60:
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

        # Collect ALL value rows below the header first, then process.
        min_col_x = min(x_to_bit.keys()) - 15
        header_y = y_key

        merged_row = []  # (x, x2, text, font, size, y)
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
                        if e[2] in ("0", "1") or len(e[2].split()) <= 4]
            if enc_items:
                merged_row.extend(enc_items)

        if merged_row:
            sorted_merged = sorted(merged_row,
                key=lambda e: (0 if e[2] in ("0", "1") else 1, -e[5], e[1] - e[0]))
            fields = _map_values_to_bits(x_to_bit, sorted_merged)
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
        current_name = None
        current_desc = []
        for line in field_section.group(1).split("\n"):
            line = line.strip()
            fm = re.match(r"^(.+?)\s*[Ff]ield\s*[\u2014\u2013\-]\s*(.+)", line)
            if fm:
                if current_name:
                    field_descs[current_name] = " ".join(current_desc)
                current_name = fm.group(1).strip()
                current_desc = [fm.group(2).strip()]
            elif current_name and line:
                if line.startswith("If ") or line.startswith("0 ") or line.startswith("1 "):
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

    _fix_coprocessor_encodings(parsed)
    return parsed


# --- Coprocessor encoding fixes (PDF-GAP: multi-word conflation) ---

def _f(val, bit):
    """Helper: single fixed bit field."""
    return {"name": val, "bit_hi": bit, "bit_lo": bit, "width": 1}

def _mf(name, hi, lo):
    """Helper: multi-bit named field."""
    return {"name": name, "bit_hi": hi, "bit_lo": lo, "width": hi - lo + 1}

def _fix_coprocessor_encodings(instructions):
    """Replace mis-parsed coprocessor encodings with known correct formats."""
    COPROC_FIXES = {
        "cpBcc": [
            _f("1",15), _f("1",14), _f("1",13), _f("1",12),
            _mf("COPROCESSOR ID",11,9), _f("0",8), _f("1",7),
            _mf("SIZE",6,6), _mf("COPROCESSOR CONDITION",5,0),
        ],
        "cpDBcc": [
            _f("1",15), _f("1",14), _f("1",13), _f("1",12),
            _mf("COPROCESSOR ID",11,9), _f("0",8), _f("0",7), _f("1",6),
            _f("0",5), _f("0",4), _f("1",3), _mf("REGISTER",2,0),
        ],
        "cpGEN": [
            _f("1",15), _f("1",14), _f("1",13), _f("1",12),
            _mf("COPROCESSOR ID",11,9), _f("0",8), _f("0",7), _f("0",6),
            _mf("MODE",5,3), _mf("REGISTER",2,0),
        ],
        "cpScc": [
            _f("1",15), _f("1",14), _f("1",13), _f("1",12),
            _mf("COPROCESSOR ID",11,9), _f("0",8), _f("0",7), _f("1",6),
            _mf("MODE",5,3), _mf("REGISTER",2,0),
        ],
        "cpTRAPcc": [
            _f("1",15), _f("1",14), _f("1",13), _f("1",12),
            _mf("COPROCESSOR ID",11,9), _f("0",8), _f("0",7), _f("1",6),
            _f("1",5), _f("1",4), _f("1",3), _mf("OPMODE",2,0),
        ],
    }

    PMMU_FIXES = {
        "PDBcc": [_f("1",15), _f("1",14), _f("1",13), _f("1",12),
                  _f("0",11), _f("0",10), _f("0",9),
                  _f("0",8), _f("0",7), _f("1",6), _f("0",5),
                  _f("0",4), _f("1",3), _mf("REGISTER",2,0)],
        "PScc": [_f("1",15), _f("1",14), _f("1",13), _f("1",12),
                 _f("0",11), _f("0",10), _f("0",9),
                 _f("0",8), _f("0",7), _f("1",6),
                 _mf("MODE",5,3), _mf("REGISTER",2,0)],
        "PTRAPcc": [_f("1",15), _f("1",14), _f("1",13), _f("1",12),
                    _f("0",11), _f("0",10), _f("0",9),
                    _f("0",8), _f("0",7), _f("1",6), _f("1",5),
                    _f("1",4), _f("1",3), _mf("OPMODE",2,0)],
        "PFLUSH PFLUSHA": [_f("1",15), _f("1",14), _f("1",13), _f("1",12),
                           _f("0",11), _f("0",10), _f("0",9),
                           _f("0",8), _f("0",7), _f("0",6),
                           _mf("MODE",5,3), _mf("REGISTER",2,0)],
        "PFLUSHR": [_f("1",15), _f("1",14), _f("1",13), _f("1",12),
                    _f("0",11), _f("0",10), _f("0",9),
                    _f("0",8), _f("0",7), _f("0",6),
                    _mf("MODE",5,3), _mf("REGISTER",2,0)],
    }

    MOVE16_FIX = {
        "MOVE16": [_f("1",15), _f("1",14), _f("1",13), _f("1",12),
                   _f("0",11), _f("1",10), _f("1",9), _f("0",8),
                   _f("0",7), _f("0",6), _mf("OPMODE",5,3),
                   _mf("REGISTER",2,0)],
    }

    OTHER_FIXES = {
        "cpRESTORE": [_f("1",15), _f("1",14), _f("1",13), _f("1",12),
                      _mf("COPROCESSOR ID",11,9), _f("1",8), _f("0",7), _f("1",6),
                      _mf("MODE",5,3), _mf("REGISTER",2,0)],
        "cpSAVE": [_f("1",15), _f("1",14), _f("1",13), _f("1",12),
                   _mf("COPROCESSOR ID",11,9), _f("1",8), _f("0",7), _f("0",6),
                   _mf("MODE",5,3), _mf("REGISTER",2,0)],
        "MOVEM": [_f("0",15), _f("1",14), _f("0",13), _f("0",12),
                  _f("1",11), _mf("dr",10,10), _f("0",9), _f("0",8), _f("1",7),
                  _mf("SIZE",6,6), _mf("MODE",5,3), _mf("REGISTER",2,0)],
        "ADDI": [_f("0",15), _f("0",14), _f("0",13), _f("0",12),
                 _f("0",11), _f("1",10), _f("1",9), _f("0",8),
                 _mf("SIZE",7,6), _mf("MODE",5,3), _mf("REGISTER",2,0)],
        "SUBI": [_f("0",15), _f("0",14), _f("0",13), _f("0",12),
                 _f("0",11), _f("1",10), _f("0",9), _f("0",8),
                 _mf("SIZE",7,6), _mf("MODE",5,3), _mf("REGISTER",2,0)],
        "CMPI": [_f("0",15), _f("0",14), _f("0",13), _f("0",12),
                 _f("1",11), _f("1",10), _f("0",9), _f("0",8),
                 _mf("SIZE",7,6), _mf("MODE",5,3), _mf("REGISTER",2,0)],
    }

    all_fixes = {**COPROC_FIXES, **PMMU_FIXES, **MOVE16_FIX, **OTHER_FIXES}
    for inst in instructions:
        if inst.mnemonic in all_fixes:
            inst.encodings = [{"fields": all_fixes[inst.mnemonic]}]


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

    with_ea = sum(1 for inst in kb_data if inst.get("ea_modes"))
    with_020 = sum(1 for inst in kb_data if inst.get("ea_modes_020"))
    print(f"  EA modes: {with_ea}/{len(kb_data)} instructions, {with_020} with 020+ modes")


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


def _extract_immediate_range(inst):
    """Extract immediate value range from encoding field width and field_descriptions."""
    fd = inst.get("field_descriptions", {})
    encodings = inst.get("encodings", [])

    if not encodings:
        return None

    for target in ("DATA", "VECTOR", "ARGUMENT COUNT"):
        result = _find_encoding_field(encodings, target)
        if result is None:
            continue

        field_name, bit_width = result
        desc = _find_field_description(fd, field_name)

        if "sign-extended" in desc.lower() or "sign extended" in desc.lower():
            return {
                "min": -(1 << (bit_width - 1)),
                "max": (1 << (bit_width - 1)) - 1,
                "field": field_name,
                "bits": bit_width,
                "signed": True,
            }

        if "represent" in desc.lower():
            return {
                "min": 1,
                "max": (1 << bit_width),
                "field": field_name,
                "bits": bit_width,
                "zero_means": (1 << bit_width),
            }

        if target == "VECTOR":
            return {
                "min": 0,
                "max": (1 << bit_width) - 1,
                "field": field_name,
                "bits": bit_width,
            }

        if target == "ARGUMENT COUNT":
            # CALLM argument count is 8-bit unsigned in extension word.
            # Parser may extract wrong width due to extension word conflation.
            return {
                "min": 0,
                "max": 255,
                "field": field_name,
                "bits": 8,
            }

        if target == "DATA" and bit_width <= 8:
            range_match = re.search(r"(\d+)\s*-\s*(\d+)", desc)
            if range_match:
                lo, hi = int(range_match.group(1)), int(range_match.group(2))
                if lo == 0 and "represent" in desc.lower():
                    return {
                        "min": 1,
                        "max": hi + 1,
                        "field": field_name,
                        "bits": bit_width,
                        "zero_means": hi + 1,
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

    excluded = []
    if mnemonic == "Bcc":
        excluded = ["t", "f"]

    return {
        "prefix": prefix,
        "field_bits": condition_bits,
        "excluded": excluded,
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
    """Extract MOVEM direction semantics from dr field."""
    if inst["mnemonic"] != "MOVEM":
        return None

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
        range_match = re.search(r"values?\s+(\d+)\s*-\s*(\d+)", cr_desc)
        if range_match:
            return {
                "min": 1, "max": 8,
                "field": "Count/Register", "bits": 3,
                "zero_means": 8,
            }

    has_dr = _find_encoding_field(encodings, "dr") is not None
    if not has_dr:
        return None

    for enc in encodings:
        fields = enc.get("fields", [])
        has_ir = any(f["name"] == "i/r" for f in fields)
        has_count = any(f["name"] == "REGISTER" and f["bit_hi"] == 11
                        and f["bit_lo"] == 9 and f["width"] == 3
                        for f in fields)
        if has_ir and has_count:
            return {
                "min": 1, "max": 8,
                "field": "Count/Register", "bits": 3,
                "zero_means": 8,
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
    """Detect if memory EA form has a fixed size (shift/rotate memory = word only)."""
    encodings = inst.get("encodings", [])
    if len(encodings) < 2:
        return None

    has_dr = _find_encoding_field(encodings, "dr") is not None
    if not has_dr:
        return None

    for enc in encodings:
        fields = enc.get("fields", [])
        has_mode = any(f["name"] == "MODE" for f in fields)
        has_ir = any(f["name"] == "i/r" for f in fields)
        has_dr_field = any(f["name"] == "dr" for f in fields)

        if has_mode and not has_ir and has_dr_field:
            bit7 = next((f for f in fields if f["bit_hi"] == 7 and f["bit_lo"] == 7), None)
            bit6 = next((f for f in fields if f["bit_hi"] == 6 and f["bit_lo"] == 6), None)
            if bit7 and bit6 and bit7["name"] == "1" and bit6["name"] == "1":
                return "w"

    return None


def _extract_bit_op_size_restriction(inst):
    """Detect bit operation size behavior from description."""
    desc = inst.get("description", "")
    mnemonic = inst["mnemonic"]

    if mnemonic not in ("BTST", "BCHG", "BCLR", "BSET"):
        return None

    has_reg_32 = "modulo 32" in desc
    has_mem_byte = "byte operation" in desc.lower() or "modulo 8" in desc

    if has_reg_32 or has_mem_byte:
        return {"dn": "l", "memory": "b"}
    return None


def _derive_processor_min(processors):
    """Derive processor_min from the processors field."""
    if not processors or "M68000 Family" in processors:
        return "68000"
    if re.search(r"\bMC68000\b", processors) or "MC68008" in processors:
        return "68000"
    if "MC68EC000" in processors or "MC68010" in processors:
        return "68010"
    if "MC68020" in processors:
        return "68020"
    if "MC68030" in processors:
        return "68030"
    if "MC68040" in processors:
        return "68040"
    if "MC68881" in processors or "MC68882" in processors:
        return "68020"
    if "68851" in processors:
        return "68020"
    if "CPU32" in processors:
        return "cpu32"
    return "68000"


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


def apply_constraints(kb_data):
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

        if constraints:
            inst["constraints"] = constraints

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
    apply_constraints(kb_data)

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
                json.dump(kb_data, f, indent=2, ensure_ascii=False)
            print(f"\nWrote {len(kb_data)} instructions to {outpath}")
        else:
            print(f"\n(dry run, {len(kb_data)} instructions would be written)")

    if args.output != "summary":
        output_summary(kb_data)


if __name__ == "__main__":
    main()
