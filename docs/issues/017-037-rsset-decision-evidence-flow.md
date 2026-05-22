# 017-037: RSSET Decision Evidence Flow

Status: active

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: first packet-to-decision-to-gate evidence flow
- Blocked by: `017-036`
- Current proposal state: RSSET evidence packets and Decision Journal replay
  exist separately. `017-036` exposes accepted/deferred/rejected journal
  projection through `decision-journal-report`, but RSSET reports do not consume
  it.
- Desired proposal state after this issue: the RSSET packet/gate can consult a
  replayed Decision Journal projection as accepted/deferred/rejected evidence
  without enabling mutation until all safe gates are satisfied.

## Protocol Delta

- Adds: RSSET evidence packet integration with replayed Decision Journal
  decisions.
- Changes: accepted RSSET app-base evidence can come from the replay
  projection as a separate read-only lane.
- Replaces: none by default. Report-private/manual-state RSSET evidence remains
  visible until a later cutover issue explicitly deletes it.
- Deletes: none unless implementation evidence proves a selected-slice helper
  is pure duplication and the proposal is updated first.
- Leaves out of scope: broad RSSET migration, broad Pandora mutation run,
  rendering, UI, enabling `rsset.binding.bind`.

## Default Behavior

- Existing RSSET report/default planner behavior must remain non-mutating.
- The selected RSSET report/packet may gain a read-only
  `journal_decision_evidence` lane, but `rsset.binding.bind` must remain
  blocked until a later safe-mutation issue wires verifier/render gates.
- Do not count journal accepted evidence as command-enabled mutation evidence
  unless every non-render gate is also explicit and render/verifier gates still
  block mutation.

## Evidence Matching Contract

Journal decisions may be associated with an RSSET selected use only when all
required identity and safety fields match:

- `action` is one of `accept_fact`, `defer_fact`, or `reject_fact`.
- `candidate_id` equals the RSSET candidate id, for Pandora
  `rsset-raw-a6:022E`.
- `selected_identity.target_id`, `segment_id`, `addr`, and `operand_index`
  match the selected use.
- If `selected_identity.selected_use_id` exists, it must match the packet
  selected-use id.
- `fact_type` for accepted facts is `rsset_app_base`.
- `scope.kind` for accepted facts is `selected_use`.
- `scope.hunk`, `scope.addr`, and `scope.operand_index` match the selected
  use.
- `conflicts` for accepted facts is explicit empty list.

Mismatches remain visible as rejected journal evidence, not accepted evidence.
Deferred/rejected records for the selected identity should be surfaced as
blockers/negative evidence, not silently ignored.

## Output Contract

Add a read-only journal evidence lane to the selected RSSET packet/report. The
shape may be adjusted to fit existing packet structure, but must expose:

- `status`: `accepted`, `blocked`, `rejected`, or `unavailable`.
- `accepted_count`: exact accepted journal decisions usable as RSSET app-base
  evidence.
- `accepted`: accepted matching decisions.
- `deferred_count` / `deferred`: selected matching defer decisions.
- `rejected_count` / `rejected`: selected matching reject decisions.
- `mismatched_count` / `mismatched`: journal decisions with same candidate or
  nearby selected identity that failed exact matching, including reason codes.
- `missing_gates`: remaining gates after journal evidence is considered.
- `mutation_enabled`: always `false` in this issue.

Reason codes should distinguish wrong candidate, wrong selected identity, wrong
fact type, missing selected-use scope, scope mismatch, and non-empty conflicts.

## Pandora Proof

- Target candidate: RSSET packet candidate `rsset-raw-a6:022E` at
  `s0:000006E4`.
- Evidence expected: packet/report output shows whether accepted/deferred/
  rejected journal decisions satisfy or block the journal app-base evidence lane.
- Decision behavior: journal accept can satisfy the accepted-base-evidence lane
  only when selected-use identity, path/lifetime scope, and empty conflicts are
  exact.
- Command gate behavior: mutation remains blocked unless all gates are present;
  render/verifier gates must remain blockers in this issue.
- Render effect: none.
- Verifier/round-trip: no output-affecting verification required.

## Implementation Slice

- C fact graph/query work: none unless implementation evidence proves a small
  read-only query is required and the proposal is updated first.
- Python/API/report work: connect RSSET packet/report evidence to replay
  projection for the selected RSSET candidate as a read-only lane.
- Journal/replay work: consume accepted/deferred/rejected projection state.
- Renderer/verifier work: none.
- Tests: accepted exact selected-use decision, rejected/deferred blockers,
  mismatched identity rejection, non-empty conflicts rejection, missing
  selected-use scope rejection, wrong candidate/fact-type rejection, malformed
  journal blocking active evidence, and no unsafe mutation.

## Research Completion Standard

Record trace blocks for RSSET packet generation, replay projection, command
catalog gates, current report-private accepted-evidence paths, Manual Action
Log accepted evidence, and the selected Pandora candidate.

## Research Coverage

- [ ] RSSET packet and gate code checked.
- [ ] Decision replay projection checked.
- [ ] Command catalog gate logic checked.
- [ ] Report-private accepted-evidence logic checked for replacement boundary.
- [ ] Manual Action Log accepted-evidence path checked for replacement
  boundary.
- [ ] Journal matching and mismatch reason codes defined.
- [ ] Pandora selected-use identity and blocker evidence checked.

## Research Review

- [ ] Second pass checked trace blocks against named files/functions.
- [ ] Cross-references searched for missed hooks.
- [ ] Proposal updated if RSSET evidence flow changes the protocol.
- [ ] Next issue scope follows from the RSSET decision flow.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Protocol delta implemented as described, or proposal updated.
- [ ] Default behavior impact verified.
- [ ] Old code deleted, or deferred deletion blocker recorded.
- [ ] RSSET decision evidence flow tested.
- [ ] Command gate refuses unsafe mutation unless all gates are present.
- [ ] Journal accepted/deferred/rejected/mismatched evidence lanes tested.
- [ ] Render/verifier/round-trip checked where output-affecting, or explicitly
  not applicable because no output changed.
- [ ] Pandora proof recorded.
- [ ] Post-commit review found no unresolved worthwhile findings.
