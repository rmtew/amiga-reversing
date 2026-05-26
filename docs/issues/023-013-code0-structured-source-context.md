# 023-013: CODE 0 Structured Source Context

Status: active
Type: AFK
Source proposal: docs/proposals/023-classic-mac-os-source-presentation.md

## Proposal Context

- Proposal 023 requires CODE 0 routing/reference context to be source-visible.
- 023-009/023-010 corrected over-claimed CODE 0 references.
- This issue turns accepted CODE 0 structure into useful source data rather than
  a leading report table.

## What To Build

Render CODE 0 routing as a structured source-body data section. Parsed jump-table
or segment-routing entries should get stable labels and link to CODE section
labels only where the evidence supports that relationship. Resources with absent
jump-table spans must remain unlinked/deferred.

If a CODE 0 field is not currently decoded, the worker must use the local Mac
docs and executable KB to decode it or record the exact byte/documentation gap
that prevents a semantic link. The source section must still render the bytes as
structured or conservative data; it must not collapse back to a report table.

## Acceptance Criteria

- [ ] CODE 0 has a source-body data section in `Asm.s`.
- [ ] Validated CODE 0 dispatch references link to corresponding CODE section
      labels where parsed evidence exists.
- [ ] CODE resources with absent jump-table spans are not rendered as accepted
      dispatch targets.
- [ ] Undecoded CODE 0 bytes remain visible as labelled data with a precise
      unproven semantic, not as an omitted report note.
- [ ] Tests cover linked behavior, absent-link behavior, and artifact rendering.
- [ ] Proposal 023 records the final CODE 0 source-context behavior.

## Blocked By

- docs/issues/023-011-source-first-asm-artifact-contract.md

May be developed alongside 023-012, but final labels and placement must match
the all-CODE source body sections.

## Required Sign-Off

- [ ] Focused Mac artifact/project/API tests pass.
- [ ] Platform executable validate/coverage pass with Mac/Amiga/Atari current
      backends.
- [ ] `cmd /c src\precommit.bat` passes if shared rendering or C code changes.
- [ ] `git diff --check` passes.
