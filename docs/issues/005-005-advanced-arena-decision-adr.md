# Advanced Arena Decision ADR

Type: HITL

## Parent

[005 Advanced Arena Forms Research](../prd/005-advanced-arena-forms-research.md)

## Candidate files

- `docs/adr/`
- [005 Advanced Arena Forms Research](../prd/005-advanced-arena-forms-research.md)
- issues `005-001` through `005-004`

## What to build

Write the decision record for advanced arena forms: either select a production migration path with tradeoffs and rollback cost, or record a no-build decision.

## Acceptance criteria

- [x] ADR cites the measurement report and fit analyses.
- [x] Decision clearly states whether any advanced arena form moves to implementation.
- [x] If implementation is recommended, follow-up PRD or issue scope is identified.
- [x] If no implementation is recommended, the no-build rationale is explicit.
- [x] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [x] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Work Notes

- ADR: `docs/adr/0003-advanced-arena-forms.md`.
- PRD status updated in `docs/prd/005-advanced-arena-forms-research.md`.
- Decision: no advanced arena form moves to production implementation under PRD005; no follow-up
  implementation PRD is opened.
- Raw heap allocation sites: documentation-only issue; touched production modules before/after 0 -> 0.
- Arena stats: no workflow code touched. ADR cites the PRD005 measurement/prototype reports.
- CDP: `uv run python -m pytest tests\test_web_e2e_cdp.py -q` passed: 29 passed in 100.62s.
- Precommit: `cmd /c src\precommit.bat` passed; style OK 19 tests, dead_code OK,
  unit OK 129 tests, integration OK 88 tests, explicit OK 41 tests.

## Blocked by

- [005-002 Virtual Reserved Arena Prototype](005-002-virtual-reserved-arena-prototype.md)
- [005-003 Growable Pool Prototype](005-003-growable-pool-prototype.md)
- [005-004 Scratch and Frame Arena Fit Analysis](005-004-scratch-frame-arena-fit-analysis.md)
