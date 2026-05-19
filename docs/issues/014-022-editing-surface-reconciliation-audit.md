Status: Complete; accepted review decisions captured
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md
Related issues: docs/issues/014-002-durable-target-identities.md, docs/issues/014-003-manual-action-coverage.md, docs/issues/014-004-command-catalog-coverage.md, docs/issues/014-005-verifier-coverage.md, docs/issues/014-006-loop-planner-command-selection.md, docs/issues/014-010-api-register-semantic-actions.md, docs/issues/014-011-app-slot-rsset-editing.md, docs/issues/014-012-structure-field-editing.md, docs/issues/014-013-correction-and-view-actions.md, docs/issues/014-014-data-global-symbol-naming.md, docs/issues/014-019-data-block-type-binding-and-platform-structs.md, docs/issues/014-020-target-equate-value-representation.md

Scope:
Investigate all source-converging editing families before adding more
family-specific implementation. Classify each edit family by whether it is
presentation-only, source-identity, classification/layout, semantic/type,
correction/view, or planner/autonomous feed work.

Goal:
Find the high-level implementation areas and deeper investigation opportunities
before changing issues or code. The proposal should become the source-of-truth
model first; issue updates should follow only after the model is discussed and
stable.

Accepted review decisions:
- Generic provenance exploration is read-only. It may report definitions, uses,
  source family, path/lifetime scope, conflicts, and possible actions, but it
  must not append to the Manual Action Log.
- Writes require an explicit accepted classification/override or a
  family-specific bind/type action consuming accepted evidence.
- Semantic/type descendants carry both `source_evidence_id` and
  `owner_action_id` when consumed evidence and generating edit differ.
- Path/lifetime scope is mandatory for non-global facts.
- Accepted evidence statuses are `analysis_proven`, `path_specific`,
  `conflicting`, `unknown`, `unresolved`, `manual_classified`, and
  `manual_override`. `path_specific` may write only to the selected scope;
  `conflicting` blocks writes until classified or overridden.
- Accepted source families are `rsset_app_base`, `library_base`,
  `struct_pointer`, `data_block_pointer`, `hardware_base`,
  `allocation_or_local`, `constant_or_equ`, `unknown`, and `conflicting`.
- Raw `$NNNN(An)`/`zzz(an)` operands and default A6 app-base fallback remain
  report-only without durable base evidence.
- RSSET same-displacement propagation requires same accepted base evidence or
  verifier-proven equivalent flow identity.
- RSSET report, bind, bind-refine, type-refine, unbind, and clear-type remain
  separate layers with owner-scoped cleanup.
- Custom typed fields and data-block type binding consume generic provenance;
  they do not re-solve it locally.
- Manual provenance overrides are correction actions and must record
  contradicted evidence id, reason, path/lifetime scope, and cleanup scope.
- Data/global names and EQU definition display stay outside provenance and
  type-flow by default.
- Provenance-backed writes require verifier layers for command payload, Manual
  Action Log replay, consumed evidence, conflict handling, descendant ownership,
  family-specific effect, cleanup, and exact round-trip when output-affecting.
- Planner reports may suggest writes, but non-dry execution requires accepted
  evidence, resolved scope, supported command, action-specific verifier, and
  already-satisfied checks against effective metadata/provenance state.
- Implementation may restart with `014-010` plus required `014-002` identity
  support. Proposal 014 remains Draft until implementation issues close.

Questions:
- Which current code paths produce the evidence for each editable fact family?
- Which manual actions are local display edits, and which reconcile with
  auto-analysis?
- Which semantic/type changes should generate or propose flow-equivalent
  descendants?
- Which descendants need owner action ids or source-fact identity for cleanup?
- Which verifiers are missing before a planner feed may execute the edit?
- Which gaps are family-specific, and which are cross-cutting identity,
  catalog, verifier, or planner gaps?

Current evidence:
- Manual Action Log families are explicit in
  `amiga_reversing/disasm/manual_actions.py`: seeds, data-symbol renames,
  register seeds, labels, comments, representations, semantic hints, seeded
  suppressions, target EQU values, custom structs/fields, RSSET regions,
  RSSET use-site bindings, data-block layouts/elements/interpreted refs,
  execution views, and review notes.
- Command catalog exposure in
  `amiga_reversing/disasm/manual_action_catalog.py` already separates row,
  range, review, target, semantic, data-block, RSSET, typed-access, correction,
  and presentation commands. This is the supported automation surface.
- Effective metadata projection in
  `amiga_reversing/disasm/effective_metadata.py` shows which actions become
  source/render policy facts: manual seeds, labels, comments, representations,
  semantic hints, register seeds, suppressions, execution views, target EQUs,
  custom structs/fields, RSSET layout regions/use-site bindings, and data-block
  metadata.
