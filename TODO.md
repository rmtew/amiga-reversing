# TODO

## Completed Phases

### Phase 1: Knowledge Base (done)
M68K instruction metadata from PDF into `m68k_instructions.json`.
127 instructions: encodings, EA modes, forms, constraints, CC semantics,
SP effects, PC effects, compute formulas, shift/rotate/overflow rules.

### Phase 2: Data-Driven Assembler (done)
`m68k/m68k_asm.py` -- 1299 tests, 90 mnemonics, verified against vasm + DevPac.
- [ ] Add local assembler support for `PACK` / `UNPK` so these forms can be round-tripped from source text instead of only tested via oracle bytes
- [ ] Fix local assembler support for `LINK.L`; `assemble_instruction("link.l ...")` currently emits the word form instead of the long form

### Phase 3: Data-Driven Effect Predictor (done)
`m68k/m68k_compute.py` -- KB-driven compute engine (CC/SP/result prediction).

### Phase 4: Verification Harness (done)
`scripts/oracle_m68k_exec.py` -- 4870 tests, 119 mnemonics, 0 failures (Musashi oracle).

### Phase 5: Symbolic Executor (done -- static analysis complete)
`m68k/m68k_executor.py` -- KB-driven abstract interpretation engine.
`m68k/analysis.py` -- shared analysis pipeline with `analyze_hunk()`.

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
- Relocated code detection: bootstrap copy-and-jump patterns,
  secondary entry discovery, payload source as core entry

GenAm results: 28.5% core (2581 blocks, 6112 instructions), 37.9% hints.
242 subroutines, 25 named, 39 library calls resolved.

Bloodwych results: 7.9% core (2979 blocks, 8663 instructions), 12.2% hints.
310 subroutines, auto-detected relocation ($5C -> $400).

Static analysis limits reached: remaining 12 unresolved dispatch sites are
runtime-dependent (callback pointers, input-dependent function pointers).

Test suite: `py -m pytest tests/` -- 1954 tests in ~2s.

### Disassembly Generator (done)
`scripts/gen_disasm.py` -> `targets/<name>/<name>.s`.
PC-relative code references labeled (LEA to instruction starts).
Hint/core overlap filtering prevents output corruption.

## Current Targets

- GenAm (DevPac 3.18 assembler): `targets/genam/`
- Bloodwych (no-OS game): `targets/bloodwych/`

## Phase 6: Beyond Static Analysis (current focus)

Static analysis has reached its limits for GenAm at 28.5% core coverage.
The remaining code is reachable only through runtime-dependent dispatch
(callback pointers, input-dependent computed addresses). Three approaches
to drive toward 100%:

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
- [ ] Re-run round-trip validation for fresh GenAm / Bloodwych output after the shared-analysis and renderer refactors, then classify any remaining binary diffs as formatting churn vs real semantic regressions

## Knowledge Base — Amiga Platform
- [ ] Refine OS version tagging (570 "1.3" functions -> 1.0/1.1/1.2/1.3)
- [ ] Complete hardware register bit definitions (104/245 done)
- [ ] Verify HUNK_OVERLAY format against ADCD primary source

## Future Work

### Compiler Fingerprinting
- [ ] Inventory Amiga compilers (SAS/C, Lattice, DICE, Aztec/Manx, GCC)
- [ ] Run under vamos, extract signatures (startup, prologues, runtime)
- [ ] Build fingerprint database for auto-identifying compiler/language
- [ ] Add local assembler support for full-extension EA syntax such as `(od,[bd,An,Xn])` and `([bd,An,Xn],od)` / PC-relative variants so these 68020 forms can be round-tripped from source text instead of only tested via oracle bytes

### Analysis Architecture
- [x] Extract jump-table-local constant/base reconstruction into shared KB-driven analysis modules (`constant_evaluator.py`, `indirect_core.py`, `subroutine_summary.py`, `address_reconstruction.py`, `table_recovery.py`, `indirect_analysis.py`)
- [ ] Decide whether the remaining orchestration in `m68k/indirect_analysis.py` should stay as one module or split further from lower-level reusable analysis
- [ ] Add a small number of whole-target integration checks around GenAm / Bloodwych output so renderer and analysis regressions are caught above the unit-test level

### KB Python Integration Debt
- [x] Extract low-level decode and operand-resolution primitives out of [`m68k/m68k_executor.py`](C:/Data/R/git/claude-repos/amiga-reversing2/m68k/m68k_executor.py)
  - `Operand`, `DecodedOps`, `decode_ea`, `decode_instruction_ops`, `xf`, `extract_branch_target` now live in [`m68k/instruction_primitives.py`](C:/Data/R/git/claude-repos/amiga-reversing2/m68k/instruction_primitives.py)
  - `resolve_ea` and full-extension EA resolution now live in [`m68k/operand_resolution.py`](C:/Data/R/git/claude-repos/amiga-reversing2/m68k/operand_resolution.py)
  - Indirect-analysis helpers no longer import executor for low-level operand plumbing
