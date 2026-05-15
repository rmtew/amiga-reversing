# 010-001: Manual Representation Actions

## Parent

[PRD 010: Semantic Helper Actions](../prd/010-semantic-helper-actions.md)

## Type

AFK

## What to build

Add **Manual Representation** actions for value and literal display preferences without treating those preferences as **Manual Seeds**.

## Acceptance criteria

- [ ] Manual representation action schema supports at least hex, binary, character, and string/literal style choices.
- [ ] Actions append to the **Manual Action Log** and project into current manual state.
- [ ] Rendering and listing display consume projected **Manual Representation** state.
- [ ] Representation changes do not by themselves reconcile a range or classify bytes as code/data.
- [ ] Backend, rendering, and web/API tests cover a representative representation change.
- [ ] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

- [006-002: Catalog Action Execution](006-002-catalog-action-execution.md)
- [007-004: Listing Element Selection](007-004-listing-element-selection.md)
