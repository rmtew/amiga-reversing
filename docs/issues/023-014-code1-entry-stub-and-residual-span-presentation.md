# 023-014: CODE 1 Entry, Stub, And Residual Span Presentation

Status: complete
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

This issue must not stop at "entry proof missing". The documented CODE layout is
already known. Use it to split metadata from executable body, then inspect the
stub bytes and local Mac docs/KB to classify what can be classified. Only the
remaining unproven semantic may stay deferred.

## Acceptance Criteria

- [x] CODE 1 metadata/header bytes are separated from executable source rows.
- [x] The first executable CODE 1 row starts at the accepted body offset.
- [x] The leading stub is labelled from accepted evidence, or explicitly marked
      as a deferred entry/stub placeholder when evidence is insufficient.
- [x] Residual bytes after the stub are rendered under clear ownership/status
      wording and are not called orphan code unless that term has a precise
      tested meaning.
- [x] Any remaining deferred CODE 1 claim names the exact missing proof after
      local documentation/KB review.
- [x] Tests assert the CODE 1 section contains clear labels and no misleading
      orphan terminology.

## Completed Result

- `Asm.s` now labels the CODE 1 far-model header separately from executable
  source rows.
- The selected CODE 1 listing starts after the documented 40-byte header and the
  section records the candidate entry/stub span `payload[40..62)`.
- Remaining CODE 1 bytes are labelled as candidate executable body
  `payload[62..29024)`, with byte-entry and Segment Loader fixup proof still
  explicitly deferred instead of described as vague orphan code.

## Blocked By

- docs/issues/023-011-source-first-asm-artifact-contract.md

May be developed alongside 023-012/023-013 if it does not change shared section
identity.

## Required Sign-Off

- [x] Focused Mac artifact/project/API tests pass.
- [x] Platform executable validate/coverage pass with Mac/Amiga/Atari current
      backends.
- [x] `cmd /c src\precommit.bat` passes if shared rendering or C code changes.
- [x] `git diff --check` passes.
