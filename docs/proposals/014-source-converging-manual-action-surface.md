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

## Editing Surface Reconciliation Audit

Before widening any one editing family, Proposal 014 needs a full editing
surface audit. The investigation lives in
`014-022-editing-surface-reconciliation-audit.md` and should update this
proposal before issue-specific implementation work continues.

Current audit result:

| Editing family | Category | Evidence source | Manual action shape | Reconciliation / cascade policy | Owner / cleanup requirement | Verifier gate | Next investigation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Comments and review notes | Presentation-only | Listing row/range locators and review item ids | `create/remove_manual_comment`, `add/edit/clear_review_note`, `resolve_review_item` | Local workflow/source annotation only. Use only when no structured fact fits. | Remove/comment or note/review id only; no analysis descendants. | Projected comment or note state; no type-flow/xref verifier. | Keep fallback-only in planner. |
| Literal representation | Presentation-only unless symbolic | Operand/data element locators, source range, operand index | `create/remove_manual_representation`, data-block element representation | Local rendering choice for hex/binary/char/string. Symbolic use-site representation becomes semantic only when backed by semantic hint, target EQU, or interpreted ref. | Representation id/element identity only unless symbolic projection is generated from another owner. | Rendered text plus exact round-trip. | Separate pure display from symbolic semantic owners in verifier reports. |
| Label and entrypoint names | Source identity | Facts v2 code starts/control targets, seeded labels, source descriptors, review labels | `create/remove/rename_manual_label`, `change_label_scope` | Rename/create source identities. May be xref-aware for candidate mining but should not create type-flow. | Label id or hunk/source/runtime identity; no cascade identity unless later label action creates derived semantic facts. | Manual label state, rendered row, exact round-trip. | Broaden autonomous feeds beyond entrypoint evidence. |
| Data/global symbols | Source identity, sometimes xref-facing | Data rows, seeded entities, runtime-address refs, data classes, internal data refs | `rename_data_symbol`, named data seeds, seeded-item suppression for removal | Render definitions and use sites; may consume xref evidence but normally does not propagate type facts. | Target hunk/range or seeded item identity; removal suppresses only selected seeded item. | Projected data symbol or suppression state plus exact round-trip. | Finish broader global/use-site workflows in `014-014`. |
| Code/data classification and data roles | Classification/layout | Facts v2 decode/data spans, review items, listing row/range bytes | `create/remove_manual_seed` with code/data role/unit/encoding | Reclassifies source ranges and rendered directives. Can invalidate decode/data descendants and produce review conflicts. | Seed id/range identity; conflicting descendants must be recomputed or owned before cleanup. | Manual seed state/removal plus exact round-trip. | Broaden planner feeds only with type-specific evidence. |
| Data-block scalar layouts | Classification/layout | Data ranges, existing data roles, source bytes, active layout context | `create/edit/remove_manual_data_block_layout`, `set/remove/represent_manual_data_block_element` | Splits opaque ranges into elements and projections. Scalar rendering is supported; type/domain binding remains separate. | Layout id plus element offset; removal restores raw/gap state. | Layout/element state, exact directive/value render checks, exact round-trip. | Add gap-specific rendering and type/platform binding. |
| Interpreted data refs | Layout plus xref-facing semantic | Data-block elements, decoded source bytes, target locators, runtime-address refs | `interpret/remove_manual_data_block_element_ref` | Converts proven byte/word/long values into symbolic refs and source-owned xrefs. | Interpreted-ref id owns symbol projection and source-owned runtime ref; cleanup must match layout/element/source value. | Ref state, symbolic render, source-owned xref cleanup, exact round-trip. | Target-side inbound xrefs and non-absolute references. |
| Target EQU/constants | Mixed display and semantic | Target-local EQU table, NDK/equate lookup, immediate operands | `create/rename/remove_manual_target_equate`, semantic equate hints | EQU definitions and symbolic use sites are semantic; EQU definition value style is presentation-only and now durable. | Equate name identity; rename/remove updates owned symbolic use-site representations. | Target-equate state or semantic-hint state plus exact round-trip. | Broader semantic/equate provenance remains separate. |
| API/LVO/register semantics | Semantic/type | LVO rows, NDK library/function metadata, selected register/memory operand contexts, typed-access analysis | `create/remove_manual_semantic_hint`, `create/remove_manual_register_seed` | Consumes API/register evidence and can seed library bases, struct pointers, LVO/field symbols, typed args/returns, and stored state. | Register seed/hint id; future propagated args/returns/type-flow need owner identity and cleanup. | Semantic hint or register-seed state plus exact round-trip; broader type-flow verifier missing. | Evidence-scoped register lifetimes and API arg/return propagation in `014-010`. |
| RSSET/app-slot regions and bindings | Semantic/type plus layout | App-slot refs, app-slot analysis, RSSET regions/gaps, raw displacement operand parts, register/base evidence | `create/remove_manual_rsset_layout_region`, `create/remove_manual_rsset_use_site_binding`; refine/type actions planned | Regions render `RS.*`; binding links selected numeric uses to a proven base/layout. Flow-equivalent same-displacement candidates are planned, not automatic. | Region identity `(layout_name, base_symbol, offset)`; binding id plus `owner_action_id` and future cascade ids for same-displacement/xref/type descendants. | RSSET region/binding state and exact round-trip; selected-use render only when existing field matches. | Flow-derived `base_evidence_id`, bind-refine, linked gaps, owned cascades. |
| Custom structs and typed fields | Semantic/type | Custom struct metadata, typed gaps/accesses, NDK/platform structs, unresolved typed access analysis | `create/rename/remove_manual_custom_struct(_field)` via target/typed commands | Effective metadata can store structs/fields; the C resolver now consumes register-seed-backed custom structs for rendered field paths. | Struct name and `(struct_name, offset)` field identity; selected typed-field writes carry consumed `struct_pointer` provenance, `parent_evidence_ids`, and projected custom-field owner/cleanup action ids; propagated typed accesses need descendant owner identity. | Selected typed-field commands now prove accepted provenance, metadata replay with matching consumed evidence/owner, rendered selected access, and exact round-trip. Target-wide metadata commands and propagated cleanup remain blocked. | Type-shape and cleanup in `014-012`. |
| Data-block type/platform binding | Semantic/type | Data-block layouts/elements, custom/platform structs, enum/equate domains, parsed include data | Row bind/clear type commands for element-scoped bindings; custom/platform struct bindings expand into typed seeded field entities; scalar domain bindings project `value_domain` for symbolic values | Should propagate typed facts, rendered nested fields, review items, and interpreted field refs only after type shape reconciles. | Layout id + element offset + type-binding id; active bindings stamp `owner_action_id`; clear-type preserves the previous binding with `cleanup_action_id`; all derived facts owner-scoped. Current struct/domain seeded entities carry the binding id as source locator; generated type-flow/review descendants still need dedicated owner fields. | Bind/clear loop path verifies reload, matching type-binding owner/cleanup, rendered bound-type token proof, binding-owned seeded descendants, accepted consumed provenance where present, typed field render for custom/platform structs, symbolic scalar domain render, and exact round-trip; generated type-flow/review cleanup verifier remains missing. | `014-019` model and verifier proof. |
| Corrections and execution views | Correction/view | Suppressible seeded metadata, target corrections, runtime/execution view evidence, reproduction mismatches | `suppress_seeded_item`, `create/remove_manual_execution_view` | Correct target-specific facts or runtime mapping. Importer/analyzer class bugs must remain upstream bugs. | Suppression `(kind,hunk,addr)` or execution-view identity; execution views carry owner/cleanup action ids; cleanup must not remove unrelated facts. | Suppressed-item or execution-view state, including view owner/cleanup ids, plus exact round-trip. | Broader reproduction/view correction commands in `014-013`. |
| Planner/autonomous feeds | Candidate surface | Inspect candidates, listing pages, navigation analysis, effective metadata, command availability | No private action; must route to catalog commands | Candidate feeds may propose only supported, verifier-backed edits. Report-only feeds are valid for unsupported semantic/type families. | Already-satisfied skips must use projected/effective state; generated candidates need source evidence identity. | Action-specific verifier required before non-dry execution. | Audit every new feed against this table before widening. |

Coverage check against current code:

- The table accounts for every source-converging `ManualActionKind` currently
  defined in `amiga_reversing/disasm/manual_actions.py`: seeds, data-symbol
  renames, register seeds, labels/scope, comments, representations, semantic
  hints, seeded-item suppressions, target EQUs, custom structs/fields, RSSET
  regions/use-site bindings, data-block layouts/elements/interpreted refs,
  execution views, review notes, and review-item resolution.
- `undo_action` and `redo_action` are Manual Action Log controls, not separate
  source fact families. Navigation and palette-opening catalog entries are
  transient UI commands and stay outside the reconciliation matrix.
- Catalog families checked in `manual_action_catalog.py` include review, row,
  range, element, target, semantic, data-block, app-slot/RSSET, typed
  gap/access, correction, and data-symbol commands. The proposal groups them by
  source effect rather than by UI entry point so row/range/review variants do
  not split the model artificially.
- Data-role seed commands currently cover string, length-prefixed string,
  string-control stream, scalar/lookup/pointer tables, copper lists, palettes,
  bitmaps, sound samples, audio tables, and sprites. These remain
  classification/layout edits unless a later typed/domain action owns semantic
  descendants.
- The current listing element contexts are operands, app-slot refs, typed
  accesses/gaps, runtime address refs, data literals, labels, and comments.
  That is enough evidence for current catalog commands, but RSSET still needs
  exported operand-scoped `base_evidence_refs` before raw displacement binding
  can safely mutate.

Evidence appendix:

- Listing context formation in `listing_context.py` is the row-to-command
  evidence boundary. It exports operand parts, app-slot refs, typed
  accesses/gaps, runtime address refs, data literals, labels, and comments. For
  semantic/type edits the important carried fields are element kind, operand
  index, register/base register, displacement, app-slot symbol/access data,
  typed root/owner struct names, field names/expressions, and unresolved
  typed-access classifications.
- Catalog execution in `manual_action_catalog.py` is the only supported
  mutation surface. Immediate values feed semantic equate/LVO/struct-offset
  hints; register contexts feed library-base and struct-pointer seeds; typed
  gaps/accesses feed custom struct field actions; app-slot and raw displacement
  contexts feed app-slot/RSSET report, bind, and unbind commands.
