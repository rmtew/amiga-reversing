# Virtual Reserved Arena Prototype

Type: AFK

## Parent

[005 Advanced Arena Forms Research](../prd/005-advanced-arena-forms-research.md)

## Candidate files

- prototype-only files under `src/` or `tests/`
- `docs/adr/`
- `docs/c-arena-allocation-inventory.md`

## What to build

Prototype a virtual-reserved contiguous arena outside the production allocation path and compare its lifetime model, API impact, and failure modes against the current linked-block arena.

## Acceptance criteria

- [x] Prototype is isolated from production behavior unless explicitly enabled for measurement.
- [x] Prototype does not change default workflow allocation behavior or public APIs.
- [x] Fit analysis covers locality, reservation limits, platform assumptions, and rollback cost.
- [x] Measurements compare prototype behavior against the current arena baseline.
- [x] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [x] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Work Notes

- Prototype: `src/test_util_arena.c` adds a test-only `TestVirtualReservedArena` backed by Windows
  `VirtualAlloc`/`VirtualFree`; no production allocator or public API changed.
- Raw heap allocation sites: production touched modules before/after 0 -> 0. The prototype adds no
  `malloc`/`calloc`/`realloc`/`free` sites and no production raw heap sites.
- Arena stats/baseline: current linked-block matched sequence from `docs/arena-measurement-report.md`
  is 5032 used bytes, 9096 capacity bytes, 4064 wasted bytes, and 2 blocks.
- Virtual prototype stats: same sequence uses 5032 bytes, reserves 65536 bytes, commits pages on
  demand, and keeps committed pages across reset for reuse.
- Fit analysis and recommendation: `docs/arena-virtual-reserved-prototype.md`.
- Precommit: final `cmd /c src\precommit.bat` passed; style OK 19 tests, dead_code OK,
  unit OK 129 tests, integration OK 88 tests, explicit OK 41 tests.
- CDP: first full `uv run python -m pytest tests\test_web_e2e_cdp.py -q` run had the known
  transient timeout in `test_brave_cdp_disk_project_browsing_and_target_listing` after 28 passed.
  Isolated rerun of that test passed in 11.83s. Full rerun passed: 29 passed in 76.09s.

## Blocked by

- [005-001 Arena Measurement Report](005-001-arena-measurement-report.md)
