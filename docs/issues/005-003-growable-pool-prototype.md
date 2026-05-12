# Growable Pool Prototype

Type: AFK

## Parent

[005 Advanced Arena Forms Research](../prd/005-advanced-arena-forms-research.md)

## Candidate files

- prototype-only files under `src/` or `tests/`
- `docs/adr/`
- `docs/c-arena-allocation-inventory.md`

## What to build

Prototype a growable pool allocator for fixed-size reusable nodes and compare it with arena allocation for workloads that repeatedly allocate similarly shaped temporary objects.

## Acceptance criteria

- [x] Prototype is isolated from production behavior unless explicitly enabled for measurement.
- [x] Prototype does not change default workflow allocation behavior or public APIs.
- [x] Fit analysis covers object lifetime, reset behavior, fragmentation, and API complexity.
- [x] Measurements identify whether fixed-size reuse beats plain arena allocation for any representative workflow.
- [x] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [x] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Work Notes

- Prototype: `src/test_util_arena.c` adds a test-only growable fixed-size pool backed by an existing
  Arena; no production allocator or public API changed.
- Raw heap allocation sites: production touched modules before/after 0 -> 0. The prototype adds no
  `malloc`/`calloc`/`realloc`/`free` sites and no production raw heap sites.
- Measurement: 16 fixed-size nodes across 3 allocation/free rounds. Plain arena allocation uses
  48 slots / 768 bytes. The growable pool allocates 16 slots / 256 bytes once and reuses slots.
- Arena stats: test asserts `plain_stats.current_used == 768` and
  `pool_stats.current_used == 256`, with 1 pool chunk, 16 allocated slots, and 16 peak live slots.
- Fit analysis and recommendation: `docs/arena-growable-pool-prototype.md`.
- Precommit: `cmd /c src\precommit.bat` passed; style OK 19 tests, dead_code OK,
  unit OK 129 tests, integration OK 88 tests, explicit OK 41 tests.
- CDP: `uv run python -m pytest tests\test_web_e2e_cdp.py -q` passed: 29 passed in 95.46s.

## Blocked by

- [005-001 Arena Measurement Report](005-001-arena-measurement-report.md)
