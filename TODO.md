# TODO

## Unsorted

Some of these may be in non-updated source in targets/, they need checking for existing fixes.

- Emulation-based tracing:
  - Local `WinUAE` usage (currently cloned to `resources/clone_common/WinUAE`):
    - It is unclear why some things are the way they are in the disassembled source code. Orphaned code blocks are one
      example of this. We should be able to use `WinUAE` (providing configuration on disk and on command-line and so on)
      and drive sessions from the command-line to take advantage of a) ability to run a target in a realistic setting
      b) to use the debugger to analyse memory and other state c) direct execution using breakpoint and more.
- Codebase auditing/global refactoring:
  - A loose approach has been taken to using static string values and string comparison as an implementation approach
    and while some of that has been cleaned up, it would be good to do a comprehensive pass over the codebase. We should
    be using bitflags or enums to replace that.
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
- [ ] Add full upstream `RTE` stack/PC/SR semantics extraction to generated M68K metadata if a target needs it; keep this spec-driven, not executor-hardcoded
- [ ] Extend the new PDF-driven compare-swap KB semantics through full `CAS2` decode/disasm/executor support; current decoded operand model cleanly supports single-`CAS`, but `CAS2` still needs first-class paired-memory operand modeling

### M68K Assembler Coverage Audit
- [ ] Make the C assembler audit comprehensive over canonical generated forms, not just one representative sample per form
- [ ] Add explicit alias coverage on top of canonical-form coverage so generated syntax aliases are tested separately from canonical forms
- [ ] Generate multiple valid EA samples per canonical `ea` form from KB `EA_MODE_TABLES`, not just the first working mode
- [ ] Extend audit sample generation from the current basic operand classes to full special-form operand synthesis where generated form metadata is not enough on its own
- [ ] Move any remaining audit-side operand guessing into generated C metadata where possible, so the audit stops encoding assembler knowledge locally
- [ ] Add a strict failure for any new canonical generated form that has neither a sample strategy nor an explicit unsupported reason
- [ ] Add a strict failure for any stale explicit unsupported reason once the form becomes sampleable
- [ ] Consider adding a parallel decode/disasm generated-form coverage-contract slice so KB/form drift is checked on both assembler and decoder sides

### Remaining Assembler Coverage Work
- [ ] Implement `MOVEC` control-register syntax and remove its explicit unsupported forms from C assembler coverage tests
- [ ] Implement `MOVES` forms and remove their explicit unsupported forms from C assembler coverage tests
- [ ] Implement `CHK2/CMP2` forms and remove their explicit unsupported forms from C assembler coverage tests
- [ ] Implement bitfield forms (`BFCHG/BFCLR/BFEXTS/BFEXTU/BFFFO/BFINS/BFSET/BFTST`) and remove their explicit unsupported forms from C assembler coverage tests
- [ ] Implement `CAS/CAS2` forms and remove their explicit unsupported forms from C assembler coverage tests
- [ ] Implement long multiply/divide register-pair syntax (`MULS/MULU/DIVS/DIVU` long forms) and remove their explicit unsupported forms from C assembler coverage tests
- [ ] Implement `RTD` immediate extension encoding and remove its explicit unsupported form from C assembler coverage tests
- [ ] Implement `STOP` immediate extension encoding and remove its explicit unsupported form from C assembler coverage tests
- [ ] Implement `TRAPcc` forms and remove their explicit unsupported forms from C assembler coverage tests
- [ ] Implement `MOVE16` forms and remove their explicit unsupported forms from C assembler coverage tests
- [ ] Implement FPU save/restore forms (`FSAVE/FRESTORE`) and remove their explicit unsupported forms from C assembler coverage tests
- [ ] Implement PMMU forms (`PFLUSH/PFLUSHA/PFLUSHR/PMOVE/PRESTORE/PSAVE/PScc/PTRAPcc/PVALID/PBcc/PDBcc`) and remove their explicit unsupported forms from C assembler coverage tests
- [ ] Implement generic coprocessor forms (`cpBcc/cpDBcc/cpGEN/cpRESTORE/cpSAVE/cpScc/cpTRAPcc`) and remove their explicit unsupported forms from C assembler coverage tests

