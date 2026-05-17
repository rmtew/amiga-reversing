# 030-001 Add Platform KB Coverage Report

Status: Ready
Source proposal: `docs/proposals/004-amiga-platform-knowledge.md`
Created: 2026-05-17

## Problem

Amiga platform KB state is spread across generated JSON, markdown inventory,
tests, and generated C metadata. There is no single command that reports what
is parsed, reviewed, unsupported, or half-represented.

## Scope

Add a command surface:

```powershell
uv run amiga-platform-kb report
uv run amiga-platform-kb check
```

The first implementation should read committed artifacts. It must not require a
local NDK install just to report current repository state.

Report sections:

- source inventory status
- NDK include/library/function/struct/constant/value-domain counts
- function `available_since` counts
- hardware register and bitfield coverage
- NDK hardware symbol coverage
- correction review-status counts
- HUNK enum, record-type, valid-load-record, and unsupported/half-represented state

## Acceptance Criteria

- `report` prints stable human-readable counts for the current repository.
- `check` fails on malformed correction review statuses, missing correction
  citations, and half-represented HUNK records.
- Initial HUNK check identifies `HUNK_OVERLAY` state cleanly instead of relying
  on hidden consumer behavior.
- Tests cover report aggregation from fixture artifacts.

## Non-Goals

- Reparse ADCD or NDK sources.
- Add new platform facts.
- Change runtime HUNK behavior.

## Verification

```text
uv run amiga-platform-kb report
uv run amiga-platform-kb check
focused platform KB report tests
cmd /c src\precommit.bat
```
