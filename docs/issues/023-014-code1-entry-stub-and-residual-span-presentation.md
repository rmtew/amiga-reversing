# 023-014: CODE 1 Entry, Stub, And Residual Span Presentation

Status: active
Type: AFK
Source proposal: docs/proposals/023-classic-mac-os-source-presentation.md

## Proposal Context

- Proposal 023 requires visible Mac source to be useful, not just covered by
  evidence packets.
- Current `Asm.s` still shows the CODE 1 leading stub and residual candidate
  bytes without enough source-quality structure.
- 024 mapped documented CODE header boundaries. This issue may consume that
  knowledge, but it must not depend on Segment Loader fixup decoding being
  complete.

## What To Build

Use known CODE resource layout to make CODE 1 readable. Separate the far-model
header from executable body output, label or precisely defer the leading stub,
and replace vague orphan/residual wording with clear code/data/unknown/deferred
ownership labels.

## Acceptance Criteria

- [ ] CODE 1 metadata/header bytes are separated from executable source rows.
- [ ] The first executable CODE 1 row starts at the accepted body offset.
- [ ] The leading stub is labelled from accepted evidence, or explicitly marked
      as a deferred entry/stub placeholder when evidence is insufficient.
- [ ] Residual bytes after the stub are rendered under clear ownership/status
      wording and are not called orphan code unless that term has a precise
      tested meaning.
- [ ] Tests assert the CODE 1 section contains clear labels and no misleading
      orphan terminology.

## Blocked By

- docs/issues/023-011-source-first-asm-artifact-contract.md

May be developed alongside 023-012/023-013 if it does not change shared section
identity.

## Required Sign-Off

- [ ] Focused Mac artifact/project/API tests pass.
- [ ] Platform executable validate/coverage pass with Mac/Amiga/Atari current
      backends.
- [ ] `cmd /c src\precommit.bat` passes if shared rendering or C code changes.
- [ ] `git diff --check` passes.