- Manual replay in `manual_actions.py` and projection in `effective_metadata.py`
  prove which edits become source/render policy facts: semantic hints,
  register seeds, custom structs/fields, RSSET regions/use-site bindings,
  data-block layouts/elements/interpreted refs, execution views, target EQUs,
  suppressions, labels, comments, and representations.
- C consumption is concentrated in `platform_file_lib.c`,
  `m68k_analysis_render_lookup.c`, and `m68k_render_ir.c`: effective metadata
  is imported into analysis policy, register seeds and platform/typed state flow
  through the CFG, API input/output facts and app-slot refs are recorded, and
  LVO/app-slot/base-field/selected-RSSET symbols are attached during rendering.
- Loop verification in `reversing_loop.py` currently proves selected semantic
  hints, library-base and struct-pointer register seeds, RSSET
  region/binding state, data-block/interpreted-ref state, target EQU state,
  manual seed state, data-symbol projection, suppressions, execution views,
  manual labels, and comments. Typed custom-field rendering, broad API
  arg/return propagation, data-block type binding, and same-flow RSSET cascades
  remain intentionally verifier-gated.
- Focused tests line up with this boundary: semantic hints and register seeds
  execute with semantic reload plus round-trip; RSSET raw displacement reports
  but does not bind without explicit evidence; selected RSSET binding can render
  one existing field without applying all same-displacement uses; data-block
  scalar/ref actions prove rendered output and source-owned xref cleanup; custom
  typed-field commands prove selected rendered accesses only when accepted
  `struct_pointer` provenance is persisted with the action.

Generic provenance / def-use exploration:

- Semantic/type reconciliation should use a shared provenance model before
  family-specific bind/type actions. The first question is generic: where is
  this register/value set, where is it used, which callers or predecessor paths
  can define it, and which source family does each definition reconcile to?
- Exploration is read-only. Catalog commands such as
  `provenance.explore_definition`, `provenance.explore_uses`, and
  `provenance.explore_source_family` should return evidence reports for UI,
  loop, and API callers without appending to the Manual Action Log. Accepted
  `provenance.classify_source`, `provenance.override_source`, link/apply, or
  family-specific commands are the write boundary.
- Provenance reports should return all candidate definitions instead of forcing
  one global answer. Statuses should include `analysis_proven`,
  `path_specific`, `conflicting`, `unknown`, `unresolved`,
  `manual_classified`, and `manual_override`. Path-specific or conflicting
  results must require path/lifetime selection before mutation.
- Initial source-family vocabulary should be bounded:
  `rsset_app_base`, `library_base`, `struct_pointer`, `data_block_pointer`,
  `hardware_base`, `allocation_or_local`, `constant_or_equ`, `unknown`, and
  `conflicting`. Family-specific details hang off that classification.
- Accepted classifications produce durable evidence ids reusable by multiple
  semantic/type commands. Generated descendants should carry both
  `source_evidence_id` and `owner_action_id` when the provenance evidence and
  the field/bind/type action are different.
- Manual classification may fill unknown/unresolved sources. Manual override
  may contradict analysis-proven evidence only when it records the contradicted
  evidence id, reason, path/lifetime scope, and cleanup ownership.
- Reference queries are part of the same model, not just UI navigation.
  "Where is this referenced?" views for labels, EQU values, app slots/RSSET
  regions, data blocks, and struct fields are evidence-bearing def-use/xref
  views that can feed propagation, verification, and cleanup.
- First implementation slice should focus on register/base provenance at
  instruction operands and base-relative memory operands. The model should
  still allow later memory-held values, stack locals, allocation/local buffers,
  and table-derived pointer values.
- Current first-slice implementation exposes read-only
  `provenance.definition.report`, `provenance.uses.report`,
  `provenance.references.report`, and `provenance.source_family.report` catalog
  entries for selected register/base operands. Reports carry stable
  `source_evidence_id`, subject, definitions/uses, reference/consumer views,
  source family/status, path/lifetime scope, confidence, conflicts, possible
  actions, and consumers, and remain non-mutable command catalog inspection
  entries.
- RSSET `rsset.binding.report` should become a family-specific view over this
  provenance model: generic provenance explains the base register/value,
  definitions, uses, path scope, conflicts, and evidence id; RSSET adds layout
  matching, fields/gaps, compatible offsets, same-lifetime displacement uses,
  and bind/refine blockers.
- Current source-flow map: `listing_context.py` exports selectable operands,
  app slots, typed accesses/gaps, and runtime refs; `manual_action_catalog.py`
  exposes report/write boundaries; `server.py` preserves explicit RSSET
  evidence through query/execute contexts; `effective_metadata.py` projects
  accepted Manual Action Log state; `reversing_loop.py` mines candidates and
  verifies action-specific state. C imports policy metadata in
  `platform_file_lib.c`, applies register/lookup seeds and updates base state
  in `m68k_analysis_render_lookup.c`, then renders LVO, base-field, typed, and
  selected RSSET symbols in `m68k_render_ir.c`.
- Focused issue split after the investigation: `014-010` owns read-only
  provenance reports and first-slice register/base evidence; `014-002` owns
  `source_evidence_id`, path/lifetime scope, and `owner_action_id`; `014-005`
  owns consumed-evidence and cleanup verifier layers; `014-006` owns
  read/report versus write/execute planner policy; RSSET, typed fields, and
  data-block type binding consume the accepted evidence in `014-011`,
  `014-012`, and `014-019`.

Cross-cutting gaps:

- Semantic/type actions need durable identities for consumed evidence, not just
  the edited use-site. RSSET base evidence and evidence-scoped register
  lifetimes are the clearest current examples.
- Generated xrefs, type-flow facts, review items, linked gaps, missed-use
  candidates, and symbolic projections must be owned by a manual action or
  source fact before cleanup can be precise.
- Supported mutations need layered verification: Manual Action Log replay,
  semantic reload, family-specific rendered/type/xref effect, owner-scoped
  cleanup where applicable, and exact round-trip when output-affecting.
- Broad autonomous feeds should follow a real target proof for each family:
  evidence mining, catalog command execution, Manual Action Log replay,
  rendered source improvement, cleanup where applicable, and exact round-trip.

Deep investigations should proceed in this order:

1. Semantic/type reconciliation across register seeds, API/LVO semantics, typed
   fields, RSSET bindings, custom structs, and data-block type bindings.
2. Generic provenance / def-use / reference exploration: definition lookup,
   use lookup, caller/path status, source-family classification, manual
   classification/override, durable evidence ids, and path/lifetime scopes.
3. RSSET/register-base evidence: consume provenance evidence as
   `base_evidence_refs`, add RSSET layout interpretation, same-flow/
   same-displacement candidates, and cascade ownership.
4. Custom structs and typed fields: C resolver/render path, typed-gap/access
   verifier, and propagated typed-access cleanup.
5. Data-block type/platform binding: type/domain identity, generated type-flow
   and review items, and removal verifier.
6. Classification/layout cleanup: reclassification descendants, layout gap
   rendering, and interpreted-ref target-side inbound xrefs.
7. Planner feed policy: per-family evidence thresholds and already-satisfied
   skip rules after the relevant verifier gates exist.

Issue routing and readiness:

| Issue | Current role in this audit | Reconciliation stance |
| --- | --- | --- |
| `014-001` | Completed capability matrix parent | Matrix remains valid, but `014-022` adds the semantic/type reconciliation layer that must be reflected before further broad expansion. |
| `014-002` | Durable identity owner | Owns consumed provenance/evidence ids, including reusable source-family evidence, RSSET `base_evidence_refs`, path/lifetime scope, `source_evidence_id`, and owner ids for generated descendants. |
| `014-003` | Manual Action Log umbrella | Existing append-only/corrective pattern is right; semantic/type actions must add paired cleanup for owned descendants when they generate analysis facts. |
| `014-004` | Command catalog umbrella | Catalog may expose report-only commands before mutation support, but mutation commands need durable identity plus verifier ownership. |
| `014-005` | Verifier umbrella | Owns the rule that semantic/type changes verify consumed evidence, generated/proposed flow-equivalent descendants, cleanup, and round-trip where output-affecting. |
| `014-006` | Planner/autonomous feed owner | Feeds may run read-only provenance reports, but write feeds stay narrow until command, identity, conflict/path-scope resolution, and action-specific verifier support exist; raw RSSET displacement feeds remain report-only until provenance-backed `base_evidence_refs` exist. |
| `014-007` | Completed data-role command coverage | Classification/layout only. Data roles may replace source rendering but do not imply type-flow or xref cascades. |
| `014-008` | Completed literal representation coverage | Presentation-only unless the symbolic text is generated from a semantic owner such as a hint, target EQU, or interpreted ref. |
| `014-009` / `014-020` | Target EQU semantics and definition display | EQU identity/use-site binding is semantic; definition value representation is implemented as display metadata and must not change numeric semantics. |
| `014-010` | API/LVO/register semantic owner | Owns register/base provenance as the first implementation slice, evidence-scoped register lifetimes, and future API arg/return/stored-state propagation. Current verifiers prove selected hints/seeds only. |
| `014-011` / `014-021` | RSSET/app-slot owner and binding investigation | Owns RSSET consumption of generic provenance, `base_evidence_refs` export/selection, bind/refine/unbind, linked gaps, same-flow candidates, and owned cascades. `014-021` is the model source; `014-011` is implementation. |
| `014-012` | Custom struct/typed-field owner | Owns C resolver/render support, type-shape compatibility, rendered custom-field verifier, and propagated typed-access cleanup. |
| `014-013` | Correction/view owner | Owns target-specific suppressions/views and cleanup semantics; analyzer/importer class bugs stay upstream bugs, not manual suppressions. |
| `014-014` | Data/global symbol owner | Owns broader data/global definition and use-site workflows. These are xref-aware source identities, not type-flow unless another semantic owner is introduced. |
| `014-016` / `014-017` | Data-block metadata and scalar render slices | Completed scalar layout/element work remains classification/layout. Type/domain binding stays separate. |
| `014-018` | Interpreted data refs | Completed for absolute byte/word/long refs with source-owned xrefs. Target-side inbound refs and non-absolute/type-derived refs remain out of scope. |
| `014-019` | Data-block type/platform binding owner | Owns type/domain binding, nested/platform struct rendering, generated type-flow/review items, and removal verification. |

Initial semantic/type reconciliation findings:

- Listing/catalog evidence is assembled from row operand parts, app-slot refs,
  typed accesses, unresolved typed accesses, runtime refs, data literals,
  labels, and comments. For semantic/type work, the critical contexts are
  selected registers or memory operands, `base_register`/`displacement`,
  API/LVO row metadata, `app_slot_refs`, and typed-gap/access records.
