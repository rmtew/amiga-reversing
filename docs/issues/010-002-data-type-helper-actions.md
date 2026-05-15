# 010-002: Data Type Helper Actions

## Parent

[PRD 010: Semantic Helper Actions](../prd/010-semantic-helper-actions.md)

## Type

AFK

## What to build

Expose data type helper actions for byte, word, long, string, table, and raw block classification as **Manual Seed** actions from catalog contexts.

## Acceptance criteria

- [ ] Helper actions create or update data **Manual Seeds** with role, unit, encoding, and range as appropriate.
- [ ] Actions rerun analysis and split rendered blocks as needed.
- [ ] Review dialog, command palette, API, and CLI can invoke the same helper entries where context is valid.
- [ ] Tests cover string and scalar/table-style conversions.
- [ ] Round-trip verification is required before review can be marked clear for rendered-source changes.
- [ ] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

- [006-002: Catalog Action Execution](006-002-catalog-action-execution.md)
- [007-004: Listing Element Selection](007-004-listing-element-selection.md)
