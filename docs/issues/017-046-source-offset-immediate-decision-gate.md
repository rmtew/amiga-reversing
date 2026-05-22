# 017-046: Source-Offset Immediate Decision Gate

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: source-offset immediate decision lane and mutation readiness
- Blocked by: `017-041`
- Current proposal state: `017-041` added a read-only
  `source_offset_immediate_evidence_packet` and proved the selected Pandora
  immediate remains blocked. The packet exposes selected identity, literal
  width/syntax, possible source-offset interpretation, landing/dataflow lanes,
  and explicit blockers while keeping packet command gates non-mutating.
- Desired proposal state after this issue: the selected Pandora source-offset
  immediate has a durable accepted, deferred, or rejected Decision Journal
  outcome. If accepted, mutation readiness is gated by command support,
  generated-source verifier, negative safety, and exact round-trip. If evidence
  is insufficient, the blocker is durable and mutation remains disabled.

## Protocol Delta

- Adds: Decision Journal lane for source-offset immediate packets.
- Changes: source-offset immediate packets can be resolved as accepted,
  deferred, or rejected protocol facts without relying on same-literal evidence
  alone.
- Replaces: none unless a selected old immediate-reference report-private rule
  is fully superseded by the packet/decision lane.
- Deletes: obsolete selected-slice helper code only if this issue fully replaces
  it and tests prove unchanged default behavior.
- Leaves out of scope: broad immediate sweep, speculative labels, UI, unrelated
  Pandora cleanup, and mutation without complete verifier/round-trip gates.

## Default Behavior

- The read-only packet command gate must remain non-mutating.
- Same-literal-only evidence must never create an accepted source-offset fact.
- `decision_journal.jsonl` may be appended only through validated append logic.
- Manual Action Log writes are forbidden unless every mutation gate is proven in
  this issue.

## Decision Contract

The issue must choose exactly one outcome for the selected Pandora packet:

- `accept_fact` only if durable evidence proves the source-offset immediate
  interpretation beyond same-literal matching;
- `defer_fact` if evidence is plausible but incomplete or missing required
  verifier/tool support;
- `reject_fact` if the packet evidence shows the interpretation is wrong or not
  useful under the protocol.

Accepted decisions must include:

- selected target identity, hunk, row, operand index, literal, width, and syntax;
- fact type for source-offset immediate provenance;
- scope for the selected operand/use;
- evidence refs to current packet/report output;
- explicit `conflicts: []`;
- reason explaining why the interpretation is durable;
- no same-literal-only acceptance.

Deferred/rejected decisions must include the same selected identity and a reason
that is specific enough for later replay/audit.

## Mutation Contract

Mutation may proceed only when all are true:

- one exact active accepted journal decision matches the selected packet;
- command support exists for the selected operand;
- generated-source verifier proves only the selected scoped render effect;
- negative safety proves unrelated immediate candidates are unchanged;
- exact round-trip passes;
- the Decision Journal audit can report verifier layers from current results,
  not inference.

If any gate is absent, record the durable decision/blocker and stop read-only.

## Pandora Proof

- Primary target candidate: Pandora `s0:000009A6` / `addi.w #4224,d1`.
- Start from the `017-041` packet and its blockers:
  `same_literal_only_not_durable_provenance`,
  `missing_accepted_runtime_address_provenance`,
  `missing_source_offset_decision_replay_support`, and
  `missing_source_offset_render_verifier_gate`.
- Demonstrate the final packet/decision/audit state after this issue.
- Do not run a broad Pandora mutation sweep.

## Implementation Slice

- C fact graph/query work: add or identify the durable provenance query needed
  to decide whether the selected immediate is source-offset, runtime-address,
  ambiguous, or unsupported.
- Python/API/report work: add the source-offset decision lane to packet/report
  output and expose exact blockers.
- Journal/replay work: support accepted/deferred/rejected source-offset
  immediate decisions with active/superseded replay and audit state.
- Renderer/verifier work: implement or report blockers for scoped render,
  negative safety, and exact round-trip gates.
- Tests/proof: same-literal-only cannot accept, accepted/deferred/rejected lane
  behavior, audit replay, default planner unchanged, and Pandora proof.

## Research Completion Standard

Record trace blocks for the `017-041` packet, existing immediate-reference
reports, source-offset/runtime-address provenance sources, command catalog,
Decision Journal append/replay/audit, renderer/verifier gates, exact round-trip,
and any old code deleted or deferred.

## Completion Evidence

- Added `decision_lane` to `source_offset_immediate_evidence_packet`.
- Appended durable Pandora `defer_fact`
  `decision-source-offset-immediate-000009a6-defer-017-046`.
- Final Pandora packet for
  `immediate-runtime-ref:s0:000009A6:instruction:664:0:00001080`
  reports `decision_lane.status=deferred`, `safe_to_mutate=false`, and the
  original same-literal/source-offset blockers.
- No mutation was run; same-literal-only evidence remains non-accepting.

## Research Coverage

- [x] `017-041` packet output checked.
- [x] Existing immediate-reference command support checked.
- [x] Durable source-offset/runtime-address provenance sources checked.
- [x] Decision Journal append/replay/audit path checked.
- [x] Generated-source verifier and negative-safety support checked.
- [x] Exact round-trip availability checked.
- [x] Default planner behavior checked.

## Research Review

- [x] Second pass checked trace blocks against named files/functions.
- [x] Cross-references searched for missed immediate/provenance hooks.
- [x] Same-literal-only acceptance risk reviewed.
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