- Catalog commands already separate immediate semantic hints
  (`semantic.equate.*`, `semantic.lvo.*`, `semantic.struct_offset.*`),
  register/base seeds (`semantic.library_base.*`,
  `semantic.register.struct_ptr`), typed field commands
  (`typed_gap.field.*`, `typed_access.field.*`), app-slot/RSSET commands, and
  data-block type work. They all route through Manual Action Log; no private
  semantic mutation path is needed.
- Effective metadata can project semantic hints, register seeds, custom
  structs/fields, RSSET layout regions, RSSET selected-use bindings, data-block
  layouts/elements, and interpreted refs. Projection support is therefore not
  the same as analysis reconciliation: custom structs and data-block type
  bindings still need C resolver/render consumption and verifiers before broad
  execution.
- `014-019` now has a first gated data-block type-binding surface: row
  bind/clear commands store durable element-scoped `type_binding` identity,
  replay stamps the binding owner action, and loop execution requires semantic
  reload, rendered bound-type token proof, exact round-trip, and accepted
  provenance when a value source is consumed. Nested/platform expansion and
  generated type-flow/review cleanup remain open until renderer and descendant
  ownership proofs exist.
- The C render/analysis lookup carries typed and platform flow state through a
  control-flow graph. Register seeds are applied at entry or seed offsets;
  platform state tracks app/library/hardware bases; typed state tracks struct
  pointers, API input/output provenance, app-slot-derived addresses, stored
  typed values, typed accesses, and unresolved typed accesses.
- That C flow state has provenance concepts, but they are not yet durable
  Manual Action Log evidence identities. The missing bridge is to expose stable
  proof identities such as "A2 is this base at this offset because of this
  seed/call/assignment" so manual semantic/type actions can reconcile with the
  existing flow state and own later cascades.
- Existing loop verifiers prove selected semantic state, such as semantic hint,
  library-base register seed, struct-pointer register seed, RSSET binding, or
  data-block ref state plus exact round-trip. They do not yet prove broad
  propagated type-flow descendants, same-flow RSSET candidates, custom struct
  field rendering, or owner-scoped cleanup for generated typed descendants.
- Focused test coverage confirms the same layering: semantic hints and
  register seeds can execute with semantic reload plus round-trip verifiers;
  data-block scalar elements and interpreted refs have rendered-source and xref
  verifier layers; typed-gap/access and custom-struct candidates route through
  catalog/MAL but are blocked for loop execution by missing action-specific
  verifiers. This is the intended gate until C resolver/render and cleanup
  behavior are proven.

Initial RSSET/register-base evidence findings:

- C platform state can know an address register is an app, library, hardware,
  or layout base from policy register seeds, lookup-derived seeds, default A6
  app-base heuristics, app/library base propagation, and instruction flow.
- App-slot analysis records accesses when a base-relative operand is considered
  app-base-compatible. Listing JSON may still expose a raw displacement only as
  an `operand_parts` displacement element, as with GenAm `$0102(a6)`, while
  broader `app_slot_analysis` can still show the surrounding RSSET gap.
- Current RSSET binding mutation accepts base evidence only from an explicit
  `base_evidence_id` or from an already selected `app_slot` context. Raw
  displacement context is enough for `rsset.binding.report`, not `bind`.
  The agreed model keeps this split, but reframes the report as a
  family-specific view over generic provenance exploration.
- Existing plumbing validates two end-to-end evidence paths: explicit element
  context can carry `layout_name`, `base_symbol`, and `base_evidence_id` through
  the catalog, loop command query, Manual Action Log payload, effective
  metadata, and C selected-use renderer; selected app-slot context can derive
  `selected-app-slot:<reg>:<base_symbol>` in the catalog. The loop only carries
  RSSET evidence when a candidate already supplies it; it does not yet mine raw
  flow evidence.
- The durable evidence bridge should distinguish at least seed-backed evidence,
  flow-derived assignment evidence, selected app-slot evidence, and manual
  binding evidence. Candidate id shapes should be explicit, for example
  `register-seed:<id>`, `flow-base:<hunk>:<origin_addr>:<reg>:<kind>`,
  `selected-app-slot:<reg>:<base_symbol>`, or `manual-binding:<action_id>`.
- Manual replay already stamps RSSET bindings with `owner_action_id`, so
  descendant cleanup can be layered on manual binding ownership. Register-seed
  and flow-derived evidence are not yet exported to listing/catalog contexts as
  durable `base_evidence_id` candidates.
- Same-displacement propagation should require matching base evidence, not only
  matching register and displacement text. A later cascade can then propose or
  apply other uses that share the same proven flow identity, and unbind can
  retract only descendants owned by that binding/cascade.

Proposed RSSET base-evidence export contract:

- C analysis should export operand-scoped provenance/base evidence alongside or
  adjacent to `operand_parts`/`app_slot_refs`, for example as
  `base_evidence_refs` on the listing row for RSSET consumers. Each record
  should include `base_register`, source family, `layout_name`, `base_symbol`,
  `base_evidence_id`, status, path/lifetime scope, `origin_kind`, origin
  hunk/offset/register, confidence, optional parent/contradicted evidence id,
  and optional `source_evidence_id`.
- `base_evidence_id` should be stable and explainable:
  `register-seed:<register_seed_id>` for policy/manual seeds,
  `flow-base:<hunk>:<origin_addr>:<reg>:<kind>` for assignments or propagated
  base state, `selected-app-slot:<reg>:<base_symbol>` for already materialized
  app-slot refs, and `manual-binding:<action_id>` only for descendants of an
  accepted binding.
- The Python listing context should copy compatible base-evidence records onto
  the selected element context. The catalog may then enable `rsset.binding.bind`
  when the selected operand has a compatible `layout_name`, `base_symbol`, and
  `base_evidence_id`; otherwise it remains report-only.
- The current conservative A6 app-base fallback is useful for reporting nearby
  RSSET gaps but should not by itself become mutation evidence. Binding needs a
  seed, assignment, selected app-slot, or other durable proof that can survive
  reload and can be cited by cascades.
- Same-flow/same-displacement candidates should be generated from shared or
  verifier-equivalent provenance/base evidence. Path-specific or conflicting
  provenance requires path/lifetime selection before mutation. Candidates should
  be proposed as owned descendants of the selected binding/cascade, not silently
  implied by one selected-use binding record.
- Ownership split: `014-002` owns the durable identity contract for
  provenance evidence, `base_evidence_refs`, `source_evidence_id`, and
  descendant owner ids; `014-010` owns the first register/base provenance slice;
  `014-011` owns RSSET/app-slot provenance consumption, catalog enablement,
  bind/refine/cascade behavior, and selected-use rendering; `014-005` owns
  verifier layers for semantic reload, rendered selected-use or linked-gap
  state, exact round-trip, and later owner-scoped descendant cleanup.

Review packet:

- Approve the model if semantic/type changes should be treated as
  analysis-facing edits that consume named evidence and own generated
  descendants, while label renames, comments, and display-only representations
  stay local.
- Change the model if any presentation/source-identity edit should trigger
  flow reconciliation by default, or if any semantic/type edit should remain a
  purely local projection.
- Approve the RSSET contract if raw `zzz(an)` operands should remain
  report-only until generic provenance/C analysis exports durable base evidence
  or the selected context already carries explicit/selected-app-slot evidence.
- Change the RSSET contract if the A6 fallback should be allowed to mutate
  without seed/flow/selected-app-slot proof, or if same-displacement uses should
  be bound automatically without shared/equivalent base evidence.
- Approve the provenance contract if "where is this set/used?" exploration
  should be read-only, multi-candidate, path/lifetime-scoped, and reusable
  across RSSET, typed fields, data-block pointers, API/register semantics, and
  future memory-held values.
- Approve the issue split if follow-up work should be routed by existing owning
  issues instead of creating one implementation issue per editing family.

Accepted review decisions:

- Reconciliation trigger: label renames, comments, and display representation
  changes stay presentation/local unless they emit a semantic fact. Type
  assignments, register seeds, RSSET bindings, custom/typed field changes,
  data-block type bindings, and API/platform semantics are analysis-facing and
  need durable consumed-evidence identity plus verifier coverage.
- RSSET evidence source: C analysis should export operand-scoped
  provenance/base evidence as `base_evidence_refs` for RSSET consumers; the
  catalog should consume that evidence, not infer mutation authority from raw
  `zzz(an)` text or the A6 fallback alone.
- Generic provenance: "where is this set/used?" is read-only and should return
  all candidate definitions/usages with source family, status, path/lifetime
  scope, conflicts, and possible manual actions. Accepted classification,
  override, link, or family-specific bind/type commands write Manual Action Log
  state.
- RSSET fallback behavior: default A6 app-base inference remains report-only
  until backed by a seed, selected app-slot, assignment/flow proof, or other
  durable base evidence.
- RSSET propagation: selected-use binding remains scoped. Same-displacement
  propagation becomes a proposed or accepted cascade only when candidate uses
  share the same/equivalent base evidence and the cascade has owner-scoped
  cleanup.
- Issue ownership: `014-002` gets base-evidence and descendant-owner identity;
  `014-010` gets first-slice register/base provenance; `014-011` gets RSSET
  provenance consumption/export/catalog/bind/refine/cascade implementation;
  `014-005` gets verifier gates; `014-006` gates broad planner feed exposure.
- Typed/custom and data-block follow-up: `014-012` remains the rendered custom
  struct/typed-field implementation owner, while `014-019` remains the
  data-block type/platform binding owner.
- Matrix interpretation: completed display/classification rows remain bounded
  wins; they do not imply semantic/type cascade support without the evidence
  and verifier contracts above.
- Review outcome: accepted. Implementation may restart after these decisions
  are recorded in owning issues, beginning with `014-010` read-only
  provenance/def-use/reference reports and the needed `014-002` identity
  support. Proposal 014 remains Draft until implementation/verifier issues
  close.

Post-review issue split checklist:

- `014-002`: add the final provenance/evidence identity contract,
  `base_evidence_refs` consumer shape, source-family evidence ids,
  path/lifetime scope, `source_evidence_id`, and generated-descendant owner ids
  for semantic/type cascades.
- `014-005`: add verifier requirements for consumed evidence, equivalent-flow
  descendants, selected/rendered effect, cleanup, and exact round-trip where
  output-affecting.
- `014-006`: allow read-only provenance exploration in planner feeds, but keep
  raw/unsupported semantic candidates report-only until command, identity,
  path/conflict resolution, and verifier gates are present; document
  already-satisfied skip requirements against effective metadata.
