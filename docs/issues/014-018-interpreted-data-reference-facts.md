Status: In progress
Source issue: docs/issues/014-015-data-block-layout-and-reference-interpretation.md
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Add durable manual interpreted-reference support for values inside data block
elements. This follows scalar layout rendering and does not own struct/type
binding.

Requirements:
- Add `interpret_manual_data_block_element_ref` Manual Action Log support,
  exposed through a `data_block.element.interpret_ref` command id. First slice
  implements replay/projection state and row command catalog exposure through
  `row.data_block.element.interpret_ref`; render/xref projection remains open.
- Model reference kind, width, signedness, base/source evidence, scale, target
  locator, confidence, and xref-generation mode.
- Project interpreted refs into a dedicated manual fact family.
- Generate symbolic rendering where supported.
- Generate bidirectional xrefs and remove them when the owning interpretation is
  removed.
- Preserve the owning layout id, element offset, and interpretation identity on
  generated xrefs so auto-analysis can distinguish manual derived refs from
  analyzer-native refs and delete them on removal.
- Expose a corrective remove/clear command for bad interpretations; verifier
  must prove symbolic rendering and generated xrefs disappear while unrelated
  refs remain.
- Support only reference kinds with clear local evidence and verifier coverage;
  unsupported kinds remain missing capability blockers.

Implemented tests:
- Manual Action Log projects active `data_block_interpreted_refs` with durable
  interpretation id, owning `layout_id`, element `offset`, width, reference
  kind, target locator, confidence, and xref-generation mode.
- Manual Action Log projects explicit interpreted-reference removal into
  `removed_data_block_interpreted_refs`.
- Removing an owning data-block layout also removes owned interpreted-reference
  state.
- Row command catalog exposes `row.data_block.element.interpret_ref` and
  `row.data_block.element.clear_ref`.
- Command execution appends interpreted-reference and corrective clear Manual
  Action Log entries and reports authoritative local effects.
- Effective metadata projects active manual interpreted-reference facts onto the
  owning `DataBlockElement.reference_interpretation`, and corrective removal
  clears that projected element interpretation.
- Loop execution still blocks interpreted-reference commands as missing an
  action-specific render/xref verifier.

Remaining:
- Symbolic rendering for supported reference kinds.
- Generated bidirectional xrefs with owner identity.
- Verifiers for rendered text, generated xrefs, cleanup disappearance, and
  exact rebuild.

Acceptance criteria:
- Replay reloads interpreted-reference state exactly.
- Render verifier checks expected symbolic text for supported kinds.
- Xref verifier checks generated source and target xrefs.
- Removal verifier proves generated xrefs and symbolic rendering disappear.
- Exact rebuild remains mandatory.
