# 017-053: Manual Action Log Sequence Repair Gate

Status: active

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
  work.

## Protocol Delta

- Adds: explicit gates for repairing or deferring Manual Action Log sequence
  normalization.
- Changes: future 017 writes must not proceed while target-local manual state
  reports unexplained sequence inconsistency.
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
  blocked on the open review item.

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

## Research Coverage

- [ ] Existing repair support checked.
- [ ] Dry-run repair shape defined.
- [ ] One-record repair gates implemented or deferral justified.
- [ ] Projection before/after equivalence checked.
- [ ] RSSET verifier artifact no-write checked.
- [ ] Exact round-trip checked.
- [ ] No unrelated target mutation checked.

## Research Review

- [ ] Second pass checked gates against `017-052` evidence.
- [ ] Risk of hiding real Manual Action Log corruption reviewed.
- [ ] Proposal updated with repair or deferral outcome.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Protocol delta implemented as described, or proposal updated.
- [ ] Default behavior impact verified.
- [ ] Old code deleted, or deferred deletion blocker recorded.
- [ ] Dry-run proof recorded before any write.
- [ ] No source/journal/generated-output mutation performed.
- [ ] Post-repair or deferral state recorded.
- [ ] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

Fill this section when completed with the dry-run repair proof, repair or
deferral decision, post-decision verifier results, and mutation audit.
