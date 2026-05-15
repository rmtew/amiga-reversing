# 014-004: Mixed Range Action Eligibility

## Parent

[PRD 014: Range Listing Selection and Catalog Context](../prd/014-range-listing-selection-and-catalog-context.md)

## Related PRDs

- [PRD 006: Manual Action Catalog, API, and CLI](../prd/006-manual-action-catalog-api-cli.md)
- [PRD 010: Semantic Helper Actions](../prd/010-semantic-helper-actions.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Return applicable, partially applicable, and unavailable catalog actions for mixed row ranges, with explicit applicable subranges and concise reasons.

## Acceptance criteria

- [ ] Catalog responses distinguish applicable, partial, and unavailable range actions.
- [ ] Partial actions include explicit applicable subranges.
- [ ] Unavailable actions include concise user-facing reasons.
- [ ] Actions with unclear range semantics are unavailable rather than guessed.
- [ ] Backend tests cover homogeneous, mixed, and invalid ranges.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [014-003: Range Catalog Context Query](014-003-range-catalog-context-query.md)
