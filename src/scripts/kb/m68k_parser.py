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

import argparse
import json
import re
import sys
from collections.abc import Callable
from copy import deepcopy
from dataclasses import asdict, dataclass
from pathlib import Path
from re import Match
from typing import Any, cast

import fitz  # type: ignore[import-untyped]

from src.scripts.kb.paths import M68K_INSTRUCTIONS_JSON

# ═══════════════════════════════════════════════════════════════════════════════
# Shared constants
# ═══════════════════════════════════════════════════════════════════════════════

# Page ranges for each section of the manual
SECTIONS = {
    4: (105, 302),   # Integer Instructions
    6: (455, 540),   # Supervisor (Privileged) Instructions
}

# Common PDF ligatures to normalize
LIGATURES = {"\ufb01": "fi", "\ufb02": "fl", "\ufb00": "ff", "\ufb03": "ffi", "\ufb04": "ffl"}

# Track B parser-assertion: EA mode encoding from PDF p29, Section 2
# "Addressing Mode Categories" Table 2-4 "Effective Address Encoding Summary".
# The (mode, register) → canonical name mapping is asserted because the PDF
# table layout cannot be reliably parsed (multi-row spanning cells with merged
# column headers). The numeric values (mode 0-7, register 0-4) are the M68K
# standard and appear throughout the PDF's instruction encoding tables.
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

# Track B parser-assertion: Processor family hierarchy.
# PDF Section 1.2 lists the M68000 family members. The ordering by capability
# (68000 < 68010 < 68020 < 68030 < 68040 < 68060) is asserted from the PDF's
# section structure and the "MC680x0 only" annotations on instruction pages.
# Aliases: CPU32 maps to 68020 features (PDF p1-1), ColdFire to 68060 subset.
# Emitted to KB _meta.cpu_hierarchy for downstream consumption.
CPU_HIERARCHY = {
    "order": ["68000", "68010", "68020", "68030", "68040", "68060"],
    "aliases": {
        "68020up": "68020",
        "cf":      "68060",
        "cfpu":    "68060",
        "cpu32":   "68020",
    },
}

JsonDict = dict[str, object]
Span = tuple[float, float, float, str, str, float]
RowItem = tuple[float, float, str, str, float]
Rows = dict[int, list[RowItem]]
EncRowItem = tuple[float, float, str, str, float, int]


def _kb_condition_codes() -> list[str]:
    """Ordered architectural condition-code mnemonics."""
    return [CC_TABLE[i] for i in sorted(CC_TABLE.keys())]


# Track C parser-assertion: Condition code test definitions from PDF Table 3-19
# (pp 90-91, "Conditional Tests"). Each condition mnemonic maps to the Boolean
# expression over CCR flags that determines whether the condition is true.
# The PDF gives these as equations like "C̄·Z̄" (meaning NOT C AND NOT Z).
# We encode as {"test": <expression>} using flag names and logical operators.
# The encoding field gives the 4-bit condition code value from the table.
# These are architectural definitions, not per-instruction — they apply
# uniformly to Bcc, DBcc, Scc, and TRAPcc.
CC_TEST_DEFINITIONS = {
    "t":  {"encoding": 0,  "test": "true"},
    "f":  {"encoding": 1,  "test": "false"},
    "hi": {"encoding": 2,  "test": "!C & !Z"},
    "ls": {"encoding": 3,  "test": "C | Z"},
    "cc": {"encoding": 4,  "test": "!C"},
    "cs": {"encoding": 5,  "test": "C"},
    "ne": {"encoding": 6,  "test": "!Z"},
    "eq": {"encoding": 7,  "test": "Z"},
    "vc": {"encoding": 8,  "test": "!V"},
    "vs": {"encoding": 9,  "test": "V"},
    "pl": {"encoding": 10, "test": "!N"},
    "mi": {"encoding": 11, "test": "N"},
    "ge": {"encoding": 12, "test": "(N & V) | (!N & !V)"},
    "lt": {"encoding": 13, "test": "(N & !V) | (!N & V)"},
    "gt": {"encoding": 14, "test": "(N & V & !Z) | (!N & !V & !Z)"},
    "le": {"encoding": 15, "test": "Z | (N & !V) | (!N & V)"},
}


def _exception_vectors() -> list[JsonDict]:
    """Parser-authored exception/autovector metadata from M68K PRM Section 6.

    Primary source:
    - p628: exception processing introduction
    - p629: vector assignment table
    - pp630-639: stack frame details by exception family

    The vector table is modeled here as parser-authored metadata because the
    PDF table layout is not yet parsed structurally. Downstream users consume
    this exactly like parsed KB data.
    """
    citation = "M68K PRM Rev 1, pp628-639 exception processing / vector assignment"

    def entry(vector: int, name: str, kind: str) -> JsonDict:
        return {
            "vector": vector,
            "address": vector * 4,
            "name": name,
            "kind": kind,
            "review_status": "seeded",
            "seed_origin": "primary_doc",
            "citation": citation,
        }

    return [
        entry(0, "Initial SSP", "reset"),
        entry(1, "Initial PC", "reset"),
        entry(2, "Bus Error", "exception"),
        entry(3, "Address Error", "exception"),
        entry(4, "Illegal Instruction", "exception"),
        entry(5, "Division by Zero", "exception"),
        entry(6, "CHK Instruction", "exception"),
        entry(7, "TRAPV Instruction", "exception"),
        entry(8, "Privilege Violation", "exception"),
        entry(9, "Trace", "exception"),
        entry(10, "Line 1010 Emulator", "exception"),
        entry(11, "Line 1111 Emulator", "exception"),
        entry(24, "Spurious Interrupt", "interrupt"),
        entry(25, "Level 1 Interrupt Autovector", "interrupt"),
        entry(26, "Level 2 Interrupt Autovector", "interrupt"),
        entry(27, "Level 3 Interrupt Autovector", "interrupt"),
        entry(28, "Level 4 Interrupt Autovector", "interrupt"),
        entry(29, "Level 5 Interrupt Autovector", "interrupt"),
        entry(30, "Level 6 Interrupt Autovector", "interrupt"),
        entry(31, "Level 7 Interrupt Autovector", "interrupt"),
        entry(32, "TRAP #0 Instruction Vector", "trap"),
        entry(33, "TRAP #1 Instruction Vector", "trap"),
        entry(34, "TRAP #2 Instruction Vector", "trap"),
        entry(35, "TRAP #3 Instruction Vector", "trap"),
        entry(36, "TRAP #4 Instruction Vector", "trap"),
        entry(37, "TRAP #5 Instruction Vector", "trap"),
        entry(38, "TRAP #6 Instruction Vector", "trap"),
        entry(39, "TRAP #7 Instruction Vector", "trap"),
        entry(40, "TRAP #8 Instruction Vector", "trap"),
        entry(41, "TRAP #9 Instruction Vector", "trap"),
        entry(42, "TRAP #10 Instruction Vector", "trap"),
        entry(43, "TRAP #11 Instruction Vector", "trap"),
        entry(44, "TRAP #12 Instruction Vector", "trap"),
        entry(45, "TRAP #13 Instruction Vector", "trap"),
        entry(46, "TRAP #14 Instruction Vector", "trap"),
        entry(47, "TRAP #15 Instruction Vector", "trap"),
    ]


def _exception_stack_frames() -> list[JsonDict]:
    """Parser-authored exception stack-frame format metadata from PRM Appendix B."""
    citation = "M68K PRM Rev 1, pp630-636 Figures B-1 through B-15"

    def field(offset: int, name: str, size_words: int = 1) -> JsonDict:
        return {
            "offset": offset,
            "name": name,
            "size_words": size_words,
        }

    def entry(
        frame_id: str,
        format_code: str | None,
        name: str,
        processors: list[str],
        kind: str,
        fields: list[JsonDict],
    ) -> JsonDict:
        return {
            "frame_id": frame_id,
            "format_code": format_code,
            "name": name,
            "processors": processors,
            "kind": kind,
            "fields": fields,
            "review_status": "seeded",
            "seed_origin": "primary_doc",
            "citation": citation,
        }

    return [
        entry(
            "mc68000_group_1_2",
            None,
            "Group 1 and 2 Exception Stack Frame",
            ["68000"],
            "exception_frame",
            [
                field(0x00, "status_register"),
                field(0x02, "program_counter_high"),
                field(0x04, "program_counter_low"),
            ],
        ),
        entry(
            "mc68000_bus_address_error",
            None,
            "Bus or Address Error Exception Stack Frame",
            ["68000"],
            "exception_frame",
            [
                field(0x00, "special_status_word"),
                field(0x02, "access_address_high"),
                field(0x04, "access_address_low"),
                field(0x06, "instruction_register"),
                field(0x08, "status_register"),
                field(0x0A, "program_counter_high"),
                field(0x0C, "program_counter_low"),
            ],
        ),
        entry(
            "format_0",
            "$0",
            "Four-Word Stack Frame",
            ["68010", "68020", "68030", "68040", "68EC040", "68LC040", "CPU32"],
            "format_frame",
            [
                field(0x00, "status_register"),
                field(0x02, "program_counter", 2),
                field(0x06, "format_and_vector_offset"),
            ],
        ),
        entry(
            "format_1",
            "$1",
            "Throwaway Four-Word Stack Frame",
            ["68010", "68020", "68030", "68040", "68EC040", "68LC040", "CPU32"],
            "format_frame",
            [
                field(0x00, "status_register"),
                field(0x02, "program_counter", 2),
                field(0x06, "format_and_vector_offset"),
            ],
        ),
        entry(
            "format_2",
            "$2",
            "Six-Word Stack Frame",
            ["68010", "68020", "68030", "68040", "68EC040", "68LC040", "CPU32"],
            "format_frame",
            [
                field(0x00, "status_register"),
                field(0x02, "program_counter", 2),
                field(0x06, "format_and_vector_offset"),
                field(0x08, "address", 2),
            ],
        ),
        entry(
            "format_3",
            "$3",
            "Floating-Point Post-Instruction Stack Frame",
            ["68040"],
            "format_frame",
            [
                field(0x00, "status_register"),
                field(0x02, "program_counter", 2),
                field(0x06, "format_and_vector_offset"),
                field(0x08, "effective_address", 2),
            ],
        ),
        entry(
            "format_4",
            "$4",
            "Floating-Point Unimplemented Stack Frame",
            ["68EC040", "68LC040"],
            "format_frame",
            [
                field(0x00, "status_register"),
                field(0x02, "program_counter", 2),
                field(0x06, "format_and_vector_offset"),
                field(0x08, "effective_address", 2),
                field(0x0C, "pc_of_faulted_instruction", 2),
            ],
        ),
        entry(
            "format_7",
            "$7",
            "Access Error Stack Frame",
            ["68040"],
            "format_frame",
            [
                field(0x00, "special_status_word"),
                field(0x02, "wb3_status"),
                field(0x04, "format_and_vector_offset"),
                field(0x06, "effective_address", 2),
                field(0x0A, "wb2_status"),
                field(0x0C, "wb3_address", 2),
                field(0x10, "wb3_data", 2),
                field(0x14, "fault_address", 2),
                field(0x18, "wb1_status"),
                field(0x1A, "wb2_address", 2),
                field(0x1E, "wb2_data", 2),
                field(0x22, "wb1_address", 2),
                field(0x26, "wb1_data_or_push_data_0", 2),
                field(0x2A, "push_data_1", 2),
                field(0x2E, "push_data_2", 2),
                field(0x32, "push_data_3", 2),
                field(0x36, "program_counter", 2),
                field(0x3A, "status_register"),
            ],
        ),
        entry(
            "format_8",
            "$8",
            "Bus and Address Error Stack Frame",
            ["68010"],
            "format_frame",
            [
                field(0x00, "status_register"),
                field(0x02, "format_and_vector_offset"),
                field(0x06, "fault_address", 2),
                field(0x0A, "special_status_word"),
                field(0x0C, "instruction_output_buffer"),
                field(0x0E, "data_input_buffer"),
                field(0x10, "data_output_buffer"),
                field(0x12, "internal_information", 16),
                field(0x32, "program_counter", 2),
            ],
        ),
        entry(
            "format_9",
            "$9",
            "Bus and Coprocessor Mid-Instruction Stack Frame",
            ["68020", "68030"],
            "format_frame",
            [
                field(0x00, "status_register"),
                field(0x02, "format_and_vector_offset"),
                field(0x08, "internal_registers", 4),
                field(0x10, "instruction_address", 2),
                field(0x14, "program_counter", 2),
            ],
        ),
        entry(
            "format_a",
            "$A",
            "Short Bus Cycle Stack Frame",
            ["68020", "68030"],
            "format_frame",
            [
                field(0x00, "status_register"),
                field(0x02, "format_and_vector_offset"),
                field(0x08, "internal_register"),
                field(0x0A, "special_status_register"),
                field(0x0C, "instruction_pipe_stage_c"),
                field(0x0E, "instruction_pipe_stage_b"),
                field(0x10, "data_cycle_fault_address", 2),
                field(0x14, "data_output_buffer", 2),
                field(0x18, "program_counter", 2),
            ],
        ),
        entry(
            "format_b",
            "$B",
            "Long Bus Cycle Stack Frame",
            ["68020", "68030"],
            "format_frame",
            [
                field(0x00, "status_register"),
                field(0x02, "format_and_vector_offset"),
                field(0x08, "internal_register"),
                field(0x0A, "special_status_register"),
                field(0x0C, "instruction_pipe_stage_c"),
                field(0x0E, "instruction_pipe_stage_b"),
                field(0x10, "data_cycle_fault_address", 2),
                field(0x14, "data_output_buffer", 2),
                field(0x18, "stage_b_address", 2),
                field(0x1C, "data_input_buffer", 2),
                field(0x20, "internal_registers", 18),
                field(0x44, "internal_information", 3),
                field(0x4A, "program_counter", 2),
            ],
        ),
        entry(
            "format_c",
            "$C",
            "CPU32 Bus Error Stack Frame",
            ["CPU32"],
            "format_frame",
            [
                field(0x00, "status_register"),
                field(0x02, "format_and_vector_offset"),
                field(0x08, "faulted_address_high"),
                field(0x0A, "faulted_address_low"),
                field(0x0C, "data_buffer_high"),
                field(0x0E, "data_buffer_low"),
                field(0x10, "internal_transfer_count_register"),
                field(0x12, "special_status_word"),
                field(0x14, "return_program_counter_high"),
                field(0x16, "return_program_counter_low"),
                field(0x18, "current_instruction_program_counter_high"),
                field(0x1A, "current_instruction_program_counter_low"),
            ],
        ),
    ]


def _exception_frame_rules() -> list[JsonDict]:
    citation = "M68K PRM Rev 1 Appendix B exception vectors/stack frames; parser-authored mapping"

    def rule(
        vector_start: int,
        vector_end: int,
        processors: list[str],
        frame_ids: list[str],
        selection: str,
    ) -> JsonDict:
        return {
            "vector_start": vector_start,
            "vector_end": vector_end,
            "processors": processors,
            "frame_ids": frame_ids,
            "selection": selection,
            "review_status": "seeded",
            "seed_origin": "primary_doc",
            "citation": citation,
        }

    return [
        rule(2, 3, ["68000"], ["mc68000_bus_address_error"], "always"),
        rule(24, 47, ["68000"], ["mc68000_group_1_2"], "always"),
        rule(4, 11, ["68000"], ["mc68000_group_1_2"], "always"),
        rule(15, 15, ["68000"], ["mc68000_group_1_2"], "always"),
        rule(24, 47, ["68010"], ["format_0"], "always"),
        rule(4, 11, ["68010"], ["format_0"], "always"),
        rule(15, 15, ["68010", "68020", "68030", "68040", "68EC040", "68LC040", "CPU32"], ["format_0"], "always"),
        # Track A parser-assertion: on 68020+ the CHK/TRAPV exception vectors use
        # the six-word format 2 frame, while the other vector-4..11 traps keep
        # format 0. This split is evident from PRM Appendix B frame examples but is
        # not emitted as a machine-readable table in the PDF, so we seed the vector
        # subsets explicitly for downstream generators.
        rule(6, 7, ["68020", "68030", "68040", "68EC040", "68LC040"], ["format_2"], "always"),
        rule(4, 5, ["68020", "68030", "68040", "68EC040", "68LC040", "CPU32"], ["format_0"], "always"),
        rule(8, 11, ["68020", "68030", "68040", "68EC040", "68LC040", "CPU32"], ["format_0"], "always"),
        rule(24, 47, ["68020", "68030", "68040", "68EC040", "68LC040", "CPU32"], ["format_0"], "always"),
        rule(2, 3, ["68010"], ["format_8"], "always"),
        rule(2, 2, ["68020", "68030"], ["format_a", "format_b"], "depends_on_bus_cycle_length"),
        rule(13, 13, ["68020", "68030"], ["format_9"], "always"),
        rule(2, 2, ["68040"], ["format_7"], "always"),
        rule(55, 55, ["68EC040", "68LC040"], ["format_4"], "always"),
        rule(2, 3, ["CPU32"], ["format_c"], "always"),
    ]


def _ea_text_forms() -> list[JsonDict]:
    """Parser-authored operand text forms for Motorola syntax.

    The PDF defines the EA mode names and example syntaxes across Section 2
    (pp29-38), but not as one parseable normalized grammar table. This emits
    the canonical text-form families the assembler frontend should recognize,
    while keeping the actual mode/reg mapping tied back to KB mode names.
    """
    return [
        {"name": "dn", "syntax_family": "reg_direct", "mode_name": "dn", "register_prefix": "d", "value_kind": "none", "cpu_min": "68000"},
        {"name": "an", "syntax_family": "reg_direct", "mode_name": "an", "register_prefix": "a", "value_kind": "none", "cpu_min": "68000"},
        {"name": "imm", "syntax_family": "immediate", "mode_name": "imm", "prefix_token": "#", "value_kind": "numeric", "cpu_min": "68000"},
        {"name": "ind", "syntax_family": "an_indirect", "mode_name": "ind", "base_token": "a", "uses_base_register": True, "prefix_token": "(", "suffix_token": ")", "value_kind": "none", "cpu_min": "68000"},
        {"name": "postinc", "syntax_family": "an_postinc", "mode_name": "postinc", "base_token": "a", "uses_base_register": True, "prefix_token": "(", "suffix_token": ")+", "value_kind": "none", "cpu_min": "68000"},
        {"name": "predec", "syntax_family": "an_predec", "mode_name": "predec", "base_token": "a", "uses_base_register": True, "prefix_token": "-(", "suffix_token": ")", "value_kind": "none", "cpu_min": "68000"},
        {"name": "disp", "syntax_family": "an_disp", "mode_name": "disp", "base_token": "a", "uses_base_register": True, "prefix_token": "", "suffix_token": ")", "value_kind": "numeric", "cpu_min": "68000"},
        {"name": "index", "syntax_family": "an_index", "mode_name": "index", "base_token": "a", "uses_base_register": True, "prefix_token": "", "suffix_token": ")", "value_kind": "numeric", "index_required": True, "cpu_min": "68000"},
        {"name": "pcdisp", "syntax_family": "pc_disp", "mode_name": "pcdisp", "base_token": "pc", "uses_base_register": False, "prefix_token": "", "suffix_token": ")", "allow_label": True, "value_kind": "numeric_or_label", "cpu_min": "68000"},
        {"name": "pcindex", "syntax_family": "pc_index", "mode_name": "pcindex", "base_token": "pc", "uses_base_register": False, "prefix_token": "", "suffix_token": ")", "allow_label": True, "value_kind": "numeric_or_label", "index_required": True, "cpu_min": "68000"},
        {"name": "absw", "syntax_family": "absolute", "mode_name": "absw", "size_suffix": "w", "value_kind": "numeric", "cpu_min": "68000"},
        {"name": "absl", "syntax_family": "absolute", "mode_name": "absl", "size_suffix": "l", "value_kind": "numeric", "cpu_min": "68000"},
    ]


def extract_ea_extension_formats(doc: Any) -> tuple[list[JsonDict], list[JsonDict]]:
    """Extract Brief and Full Extension Word field layouts from PDF page 43.

    Page 43 has three encoding tables:
      [0] Single effective address operation word
      [1] Brief Extension Word (bit 8 = 0)
      [2] Full Extension Word (bit 8 = 1, 020+)

    Returns (brief_fields, full_fields) where each is a list of
    [{name, bit_hi, bit_lo}, ...] including fixed bits (0/1) so
    downstream can derive the brief/full discriminator directly.
    """
    page = doc[42]  # page 43 (0-indexed)
    spans = extract_page_spans(page)
    rows = spans_to_rows(spans)
    encs = find_encoding_tables(rows, summary_mode=True)

    if len(encs) < 3:
        raise RuntimeError(
            f"Expected 3 encoding tables on page 43, found {len(encs)}"
        )

    def _extract_fields(enc_fields: list[BitField]) -> list[JsonDict]:
        return [
            {"name": f.name, "bit_hi": f.bit_hi, "bit_lo": f.bit_lo}
            for f in enc_fields
        ]

    brief_all = _extract_fields(encs[1])
    full_all = _extract_fields(encs[2])

    return brief_all, full_all


def extract_movem_regmask_tables(doc: Any) -> dict[str, list[str]]:
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
        for x, x2, text, _font, _size in header_items:
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
        for x, x2, text, _font, _size in reg_items:
            mid_x = (x + x2) / 2
            # Find closest header x
            closest_x = min(header_xs, key=lambda hx: abs(hx - mid_x))
            bit_pos = x_to_bit[closest_x]
            bit_to_reg[bit_pos] = text.lower()

        # Build list indexed by bit position (0..15)
        tables[labels[idx]] = [bit_to_reg[i] for i in range(16)]

    return tables


def _as_kb_payload(kb_data: list[JsonDict], pmmu_cc: list[str],
                   ea_brief_ext_word: list[JsonDict] | None = None,
                   ea_full_ext_word: list[JsonDict] | None = None,
                   movem_reg_masks: dict[str, list[str]] | None = None,
                   nop_opword: int | None = None,
                   asm_syntax_index: dict[str, str] | None = None,
                   cc_aliases: dict[str, str] | None = None,
                   immediate_routing: dict[str, str] | None = None,
                   condition_families: list[JsonDict] | None = None) -> JsonDict:
    encoding_templates: dict[str, list[JsonDict]] = {}
    field_binding_templates: dict[str, list[JsonDict]] = {}
    form_templates: dict[str, list[JsonDict]] = {}
    instructions_out: list[JsonDict] = []

    encoding_counts: dict[str, int] = {}
    binding_counts: dict[str, int] = {}
    form_counts: dict[str, int] = {}
    for inst in kb_data:
        encodings = inst.get("encodings")
        if isinstance(encodings, list) and encodings:
            key = json.dumps(encodings, sort_keys=True, ensure_ascii=True)
            encoding_counts[key] = encoding_counts.get(key, 0) + 1
        bindings = inst.get("field_bindings")
        if not isinstance(bindings, list) or not bindings:
            pass
        else:
            key = json.dumps(bindings, sort_keys=True, ensure_ascii=True)
            binding_counts[key] = binding_counts.get(key, 0) + 1
        forms = inst.get("forms")
        if isinstance(forms, list) and forms:
            normalized_forms = []
            for form in forms:
                normalized_form = cast(JsonDict, json.loads(json.dumps(form, ensure_ascii=False)))
                normalized_form.pop("syntax", None)
                normalized_forms.append(normalized_form)
            key = json.dumps(normalized_forms, sort_keys=True, ensure_ascii=True)
            form_counts[key] = form_counts.get(key, 0) + 1

    encoding_template_ids: dict[str, str] = {}
    template_ids: dict[str, str] = {}
    form_template_ids: dict[str, str] = {}
    for key, count in sorted(encoding_counts.items()):
        if count < 2:
            continue
        template_id = f"enc_{len(encoding_template_ids):03d}"
        encoding_template_ids[key] = template_id
        encoding_templates[template_id] = cast(list[JsonDict], json.loads(key))
    for key, count in sorted(binding_counts.items()):
        if count < 2:
            continue
        template_id = f"fb_{len(template_ids):03d}"
        template_ids[key] = template_id
        field_binding_templates[template_id] = cast(list[JsonDict], json.loads(key))
    for key, count in sorted(form_counts.items()):
        if count < 2:
            continue
        template_id = f"form_{len(form_template_ids):03d}"
        form_template_ids[key] = template_id
        form_templates[template_id] = cast(list[JsonDict], json.loads(key))

    for inst in kb_data:
        inst_out = cast(JsonDict, json.loads(json.dumps(inst, ensure_ascii=False)))
        encodings = inst_out.get("encodings")
        if isinstance(encodings, list) and encodings:
            key = json.dumps(encodings, sort_keys=True, ensure_ascii=True)
            template_id = encoding_template_ids.get(key)
            if template_id is not None:
                inst_out.pop("encodings", None)
                inst_out["encoding_template"] = template_id
        bindings = inst_out.get("field_bindings")
        if isinstance(bindings, list) and bindings:
            key = json.dumps(bindings, sort_keys=True, ensure_ascii=True)
            template_id = template_ids.get(key)
            if template_id is not None:
                inst_out.pop("field_bindings", None)
                inst_out["field_binding_template"] = template_id
        forms = inst_out.get("forms")
        if isinstance(forms, list) and forms:
            normalized_forms = []
            form_syntaxes: list[str] = []
            for form in forms:
                normalized_form = cast(JsonDict, json.loads(json.dumps(form, ensure_ascii=False)))
                form_syntaxes.append(str(normalized_form.pop("syntax", "")))
                normalized_forms.append(normalized_form)
            key = json.dumps(normalized_forms, sort_keys=True, ensure_ascii=True)
            template_id = form_template_ids.get(key)
            if template_id is not None:
                inst_out.pop("forms", None)
                inst_out["form_template"] = template_id
                inst_out["form_syntaxes"] = form_syntaxes
        instructions_out.append(inst_out)

    # Track B parser-assertion: CCR bit positions within SR from PDF p21,
    # Figure 1-8 "Status Register". The figure shows a 16-bit SR diagram with
    # bit numbers 15..0 and labels: bit 0=C (Carry), 1=V (Overflow), 2=Z (Zero),
    # 3=N (Negative), 4=X (Extend). Bits 5-7 are zero. This layout cannot be
    # reliably parsed from the PDF figure, so it is asserted here.
    ccr_bit_positions = {
        "C": 0, "V": 1, "Z": 2, "N": 3, "X": 4,
    }
    # Track B parser-assertion: Size suffix → byte count from PDF p29, Table 2-3
    # "Operand Data Format Summary". The table shows Byte=8 bits, Word=16 bits,
    # Long=32 bits. Byte counts (8/8=1, 16/8=2, 32/8=4) are arithmetic fact.
    # Cannot be reliably parsed from the PDF table, so asserted here.
    size_byte_count = {"b": 1, "w": 2, "l": 4}
    # Track B parser-assertion: EA mode name → (mode, register) encoding from
    # PDF p29, Table 2-4 "Effective Address Encoding Summary". Reverse of
    # MODE_MAP above. For modes 0-6, register is None (determined by operand).
    # For mode 7, register sub-selects the addressing mode.
    ea_mode_encoding = {v: list(k) for k, v in MODE_MAP.items()}
    # Track B parser-assertion: Valid sizes per EA mode from PDF Section 2
    # (pp 29-38), EA mode descriptions. All EA modes support byte, word, and
    # long EXCEPT address register direct (An, mode=1) which only supports
    # word and long. The PDF states this per-instruction (e.g. ADDA "word or
    # long", MOVEA "word or long") and no instruction's EA table ever shows An
    # with byte size. This is an architectural property of mode 1: the 68000
    # has no byte-width operation on address registers. Cannot be parsed as a
    # single statement from the PDF, so asserted from the universal pattern.
    all_sizes = ["b", "w", "l"]
    ea_mode_sizes = dict.fromkeys(ea_mode_encoding, all_sizes)
    ea_mode_sizes["an"] = ["w", "l"]
    # Track B parser-assertion: Opword size from PDF encoding tables. Every
    # instruction encoding's first word spans bits 15-0 = 16 bits = 2 bytes.
    # This is visible in every instruction's encoding table throughout Section 4
    # (pp 105-302) and Section 6 (pp 455-540). The PC advances by this amount
    # before displacement is applied (PDF p129: "the program counter contains
    # the address of the instruction word...plus two").
    opword_bytes = 2
    # Parser-assertion: Size suffixes from PDF Section 4 instruction encoding
    # tables. Every sized instruction uses .b, .w, .l suffixes. The .s suffix
    # is used for short branch displacements (BRA.S, Bcc.S). These appear
    # throughout Section 4 (pp 105-302) in syntax lines. Cannot be parsed as
    # a single list from any one page.
    size_suffixes = ["b", "w", "l", "s"]
    # Parser-assertion: Default operand size from PDF p29, Section 2.2.
    # "If the size is not specified, the assembler defaults to word." This is
    # stated in the context of MOVE instruction syntax but applies as the
    # standard Motorola assembler convention for all sized instructions.
    default_operand_size = "w"
    # Parser-assertion: Register aliases from PDF p2-2: "The stack pointer
    # is address register 7 (A7). SP is an alternate register name for A7."
    register_aliases = {"sp": "a7"}
    # Parser-assertion: Full extension word BD SIZE field from PDF p2-6,
    # Figure 2-3 "Full Format Extension Word". The BD SIZE field (bits 5-4)
    # encodes: 00=reserved, 01=null displacement, 10=word displacement,
    # 11=long word displacement. This is a 2-bit encoding that cannot be
    # reliably parsed from the PDF figure layout.
    ea_full_ext_bd_size = {"0": "reserved", "1": "null", "2": "word", "3": "long"}

    meta = {
        "condition_codes": _kb_condition_codes(),
        "pmmu_condition_codes": pmmu_cc,
        "cpu_hierarchy": CPU_HIERARCHY,
        "ccr_bit_positions": ccr_bit_positions,
        "size_byte_count": size_byte_count,
        "opword_bytes": opword_bytes,
        "ea_mode_encoding": ea_mode_encoding,
        "ea_mode_sizes": ea_mode_sizes,
        "ea_text_forms": _ea_text_forms(),
        "ea_full_extension_cpu_min": "68020",
        "ea_full_extension_cpu_min_source": "M68K PRM p.2-16 through p.2-18: full extension word memory indirect forms are 68020 and higher only",
        "size_suffixes": size_suffixes,
        "size_suffixes_source": "M68K PRM: .b/.w/.l operand sizes, .s short branch displacement",
        "default_operand_size": default_operand_size,
        "default_operand_size_source": "M68K PRM: word is the default operand size when no suffix is specified",
        "register_aliases": register_aliases,
        "register_aliases_source": "M68K PRM p.2-2: SP is an alternate name for A7",
        "exception_frame_rules": _exception_frame_rules(),
        "exception_stack_frames": _exception_stack_frames(),
        "exception_vectors": _exception_vectors(),
        "ea_full_ext_bd_size": ea_full_ext_bd_size,
        "ea_full_ext_bd_size_source": "M68K PRM: Full Extension Word BD SIZE field",
        "encoding_templates": encoding_templates,
        "field_binding_templates": field_binding_templates,
        "form_templates": form_templates,
        # Track C parser-assertion: Condition code test definitions from PDF
        # pp 90-91, Table 3-19 "Conditional Tests". The table maps each condition
        # mnemonic (T, F, HI, LS, CC, CS, NE, EQ, VC, VS, PL, MI, GE, LT, GT, LE)
        # to its 4-bit encoding and Boolean flag expression. These tests drive
        # Scc, Bcc, and DBcc instructions. The table is a simple enumeration but
        # the Boolean expressions cannot be reliably parsed from the PDF layout,
        # so they are asserted here from the manual's text.
        "cc_test_definitions": CC_TEST_DEFINITIONS,
    }
    if ea_brief_ext_word is not None:
        meta["ea_brief_ext_word"] = ea_brief_ext_word
    if ea_full_ext_word is not None:
        meta["ea_full_ext_word"] = ea_full_ext_word
    if movem_reg_masks is not None:
        meta["movem_reg_masks"] = movem_reg_masks
    if nop_opword is not None:
        meta["nop_opword"] = nop_opword
    if asm_syntax_index is not None:
        meta["asm_syntax_index"] = asm_syntax_index
    if cc_aliases is not None:
        meta["cc_aliases"] = cc_aliases
    if immediate_routing is not None:
        meta["immediate_routing"] = immediate_routing
    if condition_families is not None:
        meta["condition_families"] = condition_families
    return {
        "_meta": meta,
        "instructions": instructions_out,
    }


def extract_pmmu_cc_table(doc: Any, page_ranges: list[tuple[int, int]]) -> list[str]:
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


def _parse_pmmu_cc_table(rows: Rows) -> list[str]:
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


def extract_standard_cc_table(doc: Any) -> dict[int, str]:
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


def normalize_text(text: str) -> str:
    """Replace PDF ligatures with ASCII equivalents."""
    for lig, repl in LIGATURES.items():
        text = text.replace(lig, repl)
    return text


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 1: PDF text extraction and instruction parsing
# ═══════════════════════════════════════════════════════════════════════════════

def extract_page_spans(page: Any) -> list[Span]:
    """Extract (x, y, x2, text, font, size) from a page using PyMuPDF dict mode."""
    spans: list[Span] = []
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


def spans_to_rows(spans: list[Span], y_tolerance: int = 3) -> Rows:
    """Group spans into rows by approximate y-coordinate."""
    rows: Rows = {}
    for x, y, x2, text, font, size in spans:
        y_key = round(y / y_tolerance) * y_tolerance
        rows.setdefault(y_key, []).append((x, x2, text, font, size))
    for y_key in rows:
        rows[y_key].sort(key=lambda e: e[0])
    return rows


def rows_to_plain_text(rows: Rows) -> str:
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


def find_encoding_tables(rows: Rows, summary_mode: bool = False) -> list[list[BitField]]:
    """Find bit encoding tables using positioned text rows.

    Only accepts encoding tables preceded by "Instruction Format:" or a
    sub-format label (e.g. "Register Rotate:"), filtering out false positives
    from addressing mode tables and explanatory diagrams.

    In summary_mode, the "Instruction Format:" filter is bypassed — the summary
    section (Section 8) uses bare instruction names before encoding tables.
    """
    encodings: list[list[BitField]] = []
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
        for x, _x2, t, _, _ in row:
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

        current_cluster: list[EncRowItem] = []
        all_clusters: list[list[EncRowItem]] = []
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


def _map_values_to_bits(x_to_bit: dict[float, int], value_row: list[EncRowItem]) -> list[BitField]:
    """Map value row to bit positions using x-coordinate proximity to header columns."""
    sorted_cols = sorted(x_to_bit.items(), key=lambda e: e[0])
    bit_x = {bit: x for x, bit in sorted_cols}

    col_xs = sorted(bit_x.values())
    if len(col_xs) < 2:
        return []
    avg_spacing = (col_xs[-1] - col_xs[0]) / (len(col_xs) - 1)
    half_col = avg_spacing / 2

    fields: list[BitField] = []
    used_bits: set[int] = set()

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
            tolerance = half_col if text_width < avg_spacing * 0.7 else half_col * 1.5
            matching_bits: list[int] = []
            for bit_num, col_x in bit_x.items():
                if bit_num not in used_bits and vx - tolerance <= col_x <= vx2 + tolerance:
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
    encodings: list[JsonDict]
    field_descriptions: dict[str, str]
    page: int
    pages: list[int]


_SECTION_HEADERS = {
    "Integer Instructions", "Floating Point Instructions",
    "Supervisor (Privileged) Instructions", "Supervisor Instructions",
    "CPU32 Instructions",
}


def is_instruction_start(rows: Rows) -> dict[str, str] | None:
    """Check if these rows represent the start of an instruction entry."""
    lines: list[str] = []
    for y_key in sorted(rows.keys()):
        parts = [text for x, x2, text, font, size in rows[y_key] if x < 370]
        if parts:
            lines.append(" ".join(parts))

    content: list[str] = []
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


def parse_text_sections(text: str) -> tuple[str, list[str], str, str, dict[str, str], dict[str, str]]:
    """Parse operation, syntax, attributes, description, CCs, field descriptions."""
    operation = ""
    m = re.search(r"Operation:\s*(.+?)(?:Assembler|$)", text, re.DOTALL)
    if m:
        operation = m.group(1).strip().split("\n")[0].strip()

    syntax: list[str] = []
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

    field_descs: dict[str, str] = {}
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


