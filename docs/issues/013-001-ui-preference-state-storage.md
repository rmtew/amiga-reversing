# 013-001: UI Preference State Storage

## Parent

[PRD 013: UI Preference State and Entrypoint Open](../prd/013-ui-preference-state-and-entrypoint-open.md)

## Related PRDs

- [PRD 007: Listing Selection and Keyboard Model](../prd/007-listing-selection-keyboard-model.md)
- [PRD 018: Reproduction Profiles and Policy Summary](../prd/018-reproduction-profiles-and-policy-summary.md)
- [PRD 021: Source Export Workflow](../prd/021-source-export-workflow.md)

## Type

AFK

## Labels

done

## What to build

Add project-local **UI Preference State** storage for listing location and non-authoritative UI choices without writing reverse-engineering facts or **Manual Action Log** entries.

## Acceptance criteria

- [x] The project can persist and reload listing location preference state.
- [x] Preference state can remember reproduction profile view choice and source export assembler choice without becoming policy authority.
- [x] Preference state is scoped to the project target identity needed for UI restoration.
- [x] Writes do not touch the **Manual Action Log**.
- [x] Stale or missing preference state fails safely.
- [x] Tests cover load, save, missing file, and stale identity behavior.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Progress

Completed 2026-05-16. Added project-local `ui_preferences.json`, API routes, and storage tests.

## Blocked by

- None
