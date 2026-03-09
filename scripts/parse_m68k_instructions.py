#!/usr/bin/env python3
"""
Parse M68000 Programmer's Reference Manual PDF to extract structured
instruction data including bit encodings, condition codes, and metadata.

Uses PyMuPDF positioned text extraction (inspired by tinygrad's AMD ISA
generator approach) to correctly parse bit-level encoding tables.

Usage:
    python parse_m68k_instructions.py <pdf_path> [--output json|md|summary]
    python parse_m68k_instructions.py <pdf_path> --dump-page 107
    python parse_m68k_instructions.py <pdf_path> --sections 4,6   # integer + supervisor
"""

import fitz
import re, json, sys, argparse
from dataclasses import dataclass, field, asdict

# Page ranges for each section of the manual
SECTIONS = {
    4: (105, 302),   # Integer Instructions
    6: (455, 540),   # Supervisor (Privileged) Instructions
}

# Common PDF ligatures to normalize
LIGATURES = {"\ufb01": "fi", "\ufb02": "fl", "\ufb00": "ff", "\ufb03": "ffi", "\ufb04": "ffl"}


def normalize_text(text):
    """Replace PDF ligatures with ASCII equivalents."""
    for lig, repl in LIGATURES.items():
        text = text.replace(lig, repl)
    return text


# ═══════════════════════════════════════════════════════════════════════════════
# Positioned text extraction via PyMuPDF
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


# ═══════════════════════════════════════════════════════════════════════════════
# Encoding table extraction
# ═══════════════════════════════════════════════════════════════════════════════

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
        # at the leftmost position, so we only see "5" in texts. Check if we have
        # 0-14 and "5" appears at the leftmost x of the row.
        has_15 = 15 in bit_numbers
        if not has_15 and 5 in bit_numbers and 0 in bit_numbers and len(bit_numbers) >= 14:
            # Check if the leftmost "5" is where bit 15 should be (before bit 14's x)
            row_by_x = sorted(row, key=lambda e: e[0])
            leftmost = row_by_x[0]
            if leftmost[2].strip() == "5" and 14 in bit_numbers:
                bit_numbers.add(15)
                has_15 = True

        if not has_15 or 0 not in bit_numbers or len(bit_numbers) < 14:
            continue

        # === False-positive filter ===
        # Scan backward for the nearest section label above this bit header.
        # Real encodings are preceded by "Instruction Format:" within ~60 y-units.
        # False positives are preceded by "Source:", "Destination:", "Addressing Mode", etc.
        is_real_encoding = False
        for prev_idx in range(idx - 1, max(idx - 8, -1), -1):
            prev_y = sorted_ys[prev_idx]
            if y_key - prev_y > 60:
                break
            prev_texts = " ".join(t for _, _, t, _, _ in rows[prev_y])
            if "Instruction Format" in prev_texts:
                is_real_encoding = True
                break
            # Sub-format labels like "Register Rotate:", "Memory Rotate:", etc.
            if re.search(r"^(Register|Memory)\s+\w+:?$", prev_texts.strip()):
                is_real_encoding = True
                break
            # Stop scanning if we hit something that indicates this is NOT an encoding
            if any(kw in prev_texts for kw in
                   ("Source:", "Destination:", "Resulting", "Concatenated",
                    "Add Adjustment", "Addressing Mode", "Effective Address field")):
                break

        if not is_real_encoding:
            continue

        # Build x -> bit number mapping
        x_to_bit: dict[float, int] = {}
        leftmost_5_x = None  # Track if "15" was split into "1"+"5"
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
            # The leftmost "5" is actually bit 15; there should be another "5" for real bit 5
            min_x = min(x_to_bit.keys())
            if leftmost_5_x == min_x:
                x_to_bit[leftmost_5_x] = 15

        # Collect ALL value rows below the header first, then process.
        # Multi-row encodings have section headers (DESTINATION, SOURCE,
        # EFFECTIVE ADDRESS) on the first row and actual subfields (REGISTER,
        # MODE, SIZE, fixed bits) on subsequent rows. We must collect everything
        # before mapping, so specific fields take priority over broad labels.
        min_col_x = min(x_to_bit.keys()) - 15
        header_y = y_key

        merged_row = []  # (x, x2, text, font, size, y)
        for next_idx in range(idx + 1, min(idx + 6, len(sorted_ys))):
            next_y = sorted_ys[next_idx]
            if next_y - header_y > 45:
                break

            row_items = rows[next_y]
            # Stop if we hit "Instruction Fields:" — that's below the encoding
            row_text = " ".join(t for _, _, t, _, _ in row_items)
            if "Instruction Fields" in row_text:
                break

            enc_items = [(x, x2, t, f, s, next_y) for x, x2, t, f, s in row_items
                        if x >= min_col_x]
            # Filter out long descriptive text (extension word descriptions
            # like "16-BIT DISPLACEMENT IF 8-BIT DISPLACEMENT = $00").
            # Real field labels have at most 4 words.
            enc_items = [e for e in enc_items
                        if e[2] in ("0", "1") or len(e[2].split()) <= 4]
            if enc_items:
                merged_row.extend(enc_items)

        # Sort priority:
        # 1. Fixed bits ("0"/"1") always first
        # 2. Later rows (higher y) first — subfields on rows 2-3 override
        #    section headers (DESTINATION, SOURCE) on row 1
        # 3. Narrower items first (more specific)
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
            # Multi-bit field: use bbox to find spanned columns.
            # Use generous tolerance (1.5 * half_col on both sides) because
            # field labels like "MODE" are centered over 3 columns but their
            # text bbox is narrower than the column span.
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

    # Expand fields to cover adjacent orphan bits. This handles cases where
    # field label text is narrower than the bit columns it spans (e.g.,
    # "8-BIT DISPLACEMENT" text is 86px but covers 8 bit columns spanning 210px).
    # When an orphan is adjacent to two fields, prefer the one with the wider
    # original text bbox (it was meant to span more columns).
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
                    # Prefer the field with the wider original text bbox
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


