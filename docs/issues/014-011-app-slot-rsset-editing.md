Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Add first-class app-slot and RSSET layout editing.

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
- RSSET create/edit/rename commands preserve parser metadata
  (`parser_role`, `parser_routine`, `parse_order`) through Manual Action Log
  payloads, effective metadata projection, and loop suggestion parameters.
- Render/rebuild coverage proves a manual named RSSET region emits the RSSET
  field, rewrites a base-relative reference, and direct-rebuilds exactly; removal
  coverage proves source refs return to raw displacement and direct-rebuild
  exactly.
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

Acceptance criteria:
- App-slot and RSSET region identities are durable and not row-index based.
- Manual actions replay into effective metadata and rendered RSSET/source refs.
- Command catalog exposes add/edit/rename/remove and field/region operations.
- Verifier proves RSSET definitions, all refs, semantic reload, and round-trip.

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
- Keep broader autonomous candidate production evidence-first and de-duped by
  durable RSSET identity before adding more feed types; durable identity gaps
  belong in `014-002`, command exposure gaps in `014-004`, and RSSET-specific
  source-model gaps stay here.
