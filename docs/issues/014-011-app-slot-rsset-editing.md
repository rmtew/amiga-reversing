Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Add first-class app-slot and RSSET layout editing.

Post-`014-022` split:
RSSET should consume the generic provenance / def-use / reference model owned
by `014-010`. This issue owns RSSET-specific interpretation, binding, refine,
linked-gap, and cascade behavior on top of provenance evidence.

Accepted review state:
Raw `$NNNN(An)`/`zzz(an)` operands and default A6 fallback remain report-only
until accepted durable base evidence exists. Same-displacement propagation
requires same accepted base evidence or verifier-proven equivalent flow
identity.

Current evidence:
- Listing rows expose `app_slot` element contexts with symbol, displacement,
  base register, operand index, and access.
- Navigation exposes app-slot slots, regions, gaps, field gaps, suggestions,
  and untyped API args.
- Target metadata supports `rsset_layout_regions`.
- Manual Action Log now supports `create_manual_rsset_layout_region`, projected
  into effective `rsset_layout_regions` by durable
  `(layout_name, base_symbol, offset)` identity.
- Target command catalog exposes `target.rsset_region.add/edit/rename/remove`;
  create/edit/rename append replacement RSSET-region actions, and removal
  filters manual/seeded effective regions by the same durable identity.
- Listing app-slot elements expose `app_slot.rename/edit/remove`, which map the
  selected app-slot displacement to manual RSSET region create/remove actions
  and require an explicit symbol plus size for rename/edit.
- `014-021` completed the numeric-displacement binding investigation. Raw
  base-relative use-sites need explicit RSSET binding facts before field
  creation, with durable identity based on target, hunk, source address,
  operand index, base register, displacement, chosen `(layout_name,
  base_symbol)`, and base-evidence id.
- Manual Action Log now supports `create_manual_rsset_use_site_binding` and
  `remove_manual_rsset_use_site_binding`. Replay projects active and removed
  bindings by durable use-site identity, and creation projection stamps
  `owner_action_id` from the persisted Manual Action Log `action_id`. Binding
  payloads include `base_evidence_id` so later cleanup/cascade work keeps the
  `014-021` identity shape.
- Effective target metadata now carries active `rsset_use_site_bindings` into
  the C analysis policy. When a selected binding has explicit base evidence and
  a matching existing RSSET field, the source renderer can render that selected
  operand with the field symbol without requiring a register seed or broad
  same-displacement cascade.
- Selected numeric base-relative operands expose `rsset.binding.report` for
  exploratory use. The report now includes source locator, operand facts, base
  evidence state, candidate layout field/gap context, nearby fields, width/gap
  compatibility, existing same-displacement use summaries, expected cascade,
  render state, and missing verifier blockers.
  `rsset.binding.bind` and `rsset.binding.unbind` are exposed only when the
  selected context carries explicit RSSET/app-base evidence, such as an
  app-slot context or candidate-supplied `base_evidence_id`. The catalog must
  not infer `app/__amiga_app_base__` from an arbitrary `An` displacement, and
  report-only non-`A6` raw displacements do not receive a default app candidate.
  Bind-only records the selected use and linked-gap/raw render state without
  inventing an unlinked `RS.*` field.
- Native listing JSON now emits raw address-register displacement operands as
  selectable `operand_parts` with `base_register`, `displacement`, and
  `operand_index`. Real GenAm coverage proves `sf.b $0102(a6)` has no
  `app_slot_refs`, still exposes a selectable displacement element, and offers
  a report showing the `$0102` one-byte app-slot gap and missing base-evidence
  blocker; bind/unbind waits for explicit base evidence.
- Planned refinement actions remain `create_manual_rsset_binding_type_refinement`
  and `remove_manual_rsset_binding_type_refinement`; planned refinement command
  ids remain `rsset.binding.bind_refine`, `rsset.binding.type_refine`, and
  `rsset.binding.clear_type`.
- RSSET bind/refine commands must expose corrective unbind/remove paths. Undo
  must remove only the binding or derived field/type facts owned by the selected
  Manual Action Log action, then verify that rendered source returns to the raw
  displacement or previous RSSET field.
- RSSET create/edit/rename commands preserve parser metadata
  (`parser_role`, `parser_routine`, `parse_order`) through Manual Action Log
  payloads, effective metadata projection, and loop suggestion parameters.
- Render/rebuild coverage proves a manual named RSSET region emits the RSSET
  field, rewrites a base-relative reference, and direct-rebuilds exactly; removal
  coverage proves source refs return to raw displacement and direct-rebuild
  exactly.
- C-backed render/rebuild coverage proves a bind-only selected use can render
  an existing named RSSET field while another same-displacement use of the same
  base register stays raw, and direct-rebuilds exactly.