# ═══════════════════════════════════════════════════════════════════════════════
# Instruction parsing
# ═══════════════════════════════════════════════════════════════════════════════

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


# Section header lines to filter out
_SECTION_HEADERS = {
    "Integer Instructions", "Floating Point Instructions",
    "Supervisor (Privileged) Instructions", "Supervisor Instructions",
    "CPU32 Instructions",
}


def is_instruction_start(rows):
    """Check if these rows represent the start of an instruction entry.

    Handles:
    - Simple mnemonics: ADD, ABCD, NOP
    - Mixed-case: Bcc, DBcc, Scc, TRAPcc
    - Comma-separated: ASL, ASR / DIVS, DIVSL
    - Multi-line: MOVE + "to CCR" / CAS + "CAS2"
    """
    # Build lines from left side only (x < 370) to avoid right-side mnemonic echo
    # Right-side echo minimum x is 394 (ROXL,ROXR); left content max x is 350.
    lines = []
    row_by_line = []  # track which y_key each line comes from
    for y_key in sorted(rows.keys()):
        parts = [text for x, x2, text, font, size in rows[y_key] if x < 370]
        if parts:
            lines.append(" ".join(parts))
            row_by_line.append(y_key)

    # Filter headers/footers
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

    # Match mnemonic patterns:
    # Simple: ADD, ABCD, NOP, MOVE16
    # Mixed-case: Bcc, DBcc, Scc, TRAPcc
    # Comma-separated: ASL, ASR / DIVS, DIVSL
    if not re.match(r"^[A-Za-z][A-Za-z0-9/]{1,10}(?:,\s*[A-Za-z0-9/]+)?$", first):
        return None

    text_block = "\n".join(content[:15])
    if "Operation:" not in text_block:
        return None

    # Build full mnemonic (handle multi-line like "MOVE" + "to CCR")
    mnemonic = first
    title = content[1] if len(content) > 1 else ""

    # Check if second content line is a qualifier (e.g., "to CCR", "from SR", "CAS2", "USP")
    if len(content) > 1:
        second = content[1]
        if re.match(r"^(to |from |USP)", second) or re.match(r"^[A-Z0-9]{2,8}$", second):
            # Check if the actual title is further down (after qualifier + processor line)
            mnemonic = f"{first} {second}"
            title = content[2] if len(content) > 2 else second

    # Extract processor info
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
    # First try to capture syntax from the "Assembler" line (first form often appears there)
    m_asm = re.search(r"Assembler\s+(.+?)(?:\n|$)", text)
    if m_asm:
        asm_line = m_asm.group(1).strip()
        # The Assembler line may have the first syntax form before "Syntax:" appears
        # Skip if it just says "Syntax:" (some pages format as "Assembler Syntax:")
        if not asm_line.startswith("Syntax"):
            syntax.append(asm_line)
    # Then capture remaining syntax lines between Syntax: and Attributes:
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

    # Field descriptions — text already has ligatures normalized
    field_descs = {}
    field_section = re.search(r"Instruction Fields:\s*\n(.+?)(?:\n\s*\n\s*\n|$)", text, re.DOTALL)
    if field_section:
        current_name = None
        current_desc = []
        for line in field_section.group(1).split("\n"):
            line = line.strip()
            # Match "Xxx field—Description" or "Xxx Field—Description"
            fm = re.match(r"^(.+?)\s*[Ff]ield\s*[\u2014\u2013\-]\s*(.+)", line)
            if fm:
                if current_name:
                    field_descs[current_name] = " ".join(current_desc)
                current_name = fm.group(1).strip()
                current_desc = [fm.group(2).strip()]
            elif current_name and line:
                # Continuation lines (indented descriptions)
                if line.startswith("If ") or line.startswith("0 ") or line.startswith("1 "):
                    current_desc.append(line)
        if current_name:
            field_descs[current_name] = " ".join(current_desc)

    return operation, syntax, attributes, description, cc, field_descs