- Loop verifier selection in `amiga_reversing/reversing_loop.py` already
  distinguishes projected comments, manual-label state, data-symbol projection,
  suppression state, RSSET region/binding state, data-block state, execution
  view state, target EQU state, semantic-hint state, library-base register
  seeds, struct-pointer register seeds, and manual-seed state.
- Cross-checking `ManualActionKind` against the audit table did not reveal a
  missing source-converging family. The table now explicitly accounts for
  label-scope changes, review-note add/edit/clear, review-item resolution,
  data-block set/represent/interpret-ref actions, and execution views. Undo/redo
  are command-log controls, not separate source fact families.
- C backend/render lookup evidence shows some semantic facts are consumed by
  flow-aware render/analysis paths now: register seeds, RSSET layout regions,
  RSSET selected-use bindings, platform/API lookup, app-slot refs, typed
  accesses, and interpreted data refs. Other facts, especially custom structs
  and data-block type bindings, have metadata support before full rendered
  resolver/verifier support.

Audit buckets:
- Presentation-only edits: comments, literal representation, and EQU display
  style. These should stay local unless they emit semantic facts.
- Symbol/source identity edits: function, data, global, entrypoint, and seeded
  names, including label renames. These are xref-aware but usually not
  type-flow-producing.
- Classification/layout edits: code/data seeds, data roles, data-block layouts,
  and interpreted references. These may produce rendering, xrefs, review items,
  and cleanup requirements.
- Semantic/type edits: register/base seeds, RSSET bindings/refinements, struct
  fields, typed accesses, API/LVO semantics, and data-block type bindings. These
  need evidence reconciliation, flow-equivalent candidates, owner-scoped
  cleanup, and action-specific verifiers.
- Correction/view edits: seeded-item suppressions, execution/runtime views, and
  removals. These need precise cleanup and must not hide upstream analyzer bugs.
- Planner/autonomous feeds: candidate mining and already-satisfied skips. Feeds
  must stay report-only until command, identity, and verifier support are ready.

Investigation findings:
- The local-vs-analysis-facing boundary is the important split. Label renames,
  comments, and literal display choices do not need flow reconciliation unless
  they create semantic facts. Semantic/type-producing changes do.
- Source-identity edits such as data/global naming can be xref-aware without
  being type-flow-producing. Their verifiers should prove the intended rendered
  definition/use-site, not broad propagation.
- Classification/layout actions can invalidate or replace generated source
  ranges. They need durable range/layout/element identity and removal proof,
  but they should not silently emit type-flow unless a separate type binding
  owns it.
- Semantic/type actions must name consumed evidence and downstream ownership:
  register/base proof, RSSET base evidence, API/NDK metadata, custom/platform
  type compatibility, selected source bytes for interpreted refs, and
  flow-equivalent candidates where applicable.
- Corrective actions split into two kinds: target-specific user corrections
  such as seeded-item suppression/execution views, and cleanup of descendants
  generated by manual semantic/type choices. The latter needs owner action ids
  or source-fact identities, not broad suppressions.
- Planner feeds are downstream of the model. A feed may mine/report evidence
  before mutation support exists, but non-dry execution must require durable
  identity, catalog command support, and an action-specific verifier.

Surface audit map:

| Family | Classification | Analysis-facing? | Cascade risk | Current verifier shape | Main gap |
| --- | --- | --- | --- | --- | --- |
| Comments/review notes | Presentation | No | None | Projected comment/note state | Keep fallback-only |
| Literal representation | Presentation or symbolic semantic | Usually no | Symbolic projections if backed by semantic owner | Rendered text + round-trip | Split pure display from symbolic owners |
| Labels/entrypoints | Source identity | Limited xref-aware mining | Low; no type-flow | Manual-label state + rendered row | Broader feeds |
| Data/global symbols | Source identity/xref-facing | Yes for use-site refs, not type-flow | Use-site symbol projection and suppression cleanup | Projected symbol/suppression + round-trip | Broader global workflows |
| Code/data seeds and roles | Classification/layout | Yes | Reclassification conflicts and descendants | Manual seed state/removal + round-trip | Broader evidence-specific feeds |
| Data-block scalar layouts | Classification/layout | Yes | Element projection/removal | Layout/element state + rendered directive/value + round-trip | Gap rendering and type binding |
| Interpreted data refs | Layout/xref semantic | Yes | Symbolic refs and source-owned xrefs | Ref state/render/xref cleanup + round-trip | Target-side inbound xrefs |
| Target EQU/constants | Mixed | Yes for symbolic use sites | Rename/remove symbolic uses | Target-equate or semantic-hint state + round-trip | Definition value representation |
| API/LVO/register semantics | Semantic/type | Yes | Register/base lifetime, args/returns, stored state | Semantic-hint/register-seed state + round-trip | Evidence-scoped lifetimes/type-flow |
| RSSET/app-slot | Semantic/type/layout | Yes | Same-displacement uses, linked gaps, xrefs, type-flow | RSSET region/binding state + round-trip | Flow-derived base evidence and owned cascades |
| Custom structs/typed fields | Semantic/type | Intended yes | Typed access propagation | Metadata replay only for some paths | C resolver/render verifier |
| Data-block type binding | Semantic/type | Intended yes | Typed facts, nested fields, review items | Missing | `014-019` deep model |
| Corrections/views | Correction/view | Yes | Wrong cleanup can hide analyzer bugs | Suppression/execution-view state + round-trip | Broader reproduction/view commands |
| Planner feeds | Automation surface | Depends on family | Can over-mutate without verifier | Action-specific verifier required | Audit every new feed before widening |

