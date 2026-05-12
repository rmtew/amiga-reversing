# Atari Disk Parser Ownership Split

Type: AFK

## Parent

[004 Parser Workflow and Result Split](../prd/004-parser-workflow-result-split.md)

## Candidate files

- `src/platform_atari_st_disk.c`
- `docs/c-arena-allocation-inventory.md`

## What to build

Split Atari disk parser allocation ownership so transient directory, cluster, and image parse state uses a **Workflow Arena** and returned disk analysis internals use a **Result Arena**.

## Acceptance criteria

- [ ] Temporary Atari disk parse state does not escape the Workflow Arena.
- [ ] Returned disk analysis results own durable internals through a Result Arena.
- [ ] Existing disk import behavior remains unchanged.
- [ ] Before/after notes report raw heap allocation site count changes in touched Atari disk parser code.
- [ ] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [ ] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Blocked by

- [001-002 Typed Arena Builder Helpers](001-002-typed-arena-builder-helpers.md)
- [001-003 Builder Stats and Scratch Contract](001-003-builder-stats-and-scratch-contract.md)
