# 024-004: Attach Fixups To Restored Source Rows

Status: active
Type: AFK
Source proposal: docs/proposals/024-classic-mac-os-segment-loader-fixups.md

## Proposal Context

- 024-003 emits decoded fixup records.
- The records must become useful source context, not a detached parse report.

## What To Build

Attach decoded Segment Loader fixup records and residual placeholders to
restored-source ownership ranges/source rows where source spans are known.
Artifact/API users should be able to move from source presentation to the fixup
record and back.

## Acceptance Criteria

- [ ] Fixup records attach to ownership ranges or source rows when a source span
      is known.
- [ ] Residual placeholders also attach to the most precise span available.
- [ ] Detached records include a reason when no source row/range exists.
- [ ] Artifact/API tests prove source-to-fixup navigation evidence exists.
- [ ] Proposal 024 records attachment behavior and any residual limitations.

## Blocked By

- docs/issues/024-003-decode-first-supported-fixup-form.md

## Required Sign-Off

- [ ] Focused Mac C/backend/project/artifact tests pass.
- [ ] Platform executable validate/coverage pass.
- [ ] `cmd /c src\precommit.bat` passes.
- [ ] `git diff --check` passes.
