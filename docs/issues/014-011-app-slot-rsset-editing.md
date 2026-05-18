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
- Render/rebuild coverage proves a manual named RSSET region emits the RSSET
  field, rewrites a base-relative reference, and direct-rebuilds exactly.
- App-slot rename/edit/remove, RSSET remove, parser-role edits, and autonomous
  candidate production remain open.

Acceptance criteria:
- App-slot and RSSET region identities are durable and not row-index based.
- Manual actions replay into effective metadata and rendered RSSET/source refs.
- Command catalog exposes add/edit/rename/remove and field/region operations.
- Verifier proves RSSET definitions, all refs, semantic reload, and round-trip.

Required tests:
Identity tests, manual replay tests, catalog execution tests, rendered-source
tests, and GenAm-style loop smoke.