- `014-010`: specify read-only provenance exploration commands, first-slice
  register/base provenance, evidence-scoped lifetimes, source-family
  classification, manual classification/override, and future API
  argument/return/stored-state propagation ownership.
- `014-011`: implement RSSET consumption of provenance, RSSET-shaped
  `base_evidence_refs`, bind-refine, linked gaps, same-flow/same-displacement
  candidates, and owner-scoped cascade cleanup.
- `014-012`: keep custom struct/typed-field work focused on C resolver/render
  consumption, type-shape compatibility, rendered verifier, and propagated
  typed-access cleanup.
- `014-019`: keep data-block type/platform binding separate from scalar
  layout/ref work; first bind/clear support is identity/provenance/render
  gated; nested rendering, generated review/type-flow ownership, and removal
  verification for descendants remain the next boundary.
- `014-013`, `014-014`, and `014-020`: preserve the non-semantic boundaries for
  corrections/views, data/global symbol workflows, and EQU definition display
  style unless those actions emit semantic facts.

Issue updates should now follow the post-review checklist above, preserving the
existing owning issues rather than creating one implementation issue per editing
family.

## Data Block Layout Model

Data-block layout is a first-class source-convergence concern, not a UI-only
editor feature. A human reverser often improves source by gradually turning an
opaque data range into a known-size layout: naming fields, choosing field
widths and representations, binding fields to custom or platform structs,
marking arrays and gaps, and interpreting unrelocated values as references when
local evidence supports it. The agentic loop needs the same durable capability
through Manual Action Log actions and command catalog entries, with verifiers
for rendered source, generated xrefs/type-flow facts, removal behavior, and
exact round-trip.

This model must compose with existing data roles (`014-007`), literal
representations (`014-008`), target-local EQU values (`014-009`) and EQU value
display styles (`014-020`), API/register type flow (`014-010`), struct fields
(`014-012`), and data/global symbols (`014-014`). The investigation in
`014-015-data-block-layout-and-reference-interpretation.md` chose a new
first-class layout/element metadata family. Implementation is split across
`014-016` through `014-019`, starting with scalar layout metadata and verified
GenAm rendering before interpreted references or type-flow projection.

Auto-analysis linkage must be explicit for each change family. A manual action
may consume analysis evidence, refine effective metadata, generate derived facts
such as xrefs/type-flow/review items, or be display-only. Issues must name which
of those applies, how derived facts are removed when the owning manual action is
removed, and which verifier proves the analysis-facing effect.

Analysis reconciliation is required for semantic/type-producing changes, not
for presentation-only edits. Label renames, comments, and representation choices
may remain local unless they explicitly create semantic facts. Type assignments,
register/base seeds, RSSET bindings or refinements, struct/platform field
bindings, interpreted references, and API/register semantic actions must state
which existing analysis evidence they reconcile with, which flow-equivalent
facts they may generate or propose, and how those descendants are owned and
removed.

Mistake recovery is part of the same contract. Manual state is append-only, so
undo is expressed as a corrective action: remove, unbind, clear type, suppress,
or replace. Any action that can generate rendered changes or derived analysis
facts must expose a matching cleanup command, record enough provenance to remove
only its own effects, and verify the source/analysis state after cleanup.
This is general, not data-block-specific: type propagation, generated xrefs,
code/data reclassification descendants, inferred review items, planner
candidates, and symbolic render projections must either be recomputed from live
source facts or carry an owning manual-action/source-fact identity so a later
corrective action can retract only the affected derived facts.

## Coverage Matrix

The audit below is based on current code paths in:

- `amiga_reversing/disasm/manual_actions.py`
- `amiga_reversing/disasm/manual_action_catalog.py`
- `amiga_reversing/disasm/effective_metadata.py`
- `amiga_reversing/disasm/target_metadata.py`
- `amiga_reversing/reversing_loop.py`
- `src/m68k_render_ir.c`, `src/platform_file_lib.c`, and source model headers
- focused command/source tests under `tests/`

Read the matrix through the reconciliation audit above:

- "Complete" display or classification slices do not imply semantic/type
  cascade support. They prove their bounded rendered-source effect, replay,
  cleanup, and round-trip only.
- A symbolic projection is semantic only when it has a semantic owner such as a
  semantic hint, target EQU, interpreted ref, typed field, or RSSET binding.
  Pure representation style remains presentation-only.
- Semantic/type rows need consumed-evidence identity, generated-descendant
  ownership, and verifier coverage before planner feeds may execute them
  broadly.

