# 023-017: Source Quality Analysis Gates

Status: complete
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

- [x] The worker regenerates the committed MPW `Asm.s` and records visible
      before/after improvement in Proposal 023.
- [x] Every CODE resource has a range-level ownership summary covering metadata,
      code, data, fixup/relocation, padding, placeholder, and unknown where
      present.
- [x] No range is classified only as vague orphan code/data. Any residual span
      has exact byte range, status, reason, and next implementation step.
- [x] Reachable-code discovery uses available CODE 0 routing, segment headers,
      branch targets, JSR/BSR targets, jump tables, and known entry/stub
      patterns.
- [x] Bytes not supported as code by analysis are rendered as data, unknown, or
      source-visible placeholders, not plausible instruction listings.
- [x] Stable labels are rendered for CODE sections, entrypoints, jump-table
      targets, branch targets, data references, and placeholders where evidence
      supports them.
- [x] Source output visibly splits code/data/metadata/residual spans within each
      CODE resource instead of one flat blob.
- [x] Tests fail if the artifact regresses to fake disassembly, hidden residual
      bytes, missing labels for accepted references, or broad orphan wording.

## Completed Result

- Project/API payloads now expose `binary_container_view.source_quality_gate`
  with `kind: macos_source_quality_gate_v1`.
- The gate status is `passed_with_deferred_semantics`: it proves source-first
  coverage, range ownership, labels, explicit residuals, no vague orphan bucket,
  and no fake instruction rendering while explicitly not claiming accepted
  byte-entry proof, decoded Segment Loader fixups, A5 lifetime proof, or
  resource-fork round trip.
- The committed MPW `Asm.s` was regenerated and now renders the source-quality
  checklist before supporting evidence. CODE 1 still reports candidate entry
  and candidate residual spans; unresolved semantics name exact byte ranges and
  next implementation steps.
- Legacy raw `orphan_ranges` from the parser summary are not rendered as orphan
  buckets; their bytes are represented by source-body `metadata`, `data`,
  `candidate_code`, or `deferred` ranges.

## Blocked By

- docs/issues/023-012-all-code-source-body-sections.md
- docs/issues/023-013-code0-structured-source-context.md
- docs/issues/023-014-code1-entry-stub-and-residual-span-presentation.md

May run alongside 023-015 after the source section model exists.

## Required Sign-Off

- [x] Focused Mac backend/project/artifact/source tests pass.
- [x] Platform executable validate/coverage pass with Mac/Amiga/Atari current
      backends.
- [x] `cmd /c src\precommit.bat` passes.
- [x] `git diff --check` passes.