Cross-cutting gaps:
- Evidence identity: semantic/type actions need durable ids for the evidence
  being consumed, not just the edited use-site. RSSET base evidence and
  evidence-scoped register lifetimes are the clearest current examples.
- Owner identity: generated xrefs, type-flow facts, review items, linked gaps,
  missed-use candidates, and symbolic projections must be owned by a manual
  action or source fact before cleanup can be precise.
- Verifier layering: supported mutations need semantic reload plus the
  family-specific rendered/type/xref effect and exact round-trip when
  output-affecting.
- Planner gating: broad autonomous feeds should come after one real target path
  proves evidence mining, command execution, Manual Action Log replay, rendered
  source improvement, cleanup where applicable, and exact round-trip.

Issue routing check:
- `014-001` remains the completed matrix parent; this investigation adds the
  semantic/type reconciliation layer that the matrix did not fully spell out.
- `014-002`, `014-003`, `014-004`, `014-005`, and `014-006` own cross-cutting
  identity, Manual Action Log, catalog, verifier, and planner gates.
- Completed family slices stay bounded: `014-007` is classification/layout,
  `014-008` is presentation unless backed by a semantic owner, `014-009` owns
  target EQU identity/use sites, `014-016`/`014-017` own scalar data-block
  layout/rendering, and `014-018` owns absolute byte/word/long interpreted refs
  with source-owned xrefs.
- Open semantic/type owners are `014-010` for API/register lifetimes and
  propagation, `014-011` for RSSET base-evidence export and binding cascades,
  `014-012` for custom structs/typed fields, and `014-019` for data-block
  type/platform binding.
- Open source-identity/correction/display owners are `014-013` for corrections
  and execution views, `014-014` for broader data/global symbols, and `014-020`
  for target EQU definition value representation.
- `014-021` remains the completed RSSET binding investigation model feeding
  `014-011`, not a separate implementation owner.

Proposed deep-dive order:
1. Semantic/type reconciliation model across register seeds, API/LVO semantics,
   typed fields, RSSET bindings, custom structs, and data-block type bindings.
2. Generic provenance / def-use / reference exploration: where values are set,
   where they are used, caller/path status, source-family classification,
   manual classification/override, durable evidence ids, and path/lifetime
   scopes.
3. RSSET/register-base evidence specifically: consume generic provenance for
   `An` base values, expose RSSET-shaped `base_evidence_refs`, and define how
   same-flow/same-displacement candidates are owned.
4. Custom structs and typed fields: C resolver/render path, typed-gap/access
   verifier, and cleanup of propagated typed accesses.
5. Data-block type/platform binding: type/domain binding identity, generated
   type-flow/review items, and removal verifier.
6. Classification/layout cleanup: reclassification descendants, layout gap
   rendering, interpreted-ref target-side inbound xrefs.
7. Planner feed policy: per-family evidence thresholds and already-satisfied
   skip rules after the above verifier gates exist.

Semantic/type code-path map:
- Listing context formation:
  `amiga_reversing/disasm/listing_context.py` builds command contexts from
  operand parts, `app_slot_refs`, `typed_accesses`,
  `unresolved_typed_accesses`, runtime refs, data literals, labels, and
  comments. For semantic/type edits, the important fields are `element_kind`,
  `operand_index`, `register`, `base_register`, `displacement`, app-slot
  symbol/access data, typed root/owner struct names, field names/expressions,
  and unresolved typed-access classifications.
- Catalog mutation surface:
  `amiga_reversing/disasm/manual_action_catalog.py` maps selected context to
  Manual Action Log commands. Immediate values feed `semantic.equate.*`,
  `semantic.lvo.*`, and `semantic.struct_offset.*`; register contexts feed
  `semantic.register.struct_ptr`; structured A6 LVO contexts feed
  `semantic.library_base.*`; typed gaps/accesses feed `typed_gap.field.*` and
  `typed_access.field.*`; app-slot and raw displacement contexts feed
  app-slot/RSSET commands and `rsset.binding.report/bind/unbind`.
