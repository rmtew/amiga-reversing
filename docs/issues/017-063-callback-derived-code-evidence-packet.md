# 017-063: Callback-Derived Code Evidence Packet

Status: implemented
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: callback-derived code evidence.
- Current proposal state: callback evidence is visible in reports, but it is not a first-class evidence packet that can carry selected identity, target bytes, classification, blockers, conflicts, false-positive checks, and verifier readiness through the 017 protocol.
- Desired proposal state after this issue: callback target evidence is available as a structured protocol packet, implemented in the core analysis layer where facts/classification belong, with Python only wrapping/orchestrating/reporting.

## Protocol Delta

- Adds: callback-derived code evidence packet support for exact callback target candidates.
- Changes: callback evidence becomes protocol packet data, not just report prose.
- Replaces: ad hoc callback row descriptions for this lane.
- Deletes: nothing unless old duplicate formatting becomes unused.
- Leaves out of scope: accepting facts, rendering source changes, mutation commands, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Unchanged, v2 internal only: existing callback report output must stay compatible unless deliberately extended.
- Switched surface to v2: callback candidate evidence packet lookup for selected callback target candidates.
- Deleted old surface path: none in this issue.
- User-visible behavior: new read/inspect packet output is allowed; source-changing commands are not.

## Pandora Proof

- Target candidates: callback targets from 017-056 through 017-062, including `s0:0004D5DE`, `s0:00000B28`, `s0:0000076E`, and `s0:00000AC8`.
- Evidence packet expected: callback slot, store site, stored value source, selected target row, target bytes, current row/range classification, xrefs, inbound control-flow evidence if any, false-positive checks, blockers, conflicts, and verifier/render readiness state.
- Decision behavior: none yet; packet is evidence input only.
- Command gate behavior: no accept or seed command is enabled by this issue.
- Render effect: none.
- Verifier/round-trip: packet generation must be tested; no round-trip required unless output-affecting behavior changes.

## Implementation Slice

- C fact graph/query work: add or extend core callback target evidence extraction/classification data so packet semantics do not live only in Python strings.
- Python/API/report work: expose the packet through CLI/API, using Python as wrapper/transport and formatting layer.
- Journal/replay work: none.
- Renderer/verifier work: none.
- Tests: unit/integration tests proving packet fields for Pandora and a small fixture; tests must prove zero-fill/data-like targets carry blockers instead of actionability.

## Research Coverage

- [x] Existing callback report and review-item generation surfaces traced.
- [x] Core ownership boundary chosen and documented.
- [x] Packet schema implemented with stable selected identity.
- [x] Pandora packets generated for representative callback targets.
- [x] Fixture covers an eligible-looking callback target and a zero-fill/data-like target.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] Packet shape matches Proposal 017 protocol primitives.
- [x] Core classification is not implemented only as Python prose formatting.
- [x] Existing callback report behavior remains sane.
- [x] No source, Manual Action Log, Decision Journal, verifier artifact, generated output, or target metadata was modified.
- [x] Proposal 017 updated with implementation findings.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] Code implemented, not only documentation.
- [x] C/core ownership used for fact/classification semantics where appropriate.
- [x] Python remains wrapper/orchestration for this core behavior.
- [x] Tests cover positive packet shape and fail-closed blockers.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

- Implemented callback-derived evidence packets in `amiga_reversing.disasm.callback_slot_report`.
- C/export ownership updated with `M68K_ORPHAN_CODE_SIGNAL_CALLBACK_SLOT` and JSON/manifest name mapping.
- Focused tests: `tests/test_callback_slot_report.py`, `tests/test_manual_review_items.py`, `tests/test_decision_journal.py`, `tests/test_target_usage_manifest.py`.
- Pandora derived target `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8` generated packets; current real candidates remain blocked.
