# TODO

## vasm Bootstrap

- [x] Get vasm source, build locally (ext/vasm/)
- [ ] Document supported directives, pseudo-ops, and hunk output capabilities
- [x] Write minimal test programs to verify round-trip: source → assemble → binary
- [x] Use vasm as the assembler backend for test oracle
- [x] Identify limits/bugs as we push on edge cases (FPU, coprocessor, addressing modes)
- [ ] Document any patches we apply
- [ ] Derive assembler rule metadata from vasm by running vasm in discovery mode and emit a canonical `knowledge/vasm.json` assembler capability schema, then add a generated `knowledge/vasm_roundtrip_rules.json` that maps KB syntax to roundtrip-safe forms (size/pattern filters, skip-form lists, and canonical replacements) so roundtrip tests consume assembler intent from data only

## Disassembler & Verification

- [x] Build M68K disassembler — test-driven, using knowledge base (instructions, hardware registers, OS calls)
- [x] Build test oracle — assemble known source → binary → disassemble → reassemble → binary diff; drives error detection in data, tools, and references simultaneously
- [x] Derive M68K condition-family canonicalisation from KB data (including PMMU condition tables extracted from PDF)
- [ ] Round-trip validation tooling per CLAUDE.md: reassemble with vasm, binary-diff against original

## Data-Driven Audit — Disassembler (`m68k_disasm.py`)

Everything must be driven from `knowledge/m68k_instructions.json` parsed from the PDF.
KB loaders already exist (`_load_kb_encoding_masks`, `_load_kb_ext_field_map`, etc.) —
the infrastructure is proven, it just needs extending to cover all instructions.

### Critical — Missing 68020+ instruction variants

- [x] Add LINK.L decoding (KB has encoding[2] mask=0xFFF8/val=0x4808)
- [x] Add EXTB.L decoding (KB OPMODE=7 via mask=0xFE38)
- [x] Add CHK.L decoding (KB Size field says "10 — Long")
- [x] Add DIVU.L/DIVS.L decoding (KB has DIVUL/DIVSL entries with ext word)
- [x] Add MULU.L/MULS.L decoding (KB has MULU/MULS entries with ext word)

### High — Hardcoded mask/val pairs (use `_load_kb_encoding_masks()`)

- [x] BTST/BCHG/BCLR/BSET name tables — derive from KB encoding bits 7:6
- [x] MOVEP opmode values 4/5/6/7 — from KB opmode_table with direction from description
- [x] Immediate op name table `{0:"ori", 1:"andi", ...}` — derived `(val>>9)&7` from KB
- [x] Fixed opcodes NOP/RESET/RTE/RTS/TRAPV/RTR/ILLEGAL — all mask=0xFFFF in KB, `_load_kb_fixed_opcodes()`
- [x] TRAP mask — from KB
- [x] LINK.W mask — from KB
- [x] UNLK mask — from KB
- [x] MOVE USP mask — from KB
- [x] JSR mask — from KB
- [x] JMP mask — from KB
- [x] LEA mask — from KB
- [x] BKPT mask — from KB
- [x] SWAP mask — from KB
- [x] EXT.W/EXT.L masks — from KB
- [x] PEA mask — from KB
- [x] MOVEM mask + direction/size bit positions — from KB with `_extract_size_bits()`
- [x] MOVEM register mask tables — `_load_kb_movem_reg_masks()` from PDF page 234 (normal + predecrement)
- [x] CLR/NEG/NEGX/NOT four hardcoded mask/val pairs — from KB
- [x] TST mask — from KB
- [x] TAS mask — from KB
- [x] NBCD mask — from KB
- [x] MOVE from SR mask — from KB
- [x] MOVE to CCR mask — from KB
- [x] MOVE to SR mask — from KB
- [x] MOVEQ bit-8 validation — from KB mask=0xF100
- [x] SBCD mask — from KB
- [x] SUBA/ADDA/CMPA opmode 3=word, 7=long — from KB opmode_table
- [x] SUBX mask — from KB
- [x] CMPM detection — from KB mask
- [x] ABCD mask — from KB
- [x] EXG opmode values — from KB opmode_table with mask check and KB field positions
- [x] ADDX mask — from KB
- [x] Shift/rotate name table — `_load_kb_shift_names()` derived from KB
- [x] MOVE16 all masks — from KB, register positions from KB field maps
- [x] CAS ext word Du/Dc positions — from KB `_load_kb_ext_field_map()`
- [x] MMU type_bits dispatch — from KB masks
- [x] FPU FRESTORE/FSAVE type_bits — from KB masks
- [x] MOVEC control register name table — loaded from KB (parsed from PDF Table 6-1)

### High — Fallback defaults violate hard-fail philosophy

