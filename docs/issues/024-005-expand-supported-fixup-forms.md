# 024-005: Expand Supported Fixup Forms

Status: paused
Type: AFK
Source proposal: docs/proposals/024-classic-mac-os-segment-loader-fixups.md

## Proposal Context

- 024-003 decodes the first supported form.
- 024-004 attaches fixup records to source.
- This issue expands decoding for additional supported forms found in the
  current fixture, while preserving explicit placeholders for ambiguous forms.

## What To Build

Decode every additional Segment Loader fixup form that is clear from actual
fixup encoding bytes and existing facts. Do not infer semantics from wishful
source appearance or from CODE payload candidate spans. If a form is ambiguous,
keep it as a typed deferred placeholder with the exact blocking reason.

## Acceptance Criteria

- [ ] Additional supported fixture forms are decoded.
- [ ] Ambiguous/custom forms remain deferred with exact reasons.
- [ ] Tests cover each decoded form and each residual placeholder class.
- [ ] No unsupported form is promoted to accepted/decoded behavior.
- [ ] Proposal 024 records the supported and deferred form list.
- [ ] If 024-001/024-003 proved no supported form, this issue remains blocked
      rather than inventing a decoder.

## Blocked By

- docs/issues/024-004-attach-fixups-to-restored-source-rows.md
- 024-001 found no supported fixup forms to expand.

## Required Sign-Off

- [ ] Focused Mac C/backend/project/artifact tests pass.
- [ ] Platform executable validate/coverage pass.
- [ ] `cmd /c src\precommit.bat` passes.
- [ ] Native C unit tests cover every decoded form or the blocked state.
- [ ] `git diff --check` passes.
