# Proposal 014: Source-Converging Manual Action Surface

Status: Draft. The capability matrix is accepted as the working map, but this
proposal remains draft until the open 014 implementation issues are closed and
the matrix is updated with their final support state.

This proposal defines the full manual-edit and command surface needed for LLM
and human reversing to move rendered target source toward human-quality
reconstructed source.

Proposal 010 proved the agentic loop harness: inspect, execute through normal
commands, verify, and report. GenAm work then exposed the next layer: the loop
can only be as useful as the source facts it can edit through supported Manual
Action Log commands. If a human reverser can reasonably improve the source, the
project needs a durable manual action, command-catalog exposure, loop access,
and verifier for that improvement.

## Clean Target Model

The desired surface is capability parity across the source model:

```text
auto-analysis fact or rendered-source construct
  -> durable target identity
  -> human manual edit need
  -> Manual Action Log action
  -> command catalog entry
  -> loop candidate/action
  -> verifier
  -> rendered source closer to recovered original intent
```

The loop must not gain private powers. It should use the same command catalog
and Manual Action Log paths as UI/manual workflows. If a capability is missing,
the correct result is a precise missing-capability report and an implementation
issue, not a temporary script or direct metadata write.

## Source-Converging Work

Source-converging work improves the rendered source in ways a human reverser
would recognize:

- clearer function, label, global, app-slot, and data names;
- named constants and equates instead of unexplained immediates;
- domain-appropriate immediate representations;
- code/data/string/table/structure classification;
- typed fields, structure layouts, and register-base facts;
- API/library semantics propagated through calls, arguments, return values, and
  stored state;
- review items resolved with type-specific evidence;
- comments only for concrete semantic discoveries that do not have a better
  structured representation.

Proof actions, placeholder notes, and "note that this exists" edits are out of
scope. They exercise the harness but do not converge the target source.

## Coverage Matrix

The audit below is based on current code paths in:

- `amiga_reversing/disasm/manual_actions.py`
- `amiga_reversing/disasm/manual_action_catalog.py`
- `amiga_reversing/disasm/effective_metadata.py`
- `amiga_reversing/disasm/target_metadata.py`
- `amiga_reversing/reversing_loop.py`
- `src/m68k_render_ir.c`, `src/platform_file_lib.c`, and source model headers
- focused command/source tests under `tests/`

