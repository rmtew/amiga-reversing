Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Turn API, LVO, register-base, and struct-pointer semantic discoveries into
consumed source-converging actions.

Post-`014-022` split:
This issue owns the first focused investigation and implementation slice for
generic provenance / def-use / reference exploration. RSSET, typed fields, and
data-block type binding consume this model rather than inventing separate
provenance mechanisms.

Accepted review state:
Implementation may restart here. First slice is read-only provenance/def-use/
reference reports for register/base provenance at instruction operands and
base-relative memory operands, with required durable identity support from
`014-002`. Exploratory reports must not write Manual Action Log state.

Current evidence:
- `entry_register_seeds` are consumed by rendering and support `library_base`
  and `struct_ptr`.
- Command catalog exposes `semantic.library_base.<library>` helpers for A6 LVO
  contexts, using row API metadata when present and NDK library/function lookup
  otherwise.
- Command catalog exposes `semantic.register.struct_ptr` on register elements;
  execution writes a `struct_ptr` register seed with an explicit struct name.
- `semantic.lvo.*` commands append semantic hints; LVO hints for immediate
  operands now project to `_LVO*` symbol representations and render with NDK
  includes.
- `semantic.struct_offset.*` commands append semantic hints; struct-offset
  hints for immediate operands now project to NDK field symbol representations
  and render with includes.

Progress:
- Known LVO immediate constants are source-converging: Manual Action Log hint ->
  effective metadata -> rendered `_LVO*` symbol -> exact direct rebuild.
- Known struct-offset immediate constants are source-converging: Manual Action
  Log hint -> effective metadata -> rendered field symbol -> exact direct
  rebuild.
- A6 LVO library-base seeds are no longer exec-only; command execution records
  the selected library and named base struct when the NDK payload provides it.
- Register-selected struct-pointer seeds now use the existing Manual Action Log
  projection path and no longer default to `exec.library`.
- The loop planner now accepts explicit dynamic semantic command candidates for
  `semantic.library_base.*`, `semantic.lvo.*`, `semantic.struct_offset.*`,
  `semantic.equate.*`, and `semantic.register.struct_ptr`, routes them through
  selected listing element context, skips already-projected library-base and
  struct-pointer register seeds, and requires round-trip verification.
- Generic `run-one` now mines unresolved typed-access listing evidence into
  autonomous `semantic.register.struct_ptr` candidates when the same row exposes
  a selectable operand context for the base register, including memory operands
  whose register is supplied by operand metadata, skipping already-projected
  struct-pointer register seeds.
- Autonomous struct-pointer candidate skipping now reads effective target
  metadata as well as Manual Action Log projections, so seeded register-base
  facts from target metadata are not repeated.
- Generic `run-one` now verifies `semantic.register.struct_ptr` execution by
  checking the reloaded struct-pointer register seed rather than affected row
  metadata.
- Generic `run-one` now verifies `semantic.library_base.*` execution by checking
  the reloaded library-base register seed rather than affected row metadata.
- Register-seed verifiers now use the executed durable action payload as the
  expected seed before matching reloaded project state.
- `semantic.library_base.*` catalog entries now persist accepted first-slice
  `library_base` provenance into the register-seed Manual Action Log payload,
  effective metadata, and semantic-reload verifier.
- `semantic.register.struct_ptr` is now exposed on typed access/gap elements
  with accepted `struct_pointer` provenance and a default struct name when the
  selected context already proves the base type; the durable register seed
  preserves that consumed evidence.
- Register-seed semantic reload now compares consumed provenance fields,
  including unordered `parent_evidence_ids`, so a reloaded seed with the same
  register/library/struct but stale evidence cannot satisfy verification.
- `semantic.lvo.*`, `semantic.struct_offset.*`, and `semantic.equate.*`
  commands now preserve source evidence carried by selected/planner context in
  the semantic hint payload, verifier reload, and already-satisfied skip check.
- Semantic-hint reload verification now derives the expected hint from the
  durable Manual Action Log action before local-effect echoes, so an unrelated
  same-response local effect cannot satisfy or replace the executed semantic
  hint payload.
- Semantic-hint reload verification now also rejects local-effect-only
  responses as missing durable payloads; the expected semantic hint must come
  from the executed Manual Action Log action.
- Generic provenance reports now preserve manual-override correction fields
  (`contradicted_evidence_id`, `reason`, and `cleanup_scope`) when those fields
  are carried by selected context.
