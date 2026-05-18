# Reversing Loop Agent Playbook

Use the reversing loop as an operator of normal project workflows, not as a
private mutation path.

## Entry Commands

- `uv run python -m amiga_reversing.reversing_loop hygiene --target <target>`
- `uv run python -m amiga_reversing.reversing_loop clean-run --target <target>`
- `uv run python -m amiga_reversing.reversing_loop inspect --target <target>`
- `uv run python -m amiga_reversing.reversing_loop run-one --target <target> --dry-run`
- `uv run python -m amiga_reversing.reversing_loop run-one --target <target>`
- `uv run python -m amiga_reversing.reversing_loop run-one --target <target> --listing-backed-comment`

## Mode Choice

1. Run hygiene in `inspect` mode before any mutation.
2. Use `continue` only when durable manual state is trusted and no unknown
   target files block mutation.
3. Use `clean-run` when stale generated, obsolete UI, or local manual state
   should be reset while preserving source/import facts.
4. Use `reimport` only when the target import path should rebuild target-local
   state from source/import facts.

## Candidate Choice

1. Inspect current target state, review items, round-trip state, and candidates.
2. Check xrefs before naming, seeding, or classification decisions.
3. Prefer high-confidence candidates with a locator or durable domain id.
4. Prefer durable command/manual-action paths over direct file edits.
5. Autonomous mutation requires repo-visible evidence, rationale, suggested
   action, and verifier; command availability alone is not enough.
6. Reject row index, row text, DOM text, and screenshots as durable identity.

## Allowed Mutations

- Use command discovery before command execution.
- Use `ListingRowLocator` or a durable review item id for row/review work.
- Append through the Manual Action Log command path.
- Undo by appending a corrective action, or by explicit `clean-run`/`reimport`.
- Do not write retired target UI state or delete manual history as rollback.
- Do not treat a `.project.json` timestamp-only change as meaningful progress;
  Manual Action Log state is local/ignored and must be summarized in reports.

## Real Listing Comment Iteration

For a real locator-backed comment iteration, use one Python/server process for
listing access and command execution. Listing locators are available only after
the listing artifact is opened, and that artifact is process-local.

1. Run hygiene.
2. Open the listing with `POST /api/projects/<target>/listing/open`.
3. Wait for listing status to become ready in the same process.
4. Fetch a real row locator from `/listing`.
5. Confirm `/commands` exposes `comment.edit` for that locator.
6. Execute only `comment.edit` through `/commands/execute`.
7. Verify Manual Action Log count/head hash, semantic reload, projected
   `comment_text`, `workflow_profile`, and `agent/` report output.
8. Do not rely on `reversing_loop inspect` alone for arbitrary comment
   opportunities; current inspect candidates come from review items.
9. Prefer `run-one --target <target> --listing-backed-comment --comment-text <text>`
   for one real evidence-backed comment. The harness must select a
   high-confidence candidate from listing/project evidence, such as a source
   entrypoint row, and must stop with a report when no such candidate exists.
10. Stop if listing readiness, candidate evidence, command availability, or
    projected comment verification fails.

## Verification

- Comment or naming action: reload semantic state and verify projected metadata
  at the affected locator.
- Data/code classification: regenerate affected analysis/projection and run the
  focused round-trip check.
- Source rendering or backend change: run focused unit tests and affected
  round-trip verification.
- Performance refactor: compare named `workflow_profile` spans and rerun the
  original reversing iteration.

## Refactor Triggers

Refactor support code only when the report names:

- a repeated high-cost workflow span,
- a missing API or state contract needed for the next action,
- a verification failure caused by an absent contract,
- a manual workaround that would violate project conventions, or
- duplication blocking the current reversing action.

Do not refactor for style preference, speculative cleanup, compatibility shims,
private agent-only paths, or unrelated code churn.

## Stop Conditions

Stop and ask the user when:

- hygiene finds unknown target-local files,
- verification fails without a clear diagnosed layer,
- a required oracle or tool is unavailable,
- the next action needs domain judgment,
- a partial run cannot be safely resumed,
- support-code refactor is required before reversing can continue, or
- the configured budget is exhausted.

Summaries should cite the latest iteration report, verification layers, profile
spans, and next recommendation.

## Recommendations

- `continue`: proceed to the next high-confidence candidate.
- `verify`: run the named additional proof before another mutation.
- `refactor`: change support code only for the named span/API/state/duplication
  trigger, then rerun the original iteration.
- `stop`: report the named blocker and wait for user input or tool recovery.