### M68K Generated Metadata / Audit Plumbing
- [ ] Export any additional generated C tables needed for audit/sample generation from the C metadata pipeline
- [ ] Decide whether special-form operand sample templates should live in generated C metadata instead of coverage helpers
- [ ] Clean up extension-word/form modeling where raw encoding counts exceed canonical form counts (`CHK2/CMP2`, bitfield ops, `CALLM`, PMMU families) so coverage tooling can reason about form support without encoding-level guesswork
- [ ] Replace mnemonic-specific audit overrides with generated canonical syntax metadata where possible
- [ ] Add a small report mode for the C coverage suite so unsupported-form inventory can be viewed without reading test code

### Compiler Fingerprinting
- [ ] Inventory Amiga compilers (SAS/C, Lattice, DICE, Aztec/Manx, GCC)
- [ ] Run under vamos, extract signatures (startup, prologues, runtime)
- [ ] Build fingerprint database for auto-identifying compiler/language

### Analysis Architecture
- [ ] Decide whether any remaining indirect-analysis orchestration in C should stay monolithic or split further from lower-level reusable analysis
- [ ] Add a small number of whole-target integration checks around GenAm / Bloodwych output so renderer and analysis regressions are caught above the unit-test level
- [ ] Keep strict `mypy` coverage focused on the Python web/orchestration layer and C-backed adapters
- [ ] Add first-class support for non-AmigaDOS/custom-track disks in the import path; current strict importer only accepts AmigaDOS disks
- [ ] Extract structured file-signature KB from primary or project-trusted sources so packer/cruncher detection is KB-driven instead of omitted
- [ ] Replace sector-image non-DOS heuristics with real raw-track/custom-loader format decoding once we ingest non-ADF track data or add custom-format descriptors to the KB
- [ ] Extend typed executable structure analysis beyond resident/library classification to parse Exec library init/vector structure and surface NDK-driven exported function names in the executable view
- [ ] Tighten the remaining resident/library/device structured-entrypoint work now that bootblocks and resident auto-init vectors are modeled: finish Exec init/vector executable-layout parsing from primary-source metadata for any still-missing formal entry code, make emitted/exported entry labels version-aware from the OS KB, and add whole-target regressions that pin real exported handler coverage/naming on resident binaries
- [ ] If we import seeded target-local facts from external reverse-engineering sources, keep them in an optional import workflow and never make tests, normal target rendering, or precommit depend on the external source being present
- [ ] Add Add Project UI flow for manual raw-binary targets that requires user-supplied load address and entrypoint, using the new strict `source_binary.json` raw-binary source kind
- [ ] Auto-create non-DOS loader stage targets only when bootloader analysis can materialize concrete stage bytes plus load address and entrypoint, so inferred-only regions stay honest
- [ ] Extend runtime-built Amiga resident/device analysis for targets such as `amiga_disk_carrier-command-1994-kixx-budget__amiga_hunk_devs__ramdrive.device_2c146d8c`, where resident/device structures and dispatch code are copied and relocated before `AddDevice`; keep any source refresh gated on clean direct rebuild or explicitly classified relocation semantics.
- [ ] Keep the mojibake check in `amiga_reversing.tools.check_mojibake` tight and data-oriented; if more broken encodings appear, extend the explicit pattern list with focused regression tests rather than broad punctuation bans
- [ ] Continue the remaining M68K/disasm audit slices beyond the assembler coverage work:
  - decoder/disassembler generated-form consistency in the C disassembler/IR metadata
  - unsupported special-form implementation vs generated-form cleanup in the C generator pipeline
  - any remaining honest unresolved indirect-call classification work in the analysis path if benchmarks expose avoidable `unknown` cases
