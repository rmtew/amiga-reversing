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

- [ ] Prototype is isolated from production behavior unless explicitly enabled for measurement.
- [ ] Prototype does not change default workflow allocation behavior or public APIs.
- [ ] Fit analysis covers object lifetime, reset behavior, fragmentation, and API complexity.
- [ ] Measurements identify whether fixed-size reuse beats plain arena allocation for any representative workflow.
- [ ] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [ ] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Blocked by

- [005-001 Arena Measurement Report](005-001-arena-measurement-report.md)