- Generic `run-one` now mines listing LVO API-call rows into autonomous
  `semantic.library_base.*` candidates and skips library-base seeds already in
  effective metadata or Manual Action Log projections.
- Real C listing rows now preserve the decoded base register and displacement
  on `_LVO*(a6)` symbol operand parts. Synthetic rows had `base_register`
  already, but real GenAm rows were missing it until the C JSON emitter copied
  the effective-address register from the IR.
- Generic `run-one` now pages through bounded listing windows instead of only
  sampling the first 2048 rows, so real GenAm direct LVO rows around row 8030
  can feed autonomous `semantic.library_base.*` work.
- `tests/test_agent_reversing_loop.py::test_agent_real_genam_autonomous_lvo_library_base_candidate_converges`
  proves real GenAm LVO evidence -> `semantic.library_base.exec.library` ->
  Manual Action Log register seed -> reloaded library-base state -> exact
  round-trip.
- Generic `run-one` now verifies `semantic.lvo.*`, `semantic.struct_offset.*`,
  and `semantic.equate.*` execution by checking reloaded semantic hint state
  rather than affected row metadata.
- Planner verifier summaries now name semantic state checks as
  `semantic_hint_state`, `library_base_register_seed`, or
  `struct_pointer_register_seed` instead of generic `round_trip`.
- Command catalog now exposes read-only `provenance.definition.report`,
  `provenance.uses.report`, `provenance.references.report`, and
  `provenance.source_family.report` actions for selected register/base
  operands. These actions return `inspection` results with a stable
  `source_evidence_id`, subject, definition candidates, same-base use
  candidates, reference/consumer views, source-family/status, path/lifetime
  scope, possible actions, conflicts, and consumers, and they are rejected by
  command execution as `non_mutable_command`.
- First-slice provenance classification covers LVO A6 base operands as
  `library_base`/`analysis_proven`, typed access/gap base operands with known
  owner/root structs as `struct_pointer`/`analysis_proven`, selected app-slot or
  explicit base evidence as RSSET app-base evidence, and raw base-relative
  displacement operands as `unknown`/`unresolved` report-only evidence.
- Base-relative provenance reports reuse the existing same-displacement scan
  used by RSSET reports, so `$NNNN(An)` reports can show same-displacement
  register-base uses without creating Manual Action Log state.
- Provenance evidence ids now include every parent evidence id, not only the
  first one, so distinct path/base evidence chains cannot collapse to one
  `source_evidence_id`.
- Provenance evidence ids now include the full normalized path/lifetime scope,
  not only the scope kind, so path-specific same-subject reports remain distinct
  before any accepted classification or family-specific bind action consumes
  them.
- API call semantics, evidence-scoped register lifetimes, typed field access
  semantics, and broader struct-pointer candidate generation remain open.
- Applying a struct/platform type should be able to feed type-flow analysis:
  propagated pointer/base types, rendered field paths at other references,
  interpreted field references where supported, and review items when
  propagation is uncertain or conflicts with existing facts. This must remain
  agent-visible through Manual Action Log and command catalog capabilities, not
  UI-only state. Data-block element type binding and its type-flow/review-item
  projection are owned by `014-019-data-block-type-binding-and-platform-structs.md`.
- RSSET binding type refinement from `014-021` also feeds this issue: a bound
  app/RSSET field may propagate pointer/base type facts only after the binding
  owner, base evidence, observed access width, rendered typed path, semantic
  reload, and exact round-trip are verified. Ambiguous propagation must create
  review feedback, not silent type-flow facts.

Post-`014-022` provenance requirements:
- Add read-only catalog/report commands for provenance exploration, such as
  definition lookup, use lookup, and source-family classification. Exploration
  must not append to the Manual Action Log.
- First implementation slice should cover register/base provenance at
  instruction operands and base-relative memory operands. Later slices may add
  memory-held values, stack locals, allocation/local buffers, and table-derived
  pointer values.
- Reports should return all candidate definitions/usages with status
  (`analysis_proven`, `path_specific`, `conflicting`, `unknown`, `unresolved`,
  `manual_classified`, `manual_override`), source family, path/lifetime scope,
  confidence, conflicts, and possible manual actions.
