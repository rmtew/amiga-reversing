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
| Data/global symbols | `SeededEntityMetadata.name`, app-slot names, absolute/code labels, and rendered symbolic data refs | Replaces anonymous data labels and global slots with semantic names at definitions and use sites | Rename/create/remove data symbols, global data labels, and referenced data names from xrefs | Data row identity is hunk + source range; seeded-entity rename/remove identity is `(hunk, addr)` with optional end/source provenance; referenced data use-sites use the target hunk/offset from internal runtime-address refs and preserve existing use-site symbols as previous-name context | Data seeds can carry `name`; `rename_data_symbol` projects data-row, referenced data, and seeded-entity name overrides; seeded data symbol removal uses `suppress_seeded_item` | `row.seed.data.named`, `element.seed.data.named`, `range.seed.data.named`, and `review.seed.data.named` create named raw data seeds; data rows and internal `data_ref` elements expose `data_symbol.rename`; seeded entity rows also expose `data_symbol.remove` | Planner recognizes explicit data-symbol rename/remove candidates, skips already-satisfied projected names/removals, and mines internal `data_ref` listing elements into autonomous referenced-data rename candidates while skipping projected manual data-symbol names and matching existing use-site symbols | Seed projection can render names when supplied; manual replay, effective metadata, command payload, listing annotation, command execution, rendered definition/use-site-name/removal, existing-symbol context, and exact direct-rebuild tests cover data-row/seeded-entity rename/remove plus internal referenced data command routing; broader global verifier absent | Add use-site/global workflows in `014-014-data-global-symbol-naming.md` |
| Code/data classification seeds | Facts v2 decode/data spans; review items for orphan code, unreconciled data, suspicious decode | Reclassifies instructions/data and emitted directives | Classify a range as code or data, or correct a wrong classification | Hunk + source range; review item id for review-originated seeds; Manual Action Log `seed_id` for removals | Create/remove manual seed | Row/range/review seed commands for code, raw, byte, word, long, string, scalar table, pointer table; `manual_seed_conflict` review items can remove a conflicting seed by `seed_id` | Generic inspect can select review-item seed commands for orphan code and data/decode review candidates, accepts explicit range seed candidates with durable range locators, and mines obvious ASCII data rows into `row.seed.data.string` candidates while skipping projected manual string seeds; broader listing seed candidate feed remains | Pending analysis refresh plus round-trip expectation; action-specific loop verifier incomplete | Complete verifier/planner coverage in `014-005` and `014-006` |
| Structured data roles | C policy supports roles including string, pointer table, lookup/scalar table, copper list, palette, bitmap, sound sample, audio table, sprite, string control stream | Emits structured `dc.*`/strings/tables and navigation semantics | Choose the specific data role, unit, encoding, and range shape | Hunk + source range in `SeededEntityMetadata` | Generic data seed carries `data_role`, `unit`, `encoding` | Row/range/review catalogs expose raw data plus all supported source-rendered data roles | Planner mines obvious null-terminated printable ASCII data rows into string role candidates and accepts explicit `range.seed.data.*` candidates; broader role inference remains open in `014-006` | Per-role tests prove Manual Action Log semantic reload, rendered metadata projection, and exact direct rebuild | Complete in `014-007-data-role-command-coverage.md` |
| Comments and review notes | Policy entry comments render; review notes create review items only when tracked | Comments in source/listing; notes in review workflow | Add semantic comment only when no structured fact can represent the discovery; add/edit/clear review notes for workflow state | Hunk + source range plus comment/note ids | Create/remove comments; add/edit/clear notes | `comment.edit`, `review_note.*` | Comment path exists but is not source-converging unless no structured action fits | Manual log, semantic reload, projected comment; no source-value verifier needed for note-only | Keep as fallback-only; planner must not prefer it in `014-006` |
| Immediate representation | Render policy has manual representations; source data supports numeric/string expressions | Hex/binary/character/string for data; selected hex/binary/character display for instruction immediates | Choose operand/data literal representation when the display carries domain meaning | Hunk + source range + element provenance; operand-scoped representations now preserve `operand_index` | Create/remove manual representation | `representation.choose/hex/binary/character` on immediates and data literals | Generic planner ranks representation commands above fallback comments, skips already-satisfied projected representation candidates, and can feed byte printable-immediate listing candidates | Manual log hash/count, semantic reload, refreshed rendered text, and round-trip tests cover data literals and instruction immediates; GenAm smoke passed for `subi.b #'0'` rendering | Broaden autonomous representation candidate kinds as needed in `014-006-loop-planner-command-selection.md` |
| Equates/constants | Source model supports constants/EQU; NDK constants are searchable; C policy supports a small target-local equate table | Known NDK equate hints replace magic immediate values with included symbols; target-local equates render as `EQU` definitions and can be used by manual symbolic immediate representations | Add/edit/rename/remove a target-local constant and bind use sites to it | NDK equate use has hunk + source range + operand provenance; target-local equates use symbol name as durable identity | `create_manual_semantic_hint` for `domain="equate"` projects known symbols into manual symbol representations; `create_manual_target_equate`, `rename_manual_target_equate`, and `remove_manual_target_equate` project target-local constants; rename updates symbolic use-site representations and remove prunes them | `semantic.equate.*` candidates for matching immediate values; target catalog exposes `target.equate.add/edit/rename/remove` with create/rename/remove local effects | Planner accepts explicit `semantic.equate.*` use-site candidates and explicit `target.equate.*` target candidates with round-trip verification, and skips already-projected target-local equates | Effective metadata projection, rendered include/symbol, rendered target-local `EQU`, symbolic use-site rendering, C-backed equate navigation, rename/remove rendered-source behavior, and exact direct rebuild are covered; current C policy table is capped at 16 target-local equates to avoid stack growth | Complete in `014-009-equate-constant-editing.md` |
| LVO/API semantics | NDK libraries/LVOs, render lookup platform calls, call summaries and API arg analysis | `_LVO*` symbols, NDK field symbols, library call summaries, typed args/returns, app-slot propagation | Confirm library base, LVO function, API argument/return semantics, struct-offset meaning, and propagated stored state | LVO and struct-offset immediate use has hunk + source range + operand provenance; API semantic identity not complete | `semantic.lvo.*` and `semantic.struct_offset.*` hints for immediate operands project to manual symbol representations; register seeds can seed a library base | `semantic.lvo.*`, `semantic.struct_offset.*`, and `semantic.library_base.<library>` for A6 LVO contexts using API metadata or NDK lookup | Planner accepts explicit dynamic semantic command candidates for `semantic.library_base.*`, `semantic.lvo.*`, `semantic.struct_offset.*`, and `semantic.equate.*` with selected element context and round-trip verification, and skips already-projected library-base register seeds | Effective metadata projection, rendered include/symbol, and exact direct rebuild covered for LVO and struct-offset immediate use; library-base catalog execution covers exec and API-specific libraries; register seed render test exists | Add consumed API/register/typed-field semantic actions in `014-010-api-register-semantic-actions.md` |
| Register/base facts | `entry_register_seeds` support library base and struct pointer; render policy consumes them | Base-relative references become library/struct-aware | Add/remove register base facts with explicit lifetime/evidence | Entry offset + register + kind; not enough for all base lifetimes | Create/remove manual register seed | A6 LVO library-base helpers derive supported libraries from row API metadata or NDK library/function lookup; register elements expose a parameterized `semantic.register.struct_ptr` helper | Planner accepts explicit `semantic.register.struct_ptr` candidates with selected register element context and round-trip verification, mines unresolved typed-access listing evidence into struct-pointer candidates, and skips existing struct-pointer seeds from effective metadata; evidence-scoped lifetime inference remains open | Manual register seed render test exists; catalog coverage covers exec/non-exec LVO base helpers and register-selected struct-pointer seeds | Expand identity/commands/verifiers in `014-010-api-register-semantic-actions.md` |
| App/base-relative slots and RSSET layout regions | App-slot refs, app-slot analysis, regions/gaps/field gaps/suggestions, `rsset_layout_regions`, named layouts | `RSSET`/`RS.*`, `app_0234(a6)` names, typed field paths | Add/edit/rename/remove slots, regions, sizes, storage kinds, semantic types, parser roles, and layout gaps | App-slot context has symbol/displacement/base/access; manual RSSET region identity is `(layout_name, base_symbol, offset)` | `create_manual_rsset_layout_region` adds/replaces manual RSSET layout regions; `remove_manual_rsset_layout_region` filters regions by identity | `target.rsset_region.add/edit/rename/remove` expose target-level RSSET changes including parser role metadata; `app_slot.rename/edit/remove` expose selected app-slot rename/edit/removal via RSSET region actions | Planner recognizes explicit target RSSET and selected app-slot add/edit/rename/remove candidates, skips already-satisfied projected target RSSET/app-slot state, mines listing `app-slot-suggestions` into add/edit candidates when review candidates are empty, and preserves parser metadata from suggestions | Manual replay, effective metadata, command payload/execution, rendered RSSET field/reference, removal-to-raw-reference, app-slot command execution, parser-role payload projection, planner alias/autonomous suggestion selection, app-slot already-satisfied skip, and exact direct-rebuild tests cover add/edit/rename/remove payloads; broader autonomous workflows remain open | Continue app-slot/RSSET editing in `014-011-app-slot-rsset-editing.md` |
| Custom structs, fields, and typed accesses | `custom_structs`, RSSET regions, typed accesses, unresolved typed gaps, type-flow analysis | Struct field refs, typed field paths, gap navigation | Add/edit/rename/remove structs and fields; resolve typed gaps/accesses | Struct identity uses name; field identity uses `(struct_name, offset)` with field name carried for context; typed-access commands use selected element context | Custom struct and field add/edit/rename/remove actions project into effective metadata; field identity is `(struct_name, offset)` | `target.custom_struct.add/edit/rename/remove`, `target.custom_struct_field.add/edit/rename/remove`, `typed_gap.field.add/edit`, and `typed_access.field.edit/rename/remove` emit durable struct/field payloads and command execution local effects | Planner can form explicit target custom-struct/field and selected typed-gap/access field command candidates, skips already-projected struct/field state, but blocks unproven changes as missing an action-specific verifier until rendered custom-field paths are proven | Manual replay, command payload, command execution, effective metadata projection, and already-satisfied planner skips cover custom struct and field add/edit/rename/remove; typed-gap/access command payloads cover context routing; auto-analysis/navigation tests cover discovery only; rendered custom-struct field paths remain unverified | Add render verifiers for custom struct metadata in `014-012-structure-field-editing.md` |
| Runtime/execution views and loader ranges | `execution_views`, runtime address ranges, runtime view starts, absolute labels | ORG/runtime labels and copied-stage source | Add/edit/remove runtime views for copied or relocated code/data when auto-analysis lacks evidence | Execution view identity is `(source_start, source_end, base_addr)`; absolute labels use label identity | `create_manual_execution_view` adds/replaces manual execution views; `remove_manual_execution_view` removes by identity; absolute labels can be created through label path | `target.execution_view.add/edit/remove` for target context; label rename only for labels | Planner accepts explicit `target.execution_view.*` command candidates with target context and round-trip verification, and skips already-projected execution views | Manual replay, effective metadata, command payload, and target command execution tests cover execution-view add/edit/remove; source/reproduction tests exist; broader correction verifiers remain open | Add broader correction/view actions in `014-013-correction-and-view-actions.md` |
| Auto-analysis corrections and suppressions | `target_corrections.json`, `suppressed_seeded_items`, reproduction mismatches, blockers | Removes wrong imported/seeded facts and unblocks source render | Suppress or override target-specific auto facts only when upstream analysis is not objectively wrong for a whole class | Suppression identity is hunk + addr + seeded item kind; listing rows carry suppressible seeded source id/path/locator provenance | `suppress_seeded_item` projects target-specific seeded item suppressions | `correction.suppress_seeded_item.<kind>` row commands append seeded-item suppressions; review/reproduction correction commands absent | Planner accepts explicit `correction.suppress_seeded_item.*` candidates with row context and round-trip verification, and skips already-projected suppressions | Manual replay, effective metadata, command payload, and listing annotation tests cover seeded-item suppression; review/reproduction command verifier absent | Add execution-view and broader correction actions in `014-013-correction-and-view-actions.md` |
| Importer/analysis defects | Target import and parser logic derives target type, bootblock, resident, library/device, autoinit, and seeded facts | Corrects all affected targets by improving auto-analysis output | Fix importer/parser/analyzer upstream when a whole class of targets is objectively detected or parsed wrong | Source artifact and regression fixture identity, not per-target manual identity | Not a Manual Action Log action | Not a command catalog edit | Loop stops with implementation issue | Regression tests plus affected render/reproduction checks | Keep out of manual correction path; track as importer/analyzer bugs, or split from `014-013` when discovered |
| Review items and typed resolutions | Manual review items for conflicts, malformed logs, orphan code, unreconciled data, suspicious decode, reproduction mismatches, blockers, review notes | Clears blockers or records decisions | Resolve only with type-specific evidence and verifier | Review item id + evidence fingerprint | Resolve review item; review note actions | Review item actions for current kinds | Generic inspect uses review candidates and explicit review-item command candidates for seed create/remove and label edits; broader autonomous source-value ranking remains open | Review-item source actions route through semantic reload plus round-trip; type-specific verifiers remain incomplete | Complete through `014-005` and `014-006` |

