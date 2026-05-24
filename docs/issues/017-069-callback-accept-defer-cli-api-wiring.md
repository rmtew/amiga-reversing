# 017-069: Callback Accept/Defer CLI/API Wiring

Status: complete
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: callback-derived code accept/defer command path.
- Current proposal state: `017-065` was superseded because it added helper functions but no real CLI/API path to dry-run or append callback accept/defer decisions.
- Desired proposal state after this issue: callback-derived code candidates can be accepted or deferred through a real `reversing_loop` command/API path with dry-run, append, validation, and fail-closed behavior.

## Protocol Delta

- Adds: real callback accept/defer CLI/API wiring.
- Changes: callback-derived decision records are no longer test-only helper output.
- Replaces: `017-065` helper-only closure.
- Deletes: any duplicate or unused helper path if superseded by the command API.
- Leaves out of scope: render output changes, verifier artifact production, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Unchanged, v2 internal only: source output does not change in this issue.
- Switched surface to v2: callback accept/defer decisions are created through the normal command/API surface.
- Deleted old surface path: stale helper-only bypasses must be removed or kept private with justification.
- User-visible behavior: a dry-run command is available; append/write mode is gated and explicit.

## Pandora Proof

- Target candidate: use fixture eligible callback packet first; use Pandora only for fail-closed evidence if current candidates do not pass packet/signal gates.
- Evidence packet expected: selected callback packet, action, dry-run record, validation result, and append eligibility.
- Decision behavior: `accept_fact` and `defer_fact` records validate through Decision Journal; append writes only in explicit write mode and only when gates pass.
- Command gate behavior: fail closed on missing packet, blocked signal, unknown/non-empty conflicts, zero-fill/data-like blockers, or stale selected identity.
- Render effect: none yet.
- Verifier/round-trip: no source-changing round-trip required.

## Implementation Slice

- C fact graph/query work: none unless selected identity/packet data must be exposed from core.
- Python/API/report work: add `reversing_loop` command/API for callback decision dry-run and append.
- Journal/replay work: use existing Decision Journal validation and append IO; do not hand-roll storage.
- Renderer/verifier work: none.
- Tests: command dry-run, append with temp target/journal, fail-closed cases, validation diagnostics, no write by default.

## Research Coverage

- [x] Existing callback packet helper usage traced.
- [x] CLI/API command added.
- [x] Dry-run mode implemented and tested.
- [x] Explicit append/write mode implemented and tested.
- [x] Fail-closed cases covered.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] Command is the supported path, not test-only helpers.
- [x] Decision Journal remains durable source of decisions.
- [x] No source output changes occur.
- [x] Proposal 017 updated with implementation findings.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] `017-065` supersession addressed.
- [x] Code implemented and command/API path exists.
- [x] Tests cover dry-run, append, and fail-closed cases.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Notes

- Added `reversing_loop callback-decision` plus `decide_callback_code(...)`.
- Dry-run validates the exact Decision Journal record and writes nothing.
- `--write` appends only after the current packet, generated callback orphan-code signal, selected identity, and empty-conflict gates pass.
- Blocked packet/signal cases fail closed and do not write Manual Action Log or target metadata.

## Completion Evidence

- Focused tests: `uv run python -m pytest tests\test_reversing_loop.py tests\test_callback_slot_report.py -q` (`385 passed`).
- Required validation: `uv run python -m amiga_reversing.tools.validate_017_issues`.
- Whitespace check: `git diff --check`.
