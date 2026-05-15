# 018-004: Reproduction Profile Target Tooling Commands

## Parent

[PRD 018: Reproduction Profiles and Policy Summary](../prd/018-reproduction-profiles-and-policy-summary.md)

## Related PRDs

- [PRD 008: Command Palette and Default Key Bindings](../prd/008-command-palette-and-key-bindings.md)
- [PRD 017: Inline and Palette Parameter Sessions](../prd/017-inline-and-palette-parameter-sessions.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Expose reproduction profile selection as a **Target Tooling Command** through API, CLI, and command palette surfaces.

## Acceptance criteria

- [ ] Command is categorized as target tooling, not a manual action.
- [ ] Command palette can invoke profile selection without appending the **Manual Action Log**.
- [ ] API and CLI expose list/show/set profile flows.
- [ ] Parameter collection can reuse existing parameter-session controls where practical.
- [ ] Tests cover command execution and persistence semantics.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [018-002: Reproduction Policy Persistence and Validation](018-002-reproduction-policy-persistence-and-validation.md)

