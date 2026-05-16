# 014-006: PRD 014 Review and Tightening

## Parent

[PRD 014: Range Listing Selection and Catalog Context](../prd/014-range-listing-selection-and-catalog-context.md)

## Related PRDs

- [PRD 006: Manual Action Catalog, API, and CLI](../prd/006-manual-action-catalog-api-cli.md)
- [PRD 007: Listing Selection and Keyboard Model](../prd/007-listing-selection-keyboard-model.md)
- [PRD 011: Structured Contextual Action Metadata](../prd/011-structured-contextual-action-metadata.md)

## Type

AFK

## Labels

done

## What to build

Review range **Listing Selection** and range catalog behavior against PRD 014, especially hidden-row inference, partial applicability, and structured metadata use.

## Acceptance criteria

- [x] Range actions do not infer hidden rows outside the selected visible range.
- [x] Range action eligibility does not parse rendered source text.
- [x] Focus, anchor, and range selection behavior is covered by tests.
- [x] Mixed eligibility is covered by backend and CDP tests.
- [x] PRD 014 issue links are accurate.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Completion

Reviewed against PRD 014. The implementation uses structured row metadata and
explicit selected indexes only.

## Blocked by

- [014-001: Focus Anchor Range Selection](014-001-focus-anchor-range-selection.md)
- [014-002: Range Selection Preserved Across Refresh](014-002-range-selection-preserved-across-refresh.md)
- [014-003: Range Catalog Context Query](014-003-range-catalog-context-query.md)
- [014-004: Mixed Range Action Eligibility](014-004-mixed-range-action-eligibility.md)
- [014-005: Command Palette Range Actions](014-005-command-palette-range-actions.md)