Important audit finding: semantic hints are not automatically
source-converging. Known NDK equate, LVO immediate, and struct-offset immediate
hints now project through `effective_metadata.py` into rendered symbolic
immediates, but typed field access, API/register lifetime, and target-local
equate edit hints still need effective metadata projection and rendered-source
verification before they count as source-converging.

Implementation observation from `014-008`: listing row ordinals are not durable
identities. A backend navigation test previously compared navigation entries to
`enumerate(rows)` and failed when emitted `row_index`/navigation identity did
not match list position. Tests should assert durable listing identities such as
hunk/address/summary, or explicit projected `row_index` when the contract under
test is row-index stability.

Implementation observation from `014-006`: planner tests can use synthetic
candidate work only for ranking and skip semantics. A source-converging loop
smoke still requires real inspect/listing candidate production, command catalog
availability, execution, projection, and verifier coverage in one process.

Implementation observation from the GenAm `014-006` smoke: command execution can
invalidate listing presentation caches. Representation verification must reopen
or refresh listing projection before checking rendered text, otherwise semantic
reload and round-trip can pass while projection text is stale.

Implementation observation from `014-007`: structured data role comments are
source-converging metadata, not display-only notes. The C policy comment buffer
must be large enough for `mode`, `data_role`, `unit`, and optional `encoding`;
64 bytes truncated `length_prefixed_string`, while a modest 96-byte field keeps
the metadata intact without materially increasing stack pressure.

