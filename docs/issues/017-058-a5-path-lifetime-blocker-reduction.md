# 017-058: A5 Path/Lifetime Blocker Reduction

Status: active
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

- [ ] Current A5 report rerun for Pandora.
- [ ] One narrow unknown-use family selected and justified.
- [ ] Representative selected use inspected through current packet/report surfaces.
- [ ] CFG reachability evidence checked.
- [ ] A5 clobber/lifetime evidence checked.
- [ ] Existing accepted A5 manual state compared to avoid duplicate work.
- [ ] No 012/018/Mac/platform-format files touched.

## Research Review

- [ ] Confirmed unknown uses remain blocked unless path/lifetime proof exists.
- [ ] Confirmed no command candidate was exposed.
- [ ] Confirmed no source, Manual Action Log, Decision Journal, verifier artifact, generated output, or target metadata was modified.
- [ ] Proposal 017 living notes updated with concise findings.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] Narrow A5 family selected.
- [ ] Blocker taxonomy recorded.
- [ ] Output remains read-only.
- [ ] Any support-code change is tied to a concrete packet/report correctness blocker.
- [ ] Focused tests pass if code changes.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.
