# 023-011: Source-First Asm Artifact Contract

Status: complete
Type: AFK
Source proposal: docs/proposals/023-classic-mac-os-source-presentation.md

## Proposal Context

- Proposal 023 is reopened because the MPW `Asm.s` artifact still starts as a
  broad evidence report instead of useful source.
- 022/023 already provide C-owned restored-source packets, ownership ranges,
  references, placeholders, and verifier state.
- This issue must make the visible artifact source-first without deleting the
  evidence a reverser or reviewer still needs.

## What To Build

Change the Mac target source artifact so `Asm.s` starts with a short identity
header followed by actual restored source or source placeholder sections. Broad
file/resource inventories, coverage tables, verifier dumps, and detailed
per-CODE evidence records must move behind the source body or into a stable
sidecar artifact.

This is not a report-only issue. The visible `Asm.s` ordering must change.

If a current report block appears necessary, first identify the exact consumer
that needs it. Move it behind source or to a sidecar, then update that consumer.
Do not leave the report at the front because it is easier.

## Acceptance Criteria

- [x] `Asm.s` has at most a compact identity/header block before the first source
      section.
- [x] The first useful artifact body after the header is restored source or a
      typed source placeholder, not resource inventory/report comments.
- [x] Existing C-owned evidence remains available either after the source body or
      in a sidecar artifact with stable naming.
- [x] Any sidecar/report relocation has tests proving the evidence remains
      reachable without dominating source output.
- [x] Tests fail if a large report preamble returns to the front of `Asm.s`.
- [x] Proposal 023 records where the supporting evidence now lives.

## Completed Result

- `Asm.s` now starts with a compact identity header, selected CODE restored-source
  packet context, and the CODE 1 source listing.
- Broad file/resource inventory, CODE coverage, CODE detail evidence, non-CODE
  placeholders, and unsupported-runtime notes remain in `Asm.s` after the source
  body under a supporting-evidence section.
- Artifact tests assert source appears before report evidence so the old
  report-first preamble cannot return silently.

## Blocked By

None - can start immediately.

## Required Sign-Off

- [x] Focused Mac artifact/project/API tests pass.
- [x] Platform executable validate/coverage pass with Mac/Amiga/Atari current
      backends.
- [x] `cmd /c src\precommit.bat` passes if shared rendering or C code changes.
- [x] `git diff --check` passes.
