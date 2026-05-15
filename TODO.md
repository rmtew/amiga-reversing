# TODO

## Manual review/editing and analysis state

We added manual editing to the UI. This records logged actions against the backend that let us rename labels and
change data types, and other forms of interaction. Currently this are likely only exposed through the Review dialog
via the buttons there for each flagged review item. While the buttons are a good start, the ability to edit will
need to be exposed in two different ways.

  1. An LLM reversing a project should be able to operate it via the API or command-line tools. In this case the
     user will have directed the LLM to work away reversing a target, making use of the tools and data available
     both improving the underlying analysis framework, the C API it exposes and the tooling that provides access.
  2. Web-UI keyboard interaction by a human. For a human the Review dialog is useful to visualise the items they need
     to review. However the current options that can be selects in the dialog are ad-hoc, and we need a better way
     to contextually make them available in the main scrollable target analysis, both as a popup menu for a given
     element and hotkeys.

### LLM notes

Largely covered above. Is it better to use command-line or API? The API caches analysis and reduces access delays,
which would imply API. And the benefit of using the same API as the user via the web UI is obvious.

### WebUI notes

When something is selected in either the Review dialog or Navigate dialog, the code jumps to the given row and
the row temporarily highlights. In order for keyboard driven interaction to be viable we likely need to have the
concept of a selected row and even selection of elements within the row.

- Up/down cursor keys may move the selected row one line up or down.
- Home/End/Page up/Page down would move the viewport but not the selected row.
- The user may wish to change the representation of value (perhaps operand offset, perhaps immediate value, perhaps
  data literal, and other applicable elements). This might be showing a character constant like `'    '` instead of
  `$20202020`. It might be hex like `$2020` instead of '  '. It might be showing binary like `%00100000` instead of
  hex `$20`. "    " is the same as '    ', so our assembler should support both and perhaps it might be a rendering
  policy for which is used.
- The user may wish to change the data type of a block (byte, word, long, ..).

Then there is the interaction with the selected row. Review already exposes the ability to turn data into strings or
other data types which shows the support is there to build on. We need both the ability for the user to define
key-bindings and a decent set of defaults (the latter we can build out and should not auto-populate).

The best initial option is to adopt the command palette concept. We might simply bind it to 'p' for a start. It might
have two modes, one is contextual to editing current row and the other is the list of all possible actions that are
currently valid. Similarly how in VS Code "Control+P" brings up the options prefixed with '>' and then backspace
returns it to the file browser that "Shift+Control+P" brings up, as we are not a text-editor we can have 'p' bring
up options with a prefix indicating the context it was invoked in and use backspace to drop the contextual filter
and allow all currently valid actions matched.

### Case study: Resource

One of the most polished interactive disassemblers on the Amiga was Resource. Some notes follow on how it worked and
how we might do it better today. This relates to how basic post-analysis direction works for both LLM and user with
web UI.

#### Library calls, structs, key-bindings and analysis potential

The user has the ability to assign OS call equates. Pressing 'e' on a `JSR -m(an)` would then display the LVO symbol
in place of the offset `-m` and track it as an EQU to emit. Other default key-bindings might cover other core libraries.
However we have resources that developers in the 90's did not have. We also have type analysis which we can build on
rather than simple value mappings, and in fact there might be more value to knowing that `an` contains a given library
base and tracing back to where it is assigned, and propagating that to where it is accessed and used following what
our original auto-analysis should do for it's analysis. Similarly to how changing an orphaned code block from data to
code should trigger analysis for it. We know what the registers should be for a call too, which comes into triggered
analysis and type propagation value for the user.

Pressing 'T' was bound to the "Task control struct". While users may have custom key-bindings, having them for even
a small range of libraries or structs gets unwieldy due to limitations. We could do it better with a contextually
related auto-complete based matching. Let's say the user is looking at an immediate value, the takeaway here is that
the user may want to find equates that are of that value, or LVOs for different libraries, or even offsets for
structs that we have indexed (like those from the platform's system includes).

There's a lot of potential here for keeping it simple. We may not benefit from a context menu on these rows, we might
have a contextual command-palette that only offers selections based on the context. The core of our interactions in
all of our UI might be command-palette driven with user key-bindings. Where in Resource to change the representation
or a data type of an operand, the user presses '1', '2'.. to refer to which, then presses a key. Without that focus
it likely defers to the first operand. But for the most part, likely the default is simply the first because that's
just the nature of what it needs to refer to.

### Label/RS name/EQU/... navigation

Pressing the right cursor key on a label followed a symbol to it's location in the file, and pushes the source row onto
the navigation stack. This is an easy simple default key-binding we should adopt. And the left cursor key returned back
up the navigation stack. Currently in our web UI CTRL+click on a label, RS value or EQU IIRC opens the details for that
in the relevant natigation dialog section. It makes sense to perhaps have CTRL+right cursor allow keyboard navigation
and selection of those details (I think escape already dismisses it so the CTRL-click handler may work with  some
contextual key-bindings).

SHIFT+CTRL+up cursor jumped up to the previous label (logically the down cursor variation went down). This is a useful
way to navigate, whatever key-bindings we choose. Having this and other relative navigation options in the command
palette (next relative hunk up/down) is valuable.

## Tracing

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
