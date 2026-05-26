# 017-101: Pandora A5 Context Regression Packet

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Current 017 priority: base/context cascades.
- Concrete regression: Pandora source contains `$009C(a5)` at `abs_0_00010910`
  even though related evidence proves `A5` as the Amiga custom-chip base in this
  code family.
- This issue must produce the durable evidence packet and failing/pending proof
  that later implementation issues fix.

## Protocol Delta

- Adds: a durable regression packet for a missed base/context cascade child.
- Changes: makes the Pandora `$009C(a5)` case the active 017 proof target.
- Replaces: informal source inspection as the only evidence for this failure.
- Leaves out of scope: implementation, mutation, and cross-platform changes.

## Default Behavior

- Run read-only reports only.
- Preserve current source and target state.
- Treat unknown callback/register context as blocked, not accepted.
- Record enough evidence that dependent issues can reproduce the same row.
- This is the only diagnostic pre-step in the batch. It must be completed
  quickly and must not expand into a report-only substitute for implementation.

## What To Build

Create a current, reproducible Pandora evidence packet for the unsymbolised
`$009C(a5)` access and its surrounding callback/register context.

The packet must identify:

- the exact target and source row;
- the currently rendered text;
- the expected symbolic render target, `intreq(a5)`;
- the nearest proven or candidate `A5 = _custom` definitions;
- lifetime blockers between the definition and use;
- whether the preceding `jsr (a0)` may clobber or preserve `A5`;
- where `app_0364(a6)` is assigned and consumed, if current facts expose it;
- which current cascade/report surfaces do or do not see the missed child.

## Acceptance Criteria

- [ ] Running the chosen report/command on real Pandora reproduces the
      `$009C(a5)` missed-symbolisation case.
- [ ] The evidence packet names the target row and expected child fact.
- [ ] The packet distinguishes proven facts, candidate facts, and blockers.
- [ ] Callback/function-pointer context is recorded as proven, ambiguous, or
      blocked with a reason.
- [ ] No target source, Manual Action Log, Decision Journal, or metadata is
      mutated by this issue.
- [ ] Proposal 017 living notes are updated with the packet summary.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

## Blocked By

None - can start immediately.

## Research Coverage

- [ ] Real Pandora target and row identified.
- [ ] Current rendered text captured.
- [ ] Expected `intreq(a5)` child fact captured.
- [ ] Candidate/proven A5 definitions and lifetime blockers captured.
- [ ] Callback/function-pointer context at `app_0364(a6)` captured.

## Research Review

- [ ] Evidence distinguishes proved, candidate, ambiguous, and blocked states.
- [ ] No source progress is claimed by this read-only issue.
- [ ] Dependent issues have a reproducible fixture to fix.

## Required Sign-Off

- [ ] Proposal 017 checked before work.
- [ ] Read-only Pandora command/report evidence captured.
- [ ] Proposal 017 living notes updated.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

## Out Of Scope

- Implementing the fix.
- Accepting new facts.
- Touching Proposal 012/018, Mac OS targets, Atari/Mac parsers, or platform
  executable format KB files.

## Anti-Bypass Rule

This issue cannot close the base/context lane. If it finds missing analysis
foundation, the outcome must feed `017-102` and later issues. Do not mark later
work blocked merely because current reports lack the needed fact.