def parse_all_instructions(doc, page_ranges):
    """Parse instructions from given page ranges."""
    # Collect all page data across all ranges
    page_data = []
    for start_page, end_page in page_ranges:
        for pn in range(start_page, end_page + 1):
            page = doc[pn - 1]
            spans = extract_page_spans(page)
            rows = spans_to_rows(spans)
            header = is_instruction_start(rows)
            page_data.append((pn, rows, header))

    # Group pages into instructions
    instructions = []
    current = None  # (header, [(pn, rows)])

    for pn, rows, header in page_data:
        if header:
            if current:
                # Continuation of same instruction?
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

    # Parse each instruction
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
                d.pop("bbox_width", None)  # internal, not for output
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

    # Post-process: fix coprocessor instruction encodings.
    # The PDF has multi-word encoding tables that the parser conflates.
    # All MC68020 coprocessor instructions share word 1 format:
    #   1111 CP_ID(3) TYPE(3) [EA_MODE(3) EA_REG(3) | other]
    _fix_coprocessor_encodings(parsed)

    return parsed


def _f(val, bit):
    """Helper: single fixed bit field."""
    return {"name": val, "bit_hi": bit, "bit_lo": bit, "width": 1}

def _mf(name, hi, lo):
    """Helper: multi-bit named field."""
    return {"name": name, "bit_hi": hi, "bit_lo": lo, "width": hi - lo + 1}

