# Amiga HUNK Parser Ownership Split

Type: AFK

## Parent

[004 Parser Workflow and Result Split](../prd/004-parser-workflow-result-split.md)

## Candidate files

- `src/platform_amiga_hunk.c`
- container/reproduction tests in `src/test_m68k_container_metadata.c` and Python reproduction tests
- `docs/c-arena-allocation-inventory.md`

## What to build

Split Amiga HUNK parser allocation ownership so transient parse state uses a **Workflow Arena** and returned parsed object internals use a **Result Arena**.

## Acceptance criteria

- [ ] Temporary parse strings, payload staging, and list-building state do not escape the Workflow Arena.
- [ ] Returned HUNK parser results own durable internals through a Result Arena.
- [ ] Container and reproduction behavior remains unchanged.
- [ ] Before/after notes report raw heap allocation site count changes in touched HUNK parser code.
- [ ] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [ ] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Blocked by

- [001-002 Typed Arena Builder Helpers](001-002-typed-arena-builder-helpers.md)
- [001-003 Builder Stats and Scratch Contract](001-003-builder-stats-and-scratch-contract.md)
