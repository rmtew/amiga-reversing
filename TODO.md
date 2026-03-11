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

## Phase 2: Data-Driven Assembler

Reverse of the disassembler, driven from the same JSON.

- [ ] Operand syntax → EA mode bits (parse register names, addressing modes, immediates)
- [ ] Opword construction from encoding bit patterns + operand fields
- [ ] Extension word generation (displacements, immediate data, bit fields)
- [ ] Size suffix → size field encoding
- [ ] Verify against vasm: assemble with both, binary-diff every instruction × operand × size

## Phase 3: Data-Driven Effect Predictor (done)

Given an instruction + initial state, predict SP delta and CC result from KB rules.

- [x] SP predictor: consume JSON SP effects, compute stack pointer delta (including `load_from_reg` via `reg_state`)
- [x] CC predictor: consume JSON CC semantic rules, compute flag values from operands/result
- [x] PC predictor: next-PC calculation (sequential size from disassembler, branch targets)
- [x] Operation type classifier: Phase 11 in parser — classifies PDF `operation` text into structured types
- [x] Shift/rotate properties: `shift_count_modulus` and `rotate_extra_bits` extracted from PDF description/operation

## Phase 4: Verification Harness (in progress)

machine68k (Musashi) as independent oracle for execution semantics.
`scripts/test_m68k_execution.py` — 2817 tests, 28 mnemonics, 0 failures.

- [x] Test generator: KB-driven discovery of testable instructions, deterministic test values
- [x] Runner: instruction hook captures post-execution state without sentinel interference
- [x] Comparator: predicted CC/SP/PC vs machine68k actual, per-flag reporting

### CC verification (22 mnemonics)
- [x] ALU register-register: ADD, ADDX, SUB, SUBX, CMP, AND, OR, EOR, MOVE, NEG, NEGX, NOT, CLR, TST (14 mnemonics, 1512 tests)
- [x] Shift/rotate: ASL, ASR, LSL, LSR, ROL, ROR, ROXL, ROXR (8 mnemonics, 1296 tests)
- [ ] Multiply: MULS, MULU — need `multiply` compute handler
- [ ] Divide: DIVS/DIVSL, DIVU/DIVUL — need `divide` compute handler + division-specific CC rules
- [ ] Bit test: BTST, BCHG, BCLR, BSET — need `bit_zero` rule + `#imm,Dn` form setup
- [ ] Misc: SWAP, EXT/EXTB already tested; TAS needs `msb_operand` rule
- [ ] BCD: ABCD, SBCD, NBCD — need `decimal_carry`/`decimal_borrow` rules
- [ ] EA mode expansion: ADDI, ADDQ, SUBI, SUBQ, ANDI, ORI, EORI, CMPI, CMPM (need `#imm,Dn` form)

### SP verification (6 mnemonics)
- [x] PEA, JSR, BSR, RTS, LINK, UNLK (9 tests)
- [ ] MOVEM (push/pop multiple registers)
- [ ] RTR (return + restore CCR)

### Audits
- [x] Three audits passed — no hardcoded M68K knowledge, no silent fallbacks
- [x] All KB fields consumed: cc_semantics, operation_type, sp_effects, pc_effects, shift_count_modulus, rotate_extra_bits

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
