# 023-007: Source Display And API Consolidation

Status: active
Type: AFK
Source proposal: docs/proposals/023-classic-mac-os-source-presentation.md

## Proposal Context

- 023-002 through 023-006 build the source evidence.
- This issue makes the visible source/artifact/web/API path consume that
  evidence as the default and deletes superseded display compatibility paths.

## What To Build

Consolidate Mac source display and API output around restored-source ownership,
references, platform extensions, and placeholders. Remove compatibility display
paths once tests prove the shared records expose equivalent or better evidence.

## Acceptance Criteria

- [ ] Existing source/artifact/web/API surfaces show per-CODE status, CODE 0
      routing, fixup records/placeholders, A5 context, and linked resource
      placeholders where available.
- [ ] Python/web surfaces do not synthesize passing restored-source evidence.
- [ ] Superseded compatibility display paths are deleted after replacement
      proof.
- [ ] Obvious UI shortcomings are recorded in Proposal 023 as future UI work,
      not used to block source evidence delivery.
- [ ] Mac remains no-round-trip; Amiga/Atari exact behavior remains green.

## Blocked By

- docs/issues/023-003-code0-routing-and-source-references.md
- docs/issues/023-004-segment-loader-fixup-source-records.md
- docs/issues/023-005-mac-address-and-a5-context-presentation.md
- docs/issues/023-006-executable-resource-placeholder-linking.md

## Required Sign-Off

- [ ] Focused Mac source/artifact/web/API tests pass.
- [ ] Platform executable validate/coverage pass.
- [ ] `cmd /c src\precommit.bat` passes.
- [ ] `git diff --check` passes.
