# 017-053: Manual Action Log Sequence Repair Gate

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: target-local manual state consistency and mutation readiness
- Blocked by: `017-052`
- Current proposal state: `017-052` classified the Pandora
  `manual_action_log_inconsistency:target` as a real skipped-sequence condition
  in `manual_actions.jsonl`: the final RSSET action is file action index 59 but
  carries `sequence=60`.
- Desired proposal state after this issue: either a fully gated, dry-run-first
  repair path exists for the exact one-record skipped-sequence case, or Manual
  Action Log sequence normalization is explicitly deferred outside 017 mutation
  work with mutation readiness/reporting made to block while the open
  inconsistency remains.

## Protocol Delta

- Adds: explicit gates for repairing or deferring Manual Action Log sequence
  normalization.
- Changes: future 017 writes must not proceed while target-local manual state
  reports unexplained sequence inconsistency, and machine-readable mutation
  readiness must not report safe mutation while that inconsistency remains open.
- Replaces: ad hoc manual editing of `manual_actions.jsonl`.
- Deletes: none.
- Leaves out of scope: source mutation, Decision Journal appends, broad target
  repair, and automatic repair of malformed or multi-record log corruption.

## Default Behavior

- Default inspect/report behavior remains read-only.
- Any repair command must support a dry-run mode that reports the exact file
  edit before writing.
- Repair must be limited to the single final-record skipped-sequence condition
  proven by `017-052`.
- If repair cannot meet every gate below, defer it and keep future mutation work
  blocked on the open review item in both prose and machine-readable reports.
- Current mismatch to fix or explicitly defer: `inspect_target(...)` reports
  `safe_to_mutate=true` while `manual_action_log_inconsistency:target` is open.

## Required Repair Gates

- Exactly one `manual_action_log_inconsistency` item exists.
- The log parses successfully and action ids are unique.
- The only sequence mismatch is the final action record.
- The final action record's file index is the expected sequence.
- The proposed edit changes only that final record's `sequence` value.
- Before/after projected semantic state is equal except removal of the sequence
  inconsistency review item.
- No source, Decision Journal, verifier artifact, or generated-output file is
  changed by the repair.
- The RSSET verifier artifact producer passes in no-write mode after repair.
- Exact round-trip remains exact after repair.
- After repair, `inspect_target(...)` no longer reports
  `manual_action_log_inconsistency:target`.
- If repair is deferred, `inspect_target(...)` and any equivalent mutation
  readiness surface must report unsafe/blocked mutation while
  `manual_action_log_inconsistency:target` remains open.

## Research Coverage

- [x] Existing repair support checked.
- [x] Dry-run repair shape defined.
- [x] One-record repair gates implemented or deferral justified.
- [x] Projection before/after equivalence checked.
- [x] RSSET verifier artifact no-write checked.
- [x] Exact round-trip checked.
- [x] No unrelated target mutation checked.
- [x] Machine-readable mutation readiness checked for the open-item case.
- [x] Outcome proves either repair clears the item or readiness blocks while it remains open.

## Research Review

- [x] Second pass checked gates against `017-052` evidence.
- [x] Risk of hiding real Manual Action Log corruption reviewed.
- [x] Risk of prose-only blocker with `safe_to_mutate=true` reviewed.
- [x] Proposal updated with repair or deferral outcome.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Protocol delta implemented as described, or proposal updated.
- [x] Default behavior impact verified.
- [x] Old code deleted, or deferred deletion blocker recorded.
- [x] Dry-run proof recorded before any write.
- [x] No source/journal/generated-output mutation performed.
- [x] Machine-readable mutation readiness mismatch resolved or explicitly deferred with blocker.
- [x] Post-repair or deferral state recorded.
- [x] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

Implemented `repair-manual-action-log-sequence` as a dry-run-first command and
`repair_manual_action_log_sequence(...)` API. The command is limited to the
single final-record skipped-sequence case and blocks malformed logs, duplicate
action ids, non-final mismatches, multi-mismatch logs, and semantic projection
changes beyond clearing the sequence inconsistency.

Dry-run proof on
`amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`
passed every gate before write:

- 60 log records parsed: header plus 59 actions.
- Exactly one open `manual_action_log_inconsistency:target` existed.
- Only mismatch was final line 60, action
  `manual-6e574feccab748359c7577833fa718ba`.
- Proposed edit changed only `sequence`, from `60` to expected file action
  index `59`.
- Before/after projection was semantically equal except the sequence review
  item was cleared.

Repair decision: applied the one-record repair with `--write`. The resulting
git diff for target state changes only the final manual action `sequence`
value, `60 -> 59`.

Post-repair evidence:

- `inspect_target(...)`: `safe_to_mutate=true`, `mutation_readiness.blockers=[]`,
  and `candidate_work=[]`.
- `round_trip`: exact.
- `decision-verifier-artifact --decision-id decision-rsset-022e-accept-017-040`
  in no-write mode: `status=passed`; `generated_source`,
  `negative_safety`, `semantic_reload`, and `exact_round_trip` passed.
- `git diff --name-only` showed only implementation/test/docs files and the
  repaired `manual_actions.jsonl`; no source, Decision Journal, verifier
  artifact, or generated-output file changed.

The open-item readiness mismatch is also covered directly: before repair,
`inspect_target(...)` reported `safe_to_mutate=false` with a
`manual_action_log_inconsistency` mutation blocker while the item was open.
