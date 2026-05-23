# 017-052: Manual Action Log Inconsistency Triage

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: target-local manual state consistency and mutation readiness
- Blocked by: `017-051`
- Current proposal state: `017-051` found no useful 017 mutation unblocked. The
  only current default candidate is non-actionable
  `manual_action_log_inconsistency:target` with suggested action
  `repair_manual_action_log`.
- Desired proposal state after this issue: the manual-action-log inconsistency
  is classified as a real blocker, stale/report-only state, or out-of-scope
  deferred work, with a safe next issue defined only if repair is justified.

## Protocol Delta

- Adds: diagnostic classification for manual-action-log inconsistency before
  further 017 mutation work.
- Changes: 017 must not continue mutation work while the default planner reports
  an unexplained target-level manual-state inconsistency.
- Replaces: treating the planner candidate as self-explanatory.
- Deletes: none.
- Leaves out of scope: performing repair, rewriting target state, broad Pandora
  mutation runs, and changing source output.

## Default Behavior

- Do not repair `manual_actions.jsonl` in this issue unless the evidence is
  trivial, the repair is already fully supported by a command, and the proposal
  is updated before the write.
- Do not append to Decision Journal.
- Do not mutate source or generated output.
- If the inconsistency is stale/report-only and does not block safe mutation,
  record why and define the next 017 step.
- If repair is required, create a follow-up issue with exact gates instead of
  doing speculative repair here.

## Evidence Contract

The issue must identify:

- where `manual_action_log_inconsistency:target` is generated;
- what fields or sequence/hash condition make it appear;
- whether the inconsistency is in `manual_actions.jsonl`, projected manual
  state, target metadata, planner candidate generation, or a report mismatch;
- whether it affects current accepted RSSET binding, Decision Journal replay,
  verifier artifact production, exact round-trip, or future mutation gates;
- what command/API support exists for repair, if any;
- whether repair would be deterministic, scoped, and verifiable.

## Pandora Proof

