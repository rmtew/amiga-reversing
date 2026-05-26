# 017-105: Cross Platform Base Context Rule Shape

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Current 017 priority: base/context cascades.
- Pandora proves the implementation path, but the model must not be Amiga-only
  in shape.
- Atari ST and Mac OS have equivalent context/base patterns:
  hardware bases and trap protocols on Atari; A5 world, Toolbox traps, CODE jump
  tables, and Segment Loader context on Mac OS.

## What To Build

Document and test the generic rule shape used by base/context cascades so
future platform lanes can plug in platform-specific base facts and child rules
without duplicating the cascade engine.

This issue should add fixture-level rule tests or schema tests only. It should
not implement Atari or Mac platform parsing/rendering.

## Protocol Delta

- Adds: reusable base/context cascade rule shape.
- Changes: Amiga A5 work must be expressed in platform-neutral parent/child
  terms where practical.
- Replaces: platform-specific one-off cascade assumptions.
- Leaves out of scope: real Atari/Mac target changes and platform KB changes.

## Default Behavior

- Keep real implementation proof on Pandora.
- Use fixture/schema tests for Atari/Mac-like contexts only.
- Do not touch Proposal 012/018 files, Mac target artifacts, Atari/Mac parsers,
  or executable-format KB files.
- Do not hardcode M68K or platform knowledge into generated tooling.
- This issue must produce enforceable schema/rule tests, not only prose.

## Acceptance Criteria

- [ ] The base/context parent fact shape is documented in Proposal 017 or nearby
      017-owned docs.
- [ ] The rule shape supports parent fact, child fact, scope, conflicts,
      invalidation, render effect, blocker, and platform fact reference.
- [ ] Fixture tests cover an Amiga custom-base rule, an Atari hardware/trap-like
      rule shape, and a Mac A5-world/Toolbox-like rule shape without touching
      real Atari/Mac targets.
- [ ] Platform-specific facts remain external inputs; no hardcoded M68K or
      platform knowledge is added to generated tooling.
- [ ] No Proposal 012/018 files, Mac target artifacts, Atari/Mac parsers, or
      platform executable format KB files are changed.
- [ ] Proposal 017 living notes are updated.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

## Blocked By

- docs/issues/017-102-base-register-lifetime-parent-facts.md

## Research Coverage

- [ ] Proposal 017 cross-platform context examples checked.
- [ ] Existing cascade schema/rule tests inspected.
- [ ] Amiga, Atari-like, and Mac-like fixture shapes defined.
- [ ] Platform KB ownership boundaries checked.

## Research Review

- [ ] Rule shape is generic without becoming vague.
- [ ] Real platform parser/render changes are excluded.
- [ ] The rule shape can support parent facts, derived children, blockers,
      render effects, and verifier attribution.

## Required Sign-Off

- [ ] Proposal 017 checked before work.
- [ ] Dependency issue evidence checked before work.
- [ ] Generic rule shape is covered by executable tests or validator checks.
- [ ] Fixture/schema tests pass.
- [ ] No 012/018/Mac target/Atari parser/platform KB files touched.
- [ ] Proposal 017 living notes updated.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

## Out Of Scope

- Real Atari/Mac source changes.
- New platform KB extraction.
- Any compatibility layer for old selected-row-only A5 decisions.

## Anti-Bypass Rule

This issue cannot complete with documentation only. It must lock the reusable
shape with tests/validation so future platform lanes cannot silently regress to
one-off selected-row logic.