def _fix_coprocessor_encodings(instructions):
    """Replace mis-parsed coprocessor encodings with known correct formats."""
    # Correct word-1 encodings for coprocessor instructions
    COPROC_FIXES = {
        "cpBcc": [
            {"name": "1", "bit_hi": 15, "bit_lo": 15, "width": 1},
            {"name": "1", "bit_hi": 14, "bit_lo": 14, "width": 1},
            {"name": "1", "bit_hi": 13, "bit_lo": 13, "width": 1},
            {"name": "1", "bit_hi": 12, "bit_lo": 12, "width": 1},
            {"name": "COPROCESSOR ID", "bit_hi": 11, "bit_lo": 9, "width": 3},
            {"name": "0", "bit_hi": 8, "bit_lo": 8, "width": 1},
            {"name": "1", "bit_hi": 7, "bit_lo": 7, "width": 1},
            {"name": "SIZE", "bit_hi": 6, "bit_lo": 6, "width": 1},
            {"name": "COPROCESSOR CONDITION", "bit_hi": 5, "bit_lo": 0, "width": 6},
        ],
        "cpDBcc": [
            {"name": "1", "bit_hi": 15, "bit_lo": 15, "width": 1},
            {"name": "1", "bit_hi": 14, "bit_lo": 14, "width": 1},
            {"name": "1", "bit_hi": 13, "bit_lo": 13, "width": 1},
            {"name": "1", "bit_hi": 12, "bit_lo": 12, "width": 1},
            {"name": "COPROCESSOR ID", "bit_hi": 11, "bit_lo": 9, "width": 3},
            {"name": "0", "bit_hi": 8, "bit_lo": 8, "width": 1},
            {"name": "0", "bit_hi": 7, "bit_lo": 7, "width": 1},
            {"name": "1", "bit_hi": 6, "bit_lo": 6, "width": 1},
            {"name": "0", "bit_hi": 5, "bit_lo": 5, "width": 1},
            {"name": "0", "bit_hi": 4, "bit_lo": 4, "width": 1},
            {"name": "1", "bit_hi": 3, "bit_lo": 3, "width": 1},
            {"name": "REGISTER", "bit_hi": 2, "bit_lo": 0, "width": 3},
        ],
        "cpGEN": [
            {"name": "1", "bit_hi": 15, "bit_lo": 15, "width": 1},
            {"name": "1", "bit_hi": 14, "bit_lo": 14, "width": 1},
            {"name": "1", "bit_hi": 13, "bit_lo": 13, "width": 1},
            {"name": "1", "bit_hi": 12, "bit_lo": 12, "width": 1},
            {"name": "COPROCESSOR ID", "bit_hi": 11, "bit_lo": 9, "width": 3},
            {"name": "0", "bit_hi": 8, "bit_lo": 8, "width": 1},
            {"name": "0", "bit_hi": 7, "bit_lo": 7, "width": 1},
            {"name": "0", "bit_hi": 6, "bit_lo": 6, "width": 1},
            {"name": "MODE", "bit_hi": 5, "bit_lo": 3, "width": 3},
            {"name": "REGISTER", "bit_hi": 2, "bit_lo": 0, "width": 3},
        ],
        "cpScc": [
            {"name": "1", "bit_hi": 15, "bit_lo": 15, "width": 1},
            {"name": "1", "bit_hi": 14, "bit_lo": 14, "width": 1},
            {"name": "1", "bit_hi": 13, "bit_lo": 13, "width": 1},
            {"name": "1", "bit_hi": 12, "bit_lo": 12, "width": 1},
            {"name": "COPROCESSOR ID", "bit_hi": 11, "bit_lo": 9, "width": 3},
            {"name": "0", "bit_hi": 8, "bit_lo": 8, "width": 1},
            {"name": "0", "bit_hi": 7, "bit_lo": 7, "width": 1},
            {"name": "1", "bit_hi": 6, "bit_lo": 6, "width": 1},
            {"name": "MODE", "bit_hi": 5, "bit_lo": 3, "width": 3},
            {"name": "REGISTER", "bit_hi": 2, "bit_lo": 0, "width": 3},
        ],
        "cpTRAPcc": [
            {"name": "1", "bit_hi": 15, "bit_lo": 15, "width": 1},
            {"name": "1", "bit_hi": 14, "bit_lo": 14, "width": 1},
            {"name": "1", "bit_hi": 13, "bit_lo": 13, "width": 1},
            {"name": "1", "bit_hi": 12, "bit_lo": 12, "width": 1},
            {"name": "COPROCESSOR ID", "bit_hi": 11, "bit_lo": 9, "width": 3},
            {"name": "0", "bit_hi": 8, "bit_lo": 8, "width": 1},
            {"name": "0", "bit_hi": 7, "bit_lo": 7, "width": 1},
            {"name": "1", "bit_hi": 6, "bit_lo": 6, "width": 1},
            {"name": "1", "bit_hi": 5, "bit_lo": 5, "width": 1},
            {"name": "1", "bit_hi": 4, "bit_lo": 4, "width": 1},
            {"name": "1", "bit_hi": 3, "bit_lo": 3, "width": 1},
            {"name": "OPMODE", "bit_hi": 2, "bit_lo": 0, "width": 3},
        ],
    }

    # Also fix instructions where extension word data leaked into word 1
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

    all_fixes = {**COPROC_FIXES, **OTHER_FIXES}
    for inst in instructions:
        if inst.mnemonic in all_fixes:
            inst.encodings = [{"fields": all_fixes[inst.mnemonic]}]


# ═══════════════════════════════════════════════════════════════════════════════
# Output
# ═══════════════════════════════════════════════════════════════════════════════

