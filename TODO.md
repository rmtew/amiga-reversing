# TODO

## Current Targets

- GenAm (DevPac 3.18 assembler): `targets/genam/`
- Bloodwych (no-OS game): `targets/bloodwych/`

## Phase 6: Beyond Static Analysis

Static analysis has reached its limits for GenAm at 28.5% core coverage.
The remaining code is reachable only through runtime-dependent dispatch
(callback pointers, input-dependent computed addresses).

### Emulation-Guided Coverage
- [ ] Instrumented vamos execution of GenAm with real source files
- [ ] Coverage feedback loop: emulation traces -> new entry points -> re-analyze
- [ ] Identify dead code: addresses never executed across all input variations

### Data Structure Enumeration
- [ ] String dispatch table at pcref_3f3c: enumerate all 65 directive handlers
- [ ] Computed PEA+RTS dispatch at $7550: enumerate addressing-mode handlers ($16E0-$1D14)
- [ ] Extend jump table pattern recognition for new table formats

### Concolic Execution
- [ ] Symbolic execution with path forking at conditional branches

## Round-Trip Validation

- [ ] GenAm self-assembly: disassemble -> reassemble with GenAm via vamos -> binary diff
- [ ] Re-run round-trip validation for fresh GenAm / Bloodwych output after the shared-analysis and renderer refactors, then classify any remaining binary diffs as formatting churn vs real semantic regressions

## Knowledge Base: Amiga Platform

- [ ] Refine OS version tagging (570 "1.3" functions -> 1.0/1.1/1.2/1.3)
- [ ] Complete hardware register bit definitions (104/245 done)
- [ ] Extend NDK-derived hardware symbol coverage beyond `hardware/custom.i` and `hardware/cia.i` if targets use additional include-backed hardware families, so rendering stays source-accurate without falling back to generic absolute symbols
- [ ] Verify HUNK_OVERLAY format against ADCD primary source

## Future Work

### M68K KB / Executor
- [ ] Add full upstream `RTE` stack/PC/SR semantics extraction to the M68K parser/runtime tables if a target needs it; keep this spec-driven, not executor-hardcoded

### Compiler Fingerprinting
- [ ] Inventory Amiga compilers (SAS/C, Lattice, DICE, Aztec/Manx, GCC)
- [ ] Run under vamos, extract signatures (startup, prologues, runtime)
- [ ] Build fingerprint database for auto-identifying compiler/language

### Analysis Architecture
- [ ] Decide whether the remaining orchestration in `m68k/indirect_analysis.py` should stay as one module or split further from lower-level reusable analysis
- [ ] Add a small number of whole-target integration checks around GenAm / Bloodwych output so renderer and analysis regressions are caught above the unit-test level

### KB Python Integration Debt
- [ ] Replace remaining ad hoc small record dicts in runtime tables with tuple/type-alias forms where the schema is fixed and performance-sensitive

## Tasks Of Interest

- [ ] Investigate any remaining GenAm output drift after the inline-dispatch stale-block fix; triage formatting churn vs improved output
- [ ] Re-review Bloodwych absolute-short symbolization changes with round-trip/reassembly checks
- [ ] Add an integration regression for the contiguous `$VER: GenAm 3.18 (2.8.94)` string rendering