- Bind-only selected use-sites without a matching RSSET field now project into
  listing `app_slot_refs` and app-slot analysis/navigation as ref-only
  evidence. They do not create renderable `app_XXXX`/`RS.*` fields, so source
  remains raw and exact round-trip proof stays local until `bind_refine` exists.
- Loop planner recognizes explicit `target.rsset_region.add/edit/rename/remove`
  candidates, reports `rsset_region_state` verification, and skips
  already-satisfied projected add/edit/rename/remove state.
- Loop planner also accepts explicit `app_slot.rename/edit/remove` command
  candidates, routes them through the selected app-slot element context, skips
  already-projected app-slot region state, and reports `rsset_region_state`
  verification.
- Generic loop execution verifies RSSET/app-slot commands by matching the
  executed durable RSSET-region action payload against reloaded
  `rsset_layout_regions` or `removed_rsset_layout_regions`, then exact
  round-trip.
- Generic loop execution verifies RSSET binding commands by matching the
  durable binding payload against reloaded `rsset_use_site_bindings` or
  `removed_rsset_use_site_bindings`, including binding owner/cleanup action
  identity and consumed `base_evidence_refs`, then exact round-trip.
- When inspect has no review candidates, the loop now mines listing navigation
  `app-slot-suggestions` into autonomous `target.rsset_region.add/edit`
  candidates and skips already-projected RSSET metadata.
- The autonomous RSSET feed also uses high-confidence `app-slot-regions` from
  platform API argument analysis when no separate suggestion exists, de-duping
  identical suggestion/region candidates.
- Autonomous RSSET candidate skipping now reads effective target metadata as
  well as Manual Action Log projections, so seeded layout regions are not
  repeated.
- GenAm real-target loop smoke now copies the target to a temp project, mines a
  real `app-slot-suggestions` RSSET candidate, executes
  `target.rsset_region.add`, verifies the reloaded RSSET region from the
  durable action payload, renders the resulting `RS.*` definition, and keeps
  exact round-trip status.
- Broader autonomous candidate production remains open.
- Post-`014-022` review reframes `rsset.binding.report` as a family-specific
  view over generic provenance exploration. Generic provenance should explain
  where the base register/value is set, where it is used, caller/path status,
  conflicts, source-family classification, and durable evidence ids. RSSET then
  adds layout/base matching, nearby fields/gaps, compatible offsets,
  same-lifetime displacement uses, and bind/refine blockers.
- `rsset.binding.report` now exposes generic provenance as RSSET-shaped
  `base_evidence_refs`. Raw base-relative operands report unresolved/unknown
  evidence and remain blocked; selected app-slot or explicit base evidence
  reports accepted `rsset_app_base` refs with source evidence id,
  path/lifetime scope, confidence, origin details, layout/base identity, and
  accepted state.
- `rsset.binding.bind`/`unbind` durable payloads now carry the accepted
  `source_evidence_id`, source family/status, path/lifetime scope, confidence,
  conflicts, and `base_evidence_refs` they consume. Manual replay projects
  those fields into effective `rsset_use_site_bindings` so verifier/planner
  gates can compare against effective provenance state, not just row text.
- Planner command availability for `rsset.binding.bind`/`unbind` now requires
  the command to carry, and the refreshed catalog entry to match, the selected
  layout/base identity,
  `base_evidence_id`, displacement, and operand index. This keeps raw or stale
  same-command candidates from borrowing availability from a different proven
  RSSET binding action on the same row.
- Planner already-satisfied checks now skip bind candidates whose effective
  selected-use binding already carries the same layout/base identity and
  consumed `base_evidence_refs`, including unordered parent evidence ids.
- RSSET `base_evidence_refs` now preserve `parent_evidence_ids` as a set instead
  of collapsing provenance dependencies to one parent pointer.
- RSSET `base_evidence_refs` now preserve optional correction provenance
  (`contradicted_evidence_id` and `reason`) through command-query context,
  report output, bind/unbind durable payloads, and semantic reload comparison.
- RSSET `base_evidence_refs` now also preserve correction `cleanup_scope`
  through report output, bind/unbind durable payloads, and semantic reload
  comparison, so manual override bindings keep the same cleanup boundary as the
  contradicted base evidence they consume.
- RSSET provenance reports now prefer explicit accepted selected-use provenance
  over regenerating a `path_specific` id from `base_evidence_id`. Manual
  classification/override status, path/lifetime scope, conflicts, and
  `parent_evidence_ids` survive into `base_evidence_refs` and the top-level
  binding payload for verifier comparison.
- RSSET unbind identity payloads now preserve the same top-level
  `parent_evidence_ids` and `cleanup_scope` as bind payloads, not just the
  nested `base_evidence_refs`, so cleanup/replay matching uses the selected
  binding boundary directly.