- Initial source-family vocabulary is `rsset_app_base`, `library_base`,
  `struct_pointer`, `data_block_pointer`, `hardware_base`,
  `allocation_or_local`, `constant_or_equ`, `unknown`, and `conflicting`.
- Accepted classification/link/apply/override commands are the write boundary.
  They must produce reusable durable evidence ids and preserve path/lifetime
  scope. Manual overrides must record contradicted evidence and reason.
- Reference queries are evidence-bearing def-use/xref views, not UI-only
  navigation. They should be reusable by RSSET, typed fields, data blocks,
  labels, EQU values, and planner verification.
- Generated descendants should distinguish consumed provenance
  `source_evidence_id` from the `owner_action_id` of the field/bind/type action
  that created the projection.

Investigation result:
- Current "where is this set / used" sources are split across C analysis and
  Python catalog/planner surfaces. Python carries selected evidence from
  `listing_context.py` (`operand_parts`, `app_slot_refs`, typed accesses/gaps,
  runtime-address refs), exposes report/write commands in
  `manual_action_catalog.py`, passes explicit RSSET evidence through
  `server.py`, projects accepted actions in `effective_metadata.py`, and gates
  execution in `reversing_loop.py`. C imports effective metadata in
  `platform_file_lib.c`, applies register seeds and platform lookup state in
  `m68k_analysis_render_lookup.c`, updates platform state through instruction
  flow, records app-slot/typed accesses, and renders LVO/base-field/selected
  RSSET symbols in `m68k_render_ir.c`.
- Read-only catalog commands should be `provenance.definition.report`,
  `provenance.uses.report`, `provenance.references.report`, and
  `provenance.source_family.report`. They return reports only. They may be
  invoked from selected operand/app-slot/typed/data contexts or planner
  candidates, but never append Manual Action Log entries.
- Report shape:
  `subject` (target, hunk, source address, operand index, register/base
  register, displacement/value), `definitions`, `uses`, `references`,
  `source_family`, `status`, `path_lifetime_scope`, `source_evidence_id`,
  `confidence`, `conflicts`, `possible_actions`, and `consumers`. Definitions
  should include
  origin kind, origin hunk/offset, defining instruction/value where known,
  predecessor/caller path summary, and parent evidence ids. Uses should include
  same-flow use-sites, same-displacement candidates, typed/app-slot/data-block
  consumers, and output-affecting risk.
- Source-family classification is accepted only at the write boundary:
  `provenance.classify_source` for unknown/unresolved evidence,
  `provenance.override_source` for contradicted evidence, or a family-specific
  bind/type action that consumes an already accepted evidence id. Exploratory
  statuses do not authorize writes.
- Manual classification payloads must carry source family, evidence status,
  path/lifetime scope, reason, and the normalized subject identity. Manual
  overrides must additionally carry the contradicted evidence id and cleanup
  scope.
- First slice: export operand-scoped register/base provenance for instruction
  operands and base-relative memory operands. A report for `$NNNN(An)` should
  answer which fact currently defines `An`, whether it is entry seed, policy
  seed, lookup-derived, flow-derived, selected app-slot, manual classification,
  override, conflicting, or unknown, and which same-lifetime uses share it.
- Implementation review: the first slice intentionally reports selected
  operand/app-slot/typed facts already present in listing context. It does not
  yet import deeper C flow definitions such as lookup-derived, stored-state
  reload, API-return alias, or clobber-to-clobber lifetimes; those need backend
  exported provenance before write commands may consume them.
- Later slices may add memory-held values, stack locals, allocation/local
  buffers, table-derived pointer values, API return aliases, and stored-state
  reloads. These must reuse the same report/status/evidence id model.

Acceptance criteria:
- Register/base identities cover entry-scoped and evidence-scoped lifetimes.
- Read-only provenance exploration reports definition/use candidates, path
  status, source family, conflicts, and possible actions without mutating Manual
  Action Log state.
- Accepted provenance classifications produce durable evidence ids that later
  semantic/type actions can consume.
- LVO/API/struct-offset semantic choices project into effective metadata.
- Commands are available for supported libraries, registers, and struct pointer
  cases without hard-coded exec-only behavior.
- Loop planner support covers explicit semantic command candidates with
  source element context and round-trip verification.
- Verifiers prove rendered-source propagation through calls, arguments, return
  values, or stored state as applicable.

Required tests:
Register seed projection/render tests, semantic hint consumption tests, command
catalog tests, and loop verifier tests.