| Fact family | Auto-analysis / source model support | Rendered-source effect | Human manual edit need | Durable identity now | Manual Action Log now | Command catalog now | Loop now | Verifier now | Gap / issue |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Source labels and function entry labels | Facts v2 code starts, control targets, policy `seeded_code_labels`, `seeded_code_entrypoints`, absolute labels | `loc_*`, `abs_*`, entry labels and symbolic refs | Rename, create, remove, or change scope for code labels when xrefs/behavior justify the name | Listing row locator plus source/runtime label payloads; row index still appears as provenance only | Create/remove/rename/change scope labels | `label.rename` for label elements; review label actions | Planner accepts explicit label rename candidates and mines source-descriptor entrypoint evidence into autonomous `label.rename` candidates when the rendered label is still generated, skipping effective/manual labels already named; review label actions report `manual_label_state` | Label projection, semantic reload, and round-trip in row label-rename path; review-label actions verify manual label state/removal plus round-trip | Broaden autonomous label feeds beyond entrypoint evidence in `014-006` |
| Data/global symbols | `SeededEntityMetadata.name`, app-slot names, absolute/code labels, data-class rows, and rendered symbolic data refs | Replaces anonymous data labels and global slots with semantic names at definitions and use sites | Rename/create/remove data symbols, global data labels, and referenced data names from xrefs | Data row identity is hunk + source range; seeded-entity rename/remove identity is `(hunk, addr)` with optional end/source provenance; referenced data use-sites use the target hunk/offset from internal runtime-address refs and preserve existing use-site symbols as previous-name context | Data seeds can carry `name`; `rename_data_symbol` projects data-row, referenced data, and seeded-entity name overrides; seeded data symbol removal uses `suppress_seeded_item` | `row.seed.data.named`, `element.seed.data.named`, `range.seed.data.named`, and `review.seed.data.named` create named raw data seeds; data rows and internal `data_ref` elements expose `data_symbol.rename`; rows/use-sites with existing symbols also expose `data_symbol.rename_existing`; seeded entity rows expose `data_symbol.remove` | Planner recognizes explicit data-symbol rename/remove candidates, skips already-satisfied projected/effective names/removals, and mines internal `data_ref` listing elements plus data-class definition rows into autonomous data-symbol rename candidates while using `data_symbol.rename_existing` when an old symbol is known | Seed projection can render names when supplied; manual replay, effective metadata, command payload, listing annotation, command execution, rendered definition/use-site-name/removal, existing-symbol context, rename-existing command routing, and exact direct-rebuild tests cover data-row/seeded-entity rename/remove plus internal referenced data command routing; broader global verifier absent | Add broader global workflows in `014-014-data-global-symbol-naming.md` |
| Code/data classification seeds | Facts v2 decode/data spans; review items for orphan code, unreconciled data, suspicious decode | Reclassifies instructions/data and emitted directives | Classify a range as code or data, or correct a wrong classification | Hunk + source range; review item id for review-originated seeds; Manual Action Log `seed_id` for removals | Create/remove manual seed | Row/range/review seed commands for code, raw, byte, word, long, string, scalar table, pointer table; `manual_seed_conflict` review items can remove a conflicting seed by `seed_id` | Generic inspect can select review-item seed commands for orphan code and data/decode review candidates, accepts explicit range seed candidates with durable range locators, mines obvious ASCII data rows into `row.seed.data.string` candidates while skipping projected manual string seeds, and reports `manual_seed_state` verification | Manual seed replay, durable seed payload matching, removed-seed absence, and exact round-trip are covered in the loop path; broader listing seed candidate feed remains | Complete verifier/planner coverage in `014-005` and `014-006` |
| Structured data roles | C policy supports roles including string, pointer table, lookup/scalar table, copper list, palette, bitmap, sound sample, audio table, sprite, string control stream | Emits structured `dc.*`/strings/tables and navigation semantics | Choose the specific data role, unit, encoding, and range shape | Hunk + source range in `SeededEntityMetadata` | Generic data seed carries `data_role`, `unit`, `encoding` | Row/range/review catalogs expose raw data plus all supported source-rendered data roles | Planner mines obvious null-terminated printable ASCII data rows into string role candidates, skips effective/projected existing data roles, and accepts explicit `range.seed.data.*` candidates; broader role inference remains open in `014-006` | Per-role tests prove Manual Action Log semantic reload, rendered metadata projection, and exact direct rebuild | Complete in `014-007-data-role-command-coverage.md` |
| Data-block layouts and interpreted data references | Data ranges, data roles, manual representations, data-symbol names, runtime address refs, custom structs, RSSET regions, target equates, type-flow facts, and parsed NDK include data exist as separate mechanisms | Split opaque data blocks into ordered elements, render element-sized `dc.*`/runs/gaps, apply nested custom/platform structs or arrays, and turn non-relocated values into symbolic refs/xrefs | Break a data block into smaller elements; assign element sizes, representations, ad hoc fields, formal/platform struct fields, arrays, padding, EQU/enum domains, and interpreted reference semantics | Core metadata implemented as first-class `DataBlockLayout` plus nested `DataBlockElement`: target-local `layout_id` is the durable layout identity; create requires hunk/source range, edit/remove may target by id but validate any supplied hunk/source range as stale-edit context; element identity is layout id + offset; interpreted-reference identity is a durable data-block ref id carrying owner layout id and element offset | Manual Action Log now projects `create_manual_data_block_layout`, `edit_manual_data_block_layout`, `remove_manual_data_block_layout`, `set_manual_data_block_element`, `remove_manual_data_block_element`, `represent_manual_data_block_element`, `interpret_manual_data_block_element_ref`, `remove_manual_data_block_element_ref`, overlap conflicts, explicit replacement, stale range blocking, removed raw/gap state, element representation state, interpreted-reference state/cleanup, and data-block element type-binding state; effective metadata projects scalar elements into renderable seeded entities, element-scoped manual representations, active interpreted refs onto owning `DataBlockElement.reference_interpretation`, accepted custom-struct bindings into typed seeded field/gap entities when the bound shape fits, parsed NDK platform struct bindings into typed field entities with alias/inherited/nested expansion, and scalar domain bindings into `value_domain` metadata for symbolic values; supported absolute byte/word/long refs also project through guarded target-local `EQU` plus element-scoped symbolic representation, and owned source-row runtime-address refs carrying target locator and cleanup identity | Row/range layout creation commands `row.data_block.layout.create` and `range.data_block.layout.create` append through the public catalog; row/range element set/remove/represent commands infer active `layout_id` + offset from selected layout context or accept explicit identity parameters, and range representation uses applicable subranges like set/remove; row interpreted-reference interpret/clear commands append durable manual ref facts with source-value, target-locator, reference-kind, and element-width guards; row type-bind/clear commands append durable element-scoped bindings | No autonomous data-block layout feed; planner must stop on unsupported element/type/ref capability rather than improvise scripts/comments; real scalar GenAm table proof exists for command/verifier follow-up | Replay/effective metadata projection tests cover core state, overlap replacement, zero-offset preservation, removal, stale edit/remove blocking, scalar byte/word/long and character/gap/padding render projection including compact `dcb.b`, representation precedence, command execution for layout and element commands, active-layout identity inference, layout and element removal back to raw source, interpreted-reference replay/removal state, effective metadata projection/cleanup, command execution, symbolic render projection/cleanup, loop interpreted-ref state, loop layout/element state plus affected-row rendered-source directive/value verifiers, unsupported type/ref blocking, C-backed exact reassemble smoke, interpreted-reference source-owned runtime refs with owner identity and cleanup verifiers, >16 interpreted-ref table render/rebuild coverage, a real GenAm `ascii_hex_digit_value` table render/rebuild smoke, row type-bind/clear verifier gates, provenance-backed type-binding gates, custom/platform struct binding field render/rebuild proof, and scalar domain symbolic render/rebuild proof; gap-specific source rendering, target-side inbound xref navigation, generated type-flow/review-item verifiers, and owner-scoped descendant cleanup remain planned | Core metadata implemented in `014-016`; scalar create/render/command/verifier slice complete in `014-017`, interpreted refs in `014-018`, and type/platform binding in `014-019` |
| Comments and review notes | Policy entry comments render; review notes create review items only when tracked | Comments in source/listing; notes in review workflow | Add semantic comment only when no structured fact can represent the discovery; add/edit/clear review notes for workflow state | Hunk + source range plus comment/note ids | Create/remove comments; add/edit/clear notes | `comment.edit`, `review_note.*` | Comment path exists but is not source-converging unless no structured action fits | Manual log, semantic reload, projected comment; no source-value verifier needed for note-only | Keep as fallback-only; planner must not prefer it in `014-006` |
| Immediate representation | Render policy has manual representations; source data supports numeric/string expressions | Hex/binary/character/string for data; selected hex/binary/character display for instruction immediates | Choose operand/data literal representation when the display carries domain meaning | Hunk + source range + element provenance; operand-scoped representations now preserve `operand_index` | Create/remove manual representation | `representation.choose/hex/binary/character` on immediates and data literals | Generic planner ranks representation commands above fallback comments, skips already-satisfied projected representation candidates, and can feed byte printable-immediate listing candidates | Manual log hash/count, semantic reload, refreshed rendered text, and round-trip tests cover data literals and instruction immediates; GenAm smoke passed for `subi.b #'0'` rendering | Broaden autonomous representation candidate kinds as needed in `014-006-loop-planner-command-selection.md` |
| Equates/constants | Source model supports constants/EQU; NDK constants are searchable; C policy supports a bounded target-local equate table | Known NDK equate hints replace magic immediate values with included symbols; target-local equates render as `EQU` definitions and can be used by manual symbolic immediate representations | Add/edit/rename/remove a target-local constant, bind use sites to it, and choose definition value display when source meaning depends on hex/decimal/binary/char/symbolic form | NDK equate use has hunk + source range + operand provenance; target-local equates use symbol name as durable identity; EQU definition representation is display metadata on the same target-equate identity | `create_manual_semantic_hint` for `domain="equate"` projects known symbols into manual symbol representations; `create_manual_target_equate`, `rename_manual_target_equate`, and `remove_manual_target_equate` project target-local constants; rename updates symbolic use-site representations and remove prunes them; target-equate payloads can carry definition `value_representation`/`value_expression` | `semantic.equate.*` candidates for matching immediate values; target catalog exposes `target.equate.add/edit/represent/rename/remove` with create/rename/remove local effects | Planner accepts explicit `semantic.equate.*` use-site candidates and explicit `target.equate.*` target candidates with target-equate state verification and exact round-trip, and skips already-projected target-local equates | Effective metadata projection, rendered include/symbol, rendered target-local `EQU`, symbolic use-site rendering, C-backed equate navigation, rename/remove rendered-source behavior, loop target-equate state verification, definition value style render, and exact direct rebuild are covered; current C policy table is capped at 128 target-local equates, matching generated interpreted-ref/manual representation scale | Core complete in `014-009-equate-constant-editing.md`; definition display style implemented in `014-020-target-equate-value-representation.md` |
| LVO/API semantics | NDK libraries/LVOs, render lookup platform calls, call summaries and API arg analysis | `_LVO*` symbols, NDK field symbols, library call summaries, typed args/returns, app-slot propagation | Confirm library base, LVO function, API argument/return semantics, struct-offset meaning, and propagated stored state | LVO and struct-offset immediate use has hunk + source range + operand provenance; API semantic identity not complete | `semantic.lvo.*` and `semantic.struct_offset.*` hints for immediate operands project to manual symbol representations; register seeds can seed a library base | `semantic.lvo.*`, `semantic.struct_offset.*`, and `semantic.library_base.<library>` for A6 LVO contexts using API metadata or NDK lookup | Planner accepts explicit dynamic semantic command candidates for `semantic.library_base.*`, `semantic.lvo.*`, `semantic.struct_offset.*`, and `semantic.equate.*` with selected element context and round-trip verification, and skips already-projected library-base register seeds | Effective metadata projection, rendered include/symbol, and exact direct rebuild covered for LVO and struct-offset immediate use; library-base catalog execution covers exec and API-specific libraries; register seed render test exists | Add consumed API/register/typed-field semantic actions in `014-010-api-register-semantic-actions.md` |
| Register/base facts | `entry_register_seeds` support library base and struct pointer; render policy consumes them | Base-relative references become library/struct-aware | Add/remove register base facts with explicit lifetime/evidence | Entry offset + register + kind; not enough for all base lifetimes | Create/remove manual register seed | A6 LVO library-base helpers derive supported libraries from row API metadata or NDK library/function lookup; register elements expose a parameterized `semantic.register.struct_ptr` helper | Planner accepts explicit `semantic.register.struct_ptr` candidates with selected register element context and round-trip verification, mines unresolved typed-access listing evidence into struct-pointer candidates, and skips existing struct-pointer seeds from effective metadata; evidence-scoped lifetime inference remains open | Manual register seed render test exists; catalog coverage covers exec/non-exec LVO base helpers and register-selected struct-pointer seeds | Expand identity/commands/verifiers in `014-010-api-register-semantic-actions.md` |
| App/base-relative slots and RSSET layout regions | App-slot refs, app-slot analysis, regions/gaps/field gaps/suggestions, `rsset_layout_regions`, named layouts; raw numeric base-relative operands can still lack `app_slot` context | `RSSET`/`RS.*`, `app_0234(a6)` names, typed field paths; RSSET binding can link `$NNNN(a6)` use-sites to a chosen layout before field creation | Add/edit/rename/remove slots, regions, sizes, storage kinds, semantic types, parser roles, layout gaps, and explicit numeric-displacement use-site bindings with reversible bind/refine/unbind cleanup | App-slot context has symbol/displacement/base/access; manual RSSET region identity is `(layout_name, base_symbol, offset)`; chosen binding identity is target + hunk + source address + operand index + base register + displacement + `(layout_name, base_symbol)` + base-evidence id; missing contract is exported operand-scoped `base_evidence_refs` for register-seed and flow-derived base proof | `create_manual_rsset_layout_region` adds/replaces manual RSSET layout regions; `remove_manual_rsset_layout_region` filters regions by identity; `create_manual_rsset_use_site_binding` and `remove_manual_rsset_use_site_binding` project selected-use binding state with MAL `owner_action_id`; active bindings also project into effective target metadata/C policy so an explicitly bound use can render an existing matching field without broad same-displacement propagation; planned refinement actions are `create_manual_rsset_binding_type_refinement` and `remove_manual_rsset_binding_type_refinement` | `target.rsset_region.add/edit/rename/remove` expose target-level RSSET changes including parser role metadata; `app_slot.rename/edit/remove` expose selected app-slot rename/edit/removal; `rsset.binding.report` is broad/read-only for selected numeric displacements and reports source locator, operand facts, base evidence, current field/gap state, nearby fields, same-displacement uses, type compatibility, expected cascade, and missing verifier blockers; `rsset.binding.bind/unbind` require explicit app/RSSET base evidence such as app-slot context, candidate-supplied `base_evidence_id`, or future `base_evidence_refs`; planned refinement commands are `rsset.binding.bind_refine/type_refine/clear_type` | Planner recognizes explicit target RSSET, selected app-slot add/edit/rename/remove, and explicit RSSET binding candidates carrying base evidence; it skips already-satisfied projected target RSSET/app-slot state including effective target metadata, mines listing `app-slot-suggestions` into add/edit candidates, preserves parser metadata, and reports `rsset_region_state` or `rsset_binding_state`; broad binding feeds wait for selected-use verifier proof plus exported base evidence in `014-011` | Manual replay, effective metadata, command payload/execution, rendered RSSET field/reference, removal-to-raw-reference, app-slot command execution, parser-role payload projection, planner alias/autonomous suggestion selection, app-slot already-satisfied skip, RSSET binding replay/cleanup verification, loop RSSET-region/binding state verification from durable action payloads, richer report coverage for GenAm `$0102(a6)` gap/base-evidence blockers and same-displacement use scope, and exact direct-rebuild tests cover add/edit/rename/remove and bind/unbind payloads; C-backed selected-use render/rebuild now covers an existing-field bind while another same-displacement use stays raw; bind-refine field creation, linked field cleanup, owned cascade retraction, exported `base_evidence_refs`, and type/xref checks remain planned where applicable | Continue app-slot/RSSET editing and binding implementation in `014-011`; investigation complete in `014-021`; identity/catalog/verifier/planner/type/correction follow-ups stay in `014-002`, `014-004`, `014-005`, `014-006`, `014-010`, `014-012`, and `014-013` |
| Custom structs, fields, and typed accesses | `custom_structs`, RSSET regions, typed accesses, unresolved typed gaps, type-flow analysis | Struct field refs, typed field paths, gap navigation | Add/edit/rename/remove structs and fields; resolve typed gaps/accesses | Struct identity uses name; field identity uses `(struct_name, offset)` with field name carried for context; typed-access commands use selected element context and accepted `struct_pointer` evidence identity | Custom struct and field add/edit/rename/remove actions project into effective metadata; field identity is `(struct_name, offset)`; C policy imports custom structs and can render register-seed-backed custom field paths | `target.custom_struct.add/edit/rename/remove`, `target.custom_struct_field.add/edit/rename/remove`, `typed_gap.field.add/edit`, and `typed_access.field.edit/rename/remove` emit durable struct/field payloads and command execution local effects; typed commands persist consumed provenance | Planner can form explicit target custom-struct/field and selected typed-gap/access field command candidates, skips already-projected struct/field state, blocks unproven typed-field changes before execution, and keeps target-wide metadata commands blocked without selected rendered-field proof | Manual replay, command payload, command execution, effective metadata projection, already-satisfied planner skips, C metadata import, backend render smoke, accepted-provenance gating, and selected-row rendered-source verification cover custom struct and field add/edit/rename/remove plus direct target metadata rendering; type-shape checks and propagated cleanup remain missing | Add type-shape checks and cleanup for custom struct metadata in `014-012-structure-field-editing.md` |
| Runtime/execution views and loader ranges | `execution_views`, runtime address ranges, runtime view starts, absolute labels | ORG/runtime labels and copied-stage source | Add/edit/remove runtime views for copied or relocated code/data when auto-analysis lacks evidence | Execution view identity is `(source_start, source_end, base_addr)` plus replay owner/cleanup action ids; absolute labels use label identity | `create_manual_execution_view` adds/replaces manual execution views with owner identity; `remove_manual_execution_view` removes by identity and records cleanup identity; absolute labels can be created through label path | `target.execution_view.add/edit/remove` for target context; label rename only for labels | Planner accepts explicit `target.execution_view.*` command candidates with target context and round-trip verification, verifies owner/cleanup ids, and skips already-projected execution views | Manual replay, effective metadata, command payload, target command execution, owner/cleanup verification, and source/reproduction tests cover execution-view add/edit/remove; broader correction verifiers remain open | Add broader correction/view actions in `014-013-correction-and-view-actions.md` |
| Auto-analysis corrections and suppressions | `target_corrections.json`, `suppressed_seeded_items`, reproduction mismatches, blockers | Removes wrong imported/seeded facts and unblocks source render | Suppress or override target-specific auto facts only when upstream analysis is not objectively wrong for a whole class | Suppression identity is hunk + addr + seeded item kind; listing rows carry suppressible seeded source id/path/locator provenance | `suppress_seeded_item` projects target-specific seeded item suppressions | `correction.suppress_seeded_item.<kind>` row commands append seeded-item suppressions; review/reproduction correction commands absent | Planner accepts explicit `correction.suppress_seeded_item.*` candidates with row context and round-trip verification, and skips already-projected suppressions | Manual replay, effective metadata, command payload, and listing annotation tests cover seeded-item suppression; review/reproduction command verifier absent | Add execution-view and broader correction actions in `014-013-correction-and-view-actions.md` |
| Importer/analysis defects | Target import and parser logic derives target type, bootblock, resident, library/device, autoinit, and seeded facts | Corrects all affected targets by improving auto-analysis output | Fix importer/parser/analyzer upstream when a whole class of targets is objectively detected or parsed wrong | Source artifact and regression fixture identity, not per-target manual identity | Not a Manual Action Log action | Not a command catalog edit | Loop stops with implementation issue | Regression tests plus affected render/reproduction checks | Keep out of manual correction path; track as importer/analyzer bugs, or split from `014-013` when discovered |
| Review items and typed resolutions | Manual review items for conflicts, malformed logs, orphan code, unreconciled data, suspicious decode, reproduction mismatches, blockers, review notes | Clears blockers or records decisions | Resolve only with type-specific evidence and verifier | Review item id + evidence fingerprint | Resolve review item; review note actions | Review item actions for current kinds | Generic inspect uses review candidates and explicit review-item command candidates for seed create/remove and label edits; broader autonomous source-value ranking remains open | Review-item source actions route through semantic reload plus round-trip; type-specific verifiers remain incomplete | Complete through `014-005` and `014-006` |

