# 017-086: Wire A5 Hardware Decisions Into Replay

Status: completed
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Dependency: `017-085` must be complete first.
- Protocol area: accepting or deferring A5 hardware-reference command candidates through the normal Decision Journal path.
- Current proposal state: A5 has accepted evidence but no command-backed decision path.
- Desired proposal state after this issue: an accepted A5 hardware-reference decision replays into effective metadata, and deferred/rejected decisions remain visible and non-mutating.

## Protocol Delta

- Adds: A5 hardware-reference accept/defer/reject command handling and replay.
- Changes: effective metadata can carry accepted A5 hardware-reference facts.
- Replaces: report-only A5 accepted-use evidence that cannot affect downstream rendering.
- Leaves out of scope: final source rendering, verifier artifact writing, target metadata mutation, 012/018, Mac OS support, and Mac targets.

## Default Behavior

- Decision append must require a current `017-085` command candidate.
- Accepted decisions must include explicit empty conflicts and parent evidence ids.
- Replay must fail closed if target identity, row key, operand index, register, displacement, or parent evidence no longer matches.
- Deferred/rejected decisions must be visible in the report but must not affect effective metadata.

## Pandora Proof

- Target: `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.
- Use one `017-085` A5 command candidate as the tracer-bullet candidate.
- Expected result: dry-run accept/defer/reject behavior is demonstrable, and accepted replay appears in effective metadata without source output mutation.

## Implementation Slice

- C fact graph/query work: consume replayed A5 metadata only if the C-owned pipeline needs a schema-visible field.
- Python/API/report work: add command API and report state for accepted/deferred/rejected A5 decisions.
- Journal/replay work: add durable Decision Journal schema support and replay into effective metadata.
- Renderer/verifier work: unchanged except metadata availability for later rendering.
- Tests: append gating, dry-run behavior, stale identity fail-closed, accepted replay, deferred/rejected non-replay.

## Research Coverage

- [x] `017-085` candidate structure checked.
- [x] Existing callback/RSSET decision patterns reviewed and reused where appropriate.
- [x] Stale candidate identity failure cases covered.
- [x] Accepted, deferred, and rejected decision paths covered.
- [x] No target metadata or generated source output written by this issue.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] This creates an implemented mutation path, not another evidence summary.
- [x] Accepted A5 facts become effective metadata through the normal replay path.
- [x] Deferred/rejected facts stay report-visible and source-inert.
- [x] Proposal 017 living notes updated with the implementation result.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] `017-085` complete.
- [x] Focused A5 Decision Journal tests pass.
- [x] Real Pandora dry-run accept/defer/reject behavior demonstrated.
- [x] Effective metadata replay test passes.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

- `a5-decision` dry-run accepts the real Pandora candidate `a5-custom-cfg:h0:00000498->000004A6:op1:d0096` with explicit empty conflicts and stable selected identity.
- Focused tests passed for A5 Decision Journal append/dry-run/stale identity and `tests/test_manual_seed_effective_metadata.py -q -k a5`.
