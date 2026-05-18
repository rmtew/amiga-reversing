Status: Complete
Source proposal: docs/proposals/010-agentic-reversing-loop.md

## Scope

Make autonomous `run-one` action selection evidence-backed instead of selecting
the first row that happens to support `comment.edit`.

The loop should choose from repo-derived reversing candidates and mutate only
when the selected candidate includes enough evidence, a rationale, a stable
locator or durable identity, an allowed action, and a verifier.

Initial candidate sources should be conservative and cheap:

- current Manual Review Items,
- source entrypoint/startup rows,
- xref-rich labels or rows,
- API call rows,
- unresolved typed gaps,
- reproduction/manual review blockers when present.

Each candidate should expose:

```text
candidate_id
kind
locator or durable identity
evidence summary
xref summary when relevant
current metadata/comment state
suggested action kind
default verifier
confidence
rationale
stop reason if not actionable
```

`run-one` should mutate only high-confidence actionable candidates. If no
evidence-backed candidate exists, it should stop with a report rather than
creating a generic comment.

## Out of scope

- Fully automatic multi-iteration loops.
- Large semantic naming/classification changes.
- New private agent-only mutation paths.
- Browser/DOM scraping.
- User-provided explicit locators as the primary autonomy model.

## Files likely touched

- `amiga_reversing/reversing_loop.py`
- `tests/test_reversing_loop.py`
- `tests/test_agent_reversing_loop.py`
- `docs/agents/reversing-loop.md`
- `docs/proposals/010-agentic-reversing-loop.md`

## Acceptance criteria

- [x] Listing-backed comment mode no longer uses "first row with
      `comment.edit`" as production action selection.
- [x] Candidate discovery includes at least entrypoint/startup or another
      repo-derived evidence source beyond Manual Review Items.
- [x] Candidate reports include locator/durable identity, evidence, confidence,
      rationale, suggested action, and verifier.
- [x] `run-one` mutates only actionable candidates with high confidence and a
      verifier.
- [x] No-candidate state produces a stop recommendation and report.
- [x] Reports include the selected candidate rationale and checked evidence.
- [x] Arbitrary row selection remains only in tests or explicit test fixtures.
- [x] Agent playbook documents that autonomous changes require evidence-backed
      candidates, not mechanical command availability.

## Required tests

- [x] Focused candidate discovery test for entrypoint/startup or equivalent
      evidence-backed source.
- [x] Focused test that first-commentable-row fallback is not used for
      production mutation.
- [x] Focused high-confidence candidate mutation test.
- [x] Focused no-candidate stop/report test.
- [x] Focused report shape test for rationale/evidence/verifier.
- [x] Agent smoke uses evidence-backed candidate selection.

## Blocked by

- `010-010-listing-backed-comment-iteration.md`

## Cleanup / deletion

- Do not create a new proposal.
- Promote durable action-selection rules into Proposal 010 and
  `docs/agents/reversing-loop.md`.
- Delete or mark this issue complete only after focused verification passes.

## Notes for agents

The purpose of the loop is autonomous reversing progress: the agent should use
domain knowledge channelled through repo-visible analysis facts, xrefs, listing
locators, command metadata, and verification reports. Mechanical command
availability is not enough evidence for a mutation. A generic comment on the
first mutable row is useful for smoke tests only, not real reversing.

## Completion

Implemented source-entrypoint-backed autonomous comment selection. Verification
passed:

```text
uv run python -m pytest tests\test_reversing_loop.py tests\test_agent_reversing_loop.py -q
  28 passed

uv run python -m pytest tests\test_api_workflow_harness.py tests\test_disasm_server.py -q
  136 passed

uv run ruff check amiga_reversing\reversing_loop.py tests\test_reversing_loop.py tests\test_agent_reversing_loop.py
  All checks passed

cmd /c src\precommit.bat
  passed
```
