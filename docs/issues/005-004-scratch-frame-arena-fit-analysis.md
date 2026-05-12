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

- [ ] Analysis covers per-thread scratch lifetime risks and conflict-avoidance requirements.
- [ ] Analysis covers frame/double-buffer applicability to repeated project workflows.
- [ ] Recommendation states whether either form should advance to implementation work.
- [ ] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [ ] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Blocked by

- [005-001 Arena Measurement Report](005-001-arena-measurement-report.md)