def parse_all_instructions(doc: Any, page_ranges: list[tuple[int, int]]) -> list[Instruction]:
    """Parse instructions from given page ranges."""
    page_data: list[tuple[int, Rows, dict[str, str] | None]] = []
    for start_page, end_page in page_ranges:
        for pn in range(start_page, end_page + 1):
            page = doc[pn - 1]
            spans = extract_page_spans(page)
            rows = spans_to_rows(spans)
            header = is_instruction_start(rows)
            page_data.append((pn, rows, header))

    instructions: list[tuple[dict[str, str], list[tuple[int, Rows]]]] = []
    current: tuple[dict[str, str], list[tuple[int, Rows]]] | None = None

    for pn, rows, header in page_data:
        if header:
            if current:
                if header["mnemonic"] == current[0]["mnemonic"]:
                    current[1].append((pn, rows))
                    continue
                instructions.append(current)
            current = (header, [(pn, rows)])
        elif current:
            current[1].append((pn, rows))

    if current:
        instructions.append(current)

    parsed: list[Instruction] = []
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
            encodings=cast(list[JsonDict], enc_data),
            field_descriptions=field_descs,
            page=page_nums[0],
            pages=page_nums,
        ))

    # Deduplicate instructions that appear in multiple PDF sections
    # (e.g. MOVE from SR appears in both Integer Instructions §4 and
    # Supervisor Instructions §6 — same encoding, different privilege context).
    # Keep the first occurrence; merge pages from duplicates.
    seen: dict[str, Instruction] = {}
    deduped: list[Instruction] = []
    for inst in parsed:
        if inst.mnemonic in seen:
            # Merge page numbers from the duplicate
            first = seen[inst.mnemonic]
            first.pages.extend(inst.pages)
        else:
            seen[inst.mnemonic] = inst
            deduped.append(inst)
    parsed = deduped

    _cross_check_with_summary(parsed, doc)
    return parsed


# --- Cross-check detail encodings against Section 8 summary ---

# Page range for Section 8: Instruction Format Summary
SUMMARY_PAGES = (561, 596)


def _encoding_mask_val(enc_fields: list[JsonDict] | list[BitField]) -> tuple[int, int]:
    """Compute (mask, val) from encoding fields — only fixed 0/1 bits contribute."""
    mask = 0
    val = 0
    for f in enc_fields:
        if isinstance(f, dict):
            name = str(f["name"])
            bit_hi = cast(int, f["bit_hi"])
            bit_lo = cast(int, f["bit_lo"])
        else:
            name = f.name
            bit_hi = f.bit_hi
            bit_lo = f.bit_lo
        if name in ("0", "1"):
            for b in range(bit_lo, bit_hi + 1):
                mask |= (1 << b)
                if name == "1":
                    val |= (1 << b)
    return mask, val


def parse_summary_encodings(doc: Any) -> dict[str, list[tuple[int, int, list[BitField]]]]:
    """Parse opword encodings from Section 8 (Instruction Format Summary).

    Returns dict mapping instruction_name -> list of (mask, val, fields).
    Each instruction may have multiple encoding forms in the summary.
    """
    summary: dict[str, list[tuple[int, int, list[BitField]]]] = {}
    start, end = SUMMARY_PAGES

    for pn in range(start, end + 1):
        page = doc[pn - 1]
        spans = extract_page_spans(page)
        rows = spans_to_rows(spans)
        sorted_ys = sorted(rows.keys())

        # Find all bit header positions
        bit_headers: list[tuple[int, int]] = []
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


def _cross_check_with_summary(instructions: list[Instruction], doc: Any) -> None:
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
    all_opwords: dict[str, tuple[int, int]] = {}
    for inst in instructions:
        if inst.encodings:
            m, v = _encoding_mask_val(cast(list[JsonDict], inst.encodings[0]["fields"]))
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
        detail_mask, detail_val = _encoding_mask_val(cast(list[JsonDict], opword["fields"]))

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

def _ea_sort_key(m: str) -> int:
    return EA_ORDER.get(m, 99)


def _parse_3bit(text: str) -> int | None:
    """Parse a 3-digit binary string to int, or return None."""
    text = text.strip()
    if len(text) == 3 and all(c in '01' for c in text):
        return int(text, 2)
    return None


def find_ea_tables_on_page(rows: Rows) -> list[tuple[str, list[str], list[str]]]:
    """Find EA mode tables on a page.

    Returns list of (label, valid_modes, modes_020) tuples.
    """
    tables: list[tuple[str, list[str], list[str]]] = []
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

        valid_modes: set[str] = set()
        modes_020: set[str] = set()

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
                            elif mode_val == 7 and col_idx < len(reg_col_xs):
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


