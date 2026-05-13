# 0001-006 Checklist Review UI And Suggested Actions

## Parent

PRD 0001: Manual Review Workflow

## What to build

Build the checklist-first Manual Review UI. The primary workflow is an ordered list of Manual Review Items with facets for kind, confidence, state, section, source, and range. Each item can navigate to evidence and can offer structured Suggested Review Actions that either stay transient or append domain actions to the Manual Action Log.

## Acceptance criteria

- [ ] Users can view Manual Review Items as a checklist sorted by severity, scope, and range.
- [ ] Users can filter by kind, confidence, state, section, source, and range.
- [ ] Users can navigate from a Manual Review Item to the relevant listing range without appending log actions.
- [ ] Users can create Manual Seeds from structured suggested actions.
- [ ] Users can resolve or acknowledge review items through Manual Action Log actions.
- [ ] Orphan code candidates offer navigate, create required code Manual Seed, and resolve as data or padding actions.
- [ ] Unreconciled data ranges offer navigate, create data Manual Seed as string/scalar table/pointer table/raw unit, and resolve as opaque data actions.
- [ ] Suspicious instruction decodes offer navigate, create data Manual Seed, and acknowledge actions.
- [ ] Manual label/comment unreconciled items offer create Manual Seed, remove annotation, and acknowledge actions.
- [ ] Reproduction mismatches offer open comparison, rerun Round-Trip Verification, and acknowledge container-only difference actions when Content Exactness is preserved.
- [ ] The UI distinguishes normal open work, resolved work, changed-since-resolution work, and live blockers.
- [ ] CDP tests pass.
- [ ] `cmd /c src\precommit.bat` passes.

## Blocked by

- 0001-004 Manual Review Item Generation
- 0001-005 Manual Labels Comments And Label Scope
