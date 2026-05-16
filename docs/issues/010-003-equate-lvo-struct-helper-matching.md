# 010-003: Equate, LVO, and Struct Helper Matching

## Parent

[PRD 010: Semantic Helper Actions](../prd/010-semantic-helper-actions.md)

## Related PRDs

- [PRD 017: Inline and Palette Parameter Sessions](../prd/017-inline-and-palette-parameter-sessions.md)

## Type

AFK

## Labels

done

## What to build

Add contextual helper matching so selected immediate values can find value-equivalent equates, LVOs, and struct offsets from project knowledge and current facts.

## Acceptance criteria

- [x] Catalog entries can present equate, LVO, and struct-offset candidates for a selected immediate value.
- [x] Candidate output includes source namespace and enough context for a user or LLM to choose safely.
- [x] Chosen helper action appends domain intent rather than editing source text.
- [x] Tests cover matching, disambiguation, and invalid-context behavior.
- [x] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

- [010-001: Manual Representation Actions](010-001-manual-representation-actions.md)