- RSSET semantic reload verification now compares top-level
  `parent_evidence_ids` and nested `base_evidence_refs.parent_evidence_ids` as
  unordered dependency sets, so equivalent provenance lineage survives replay
  or report ordering differences while mismatched parent evidence still fails.
- RSSET bind/unbind catalog exposure now treats explicit selected-use
  provenance as authoritative. If a selected context carries unresolved,
  unknown, conflicting, non-`rsset_app_base`, or incomplete override evidence,
  `base_evidence_id` alone no longer exposes mutation; the operand remains
  report-only with a classify-source boundary.

Acceptance criteria:
- App-slot and RSSET region identities are durable and not row-index based.
- RSSET binding consumes provenance-backed base evidence; raw `zzz(an)` /
  `$NNNN(an)` operands remain report-only until provenance, explicit evidence,
  or selected app-slot context proves the base.
- Manual actions replay into effective metadata and rendered RSSET/source refs.
- Command catalog exposes add/edit/rename/remove, bind/unbind, and field/region
  operations.
- Verifier proves RSSET definitions, linked use-site refs, cleanup/undo state,
  semantic reload, and round-trip.

Required tests:
Identity tests, manual replay tests, catalog execution tests, rendered-source
tests, and GenAm-style loop smoke.

Working goal:
- Keep Proposal 014 and this issue synchronized with every RSSET/app-slot
  implementation change. Matrix text should name the exact supported Manual
  Action Log, command catalog, loop, and verifier state.
- Prefer real target RSSET convergence before expanding autonomous RSSET feeds:
  mined app-slot evidence, selected command, durable RSSET action payload,
  reloaded `rsset_layout_regions` or removal state, rendered source effect, and
  exact round-trip.

Remaining work:
- Broaden generic provenance consumption beyond first-slice selected-use
  `base_evidence_refs` once backend flow definitions can distinguish
  equivalent lifetimes, clobbers, stored-state reloads, and caller/path
  alternatives.
- Keep default A6 fallback report-only. Mutation needs seed-backed,
  selected-app-slot, flow-derived, manually classified, or override evidence
  with a durable id.
- Broaden `rsset.binding.report` from selected-use and same-displacement
  summaries into generated xref/type-flow descendants once bind-refine and
  cascade ownership exist.
- Add `rsset.binding.bind_refine` so a binding can own creation/refinement of a
  missing RSSET field such as GenAm `$0102(a6)`; bind-only still leaves missing
  fields raw/linked-gap until that field action exists.
- Add conflict feedback for bind+type refinement: if observed access width,
  base evidence, or platform/custom type application does not reconcile, block
  the application or create a review item instead of silently applying it.
- Make generated binding descendants carry owner action ids so unbind or
  clear-type retracts same-displacement candidates, linked gaps, xrefs,
  review items, and type-flow facts without deleting unrelated RSSET fields.
- For provenance-derived descendants, carry both consumed `source_evidence_id`
  and binding/refinement `owner_action_id`. Path-specific or conflicting
  provenance must block global binding until the user selects a path/lifetime
  scope or records a manual classification/override.
- `rsset.binding.report` should be the RSSET view over generic provenance:
  it consumes provenance definitions/uses/source-family status, then adds
  candidate layout/base symbol, field-or-gap at displacement, nearby fields,
  observed access width, same-flow/same-displacement use summary,
  bind/refine/type blockers, expected cascade, and cleanup owner.
- `base_evidence_refs` consumer shape includes operand index, base
  register, displacement, source family, status, `source_evidence_id`,
  `base_evidence_id`, path/lifetime scope, confidence, origin kind, origin
  hunk/offset/register, optional parent evidence ids, optional correction
  cleanup scope, layout name, and base symbol for selected-use refs. Broader
  flow-derived refs still need backend provenance facts before this shape can be
  widened.
- Same-flow/same-displacement candidates require the same accepted
  `base_evidence_id` or a verifier-proven equivalent flow identity. Matching
  only register name plus displacement is insufficient, including A6 fallback
  cases.
- Availability checks already enforce exact selected-use RSSET binding
  identity. Future same-flow/same-displacement feed widening must keep this
  property and add flow-equivalence proof explicitly rather than relying on
  command id matches.
- Bind/refine/cascade ownership:
  bind-only owns selected-use state; bind-refine owns linked field/gap
  descendants it creates; type-refine owns type/domain descendants. Unbind and
  clear-type must retract only descendants matching the selected
  `owner_action_id`/cascade id and must leave independently accepted RSSET
  regions or bindings intact.
- Keep broader autonomous candidate production evidence-first and de-duped by
  durable RSSET identity before adding more feed types; durable identity gaps
  belong in `014-002`, command exposure gaps in `014-004`, and RSSET-specific
  source-model gaps stay here.
