Status: In progress
Source issue: docs/issues/014-015-data-block-layout-and-reference-interpretation.md
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Expose scalar data block layout commands, render layout elements, and verify
source convergence. This is the first production slice after `014-016`.

Requirements:
- Expose row/range commands to create scalar layouts over selected data ranges. First slice implemented:
  `row.data_block.layout.create` and `range.data_block.layout.create` append
  `create_manual_data_block_layout` through the public command catalog.
- Expose element commands to set/remove/represent scalar byte/word/long
  elements, arrays/runs, padding, and gaps. First slice implemented:
  `row/range.data_block.element.set`, `.remove`, and `.represent` append
  element actions through the public command catalog with explicit `layout_id`
  and layout-relative `offset`; selected rows/ranges infer width where needed.
- Render element-sized `dc.b`, `dc.w`, `dc.l`, `dcb.*`, numeric values, and
  character values while preserving exact rebuild. First slice implemented for
  scalar element projection via effective metadata: data-block elements emit
  renderable seeded entities, and element representation emits render policy
  manual representations.
- Make element representation authoritative over overlapping standalone manual
  representations. First slice implemented in effective metadata by removing
  overlapping standalone representations while the data-block element
  representation is active.
- Treat scalar layout as rendering/effective-metadata only: it may consume
  existing analysis evidence for candidates, but must not generate xrefs,
  type-flow facts, or review items.
- Add replay, rendered-source, removal, and exact round-trip verifiers.
- Add loop execution coverage that reports the action-specific verifier.
- Add a GenAm smoke for `loc_0_00001442` as `ascii_hex_digit_value`.

Implemented tests:
- Effective metadata projects data-block elements into seeded entities and
  element-scoped manual representations.
- Effective metadata gives element representation precedence over overlapping
  standalone manual representations.
- Effective metadata restores an overlapping standalone manual representation
  after the owning data-block element is removed.
- Command catalog availability and `/commands/execute` cover range layout
  creation.
- Command catalog availability and `/commands/execute` cover row/range
  element set/remove/represent commands.
- Reversing loop execution now selects data-block layout/element state
  verifiers, checks Manual Action Log replay, semantic reload state for element
  set/represent/remove, exact round-trip, and blocks unsupported type/ref
  commands without a verifier.
- C backend render matrix covers data-block scalar byte/word/long elements,
  character byte arrays, explicit gap bytes, and padding bytes with exact
  rebuild.
- C backend smoke proves a data-block layout element renders named character
  `dc.b` source and reassembles exactly.

Remaining:
- Active-layout-aware element selection context, so element commands no longer
  need explicit layout id/offset parameters.
- Removal-to-raw/gap rendered-source verifier.
- Rendered-source verifier coverage beyond semantic state and exact round-trip.
- Compact `dcb.*` run rendering for padding/gap spans and GenAm
  `loc_0_00001442` smoke.

Acceptance criteria:
- The command catalog exposes supported layout commands without private loop
  routes.
- Applying the GenAm hex table layout changes rendered source as expected and
  rebuilds exactly.
- Removing the layout returns the affected source to raw/coarse data rendering.
- Effective metadata gives data-block element representation precedence over
  overlapping standalone manual representations, and removing the element or
  layout restores the standalone representation where it still applies.
- The loop blocks unsupported layout/type/ref requests with precise missing
  capability reports.

Required tests:
- Command catalog availability and `/commands/execute` tests for row/range
  layout creation and element set/remove/represent commands.
- Rendered-source and exact rebuild tests for scalar byte/word/long elements,
  padding/gaps, numeric values, and character values; compact run rendering
  remains open.
- Effective-metadata precedence tests for data-block element representations
  over standalone manual representations, plus removal fallback.
- Loop verifier tests for replay, rendered source, removal, exact round-trip,
  and unsupported type/ref blockers.