| Fact family | Auto-analysis / source model support | Rendered-source effect | Human manual edit need | Durable identity now | Manual Action Log now | Command catalog now | Loop now | Verifier now | Gap / issue |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Source labels and function entry labels | Facts v2 code starts, control targets, policy `seeded_code_labels`, `seeded_code_entrypoints`, absolute labels | `loc_*`, `abs_*`, entry labels and symbolic refs | Rename, create, remove, or change scope for code labels when xrefs/behavior justify the name | Listing row locator plus source/runtime label payloads; row index still appears as provenance only | Create/remove/rename/change scope labels | `label.rename` for label elements; review label actions | Parameterized label rename only; no autonomous candidate ranking | Label projection, semantic reload, round-trip in label-rename path | Finish autonomous selection and already-renamed skipping in `014-006` |
| Data/global symbols | `SeededEntityMetadata.name`, app-slot names, absolute/code labels, and rendered symbolic data refs | Replaces anonymous data labels and global slots with semantic names at definitions and use sites | Rename/create/remove data symbols, global data labels, and referenced data names from xrefs | Seeded data identity is hunk + source range; durable rename identity for existing data/global symbol is not specified | Data seeds can carry `name`; no first-class data/global rename action | No row/element data-symbol rename/add/edit command | None | Seed projection can render names when supplied; rename/use-site verifier absent | Add data/global symbol naming in `014-014-data-global-symbol-naming.md` |
| Code/data classification seeds | Facts v2 decode/data spans; review items for orphan code, unreconciled data, suspicious decode | Reclassifies instructions/data and emitted directives | Classify a range as code or data, or correct a wrong classification | Hunk + source range; review item id for review-originated seeds | Create/remove manual seed | Row/range/review seed commands for code, raw, byte, word, long, string, scalar table, pointer table | Not selected autonomously | Pending analysis refresh plus round-trip expectation; action-specific loop verifier incomplete | Complete verifier/planner coverage in `014-005` and `014-006` |
| Structured data roles | C policy supports roles including string, pointer table, lookup/scalar table, copper list, palette, bitmap, sound sample, audio table, sprite, string control stream | Emits structured `dc.*`/strings/tables and navigation semantics | Choose the specific data role, unit, encoding, and range shape | Hunk + source range in `SeededEntityMetadata` | Generic data seed can carry `data_role`, `unit`, `encoding` | Catalog exposes only raw/string/scalar_table/pointer_table plus byte/word/long units | None | Partial source/render tests for some roles; no complete command/verifier map | Add full role coverage in `014-007-data-role-command-coverage.md` |
| Comments and review notes | Policy entry comments render; review notes create review items only when tracked | Comments in source/listing; notes in review workflow | Add semantic comment only when no structured fact can represent the discovery; add/edit/clear review notes for workflow state | Hunk + source range plus comment/note ids | Create/remove comments; add/edit/clear notes | `comment.edit`, `review_note.*` | Comment path exists but is not source-converging unless no structured action fits | Manual log, semantic reload, projected comment; no source-value verifier needed for note-only | Keep as fallback-only; planner must not prefer it in `014-006` |
| Immediate representation | Render policy has manual representations; source data supports numeric/string expressions | Hex/binary/character/string for data; selected hex/binary/character display for instruction immediates | Choose operand/data literal representation when the display carries domain meaning | Hunk + source range + element provenance; operand-scoped representations now preserve `operand_index` | Create/remove manual representation | `representation.choose/hex/binary/character` on immediates and data literals | Representation command verifier exists; autonomous candidate selection remains in `014-006` | Manual log hash/count, semantic reload, rendered text, and round-trip tests cover data literals and instruction immediates | Planner ranking/selection remains in `014-006-loop-planner-command-selection.md` |
| Equates/constants | Source model supports constants/EQU; NDK constants are searchable | Replaces magic values with named constants and emits/uses EQU where needed | Add/edit/rename/remove a constant and bind use sites to it | No target-local equate identity | `create_manual_semantic_hint` can record an equate candidate, but effective metadata/rendering does not consume it | `semantic.equate.*` candidates for matching immediate values | None | Catalog append test only; no rendered-source effect | Add target equate actions/projection in `014-009-equate-constant-editing.md` |
| LVO/API semantics | NDK libraries/LVOs, render lookup platform calls, call summaries and API arg analysis | `_LVO*` symbols, library call summaries, typed args/returns, app-slot propagation | Confirm library base, LVO function, API argument/return semantics, and propagated stored state | LVO immediate element exists; API semantic identity not complete | Semantic hints can record LVO candidates but are not consumed; register seeds can seed a library base | `semantic.lvo.*` hint commands; `semantic.library_base.exec` for A6 LVO context only | None | Append tests only for hints; register seed render test exists | Add consumed API/register semantic actions in `014-010-api-register-semantic-actions.md` |
| Register/base facts | `entry_register_seeds` support library base and struct pointer; render policy consumes them | Base-relative references become library/struct-aware | Add/remove register base facts with explicit lifetime/evidence | Entry offset + register + kind; not enough for all base lifetimes | Create/remove manual register seed | Only hard-coded exec.library A6 helper | None | Manual register seed render test exists; catalog coverage narrow | Expand identity/commands/verifiers in `014-010-api-register-semantic-actions.md` |
| App/base-relative slots and RSSET layout regions | App-slot refs, app-slot analysis, regions/gaps/field gaps/suggestions, `rsset_layout_regions`, named layouts | `RSSET`/`RS.*`, `app_0234(a6)` names, typed field paths | Add/edit/rename/remove slots, regions, sizes, storage kinds, semantic types, parser roles, and layout gaps | App-slot context has symbol/displacement/base/access; durable region identity is not specified | No app-slot or RSSET-region manual action | No app-slot rename/add/edit command | None | Auto-analysis tests only | Add app-slot/RSSET editing in `014-011-app-slot-rsset-editing.md` |
| Custom structs, fields, and typed accesses | `custom_structs`, RSSET regions, typed accesses, unresolved typed gaps, type-flow analysis | Struct field refs, typed field paths, gap navigation | Add/edit/rename/remove structs and fields; resolve typed gaps/accesses | Struct/field names and offsets exist in metadata; command identity absent | No manual struct/field action | No typed-access or field-gap edit command | None | Auto-analysis/navigation tests only | Add structure/type/field editing in `014-012-structure-field-editing.md` |
| Runtime/execution views and loader ranges | `execution_views`, runtime address ranges, runtime view starts, absolute labels | ORG/runtime labels and copied-stage source | Add/edit/remove runtime views for copied or relocated code/data when auto-analysis lacks evidence | Metadata supports execution views and absolute labels; command identity absent | Absolute labels can be created through label path; no execution-view action | Label rename only | None | Source/reproduction tests exist; no manual view verifier | Add correction/view actions in `014-013-correction-and-view-actions.md` |
| Auto-analysis corrections and suppressions | `target_corrections.json`, `suppressed_seeded_items`, reproduction mismatches, blockers | Removes wrong imported/seeded facts and unblocks source render | Suppress or override target-specific auto facts only when upstream analysis is not objectively wrong for a whole class | Suppression identity is hunk + addr + seeded item kind | No Manual Action Log action for suppressing auto facts | Review actions can acknowledge/remove manual annotations, not suppress auto facts | None | Review/reproduction checks only | Add durable correction/suppression action in `014-013-correction-and-view-actions.md` |
| Importer/analysis defects | Target import and parser logic derives target type, bootblock, resident, library/device, autoinit, and seeded facts | Corrects all affected targets by improving auto-analysis output | Fix importer/parser/analyzer upstream when a whole class of targets is objectively detected or parsed wrong | Source artifact and regression fixture identity, not per-target manual identity | Not a Manual Action Log action | Not a command catalog edit | Loop stops with implementation issue | Regression tests plus affected render/reproduction checks | Keep out of manual correction path; track as importer/analyzer bugs, or split from `014-013` when discovered |
| Review items and typed resolutions | Manual review items for conflicts, malformed logs, orphan code, unreconciled data, suspicious decode, reproduction mismatches, blockers, review notes | Clears blockers or records decisions | Resolve only with type-specific evidence and verifier | Review item id + evidence fingerprint | Resolve review item; review note actions | Review item actions for current kinds | Generic inspect uses review candidates; no source-value ranking | Type-specific verifiers incomplete | Complete through `014-005` and `014-006` |

