# 0001-004 Manual Review Item Generation

## Parent

PRD 0001: Manual Review Workflow

## What to build

Generate base Manual Review Items from current analysis facts and projected manual state. Items have stable ids, Evidence Fingerprints, range or target scope, Review Confidence, state, and structured Suggested Review Actions. Apply Manual Resolutions by matching Evidence Fingerprints, reopening changed evidence as needed. Compute Review State as `clear`, `needs_review`, or `blocked`.

## Acceptance criteria

- [ ] Review item ids are stable for target, kind, and normalized scope.
- [ ] Evidence Fingerprints change when supporting facts change.
- [ ] Resolutions close matching current evidence but changed evidence reopens review work.
- [ ] Review item kinds include reproduction mismatch, unsupported container shape, orphan code candidate, unreconciled data range, suspicious instruction decode, manual seed conflict, manual action log inconsistency, and manual action log target mismatch.
- [ ] `manual_action_log_target_mismatch` can be emitted from log/header validation even when normal manual projection is skipped.
- [ ] Content Exactness failures or uncheckable content comparison set Review State to `blocked`.
- [ ] Container-only differences create review work without necessarily blocking.
- [ ] `clear` means no known actionable manual work remains, not full understanding.
- [ ] CDP tests pass.
- [ ] `cmd /c src\precommit.bat` passes.

## Blocked by

- 0001-001 Manual Action Log Projection
- 0001-003 Manual Seeds In Analysis
