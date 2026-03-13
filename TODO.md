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

## Phase 2: Data-Driven Assembler (done)

Reverse of the disassembler, driven from the same JSON.
`scripts/m68k_asm.py` — 1299 tests, 90 mnemonics, 0 failures, 27 known divergences (imm routing).

- [x] Operand syntax → EA mode bits (parse register names, addressing modes, immediates)
- [x] Opword construction from encoding bit patterns + operand fields
- [x] Extension word generation (displacements, immediate data, bit fields)
- [x] Size suffix → size field encoding
- [x] Verify against vasm: 1273/1300 passed, 27 known divergences, 0 mismatches
- [x] Verify against DevPac GenAm 3.18: 1297/1301 passed, 4 known divergences, 0 mismatches
- [x] Unified oracle test harness: `scripts/test_m68k_oracle.py` (vasm | devpac)
- [x] Per-assembler behavior JSON: `knowledge/asm_vasm.json`, `knowledge/asm_devpac.json`
- [x] Branch/label support with PC-relative displacement calculation
- [x] SR/CCR/USP operand support (separate KB instructions)
- [x] Auto-routing aliases (ADD #imm → ADDI, DBRA → DBF, BLO → BCS)

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
- [x] Condition test definitions: `cc_test_definitions` in KB `_meta` (parser-asserted, PDF pp 90-91 Table 3-19)
- [x] Source sign-extension: `source_sign_extend` from PDF description + opmode_table (ADDA, SUBA, MOVEA, CMPA)
- [x] Transfer layout: `transfer_layout` from PDF description (MOVEP: stride=2, byte_order=big_endian)
- [x] Bounds-check trap condition: `trap_condition` from PDF operation text (CHK: signed, 0 ≤ Dn ≤ Source)

## Phase 4: Verification Harness (done)

machine68k (Musashi) as independent oracle for execution semantics.
`scripts/test_m68k_execution.py` — 4870 tests, 119 mnemonics, 0 failures.
`scripts/m68k_compute.py` — KB-driven compute engine (CC/SP/result prediction, condition evaluator).

- [x] Test generator: KB-driven discovery of testable instructions, deterministic test values
- [x] Runner: instruction hook captures post-execution state without sentinel interference
- [x] Comparator: predicted CC/SP/PC vs machine68k actual, per-flag reporting
- [x] Compute module extracted: `m68k_compute.py` — pure functions, no machine68k dependency

### CC verification (54 mnemonics)
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
- [x] CCR/SR manipulation: ANDI/ORI/EORI/MOVE to CCR, ANDI/ORI/EORI to SR (7 mnemonics) — KB `ccr_op`/`sr_op` bypass, `imm_bit_*`/`source_bit` rules
- [x] MOVEQ (1 mnemonic) — KB `imm_dn` form type with signed byte immediate range

### SP verification (9 mnemonics)
- [x] PEA, JSR, BSR, RTS, LINK, UNLK (9 tests)
- [x] MOVEM (4 tests) — push/pop via `-(A7)`/`(A7)+`, SP delta = register_count × size
- [x] RTR (1 test) — return + restore CCR from stack, KB `loaded_from_stack` CC rule

### Register/flow verification (10 mnemonics)
- [x] An-destination: ADDA, SUBA, MOVEA (.W + .L) — KB `source_sign_extend` + `cc_result_bits` for .W sign-extension
- [x] EXG: 3 forms (Dx/Dy, Ax/Ay, Dx/Ay) — KB `operation_type=swap`
- [x] LEA: indirect, displaced, absolute — KB `compute_formula`
- [x] MOVE from SR — verify CCR bits in result
- [x] NOP, BRA, JMP — PC advancement / unconditional flow

### Condition test verification (46 mnemonics)
- [x] Scc: 16 conditions × 12 CCR states — KB `cc_test_definitions` + `evaluate_cc_test()`
- [x] Bcc: 14 conditions × 12 CCR states (taken/not-taken PC) — KB `cc_test_definitions`
- [x] DBcc: 16 conditions × scenarios (cc-true/loop/exhaust) — KB `cc_test_definitions`

### Peripheral/bounds verification (2 mnemonics)
- [x] MOVEP: memory→register byte-striped read — KB `transfer_layout` (stride, byte_order)
- [x] CHK: non-trapping bounds check — KB `trap_condition` (signed comparison, lower/upper bounds)

### Untestable (12 KB entries)
- 6 privileged: MOVE USP, MOVE to SR, RESET, RTE, STOP, PTRAPcc
- 4 exception-generating: TRAP, TRAPV, ILLEGAL, BKPT
- 2 partially tested: CHK (trapping path needs exception handler), MOVEP (reg→mem needs memory capture)

### Audits
- [x] Three audits passed — no hardcoded M68K knowledge, no silent fallbacks
- [x] All KB fields consumed: cc_semantics, operation_type, sp_effects, pc_effects, shift_count_modulus, rotate_extra_bits, compute_formula, bit_modulus, size_by_ea_category, cc_result_bits, ccr_bit_positions
- [x] Tier 5 audit: compute semantics moved from hardcoded handlers to KB `compute_formula`
- [x] Tier 5 audit: overflow rules specialized, fill/implicit defaults replaced with hard errors
- [x] Tier 5 audit: 020+ variant skip moved from string heuristic to KB `processor_020` flag
- [x] Tier 6 audit: CCR bit positions from KB, implicit_operand hard error, Track B citations on MODE_MAP/CPU_HIERARCHY/SIZE_MAP/coprocessor
- [x] Tier 6 audit: size_by_ea_category eliminates silent .b assembly-failure skip for bit tests
- [x] Tier 6 audit: EXTB source_bits derived from PDF bit number, cc_result_bits checks all 5 flags
- [x] Tier 7 audit: sign-extension from KB `source_sign_extend`, MOVEP from KB `transfer_layout`, CHK from KB `trap_condition`
- [x] Tier 7 audit: dead code removed (MOVEP reg→mem), assembly failure warnings added (Scc/Bcc/DBcc)

## Phase 5: Symbolic Executor (in progress)

KB-driven abstract interpretation engine for static analysis of disassembled code.
`scripts/m68k_executor.py` — block discovery, demand-driven disassembly, structured EA decoding.
Foundation: `scripts/m68k_compute.py` (verified against Musashi with 4870 tests).

- [x] `predict_pc()`: KB `pc_effects` + `opword_bytes` for branch target resolution
- [x] EA decoder: structured `Operand` from opcode bits via KB `ea_mode_encoding` + `ea_brief_ext_word`
- [x] EA resolver: translate Operand to effective address from abstract state
- [x] Abstract state model: `CPUState` — register file + CCR, layout from KB `movem_reg_masks` + `ccr_bit_positions`
- [x] Basic block discovery: two-pass flow-following with demand-driven disassembly (handles mixed code/data)
- [x] Cross-reference tracking: branch, jump, call, fallthrough xrefs with conditional flag
- [x] Branch target extraction: KB `displacement_encoding` (word/long signals), KB encoding fields for JMP/JSR EA
- [x] CC family resolution: KB `cc_parameterized` prefix lookup (Bcc, Scc, DBcc, PTRAPcc)
- [x] Audit: no hardcoded M68K knowledge — opword size, register counts, flag names, CC families, displacement signals all from KB
- [x] Memory model: `AbstractMemory` — sparse byte-granularity map, big-endian read/write at b/w/l sizes
- [x] State propagation: `propagate_states()` — BFS walk, per-instruction abstract execution, conservative join at merge points
- [x] Instruction effects: MOVE/MOVEA/MOVEQ, LEA, ADD/SUB/AND/OR/EOR, CLR, EXG, SWAP, EXT, SP effects
- [x] Verification: 8 tests (memory r/w, copy, join, MOVEQ+LEA through memory, ADD, CLR, merge, EXG)
- [ ] Integration with entity system: feed discovered xrefs into `entities.jsonl`

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
