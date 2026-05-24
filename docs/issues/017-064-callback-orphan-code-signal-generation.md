# 017-064: Callback Orphan-Code Signal Generation

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: callback-derived orphan/code signal generation.
- Current proposal state: callback target rows can be reported, but callback evidence does not generate `orphan_code_signal` data or reviewable orphan/code candidates.
- Desired proposal state after this issue: eligible callback targets generate reviewable orphan/code signals, while zero-fill/data-like/ambiguous targets fail closed with explicit blockers.

## Protocol Delta

- Adds: callback-derived orphan/code signal generation.
- Changes: callback target evidence can feed review-item generation when evidence passes false-positive checks.
- Replaces: dead-end callback target rows that cannot become review candidates.
- Deletes: no old path unless proven redundant.
- Leaves out of scope: accepting code facts, source rendering, final mutation, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Unchanged, v2 internal only: unsafe callback targets remain blocked.
- Switched surface to v2: review-item generation may consume callback-derived orphan/code signals.
- Deleted old surface path: none unless replaced by tested signal generation.
- User-visible behavior: new reviewable candidates may appear only when evidence passes implemented guards.

## Pandora Proof

- Target candidates: existing Pandora callback target rows from 017-056 through 017-062.
- Evidence packet expected: generated signal or explicit no-signal reason for each representative candidate.
- Decision behavior: none; review candidates are not accepted facts.
- Command gate behavior: any callback seed/review command must remain gated by generated review item plus later verifier requirements.
- Render effect: none.
- Verifier/round-trip: no source-changing verification required unless behavior changes generated output.

## Implementation Slice

- C fact graph/query work: implement callback-derived signal facts or equivalent core analysis records where signal semantics belong.
- Python/API/report work: expose generated signal state and no-signal reasons through existing callback/review APIs.
- Journal/replay work: none.
- Renderer/verifier work: none.
- Tests: fixtures must prove an eligible callback target becomes reviewable, zero-fill targets stay blocked, data-like targets stay blocked, and current Pandora targets do not become unsafe code seeds.

## Research Coverage

- [ ] Signal inputs from 017-063 packet support consumed.
- [ ] False-positive guards implemented for zero-fill/data-like rows.
- [ ] Review-item generation connected to callback-derived signals.
- [ ] Pandora current candidates evaluated through the new signal path.
- [ ] Fixture proves at least one eligible callback target generates a review item.
- [ ] No 012/018/Mac/platform-format files touched.

## Research Review

- [ ] Generated signals are durable structured data, not report-only prose.
- [ ] Unsafe Pandora targets remain blocked with explicit reasons.
- [ ] Eligible fixture target becomes reviewable.
- [ ] No source, Manual Action Log, Decision Journal, verifier artifact, generated output, or target metadata was modified unless tests require fixture output.
- [ ] Proposal 017 updated with implementation findings.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] Code implemented, not only documentation.
- [ ] Signal semantics live in core analysis where appropriate.
- [ ] Python remains wrapper/orchestration for this core behavior.
- [ ] Focused tests prove eligible and rejected cases.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.
