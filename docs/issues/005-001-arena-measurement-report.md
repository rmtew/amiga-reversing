# Arena Measurement Report

Type: AFK

## Parent

[005 Advanced Arena Forms Research](../prd/005-advanced-arena-forms-research.md)

## Candidate files

- `src/util_arena.c`
- `src/util_arena.h`
- `docs/c-arena-allocation-inventory.md`
- benchmark or profiling tooling under `scripts/` and `tests/`

## What to build

Produce a measurement report for current arena behavior across representative workflows, including block counts, allocated bytes, wasted bytes, and hot allocation sites.

## Acceptance criteria

- [x] Report includes representative workflow measurements.
- [x] Report separates benchmark noise from allocation counts and arena stats.
- [x] Report identifies whether linked-block arena behavior is a proven bottleneck or only a cleanup opportunity.
- [x] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [x] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Work notes

- Added `docs/arena-measurement-report.md`.
- Extended `ArenaStats` with `current_capacity` and `peak_capacity` so wasted bytes can be measured
  as `capacity - used`.
- Added arena stats assertions for small mark/rewind, large transient block rewind, reset, null
  stats, and overflow rejection cases.
- Raw heap allocation sites: no new raw heap sites in production; stats fields only.
- Arena stats recorded in report:
  - Small mark/rewind peak: 40 used / 4096 capacity / 4056 wasted / 1 block.
  - Large transient peak: 5032 used / 9096 capacity / 4064 wasted / 2 blocks.
  - Large transient after rewind: 32 used / 4096 capacity / 4064 wasted / 1 current block, 2 total.
- `cmd /c src\precommit.bat`: passed. Summary: style OK, dead_code OK, unit OK, integration OK, explicit OK.
- `uv run python -m pytest tests\test_web_e2e_cdp.py -q`: first run hit a transient
  `facts_v2 render preview build failed`; isolated rerun passed, then full rerun passed with
  `29 passed in 70.05s`.

## Blocked by

None - can start immediately.
