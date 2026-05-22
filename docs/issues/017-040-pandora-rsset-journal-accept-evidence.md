# 017-040: Pandora RSSET Journal Accept Evidence

Status: complete

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: durable Decision Journal evidence required before mutation
- Blocked by: `017-038`
- Current proposal state: `017-038` can report the selected RSSET gate as ready
  only when a durable active journal accept exists. `017-039` is blocked because
  the real Pandora target has no active `accept_fact` for
  `rsset-raw-a6:022E` at `s0:000006E4:op1`.
- Desired proposal state after this issue: Pandora has a validated durable
  Decision Journal `accept_fact` for the selected RSSET app-base evidence, and
  `017-038` reports `ready_for_039=true` while mutation remains disabled.

## Protocol Delta

- Adds: one real durable Decision Journal accept for the selected Pandora RSSET
  evidence, if the evidence is genuinely sufficient.
- Changes: the selected RSSET gate may become ready for `017-039`, but not
  executable.
- Replaces: none.
- Deletes: none.
- Leaves out of scope: enabling `rsset.binding.bind`, writing Manual Action Log
  mutation state, changing rendered source, broad RSSET migration, UI.

## Default Behavior

- Existing planner/default mutation behavior must remain unchanged.
- `rsset.binding.bind` must remain disabled.
- `decision_journal.jsonl` may be written only through the Decision Journal
  append path, with valid hash-chain `prev`.

## Evidence Standard

Do not create a synthetic accept just to unblock mutation. The accept must be
backed by current durable evidence:

- exact selected identity for Pandora `rsset-raw-a6:022E` at `s0:000006E4:op1`;
- `fact_type=rsset_app_base`;
- `scope.kind=selected_use`;
- scope hunk/address/operand equals the selected use;
- `conflicts: []`;
- evidence refs point at current packet/report evidence;
- actor metadata and reason explain why this selected use is accepted;
- existing journal chain remains valid, or the issue records why it cannot be
  appended.

If real evidence is insufficient, do not append. Mark this issue blocked and
record the missing evidence.

## Pandora Proof

- Target candidate: RSSET packet candidate `rsset-raw-a6:022E` at
  `s0:000006E4`.
- Evidence expected: `decision-journal-report` shows one active accepted
  journal fact for the selected RSSET use.
- Gate expected: RSSET `journal_mutation_gate.ready_for_039=true` and
  `mutation_enabled=false`.
- Command gate behavior: `rsset.binding.bind` remains blocked/disabled until
  `017-039`.
- Render effect: none.
- Verifier/round-trip: no output-affecting verification required; exact
  round-trip availability must still be reported by the gate.

## Implementation Slice

- C fact graph/query work: none.
- Python/API/report work: use existing Decision Journal append/report and RSSET
  report surfaces; add only helper/test support if unavoidable.
- Journal/replay work: append or validate the durable accept record.
- Renderer/verifier work: none.
- Tests/proof: journal append/read validation, active projection shows accept,
  RSSET journal evidence lane shows accepted, `journal_mutation_gate` reports
  ready for 039 and mutation disabled, default planner still no action.

## Research Completion Standard

Record trace blocks for the RSSET packet evidence, Decision Journal append path,
projection output, `017-038` gate output, target-local state impact, and any
reason evidence is insufficient.

## Research Coverage

- [x] Selected Pandora RSSET packet/report evidence checked.
- [x] Existing `decision_journal.jsonl` state checked.
- [x] Decision Journal append/hash-chain path checked.
- [x] Active projection checked after append or proposed append.
- [x] `017-038` gate checked after append or proposed append.
- [x] Default planner and command gate checked to prove no mutation.

## Research Review

- [x] Second pass checked trace blocks against named files/functions.
- [x] Cross-references searched for missed hooks.
- [x] Proposal updated if evidence rules change.
- [x] `017-039` unblocked only if `ready_for_039=true`; otherwise keep it
  blocked with missing gates.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Protocol delta implemented as described, or proposal updated.
- [x] Default behavior impact verified.
- [x] Old code deleted, or deferred deletion blocker recorded.
- [x] Durable journal accept validated, or blocker recorded.
- [x] `decision-journal-report` projection proof recorded.
- [x] RSSET `journal_mutation_gate` proof recorded.
- [x] `mutation_enabled=false` and command gate blocked verified.
- [x] Render/verifier/round-trip checked where output-affecting, or explicitly
  not applicable because no output changed.
- [x] Pandora proof recorded.
- [x] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

- Commit `cf1067b8` added the durable target-local
  `decision_journal.jsonl` accept for `rsset-raw-a6:022E` at
  `s0:000006E4:op1`.
- The accepted record has `fact_type=rsset_app_base`,
  `scope.kind=selected_use`, matching hunk/address/operand, `conflicts: []`,
  actor metadata, reason, and evidence refs for packet/report/source/rebuild.
- After append, the selected RSSET gate reported `ready_for_039=true`,
  `mutation_enabled=false`, no missing gates, one active accepted decision,
  and exact round-trip availability.
- 017-039 subsequently consumed this durable accept through the gated command
  path; 017-040 itself performed no render mutation.
