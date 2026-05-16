# 018-003: Reproduction Profile Summary UI

## Parent

[PRD 018: Reproduction Profiles and Policy Summary](../prd/018-reproduction-profiles-and-policy-summary.md)

## Type

AFK

## Labels

done

## What to build

Show the active reproduction profile and concrete policy summary in the Web UI reproduction panel.

## Acceptance criteria

- [x] UI shows profile id/name, mode, assembler, backend, CPU, comparison level, and requested oracles.
- [x] Stale reproduction state is visible after policy changes.
- [x] Oracle profile selection is visually distinct from the exactness gate result.
- [x] Missing or invalid policy is shown with a clear reason.
- [x] Web tests cover summary display and stale state.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Completion Notes

- The reproduction panel now renders a policy summary from `policy_summary` or stamped report input data.
- CDP coverage verifies profile selection updates the panel summary and stale state.

## Blocked by

- [018-002: Reproduction Policy Persistence and Validation](018-002-reproduction-policy-persistence-and-validation.md)
