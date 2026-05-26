# 024-002: C Fixup Record Model

Status: blocked
Type: AFK
Source proposal: docs/proposals/024-classic-mac-os-segment-loader-fixups.md

## Proposal Context

- 024-001 defines the byte inventory and parser boundary.
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

- docs/issues/024-001-current-fixup-byte-inventory-and-parser-boundary.md
- 024-009 mapped the documented CODE layout. Current MPW `Asm` resources either
  use near-model headers with no relocation-info fields or far-model headers
  whose A5/segment relocation offsets are zero. Record-model work must not
  invent decoded forms without a real encoding span.

## Required Sign-Off

- [ ] Focused Mac C/backend/project/artifact tests pass.
- [ ] Platform executable validate/coverage pass.
- [ ] `cmd /c src\precommit.bat` passes.
- [ ] `git diff --check` passes.