def _merge_ea_tables(tables_by_page: dict[int, list[tuple[str, list[str], list[str]]]],
                     pages: list[int]) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Merge EA tables from all pages of an instruction."""
    all_tables: list[tuple[str, list[str], list[str]]] = []
    for pg in pages:
        if pg in tables_by_page:
            all_tables.extend(tables_by_page[pg])

    if not all_tables:
        return {}, {}

    by_label: dict[str, set[str]] = {}
    by_label_020: dict[str, set[str]] = {}
    for label, modes, modes_020 in all_tables:
        key = label or "ea"
        if key not in by_label:
            by_label[key] = set(modes)
            by_label_020[key] = set(modes_020)
        else:
            by_label[key] |= set(modes)
            by_label_020[key] |= set(modes_020)

    result: dict[str, list[str]] = {}
    result_020: dict[str, list[str]] = {}
    for key, mode_set in by_label.items():
        result[key] = sorted(mode_set, key=_ea_sort_key)
    for key, mode_set in by_label_020.items():
        if mode_set:
            result_020[key] = sorted(mode_set, key=_ea_sort_key)

    return result, result_020


def apply_ea_modes(kb_data: list[JsonDict], doc: Any,
                   page_ranges: list[tuple[int, int]]) -> None:
    """Phase 2: Extract EA tables from PDF and merge into instruction dicts."""
    tables_by_page: dict[int, list[tuple[str, list[str], list[str]]]] = {}
    for start_page, end_page in page_ranges:
        for pn in range(start_page, end_page + 1):
            page = doc[pn - 1]
            spans = extract_page_spans(page)
            rows = spans_to_rows(spans)
            tables = find_ea_tables_on_page(rows)
            if tables:
                tables_by_page[pn] = tables

    for inst in kb_data:
        raw_pages = inst.get("pages", [inst.get("page", 0)])
        pages = [int(pg) for pg in raw_pages] if isinstance(raw_pages, list) else []
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


def apply_ea_direction_split(kb_data: list[JsonDict]) -> None:
    """Post-process: for instructions with movem_direction, split EA modes by direction.

    Uses stashed per-page EA tables from Phase 2 plus direction constraints from Phase 4.
    The PDF lists separate EA tables for each direction (e.g. MOVEM has one table for
    reg-to-mem and another for mem-to-reg on consecutive pages).
    """
    count = 0
    for inst in kb_data:
        constraints = inst.get("constraints", {})
        if not isinstance(constraints, dict):
            continue
        movem_dir = constraints.get("movem_direction")
        raw_tables = inst.pop("_ea_tables_by_page", {})

        if not isinstance(movem_dir, dict) or not isinstance(raw_tables, dict) or not raw_tables:
            continue

        dir_values = movem_dir.get("values", {})
        if not isinstance(dir_values, dict):
            continue
        if len(dir_values) != 2:
            continue

        # Direction order matches page order in the PDF
        dir_labels = [str(v) for v in dir_values.values()]
        typed_raw_tables = raw_tables
        ea_per_dir: dict[str, list[str]] = {}
        dir_idx = 0
        for pg in sorted(typed_raw_tables.keys()):
            page_tables = typed_raw_tables[pg]
            if not isinstance(page_tables, list):
                continue
            for _label, modes, _modes_020 in page_tables:
                if dir_idx < len(dir_labels):
                    ea_per_dir[dir_labels[dir_idx]] = modes
                    dir_idx += 1

        if ea_per_dir:
            inst["ea_modes_by_direction"] = ea_per_dir
            count += 1

    if count:
        print(f"  EA direction splits: {count} instructions")


def apply_parser_asserted_ea_mode_fixes(kb_data: list[JsonDict]) -> None:
    """Apply narrow parser-authored EA legality corrections.

    Track B parser-assertion: CMPI destination EA modes exclude PC-relative
    addressing. The CMPI page text says the immediate value is compared against
    the destination operand and the destination is not changed, but the page's
    EA table layout is close enough to adjacent compare forms that our generic
    table merger currently leaks `pcdisp`/`pcindex` into `dst`. The PRM CMPI
    addressing-mode table on p183 matches the standard immediate-data operation
    destination set and excludes PC-relative modes. We assert that correction
    here so downstream tools and oracle corpora stay spec-aligned.

    Track B parser-assertion: SUBQ address-register direct is legal on 68000.
    PRM p4-173 states "Only word and long operations can be used with address
    registers", which constrains size but does not make An a 68020-only EA.
    Our generic EA-table merge currently leaks `an` into `ea_modes_020.dst`
    for SUBQ, which incorrectly removes valid 68000 forms like `SUBQ.W #1,A0`
    from downstream legality and corpus generation. We assert removal of that
    spurious 020-only tag here; the existing `an_sizes` constraint remains the
    correct legality source for byte exclusion.
    """
    for inst in kb_data:
        mnemonic = str(inst.get("mnemonic"))
        if mnemonic == "CMPI":
            ea_modes = inst.get("ea_modes")
            if not isinstance(ea_modes, dict):
                continue
            dst_modes = ea_modes.get("dst")
            if not isinstance(dst_modes, list):
                continue
            ea_modes["dst"] = [mode for mode in dst_modes if mode not in ("pcdisp", "pcindex")]
            continue
        if mnemonic != "SUBQ":
            continue
        ea_modes_020 = inst.get("ea_modes_020")
        if not isinstance(ea_modes_020, dict):
            continue
        dst_modes_020 = ea_modes_020.get("dst")
        if not isinstance(dst_modes_020, list):
            continue
        filtered = [mode for mode in dst_modes_020 if mode != "an"]
        if filtered:
            ea_modes_020["dst"] = filtered
        else:
            del ea_modes_020["dst"]
            if not ea_modes_020:
                del inst["ea_modes_020"]


PMMU_68030_FC_VARIANTS: tuple[tuple[str, str, int, str], ...] = (
    ("FC", "ctrl_reg", 0, "value"),
    ("Dn", "dn", 1, "reg"),
    ("# <fc>", "imm", 2, "value"),
)


def _pmmu_68030_fc_operand(kind: str) -> JsonDict:
    return {"type": kind}


def _pmmu_68030_fc_form(
    syntax: str,
    fc_kind: str,
    operands: list[JsonDict],
    *,
    processor_set: list[str] | None = None,
    encoding_group_index: int | None = None,
    encoding_group_span: int | None = None,
) -> JsonDict:
    form: JsonDict = {
        "syntax": syntax,
        "operands": [_pmmu_68030_fc_operand(fc_kind), *operands],
    }
    if processor_set is not None:
        form["processor_set"] = processor_set
    if encoding_group_index is not None:
        form["encoding_group_index"] = encoding_group_index
    if encoding_group_span is not None:
        form["encoding_group_span"] = encoding_group_span
    if fc_kind == "ctrl_reg":
        form["control_registers"] = ["sfc", "dfc"]
    return form


def _pmmu_68030_pload_forms() -> list[JsonDict]:
    forms: list[JsonDict] = []
    for mnemonic in ("PLOADR", "PLOADW"):
        for fc_syntax, fc_kind, _, _ in PMMU_68030_FC_VARIANTS:
            forms.append(
                _pmmu_68030_fc_form(
                    f"{mnemonic} {fc_syntax},<ea>",
                    fc_kind,
                    [{"type": "ea"}],
                )
            )
    return forms


def _pmmu_68030_pflush_forms() -> list[JsonDict]:
    forms: list[JsonDict] = [
        {
            "syntax": "PFLUSHA",
            "encoding_group_index": 0,
            "encoding_group_span": 2,
            "processor_set": ["68030"],
            "operands": [],
        }
    ]
    for fc_syntax, fc_kind, _, _ in PMMU_68030_FC_VARIANTS:
        forms.append(
            _pmmu_68030_fc_form(
                f"PFLUSH {fc_syntax},# <mask>",
                fc_kind,
                [{"type": "imm"}],
                processor_set=["68030"],
                encoding_group_index=0,
                encoding_group_span=2,
            )
        )
    for fc_syntax, fc_kind, _, _ in PMMU_68030_FC_VARIANTS:
        forms.append(
            _pmmu_68030_fc_form(
                f"PFLUSH {fc_syntax},# <mask>,<ea>",
                fc_kind,
                [{"type": "imm"}, {"type": "ea"}],
                processor_set=["68030"],
                encoding_group_index=0,
                encoding_group_span=2,
            )
        )
    forms.extend(
        [
            {
                "syntax": "PFLUSHA",
                "encoding_group_index": 1,
                "encoding_group_span": 1,
                "processor_set": ["68040"],
                "operands": [],
            },
            {
                "syntax": "PFLUSH (An)",
                "encoding_group_index": 1,
                "encoding_group_span": 1,
                "processor_set": ["68040"],
                "operands": [{"type": "ind"}],
            },
            {
                "syntax": "PFLUSHA",
                "encoding_group_index": 2,
                "encoding_group_span": 1,
                "processor_set": ["68040"],
                "operands": [],
            },
            {
                "syntax": "PFLUSH (An)",
                "encoding_group_index": 2,
                "encoding_group_span": 1,
                "processor_set": ["68040"],
                "operands": [{"type": "ind"}],
            },
        ]
    )
    return forms


def _pmmu_68030_ptest_forms() -> list[JsonDict]:
    forms: list[JsonDict] = []
    for mnemonic in ("PTESTR", "PTESTW"):
        for fc_syntax, fc_kind, _, _ in PMMU_68030_FC_VARIANTS:
            forms.append(
                _pmmu_68030_fc_form(
                    f"{mnemonic} {fc_syntax},<ea>,# <level>",
                    fc_kind,
                    [{"type": "ea"}, {"type": "imm"}],
                    processor_set=["68030"],
                    encoding_group_index=0,
                    encoding_group_span=2,
                )
            )
    for mnemonic in ("PTESTR", "PTESTW"):
        for fc_syntax, fc_kind, _, _ in PMMU_68030_FC_VARIANTS:
            forms.append(
                _pmmu_68030_fc_form(
                    f"{mnemonic} {fc_syntax},<ea>,# <level>,An",
                    fc_kind,
                    [{"type": "ea"}, {"type": "imm"}, {"type": "an"}],
                    processor_set=["68030"],
                    encoding_group_index=0,
                    encoding_group_span=2,
                )
            )
    forms.extend(
        [
            {
                "syntax": "PTESTR FC,<ea>,# <level>",
                "encoding_group_index": 1,
                "encoding_group_span": 2,
                "processor_set": ["68030"],
                "operands": [{"type": "ctrl_reg"}, {"type": "ea"}, {"type": "imm"}],
            },
            {
                "syntax": "PTESTW FC,<ea>,# <level>",
                "encoding_group_index": 1,
                "encoding_group_span": 2,
                "processor_set": ["68030"],
                "operands": [{"type": "ctrl_reg"}, {"type": "ea"}, {"type": "imm"}],
            },
            {
                "syntax": "PTESTR (An)",
                "encoding_group_index": 2,
                "encoding_group_span": 1,
                "processor_set": ["68040"],
                "operands": [{"type": "ind"}],
            },
            {
                "syntax": "PTESTW (An)",
                "encoding_group_index": 3,
                "encoding_group_span": 1,
                "processor_set": ["68040"],
                "operands": [{"type": "ind"}],
            },
            {
                "syntax": "PTESTR FC,<ea>,# <level>,An",
                "encoding_group_index": 4,
                "encoding_group_span": 2,
                "processor_set": ["68020", "68030"],
                "operands": [{"type": "ctrl_reg"}, {"type": "ea"}, {"type": "imm"}, {"type": "an"}],
            },
            {
                "syntax": "PTESTW FC,<ea>,# <level>,An",
                "encoding_group_index": 4,
                "encoding_group_span": 2,
                "processor_set": ["68020", "68030"],
                "operands": [{"type": "ctrl_reg"}, {"type": "ea"}, {"type": "imm"}, {"type": "an"}],
            },
        ]
    )
    return forms


def _pmmu_68030_pload_field_values() -> list[JsonDict]:
    rw_values: dict[int, int] = {}
    fc_mode_values: dict[int, int] = {}
    for form_index in range(6):
        rw_values[form_index] = 1 if form_index < 3 else 0
        fc_mode_values[form_index] = PMMU_68030_FC_VARIANTS[form_index % 3][2]
    return [
        {"field": "R/ W", "form_field_value": rw_values},
        {"field": "FC-MODE", "occurrence": 0, "form_field_value": fc_mode_values},
    ]


def _pmmu_68030_pload_field_bindings() -> list[JsonDict]:
    bindings: list[JsonDict] = []
    for form_index in range(6):
        _, _, _, fc_value_source = PMMU_68030_FC_VARIANTS[form_index % 3]
        bindings.extend(
            [
                {"form_index": form_index, "field": "MODE", "occurrence": 0, "operand_index": 1, "value_source": "ea_mode"},
                {"form_index": form_index, "field": "REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "ea_reg"},
                {"form_index": form_index, "field": "FC", "occurrence": 0, "operand_index": 0, "value_source": fc_value_source},
            ]
        )
    return bindings


def _pmmu_68030_pflush_field_values() -> list[JsonDict]:
    fc_mode_values = {0: 0}
    for form_index in range(1, 7):
        fc_mode_values[form_index] = PMMU_68030_FC_VARIANTS[(form_index - 1) % 3][2]
    return [
        {"field": "MODE", "occurrence": 0, "form_field_value": {0: 0, 1: 0, 2: 0, 3: 0}},
        {"field": "REGISTER", "occurrence": 0, "form_field_value": {0: 0, 1: 0, 2: 0, 3: 0, 7: 0, 9: 0}},
        {"field": "MODE", "occurrence": 1, "form_field_value": {0: 1, 1: 4, 2: 4, 3: 4, 4: 6, 5: 6, 6: 6}},
        {"field": "MASK", "occurrence": 0, "form_field_value": {0: 0}},
        {"field": "FC-MODE", "occurrence": 0, "form_field_value": fc_mode_values},
        {"field": "FC", "occurrence": 0, "form_field_value": {0: 0}},
        {"field": "OPMODE", "occurrence": 0, "form_field_value": {7: 3, 8: 1, 9: 3, 10: 1}},
    ]


def _pmmu_68030_pflush_field_bindings() -> list[JsonDict]:
    bindings: list[JsonDict] = []
    for form_index in range(1, 4):
        _, _, _, fc_value_source = PMMU_68030_FC_VARIANTS[(form_index - 1) % 3]
        bindings.extend(
            [
                {"form_index": form_index, "field": "MASK", "occurrence": 0, "operand_index": 1, "value_source": "value"},
                {"form_index": form_index, "field": "FC", "occurrence": 0, "operand_index": 0, "value_source": fc_value_source},
            ]
        )
    for form_index in range(4, 7):
        _, _, _, fc_value_source = PMMU_68030_FC_VARIANTS[(form_index - 4) % 3]
        bindings.extend(
            [
                {"form_index": form_index, "field": "MODE", "occurrence": 0, "operand_index": 2, "value_source": "ea_mode"},
                {"form_index": form_index, "field": "REGISTER", "occurrence": 0, "operand_index": 2, "value_source": "ea_reg"},
                {"form_index": form_index, "field": "MASK", "occurrence": 0, "operand_index": 1, "value_source": "value"},
                {"form_index": form_index, "field": "FC", "occurrence": 0, "operand_index": 0, "value_source": fc_value_source},
            ]
        )
    return bindings


def _pmmu_68030_ptest_field_values() -> list[JsonDict]:
    rw_values: dict[int, int] = {}
    a_values: dict[int, int] = {}
    fc_mode_values: dict[int, int] = {}
    register_values: dict[int, int] = {}
    for form_index in range(12):
        is_read = form_index < 3 or 6 <= form_index < 9
        has_an = form_index >= 6
        variant_index = form_index % 3
        rw_values[form_index] = 1 if is_read else 0
        a_values[form_index] = 1 if has_an else 0
        fc_mode_values[form_index] = PMMU_68030_FC_VARIANTS[variant_index][2]
        if not has_an:
            register_values[form_index] = 0
    rw_values.update({12: 1, 13: 0, 14: 1, 15: 0, 16: 1, 17: 0})
    return [
        {"field": "R/ W", "form_field_value": rw_values},
        {"field": "A", "form_field_value": a_values},
        {"field": "REGISTER", "occurrence": 1, "form_field_value": register_values},
        {"field": "FC-MODE", "occurrence": 0, "form_field_value": fc_mode_values},
    ]


def _pmmu_68030_ptest_field_bindings() -> list[JsonDict]:
    bindings: list[JsonDict] = []
    for form_index in range(12):
        has_an = form_index >= 6
        _, _, _, fc_value_source = PMMU_68030_FC_VARIANTS[form_index % 3]
        bindings.extend(
            [
                {"form_index": form_index, "field": "MODE", "occurrence": 0, "operand_index": 1, "value_source": "ea_mode"},
                {"form_index": form_index, "field": "REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "ea_reg"},
                {"form_index": form_index, "field": "FC", "occurrence": 0, "operand_index": 0, "value_source": fc_value_source},
                {"form_index": form_index, "field": "LEVEL", "occurrence": 0, "operand_index": 2, "value_source": "value"},
            ]
        )
        if has_an:
            bindings.append(
                {"form_index": form_index, "field": "REGISTER", "occurrence": 1, "operand_index": 3, "value_source": "reg"}
            )
    bindings.extend(
        [
            {"form_index": 12, "field": "MODE", "occurrence": 0, "operand_index": 1, "value_source": "ea_mode"},
            {"form_index": 12, "field": "REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "ea_reg"},
            {"form_index": 12, "field": "FC", "occurrence": 0, "operand_index": 0, "value_source": "value"},
            {"form_index": 13, "field": "MODE", "occurrence": 0, "operand_index": 1, "value_source": "ea_mode"},
            {"form_index": 13, "field": "REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "ea_reg"},
            {"form_index": 13, "field": "FC", "occurrence": 0, "operand_index": 0, "value_source": "value"},
            {"form_index": 14, "field": "REGISTER", "occurrence": 0, "operand_index": 0, "value_source": "reg"},
            {"form_index": 15, "field": "REGISTER", "occurrence": 0, "operand_index": 0, "value_source": "reg"},
            {"form_index": 16, "field": "MODE", "occurrence": 0, "operand_index": 1, "value_source": "ea_mode"},
            {"form_index": 16, "field": "REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "ea_reg"},
            {"form_index": 16, "field": "FC", "occurrence": 0, "operand_index": 0, "value_source": "value"},
            {"form_index": 16, "field": "LEVEL", "occurrence": 0, "operand_index": 2, "value_source": "value"},
            {"form_index": 16, "field": "A-REGISTER", "occurrence": 0, "operand_index": 3, "value_source": "reg"},
            {"form_index": 17, "field": "MODE", "occurrence": 0, "operand_index": 1, "value_source": "ea_mode"},
            {"form_index": 17, "field": "REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "ea_reg"},
            {"form_index": 17, "field": "FC", "occurrence": 0, "operand_index": 0, "value_source": "value"},
            {"form_index": 17, "field": "LEVEL", "occurrence": 0, "operand_index": 2, "value_source": "value"},
            {"form_index": 17, "field": "A-REGISTER", "occurrence": 0, "operand_index": 3, "value_source": "reg"},
        ]
    )
    return bindings


PARSER_ASSERTED_SYNTAX_FIXES: dict[str, dict[str, object]] = {
    "EXT, EXTB": {
        "syntax": ["EXT.W Dn", "EXT.L Dn", "EXTB.L Dn"],
        "forms": [
            {"syntax": "EXT.W Dn", "operands": [{"type": "dn"}]},
            {"syntax": "EXT.L Dn", "operands": [{"type": "dn"}]},
            {"syntax": "EXTB.L Dn", "operands": [{"type": "dn"}], "processor_020": True},
        ],
    },
    "ABCD": {
        "syntax": ["ABCD Dy,Dx", "ABCD -(Ay),-(Ax)"],
        "forms": [
            {"syntax": "ABCD Dy,Dx", "operands": [{"type": "dn"}, {"type": "dn"}]},
            {"syntax": "ABCD -(Ay),-(Ax)", "operands": [{"type": "predec"}, {"type": "predec"}]},
        ],
    },
    "SBCD": {
        "syntax": ["SBCD Dx,Dy", "SBCD -(Ax),-(Ay)"],
        "forms": [
            {"syntax": "SBCD Dx,Dy", "operands": [{"type": "dn"}, {"type": "dn"}]},
            {"syntax": "SBCD -(Ax),-(Ay)", "operands": [{"type": "predec"}, {"type": "predec"}]},
        ],
    },
    "ADDX": {
        "syntax": ["ADDX Dy,Dx", "ADDX -(Ay),-(Ax)"],
        "forms": [
            {"syntax": "ADDX Dy,Dx", "operands": [{"type": "dn"}, {"type": "dn"}]},
            {"syntax": "ADDX -(Ay),-(Ax)", "operands": [{"type": "predec"}, {"type": "predec"}]},
        ],
    },
    "SUBX": {
        "syntax": ["SUBX Dx,Dy", "SUBX -(Ax),-(Ay)"],
        "forms": [
            {"syntax": "SUBX Dx,Dy", "operands": [{"type": "dn"}, {"type": "dn"}]},
            {"syntax": "SUBX -(Ax),-(Ay)", "operands": [{"type": "predec"}, {"type": "predec"}]},
        ],
    },
    "PACK": {
        "syntax": ["PACK -(Ax),-(Ay),# <adjustment>", "PACK Dx,Dy,# <adjustment>"],
        "forms": [
            {"syntax": "PACK -(Ax),-(Ay),# <adjustment>", "operands": [{"type": "predec"}, {"type": "predec"}, {"type": "imm"}]},
            {"syntax": "PACK Dx,Dy,# <adjustment>", "operands": [{"type": "dn"}, {"type": "dn"}, {"type": "imm"}]},
        ],
    },
    "UNPK": {
        "syntax": ["UNPK -(Ax),-(Ay),# <adjustment>", "UNPK Dx,Dy,# <adjustment>"],
        "forms": [
            {"syntax": "UNPK -(Ax),-(Ay),# <adjustment>", "operands": [{"type": "predec"}, {"type": "predec"}, {"type": "imm"}]},
            {"syntax": "UNPK Dx,Dy,# <adjustment>", "operands": [{"type": "dn"}, {"type": "dn"}, {"type": "imm"}]},
        ],
    },
    "CHK2": {"syntax": ["CHK2 <ea>,Rn"], "forms": [{"syntax": "CHK2 <ea>,Rn", "operands": [{"type": "ea"}, {"type": "rn"}]}]},
    "CMP2": {"syntax": ["CMP2 <ea>,Rn"], "forms": [{"syntax": "CMP2 <ea>,Rn", "operands": [{"type": "ea"}, {"type": "rn"}]}]},
    "CINV": {
        "syntax": ["CINVL <caches>,(An)", "CINVP <caches>,(An)", "CINVA <caches>"],
        "forms": [
            {"syntax": "CINVL <caches>,(An)", "operands": [{"type": "cache_sel"}, {"type": "ind"}]},
            {"syntax": "CINVP <caches>,(An)", "operands": [{"type": "cache_sel"}, {"type": "ind"}]},
            {"syntax": "CINVA <caches>", "operands": [{"type": "cache_sel"}]},
        ],
    },
    "CPUSH": {
        "syntax": ["CPUSHL <caches>,(An)", "CPUSHP <caches>,(An)", "CPUSHA <caches>"],
        "forms": [
            {"syntax": "CPUSHL <caches>,(An)", "operands": [{"type": "cache_sel"}, {"type": "ind"}]},
            {"syntax": "CPUSHP <caches>,(An)", "operands": [{"type": "cache_sel"}, {"type": "ind"}]},
            {"syntax": "CPUSHA <caches>", "operands": [{"type": "cache_sel"}]},
        ],
    },
    "FSAVE": {
        "syntax": ["FSAVE <ea>"],
        "forms": [{"syntax": "FSAVE <ea>", "operands": [{"type": "ea"}]}],
    },
    "FRESTORE": {
        "syntax": ["FRESTORE <ea>"],
        "forms": [{"syntax": "FRESTORE <ea>", "operands": [{"type": "ea"}]}],
    },
    "PFLUSH": {
        "syntax": [
            "PFLUSHA",
            "PFLUSH FC,# <mask>",
            "PFLUSH FC,# <mask>,<ea>",
            "PFLUSHA",
            "PFLUSH (An)",
            "PFLUSHA",
            "PFLUSH (An)",
        ],
        "forms": _pmmu_68030_pflush_forms(),
    },
    "PFLUSH PFLUSHA": {
        "syntax": ["PFLUSHA", "PFLUSH FC,# <mask>", "PFLUSH FC,# <mask>,<ea>"],
        "forms": [
            {"syntax": "PFLUSHA", "processor_set": ["68020", "68030"], "operands": []},
            {
                "syntax": "PFLUSH FC,# <mask>",
                "processor_set": ["68020", "68030"],
                "operands": [{"type": "ctrl_reg"}, {"type": "imm"}],
            },
            {
                "syntax": "PFLUSH FC,# <mask>,<ea>",
                "processor_set": ["68020", "68030"],
                "operands": [{"type": "ctrl_reg"}, {"type": "imm"}, {"type": "ea"}],
            },
        ],
    },
    "PBcc": {
        "syntax": ["PBcc.W <label>", "PBcc.L <label>"],
        "forms": [
            {"syntax": "PBcc.W <label>", "operands": [{"type": "label"}]},
            {"syntax": "PBcc.L <label>", "operands": [{"type": "label"}]},
        ],
    },
    "PDBcc": {
        "syntax": ["PDBcc Dn,<label>"],
        "forms": [{"syntax": "PDBcc Dn,<label>", "operands": [{"type": "dn"}, {"type": "label"}]}],
    },
    "PScc": {
        "syntax": ["PScc <ea>"],
        "forms": [{"syntax": "PScc <ea>", "operands": [{"type": "ea"}]}],
    },
    "PTRAPcc": {
        "syntax": ["PTRAPcc", "PTRAPcc.W # <data>", "PTRAPcc.L # <data>"],
        "forms": [
            {"syntax": "PTRAPcc", "operands": []},
            {"syntax": "PTRAPcc.W # <data>", "operands": [{"type": "imm"}]},
            {"syntax": "PTRAPcc.L # <data>", "operands": [{"type": "imm"}]},
        ],
    },
    "PVALID": {
        "syntax": ["PVALID VAL,<ea>", "PVALID An,<ea>"],
        "forms": [
            {
                "syntax": "PVALID VAL,<ea>",
                "encoding_group_index": 0,
                "encoding_group_span": 2,
                "control_registers": ["val"],
                "operands": [{"type": "ctrl_reg"}, {"type": "ea"}],
            },
            {
                "syntax": "PVALID An,<ea>",
                "encoding_group_index": 1,
                "encoding_group_span": 2,
                "operands": [{"type": "an"}, {"type": "ea"}],
            },
        ],
    },
    "cpBcc": {
        "syntax": ["cpBcc <label>"],
        "forms": [{"syntax": "cpBcc <label>", "operands": [{"type": "label"}]}],
    },
    "cpDBcc": {
        "syntax": ["cpDBcc Dn,<label>"],
        "forms": [{"syntax": "cpDBcc Dn,<label>", "operands": [{"type": "dn"}, {"type": "label"}]}],
    },
    "cpGEN": {
        "syntax": ["cpGEN < parameters as defined by coprocessor >"],
        "forms": [
            {
                "syntax": "cpGEN < parameters as defined by coprocessor >",
                "operands": [{"type": "unknown", "raw": "< parameters as defined by coprocessor >"}],
            }
        ],
    },
    "cpRESTORE": {
        "syntax": ["cpRESTORE <ea>"],
        "forms": [{"syntax": "cpRESTORE <ea>", "operands": [{"type": "ea"}]}],
    },
    "cpSAVE": {
        "syntax": ["cpSAVE <ea>"],
        "forms": [{"syntax": "cpSAVE <ea>", "operands": [{"type": "ea"}]}],
    },
    "cpScc": {
        "syntax": ["cpScc <ea>"],
        "forms": [{"syntax": "cpScc <ea>", "operands": [{"type": "ea"}]}],
    },
    "cpTRAPcc": {
        "syntax": ["cpTRAPcc", "cpTRAPcc.W # <data>", "cpTRAPcc.L # <data>"],
        "forms": [
            {"syntax": "cpTRAPcc", "operands": []},
            {"syntax": "cpTRAPcc.W # <data>", "operands": [{"type": "imm"}]},
            {"syntax": "cpTRAPcc.L # <data>", "operands": [{"type": "imm"}]},
        ],
    },
    "PLOAD": {
        "syntax": ["PLOADR FC,<ea>", "PLOADW FC,<ea>"],
        "forms": _pmmu_68030_pload_forms(),
    },
    "PMOVE": {
        "syntax": [
            "PMOVE <ctrl_reg>,<ea>",
            "PMOVE <ea>,<ctrl_reg>",
            "PMOVE <ctrl_reg>,<ea>",
            "PMOVE <ea>,<ctrl_reg>",
            "PMOVE <ctrl_reg>,<ea>",
            "PMOVE <ea>,<ctrl_reg>",
        ],
        "forms": [
            {
                "syntax": "PMOVE <ctrl_reg>,<ea>",
                "encoding_group_index": 0,
                "encoding_group_span": 2,
                "processor_set": ["68030"],
                "control_registers": ["tc", "srp", "crp"],
                "operands": [{"type": "ctrl_reg"}, {"type": "ea"}],
            },
            {
                "syntax": "PMOVE <ea>,<ctrl_reg>",
                "encoding_group_index": 0,
                "encoding_group_span": 2,
                "processor_set": ["68030"],
                "control_registers": ["tc", "srp", "crp"],
                "operands": [{"type": "ea"}, {"type": "ctrl_reg"}],
            },
            {
                "syntax": "PMOVE <ctrl_reg>,<ea>",
                "encoding_group_index": 1,
                "encoding_group_span": 2,
                "processor_set": ["68030"],
                "control_registers": ["psr"],
                "operands": [{"type": "ctrl_reg"}, {"type": "ea"}],
            },
            {
                "syntax": "PMOVE <ea>,<ctrl_reg>",
                "encoding_group_index": 1,
                "encoding_group_span": 2,
                "processor_set": ["68030"],
                "control_registers": ["psr"],
                "operands": [{"type": "ea"}, {"type": "ctrl_reg"}],
            },
            {
                "syntax": "PMOVE <ctrl_reg>,<ea>",
                "encoding_group_index": 2,
                "encoding_group_span": 2,
                "processor_set": ["68030"],
                "control_registers": ["tt0", "tt1"],
                "operands": [{"type": "ctrl_reg"}, {"type": "ea"}],
            },
            {
                "syntax": "PMOVE <ea>,<ctrl_reg>",
                "encoding_group_index": 2,
                "encoding_group_span": 2,
                "processor_set": ["68030"],
                "control_registers": ["tt0", "tt1"],
                "operands": [{"type": "ea"}, {"type": "ctrl_reg"}],
            },
        ],
    },
    "PTEST": {
        "syntax": [
            "PTESTR FC,<ea>,# <level>",
            "PTESTW FC,<ea>,# <level>",
            "PTESTR FC,<ea>,# <level>,An",
            "PTESTW FC,<ea>,# <level>,An",
            "PTESTR <ea>",
            "PTESTW <ea>",
        ],
        "forms": _pmmu_68030_ptest_forms(),
    },
    "CAS CAS2": {
        "syntax": ["CAS Dc,Du,<ea>", "CAS2 Dc1:Dc2,Du1:Du2,(Rn1):(Rn2)"],
        "forms": [
            {"syntax": "CAS Dc,Du,<ea>", "encoding_group_index": 0, "encoding_group_span": 2, "operands": [{"type": "dn"}, {"type": "dn"}, {"type": "ea"}]},
            {"syntax": "CAS2 Dc1:Dc2,Du1:Du2,(Rn1):(Rn2)", "encoding_group_index": 1, "encoding_group_span": 3, "operands": [{"type": "dn_pair"}, {"type": "dn_pair"}, {"type": "rn_pair"}]},
        ],
    },
    "MOVE16": {
        "syntax": [
            "MOVE16 (Ax)+,(Ay)+",
            "MOVE16 (xxx).L,(An)",
            "MOVE16 (xxx).L,(An)+",
            "MOVE16 (An),(xxx).L",
            "MOVE16 (An)+,(xxx).L",
        ],
        "forms": [
            {"syntax": "MOVE16 (Ax)+,(Ay)+", "encoding_group_index": 0, "encoding_group_span": 2, "operands": [{"type": "postinc"}, {"type": "postinc"}]},
            {"syntax": "MOVE16 (xxx).L,(An)", "encoding_group_index": 1, "encoding_group_span": 3, "operands": [{"type": "absl"}, {"type": "ind"}]},
            {"syntax": "MOVE16 (xxx).L,(An)+", "encoding_group_index": 1, "encoding_group_span": 3, "operands": [{"type": "absl"}, {"type": "postinc"}]},
            {"syntax": "MOVE16 (An),(xxx).L", "encoding_group_index": 1, "encoding_group_span": 3, "operands": [{"type": "ind"}, {"type": "absl"}]},
            {"syntax": "MOVE16 (An)+,(xxx).L", "encoding_group_index": 1, "encoding_group_span": 3, "operands": [{"type": "postinc"}, {"type": "absl"}]},
        ],
    },
    "ASL, ASR": {
        "syntax": ["ASd Dx,Dy", "ASd # <data>,Dy", "ASd <ea>"],
        "forms": [
            {"syntax": "ASd Dx,Dy", "operands": [{"type": "dn"}, {"type": "dn"}], "encoding_group_index": 0},
            {"syntax": "ASd # <data>,Dy", "operands": [{"type": "imm"}, {"type": "dn"}], "encoding_group_index": 0},
            {"syntax": "ASd <ea>", "operands": [{"type": "ea"}], "encoding_group_index": 1},
        ],
    },
    "LSL, LSR": {
        "syntax": ["LSd Dx,Dy", "LSd # <data>,Dy", "LSd <ea>"],
        "forms": [
            {"syntax": "LSd Dx,Dy", "operands": [{"type": "dn"}, {"type": "dn"}], "encoding_group_index": 0},
            {"syntax": "LSd # <data>,Dy", "operands": [{"type": "imm"}, {"type": "dn"}], "encoding_group_index": 0},
            {"syntax": "LSd <ea>", "operands": [{"type": "ea"}], "encoding_group_index": 1},
        ],
    },
    "ROL, ROR": {
        "syntax": ["ROd Dx,Dy", "ROd # <data>,Dy", "ROd <ea>"],
        "forms": [
            {"syntax": "ROd Dx,Dy", "operands": [{"type": "dn"}, {"type": "dn"}], "encoding_group_index": 0},
            {"syntax": "ROd # <data>,Dy", "operands": [{"type": "imm"}, {"type": "dn"}], "encoding_group_index": 0},
            {"syntax": "ROd <ea>", "operands": [{"type": "ea"}], "encoding_group_index": 1},
        ],
    },
    "ROXL, ROXR": {
        "syntax": ["ROXd Dx,Dy", "ROXd # <data>,Dy", "ROXd <ea>"],
        "forms": [
            {"syntax": "ROXd Dx,Dy", "operands": [{"type": "dn"}, {"type": "dn"}], "encoding_group_index": 0},
            {"syntax": "ROXd # <data>,Dy", "operands": [{"type": "imm"}, {"type": "dn"}], "encoding_group_index": 0},
            {"syntax": "ROXd <ea>", "operands": [{"type": "ea"}], "encoding_group_index": 1},
        ],
    },
    "MULS": {
        "syntax": ["MULS.W <ea>,Dn"],
        "forms": [{
            "syntax": "MULS.W <ea>,Dn",
            "operands": [{"type": "ea"}, {"type": "dn"}],
            "encoding_group_index": 0,
            "data_sizes": {"type": "multiply", "src_bits": 16, "dst_bits": 16, "result_bits": 32},
        }],
    },
    "MULU": {
        "syntax": ["MULU.W <ea>,Dn"],
        "forms": [{
            "syntax": "MULU.W <ea>,Dn",
            "operands": [{"type": "ea"}, {"type": "dn"}],
            "encoding_group_index": 0,
            "data_sizes": {"type": "multiply", "src_bits": 16, "dst_bits": 16, "result_bits": 32},
        }],
    },
    "DIVS, DIVSL": {
        "syntax": ["DIVS.W <ea>,Dn"],
        "forms": [{
            "syntax": "DIVS.W <ea>,Dn",
            "operands": [{"type": "ea"}, {"type": "dn"}],
            "encoding_group_index": 0,
            "data_sizes": {"type": "divide", "dividend_bits": 32, "divisor_bits": 16, "quotient_bits": 16},
        }],
        "variants": [{"mnemonic": "DIVS", "processor_020": False}, {"mnemonic": "DIVSL", "processor_020": True}],
    },
    "DIVU, DIVUL": {
        "syntax": ["DIVU.W <ea>,Dn"],
        "forms": [{
            "syntax": "DIVU.W <ea>,Dn",
            "operands": [{"type": "ea"}, {"type": "dn"}],
            "encoding_group_index": 0,
            "data_sizes": {"type": "divide", "dividend_bits": 32, "divisor_bits": 16, "quotient_bits": 16},
        }],
        "variants": [{"mnemonic": "DIVU", "processor_020": False}, {"mnemonic": "DIVUL", "processor_020": True}],
    },
}

PARSER_ASSERTED_FIELD_VALUE_FIXES: dict[str, list[JsonDict]] = {
    "EXT, EXTB": [{"field": "OPMODE", "form_field_value": {0: 2, 1: 3, 2: 7}}],
    "ABCD": [{"field": "R/M", "form_field_value": {0: 0, 1: 1}}],
    "SBCD": [{"field": "R/M", "form_field_value": {0: 0, 1: 1}}],
    "ADDX": [{"field": "R/M", "form_field_value": {0: 0, 1: 1}}],
    "SUBX": [{"field": "R/M", "form_field_value": {0: 0, 1: 1}}],
    "PACK": [{"field": "R/M", "form_field_value": {0: 0, 1: 1}}],
    "UNPK": [{"field": "R/M", "form_field_value": {0: 0, 1: 1}}],
    "MOVES": [{"field": "dr", "form_field_value": {0: 1, 1: 0}}],
    "MOVE16": [{"field": "OPMODE", "form_field_value": {1: 3, 2: 1, 3: 2, 4: 0}}],
    "TRAPcc": [{"field": "OPMODE", "form_field_value": {0: 4, 1: 2, 2: 3}}],
    "CINV": [
        {"field": "SCOPE", "form_field_value": {0: 1, 1: 2, 2: 3}},
        {"field": "REGISTER", "form_field_value": {2: 0}},
    ],
    "CPUSH": [
        {"field": "SCOPE", "form_field_value": {0: 1, 1: 2, 2: 3}},
        {"field": "REGISTER", "form_field_value": {2: 0}},
    ],
    "PFLUSH PFLUSHA": [
        {"field": "MODE", "form_field_value": {0: 1, 1: 4, 2: 7}},
        {"field": "REGISTER", "form_field_value": {0: 0}},
    ],
    "PFLUSH": _pmmu_68030_pflush_field_values(),
    "PLOAD": _pmmu_68030_pload_field_values(),
    "PMOVE": [{"field": "R/ W", "form_field_value": {0: 1, 1: 0, 2: 1, 3: 0, 4: 1, 5: 0}}],
    "FSAVE": [{"field": "ID", "form_field_value": {0: 1}}],
    "FRESTORE": [{"field": "ID", "form_field_value": {0: 1}}],
    "cpTRAPcc": [{"field": "OPMODE", "form_field_value": {0: 4, 1: 2, 2: 3}}],
    "PBcc": [{"field": "SIZE", "form_field_value": {0: 0, 1: 1}}],
    "PTRAPcc": [{"field": "OPMODE", "form_field_value": {0: 4, 1: 2, 2: 3}}],
    "PTEST": _pmmu_68030_ptest_field_values(),
    "ASL, ASR": [{"field": "i/r", "form_field_value": {0: 1, 1: 0}}],
    "LSL, LSR": [{"field": "i/r", "form_field_value": {0: 1, 1: 0}}],
    "ROL, ROR": [{"field": "i/r", "form_field_value": {0: 1, 1: 0}}],
    "ROXL, ROXR": [{"field": "i/r", "form_field_value": {0: 1, 1: 0}}],
}

PARSER_ASSERTED_ENCODING_FIXES: dict[str, list[JsonDict]] = {
    "cpBcc": [
        {
            "fields": [
                {"name": "1", "bit_hi": 15, "bit_lo": 15, "width": 1},
                {"name": "1", "bit_hi": 14, "bit_lo": 14, "width": 1},
                {"name": "1", "bit_hi": 13, "bit_lo": 13, "width": 1},
                {"name": "1", "bit_hi": 12, "bit_lo": 12, "width": 1},
                {"name": "ID", "bit_hi": 11, "bit_lo": 9, "width": 3},
                {"name": "0", "bit_hi": 8, "bit_lo": 8, "width": 1},
                {"name": "1", "bit_hi": 7, "bit_lo": 7, "width": 1},
                {"name": "SIZE", "bit_hi": 6, "bit_lo": 6, "width": 1},
                {"name": "COPROCESSOR CONDITION", "bit_hi": 5, "bit_lo": 0, "width": 6},
            ]
        }
    ],
    "cpDBcc": [
        {
            "fields": [
                {"name": "1", "bit_hi": 15, "bit_lo": 15, "width": 1},
                {"name": "1", "bit_hi": 14, "bit_lo": 14, "width": 1},
                {"name": "1", "bit_hi": 13, "bit_lo": 13, "width": 1},
                {"name": "1", "bit_hi": 12, "bit_lo": 12, "width": 1},
                {"name": "ID", "bit_hi": 11, "bit_lo": 9, "width": 3},
                {"name": "0", "bit_hi": 8, "bit_lo": 8, "width": 1},
                {"name": "0", "bit_hi": 7, "bit_lo": 7, "width": 1},
                {"name": "1", "bit_hi": 6, "bit_lo": 6, "width": 1},
                {"name": "0", "bit_hi": 5, "bit_lo": 5, "width": 1},
                {"name": "0", "bit_hi": 4, "bit_lo": 4, "width": 1},
                {"name": "1", "bit_hi": 3, "bit_lo": 3, "width": 1},
                {"name": "REGISTER", "bit_hi": 2, "bit_lo": 0, "width": 3},
            ]
        },
        {
            "fields": [
                {"name": "0", "bit_hi": 15, "bit_lo": 15, "width": 1},
                {"name": "0", "bit_hi": 14, "bit_lo": 14, "width": 1},
                {"name": "0", "bit_hi": 13, "bit_lo": 13, "width": 1},
                {"name": "0", "bit_hi": 12, "bit_lo": 12, "width": 1},
                {"name": "0", "bit_hi": 11, "bit_lo": 11, "width": 1},
                {"name": "0", "bit_hi": 10, "bit_lo": 10, "width": 1},
                {"name": "0", "bit_hi": 9, "bit_lo": 9, "width": 1},
                {"name": "0", "bit_hi": 8, "bit_lo": 8, "width": 1},
                {"name": "0", "bit_hi": 7, "bit_lo": 7, "width": 1},
                {"name": "0", "bit_hi": 6, "bit_lo": 6, "width": 1},
                {"name": "COPROCESSOR CONDITION", "bit_hi": 5, "bit_lo": 0, "width": 6},
            ]
        },
        {
            "fields": [
                {"name": "16-BIT DISPLACEMENT", "bit_hi": 15, "bit_lo": 0, "width": 16}
            ]
        },
    ],
    "cpTRAPcc": [
        {
            "fields": [
                {"name": "1", "bit_hi": 15, "bit_lo": 15, "width": 1},
                {"name": "1", "bit_hi": 14, "bit_lo": 14, "width": 1},
                {"name": "1", "bit_hi": 13, "bit_lo": 13, "width": 1},
                {"name": "1", "bit_hi": 12, "bit_lo": 12, "width": 1},
                {"name": "ID", "bit_hi": 11, "bit_lo": 9, "width": 3},
                {"name": "0", "bit_hi": 8, "bit_lo": 8, "width": 1},
                {"name": "0", "bit_hi": 7, "bit_lo": 7, "width": 1},
                {"name": "1", "bit_hi": 6, "bit_lo": 6, "width": 1},
                {"name": "1", "bit_hi": 5, "bit_lo": 5, "width": 1},
                {"name": "1", "bit_hi": 4, "bit_lo": 4, "width": 1},
                {"name": "1", "bit_hi": 3, "bit_lo": 3, "width": 1},
                {"name": "OPMODE", "bit_hi": 2, "bit_lo": 0, "width": 3},
            ]
        },
        {
            "fields": [
                {"name": "0", "bit_hi": 15, "bit_lo": 15, "width": 1},
                {"name": "0", "bit_hi": 14, "bit_lo": 14, "width": 1},
                {"name": "0", "bit_hi": 13, "bit_lo": 13, "width": 1},
                {"name": "0", "bit_hi": 12, "bit_lo": 12, "width": 1},
                {"name": "0", "bit_hi": 11, "bit_lo": 11, "width": 1},
                {"name": "0", "bit_hi": 10, "bit_lo": 10, "width": 1},
                {"name": "0", "bit_hi": 9, "bit_lo": 9, "width": 1},
                {"name": "0", "bit_hi": 8, "bit_lo": 8, "width": 1},
                {"name": "0", "bit_hi": 7, "bit_lo": 7, "width": 1},
                {"name": "0", "bit_hi": 6, "bit_lo": 6, "width": 1},
                {"name": "COPROCESSOR CONDITION", "bit_hi": 5, "bit_lo": 0, "width": 6},
            ]
        },
        {
            "fields": [
                {"name": "OPTIONAL WORD", "bit_hi": 15, "bit_lo": 0, "width": 16}
            ]
        },
    ],
    "PTRAPcc": [
        {
            "fields": [
                {"name": "0", "bit_hi": 15, "bit_lo": 15, "width": 1},
                {"name": "0", "bit_hi": 14, "bit_lo": 14, "width": 1},
                {"name": "0", "bit_hi": 13, "bit_lo": 13, "width": 1},
                {"name": "0", "bit_hi": 12, "bit_lo": 12, "width": 1},
                {"name": "0", "bit_hi": 11, "bit_lo": 11, "width": 1},
                {"name": "0", "bit_hi": 10, "bit_lo": 10, "width": 1},
                {"name": "0", "bit_hi": 9, "bit_lo": 9, "width": 1},
                {"name": "0", "bit_hi": 8, "bit_lo": 8, "width": 1},
                {"name": "0", "bit_hi": 7, "bit_lo": 7, "width": 1},
                {"name": "1", "bit_hi": 6, "bit_lo": 6, "width": 1},
                {"name": "1", "bit_hi": 5, "bit_lo": 5, "width": 1},
                {"name": "1", "bit_hi": 4, "bit_lo": 4, "width": 1},
                {"name": "1", "bit_hi": 3, "bit_lo": 3, "width": 1},
                {"name": "OPMODE", "bit_hi": 2, "bit_lo": 0, "width": 3},
            ]
        },
        {
            "fields": [
                {"name": "0", "bit_hi": 15, "bit_lo": 15, "width": 1},
                {"name": "0", "bit_hi": 14, "bit_lo": 14, "width": 1},
                {"name": "0", "bit_hi": 13, "bit_lo": 13, "width": 1},
                {"name": "0", "bit_hi": 12, "bit_lo": 12, "width": 1},
                {"name": "0", "bit_hi": 11, "bit_lo": 11, "width": 1},
                {"name": "0", "bit_hi": 10, "bit_lo": 10, "width": 1},
                {"name": "0", "bit_hi": 9, "bit_lo": 9, "width": 1},
                {"name": "0", "bit_hi": 8, "bit_lo": 8, "width": 1},
                {"name": "0", "bit_hi": 7, "bit_lo": 7, "width": 1},
                {"name": "0", "bit_hi": 6, "bit_lo": 6, "width": 1},
                {"name": "MC68851 CONDITION", "bit_hi": 5, "bit_lo": 0, "width": 6},
            ]
        },
        {
            "fields": [
                {"name": "OPTIONAL WORD", "bit_hi": 15, "bit_lo": 0, "width": 16}
            ]
        },
    ],
    "PVALID": [
        {
            "fields": [
                {"name": "1", "bit_hi": 15, "bit_lo": 15, "width": 1},
                {"name": "1", "bit_hi": 14, "bit_lo": 14, "width": 1},
                {"name": "1", "bit_hi": 13, "bit_lo": 13, "width": 1},
                {"name": "1", "bit_hi": 12, "bit_lo": 12, "width": 1},
                {"name": "0", "bit_hi": 11, "bit_lo": 11, "width": 1},
                {"name": "0", "bit_hi": 10, "bit_lo": 10, "width": 1},
                {"name": "0", "bit_hi": 9, "bit_lo": 9, "width": 1},
                {"name": "0", "bit_hi": 8, "bit_lo": 8, "width": 1},
                {"name": "0", "bit_hi": 7, "bit_lo": 7, "width": 1},
                {"name": "0", "bit_hi": 6, "bit_lo": 6, "width": 1},
                {"name": "MODE", "bit_hi": 5, "bit_lo": 3, "width": 3},
                {"name": "REGISTER", "bit_hi": 2, "bit_lo": 0, "width": 3},
            ]
        },
        {
            "fields": [
                {"name": "0", "bit_hi": 15, "bit_lo": 15, "width": 1},
                {"name": "0", "bit_hi": 14, "bit_lo": 14, "width": 1},
                {"name": "1", "bit_hi": 13, "bit_lo": 13, "width": 1},
                {"name": "0", "bit_hi": 12, "bit_lo": 12, "width": 1},
                {"name": "1", "bit_hi": 11, "bit_lo": 11, "width": 1},
                {"name": "0", "bit_hi": 10, "bit_lo": 10, "width": 1},
                {"name": "0", "bit_hi": 9, "bit_lo": 9, "width": 1},
                {"name": "0", "bit_hi": 8, "bit_lo": 8, "width": 1},
                {"name": "0", "bit_hi": 7, "bit_lo": 7, "width": 1},
                {"name": "0", "bit_hi": 6, "bit_lo": 6, "width": 1},
                {"name": "0", "bit_hi": 5, "bit_lo": 5, "width": 1},
                {"name": "0", "bit_hi": 4, "bit_lo": 4, "width": 1},
                {"name": "0", "bit_hi": 3, "bit_lo": 3, "width": 1},
                {"name": "0", "bit_hi": 2, "bit_lo": 2, "width": 1},
                {"name": "0", "bit_hi": 1, "bit_lo": 1, "width": 1},
                {"name": "0", "bit_hi": 0, "bit_lo": 0, "width": 1},
            ]
        },
        {
            "fields": [
                {"name": "1", "bit_hi": 15, "bit_lo": 15, "width": 1},
                {"name": "1", "bit_hi": 14, "bit_lo": 14, "width": 1},
                {"name": "1", "bit_hi": 13, "bit_lo": 13, "width": 1},
                {"name": "1", "bit_hi": 12, "bit_lo": 12, "width": 1},
                {"name": "0", "bit_hi": 11, "bit_lo": 11, "width": 1},
                {"name": "0", "bit_hi": 10, "bit_lo": 10, "width": 1},
                {"name": "0", "bit_hi": 9, "bit_lo": 9, "width": 1},
                {"name": "0", "bit_hi": 8, "bit_lo": 8, "width": 1},
                {"name": "0", "bit_hi": 7, "bit_lo": 7, "width": 1},
                {"name": "0", "bit_hi": 6, "bit_lo": 6, "width": 1},
                {"name": "MODE", "bit_hi": 5, "bit_lo": 3, "width": 3},
                {"name": "REGISTER", "bit_hi": 2, "bit_lo": 0, "width": 3},
            ]
        },
        {
            "fields": [
                {"name": "0", "bit_hi": 15, "bit_lo": 15, "width": 1},
                {"name": "0", "bit_hi": 14, "bit_lo": 14, "width": 1},
                {"name": "1", "bit_hi": 13, "bit_lo": 13, "width": 1},
                {"name": "0", "bit_hi": 12, "bit_lo": 12, "width": 1},
                {"name": "1", "bit_hi": 11, "bit_lo": 11, "width": 1},
                {"name": "1", "bit_hi": 10, "bit_lo": 10, "width": 1},
                {"name": "0", "bit_hi": 9, "bit_lo": 9, "width": 1},
                {"name": "0", "bit_hi": 8, "bit_lo": 8, "width": 1},
                {"name": "0", "bit_hi": 7, "bit_lo": 7, "width": 1},
                {"name": "0", "bit_hi": 6, "bit_lo": 6, "width": 1},
                {"name": "0", "bit_hi": 5, "bit_lo": 5, "width": 1},
                {"name": "0", "bit_hi": 4, "bit_lo": 4, "width": 1},
                {"name": "0", "bit_hi": 3, "bit_lo": 3, "width": 1},
                {"name": "REGISTER", "bit_hi": 2, "bit_lo": 0, "width": 3},
            ]
        },
    ],
}

PARSER_ASSERTED_RM_FAMILY_BINDINGS: list[JsonDict] = [
    {"form_index": 0, "field": "REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "reg"},
    {"form_index": 0, "field": "REGISTER", "occurrence": 1, "operand_index": 0, "value_source": "reg"},
    {"form_index": 1, "field": "REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "reg"},
    {"form_index": 1, "field": "REGISTER", "occurrence": 1, "operand_index": 0, "value_source": "reg"},
    {"form_index": 0, "field": "DATA", "occurrence": 0, "operand_index": 2, "value_source": "value"},
    {"form_index": 1, "field": "DATA", "occurrence": 0, "operand_index": 2, "value_source": "value"},
]

PARSER_ASSERTED_SHIFT_FAMILY_BINDINGS: list[JsonDict] = [
    {"form_index": 0, "field": "REGISTER", "occurrence": 0, "operand_index": 0, "value_source": "reg"},
    {"form_index": 0, "field": "REGISTER", "occurrence": 1, "operand_index": 1, "value_source": "reg"},
    {"form_index": 1, "field": "REGISTER", "occurrence": 0, "operand_index": 0, "value_source": "value"},
    {"form_index": 1, "field": "REGISTER", "occurrence": 1, "operand_index": 1, "value_source": "reg"},
    {"form_index": 2, "field": "MODE", "occurrence": 0, "operand_index": 0, "value_source": "ea_mode"},
    {"form_index": 2, "field": "REGISTER", "occurrence": 0, "operand_index": 0, "value_source": "ea_reg"},
]

PARSER_ASSERTED_FIELD_BINDING_FIXES: dict[str, list[JsonDict]] = {
    "DBcc": [
        {"form_index": 0, "field": "REGISTER", "occurrence": 0, "operand_index": 0, "value_source": "reg"},
        {"form_index": 0, "field": "16-BIT DISPLACEMENT", "occurrence": 0, "operand_index": 1, "value_source": "value"},
    ],
    "cpBcc": [],
    "cpDBcc": [
        {"form_index": 0, "field": "REGISTER", "occurrence": 0, "operand_index": 0, "value_source": "reg"},
        {"form_index": 0, "field": "16-BIT DISPLACEMENT", "occurrence": 0, "operand_index": 1, "value_source": "value"},
    ],
    "PBcc": [],
    "PDBcc": [
        {"form_index": 0, "field": "COUNT REGISTER", "occurrence": 0, "operand_index": 0, "value_source": "reg"},
        {"form_index": 0, "field": "16-BIT DISPLACEMENT", "occurrence": 0, "operand_index": 1, "value_source": "value"},
    ],
    "ABCD": PARSER_ASSERTED_RM_FAMILY_BINDINGS,
    "SBCD": PARSER_ASSERTED_RM_FAMILY_BINDINGS,
    "ADDX": PARSER_ASSERTED_RM_FAMILY_BINDINGS,
    "SUBX": PARSER_ASSERTED_RM_FAMILY_BINDINGS,
    "PACK": PARSER_ASSERTED_RM_FAMILY_BINDINGS,
    "UNPK": PARSER_ASSERTED_RM_FAMILY_BINDINGS,
    "CMPM": [
        {"form_index": 0, "field": "REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "reg"},
        {"form_index": 0, "field": "REGISTER", "occurrence": 1, "operand_index": 0, "value_source": "reg"},
    ],
    "MOVES": [
        {"form_index": 0, "field": "MODE", "occurrence": 0, "operand_index": 1, "value_source": "ea_mode"},
        {"form_index": 0, "field": "REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "ea_reg"},
        {"form_index": 0, "field": "A/D", "occurrence": 0, "operand_index": 0, "value_source": "reg_kind"},
        {"form_index": 0, "field": "REGISTER", "occurrence": 1, "operand_index": 0, "value_source": "reg"},
        {"form_index": 1, "field": "MODE", "occurrence": 0, "operand_index": 0, "value_source": "ea_mode"},
        {"form_index": 1, "field": "REGISTER", "occurrence": 0, "operand_index": 0, "value_source": "ea_reg"},
        {"form_index": 1, "field": "A/D", "occurrence": 0, "operand_index": 1, "value_source": "reg_kind"},
        {"form_index": 1, "field": "REGISTER", "occurrence": 1, "operand_index": 1, "value_source": "reg"},
    ],
    "CALLM": [
        {"form_index": 0, "field": "MODE", "occurrence": 0, "operand_index": 1, "value_source": "ea_mode"},
        {"form_index": 0, "field": "REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "ea_reg"},
        {"form_index": 0, "field": "ARGUMENT COUNT", "occurrence": 0, "operand_index": 0, "value_source": "value"},
    ],
    "MOVEC": [
        {"form_index": 0, "field": "CONTROL REGISTER", "occurrence": 0, "operand_index": 0, "value_source": "value"},
        {"form_index": 0, "field": "A/D", "occurrence": 0, "operand_index": 1, "value_source": "reg_kind"},
        {"form_index": 0, "field": "REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "reg"},
        {"form_index": 1, "field": "A/D", "occurrence": 0, "operand_index": 0, "value_source": "reg_kind"},
        {"form_index": 1, "field": "REGISTER", "occurrence": 0, "operand_index": 0, "value_source": "reg"},
        {"form_index": 1, "field": "CONTROL REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "value"},
    ],
    "MOVE16": [
        {"form_index": 0, "field": "REGISTER Ax", "occurrence": 0, "operand_index": 0, "value_source": "reg"},
        {"form_index": 0, "field": "REGISTER Ay", "occurrence": 0, "operand_index": 1, "value_source": "reg"},
        {"form_index": 1, "field": "REGISTER Ay", "occurrence": 0, "operand_index": 1, "value_source": "reg"},
        {"form_index": 1, "field": "HIGH-ORDER ADDRESS", "occurrence": 0, "operand_index": 0, "value_source": "value_hi16"},
        {"form_index": 1, "field": "LOW-ORDER ADDRESS", "occurrence": 0, "operand_index": 0, "value_source": "value_lo16"},
        {"form_index": 2, "field": "REGISTER Ay", "occurrence": 0, "operand_index": 1, "value_source": "reg"},
        {"form_index": 2, "field": "HIGH-ORDER ADDRESS", "occurrence": 0, "operand_index": 0, "value_source": "value_hi16"},
        {"form_index": 2, "field": "LOW-ORDER ADDRESS", "occurrence": 0, "operand_index": 0, "value_source": "value_lo16"},
        {"form_index": 3, "field": "REGISTER Ay", "occurrence": 0, "operand_index": 0, "value_source": "reg"},
        {"form_index": 3, "field": "HIGH-ORDER ADDRESS", "occurrence": 0, "operand_index": 1, "value_source": "value_hi16"},
        {"form_index": 3, "field": "LOW-ORDER ADDRESS", "occurrence": 0, "operand_index": 1, "value_source": "value_lo16"},
        {"form_index": 4, "field": "REGISTER Ay", "occurrence": 0, "operand_index": 0, "value_source": "reg"},
        {"form_index": 4, "field": "HIGH-ORDER ADDRESS", "occurrence": 0, "operand_index": 1, "value_source": "value_hi16"},
        {"form_index": 4, "field": "LOW-ORDER ADDRESS", "occurrence": 0, "operand_index": 1, "value_source": "value_lo16"},
    ],
    "PFLUSH PFLUSHA": [
        {"form_index": 1, "field": "FC", "occurrence": 0, "operand_index": 0, "value_source": "value"},
        {"form_index": 1, "field": "MASK", "occurrence": 0, "operand_index": 1, "value_source": "value"},
        {"form_index": 2, "field": "MODE", "occurrence": 0, "operand_index": 2, "value_source": "ea_mode"},
        {"form_index": 2, "field": "REGISTER", "occurrence": 0, "operand_index": 2, "value_source": "ea_reg"},
        {"form_index": 2, "field": "FC", "occurrence": 0, "operand_index": 0, "value_source": "value"},
        {"form_index": 2, "field": "MASK", "occurrence": 0, "operand_index": 1, "value_source": "value"},
    ],
    "PFLUSH": _pmmu_68030_pflush_field_bindings(),
    "cpScc": [
        {"form_index": 0, "field": "MODE", "occurrence": 0, "operand_index": 0, "value_source": "ea_mode"},
        {"form_index": 0, "field": "REGISTER", "occurrence": 0, "operand_index": 0, "value_source": "ea_reg"},
    ],
    "cpTRAPcc": [
        {"form_index": 1, "field": "DATA", "occurrence": 0, "operand_index": 0, "value_source": "value"},
        {"form_index": 2, "field": "DATA", "occurrence": 0, "operand_index": 0, "value_source": "value"},
    ],
    "PScc": [
        {"form_index": 0, "field": "MODE", "occurrence": 0, "operand_index": 0, "value_source": "ea_mode"},
        {"form_index": 0, "field": "REGISTER", "occurrence": 0, "operand_index": 0, "value_source": "ea_reg"},
    ],
    "PTRAPcc": [
        {"form_index": 1, "field": "DATA", "occurrence": 0, "operand_index": 0, "value_source": "value"},
        {"form_index": 2, "field": "DATA", "occurrence": 0, "operand_index": 0, "value_source": "value"},
    ],
    "PVALID": [
        {"form_index": 0, "field": "MODE", "occurrence": 0, "operand_index": 1, "value_source": "ea_mode"},
        {"form_index": 0, "field": "REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "ea_reg"},
        {"form_index": 0, "field": "REGISTER", "occurrence": 1, "operand_index": 0, "value_source": "value"},
        {"form_index": 1, "field": "MODE", "occurrence": 0, "operand_index": 1, "value_source": "ea_mode"},
        {"form_index": 1, "field": "REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "ea_reg"},
        {"form_index": 1, "field": "REGISTER", "occurrence": 1, "operand_index": 0, "value_source": "reg"},
    ],
    "PLOAD": _pmmu_68030_pload_field_bindings(),
    "PMOVE": [
        {"form_index": 0, "field": "P-REGISTER", "occurrence": 0, "operand_index": 0, "value_source": "value"},
        {"form_index": 0, "field": "MODE", "occurrence": 0, "operand_index": 1, "value_source": "ea_mode"},
        {"form_index": 0, "field": "REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "ea_reg"},
        {"form_index": 1, "field": "MODE", "occurrence": 0, "operand_index": 0, "value_source": "ea_mode"},
        {"form_index": 1, "field": "REGISTER", "occurrence": 0, "operand_index": 0, "value_source": "ea_reg"},
        {"form_index": 1, "field": "P-REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "value"},
        {"form_index": 2, "field": "MODE", "occurrence": 0, "operand_index": 1, "value_source": "ea_mode"},
        {"form_index": 2, "field": "REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "ea_reg"},
        {"form_index": 3, "field": "MODE", "occurrence": 0, "operand_index": 0, "value_source": "ea_mode"},
        {"form_index": 3, "field": "REGISTER", "occurrence": 0, "operand_index": 0, "value_source": "ea_reg"},
        {"form_index": 4, "field": "P-REGISTER", "occurrence": 0, "operand_index": 0, "value_source": "value"},
        {"form_index": 4, "field": "MODE", "occurrence": 0, "operand_index": 1, "value_source": "ea_mode"},
        {"form_index": 4, "field": "REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "ea_reg"},
        {"form_index": 5, "field": "MODE", "occurrence": 0, "operand_index": 0, "value_source": "ea_mode"},
        {"form_index": 5, "field": "REGISTER", "occurrence": 0, "operand_index": 0, "value_source": "ea_reg"},
        {"form_index": 5, "field": "P-REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "value"},
    ],
    "PTEST": _pmmu_68030_ptest_field_bindings(),
    "CAS CAS2": [
        {"form_index": 0, "field": "MODE", "occurrence": 0, "operand_index": 2, "value_source": "ea_mode"},
        {"form_index": 0, "field": "REGISTER", "occurrence": 0, "operand_index": 2, "value_source": "ea_reg"},
        {"form_index": 0, "field": "Dc", "occurrence": 0, "operand_index": 0, "value_source": "reg"},
        {"form_index": 0, "field": "Du", "occurrence": 0, "operand_index": 1, "value_source": "reg"},
        {"form_index": 1, "field": "Dc1", "occurrence": 0, "operand_index": 0, "value_source": "reg_first"},
        {"form_index": 1, "field": "Dc2", "occurrence": 0, "operand_index": 0, "value_source": "reg_second"},
        {"form_index": 1, "field": "Du1", "occurrence": 0, "operand_index": 1, "value_source": "reg_first"},
        {"form_index": 1, "field": "Du2", "occurrence": 0, "operand_index": 1, "value_source": "reg_second"},
        {"form_index": 1, "field": "D/A1", "occurrence": 0, "operand_index": 2, "value_source": "reg_kind_first"},
        {"form_index": 1, "field": "Rn1", "occurrence": 0, "operand_index": 2, "value_source": "reg_first"},
        {"form_index": 1, "field": "D/A2", "occurrence": 0, "operand_index": 2, "value_source": "reg_kind_second"},
        {"form_index": 1, "field": "Rn2", "occurrence": 0, "operand_index": 2, "value_source": "reg_second"},
    ],
    "RTD": [
        {"form_index": 0, "field": "16-BIT DISPLACEMENT", "occurrence": 0, "operand_index": 0, "value_source": "value"},
    ],
    "CHK2": [
        {"form_index": 0, "field": "MODE", "occurrence": 0, "operand_index": 0, "value_source": "ea_mode"},
        {"form_index": 0, "field": "REGISTER", "occurrence": 0, "operand_index": 0, "value_source": "ea_reg"},
        {"form_index": 0, "field": "D/A", "occurrence": 0, "operand_index": 1, "value_source": "reg_kind"},
        {"form_index": 0, "field": "REGISTER", "occurrence": 1, "operand_index": 1, "value_source": "reg"},
    ],
    "CMP2": [
        {"form_index": 0, "field": "MODE", "occurrence": 0, "operand_index": 0, "value_source": "ea_mode"},
        {"form_index": 0, "field": "REGISTER", "occurrence": 0, "operand_index": 0, "value_source": "ea_reg"},
        {"form_index": 0, "field": "D/A", "occurrence": 0, "operand_index": 1, "value_source": "reg_kind"},
        {"form_index": 0, "field": "REGISTER", "occurrence": 1, "operand_index": 1, "value_source": "reg"},
    ],
    "CINV": [
        {"form_index": 0, "field": "CACHE", "occurrence": 0, "operand_index": 0, "value_source": "value"},
        {"form_index": 0, "field": "REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "ea_reg"},
        {"form_index": 1, "field": "CACHE", "occurrence": 0, "operand_index": 0, "value_source": "value"},
        {"form_index": 1, "field": "REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "ea_reg"},
        {"form_index": 2, "field": "CACHE", "occurrence": 0, "operand_index": 0, "value_source": "value"},
    ],
    "CPUSH": [
        {"form_index": 0, "field": "CACHE", "occurrence": 0, "operand_index": 0, "value_source": "value"},
        {"form_index": 0, "field": "REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "ea_reg"},
        {"form_index": 1, "field": "CACHE", "occurrence": 0, "operand_index": 0, "value_source": "value"},
        {"form_index": 1, "field": "REGISTER", "occurrence": 0, "operand_index": 1, "value_source": "ea_reg"},
        {"form_index": 2, "field": "CACHE", "occurrence": 0, "operand_index": 0, "value_source": "value"},
    ],
    "ASL, ASR": PARSER_ASSERTED_SHIFT_FAMILY_BINDINGS,
    "LSL, LSR": PARSER_ASSERTED_SHIFT_FAMILY_BINDINGS,
    "ROL, ROR": PARSER_ASSERTED_SHIFT_FAMILY_BINDINGS,
    "ROXL, ROXR": PARSER_ASSERTED_SHIFT_FAMILY_BINDINGS,
}

def apply_parser_asserted_syntax_fixes(kb_data: list[JsonDict]) -> None:
    """Apply narrow parser-authored syntax corrections.

    Track B parser-assertion: EXT/EXTB syntax on PRM p210 is being extracted with
    descriptive prose fused into the operand token (for example
    ``EXT.W Dnextend byte to word``). The page's real syntax lines are the
    standard Motorola assembler forms:
      EXT.W Dn
      EXT.L Dn
      EXTB.L Dn   (68020+ only)
    The PDF text extraction loses the line/column boundary between the operand
    and the following explanation, so this cannot be recovered by the generic
    syntax parser alone. We assert the exact syntax forms here from the PRM page
    so downstream tools consume clean assembler syntax from the KB.

    Track B parser-assertion: ABCD/SBCD/ADDX/SUBX/PACK/UNPK/CHK2/CMP2 on PRM pp106/274/117/287/260/299/175/186 use the printed
    predecrement notation ``–(Ay), –(Ax)`` / ``–(Ax), –(Ay)`` with an en dash
    that the PDF extractor preserves inconsistently, and the current generic
    syntax parser fails to turn those lines into structured forms. The real
    Motorola assembler syntax is:
      ABCD Dy,Dx
      ABCD -(Ay),-(Ax)
      SBCD Dx,Dy
      SBCD -(Ax),-(Ay)
      ADDX Dy,Dx
      ADDX -(Ay),-(Ax)
      SUBX Dx,Dy
      SUBX -(Ax),-(Ay)
      PACK -(Ax),-(Ay),# <adjustment>
      PACK Dx,Dy,# <adjustment>
      UNPK -(Ax),-(Ay),# <adjustment>
      UNPK Dx,Dy,# <adjustment>
      CHK2 <ea>,Rn
      CMP2 <ea>,Rn
    We assert those exact forms here from the instruction pages so downstream
    tools consume clean source/destination forms from the KB.

    Track B parser-assertion: CAS/CAS2 on PRM pp168-170 are combined on one
    page, and the extracted syntax retains spacing noise plus a dangling `*`
    bullet. We assert clean assembler-facing forms here and preserve their
    encoding-group mapping:
      CAS Dc,Du,<ea>
      CAS2 Dc1:Dc2,Du1:Du2,(Rn1):(Rn2)

    Track B parser-assertion: cpGEN on PRM p190 is explicitly a generic
    coprocessor escape with "parameters as defined by coprocessor". The page
    defines the opword shape but not a Motorola-level operand structure for the
    trailing coprocessor-specific parameter block. We assert that syntax stays
    opaque here so downstream tools do not invent structure the PDF does not.

    Track B parser-assertion: PVALID on PRM pp534-536 is printed with two
    explicit forms, `PVALID VAL,<ea>` and `PVALID An,<ea>`, but the extraction
    still carries spacing noise around the operands. We assert the clean
    assembler-facing forms here while preserving the PDF's distinction between
    the fixed `VAL` source and the address-register source. The fixed `VAL`
    source is modeled as a constrained control-register operand so downstream
    generators can keep it on the same structured path as other register-like
    PMMU operands.
    """
    for inst in kb_data:
        if str(inst.get("mnemonic")) == "PMOVE":
            pages = inst.get("pages")
            if isinstance(pages, list):
                kept_pages = [int(page) for page in pages if int(page) <= 504]
                if kept_pages:
                    inst["pages"] = kept_pages
                    inst["page"] = kept_pages[0]
            encodings = inst.get("encodings")
            if isinstance(encodings, list) and len(encodings) > 6:
                inst["encodings"] = encodings[:6]
        fix = PARSER_ASSERTED_SYNTAX_FIXES.get(str(inst.get("mnemonic")))
        if fix is None:
            continue
        inst["syntax"] = deepcopy(cast(list[str], fix["syntax"]))
        inst["forms"] = deepcopy(cast(list[JsonDict], fix["forms"]))


def apply_parser_asserted_field_value_fixes(kb_data: list[JsonDict]) -> None:
    """Apply narrow parser-authored per-form field values.

    Track B parser-assertion: EXT/EXTB on PRM p210 uses the OPMODE field to
    distinguish the three syntax forms:
      EXT.W Dn  -> OPMODE=010
      EXT.L Dn  -> OPMODE=011
      EXTB.L Dn -> OPMODE=111
    The generic opmode-table extractor records these rows, but downstream code
    also needs the form-specific constant field values in machine-readable form.
    We assert them here from the PDF table so generated tools can consume them
    without mnemonic-specific hardcoding.

    Track B parser-assertion: ABCD/SBCD/ADDX/SUBX/PACK/UNPK on PRM pp106/274/117/287/260/299 use the single-bit
    ``R/M`` field to distinguish register-direct and address-predecrement
    source/destination forms:
      0 -> Dn,Dn form
      1 -> -(An),-(An) form
    The PDF syntax makes this distinction obvious, but the current generic
    extraction does not derive per-form constant field values for ``R/M``.
    We assert those exact per-form constants here from the encoding diagram.

    Track B parser-assertion: MOVES on PRM p478 uses the extension-word ``dr``
    bit to distinguish the two syntax forms:
      MOVES Rn,<ea>  -> dr=1
      MOVES <ea>,Rn  -> dr=0
    The PDF extension-word diagram makes this explicit, but the current generic
    extraction does not derive per-form constant field values for that bit.

    Track B parser-assertion: TRAPcc on PRM p293 uses OPMODE to distinguish
    the three syntax forms:
      TRAPcc           -> OPMODE=100
      TRAPcc.W #<data> -> OPMODE=010
      TRAPcc.L #<data> -> OPMODE=011
    The opmode table on the page gives these rows directly, but downstream code
    needs the per-form constant field values in machine-readable form.

    Track B parser-assertion: FRESTORE on PRM p467 and FSAVE on PRM p470 show
    the coprocessor instruction format with explicit `ID` bits:
      FRESTORE -> `COPROCESSOR ID 1 0 1 EFFECTIVE ADDRESS`
      FSAVE    -> `COPROCESSOR ID 1 0 0 EFFECTIVE ADDRESS`
    The extracted templates preserve `ID` as a variable field, but for the
    documented MC68040 forms that field is fixed to `001`. We assert that
    constant per form here so generated tools emit the PDF encoding rather than
    relying on downstream oracle-only correction.

    Track B parser-assertion: PBcc on PRM p482 and PTRAPcc on PRM p532 retain
    fused size/opmode syntax in the raw extraction. The pages document explicit
    per-form selectors:
      PBcc.W / PBcc.L
      PTRAPcc / PTRAPcc.W / PTRAPcc.L
    We assert those selector values here so the KB exposes the real PMMU forms
    directly instead of one merged textual placeholder.
    """
    for inst in kb_data:
        fix = PARSER_ASSERTED_FIELD_VALUE_FIXES.get(str(inst.get("mnemonic")))
        if fix is not None:
            inst["field_form_values"] = deepcopy(fix)


def apply_parser_asserted_encoding_fixes(kb_data: list[JsonDict]) -> None:
    """Apply narrow parser-authored encoding corrections.

    Track B parser-assertion: cpBcc and cpDBcc on PRM pp188-189 have concrete
    first-word layouts in the PDF that the current generic coprocessor extractor
    still collapses into the shared opaque `ID`/condition template. We assert
    the documented word structure here so downstream tools see the real opcode
    fields instead of misleading generic placeholders:
      cpBcc  -> first word carries ID, size, and coprocessor condition
      cpDBcc -> first word carries ID and data register, followed by a
                condition word and a 16-bit displacement word
    The unsized cpBcc syntax still does not identify which displacement width is
    chosen, so we intentionally do not bind its label operand to a specific
    displacement field until that distinction is modeled honestly upstream.

    Track B parser-assertion: cpTRAPcc on PRM p193 uses the same three-form
    opmode split as TRAPcc, but the current syntax extraction collapses it to a
    single immediate form and the generic coprocessor extractor again leaves the
    opcode in the opaque `ID`/condition template. The page's instruction-format
    diagram explicitly shows a first word with `ID` and `OPMODE`, followed by a
    condition word; the opmode field selects the no-operand, word-immediate, and
    long-immediate forms:
      cpTRAPcc           -> OPMODE=100
      cpTRAPcc.W #<data> -> OPMODE=010
      cpTRAPcc.L #<data> -> OPMODE=011
    We assert that structure here so the KB represents the documented family
    instead of an accidental partial parse.

    Track B parser-assertion: PTRAPcc on PRM p532 is the PMMU analogue of
    cpTRAPcc. The current extraction preserves the first PMMU word and condition
    word but drops the optional immediate payload word needed by the .W and .L
    forms. We assert that third word here so downstream tools see the complete
    documented encoding family.
    """
    for inst in kb_data:
        fix = PARSER_ASSERTED_ENCODING_FIXES.get(str(inst.get("mnemonic")))
        if fix is not None:
            inst["encodings"] = deepcopy(fix)


def _replace_encoding_field(
    fields: list[JsonDict],
    *,
    name: str,
    bit_hi: int,
    bit_lo: int,
    replacements: list[JsonDict],
) -> None:
    for index, field in enumerate(fields):
        if (
            str(field.get("name")) == name
            and int(field.get("bit_hi", -1)) == bit_hi
            and int(field.get("bit_lo", -1)) == bit_lo
        ):
            fields[index : index + 1] = deepcopy(replacements)
            return
    raise RuntimeError(f"missing encoding field {name} {bit_hi}:{bit_lo}")


def apply_parser_asserted_pmmu_fc_encoding_fixes(kb_data: list[JsonDict]) -> None:
    """Split 68030 PMMU function-code selector fields.

    Track B parser-assertion: the 68030 PMMU FC operand used by PFLUSH
    (PRM p486), PLOAD (PRM p497), and PTEST (PRM p517) is documented as one
    assembler operand that may be SFC/DFC, Dn, or an immediate value. The PDF
    diagrams label the packed bits as `FC`, but the prose defines the three
    operand classes; the current table extractor therefore collapses the class
    selector and value bits into one opaque field. We assert the standard split:
      selector 00 -> SFC/DFC value bits
      selector 01 -> Dn value bits
      selector 10 -> immediate value bits
    This keeps the generated assembler/disassembler driven by JSON fields
    instead of downstream PMMU opcode special cases.
    """
    for inst in kb_data:
        mnemonic = str(inst.get("mnemonic"))
        if mnemonic not in {"PFLUSH", "PLOAD", "PTEST"}:
            continue
        encodings = inst.get("encodings")
        if not isinstance(encodings, list):
            continue
        if mnemonic == "PLOAD":
            fields = cast(list[JsonDict], encodings[1]["fields"])
            _replace_encoding_field(
                fields,
                name="FC",
                bit_hi=4,
                bit_lo=0,
                replacements=[
                    {"name": "FC-MODE", "bit_hi": 4, "bit_lo": 3, "width": 2},
                    {"name": "FC", "bit_hi": 2, "bit_lo": 0, "width": 3},
                ],
            )
        elif mnemonic == "PFLUSH":
            fields = cast(list[JsonDict], encodings[1]["fields"])
            _replace_encoding_field(
                fields,
                name="MASK",
                bit_hi=7,
                bit_lo=4,
                replacements=[{"name": "MASK", "bit_hi": 7, "bit_lo": 5, "width": 3}],
            )
            _replace_encoding_field(
                fields,
                name="FC",
                bit_hi=3,
                bit_lo=0,
                replacements=[
                    {"name": "FC-MODE", "bit_hi": 4, "bit_lo": 3, "width": 2},
                    {"name": "FC", "bit_hi": 2, "bit_lo": 0, "width": 3},
                ],
            )
        elif mnemonic == "PTEST":
            fields = cast(list[JsonDict], encodings[1]["fields"])
            _replace_encoding_field(
                fields,
                name="REGISTER",
                bit_hi=7,
                bit_lo=3,
                replacements=[
                    {"name": "REGISTER", "bit_hi": 7, "bit_lo": 5, "width": 3},
                    {"name": "FC-MODE", "bit_hi": 4, "bit_lo": 3, "width": 2},
                ],
            )


def apply_parser_asserted_field_binding_fixes(kb_data: list[JsonDict]) -> None:
    """Apply narrow parser-authored field-binding corrections.

    Track B parser-assertion: DBcc uses a second instruction word containing a
    full 16-bit displacement on PRM p189. The current generic binding extractor
    incorrectly leaves the label operand bound to an inexistent
    ``8-BIT DISPLACEMENT`` field on the first word. The actual encoding is:
      first word: condition + data register
      second word: 16-BIT DISPLACEMENT
    We correct the binding so downstream generators attach the label operand to
    the true extension-word field instead of patching DBcc specially.

    Track B parser-assertion: PDBcc on PRM p484 is the PMMU analogue of DBcc.
    The generic extractor still misses the operand mapping onto `COUNT
    REGISTER` and the true 16-bit displacement extension. PTRAPcc on PRM p532
    likewise needs explicit immediate-data bindings for its .W and .L forms once
    the syntax is split. We assert those PMMU bindings here so the KB stays
    structurally faithful upstream.

    Track B parser-assertion: PVALID on PRM pp534-536 has two forms. Both bind
    the destination effective address through MODE/REGISTER, but only the second
    form binds the main-processor address-register source in the final word's
    REGISTER field, while the first form binds the fixed `VAL` source in the
    same field with value 000. The current extractor only binds the
    effective-address operand. We add the missing source bindings here so the
    two PDF forms are represented faithfully.

    Track B parser-assertion: ABCD/SBCD/ADDX/SUBX/CMPM/PACK/UNPK/CHK2/CMP2 on PRM pp106/274/117/287/185/260/299/175/186 encode the destination
    register in bits 11-9 and the source register in bits 2-0 for both the
    data-register and predecrement forms. The field names differ slightly
    between the two pages (`REGISTER Rx/Ry` vs `REGISTER Dx/Ax` and
    `REGISTER Dy/Ay`; `CMPM` uses `REGISTER Ax` / `REGISTER Ay` for the paired
    postincrement form; `PACK`/`UNPK` use the same `Dx/Ax` and `Dy/Ay` naming
    across their register and predecrement forms), so we assert the operand-to-field bindings explicitly
    from the encoding diagram to preserve the generic downstream register path.

    Track B parser-assertion: MOVES on PRM p478 uses:
    first word: effective-address MODE/REGISTER for the <ea> operand
    second word: A/D + REGISTER for the Rn operand, plus constant dr bit
    The current generic extractor does not bind these fields onto the two
    source/destination syntax forms, so we assert the operand mappings here
    from the two-word encoding diagram.

    Track B parser-assertion: CALLM on PRM p168 uses:
      first word: effective-address MODE/REGISTER for the module descriptor
      second word: ARGUMENT COUNT for the immediate byte count
    The generic extractor preserves the two-word encoding but does not bind the
    extension-word argument-count field onto the ``#<data>`` operand, so we
    assert that mapping here from the instruction diagram.

    Track B parser-assertion: CAS on PRM p168 uses:
      first word: effective-address MODE/REGISTER for the destination <ea>
      second word: Du and Dc register fields for the two data-register operands
    The generic extractor preserves the two-word encoding but does not bind the
    extension-word compare/update register fields, so we assert them here.

    Track B parser-assertion: RTD on PRM p490 uses a second-word
    ``16-BIT DISPLACEMENT`` extension for its single immediate operand. The
    generic binding extractor currently leaves that extension field unbound, so
    we assert the immediate-to-extension mapping directly from the diagram.

    Track B parser-assertion: CHK2/CMP2 on PRM pp175/186 use:
      first word: effective-address MODE/REGISTER for the <ea> operand
      second word: D/A + REGISTER for the Rn operand
    The second-word bit 11 is already constant in the encoding diagrams
    (1 for CHK2, 0 for CMP2); we only need to bind the variable fields onto
    the <ea>,Rn syntax form.
    """
    for inst in kb_data:
        fix = PARSER_ASSERTED_FIELD_BINDING_FIXES.get(str(inst.get("mnemonic")))
        if fix is not None:
            if fix:
                inst["field_bindings"] = deepcopy(fix)
            else:
                inst.pop("field_bindings", None)


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 3: Syntax pattern parsing
# ═══════════════════════════════════════════════════════════════════════════════

def _normalize_syntax(raw: str) -> str:
    """Normalize a raw PDF syntax string."""
    s = raw.strip()
    s = s.lstrip("*").strip()
    s = re.sub(r"<\s*(\w+)\s*>", r"<\1>", s)
    s = re.sub(r"\s*,\s*", ",", s)
    s = re.sub(r"–\s*\(", "-(", s)
    s = re.sub(r"\)\s*\+", ")+", s)
    return re.sub(r"\s+", " ", s)


def _parse_operand(token: str) -> JsonDict:
    """Parse a single operand token into a type descriptor."""
    t = token.strip()
    t = re.sub(r"^<size>\s+", "", t, flags=re.IGNORECASE)

    if t in ("<ea>",):
        return {"type": "ea"}
    if t in ("<label>",):
        return {"type": "label"}
    if t.lower().replace(" ", "") == "<caches>":
        return {"type": "cache_sel"}
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

    # PMOVE-style MMU register operand
    if re.match(r"^[Mm][Rr][Nn]\d*$", t):
        return {"type": "ctrl_reg"}
    if re.match(r"^<\s*PMMU\s+Register\s*>$", t, re.IGNORECASE):
        return {"type": "ctrl_reg"}

    # Generic register Rn (MOVEC Rn, MOVES Rn, RTM Rn, CMP2/CHK2 Rn)
    if re.match(r"^[Rr]n\d*$", t):
        return {"type": "rn"}

    # Bit-field EA: "<ea> {offset:width}" forms (BFTST, BFCHG, BFINS, etc.)
    if re.match(r"^<ea>\s*\{", t):
        return {"type": "bf_ea"}

    return {"type": "unknown", "raw": t}


def _split_operands(s: str) -> list[str]:
    """Split operand string by commas, respecting parentheses."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
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


