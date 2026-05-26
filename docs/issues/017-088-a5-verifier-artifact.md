# 017-088: Add A5 Hardware Reference Verifier Artifact

Status: completed
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Dependency: `017-087` must be complete first.
- Protocol area: verifier-backed safety for A5 hardware-reference source changes.
- Current proposal state: accepted A5 facts can render only after `017-087`, but the verifier artifact must prove semantic reload, source effect, negative safety, and exact round-trip.
- Desired proposal state after this issue: A5 decisions have a no-write and write-capable verifier artifact path equivalent in rigor to callback and RSSET.

## Protocol Delta

- Adds: A5 hardware-reference decision verifier artifact production.
- Changes: A5 render changes are not considered complete until verifier layers pass.
- Replaces: ad hoc inspection of A5 source diffs.
- Leaves out of scope: generating new command candidates, accepting new facts, unrelated verifier refactors, 012/018, Mac OS support, and Mac targets.

## Default Behavior

- No-write verification must be available and must not mutate files.
- Write mode must be gated on all verifier layers passing.
- Artifact layers must include semantic reload, generated-source effect, negative safety, and exact round-trip.
- Failed or stale A5 decisions must produce actionable blockers, not partial artifacts.

## Pandora Proof

- Target: `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.
- Use the same tracer-bullet A5 decision from `017-086` and rendering from `017-087`.
- Expected result: no-write verifier passes all required layers for the accepted A5 fact, or fails closed with a precise implementation blocker.

## Implementation Slice

- C fact graph/query work: expose semantic reload state needed to prove the accepted A5 fact is active.
- Python/API/report work: add A5 decision verifier artifact support.
- Journal/replay work: verify replayed accepted facts only.
- Renderer/verifier work: compare baseline and accepted-render source, check negative safety, and require exact round-trip.
- Tests: passing artifact, stale decision failure, negative-safety failure, no-write behavior, write-gated behavior.

## Research Coverage

- [x] Callback and RSSET verifier artifact patterns reviewed.
- [x] Semantic reload proves the accepted A5 fact exists in effective metadata.
- [x] Generated-source layer proves the intended narrow source effect.
- [x] Negative-safety layer proves unrelated A5 uses did not change.
- [x] Exact round-trip is required for any output-affecting mutation.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] This makes A5 rendering verifier-backed, not manually eyeballed.
- [x] The verifier fails closed on stale identity and broad source diffs.
- [x] Artifact write mode is gated by passing layers.
- [x] Proposal 017 living notes updated with the implementation result.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] `017-087` complete.
- [x] Focused verifier tests pass.
- [x] Real Pandora no-write verifier passes or reports a precise blocker.
- [x] Exact round-trip check included.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

- Added A5 decision verifier artifact coverage for pass/write, current no-write, stale row identity, negative-safety failure, and exact-round-trip write gating.
- Real Pandora verifier artifact for `decision-a5-dmacon-000004a6-accept-017-089` passes semantic reload, generated source, negative safety, and exact round-trip.