Important audit finding: semantic hints are currently append-only projection
state. They are not consumed by `effective_metadata.py` and do not yet change
rendered source. Equate, LVO, and struct-offset hint commands therefore cannot
be treated as source-converging until they project into effective metadata and
have rendered-source verification.

Implementation observation from `014-008`: listing row ordinals are not durable
identities. A backend navigation test previously compared navigation entries to
`enumerate(rows)` and failed when emitted `row_index`/navigation identity did
not match list position. Tests should assert durable listing identities such as
hunk/address/summary, or explicit projected `row_index` when the contract under
test is row-index stability.

## Principles

- Build from the source model outward. Do not add commands just because one
  target exposed a local need.
- Every command needs a durable target identity that survives projection
  rebuilds.
- Every command needs a verifier: semantic reload, projection/rendered text,
  round-trip exactness, or a type-specific oracle.
- Manual Action Log remains the durable intervention model.
- Command catalog exposure is the supported automation surface.
- Loop planning ranks source-converging actions and reports why skipped actions
  were not chosen.
- Missing command support is a blocker, not permission for scripts or direct
  metadata writes.

## Implementation Slices

1. Build the source-convergence capability matrix. (`014-001`)
2. Define or fill durable target identities for editable source constructs.
   (`014-002`)
3. Add missing Manual Action Log actions. (`014-003`, with concrete capability
   issues `014-007` through `014-014`)
4. Expose supported actions through the command catalog. (`014-004`)
5. Add verifiers for every action family. (`014-005`)
6. Teach the loop planner to use command-catalog capabilities instead of
   bespoke proof paths.
7. Run a GenAm trial that performs a non-comment source-converging action and
   stops only on the next precise missing capability.

## Status Discipline

- Keep this proposal in Draft while any required 014 issue remains open.
- When an implementation issue closes, update the matrix row with final Manual
  Action Log, command catalog, loop, and verifier state.
- Do not close the proposal while any supported source-converging command lacks
  a durable identity or verifier.

## Non-Goals

- No private agent mutation APIs.
- No direct target metadata writes outside command/manual-action paths.
- No unsupported temporary scripts as a substitute for command coverage.
- No automatic decompiler promise.
- No broad speculative edit without local evidence and a verifier.

## Acceptance Criteria

- The matrix covers all current auto-analysis fact families and rendered-source
  constructs that a human reverser would edit.
- Each supported source-converging edit has Manual Action Log, command catalog,
  loop, and verifier coverage.
- Each unsupported but required edit has a specific issue with identity,
  command, and verifier requirements.
- Agent instructions point agents to the matrix and require missing-capability
  reports instead of workarounds.
- A target loop can continue with real source-converging work until it reaches a
  documented missing capability.
