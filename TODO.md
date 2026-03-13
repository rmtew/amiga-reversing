# TODO

## Phase 1: Complete the Knowledge Base

Extract all instruction metadata from the PDF into `m68k_instructions.json`.

### Encodings & Forms (done)
- [x] Opword bit patterns for all 127 instructions
- [x] Extension word fields (displacement, immediate data)
- [x] EA mode tables (src/dst/ea, 020+ markers)
- [x] Syntax forms and operand type patterns
- [x] Constraints (immediate ranges, CC parameterization, direction variants, etc.)

### Condition Code Semantics (done)
- [x] Parse CC description text from each instruction's "Condition Codes" section
- [x] Classify each flag effect into semantic rules (result-based, operand-based, operation-specific)
- [x] Emit structured `cc_semantics` per instruction in JSON (127/127 classified, hard-fail on unrecognized)

### SP Effects (done)
- [x] Parse Operation field into structured SP delta expressions
- [x] Classify: decrement N, increment N, displacement-adjust, load/save reg, compound (LINK/UNLK)
- [x] Emit per-instruction `sp_effects` in JSON (9 instructions, hard-fail on unmatched SP clauses)

### PC Effects (done)
- [x] Derive base instruction size from encoding structure (opword + extension words)
- [x] Flag control-flow instructions (branch, jump, call, return, trap) with conditional flag
- [x] Emit per-instruction `pc_effects` in JSON (22 control flow, no hardcoded mnemonic names)

## Phase 2: Data-Driven Assembler (in progress)

Reverse of the disassembler, driven from the same JSON.
`scripts/m68k_asm.py` — 1295 tests, 88 mnemonics, 0 failures.

