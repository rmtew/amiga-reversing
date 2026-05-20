Status: implemented
Type: AFK
Source proposal: docs/proposals/017-pandora-post-hardening-reversal.md
Promoted from: post-017-020 Pandora queue review

Scope:
Make `a5-hardware-report` suppress command candidates that are already present
in durable manual A5 hardware-ref state.

Problem:
After 017-019 exhausted the render-safe A5 family, `a5-hardware-report` still
reported top-level `safe_to_mutate=true` and 19 command candidates. Those
candidates were already recorded in `manual_state.a5_hardware_refs`, so the
report could invite duplicate mutations instead of showing that the safe A5
queue was exhausted.

Required work:
- Load existing A5 hardware refs for the target when building the report.
- Keep accepted path/lifetime evidence visible.
- Remove command/verifier payloads from uses whose source evidence is already
  recorded.
- Recompute A5 rendering gate and top-level `safe_to_mutate` after suppression.
- Keep command/verifier support reported as available; the blocked gate is the
  absence of a fresh command candidate, not missing tooling.

Acceptance:
- Fresh accepted A5 evidence still exposes `a5_hardware_ref.interpret`.
- Existing manual A5 refs remain visible as existing state, not command
  candidates.
- Pandora reports zero remaining A5 command candidates after the sweep.

Result:
- `a5-hardware-report` now marks already-recorded refs with
  `existing_manual_state`, removes their command payloads, and recomputes the
  gate from remaining unrecorded candidates.