Implementation observation from `014-009`: manual symbol representations should
store compact platform symbol ids, not per-slot strings. A per-slot 64-byte
buffer materially increased native policy stack pressure; using KB ids preserves
include resolution while keeping the policy small.

Implementation observation from `014-009`: target-local equate definitions need
one shared symbol table, not per-use-site strings. The first implementation uses
a small 16-entry C policy table so manual symbolic representations can store an
index, but higher capacity should move the table out of stack-allocated
`M68kAnalysisPolicy`.

Implementation observation from `014-009`: target-equate rename/remove must
also update symbolic immediate representations. Otherwise a rename silently
loses source convergence, while a remove can leave dangling symbols that fail
policy loading instead of falling back to numeric immediates.

Implementation observation from `014-012`: round-trip exactness alone is not a
valid verifier for custom-struct commands while rendered custom-field paths are
unproven. The loop should surface a missing action-specific verifier instead of
executing metadata-only struct edits as source-converging work.

Implementation observation from `014-006`: already-satisfied checks for rename
commands must compare projected state to the requested new identity. Comparing
all command parameters treats `previous_name` as required future state and can
repeat a rename after it has already converged.

Implementation observation from `014-006`: planner reports must show the
candidate-specific verifier used for selection. Static command defaults are only
fallbacks and can misdescribe candidates with stricter projection verifiers.

