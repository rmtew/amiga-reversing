Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Define durable target identities for every editable source-converging construct
identified by 014-001.

Out of scope:
Do not add UI-only or agent-only identifiers. Do not rely on row index, row
text, DOM text, or screenshots.

Files likely touched:
- listing locator and element identity code
- manual action/catalog identity helpers
- source rendering/projection tests
- proposal matrix

Acceptance criteria:
- Each editable construct has a stable identity contract.
- Identities survive projection rebuilds and can be used by Manual Action Log
  replay, command discovery, command execution, and verification.
- Derived analysis facts carry enough ownership identity to be recomputed or
  retracted when their source manual action or source fact is removed.
- Missing identity support is broken into implementation issues.

Current observations:
- `suppress_seeded_item` uses the durable tuple `(kind, hunk, addr)` for
  Manual Action Log replay and effective metadata projection.
- Listing and command row contexts now surface suppressible
  `target_seeded_metadata.json` entries with `(kind, hunk, addr)` plus source
  id/path/locator provenance, which is enough for seeded-item suppression
  commands.
- Listing element identity preserves operand index `0` for selected operands,
  app slots, typed accesses, and typed gaps instead of treating it as absent.
- Command mutation metadata preserves row index `0` when reporting label local
  effects and pending analysis ranges.
- Data-block layout identity is now defined by the `014-015` investigation:
  source-backed layouts use target, hunk, source range, and layout id;
  runtime-backed layouts also include source/origin execution-view identity;
  elements use layout id plus offset. Implementation belongs in
  `014-016-data-block-layout-core-metadata.md`, with command-specific use in
  `014-017` through `014-019`.
- RSSET numeric use-site binding identity is now defined by the `014-021`
  investigation: target, hunk, source address, operand index, base register,
  displacement, chosen `(layout_name, base_symbol)`, and base-evidence id.
  Implementation belongs in `014-011`; identity helpers must preserve operand
  index `0` and must not use row index or rendered text as identity.
- Derived analysis facts need ownership identity too. Xrefs, type-flow facts,
  review items, symbolic projections, and other descendants of a manual action
  must be attributable to the source manual action or source fact so corrective
  actions can retract only those descendants.
- Review-item/reproduction correction identities beyond seeded-item row
  suppression still need specific contracts.

Required tests:
Focused identity/locator tests for any new identity contracts.

Cleanup / deletion:
Delete after all required identity gaps are either implemented or split into
specific issues.
