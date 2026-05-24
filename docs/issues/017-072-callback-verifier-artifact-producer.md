# 017-072: Callback Verifier Artifact Producer

Status: complete
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: verifier artifacts for callback-derived code facts.
- Current proposal state: `017-067` was superseded because verifier gates are helper-only; `decision-verifier-artifact` still supports only `rsset_app_base` and rejects callback facts.
- Desired proposal state after this issue: `decision-verifier-artifact` supports `callback_derived_code` decisions and enforces semantic reload, generated-source diff, negative safety, and exact round-trip layers.

## Protocol Delta

- Adds: verifier artifact producer support for callback-derived code facts.
- Changes: callback source-changing readiness uses real verifier artifacts.
- Replaces: helper-only `callback_verifier_gate`.
- Deletes: verifier bypasses or unused helper path if obsolete.
- Leaves out of scope: unrelated verifier refactors, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Unchanged, v2 internal only: callback decisions fail closed unless verifier layers pass.
- Switched surface to v2: `decision-verifier-artifact --decision-id <callback>` can produce no-write and write artifacts.
- Deleted old surface path: helper-only verifier bypass removed or private.
- User-visible behavior: verifier artifact shows pass/fail layers and blockers.

## Pandora Proof

- Target candidate: fixture accepted callback decision; Pandora if real accepted callback decision exists.
- Evidence packet expected: decision audit record, current packet/replay/render match, semantic reload, generated-source diff, negative safety, exact round-trip.
- Decision behavior: artifact producer rejects non-active/non-accepted/stale/mismatched decisions.
- Command gate behavior: source-changing callback command requires current passing artifact.
- Render effect: verified from normal source pipeline.
- Verifier/round-trip: mandatory.

## Implementation Slice

- C fact graph/query work: expose render/replay state needed by verifier.
- Python/API/report work: extend `produce_decision_verifier_artifact` beyond `rsset_app_base` for `callback_derived_code`.
- Journal/replay work: consume active callback decisions.
- Renderer/verifier work: implement semantic reload, generated-source, negative-safety, exact-round-trip checks for callback facts.
- Tests: no-write artifact, write artifact on temp target, stale/missing/failing layer blockers, unsupported fact remains rejected.

## Research Coverage

- [x] Existing RSSET verifier producer path traced for reuse.
- [x] Callback decision audit lookup implemented.
- [x] Callback render/source diff verifier implemented.
- [x] Negative safety checks neighboring ranges.
- [x] Exact round-trip integrated.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] `unsupported_decision_fact_type` no longer applies to valid callback facts.
- [x] Verifier gates are artifact/command-enforced, not helper-only.
- [x] Stale/missing/failing states fail closed.
- [x] Proposal 017 updated with implementation findings.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] `017-067` supersession addressed.
- [x] Code implemented in real verifier artifact producer.
- [x] Tests cover pass and fail-closed cases.
- [x] Exact round-trip passes where output changes.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Notes

- `decision-verifier-artifact` now accepts active `callback_derived_code` `accept_fact` records.
- The callback producer enforces current packet replay, selected identity match, normal effective-metadata generated-source diff, negative safety, and exact round-trip.
- Passing callback artifacts include semantic reload, generated source, negative safety, and exact round-trip layers.

## Completion Evidence

- Focused tests: `uv run python -m pytest tests\test_manual_seed_effective_metadata.py tests\test_reversing_loop.py tests\test_callback_slot_report.py -q` (`428 passed`).
- C backend coverage: `uv run python -m pytest tests\test_c_backend.py -q` (`198 passed, 15 skipped`).
- Required validation: `uv run python -m amiga_reversing.tools.validate_017_issues`.
- Whitespace check: `git diff --check`.
