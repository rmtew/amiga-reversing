# 023-003: CODE 0 Routing And Source References

Status: active
Type: AFK
Source proposal: docs/proposals/023-classic-mac-os-source-presentation.md

## Proposal Context

- CODE 0 currently has metadata significance but is not enough of a source-level
  navigation object.
- 023 requires CODE 0 to contribute routing/reference context without promoting
  unsupported loader semantics.

## What To Build

Represent CODE 0 dispatch/resource relationships as shared source reference
records or typed placeholders. The result should let a reverser see how CODE 0
relates to executable CODE resources from the same source/artifact/API surfaces
used for normal source references.

## Acceptance Criteria

- [ ] CODE 0 appears in Mac restored-source/platform-extension evidence with
      explicit role and status.
- [ ] Known CODE 0 to CODE-resource relationships become source reference
      records where evidence supports them.
- [ ] Unknown or unsupported CODE 0 entries become typed placeholders, not broad
      notes.
- [ ] Web/API/artifact presentation exposes the CODE 0 routing context.
- [ ] No byte-entry or Segment Loader fact is promoted beyond its current
      evidence status.

## Blocked By

- docs/issues/023-002-all-code-resource-restored-source-coverage.md

## Required Sign-Off

- [ ] Baseline/per-CODE proof updated for CODE 0 routing evidence.
- [ ] Focused Mac tests pass.
- [ ] Platform executable validate/coverage pass.
- [ ] `git diff --check` passes.
