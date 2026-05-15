# 018-001: Built-In Reproduction Profile Registry

## Parent

[PRD 018: Reproduction Profiles and Policy Summary](../prd/018-reproduction-profiles-and-policy-summary.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Add built-in **Reproduction Profile** definitions for exact framework, vasm source oracle, GenAm/DevPac-compatible source oracle, and content-semantic comparison.

## Acceptance criteria

- [ ] Built-in profile ids are stable and documented.
- [ ] Each profile expands to concrete reproduction options.
- [ ] Oracle profiles do not select an external assembler as the exactness gate.
- [ ] Tests cover every built-in profile expansion.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- None

