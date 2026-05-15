# 018-002: Reproduction Policy Persistence and Validation

## Parent

[PRD 018: Reproduction Profiles and Policy Summary](../prd/018-reproduction-profiles-and-policy-summary.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Persist selected **Reproduction Policy** as concrete target reproduction options with optional profile id provenance.

## Acceptance criteria

- [ ] Profile selection writes concrete options through target reproduction configuration.
- [ ] Optional profile id is retained for display/provenance.
- [ ] Invalid option values are rejected using existing typed sets in `reproduction.py`.
- [ ] Updating policy marks existing reproduction reports stale.
- [ ] Tests prove no **Manual Action Log** entry is written.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [018-001: Built-In Reproduction Profile Registry](018-001-built-in-reproduction-profile-registry.md)

