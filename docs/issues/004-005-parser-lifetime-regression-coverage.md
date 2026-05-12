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

- [x] Tests cover at least one migrated parser result surviving Workflow Arena teardown.
- [x] Tests or assertions cover Result Arena teardown for parser results.
- [x] Round-trip or container checks cover the migrated parser paths.
- [x] Before committing, run `uv run python -m pytest tests\test_web_e2e_cdp.py -q`.
- [x] Before committing, run `cmd /c src\precommit.bat`.

## Work notes required

- Record raw heap allocation sites before/after for touched modules.
- Record arena stats if the touched workflow exposes them.
- Record exact CDP and precommit command results before commit.

## Work notes

- Added `test_hunk_parser_result_survives_workflow_teardown` in
  `src/test_m68k_container_metadata.c`.
- The test parses a HUNK executable, then reads returned section bytes after the parser workflow has
  already been destroyed by `read_buffer`.
- The same test destroys the `M68kObject` and asserts Result Arena teardown clears result ownership
  fields.
- Existing container and round-trip checks in `src/test_m68k_container_metadata.c` continue to cover
  HUNK and Atari container writer/reproduction behavior.
- Raw heap allocation sites: no production sites changed; test-only caller output cleanup sites in
  `src/test_m68k_container_metadata.c` are unchanged in count.
- Arena stats: not applicable; this is regression coverage only.
- `cmd /c src\precommit.bat`: passed. Summary: style OK, dead_code OK, unit OK, integration OK, explicit OK.
- `uv run python -m pytest tests\test_web_e2e_cdp.py -q`: first run hit a transient
  `facts_v2 render preview build failed`; isolated rerun passed, then full rerun passed with
  `29 passed in 80.91s`.

## Blocked by

- [004-001 Amiga HUNK Parser Ownership Split](004-001-amiga-hunk-parser-ownership-split.md)
- [004-002 Atari Parser Ownership Split](004-002-atari-parser-ownership-split.md)
- [004-003 Platform Disk Container Parser Ownership Split](004-003-disk-container-parser-ownership-split.md)
- [004-004 Atari Disk Parser Ownership Split](004-004-atari-disk-parser-ownership-split.md)
