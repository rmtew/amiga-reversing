# 006-004: Manual Action CLI

## Parent

[PRD 006: Manual Action Catalog, API, and CLI](../prd/006-manual-action-catalog-api-cli.md)

## Type

AFK

## Labels

done

## What to build

Add thin CLI access for listing catalog actions, inspecting required parameters, and invoking valid log actions against a project without browser state.

## Acceptance criteria

- [x] CLI can list catalog entries for target, review item, row, and element contexts.
- [x] CLI can show parameter requirements for a selected catalog entry.
- [x] CLI can invoke a valid log action and report the appended action id.
- [x] CLI errors are actionable for invalid action ids, invalid parameters, and transient actions.
- [x] CLI tests cover list, show, invoke, and failure cases.
- [x] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

- [006-002: Catalog Action Execution](006-002-catalog-action-execution.md)
- [006-003: Target and Listing Action Contexts](006-003-target-and-listing-action-contexts.md)
