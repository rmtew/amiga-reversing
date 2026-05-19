Status: Open
Source issue: docs/issues/014-015-data-block-layout-and-reference-interpretation.md
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Bind data block elements to custom/platform types, enum/equate domains, arrays,
nested structs, and type-flow effects. This follows scalar layout rendering and
depends on rendered typed-field verifier proof from `014-012`.

Current implementation:
- Row catalog exposes `row.data_block.element.bind_type` and
  `row.data_block.element.clear_type` through the existing data-block element
  Manual Action Log projection.
- Bind payloads carry durable `type_binding` identity: layout id, element
  offset/width, binding kind, bound type/domain id, optional array count, and
  consumed source evidence when supplied.
- Manual Action Log replay stamps `type_binding.owner_action_id` from the
  append action. Clear-type payloads preserve `previous_type_binding` for stale
  render checks while removing the active binding.
- Loop execution is verifier-gated: source-dependent binds require accepted
  `data_block_pointer`, `struct_pointer`, `constant_or_equ`, or
  `rsset_app_base` evidence with lifetime scope; verification proves reload,
  rendered type token presence/absence, provenance consumption where present,
  and exact round-trip.
- Nested/platform field expansion, generated type-flow facts/review items, and
  owner-scoped descendant cleanup remain open.

Requirements:
- Bind elements to existing custom structs by target struct identity.
- Bind elements to platform structs/enums by compact parsed include or KB ids.
- Support arrays, nested structs, padding, and gaps without copying platform
  text into every action.
- Support enum/equate domains for scalar element values.
- Consume target-local equate definitions and value-display metadata owned by
  `014-009` and `014-020`; this issue does not own EQU definition rendering.
- Project supported pointer/base field type-flow facts.
- Create review items rather than silent facts for ambiguous propagation.
- Preserve the owning layout id, element offset, and type-binding identity on
  generated type-flow facts and review items so removal can delete only the
  facts derived from that binding.
- Expose corrective unbind/clear-type commands for bad type applications;
  verifier must prove generated type-flow facts/review items disappear and
  previous scalar/layout rendering remains valid.
- Compose with RSSET/app-slot refinement where a layout element identifies a
  base-relative field.

Acceptance criteria:
- Render verifier proves custom/platform typed-field paths before loop use.
- Replay reloads type bindings and domains exactly.
- Type-flow verifier proves supported propagated facts or expected review
  items.
- Removal verifier proves type-flow/review projections from the deleted binding
  disappear.
- Exact rebuild remains mandatory.
