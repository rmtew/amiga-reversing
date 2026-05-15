# TODO

## Unsorted

- Row selection needs to be more flexible. As up or down cursor key moves the selected row, shift+up or down should
  extend the selection to cover the previous row and the current focus row. This implies there is a concept of focus
  row and selected rows, although I suspect there is a standard UI paradigm for this we can follow. This then applies
  to filtering command palette actions - what ones do we offer? How do they work when presented rows which may or may
  not be applicable to them - there is a value in deprioritising them visually and showing a hint against the row
  why they can't be applied to the selected rows.
  - An example of row selection. The user sees a block of dc.b. He concerts it to longs. Then he selects sub-rows and
    then converts to strings. Maybe other rows are words, others are bytes.
  Proposal: `docs/proposals/001-manual-review-ui-workflows.md`.
- Manual edits in the web UI should appear natural and seamless, not incur loading dialogs and reanalysis.
  When I renamed the label even if it had updated the given row, the action was followed by a interruption with
  reanalysis perhaps happening and loading dialogs. Being able to do edits and changes immediately is a huge improvement
  in user experience and doesn't look bolted on.
  Proposal: `docs/proposals/001-manual-review-ui-workflows.md`.
- Renaming a label shouldn't pop up a browser dialog. It should edit in place.
  Proposal: `docs/proposals/001-manual-review-ui-workflows.md`.
  At time of writing I press 'p' on a label line, select rename label, then a input browser dialog opens.
- Opening a target with no persisted last open location should place the selected row at the entrypoint row and center
  it in the viewport. If we persist project config (given that web UI preferences do not add to the manual edit log)
  we would persist key-bindings, last position and preferences to use for render profiles or assemble/reproduction
  profiles like what disassemblers to try it against.
  Proposal: `docs/proposals/001-manual-review-ui-workflows.md`.
- What assemblers we reproduce against are useful. Currently an EXACT reproduction likely implies that we are using
  our framework assembler, which factors in extra legwork to full file reproduction rather than just content
  reproduction. It will be useful for the user to specify the assembler to use, whether vasm, genam or the framework
  one. Also whether we can find the assembler they want to use (is machine68k installed? is vamos installed? what
  files do we need to run Genam for Amiga just the binary?).
  Proposal: `docs/proposals/002-reproduction-profiles-and-oracles.md`.
- The manual review list currently contains things that the analysis identified. However there is value in the user
  being able to mark rows/ranges and add notes about things they want to come back to, and have them appear in their
  manual review list.
  Proposal: `docs/proposals/001-manual-review-ui-workflows.md`.

## Manual review/editing and analysis state

Proposal: `docs/proposals/001-manual-review-ui-workflows.md`.

Manual editing is now exposed through a shared action catalog used by the Review dialog, listing contexts, command
palette, API, and CLI. Actions are appended to the Manual Action Log and projected into effective metadata instead of
mutating analysis state directly.

  1. An LLM reversing a project should be able to operate it via the API or command-line tools. In this case the
     user will have directed the LLM to work away reversing a target, making use of the tools and data available
     both improving the underlying analysis framework, the C API it exposes and the tooling that provides access.
  2. Web-UI keyboard interaction by a human. For a human the Review dialog is useful to visualise the items they need
     to review. However the current options that can be selects in the dialog are ad-hoc, and we need a better way
     to contextually make them available in the main scrollable target analysis, both as a popup menu for a given
     element and hotkeys.

### WebUI notes

Implemented baseline: selected listing row, keyboard navigation, command palette, reference-follow/back navigation,
manual data-type seed helpers, manual value representations, semantic hint capture, and library-base register seed
helpers. Manual representation now flows through effective metadata into the C analysis policy and source renderer,
with round-trip coverage for rendered-source changes.

Future directions:

- Promote semantic hints for equates and struct offsets into first-class render policy once the C renderer has a clean
  non-text-substitution slot for chosen constants/fields.
- Add UI affordances to inspect existing semantic hints and remove/replace them from the command palette.
- Extend library-base helpers beyond the initial exec.library/A6 path by ranking candidates from observed LVO sets and
  known OpenLibrary/OpenDevice propagation facts.
- Continue enriching C listing element metadata for operand sub-ranges, data literal spans wider than one rendered row,
  comments, and equate definitions so every contextual action can keep element precision after refresh.
- Persist user key-binding overrides only after the command/action model stabilises across more reversing sessions.

## Tracing

Proposal: `docs/proposals/003-runtime-tracing.md`.

- Deferred: WinUAE debugger-assisted tracing.
  - Local WinUAE source is cloned at `resources/clone_common/WinUAE`, but no runnable `winuae64.exe` is present there.
  - Keep the current `amiga_reversing.tools.winuae_session` launcher/startup-sequence helpers as groundwork only.
  - Resume this when a usable WinUAE executable path is available. Then add deterministic `.uae` config generation,
    host-directory mounting, debugger console logging, scripted breakpoints/runs, and trace/memory-state import back into
    analysis facts.

Deferred until IRA-style concerns WRT WinUAE are considered.

## Phase 6: Beyond Static Analysis