def _split_concatenated_forms(syntax_list: list[str], mnemonic: str) -> list[tuple[str, bool]]:
    """Split concatenated syntax entries into separate forms.

    Returns list of (syntax_str, is_020plus) tuples.
    """
    result: list[tuple[str, bool]] = []
    base = mnemonic.split(",")[0].split()[0]

    for raw_s in syntax_list:
        # Track A: PDF marks 020+ forms with "*" prefix, or embeds
        # "(MC68020..." in syntax text (e.g. EXTB.L on PDF p209)
        is_020 = (raw_s.strip().startswith("*") or
                  "MC68020" in raw_s or "68020" in raw_s)
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


def _parse_syntax_to_form(mnemonic: str, syntax_str: str) -> JsonDict | None:
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
    if inst_base not in known_variants and not (
        inst_base.endswith("D")
        and any(
            v.startswith(inst_base[:-1]) and len(v) == len(inst_base)
            for v in known_variants
        )
    ):
        return None

    operand_str = parts[1] if len(parts) > 1 else ""
    operand_str = re.sub(r"\s+where\s+.*$", "", operand_str, flags=re.IGNORECASE)
    operand_str = re.sub(r"\s*(?:→|->).*$", "", operand_str)

    if not operand_str:
        return {"syntax": s, "operands": []}

    tokens = _split_operands(operand_str)
    operands: list[JsonDict] = []
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


def _parse_operation_effects(operation: str, condition_codes: dict[str, str], mnemonic: str) -> JsonDict:
    """Parse the operation field into structured read/write effects."""
    effects: JsonDict = {
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
    cc_write: list[str] = []
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


def apply_syntax_forms(kb_data: list[JsonDict]) -> None:
    """Phase 3: Parse syntax patterns into structured forms."""
    for inst in kb_data:
        mnemonic = str(inst["mnemonic"])
        raw_syntax_list = inst.get("syntax", [])
        syntax_list = raw_syntax_list if isinstance(raw_syntax_list, list) else []
        syntax_texts = [str(s) for s in syntax_list]

        split_syntaxes = _split_concatenated_forms(syntax_texts, mnemonic)
        forms: list[JsonDict] = []
        for syn, is_020 in split_syntaxes:
            form = _parse_syntax_to_form(mnemonic, syn)
            if form:
                if is_020:
                    form["processor_020"] = True
                forms.append(form)
        inst["forms"] = forms

        raw_cc = inst.get("condition_codes", {})
        effects = _parse_operation_effects(
            str(inst.get("operation", "")),
            {str(k): str(v) for k, v in raw_cc.items()} if isinstance(raw_cc, dict) else {},
            mnemonic,
        )
        inst["effects"] = effects

    with_forms = sum(1 for i in kb_data if i["forms"])
    total_forms = sum(len(cast(list[JsonDict], i["forms"])) for i in kb_data)
    print(f"  Syntax forms: {with_forms}/{len(kb_data)} instructions, {total_forms} total forms")


def _infer_operand_roles(inst: JsonDict, operands: list[JsonDict]) -> list[str | None]:
    roles: list[str | None] = [cast(str | None, operand.get("role")) for operand in operands]
    ea_indexes = [index for index, operand in enumerate(operands) if str(operand.get("type")) == "ea"]
    if any(role is not None for role in roles):
        return roles
    ea_modes = cast(JsonDict, inst.get("ea_modes", {}))
    if len(ea_indexes) == 1:
        if "src" in ea_modes:
            roles[ea_indexes[0]] = "src"
        elif "dst" in ea_modes:
            roles[ea_indexes[0]] = "dst"
        elif "ea" in ea_modes:
            roles[ea_indexes[0]] = "ea"
    elif len(ea_indexes) == 2 and "src" in ea_modes and "dst" in ea_modes:
        roles[ea_indexes[0]] = "src"
        roles[ea_indexes[1]] = "dst"
    return roles


def _apply_field_bindings(kb_data: list[JsonDict]) -> int:
    """Bind repeated encoding fields to operand/value sources.

    Some encodings, notably MOVE, repeat generic field names like MODE/REGISTER
    for multiple operands. The PDF field descriptions distinguish "Source
    Effective Address" vs "Destination Effective Address", but the extracted bit
    tables do not retain that association. This pass reconstructs operand-field
    bindings from the parsed syntax, EA direction tables, and field-description
    labels so downstream generators do not guess from mnemonic-specific rules.
    """
    count = 0
    for inst in kb_data:
        forms = cast(list[JsonDict], inst.get("forms", []))
        encodings = cast(list[JsonDict], inst.get("encodings", []))
        if not forms or not encodings:
            continue
        fields = cast(list[JsonDict], encodings[0].get("fields", []))
        field_descriptions = {str(k): str(v) for k, v in cast(dict[str, str], inst.get("field_descriptions", {})).items()}
        occurrences: dict[str, int] = {}
        register_groups: list[list[tuple[str, int]]] = []
        ea_groups: list[list[tuple[str, int]]] = []
        field_index = 0
        while field_index < len(fields):
            field_name = str(fields[field_index]["name"])
            occurrence = occurrences.get(field_name, 0)
            occurrences[field_name] = occurrence + 1
            if field_name not in {"MODE", "REGISTER"}:
                field_index += 1
                continue
            group = [(field_name, occurrence)]
            if field_index + 1 < len(fields):
                next_name = str(fields[field_index + 1]["name"])
                if {field_name, next_name} == {"MODE", "REGISTER"}:
                    next_occurrence = occurrences.get(next_name, 0)
                    occurrences[next_name] = next_occurrence + 1
                    group.append((next_name, next_occurrence))
                    field_index += 2
                else:
                    field_index += 1
            else:
                field_index += 1
            if len(group) == 2 and {name for name, _occ in group} == {"MODE", "REGISTER"}:
                ea_groups.append(group)
            else:
                register_groups.append(group)

        bindings: list[JsonDict] = []
        has_opmode = any(str(field["name"]) == "OPMODE" for field in fields)
        opmode_table = cast(list[JsonDict], cast(JsonDict, inst.get("constraints", {})).get("opmode_table", []))
        for form_index, form in enumerate(forms):
            operands = cast(list[JsonDict], form.get("operands", []))
            operand_roles = _infer_operand_roles(inst, operands)
            imm_indexes = [index for index, operand in enumerate(operands) if str(operand.get("type")) == "imm"]
            label_indexes = [index for index, operand in enumerate(operands) if str(operand.get("type")) == "label"]

            for occurrence, operand_index in enumerate(imm_indexes):
                bindings.append(
                    {
                        "form_index": form_index,
                        "field": "DATA",
                        "occurrence": occurrence,
                        "operand_index": operand_index,
                        "value_source": "value",
                    }
                )
            for occurrence, operand_index in enumerate(label_indexes):
                bindings.append(
                    {
                        "form_index": form_index,
                        "field": "8-BIT DISPLACEMENT",
                        "occurrence": occurrence,
                        "operand_index": operand_index,
                        "value_source": "value",
                    }
                )

            ea_operand_indexes = [index for index, operand in enumerate(operands) if str(operand.get("type")) == "ea"]
            ea_binding_order = ea_operand_indexes
            if len(ea_groups) == 2 and len(ea_operand_indexes) == 2:
                roles_to_index = {operand_roles[index]: index for index in ea_operand_indexes}
                if "Destination Effective Address" in field_descriptions and "Source Effective Address" in field_descriptions:
                    ea_binding_order = [
                        roles_to_index.get("dst", ea_operand_indexes[1]),
                        roles_to_index.get("src", ea_operand_indexes[0]),
                    ]
            for group, operand_index in zip(ea_groups, ea_binding_order, strict=False):
                for field_name, occurrence in group:
                    bindings.append(
                        {
                            "form_index": form_index,
                            "field": field_name,
                            "occurrence": occurrence,
                            "operand_index": operand_index,
                            "value_source": "ea_mode" if field_name == "MODE" else "ea_reg",
                        }
                    )

            register_operand_indexes = [
                index for index, operand in enumerate(operands)
                if str(operand.get("type")) in {"an", "dn", "rn"}
            ]
            for group, operand_index in zip(register_groups, register_operand_indexes, strict=False):
                for field_name, occurrence in group:
                    if field_name != "REGISTER":
                        continue
                    bindings.append(
                        {
                            "form_index": form_index,
                            "field": field_name,
                            "occurrence": occurrence,
                            "operand_index": operand_index,
                            "value_source": "reg",
                        }
                    )

            if has_opmode and opmode_table:
                operand_types = tuple(str(operand.get("type")) for operand in operands)
                if operand_types == ("ea", "dn"):
                    ea_is_source = True
                elif operand_types == ("dn", "ea"):
                    ea_is_source = False
                else:
                    ea_is_source = None
                if ea_is_source is not None and any(entry.get("ea_is_source") == ea_is_source for entry in opmode_table):
                    bindings.append(
                        {
                            "form_index": form_index,
                            "field": "OPMODE",
                            "occurrence": 0,
                            "operand_index": -1,
                            "value_source": "opmode",
                        }
                    )

        if bindings:
            bindings.sort(key=lambda entry: (int(entry["form_index"]), str(entry["field"]), int(entry["occurrence"])))
            inst["field_bindings"] = bindings
            count += 1
    return count


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 4: Constraint derivation
# ═══════════════════════════════════════════════════════════════════════════════

def _find_encoding_field(encodings: list[JsonDict], target_name: str) -> tuple[str, int] | None:
    """Find a named field in the encodings list, return (name, width) or None."""
    target_upper = target_name.upper()
    for enc in encodings:
        fields = cast(list[JsonDict], enc.get("fields", []))
        for f in fields:
            name = str(f["name"])
            if name.upper() == target_upper:
                return name, cast(int, f["width"])
    return None


def _find_field_description(fd: dict[str, str], field_name: str) -> str:
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


def _extract_immediate_range(inst: JsonDict) -> JsonDict | None:
    """Extract immediate value range from encoding field width and field_descriptions."""
    fd = cast(dict[str, str], inst.get("field_descriptions", {}))
    encodings = cast(list[JsonDict], inst.get("encodings", []))

    if not encodings:
        return None

    # Iterate over all named encoding fields; let descriptions drive extraction
    for enc in encodings:
        for f in cast(list[JsonDict], enc.get("fields", [])):
            field_name = str(f["name"])
            if field_name in ("0", "1"):
                continue
            if _STRUCTURAL_FIELD_RE.search(field_name):
                continue

            bit_width = cast(int, f["width"])
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


def _extract_cc_parameterization(inst: JsonDict) -> JsonDict | None:
    """Extract condition code parameterization from encoding and mnemonic."""
    mnemonic = str(inst["mnemonic"])

    if "cc" not in mnemonic:
        return None

    encodings = cast(list[JsonDict], inst.get("encodings", []))
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


def _extract_direction_variants(inst: JsonDict) -> JsonDict | None:
    """Extract direction variant info from dr field description."""
    fd = cast(dict[str, str], inst.get("field_descriptions", {}))
    mnemonic = str(inst["mnemonic"])

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


def _extract_operand_modes(inst: JsonDict) -> JsonDict | None:
    """Extract R/M operand mode variants from field description."""
    fd = cast(dict[str, str], inst.get("field_descriptions", {}))

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


def _extract_movem_direction(inst: JsonDict) -> JsonDict | None:
    """Extract register-to-memory/memory-to-register direction from dr field description."""
    fd = cast(dict[str, str], inst.get("field_descriptions", {}))
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


def _extract_shift_count_range(inst: JsonDict) -> JsonDict | None:
    """Extract shift/rotate count range from encoding structure."""
    fd = cast(dict[str, str], inst.get("field_descriptions", {}))
    encodings = cast(list[JsonDict], inst.get("encodings", []))

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
            bits = cr_field[1] if cr_field else hi.bit_length()
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
        fields = cast(list[JsonDict], enc.get("fields", []))
        has_ir = any(str(f["name"]) == "i/r" for f in fields)
        count_field = next((f for f in fields if str(f["name"]) == "REGISTER"
                           and cast(int, f["width"]) == 3 and cast(int, f["bit_hi"]) >= 9), None)
        if has_ir and count_field:
            bits = cast(int, count_field["width"])
            return {
                "min": 1, "max": 1 << bits,
                "field": "Count/Register", "bits": bits,
                "zero_means": 1 << bits,
            }

    return None


def _extract_sizes_68000(inst: JsonDict) -> list[str] | None:
    """Filter sizes to 68000-only by checking asterisk in attributes."""
    attrs = str(inst.get("attributes", ""))
    sizes = cast(list[str], inst.get("sizes", []))

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


def _extract_memory_size_restriction(inst: JsonDict) -> str | None:
    """Detect if memory EA form has a fixed size (shift/rotate memory = word only).

    Derives size field position from the register-form encoding's SIZE field,
    then checks if those bits are all-fixed in the memory-form encoding.
    """
    encodings = cast(list[JsonDict], inst.get("encodings", []))
    if len(encodings) < 2:
        return None

    has_dr = _find_encoding_field(encodings, "dr") is not None
    if not has_dr:
        return None

    # Find SIZE field position from register-form encoding (has i/r field)
    size_hi = size_lo = None
    for enc in encodings:
        fields = cast(list[JsonDict], enc.get("fields", []))
        if any(str(f["name"]) == "i/r" for f in fields):
            for f in fields:
                if str(f["name"]) == "SIZE":
                    size_hi, size_lo = cast(int, f["bit_hi"]), cast(int, f["bit_lo"])
                    break
            if size_hi is not None:
                break
    if size_hi is None:
        return None

    # Track B parser-assertion: Size field encoding from PDF p29, Table 2-3
    # "Operand Data Length": 00=byte, 01=word, 10=long.
    # This encoding appears in instruction format fields throughout Section 4.
    SIZE_MAP = {0: "b", 1: "w", 2: "l"}

    # Check memory-form encoding (has MODE but not i/r)
    for enc in encodings:
        fields = cast(list[JsonDict], enc.get("fields", []))
        has_mode = any(str(f["name"]) == "MODE" for f in fields)
        has_ir = any(str(f["name"]) == "i/r" for f in fields)
        has_dr_field = any(str(f["name"]) == "dr" for f in fields)

        if has_mode and not has_ir and has_dr_field:
            # Check if all bits at the SIZE field position are fixed
            fixed_val = 0
            all_fixed = True
            assert size_lo is not None
            for bit in range(size_lo, size_hi + 1):
                bf = next((f for f in fields if cast(int, f["bit_hi"]) == bit and cast(int, f["bit_lo"]) == bit), None)
                if bf and str(bf["name"]) in ("0", "1"):
                    fixed_val |= int(str(bf["name"])) << (bit - size_lo)
                else:
                    all_fixed = False
                    break
            if all_fixed:
                if fixed_val in SIZE_MAP:
                    return SIZE_MAP[fixed_val]
                # Non-standard SIZE value — memory-form discriminator;
                # derive actual size from instruction attributes
                attrs = str(inst.get("attributes", "")).lower()
                for sz_name, sz_letter in [("word", "w"), ("byte", "b"), ("long", "l")]:
                    if sz_name in attrs:
                        return sz_letter

    return None


def _extract_bit_op_size_restriction(inst: JsonDict) -> JsonDict | None:
    """Detect bit operation size behavior from description."""
    desc = str(inst.get("description", ""))
    has_reg_32 = "modulo 32" in desc
    has_mem_byte = "byte operation" in desc.lower() or "modulo 8" in desc

    if has_reg_32 or has_mem_byte:
        return {"dn": "l", "memory": "b"}
    return None


def _extract_an_size_restriction(inst: JsonDict) -> list[str] | None:
    """Detect address register size restriction from description.

    Parser-asserted KB entry: ADDQ and SUBQ descriptions state that only
    word and long operations are allowed on address registers. The PDF
    lists byte in the overall sizes but restricts An destinations to
    word/long. This is a standard M68K constraint: byte-size operations
    on address registers are architecturally invalid.

    Cited from PDF pages 4-11 (ADDQ) and 4-173 (SUBQ):
      ADDQ: "Word and long operations are also allowed on the address registers."
      SUBQ: "Only word and long operations can be used with address registers"

    Cannot be parsed from the encoding alone because the SIZE field allows
    byte, but the combination of SIZE=byte + MODE=An is reserved.
    """
    desc = str(inst.get("description", ""))
    ea = cast(dict[str, list[str]], inst.get("ea_modes", {}))
    sizes = cast(list[str], inst.get("sizes", []))
    if "an" not in ea.get("dst", []):
        return None
    if "b" not in sizes:
        return None
    # Match both ADDQ and SUBQ description patterns
    desc_lower = desc.lower()
    if ("word and long" in desc_lower and "address register" in desc_lower):
        return ["w", "l"]
    if ("only word" in desc_lower and "address register" in desc_lower):
        return ["w", "l"]
    return None


def _derive_processor_min(processors: str) -> str:
    """Derive processor_min from the processors field using CPU_HIERARCHY."""
    if not processors or "M68000 Family" in processors:
        return "68000"

    order = cast(list[str], CPU_HIERARCHY["order"])
    # Track B parser-assertion: Coprocessors (68881/68882/68851) require 68020+.
    # PDF Section 1.2 (p1-1): the 68881/68882 FPU and 68851 PMMU are described
    # as coprocessors for the MC68020 and above. No coprocessor instruction page
    # lists MC68000 or MC68010 in its processor field.
    _COPROCESSOR_IMPLIES = "68020"
    min_idx = len(order)
    has_cpu32 = False
    deferred_variant_indices: list[int] = []

    for proc_token in re.findall(r"M(?:C)?68\w+|CPU32", processors):
        if proc_token == "CPU32":
            has_cpu32 = True
            continue
        token = proc_token
        if token.startswith("MC"):
            token = token[2:]
        elif token.startswith("M"):
            token = token[1:]
        is_family_variant = bool(re.match(r"68(?:EC|LC)\d+$", token))
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

        if is_family_variant:
            deferred_variant_indices.append(idx)
        elif idx < min_idx:
            min_idx = idx

    if min_idx == len(order) and deferred_variant_indices:
        min_idx = min(deferred_variant_indices)

    if min_idx < len(order):
        return order[min_idx]
    if has_cpu32:
        return "cpu32"
    return "68000"


def _derive_processor_set(processors: str) -> list[str]:
    """Derive exact supported base CPUs from the processors field."""
    order = cast(list[str], CPU_HIERARCHY["order"])
    if not processors or "M68000 Family" in processors:
        return list(order)

    explicit: set[str] = set()
    has_cpu32 = False
    has_coprocessor_only = False

    for proc_token in re.findall(r"M(?:C)?68\w+|CPU32", processors):
        if proc_token == "CPU32":
            has_cpu32 = True
            continue
        token = proc_token
        if token.startswith("MC"):
            token = token[2:]
        elif token.startswith("M"):
            token = token[1:]
        core = re.sub(r"^68[A-Z]{1,2}(\d)", r"68\1", token)
        if core in ("68881", "68882", "68851"):
            has_coprocessor_only = True
            continue
        if core in order:
            explicit.add(core)
            continue
        matched = next((cpu for cpu in order if core.startswith(cpu[:4])), None)
        if matched is not None:
            explicit.add(matched)

    if explicit:
        return [cpu for cpu in order if cpu in explicit]
    if has_cpu32 or has_coprocessor_only:
        return [cpu for cpu in order if order.index(cpu) >= order.index("68020")]
    return list(order)


def _extract_opmode_table(doc: Any, inst: JsonDict) -> list[JsonDict] | None:
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
    raw_pages = inst.get("pages", [inst.get("page", 0)])
    pages = [int(pg) for pg in raw_pages] if isinstance(raw_pages, list) else []
    if not pages:
        return None

    # Check if this instruction has an OPMODE encoding field
    has_opmode = False
    for enc in cast(list[JsonDict], inst.get("encodings", [])):
        for f in cast(list[JsonDict], enc.get("fields", [])):
            if str(f["name"]).upper() == "OPMODE":
                has_opmode = True
                break
    if not has_opmode:
        return None

    SIZE_MAP = {"byte": "b", "word": "w", "long": "l"}
    entries: list[JsonDict] = []

    for pg in pages:
        page = doc[pg - 1]
        spans = extract_page_spans(page)
        rows = spans_to_rows(spans)
        sorted_ys = sorted(rows.keys())

        in_opmode = False
        header_cols: dict[str, float] = {}  # "Byte"->x, "Word"->x, "Long"->x, "Operation"->x
        src_dst_cols: dict[str, float] = {}  # "source"->x, "destination"->x, "syntax"->x (Format 3)

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
            row_texts = [t for _, _, t, _, _ in row_items]
            if ("Byte" in row_texts or "byte" in texts) and ("word" in texts or "Word" in row_texts):
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
                                best_dist = int(dist)
                                best_size = sz_name
                        if best_size:
                            entry = {
                                "opmode": opmode_val,
                                "size": SIZE_MAP.get(best_size, best_size),
                                "operation": operation,
                            }
                            # Derive ea_is_source from operation text.
                            # Parser-asserted from PDF Section 4 opmode tables.
                            # Format 1 operations use Unicode arrow U+2192.
                            # "< ea > OP Dn -> Dn" means EA is source,
                            # "Dn OP < ea > -> < ea >" means EA is destination.
                            # CMP has no arrow (no writeback): "Dn - < ea >",
                            # always ea_is_source=True.
                            if "\u2192" in operation:
                                result = operation.split("\u2192")[-1].lower()
                                if "dn" in result:
                                    entry["ea_is_source"] = True
                                elif "ea" in result:
                                    entry["ea_is_source"] = False
                            elif "ea" in operation.lower():
                                # No arrow = no writeback (CMP): ea is source
                                entry["ea_is_source"] = True
                            entries.append(entry)

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
                entry = {
                    "opmode": opmode_val,
                    "size": sz,
                    "description": desc,
                }
                # Derive ea_is_source for instructions with EA operand.
                # Parser-asserted: ADDA, CMPA, SUBA syntax is "<ea> , An"
                # — the EA is always the source operand (PDF pp 4-7, 4-34,
                # 4-174). Match with spaces normalized.
                inst_syntax = cast(list[str], inst.get("syntax", []))
                for s in inst_syntax:
                    sn = s.replace(" ", "").lower()
                    if "<ea>" in sn and (",a" in sn or ",d" in sn):
                        entry["ea_is_source"] = True
                        break
                # Derive rx_mode/ry_mode for EXG from description text.
                # Parser-asserted from PDF p4-105, EXG Instruction Fields:
                #   01000 = "Data registers"
                #   01001 = "Address registers"
                #   10001 = "Data register and address register"
                # Only applies to EXG (not other Format 2 instructions).
                if "EXG" in str(inst.get("mnemonic", "")):
                    if "data register" in dl and "address register" in dl:
                        entry["rx_mode"] = "dn"
                        entry["ry_mode"] = "an"
                    elif "data register" in dl:
                        entry["rx_mode"] = "dn"
                        entry["ry_mode"] = "dn"
                    elif "address register" in dl:
                        entry["rx_mode"] = "an"
                        entry["ry_mode"] = "an"
                entries.append(entry)

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


def _extract_control_registers(doc: Any, inst: JsonDict) -> list[JsonDict] | None:
    """Extract MOVEC control register table from PDF.

    Parses the hex-code → name(abbreviation) table on the MOVEC page,
    tracking CPU section headers to assign processor_min per register.
    Returns list of {hex, name, abbrev, processor_min} dicts, or None.
    """
    raw_pages = inst.get("pages", [inst.get("page", 0)])
    pages = [int(pg) for pg in raw_pages] if isinstance(raw_pages, list) else []
    if not pages:
        return None

    def _is_hex3(t: str) -> bool:
        return len(t) == 3 and all(c in "0123456789ABCDEFabcdef" for c in t)

    def _find_desc(row_items: list[RowItem]) -> str:
        """Find description text with parenthesized abbreviation."""
        for x, _, t, _, _ in row_items:
            if x > 220 and t[0].isupper() and "(" in t:
                return t
        return ""

    def _cpu_set_from_header(text: str) -> list[str] | None:
        """Derive exact supported CPUs from a CPU section header."""
        cpus = re.findall(r"MC?68(\d{3})", text)
        if cpus:
            explicit = {f"68{int(cpu):03d}" for cpu in cpus}
            order = cast(list[str], CPU_HIERARCHY["order"])
            return [cpu for cpu in order if cpu in explicit]
        if "CPU32" in text:
            order = cast(list[str], CPU_HIERARCHY["order"])
            return [cpu for cpu in order if order.index(cpu) >= order.index("68020")]
        return None

    regs: list[JsonDict] = []
    seen_hex: set[tuple[str, str]] = set()
    for pg in pages:
        page = doc[pg - 1]
        spans = extract_page_spans(page)
        rows = spans_to_rows(spans)
        sorted_ys = sorted(rows.keys())

        current_cpu_set = _derive_processor_set(str(inst.get("processors", "")))
        current_cpu = current_cpu_set[0]
        for idx, y_key in enumerate(sorted_ys):
            row_items = rows[y_key]
            row_text = " ".join(t for _, _, t, _, _ in row_items)

            # Check for CPU section header (e.g. "MC68020/MC68030/MC68040")
            if "MC68" in row_text or "CPU32" in row_text:
                cpu_set = _cpu_set_from_header(row_text)
                if cpu_set and not _is_hex3(row_text.split()[0] if row_text.split() else ""):
                    current_cpu_set = cpu_set
                    current_cpu = current_cpu_set[0]
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
                        "processor_set": current_cpu_set,
                    })

    return regs if regs else None


