# 004-011 Structure Platform Source Inventory

Status: Done
Source proposal: `docs/proposals/004-amiga-platform-knowledge.md`
Created: 2026-05-17

## Problem

The platform KB report derives source inventory counts by scraping markdown
table text from `knowledge/adcd21_inventory.md`.

The proposal requires source ownership/counts/statuses to come from structured
data, while markdown remains human narrative.

## Scope

- Add a machine-readable platform source inventory artifact.
- Represent source statuses such as `parsed`, `parser_asserted`,
  `seeded_correction`, `validated_correction`, `candidate`, `deferred`, and
  `unsupported`.
- Make `amiga-platform-kb report` read the structured artifact.
- Keep `knowledge/adcd21_inventory.md` as narrative or generated summary, not
  the source of truth for counts.
- Add checks for unknown inventory statuses and duplicate source ids.

## Acceptance Criteria

- Source inventory report no longer parses markdown table text.
- Report distinguishes parsed, candidate, deferred, and unsupported sources
  from structured data.
- Check fails on unknown statuses or duplicate source ids.
- Markdown inventory and structured inventory cannot silently drift.

## Verification

```text
focused platform KB inventory tests
uv run amiga-platform-kb report
uv run amiga-platform-kb check
cmd /c src\precommit.bat
```

## Implementation Notes

- Added `knowledge/platform_source_inventory.json` as the machine-readable
  source inventory.
- `amiga-platform-kb report` now uses the structured artifact for source
  counts and status grouping.
- Markdown inventory remains narrative; checks compare markdown paths with the
  structured inventory so drift is reported.
- Strict check reports duplicate ids, duplicate paths, unknown statuses, and
  markdown/JSON path drift.

## Verified

```text
uv run python -m pytest tests\test_platform_kb.py -q
uv run ruff check amiga_reversing\tools\platform_kb.py tests\test_platform_kb.py
uv run amiga-platform-kb report
uv run amiga-platform-kb check
```
