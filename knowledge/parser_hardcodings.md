# Parser Hardcodings Ledger

Every hardcoded value in the parsing and testing pipeline that cannot be derived
from the PDF or other authoritative source. Each entry must have a designation
and reasoning.

## Designations
- **PDF-GAP**: The PDF contains the data but our parser failed to extract it
- **PDF-AMBIGUOUS**: The PDF is ambiguous or uses inconsistent notation
- **FORMAT-CONVENTION**: A formatting choice for output, not a data issue
- **VASM-COMPAT**: Required for vasm assembler compatibility

## parse_m68k_instructions.py

### Multi-word encoding fixes
- **Designation**: PDF-GAP
- **Reason**: Multi-word encoding tables confuse the single-word bit field parser.
  Instructions with 2+ word encodings have extension word fields conflated into
  word 1. Fixed with known-correct values from the manual.
- **Affected**:
  - Coprocessor: cpBcc, cpDBcc, cpGEN, cpScc, cpTRAPcc, cpRESTORE, cpSAVE
  - PMMU (68851): PDBcc, PScc, PTRAPcc, PFLUSH PFLUSHA, PFLUSHR
  - Extension word leak: MOVEM, ADDI, SUBI, CMPI
  - 68040: MOVE16

### Section page ranges (SECTIONS dict)
- **Designation**: FORMAT-CONVENTION
- **Reason**: Page ranges for each section of the PDF. These are structural
  metadata about the PDF layout, not instruction data. Could be auto-detected
  but not worth the complexity.
- **Values**: Section 4 (Integer): pages 105-302, Section 6 (Supervisor): pages 455-540

## parse_ea_modes.py

### No hardcodings
- EA mode tables are extracted entirely from PDF positioned text.
- MODE_MAP (mode bits to canonical names) is the standard M68K encoding
  defined by Motorola, not a parser decision.
- 020+ EA modes detected via footnote markers (`*`, `**`) on addressing mode
  names in the PDF tables. Tracked in `ea_modes_020` field.

## parse_syntax_patterns.py

### Syntax normalization (normalize_syntax)
- **Designation**: PDF-AMBIGUOUS
- **Reason**: PDF rendering introduces inconsistent spacing in syntax patterns.
  `"< ea >"` vs `"<ea>"`, `"– (Ax)"` vs `"-(Ax)"`, `"(Ay) +"` vs `"(Ay)+"`.
  These are rendering artifacts, not data differences.

### Concatenated syntax splitting (split_concatenated_forms)
- **Designation**: PDF-GAP
- **Reason**: Some instructions have multiple syntax forms concatenated into one
  string by the PDF parser. E.g., `"EXG Ax,Ay EXG Dx,Ay"` is two forms.
  Split heuristic: detect repeated mnemonic pattern within a single string.
- **Affected**: EXG, ROL/ROR, ASL/ASR, LSL/LSR

### Token cleanup regexes (parse_syntax_to_form)
- **Designation**: PDF-GAP
- **Reason**: PDF concatenates description text with operand tokens
  (e.g., `"Dn32/16 16r – 16q"`, `"Dnextend byte to word"`). Cleanup regexes
  strip trailing descriptions. Not instruction-specific — pattern-based.

## parse_instruction_constraints.py

### CC_TABLE (condition code encoding)
- **Designation**: None (architectural)
- **Reason**: Standard M68K condition code encoding defined by Motorola.
  Same as MODE_MAP — hardware-defined, not a parser decision.

### ARGUMENT COUNT immediate range (CALLM)
- **Designation**: PDF-GAP
- **Reason**: CALLM's argument count is 8 bits in extension word, but the parser
  extracted width=4 due to multi-word conflation. The constraint parser hardcodes
  the ARGUMENT COUNT field to 8 bits / 0-255 range.

## test_m68k_roundtrip.py

### Branch detection
- **Designation**: None (data-driven)
- **Reason**: Uses `uses_label` field from KB, which is derived from `< label >`
  in the PDF syntax patterns. No hardcoding.

### EA syntax generation (ea_syntax function)
- **Designation**: FORMAT-CONVENTION
- **Reason**: Default register choices (d0, a0, d1, a1) and immediate values
  (#$12, #$1234, #$12345678) for test generation. These are arbitrary valid
  values, not data from the PDF.

## Resolved PDF-GAPs (previously hardcoded, now extracted)

### ROXL, ROXR — RESOLVED
- Previously missing from PDF parse. Fixed by adjusting x-position cutoff
  in `is_instruction_start` (370 instead of 400) to exclude right-side
  mnemonic echo.

### Incomplete syntax forms — RESOLVED
- ADD/SUB/AND/OR both forms, ABCD/SBCD/ADDX/SUBX Dn,Dn and predec,predec
  forms now captured via Assembler line extraction in `parse_m68k_instructions.py`.

### MULS/MULU/DIVS/DIVU .L = 020+ — RESOLVED
- `*` prefix on syntax lines detected in `split_concatenated_forms`, stored as
  `processor_020: true` on forms.

### TST/CMPI 020+ EA modes — RESOLVED
- Footnote markers (`*`, `**`) on EA table addressing mode names now detected
  per-column in `parse_ea_modes.py`. Stored in `ea_modes_020` field.

### EXG missing Dn,Dn form
- **Designation**: PDF-GAP (still open)
- **Reason**: PDF has `"EXG Dx,Dy EXG Ax,Ay EXG Dx,Ay"` but the Dx,Dy form
  was lost. The parser only captured the An,An and Dn,An forms.
