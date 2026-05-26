# 023-005: Mac Address And A5 Context Presentation

Status: active
Type: AFK
Source proposal: docs/proposals/023-classic-mac-os-source-presentation.md

## Proposal Context

- Mac source presentation needs address-space and A5/world/global-base context
  to be useful.
- Existing A5 evidence must remain candidate/deferred unless real path/lifetime
  proof exists.

## What To Build

Surface Mac address model and A5/world/global-base context through source rows,
source reference records, or platform extensions. A5-relative instructions
should be visible and navigable as candidate/deferred context without claiming
durable accepted hardware-base evidence.

## Acceptance Criteria

- [ ] Mac source records distinguish resource payload offsets, local source
      offsets, and runtime/address-model context.
- [ ] A5-relative uses are visible in restored-source evidence where detected.
- [ ] A5/world/global context carries candidate/deferred status and provenance.
- [ ] No report or UI surface calls A5 context proven/accepted unless lifetime
      evidence exists.
- [ ] Artifact/web/API output exposes the context for source navigation.

## Blocked By

- docs/issues/023-002-all-code-resource-restored-source-coverage.md

## Required Sign-Off

- [ ] Baseline/per-CODE proof updated for address/A5 context visibility.
- [ ] Focused Mac tests pass.
- [ ] Platform executable validate/coverage pass.
- [ ] `git diff --check` passes.
