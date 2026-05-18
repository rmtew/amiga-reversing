Status: Open
Source proposal: docs/proposals/010-agentic-reversing-loop.md

## Scope

Add an end-to-end smoke that follows the playbook for one representative target
and one safe action. It should exercise hygiene inspection, read-only target
reporting, dry-run/action selection, command execution, semantic verification,
workflow profile capture, and iteration report output.

## Out of scope

- Full autonomous multi-iteration reversing.
- Broad browser UI testing unless the chosen smoke requires browser debug state.
- Full `src/precommit.bat` inside the test.

## Files likely touched

- `tests/test_agent_reversing_loop.py` or `tests/test_reversing_loop.py`
- `docs/agents/reversing-loop.md`
- `amiga_reversing/reversing_loop.py` or equivalent
- `amiga_reversing/reversing_workspace.py` or equivalent

## Acceptance criteria

- [ ] Smoke starts with target workspace hygiene.
- [ ] Smoke produces a read-only target report.
- [ ] Smoke executes one safe locator-backed command action.
- [ ] Smoke verifies semantic state after reload.
- [ ] Smoke records workflow profile spans in the iteration report.
- [ ] Smoke produces a stop/continue recommendation.
- [ ] Smoke does not scrape DOM text or patch private server globals as normal behavior.

## Required tests

- [ ] End-to-end smoke test.
- [ ] Focused tests from prerequisite slices remain passing.
- [ ] CDP smoke only if browser/debug behavior is changed.

## Blocked by

- `010-001-agent-playbook-draft.md`
- `010-002-target-workspace-hygiene-report.md`
- `010-003-safe-clean-run-cleanup.md`
- `010-004-reversing-loop-read-only-report.md`
- `010-005-run-identity-and-report-storage.md`
- `010-006-one-manual-mutation-iteration.md`
- `010-007-verification-and-durability-contract.md`
- `010-008-refactor-trigger-and-profiling-policy.md`

## Cleanup / deletion

- Delete or update any stale issue notes whose durable reasoning is promoted
  into the proposal during implementation.

## Notes for agents

This is the proof that `/goal` can drive the loop through repo mechanics rather
than only through chat instructions.
