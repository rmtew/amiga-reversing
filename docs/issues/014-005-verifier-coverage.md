Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Define and implement verifier coverage for source-converging action families.

Accepted review state:
Verifier work for provenance-backed writes must use the accepted layered model:
durable payload, Manual Action Log replay, consumed evidence/status/scope,
conflict or override handling, descendant ownership, family effect,
owner-scoped cleanup, and exact round-trip when output-affecting.

Out of scope:
Do not bless actions as loop-executable without an action-specific verifier.

Files likely touched:
- reversing loop verification code
- reproduction/round-trip helpers
- projection/source rendering tests
- proposal matrix

Acceptance criteria:
- Every supported action family has a verifier: semantic reload,
  projected/rendered source effect, round-trip exactness, or type-specific
  oracle.
- Verification failures name the failed layer and stop the loop.
- Output-affecting source changes require round-trip exactness or a documented
  unavailable-oracle stop.
- Corrective actions that undo or replace a source fact must verify cleanup of
  owned derived analysis facts, including xrefs, type-flow facts, review items,
  symbolic projections, and invalidated code/data descendants where applicable.
- Semantic/type-producing actions must also verify their analysis-facing
  reconciliation: consumed evidence, generated or proposed flow-equivalent
  descendants, and owner-scoped cleanup. Presentation-only edits such as label
  renames, comments, and literal representation choices do not need this layer
  unless they emit semantic analysis facts.
- Provenance-backed semantic/type actions must verify the accepted provenance
  status and scope: source-family classification, path/lifetime selection,
  conflict or override handling, consumed `source_evidence_id`, generated
  `owner_action_id`, cleanup, and exact round-trip where output-affecting.
- Verifier layers for provenance-backed actions:
  1. executed action payload matches the durable command identity;
  2. Manual Action Log replay reloads the owning action;
  3. consumed evidence id exists, has an accepted status, matches required
     source family, and its path/lifetime scope covers the selected use;
  4. conflicts are absent or resolved by a manual classification/override that
     records contradicted evidence and reason;
  5. generated descendants carry the expected `source_evidence_id` and
     `owner_action_id`;
  6. rendered/type/xref/review effects match the family-specific expectation;
  7. cleanup/removal deletes only descendants owned by that action/evidence;
  8. exact round-trip passes for output-affecting changes.
- Exploratory provenance reports have no mutation verifier. Their verifier is
  limited to report consistency and no Manual Action Log append.

Required tests:
Positive and negative verifier tests for each implemented action family.

Working goal:
- Treat proposal and issue updates as part of verifier implementation. Each new
  verifier or verifier blocker must update Proposal 014 plus this issue before
  the work is considered complete.
- Prefer action-specific proof over generic pass/fail plumbing: durable action
  payload, Manual Action Log replay, reloaded semantic/manual state or rendered
  projection, and exact round-trip when output-affecting.
- Keep metadata-only actions blocked until a rendered-source or type-specific
  verifier exists.

Current evidence:
- Generic output-affecting manual mutations now run a round-trip verification
  layer after command execution, instead of only checking that a round-trip
  verifier is available before execution.
- Target-context mutations now use `/commands/execute` local effects as their
  projection verifier instead of requiring row affected-locator metadata.
- Target-context projection verification now requires a command-specific local
  effect kind and matching parameter payload, so unrelated local effects cannot
  satisfy the verifier.
- Seeded data-symbol rename has rendered definition-name plus exact
  direct-rebuild coverage in
  `test_real_dll_manual_data_symbol_rename_updates_rendered_seeded_entity`.
- Ordinary data-row symbol rename has rendered definition-name plus exact
  direct-rebuild coverage in
  `test_real_dll_manual_data_symbol_rename_renders_ordinary_data_row`.
- Data-symbol rename has rendered instruction use-site plus exact direct-rebuild
  coverage in
  `test_real_dll_manual_data_symbol_rename_updates_rendered_use_site`.
- Seeded data-symbol removal has rendered suppression plus exact direct-rebuild
  coverage in
  `test_real_dll_manual_data_symbol_remove_suppresses_rendered_seeded_entity`.
- Generic `run-one` `label.rename` execution now uses the label-specific
  verifier: Manual Action Log match, semantic label reload, projected label row,
  and exact round-trip.
