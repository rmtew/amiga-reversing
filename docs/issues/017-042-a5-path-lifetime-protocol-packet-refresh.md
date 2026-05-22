# 017-042: A5 Path/Lifetime Protocol Packet Refresh

Status: completed

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

- [x] Existing A5 reports checked.
- [x] Prior accepted A5 manual actions checked.
- [x] C reachability/clobber/lifetime sources checked.
- [x] Custom/app-base delta handling checked.
- [x] Command, renderer, verifier, and exact round-trip gates checked.
- [x] Listing-state-only blocked behavior checked.

## Research Review

- [x] Second pass checked trace blocks against named files/functions.
- [x] Cross-references searched for missed A5 hooks.
- [x] Old selected-slice behavior classified as reuse, replace, or deferred.
- [x] Proposal updated with model corrections or deferred follow-ups.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Protocol delta implemented as described, or proposal updated.
- [x] Default behavior impact verified.
- [x] Old code deleted, or deferred deletion blocker recorded.
- [x] Evidence packet shape tested.
- [x] Decision/replay behavior tested where applicable.
- [x] Every read-only packet command gate is explicitly non-mutating and cannot
  be consumed as mutation authority.
- [x] Public CLI/API/report access to the packet is wired and tested, or the
  issue records why private helper access is intentionally sufficient.
- [x] Mutation stayed blocked unless every safe gate was proven.
- [x] Pandora proof recorded.
- [x] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

- Added read-only `a5_path_lifetime_evidence_packet` assembly in
  `amiga_reversing/reversing_loop.py`, reusing the existing A5 CFG lifetime
  report plus existing Manual Action Log state suppression.
- Pandora accepted-existing proof: selected `s0:0000045C:op0`, source evidence
  `a5-custom-cfg:h0:00000456->0000045C:op0:b0002+d0000`, status
  `accepted_existing_manual_state`, blockers `already_recorded_in_manual_state`
  and `missing_command_candidate`, with mutation still read-only.
- Pandora blocked listing-state proof: selected `s0:000004E6:op1`, blockers
  `call before selected use may clobber A5`,
  `missing_accepted_path_lifetime_scope`, and `missing_command_candidate`.
- Focused tests:
  `test_a5_path_lifetime_packet_reports_existing_manual_state_without_mutation`
  and the blocked packet assertions in
  `test_a5_hardware_lifetime_report_marks_unknown_without_custom_definition`.
- Verification: focused 369-test pytest run and changed-file `ruff check` both
  passed.
- Reopen hardening: `a5-path-lifetime-packet` is now a supported CLI surface,
  covered by `test_packet_query_cli_commands_emit_json` and
  `test_query_a5_path_lifetime_packet_reports_command_candidate_as_read_only`.
  Packet-level `command_gate.enabled=false` and
  `command_gate.safe_to_mutate=false` for read-only packets even when a lower
  A5 report candidate has command support; availability is reported only as
  `candidate_command_available`.
- Pandora CLI proof after hardening:
  `uv run python -m amiga_reversing.reversing_loop a5-path-lifetime-packet --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8 --selected-use-id s0:0000045C:op0 --listing-timeout-seconds 10`
  returned `status=accepted_existing_manual_state`,
  `mutation_policy=read_only`, `command_gate.enabled=false`, and
  `command_gate.safe_to_mutate=false`.

## Reopen Findings

- `command_gate.enabled` and `command_gate.safe_to_mutate` must remain false for
  this read-only packet even if a lower-level command exists. A consumer must not
  be able to treat packet metadata as mutation authority.
- The packet query must be reachable through a supported CLI/API/report path and
  tested at that boundary, or the issue must explicitly justify private helper
  access as the completed surface.
