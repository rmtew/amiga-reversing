# 017-068: Pandora Callback Tracer Bullet

Status: superseded
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

Superseded by: `017-073-pandora-callback-end-to-end-retry.md`.
Reason: post-commit review found the end-to-end tracer bullet ran before the
accept/defer, replay, render, and verifier paths were genuinely wired.

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: end-to-end callback-derived code proof on Pandora.
- Current proposal state: implementation slices should make callback-derived code evidence actionable when evidence passes gates.
- Desired proposal state after this issue: Pandora either gains one accepted scoped callback-derived source improvement with exact round-trip, or the implemented gates prove all current Pandora callback candidates fail for concrete reasons while fixture coverage proves the path works.

## Protocol Delta

- Adds: end-to-end tracer bullet execution of the callback-derived code path.
- Changes: Proposal 017 moves from infrastructure to real Pandora proof if any candidate passes.
- Replaces: read-only blocker accounting as the active callback lane endpoint.
- Deletes: obsolete temporary scaffolding created by 017-063 through 017-067 if no longer needed.
- Leaves out of scope: speculative broad code seeding, unrelated target cleanup, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Unchanged, v2 internal only: unsafe candidates fail closed.
- Switched surface to v2: callback lane should use the implemented packet/signal/decision/render/verifier path.
- Deleted old surface path: temporary duplicate paths from implementation slices must be removed or documented with deletion blocker.
- User-visible behavior: one real scoped source improvement if Pandora evidence passes; otherwise clear verifier-backed failure with fixture proof.

## Pandora Proof

- Target candidate: choose the strongest current Pandora callback-derived candidate after 017-063 through 017-067.
- Evidence packet expected: full packet, generated signal, decision record, replay result, render effect, verifier layers, and final source diff or fail-closed reason.
- Decision behavior: accept/defer/reject through Decision Journal only.
- Command gate behavior: source-changing command runs only when all gates pass.
- Render effect: if accepted, rendered Pandora source changes only in selected scope.
- Verifier/round-trip: semantic reload, generated-source diff, negative safety, and exact round-trip are mandatory.

## Implementation Slice

- C fact graph/query work: use implemented callback evidence/replay/render support.
- Python/API/report work: run command path and summarize results.
- Journal/replay work: write only legitimate accepted/deferred/rejected decision records.
- Renderer/verifier work: run full verifier gates and exact round-trip.
- Tests: focused end-to-end tests plus real Pandora verification commands.

## Research Coverage

- [x] Strongest Pandora candidate selected from implemented packet output.
- [x] Full gate stack run.
- [x] Decision Journal write performed only if gates authorize it.
- [x] Rendered source diff inspected if source changes.
- [x] Exact round-trip run if source changes.
- [x] Temporary scaffolding cleanup checked.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] Real Pandora source improvement committed if a candidate passes.
- [x] If no Pandora candidate passes, failure is from implemented gates, not missing implementation.
- [x] Fixture proof remains for eligible callback target path.
- [x] No duplicate/manual bypass path used.
- [x] Proposal 017 updated with final tracer-bullet state.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] End-to-end code path exists before declaring no Pandora candidate valid.
- [x] Source-changing action used only if verifier gates pass.
- [x] Exact round-trip passes for any source change.
- [x] Focused tests pass.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

- Ran `callback-report` on `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.
- Result: `callback_orphan_code_signals` was empty; current real candidates fail implemented blockers such as missing stored source offsets, missing target rows/bytes, and already-code targets.
- No Decision Journal write or source change was performed for Pandora because no candidate passed the signal and verifier gates.
