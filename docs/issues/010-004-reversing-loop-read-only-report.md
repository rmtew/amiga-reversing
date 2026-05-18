Status: Open
Source proposal: docs/proposals/010-agentic-reversing-loop.md

## Scope

Add a read-only reversing loop report that inspects a target and emits current
state plus actionable candidate work without mutating project state.

The report should combine the target hygiene result, current projection/manual
state, round-trip status where available, unresolved work candidates, available
verification paths, and profile summaries.

## Out of scope

- Executing mutations.
- Cleaning target files.
- Browser/CDP operation.
- Long-running autonomous loops.

## Files likely touched

- `amiga_reversing/reversing_loop.py` or equivalent
- `amiga_reversing/reversing_workspace.py` or equivalent from `010-002`
- `tests/test_reversing_loop.py`
- Optional CLI entrypoint.

## Acceptance criteria

- [ ] Read-only report includes target id and hygiene status.
- [ ] Read-only report is available through a stable CLI command.
- [ ] Report includes current projection/manual state stamps when available.
- [ ] Report lists candidate work items with locator or durable domain identity.
- [ ] Candidate work items include evidence summary, such as xref availability.
- [ ] Candidate work items include suggested action kinds.
- [ ] Report includes available verification paths.
- [ ] Report has an explicit `safe_to_mutate` or equivalent gate.

## Required tests

- [ ] Focused test for report generation without mutation.
- [ ] Focused test that candidates include locators or durable ids.
- [ ] Focused test that unsafe hygiene blocks mutation readiness.
- [ ] Focused CLI inspect command test.

## Blocked by

- `010-002-target-workspace-hygiene-report.md`
- `010-003-safe-clean-run-cleanup.md`

## Cleanup / deletion

- Avoid direct private-server-global dependencies as normal report inputs.
- Avoid row index or row text as durable candidate identity.

## Notes for agents

This is the first harness surface an LLM should inspect. It should make "what
can I safely do next?" answerable without chat-only reasoning.