def _extract_pmove_control_registers(doc: Any, inst: JsonDict) -> list[JsonDict] | None:
    """Extract 68030 PMOVE register names and encoded values from the PDF.

    PMOVE on PRM pp.6-48 through 6-52 is split across several sub-pages:
    - p.6-49 lists the P-REGISTER values for TC/SRP/CRP.
    - p.6-49 also gives the dedicated MMU status register format.
    - p.6-50 lists the P-REGISTER values for TT0/TT1.
    We parse those page texts directly so the KB carries the PMOVE register set
    from the manual instead of keeping MRn as an opaque placeholder.

    The 68030 manual page names the dedicated status-register form "MMU Status
    Register" but later PMOVE pages use the PMMU abbreviation "PSR". We expose
    the 68030 spelling as `psr` so downstream tools can share one control-
    register namespace with the existing assembler/disassembler oracle cases.
    """
    raw_pages = inst.get("pages", [inst.get("page", 0)])
    pages = [int(pg) for pg in raw_pages] if isinstance(raw_pages, list) else []
    if not pages:
        return None

    page_texts: dict[int, str] = {}
    for pg in pages:
        page_texts[pg] = doc[pg - 1].get_text("text")

    regs: list[JsonDict] = []
    seen: set[str] = set()

    def add_reg(abbrev: str, value: int, processor_set: list[str]) -> None:
        if abbrev in seen:
            return
        seen.add(abbrev)
        regs.append({
            "hex": f"{value:03X}",
            "name": abbrev.upper(),
            "abbrev": abbrev,
            "processor_min": processor_set[0],
            "processor_set": processor_set,
        })

    text_503 = page_texts.get(503, "")
    if "Translation Control Register" in text_503:
        mappings = {
            "tc": r"000—Translation Control Register",
            "srp": r"010—Supervisor Root Pointer",
            "crp": r"011—CPU Root Pointer",
        }
        values = {"tc": 0x000, "srp": 0x002, "crp": 0x003}
        for abbrev, pattern in mappings.items():
            if re.search(pattern, text_503):
                add_reg(abbrev, values[abbrev], ["68030"])
        if "MMU Status Register" in text_503:
            # Parser-asserted alias from PMOVE PRM pp.6-49 and 6-56:
            # p.6-49 defines the dedicated 68030 "MMU Status Register" PMOVE
            # form, while p.6-56 names the same PMMU status register as PSR.
            # The manual does not restate the abbreviation on the 68030 page,
            # but both pages describe the same register/function. Downstream
            # tools need one stable operand spelling, so expose it as `psr`.
            add_reg("psr", 0x018, ["68030"])

    text_504 = page_texts.get(504, "")
    if "Transparent Translation Register 0" in text_504:
        mappings = {
            "tt0": r"010—Transparent Translation Register 0",
            "tt1": r"011—Transparent Translation Register 1",
        }
        values = {"tt0": 0x002, "tt1": 0x003}
        for abbrev, pattern in mappings.items():
            if re.search(pattern, text_504):
                add_reg(abbrev, values[abbrev], ["68030"])

    return regs if regs else None


def _extract_pvalid_control_registers(doc: Any, inst: JsonDict) -> list[JsonDict] | None:
    """Extract the fixed VAL PMMU register operand from the PVALID pages.

    PRM pp.6-80 through 6-82 print two explicit PVALID formats:
    - `PVALID VAL,<ea>`
    - `PVALID An,<ea>`
    The VAL form is a fixed PMMU valid-access-level register selector, not a
    generic unknown token. The PDF does not provide a separate register table,
    but the instruction-format text explicitly names the operand and the
    encoding shows the trailing register field fixed to 000 for that form.
    Expose it as a structured control register so the KB and generators can
    carry the form honestly.
    """
    raw_pages = inst.get("pages", [inst.get("page", 0)])
    pages = [int(pg) for pg in raw_pages] if isinstance(raw_pages, list) else []
    if not pages:
        return None
    for pg in pages:
        page_text = doc[pg - 1].get_text("text")
        if "PVALID VAL,<ea>" in page_text or "VAL Contains Access Level to Test Against" in page_text:
            return [{
                "hex": "000",
                "name": "Valid Access Level Register",
                "abbrev": "val",
                "processor_min": "68020",
                "processor_set": ["68020", "68030", "68040", "68060"],
            }]
    return None


def _derive_cc_exclusions(kb_data: list[JsonDict]) -> None:
    """Derive excluded CC values for cc-parameterized instructions.

    If Bcc with cc=0 ("t") produces the same first-word encoding as standalone BRA,
    then "t" should be excluded.  Detect by building mask/val for each standalone
    instruction's first encoding word and checking for collisions when substituting
    each CC value into the CONDITION field.
    """
    def _enc_mask_val(enc: JsonDict) -> tuple[int, int]:
        """Build (mask, val) from an encoding's first word fixed bits."""
        mask = 0
        val = 0
        for f in cast(list[JsonDict], enc["fields"]):
            bit_lo = cast(int, f["bit_lo"])
            bit_hi = cast(int, f["bit_hi"])
            if bit_lo < 0:  # extension word field
                break
            try:
                fv = int(str(f["name"]))
                for b in range(bit_lo, bit_hi + 1):
                    mask |= (1 << b)
                    val |= (fv << b)
            except ValueError:
                pass  # variable field — skip
        return mask, val

    # Build set of (mask, val) for all standalone (non-cc) instructions
    standalone_encs: set[tuple[int, int]] = set()
    for inst in kb_data:
        if "cc" in str(inst["mnemonic"]).lower():
            continue
        for enc in cast(list[JsonDict], inst.get("encodings", [])):
            standalone_encs.add(_enc_mask_val(enc))

    for inst in kb_data:
        constraints = cast(dict[str, JsonDict], inst.get("constraints", {}))
        cc_param = constraints.get("cc_parameterized")
        if not cc_param:
            continue
        for enc in cast(list[JsonDict], inst.get("encodings", [])):
            # Find the CONDITION field
            cc_field = None
            for f in cast(list[JsonDict], enc["fields"]):
                if str(f["name"]).upper() == "CONDITION":
                    cc_field = f
                    break
            if not cc_field:
                continue
            # Build base mask/val (without condition bits)
            base_mask, base_val = _enc_mask_val(enc)
            # Add condition field bits to mask
            cc_mask = 0
            cc_bit_lo = cast(int, cc_field["bit_lo"])
            cc_bit_hi = cast(int, cc_field["bit_hi"])
            for b in range(cc_bit_lo, cc_bit_hi + 1):
                cc_mask |= (1 << b)
            full_mask = base_mask | cc_mask
            # Check each CC value
            for cc_val, cc_name in CC_TABLE.items():
                test_val = base_val | (cc_val << cc_bit_lo)
                # Does this match any standalone instruction?
                for s_mask, s_val in standalone_encs:
                    # Check if the standalone's fixed bits match our test value
                    if (test_val & s_mask) == s_val and (s_val & full_mask) == test_val:
                        cast(list[str], cc_param["excluded"]).append(cc_name)
                        break


def _parse_sizes(attrs_str: str) -> list[str]:
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


def apply_constraints(kb_data: list[JsonDict], doc: Any = None) -> None:
    """Phase 4: Extract constraints from instruction data."""
    for inst in kb_data:
        inst["processor_min"] = _derive_processor_min(str(inst.get("processors", "")))
        inst["processor_set"] = _derive_processor_set(str(inst.get("processors", "")))
        inst["sizes"] = _parse_sizes(str(inst.get("attributes", "")))
        syntax = cast(list[str], inst.get("syntax", []))
        inst["uses_label"] = any("<label>" in s.lower() or "< label >" in s.lower()
                                 for s in syntax)
        # Derive operation_class from title text.
        # Parser-asserted: the instruction title uniquely identifies certain
        # classes needed by downstream tools. "Load Effective Address" (LEA,
        # PDF p4-110) and "Move Multiple Registers" (MOVEM, p4-128) have
        # special semantics that cannot be inferred from other KB fields.
        _TITLE_TO_CLASS = {
            "Load Effective Address": "load_effective_address",
            "Move Multiple Registers": "multi_register_transfer",
        }
        title = str(inst.get("title", ""))
        op_class = _TITLE_TO_CLASS.get(title)
        if op_class:
            inst["operation_class"] = op_class

        constraints: JsonDict = {}

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

        asr = _extract_an_size_restriction(inst)
        if asr:
            constraints["an_sizes"] = asr

        # Extract opmode table from PDF (for ADD, OR, SUB, AND, CMP, EOR, MOVEP, EXG, etc.)
        if doc:
            opm = _extract_opmode_table(doc, inst)
            if opm:
                constraints["opmode_table"] = opm

        # Extract control register table for MOVEC/PMOVE-like instructions
        forms = cast(list[JsonDict], inst.get("forms", []))
        if doc and any(f.get("operands") and
                       any(op.get("type") == "ctrl_reg"
                           for op in cast(list[JsonDict], f["operands"]))
                       for f in forms):
            if str(inst.get("mnemonic")) == "PMOVE":
                ctrl_regs = _extract_pmove_control_registers(doc, inst)
            elif str(inst.get("mnemonic")) == "PVALID":
                ctrl_regs = _extract_pvalid_control_registers(doc, inst)
            else:
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


def _classify_cc_description(desc: str) -> JsonDict | None:
    """Classify a CC description string into a semantic rule dict."""
    for pattern, factory in _CC_SEMANTIC_PATTERNS:
        m = re.match(pattern, desc)
        if m:
            return cast(Callable[[Match[str]], JsonDict], factory)(m)
    return None


def apply_cc_semantics(kb_data: list[JsonDict]) -> int:
    """Phase 8: Classify CC descriptions into semantic rules."""
    classified = 0
    unclassified = []

    for inst in kb_data:
        cc = cast(dict[str, str], inst.get("condition_codes", {}))
        # Track A: PDF p271 RTR has blanket "Set to the condition codes from
        # the stack" instead of per-flag entries. Detect from Description text.
        description = str(inst.get("description", "")).lower()
        if re.search(r'(?:pulls?|loads?|restores?)\s+(?:the\s+)?condition\s+code', description):
            inst["cc_semantics"] = {f: {"rule": "loaded_from_stack"}
                                    for f in ("X", "N", "Z", "V", "C")}
            classified += 1
            continue
        semantics: JsonDict = {}
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
            "Unclassified CC descriptions — add patterns to "
            "_CC_SEMANTIC_PATTERNS:\n  " + "\n  ".join(msgs)
        )

    return classified


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 9: SP effect extraction from Operation field
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_sp_effects(operation: str, mnemonic: str) -> tuple[list[JsonDict], bool]:
    """Parse an Operation string into a list of structured SP effects.

    Returns a list of effect dicts, e.g.:
      [{"action": "push", "bytes": 4}, {"action": "adjust", "expr": "d"}]
    Returns (effects, complete) where complete means the operation was fully
    represented by structured SP effects.
    Returns ([], False) if no SP effects.
    Raises RuntimeError if a clause references SP but no pattern matched.
    """
    if not operation or ("SP" not in operation and "SSP" not in operation):
        return [], False

    effects: list[JsonDict] = []
    complete = True
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

        # (SP) → An  (load address register from stack, e.g. UNLK)
        m = re.match(r"\(SP\)\s*→\s*An", clause)
        if m:
            effects.append({"action": "load_from_stack_to_reg", "bytes": 4, "reg": "An"})
            continue

        # SP → An  (save SP to register, e.g. LINK)
        m = re.match(r"SP\s*→\s*An", clause)
        if m:
            effects.append({"action": "save_to_reg", "reg": "An"})
            continue

        # An → (SP)  (store address register to stack, e.g. LINK)
        m = re.match(r"An\s*→\s*\(SP\)", clause)
        if m:
            effects.append({"action": "store_reg_to_stack", "bytes": 4, "reg": "An"})
            continue

        # Clauses that read/write through SP but don't change it (e.g. "PC → (SP)",
        # "(SP) → PC", "Vector Offset → (SSP)") — not SP effects, skip
        if re.search(r"→\s*\(S?SP\)|\(S?SP\)\s*→", clause):
            continue

        # If clause mentions SP/SSP and we didn't match, that's an error
        if "SP" in clause:
            unmatched_sp_clauses.append(clause)
            complete = False
            continue

        complete = False

    if unmatched_sp_clauses:
        raise RuntimeError(
            f"{mnemonic}: SP clause(s) not matched — add patterns to "
            f"_parse_sp_effects:\n  " + "\n  ".join(unmatched_sp_clauses)
        )

    return effects, complete


def _sp_effects_complete(operation: str) -> bool:
    """Return True when the Operation field is fully represented by SP effects."""
    if not operation or ("SP" not in operation and "SSP" not in operation):
        return False

    clauses = [c.strip() for c in operation.split(";")]
    normalized_clauses = [
        clause.replace("\u2013", "-").replace("\u2014", "-").replace("\u2192", "->")
        for clause in clauses
        if clause
    ]
    normalized_patterns = (
        r"\*?S?SP\s*-\s*(\d+)\s*->\s*\*?S?[Ss][Pp]",
        r"S?SP\s*\+\s*(\d+)\s*->\s*S?[Ss][Pp]",
        r"S?SP\s*\+\s*([a-z_]\w*)\s*->\s*S?[Ss][Pp]",
        r"S?SP\s*\+\s*(\d+)\s*\+\s*([a-z_]\w*)\s*->\s*S?[Ss][Pp]",
        r"An\s*->\s*SP",
        r"\(SP\)\s*->\s*An",
        r"SP\s*->\s*An",
        r"An\s*->\s*\(SP\)",
    )
    if all(any(re.match(pattern, clause) for pattern in normalized_patterns)
           for clause in normalized_clauses):
        return True

    represented_patterns = (
        r"\*?S?SP\s*[\u2013\u2014-]\s*(\d+)\s*\u2192\s*\*?S?[Ss][Pp]",
        r"S?SP\s*\+\s*(\d+)\s*\u2192\s*S?[Ss][Pp]",
        r"S?SP\s*\+\s*([a-z_]\w*)\s*\u2192\s*S?[Ss][Pp]",
        r"S?SP\s*\+\s*(\d+)\s*\+\s*([a-z_]\w*)\s*\u2192\s*S?[Ss][Pp]",
        r"An\s*\u2192\s*SP",
        r"\(SP\)\s*\u2192\s*An",
        r"SP\s*\u2192\s*An",
        r"An\s*\u2192\s*\(SP\)",
    )
    for clause in clauses:
        if not clause:
            continue
        if not any(re.match(pattern, clause) for pattern in represented_patterns):
            return False
    return True


def apply_sp_effects(kb_data: list[JsonDict]) -> int:
    """Phase 9: Extract structured SP effects from Operation field."""
    with_effects = 0
    for inst in kb_data:
        operation = str(inst.get("operation", ""))
        sp_effects, _complete = _parse_sp_effects(operation, str(inst["mnemonic"]))
        if sp_effects:
            inst["sp_effects"] = sp_effects
            if _sp_effects_complete(operation):
                inst["sp_effects_complete"] = True
            with_effects += 1
    return with_effects


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 10: PC effect extraction
# ═══════════════════════════════════════════════════════════════════════════════

def _is_real_extension_word(enc: JsonDict) -> bool:
    """Return True if this encoding entry is a real extension word, not a label."""
    fields = cast(list[JsonDict], enc.get("fields", []))
    if len(fields) != 1:
        return False
    name = str(fields[0]["name"])
    # Filter out spurious PDF labels that got captured as encodings
    return not name.startswith("Instruction F")


def _compute_encoding_variants(encodings: list[JsonDict]) -> list[JsonDict]:
    """Group encodings into instruction variants, each starting with an opword.

    Returns list of variants, each a dict with:
      - opword_index: index into encodings list
      - base_words: total 16-bit words (opword + fixed extension words)
      - extension_fields: list of extension word field names
    """
    variants: list[JsonDict] = []
    current: JsonDict | None = None

    for i, enc in enumerate(encodings):
        fields = cast(list[JsonDict], enc.get("fields", []))
        has_fixed_bits = any(str(f["name"]) in ("0", "1") for f in fields)

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
            current["base_words"] = cast(int, current["base_words"]) + 1
            cast(list[str], current["extension_fields"]).append(str(fields[0]["name"]))

    if current is not None:
        variants.append(current)

    return variants


def _classify_flow_type(inst: JsonDict) -> JsonDict:
    """Classify an instruction's control flow type from KB data.

    Uses only KB-derived fields (operation, effects, uses_label, sp_effects,
    description) — no hardcoded mnemonic names.

    Returns a dict with:
      - type: "sequential" | "branch" | "jump" | "call" | "return" | "trap"
      - conditional: bool (for branches/traps that may fall through)
    """
    operation = str(inst.get("operation", ""))
    description = str(inst.get("description", "")).lower()
    effects = cast(JsonDict, inst.get("effects", {}))
    uses_label = inst.get("uses_label", False)
    writes_pc = effects.get("writes_pc", False)
    sp_effects = cast(list[JsonDict], inst.get("sp_effects", []))
    has_push = any(e.get("action") == "decrement" for e in sp_effects)

    # Returns: pop PC from stack (RTS, RTR, RTD, RTE)
    if "(SP) → PC" in operation:
        return {"type": "return", "conditional": False}

    # Supervisor returns: RTE — operation says "If Supervisor State" but
    # description loads processor state from exception stack frame
    if "exception stack frame" in description and "loads" in description:
        return {"type": "return", "conditional": False}

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
        return {"type": "jump", "conditional": False}

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
        return {"type": "trap", "conditional": False}

    # Everything else is sequential
    return {"type": "sequential", "conditional": False}