- [x] BFxxx `.get("Do", (11,10,2))` etc — removed fallbacks, hard-fail on missing KB data

### Medium — Architectural patterns

- [x] Opmode-to-size/direction pattern shared across OR/AND/ADD/SUB/CMP/EOR — `_load_kb_opmode_tables()` with `_opmode_ea_to_dn()` helper
- [x] Shift direction bit position (bit 8) — from KB `dr` field via `_load_kb_shift_fields()`
- [x] Shift i/r bit (bit 5) — from KB `i/r` field via `_load_kb_shift_fields()`
- [x] Shift count 0→8 rule — from KB `immediate_range.zero_means` via `_load_kb_shift_fields()`
- [x] Line-F cpid position/values — from KB FRESTORE `ID` field via `_load_kb_cpid_field()`
- [x] BFINS reversed operand order — from KB forms operand type ordering
- [x] PFLUSH ext word field positions — from KB `_load_kb_ext_field_map()["PFLUSH"]` + `_load_kb_ext_encoding_masks()`
- [x] TRAPcc opmode values — from KB opmode_table
- [x] MOVE16 opmode-to-syntax — from KB opmode_table with source/destination fields

## Data-Driven Audit — PDF Parser (`parse_m68k.py`)

### Critical — Hardcoded override masking parsing bug

- [x] `ARGUMENT COUNT` hardcoded to 8-bit/255 (lines 1411-1419) — generalized to use field width from encoding

### High — Should be data-driven

- [x] `CC_TABLE` hardcoded (lines 61-66) — PMMU CCs are parsed from PDF, standard CCs should be too
- [x] `_extract_movem_direction` gated on `mnemonic == "MOVEM"` (lines 1538-1539) — let field description content drive it
- [x] `_extract_bit_op_size_restriction` gated on `("BTST","BCHG","BCLR","BSET")` (line 1646) — let description drive it
- [x] Bcc excludes CCs `["t","f"]` by hardcoded name (lines 1457-1458) — derive from BRA/BSR being separately parsed
- [x] Shift count range: regex captures groups but never uses them, returns hardcoded 1-8 (lines 1569-1574)
- [x] Shift count fallback: hardcoded field name "i/r", bit positions 11-9, returns hardcoded 1-8 (lines 1580-1593)

### Medium

- [x] `EA_ALL` duplicates `MODE_MAP` — derive from it (lines 56-58)
- [x] `_extract_immediate_range` targets list — iterate all non-structural encoding fields, let descriptions drive extraction
- [x] Memory shift size detection — derive SIZE field position from register-form encoding, check fixed bits in memory-form
- [x] `_derive_processor_min` is a manual if-else chain (lines 1657-1677) — now data-driven from CPU_HIERARCHY
- [x] Opmode table extraction: 3 PDF formats (multi-column, value-description, source/destination) with orphaned arrow merging

## Data-Driven Audit — Round-Trip Tests (`test_m68k_roundtrip.py`)

### High

- [x] CCR/SR immediate forms use hardcoded default sizes `.b`/`.w` instead of KB `sizes` (lines 396-402)
- [x] `_gen_movem_tests` receives `movem_dir` from KB but never uses it — direction-to-mode mapping entirely hardcoded (lines 594-612) — now uses `ea_modes_by_direction` parsed from PDF
- [x] MOVEC only tests `vbr` — KB should enumerate valid control registers (lines 472-479) — now tests all 20 registers from PDF Table 6-1
- [x] `imm` exclusion for bit-op immediate source is procedural, not KB-driven (lines 343-344) — driven by `bit_op_sizes` constraint from KB

### Medium

- [x] Bit-number immediate `#4` arbitrary (line 341) — acceptable test value, not derivable from KB
- [x] Bit-field `{2:8}` offset/width arbitrary (lines 486-498) — acceptable test values
- [x] Branch size `"b"`→`".s"` mapping — now from `vasm_compat.json` `branch_size_map`
- [ ] LINK immediates hardcoded, no `immediate_range` in KB (lines 411-413)
- [x] `"movem"` string literal instead of `m_lower` parameter (lines 597-611)

## Compiler Fingerprinting

- [ ] Inventory available Amiga compilers (ADCD disc, archives) — SAS/C, Lattice, DICE, Aztec/Manx, GCC, etc.
- [ ] Run compilers under vamos to compile test programs at various optimization levels
- [ ] Extract signatures: startup code, function prologues/epilogues, runtime library functions, register conventions
- [ ] Build fingerprint database for auto-identifying compiler/language in unknown binaries

## Knowledge Base

- [ ] Refine OS version tagging — differentiate 570 "1.3" functions into 1.0/1.1/1.2/1.3 if possible
- [ ] Complete hardware register bit definitions (104/245 done)

## Disassembly

- [ ] Select a game binary to begin actual disassembly
