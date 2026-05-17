# 030-004 Resolve HUNK_OVERLAY Support State

Status: Ready
Source proposal: `docs/proposals/004-amiga-platform-knowledge.md`
Created: 2026-05-17

## Problem

`HUNK_OVERLAY` is half-represented:

- present in the HUNK enum
- present in `load_file_valid_record_types`
- absent from normalized generated record metadata
- documented in markdown without current parser/runtime fixture coverage

This creates implicit behavior around an unsupported container record.

## Scope

Make `HUNK_OVERLAY` either supported or explicitly unsupported.

Preferred path unless primary-source evidence and fixtures are available in the
same issue:

- remove `HUNK_OVERLAY` from valid load-file record types
- keep the enum id if useful for diagnostics
- report overlay as unsupported inventory in the platform KB report/check
- make consumers produce a clear unsupported-record diagnostic

Support path, if evidence is available:

- add cited normalized record metadata
- add a primary-source-backed fixture or vetted real sample
- add parser/runtime tests proving overlay layout and skip behavior

## Acceptance Criteria

- `HUNK_OVERLAY` is no longer half-represented.
- `amiga-platform-kb check` passes because overlay is either supported with
  tests or explicitly unsupported.
- Runtime behavior for overlay records is deliberate and tested.
- Proposal 004 is updated with the final decision.

## Non-Goals

- Guess overlay layout from secondary notes.
- Add UI features for overlays.
- Preserve current implicit unknown-record behavior.

## Verification

```text
uv run amiga-platform-kb check
focused HUNK parser/runtime tests
cmd /c src\precommit.bat
```