- Manual replay/projection:
  `amiga_reversing/disasm/manual_actions.py` stores append-only semantic hints,
  register seeds, custom structs/fields, RSSET regions/use-site bindings, and
  data-block metadata. `effective_metadata.py` projects them into target
  metadata or render policy objects through helpers such as
  `_manual_semantic_hint_to_representation`,
  `_manual_register_seed_to_metadata`,
  `_manual_custom_struct_to_metadata`,
  `_manual_rsset_layout_region_to_metadata`,
  `_manual_rsset_use_site_binding_to_metadata`, and data-block layout/ref
  projection helpers.
- C policy/render consumption:
  `src/platform_file_lib.c` imports effective metadata into `M68kAnalysisPolicy`.
  `src/m68k_analysis_render_lookup.c` applies register seeds into typed and
  platform state, runs typed/platform state through a CFG, records typed
  accesses and unresolved typed accesses, applies API input/output type facts,
  records app-slot refs, and preserves typed provenance internally.
  `src/m68k_render_ir.c` consumes platform state and policy to attach LVO,
  app-slot, base-field, and selected RSSET binding symbols during rendering.
- Loop planner/verifier:
  `amiga_reversing/reversing_loop.py` mines listing-derived struct-pointer and
  library-base candidates, ranks semantic/type commands, blocks commands with
  no action-specific verifier, and verifies semantic hints, library-base
  register seeds, struct-pointer register seeds, RSSET binding state, target
  EQU state, manual seed state, and data-block/interpreted-ref state.

Semantic/type gap map:
- Register/base seeds: current identity is register + kind plus entry/seed
  offset metadata. Needed: evidence-scoped lifetime ids for non-entry facts,
  especially when a base value is established by a move/lea/call result inside
  current flow.
- API/LVO semantic hints: current hints render selected symbols or seed A6
  library bases. Needed: owner-scoped propagation for API argument/return
  facts, stored state, and review feedback when call semantics conflict.
- Typed gaps/accesses and custom structs: catalog and metadata exist, but C
  resolver/render support for custom structs is not proven. Needed: rendered
  field verifier, type-shape compatibility checks, and cleanup for propagated
  typed accesses.
- RSSET bindings: selected-use binding state and selected existing-field render
  are supported. Needed: flow-derived `base_evidence_id`, bind-refine field
  creation, linked-gap navigation, same-flow/same-displacement candidate
  ownership, and cleanup of generated xrefs/type-flow/review items.
- Data-block type bindings: scalar layout and interpreted absolute refs are
  supported separately. Needed: type/domain binding actions, nested/platform
  struct rendering, generated type-flow/review items, and removal verifiers.
- Interpreted refs: supported absolute byte/word/long refs own source-side
  runtime refs. Needed: target-side inbound navigation and non-absolute or
  type-derived reference interpretations.

Generic provenance / def-use review decisions:
- Add a cross-cutting provenance exploration model before RSSET-specific work.
  The generic question is: where is this register/value set, where is it used,
  which callers/predecessor paths define it, and which source family does each
  definition reconcile to?
- Exploration is read-only by default. The supported command ids are
  `provenance.definition.report`, `provenance.uses.report`,
  `provenance.references.report`, and `provenance.source_family.report`; legacy
  `provenance.explore_*` wording is obsolete and must not feed planner command
  normalization. Reports may feed UI, loop, and API callers without writing to
  Manual Action Log. Accepted classification/link/apply commands are the write
  boundary.
- Reports should return all candidate definitions, not a single forced answer.
  Statuses: `analysis_proven`, `path_specific`, `conflicting`, `unknown`,
  `unresolved`, `manual_classified`, and `manual_override`.
- Initial source-family vocabulary:
  `rsset_app_base`, `library_base`, `struct_pointer`, `data_block_pointer`,
  `hardware_base`, `allocation_or_local`, `constant_or_equ`, `unknown`, and
  `conflicting`.
- Path-specific or conflicting provenance blocks global semantic/type mutation.
  The user must choose a path/lifetime scope or add manual classification before
  write actions can apply.
- Manual classification can create durable evidence for unknown/unresolved
  sources. Manual override can contradict analysis-proven evidence only when it
  records the contradicted evidence id, reason, path/lifetime scope, and cleanup
  ownership.
- Accepted classifications should produce reusable durable evidence ids.
  Descendant facts should carry both `source_evidence_id` and `owner_action_id`
  when provenance evidence and the field/bind/type action are different.
- Reference queries are evidence-bearing def-use/xref views, not just
  navigation. "Where is this referenced?" should feed propagation, verification,
  and cleanup for labels, EQU values, app slots/RSSET regions, data blocks, and
  struct fields.
