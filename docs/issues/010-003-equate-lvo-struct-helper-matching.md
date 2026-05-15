# 010-003: Equate, LVO, and Struct Helper Matching

## Parent

[PRD 010: Semantic Helper Actions](../prd/010-semantic-helper-actions.md)

## Type

AFK

## What to build

Add contextual helper matching so selected immediate values can find value-equivalent equates, LVOs, and struct offsets from project knowledge and current facts.

## Acceptance criteria

- [ ] Catalog entries can present equate, LVO, and struct-offset candidates for a selected immediate value.
- [ ] Candidate output includes source namespace and enough context for a user or LLM to choose safely.
- [ ] Chosen helper action appends domain intent rather than editing source text.
- [ ] Tests cover matching, disambiguation, and invalid-context behavior.
- [ ] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

- [010-001: Manual Representation Actions](010-001-manual-representation-actions.md)