Use only the focused Pandora subtarget:
`amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.

The proof must show:

- current `inspect_target(...)` or CLI equivalent still reports the
  inconsistency;
- the exact current log/projection condition that triggers it;
- whether current RSSET verifier chain still passes despite the inconsistency;
- no source, Decision Journal, Manual Action Log, or generated-output mutation
  was made by this triage issue.

## Implementation Slice

- C fact graph/query work: none expected.
- Python/API/report work: add narrow read-only diagnostics only if existing
  output cannot explain the inconsistency.
- Journal/replay work: none.
- Renderer/verifier work: none.
- Tests/proof: docs-only completion is acceptable if existing commands expose
  the needed evidence; add tests only for any new diagnostic surface.

## Research Completion Standard

Record trace blocks for generation site, current Pandora target state, manual
action log sequence/hash details, planner candidate details, verifier impact,
repair support, and the recommended next issue or deferral.

## Research Coverage

- [x] Generation site for `manual_action_log_inconsistency:target` found.
- [x] Current Pandora inspect/planner output checked.
- [x] Current `manual_actions.jsonl` sequence/hash state checked.
- [x] Projected manual state checked.
- [x] Impact on RSSET verifier chain checked.
- [x] Repair command/API support checked.
- [x] Safe repair gates or deferral criteria defined.

## Research Review

- [x] Second pass checked trace blocks against named files/functions.
- [x] Cross-references searched for existing repair or consistency helpers.
- [x] Risk of hiding real manual-state corruption reviewed.
- [x] Proposal updated with classification and next step.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Protocol delta implemented as described, or proposal updated.
- [x] Default behavior impact verified.
- [x] Old code deleted, or deferred deletion blocker recorded.
- [x] No source/journal/manual/generated-output mutation performed.
- [x] Current blocker classification recorded.
- [x] Follow-up repair issue or deferral recorded.
- [x] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

Classification: real target-local Manual Action Log sequence inconsistency,
non-corrupting for current projection, but not safe to ignore for future
mutation readiness.

Trace blocks:

- Generation site:
  `amiga_reversing/disasm/manual_actions.py` `load_manual_projection(...)`
  iterates log records in file order with `expected_sequence = 1`. The first
  action whose `sequence` differs appends
  `ReviewItemKind.MANUAL_ACTION_LOG_INCONSISTENCY` with message
  `Action <id> has sequence <actual>; expected <expected>`, then continues
  projecting later actions. `_project_actions(...)` finalizes the item into
  `review_state=needs_review`, not `blocked`, because the item is open but does
  not carry `review_blocker=true`.
- Current inspect/planner surface:
  `inspect_target(...)` reports exactly one candidate:
  `manual_action_log_inconsistency:target`, kind `manual_review_item`,
  suggested action `repair_manual_action_log`, `actionable=false`, verifier
  `null`, and stop reason `candidate lacks locator, xref evidence, or
  verifier`.
- Current log condition:
  `manual_actions.jsonl` has 60 JSONL records: one header plus 59
  `manual_action` records. Action ids are unique. The only sequence mismatch is
  file action index 59:
  `manual-6e574feccab748359c7577833fa718ba` has `sequence=60`, expected
  `59`, kind `create_manual_rsset_use_site_binding`. The previous tail is
  contiguous through sequence 58, so current evidence shows a skipped sequence
  number rather than duplicate ids or malformed JSON.
- Projected manual state:
  `load_manual_projection(...)` still includes 59 active action ids, including
  the final RSSET action. Projected `review_state` is `needs_review`; the open
  review item has `item_id=manual_action_log_inconsistency:target`,
  evidence fingerprint
  `6deb68849e099fd1d642e5c5912cfd252d4eca1a18a791202dbfafddd0aa3c82`, and
  suggested action `repair_manual_action_log`.
- RSSET/verifier impact:
  the accepted RSSET binding still projects from manual state with
  `owner_action_id=manual-6e574feccab748359c7577833fa718ba`.
  `produce_decision_verifier_artifact(..., write=False)` returns
  `status=passed`, `written=false`, and `generated_source`,
  `negative_safety`, and `exact_round_trip` all `passed`.
  `_round_trip_state(...)` returns `available=true`, `status=exact`.
  `inspect_decision_journal(...)` still reports Decision Journal and semantic
  reload layers passed and selected rendered-source effect present. Its stored
  verifier artifact was stale in this run (`verifier_artifact_stale`), but the
  no-write producer proves that is regenerable verifier state, not an impact of
  the Manual Action Log sequence mismatch.
- Repair support:
  cross-reference search found `repair_manual_action_log` only as
  `SuggestedReviewActionKind.REPAIR_MANUAL_ACTION_LOG` and as the suggested
  action for log inconsistency/malformed/target-mismatch review items. No
  executable command, CLI/API repair surface, verifier, or test-backed repair
  workflow exists. `append_manual_action(...)` chooses `max(sequence)+1`, so a
  future append would continue after 60 and would not close the skipped 59
  condition.
- Mutation safety:
  no broad mutation run was performed. No source, Decision Journal, Manual
  Action Log, or generated-output file changed; `git diff -- manual_actions.jsonl
  decision_journal.jsonl pandora_3e1ee0f1_bk_00_000000e8.s reproduction.json`
  was empty.

Decision:

- Do not repair in `017-052`. The one-record renumbering may be deterministic,
  but it would rewrite target-local manual state without a supported command,
  verifier, or rollback/proof surface.
- Treat the inconsistency as a real hygiene blocker for future write work, not
  as corruption of the current accepted RSSET projection.
- Follow-up: `017-053` should either implement a dry-run-first repair command
  for this exact one-record skipped-sequence case or explicitly defer Manual
  Action Log sequence normalization outside the 017 protocol. Required repair
  gates: one mismatch only, final record only, unique action ids, before/after
  projected semantic state equal except the review item removal, no source or
  Decision Journal changes, verifier artifact no-write passes, and exact
  round-trip remains exact.

Verification:

- `uv run python -m amiga_reversing.tools.validate_017_issues`
- `git diff --check -- docs/issues/017-052-manual-action-log-inconsistency-triage.md
  docs/issues/017-053-manual-action-log-sequence-repair-gate.md
  docs/proposals/017-evidence-driven-analysis-protocol.md`
