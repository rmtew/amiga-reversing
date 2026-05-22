# 017-044: Orphan/Code-Island Evidence Packet

Status: completed

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

- [x] Existing orphan/code/data review reports checked.
- [x] C range classification sources checked.
- [x] Xref and control-flow reachability sources checked.
- [x] Overlap detection sources checked.
- [x] Command, renderer, verifier, and exact round-trip gates checked.
- [x] Default auto-analysis behavior checked for hidden assumptions.

## Research Review

- [x] Second pass checked trace blocks against named files/functions.
- [x] Cross-references searched for missed review-item hooks.
- [x] Hidden speculative classification risk reviewed.
- [x] Proposal updated with model corrections or deferred follow-ups.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Protocol delta implemented as described, or proposal updated.
- [x] Default behavior impact verified.
- [x] Old code deleted, or deferred deletion blocker recorded.
- [x] Evidence packet shape tested.
- [x] Decision/replay behavior tested where applicable.
- [x] Mutation stayed blocked unless every safe gate was proven.
- [x] Public CLI/API/report access to the packet is wired and tested, or the
  issue records why private helper access is intentionally sufficient.
- [x] Pandora proof recorded.
- [x] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

- Added read-only `orphan_code_island_evidence_packet` assembly over manual
  review candidates and listing-backed data-symbol candidates. It exposes range
  identity, xref/control-flow lane, overlap blocker, decoded/range evidence,
  render effects, conflicts, safe next actions, and mutation blockers.
- Pandora proof selected real listing data-range candidate
  `data-class-symbol:s0:000010F3:data:1111:0:000010F3:string_000210F3`:
  family `ambiguous_data_range`, range `s0:$000010F3-$00001113`,
  classification `string`, blockers `missing_direct_xref_evidence` and
  `missing_exact_round_trip_gate`, safe next action `data_symbol.rename`
  blocked, and `safe_to_mutate=false`.
- Focused test:
  `test_orphan_code_island_packet_exposes_range_evidence_and_blockers`.
- Verification: focused 369-test pytest run and changed-file `ruff check` both
  passed.
- Reopen hardening: `orphan-code-island-packet` is now a supported CLI surface,
  covered by `test_packet_query_cli_commands_emit_json` and
  `test_query_orphan_code_island_packet_uses_inspect_listing_surface`.
- Pandora CLI proof after hardening:
  `uv run python -m amiga_reversing.reversing_loop orphan-code-island-packet --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8 --candidate-id data-class-symbol:s0:000010F3:data:1111:0:000010F3:string_000210F3`
  returned the real `ambiguous_data_range` packet with `status=blocked`,
  `mutation_policy=read_only`, blocked safe next action `data_symbol.rename`,
  and `safe_to_mutate=false`.

## Reopen Findings

- The packet query must be reachable through a supported CLI/API/report path and
  tested at that boundary, or the issue must explicitly justify private helper
  access as the completed surface.
