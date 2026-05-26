# 024-008: Segment Loader Fixup Closeout

Status: active
Type: AFK
Source proposal: docs/proposals/024-classic-mac-os-segment-loader-fixups.md

## Proposal Context

- This closes Proposal 024 after decoded fixup records and residual placeholders
  are source-visible and verified.

## What To Build

Run and record the final proof. Promote durable outcomes into Proposal 024 and
delete completed 024 issue files only after their results are represented in
the proposal.

## Acceptance Criteria

- [ ] Proposal 024 records decoded supported forms and residual deferred forms.
- [ ] Mac source/artifact/web/API output shows decoded fixup records and precise
      residual placeholders.
- [ ] No unsupported/custom form is promoted beyond evidence.
- [ ] Proposal 023 source-presentation behavior remains intact.
- [ ] Amiga/Atari exact gates remain green when applicable.
- [ ] Completed 024 issue files are deleted after proposal promotion.

## Blocked By

- docs/issues/024-007-source-display-and-web-api-exposure.md

## Required Sign-Off

- [ ] Focused Mac tests pass.
- [ ] Platform executable validate/coverage pass.
- [ ] `cmd /c src\precommit.bat` passes.
- [ ] `git diff --check` passes.
