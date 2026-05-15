# 017-005: Semantic Filtered Chooser Mechanics

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

Render filtered chooser **Parameter Sessions** for semantic helper actions using backend-provided options, local filtering, cursor selection, preview, cancel, and commit mechanics.

## Acceptance criteria

- [ ] Backend-provided semantic options render in a filtered chooser with top input.
- [ ] Typing filters returned options locally.
- [ ] Arrow keys move selection and Enter commits the selected option.
- [ ] Option metadata supports local preview through typed preview kinds.
- [ ] UI does not compute semantic eligibility or option ranking.
- [ ] Tests cover chooser mechanics with fixture options for a semantic helper action.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [017-004: Representation Choice Grid](017-004-representation-choice-grid.md)
- [010-003: Equate, LVO, and Struct Helper Matching](010-003-equate-lvo-struct-helper-matching.md)
- [011-003: Replace Text-Based Semantic Matching](011-003-replace-text-based-semantic-matching.md)
