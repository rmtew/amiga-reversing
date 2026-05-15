# 011-003: Replace Text-Based Semantic Matching

## Parent

[PRD 011: Structured Contextual Action Metadata](../prd/011-structured-contextual-action-metadata.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Replace semantic helper eligibility based on rendered/source text scanning with structured value and reference matching from the catalog context model.

## Acceptance criteria

- [ ] Equate, LVO, and struct-offset helper candidates are generated only from structured selected values.
- [ ] Numeric-looking labels, symbols, comments, and directive text do not produce value helper candidates.
- [ ] Decimal, hex, negative, and sized immediate values are handled through structured metadata.
- [ ] Existing Manual Semantic Hint payloads still record domain intent rather than source text edits.
- [ ] The old text numeric scanner is removed or limited to test-only fallback with a tracked removal note.
- [ ] Backend tests cover immediate helper matching, non-immediate rejection, and numeric-looking label regression.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [011-002: Structured Catalog Context Model](011-002-structured-catalog-context-model.md)
