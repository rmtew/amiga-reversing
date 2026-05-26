# 023-004: Segment Loader Fixup Source Records

Status: active
Type: AFK
Source proposal: docs/proposals/023-classic-mac-os-source-presentation.md

## Proposal Context

- 022 added deferred Segment Loader placeholder references.
- 023 requires source-level fixup visibility that is precise enough for a
  reverser to locate the affected bytes/rows and understand what remains
  undecoded.

## What To Build

Replace broad relocation/fixup notes with source reference records tied to
resource identity and source byte spans or rows. Decode only what current
evidence supports. Anything unresolved must remain a typed placeholder with
status, reason, provenance, and source-visible location.

## Acceptance Criteria

- [ ] Segment Loader effects are represented as shared source reference records
      or span-specific placeholders.
- [ ] Records include CODE resource identity and source offset/row context when
      known.
- [ ] Placeholder reasons distinguish unsupported custom extension decoding from
      missing evidence.
- [ ] Artifact/web/API output exposes the fixup records in the same source
      evidence path as other references.
- [ ] Verifier/source presentation tests fail if fixup evidence regresses to a
      broad-only note.

## Blocked By

- docs/issues/023-002-all-code-resource-restored-source-coverage.md

## Required Sign-Off

- [ ] Baseline/per-CODE proof updated for fixup record visibility.
- [ ] Focused Mac tests pass.
- [ ] Platform executable validate/coverage pass.
- [ ] `cmd /c src\precommit.bat` passes if shared C source/render code changes.
- [ ] `git diff --check` passes.
