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

- [ ] Prototype is isolated from production behavior unless explicitly enabled for measurement.
- [ ] Prototype does not change default workflow allocation behavior or public APIs.
- [ ] Fit analysis covers locality, reservation limits, platform assumptions, and rollback cost.
- [ ] Measurements compare prototype behavior against the current arena baseline.
- [ ] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [ ] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Blocked by

- [005-001 Arena Measurement Report](005-001-arena-measurement-report.md)
