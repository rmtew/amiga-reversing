# 004-007 Fix Raw Amiga OS Version Ranking

Status: Done
Source proposal: `docs/proposals/004-amiga-platform-knowledge.md`
Created: 2026-05-17

## Problem

Raw Amiga OS availability ordering is required to be:

```text
1.0 < 1.1 < 1.2 < 1.3 < 2.0 < 2.04 < 2.1 < 3.0 < 3.1 < 3.5
```

The generated runtime currently ranks dotted versions by numeric components.
That makes `2.1` rank lower than `2.04`, so target summaries can choose the
wrong maximum OS requirement.

## Scope

- Replace generic dotted-version ranking with the explicit Amiga OS rank model.
- Generate the same rank table into C runtime metadata.
- Use the generated rank helper for target platform summary aggregation.
- Keep raw `available_since` strings unchanged.
- Keep normalized compatibility enum as derived data only.

## Acceptance Criteria

- `2.04` sorts before `2.1`.
- `2.1` sorts before `3.0`.
- A target with observed calls at `2.04` and `2.1` reports minimum required
  `2.1`.
- Source OS compatibility header and source-analysis JSON agree on the maximum.
- Tests cover raw `1.2`, `2.04`, `2.1`, `3.0`, and `3.1` ordering.

## Verification

```text
focused runtime OS rank tests
focused target platform summary tests
uv run amiga-platform-kb check
cmd /c src\precommit.bat
```

## Implementation Notes

- Replaced generic dotted-version ranking in the Amiga OS runtime generator
  with the explicit Amiga OS release order.
- Regenerated `src/generated/amiga_os_runtime.c`; raw `2.04` now ranks before
  `2.1`, and `2.1` ranks before `3.0`.
- Added C coverage for raw OS rank ordering and Python coverage for the report
  helper ordering.

## Verified

```text
uv run python -m pytest tests\test_platform_kb.py -q
uv run amiga-platform-kb check
cmd /c src\precommit.bat
```
