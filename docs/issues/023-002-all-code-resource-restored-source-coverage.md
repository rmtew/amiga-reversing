# 023-002: All CODE Resource Restored-Source Coverage

Status: active
Type: AFK
Source proposal: docs/proposals/023-classic-mac-os-source-presentation.md

## Proposal Context

- 022 proved C-owned restored-source authority for the selected Mac CODE path.
- 023 requires source presentation across executable CODE resources, not only
  the currently selected CODE resource.

## What To Build

Extend the Mac source model so every executable CODE resource in the committed
fixture has one of:

- a C-owned restored-source packet with ownership ranges and verifier result; or
- a typed deferred source placeholder with resource identity, reason, status,
  provenance, and source-visible presentation.

CODE 0 may remain metadata/routing, but it must be represented explicitly rather
than omitted from the source presentation model.

## Acceptance Criteria

- [ ] The Mac project/artifact/API path exposes per-CODE restored-source status.
- [ ] Executable CODE resources are not silently omitted.
- [ ] C-owned verifier results cover rendered CODE resources.
- [ ] Deferred CODE resources have typed placeholders with stable identity.
- [ ] Compatibility fields are not treated as restored-source authority.
- [ ] Proposal 023 records the completed per-CODE coverage result.

## Blocked By

- docs/issues/023-001-mac-source-presentation-baseline-harness.md

## Required Sign-Off

- [ ] 023-001 baseline proof updated to require the new per-CODE behavior.
- [ ] Focused Mac tests pass.
- [ ] Platform executable validate/coverage pass.
- [ ] `cmd /c src\precommit.bat` passes if shared C source/render code changes.
- [ ] `git diff --check` passes.
