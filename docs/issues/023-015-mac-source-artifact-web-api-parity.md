# 023-015: Mac Source Artifact Web/API Parity

Status: active
Type: AFK
Source proposal: docs/proposals/023-classic-mac-os-source-presentation.md

## Proposal Context

- 023-011 through 023-014 make `Asm.s` source-first and all-CODE visible.
- Proposal 023 also requires project/API/web surfaces to consume the same
  C-owned source presentation evidence.
- This issue prevents the artifact from improving while web/API views remain on
  report-first or selected-CODE-centric assumptions.

## What To Build

Expose the same source-first, all-CODE section model through project/API/web
payloads that `Asm.s` uses. Broad evidence should remain available as supporting
context, but source navigation must list and identify all CODE sections and
their full/partial/deferred state.

Do not create a parallel compatibility surface. The API/web path must consume
the same section identity and status model as the source artifact, or the shared
model must be extended until it can serve all three.

## Acceptance Criteria

- [ ] API/project payloads expose source-body section order and section
      identities matching the artifact.
- [ ] Web/source views can list all CODE source sections and distinguish full,
      partial, and placeholder/deferred sections.
- [ ] Supporting evidence remains available but is not the primary source view.
- [ ] No web/API field synthesizes source status that is absent from the shared
      artifact/source model.
- [ ] Tests cover artifact/API/web parity for section count, section ids, and
      deferred/source-visible status.
- [ ] Proposal 023 records any remaining UI-only follow-up ideas without making
      them blockers for source correctness.

## Blocked By

- docs/issues/023-012-all-code-source-body-sections.md
- docs/issues/023-013-code0-structured-source-context.md
- docs/issues/023-014-code1-entry-stub-and-residual-span-presentation.md

## Required Sign-Off

- [ ] Focused Mac artifact/project/API/web tests pass.
- [ ] Platform executable validate/coverage pass with Mac/Amiga/Atari current
      backends.
- [ ] `cmd /c src\precommit.bat` passes if shared rendering or C code changes.
- [ ] `git diff --check` passes.
