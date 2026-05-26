# 017-104: Callback Inherited Register Context

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Current 017 priority: base/context cascades.
- The Pandora regression row calls through a function pointer immediately before
  using `A5`:

```asm
	movea.l app_0364(a6),a0
	jsr (a0)
	move.w #$20,$009C(a5)
```

- The analysis must decide whether callback/function-pointer paths preserve,
  clobber, or inherit base-register context. It must not guess.

## Protocol Delta

- Adds: inherited register-context evidence for indirect calls/callbacks.
- Changes: callback packets can feed base/context cascade rules when proven.
- Replaces: treating function-pointer calls only as opaque blockers.
- Leaves out of scope: speculative code promotion and target mutation without
  verifier-backed source deltas.

## Default Behavior

- Unknown indirect calls are clobber boundaries unless evidence proves
  otherwise.
- Inherited context must carry provenance from caller setup, slot assignment,
  call site, and clobber analysis.
- Ambiguous function-pointer targets remain blocked.
- No callback-derived source mutation is allowed without baseline-delta,
  negative-safety, fixed-point, and exact-round-trip proof.
- The work must improve callback/register-context analysis. Merely reporting
  "unknown callback context" is not sufficient completion.

## What To Build

Extend callback/function-pointer evidence so inherited register context can be
proven, propagated, or blocked. When a callback target or indirect callee is
known to execute under a caller-established base register, the derived entry
context should participate in the same base/context cascade model.

## Acceptance Criteria

- [ ] Callback packets include live base-register context at the indirect call
      site when current facts can prove it.
- [ ] Callback target facts can inherit `A5 = _custom` only when definition,
      call path, and clobber evidence are sufficient.
- [ ] Unknown function-pointer target, ambiguous slot assignment, or possible
      clobber produces a blocker such as `callback_register_context_unproven`.
- [ ] The `app_0364(a6)` Pandora site is classified as proven, ambiguous, or
      blocked with a concrete reason.
- [ ] If the `app_0364(a6)` site remains blocked, at least one missing analysis
      foundation needed to resolve it is implemented, unless the binary proves a
      genuine contradiction or unresolvable ambiguity.
- [ ] Inherited callback context can enqueue child hardware-register analysis
      when safe.
- [ ] Focused tests cover direct known callback, slot-loaded callback,
      ambiguous slot, clobbered register, and missing target cases.
- [ ] No callback-derived source mutation occurs without verifier-backed delta,
      negative safety, and exact round-trip.
- [ ] Proposal 017 living notes are updated.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

## Blocked By

- docs/issues/017-103-a5-hardware-child-cascade-rendering.md

## Research Coverage

- [ ] Current callback report packet shape inspected.
- [ ] `app_0364(a6)` assignment/consumer evidence checked.
- [ ] Current clobber and register-lifetime data checked.
- [ ] Prior callback closeout notes in Proposal 017 checked.

## Research Review

- [ ] Proven, ambiguous, and blocked callback context states are distinct.
- [ ] Unknown indirect calls do not silently preserve A5.
- [ ] Inherited context can enqueue hardware-register child analysis only when
      evidence is sufficient.

## Required Sign-Off

- [ ] Proposal 017 checked before work.
- [ ] Dependency issue evidence checked before work.
- [ ] Callback/register-context analysis was extended beyond current reporting.
- [ ] Focused callback context tests pass.
- [ ] Real Pandora `app_0364(a6)` classification captured.
- [ ] Exact round-trip passes for any source change.
- [ ] Proposal 017 living notes updated.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

## Out Of Scope

- Promoting data rows to code without existing callback code evidence.
- Reopening completed callback target classification work unless this issue
  needs its data as input.

## Anti-Bypass Rule

Do not close this issue by restating prior callback closeout results. The issue
exists because callback context must participate in base/context cascades. If a
current helper cannot answer the question, extend the analysis model or create a
concrete implementation follow-up that does.
