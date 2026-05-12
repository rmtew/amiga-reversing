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

- [ ] Report includes representative workflow measurements.
- [ ] Report separates benchmark noise from allocation counts and arena stats.
- [ ] Report identifies whether linked-block arena behavior is a proven bottleneck or only a cleanup opportunity.
- [ ] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [ ] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Blocked by

None - can start immediately.
