# 024-002: C Fixup Record Model

Status: paused
Type: AFK
Source proposal: docs/proposals/024-classic-mac-os-segment-loader-fixups.md

## Proposal Context

- 024-001 defined the current-parser inventory boundary.
- 024-009 must add the documented CODE segment layout parser boundary before
  this issue resumes.
- Later 024 issues need a C-owned record shape for decoded effects and residual
  placeholders.

## What To Build

Add a C-owned Segment Loader fixup record model. It must represent decoded
effects and deferred placeholders without relying on Python-side synthesis.

Records must carry at least:

- resource type/id;
- byte space;
- source offset/range;
- effect kind or placeholder kind;
- target when known;
- status;
- reason;
- provenance;
- source visibility;
- fact status/parser-use where available.

## Acceptance Criteria

- [ ] C owns the fixup record model and JSON/API emission.
- [ ] Python surfaces consume the C record model or fail closed.
- [ ] Decoded and deferred records share one stable shape.
- [ ] Tests cover valid records and malformed/missing model output.
- [ ] Proposal 024 records the model boundary.

## Blocked By

- docs/issues/024-009-documented-code-segment-layout-parser.md

## Required Sign-Off

- [ ] Focused Mac C/backend/project/artifact tests pass.
- [ ] Platform executable validate/coverage pass.
- [ ] `cmd /c src\precommit.bat` passes.
- [ ] `git diff --check` passes.
