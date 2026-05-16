# 021-001: Source Export Route and Browser Save

## Parent

[PRD 021: Source Export Workflow](../prd/021-source-export-workflow.md)

## Type

AFK

## Labels

done

## What to build

Add a source export route that returns a browser-saveable `.s` file.

## Acceptance criteria

- [x] Route renders source for the selected target and assembler profile.
- [x] Response uses a sensible `.s` filename.
- [x] Browser save flow writes user-owned external output, not a project artifact.
- [x] Export can run without a reproduction/oracle run.
- [x] Route tests cover success and render refusal.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- None