- First implementation slice should cover register/base provenance at
  instruction operands and base-relative memory operands. The model should
  extend later to memory-held values, stack locals, allocation/local buffers,
  and table-derived pointer values.
- RSSET `rsset.binding.report` should be a family-specific view over generic
  provenance results. Generic provenance proves or explains the base
  register/value, definitions, uses, path scope, conflicts, and evidence id;
  RSSET adds layout matching, fields/gaps, compatible offsets, same-lifetime
  displacement uses, and bind/refine blockers.

Semantic/type validation against focused tests:
- Semantic hints:
  `test_run_one_semantic_hint_executes_with_hint_verifier` proves catalog/loop
  execution through semantic hint state plus round-trip. The verifier proves the
  selected hint reload, not broad API argument/return propagation.
- Library-base and struct-pointer register seeds:
  `test_run_one_library_base_executes_with_register_seed_verifier` and
  `test_run_one_struct_pointer_seed_executes_with_register_seed_verifier` prove
  Manual Action Log replay, semantic reload, and round-trip for selected
  register seeds. C/backend tests prove register seeds affect rendering and
  typed analysis, but current contexts do not export seed identity as RSSET base
  evidence.
- Typed gaps/accesses and custom structs:
  `test_route_manual_action_catalog_execute_returns_custom_struct_local_effect`
  and `test_route_manual_action_catalog_execute_returns_typed_field_local_effect`
  prove catalog/MAL payloads and local effects. Reversing-loop tests assert
  `target.custom_struct_field.add` and `typed_gap.field.add` currently have no
  action-specific verifier and are skipped for autonomous execution unless
  already projected.
- RSSET bindings:
  server and C/backend tests prove report-only raw displacement, explicit
  evidence-enabled bind, selected-use binding replay, and selected existing-field
  render. They also prove same-displacement uses are reported but not applied as
  an implicit cascade.
- Data-block scalar/ref actions:
  C/backend, server, and loop tests prove layout/element/interpreted-ref replay,
  rendered source checks, source-owned xref checks for interpreted refs, cleanup
  state, and round-trip. Type/platform binding remains outside that proven
  scalar/ref surface.
- Data-block type binding:
  loop ranking contains a future `row.data_block.element.bind_type` shape, but
  no action-specific verifier or MAL action is proven. Keep this in `014-019`.

RSSET/register-base evidence trace:
- Source of truth in C flow:
  `platform_state_apply_policy_register_seeds` applies manual/target register
  seeds to platform state at entry/seed offsets. `platform_state_apply_lookup_register_seeds`
  adds lookup-derived seeds such as inferred hardware bases. `platform_state_update_after_instruction`
  propagates and clears platform base state through instructions.
- App-base decision:
  `render_state_operand_uses_app_base` treats explicit app-base state as
  app-base, treats library bases as app-compatible only where library extension
  slots allow it, rejects known hardware bases, and still has the conservative
  `A6` fallback for non-hardware offsets.
- App-slot access evidence:
  `render_lookup_analyze_amiga_app_state_slots` walks accepted instructions,
  applies current platform state, checks base-relative operands, and records
  app-slot access refs through `render_lookup_add_app_access_ref`.
  `render_lookup_record_typed_app_slot_pointer_accesses` separately tracks
  app-slot-derived pointers through local LEA/MOVE flow.
- Render consumption:
  `attach_amiga_app_base_slot_symbols` first checks selected RSSET
  use-site bindings, then normal app/base field slot lookup. A selected binding
  can render one existing field without forcing all same-displacement uses.
- Listing/catalog loss point:
  Real GenAm `$0102(a6)` currently exposes `base_register=A6` and
  `displacement=0x0102` through `operand_parts`, and the profile exposes the
  surrounding one-byte app-slot gap through `app_slot_analysis`, but the row has
  no `app_slot_refs`. The catalog therefore can report the candidate layout and
  gap, but mutation is blocked because no explicit `base_evidence_id` reaches
  the selected context.
- Current mutation evidence:
  `_rsset_binding_evidence_parameters` accepts an explicit `base_evidence_id`
  or derives `selected-app-slot:<reg>:<base_symbol>` from an `app_slot` element.
  Raw `An` displacement visibility deliberately remains report-only. Under the
  reviewed model, that report should be backed by generic provenance results
  when available, but should still not mutate without accepted durable evidence.
- Candidate durable evidence ids:
  `register-seed:<register_seed_id>` for manual/target seeds;
  `flow-base:<hunk>:<origin_addr>:<reg>:<kind>` for flow-derived assignment or
  call-result proofs;
  `selected-app-slot:<reg>:<base_symbol>` for already materialized app-slot
  refs; `manual-binding:<action_id>` for cascades derived from an accepted
  binding.