Important audit finding: semantic hints are not automatically
source-converging. Known NDK equate, LVO immediate, and struct-offset immediate
hints now project through `effective_metadata.py` into rendered symbolic
immediates; selected typed-field access now has provenance-backed rendered
proof. API/register lifetime, target-local equate edit hints, broad
typed-access propagation, and cleanup still need effective metadata projection
or rendered-source verification before they count as source-converging.

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

Implementation observation from `014-009`: target-equate command parameters
must be normalized to catalog-owned identity/value fields before planner
satisfaction checks. Provenance/report fields can explain why an EQU candidate
was proposed, but they are not part of target-equate state and must not keep an
already-projected add/edit/rename/remove candidate executable.

Implementation observation from `014-020`: EQU definition value style is
display-only but still travels through the C policy struct. Adding arbitrary
per-equate expression text to the stack-resident `M68kAnalysisPolicy` overflowed
native C tests, so symbolic expression display currently uses bounded inline
storage. If longer expressions become necessary, move optional target-equate
strings out of the stack-heavy policy arrays instead of enlarging every slot.

Implementation observation from `014-020`: display-style command parameters
must stop at the display payload. Planner/report fields such as evidence ids or
path lifetime scope can be ignored by catalog execution but still pollute
already-satisfied checks, making presentation-only EQU edits look like accepted
provenance writes or never-satisfied commands.

Implementation observation from `014-012`: round-trip exactness alone is not a
valid verifier for custom-struct commands while action-specific rendered-field
proof is missing. The loop should surface a missing action-specific verifier
instead of executing metadata-only struct edits as source-converging work.

Implementation observation from `014-006`/`014-012`: the missing-verifier guard
must run immediately before non-dry execution, not only during planner
selection. Tests can force selections, and stale reports can carry commands
whose verifier support has since been removed.

Implementation observation from `014-006`/`014-012`/`014-019`:
pre-execution provenance gates must distinguish consumed evidence from cleanup
evidence. Direct command/parameter `source_evidence_id` is the write input;
nested cleanup scopes may mention older evidence but cannot satisfy the accepted
provenance prerequisite for typed-field or data-block type writes.

Implementation observation from `014-005`: the same cleanup/evidence boundary
applies to executed durable results. A nested `cleanup_scope.source_evidence_id`
records which old descendants are being removed; it is not consumed provenance
for the new mutation and must not trigger the generic provenance layer.

Implementation observation from `014-006`: catalog availability for
evidence-bearing writes must compare the full consumed provenance boundary, not
just the command id and target coordinate. For typed-field and data-block type
writes, mismatched `source_evidence_id`, path/lifetime scope, conflict or
override fields, or cleanup scope should stop before execution.

Implementation observation from `014-006`: already-satisfied checks for rename
commands must compare projected state to the requested new identity. Comparing
all command parameters treats `previous_name` as required future state and can
repeat a rename after it has already converged.

Implementation observation from `014-006`: planner reports must show the
candidate-specific verifier used for selection. Static command defaults are only
fallbacks and can misdescribe candidates with stricter projection verifiers.

Implementation observation from `014-006`: a candidate's generic `round_trip`
fallback must not override a stricter command-specific verifier. Explicit or
older candidates can carry stale verifier labels, so planner summaries should
prefer command-specific state verifiers whenever they are more precise.

Implementation observation from `014-005`: broad prefix fallbacks to
`round_trip` are unsafe for source-valued command families. Unknown
`data_symbol.*` or semantic commands should stop as missing-verifier work until
their rendered/state verifier is explicit.

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

Implementation observation from `014-015`: data-block layout needs a new
ordered metadata family. Seeded entities, manual representations, RSSET
regions, custom structs, target equates, and runtime-address refs each cover a
piece, but none owns stable child elements, removal semantics, generated xrefs,
and type-flow projections together.

Implementation observation from `014-015`: runtime-backed layout identity must
include source/origin execution-view identity. Runtime address alone is not
durable for copied or relocated data and can misattribute layout facts across
execution views.

Implementation observation from `014-015`: the first implementation slice
should be scalar layout rendering only. GenAm `loc_0_00001442` provides a real
ASCII hex digit lookup table with local xref evidence, exact bytes, and no need
to solve enum domains, interpreted references, or type-flow before proving the
layout command/render/verifier path.

Implementation observation from `014-011`: app-slot suggestions and platform
API-derived app-slot regions can describe the same durable RSSET identity.
Autonomous candidates must de-dupe by `(layout_name, base_symbol, offset,
symbol)` so the planner does not repeat equivalent edits.

Implementation observation from `014-010`: autonomous struct-pointer register
seeds need a concrete register element, not just a typed-gap element, because
`semantic.register.struct_ptr` is exposed and executed through register element
context.

Implementation observation from `014-006`: planner candidates can expose more
than one command option. Selection must evaluate each option's verifier and
durable context, otherwise one unverified option can hide a valid supported
action from the same evidence.

Implementation observation from `014-006`: command availability is also
option-specific. A candidate can have a valid lower-ranked catalog command even
when the first selected command is unavailable, so non-dry execution must retry
eligible alternates before reporting a command-coverage blocker.

Implementation observation from `014-006`: source descriptor entrypoint evidence
can drive a structured label rename before falling back to an entrypoint
comment, but only when the current listing label is still generated and matches
the same hunk/offset identity.

Implementation observation from `014-005`: once `label.rename` is reachable
through generic `run-one`, verification must remain label-specific. Generic
projection metadata is insufficient without checking the semantic label and the
rendered label row at the selected source location.

Implementation observation from `014-005`/`014-006`: `review.label.*` actions
mutate manual label state through review item ids, not listing row locators.
Their verifier should derive the expected label payload or removed label id
from the executed durable action payload, then check the reloaded Manual Action
Log projection and round-trip instead of generic `round_trip`.

The same applies to fallback comments: generic `run-one` must verify the
projected comment text, not merely that command execution reported an affected
locator.

Implementation observation from `014-006`/`014-014`: data-class annotations on
definition rows are durable enough to feed row-level data-symbol naming. Use the
row hunk/offset identity and skip projected names before proposing a rename.

