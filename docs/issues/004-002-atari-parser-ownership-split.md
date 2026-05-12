# Atari Parser Ownership Split

Type: AFK

## Parent

[004 Parser Workflow and Result Split](../prd/004-parser-workflow-result-split.md)

## Candidate files

- `src/platform_atari_st.c`
- Atari/container tests
- `docs/c-arena-allocation-inventory.md`

## What to build

Split Atari parser allocation ownership so transient parse state uses a **Workflow Arena** and returned parsed object internals use a **Result Arena**.

## Acceptance criteria

- [x] Temporary Atari parse state does not escape the Workflow Arena.
- [x] Returned Atari parser results own durable internals through a Result Arena.
- [x] Binary/container semantics remain unchanged.
- [x] Before/after notes report raw heap allocation site count changes in touched Atari parser code.
- [x] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [x] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Work notes

- Audited `src/platform_atari_st.c`: `atari_st_read_buffer` has no parser-local raw heap
  allocation sites to migrate.
- Returned parser results already copy durable data into the `M68kObject` Result Arena:
  sections through `m68k_object_add_section`, platform metadata through `m68k_object_alloc`,
  and symbol/relocation streams through object-arena storage.
- No Workflow Arena was added because there is no Atari parser temporary heap state to own.
- Raw heap allocation sites in Atari parser code: 0 before, 0 after. Existing direct heap sites in
  `src/platform_atari_st.c` are writer payload/output and external file-read boundaries.
- Arena stats: not applicable; no Atari parser workflow arena exists.
- `cmd /c src\precommit.bat`: passed. Summary: style OK, dead_code OK, unit OK, integration OK, explicit OK.
- `uv run python -m pytest tests\test_web_e2e_cdp.py -q`: first run hit a transient
  `facts_v2 render preview build failed`; isolated rerun passed. First full rerun hit a transient
  `Inspected target navigated or closed`; isolated rerun passed. Final full rerun passed with
  `29 passed in 61.39s`.

## Blocked by

- [001-002 Typed Arena Builder Helpers](001-002-typed-arena-builder-helpers.md)
- [001-003 Builder Stats and Scratch Contract](001-003-builder-stats-and-scratch-contract.md)