- Validation against current plumbing:
  explicit element context already carries `layout_name`, `base_symbol`, and
  `base_evidence_id` through catalog query/execution, loop command context,
  Manual Action Log payload, effective metadata, and selected-use render lookup.
  Selected `app_slot` contexts derive `selected-app-slot:<reg>:<base_symbol>`
  directly in the catalog. Loop RSSET binding candidates can pass
  `base_evidence_id` through when they already have it, but no current feed mines
  raw flow/base evidence into that field.
- Evidence ids not yet wired:
  `register-seed:<register_seed_id>` needs the seed id/lifetime exported on the
  selected listing context or candidate. `flow-base:<hunk>:<origin_addr>:<reg>:<kind>`
  needs a durable C analysis provenance object for the assignment or propagated
  base state. `manual-binding:<action_id>` is usable for descendants because MAL
  replay already stamps RSSET bindings with `owner_action_id`, but it is not a
  first bind source.
- Cascade rule:
  same-displacement proposals should match the same base evidence id or a
  verifier-proven equivalent flow identity. Matching `A6` and displacement text
  alone is not enough.

Proposed RSSET base-evidence export point:
- The source should be generic C provenance analysis, not RSSET catalog
  inference. `M68kRenderPlatformState` already carries base state through
  `platform_state_apply_policy_register_seeds`,
  `platform_state_apply_lookup_register_seeds`, and
  `platform_state_update_after_instruction`; typed analysis already has a
  provenance model exported on typed/unresolved typed accesses. RSSET should
  consume an operand-scoped export of that shared provenance/base identity.
- Add a row/operand-facing evidence list, tentatively `base_evidence_refs` for
  RSSET consumers, emitted beside `operand_parts`, `app_slot_refs`, and typed
  accesses. Each record should include `operand_index`, `base_register`,
  `displacement`, source family, `layout_name`, `base_symbol`,
  `base_evidence_id`, status, path/lifetime scope, `origin_kind`, origin
  hunk/offset/register, confidence, optional `parent_evidence_id`, optional
  contradicted evidence id, and optional `source_evidence_id`.
- Python listing context should copy compatible evidence records into selected
  element contexts. The existing catalog, server query, loop command context,
  MAL payload, effective metadata, and C render lookup can already carry an
  explicit `base_evidence_id` once it reaches the context.
- Do not treat the default A6 app-base fallback as bind evidence. It may support
  `rsset.binding.report`, gap discovery, and suggested next steps, but mutation
  needs a seed-backed, selected-app-slot, or flow-derived proof with a durable
  id.
- Same-displacement cascade candidates should be generated from shared
  `base_evidence_id` or an explicit equivalence proof between two
  `flow-base:*` ids. Path-specific/conflicting provenance requires user path
  selection before mutation. The accepted selected-use binding should own
  generated descendants via `owner_action_id`/cascade ids so unbind can remove
  only its own projections.
- Fit against owning issues:
  `014-002` already defines RSSET numeric use-site identity as hunk, source
  address, operand index, base register, displacement, layout/base symbol, and
  base-evidence id. The new `base_evidence_refs` shape is the missing evidence
  identity input to that contract, not a replacement for binding identity.
  `014-011` already owns raw displacement report-only behavior, explicit
  evidence bind/unbind, bind-refine, linked gaps, and cascade ownership; it is
  the right implementation home for exporting and consuming RSSET base evidence.
  `014-005` remains the verifier owner for semantic reload, rendered selected
  use or linked-gap state, exact round-trip, and later owner-scoped cleanup.

Typed/custom verifier ownership:
- `014-012` should own the custom-struct and typed-field implementation proof:
  importing custom structs into the C typed resolver, rendering custom field
  paths, checking type-shape compatibility, and cleaning up propagated typed
  accesses. `014-005` should keep the cross-cutting verifier requirement but
  does not need a separate shared implementation issue unless the same
  owner-identity mechanism is reused by several families.

Review packet:
- Approve the model if semantic/type changes should consume named evidence and
  own generated descendants, while label renames, comments, and display-only
  representations stay local.
- Change the model if any presentation/source-identity edit should trigger flow
  reconciliation by default, or if any semantic/type edit should stay purely
  local.
- Approve the RSSET contract if raw `zzz(an)` operands remain report-only until
  generic provenance/C analysis exports durable base evidence or the selected
  context already has explicit or selected-app-slot evidence.
- Change the RSSET contract if the A6 fallback can mutate without seed/flow or
  selected-app-slot proof, or if same-displacement uses should bind
  automatically without shared/equivalent base evidence.
- Approve the issue split if follow-up work should route through existing
  owning issues instead of creating one implementation issue per editing family.
