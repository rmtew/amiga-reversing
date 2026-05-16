# 018-001: Built-In Reproduction Profile Registry

## Parent

[PRD 018: Reproduction Profiles and Policy Summary](../prd/018-reproduction-profiles-and-policy-summary.md)

## Type

AFK

## Labels

done

## What to build

Add built-in **Reproduction Profile** definitions for exact framework, vasm source oracle, GenAm/DevPac-compatible source oracle, and content-semantic comparison.

## Acceptance criteria

- [x] Built-in profile ids are stable and documented.
- [x] Each profile expands to concrete reproduction options.
- [x] Oracle profiles do not select an external assembler as the exactness gate.
- [x] Tests cover every built-in profile expansion.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Completion Notes

- Built-in profile ids are `exact-framework`, `source-vasm`, `source-devpac`, and `content-semantic`.
- Oracle profiles request `oracle_modes` while keeping `assembler` on `our`.

## Blocked by

- None