Implementation observation from `014-005`: checking that `round_trip` is
available before execution is not enough. Generic output-affecting mutations
must include an actual post-execution round-trip layer so stale or mismatched
reproduction state blocks progress.

Implementation observation from `014-005`: target-context commands do not have
row affected-locator metadata. Their projection verifier must use authoritative
`/commands/execute` local effects, matched by command-specific effect kind and
payload, then rely on semantic reload and round-trip layers for source
convergence.

Implementation observation from `014-002`: selected listing element identities
must preserve zero-valued operand indexes. Treating `0` as absent makes first
operand app-slot and typed-field command contexts unrecoverable.

Implementation observation from `014-002`: mutation metadata must preserve
zero-valued row indexes. Using truthiness to choose between source and fallback
indexes can move row `0` effects to the wrong row.

Implementation observation from `014-006`: inspect candidates can be real but
all skipped because projected state already satisfies them or their verifier is
missing. Generic `run-one` must retry listing-derived candidate mining in that
case; otherwise stale review work can hide available source-converging listing
edits.

Implementation observation from `014-006`: `comment.edit` is still valid as a
last resort, but it must not be the first accepted generic `run-one` action when
the listing has not been mined for source-converging candidates.

Implementation observation from `014-011`: app-slot suggestions and platform
API-derived app-slot regions can describe the same durable RSSET identity.
Autonomous candidates must de-dupe by `(layout_name, base_symbol, offset,
symbol)` so the planner does not repeat equivalent edits.

Implementation observation from `014-010`: autonomous struct-pointer register
seeds need a concrete register element, not just a typed-gap element, because
`semantic.register.struct_ptr` is exposed and executed through register element
context.

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
