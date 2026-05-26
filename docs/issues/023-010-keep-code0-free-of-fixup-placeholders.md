# 023-010: Keep CODE 0 Free Of Segment Loader Fixup Placeholders

Status: active
Type: AFK
Source proposal: docs/proposals/023-classic-mac-os-source-presentation.md

## Proposal Context

- Proposal 023 closeout review found that CODE 0 receives a
  `segment_loader_fixup_placeholder`.
- CODE 0 is metadata/routing in the current Mac source presentation, not an
  ordinary executable CODE segment fixup span.
- Emitting a Segment Loader fixup placeholder on CODE 0 makes the source output
  imply deferred fixup evidence where none is established.

## What To Build

Adjust the C-owned Mac restored-source reference builder so CODE 0 emits only
metadata/routing references unless explicit fixup evidence exists.

Nonzero CODE resources should keep span-specific deferred Segment Loader fixup
placeholders where the current evidence supports deferred fixup context.

## Acceptance Criteria

- [ ] CODE 0 restored-source records do not include
      `segment_loader_fixup_placeholder` for the normal metadata/routing packet.
- [ ] CODE 0 keeps validated routing/metadata references where supported.
- [ ] Nonzero CODE resources keep Segment Loader placeholders with resource id,
      byte space, source offset/range, deferred status, reason, provenance, and
      source visibility.
- [ ] Tests fail if CODE 0 regresses to broad fixup-placeholder output.
- [ ] Proposal 023 records the corrected behavior.

## Blocked By

- docs/issues/023-009-guard-code0-dispatch-references.md

## Required Sign-Off

- [ ] Focused Mac C/backend/project/artifact tests pass.
- [ ] Platform executable validate/coverage pass.
- [ ] `cmd /c src\precommit.bat` passes if shared C/source output changes.
- [ ] `git diff --check` passes.
