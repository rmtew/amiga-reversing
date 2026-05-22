# 017-047: A5 Path/Lifetime Decision Gate

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: A5 path/lifetime decision lane and mutation readiness
- Blocked by: `017-042`
- Current proposal state: `017-042` added a read-only
  `a5_path_lifetime_evidence_packet` over existing A5 CFG lifetime reports. It
  distinguishes accepted existing manual state from listing-state-only blocked
  candidates, and packet command gates are non-mutating.
- Desired proposal state after this issue: one selected Pandora A5 packet has a
  durable accepted, deferred, or rejected Decision Journal outcome. If accepted,
  any mutation remains gated by path/lifetime scope, command support,
  generated-source verifier, negative safety, exact round-trip, and audit
  verifier evidence.

## Protocol Delta

- Adds: Decision Journal lane for A5 path/lifetime packets.
- Changes: A5 packet state can be resolved as accepted, deferred, or rejected
  without treating linear listing-state evidence as accepted provenance.
- Replaces: none unless a selected old A5 report-private decision path is fully
  superseded by packet/replay state.
- Deletes: obsolete selected-slice helper code only if this issue fully replaces
  it and tests prove unchanged default behavior.
- Leaves out of scope: broad A5 sweep, cosmetic label churn, UI, and mutation
  without complete verifier/round-trip gates.

## Default Behavior

- Read-only packet command gates must remain non-mutating.
- Linear listing-state evidence alone must never create accepted A5
  path/lifetime provenance.
- `decision_journal.jsonl` may be appended only through validated append logic.
- Manual Action Log writes are forbidden unless every mutation gate is proven in
  this issue.

## Decision Contract

The issue must choose exactly one outcome for the selected Pandora packet:

- `accept_fact` only if durable evidence proves base setup, path/lifetime scope,
  no clobber before use, explicit conflicts, and selected render intent;
- `defer_fact` if evidence is plausible but incomplete or verifier/tool support
  is missing;
- `reject_fact` if the candidate is wrong or not useful under the protocol.

Accepted decisions must include selected identity, base register, displacement,
computed base expression, path/lifetime scope, evidence refs to current packet
output, explicit `conflicts: []`, and a reason explaining why the selected use
is durable. Deferred/rejected decisions must include the same identity and a
specific reason.

## Mutation Contract

Mutation may proceed only when all are true:

- one exact active accepted journal decision matches the selected A5 packet;
- command support exists for the selected operand;
- generated-source verifier proves only the selected scoped render effect;
- negative safety proves unrelated A5 candidates are unchanged;
- exact round-trip passes;
- Decision Journal audit verifier layers are backed by current verifier results,
  not inference.

If any gate is absent, record the durable decision/blocker and stop read-only.

## Pandora Proof

- Start from the `017-042` accepted-existing candidate and blocked
  listing-state candidate.
- Prefer a selected candidate that can prove why no fresh mutation is needed or
  why mutation remains blocked.
- Demonstrate final packet/decision/audit state after this issue.
- Do not run a broad Pandora mutation sweep.

## Implementation Slice

- C fact graph/query work: identify or add only the narrow path/lifetime query
  needed for the selected A5 decision.
- Python/API/report work: add the A5 decision lane to packet/report output and
  exact blockers.
- Journal/replay work: support accepted/deferred/rejected A5 decisions with
  active/superseded replay and audit state.
- Renderer/verifier work: implement or report blockers for scoped render,
  negative safety, and exact round-trip gates.
- Tests/proof: listing-state-only cannot accept, accepted/deferred/rejected lane
  behavior, audit replay, default planner unchanged, and Pandora proof.

## Research Completion Standard

Record trace blocks for the `017-042` packet, existing A5 reports/manual state,
C path/lifetime facts, command catalog, Decision Journal append/replay/audit,
renderer/verifier gates, exact round-trip, and any old code deleted or
deferred.

## Completion Evidence

- Added `decision_lane` to `a5_path_lifetime_evidence_packet`.
- Appended durable Pandora `defer_fact`
  `decision-a5-path-lifetime-0000045c-defer-017-047`.
- Final Pandora packet for `s0:0000045C:op0` reports
  `decision_lane.status=deferred`, `safe_to_mutate=false`, and existing manual
  state with `already_recorded_in_manual_state`/`missing_command_candidate`
  blockers.
- No mutation was run; listing-state-only A5 evidence remains non-accepting.

## Research Coverage

- [x] `017-042` packet output checked.
- [x] Existing A5 command support checked.
- [x] Durable A5 path/lifetime provenance sources checked.
- [x] Decision Journal append/replay/audit path checked.
- [x] Generated-source verifier and negative-safety support checked.
- [x] Exact round-trip availability checked.
- [x] Default planner behavior checked.

## Research Review

- [x] Second pass checked trace blocks against named files/functions.
- [x] Cross-references searched for missed A5/provenance hooks.
- [x] Listing-state-only acceptance risk reviewed.
- [x] Proposal updated with model corrections or deferred follow-ups.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Protocol delta implemented as described, or proposal updated.
- [x] Default behavior impact verified.
- [x] Old code deleted, or deferred deletion blocker recorded.
- [x] Decision lane tested.
- [x] Audit replay tested.
- [x] Mutation stayed blocked unless every safe gate was proven.
- [x] Pandora proof recorded.
- [x] Post-commit review found no unresolved worthwhile findings.
