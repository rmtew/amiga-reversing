# 023-016: Visible Mac Source Presentation Closeout

Status: active
Type: AFK
Source proposal: docs/proposals/023-classic-mac-os-source-presentation.md

## Proposal Context

- Proposal 023 was reopened because evidence/report availability did not produce
  visible `Asm.s` reversing improvement.
- This issue closes 023 only after the corrected visible-source contract is true.

## What To Build

Perform the final closeout for the reopened 023 source-output track. The closeout
must prove that the committed MPW `Asm.s` artifact is source-first, all CODE
resources are visibly represented, CODE 0 context is source-visible, CODE 1
entry/stub/residual spans are presented clearly, and API/web surfaces match the
artifact.

## Acceptance Criteria

- [ ] Proposal 023 status is updated only after 023-011 through 023-015 are
      complete.
- [ ] The proposal records the corrected final source-output state and does not
      treat evidence/report visibility as sufficient.
- [ ] Generated `Asm.s` starts with useful source after a compact header.
- [ ] Every CODE resource is visible in source-body output.
- [ ] CODE 0 and CODE 1 presentation requirements are covered by tests.
- [ ] No Mac round-trip or unsupported semantic promotion is claimed.
- [ ] Completed 023 issue files are deleted only after their work is represented
      in the proposal.

## Blocked By

- docs/issues/023-011-source-first-asm-artifact-contract.md
- docs/issues/023-012-all-code-source-body-sections.md
- docs/issues/023-013-code0-structured-source-context.md
- docs/issues/023-014-code1-entry-stub-and-residual-span-presentation.md
- docs/issues/023-015-mac-source-artifact-web-api-parity.md

## Required Sign-Off

- [ ] Platform executable validate passes.
- [ ] Platform executable coverage passes with Mac/Amiga/Atari current backends.
- [ ] Focused Mac backend/project/artifact/web/source tests pass.
- [ ] `cmd /c src\precommit.bat` passes.
- [ ] `git diff --check` passes.
