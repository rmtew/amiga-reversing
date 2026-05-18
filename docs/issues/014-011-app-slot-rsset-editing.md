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
- Target command catalog exposes `target.rsset_region.add`; command execution
  appends the action and reports a local RSSET-region effect.
- Target command catalog exposes `target.rsset_region.remove`; Manual Action
  Log removal filters manual/seeded effective regions by the same durable
  identity.
- Listing app-slot elements expose `app_slot.rename`, which maps the selected
  app-slot displacement to `create_manual_rsset_layout_region` and requires an
  explicit symbol plus size.
- Render/rebuild coverage proves a manual named RSSET region emits the RSSET
  field, rewrites a base-relative reference, and direct-rebuilds exactly; removal
  coverage proves source refs return to raw displacement and direct-rebuild
  exactly.
- Loop planner recognizes explicit `target.rsset_region.add/remove` candidates,
  requires round-trip verification, and skips already-satisfied projected
  add/remove state.
- App-slot edit/remove, RSSET edit/rename, parser-role edits, and
  autonomous candidate production remain open.

Acceptance criteria:
- App-slot and RSSET region identities are durable and not row-index based.
- Manual actions replay into effective metadata and rendered RSSET/source refs.
- Command catalog exposes add/edit/rename/remove and field/region operations.
- Verifier proves RSSET definitions, all refs, semantic reload, and round-trip.

Required tests:
Identity tests, manual replay tests, catalog execution tests, rendered-source
tests, and GenAm-style loop smoke.