Static analysis has reached its limits for GenAm at 28.5% core coverage.
The remaining code is reachable only through runtime-dependent dispatch
(callback pointers, input-dependent computed addresses).

### Emulation-Guided Coverage

Proposal: `docs/proposals/003-runtime-tracing.md`.

- [ ] Instrumented vamos execution of GenAm with real source files
- [ ] Coverage feedback loop: emulation traces -> new entry points -> re-analyze
- [ ] Identify dead code: addresses never executed across all input variations

### Data Structure Enumeration

Proposal: `docs/proposals/006-target-import-and-analysis-architecture.md`.

- [ ] Extend jump table pattern recognition for new table formats

## Round-Trip Validation

Proposal: `docs/proposals/002-reproduction-profiles-and-oracles.md`.

- [ ] Re-run round-trip validation for fresh GenAm / Bloodwych output after the shared-analysis and renderer refactors, then classify any remaining binary diffs as formatting churn vs real semantic regressions

## Knowledge Base: Amiga Platform

Proposal: `docs/proposals/004-amiga-platform-knowledge.md`.

- [ ] Refine OS version tagging (570 "1.3" functions -> 1.0/1.1/1.2/1.3)
- [ ] Complete hardware register bit definitions (104/245 done)
- [ ] Extend NDK-derived hardware symbol coverage beyond `hardware/custom.i` and `hardware/cia.i` if targets use additional include-backed hardware families, so rendering stays source-accurate without falling back to generic absolute symbols
- [ ] Review entries in `knowledge/amiga_ndk_corrections.json` and promote `review_status` from `seeded` to `validated` only when a human has explicitly checked the cited source
- [ ] Add a seed-generation/review flow for corrections so autodoc-derived candidates can be proposed without being silently treated as validated KB
- [ ] Verify HUNK_OVERLAY format against ADCD primary source
- [ ] Add primary-source sample/fixture coverage for `HUNK_OVERLAY`; `vasm` hunk output has no overlay support, so this needs a different oracle or a vetted real sample

## Future Work

### M68K KB / Executor

Proposal: `docs/proposals/005-m68k-generated-coverage.md`.

- [ ] Add full upstream `RTE` stack/PC/SR semantics extraction to generated M68K metadata if a target needs it; keep this spec-driven, not executor-hardcoded
- [ ] Extend the new PDF-driven compare-swap KB semantics through full `CAS2` decode/disasm/executor support; current decoded operand model cleanly supports single-`CAS`, but `CAS2` still needs first-class paired-memory operand modeling

### M68K Assembler Coverage Audit

Proposal: `docs/proposals/005-m68k-generated-coverage.md`.

- [ ] Make the C assembler audit comprehensive over canonical generated forms, not just one representative sample per form
- [ ] Add explicit alias coverage on top of canonical-form coverage so generated syntax aliases are tested separately from canonical forms
- [ ] Generate multiple valid EA samples per canonical `ea` form from KB `EA_MODE_TABLES`, not just the first working mode
- [ ] Extend audit sample generation from the current basic operand classes to full special-form operand synthesis where generated form metadata is not enough on its own
- [ ] Move any remaining audit-side operand guessing into generated C metadata where possible, so the audit stops encoding assembler knowledge locally
- [ ] Add a strict failure for any new canonical generated form that has neither a sample strategy nor an explicit unsupported reason
- [ ] Add a strict failure for any stale explicit unsupported reason once the form becomes sampleable
- [ ] Consider adding a parallel decode/disasm generated-form coverage-contract slice so KB/form drift is checked on both assembler and decoder sides

### Remaining Assembler Coverage Work

Proposal: `docs/proposals/005-m68k-generated-coverage.md`.

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

Proposal: `docs/proposals/005-m68k-generated-coverage.md`.

- [ ] Export any additional generated C tables needed for audit/sample generation from the C metadata pipeline
- [ ] Decide whether special-form operand sample templates should live in generated C metadata instead of coverage helpers
- [ ] Clean up extension-word/form modeling where raw encoding counts exceed canonical form counts (`CHK2/CMP2`, bitfield ops, `CALLM`, PMMU families) so coverage tooling can reason about form support without encoding-level guesswork
- [ ] Replace mnemonic-specific audit overrides with generated canonical syntax metadata where possible
- [ ] Add a small report mode for the C coverage suite so unsupported-form inventory can be viewed without reading test code

### Compiler Fingerprinting

Proposal: `docs/proposals/003-runtime-tracing.md`.

- [ ] Inventory Amiga compilers (SAS/C, Lattice, DICE, Aztec/Manx, GCC)
- [ ] Run under vamos, extract signatures (startup, prologues, runtime)
- [ ] Build fingerprint database for auto-identifying compiler/language

### Analysis Architecture

Proposal: `docs/proposals/006-target-import-and-analysis-architecture.md`.

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
  Proposal: `docs/proposals/005-m68k-generated-coverage.md`.
  - decoder/disassembler generated-form consistency in the C disassembler/IR metadata
  - unsupported special-form implementation vs generated-form cleanup in the C generator pipeline
  - any remaining honest unresolved indirect-call classification work in the analysis path if benchmarks expose avoidable `unknown` cases
