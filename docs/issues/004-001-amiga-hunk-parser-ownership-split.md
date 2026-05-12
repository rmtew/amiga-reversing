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

- [x] Temporary parse strings, payload staging, and list-building state do not escape the Workflow Arena.
- [x] Returned HUNK parser results own durable internals through a Result Arena.
- [x] Container and reproduction behavior remains unchanged.
- [x] Before/after notes report raw heap allocation site count changes in touched HUNK parser code.
- [x] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [x] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Work notes

- `src/platform_amiga_hunk.c` now creates one local Workflow Arena per `amiga_hunk_read_buffer`.
- BSTR names, HUNK_EXT names, HUNK_DEBUG staging data, section payload staging data, and executable
  header tables allocate from the Workflow Arena.
- Durable results still copy into the `M68kObject` Result Arena through `m68k_object_add_section`,
  `m68k_object_add_symbol`, `m68k_object_set_section_debug_data`, and `m68k_object_memdup`.
- Fixed `AmigaHunkPlatformData.unit_name` to copy into the object Result Arena instead of retaining
  parser-local storage.
- Raw heap allocation sites in HUNK parser code: 45 before, 0 after. Remaining direct heap sites in
  `src/platform_amiga_hunk.c` are file-read and writer-output boundaries: 6.
- Arena stats: the HUNK parse workflow does not expose stats.
- `cmd /c src\precommit.bat`: passed. Summary: style OK, dead_code OK, unit OK, integration OK, explicit OK.
- `uv run python -m pytest tests\test_web_e2e_cdp.py -q`: first run hit a transient browser
  `net::ERR_INSUFFICIENT_RESOURCES`; isolated rerun of the failed test passed, then full rerun passed
  with `29 passed in 64.53s`.

## Blocked by

- [001-002 Typed Arena Builder Helpers](001-002-typed-arena-builder-helpers.md)
- [001-003 Builder Stats and Scratch Contract](001-003-builder-stats-and-scratch-contract.md)
