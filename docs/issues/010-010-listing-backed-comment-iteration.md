Status: Complete
Source proposal: docs/proposals/010-agentic-reversing-loop.md

## Scope

Make the existing Proposal 010 harness capable of one real listing-backed
comment iteration without hand-rolled agent scripting.

The harness should acquire a real `ListingRowLocator` in the same Python/server
process that executes the command:

1. run target hygiene,
2. open/build the listing artifact,
3. wait until listing is ready,
4. fetch a real row locator,
5. confirm `comment.edit` command availability,
6. execute `comment.edit` through `/commands/execute`,
7. verify Manual Action Log count/head hash,
8. verify semantic reload,
9. verify projected `comment_text` at the affected locator,
10. write an iteration report that reflects the actual action.

## Out of scope

- Autonomous multi-iteration reversing.
- Naming, seed, or classification actions.
- Browser/CDP behavior unless a server-only path is insufficient.
- Committing target-local Manual Action Log state.
- Treating `.project.json` timestamp-only changes as meaningful progress.

## Files likely touched

- `amiga_reversing/reversing_loop.py`
- `tests/test_reversing_loop.py`
- `tests/test_agent_reversing_loop.py`
- `docs/agents/reversing-loop.md`
- `docs/proposals/010-agentic-reversing-loop.md`

## Acceptance criteria

- [x] Harness has a command or mode that performs listing open/wait/locator
      acquisition and `comment.edit` in one process.
- [x] The flow does not rely on `reversing_loop inspect` review-item candidates
      for arbitrary comment opportunities.
- [x] Command availability is checked before execution.
- [x] Mutation executes through the existing command/manual-action route.
- [x] Report records selected locator, command, durable result, verification
      layers, workflow profile, and next recommendation.
- [x] Verification checks projected `comment_text` at the affected locator after
      reload/projection.
- [x] Partial or failed listing readiness names the failing layer and stops.
- [x] No tracked timestamp-only target changes are committed.

## Required tests

- [x] Focused test for listing-backed locator acquisition.
- [x] Focused test for command availability before execution.
- [x] Focused test that projected `comment_text` is verified.
- [x] Focused failure-layer test for listing readiness failure.
- [x] End-to-end smoke using the harness path without DOM scraping or private
      state patching.

## Blocked by

None. This is a follow-up hardening issue for Proposal 010.

## Cleanup / deletion

- Do not create a new proposal.
- Promote durable lessons or changed operating rules into Proposal 010 and
  `docs/agents/reversing-loop.md`.
- Delete or mark this issue complete only after focused verification passes.

## Notes for agents

The previous real `amiga_hunk_genam` attempt showed that listing artifacts are
process-local. A fresh CLI `inspect` process cannot see row locators unless it
opens and waits for the listing artifact in that same process. The implementation
should encode that workflow in the harness so future goals do not need to
hand-roll it.

## Completion

Implemented in `run-one --listing-backed-comment`. Verification passed:

```text
uv run python -m pytest tests\test_reversing_loop.py tests\test_agent_reversing_loop.py -q
  25 passed

uv run python -m pytest tests\test_api_workflow_harness.py tests\test_disasm_server.py -q
  136 passed

uv run ruff check amiga_reversing\reversing_loop.py tests\test_reversing_loop.py tests\test_agent_reversing_loop.py
  All checks passed

cmd /c src\precommit.bat
  passed
```
