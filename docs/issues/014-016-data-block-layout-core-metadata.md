Status: Open
Source issue: docs/issues/014-015-data-block-layout-and-reference-interpretation.md
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Implement the first-class data block layout source model and Manual Action Log
projection. This issue owns identity, metadata shape, effective metadata merge,
overlap handling, and removal behavior. It does not own command catalog
exposure, rendering, or interpreted references.

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

Acceptance criteria:
- Manual replay produces deterministic effective layout/element state.
- Layout and element identities survive reload and unrelated source rendering
  changes.
- Overlap and replacement behavior is tested.
- Removal returns layout spans to raw/gap metadata state.
- No command catalog or loop-private mutation route is introduced here.
