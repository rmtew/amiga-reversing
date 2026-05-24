# 017-058: A5 Path/Lifetime Blocker Reduction

Status: completed
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: A5 path/lifetime evidence.
- Current proposal state: A5 discovery reports 20 already accepted custom-base uses and 505 path-proof-blocked unknown uses, with no command candidate.
- Desired proposal state after this issue: a narrow unknown-use family is classified into precise blocker reasons, reducing the ambiguity of the A5 path/lifetime backlog without exposing mutation.

## Protocol Delta

- Adds: a read-only blocker taxonomy for a selected narrow family of unknown A5 uses.
- Changes: proposal living notes with the selected family, count, representative candidate, and exact blocker pattern.
- Replaces: no existing protocol model.
- Deletes: nothing.
- Leaves out of scope: mutation, source edits, Manual Action Log writes, Decision Journal writes, verifier artifact writes, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Unchanged, v2 internal only: A5 path/lifetime packet and report surfaces stay read-only for unknown uses.
- Switched surface to v2: none.
- Deleted old surface path: none.
- User-visible behavior: no new A5 command candidate may be exposed by this issue.

## Pandora Proof

- Target candidate: choose one narrow family from current A5 unknown-use output, preferably the highest-value family with repeated blocker shape.
- Evidence packet expected: selected use identity, current A5 base evidence, CFG reachability state, clobber/lifetime state, accepted existing manual-state comparison, conflicts, blocker reason, and why mutation is not safe.
- Decision behavior: no accept decision; record blocker/defer classification only.
- Command gate behavior: no A5 hardware/base mutation command may become enabled.
- Render effect: none.
- Verifier/round-trip: no output-affecting verification unless support code changes.

## Implementation Slice

- C fact graph/query work: none unless current path/lifetime query omits a necessary read-only blocker reason.
- Python/API/report work: inspect `a5-hardware-report` and `a5-path-lifetime-packet`; add narrow read-only blocker classification only if needed.
- Journal/replay work: inspect existing deferred lane if relevant; do not append.
- Renderer/verifier work: none.
- Tests: focused packet/report tests if output shape changes; otherwise document report outputs.

## Research Coverage

- [x] Current A5 report rerun for Pandora.
- [x] One narrow unknown-use family selected and justified.
- [x] Representative selected use inspected through current packet/report surfaces.
- [x] CFG reachability evidence checked.
- [x] A5 clobber/lifetime evidence checked.
- [x] Existing accepted A5 manual state compared to avoid duplicate work.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] Confirmed unknown uses remain blocked unless path/lifetime proof exists.
- [x] Confirmed no command candidate was exposed.
- [x] Confirmed no source, Manual Action Log, Decision Journal, verifier artifact, generated output, or target metadata was modified.
- [x] Proposal 017 living notes updated with concise findings.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] Narrow A5 family selected.
- [x] Blocker taxonomy recorded.
- [x] Output remains read-only.
- [x] Any support-code change is tied to a concrete packet/report correctness blocker.
- [x] Focused tests pass if code changes.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

Pandora target:
`amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.

Read-only commands rerun:

- `uv run python -m amiga_reversing.reversing_loop a5-hardware-report --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`
- `uv run python -m amiga_reversing.reversing_loop a5-path-lifetime-packet --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8 --selected-use-id s0:00006C96:op0`
- `uv run python -m amiga_reversing.reversing_loop decision-journal-report --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`

Current A5 report summary:

- 525 CFG path/lifetime uses.
- 20 `accepted_custom_base` uses, all already represented by existing manual
  state.
- 505 `unknown` uses remain path-proof-blocked.
- Rendering gate remains blocked by `command_candidate`;
  `a5_hardware_ref.interpret` has no command candidates.

Selected narrow family:

- Family: A5 base definition at `s0:00006C68:instruction:4379`.
- Count: 165 unknown uses, the largest repeated unknown-use family in the
  current report.
- Repeated blocker shape: `branch before selected use requires full CFG path
  proof`.
- Representative packet: `a5-path-lifetime-packet:s0:00006C96:op0`.
- Candidate id: `a5-custom-cfg:h0:00006C68->00006C96:op0:d001E`.

Representative selected use:

- Selected identity: `s0:00006C96:op0`, hunk 0, addr 27798,
  operand index 0.
- Base setup: A5 computed as `_custom` at
  `s0:00006C68:instruction:4379`.
- Custom delta: displacement 30 / hardware register offset 30.
- Existing manual state: none.
- Decision lane: unavailable, with `missing_active_accepted_decision`.

Blocker taxonomy:

- CFG reachability is `unproven` because a branch occurs before the selected
  use and the current proof is only conservative straight-line CFG.
- A5 clobber before use is `unknown`; there is no accepted path/lifetime scope
  covering the selected use.
- Conflicts are unknown, not explicit empty.
- Command candidate is missing, so no new `a5_hardware_ref.interpret` mutation
  is exposed.
- Generated-source verifier is blocked and exact round-trip remains only a
  required future gate for any output-affecting mutation.

The selected family reduces the 505-use backlog to a concrete repeated blocker:
prove full CFG path reachability/lifetime across a branch before considering
any A5 command candidate. This issue exposes no mutation surface.

No code changed, so no focused tests were required beyond issue validation and
diff checks.
