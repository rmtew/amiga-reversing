# 017-103: A5 Hardware Child Cascade Rendering

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Current 017 priority: base/context cascades.
- `017-102` provides the parent lifetime fact.
- The desired source result is not one accepted operand. It is all safe
  hardware-register children derived from the parent lifetime.

## Protocol Delta

- Adds: derived A5 hardware-register child facts and render effects.
- Changes: source rendering consumes derived lifetime children through normal
  effective analysis state.
- Replaces: one-off A5 selected operand rendering as proof of progress.
- Leaves out of scope: callback target promotion and non-Amiga platform
  implementation.

## Default Behavior

- Derive every safe child in scope, not only the selected regression row.
- Block every child outside scope or across an unproved clobber.
- Render only through normal analysis/effective metadata paths.
- Require baseline-without-parent versus effective-with-parent verification for
  output-affecting source deltas.
- The target outcome is a real source delta for Pandora unless binary evidence
  proves the `$009C(a5)` transformation unsafe.

## What To Build

Derive symbolic Amiga hardware-register child facts from a proved `A5 = _custom`
lifetime and render all verifier-safe children in source export.

The real Pandora proof must include the current missed access:

```asm
	move.w #$20,$009C(a5)
```

It should render symbolically as an `intreq(a5)` access when the parent lifetime
scope proves `A5 = _custom` at that row.

## Acceptance Criteria

- [ ] Cascade derives child hardware-register facts for all safe `disp(a5)`
      accesses inside the accepted/proved lifetime.
- [ ] `$009C(a5)` at the Pandora regression row is derived as `intreq(a5)` or
      an equivalent canonical custom-register symbol.
- [ ] If `$009C(a5)` cannot render symbolically, the issue records the exact
      contradictory evidence and creates or updates the next implementation
      issue that removes any non-contradictory blocker.
- [ ] Children outside the lifetime, across clobber boundaries, or with unknown
      base are blocked with precise reasons.
- [ ] Source export renders derived children symbolically through normal
      effective analysis state, not ad hoc text replacement.
- [ ] Baseline-without-parent versus effective-with-parent verifier delta proves
      the new source text is caused by the parent lifetime.
- [ ] Negative safety proves nearby non-child `a5` uses are unchanged.
- [ ] Exact round-trip passes for output-affecting changes.
- [ ] Focused fixture tests cover multiple children from one lifetime.
- [ ] Real Pandora proof is recorded in Proposal 017 living notes.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

## Blocked By

- docs/issues/017-102-base-register-lifetime-parent-facts.md

## Research Coverage

- [ ] Hardware register symbol source checked.
- [ ] Existing A5 render/effective metadata path inspected.
- [ ] Existing cascade verifier/apply path inspected.
- [ ] Pandora `$009C(a5)` row used as required fixture.

## Research Review

- [ ] Multiple children can derive from one parent lifetime.
- [ ] `intreq(a5)` render is caused by the parent lifetime, not text patching.
- [ ] Negative safety covers nearby non-child A5 uses.
- [ ] Exact round-trip is required for any source change.

## Required Sign-Off

- [ ] Proposal 017 checked before work.
- [ ] Dependency issue evidence checked before work.
- [ ] `$009C(a5)` is either rendered symbolically or rejected by concrete
      semantic contradiction, not by missing plumbing.
- [ ] Focused child-derivation tests pass.
- [ ] Real Pandora baseline-delta verifier proof captured.
- [ ] Exact round-trip passes for output-affecting changes.
- [ ] Proposal 017 living notes updated.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

## Out Of Scope

- Callback target promotion.
- App-base/RSSET changes unless they are required by the shared cascade engine.
- Mac/Atari implementation.

## Anti-Bypass Rule

Report-only output is not completion. Already-represented output is not
completion for the `$009C(a5)` regression unless the checked-in source already
renders the expected symbolic register. Missing renderer/effective-metadata
plumbing must be implemented.