Implementation observation from `014-006`: source-label feeds also need
effective metadata skips, because generated listing text can lag projected
label state during a loop iteration.

Implementation observation from `014-010`: struct-pointer candidates should use
any selectable operand context that carries the base register, not only operands
whose element kind is `register`; memory operands often carry the register via
operand metadata.

Implementation observation from `014-005`: data-symbol rename verification must
look at the refreshed listing text/name at the selected source location. An
affected-locator echo proves command execution touched a row, but not that the
source now renders the requested symbol.

Implementation observation from `014-005`/`014-010`:
`semantic.register.struct_ptr` produces register-seed state, not row projection
state. Its verifier should check the reloaded register seed and round-trip
instead of affected locators.

Implementation observation from `014-005`/`014-010`: register-seed verifiers
must derive their expected seed from the executed durable action payload before
matching reloaded project state. Command intent plus matching project state can
otherwise mask a missing or mismatched action result.

Implementation observation from `014-005`/`014-010`:
`semantic.library_base.*` also produces register-seed state. Its verifier should
check the reloaded library-base seed and round-trip instead of affected
locators. Planner summaries should report the semantic state verifier names, not
generic `round_trip`, so operators can see which state is being checked.

Implementation observation from `014-005`/`014-009`: target-equate commands
produce target metadata state. Their loop verifier should derive the expected
equate from the executed durable action payload, then check the reloaded
target-equate, rename, or removal projection and round-trip, not only the
command's local-effect echo.

Implementation observation from `014-005`/`014-011`: target RSSET and selected
app-slot commands produce RSSET-region state. Their loop verifier should derive
the expected region from the executed durable action payload, then check the
reloaded region/removal projection and round-trip, not only the command's
local-effect echo.

Implementation observation from `014-006`/`014-011`: the first real GenAm
autonomous RSSET smoke proves the `app-slot-suggestions` feed through
`target.rsset_region.add`, Manual Action Log replay, reloaded RSSET metadata,
rendered `RS.*` source, and exact round-trip status. Use the same evidence shape
before widening other autonomous feeds.

Implementation observation from `014-005`/`014-014`:
`data_symbol.remove` produces suppressed seeded item state. Its verifier should
check that reloaded suppression and round-trip instead of affected locators.
Planner summaries should expose the same action-specific verifier names so
operators can distinguish rendered symbol checks from suppression-state checks.

Implementation observation from `014-010`:
Listing rows with LVO API-call metadata are enough to produce conservative
`semantic.library_base.*` candidates when the selected symbol operand carries a
base register and API library/function identity.

Implementation observation from `014-006`/`014-010`: real target evidence can
sit far outside the first listing page. GenAm direct LVO rows first appeared
around row 8030, so source-candidate mining needs bounded pagination rather
than a single 2048-row sample.

Implementation observation from `014-005`/`014-010`:
`semantic.lvo.*`, `semantic.struct_offset.*`, and `semantic.equate.*` produce
semantic-hint state. Their verifier should check the reloaded hint and
round-trip instead of affected locators.

Implementation observation from `014-005`/`014-006`: row/range/review seed
commands produce manual seed state, and `review.seed.remove` removes that state
by seed id. Their verifier should derive the expected seed or removed seed id
from the executed durable action payload, then check the reloaded Manual Action
Log projection and round-trip instead of affected locators.

Implementation observation from `014-006`/`014-014`:
`runtime_address_refs` without a `data_class` can still support conservative
global naming when they carry a stable runtime address; use
`runtime_address_XXXXXXXX` rather than dropping the candidate.

Implementation observation from `014-014`: data-symbol naming needs a visible
rename-existing path when the source already has a generated or previous
symbol. The durable action remains `rename_data_symbol`, but the catalog and
planner should surface `data_symbol.rename_existing` when `previous_name` is
known so operators can distinguish replacement from first naming.

Implementation observation from `014-014`: data-symbol command parameters must
not double as provenance reports. Candidate and embedded command payloads should
strip xref/source-family evidence before execution; the catalog row/element
context supplies source identity, while separate semantic commands own any
accepted provenance or type-flow descendants.

Implementation observation from `014-005`/`014-013`:
Seeded-item correction commands produce suppression state just like
`data_symbol.remove`; their verifier should check the reloaded suppression and
round-trip instead of affected locators.

Implementation observation from `014-006`/`014-013`: seeded-item correction
availability must compare the selected suppression identity `(kind, hunk, addr)`
against the refreshed catalog entry. A row-level
`correction.suppress_seeded_item.*` command id alone is not enough authority to
suppress a different analyzer/imported fact.

Implementation observation from `014-005`/`014-013`:
Execution-view commands produce target runtime view state; their verifier should
check the reloaded execution view or removed-view identity plus round-trip
instead of accepting target local-effect metadata alone.

Implementation observation from `014-012`: custom struct and typed-field Manual
Action Log entries project into effective target metadata, and the C analysis
policy now imports `custom_structs` into the typed-reference resolver for
register-seed-backed field rendering. Keep target-wide custom-field writes and
propagated typed-access cleanup blocked until they have selected rendered-field
verification, accepted provenance consumption, and owner-scoped cleanup proof.

Implementation observation from `014-012`: selected typed-field writes need both
the consumed provenance id and the write owner id in projected state. Matching
only `(struct_name, offset, name)` during semantic reload can hide a stale or
wrong evidence link, so the verifier treats consumed provenance and owner
metadata as part of selected custom-field state.

Implementation observation from `014-012`: accepted `struct_pointer`
provenance is necessary but not sufficient for a selected typed-field write.
When the selected access width is known, pre-execution gating must reject a
field size that does not match the observed access before command execution.

Implementation observation from `014-006`: loop command-availability queries
must preserve the selected command context exactly. Range commands use
`context=range` plus serialized locators; falling through to target context
makes valid range seed candidates look unavailable in non-dry execution.

Implementation observation from `014-021`: numeric base-relative operands need
an explicit RSSET use-site binding fact before field creation. Binding
`$NNNN(a6)` directly by creating an `RS.*` field can create unlinked fields and
cannot retract generated xrefs/type-flow cleanly after a bad choice.

Implementation observation from `014-021`: exploratory RSSET reports must show
the candidate layouts, base evidence, current field or gap, access width,
nearby fields, expected cascade, and missing verifiers before mutation. A
bind-only action may leave raw rendering in place when no field exists yet.

Implementation observation from `014-021`: generated binding cascades need
owner action ids. Same-displacement missed-use candidates, linked gaps, review
items, xrefs, and type-flow facts must be removable by unbind or clear-type
without deleting unrelated accepted RSSET fields.

Implementation observation from `014-002`/`014-021`: Manual Action Log records
already persist stable `action_id` values and replay rejects duplicates. RSSET
binding cleanup can use those ids as `owner_action_id`; the remaining identity
work is numeric use-site/base-evidence identity and cascade ownership on
generated descendants.

Implementation observation from `014-011`: the first bind-only RSSET slice keeps
missing-field source rendering conservative. `rsset.binding.bind` persists the
selected use-site and exposes linked-gap/raw render state; symbolic selected-use
rendering is still gated on an existing field or a later bind-refine field
action.

Implementation observation from `014-011`: command-catalog support for raw
numeric RSSET operands depends on native listing JSON exposing them as
selectable operand parts. GenAm `$0102(a6)` had access metadata but no
`operand_parts`, so the first real smoke required emitting raw
address-register displacement operands with `base_register`, `displacement`,
and `operand_index`.

Implementation observation from `014-011`: exploratory RSSET binding reports
need app-slot navigation analysis at command-locator time, not just the selected
row. Without the current region/gap view the report can prove that mutation is
blocked, but it cannot explain whether a displacement is an existing field, a
one-byte gap, or an ambiguous layout candidate.

Implementation observation from `014-011`: same-displacement binding scope is a
listing-wide question, not a selected-row question. The report should summarize
matching raw/app-slot uses before any cascade feed is widened, so a bind/refine
proposal can state exactly what later same-displacement propagation would touch.

Implementation observation from `014-011`: selected-use RSSET rendering needs
the binding fact in effective target metadata, not only Manual Action Log replay
state. The C renderer now consults the selected binding before normal register
base-state checks, so an existing field can render at one proven use without
forcing every same-displacement raw use to change.

Implementation observation from `014-011`: selected-use rendering and bind-only
navigation are separate. The current C policy path can render an existing field
for one bound operand, but linked-gap/listing navigation for a binding with no
field still needs an explicit projection before `bind_refine` can be called
complete.

Implementation observation from `014-016`: overlapping manual data-block
layouts should produce reviewable conflict state unless replacement is explicit.
Blocking the entire Manual Action Log as malformed would hide unrelated valid
manual facts; projecting the existing layout and emitting
`manual_data_block_layout_conflict` keeps recovery append-only and local to the
bad layout choice.

Implementation observation from the first `014-017` slice: scalar data-block
rendering can reuse the existing source renderer by projecting effective
data-block elements into renderable seeded entities plus element-scoped manual
representations. That gives immediate exact-rebuild proof without adding
type-flow or interpreted-reference derivations; deeper element commands and
verifiers still need native data-block-specific coverage.

Implementation observation from the `014-017` verifier review: rendered-source
checks for scalar data-block elements must prove the exact emitted directive
family (`dc.b`, `dc.w`, `dc.l`, `dcb.b`) and removal restore evidence. Broad
nearby-token checks such as `dc.` are smoke coverage only and can pass on
unrelated source.

Implementation observation from `014-019`: custom-struct data-block binding can
reuse the seeded-entity structured-data renderer if effective metadata projects
each bound field, plus explicit gaps, as renderable child entities. This gives
typed comments and exact-rebuild proof without copying include text, but the
projection currently uses seeded entity source locators for binding identity;
generated type-flow/review descendants still need first-class owner/evidence ids
before broad cleanup can be verified.

Follow-up observation from `014-019`: parsed NDK platform structs fit the same
projection shape once C aliases are resolved to assembler struct ids and base or
nested struct fields are flattened before render. This avoids embedding include
text in manual actions. The remaining boundary is semantic ownership: inherited
and nested field projections render correctly, but generated type-flow facts and
review items still need owner-scoped descendant identity before automatic
propagation or cleanup should run.

Follow-up observation from `014-019`: scalar enum/equate domain bindings do not
need a parallel renderer. Projecting the bound domain as structured-data
`value_domain` lets the existing value-domain renderer choose symbols such as
`NT_LIBRARY` and keeps exact rebuild proof local to the bound element. This is
still a render-only fact until generated type-flow/review descendants have
owner-scoped identity.

