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
  candidates, requires round-trip verification, and skips already-satisfied
  projected add/edit/rename/remove state.
- Loop planner also accepts explicit `app_slot.rename/edit/remove` command
  candidates, routes them through the selected app-slot element context, skips
  already-projected app-slot region state, and requires round-trip
  verification.
- When inspect has no review candidates, the loop now mines listing navigation
  `app-slot-suggestions` into autonomous `target.rsset_region.add/edit`
  candidates and skips already-projected RSSET metadata.
- Broader autonomous candidate production remains open.

Acceptance criteria:
- App-slot and RSSET region identities are durable and not row-index based.
- Manual actions replay into effective metadata and rendered RSSET/source refs.
- Command catalog exposes add/edit/rename/remove and field/region operations.
- Verifier proves RSSET definitions, all refs, semantic reload, and round-trip.

Required tests:
Identity tests, manual replay tests, catalog execution tests, rendered-source
tests, and GenAm-style loop smoke.