- Generic `run-one` `review.label.*` execution now verifies Manual Action Log
  replay, reloaded manual label state or removed-label absence, and exact
  round-trip.
- Manual-label verifiers derive expected label payloads or removed label ids
  from executed durable action payloads, so matching project state alone cannot
  satisfy a missing or mismatched action result.
- Generic `run-one` `comment.edit` execution now uses the projected-comment
  verifier instead of accepting affected-locator metadata alone.
- Generic `run-one` `data_symbol.rename` execution now verifies Manual Action
  Log replay, semantic reload, projected listing text/name, and exact
  round-trip instead of accepting affected-locator metadata alone.
- Generic `run-one` `data_symbol.remove` execution now verifies Manual Action
  Log replay, either reloaded suppressed seeded item state or removed manual
  data-symbol seed absence, and exact round-trip instead of accepting
  affected-locator metadata alone.
- Generic `run-one` `correction.suppress_seeded_item.*` execution now verifies
  Manual Action Log replay, reloaded suppressed seeded item state, and exact
  round-trip instead of accepting affected-locator metadata alone.
- Generic `run-one` `target.execution_view.*` execution now verifies Manual
  Action Log replay, reloaded execution-view state, and exact round-trip instead
  of accepting target local-effect metadata alone.
- Planner verifier summaries now report `projected_data_symbol_name` for
  `data_symbol.rename` and `suppressed_seeded_item` for `data_symbol.remove`.
- Planner verifier summaries now report `suppressed_seeded_item` for seeded-item
  corrections and `execution_view_state` for execution-view commands.
- Planner verifier summaries now report `semantic_hint_state`,
  `library_base_register_seed`, and `struct_pointer_register_seed` for semantic
  hint/register-seed command families instead of generic `round_trip`.
- Unsupported future `data_symbol.*` and semantic command prefixes no longer
  receive a generic `round_trip` fallback; they stop as missing-verifier work
  until a type-specific verifier is added.
- Generic `run-one` `target.equate.*` execution now verifies Manual Action Log
  replay, reloaded target-equate/rename/removal state, and exact round-trip
  instead of accepting target local-effect metadata alone.
- Target-equate verifiers derive the expected equate from the executed durable
  action payload, so matching project state plus a local-effect echo cannot hide
  a missing or mismatched action result.
- Generic `run-one` `target.rsset_region.*` and `app_slot.*` execution now
  verifies Manual Action Log replay, reloaded RSSET region/removal state, and
  exact round-trip instead of accepting target local-effect metadata alone.
- RSSET/app-slot verifiers derive the expected region from the executed durable
  action payload, so matching project state plus a local-effect echo cannot hide
  a missing or mismatched action result.
- Generic `run-one` `semantic.register.struct_ptr` execution now verifies
  Manual Action Log replay, reloaded struct-pointer register seed, and exact
  round-trip instead of accepting affected-locator metadata alone.
- Generic `run-one` `semantic.library_base.*` execution now verifies Manual
  Action Log replay, reloaded library-base register seed, and exact round-trip
  instead of accepting affected-locator metadata alone.
- Register-seed verifiers now derive the expected seed from the executed
  durable action payload, so matching project state alone cannot satisfy a
  missing or mismatched action result.
- Register-seed verifiers now also compare consumed provenance carried by the
  executed library-base or struct-pointer seed against reloaded semantic state,
  treating `parent_evidence_ids` as an unordered dependency set. This prevents
  a same register/library/struct seed with stale provenance from satisfying the
  semantic reload layer.
- Generic `run-one` `semantic.lvo.*`, `semantic.struct_offset.*`, and
  `semantic.equate.*` execution now verifies Manual Action Log replay, reloaded
  semantic hint state, and exact round-trip instead of accepting affected-row
  metadata alone.
- Generic `run-one` row/range/review seed creation and review seed removal now
  verify Manual Action Log replay, reloaded manual seed state or removed-seed
  absence, and exact round-trip.
- Manual-seed verifiers derive expected seeds or removed seed ids from executed
  durable action payloads, so matching project state alone cannot satisfy a
  missing or mismatched action result.
- `tests/test_agent_reversing_loop.py::test_agent_reversing_loop_smoke` now
  returns durable Manual Action Log hash/count metadata and refreshed projected
  comment rows, so it exercises the projected-comment verifier instead of the
  old affected-locator-only behavior.
