# 017-004: Representation Choice Grid

## Parent

[PRD 017: Inline and Palette Parameter Sessions](../prd/017-inline-and-palette-parameter-sessions.md)

## Related PRDs

- [PRD 010: Semantic Helper Actions](../prd/010-semantic-helper-actions.md)
- [PRD 011: Structured Contextual Action Metadata](../prd/011-structured-contextual-action-metadata.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Add choice-grid **Parameter Sessions** for **Manual Representation** actions so users can choose value display forms with local preview and catalog-backed commit.

## Acceptance criteria

- [ ] Representation options are backend-provided and rendered as a compact choice grid.
- [ ] Options show type and rendered-value preview, such as binary, hex, decimal, or char form.
- [ ] Moving selection updates local preview without server round-trips.
- [ ] Enter commits a **Manual Representation** action; Escape cancels.
- [ ] Works in inline host and palette host from the same interaction schema.
- [ ] Tests cover preview, commit, cancel, and catalog payload.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [017-002: Palette Hosted Parameter Sessions](017-002-palette-hosted-parameter-sessions.md)
- [017-003: Inline Text Editors For Labels And Comments](017-003-inline-text-editors-for-labels-and-comments.md)
- [010-001: Manual Representation Actions](010-001-manual-representation-actions.md)
