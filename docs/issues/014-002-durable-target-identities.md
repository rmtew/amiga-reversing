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
- Review-item/reproduction correction identities beyond seeded-item row
  suppression still need specific contracts.

Required tests:
Focused identity/locator tests for any new identity contracts.

Cleanup / deletion:
Delete after all required identity gaps are either implemented or split into
specific issues.
