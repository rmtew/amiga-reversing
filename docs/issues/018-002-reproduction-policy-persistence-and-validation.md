# 018-002: Reproduction Policy Persistence and Validation

## Parent

[PRD 018: Reproduction Profiles and Policy Summary](../prd/018-reproduction-profiles-and-policy-summary.md)

## Type

AFK

## Labels

done

## What to build

Persist selected **Reproduction Policy** as concrete target reproduction options with optional profile id provenance.

## Acceptance criteria

- [x] Profile selection writes concrete options through target reproduction configuration.
- [x] Optional profile id is retained for display/provenance.
- [x] Invalid option values are rejected using existing typed sets in `reproduction.py`.
- [x] Updating policy marks existing reproduction reports stale.
- [x] Tests prove no **Manual Action Log** entry is written.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Completion Notes

- Profile and policy updates append `reproduction_options` target UI edits, not Manual Action Log entries.
- Reproduction input stamps include both concrete options and derived policy, so existing reports become stale when policy changes.

## Blocked by

- [018-001: Built-In Reproduction Profile Registry](018-001-built-in-reproduction-profile-registry.md)
