# 017-102: Base Register Lifetime Parent Facts

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Current 017 priority: base/context cascades.
- `017-101` supplies the Pandora regression packet.
- The selected-row A5 model is insufficient. A durable parent fact must describe
  a bounded base-register lifetime, not one operand.

## Protocol Delta

- Adds: base-register lifetime as a parent fact.
- Changes: A5 custom-base evidence becomes scoped lifetime evidence.
- Replaces: selected-row-only A5 operand decisions for lifetime facts.
- Leaves out of scope: rendering child facts and platform-specific Atari/Mac
  implementation.

## Default Behavior

- Prefer C-owned fact graph data where the existing framework has an equivalent
  Amiga/Atari path in C.
- Python may wrap/query C facts and expose reports, but must not become the
  durable analysis owner where analogous code is C-owned.
- Fail closed on ambiguous definitions, clobbers, returns, and save/restore
  uncertainty.
- Do not mutate source unless a later issue adds verified render effects.
- If current facts cannot prove or disprove the Pandora A5 lifetime, implement
  the missing core analysis needed to reach that proof. Do not close this issue
  by restating that current reports are insufficient.

## What To Build

Implement or extend the analysis fact model so a proved base-register lifetime
can be represented as a parent fact with stable identity, source scope,
definition evidence, clobber boundaries, conflicts, and invalidation inputs.

For the Pandora fixture, the model must be able to represent an `A5 = _custom`
lifetime that can own multiple child hardware-register references.

## Acceptance Criteria

- [ ] A base-register lifetime fact can represent register, base symbol, base
      address, source/range scope, definition evidence, clobber boundaries, and
      conflicts.
- [ ] The fact identity is stable across reruns unless semantic inputs change.
- [ ] The model is general enough for Amiga custom/library/app bases and future
      Atari/Mac context bases, without implementing those platforms here.
- [ ] Pandora report output exposes the parent lifetime fact or a precise
      blocker explaining why it cannot yet be proved.
- [ ] Any blocker remaining for the Pandora A5 lifetime is backed by a concrete
      binary/control-flow contradiction or by a newly created follow-up issue
      that implements the missing foundation.
- [ ] Ambiguous definitions, register redefinitions, call clobbers, return
      boundaries, and save/restore uncertainty fail closed.
- [ ] Focused tests cover proved, ambiguous, clobbered, and redefined lifetime
      cases.
- [ ] Proposal 017 living notes are updated.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

## Blocked By

- docs/issues/017-101-pandora-a5-context-regression-packet.md

## Research Coverage

- [ ] Existing A5 report/cascade paths inspected.
- [ ] Current C-owned fact graph surfaces inspected.
- [ ] Pandora lifetime blockers from `017-101` used as fixtures.
- [ ] Cross-platform shape requirements checked against Proposal 017.

## Research Review

- [ ] Parent fact identity is stable and scoped.
- [ ] Conflict and invalidation inputs are explicit.
- [ ] The model is not selected-row-only.
- [ ] Ambiguous cases produce blockers instead of accepted facts.

## Required Sign-Off

- [ ] Proposal 017 checked before work.
- [ ] Dependency issue evidence checked before work.
- [ ] Missing analysis foundation was implemented rather than treated as a final
      blocker.
- [ ] Focused tests pass.
- [ ] Real Pandora report proof captured.
- [ ] Proposal 017 living notes updated.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

## Out Of Scope

- Rendering child hardware references.
- Applying source changes.
- Mac/Atari platform implementation.

## Anti-Bypass Rule

The worker must not complete this issue with "current architecture lacks a
lifetime fact" or equivalent. That is the work. Build the proper core fact
foundation, preferably in C where analogous platform analysis lives, then expose
it through the existing Python/report surfaces.