- Agreed review decision: add generic provenance/def-use/reference exploration
  as a cross-cutting drill-down that RSSET consumes.

Review decisions before issue split:
- Confirm the reconciliation boundary: label renames, comments, and display
  representation changes stay local unless they emit semantic facts; type
  assignments, register seeds, RSSET bindings, custom/typed field changes,
  data-block type bindings, and API/platform semantics are analysis-facing.
- Confirm the RSSET evidence contract: C exports operand-scoped
  provenance/base evidence as `base_evidence_refs` for RSSET consumers; catalog
  bind/refine/cascade consumes that evidence instead of deriving mutation
  authority from raw displacement text.
- Confirm the generic provenance contract: read-only exploration returns
  multi-candidate definition/use/source-family reports; accepted
  classification, override, link, or family-specific bind/type commands write
  Manual Action Log state.
- Confirm default A6 app-base fallback remains report-only unless backed by a
  seed, selected app-slot, assignment/flow proof, or other durable base evidence.
- Confirm selected-use RSSET binding stays scoped, and same-displacement
  propagation is only a proposed/accepted cascade when candidates share
  same/equivalent base evidence and have owner-scoped cleanup.
- Confirm the issue split:
  `014-002` for evidence/owner identity, `014-010` for first-slice
  register/base provenance and API/register semantics, `014-011` for RSSET
  provenance consumption/export and binding behavior, `014-005` for verifier
  gates, `014-006` for planner feed gating, `014-012` for custom typed
  rendering, and `014-019` for data-block type/platform binding.
- Confirm completed display/classification matrix rows are bounded wins and do
  not imply semantic/type cascade support without the evidence and verifier
  contracts above.

Post-review issue split checklist:
- `014-002`: final durable identity updates for provenance evidence,
  `base_evidence_refs`, source-family evidence ids, path/lifetime scope,
  `source_evidence_id`, and generated-descendant owner ids.
- `014-005`: verifier coverage for consumed evidence, flow-equivalent
  descendants, selected/rendered effect, cleanup, and round-trip.
- `014-006`: planner feed gates and already-satisfied skip rules; read-only
  provenance exploration may feed suggestions, but unsupported semantic/type
  candidates remain report-only until durable evidence and verifiers exist.
- `014-010`: read-only provenance exploration commands, first-slice
  register/base provenance, evidence-scoped lifetimes, source-family
  classification, manual classification/override, plus API argument/return and
  stored-state propagation ownership.
- `014-011`: RSSET consumption of provenance, RSSET-shaped
  `base_evidence_refs`, bind-refine, linked gaps, same-flow/same-displacement
  candidates, and owned cascade cleanup.
- `014-012`: custom struct/typed-field C resolver/render support,
  type-shape compatibility, rendered verifier, and propagated typed-access
  cleanup.
- `014-019`: data-block type/platform binding identity, nested rendering,
  generated type-flow/review ownership, and removal verification.
- `014-013`, `014-014`, and `014-020`: preserve correction/view,
  data/global-symbol, and EQU display boundaries unless the actions emit
  semantic facts.

Expected output:
- A proposal section summarizing the editing surface categories.
- A table or checklist mapping each family to evidence source, manual action
  shape, local-vs-analysis-facing behavior, possible cascades, cleanup owner
  requirement, verifier state, and next deep investigation.
- A proposed order for deeper investigations, starting with the highest-risk
  semantic/type families.

Current output:
- Proposal 014 now has an "Editing Surface Reconciliation Audit" section with
  the family map and next investigation column.
- Proposal 014 now also records the first semantic/type reconciliation pass:
  listing/catalog evidence sources, Manual Action Log projection boundaries,
  C typed/platform flow state, and the missing durable evidence bridge between
  flow provenance and manual semantic/type actions.
- Proposal 014 now records the RSSET/register-base evidence finding: C can know
  base state, but catalog/MAL identity currently only receives selected
  app-slot or explicit evidence, leaving raw displacement binding report-only.
- The review added a generic provenance/def-use/reference model above RSSET:
  read-only exploration, multi-candidate path/lifetime status, source-family
  classification, manual classification/override, reusable evidence ids, and
  evidence-bearing reference views.
- The RSSET evidence-id check is now split into proven paths
  (`explicit_context`, `selected-app-slot`) and not-yet-wired paths
  (`register-seed`, `flow-base`, first-bind `manual-binding`).
- The audit map has been checked against the current Manual Action Log families
  and loop command rankings/verifier dispatch.
- The semantic/type code-path map now has focused test evidence for which
  families are proven, verifier-blocked, or future-only.
- Proposal 014 now contains the proposed RSSET base-evidence export contract.
- The proposed base-evidence contract has been checked against `014-002`,
  `014-011`, and `014-005`; no new owning issue is needed before discussion.
