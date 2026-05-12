# Introduce facts Workflow Arena

Type: AFK

## Parent

[C Arena Ownership Refactor PRD](../prd/c-arena-ownership-refactor.md)

## What to build

Introduce explicit **Workflow Arena** ownership for the facts/source-rendering workflow, including **Scratch Marks** for pass-local temporary arrays. The workflow should keep structured diagnostics and failure stages while reducing repeated cleanup paths.

## Acceptance criteria

- [ ] Facts/source-rendering workflow has one explicit workflow-owned state.
- [ ] Pass-local temporary allocations use **Scratch Marks** where appropriate.
- [ ] Result objects and caller-freed outputs do not point into the **Workflow Arena**.
- [ ] Failure diagnostics still report the relevant stage.
- [ ] Existing facts, render, and round-trip tests pass.

## Blocked by

- [0002-add-arena-stats-and-tests.md](0002-add-arena-stats-and-tests.md)
