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
- `uv run python -m amiga_reversing.reversing_loop run-one --target <target> --listing-backed-label-rename --label-offset <offset> --label-name <name>`

## Mode Choice

1. Run hygiene in `inspect` mode before any mutation.
2. Use `continue` only when durable manual state is trusted and no unknown
   target files block mutation.
3. Use `clean-run` when stale generated, obsolete UI, or local manual state
   should be reset while preserving source/import facts.
4. Use `reimport` only when the target import path should rebuild target-local
   state from source/import facts.

## Candidate Choice

1. Select work that moves rendered source closer to human-quality reconstructed
   source, not work that merely proves the loop can mutate.
2. Inspect current target state, review items, round-trip state, listing
   navigation, analysis facts, and candidates.
3. Check xrefs before naming, seeding, or classification decisions.
4. Prefer high-confidence candidates with a locator or durable domain id.
5. Prefer durable command/manual-action paths over direct file edits.
6. Autonomous mutation requires repo-visible evidence, rationale, suggested
   action, and verifier; command availability alone is not enough.
7. Reject row index, row text, DOM text, and screenshots as durable identity.
8. Treat inferred data type/class as a safe surface for action, not as enough
   evidence that a manual rename is worthwhile.
9. Generic class-prefix renames such as `string_XXXXXXXX` or
   `table_XXXXXXXX` are framework/analyzer naming policy unless target context
   supports a semantic name.
10. Generic `run-one` records planner state: ranked candidates, selected command,
   and skipped-candidate reasons. Treat an already-satisfied skip as evidence
   to move to the next candidate, not as progress.

## Source-Converging Work

Useful target-progress actions improve the rendered source in ways a human
reverser would recognize:

- name functions, labels, globals, and referenced data from xrefs and behavior;
- add, edit, or rename app/base-relative slots when the command catalog exposes
  durable app-slot actions;
- add, edit, or rename equates for domain constants when equate commands are
  supported;
- change immediate value representations when an operand-level representation
  command is supported and the new form carries domain meaning;
- classify code, raw data, strings, scalar tables, pointer tables, structured
  data, and broader representations;
- record API/library call semantics and propagate them through callers,
  arguments, return values, and stored state;
- add type, structure, field, or register-base facts when evidence supports
  them;
- resolve review items only with the type-specific verifier.

For data naming, prefer semantic names derived from program context, xrefs,
contents, and call behavior, such as `credit_text`, `key_prompt_text`, or
`title_screen_palette`. Do not spend target-iteration budget on mechanical
restyling from class and address alone, such as renaming an anonymous string row
to `string_0002109E`; implement that as general analysis/rendering policy, or
log it as framework work, unless the current target action is to fix that
general policy.

Use `docs/proposals/014-source-converging-manual-action-surface.md` as the
capability map. If the best source-converging action is not in the matrix, or
the matrix says identity/command/verifier support is missing, report that as
the blocker instead of using a script or direct target metadata edit.

Comments are allowed only for concrete semantic discoveries that cannot be
represented by a more structured command. Do not create entrypoint, placeholder,
proof, fallback, or "note that this exists" comments as autonomous progress.
Every selected action must state the evidence used, the expected rendered-source
improvement, the command/manual action used, and the verifier.

If the ideal source-converging action is not available in the command catalog,
do not write a temporary script or mutate target metadata directly. Stop with a
precise missing-capability report, then add or complete the command support
issue before trying the target action again.

## Allowed Mutations

- Use command discovery before command execution.
- Use `ListingRowLocator` or a durable review item id for row/review work.
- Append through the Manual Action Log command path.
- Undo by appending a corrective action, or by explicit `clean-run`/`reimport`.
- Do not write retired target UI state or delete manual history as rollback.
- Do not treat a `.project.json` timestamp-only change as meaningful progress;
  Manual Action Log state is local/ignored and must be summarized in reports.

## Listing Workflow

Use one Python/server process for listing access and command execution. Listing
locators are available only after the listing artifact is opened, and that
artifact is process-local.

1. Run hygiene.
2. Open the listing with `POST /api/projects/<target>/listing/open`.
3. Wait for listing status to become ready in the same process.
4. Fetch real row locators, navigation groups, and command catalogs from the
   opened listing.
5. Choose the highest-value source-converging action with evidence and a
   verifier.
6. Execute only through `/commands/execute`.
7. Verify Manual Action Log count/head hash, semantic reload, projected state,
   `workflow_profile`, and source/rendering checks appropriate to the action.
8. Stop if listing readiness, candidate evidence, command availability, or
   action-specific verification fails.

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
