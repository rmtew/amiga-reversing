# 017-005: Semantic Filtered Chooser Mechanics

## Parent

[PRD 017: Inline and Palette Parameter Sessions](../prd/017-inline-and-palette-parameter-sessions.md)

## Related PRDs

- [PRD 010: Semantic Helper Actions](../prd/010-semantic-helper-actions.md)
- [PRD 011: Structured Contextual Action Metadata](../prd/011-structured-contextual-action-metadata.md)

## Type

AFK

## Labels

done

## What to build

Render filtered chooser **Parameter Sessions** for semantic helper actions using backend-provided options, local filtering, cursor selection, preview, cancel, and commit mechanics.

## Acceptance criteria

- [x] Backend-provided semantic options render in a filtered chooser with top input.
- [x] Typing filters returned options locally.
- [x] Arrow keys move selection and Enter commits the selected option.
- [x] Option metadata supports local preview through typed preview kinds.
- [x] UI does not compute semantic eligibility or option ranking.
- [x] Tests cover chooser mechanics with fixture options for a semantic helper action.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Completion Notes

- Semantic helper actions now expose filtered-chooser metadata with backend-owned options and `s` as the direct binding.
- UI filtering and selection are local; payload parameters come from the selected backend option.

## Blocked by

- [017-004: Representation Choice Grid](017-004-representation-choice-grid.md)
- [010-003: Equate, LVO, and Struct Helper Matching](010-003-equate-lvo-struct-helper-matching.md)
- [011-003: Replace Text-Based Semantic Matching](011-003-replace-text-based-semantic-matching.md)
