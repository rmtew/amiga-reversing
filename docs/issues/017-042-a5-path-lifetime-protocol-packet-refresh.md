# 017-042: A5 Path/Lifetime Protocol Packet Refresh

Status: active

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: A5 hardware/base path and lifetime evidence packet
- Blocked by: none after `017-040`
- Current proposal state: earlier A5 work produced command-backed Pandora
  hardware-reference improvements, but the protocol now requires a shared
  packet model that separates accepted path/lifetime evidence from linear
  listing-state candidates.
- Desired proposal state after this issue: one A5 candidate has a packet that
  shows base setup, expression, reachability, lifetime, conflicts, render intent,
  verifier gates, and exact round-trip status under the shared protocol.

## Protocol Delta

- Adds: protocol packet shape for A5 path/lifetime evidence.
- Changes: A5 reports identify why a candidate is accepted, blocked, deferred,
  or render-unsafe without relying on listing order alone.
- Replaces: any selected-slice report-private acceptance rule that treats linear
  listing-state evidence as accepted path/lifetime provenance.
- Deletes: obsolete selected-slice fallback only if the packet fully owns the
  selected behavior.
- Leaves out of scope: broad A5 sweep, cosmetic label churn, UI, and mutation of
  candidates that lack complete path/lifetime scope.

## Default Behavior

- Existing accepted A5 manual state must not regress.
- New report-only A5 candidates must not become mutation-capable from linear
  listing-state evidence alone.
- If v2 packet output replaces an existing selected A5 default surface, old
  selected-slice code must be deleted or a deletion blocker recorded.

## Evidence Standard

The packet must include:

- selected target identity, hunk, row, operand index, base register, and
  displacement;
- A5 base setup instruction and computed base expression;
- custom/app-base delta interpretation where relevant;
- CFG reachability from definition to use;
- no A5 clobber before selected use;
- lifetime end or explicit lifetime blocker;
- explicit conflicts or `conflicts: []`;
- render intent, unsafe render forms, verifier plan, and exact round-trip
  availability.

Linear listing-state evidence alone must produce a blocked or candidate status,
never an accepted mutation authority.

## Pandora Proof

- Choose one real Pandora A5 candidate from existing A5 reports/manual state that
  can demonstrate the packet clearly.
- Prefer a candidate with prior accepted A5 command evidence so the issue can
  compare old accepted state with the new packet.
- Show at least one blocked/candidate A5 row where listing-state evidence is not
  enough.
- Mutate only if the selected candidate has accepted path/lifetime scope,
  command support, generated-source verifier support, negative safety, and exact
  round-trip. Otherwise stop read-only.

## Implementation Slice

- C fact graph/query work: locate or add the narrow query needed for A5 base,
  reachability, clobber, and lifetime facts.
- Python/API/report work: expose the A5 packet through the relevant report or
  inspect surface.
- Journal/replay work: add decision lane support only if selected identity and
  scope are stable enough.
- Renderer/verifier work: surface render intent and unsafe forms; do not enable
  mutation without verifier and exact round-trip proof.
- Tests/proof: accepted packet, listing-state-only blocked packet, conflict
  handling, default planner behavior, and Pandora proof.

## Research Completion Standard

Record trace blocks for A5 discovery, C facts, Python report assembly, existing
manual state, command catalog, renderer/verifier, exact round-trip, replaced
code, and out-of-scope sweep work.

## Research Coverage

- [ ] Existing A5 reports checked.
- [ ] Prior accepted A5 manual actions checked.
- [ ] C reachability/clobber/lifetime sources checked.
- [ ] Custom/app-base delta handling checked.
- [ ] Command, renderer, verifier, and exact round-trip gates checked.
- [ ] Listing-state-only blocked behavior checked.

## Research Review

- [ ] Second pass checked trace blocks against named files/functions.
- [ ] Cross-references searched for missed A5 hooks.
- [ ] Old selected-slice behavior classified as reuse, replace, or deferred.
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
