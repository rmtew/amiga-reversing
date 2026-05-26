# 024-006: Replace Broad Fixup Placeholders

Status: blocked
Type: AFK
Source proposal: docs/proposals/024-classic-mac-os-segment-loader-fixups.md

## Proposal Context

- 023 used broad Segment Loader placeholders because no decoder existed.
- 024 now has decoded records and precise residual placeholders.

## What To Build

Delete broad fixup placeholder output where decoded fixup records or precise
per-span placeholders now exist. Keep fail-closed behavior if the C-owned parse
model is missing.

## Acceptance Criteria

- [ ] Default Mac source output no longer relies on broad fixup placeholders for
      spans that have decoded records or precise residual placeholders.
- [ ] Missing C-owned fixup model output fails closed.
- [ ] Tests prove Python/web/API do not synthesize decoded fixup authority.
- [ ] Proposal 024 records deleted/replaced compatibility paths.

## Blocked By

- docs/issues/024-005-expand-supported-fixup-forms.md
- 024-001 found no actual Segment Loader fixup encoding byte provenance, so the
  broad deferred placeholder remains the correct fail-closed output.

## Required Sign-Off

- [ ] Focused Mac C/backend/project/artifact/web tests pass.
- [ ] Platform executable validate/coverage pass.
- [ ] `cmd /c src\precommit.bat` passes.
- [ ] `git diff --check` passes.
