# 017-048: Orphan/Code-Island Decision Lane

Status: active

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: orphan/code-island and ambiguous data-range decision lane
- Blocked by: `017-044`
- Current proposal state: `017-044` added a read-only
  `orphan_code_island_evidence_packet` over review/listing candidates. The
  selected Pandora proof is blocked and read-only, with explicit xref,
  overlap/range, render-effect, and exact-round-trip blockers.
- Desired proposal state after this issue: one selected Pandora orphan/code
  island or ambiguous data-range packet has a durable accepted, deferred, or
  rejected Decision Journal outcome. Ambiguity must become explicit protocol
  state, not hidden auto-analysis behavior.

## Protocol Delta

- Adds: Decision Journal lane for orphan/code-island and ambiguous data-range
  packets.
- Changes: ambiguous range/code packets can be resolved as accepted, deferred,
  or rejected protocol facts with durable reasons.
- Replaces: hidden speculative classification for the selected packet, if any is
  found during research.
- Deletes: obsolete selected-slice helper code only if this issue fully replaces
  it and tests prove unchanged default behavior.
- Leaves out of scope: broad target sweep, speculative code seeding, UI, and
  mutation without complete command/verifier/round-trip gates.

## Default Behavior

- Auto-analysis must not silently classify ambiguous islands as accepted without
  packet/decision evidence.
- Read-only packet command gates and safe-next-action surfaces must remain
  non-mutating.
- `decision_journal.jsonl` may be appended only through validated append logic.
- Manual Action Log writes are forbidden unless every mutation gate is proven in
  this issue.

## Decision Contract

The issue must choose exactly one outcome for the selected Pandora packet:

- `accept_fact` only if durable evidence proves classification, range identity,
  xrefs/control-flow/overlap state, conflicts, and render intent;
- `defer_fact` if the candidate is plausible but missing xrefs, overlap,
  range-byte, verifier, or round-trip support;
- `reject_fact` if the candidate is wrong, duplicate, or not useful under the
  protocol.

Accepted/deferred/rejected decisions must include selected range identity,
current classification, evidence refs to current packet output, conflicts or
specific blocker reason, and a reason suitable for later replay/audit.

## Mutation Contract

Mutation may proceed only when all are true:

- one exact active accepted journal decision matches the selected packet;
- command support exists for the selected action;
- generated-source verifier proves only the selected scoped render effect;
- negative safety proves unrelated ranges/candidates are unchanged;
- exact round-trip passes;
- Decision Journal audit verifier layers are backed by current verifier results,
  not inference.

If any gate is absent, record the durable decision/blocker and stop read-only.

## Pandora Proof

- Start from the `017-044` selected Pandora data-range/string packet unless
  research finds a better real candidate with stronger evidence.
- Demonstrate final packet/decision/audit state after this issue.
- Prefer durable `defer_fact` over speculative accept when xref/overlap/range
  evidence is incomplete.
- Do not run a broad Pandora mutation sweep.

## Implementation Slice

- C fact graph/query work: identify or add only the narrow xref/overlap/range
  query needed for the selected decision.
- Python/API/report work: add the orphan/code-island decision lane to packet or
  report output and exact blockers.
- Journal/replay work: support accepted/deferred/rejected range decisions with
  active/superseded replay and audit state.
- Renderer/verifier work: implement or report blockers for scoped render,
  negative safety, and exact round-trip gates.
- Tests/proof: ambiguous evidence cannot auto-accept, accepted/deferred/rejected
  lane behavior, audit replay, default planner unchanged, and Pandora proof.

## Research Completion Standard

Record trace blocks for the `017-044` packet, current review item generation,
C range/xref/overlap facts, command catalog, Decision Journal append/replay/audit,
renderer/verifier gates, exact round-trip, and any old code deleted or
deferred.

## Research Coverage

- [ ] `017-044` packet output checked.
- [ ] Existing orphan/code/data command support checked.
- [ ] Durable xref/control-flow/overlap/range evidence sources checked.
- [ ] Decision Journal append/replay/audit path checked.
- [ ] Generated-source verifier and negative-safety support checked.
- [ ] Exact round-trip availability checked.
- [ ] Default auto-analysis behavior checked.

## Research Review

- [ ] Second pass checked trace blocks against named files/functions.
- [ ] Cross-references searched for missed range/review hooks.
- [ ] Hidden speculative acceptance risk reviewed.
- [ ] Proposal updated with model corrections or deferred follow-ups.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Protocol delta implemented as described, or proposal updated.
- [ ] Default behavior impact verified.
- [ ] Old code deleted, or deferred deletion blocker recorded.
- [ ] Decision lane tested.
- [ ] Audit replay tested.
- [ ] Mutation stayed blocked unless every safe gate was proven.
- [ ] Pandora proof recorded.
- [ ] Post-commit review found no unresolved worthwhile findings.