def output_summary(instructions):
    has_enc = sum(1 for i in instructions if i.encodings)
    has_cc = sum(1 for i in instructions if any(v != "\u2014" for v in i.condition_codes.values()))
    has_desc = sum(1 for i in instructions if i.description)
    has_fields = sum(1 for i in instructions if i.field_descriptions)
    has_syntax = sum(1 for i in instructions if i.syntax)

    print(f"Parsed {len(instructions)} instructions:\n")
    print(f"  With encoding:    {has_enc}/{len(instructions)}")
    print(f"  With CC:          {has_cc}/{len(instructions)}")
    print(f"  With description: {has_desc}/{len(instructions)}")
    print(f"  With fields:      {has_fields}/{len(instructions)}")
    print(f"  With syntax:      {has_syntax}/{len(instructions)}")
    print()

    for inst in instructions:
        n_enc = len(inst.encodings)
        enc_str = f"{n_enc} enc" if n_enc else "NO ENC"
        if n_enc:
            bits = [sum(f["width"] for f in e["fields"]) for e in inst.encodings]
            enc_str += f" ({','.join(str(b) for b in bits)}b)"
        print(f"  p{inst.page:3d}  {inst.mnemonic:20s}  {inst.title:45s}  [{enc_str:20s}]  {inst.processors}")


def output_json(instructions, outfile):
    data = [asdict(inst) for inst in instructions]
    text = json.dumps(data, indent=2, ensure_ascii=False)
    if outfile:
        with open(outfile, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Wrote {len(data)} instructions to {outfile}")
    else:
        print(text)


def output_markdown(instructions, outfile):
    lines = [f"# M68000 Instruction Set Reference\n",
             f"Extracted from M68000 Programmer's Reference Manual. {len(instructions)} instructions.\n",
             "## Index\n"]
    for inst in instructions:
        anchor = inst.mnemonic.lower().replace(" ", "-").replace(",", "")
        lines.append(f"- [{inst.mnemonic}](#{anchor}) \u2014 {inst.title}")
    lines.append("")

    for inst in instructions:
        lines.append(f"## {inst.mnemonic}")
        lines.append(f"**{inst.title}**\n")
        lines.append(f"- **Processors**: {inst.processors}")
        if inst.operation:
            lines.append(f"- **Operation**: `{inst.operation}`")
        if inst.syntax:
            lines.append(f"- **Syntax**: {', '.join(f'`{s}`' for s in inst.syntax)}")
        if inst.attributes:
            lines.append(f"- **Size**: {inst.attributes}")
        lines.append(f"- **Page**: {inst.page}\n")

        if inst.description:
            lines.append(f"{inst.description}\n")

        cc = inst.condition_codes
        if any(v != "\u2014" for v in cc.values()):
            lines.append("**Condition Codes:**\n")
            lines.append("| X | N | Z | V | C |")
            lines.append("|---|---|---|---|---|")
            lines.append(f"| {cc['X']} | {cc['N']} | {cc['Z']} | {cc['V']} | {cc['C']} |")
            lines.append("")

        if inst.encodings:
            lines.append("**Encoding:**\n")
            for enc in inst.encodings:
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

        if inst.field_descriptions:
            lines.append("**Fields:**\n")
            for fname, fdesc in inst.field_descriptions.items():
                lines.append(f"- **{fname}**: {fdesc}")
            lines.append("")

        lines.append("---\n")

    text = "\n".join(lines)
    if outfile:
        with open(outfile, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Wrote {len(instructions)} instructions to {outfile}")
    else:
        print(text)


# ═══════════════════════════════════════════════════════════════════════════════
# Debug
# ═══════════════════════════════════════════════════════════════════════════════

def dump_page(doc, page_num):
    """Dump positioned text and detected encodings for a page."""
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


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Parse M68K instruction reference from PDF")
    parser.add_argument("pdf", help="Path to M68000 PRM PDF")
    parser.add_argument("--output", choices=["json", "md", "summary"], default="summary")
    parser.add_argument("--outfile", help="Output file path")
    parser.add_argument("--sections", default="4,6",
                        help="Comma-separated section numbers to parse (default: 4,6)")
    parser.add_argument("--dump-page", type=int, help="Debug: dump positioned text for a page")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    doc = fitz.open(args.pdf)

    if args.dump_page:
        dump_page(doc, args.dump_page)
        return

    # Build page ranges from section numbers
    section_nums = [int(s) for s in args.sections.split(",")]
    page_ranges = [SECTIONS[s] for s in section_nums if s in SECTIONS]

    instructions = parse_all_instructions(doc, page_ranges)

    if args.output == "json":
        output_json(instructions, args.outfile)
    elif args.output == "md":
        output_markdown(instructions, args.outfile)
    else:
        output_summary(instructions)


if __name__ == "__main__":
    main()
