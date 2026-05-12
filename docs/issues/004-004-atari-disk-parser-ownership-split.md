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

- [x] Temporary Atari disk parse state does not escape the Workflow Arena.
- [x] Returned disk analysis results own durable internals through a Result Arena.
- [x] Existing disk import behavior remains unchanged.
- [x] Before/after notes report raw heap allocation site count changes in touched Atari disk parser code.
- [x] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [x] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Work notes

- `src/platform_atari_st_disk.c` now creates a local Workflow Arena for `atari_st_disk_analyze_buffer`
  and `atari_st_disk_analyze_image`.
- Subdirectory cluster buffers use `arena_realloc_copy` in the Workflow Arena, with Scratch Mark
  rewinds around recursive subdirectory parsing.
- Disk image reads in `atari_st_disk_analyze_image` now allocate from the same Workflow Arena.
- Returned disk analysis results continue to own paths, extents, and entries through
  `AtariStDiskAnalysis.arena`.
- Raw heap allocation sites:
  - Atari disk parser workflow sites: 7 before, 0 after.
  - Atari disk image external read-buffer heap sites: 3 before, 0 after.
  - Result arena site remains `atari_st_disk_analysis_create`.
- Arena stats: the Atari disk workflow arena does not expose stats.
- `cmd /c src\precommit.bat`: first run failed because the Arena Builder init return check was inverted;
  second run failed in the same directory-chain tests, so directory buffer growth was switched to
  `arena_realloc_copy`. Final run passed: style OK, dead_code OK, unit OK, integration OK, explicit OK.
- `uv run python -m pytest tests\test_web_e2e_cdp.py -q`: first run hit a transient
  `facts_v2 render preview build failed`; isolated rerun passed, then full rerun passed with
  `29 passed in 82.00s`.

## Blocked by

- [001-002 Typed Arena Builder Helpers](001-002-typed-arena-builder-helpers.md)
- [001-003 Builder Stats and Scratch Contract](001-003-builder-stats-and-scratch-contract.md)
