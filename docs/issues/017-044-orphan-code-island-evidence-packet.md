# 017-044: Orphan/Code-Island Evidence Packet

Status: active

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: orphan code, code islands, tables, strings, and data ranges
- Blocked by: none after `017-040`
- Current proposal state: the protocol can describe selected operand/fact
  candidates, but ambiguous code/data islands still risk remaining hidden as raw
  output or speculative auto-analysis decisions.
- Desired proposal state after this issue: one Pandora orphan/code-island or
  ambiguous data-range candidate has a packet that exposes xrefs, reachability,
  overlaps, range classification, conflicts, decision status, and safe next
  actions.

## Protocol Delta

- Adds: evidence packet shape for ambiguous code/data islands.
- Changes: orphan/data-range review candidates expose decidable, blocked,
  deferred, rejected, and action-ready status through the shared protocol.
- Replaces: hidden speculative classification for the selected packet.
- Deletes: none unless a selected old report-private path is fully replaced.
- Leaves out of scope: broad target sweep, speculative code seeding, UI, and
  output mutation without command/verifier/round-trip gates.

## Default Behavior

- Auto-analysis must not silently classify ambiguous islands as accepted without
  packet evidence.
- Existing rendered source must not change unless a selected command is proven
  safe.
- Ambiguous islands should become explicit blocked/deferred packet results, not
  hidden assumptions.

## Evidence Standard

The packet must include:

- selected range identity, hunk, start, end, and current classification;
- direct xrefs and potential incoming control-flow edges;
- overlap with known code, data, strings, tables, resources, or manual state;
- range bytes/decoded candidates sufficient for review;
- downstream render effect for each supported action;
- conflicts or explicit `conflicts: []`;
- decision status and blockers for seed code, seed data, reject, or defer.

## Pandora Proof

- Select one real Pandora orphan/code-island, table, string, or data-range
  candidate from existing reports.
- Prefer a candidate where the packet can clearly show why it is decidable or
  why it must remain deferred.
- Demonstrate at least one safe next action only if command, verifier, negative
  safety, and exact round-trip gates are present. Otherwise stop read-only with
  blockers.
- Do not run a broad Pandora mutation sweep.

## Implementation Slice

- C fact graph/query work: identify current code/data range, xref, overlap, and
  reachability facts; add a narrow query only if needed.
- Python/API/report work: expose one packet through the relevant review/inspect
  surface.
- Journal/replay work: add decision lane support only if selected range identity
  is stable enough.
- Renderer/verifier work: report render effect and missing verifier gates; do
  not enable mutation without exact proof.
- Tests/proof: packet shape, decidable/deferred/rejected statuses, overlap and
  xref evidence, no hidden auto-accept, unchanged default planner unless gated.

## Research Completion Standard

Record trace blocks for current review item generation, C range facts, xrefs,
overlap classification, command catalog, renderer/verifier, exact round-trip,
and selected Pandora proof.

## Research Coverage

- [ ] Existing orphan/code/data review reports checked.
- [ ] C range classification sources checked.
- [ ] Xref and control-flow reachability sources checked.
- [ ] Overlap detection sources checked.
- [ ] Command, renderer, verifier, and exact round-trip gates checked.
- [ ] Default auto-analysis behavior checked for hidden assumptions.

## Research Review

- [ ] Second pass checked trace blocks against named files/functions.
- [ ] Cross-references searched for missed review-item hooks.
- [ ] Hidden speculative classification risk reviewed.
- [ ] Proposal updated with model corrections or deferred follow-ups.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Protocol delta implemented as described, or proposal updated.
- [ ] Default behavior impact verified.
- [ ] Old code deleted, or deferred deletion blocker recorded.
- [ ] Evidence packet shape tested.
- [ ] Decision/replay behavior tested where applicable.
- [ ] Mutation stayed blocked unless every safe gate was proven.
- [ ] Pandora proof recorded.
- [ ] Post-commit review found no unresolved worthwhile findings.
