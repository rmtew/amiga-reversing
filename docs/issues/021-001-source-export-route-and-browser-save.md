# 021-001: Source Export Route and Browser Save

## Parent

[PRD 021: Source Export Workflow](../prd/021-source-export-workflow.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Add a source export route that returns a browser-saveable `.s` file.

## Acceptance criteria

- [ ] Route renders source for the selected target and assembler profile.
- [ ] Response uses a sensible `.s` filename.
- [ ] Browser save flow writes user-owned external output, not a project artifact.
- [ ] Export can run without a reproduction/oracle run.
- [ ] Route tests cover success and render refusal.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- None

