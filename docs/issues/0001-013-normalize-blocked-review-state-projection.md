# 0001-013 Normalize Blocked Review State Projection

## Parent

PRD 0001: Manual Review Workflow

## What to build

Make Review State calculation consistent at the manual projection, project payload, listing, rendering, and export levels. Any live hard-blocking Manual Review Item should produce `blocked` wherever Review State is exposed, not only after a later project-level combination step.

This keeps direct manual-state consumers and project UI consumers from disagreeing about the same target.

## Acceptance criteria

- [ ] Manual projection returns `blocked` when any live hard-blocking Manual Review Item exists.
- [ ] Manual projection returns `needs_review` when open non-blocking Manual Review Items exist and no live blockers exist.
- [ ] Manual projection returns `clear` only when no open review work remains.
- [ ] Project listing, detail, rendering, and export warnings agree with manual projection Review State.
- [ ] Tests cover direct manual-state payloads and project-level payloads for `clear`, `needs_review`, and `blocked`.
- [ ] CDP tests pass.
- [ ] `cmd /c src\precommit.bat` passes.

## Blocked by

- 0001-010 Keep Live Blockers Blocked

