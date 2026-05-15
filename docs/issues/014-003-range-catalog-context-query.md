# 014-003: Range Catalog Context Query

## Parent

[PRD 014: Range Listing Selection and Catalog Context](../prd/014-range-listing-selection-and-catalog-context.md)

## Related PRDs

- [PRD 006: Manual Action Catalog, API, and CLI](../prd/006-manual-action-catalog-api-cli.md)
- [PRD 011: Structured Contextual Action Metadata](../prd/011-structured-contextual-action-metadata.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Add a range-selection catalog query context that sends explicit selected row identities and visible structured row metadata to the backend.

## Acceptance criteria

- [x] The web UI can query the catalog for a selected row range.
- [x] Requests include selected row ids/indexes and visible structured row metadata.
- [x] The backend accepts range context as distinct from row and element context.
- [x] Hidden rows outside the selected visible range are not inferred.
- [x] Route and web tests cover valid and stale range contexts.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Completion

Added `context=range` catalog requests with explicit `row_indexes` and JSON row
metadata. Backend rejects stale row metadata that does not match row indexes.

## Blocked by

- [014-002: Range Selection Preserved Across Refresh](014-002-range-selection-preserved-across-refresh.md)
- [011-002: Structured Catalog Context Model](011-002-structured-catalog-context-model.md)
