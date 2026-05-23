# 017-052: Manual Action Log Inconsistency Triage

Status: active

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

- [ ] Generation site for `manual_action_log_inconsistency:target` found.
- [ ] Current Pandora inspect/planner output checked.
- [ ] Current `manual_actions.jsonl` sequence/hash state checked.
- [ ] Projected manual state checked.
- [ ] Impact on RSSET verifier chain checked.
- [ ] Repair command/API support checked.
- [ ] Safe repair gates or deferral criteria defined.

## Research Review

- [ ] Second pass checked trace blocks against named files/functions.
- [ ] Cross-references searched for existing repair or consistency helpers.
- [ ] Risk of hiding real manual-state corruption reviewed.
- [ ] Proposal updated with classification and next step.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Protocol delta implemented as described, or proposal updated.
- [ ] Default behavior impact verified.
- [ ] Old code deleted, or deferred deletion blocker recorded.
- [ ] No source/journal/manual/generated-output mutation performed.
- [ ] Current blocker classification recorded.
- [ ] Follow-up repair issue or deferral recorded.
- [ ] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

Fill this section when completed with the generation site, root cause, current
Pandora proof, verifier impact, and the next issue or deferral decision.
