Status: Implementation complete
Source issue: docs/issues/014-015-data-block-layout-and-reference-interpretation.md
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Implement the first-class data block layout source model and Manual Action Log
projection. This issue owns identity, metadata shape, effective metadata merge,
overlap handling, and removal behavior. It does not own command catalog
exposure, rendering, or interpreted references.

Identity contract:
- `layout_id` is the stable durable identity for a data-block layout within one
  target. Hunk/source range is required when creating a layout and remains
  validation/context for edits and removals.
- `edit_manual_data_block_layout` and `remove_manual_data_block_layout` may
  target by `layout_id` alone. If they also carry `hunk`, `source_start`, or
  `source_end`, those fields must match the active layout; mismatches block
  replay as stale Manual Action Log state instead of silently editing another
  source range.
- Element identity remains `(layout_id, offset)`.

Requirements:
- Add durable `DataBlockLayout` metadata with hunk/source range, layout id,
  optional runtime execution-view identity, role/name/default unit, version, and
  provenance.
- Add durable `DataBlockElement` metadata with layout id, offset, width, kind,
  optional name, array count/stride, representation, type binding placeholder,
  reference interpretation placeholder, and provenance.
- Add Manual Action Log actions for layout create/edit/remove and element
  set/remove/represent.
- Project Manual Action Log entries through effective metadata.
- Reject or explicitly replace overlapping manual layouts.
- Preserve zero offsets and zero-width-invalid checks without truthiness bugs.
- Removing a layout or element must produce explicit raw/gap state and remove
  generated element facts.

Current evidence:
- Target metadata now has first-class `data_block_layouts` containing
  `DataBlockLayout` and nested `DataBlockElement` metadata. Layouts carry
  `layout_id`, hunk/source range, optional runtime identity, role/name/default
  unit, version, provenance, citation, and review fields. Elements carry
  `layout_id`, offset, width, kind, optional name, array shape,
  representation, type-binding placeholder, reference-interpretation
  placeholder, provenance, citation, and review fields.
- Manual Action Log replay supports `create_manual_data_block_layout`,
  `edit_manual_data_block_layout`, `remove_manual_data_block_layout`,
  `set_manual_data_block_element`, `remove_manual_data_block_element`, and
  `represent_manual_data_block_element`.
- Replay preserves zero offsets, rejects invalid zero/negative element widths,
  rejects element spans outside the owning layout, and projects element
  representation changes onto the owning element.
- Overlapping manual layouts are blocked with a
  `manual_data_block_layout_conflict` review item unless the newer layout
  explicitly sets `replace_overlaps=true`; explicit replacement removes the
  replaced layout and its owned elements from active projection.
- Effective metadata projects active manual data-block layouts and nested
  elements into `data_block_layouts`; removing a layout removes it from
  effective metadata and records explicit cleanup/raw state in Manual Action
  Log projection. Removing an element also removes that element from existing
  effective layout metadata when the action provides an explicit span.
- Replay treats `layout_id` as the durable target-local key and validates any
  supplied hunk/source range on edit/remove against the active layout to catch
  stale source-range edits.
- No command catalog, renderer, loop, xref, or type-flow route has been added
  in this issue.

Acceptance criteria:
- Manual replay produces deterministic effective layout/element state. Covered
  by `tests/test_manual_action_log.py`.
- Layout and element identities survive reload and unrelated source rendering
  changes; stale edit/remove range context is blocked. Covered by
  `tests/test_manual_seed_effective_metadata.py` effective metadata projection
  tests and `tests/test_manual_action_log.py` replay validation tests.
- Overlap and replacement behavior is tested.
- Removal returns layout spans to raw/gap metadata state in projection and
  removes active effective layout metadata.
- No command catalog or loop-private mutation route is introduced here.

Remaining work:
- `014-017` owns command catalog exposure, rendering, rendered-source
  verifiers, exact rebuild checks, representation precedence over standalone
  manual representations, and the GenAm `loc_0_00001442` smoke.
- `014-018` owns interpreted-reference facts/xrefs.
- `014-019` owns type/platform binding and type-flow projection.
