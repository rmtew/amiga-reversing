# Scratch and Frame Arena Fit Analysis

Type: AFK

## Parent

[005 Advanced Arena Forms Research](../prd/005-advanced-arena-forms-research.md)

## Candidate files

- `CONTEXT.md`
- `docs/c-arena-allocation-inventory.md`
- relevant workflow code identified by the measurement report

## What to build

Analyze per-thread scratch arenas and frame/double-buffer-style arenas against project workflows, including conflict-avoidance needs and whether repeated workflows justify the added allocator shape.

## Acceptance criteria

- [x] Analysis covers per-thread scratch lifetime risks and conflict-avoidance requirements.
- [x] Analysis covers frame/double-buffer applicability to repeated project workflows.
- [x] Recommendation states whether either form should advance to implementation work.
- [x] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [x] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Work Notes

- Analysis: `docs/arena-scratch-frame-fit-analysis.md`.
- Raw heap allocation sites: documentation-only issue; touched production modules before/after 0 -> 0.
- Arena stats: no workflow code touched. Analysis references existing stats from
  `docs/arena-measurement-report.md` and prototype measurements from PRD005 issues 005-002/005-003.
- Recommendation: do not advance per-thread scratch arenas or frame/double-buffer arenas to
  production implementation without a future measured repeated-workflow bottleneck.
- CDP: `uv run python -m pytest tests\test_web_e2e_cdp.py -q` passed: 29 passed in 87.67s.
- Precommit: `cmd /c src\precommit.bat` passed; style OK 19 tests, dead_code OK,
  unit OK 129 tests, integration OK 88 tests, explicit OK 41 tests.

## Blocked by

- [005-001 Arena Measurement Report](005-001-arena-measurement-report.md)