- Typed/custom rendered-field verification remains owned by `014-012` with
  `014-005` as the verifier-policy tracker.
- Proposal 014 now includes an issue routing/readiness map so every audit
  family has an owning issue and a local-vs-analysis-facing stance.
- Proposal 014 now includes the explicit coverage check against current
  `ManualActionKind` and catalog families, including data-role commands and the
  distinction between source fact families and transient/undo-redo controls.
- Proposal 014 now includes a condensed evidence appendix covering listing
  context formation, catalog execution, Manual Action Log projection, C
  consumption, loop verification, and focused test boundaries.
- Proposal 014's older coverage matrix now has interpretation rules tying it
  back to this reconciliation audit, and its RSSET row explicitly names the
  missing `base_evidence_refs` export contract.
- Proposal 014 now includes the review decision points that should be settled
  before findings are split into owning issues.
- Proposal 014 now includes the post-review issue split checklist, so the
  approved model can be folded into owning issues without reopening the surface
  audit.
- Proposal 014 now includes a compact review packet that names what approving
  or changing the model means.
- The grill-me review decisions have been captured: semantic/type edits consume
  evidence and own descendants; presentation/source-identity edits stay local
  unless they emit semantic facts; generic provenance is read-only until an
  accepted classification/link/apply action writes MAL; RSSET consumes generic
  provenance and does not mutate from raw `zzz(an)`/A6 fallback alone; path
  conflicts block global mutation.
- Findings have been split into owning issues:
  `014-002` for durable provenance/evidence identity,
  `014-005` for provenance-backed verifier gates,
  `014-006` for planner feed gating,
  `014-010` for generic provenance/def-use/reference exploration and first
  register/base slice,
  `014-011` for RSSET provenance consumption and binding/refine/cascade work,
  `014-012` for custom typed resolver/render/cleanup,
  `014-019` for data-block type/platform binding,
  `014-013` for correction/override boundaries,
  `014-014` for source-identity naming boundaries, and
  `014-020` for EQU display-only boundaries.

Completion audit against objective:

| Requirement | Evidence | Status |
| --- | --- | --- |
| Investigate all source-converging editing families | `ManualActionKind` inventory, command catalog families, listing contexts, effective metadata, verifier dispatch, and C render/analysis paths are all summarized above and cross-checked against the proposal audit table. | Satisfied from current code evidence. |
| Update Proposal 014 with the surface audit | Proposal 014 has the "Editing Surface Reconciliation Audit" section, coverage check, family table, issue routing, RSSET base-evidence contract, decision points, and matrix interpretation rules. | Satisfied. |
| Classify each family as local/analysis-facing/mixed | The audit buckets, surface audit map, and Proposal 014 table classify presentation, source identity, classification/layout, semantic/type, correction/view, and planner feed families. | Satisfied. |
| Separate cross-cutting gaps from family-specific gaps | Cross-cutting evidence identity, owner identity, verifier layering, and planner gating are separated from the semantic/type, RSSET, custom-typed, data-block, correction, and planner family gaps. | Satisfied. |
| Name next deep investigations before implementation resumes | The deep-dive order and issue routing map name generic provenance/def-use/reference exploration plus the owning follow-ups: `014-010`, `014-011`, `014-012`, `014-019`, `014-013`, `014-014`, `014-020`, plus cross-cutting `014-002`/`014-005`/`014-006`. | Satisfied. |
| Validate the RSSET/auto-analysis concern | The RSSET/register-base evidence trace explains current report-only raw displacement behavior, proven explicit/selected-app-slot evidence paths, missing `register-seed`/`flow-base` export, and proposed `base_evidence_refs`. | Satisfied from investigation; implementation remains in owning issues. |
| Agree the model before splitting findings into owning issues | The grill-me review accepted the reconciliation boundary, generic provenance model, source-family vocabulary, read-only exploration/write boundary, path/lifetime scoping, manual classification/override rules, RSSET-as-consumer model, and existing-issue split. The owning issues now carry the split findings. | Satisfied. |

Remaining investigation work:
- None in this audit issue. Continue with focused investigations on the owning
  issues, starting with `014-010` generic provenance / def-use / reference
  exploration.

Non-goals:
- No production code changes from this issue alone.
- No broad planner feed expansion.
- No family issue rewrites until the proposal model is discussed.

Acceptance criteria:
- Proposal 014 contains the agreed editing-surface reconciliation model.
- Each family is classified as local, analysis-facing, or mixed.
- Cross-cutting gaps are separated from family-specific gaps.
- The next deep investigations are named before implementation work resumes.

Cleanup / deletion:
Keep as the completed audit/source-of-decisions until the owning issues no
longer need the cross-reference, then delete or archive with Proposal 014.
