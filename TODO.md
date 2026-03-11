# TODO

## Phase 1: Complete the Knowledge Base

Extract all instruction metadata from the PDF into `m68k_instructions.json`.

### Encodings & Forms (done)
- [x] Opword bit patterns for all 127 instructions
- [x] Extension word fields (displacement, immediate data)
- [x] EA mode tables (src/dst/ea, 020+ markers)
- [x] Syntax forms and operand type patterns
- [x] Constraints (immediate ranges, CC parameterization, direction variants, etc.)

### Condition Code Semantics (new)
- [ ] Parse CC description text from each instruction's "Condition Codes" section
- [ ] Classify each flag effect into semantic rules (result-based, operand-based, operation-specific)
- [ ] Emit structured CC rules per instruction in JSON (not just `*`/`—`/`0`/`1`/`U` markers)

### SP Effects (new)
- [ ] Parse Operation field into structured SP delta expressions
- [ ] Classify: push N, pop N, displacement-adjust, compound (LINK/UNLK), none
- [ ] Emit per-instruction SP effect in JSON

### PC Effects (new)
- [ ] Derive instruction size from encoding structure (opword + extension words)
- [ ] Flag control-flow instructions (branch, jump, return, trap) with target semantics
- [ ] Emit per-instruction PC effect in JSON (advance-by-size, branch, jump, etc.)

## Phase 2: Data-Driven Assembler

Reverse of the disassembler, driven from the same JSON.

- [ ] Operand syntax → EA mode bits (parse register names, addressing modes, immediates)
- [ ] Opword construction from encoding bit patterns + operand fields
- [ ] Extension word generation (displacements, immediate data, bit fields)
- [ ] Size suffix → size field encoding
- [ ] Verify against vasm: assemble with both, binary-diff every instruction × operand × size

## Phase 3: Data-Driven Effect Predictor

Given an instruction + initial state, predict SP delta and CC result from KB rules.

- [ ] SP predictor: consume JSON SP effects, compute stack pointer delta
- [ ] CC predictor: consume JSON CC semantic rules, compute flag values from operands/result
- [ ] PC predictor: next-PC calculation (sequential, branch-taken, branch-not-taken)
- [ ] Verify against machine68k: execute one instruction, compare predicted vs actual SP/CC/PC

## Phase 4: Verification Harness

machine68k (Musashi) as independent oracle for execution semantics.

- [ ] Test generator: for each KB instruction, produce (initial state, binary) pairs
- [ ] Runner: load binary into machine68k, set initial state, execute, capture final state
- [ ] Comparator: check assembler output, disassembler output, and effect predictions against machine68k
- [ ] Coverage tracker: which instructions × sizes × EA modes have been oracle-verified

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
