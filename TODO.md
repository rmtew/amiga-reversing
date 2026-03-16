# TODO

## Completed Phases

### Phase 1: Knowledge Base (done)
M68K instruction metadata from PDF into `m68k_instructions.json`.
127 instructions: encodings, EA modes, forms, constraints, CC semantics,
SP effects, PC effects, compute formulas, shift/rotate/overflow rules.

### Phase 2: Data-Driven Assembler (done)
`m68k/m68k_asm.py` -- 1299 tests, 90 mnemonics, verified against vasm + DevPac.

### Phase 3: Data-Driven Effect Predictor (done)
`m68k/m68k_compute.py` -- KB-driven compute engine (CC/SP/result prediction).

### Phase 4: Verification Harness (done)
`scripts/test_m68k_execution.py` -- 4870 tests, 119 mnemonics, 0 failures (Musashi oracle).

### Phase 5: Symbolic Executor (done — static analysis complete)
`m68k/m68k_executor.py` — KB-driven abstract interpretation engine.
`m68k/analysis.py` — shared analysis pipeline with `analyze_hunk()`.

Key capabilities:
- Block discovery, state propagation, conservative joins
- Jump table detection (patterns A-D), indirect target resolution
- Per-caller context-sensitive analysis with nested callee execution
- OS library call identification (39 calls, exec + dos)
- Subroutine summaries: preservation, SP delta, produced return values
- Summary-aware scratch invalidation
- Multi-entry propagation seeding (3109/3110 blocks with exit states)
- Sound init memory join semantics
- Store pass for app base memory values (219 across 3 passes)
- Heuristic subroutine scan, hint block validation

GenAm results: 34.4% core (3110 blocks, 7393 instructions), 20.6% hints.
279 subroutines, 25 named, 39 library calls resolved.

Static analysis limits reached: remaining 12 unresolved dispatch sites are
runtime-dependent (callback pointers, input-dependent function pointers).

Test suite: `py -m pytest tests/` -- 1903 tests in ~2s.

### Disassembly Generator (done)
`scripts/gen_disasm.py` -> `disasm/genam.s` (vasm-compatible, zero errors).

## Phase 6: Beyond Static Analysis (current focus)

Static analysis has reached its limits at 34.4% core coverage. The remaining
code is reachable only through runtime-dependent dispatch (callback pointers,
input-dependent computed addresses). Three approaches to drive toward 100%:

### Emulation-Guided Coverage (highest priority)
- [ ] Instrumented vamos execution of GenAm with real source files
  - Run `vamos GenAm source.s` with PC trace collection
  - Collect every executed address -> ground-truth code map
  - Diff against static analysis to identify missed code vs dead code
  - Feed verified addresses as entry points (not hints -- proven reachable)
  - Vary inputs (directives, addressing modes, error cases) for path coverage
- [ ] Coverage feedback loop: emulation traces -> new entry points -> re-analyze
- [ ] Identify dead code: addresses never executed across all input variations

### Data Structure Enumeration
- [ ] String dispatch table at pcref_3f3c: 65 assembler directives
  - Table data is in code section, entries are self-relative handler offsets
  - Enumerate all entries to discover handler code without resolving runtime index
  - Currently hint-only -- will become core once upstream dispatch resolves
- [ ] Computed PEA+RTS dispatch at $7550: addressing mode handlers ($16E0-$1D14)
  - Table of handler offsets indexed by instruction encoding fields
  - Enumerate table entries to discover all handler entry points
- [ ] Extend jump table pattern recognition for new table formats

### Concolic Execution (future)
- [ ] Symbolic execution with path forking at conditional branches
  - Track symbolic constraints, explore both paths at branches on unknown values
  - Naturally handles input-dependent dispatch by exploring all branch outcomes
  - KB-driven executor is 80% of the infrastructure -- needs branch forking + constraint tracking

## Existing Infrastructure

### vasm
- [x] Built locally (`ext/vasm/`), used as assembler backend and oracle

### Round-Trip Validation
- [x] GenAm -> disasm -> vasm -> binary-diff = 0 bytes, 0 relocs different
- [ ] GenAm self-assembly: disassemble -> reassemble with GenAm via vamos -> binary diff

## Knowledge Base — Amiga Platform
- [ ] Refine OS version tagging (570 "1.3" functions -> 1.0/1.1/1.2/1.3)
- [ ] Complete hardware register bit definitions (104/245 done)
- [ ] Verify HUNK_OVERLAY format against ADCD primary source

## Future Work

### Compiler Fingerprinting
- [ ] Inventory Amiga compilers (SAS/C, Lattice, DICE, Aztec/Manx, GCC)
- [ ] Run under vamos, extract signatures (startup, prologues, runtime)
- [ ] Build fingerprint database for auto-identifying compiler/language