Implementation observation from `014-019`: data-block bind-type verification
must treat the projected type-binding `owner_action_id` as part of semantic
reload state. Matching only layout/offset/bound type can hide stale or
mis-owned bindings, so bind verification now derives the expected owner from
the durable Manual Action Log action id.

Implementation observation from `014-019`: clear-type is also an ownership
boundary. The previous binding must remain available for stale render checks,
but it also needs `cleanup_action_id` in replay and verifier state so a later
clear/rebind sequence cannot satisfy cleanup proof with the wrong action.

Implementation observation from `014-019`: generated structured-data seeded
entities are the first concrete descendants of a data-block type binding. Until
type-flow/review descendants have dedicated owner fields, the verifier should at
least require active bindings to project seeded descendants with
`source_locator=type_binding_id` and clear-type to remove descendants with the
cleared binding id.

Implementation observation from `014-006`/`014-019`: data-block type bind/clear
availability must compare the selected element identity `(layout_id, offset,
width)` against the refreshed catalog entry. The command catalog does not choose
the bound type or provenance evidence, but it must still prevent a stale
type-binding candidate from executing against a different data-block element.

Implementation observation from the `014-018` guard slice: interpreted data
references must not become output-affecting from target intent alone. Durable
actions carry decoded selected source bytes as `source_value`, and replay must
prove reference kind, target locator, element width, and decoded value agree
before later render/xref projection can use the fact.

Implementation observation from the `014-018` symbolic-render slice: C rendering
had separate byte, word, and long data directive paths. Supporting symbolic
interpreted refs required the word/long structured-data path to consume exact
manual symbol representations too; otherwise effective metadata could contain a
valid symbol projection while rendered source stayed numeric.

Implementation observation from the `014-018` xref slice: interpreted-reference
xref projection needs a distinct owned runtime-address-ref metadata family.
Reusing symbolic render metadata is not enough because cleanup verification must
match source span, target hunk/offset, owning layout id, element offset, and
interpreted-ref id. C target validation should reject generated xrefs whose
target hunk/offset is outside target-local source.

Implementation observation from the `014-018` scalability correction:
interpreted-reference symbols can be emitted for every proven table element, so
they must not depend on a tiny human-edit EQU capacity. The current bounded C
policy table is 128 entries to match manual representation and runtime-ref
projection scale; a future larger table should move target equates out of the
stack-heavy policy struct.

Implementation observation from the `014-018` xref review: current
runtime-address-ref projection is source-owned. It proves the source row carries
the target locator and cleanup owner; it does not yet create target-side inbound
navigation. Documentation and verifiers must keep that distinction explicit
until inbound xref projection exists.

Implementation observation from `014-010`: selected element context re-selection
can drop server-only identity fields unless they are explicitly preserved.
Provenance evidence ids need target identity carried through catalog lookup, not
only through the request cache key.

Implementation observation from `014-010`/`014-002`: parent provenance identity
is a set of dependencies, not a single pointer. Generated `source_evidence_id`
values must include every parent evidence id; otherwise two path-specific
accepted base classifications that share the first parent can collapse to one
consumable write authority.

Implementation observation from `014-011`: RSSET `base_evidence_refs` should
carry `parent_evidence_ids` as the durable dependency set. A single parent id
field loses proof shape once register/base provenance depends on multiple
definitions, overrides, or flow joins.

Implementation observation from `014-005`: provenance-backed writes need a
generic verifier layer in addition to family-specific state/render checks. The
layer should fail command-only evidence, unresolved or conflicting evidence,
missing path/lifetime scope, missing source family/status, and generated
descendants without `owner_action_id`; family commands must persist those fields
before planner execution can consume generic provenance broadly.

Implementation observation from `014-005`: consumed provenance identity must be
checked across the write boundary. If a selected command names
`source_evidence_id`, the durable action payload must replay that same id; an
otherwise accepted durable evidence payload with a different id is a verifier
failure, not proof that the requested evidence path was consumed.

Implementation observation from `014-013`: `manual_override` provenance evidence
is a correction boundary, not just another accepted status. The command payload
and durable replay must carry `contradicted_evidence_id`, reason, path/lifetime
scope, and cleanup scope before planner execution or post-mutation verification
may accept the write.

Implementation observation from `014-013`: pre-execution override gates must
validate the correction boundary fields by type, not truthiness. Non-string
`contradicted_evidence_id` or reason values can otherwise slip past planner
selection and fail only after mutation.

Implementation observation from `014-013`: override cleanup ownership must point
at the contradicted fact. For `owned_descendants`, `cleanup_scope.source_evidence_id`
must equal `contradicted_evidence_id`; otherwise a manual override can claim
cleanup proof for a different stale evidence path.

Implementation observation from `014-013`: execution views are correction/view
state but still need action ownership in the Manual Action Log projection.
Create/edit views now stamp `owner_action_id`; remove preserves the active view
identity when present and stamps `cleanup_action_id`, and the verifier treats
those ids as reload state instead of trusting local effect payloads alone.

Implementation observation from `014-010`: first-slice provenance can report
LVO library-base, typed-access struct-pointer, app-slot/base evidence, and raw
base-relative unknowns from listing context, but deeper C flow definitions are
not exported yet. Lookup-derived bases, stored-state reloads, API-return aliases,
and clobber-scoped lifetimes remain report gaps until backend provenance facts
are surfaced.

Implementation observation from `014-006`: planner command availability must be
checked against execution policy, not just command id presence. Catalog entries
with `effect=inspection` or `appends_to_manual_action_log=false` can be useful
evidence surfaces, but non-dry `run-one` must stop at a
`command_execution_policy` blocker instead of POSTing them.

Implementation observation from `014-011`: RSSET binding needs both the
family-specific identity (`base_evidence_id`, layout/base, displacement) and
the generic provenance identity (`source_evidence_id`, source family/status,
path/lifetime scope). The report can expose unresolved raw bases, but bind
payloads and effective metadata should only carry accepted provenance refs so
the generic provenance verifier can gate semantic writes.

Implementation observation from `014-011`: selected RSSET binding verification
must treat binding owner/cleanup action ids and consumed `base_evidence_refs`
as semantic reload state. Matching only the selected-use identity tuple can
hide stale ownership or stale provenance after unbind/rebind.

Implementation observation from `014-006`/`014-011`: planner command
availability for RSSET binding must require and compare evidence-bearing
identity parameters, not just `command_id`. A selected row can expose
`rsset.binding.bind` for one proven `base_evidence_id`; that must not authorize
a stale candidate whose layout/base, displacement, operand index, or
`base_evidence_id` describes a different binding.

Implementation observation from `014-011`: bind-only RSSET use-site visibility
needs a ref-only projection path separate from renderable app-slot fields.
Creating a generic `app_XXXX` field for a missing RSSET layout would make source
rendering output-affecting before `bind_refine`; listing/navigation refs can
expose the linked gap while keeping the operand raw and round-trip proof exact.

Implementation observation from `014-012`: extending `M68kAnalysisPolicy` with
custom structs should not add large inline arrays to stack-heavy analysis
structures. Heap-owned custom-struct storage plus explicit policy deep-copy and
destroy paths kept native unit stack use bounded.

Implementation observation from `014-012`: custom structs currently share the
same resolver namespace as platform/NDK structs, and platform names win on
collision. Use target-specific names for now; explicit namespace identity is
future work if custom structs need to shadow platform names.

Implementation observation from `014-012`: accepted provenance must gate typed
field writes before command availability/execution, not only after durable
payload verification. Otherwise a forced selected command could create a field
from exploratory typed-gap context and fail only after mutation.

Implementation observation from `014-006`/`014-012`: typed-field catalog
availability must compare selected struct/offset and consumed
`struct_pointer` evidence identity, not just `typed_gap.field.*` or
`typed_access.field.*` command ids. Stale typed-field candidates must not borrow
availability from a different typed access/gap on the same row.

Implementation observation from `014-012`: selected typed-field rename proof
must use the previous name from command context to reject stale selected-row
typed accesses after render; absence of that previous name is a verifier
failure, not a successful rename proof. This is still only selected-row proof;
propagated typed-access descendants need owner-scoped cleanup before broad
rename/remove cascades are safe.

Implementation observation from `014-012`: typed-field writes need to preserve
`parent_evidence_ids` across catalog payload, planner command generation,
availability matching, durable payload replay, and semantic reload verification.
The consumed `source_evidence_id` is not enough once struct-pointer authority is
derived from more than one upstream base/register fact.

Implementation observation from `014-014`: data-symbol removal is not a single
cleanup shape. Generated seeded entities should be suppressed by hunk/address,
but source-owned manual data-symbol names must remove their `ManualSeed:*`
projection instead; otherwise a manual rename cleanup can overreach into
generated seeded identity.

Implementation observation from `014-006`/`014-014`: `data_symbol.remove`
availability must match the cleanup identity shape before execution. The shared
command id can mean generated seeded-item suppression by `(kind, hunk, addr)` or
source-owned manual seed removal by `seed_id`; command id presence alone must
not authorize the other cleanup path.

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
- Proposal and issue state are part of the implementation work. When code
  changes support, verifier behavior, loop selection, or remaining gaps, update
  this matrix and the owning issue in the same change.
- Prefer real target source convergence over surface expansion. Before adding
  broad autonomous candidate feeds for a family, prove at least one real target
  path from mined evidence through command execution, Manual Action Log replay,
  rendered-source improvement, and exact round-trip; track verifier proof in
  `014-005` and planner/feed proof in `014-006` plus the family issue.

## Implementation Slices

1. Build the source-convergence capability matrix. (`014-001`)
2. Define or fill durable target identities for editable source constructs.
   (`014-002`)
3. Add missing Manual Action Log actions. (`014-003`, with concrete capability
   issues `014-007` through `014-014`, `014-020`, and `014-021`; `014-015` investigated
   the data-block model and split implementation work into `014-016` through
   `014-019`; `014-022` audits the editing surface before further broad
   expansion)
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
- While an implementation issue remains open, keep its "Current evidence" and
  "Remaining work" sections current enough that another agent can resume from
  the issue without re-auditing recent commits.
- If work discovers a missing verifier, missing durable identity, stale smoke,
  or metadata-only path, record it in the owning issue before continuing broad
  planner expansion: durable identities in `014-002`, Manual Action Log gaps in
  `014-003`, catalog gaps in `014-004`, verifiers in `014-005`, planner feeds
  in `014-006`, and family-specific gaps in `014-007` through `014-021`.
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