- [x] Operand syntax → EA mode bits (parse register names, addressing modes, immediates)
- [x] Opword construction from encoding bit patterns + operand fields
- [x] Extension word generation (displacements, immediate data, bit fields)
- [x] Size suffix → size field encoding
- [x] Verify against vasm: assemble with both, binary-diff every instruction × operand × size
- [x] Verify against DevPac GenAm 3.18: 1245/1270 passed, 25 divergences (all valid alternate encodings)
- [x] Per-assembler behavior JSON: `knowledge/asm_vasm.json`, `knowledge/asm_devpac.json`
- [x] Branch/label support with PC-relative displacement calculation
- [x] SR/CCR/USP operand support (separate KB instructions)
- [ ] Auto-routing aliases (ADD #imm,<ea> → ADDI, DBRA → DBF)

## Phase 3: Data-Driven Effect Predictor (done)

Given an instruction + initial state, predict SP delta and CC result from KB rules.

- [x] SP predictor: consume JSON SP effects, compute stack pointer delta (including `load_from_reg` via `reg_state`)
- [x] CC predictor: consume JSON CC semantic rules, compute flag values from operands/result
- [x] PC predictor: next-PC calculation (sequential size from disassembler, branch targets)
- [x] Operation type classifier: Phase 11 in parser — classifies PDF `operation` text into structured types
- [x] Shift/rotate properties: `shift_count_modulus` and `rotate_extra_bits` extracted from PDF description/operation
- [x] Compute formulas: `compute_formula` extracted from PDF Operation text (63 instructions)
- [x] Specialized overflow rules: `overflow_add/sub/neg/negx/multiply` (parser-asserted, Track B)
- [x] Carry/borrow detection, shift carry/MSB semantics (parser-asserted, Track B)
- [x] Shift fill behavior: `fill` field on variants from PDF description (sign/zero/rotate)
- [x] Combined mnemonic variants: `processor_020` flag derived from form data
- [x] Implicit operands: `implicit_operand` extracted from PDF Operation text
- [x] Size-by-EA-category: `size_by_ea_category` extracted from PDF description (register=long, memory=byte)
- [x] CC result width override: `cc_result_bits` extracted from PDF CC descriptions (SWAP: 32-bit despite Size=Word)
- [x] Sign-extend formula: `sign_extend` with `source_bits_by_size` from PDF description text
- [x] CCR bit positions: `ccr_bit_positions` in KB `_meta` (parser-asserted, PDF p21 Figure 1-8)

## Phase 4: Verification Harness (in progress)

machine68k (Musashi) as independent oracle for execution semantics.
`scripts/test_m68k_execution.py` — 4142 tests, 54 mnemonics, 0 failures.

- [x] Test generator: KB-driven discovery of testable instructions, deterministic test values
- [x] Runner: instruction hook captures post-execution state without sentinel interference
- [x] Comparator: predicted CC/SP/PC vs machine68k actual, per-flag reporting

### CC verification (46 mnemonics)
- [x] ALU register-register: ADD, ADDX, SUB, SUBX, CMP, AND, OR, EOR, MOVE, NEG, NEGX, NOT, CLR, TST (14 mnemonics, 1512 tests)
- [x] Shift/rotate: ASL, ASR, LSL, LSR, ROL, ROR, ROXL, ROXR (8 mnemonics, 1296 tests)
- [x] Multiply: MULS, MULU (2 mnemonics, 72 tests) — KB `compute_formula` + `overflow_multiply` rule
- [x] Divide: DIVS, DIVU (2 mnemonics, 84 tests) — KB `compute_formula` + `division_overflow`/quotient CC rules
- [x] Bit test: BTST, BCHG, BCLR, BSET (4 mnemonics, 192 tests) — KB `compute_formula` (bit_test/change/clear/set) + `bit_zero` rule
- [x] EA mode `#imm,Dn`: ADDI, ADDQ, ANDI, CMPI, EORI, ORI, SUBI, SUBQ (8 mnemonics, 540 tests) — `imm_dn` form type
- [x] Direct Dn form: SWAP, EXT (3 mnemonics, 108 tests) — KB `sign_extend` + `exchange` formulas, `cc_result_bits`, `["dn"]` form type
- [x] Memory compare: CMPM (1 mnemonic, 108 tests) — `postinc_postinc` form type with memory test infrastructure
- [x] Address register compare: CMPA (1 mnemonic, 72 tests) — `dn_an` form type, KB `source_sign_extend` + `cc_result_bits`
- [x] TAS (1 mnemonic, 36 tests) — KB `msb_operand` CC rule, `test` compute formula, `single_op` form type
- [x] BCD: ABCD, SBCD, NBCD (3 mnemonics, 108 tests) — KB `add_decimal`/`subtract_decimal` compute formulas, `decimal_carry`/`decimal_borrow` CC rules

### SP verification (9 mnemonics)
- [x] PEA, JSR, BSR, RTS, LINK, UNLK (9 tests)
- [x] MOVEM (4 tests) — push/pop via `-(A7)`/`(A7)+`, SP delta = register_count × size
- [x] RTR (1 test) — return + restore CCR from stack, KB `loaded_from_stack` CC rule

### Audits
- [x] Three audits passed — no hardcoded M68K knowledge, no silent fallbacks
- [x] All KB fields consumed: cc_semantics, operation_type, sp_effects, pc_effects, shift_count_modulus, rotate_extra_bits, compute_formula, bit_modulus, size_by_ea_category, cc_result_bits, ccr_bit_positions
- [x] Tier 5 audit: compute semantics moved from hardcoded handlers to KB `compute_formula`
- [x] Tier 5 audit: overflow rules specialized, fill/implicit defaults replaced with hard errors
- [x] Tier 5 audit: 020+ variant skip moved from string heuristic to KB `processor_020` flag
- [x] Tier 6 audit: CCR bit positions from KB, implicit_operand hard error, Track B citations on MODE_MAP/CPU_HIERARCHY/SIZE_MAP/coprocessor
- [x] Tier 6 audit: size_by_ea_category eliminates silent .b assembly-failure skip for bit tests
- [x] Tier 6 audit: EXTB source_bits derived from PDF bit number, cc_result_bits checks all 5 flags

## Existing Infrastructure

### vasm Bootstrap
- [x] Get vasm source, build locally (ext/vasm/)
- [ ] Document supported directives, pseudo-ops, and hunk output capabilities
- [x] Write minimal test programs to verify round-trip: source → assemble → binary
- [x] Use vasm as the assembler backend for test oracle
- [x] Identify limits/bugs as we push on edge cases (FPU, coprocessor, addressing modes)
- [ ] Document any patches we apply
- [ ] Derive assembler rule metadata from vasm discovery mode → `vasm.json` schema

### Disassembler & Round-Trip
- [x] Build M68K disassembler — test-driven, using knowledge base
- [x] Build test oracle — assemble → disassemble → reassemble → binary diff (1804 tests, 110/126 mnemonics)
- [x] Derive M68K condition-family canonicalisation from KB data (including PMMU condition tables)
- [ ] Round-trip validation tooling per CLAUDE.md: reassemble with vasm, binary-diff against original

### Data-Driven Audit — Round-Trip Tests
- [x] Bit-number immediate `#4` arbitrary — acceptable test value, not derivable from KB
- [x] Bit-field `{2:8}` offset/width arbitrary — acceptable test values
- [x] Branch size `"b"`→`".s"` mapping — now from `vasm_compat.json`
- [x] LINK immediates — now from KB `immediate_range` (extension word displacement extraction)
- [x] `"movem"` string literal — now uses `m_lower` parameter

## Future Work

### Compiler Fingerprinting
- [ ] Inventory available Amiga compilers (SAS/C, Lattice, DICE, Aztec/Manx, GCC, etc.)
- [ ] Run compilers under vamos to compile test programs at various optimization levels
- [ ] Extract signatures: startup code, prologues/epilogues, runtime library functions
- [ ] Build fingerprint database for auto-identifying compiler/language in unknown binaries

### Knowledge Base — Amiga Platform
- [ ] Refine OS version tagging — differentiate 570 "1.3" functions into 1.0/1.1/1.2/1.3
- [ ] Complete hardware register bit definitions (104/245 done)

### Disassembly
- [ ] Select a game binary to begin actual disassembly
