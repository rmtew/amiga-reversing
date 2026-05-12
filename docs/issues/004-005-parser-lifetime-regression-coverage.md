# Parser Lifetime Regression Coverage

Type: AFK

## Parent

[004 Parser Workflow and Result Split](../prd/004-parser-workflow-result-split.md)

## Candidate files

- migrated parser tests in `src/test_*.c`
- parser paths changed by issues `004-001` through `004-004`

## What to build

Add parser lifetime regression coverage that proves returned parser results survive workflow teardown and are released by result teardown.

## Acceptance criteria

- [ ] Tests cover at least one migrated parser result surviving Workflow Arena teardown.
- [ ] Tests or assertions cover Result Arena teardown for parser results.
- [ ] Round-trip or container checks cover the migrated parser paths.
- [ ] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [ ] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Blocked by

- [004-001 Amiga HUNK Parser Ownership Split](004-001-amiga-hunk-parser-ownership-split.md)
- [004-002 Atari Parser Ownership Split](004-002-atari-parser-ownership-split.md)
- [004-003 Platform Disk Container Parser Ownership Split](004-003-disk-container-parser-ownership-split.md)
- [004-004 Atari Disk Parser Ownership Split](004-004-atari-disk-parser-ownership-split.md)
