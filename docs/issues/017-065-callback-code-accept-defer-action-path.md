# 017-065: Callback Code Accept/Defer Action Path

Status: superseded
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

Superseded by: `017-069-callback-accept-defer-cli-api-wiring.md` and
`017-070-callback-accepted-fact-replay-into-analysis.md`.
Reason: post-commit review found this issue was closed with helper functions
only. There is no real CLI/API accept/defer path and no normal replay wiring.

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: callback-derived code decision actions.
- Current proposal state: callback-derived candidates cannot be accepted or deferred through the Decision Journal/replay protocol.
- Desired proposal state after this issue: callback-derived code candidates have scoped accept/defer actions backed by Decision Journal records and replay into analysis state.

## Protocol Delta

- Adds: accept/defer action support for callback-derived code candidates.
- Changes: eligible callback review candidates can produce replayable decisions.
- Replaces: any callback-specific non-journal state for this lane.
- Deletes: obsolete duplicate command path if one is found.
- Leaves out of scope: broad automatic acceptance, ungated source mutation, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Unchanged, v2 internal only: no source-changing action without accepted evidence and verifier gates.
- Switched surface to v2: callback code decisions use Decision Journal records.
- Deleted old surface path: any replaced non-journal callback decision path must be removed or explicitly blocked.
- User-visible behavior: accept/defer command becomes available only for eligible callback-derived review candidates.

## Pandora Proof

- Target candidate: use a safe fixture candidate first; use Pandora only if 017-064 produced an eligible non-false-positive candidate.
- Evidence packet expected: selected identity, generated callback signal, conflicts, blockers, accept/defer payload, and replay result.
- Decision behavior: accept writes accepted fact only when gates pass; defer writes scoped defer reason; rejected/unsafe candidates fail closed.
- Command gate behavior: command refuses missing packet, missing signal, non-empty/unknown conflicts, zero-fill/data-like blockers, and missing verifier readiness.
- Render effect: accepted fact may affect analysis state, but rendered source change may wait for 017-066.
- Verifier/round-trip: command/replay tests required; exact round-trip required if source output changes.

## Implementation Slice

- C fact graph/query work: replay accepted callback code facts into analysis state/fact graph.
- Python/API/report work: add command/API path for accept/defer with dry-run and explicit write behavior.
- Journal/replay work: add Decision Journal fact type/action validation and replay projection.
- Renderer/verifier work: no final render required yet unless already supported safely.
- Tests: journal validation, dry-run, append, replay, fail-closed cases, and no duplicate decision identity.

## Research Coverage

- [x] Decision fact schema defined for callback-derived code classification.
- [x] Accept/defer command dry-run implemented.
- [x] Journal append implemented only behind gates.
- [x] Replay projection implemented.
- [x] Fail-closed cases covered.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] Accepted facts require selected identity and explicit conflict state.
- [x] Defer records preserve reason and selected scope.
- [x] Replay is deterministic after semantic reload.
- [x] No unsafe Pandora mutation occurred.
- [x] Proposal 017 updated with implementation findings.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] Code implemented, not only documentation.
- [x] Decision Journal is durable source of decisions.
- [x] Replay feeds analysis state instead of report-only state.
- [x] Focused tests pass.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

- Added `callback_decision_record`, `callback_decision_lane`, and `analysis_with_accepted_callback_code`.
- Decision Journal validation covers accept/defer records with selected identity, conflicts, and scoped replay.
- Pandora remained read-only because no real callback orphan-code signal passed gates.
