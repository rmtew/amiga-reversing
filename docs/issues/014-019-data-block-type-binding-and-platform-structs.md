Status: Open
Source issue: docs/issues/014-015-data-block-layout-and-reference-interpretation.md
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Bind data block elements to custom/platform types, enum/equate domains, arrays,
nested structs, and type-flow effects. This follows scalar layout rendering and
depends on rendered typed-field verifier proof from `014-012`.

Post-`014-022` split:
This issue consumes generic provenance from `014-010` for data-block pointer
sources and uses the source-family/evidence model rather than inventing a
separate type-binding provenance system.

Accepted review state:
Data-block type/platform binding consumes accepted provenance where value
source matters and must not execute from exploratory reports alone. Generated
type-flow/review descendants require consumed `source_evidence_id` plus
type-binding `owner_action_id`.

Current implementation:
- Row catalog exposes `row.data_block.element.bind_type` and
  `row.data_block.element.clear_type` through the existing data-block element
  Manual Action Log projection.
- Bind payloads carry durable `type_binding` identity: layout id, element
  offset/width, binding kind, bound type/domain id, optional array count, and
  consumed source evidence when supplied.
- Bind payloads now preserve `parent_evidence_ids` with consumed source
  evidence, and catalog availability plus semantic reload verification compare
  that parent dependency set.
- Bind payloads now also preserve consumed evidence `confidence`, matching the
  public type-bind schema and selected row command context.
- Row-scoped data-block type binding now preserves selected provenance carried
  on row command context through command re-selection and execution parameter
  merge, so manual-classified `data_block_pointer` evidence is not dropped or
  regenerated before the durable bind payload.
- Data-block type-bind parameter schemas now advertise the full accepted
  provenance boundary, including path/lifetime scope, conflicts, parent ids,
  manual override reason, and cleanup scope. The public catalog contract now
  matches the evidence fields preserved in bind payloads and checked by
  planner/verifier gates.
- Manual Action Log replay stamps `type_binding.owner_action_id` from the
  append action. Clear-type payloads preserve `previous_type_binding` for stale
  render checks and stamp `previous_type_binding.cleanup_action_id` from the
  clearing action while removing the active binding.
- Clear-type command parameters and schema now expose the active
  type-binding id, binding kind, bound type/domain, owner action, and consumed
  provenance lineage that the clear operation is about to clean up.
- Loop execution is verifier-gated: source-dependent binds require accepted
  `data_block_pointer`, `struct_pointer`, `constant_or_equ`, or
  `rsset_app_base` evidence with lifetime scope; verification proves reload,
  rendered type token presence/absence, provenance consumption where present,
  matching type-binding `owner_action_id`, matching clear-type
  `cleanup_action_id`, and exact round-trip.
- Bind/clear verification now checks generated structured-data seeded entities
  by `source_id=manual_action_log` and `source_locator=type_binding_id`, proving
  active bindings have binding-owned rendered descendants and clear-type removes
  descendants from the cleared binding id.
- Generated structured-data seeded descendants now carry the type-binding
  `owner_action_id`, consumed `source_evidence_id`, and
  `parent_evidence_ids`; bind verification rejects descendants that match the
  binding id but lost or changed the owner/evidence lineage. Descendant
  verification treats `parent_evidence_ids` as an unordered dependency set, so
  replay/catalog ordering differences do not reject equivalent lineage.
- Planner command availability for `row.data_block.element.bind_type` and
  `row.data_block.element.clear_type` now requires the refreshed catalog entry
  to match the selected data-block element identity `(layout_id, offset,
  width)`. A stale type-binding candidate can no longer borrow availability
  from a different element row.
- Clear-type availability also compares the selected active binding id,
  binding kind, bound type/domain, owner action, and consumed provenance fields
  when the command carries them, preventing stale cleanup against a later
  binding on the same data-block element.
- Effective metadata expands accepted custom-struct data-block bindings into
  typed structured-data field entities. The C policy loader now preserves
  `struct_name`, `field_name`, `field_type`, `c_type`, `pointer_struct`, and
  `value_domain` from seeded entities so the existing renderer emits typed
  field comments while exact bytes and round-trip stay unchanged.
- Custom-struct expansion covers explicit gaps and arrays when the bound shape
  fits the element width.
- Platform struct bindings now resolve parsed NDK struct ids and C aliases
  such as `MsgPort` -> `MP`, flatten inherited base fields and nested struct
  fields, and render the resulting typed field entities with exact rebuild
  proof.
- Scalar enum/equate domain bindings project `value_domain` onto the bound
  element's structured-data item so known values render symbolically, with exact
  rebuild proof.
- Generated type-flow facts/review items remain open beyond active binding
  owner, binding-owned seeded descendants with consumed evidence lineage, and
  clear-type cleanup verification.

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
- Consume accepted `data_block_pointer`, `struct_pointer`, `constant_or_equ`,
  or `rsset_app_base` provenance evidence where type binding depends on a
  value's source. Generated type-flow/review descendants should carry consumed
  `source_evidence_id` plus the type-binding `owner_action_id`.
- Block propagation on path-specific/conflicting provenance until the user
  selects a path/lifetime scope or records a manual classification/override.

Acceptance criteria:
- Render verifier proves custom/platform typed-field paths before loop use.
- Type binding consumes accepted provenance evidence where applicable and does
  not treat exploratory provenance reports as write authority.
- Type/domain binding identity should include layout id, element offset,
  element width/count, binding kind, bound custom/platform type or domain id,
  consumed `source_evidence_id` when value source matters, and the generating
  `owner_action_id`.
- Nested/platform struct rendering must use parsed platform/KB ids or target
  custom struct identities, not copied include text. Rendering should preserve
  scalar layout bytes, expand fields only where type shape covers the element,
  and keep gaps/padding explicit.
- Generated type-flow/review descendants must be owner-scoped: propagated
  pointer/base facts, nested field refs, interpreted field refs, xrefs, and
  ambiguity review items carry the binding owner and consumed evidence id.
- Removal verifier must prove the binding is gone, all owned descendants are
  gone, unrelated scalar layout/interpreted refs/independent type bindings
  remain, and exact rebuild still passes.
- Availability checks already enforce selected data-block element identity for
  bind/clear commands. Future type-flow/review propagation must preserve that
  element identity plus the type-binding owner id and consumed
  `source_evidence_id`/`parent_evidence_ids`.
- Replay reloads type bindings and domains exactly.
- Type-flow verifier proves supported propagated facts or expected review
  items.
- Removal verifier proves type-flow/review projections from the deleted binding
  disappear.
- Exact rebuild remains mandatory.
