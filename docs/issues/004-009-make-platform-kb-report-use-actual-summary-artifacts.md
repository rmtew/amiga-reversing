# 004-009 Make Platform KB Report Use Actual Summary Artifacts

Status: Done
Source proposal: `docs/proposals/004-amiga-platform-knowledge.md`
Created: 2026-05-17

## Problem

`amiga-platform-kb report` only scans `targets/*/platform_summary.json`, but
the implemented analysis path exposes `platform_summary` inside
`source_analysis.json`.

The live report can therefore say target summary schema is absent even when the
implemented summary exists in source-analysis output.

## Scope

- Teach the report to discover committed target platform summaries from the
  actual artifact shape.
- Prefer standalone `platform_summary.json` if present.
- Fall back to `source_analysis.json.platform_summary`.
- Report which artifact source was used.
- Keep `target-gaps` and `report` using the same summary loading helper.

## Acceptance Criteria

- Report counts `observed`, `no_os_calls`, and `unknown` from embedded
  `source_analysis.json.platform_summary`.
- Report still supports standalone `platform_summary.json` fixtures.
- Report output distinguishes standalone and embedded summary sources.
- `check` fails if summary artifacts are malformed, but not merely absent for
  targets that have no committed analysis output.
- Tests cover standalone summary, embedded summary, and missing summary.

## Verification

```text
focused platform KB report tests
uv run amiga-platform-kb report
uv run amiga-platform-kb check
cmd /c src\precommit.bat
```

## Implementation Notes

- Added one platform-summary artifact loader for report and target-gap paths.
- `amiga-platform-kb report` now prefers `platform_summary.json` and falls
  back to `source_analysis.json.platform_summary`.
- Report output includes artifact source counts so standalone and embedded
  summaries are visible.
- Strict check reports malformed summary artifacts but does not fail just
  because a target has no committed analysis summary.

## Verified

```text
uv run python -m pytest tests\test_platform_kb.py -q
uv run ruff check amiga_reversing\tools\platform_kb.py tests\test_platform_kb.py
uv run amiga-platform-kb report
uv run amiga-platform-kb check
```
