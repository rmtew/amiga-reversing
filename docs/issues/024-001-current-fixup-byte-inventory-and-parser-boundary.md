# 024-001: Current Fixup Byte Inventory And Parser Boundary

Status: active
Type: AFK
Source proposal: docs/proposals/024-classic-mac-os-segment-loader-fixups.md

## Proposal Context

- Proposal 023 left Segment Loader fixups as precise deferred source-visible
  placeholders.
- Proposal 024 starts real decoding work.
- This first issue must establish what current MPW `Asm` bytes expose and where
  the parser boundary is, using executable checks.

## What To Build

Add a narrow C/API/test harness that locates Segment Loader fixup candidate spans
for current CODE resources and classifies each span as parseable, unsupported,
custom/unknown, malformed, or absent.

This is not a pure report. The result must be reusable by later 024 issues as
the input boundary for decoded fixup records.

## Acceptance Criteria

- [ ] The committed MPW `Asm` fixture produces a deterministic fixup inventory.
- [ ] Inventory records include CODE resource id, byte space, source offset/range,
      status, reason, provenance, and source visibility.
- [ ] The harness distinguishes parseable bytes from unsupported/custom bytes.
- [ ] Missing or malformed fixup data fails closed and cannot become accepted
      source references.
- [ ] Proposal 024 records the current boundary and next decoder target.

## Blocked By

None - can start immediately.

## Required Sign-Off

- [ ] Focused Mac C/backend/project/artifact tests pass.
- [ ] Platform executable validate/coverage pass.
- [ ] `cmd /c src\precommit.bat` passes if C/source output changes.
- [ ] `git diff --check` passes.