def apply_pc_effects(kb_data: list[JsonDict]) -> int:
    """Phase 10: Extract PC effects — flow type and base instruction size."""
    count = 0
    for inst in kb_data:
        pc_effects: JsonDict = {}

        # Flow type
        flow = _classify_flow_type(inst)
        pc_effects["flow"] = flow

        # Base instruction size from encoding variants
        encodings = cast(list[JsonDict], inst.get("encodings", []))
        variants = _compute_encoding_variants(encodings)
        if variants:
            sizes = [cast(int, v["base_words"]) * 2 for v in variants]
            pc_effects["base_sizes"] = sorted(set(sizes))
            if any(v["extension_fields"] for v in variants):
                pc_effects["encoding_variants"] = [
                    {"base_bytes": cast(int, v["base_words"]) * 2,
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

def _classify_operation_type(operation: str) -> str | None:
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


def _extract_compute_formula(inst: Any) -> Any:
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

    # Skip instructions whose operation text describes SP manipulation,
    # not data computation.  These have sp_effects and flow effects
    # (call/return/trap) — their operation text contains stack
    # operations that the classifier misreads as add/subtract formulas.
    if inst.get("sp_effects"):
        flow_type = (inst.get("pc_effects", {})
                     .get("flow", {}).get("type"))
        if flow_type in ("call", "return", "trap"):
            return
        # LINK/UNLK: have sp_effects but sequential flow.
        # Their operation_type is "sub" or "add" from SP arithmetic,
        # not from a data computation.  Detect by checking if the
        # operation text only references SP/An, not Source/Destination
        # or effective address.
        if ("Source" not in operation and "Destination" not in operation
                and "< ea >" not in operation
                and "source" not in operation.lower()):
            return

    # Map operation_type to structured formula based on PDF Operation text.
    # Each formula captures the operator and operand order FROM the PDF.

    if op_type == "add_decimal":
        # PDF p115 ABCD: "Source10 + Destination10 + X → Destination"
        # BCD addition with extend — same term order as addx but decimal arithmetic
        inst["compute_formula"] = {
            "op": "add_decimal", "terms": ["source", "destination", "X"]
        }
    elif op_type == "sub_decimal":
        # PDF p271 SBCD: "Destination10 – Source10 – X → Destination"
        # BCD subtraction with extend — same term order as subx but decimal arithmetic
        inst["compute_formula"] = {
            "op": "subtract_decimal", "terms": ["destination", "source", "X"]
        }
    elif op_type == "add":
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
        # PDF p209: "Destination Sign-Extended → Destination"
        # EXT.W: byte→word (source_bits=8), EXT.L: word→long (source_bits=16),
        # EXTB.L: byte→long (source_bits=8).
        # Extract per-form source widths from PDF description text:
        # "extends a byte...to a word" → source_bits=8 for size=w
        # "extends a word...to a long word" → source_bits=16 for size=l
        # "EXTB form copies bit 7...to bits 31–8" → source_bits=8 for size=l (EXTB)
        desc = inst.get("description", "").lower()
        source_bits_by_size = {}
        if re.search(r'extends?\s+a\s+byte.*?to\s+a\s+word', desc):
            source_bits_by_size["w"] = 8
        if re.search(r'extends?\s+a\s+word.*?to\s+a\s+long', desc):
            source_bits_by_size["l"] = 16
        # EXTB: "copies bit N...to bits M–N+1" — source width = N+1
        m_extb = re.search(r'extb\s+form\s+copies\s+bit\s+(\d+)', desc)
        if m_extb:
            source_bits_by_size["extb_l"] = int(m_extb.group(1)) + 1
        inst["compute_formula"] = {
            "op": "sign_extend", "terms": ["destination"],
            "source_bits_by_size": source_bits_by_size,
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

    # Track A: If CC semantics specify decimal_carry or decimal_borrow, the
    # operation is BCD arithmetic even when the Operation text omits the "10"
    # subscript (e.g. NBCD: "0 – Destination – X" but Description says
    # "binary-coded decimal arithmetic", PDF p226). Upgrade the formula op
    # to its decimal variant so downstream computes BCD results.
    if "compute_formula" in inst:
        cc_sem = inst.get("cc_semantics", {})
        cc_rules = {v.get("rule") for v in cc_sem.values()}
        if "decimal_carry" in cc_rules or "decimal_borrow" in cc_rules:
            op = inst["compute_formula"]["op"]
            if op == "add":
                inst["compute_formula"]["op"] = "add_decimal"
            elif op == "subtract":
                inst["compute_formula"]["op"] = "subtract_decimal"


def _extract_compare_swap_effects(inst: Any) -> None:
    """Extract structured compare-swap effects from PDF description text.

    The CAS/CAS2 pages describe two conditional write behaviors:
    - CAS: compare memory against Dc, write Du to memory on success, else write
      memory back to Dc.
    - CAS2: compare two memory operands against Dc1/Dc2, write Du1/Du2 to
      memory on success, else write memory operands back to Dc1/Dc2.

    This structure is carried in the KB so executor semantics are derived from
    the PDF-derived instruction model rather than hardcoded by mnemonic.
    """
    if inst.get("operation_type") != "compare_swap":
        return

    description = str(inst.get("description", ""))
    forms = cast(list[JsonDict], inst.get("forms", []))
    if not description or not forms:
        return

    effects: list[JsonDict] = []
    has_single_desc = bool(re.search(
        r"writes the update operand \(Du\) to the effective address operand.*?"
        r"writes the effective address operand to the compare operand \(Dc\)",
        description,
        re.IGNORECASE,
    ))
    has_double_desc = bool(re.search(
        r"writes the update operands \(Du1 and Du2\) to the memory operands \(Rn1 and Rn2\).*?"
        r"writes the memory operands \(Rn1 and Rn2\) to the compare oper-\s*ands \(Dc1 and Dc2\)",
        description,
        re.IGNORECASE,
    ))

    for form in forms:
        operand_types = tuple(
            str(op["type"])
            for op in cast(list[JsonDict], form.get("operands", []))
        )
        if operand_types == ("dn", "dn", "ea"):
            assert has_single_desc, "CAS description missing single-operand compare-swap semantics"
            effects.append({
                "operand_types": list(operand_types),
                "compare_pairs": [["destination", "compare"]],
                "success_writes": [["destination", "update"]],
                "failure_writes": [["compare", "destination"]],
            })
        elif operand_types == ("dn_pair", "dn_pair", "rn_pair"):
            assert has_double_desc, "CAS2 description missing dual-operand compare-swap semantics"
            effects.append({
                "operand_types": list(operand_types),
                "compare_pairs": [["destination1", "compare1"], ["destination2", "compare2"]],
                "success_writes": [["destination1", "update1"], ["destination2", "update2"]],
                "failure_writes": [["compare1", "destination1"], ["compare2", "destination2"]],
            })

    if effects:
        inst["compare_swap_effects"] = effects


def _extract_bit_modulus(inst: Any) -> Any:
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


def _extract_size_by_ea_category(inst: Any) -> Any:
    """Extract per-EA-category size constraints from PDF description text.

    Track A: PDF p164 BTST, p130 BCHG, p133 BCLR, p159 BSET all state:
    - "When a data register is the destination, any of the 32 bits..."
    - "When a memory location is the destination, the operation is a byte operation"

    This means the instruction's listed sizes (Byte, Long) are not freely
    combinable — Long applies to register destinations, Byte to memory.
    Stores as 'size_by_ea_category' dict mapping 'register' and 'memory' to size letters.
    """
    description = inst.get("description", "")
    if not description:
        return
    desc_lower = description.lower()
    # Pattern: register destination → 32 bits, memory destination → byte
    # PDF uses both "a data register is the destination" and
    # "the destination is a data register" across different instructions
    has_reg_32 = bool(re.search(
        r'(?:(?:data\s+)?register\s+is\s+the\s+destination|destination\s+is\s+a\s+data\s+register).*?32\s+bits',
        desc_lower))
    has_mem_byte = bool(re.search(
        r'(?:memory\s+(?:location\s+)?is\s+the\s+destination|destination\s+is\s+a\s+memory\s+(?:location)?).*?byte\s+operation',
        desc_lower))
    if has_reg_32 and has_mem_byte:
        inst["size_by_ea_category"] = {"register": "l", "memory": "b"}


def _extract_source_sign_extend(inst: Any) -> Any:
    """Extract source sign-extension + 32-bit operation from PDF description text.

    Track A: PDF p181 CMPA, p117 ADDA, p283 SUBA all state:
    - "Word-length source operands are sign-extended to 32 bits for comparison/operation"
    - Opmode description: "the operation is performed on the address register using all 32 bits"

    This means the instruction always operates at 32 bits regardless of size suffix.
    The word size only affects how the source operand is read (and sign-extended).
    Stores 'source_sign_extend' and 'cc_result_bits' on the instruction.
    """
    description = inst.get("description", "")
    if not description:
        return
    desc_lower = description.lower()
    # Only match when sign-extension is for source operand comparison/operation
    # (CMPA, ADDA, SUBA), not for general register loading (MOVEM)
    forms = inst.get("forms", [])
    has_an_dest = any("an" in [o["type"] for o in f.get("operands", [])]
                      for f in forms)
    if not has_an_dest:
        return
    if re.search(
            r'source\s+operands?\s+(?:is|are)\s+sign[\s-]*extended\s+to\s+32[\s-]*bit',
            desc_lower):
        inst["source_sign_extend"] = True
        inst["cc_result_bits"] = 32
        return
    # Track A fallback: PDF p111-112 ADDA — the description says "entire destination
    # address register is used regardless of the operation size" but does not explicitly
    # say "sign-extended". However, the opmode_table for the word (.w) entry states
    # "the source operand is sign-extended to a long operand". Check opmode_table.
    opmode_table = inst.get("constraints", {}).get("opmode_table", [])
    for entry in opmode_table:
        entry_desc = entry.get("description", "").lower()
        if re.search(r'source\s+operand\s+is\s+sign[\s-]*extended', entry_desc):
            inst["source_sign_extend"] = True
            inst["cc_result_bits"] = 32
            return


def _extract_transfer_layout(inst: Any) -> Any:
    """Extract byte-striped transfer layout for MOVEP from PDF description.

    Track A: PDF pp 235-237 MOVEP description states:
    - "alternate bytes within the address space...incrementing by two"
      → stride = 2
    - "high-order byte of the data register is transferred first"
      → byte_order = "big_endian" (MSB at lowest address)
    - Byte diagrams show register bytes mapped to every other memory address

    Stores 'transfer_layout' on the instruction with stride and byte_order fields.
    """
    description = inst.get("description", "")
    if not description:
        return
    desc_lower = description.lower()
    # Match "alternate bytes" + "incrementing by two" pattern
    has_alternate = re.search(r'alternate\s+bytes', desc_lower)
    m_stride = re.search(r'increment(?:ing)?\s+by\s+(\w+)', desc_lower)
    has_high_first = re.search(r'high[\s-]*order\s+byte.*?transferred\s+first', desc_lower)
    if has_alternate and m_stride:
        stride_word = m_stride.group(1)
        stride_map = {"two": 2, "2": 2, "four": 4, "4": 4}
        stride = stride_map.get(stride_word)
        if stride is None:
            return
        byte_order = "big_endian" if has_high_first else "unknown"
        inst["transfer_layout"] = {
            "stride": stride,
            "byte_order": byte_order,
        }


def _extract_bounds_check(inst: Any) -> Any:
    """Extract structured bounds-check semantics from PDF text.

    Track A: PDF p173 CHK operation says:
      "If Dn < 0 or Dn > Source"
    And the description states:
      "Compares the value in the data register...to zero and to the upper bound"
      "If the register value is less than zero or greater than the upper bound,
       a CHK instruction exception...occurs"

    This means: trap if destination < 0 (signed) or destination > source (signed).
    The non-trapping path: 0 ≤ destination ≤ source (signed comparison).
    """
    op_type = inst.get("operation_type")
    if op_type != "bounds_check":
        return
    mnemonic = inst.get("mnemonic")
    operation = inst.get("operation", "")
    description = inst.get("description", "")
    # Match "If Dn < 0 or Dn > Source" pattern
    m = re.search(r'If\s+Dn\s*<\s*0\s+or\s+Dn\s*>\s*Source', operation)
    if m:
        inst["bounds_check"] = {
            "register_operand": "destination",
            "lower_bound": "zero",
            "upper_bound": "source",
            "comparison": "signed",
            "sign_extend_bounds_for_address_register": False,
            "trap_on_out_of_bounds": True,
        }
        inst["trap_condition"] = {
            "test": "destination < 0 || destination > source",
            "comparison": "signed",
            "lower_bound": 0,
            "upper_bound": "source",
        }
        return
    if mnemonic in {"CHK2", "CMP2"} and re.search(
            r'(?:If|Compare)\s+Rn\s*<\s*LB\s+or\s+Rn\s*>\s*UB', operation):
        comparison = None
        desc_lower = description.lower()
        if "for signed comparisons" in desc_lower and "for unsigned comparisons" not in desc_lower:
            comparison = "signed"
        elif "for unsigned comparisons" in desc_lower and "for signed comparisons" not in desc_lower:
            comparison = "unsigned"
        inst["bounds_check"] = {
            "register_operand": "rn",
            "lower_bound": "ea_lower",
            "upper_bound": "ea_upper",
            "comparison": comparison,
            "sign_extend_bounds_for_address_register": True,
            "trap_on_out_of_bounds": mnemonic == "CHK2",
        }


def _extract_cc_result_bits(inst: Any) -> Any:
    """Extract explicit CC result width from PDF CC description text.

    Track A: PDF p288 SWAP CC says "32-bit result" despite Size=(Word).
    When the CC description explicitly qualifies the result with a bit width
    different from the instruction's declared sizes, store it so the predictor
    can override the default size-derived width.
    """
    cc = inst.get("condition_codes", {})
    sizes = inst.get("sizes", [])
    # Check all CC flag descriptions for explicit "NN-bit result" qualifiers
    for flag in ("X", "N", "Z", "V", "C"):
        desc = cc.get(flag, "")
        m = re.search(r'(\d+)-bit\s+result', desc)
        if m:
            explicit_bits = int(m.group(1))
            size_bits = {"b": 8, "w": 16, "l": 32}
            declared_bits = [size_bits.get(s, 0) for s in sizes]
            if explicit_bits not in declared_bits:
                inst["cc_result_bits"] = explicit_bits
                return


def _extract_shift_fill(inst: Any) -> Any:
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


def _extract_shift_properties(inst: Any) -> Any:
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


def _extract_mul_div_data_sizes(inst: Any) -> Any:
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


def _extract_shift_variants(inst: Any) -> Any:
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


def _extract_mul_div_signed(inst: Any) -> Any:
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


def _create_combined_variants(inst: Any) -> Any:
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
                existing_map[v["mnemonic"]]["processor_020"] = bool(
                    existing_map[v["mnemonic"]].get("processor_020") or v["processor_020"]
                )
            else:
                existing.append(v)
    else:
        inst["variants"] = variants


def _extract_implicit_operand(inst: Any) -> Any:
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


def _specialize_overflow_rules(inst: Any) -> None:
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

    for _flag, spec in cc_sem.items():
        if spec.get("rule") == "overflow" and op_type in overflow_map:
            spec["rule"] = overflow_map[op_type]


def _specialize_carry_borrow_rules(inst: Any) -> None:
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
    for _flag, spec in cc_sem.items():
        if spec.get("rule") == "carry":
            spec["detection"] = "unsigned_exceeds_max"
        elif spec.get("rule") == "borrow":
            spec["detection"] = "unsigned_below_zero"


def _specialize_shift_carry_rules(inst: Any) -> None:
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
    op_type = inst.get("operation_type")

    if op_type not in ("shift", "rotate", "rotate_extend"):
        return

    for _flag, spec in cc_sem.items():
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


def _execution_cc_formula(inst: JsonDict) -> str | None:
    mnemonic = str(inst.get("mnemonic", ""))
    op_type = str(inst.get("operation_type", ""))
    flow_type = str(cast(JsonDict, cast(JsonDict, inst.get("pc_effects", {})).get("flow", {})).get("type", "sequential"))
    if flow_type in ("jump", "call", "return", "trap") or mnemonic in (
        "LEA", "MOVEA", "MOVEC", "MOVEM", "MOVEP", "MOVES",
        "MOVE from CCR", "MOVE from SR", "MOVE USP",
        "EXG", "Scc", "DBcc", "PEA", "LINK", "UNLK"
    ):
        return None
    if mnemonic == "MOVE to CCR":
        return "write_ccr"
    if mnemonic == "MOVE to SR":
        return "write_sr"
    if mnemonic == "CLR":
        return "clear_flags"
    if op_type == "bit_test":
        return "bit_test_flags"
    if op_type == "test":
        return "test_flags"
    if op_type == "shift":
        return "shift_flags"
    if op_type == "rotate":
        return "rotate_flags"
    if op_type == "rotate_extend":
        return "rotate_extend_flags"
    if op_type == "bitfield":
        return "bitfield_flags"
    if op_type == "bounds_check":
        return "bounds_check_flags"
    if op_type == "compare_swap":
        return "sub_flags"
    if op_type in ("add_decimal",):
        return "add_decimal_flags"
    if op_type in ("sub_decimal",):
        return "sub_decimal_flags"
    if op_type == "multiply":
        return "multiply_flags"
    if op_type == "divide":
        return "divide_flags"
    if mnemonic in ("MOVE", "MOVEQ") or op_type == "move":
        return "move_flags"
    if op_type in ("add", "addx"):
        return "add_flags"
    if op_type in ("sub", "subx", "negx", "compare"):
        return "sub_flags"
    return None


def _execution_result_formula(inst: JsonDict) -> str | None:
    mnemonic = str(inst.get("mnemonic", ""))
    op_type = str(inst.get("operation_type", ""))
    if mnemonic == "LEA":
        return "ea_address"
    if mnemonic in ("PEA", "LINK", "UNLK"):
        return None
    if mnemonic in ("MOVEM", "MOVEP"):
        return None
    if mnemonic in ("MOVEC", "MOVES", "MOVE from CCR", "MOVE to CCR", "MOVE from SR", "MOVE to SR", "MOVE USP"):
        return "move_source"
    if mnemonic in ("ANDI to CCR", "ANDI to SR"):
        return "bitwise_and"
    if mnemonic in ("EORI to CCR", "EORI to SR"):
        return "bitwise_xor"
    if mnemonic in ("ORI to CCR", "ORI to SR"):
        return "bitwise_or"
    if op_type == "and":
        return "bitwise_and"
    if op_type == "or":
        return "bitwise_or"
    if op_type == "xor":
        return "bitwise_xor"
    if mnemonic == "TAS":
        return "test_and_set"
    if mnemonic == "BFEXTS":
        return "bitfield_extract_signed"
    if mnemonic == "BFEXTU":
        return "bitfield_extract_unsigned"
    if mnemonic == "BFFFO":
        return "bitfield_find_first_one"
    if mnemonic == "BFINS":
        return "bitfield_insert"
    if mnemonic == "BFCHG":
        return "bitfield_change"
    if mnemonic == "BFCLR":
        return "bitfield_clear"
    if mnemonic == "BFSET":
        return "bitfield_set"
    if mnemonic == "BFTST":
        return "bitfield_test"
    if op_type == "bit_test":
        compute = cast(JsonDict, inst.get("compute_formula", {}))
        return str(compute.get("op", "bit_test")) if isinstance(compute, dict) else "bit_test"
    if mnemonic == "CLR":
        return "zero"
    if op_type == "bounds_check":
        return "bounds_check"
    if op_type == "compare_swap":
        return "sub"
    if op_type == "test":
        return "test"
    if op_type in ("shift", "rotate", "rotate_extend"):
        compute = cast(JsonDict, inst.get("compute_formula", {}))
        return str(compute.get("op", op_type)) if isinstance(compute, dict) else op_type
    if mnemonic in ("MOVE", "MOVEA", "MOVEQ") or op_type == "move":
        return "move_source"
    if op_type == "multiply":
        return "multiply"
    if op_type == "divide":
        return "divide"
    if op_type in ("add", "addx", "add_decimal"):
        return "add"
    if op_type in ("sub", "subx", "negx", "sub_decimal", "compare"):
        return "sub"
    return None


def _execution_semantic_op(inst: JsonDict) -> str | None:
    mnemonic = str(inst.get("mnemonic", ""))
    op_type = str(inst.get("operation_type", ""))
    if mnemonic == "NOP":
        return "nop"
    if mnemonic == "RESET":
        return "reset"
    if mnemonic == "RTM":
        return "rtm"
    if mnemonic == "ILLEGAL":
        return "illegal"
    if mnemonic == "BKPT":
        return "bkpt"
    if mnemonic == "STOP":
        return "stop"
    if mnemonic == "TRAPV":
        return "trapv"
    if mnemonic == "PACK":
        return "pack"
    if mnemonic == "UNPK":
        return "unpack"
    if mnemonic == "TRAP":
        return "trap"
    if mnemonic == "CINV":
        return "cache_invalidate"
    if mnemonic == "CPUSH":
        return "cache_push"
    if mnemonic in ("PFLUSH", "PFLUSH PFLUSHA"):
        return "pflush"
    if mnemonic == "PFLUSHR":
        return "pflushr"
    if mnemonic == "PLOAD":
        return "pload"
    # Parser assertion: PRM supervisor instruction pages for cpSAVE/cpRESTORE
    # describe the same state-frame memory write/read shape as FSAVE/FRESTORE
    # and PSAVE/PRESTORE, but with a generic coprocessor ID.
    if mnemonic == "cpSAVE":
        return "cpsave"
    if mnemonic == "cpRESTORE":
        return "cprestore"
    if mnemonic == "FSAVE":
        return "fsave"
    if mnemonic == "FRESTORE":
        return "frestore"
    if mnemonic == "PSAVE":
        return "psave"
    if mnemonic == "PRESTORE":
        return "prestore"
    if mnemonic == "PMOVE":
        return "pmove"
    if mnemonic == "PTEST":
        return "ptest"
    if op_type == "shift":
        return "shift"
    if op_type == "rotate":
        return "rotate"
    if op_type == "rotate_extend":
        return "rotate_extend"
    if op_type == "compare_swap":
        return "compare_swap"
    if mnemonic == "CALLM":
        return "call_module"
    if mnemonic == "LEA":
        return "compute_ea"
    if mnemonic == "MOVEM":
        return "move_multiple"
    if mnemonic == "MOVEP":
        return "move_peripheral"
    if mnemonic == "PEA":
        return "push_ea"
    if mnemonic == "LINK":
        return "link"
    if mnemonic == "UNLK":
        return "unlk"
    if mnemonic == "DBcc":
        return "dbcc"
    if mnemonic == "CLR":
        return "write_constant"
    if mnemonic == "EXG":
        return "exchange"
    if mnemonic == "MOVEA":
        return "move_address"
    if mnemonic in ("MOVEC", "MOVES", "MOVE from CCR", "MOVE to CCR", "MOVE from SR", "MOVE to SR", "MOVE USP"):
        return "move_value"
    if mnemonic in ("ANDI to CCR", "ANDI to SR"):
        return "logic_and"
    if mnemonic in ("EORI to CCR", "EORI to SR"):
        return "logic_xor"
    if mnemonic in ("ORI to CCR", "ORI to SR"):
        return "logic_or"
    if op_type == "neg":
        return "negate"
    if op_type == "not":
        return "bitwise_not"
    if mnemonic == "SWAP":
        return "swap_words"
    if op_type == "sign_extend":
        return "sign_extend"
    if op_type == "and":
        return "logic_and"
    if op_type == "or":
        return "logic_or"
    if op_type == "xor":
        return "logic_xor"
    if mnemonic in ("MOVE", "MOVEQ") or op_type == "move":
        return "move_value"
    if mnemonic == "Scc":
        return "set_condition"
    if mnemonic == "TAS":
        return "test_and_set"
    if mnemonic == "BFCHG":
        return "bitfield_change"
    if mnemonic == "BFCLR":
        return "bitfield_clear"
    if mnemonic == "BFEXTS":
        return "bitfield_extract_signed"
    if mnemonic == "BFEXTU":
        return "bitfield_extract_unsigned"
    if mnemonic == "BFFFO":
        return "bitfield_find_first_one"
    if mnemonic == "BFINS":
        return "bitfield_insert"
    if mnemonic == "BFSET":
        return "bitfield_set"
    if mnemonic == "BFTST":
        return "bitfield_test"
    if op_type == "bit_test":
        compute = cast(JsonDict, inst.get("compute_formula", {}))
        op_name = str(compute.get("op", "")) if isinstance(compute, dict) else ""
        if op_name == "bit_set":
            return "bit_set"
        if op_name == "bit_clear":
            return "bit_clear"
        if op_name == "bit_change":
            return "bit_change"
        return "bit_test"
    if op_type == "compare":
        return "compare"
    if op_type == "test":
        return "test"
    if op_type == "bounds_check":
        return "bounds_check"
    if op_type == "multiply":
        return "multiply"
    if op_type == "divide":
        return "divide"
    if op_type == "add":
        return "add"
    if op_type == "sub":
        return "sub"
    if op_type in ("addx", "add_decimal", "subx", "sub_decimal", "negx"):
        return op_type
    return None


def _exception_vector_by_name(name: str) -> int | None:
    for entry in _exception_vectors():
        if str(entry.get("name", "")) == name:
            return int(entry["vector"])
    return None


def _execution_exception(inst: JsonDict) -> JsonDict | None:
    mnemonic = str(inst.get("mnemonic", ""))
    op_type = str(inst.get("operation_type", ""))
    bounds = cast(JsonDict, inst.get("bounds_check", {}))
    if mnemonic == "BKPT":
        return {
            "trigger": "always",
            "vector_source": "fixed",
            "vector": _exception_vector_by_name("Illegal Instruction"),
            "pc_source": "current",
            "address_source": "none",
            "stacked_sr_source": "current",
        }
    if mnemonic == "TRAP":
        return {
            "trigger": "always",
            "vector_source": "trap_immediate",
            "pc_source": "next",
            "address_source": "none",
            "stacked_sr_source": "current",
        }
    if mnemonic == "ILLEGAL":
        return {
            "trigger": "always",
            "vector_source": "fixed",
            "vector": _exception_vector_by_name("Illegal Instruction"),
            "pc_source": "current",
            "address_source": "none",
            "stacked_sr_source": "current",
        }
    if mnemonic == "TRAPV":
        return {
            "trigger": "if_overflow",
            "vector_source": "fixed",
            "vector": _exception_vector_by_name("TRAPV Instruction"),
            "pc_source": "next",
            "address_source": "current_pc",
            "stacked_sr_source": "current",
        }
    if mnemonic == "STOP":
        return {
            "trigger": "if_user_mode",
            "vector_source": "fixed",
            "vector": _exception_vector_by_name("Privilege Violation"),
            "pc_source": "current",
            "address_source": "none",
            "stacked_sr_source": "current",
        }
    if mnemonic == "RTE":
        return {
            "trigger": "if_user_mode",
            "vector_source": "fixed",
            "vector": _exception_vector_by_name("Privilege Violation"),
            "pc_source": "current",
            "address_source": "none",
            "stacked_sr_source": "current",
        }
    if op_type == "bounds_check" and bool(bounds.get("trap_on_out_of_bounds")):
        return {
            "trigger": "if_bounds_fail",
            "vector_source": "fixed",
            "vector": _exception_vector_by_name("CHK Instruction"),
            "pc_source": "next",
            "address_source": "current_pc",
            "stacked_sr_source": "updated_flags" if mnemonic == "CHK2" else "current",
        }
    return None


def _execution_result_kind(inst: JsonDict) -> str:
    mnemonic = str(inst.get("mnemonic", ""))
    op_type = str(inst.get("operation_type", ""))
    if mnemonic in ("LEA", "MOVEA"):
        return "address"
    if mnemonic in ("PEA", "LINK", "UNLK"):
        return "none"
    if mnemonic in ("MOVEM", "MOVEP"):
        return "none"
    if mnemonic in ("MOVEC", "MOVES", "MOVE from CCR", "MOVE to CCR", "MOVE from SR", "MOVE to SR", "MOVE USP",
                    "ANDI to CCR", "ANDI to SR", "EORI to CCR", "EORI to SR", "ORI to CCR", "ORI to SR"):
        return "scalar"
    if mnemonic == "TAS":
        return "scalar"
    if mnemonic in ("BFEXTS", "BFEXTU", "BFFFO"):
        return "scalar"
    if op_type == "bitfield":
        return "none"
    if op_type == "bounds_check":
        return "none"
    if op_type == "compare_swap":
        return "scalar"
    if mnemonic == "CLR" or op_type in (
        "move", "add", "addx", "add_decimal", "sub", "subx", "sub_decimal", "negx",
        "and", "or", "xor", "shift", "rotate", "rotate_extend", "multiply", "divide"
    ):
        return "scalar"
    return "none"


def _execution_operation_class(inst: JsonDict) -> str | None:
    mnemonic = str(inst.get("mnemonic", ""))
    if mnemonic == "LEA":
        return "load_effective_address"
    op_class = inst.get("operation_class")
    return str(op_class) if isinstance(op_class, str) and op_class else None


def _execution_target_kind(inst: JsonDict) -> str:
    flow = cast(JsonDict, inst.get("pc_effects", {})).get("flow", {})
    flow_type = str(cast(JsonDict, flow).get("type", "sequential")) if isinstance(flow, dict) else "sequential"
    forms = cast(list[JsonDict], inst.get("forms", []))
    operands = cast(list[JsonDict], forms[0].get("operands", [])) if forms else []
    last_operand_type = str(operands[-1].get("type", "")) if operands else ""
    if flow_type in ("jump", "call") and last_operand_type != "label":
        return "ea_address"
    if flow_type in ("branch", "call"):
        return "branch_disp"
    return "none"


def _execution_has_fallthrough(inst: JsonDict) -> bool:
    flow = cast(JsonDict, inst.get("pc_effects", {})).get("flow", {})
    flow_type = str(cast(JsonDict, flow).get("type", "sequential")) if isinstance(flow, dict) else "sequential"
    return flow_type not in ("jump", "return", "trap")


def _execution_return(inst: JsonDict) -> JsonDict | None:
    mnemonic = str(inst.get("mnemonic", ""))
    if mnemonic == "RTS":
        return {"restore": "pc_only", "stack_adjust_operand_index": None}
    if mnemonic == "RTD":
        return {"restore": "pc_only", "stack_adjust_operand_index": 0}
    if mnemonic == "RTR":
        return {"restore": "ccr_then_pc", "stack_adjust_operand_index": None}
    if mnemonic == "RTE":
        return {"restore": "exception_frame", "stack_adjust_operand_index": None}
    return None


def _operand_width_for_instruction(inst: JsonDict) -> int | None:
    sizes = cast(list[str], inst.get("sizes", []))
    if sizes == ["b"]:
        return 1
    if sizes == ["w"]:
        return 2
    if sizes == ["l"]:
        return 4
    if str(inst.get("mnemonic", "")) == "STOP":
        return 2
    if str(inst.get("mnemonic", "")) == "BKPT":
        return 2
    return None


def _execution_operand_width_source(inst: JsonDict, operand_index: int, operand_type: str) -> str | None:
    del operand_type
    mnemonic = str(inst.get("mnemonic", ""))
    op_type = str(inst.get("operation_type", ""))
    flow_kind = _execution_target_kind(inst)
    op_count = len(_execution_operand_types(inst))
    if flow_kind == "ea_address" and operand_index == op_count - 1:
        return None
    if op_type in ("neg", "not"):
        return "instruction_size"
    if mnemonic == "MOVE":
        return "instruction_size"
    if mnemonic in ("MOVEA", "MOVE16", "MOVEP", "MOVES", "MOVEM"):
        return "instruction_size"
    if mnemonic == "RTM":
        return "full_register"
    if op_type in ("shift", "rotate", "rotate_extend"):
        return "instruction_size"
    if op_type in ("add", "addx", "sub", "subx", "negx", "compare", "test", "bounds_check"):
        return "instruction_size"
    if op_type in ("multiply", "divide"):
        return "instruction_size"
    if op_type in ("bit_test",):
        return "instruction_size"
    if mnemonic in ("AND", "ANDI", "EOR", "EORI", "OR", "ORI", "CLR"):
        return "instruction_size"
    if mnemonic in ("BSET", "BCLR", "BCHG", "BTST"):
        return "instruction_size"
    if mnemonic in ("ABCD", "SBCD", "NBCD"):
        return "instruction_size"
    if mnemonic == "SWAP":
        return "full_register"
    return None


def _operand_access_kind(operand_type: str, usage: str) -> str:
    if usage == "target":
        return "branch_target"
    if operand_type == "imm":
        return "immediate"
    if operand_type == "label":
        return "branch_target"
    if operand_type == "reglist":
        return "register_list_write" if usage == "write" else "register_list_read"
    if operand_type in ("ccr", "ctrl_reg", "sr", "usp"):
        return "register_write" if usage == "write" else "register_read"
    if usage == "read_modify_write":
        return "register_write" if operand_type in ("dn", "an", "rn") else "memory_write"
    if usage == "write":
        return "register_write" if operand_type in ("dn", "an", "rn") else "memory_write"
    if usage == "address":
        return "compute_address"
    if operand_type in ("dn", "an", "rn"):
        return "register_read"
    return "memory_read"


def _form_adjusted_access_kind(form_operand_type: str, access_kind: str) -> str:
    if form_operand_type == "imm":
        return "immediate"
    if form_operand_type in ("dn", "an") and access_kind == "memory_write":
        return "register_write"
    if form_operand_type in ("dn", "an") and access_kind == "memory_read":
        return "register_read"
    return access_kind


def _expected_operand_kind(form_operand_type: str) -> str:
    kind_map = {
        "dn": "dn",
        "an": "an",
        "rn": "rn",
        "ea": "ea",
        "ind": "ind",
        "postinc": "postinc",
        "predec": "predec",
        "disp": "disp",
        "index": "index",
        "absw": "absw",
        "absl": "absl",
        "pcdisp": "pcdisp",
        "pcindex": "pcindex",
        "imm": "imm",
        "label": "label",
        "ccr": "ccr",
        "ctrl_reg": "ctrl_reg",
        "sr": "sr",
        "usp": "usp",
        "reglist": "reglist",
    }
    return kind_map.get(form_operand_type, "any")


def _ea_address_shape_for_operand_type(form_operand_type: str) -> str | None:
    shape_map = {
        "ind": "indirect",
        "postinc": "postincrement",
        "predec": "predecrement",
        "disp": "displacement",
        "index": "index",
        "absw": "absolute_word",
        "absl": "absolute_long",
        "pcdisp": "pc_displacement",
        "pcindex": "pc_index",
    }
    return shape_map.get(form_operand_type)


def _ea_address_formula_for_operand_type(form_operand_type: str) -> str | None:
    formula_map = {
        "ind": "an",
        "postinc": "an",
        "predec": "an",
        "disp": "an_plus_disp",
        "index": "an_plus_disp_plus_index",
        "absw": "absolute_literal",
        "absl": "absolute_literal",
        "pcdisp": "pc_plus_disp",
        "pcindex": "pc_plus_disp_plus_index",
    }
    return formula_map.get(form_operand_type)


def _ea_register_update_for_operand_type(form_operand_type: str) -> str | None:
    if form_operand_type == "postinc":
        return "postincrement"
    if form_operand_type == "predec":
        return "predecrement"
    return "none"


def _ea_index_extension_format_for_operand_type(form_operand_type: str) -> str | None:
    if form_operand_type in ("index", "pcindex"):
        return "brief"
    return "none"


def _ea_index_register_class_for_operand_type(form_operand_type: str) -> str | None:
    if form_operand_type in ("index", "pcindex"):
        return "data_or_address"
    return "none"


def _ea_index_value_width_source_for_operand_type(form_operand_type: str) -> str | None:
    if form_operand_type in ("index", "pcindex"):
        return "extension_word"
    return "none"


def _ea_index_scale_source_for_operand_type(form_operand_type: str) -> str | None:
    if form_operand_type in ("index", "pcindex"):
        return "extension_word"
    return "none"


def _ea_index_sign_source_for_operand_type(form_operand_type: str) -> str | None:
    if form_operand_type in ("index", "pcindex"):
        return "extension_word"
    return "none"


def _ea_displacement_source_for_operand_type(form_operand_type: str) -> str | None:
    if form_operand_type in ("disp", "index", "pcdisp", "pcindex"):
        return "operand_value"
    return "none"


def _ea_base_kind_for_operand_type(form_operand_type: str) -> str | None:
    if form_operand_type in ("ind", "postinc", "predec", "disp", "index"):
        return "an"
    if form_operand_type in ("pcdisp", "pcindex"):
        return "pc"
    if form_operand_type in ("absw", "absl"):
        return "absolute"
    return None


def _ea_uses_displacement_for_operand_type(form_operand_type: str) -> bool:
    return form_operand_type in ("disp", "index", "pcdisp", "pcindex")


def _ea_uses_index_for_operand_type(form_operand_type: str) -> bool:
    return form_operand_type in ("index", "pcindex")


def _ea_pc_base_bias_bytes_for_operand_type(form_operand_type: str) -> int:
    if form_operand_type in ("pcdisp", "pcindex"):
        return 2
    return 0


def _ea_address_literal_width_bytes_for_operand_type(form_operand_type: str) -> int:
    if form_operand_type == "absw":
        return 2
    if form_operand_type == "absl":
        return 4
    return 0


def _build_form_access_overrides(inst: JsonDict, execution_operands: list[JsonDict]) -> JsonDict:
    forms = cast(list[JsonDict], inst.get("forms", []))
    overrides: JsonDict = {}
    for form_index, form in enumerate(forms):
        form_operands = cast(list[JsonDict], form.get("operands", []))
        if len(form_operands) != len(execution_operands):
            continue
        overridden_operands: list[JsonDict] = []
        changed = False
        for base_operand, form_operand in zip(execution_operands, form_operands, strict=True):
            overridden = dict(base_operand)
            access = dict(cast(JsonDict, base_operand.get("access", {})))
            form_operand_type = str(form_operand.get("type", "unknown"))
            adjusted_access_kind = _form_adjusted_access_kind(form_operand_type, str(access.get("kind", "")))
            expected_kind = _expected_operand_kind(form_operand_type)
            ea_address_formula = _ea_address_formula_for_operand_type(form_operand_type)
            ea_register_update = _ea_register_update_for_operand_type(form_operand_type)
            ea_index_extension_format = _ea_index_extension_format_for_operand_type(form_operand_type)
            ea_index_register_class = _ea_index_register_class_for_operand_type(form_operand_type)
            ea_index_value_width_source = _ea_index_value_width_source_for_operand_type(form_operand_type)
            ea_index_scale_source = _ea_index_scale_source_for_operand_type(form_operand_type)
            ea_index_sign_source = _ea_index_sign_source_for_operand_type(form_operand_type)
            ea_displacement_source = _ea_displacement_source_for_operand_type(form_operand_type)
            ea_address_shape = _ea_address_shape_for_operand_type(form_operand_type)
            ea_base_kind = _ea_base_kind_for_operand_type(form_operand_type)
            ea_uses_displacement = _ea_uses_displacement_for_operand_type(form_operand_type)
            ea_uses_index = _ea_uses_index_for_operand_type(form_operand_type)
            ea_pc_base_bias_bytes = _ea_pc_base_bias_bytes_for_operand_type(form_operand_type)
            ea_address_literal_width_bytes = _ea_address_literal_width_bytes_for_operand_type(form_operand_type)
            if form_operand_type == "ea":
                ea_address_formula = base_operand.get("ea_address_formula")
                ea_register_update = base_operand.get("ea_register_update")
                ea_index_extension_format = base_operand.get("ea_index_extension_format")
                ea_index_register_class = base_operand.get("ea_index_register_class")
                ea_index_value_width_source = base_operand.get("ea_index_value_width_source")
                ea_index_scale_source = base_operand.get("ea_index_scale_source")
                ea_index_sign_source = base_operand.get("ea_index_sign_source")
                ea_displacement_source = base_operand.get("ea_displacement_source")
                ea_address_shape = base_operand.get("ea_address_shape")
                ea_base_kind = base_operand.get("ea_base_kind")
                ea_uses_displacement = bool(base_operand.get("ea_uses_displacement", False))
                ea_uses_index = bool(base_operand.get("ea_uses_index", False))
                ea_pc_base_bias_bytes = int(base_operand.get("ea_pc_base_bias_bytes", 0))
                ea_address_literal_width_bytes = int(base_operand.get("ea_address_literal_width_bytes", 0))
            if adjusted_access_kind != str(access.get("kind", "")):
                access["kind"] = adjusted_access_kind
                overridden["access"] = access
                changed = True
            if expected_kind != str(base_operand.get("expected_kind", "any")):
                overridden["expected_kind"] = expected_kind
                changed = True
            if ea_address_formula != base_operand.get("ea_address_formula"):
                overridden["ea_address_formula"] = ea_address_formula
                changed = True
            if ea_register_update != base_operand.get("ea_register_update"):
                overridden["ea_register_update"] = ea_register_update
                changed = True
            if ea_index_extension_format != base_operand.get("ea_index_extension_format"):
                overridden["ea_index_extension_format"] = ea_index_extension_format
                changed = True
            if ea_index_register_class != base_operand.get("ea_index_register_class"):
                overridden["ea_index_register_class"] = ea_index_register_class
                changed = True
            if ea_index_value_width_source != base_operand.get("ea_index_value_width_source"):
                overridden["ea_index_value_width_source"] = ea_index_value_width_source
                changed = True
            if ea_index_scale_source != base_operand.get("ea_index_scale_source"):
                overridden["ea_index_scale_source"] = ea_index_scale_source
                changed = True
            if ea_index_sign_source != base_operand.get("ea_index_sign_source"):
                overridden["ea_index_sign_source"] = ea_index_sign_source
                changed = True
            if ea_displacement_source != base_operand.get("ea_displacement_source"):
                overridden["ea_displacement_source"] = ea_displacement_source
                changed = True
            if ea_address_shape != base_operand.get("ea_address_shape"):
                overridden["ea_address_shape"] = ea_address_shape
                changed = True
            if ea_base_kind != base_operand.get("ea_base_kind"):
                overridden["ea_base_kind"] = ea_base_kind
                changed = True
            if ea_uses_displacement != bool(base_operand.get("ea_uses_displacement", False)):
                overridden["ea_uses_displacement"] = ea_uses_displacement
                changed = True
            if ea_uses_index != bool(base_operand.get("ea_uses_index", False)):
                overridden["ea_uses_index"] = ea_uses_index
                changed = True
            if ea_pc_base_bias_bytes != int(base_operand.get("ea_pc_base_bias_bytes", 0)):
                overridden["ea_pc_base_bias_bytes"] = ea_pc_base_bias_bytes
                changed = True
            if ea_address_literal_width_bytes != int(base_operand.get("ea_address_literal_width_bytes", 0)):
                overridden["ea_address_literal_width_bytes"] = ea_address_literal_width_bytes
                changed = True
            overridden_operands.append(overridden)
        if changed:
            overrides[str(form_index)] = {"operands": overridden_operands}
    return overrides


def _merge_execution_form_overrides(execution: JsonDict, form_index: str, override: JsonDict) -> None:
    form_overrides = execution.get("form_overrides")
    base_operands = execution.get("operands")
    if not isinstance(form_overrides, dict):
        form_overrides = {}
        execution["form_overrides"] = form_overrides
    existing = form_overrides.get(form_index)
    if not isinstance(existing, dict):
        merged = dict(override)
        override_operands = override.get("operands")
        if isinstance(base_operands, list) and isinstance(override_operands, list):
            merged_operands: list[JsonDict] = []
            for operand_index, override_operand in enumerate(override_operands):
                base_operand = base_operands[operand_index] if operand_index < len(base_operands) else {}
                if isinstance(base_operand, dict) and isinstance(override_operand, dict):
                    combined_operand = dict(base_operand)
                    for key, value in override_operand.items():
                        if key == "access" and isinstance(value, dict) and isinstance(base_operand.get("access"), dict):
                            combined_access = dict(cast(JsonDict, base_operand.get("access", {})))
                            combined_access.update(cast(JsonDict, value))
                            combined_operand["access"] = combined_access
                        else:
                            combined_operand[key] = value
                    merged_operands.append(combined_operand)
                elif isinstance(override_operand, dict):
                    merged_operands.append(dict(override_operand))
            merged["operands"] = merged_operands
        form_overrides[form_index] = merged
        return
    merged = dict(existing)
    for key, value in override.items():
        if key == "operands" and isinstance(value, list):
            existing_operands = existing.get("operands")
            source_operands = existing_operands if isinstance(existing_operands, list) else base_operands
            if isinstance(source_operands, list):
                merged_operands: list[JsonDict] = []
                for operand_index, override_operand in enumerate(value):
                    source_operand = source_operands[operand_index] if operand_index < len(source_operands) else {}
                    if isinstance(source_operand, dict) and isinstance(override_operand, dict):
                        combined_operand = dict(source_operand)
                        for operand_key, operand_value in override_operand.items():
                            if operand_key == "access" and isinstance(operand_value, dict) and isinstance(source_operand.get("access"), dict):
                                combined_access = dict(cast(JsonDict, source_operand.get("access", {})))
                                combined_access.update(cast(JsonDict, operand_value))
                                combined_operand["access"] = combined_access
                            else:
                                combined_operand[operand_key] = operand_value
                        merged_operands.append(combined_operand)
                    elif isinstance(override_operand, dict):
                        merged_operands.append(dict(override_operand))
                merged[key] = merged_operands
            else:
                merged[key] = value
        else:
            merged[key] = value
    form_overrides[form_index] = merged


def _execution_operand_for_form_type(
    operand_index: int,
    operand_type: str,
    *,
    role: str,
    usage: str,
) -> JsonDict:
    access_kind = _operand_access_kind(operand_type, usage)
    result_kind = "address" if usage == "address" else (
        "control_target" if access_kind == "branch_target" else "scalar"
    )
    ea_address_formula = _ea_address_formula_for_operand_type(operand_type)
    if ea_address_formula is None and usage in ("address", "target") and operand_type == "ea":
        ea_address_formula = "decoded_ea"
    return {
        "index": operand_index,
        "role": role,
        "usage": usage,
        "expected_kind": _expected_operand_kind(operand_type),
        "ea_address_formula": ea_address_formula,
        "ea_register_update": _ea_register_update_for_operand_type(operand_type),
        "ea_index_extension_format": _ea_index_extension_format_for_operand_type(operand_type),
        "ea_index_register_class": _ea_index_register_class_for_operand_type(operand_type),
        "ea_index_value_width_source": _ea_index_value_width_source_for_operand_type(operand_type),
        "ea_index_scale_source": _ea_index_scale_source_for_operand_type(operand_type),
        "ea_index_sign_source": _ea_index_sign_source_for_operand_type(operand_type),
        "ea_displacement_source": _ea_displacement_source_for_operand_type(operand_type),
        "ea_address_shape": _ea_address_shape_for_operand_type(operand_type),
        "ea_base_kind": _ea_base_kind_for_operand_type(operand_type),
        "ea_uses_displacement": _ea_uses_displacement_for_operand_type(operand_type),
        "ea_uses_index": _ea_uses_index_for_operand_type(operand_type),
        "ea_pc_base_bias_bytes": _ea_pc_base_bias_bytes_for_operand_type(operand_type),
        "ea_address_literal_width_bytes": _ea_address_literal_width_bytes_for_operand_type(operand_type),
        "access": {
            "kind": access_kind,
            "width": None,
            "width_source": None,
            "result_kind": result_kind,
        },
    }


def _pmmu_form_execution_operands(mnemonic: str, form: JsonDict) -> list[JsonDict]:
    operand_types = [
        str(operand.get("type", "unknown"))
        for operand in cast(list[JsonDict], form.get("operands", []))
    ]
    if mnemonic == "PLOAD":
        if len(operand_types) != 2:
            return []
        return [
            _execution_operand_for_form_type(0, operand_types[0], role="source", usage="value"),
            _execution_operand_for_form_type(1, operand_types[1], role="source", usage="address"),
        ]
    if mnemonic in ("PFLUSH", "PFLUSH PFLUSHA"):
        if not operand_types:
            return []
        if len(operand_types) == 1:
            return [_execution_operand_for_form_type(0, operand_types[0], role="source", usage="address")]
        if len(operand_types) == 2:
            return [
                _execution_operand_for_form_type(0, operand_types[0], role="source", usage="value"),
                _execution_operand_for_form_type(1, operand_types[1], role="source", usage="value"),
            ]
        if len(operand_types) == 3:
            return [
                _execution_operand_for_form_type(0, operand_types[0], role="source", usage="value"),
                _execution_operand_for_form_type(1, operand_types[1], role="source", usage="value"),
                _execution_operand_for_form_type(2, operand_types[2], role="source", usage="address"),
            ]
    if mnemonic == "PTEST":
        if len(operand_types) == 1:
            return [_execution_operand_for_form_type(0, operand_types[0], role="source", usage="address")]
        if len(operand_types) == 3:
            return [
                _execution_operand_for_form_type(0, operand_types[0], role="source", usage="value"),
                _execution_operand_for_form_type(1, operand_types[1], role="source", usage="address"),
                _execution_operand_for_form_type(2, operand_types[2], role="source", usage="value"),
            ]
        if len(operand_types) == 4:
            return [
                _execution_operand_for_form_type(0, operand_types[0], role="source", usage="value"),
                _execution_operand_for_form_type(1, operand_types[1], role="source", usage="address"),
                _execution_operand_for_form_type(2, operand_types[2], role="source", usage="value"),
                _execution_operand_for_form_type(3, operand_types[3], role="dest", usage="write"),
            ]
    return []


def _replace_pmmu_execution_operands_from_forms(inst: JsonDict, execution: JsonDict) -> None:
    forms = cast(list[JsonDict], inst.get("forms", []))
    if not forms:
        return
    mnemonic = str(inst.get("mnemonic", ""))
    # Parser assertion: PRM PMMU pages define FC operands as SFC/DFC, Dn, or
    # immediate variants (PFLUSH p486, PLOAD p497, PTEST p517). After the PDF
    # parser expands those forms, execution metadata must follow the expanded
    # JSON forms instead of the earlier generic FC placeholder.
    base_operands = _pmmu_form_execution_operands(mnemonic, forms[0])
    execution["operands"] = base_operands
    form_overrides: JsonDict = {}
    for form_index, form in enumerate(forms[1:], start=1):
        operands = _pmmu_form_execution_operands(mnemonic, form)
        if operands != base_operands:
            form_overrides[str(form_index)] = {"operands": operands}
    if form_overrides:
        execution["form_overrides"] = form_overrides
    else:
        execution.pop("form_overrides", None)


def _execution_operand_usage(inst: JsonDict, operand_index: int, operand_type: str) -> str:
    mnemonic = str(inst.get("mnemonic", ""))
    op_type = str(inst.get("operation_type", ""))
    flow_kind = _execution_target_kind(inst)
    op_count = len(_execution_operand_types(inst))
    if flow_kind != "none" and operand_index == op_count - 1:
        return "target"
    if mnemonic == "LEA" and operand_index == 0:
        return "address"
    if mnemonic == "PEA" and operand_index == 0:
        return "address"
    if mnemonic in ("LINK", "UNLK"):
        return "value"
    if mnemonic == "MOVEM":
        return "value" if operand_type == "reglist" else ("write" if operand_index == 1 else "value")
    if mnemonic == "TAS":
        return "read_modify_write"
    if op_type == "bitfield":
        if mnemonic in ("BFCHG", "BFCLR", "BFSET") and operand_index == 0:
            return "read_modify_write"
        if mnemonic == "BFINS":
            return "value" if operand_index == 0 else "read_modify_write"
        if mnemonic in ("BFEXTS", "BFEXTU", "BFFFO"):
            return "value" if operand_index == 0 else "write"
        return "value"
    if op_type in ("neg", "negx", "not", "sign_extend", "swap"):
        return "read_modify_write"
    if mnemonic == "NBCD":
        return "read_modify_write"
    if op_type == "bit_test":
        if operand_index == 0:
            return "value"
        compute = cast(JsonDict, inst.get("compute_formula", {}))
        op_name = str(compute.get("op", "")) if isinstance(compute, dict) else ""
        return "value" if op_name == "bit_test" else "read_modify_write"
    if op_type in ("compare", "test", "bounds_check", "multiply", "divide"):
        return "value"
    if mnemonic in ("CLR", "Scc"):
        return "write"
    if operand_index == op_count - 1 and op_count > 1:
        return "write"
    if operand_type == "an" and mnemonic == "MOVEA" and operand_index == 1:
        return "write"
    return "value"


def _execution_operand_role(inst: JsonDict, operand_index: int, operand_count: int, usage: str) -> str:
    mnemonic = str(inst.get("mnemonic", ""))
    if _execution_target_kind(inst) != "none" and operand_index == operand_count - 1:
        return "target"
    if mnemonic in ("PEA", "LINK", "UNLK"):
        return "source"
    if usage == "write":
        return "dest"
    if operand_count == 2 and operand_index == 0:
        return "source"
    if operand_count == 2 and operand_index == 1:
        return "dest"
    return "source"


def _execution_operand_types(inst: JsonDict) -> list[str]:
    forms = cast(list[JsonDict], inst.get("forms", []))
    if forms:
        operands = cast(list[JsonDict], forms[0].get("operands", []))
        return [str(operand.get("type", "unknown")) for operand in operands]
    mnemonic = str(inst.get("mnemonic", ""))
    if mnemonic in {"BTST", "BSET", "BCLR", "BCHG"}:
        return ["dn", "ea"]
    if mnemonic in {"Bcc", "BRA", "BSR"}:
        return ["label"]
    if mnemonic == "DBcc":
        return ["dn", "label"]
    if mnemonic == "Scc":
        return ["ea"]
    if mnemonic == "TRAPcc":
        return []
    if mnemonic in {"ABCD", "SBCD", "ADDX", "SUBX"}:
        return ["dn", "dn"]
    if mnemonic in {"NEGX", "NBCD"}:
        return ["ea"]
    if mnemonic in {"BFCHG", "BFCLR", "BFSET", "BFTST"}:
        return ["ea"]
    if mnemonic in {"BFEXTS", "BFEXTU", "BFFFO"}:
        return ["ea", "dn"]
    if mnemonic == "BFINS":
        return ["dn", "ea"]
    if mnemonic in {"CINV", "CPUSH"}:
        return ["ctrl_reg", "ind"]
    if mnemonic == "PFLUSHR":
        return ["ea"]
    if mnemonic in {"FSAVE", "FRESTORE", "PSAVE", "PRESTORE", "cpSAVE", "cpRESTORE"}:
        return ["ea"]
    if mnemonic == "CALLM":
        return ["imm", "ea"]
    if mnemonic == "TRAP":
        return ["imm"]
    if mnemonic == "CHK":
        return ["ea", "dn"]
    if mnemonic in {"CHK2", "CMP2"}:
        return ["ea", "rn"]
    if mnemonic in {"MULS", "MULU", "DIVS, DIVSL", "DIVU, DIVUL"}:
        return ["ea", "dn"]
    if mnemonic in {"BKPT", "STOP"}:
        return ["imm"]
    return []


def _build_execution_metadata(inst: JsonDict) -> JsonDict | None:
    mnemonic = str(inst.get("mnemonic", ""))
    operand_types = _execution_operand_types(inst)
    flow = cast(JsonDict, cast(JsonDict, inst.get("pc_effects", {})).get("flow", {}))
    flow_type = str(flow.get("type", "sequential"))
    if flow_type == "trap" and mnemonic not in {"ILLEGAL", "BKPT", "STOP", "TRAP", "TRAPV", "TRAPcc"}:
        return None
    if not operand_types and flow_type != "return" and mnemonic not in {"RTS", "NOP", "RESET", "ILLEGAL", "TRAPV", "TRAPcc", "PFLUSH", "PFLUSH PFLUSHA"}:
        return None
    semantic_op = _execution_semantic_op(inst)
    target_kind = _execution_target_kind(inst)
    if semantic_op is None and target_kind == "none" and flow_type == "sequential":
        return None
    width = _operand_width_for_instruction(inst)
    execution_operands: list[JsonDict] = []
    for operand_index, operand_type in enumerate(operand_types):
        usage = _execution_operand_usage(inst, operand_index, operand_type)
        access_kind = _operand_access_kind(operand_type, usage)
        width_source = _execution_operand_width_source(inst, operand_index, operand_type)
        result_kind = "control_target" if access_kind == "branch_target" else (
            "address" if usage == "address" or (usage == "write" and mnemonic in ("LEA", "MOVEA")) or mnemonic == "MOVEA" else "scalar"
        )
        ea_address_formula = _ea_address_formula_for_operand_type(operand_type)
        if ea_address_formula is None and usage in ("address", "target") and operand_type == "ea":
            ea_address_formula = "decoded_ea"
        execution_operands.append({
            "index": operand_index,
            "role": _execution_operand_role(inst, operand_index, len(operand_types), usage),
            "usage": usage,
            "expected_kind": _expected_operand_kind(operand_type),
            "ea_address_formula": ea_address_formula,
            "ea_register_update": _ea_register_update_for_operand_type(operand_type),
            "ea_index_extension_format": _ea_index_extension_format_for_operand_type(operand_type),
            "ea_index_register_class": _ea_index_register_class_for_operand_type(operand_type),
            "ea_index_value_width_source": _ea_index_value_width_source_for_operand_type(operand_type),
            "ea_index_scale_source": _ea_index_scale_source_for_operand_type(operand_type),
            "ea_index_sign_source": _ea_index_sign_source_for_operand_type(operand_type),
            "ea_displacement_source": _ea_displacement_source_for_operand_type(operand_type),
            "ea_address_shape": _ea_address_shape_for_operand_type(operand_type),
            "ea_base_kind": _ea_base_kind_for_operand_type(operand_type),
            "ea_uses_displacement": _ea_uses_displacement_for_operand_type(operand_type),
            "ea_uses_index": _ea_uses_index_for_operand_type(operand_type),
            "ea_pc_base_bias_bytes": _ea_pc_base_bias_bytes_for_operand_type(operand_type),
            "ea_address_literal_width_bytes": _ea_address_literal_width_bytes_for_operand_type(operand_type),
            "access": {
                "kind": access_kind,
                "width": None if width_source is not None else width,
                "width_source": width_source,
                "result_kind": result_kind,
            },
        })
    ccr_formula = _execution_cc_formula(inst)
    execution: JsonDict = {
        "semantic_op": semantic_op,
        "operation_class": _execution_operation_class(inst),
        "flow": {
            "kind": flow_type,
            "conditional": bool(flow.get("conditional", False)),
            "has_fallthrough": _execution_has_fallthrough(inst),
            "target_kind": target_kind,
        },
        "result": {
            "kind": _execution_result_kind(inst),
            "formula": _execution_result_formula(inst),
        },
        "ccr": {
            "writes": ccr_formula is not None,
            "formula": ccr_formula,
        },
        "stack": {
            "effect_id": mnemonic if inst.get("sp_effects") else None,
            "effects": inst.get("sp_effects", []),
        },
        "implicit_reads": [],
        "implicit_writes": [],
        "operands": execution_operands,
    }
    exception = _execution_exception(inst)
    if exception is not None:
        execution["exception"] = exception
    return_effect = _execution_return(inst)
    if return_effect is not None:
        execution["return"] = return_effect
    form_access_overrides = _build_form_access_overrides(inst, execution_operands)
    if form_access_overrides:
        execution["form_overrides"] = form_access_overrides
    if mnemonic in ("MOVE from CCR", "MOVE from SR", "MOVE USP"):
        execution["operands"] = [
            {
                "index": 0,
                "role": "source",
                "usage": "value",
                "expected_kind": "ccr" if mnemonic == "MOVE from CCR" else ("sr" if mnemonic == "MOVE from SR" else "usp"),
                "ea_address_shape": None,
                "access": {
                    "kind": "register_read",
                    "width": width,
                    "width_source": None,
                    "result_kind": "scalar",
                },
            },
            {
                "index": 1,
                "role": "dest",
                "usage": "write",
                "expected_kind": "ea" if mnemonic != "MOVE USP" else "an",
                "ea_address_shape": None,
                "access": {
                    "kind": "memory_write" if mnemonic != "MOVE USP" else "register_write",
                    "width": width,
                    "width_source": None,
                    "result_kind": "scalar",
                },
            },
        ]
    if mnemonic in ("PACK", "UNPK"):
        execution["ccr"] = {
            "writes": False,
            "formula": None,
        }
        execution["operands"] = [
            {
                "index": 0,
                "role": "source",
                "usage": "value",
                "expected_kind": "predec",
                "ea_address_formula": "an",
                "ea_register_update": "predecrement",
                "ea_index_extension_format": "none",
                "ea_index_register_class": "none",
                "ea_index_value_width_source": "none",
                "ea_index_scale_source": "none",
                "ea_index_sign_source": "none",
                "ea_displacement_source": "none",
                "ea_address_shape": "predecrement",
                "ea_base_kind": "an",
                "ea_uses_displacement": False,
                "ea_uses_index": False,
                "ea_pc_base_bias_bytes": 0,
                "ea_address_literal_width_bytes": 0,
                "access": {
                    "kind": "memory_read",
                    "width": 2 if mnemonic == "PACK" else 1,
                    "width_source": None,
                    "result_kind": "scalar",
                },
            },
            {
                "index": 1,
                "role": "dest",
                "usage": "write",
                "expected_kind": "predec",
                "ea_address_formula": "an",
                "ea_register_update": "predecrement",
                "ea_index_extension_format": "none",
                "ea_index_register_class": "none",
                "ea_index_value_width_source": "none",
                "ea_index_scale_source": "none",
                "ea_index_sign_source": "none",
                "ea_displacement_source": "none",
                "ea_address_shape": "predecrement",
                "ea_base_kind": "an",
                "ea_uses_displacement": False,
                "ea_uses_index": False,
                "ea_pc_base_bias_bytes": 0,
                "ea_address_literal_width_bytes": 0,
                "access": {
                    "kind": "memory_write",
                    "width": 1 if mnemonic == "PACK" else 2,
                    "width_source": None,
                    "result_kind": "scalar",
                },
            },
            {
                "index": 2,
                "role": "aux",
                "usage": "value",
                "expected_kind": "imm",
                "ea_address_shape": None,
                "access": {
                    "kind": "immediate",
                    "width": 2,
                    "width_source": None,
                    "result_kind": "scalar",
                },
            },
        ]
        _merge_execution_form_overrides(execution, "1", {
            "operands": [
                {
                    "index": 0,
                    "role": "source",
                    "usage": "value",
                    "expected_kind": "dn",
                    "ea_address_formula": None,
                    "ea_register_update": "none",
                    "ea_index_extension_format": "none",
                    "ea_index_register_class": "none",
                    "ea_index_value_width_source": "none",
                    "ea_index_scale_source": "none",
                    "ea_index_sign_source": "none",
                    "ea_displacement_source": "none",
                    "ea_address_shape": None,
                    "ea_base_kind": None,
                    "ea_uses_displacement": False,
                    "ea_uses_index": False,
                    "ea_pc_base_bias_bytes": 0,
                    "ea_address_literal_width_bytes": 0,
                    "access": {
                        "kind": "register_read",
                        "width": 2 if mnemonic == "PACK" else 1,
                        "width_source": None,
                        "result_kind": "scalar",
                    },
                },
                {
                    "index": 1,
                    "role": "dest",
                    "usage": "write",
                    "expected_kind": "dn",
                    "ea_address_formula": None,
                    "ea_register_update": "none",
                    "ea_index_extension_format": "none",
                    "ea_index_register_class": "none",
                    "ea_index_value_width_source": "none",
                    "ea_index_scale_source": "none",
                    "ea_index_sign_source": "none",
                    "ea_displacement_source": "none",
                    "ea_address_shape": None,
                    "ea_base_kind": None,
                    "ea_uses_displacement": False,
                    "ea_uses_index": False,
                    "ea_pc_base_bias_bytes": 0,
                    "ea_address_literal_width_bytes": 0,
                    "access": {
                        "kind": "register_write",
                        "width": 1 if mnemonic == "PACK" else 2,
                        "width_source": None,
                        "result_kind": "scalar",
                    },
                },
                {
                    "index": 2,
                    "role": "aux",
                    "usage": "value",
                    "expected_kind": "imm",
                    "ea_address_formula": None,
                    "ea_register_update": "none",
                    "ea_index_extension_format": "none",
                    "ea_index_register_class": "none",
                    "ea_index_value_width_source": "none",
                    "ea_index_scale_source": "none",
                    "ea_index_sign_source": "none",
                    "ea_displacement_source": "none",
                    "ea_address_shape": None,
                    "ea_base_kind": None,
                    "ea_uses_displacement": False,
                    "ea_uses_index": False,
                    "ea_pc_base_bias_bytes": 0,
                    "ea_address_literal_width_bytes": 0,
                    "access": {
                        "kind": "immediate",
                        "width": 2,
                        "width_source": None,
                        "result_kind": "scalar",
                    },
                },
            ],
        })
    if mnemonic in ("MOVE to CCR", "MOVE to SR"):
        execution["operands"] = [
            {
                "index": 0,
                "role": "source",
                "usage": "value",
                "expected_kind": "ea",
                "ea_address_shape": None,
                "access": {
                    "kind": "memory_read",
                    "width": width,
                    "width_source": None,
                    "result_kind": "scalar",
                },
            },
            {
                "index": 1,
                "role": "dest",
                "usage": "write",
                "expected_kind": "ccr" if mnemonic == "MOVE to CCR" else "sr",
                "ea_address_shape": None,
                "access": {
                    "kind": "register_write",
                    "width": width,
                    "width_source": None,
                    "result_kind": "scalar",
                },
            },
        ]
    if mnemonic in ("ANDI to CCR", "ANDI to SR", "EORI to CCR", "EORI to SR", "ORI to CCR", "ORI to SR"):
        execution["operands"] = [
            {
                "index": 0,
                "role": "source",
                "usage": "value",
                "expected_kind": "imm",
                "ea_address_shape": None,
                "access": {
                    "kind": "immediate",
                    "width": width,
                    "width_source": None,
                    "result_kind": "scalar",
                },
            },
            {
                "index": 1,
                "role": "dest",
                "usage": "write",
                "expected_kind": "ccr" if "CCR" in mnemonic else "sr",
                "ea_address_shape": None,
                "access": {
                    "kind": "register_write",
                    "width": width,
                    "width_source": None,
                    "result_kind": "scalar",
                },
            },
        ]
    if mnemonic == "MOVEM":
        execution["operands"] = [
            {
                "index": 0,
                "role": "source",
                "usage": "value",
                "access": {
                    "kind": "register_list_read",
                    "width": width,
                    "width_source": "instruction_size",
                    "result_kind": "scalar",
                },
            },
            {
                "index": 1,
                "role": "dest",
                "usage": "write",
                "access": {
                    "kind": "memory_write",
                    "width": width,
                    "width_source": "instruction_size",
                    "result_kind": "scalar",
                },
            },
        ]
        execution["multi_transfer"] = {
            "reglist_operand_index": 0,
            "address_operand_index": 1,
            "direction": "register_to_memory",
            "address_update": "predecrement_if_predec",
            "reg_iteration": "ascending_mask_bits",
            "source_snapshot": "before_write",
        }
        _merge_execution_form_overrides(execution, "1", {
            "operands": [
                {
                    "index": 0,
                    "role": "source",
                    "usage": "value",
                    "access": {
                        "kind": "memory_read",
                        "width": width,
                        "width_source": "instruction_size",
                        "result_kind": "scalar",
                    },
                },
                {
                    "index": 1,
                    "role": "dest",
                    "usage": "write",
                    "access": {
                        "kind": "register_list_write",
                        "width": width,
                        "width_source": "instruction_size",
                        "result_kind": "scalar",
                    },
                },
            ],
            "multi_transfer": {
                "reglist_operand_index": 1,
                "address_operand_index": 0,
                "direction": "memory_to_register",
                "address_update": "postincrement_if_postinc",
                "reg_iteration": "ascending_mask_bits",
                "source_snapshot": "none",
            },
        })
    if mnemonic == "MOVEP":
        transfer_layout = cast(JsonDict, inst.get("transfer_layout", {}))
        execution["operands"] = [
            {
                "index": 0,
                "role": "source",
                "usage": "value",
                "expected_kind": "dn",
                "access": {
                    "kind": "register_read",
                    "width": width,
                    "width_source": "instruction_size",
                    "result_kind": "scalar",
                },
            },
            {
                "index": 1,
                "role": "dest",
                "usage": "write",
                "expected_kind": "ea",
                "access": {
                    "kind": "memory_write",
                    "width": width,
                    "width_source": "instruction_size",
                    "result_kind": "scalar",
                },
            },
        ]
        execution["striped_transfer"] = {
            "reg_operand_index": 0,
            "address_operand_index": 1,
            "direction": "register_to_memory",
            "stride": int(transfer_layout.get("stride", 2)),
            "byte_order": str(transfer_layout.get("byte_order", "big_endian")),
        }
        _merge_execution_form_overrides(execution, "1", {
            "operands": [
                {
                    "index": 0,
                    "role": "source",
                    "usage": "value",
                    "access": {
                        "kind": "memory_read",
                        "width": width,
                        "width_source": "instruction_size",
                        "result_kind": "scalar",
                    },
                },
                {
                    "index": 1,
                    "role": "dest",
                    "usage": "write",
                    "access": {
                        "kind": "register_write",
                        "width": width,
                        "width_source": "instruction_size",
                        "result_kind": "scalar",
                    },
                },
            ],
            "striped_transfer": {
                "reg_operand_index": 1,
                "address_operand_index": 0,
                "direction": "memory_to_register",
                "stride": int(transfer_layout.get("stride", 2)),
                "byte_order": str(transfer_layout.get("byte_order", "big_endian")),
            },
        })
    if mnemonic == "MOVES":
        _merge_execution_form_overrides(execution, "1", {
            "operands": [
                {
                    "index": 0,
                    "role": "source",
                    "usage": "value",
                    "access": {
                        "kind": "memory_read",
                        "width": width,
                        "width_source": "instruction_size",
                        "result_kind": "scalar",
                    },
                },
                {
                    "index": 1,
                    "role": "dest",
                    "usage": "write",
                    "access": {
                        "kind": "register_write",
                        "width": width,
                        "width_source": "instruction_size",
                        "result_kind": "scalar",
                    },
                },
            ],
        })
    if mnemonic == "MOVEC":
        _merge_execution_form_overrides(execution, "1", {
            "operands": [
                {
                    "index": 0,
                    "role": "source",
                    "usage": "value",
                    "access": {
                        "kind": "register_read",
                        "width": width,
                        "width_source": "instruction_size",
                        "result_kind": "scalar",
                    },
                },
                {
                    "index": 1,
                    "role": "dest",
                    "usage": "write",
                    "access": {
                        "kind": "register_write",
                        "width": width,
                        "width_source": "instruction_size",
                        "result_kind": "scalar",
                    },
                },
            ],
        })
    if mnemonic == "TRAPcc":
        _merge_execution_form_overrides(execution, "1", {
            "operands": [
                {
                    "index": 0,
                    "role": "source",
                    "usage": "value",
                    "expected_kind": "imm",
                    "ea_address_formula": None,
                    "ea_register_update": "none",
                    "ea_index_extension_format": "none",
                    "ea_index_register_class": "none",
                    "ea_index_value_width_source": "none",
                    "ea_index_scale_source": "none",
                    "ea_index_sign_source": "none",
                    "ea_displacement_source": "none",
                    "ea_address_shape": None,
                    "ea_base_kind": None,
                    "ea_uses_displacement": False,
                    "ea_uses_index": False,
                    "ea_pc_base_bias_bytes": 0,
                    "ea_address_literal_width_bytes": 0,
                    "access": {
                        "kind": "immediate",
                        "width": 2,
                        "width_source": None,
                        "result_kind": "scalar",
                    },
                },
            ],
        })
        _merge_execution_form_overrides(execution, "2", {
            "operands": [
                {
                    "index": 0,
                    "role": "source",
                    "usage": "value",
                    "expected_kind": "imm",
                    "ea_address_formula": None,
                    "ea_register_update": "none",
                    "ea_index_extension_format": "none",
                    "ea_index_register_class": "none",
                    "ea_index_value_width_source": "none",
                    "ea_index_scale_source": "none",
                    "ea_index_sign_source": "none",
                    "ea_displacement_source": "none",
                    "ea_address_shape": None,
                    "ea_base_kind": None,
                    "ea_uses_displacement": False,
                    "ea_uses_index": False,
                    "ea_pc_base_bias_bytes": 0,
                    "ea_address_literal_width_bytes": 0,
                    "access": {
                        "kind": "immediate",
                        "width": 4,
                        "width_source": None,
                        "result_kind": "scalar",
                    },
                },
            ],
        })
    if mnemonic == "CAS CAS2":
        execution["operands"] = [
            {
                "index": 0,
                "role": "source",
                "usage": "value",
                "expected_kind": "dn",
                "ea_address_shape": None,
                "access": {
                    "kind": "register_read",
                    "width": None,
                    "width_source": "instruction_size",
                    "result_kind": "scalar",
                },
            },
            {
                "index": 1,
                "role": "source",
                "usage": "value",
                "expected_kind": "dn",
                "ea_address_shape": None,
                "access": {
                    "kind": "register_read",
                    "width": None,
                    "width_source": "instruction_size",
                    "result_kind": "scalar",
                },
            },
            {
                "index": 2,
                "role": "dest",
                "usage": "read_modify_write",
                "expected_kind": "ea",
                "access": {
                    "kind": "memory_write",
                    "width": None,
                    "width_source": "instruction_size",
                    "result_kind": "scalar",
                },
            },
        ]
        _merge_execution_form_overrides(execution, "1", {
            "operands": [
                {
                    "index": 0,
                    "role": "source",
                    "usage": "value",
                    "expected_kind": "any",
                    "ea_address_shape": None,
                    "access": {
                        "kind": "register_read",
                        "width": None,
                        "width_source": "instruction_size",
                        "result_kind": "scalar",
                    },
                },
                {
                    "index": 1,
                    "role": "source",
                    "usage": "value",
                    "expected_kind": "any",
                    "ea_address_shape": None,
                    "access": {
                        "kind": "register_read",
                        "width": None,
                        "width_source": "instruction_size",
                        "result_kind": "scalar",
                    },
                },
                {
                    "index": 2,
                    "role": "dest",
                    "usage": "read_modify_write",
                    "expected_kind": "rn",
                    "ea_address_shape": None,
                    "access": {
                        "kind": "register_write",
                        "width": None,
                        "width_source": "instruction_size",
                        "result_kind": "scalar",
                    },
                },
            ],
        })
    if mnemonic == "CALLM":
        execution["operands"] = [
            {
                "index": 0,
                "role": "source",
                "usage": "value",
                "expected_kind": "imm",
                "ea_address_shape": None,
                "access": {
                    "kind": "immediate",
                    "width": 1,
                    "width_source": None,
                    "result_kind": "scalar",
                },
            },
            {
                "index": 1,
                "role": "target",
                "usage": "address",
                "expected_kind": "ea",
                "access": {
                    "kind": "compute_address",
                    "width": None,
                    "width_source": None,
                    "result_kind": "address",
                },
            },
        ]
        execution["flow"]["kind"] = "call"
        execution["flow"]["has_fallthrough"] = False
        execution["flow"]["target_kind"] = "ea_address"
    if mnemonic in ("CINV", "CPUSH"):
        execution["operands"] = [
            {
                "index": 0,
                "role": "source",
                "usage": "value",
                "expected_kind": "ctrl_reg",
                "ea_address_shape": None,
                "access": {
                    "kind": "register_read",
                    "width": None,
                    "width_source": None,
                    "result_kind": "scalar",
                },
            },
            {
                "index": 1,
                "role": "source",
                "usage": "address",
                "expected_kind": "ind",
                "access": {
                    "kind": "compute_address",
                    "width": None,
                    "width_source": None,
                    "result_kind": "address",
                },
            },
        ]
        _merge_execution_form_overrides(execution, "2", {
            "operands": [
                {
                    "index": 0,
                    "role": "source",
                    "usage": "value",
                    "expected_kind": "ctrl_reg",
                    "ea_address_shape": None,
                    "access": {
                        "kind": "register_read",
                        "width": None,
                        "width_source": None,
                        "result_kind": "scalar",
                    },
                },
            ],
        })
    if mnemonic in ("PFLUSH", "PFLUSH PFLUSHA"):
        execution["operands"] = []
        _merge_execution_form_overrides(execution, "1", {
            "operands": [
                {
                    "index": 0,
                    "role": "source",
                    "usage": "value",
                    "expected_kind": "ctrl_reg",
                    "ea_address_shape": None,
                    "access": {
                        "kind": "register_read",
                        "width": None,
                        "width_source": None,
                        "result_kind": "scalar",
                    },
                },
                {
                    "index": 1,
                    "role": "source",
                    "usage": "value",
                    "expected_kind": "imm",
                    "ea_address_shape": None,
                    "access": {
                        "kind": "immediate",
                        "width": None,
                        "width_source": None,
                        "result_kind": "scalar",
                    },
                },
            ],
        })
        _merge_execution_form_overrides(execution, "2", {
            "operands": [
                {
                    "index": 0,
                    "role": "source",
                    "usage": "value",
                    "expected_kind": "ctrl_reg",
                    "ea_address_shape": None,
                    "access": {
                        "kind": "register_read",
                        "width": None,
                        "width_source": None,
                        "result_kind": "scalar",
                    },
                },
                {
                    "index": 1,
                    "role": "source",
                    "usage": "value",
                    "expected_kind": "imm",
                    "ea_address_shape": None,
                    "access": {
                        "kind": "immediate",
                        "width": None,
                        "width_source": None,
                        "result_kind": "scalar",
                    },
                },
                {
                    "index": 2,
                    "role": "source",
                    "usage": "address",
                    "expected_kind": "ea",
                    "access": {
                        "kind": "compute_address",
                        "width": None,
                        "width_source": None,
                        "result_kind": "address",
                    },
                },
            ],
        })
        _merge_execution_form_overrides(execution, "4", {
            "operands": [
                {
                    "index": 0,
                    "role": "source",
                    "usage": "address",
                    "expected_kind": "ind",
                    "access": {
                        "kind": "compute_address",
                        "width": None,
                        "width_source": None,
                        "result_kind": "address",
                    },
                },
            ],
        })
        _merge_execution_form_overrides(execution, "6", {
            "operands": [
                {
                    "index": 0,
                    "role": "source",
                    "usage": "address",
                    "expected_kind": "ind",
                    "access": {
                        "kind": "compute_address",
                        "width": None,
                        "width_source": None,
                        "result_kind": "address",
                    },
                },
            ],
        })
    if mnemonic == "PFLUSHR":
        execution["operands"] = [
            {
                "index": 0,
                "role": "source",
                "usage": "address",
                "expected_kind": "ea",
                "access": {
                    "kind": "compute_address",
                    "width": None,
                    "width_source": None,
                    "result_kind": "address",
                },
            },
        ]
    if mnemonic in ("FSAVE", "PSAVE", "cpSAVE"):
        execution["operands"] = [
            {
                "index": 0,
                "role": "dest",
                "usage": "write",
                "expected_kind": "ea",
                "access": {
                    "kind": "memory_write",
                    "width": None,
                    "width_source": None,
                    "result_kind": "scalar",
                },
            },
        ]
    if mnemonic in ("FRESTORE", "PRESTORE", "cpRESTORE"):
        execution["operands"] = [
            {
                "index": 0,
                "role": "source",
                "usage": "value",
                "expected_kind": "ea",
                "access": {
                    "kind": "memory_read",
                    "width": None,
                    "width_source": None,
                    "result_kind": "scalar",
                },
            },
        ]
    if mnemonic == "PLOAD":
        execution["operands"] = [
            {
                "index": 0,
                "role": "source",
                "usage": "value",
                "expected_kind": "ctrl_reg",
                "ea_address_shape": None,
                "access": {
                    "kind": "register_read",
                    "width": None,
                    "width_source": None,
                    "result_kind": "scalar",
                },
            },
            {
                "index": 1,
                "role": "source",
                "usage": "address",
                "expected_kind": "ea",
                "access": {
                    "kind": "compute_address",
                    "width": None,
                    "width_source": None,
                    "result_kind": "address",
                },
            },
        ]
    if mnemonic == "PMOVE":
        execution["operands"] = [
            {
                "index": 0,
                "role": "source",
                "usage": "value",
                "expected_kind": "ctrl_reg",
                "ea_address_shape": None,
                "access": {
                    "kind": "register_read",
                    "width": None,
                    "width_source": None,
                    "result_kind": "scalar",
                },
            },
            {
                "index": 1,
                "role": "dest",
                "usage": "write",
                "expected_kind": "ea",
                "access": {
                    "kind": "memory_write",
                    "width": None,
                    "width_source": None,
                    "result_kind": "scalar",
                },
            },
        ]
    if mnemonic == "PTEST":
        execution["operands"] = [
            {
                "index": 0,
                "role": "source",
                "usage": "value",
                "expected_kind": "ctrl_reg",
                "ea_address_shape": None,
                "access": {
                    "kind": "register_read",
                    "width": None,
                    "width_source": None,
                    "result_kind": "scalar",
                },
            },
            {
                "index": 1,
                "role": "source",
                "usage": "address",
                "expected_kind": "ea",
                "access": {
                    "kind": "compute_address",
                    "width": None,
                    "width_source": None,
                    "result_kind": "address",
                },
            },
            {
                "index": 2,
                "role": "source",
                "usage": "value",
                "expected_kind": "imm",
                "ea_address_shape": None,
                "access": {
                    "kind": "immediate",
                    "width": None,
                    "width_source": None,
                    "result_kind": "scalar",
                },
            },
        ]
        _merge_execution_form_overrides(execution, "2", {
            "operands": [
                {
                    "index": 0,
                    "role": "source",
                    "usage": "value",
                    "expected_kind": "ctrl_reg",
                    "ea_address_shape": None,
                    "access": {
                        "kind": "register_read",
                        "width": None,
                        "width_source": None,
                        "result_kind": "scalar",
                    },
                },
                {
                    "index": 1,
                    "role": "source",
                    "usage": "address",
                    "expected_kind": "ea",
                    "access": {
                        "kind": "compute_address",
                        "width": None,
                        "width_source": None,
                        "result_kind": "address",
                    },
                },
                {
                    "index": 2,
                    "role": "source",
                    "usage": "value",
                    "expected_kind": "imm",
                    "ea_address_shape": None,
                    "access": {
                        "kind": "immediate",
                        "width": None,
                        "width_source": None,
                        "result_kind": "scalar",
                    },
                },
                {
                    "index": 3,
                    "role": "dest",
                    "usage": "write",
                    "expected_kind": "an",
                    "ea_address_shape": None,
                    "access": {
                        "kind": "register_write",
                        "width": None,
                        "width_source": None,
                        "result_kind": "scalar",
                    },
                },
            ],
        })
        _merge_execution_form_overrides(execution, "3", {
            "operands": [
                {
                    "index": 0,
                    "role": "source",
                    "usage": "value",
                    "expected_kind": "ctrl_reg",
                    "ea_address_shape": None,
                    "access": {
                        "kind": "register_read",
                        "width": None,
                        "width_source": None,
                        "result_kind": "scalar",
                    },
                },
                {
                    "index": 1,
                    "role": "source",
                    "usage": "address",
                    "expected_kind": "ea",
                    "access": {
                        "kind": "compute_address",
                        "width": None,
                        "width_source": None,
                        "result_kind": "address",
                    },
                },
                {
                    "index": 2,
                    "role": "source",
                    "usage": "value",
                    "expected_kind": "imm",
                    "ea_address_shape": None,
                    "access": {
                        "kind": "immediate",
                        "width": None,
                        "width_source": None,
                        "result_kind": "scalar",
                    },
                },
                {
                    "index": 3,
                    "role": "dest",
                    "usage": "write",
                    "expected_kind": "an",
                    "ea_address_shape": None,
                    "access": {
                        "kind": "register_write",
                        "width": None,
                        "width_source": None,
                        "result_kind": "scalar",
                    },
                },
            ],
        })
        _merge_execution_form_overrides(execution, "6", {
            "operands": [
                {
                    "index": 0,
                    "role": "source",
                    "usage": "address",
                    "expected_kind": "ind",
                    "access": {
                        "kind": "compute_address",
                        "width": None,
                        "width_source": None,
                        "result_kind": "address",
                    },
                },
            ],
        })
        _merge_execution_form_overrides(execution, "7", {
            "operands": [
                {
                    "index": 0,
                    "role": "source",
                    "usage": "address",
                    "expected_kind": "ind",
                    "access": {
                        "kind": "compute_address",
                        "width": None,
                        "width_source": None,
                        "result_kind": "address",
                    },
                },
            ],
        })
        _merge_execution_form_overrides(execution, "8", {
            "operands": [
                {
                    "index": 0,
                    "role": "source",
                    "usage": "value",
                    "expected_kind": "ctrl_reg",
                    "ea_address_shape": None,
                    "access": {
                        "kind": "register_read",
                        "width": None,
                        "width_source": None,
                        "result_kind": "scalar",
                    },
                },
                {
                    "index": 1,
                    "role": "source",
                    "usage": "address",
                    "expected_kind": "ea",
                    "access": {
                        "kind": "compute_address",
                        "width": None,
                        "width_source": None,
                        "result_kind": "address",
                    },
                },
                {
                    "index": 2,
                    "role": "source",
                    "usage": "value",
                    "expected_kind": "imm",
                    "ea_address_shape": None,
                    "access": {
                        "kind": "immediate",
                        "width": None,
                        "width_source": None,
                        "result_kind": "scalar",
                    },
                },
                {
                    "index": 3,
                    "role": "dest",
                    "usage": "write",
                    "expected_kind": "an",
                    "ea_address_shape": None,
                    "access": {
                        "kind": "register_write",
                        "width": None,
                        "width_source": None,
                        "result_kind": "scalar",
                    },
                },
            ],
        })
        _merge_execution_form_overrides(execution, "9", {
            "operands": [
                {
                    "index": 0,
                    "role": "source",
                    "usage": "value",
                    "expected_kind": "ctrl_reg",
                    "ea_address_shape": None,
                    "access": {
                        "kind": "register_read",
                        "width": None,
                        "width_source": None,
                        "result_kind": "scalar",
                    },
                },
                {
                    "index": 1,
                    "role": "source",
                    "usage": "address",
                    "expected_kind": "ea",
                    "access": {
                        "kind": "compute_address",
                        "width": None,
                        "width_source": None,
                        "result_kind": "address",
                    },
                },
                {
                    "index": 2,
                    "role": "source",
                    "usage": "value",
                    "expected_kind": "imm",
                    "ea_address_shape": None,
                    "access": {
                        "kind": "immediate",
                        "width": None,
                        "width_source": None,
                        "result_kind": "scalar",
                    },
                },
                {
                    "index": 3,
                    "role": "dest",
                    "usage": "write",
                    "expected_kind": "an",
                    "ea_address_shape": None,
                    "access": {
                        "kind": "register_write",
                        "width": None,
                        "width_source": None,
                        "result_kind": "scalar",
                    },
                },
            ],
        })
    if mnemonic in ("PLOAD", "PFLUSH", "PFLUSH PFLUSHA", "PTEST"):
        _replace_pmmu_execution_operands_from_forms(inst, execution)
    if mnemonic in ("ABCD", "SBCD", "ADDX", "SUBX"):
        _merge_execution_form_overrides(execution, "1", {
            "operands": [
                {
                    "index": 0,
                    "role": "source",
                    "usage": "value",
                    "expected_kind": "predec",
                    "ea_address_formula": "an",
                    "ea_register_update": "predecrement",
                    "ea_index_extension_format": "none",
                    "ea_index_register_class": "none",
                    "ea_index_value_width_source": "none",
                    "ea_index_scale_source": "none",
                    "ea_index_sign_source": "none",
                    "ea_displacement_source": "none",
                    "ea_address_shape": "predecrement",
                    "ea_base_kind": "an",
                    "ea_uses_displacement": False,
                    "ea_uses_index": False,
                    "ea_pc_base_bias_bytes": 0,
                    "ea_address_literal_width_bytes": 0,
                    "access": {
                        "kind": "memory_read",
                        "width": None,
                        "width_source": "instruction_size",
                        "result_kind": "scalar",
                    },
                },
                {
                    "index": 1,
                    "role": "dest",
                    "usage": "write",
                    "expected_kind": "predec",
                    "ea_address_formula": "an",
                    "ea_register_update": "predecrement",
                    "ea_index_extension_format": "none",
                    "ea_index_register_class": "none",
                    "ea_index_value_width_source": "none",
                    "ea_index_scale_source": "none",
                    "ea_index_sign_source": "none",
                    "ea_displacement_source": "none",
                    "ea_address_shape": "predecrement",
                    "ea_base_kind": "an",
                    "ea_uses_displacement": False,
                    "ea_uses_index": False,
                    "ea_pc_base_bias_bytes": 0,
                    "ea_address_literal_width_bytes": 0,
                    "access": {
                        "kind": "memory_write",
                        "width": None,
                        "width_source": "instruction_size",
                        "result_kind": "scalar",
                    },
                },
            ],
        })
    if mnemonic in ("NEGX", "NBCD"):
        _merge_execution_form_overrides(execution, "1", {
            "operands": [
                {
                    "index": 0,
                    "role": "dest",
                    "usage": "read_modify_write",
                    "expected_kind": "dn",
                    "ea_address_formula": None,
                    "ea_register_update": "none",
                    "ea_index_extension_format": "none",
                    "ea_index_register_class": "none",
                    "ea_index_value_width_source": "none",
                    "ea_index_scale_source": "none",
                    "ea_index_sign_source": "none",
                    "ea_displacement_source": "none",
                    "ea_address_shape": None,
                    "ea_base_kind": None,
                    "ea_uses_displacement": False,
                    "ea_uses_index": False,
                    "ea_pc_base_bias_bytes": 0,
                    "ea_address_literal_width_bytes": 0,
                    "access": {
                        "kind": "register_write",
                        "width": None,
                        "width_source": "instruction_size",
                        "result_kind": "scalar",
                    },
                },
            ],
        })
    if mnemonic == "EXT, EXTB":
        execution["operands"] = [
            {
                "index": 0,
                "role": "source",
                "usage": "read_modify_write",
                "expected_kind": "dn",
                "access": {
                    "kind": "register_write",
                    "width": 2,
                    "width_source": None,
                    "result_kind": "scalar",
                },
            },
        ]
        execution["unary"] = {
            "sign_extend_source_bits": 8,
        }
        _merge_execution_form_overrides(execution, "0", {
            "unary": {
                "sign_extend_source_bits": 8,
            },
            "operands": [
                {
                    "index": 0,
                    "role": "source",
                    "usage": "read_modify_write",
                    "access": {
                        "kind": "register_write",
                        "width": 2,
                        "width_source": None,
                        "result_kind": "scalar",
                    },
                },
            ],
        })
        _merge_execution_form_overrides(execution, "1", {
            "unary": {
                "sign_extend_source_bits": 16,
            },
            "operands": [
                {
                    "index": 0,
                    "role": "source",
                    "usage": "read_modify_write",
                    "access": {
                        "kind": "register_write",
                        "width": 4,
                        "width_source": None,
                        "result_kind": "scalar",
                    },
                },
            ],
        })
        _merge_execution_form_overrides(execution, "2", {
            "unary": {
                "sign_extend_source_bits": 8,
            },
            "operands": [
                {
                    "index": 0,
                    "role": "source",
                    "usage": "read_modify_write",
                    "access": {
                        "kind": "register_write",
                        "width": 4,
                        "width_source": None,
                        "result_kind": "scalar",
                    },
                },
            ],
        })
    return execution


def apply_execution_metadata(kb_data: list[JsonDict]) -> int:
    """Phase 11b: derive normalized execution metadata from PDF-backed fields."""
    count = 0
    for inst in kb_data:
        execution = _build_execution_metadata(inst)
        if execution is None:
            continue
        inst["execution"] = execution
        count += 1
    return count


def _extract_overflow_undefined_flags(inst: Any) -> Any:
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


def _derive_nop_encoding(kb_data: list[JsonDict]) -> Any:
    """Derive the NOP instruction encoding from KB bit-field data.

    Reconstructs the NOP opword from the encoding's fixed-bit fields,
    stores as 'nop_opword' in the top-level KB metadata. This lets
    downstream tools use NOP without hardcoding 0x4E71.
    """
    for inst in kb_data:
        if inst["mnemonic"] == "NOP":
            encodings = cast(list[JsonDict], inst.get("encodings", []))
            if not encodings:
                continue
            enc = encodings[0]
            opword = 0
            for field in cast(list[JsonDict], enc.get("fields", [])):
                name = str(field["name"])
                if name in ("0", "1"):
                    bit_val = int(name)
                    bit_lo = cast(int, field["bit_lo"])
                    bit_hi = cast(int, field["bit_hi"])
                    for bit in range(bit_lo, bit_hi + 1):
                        opword |= (bit_val << bit)
            return opword
    return None


def apply_operation_types(kb_data: list[JsonDict]) -> tuple[int, Any]:
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
        operation = str(inst.get("operation", ""))
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
                if any("data_sizes" in f for f in cast(list[JsonDict], inst.get("forms", []))):
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
            if op_type == "compare_swap":
                _extract_compare_swap_effects(inst)
            # Extract shift fill behavior from Description (Track A)
            if op_type in ("shift", "rotate", "rotate_extend"):
                _extract_shift_fill(inst)
            # Extract bit modulus and size-by-EA-category from Description (Track A)
            if op_type == "bit_test":
                _extract_bit_modulus(inst)
                _extract_size_by_ea_category(inst)
            # Extract source sign-extension from Description (Track A)
            _extract_source_sign_extend(inst)
            # Extract byte-striped transfer layout from Description (Track A)
            _extract_transfer_layout(inst)
            # Extract bounds-check trap condition from Operation text (Track A)
            _extract_bounds_check(inst)
            # Extract CC result width override from CC descriptions (Track A)
            _extract_cc_result_bits(inst)
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

def output_summary(kb_data: Any) -> None:
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


def output_markdown(kb_data: Any, outfile: Any) -> None:
    lines = ["# M68000 Instruction Set Reference\n",
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

def dump_page(doc: Any, page_num: int) -> None:
    """Dump positioned text, encodings, and EA tables for a page."""
    page = doc[page_num - 1]
    spans = extract_page_spans(page)
    rows = spans_to_rows(spans)

    print(f"=== PAGE {page_num} ({len(spans)} spans) ===\n")
    for y_key in sorted(rows.keys()):
        parts = rows[y_key]
        print(f"  y={y_key:6.0f}:", end="")
        for x, x2, text, _font, _size in parts:
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
# Phase 12: Assembly syntax index
# ═══════════════════════════════════════════════════════════════════════════════

def _build_asm_syntax_index(kb_data: list[JsonDict]) -> dict[str, Any]:
    """Build (asm_mnemonic, operand_types) → KB mnemonic lookup from forms.

    For each KB instruction, extract the assembly mnemonic (first word of
    the form syntax) and the operand type tuple. This allows resolving
    'andi #x,ccr' → KB instruction "ANDI to CCR" without hardcoding.

    Returns dict mapping "asm_mnemonic:type1,type2" → KB mnemonic.
    """
    index = {}
    for inst in kb_data:
        mnemonic = str(inst["mnemonic"])
        for form in cast(list[JsonDict], inst.get("forms", [])):
            syntax = str(form.get("syntax", ""))
            if not syntax:
                continue
            # Assembly mnemonic = first word of syntax, lowered, size suffix stripped
            asm_word = syntax.split()[0].lower()
            if "." in asm_word:
                asm_word = asm_word.split(".")[0]
            ops = tuple(str(o["type"]) for o in cast(list[JsonDict], form.get("operands", [])))
            key = f"{asm_word}:{','.join(ops)}"
            # First entry wins (avoids duplicate forms overwriting)
            if key not in index:
                index[key] = mnemonic
    return index


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 14: Displacement encoding extraction
# ═══════════════════════════════════════════════════════════════════════════════

def _extract_displacement_encoding(kb_data: list[JsonDict]) -> Any:
    """Extract displacement encoding rules from instruction description text.

    For branch instructions (Bcc, BRA, BSR), the PDF description explicitly
    states which values in the 8-bit displacement field signal word or long
    extension words:
      - "If the 8-bit displacement field... is zero, a 16-bit displacement
        (the word immediately following the instruction) is used."
      - "If the 8-bit displacement field... is all ones ($FF), the 32-bit
        displacement (long word immediately following the instruction) is used."

    Emits 'displacement_encoding' in constraints:
        {
            "field": "8-BIT DISPLACEMENT",
            "word_signal": 0,        # value that signals 16-bit extension
            "long_signal": 255,      # value that signals 32-bit extension
            "word_bits": 16,
            "long_bits": 32
        }

    Parser-asserted: PDF p129 (Bcc), p159 (BRA), p163 (BSR).
    The text is parseable but uses two different phrasings:
      "is zero" and "is all ones ($FF)".
    We match both patterns from the description field.
    """
    import re

    count = 0
    for inst in kb_data:
        if not inst.get("uses_label"):
            continue

        desc = str(inst.get("description", ""))

        # Look for the word-signal pattern: "displacement field... is zero"
        # and long-signal pattern: "displacement field... is all ones ($FF)"
        has_word = bool(re.search(
            r"8-bit displacement field.*?is zero.*?16-bit displacement", desc,
            re.IGNORECASE))
        has_long = bool(re.search(
            r"8-bit displacement field.*?all ones.*?\$FF.*?32-bit displacement",
            desc, re.IGNORECASE))

        if not has_word and not has_long:
            continue

        # Find the displacement field in the encoding
        enc = cast(list[JsonDict], inst["encodings"])[0]
        disp_field = None
        for f in cast(list[JsonDict], enc["fields"]):
            field_name = str(f["name"])
            if "displacement" in field_name.lower():
                disp_field = field_name
                break

        if disp_field is None:
            continue

        disp_enc: JsonDict = {"field": disp_field}
        if has_word:
            disp_enc["word_signal"] = 0
            disp_enc["word_bits"] = 16
        if has_long:
            disp_enc["long_signal"] = 255
            disp_enc["long_bits"] = 32

        constraints = cast(JsonDict, inst.setdefault("constraints", {}))
        constraints["displacement_encoding"] = disp_enc
        count += 1

    return count


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 15: Mnemonic alias extraction
# ═══════════════════════════════════════════════════════════════════════════════

def _extract_cc_aliases(doc: Any) -> dict[str, str]:
    """Extract condition code aliases from PDF Table 3-19 parenthetical notation.

    The PDF's Table 3-19 "Conditional Tests" lists some condition codes with
    parenthetical alternate names: CC(HS) and CS(LO).  Phase 0 strips these
    to get the primary mnemonic; here we re-scan the same table to capture the
    alias mappings.

    Also asserts DBRA → DBF: PDF p189 (DBcc) describes condition code F (False,
    encoding 0001) which "always decrements the counter and branches".  The
    mnemonic DBRA ("Decrement and Branch Always") is the universally-used alias
    for DBF in all M68K assemblers, but the PDF does not explicitly state this
    equivalence.  Asserted because: (1) every M68K assembler recognises DBRA,
    (2) the Motorola M68K Family reference card lists DBRA as a synonym for DBF,
    (3) DBRA has no other possible interpretation.

    Returns dict mapping alias_suffix → canonical_suffix, e.g. {"hs": "cc", ...}
    """
    aliases = {}
    pending_aliases = []
    # Primary CC mnemonics from Phase 0 (already extracted into global CC_TABLE)
    primary_ccs = set(CC_TABLE.values())

    # Scan PDF Table 3-19 for parenthetical alternate names
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
            for next_idx in range(idx + 1, min(idx + 25, len(sorted_ys))):
                next_y = sorted_ys[next_idx]
                next_row = rows[next_y]

                # Find mnemonic text with parenthetical alias
                for _, _, text_span, _, _ in next_row:
                    if len(text_span) == 4 and all(c in "01" for c in text_span):
                        continue  # skip encoding
                    # Match patterns like "CC(HI)" or "CS(LO)"
                    alias_match = re.match(
                        r"([A-Za-z]+)\(([A-Za-z]+)\)", text_span.rstrip("*"))
                    if alias_match:
                        primary = alias_match.group(1).lower()
                        alt = alias_match.group(2).lower()
                        pending_aliases.append((alt, primary))

            break  # only process first matching page

    # Filter: only keep aliases that don't conflict with primary CC names.
    # PDF shows "CC(HI)" but HI is already code 2 ("High"), so that
    # parenthetical is descriptive, not an assembler alias.  Only "LO"
    # (not a primary CC) is a genuine assembler alias for CS.
    for alt, primary in pending_aliases:
        if alt not in primary_ccs:
            aliases[alt] = primary

    # Parser-asserted: DBRA → DBF.  See docstring for justification.
    # PDF p189 Section 4, DBcc instruction.
    aliases["ra"] = "f"

    return aliases


def _extract_immediate_routing(kb_data: list[JsonDict]) -> dict[str, str]:
    """Build immediate routing map from KB instruction data.

    When the PDF defines both a general instruction (ADD) and an immediate-
    specific variant (ADDI), they are functionally equivalent for #imm source
    operands.  This map lets assemblers route ADD #imm,Dn through ADDI for
    shorter/canonical encoding.

    Detection: instruction mnemonic ends with "I", the base instruction
    (mnemonic without trailing "I") exists in the KB, AND either:
      (a) title contains "Immediate", or
      (b) the immediate instruction has a form with first operand type "imm"
          and the base instruction has an opmode_table (general-purpose ALU)

    Returns dict mapping base_mnemonic → immediate_mnemonic, e.g. {"ADD": "ADDI"}.
    """
    by_mnemonic = {inst["mnemonic"]: inst for inst in kb_data}
    routing = {}

    for inst in kb_data:
        mn = str(inst["mnemonic"])
        # Must end with "I" and not contain spaces (skip "ORI to CCR" etc.)
        if not mn.endswith("I") or " " in mn:
            continue

        base = mn[:-1]
        base_inst = by_mnemonic.get(base)
        if base_inst is None:
            continue

        title = str(inst.get("title", ""))
        # Check title contains "Immediate"
        if "Immediate" in title:
            routing[base] = mn
            continue

        # Fallback: check structural match — immediate inst has #imm form,
        # base inst has opmode_table (general-purpose ALU instruction)
        has_imm_form = any(
            cast(list[JsonDict], f.get("operands", []))[0].get("type") == "imm"
            for f in cast(list[JsonDict], inst.get("forms", []))
            if cast(list[JsonDict], f.get("operands", []))
        )
        has_opmode = bool(cast(JsonDict, base_inst.get("constraints", {})).get("opmode_table"))
        if has_imm_form and has_opmode:
            routing[base] = mn

    return routing


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 13: Direction field value extraction
# ═══════════════════════════════════════════════════════════════════════════════

_SIZE_ENCODING_PATTERN = re.compile(
    r"([01]{1,2})\s*[\u2014\u2013\-]\s*(Byte|Word|Long)",
    re.IGNORECASE,
)


def _apply_size_encodings(kb_data: list[JsonDict]) -> int:
    """Extract structured SIZE field encodings from PDF field descriptions."""
    size_name_map = {"byte": "b", "word": "w", "long": "l"}
    count = 0

    for inst in kb_data:
        size_fields = [
            size_field
            for enc in cast(list[JsonDict], inst.get("encodings", []))
            for size_field in cast(list[JsonDict], enc.get("fields", []))
            if str(size_field["name"]) == "SIZE"
        ]
        if not size_fields:
            continue

        size_desc = cast(dict[str, str], inst.get("field_descriptions", {})).get("Size")
        values: list[dict[str, int | str]] = []
        if size_desc:
            seen_sizes = set()
            seen_bits = set()
            for match in _SIZE_ENCODING_PATTERN.finditer(size_desc):
                bits = int(match.group(1), 2)
                size = size_name_map[match.group(2).lower()]
                if size in seen_sizes:
                    raise RuntimeError(
                        f"{inst['mnemonic']}: duplicate size encoding for {size!r}"
                    )
                if bits in seen_bits:
                    raise RuntimeError(
                        f"{inst['mnemonic']}: duplicate SIZE bit pattern {bits:02b}"
                    )
                seen_sizes.add(size)
                seen_bits.add(bits)
                values.append({"size": size, "bits": bits})
        else:
            # Parser-asserted from the PDF multiply/divide syntax lines:
            # the only instructions with a SIZE bit but no Size field table are
            # MULS/MULU/DIVS/DIVU long-form extension words. Their syntax shows
            # a word form and a long form, and the extension SIZE field is 1 bit,
            # so encode word=0, long=1 structurally from the form set.
            sizes = inst.get("sizes", [])
            width = cast(int, size_fields[0]["width"])
            if width == 1 and sizes == ["w", "l"]:
                values = [{"size": "w", "bits": 0}, {"size": "l", "bits": 1}]
            else:
                continue

        if not values:
            continue

        inst["size_encoding"] = {
            "field": "SIZE",
            "values": values,
        }
        count += 1

    return count


def _build_condition_families(kb_data: list[JsonDict], pmmu_cc: list[str]) -> list[JsonDict]:
    """Build structured condition-code mnemonic families from canonical data."""
    cpu_codes = tuple(code.lower() for code in _kb_condition_codes())
    pmmu_codes = tuple(code.lower() for code in pmmu_cc)
    families: dict[str, JsonDict] = {}

    for inst in kb_data:
        constraints = cast(JsonDict, inst.get("constraints", {}))
        cc_param = cast(JsonDict | None, constraints.get("cc_parameterized"))
        is_pmmu = "68851" in str(inst.get("processors", ""))
        codes = pmmu_codes if is_pmmu else cpu_codes
        excluded = tuple(sorted(code.lower() for code in cast(list[str], cc_param.get("excluded", [])))) if cc_param else ()

        for raw_name in str(inst["mnemonic"]).split(","):
            canonical = raw_name.strip().lower().replace(" ", "")
            if not canonical.endswith("cc"):
                continue
            prefix = canonical[:-2]
            if not prefix:
                continue
            entry = {
                "prefix": prefix,
                "canonical": canonical,
                "codes": codes,
                "match_numeric_suffix": is_pmmu,
                "exclude_from_family": excluded,
            }
            existing = families.get(canonical)
            if existing is not None and existing != entry:
                raise RuntimeError(
                    f"Conflicting condition family definition for {canonical!r}"
                )
            families[canonical] = entry

    return [families[key] for key in sorted(families)]


def _apply_direction_field_values(kb_data: list[JsonDict]) -> int:
    """Parse direction field descriptions into structured form-to-field-value mapping.

    For instructions with a 'dr' encoding field and corresponding text in
    field_descriptions, parse the description to extract the numeric value
    associated with each transfer direction, and map it to the form index.

    Emits 'direction_field_values' on the instruction:
        {"field": "dr", "form_field_value": {0: <int>, 1: <int>}}
    where form_field_value maps form index → dr bit value for that form.
    """
    count = 0
    for inst in kb_data:
        enc = cast(list[JsonDict], inst.get("encodings", []))
        if not enc:
            continue
        # Skip instructions where dr is a shift/rotate direction — these use
        # direction_variants constraint instead of transfer direction semantics
        constraints = cast(JsonDict, inst.get("constraints", {}))
        if constraints.get("direction_variants"):
            continue
        # Find 'dr' or similar direction fields in encoding
        dr_field = None
        for f in cast(list[JsonDict], enc[0].get("fields", [])):
            if str(f["name"]) == "dr":
                dr_field = f
                break
        if dr_field is None:
            continue

        fd = cast(dict[str, str], inst.get("field_descriptions", {}))
        dr_desc = fd.get("dr", "")
        if not dr_desc:
            continue

        forms = cast(list[JsonDict], inst.get("forms", []))
        if len(forms) < 2:
            continue

        # Parse "0 — <text>" / "1 — <text>" patterns from field description
        # The description text uses em-dash or en-dash separators
        val_descs: dict[int, str] = {}
        for m in re.finditer(r"(\d)\s*[\u2014\u2013\-]\s*([^.]+)", dr_desc):
            val_descs[int(m.group(1))] = m.group(2).strip().lower()

        if not val_descs:
            continue

        # Map form operand types to direction values by matching description
        # text against form operand patterns.
        # Strategy: each dr value description says "<source> to <destination>".
        # Match the source/destination keywords against form operand types.
        type_keywords = {
            "an": ["address register", "general register"],
            "dn": ["data register", "general register"],
            "usp": ["user stack pointer"],
            "sr": ["status register"],
            "ccr": ["condition code register"],
            "ea": ["memory", "effective address"],
            "reglist": ["register"],
            "ctrl_reg": ["control register"],
            "rn": ["general register"],
        }
        form_field_value: dict[int, int] = {}
        for val, desc in val_descs.items():
            if "to" not in desc:
                continue
            src_part = desc.split("to", 1)[0].strip()
            dst_part = desc.split("to", 1)[1].strip()
            # Find the form where first operand matches src and second matches dst
            for form_idx, form in enumerate(forms):
                if form_idx in form_field_value:
                    continue
                ops = [str(o["type"]) for o in cast(list[JsonDict], form.get("operands", []))]
                if len(ops) < 2:
                    continue
                src_kws = type_keywords.get(ops[0], [])
                dst_kws = type_keywords.get(ops[1], [])
                src_match = any(kw in src_part for kw in src_kws)
                dst_match = any(kw in dst_part for kw in dst_kws)
                if src_match and dst_match:
                    form_field_value[form_idx] = val

        if len(form_field_value) == len(forms):
            inst["direction_field_values"] = {
                "field": "dr",
                "form_field_value": form_field_value,
            }
            count += 1
        else:
            # Hard error: if we found a dr field with description but couldn't
            # map all forms, something is wrong with our parsing
            raise RuntimeError(
                f"{inst['mnemonic']}: found dr field with description but could "
                f"only map {len(form_field_value)}/{len(forms)} forms. "
                f"val_descs={val_descs}, forms={[f.get('operands') for f in forms]}"
            )

    return count


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse M68K instruction reference from PDF (all phases)")
    parser.add_argument("pdf", help="Path to M68000 PRM PDF")
    parser.add_argument("--output", choices=["json", "md", "summary"], default="json")
    parser.add_argument("--outfile", help=f"Output file path (default: {M68K_INSTRUCTIONS_JSON.as_posix()})")
    parser.add_argument("--sections", default="4,6",
                        help="Comma-separated section numbers to parse (default: 4,6)")
    parser.add_argument("--dump-page", type=int, help="Debug: dump positioned text for a page")
    parser.add_argument("--dry-run", action="store_true", help="Don't write output files")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
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
    apply_parser_asserted_syntax_fixes(kb_data)
    apply_parser_asserted_encoding_fixes(kb_data)
    apply_parser_asserted_pmmu_fc_encoding_fixes(kb_data)
    apply_parser_asserted_field_value_fixes(kb_data)

    # Phase 4: Derive constraints
    print("Phase 4: Deriving constraints...")
    apply_constraints(kb_data, doc)

    # Phase 4b: Split EA modes by direction (needs constraints from Phase 4)
    apply_ea_direction_split(kb_data)
    apply_parser_asserted_ea_mode_fixes(kb_data)
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

    # Phase 6: Extract EA extension word formats (Brief + Full from PDF page 43)
    print("Phase 6: Extracting EA extension word formats...")
    ea_brief, ea_full = extract_ea_extension_formats(doc)
    print(f"  Brief extension word fields: {[f['name'] for f in ea_brief]}")
    print(f"  Full extension word fields: {[f['name'] for f in ea_full]}")

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

    # Phase 11b: derive normalized execution metadata for downstream generators.
    print("Phase 11b: Deriving execution metadata...")
    execution_count = apply_execution_metadata(kb_data)
    print(f"  Instructions with execution metadata: {execution_count}")

    # Phase 12: Build assembly syntax index for multi-word mnemonic resolution
    # When the PDF defines an instruction with a multi-word KB mnemonic
    # (e.g. "ANDI to CCR", "MOVE from SR", "MOVE USP"), the assembly text
    # uses only the first word ("andi", "move") with operand types ("ccr",
    # "sr", "usp") determining which KB instruction is meant.  This index
    # lets downstream tools resolve (asm_mnemonic, operand_type_tuple) to
    # the correct KB instruction without hardcoding mnemonic names.
    print("Phase 12: Building assembly syntax index...")
    asm_syntax_index = _build_asm_syntax_index(kb_data)
    print(f"  Indexed {len(asm_syntax_index)} syntax entries")

    print("Phase 13: Extracting size encodings...")
    size_encoding_count = _apply_size_encodings(kb_data)
    print(f"  Instructions with size encodings: {size_encoding_count}")

    # Phase 14: Parse direction field descriptions into structured values
    # Instructions like MOVE USP have a 'dr' field whose meaning is described
    # in natural language in field_descriptions. Parse "0 — Transfer the
    # address register to the user stack pointer" into {0: "an_to_usp",
    # 1: "usp_to_an"} so downstream tools don't need to parse English text.
    print("Phase 14: Extracting direction field values...")
    dir_count = _apply_direction_field_values(kb_data)
    print(f"  Instructions with direction field values: {dir_count}")

    # Phase 14b: Bind repeated encoding fields to operand/value sources.
    # MOVE-style encodings repeat generic MODE/REGISTER field names. Emit
    # operand bindings here so downstream generators use parser-produced KB
    # structure rather than inferring from mnemonic-specific rules.
    print("Phase 14b: Extracting field bindings...")
    binding_count = _apply_field_bindings(kb_data)
    apply_parser_asserted_field_binding_fixes(kb_data)
    print(f"  Instructions with field bindings: {binding_count}")

    # Phase 15: Extract displacement encoding from description text
    # PDF descriptions for Bcc/BRA/BSR explicitly state the reserved values
    # in the 8-bit displacement field that signal word/long extension.
    # Parse these into structured data so downstream tools don't hardcode them.
    print("Phase 15: Extracting displacement encoding...")
    disp_count = _extract_displacement_encoding(kb_data)
    print(f"  Instructions with displacement_encoding: {disp_count}")

    # Phase 16: Extract mnemonic aliases and immediate routing
    # CC aliases from PDF Table 3-19 parenthetical notation (e.g. CC(HS) → hs=cc)
    # plus parser-asserted DBRA → DBF. Immediate routing from title pattern matching
    # (ADDI title "Add Immediate" → ADD routes to ADDI for #imm operands).
    print("Phase 16: Extracting mnemonic aliases...")
    cc_aliases = _extract_cc_aliases(doc)
    immediate_routing = _extract_immediate_routing(kb_data)
    condition_families = _build_condition_families(kb_data, pmmu_cc)
    print(f"  CC aliases: {cc_aliases}")
    print(f"  Immediate routing: {immediate_routing}")
    print(f"  Condition families: {len(condition_families)}")

    # Track B parser-assertion: EXG encoding field boundaries.
    # PDF p128 Figure shows OPMODE as bits 7:3 (5 bits) and REGISTER Ry as
    # bits 2:0 (3 bits). The PDF text extraction misparses these as 7:4 and
    # 3:0 because the table column alignment is ambiguous. The opmode values
    # (8=01000, 9=01001, 17=10001) require 5 bits — they cannot fit in 4.
    for inst in kb_data:
        if inst["mnemonic"] == "EXG":
            enc = inst["encodings"][0]
            for f in enc["fields"]:
                if f["name"] == "OPMODE" and f["bit_lo"] == 4:
                    f["bit_lo"] = 3
                    f["width"] = f["bit_hi"] - f["bit_lo"] + 1
                elif f["name"].startswith("REGISTER") and f["bit_hi"] == 3:
                    f["bit_hi"] = 2
                    f["width"] = f["bit_hi"] - f["bit_lo"] + 1
            break

    # Track B parser-assertion: BTST/BCHG/BCLR/BSET immediate forms use a full
    # 16-bit extension word for the bit number on PRM pp131/134/160/165. The
    # extracted extension encoding currently keeps only the variable low bits
    # (`BIT NUMBER` width 8 or 9), dropping the fixed zero upper bits because
    # the centered extension-word label is parsed without the surrounding word
    # frame. Downstream generators need this modeled as a normal full extension
    # word so the existing two-word encoding path can consume it generically.
    for inst in kb_data:
        if inst["mnemonic"] not in {"BTST", "BCHG", "BCLR", "BSET"}:
            continue
        encodings = cast(list[JsonDict], inst.get("encodings", []))
        if len(encodings) < 3:
            continue
        ext_fields = cast(list[JsonDict], encodings[2].get("fields", []))
        if sum(int(field.get("width", 0)) for field in ext_fields) != 16:
            continue
        variable_fields = [field for field in ext_fields if field.get("name") not in {"0", "1"}]
        if len(variable_fields) != 1 or variable_fields[0].get("name") != "BIT NUMBER":
            continue
        if inst["mnemonic"] == "BSET":
            # Track B parser-assertion: PRM p160 shows the immediate BSET bit
            # number in the low byte of the extension word, same structure as
            # BTST/BCHG/BCLR. The extracted table currently stretches BIT NUMBER
            # across bits 8:0, which incorrectly implies a 9-bit immediate.
            # Normalize it to an 8-bit field and restore the fixed zero in bit 8
            # so downstream range extraction and encoders stay spec-driven.
            variable_fields[0]["bit_hi"] = 7
            variable_fields[0]["bit_lo"] = 0
            variable_fields[0]["width"] = 8
            if not any(field.get("name") == "0" and int(field.get("bit_hi", -1)) == 8 and int(field.get("bit_lo", -1)) == 8 for field in ext_fields):
                ext_fields.insert(7, {"name": "0", "bit_hi": 8, "bit_lo": 8, "width": 1})
        constraints = cast(JsonDict, inst.setdefault("constraints", {}))
        constraints["immediate_range"] = {
            "min": 0,
            "max": (1 << int(variable_fields[0]["width"])) - 1,
            "field": "BIT NUMBER",
            "bits": int(variable_fields[0]["width"]),
        }
        # Track B parser-assertion: the same PRM pages show the immediate form's
        # opword uses fixed bits 11:9 = 100, so the only remaining REGISTER field
        # in the opword is the destination EA register. The shared extracted
        # fb_011 template still binds form 1 REGISTER occurrence 1 to <ea>, but
        # after the fixed 100 bits there is only occurrence 0 left in encoding[1].
        # We assert explicit per-form bindings here so downstream generators see
        # the actual encoded field order from the PDF opword rather than carrying
        # a mnemonic-specific workaround.
        inst["field_bindings"] = [
            {"field": "MODE", "form_index": 0, "occurrence": 0, "operand_index": 1, "value_source": "ea_mode"},
            {"field": "REGISTER", "form_index": 0, "occurrence": 0, "operand_index": 0, "value_source": "reg"},
            {"field": "REGISTER", "form_index": 0, "occurrence": 1, "operand_index": 1, "value_source": "ea_reg"},
            {"field": "DATA", "form_index": 1, "occurrence": 0, "operand_index": 0, "value_source": "value"},
            {"field": "MODE", "form_index": 1, "occurrence": 0, "operand_index": 1, "value_source": "ea_mode"},
            {"field": "REGISTER", "form_index": 1, "occurrence": 0, "operand_index": 1, "value_source": "ea_reg"},
        ]
        inst.pop("field_binding_template", None)
        # Track B parser-assertion: PRM BTST syntax/description allows a data
        # register or memory destination, not an immediate destination. The
        # extracted BTST EA table currently leaks `imm` into dst modes while the
        # same pages also state the destination is tested as register/memory.
        # Remove only the invalid immediate destination upstream so downstream
        # corpus generation and legality checks stay KB-driven.
        if inst["mnemonic"] == "BTST":
            ea_modes = cast(JsonDict, inst.get("ea_modes", {}))
            dst_modes = cast(list[str], ea_modes.get("dst", []))
            ea_modes["dst"] = [mode for mode in dst_modes if mode != "imm"]
        ea_modes_020 = cast(JsonDict, inst.get("ea_modes_020", {}))
        dst_modes_020 = cast(list[str], ea_modes_020.get("dst", []))
        if "dn" in dst_modes_020:
            ea_modes_020["dst"] = [mode for mode in dst_modes_020 if mode != "dn"]

    # Track B parser-assertion: MOVEP's opword uses separate DATA REGISTER and
    # ADDRESS REGISTER fields plus a 16-bit displacement extension word on PRM
    # p235. The extracted forms already capture the two syntaxes, but the field
    # bindings are not recoverable from the prose alone. Assert the bindings from
    # the encoding diagram so downstream generators can consume MOVEP on the same
    # generic reg/value patch path used elsewhere.
    for inst in kb_data:
        if inst["mnemonic"] != "MOVEP":
            continue
        inst["field_bindings"] = [
            {"field": "DATA REGISTER", "form_index": 0, "occurrence": 0, "operand_index": 0, "value_source": "reg"},
            {"field": "ADDRESS REGISTER", "form_index": 0, "occurrence": 0, "operand_index": 1, "value_source": "reg"},
            {"field": "16-BIT DISPLACEMENT", "form_index": 0, "occurrence": 0, "operand_index": 1, "value_source": "value"},
            {"field": "DATA REGISTER", "form_index": 1, "occurrence": 0, "operand_index": 1, "value_source": "reg"},
            {"field": "ADDRESS REGISTER", "form_index": 1, "occurrence": 0, "operand_index": 0, "value_source": "reg"},
            {"field": "16-BIT DISPLACEMENT", "form_index": 1, "occurrence": 0, "operand_index": 0, "value_source": "value"},
        ]
        inst.pop("field_binding_template", None)

    # Track B parser-assertion: MOVEM on PRM p232 always includes a 16-bit
    # register-list mask extension word immediately after the opword. The
    # extracted encoding currently misses that second word even though the field
    # description table contains "Register List Mask". Add the missing extension
    # encoding upstream so downstream tools keep using the generic bound-extension
    # path, and assert explicit bindings for the reglist operand.
    for inst in kb_data:
        if inst["mnemonic"] != "MOVEM":
            continue
        encodings = cast(list[JsonDict], inst.get("encodings", []))
        if len(encodings) == 1:
            encodings.append({"fields": [{"name": "REGISTER LIST MASK", "bit_hi": 15, "bit_lo": 0, "width": 16}]})
        inst["field_bindings"] = [
            {"field": "MODE", "form_index": 0, "occurrence": 0, "operand_index": 1, "value_source": "ea_mode"},
            {"field": "REGISTER", "form_index": 0, "occurrence": 0, "operand_index": 1, "value_source": "ea_reg"},
            {"field": "REGISTER LIST MASK", "form_index": 0, "occurrence": 0, "operand_index": 0, "value_source": "value"},
            {"field": "MODE", "form_index": 1, "occurrence": 0, "operand_index": 0, "value_source": "ea_mode"},
            {"field": "REGISTER", "form_index": 1, "occurrence": 0, "operand_index": 0, "value_source": "ea_reg"},
            {"field": "REGISTER LIST MASK", "form_index": 1, "occurrence": 0, "operand_index": 1, "value_source": "value"},
        ]
        inst.pop("field_binding_template", None)

    # Track B parser-assertion: MC68851 PFLUSH/PFLUSHA extension word fields.
    # The PDF multi-word table for PFLUSH PFLUSHA is one of the known PMMU
    # extraction gaps. The extracted encoding[1] currently conflates the MASK
    # and FC spans as MASK=8:6 and FC=5:0. Oracle assembly against the bundled
    # vasm shows the immediate-form command word uses MASK in bits 7:5 and FC
    # in bits 3:0 (e.g. "pflush #1,#2,(a0)" -> ext word $3851, where 7:5=010
    # and 3:0=0001). This matches the manual's prose on pp. 492-494 that the
    # MC68851 mask is 3 bits and the immediate FC is 4 bits. Downstream tools
    # must consume the corrected field positions from the KB rather than
    # hardcoding decode logic.
    for inst in kb_data:
        if inst["mnemonic"] == "PFLUSH PFLUSHA":
            enc = inst["encodings"][1]
            for f in enc["fields"]:
                if f["name"] == "MASK":
                    f["bit_hi"] = 7
                    f["bit_lo"] = 5
                    f["width"] = 3
                elif f["name"] == "FC":
                    f["bit_hi"] = 3
                    f["bit_lo"] = 0
                    f["width"] = 4
            break

    # Output
    outfile = args.outfile or str(M68K_INSTRUCTIONS_JSON)

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
            with open(outpath, "w", encoding="utf-8", newline="\n") as f:
                json.dump(
                    _as_kb_payload(
                        kb_data,
                        pmmu_cc,
                        ea_brief,
                        ea_full,
                        movem_masks,
                        nop_opword,
                        asm_syntax_index,
                        cc_aliases,
                        immediate_routing,
                        condition_families,
                    ),
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
            print(f"\nWrote {len(kb_data)} instructions to {outpath}")
        else:
            print(f"\n(dry run, {len(kb_data)} instructions would be written)")

    if args.output != "summary":
        output_summary(kb_data)


if __name__ == "__main__":
    main()
