# 023-017: Source Quality Analysis Gates

Status: active
Type: AFK
Source proposal: docs/proposals/023-classic-mac-os-source-presentation.md

## Proposal Context

- 023-011 through 023-014 make `Asm.s` source-first, all-CODE visible, and
  structured around CODE 0/CODE 1.
- That is necessary but not sufficient. A neatly rearranged artifact can still
  be poor reversing output if it renders fake code, hides unknown bytes, lacks
  labels/xrefs, or leaves residual spans vague.
- This issue adds the quality gates that prove the rendered source is materially
  better for a reverser.

## What To Build

Add source-quality checks over the generated MPW `Asm.s` and the underlying
Mac source model. These checks must force real analysis quality: ownership
coverage, conservative code/data splitting, reachable-code evidence, stable
labels, xrefs, residual accounting, and visible before/after proof.

This is not a report-only issue. If a check exposes missing implementation, add
the implementation using the Proposal 023 execution standard: inspect bytes and
parser output, use local Mac docs/KB, formalize missing facts when needed, and
continue.

## Acceptance Criteria

- [ ] The worker regenerates the committed MPW `Asm.s` and records visible
      before/after improvement in Proposal 023.
- [ ] Every CODE resource has a range-level ownership summary covering metadata,
      code, data, fixup/relocation, padding, placeholder, and unknown where
      present.
- [ ] No range is classified only as vague orphan code/data. Any residual span
      has exact byte range, status, reason, and next implementation step.
- [ ] Reachable-code discovery uses available CODE 0 routing, segment headers,
      branch targets, JSR/BSR targets, jump tables, and known entry/stub
      patterns.
- [ ] Bytes not supported as code by analysis are rendered as data, unknown, or
      source-visible placeholders, not plausible instruction listings.
- [ ] Stable labels are rendered for CODE sections, entrypoints, jump-table
      targets, branch targets, data references, and placeholders where evidence
      supports them.
- [ ] Source output visibly splits code/data/metadata/residual spans within each
      CODE resource instead of one flat blob.
- [ ] Tests fail if the artifact regresses to fake disassembly, hidden residual
      bytes, missing labels for accepted references, or broad orphan wording.

## Blocked By

- docs/issues/023-012-all-code-source-body-sections.md
- docs/issues/023-013-code0-structured-source-context.md
- docs/issues/023-014-code1-entry-stub-and-residual-span-presentation.md

May run alongside 023-015 after the source section model exists.

## Required Sign-Off

- [ ] Focused Mac backend/project/artifact/source tests pass.
- [ ] Platform executable validate/coverage pass with Mac/Amiga/Atari current
      backends.
- [ ] `cmd /c src\precommit.bat` passes.
- [ ] `git diff --check` passes.
