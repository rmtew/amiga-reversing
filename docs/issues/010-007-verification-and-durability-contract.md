Status: Open
Source proposal: docs/proposals/010-agentic-reversing-loop.md

## Scope

Attach verification contracts to reversing loop iteration reports. After a
manual mutation, the harness should prove durable state and projected state
after reload. Output-affecting actions should require the relevant round-trip or
focused verification.

## Out of scope

- Adding new action kinds beyond what `010-006` supports unless needed for tests.
- Full precommit automation for every iteration.
- Browser/CDP smoke unless browser debug behavior changes.

## Files likely touched

- `amiga_reversing/reversing_loop.py` or equivalent
- `tests/workflow_harness.py` if reusable assertions need a small extension
- `tests/test_reversing_loop.py`
- `tests/test_api_workflow_harness.py` if shared helpers change

## Acceptance criteria

- [ ] Iteration report records which verification layers ran.
- [ ] Manual mutation report proves semantic state after reload.
- [ ] Projection check verifies expected locator/effective metadata.
- [ ] Durability boundary failures name the failing layer.
- [ ] Output-affecting action classes are blocked unless a round-trip/focused verifier is configured.
- [ ] Verification failure produces a stop recommendation.

## Required tests

- [ ] Focused semantic reload verification test.
- [ ] Focused projection verification test.
- [ ] Focused failure-layer naming test.
- [ ] Focused output-affecting action requires verifier test.

## Blocked by

- `010-006-one-manual-mutation-iteration.md`

## Cleanup / deletion

- Do not accept first-visible UI state as verification.
- Do not hide verification failures behind retry/sleep behavior.

## Notes for agents

This slice makes the loop trustworthy. A successful action is not done until
durable state and reconstructed state are proven.