- `tests/test_agent_reversing_loop.py::test_agent_real_genam_autonomous_rsset_candidate_converges_source`
  proves an autonomous GenAm RSSET candidate through command execution, reloaded
  RSSET state, rendered RSSET definition, and exact round-trip availability.
- `tests/test_agent_reversing_loop.py::test_agent_real_genam_autonomous_lvo_library_base_candidate_converges`
  proves an autonomous GenAm LVO library-base candidate through command
  execution, durable Manual Action Log state, reloaded library-base register
  seed, and exact round-trip availability.
- `tests/test_agent_reversing_loop.py::test_agent_real_genam_autonomous_data_symbol_candidate_converges`
  proves autonomous GenAm data-symbol naming through command execution,
  projected rendered-name verification, and exact round-trip availability.
- Generic mutation verification now adds a `provenance_evidence` layer when the
  executed durable action payload carries `source_evidence_id`. The layer
  requires durable payload evidence, accepted source family, accepted evidence
  status (`analysis_proven`, `path_specific`, `manual_classified`, or
  `manual_override`), explicit path/lifetime scope, owner action identity, and
  conflict handling. Command-only `source_evidence_id` is a verifier failure.
- When a selected command carries `source_evidence_id`, the provenance verifier
  now requires the executed durable payload to carry the same evidence id, so a
  mutation cannot satisfy one requested evidence path with a different durable
  accepted path.
- Selected command context is also treated as consumed provenance evidence when
  parameters do not carry `source_evidence_id`, so context-backed semantic/type
  writes cannot bypass the durable evidence match.
- Manual overrides in the provenance verifier require both
  `contradicted_evidence_id` and `reason`; unresolved, unknown, or conflicting
  evidence cannot satisfy a provenance-backed write.
- The generic provenance verifier now ignores nested durable `cleanup_scope`
  evidence ids when searching for consumed provenance, matching the existing
  command-side cleanup/evidence boundary. Cleanup-only mutations must be proven
  by their family cleanup verifier, not by treating old evidence as new consumed
  evidence.
- Route-level verifier tests now keep command-locator fixtures aligned with the
  production contract: selected interpreted-reference rows must carry enough
  source bytes for the requested width, and fake listing artifacts used for
  command execution must provide navigation payloads.
- The generic provenance verifier no longer treats nested reference-only
  evidence as consumed write evidence. `base_evidence_refs`, `conflicts`, and
  `cleanup_scope` may document inputs or cleanup, but the durable action payload
  itself must carry the consumed `source_evidence_id`.
- Generic provenance verifier and catalog identity matching now treat
  `parent_evidence_ids` as an unordered dependency set, so equivalent accepted
  evidence is not rejected only because the command and durable payload list
  parent ids in different orders.

Remaining work:
- Extend family-specific write commands to persist `source_evidence_id`,
  accepted status, source family, path/lifetime scope, conflicts/override
  fields, and descendant `owner_action_id` where still missing. Library-base and
  selected typed struct-pointer register seeds now persist and verify consumed
  provenance; broader API arg/return and propagated descendants remain open.
- Add or document one real-target smoke for each newly executable action family
  before treating synthetic verifier coverage as sufficient; record the
  verifier evidence here and the candidate/feed evidence in `014-006` or the
  family issue (`014-010`, `014-011`, `014-012`, `014-013`, `014-014`,
  `014-017`, `014-018`, `014-019`, `014-020`). `014-016` only needs replay and
  metadata invariants until rendering/command slices depend on it.
- Keep custom struct and typed-field commands blocked until rendered custom
  field paths and their verifier are proven in `014-012`.
- Keep data-block layout and interpreted-reference commands blocked until
  layout rendering, generated xrefs, removal behavior, and exact round-trip
  verifiers are proven in `014-017`, `014-018`, and `014-019`.
- Keep target-equate definition representation commands blocked until rendered
  `EQU` value text, semantic reload, and exact round-trip verifiers are proven
  in `014-020`.
- Keep RSSET numeric binding commands blocked until `014-011` proves replay,
  selected-use rendering or linked-gap state, owned descendant cleanup, exact
  round-trip, and type/xref verifiers where applicable. `014-021` defines the
  verifier shape.

Cleanup / deletion:
Delete after the verifier column in the matrix has no unspecified supported
actions.
