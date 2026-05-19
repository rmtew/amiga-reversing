Status: Complete for supported absolute byte/word/long refs; broader reference
kinds deferred until local evidence and verifier coverage exist.
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
  `row.data_block.element.interpret_ref`; symbolic render projection is now
  covered for supported absolute byte/word/long refs, and generated
  source-owned runtime-address ref projection is covered for those refs.
- Model reference kind, width, signedness, base/source evidence, scale, target
  locator, confidence, and xref-generation mode.
- Project interpreted refs into a dedicated manual fact family.
- Generate symbolic rendering where supported.
- Generate source-owned runtime-address refs carrying target hunk/offset and
  remove them when the owning interpretation is removed. Target-side inbound
  navigation remains a follow-up and must not be implied by current verifier
  coverage.
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
- Interpret-ref command payloads record decoded selected source bytes as
  `source_value`, and Manual Action Log replay rejects unsupported kinds,
  missing/mismatched absolute target locators, width mismatches against the
  owning element, and source values that do not equal the intended target.
- Effective metadata reuses those guards before output projection, then emits a
  generated target-local `EQU` plus element-scoped symbolic representation for
  supported absolute byte/word/long refs.
- The C policy target-equate table is sized to the generated interpreted-ref
  table slice, and C-backed coverage proves more than 16 interpreted refs render
  and rebuild exactly.
- Effective metadata emits owned manual runtime-address refs for supported
  absolute refs when `xref_generation_mode` is `bidirectional` or
  `source_only`; generated refs carry the owning layout id, element offset,
  interpreted-ref id, target hunk/offset, runtime address, and generation mode.
- C listing/analysis JSON imports those manual runtime-address refs and exposes
  the owner identity on `runtime_address_refs`; target validation rejects
  generated xrefs whose source span or target hunk/offset is outside the
  target-local source.
- C source rendering consumes symbol manual representations for scalar
  byte/word/long data and exact rebuild coverage proves `dc.l dblk_ref_*`
  remains byte-identical.
- Loop execution verifies interpreted-reference state, rendered directive plus
  symbol presence, generated runtime-address ref presence, corrective symbol
  and xref disappearance, and exact round-trip.

Remaining:
- Broader reference kinds beyond locally proven absolute byte/word/long refs are
  out of this slice and remain missing-capability blockers.

Acceptance criteria:
- Replay reloads interpreted-reference state exactly.
- Render verifier checks expected symbolic text for supported kinds. Covered for
  absolute byte/word/long refs.
- Xref verifier checks generated source-owned runtime-address refs carrying the
  target hunk/offset and owner identity. Target-side inbound xref navigation is
  not part of this completed slice.
- Removal verifier proves generated xrefs and symbolic rendering disappear.
  Covered for supported absolute refs.
- Exact rebuild remains mandatory. Covered for symbolic render.
