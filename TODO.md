# TODO

## Phase 6: Beyond Static Analysis

Static analysis has reached its limits for GenAm at 28.5% core coverage.
The remaining code is reachable only through runtime-dependent dispatch
(callback pointers, input-dependent computed addresses).

### Emulation-Guided Coverage
- [ ] Instrumented vamos execution of GenAm with real source files
- [ ] Coverage feedback loop: emulation traces -> new entry points -> re-analyze
- [ ] Identify dead code: addresses never executed across all input variations

### Data Structure Enumeration
- [ ] Extend jump table pattern recognition for new table formats

## Round-Trip Validation

- [ ] Re-run round-trip validation for fresh GenAm / Bloodwych output after the shared-analysis and renderer refactors, then classify any remaining binary diffs as formatting churn vs real semantic regressions

## Knowledge Base: Amiga Platform

- [ ] Refine OS version tagging (570 "1.3" functions -> 1.0/1.1/1.2/1.3)
- [ ] Complete hardware register bit definitions (104/245 done)
- [ ] Extend NDK-derived hardware symbol coverage beyond `hardware/custom.i` and `hardware/cia.i` if targets use additional include-backed hardware families, so rendering stays source-accurate without falling back to generic absolute symbols
- [ ] Review entries in `knowledge/amiga_ndk_corrections.json` and promote `review_status` from `seeded` to `validated` only when a human has explicitly checked the cited source
- [ ] Add a seed-generation/review flow for corrections so autodoc-derived candidates can be proposed without being silently treated as validated KB
- [ ] Verify HUNK_OVERLAY format against ADCD primary source
- [ ] Add primary-source sample/fixture coverage for `HUNK_OVERLAY`; `vasm` hunk output has no overlay support, so this needs a different oracle or a vetted real sample

## Future Work

### M68K KB / Executor
- [ ] Add full upstream `RTE` stack/PC/SR semantics extraction to the M68K parser/runtime tables if a target needs it; keep this spec-driven, not executor-hardcoded
- [ ] Extend the new PDF-driven compare-swap KB semantics through full `CAS2` decode/disasm/executor support; current decoded operand model cleanly supports single-`CAS`, but `CAS2` still needs first-class paired-memory operand modeling

### M68K Assembler Coverage Audit
- [ ] Make the audit comprehensive over canonical runtime forms, not just one representative sample per form
- [ ] Add explicit alias coverage on top of canonical-form coverage so runtime syntax aliases are tested separately from canonical forms
- [ ] Generate multiple valid EA samples per canonical `ea` form from KB `EA_MODE_TABLES`, not just the first working mode
- [ ] Extend audit sample generation from the current basic operand classes to full special-form operand synthesis where runtime form types are not enough on their own
- [ ] Move any remaining audit-side operand guessing into generated/runtime metadata where possible, so the audit stops encoding assembler knowledge locally
- [ ] Add a strict failure for any new canonical runtime form that has neither a sample strategy nor an explicit unsupported reason
- [ ] Add a strict failure for any stale explicit unsupported reason once the form becomes sampleable
- [ ] Consider adding a parallel decode/disasm runtime coverage-contract slice so KB/runtime form drift is checked on both assembler and decoder sides

### Remaining Assembler Coverage Work
- [ ] Implement `MOVEC` control-register syntax and remove its explicit unsupported forms from `tests/test_asm_runtime_coverage.py`
- [ ] Implement `MOVES` forms and remove their explicit unsupported forms from `tests/test_asm_runtime_coverage.py`
- [ ] Implement `CHK2/CMP2` forms and remove their explicit unsupported forms from `tests/test_asm_runtime_coverage.py`
- [ ] Implement bitfield forms (`BFCHG/BFCLR/BFEXTS/BFEXTU/BFFFO/BFINS/BFSET/BFTST`) and remove their explicit unsupported forms from `tests/test_asm_runtime_coverage.py`
- [ ] Implement `CAS/CAS2` forms and remove their explicit unsupported forms from `tests/test_asm_runtime_coverage.py`
- [ ] Implement long multiply/divide register-pair syntax (`MULS/MULU/DIVS/DIVU` long forms) and remove their explicit unsupported forms from `tests/test_asm_runtime_coverage.py`
- [ ] Implement `RTD` immediate extension encoding and remove its explicit unsupported form from `tests/test_asm_runtime_coverage.py`
- [ ] Implement `STOP` immediate extension encoding and remove its explicit unsupported form from `tests/test_asm_runtime_coverage.py`
- [ ] Implement `TRAPcc` forms and remove their explicit unsupported forms from `tests/test_asm_runtime_coverage.py`
- [ ] Implement `MOVE16` forms and remove their explicit unsupported forms from `tests/test_asm_runtime_coverage.py`
- [ ] Implement FPU save/restore forms (`FSAVE/FRESTORE`) and remove their explicit unsupported forms from `tests/test_asm_runtime_coverage.py`
- [ ] Implement PMMU forms (`PFLUSH/PFLUSHA/PFLUSHR/PMOVE/PRESTORE/PSAVE/PScc/PTRAPcc/PVALID/PBcc/PDBcc`) and remove their explicit unsupported forms from `tests/test_asm_runtime_coverage.py`
- [ ] Implement generic coprocessor forms (`cpBcc/cpDBcc/cpGEN/cpRESTORE/cpSAVE/cpScc/cpTRAPcc`) and remove their explicit unsupported forms from `tests/test_asm_runtime_coverage.py`

