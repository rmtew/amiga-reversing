# 017-041: Source-Offset Immediate Provenance Packet

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: source-offset immediate evidence packet and decision lane
- Blocked by: none after `017-040`
- Current proposal state: RSSET/app-base has demonstrated the full journal to
  verifier to mutation path for one selected Pandora use. Source-offset
  immediates still rely on narrower immediate-reference reports and must not
  promote same-literal evidence as durable provenance.
- Desired proposal state after this issue: one selected Pandora source-offset
  immediate has a protocol packet with identity, possible meanings, landing
  range, dataflow, conflicts, decision status, and clear blockers for any later
  mutation.

## Protocol Delta

- Adds: shared evidence packet shape for source-offset immediate candidates.
- Changes: immediate-reference reports expose selected-operand evidence and
  blockers through the Evidence-Driven Analysis Protocol.
- Replaces: same-literal-only promotion as a sufficient source-offset proof.
- Deletes: none unless research finds obsolete report-private helper code fully
  replaced by the packet.
- Leaves out of scope: broad immediate sweep, speculative labels, UI, unrelated
  Pandora cleanup, output mutation unless every gate is already present.

## Default Behavior

- Existing generated source and default planner behavior must remain unchanged.
- Same-literal-only evidence must remain report-only.
- No Manual Action Log write is allowed unless this issue explicitly proves
  command support, generated-source verifier support, negative safety, and exact
  round-trip.

## Evidence Standard

The packet must distinguish a durable source-offset interpretation from a
coincidental literal. It must include:

- selected target identity, hunk, row, operand index, and literal value;
- literal width, signedness, and syntax form;
- possible interpretations, including source offset and runtime address where
  applicable;
- landing range classification and whether the target lies inside the loaded
  binary;
- local and downstream dataflow from the immediate result;
- conflicting interpretations or explicit `conflicts: []`;
- current render intent and whether mutation is blocked, deferred, rejected, or
  accept-ready.

If any required evidence is unavailable, record the blocker instead of creating
an accept.

## Pandora Proof

- Primary target candidate: Pandora `s0:000009A6` / `addi.w #4224,d1`.
- Demonstrate the packet from current analysis facts and reports.
- Show why same-literal evidence alone is insufficient.
- Show the concrete blocker list for accepting or mutating the candidate.
- If the packet is sufficient and all mutation gates already exist, perform only
  one scoped command-backed mutation with generated-source, negative-safety, and
  exact round-trip verification. Otherwise stop read-only.

## Implementation Slice

- C fact graph/query work: identify whether operand identity, range, and
  dataflow facts already exist in C analysis or need a narrow query.
- Python/API/report work: expose a source-offset-immediate packet through the
  relevant report/inspect surface.
- Journal/replay work: add accepted/deferred/rejected/mismatched decision lane
  support for this packet only if packet identity is stable enough.
- Renderer/verifier work: report render intent and missing verifier gates; do
  not implement mutation unless all safe gates are present.
- Tests/proof: packet shape, same-literal-only report-only behavior, blocker
  naming, selected Pandora packet proof, and unchanged default planner behavior.

## Research Completion Standard

Record trace blocks for immediate discovery, operand identity, range/landing
classification, dataflow/xref sources, report surfaces, command catalog,
renderer/verifier support, exact round-trip availability, and any old code
deleted or deferred.

## Research Coverage

- [x] Existing immediate-reference reports checked.
- [x] C/Python ownership of operand identity checked.
- [x] Literal width/signedness source checked.
- [x] Source-offset/runtime-address interpretation path checked.
- [x] Landing range and downstream dataflow sources checked.
- [x] Command, renderer, verifier, and exact round-trip gates checked.
- [x] Default planner behavior checked.

## Research Review

- [x] Second pass checked trace blocks against named files/functions.
- [x] Cross-references searched for missed immediate-reference hooks.
- [x] Same-literal-only false promotion risk reviewed.
- [x] Proposal updated with model corrections or deferred follow-ups.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Protocol delta implemented as described, or proposal updated.
- [x] Default behavior impact verified.
- [x] Old code deleted, or deferred deletion blocker recorded.
- [x] Evidence packet shape tested.
- [x] Decision/replay behavior tested where applicable.
- [x] Mutation stayed blocked unless every safe gate was proven.
- [x] Pandora proof recorded.
- [x] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

- Added read-only `source_offset_immediate_evidence_packet` assembly in
  `amiga_reversing/reversing_loop.py`, reusing existing immediate-reference
  report rows and leaving default report/planner mutation behavior unchanged.
- Pandora proof command selected `s0:000009A6:op0` /
  `addi.w #4224,d1`: packet status `blocked`, source family `source_offset`,
  blockers `same_literal_only_not_durable_provenance`,
  `missing_accepted_runtime_address_provenance`,
  `missing_source_offset_decision_replay_support`, and
  `missing_source_offset_render_verifier_gate`; report mutation gate stayed
  `safe_to_mutate=false` with 9 report-only candidates.
- Focused tests: `test_source_offset_immediate_packet_keeps_same_literal_report_only`.
- Verification: `uv run python -m pytest tests\test_reversing_loop.py tests\test_decision_journal.py tests\test_validate_017_issues.py -q`
  passed with 369 tests; changed-file `ruff check` passed.
