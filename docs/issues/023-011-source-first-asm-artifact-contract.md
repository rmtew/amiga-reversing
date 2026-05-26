# 023-011: Source-First Asm Artifact Contract

Status: active
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

## Acceptance Criteria

- [ ] `Asm.s` has at most a compact identity/header block before the first source
      section.
- [ ] The first useful artifact body after the header is restored source or a
      typed source placeholder, not resource inventory/report comments.
- [ ] Existing C-owned evidence remains available either after the source body or
      in a sidecar artifact with stable naming.
- [ ] Tests fail if a large report preamble returns to the front of `Asm.s`.
- [ ] Proposal 023 records where the supporting evidence now lives.

## Blocked By

None - can start immediately.

## Required Sign-Off

- [ ] Focused Mac artifact/project/API tests pass.
- [ ] Platform executable validate/coverage pass with Mac/Amiga/Atari current
      backends.
- [ ] `cmd /c src\precommit.bat` passes if shared rendering or C code changes.
- [ ] `git diff --check` passes.
