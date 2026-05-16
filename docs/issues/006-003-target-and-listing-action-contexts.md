# 006-003: Target and Listing Action Contexts

## Parent

[PRD 006: Manual Action Catalog, API, and CLI](../prd/006-manual-action-catalog-api-cli.md)

## Type

AFK

## Labels

done

## What to build

Extend catalog queries beyond review items so target-wide, listing-row, and listing-element contexts can return currently valid log and transient actions.

## Acceptance criteria

- [x] Catalog queries support target-wide, row, and element contexts.
- [x] Returned actions distinguish durable log actions from transient UI/navigation actions.
- [x] Context payloads include enough evidence for LLM and CLI callers to choose actions without scraping UI text.
- [x] Tests cover at least one target-wide action, one row action, and one element action.
- [x] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

- [006-001: Review Item Action Catalog](006-001-review-item-action-catalog.md)
