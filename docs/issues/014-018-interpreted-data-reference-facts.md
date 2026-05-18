Status: Open
Source issue: docs/issues/014-015-data-block-layout-and-reference-interpretation.md
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Add durable manual interpreted-reference support for values inside data block
elements. This follows scalar layout rendering and does not own struct/type
binding.

Requirements:
- Add `interpret_manual_data_block_element_ref` Manual Action Log support,
  exposed through a `data_block.element.interpret_ref` command id.
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

Acceptance criteria:
- Replay reloads interpreted-reference state exactly.
- Render verifier checks expected symbolic text for supported kinds.
- Xref verifier checks generated source and target xrefs.
- Removal verifier proves generated xrefs and symbolic rendering disappear.
- Exact rebuild remains mandatory.
