# Platform Disk Container Parser Ownership Split

Type: AFK

## Parent

[004 Parser Workflow and Result Split](../prd/004-parser-workflow-result-split.md)

## Candidate files

- `src/platform_disk_lib.c`
- `src/platform_amiga_disk.c`
- `docs/c-arena-allocation-inventory.md`

## What to build

Split platform disk/container parser allocation ownership so transient payload, image, and container parse state uses a **Workflow Arena** and returned parsed object internals use a **Result Arena**.

## Acceptance criteria

- [x] Temporary platform disk/container parse state does not escape the Workflow Arena.
- [x] Returned platform disk/container parser results own durable internals through a Result Arena.
- [x] Existing import and reproduction behavior remains unchanged.
- [x] Before/after notes report raw heap allocation site count changes in touched disk/container parser code.
- [x] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [x] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Work notes

- `src/platform_disk_lib.c` now uses a local Workflow Arena for disk path image buffers in
  inspect/extract-entry workflows.
- Amiga disk entry content classification payloads now allocate from the same Workflow Arena with a
  Scratch Mark rewind per entry. Public extracted entry bytes remain caller-freed output buffers.
- Returned disk/container analysis internals remain Result Arena owned by `AmigaDiskAnalysis` and
  `AtariStDiskAnalysis`; `src/platform_amiga_disk.c` already uses `AmigaDiskAnalysis.arena`.
- Raw heap allocation sites:
  - `src/platform_disk_lib.c` workflow-classified sites: 8 before, 0 after.
  - `src/platform_disk_lib.c` external read-buffer heap sites for disk path image reads: 2 before, 0 after.
  - Remaining direct heap sites are caller-freed text/byte output boundaries.
- Arena stats: the platform disk workflow arena does not expose stats.
- `cmd /c src\precommit.bat`: passed. Summary: style OK, dead_code OK, unit OK, integration OK, explicit OK.
- `uv run python -m pytest tests\test_web_e2e_cdp.py -q`: first run hit a transient
  `facts_v2 render preview build failed`; isolated rerun passed, then full rerun passed with
  `29 passed in 70.64s`.

## Blocked by

- [001-002 Typed Arena Builder Helpers](001-002-typed-arena-builder-helpers.md)
- [001-003 Builder Stats and Scratch Contract](001-003-builder-stats-and-scratch-contract.md)