- [x] Finish flow enum normalization across consumers
  - `instruction_flow()` now returns `FlowType` directly
  - Closed flow-domain comparisons now use `FlowType` enums across executor, indirect analysis/core, jump tables, subroutine scan/summary, analysis, operands, hint validation, and validation
  - Remaining `xref.type` strings are a separate xref data surface, not instruction-flow KB leakage
- [x] Remove the broad root runtime surface from production where possible
  - Production code now uses consumer-specific generated modules (`runtime_m68k_decode`, `runtime_m68k_disasm`, `runtime_m68k_asm`, `runtime_m68k_analysis`, `runtime_m68k_compute`, `runtime_m68k_executor`)
  - [`knowledge/runtime_m68k.py`](C:/Data/R/git/claude-repos/amiga-reversing2/knowledge/runtime_m68k.py) is now effectively an aggregate/test surface, not a production integration layer
- [x] Reduce repeated decode orchestration around `decode_instruction_operands()` / `decode_destination()`
  - Added explicit instruction-level helpers in [`m68k/instruction_decode.py`](C:/Data/R/git/claude-repos/amiga-reversing2/m68k/instruction_decode.py): `decode_inst_operands()` and `decode_inst_destination()`
  - Converted the main hotspot callers and secondary production paths: [`m68k/address_reconstruction.py`](C:/Data/R/git/claude-repos/amiga-reversing2/m68k/address_reconstruction.py), [`m68k/analysis.py`](C:/Data/R/git/claude-repos/amiga-reversing2/m68k/analysis.py), [`m68k/constant_evaluator.py`](C:/Data/R/git/claude-repos/amiga-reversing2/m68k/constant_evaluator.py), [`m68k/indirect_core.py`](C:/Data/R/git/claude-repos/amiga-reversing2/m68k/indirect_core.py), [`m68k/jump_tables.py`](C:/Data/R/git/claude-repos/amiga-reversing2/m68k/jump_tables.py), [`m68k/os_calls.py`](C:/Data/R/git/claude-repos/amiga-reversing2/m68k/os_calls.py), [`m68k/subroutine_summary.py`](C:/Data/R/git/claude-repos/amiga-reversing2/m68k/subroutine_summary.py), [`m68k/table_recovery.py`](C:/Data/R/git/claude-repos/amiga-reversing2/m68k/table_recovery.py), [`disasm/data_access.py`](C:/Data/R/git/claude-repos/amiga-reversing2/disasm/data_access.py), [`disasm/operands.py`](C:/Data/R/git/claude-repos/amiga-reversing2/disasm/operands.py), [`disasm/substitutions.py`](C:/Data/R/git/claude-repos/amiga-reversing2/disasm/substitutions.py)
  - [`disasm/decode.py`](C:/Data/R/git/claude-repos/amiga-reversing2/disasm/decode.py) now uses the instruction-shaped path as its primary boundary; remaining raw decode calls are just the low-level primitives themselves
- [x] Push remaining mnemonic/condition-family lookup logic upstream into generated runtime where viable
  - Generated analysis runtime now provides direct `LOOKUP_CANONICAL` and `LOOKUP_NUMERIC_CC_PREFIXES`
  - [`m68k/instruction_kb.py`](C:/Data/R/git/claude-repos/amiga-reversing2/m68k/instruction_kb.py) is reduced to direct table lookup plus the minimal numeric `#...` suffix rule
- [ ] Replace remaining ad hoc small record dicts in runtime tables with tuple/type-alias forms where the schema is fixed and performance-sensitive
- [x] Continue flattening consumers onto the dedicated generated runtime modules where it genuinely removes cross-module shape knowledge, especially remaining generic lookup/helper paths
- [x] Flatten the main disassembler runtime accessor layer
  - [`m68k/m68k_disasm.py`](C:/Data/R/git/claude-repos/amiga-reversing2/m68k/m68k_disasm.py) now reads `runtime_m68k_disasm` directly instead of routing through a `_load_kb_*` helper layer
  - Companion assembler flattening is now also done in [`m68k/m68k_asm.py`](C:/Data/R/git/claude-repos/amiga-reversing2/m68k/m68k_asm.py)
- [x] Consolidate repeated tiny runtime accessors (`_kb_*`, `_runtime_*`) where they no longer add validation or semantic value
- [x] Remove any remaining production reads of canonical-shape instruction fields from runtime consumers; keep canonical JSON for generation/testing only
  - Production `m68k/` and `disasm/` code no longer reads canonical instruction bag fields like `forms`, `constraints`, `ea_modes`, `pc_effects`, or `encodings`
  - Added an architecture test to keep that boundary from regressing
- [ ] Add one explicit generated-runtime shape test per KB module (`runtime_m68k.py`, `runtime_os.py`, `runtime_hunk.py`, `runtime_naming.py`) so direct-import cleanup does not regress silently

## Tasks Of Interest

- [ ] Investigate any remaining GenAm output drift after the inline-dispatch stale-block fix; the core semantic issue is fixed, but remaining diff should be triaged into formatting churn vs improved output
- [ ] Re-review Bloodwych absolute-short symbolization changes with round-trip/reassembly checks to confirm they are semantic improvements, not just prettier text
- [ ] Add an integration regression for the contiguous `$VER: GenAm 3.18 (2.8.94)` string rendering so that improved string emission stays stable
