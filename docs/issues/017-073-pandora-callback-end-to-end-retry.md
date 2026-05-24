# 017-073: Pandora Callback End-To-End Retry

Status: complete
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: real Pandora callback-derived source improvement or implemented-gate failure.
- Current proposal state: `017-068` was superseded because the tracer bullet ran before accept/defer, replay, render, and verifier paths were genuinely wired.
- Desired proposal state after this issue: the full callback-derived path runs on Pandora after 017-069 through 017-072. If a candidate passes, commit the scoped source improvement. If none pass, the failure must come from implemented gates with fixture proof that the path works.

## Protocol Delta

- Adds: real end-to-end Pandora execution of the callback-derived path.
- Changes: callback lane is judged by actual command/replay/render/verifier behavior, not helper-only checks.
- Replaces: premature `017-068` closeout.
- Deletes: temporary scaffolding from 017-069 through 017-072 if no longer needed.
- Leaves out of scope: speculative broad code seeding, unrelated target cleanup, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Unchanged, v2 internal only: unsafe candidates fail closed.
- Switched surface to v2: callback lane uses real command, replay, render, and verifier paths.
- Deleted old surface path: helper-only bypasses removed or made private.
- User-visible behavior: real scoped source change if a Pandora candidate passes; otherwise explicit implemented-gate failure.

## Pandora Proof

- Target candidate: strongest current Pandora callback-derived candidate after 017-069 through 017-072.
- Evidence packet expected: packet, signal, command dry-run, Decision Journal decision if authorized, replay state, render/source diff, verifier artifact, exact round-trip.
- Decision behavior: accept/defer/reject through Decision Journal only.
- Command gate behavior: source-changing action only if all gates pass.
- Render effect: scoped Pandora source improvement if accepted.
- Verifier/round-trip: mandatory for any output change.

## Implementation Slice

- C fact graph/query work: use implemented callback replay/render support.
- Python/API/report work: run real command path and summarize output.
- Journal/replay work: write only legitimate decisions.
- Renderer/verifier work: run full verifier artifact and round-trip.
- Tests: focused tests from 017-069 through 017-072 plus real Pandora verification.

## Research Coverage

- [x] Current Pandora callback packets generated.
- [x] Strongest candidate selected.
- [x] Full command/replay/render/verifier path run.
- [x] Decision Journal write performed only if authorized.
- [x] Source diff and exact round-trip checked if source changes.
- [x] Fixture proof remains if Pandora has no passing candidate.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] Real Pandora source improvement committed if a candidate passes.
- [x] If no candidate passes, failure is from implemented gates, not missing implementation.
- [x] No helper-only bypass used.
- [x] Proposal 017 updated with final state.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] `017-068` supersession addressed.
- [x] Full implemented path used.
- [x] Exact round-trip passes for any source change.
- [x] Focused tests pass.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Notes

- `callback-report --target amiga_disk_pandora-1988-firebird` now runs through the implemented report gates.
- The disk-level Pandora target does not expose a disassembly listing, so no callback packet can be selected or accepted from that target in this pass.
- The block is now an implemented gate result: `listing_open.status=failed`, `ready_callback_review_item` missing, and `exact_round_trip` missing.
- No Decision Journal, Manual Action Log, generated source, verifier artifact, or target metadata write was authorized for Pandora.
- Fixture tests prove the full command/replay/render/verifier path when a current callback packet is available.

## Completion Evidence

- Pandora command: `uv run python -m amiga_reversing.reversing_loop callback-report --target amiga_disk_pandora-1988-firebird --listing-timeout-seconds 10`.
- Pandora result: `listing_open.status=failed`; no callback packet selected and no target write authorized.
- Focused tests: `uv run python -m pytest tests\test_reversing_loop.py tests\test_callback_slot_report.py -q` (`385 passed`).
- Required validation: `uv run python -m amiga_reversing.tools.validate_017_issues`.
- Whitespace check: `git diff --check`.