### M68K Runtime / Audit Plumbing
- [ ] Export any additional runtime tables needed for audit/sample generation to `m68k_kb/runtime_m68k_asm.py` the same way `OPERAND_MODE_TABLES` is now exported
- [ ] Decide whether special-form operand sample templates should live in generated runtime metadata instead of the pytest coverage helper
- [ ] Clean up extension-word/runtime form modeling where raw encoding counts exceed canonical form counts (`CHK2/CMP2`, bitfield ops, `CALLM`, PMMU families) so coverage tooling can reason about form support without encoding-level guesswork
- [ ] Replace mnemonic-specific audit overrides with generated canonical syntax metadata where possible
- [ ] Add a small report mode for the runtime coverage suite so unsupported-form inventory can be viewed without reading test code

### Compiler Fingerprinting
- [ ] Inventory Amiga compilers (SAS/C, Lattice, DICE, Aztec/Manx, GCC)
- [ ] Run under vamos, extract signatures (startup, prologues, runtime)
- [ ] Build fingerprint database for auto-identifying compiler/language

### Analysis Architecture
- [ ] Decide whether the remaining orchestration in `m68k/indirect_analysis.py` should stay as one module or split further from lower-level reusable analysis
- [ ] Add a small number of whole-target integration checks around GenAm / Bloodwych output so renderer and analysis regressions are caught above the unit-test level
- [ ] Expand strict `mypy` coverage beyond the current typed helper/core slice, shared analysis helpers, typed reusable analysis modules (`m68k/indirect_core.py`, `m68k/indirect_analysis.py`, `m68k/analysis.py`), and typed early disassembly helpers (`disasm/discovery.py`, `disasm/metadata.py`, `disasm/hunks.py`, `disasm/session.py`, `disasm/instruction_rows.py`, `disasm/emitter.py`) into the next M68K/disassembly modules without introducing `Any` shims
- [ ] Add first-class support for non-AmigaDOS/custom-track disks in the import path; current strict importer only accepts AmigaDOS disks
- [ ] Extract structured file-signature KB from primary or project-trusted sources so packer/cruncher detection is KB-driven instead of omitted
- [ ] Replace sector-image non-DOS heuristics with real raw-track/custom-loader format decoding once we ingest non-ADF track data or add custom-format descriptors to the KB
- [ ] Extend typed executable structure analysis beyond resident/library classification to parse Exec library init/vector structure and surface NDK-driven exported function names in the executable view
- [ ] Tighten the remaining resident/library/device structured-entrypoint work now that bootblocks and resident auto-init vectors are modeled: finish Exec init/vector executable-layout parsing from primary-source metadata for any still-missing formal entry code, make emitted/exported entry labels version-aware from the OS KB, and add whole-target regressions that pin real exported handler coverage/naming on resident binaries
- [ ] If we import seeded target-local facts from external reverse-engineering sources, keep them in an optional import workflow and never make tests, normal target rendering, or precommit depend on the external source being present
- [ ] Add Add Project UI flow for manual raw-binary targets that requires user-supplied load address and entrypoint, using the new strict `source_binary.json` raw-binary source kind
- [ ] Auto-create non-DOS loader stage targets only when bootloader analysis can materialize concrete stage bytes plus load address and entrypoint, so inferred-only regions stay honest
- [ ] Keep the mojibake check in `scripts/check_mojibake.py` tight and data-oriented; if more broken encodings appear, extend the explicit pattern list with focused regression tests rather than broad punctuation bans
- [ ] Continue the remaining M68K/disasm audit slices beyond the assembler coverage work:
  - decoder/disassembler runtime-form consistency in `m68k/instruction_decode.py` and `m68k/m68k_disasm.py`
  - unsupported special-form implementation vs runtime-shape cleanup in `kb/runtime_builder.py`
  - any remaining honest unresolved indirect-call classification work in the analysis path if benchmarks expose avoidable `unknown` cases
