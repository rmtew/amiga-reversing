# 024-007: Source Display And Web/API Exposure

Status: paused
Type: AFK
Source proposal: docs/proposals/024-classic-mac-os-segment-loader-fixups.md

## Proposal Context

- 024-006 replaces broad placeholders with decoded records and precise residual
  placeholders.
- Existing source/artifact/web/API surfaces must show that evidence.

## What To Build

Expose decoded Segment Loader fixup effects and residual placeholders through
existing source, artifact, web, and API surfaces. Do not redesign the UI; make
the evidence visible and navigable in the current Mac source panels.

## Acceptance Criteria

- [ ] Artifact output shows decoded effect kinds, targets when known, and source
      spans.
- [ ] Web/API output shows decoded records and residual placeholder reasons.
- [ ] Existing compact UI remains usable and does not hide residual deferred
      states.
- [ ] Future UI improvements are recorded in Proposal 024 if obvious.

## Blocked By

- docs/issues/024-006-replace-broad-fixup-placeholders.md
- 024-001 found no decoded fixup records or precise per-fixup placeholders to
  expose.

## Required Sign-Off

- [ ] Focused Mac project/artifact/web/source tests pass.
- [ ] Platform executable validate/coverage pass.
- [ ] `git diff --check` passes.
