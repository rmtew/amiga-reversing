# 018-003: Reproduction Profile Summary UI

## Parent

[PRD 018: Reproduction Profiles and Policy Summary](../prd/018-reproduction-profiles-and-policy-summary.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Show the active reproduction profile and concrete policy summary in the Web UI reproduction panel.

## Acceptance criteria

- [ ] UI shows profile id/name, mode, assembler, backend, CPU, comparison level, and requested oracles.
- [ ] Stale reproduction state is visible after policy changes.
- [ ] Oracle profile selection is visually distinct from the exactness gate result.
- [ ] Missing or invalid policy is shown with a clear reason.
- [ ] Web tests cover summary display and stale state.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [018-002: Reproduction Policy Persistence and Validation](018-002-reproduction-policy-persistence-and-validation.md)

