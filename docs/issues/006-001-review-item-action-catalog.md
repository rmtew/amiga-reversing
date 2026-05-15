# 006-001: Review Item Action Catalog

## Parent

[PRD 006: Manual Action Catalog, API, and CLI](../prd/006-manual-action-catalog-api-cli.md)

## Type

AFK

## What to build

Move existing **Manual Review Item** action eligibility into the backend-owned **Manual Action Catalog** and have the Review panel render those catalog entries instead of maintaining its own action rules.

## Acceptance criteria

- [ ] Backend catalog entries cover the current Review panel actions for all existing review item kinds.
- [ ] Catalog entries include stable id, label, enabled state, target context, log/transient marker, and parameter shape.
- [ ] The Review panel renders actions from catalog data without duplicating eligibility logic.
- [ ] Backend and web tests cover representative review item kinds.
- [ ] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

None - can start immediately
