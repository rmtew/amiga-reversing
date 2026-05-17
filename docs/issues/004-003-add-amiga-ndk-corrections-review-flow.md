# 004-003 Add Amiga NDK Corrections Review Flow

Status: Implemented
Source proposal: `docs/proposals/004-amiga-platform-knowledge.md`
Created: 2026-05-17

## Problem

`knowledge/amiga_ndk_corrections.json` records `review_status`, but there is no
operable review flow. Seeded and validated corrections are visible in data, yet
developers cannot list or promote them through a checked command.

## Scope

Add commands under the platform KB tool:

```powershell
uv run amiga-platform-kb corrections list
uv run amiga-platform-kb corrections check
uv run amiga-platform-kb corrections promote <id> --reviewer <name>
```

The command should preserve the existing JSON shape unless a small schema
cleanup is needed to make correction ids stable.

## Acceptance Criteria

- `list` shows id, category, affected symbol/function/structure, source file,
  citation, reason, and review status.
- `check` fails on unknown statuses, missing citations, duplicate ids, or
  validated entries without review provenance.
- `promote` changes only the selected correction from `seeded` to `validated`
  and records reviewer/date while preserving citation/source fields.
- Generation may continue consuming corrections, but reports distinguish seeded
  review debt from validated facts.
- Tests cover list, check, successful promote, and rejected promote cases.

## Non-Goals

- Automatically validate corrections against external sources.
- Bulk-promote seeded corrections.
- Add more corrections.

## Verification

```text
uv run amiga-platform-kb corrections list
uv run amiga-platform-kb corrections check
focused corrections review tests
cmd /c src\precommit.bat
```

## Implementation Notes

- Added `amiga-platform-kb corrections list/check/promote`.
- Correction ids are stable derived ids unless an entry already has `id`.
- `check` reports unknown statuses, missing citations, duplicate ids, and
  validated entries without review provenance.
- `promote` updates only one seeded entry to `validated` and records
  `reviewed_by`/`reviewed_at`.
- Existing validated correction metadata now records review provenance.
