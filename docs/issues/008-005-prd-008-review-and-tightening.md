# 008-005: PRD 008 Review and Tightening

## Parent

[PRD 008: Command Palette and Default Key Bindings](../prd/008-command-palette-and-key-bindings.md)

## Type

AFK

## What to build

Review the completed PRD 008 palette and key-binding work, identify missed commands, confusing defaults, over-complicated registry behavior, or weak tests, and address them directly or split follow-up issues.

## Acceptance criteria

- [ ] Review palette behavior, binding badges, registry shape, review-action parity, and tests against PRD 008.
- [ ] Simplify unnecessary abstraction or duplicated command definitions found during review.
- [ ] Add missing tests or issue follow-ups for broader gaps.
- [ ] PRD 008 links and issue statuses remain accurate after review.
- [ ] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

- [008-001: Key Binding Registry](008-001-key-binding-registry.md)
- [008-002: Contextual Command Palette](008-002-contextual-command-palette.md)
- [008-003: Palette Global Mode](008-003-palette-global-mode.md)
- [008-004: Review Actions Through Catalog](008-004-review-actions-through-catalog.md)
