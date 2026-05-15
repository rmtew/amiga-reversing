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

- [x] Catalog responses distinguish applicable, partial, and unavailable range actions.
- [x] Partial actions include explicit applicable subranges.
- [x] Unavailable actions include concise user-facing reasons.
- [x] Actions with unclear range semantics are unavailable rather than guessed.
- [x] Backend tests cover homogeneous, mixed, and invalid ranges.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Completion

Range seed actions report availability and row-level reasons. Semantic helper
range actions are unavailable unless a precise element context is selected.

## Blocked by

- [014-003: Range Catalog Context Query](014-003-range-catalog-context-query.md)
