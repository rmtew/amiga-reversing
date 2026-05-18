Status: Open
Source proposal: docs/proposals/010-agentic-reversing-loop.md

## Scope

Add support for profile-backed next-step recommendations. The harness should be
able to recommend `continue`, `verify`, `refactor`, or `stop` based on
iteration results, workflow profile spans, missing API/state contracts, and
verification failures.

## Out of scope

- Performing the refactor automatically.
- Building a general planner.
- Adding timing thresholds as hard gates.

## Files likely touched

- `amiga_reversing/reversing_loop.py` or equivalent
- `tests/test_reversing_loop.py`
- Possibly `docs/agents/reversing-loop.md`

## Acceptance criteria

- [ ] Iteration report summarizes relevant workflow profile spans.
- [ ] Harness can recommend `continue` when verification passes and no blocker is present.
- [ ] Harness can recommend `verify` when additional proof is required.
- [ ] Harness can recommend `refactor` only with a named span, missing API/state contract, or blocking duplication.
- [ ] Harness can recommend `stop` on unknown verification failure, unknown target files, unavailable oracle/tool, or missing domain judgment.
- [ ] Playbook documents how Codex should respond to each recommendation.

## Required tests

- [ ] Focused continue recommendation test.
- [ ] Focused refactor recommendation requires evidence test.
- [ ] Focused stop recommendation test.
- [ ] Focused profile summary shape test.

## Blocked by

- `010-007-verification-and-durability-contract.md`

## Cleanup / deletion

- Avoid wall-clock timing gates.
- Avoid speculative cleanup recommendations without evidence.

## Notes for agents

This slice controls when "improve the supporting code as it goes" is allowed.
The answer must come from evidence, not preference.
