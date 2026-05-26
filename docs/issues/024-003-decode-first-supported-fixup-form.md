# 024-003: Decode First Supported Fixup Form

Status: paused
Type: AFK
Source proposal: docs/proposals/024-classic-mac-os-segment-loader-fixups.md

## Proposal Context

- 024-009 identifies parseable fixup candidates from documented CODE segment
  layout.
- 024-002 provides the record model.
- This issue must turn at least one supported fixup form into decoded source
  reference records.

## What To Build

Implement the first supported Segment Loader fixup decoder found in the current
MPW `Asm` fixture. Emit decoded records through the C-owned model and keep every
other unsupported/custom form as typed deferred placeholders.

If 024-001 did not prove a supported fixup form with actual fixup encoding byte
provenance, do not implement a speculative decoder. Record the blocker in
Proposal 024 and leave 024-003/024-005 blocked until evidence exists.

## Acceptance Criteria

- [ ] At least one real fixture fixup form is decoded from bytes.
- [ ] Decoded records include effect kind, source span, target when known,
      provenance, and source visibility.
- [ ] Unsupported/custom forms remain deferred placeholders.
- [ ] Tests prove decoded records cannot be emitted from malformed or absent
      evidence.
- [ ] Proposal 024 records the decoded form and residual deferred forms.
- [ ] If no supported form exists, Proposal 024 records the blocker and no
      decoded records are emitted.

## Blocked By

- docs/issues/024-002-c-fixup-record-model.md
- 024-001 found no supported fixup form with actual encoding byte provenance.
  Do not implement a speculative decoder.

## Required Sign-Off

- [ ] Focused Mac C/backend/project/artifact tests pass.
- [ ] Platform executable validate/coverage pass.
- [ ] `cmd /c src\precommit.bat` passes.
- [ ] Native C unit tests cover the decoder or the no-supported-form blocker.
- [ ] `git diff --check` passes.
