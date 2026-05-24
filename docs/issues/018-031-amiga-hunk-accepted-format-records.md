# 018-031: Amiga HUNK Accepted Format Records

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Blocked by: `docs/issues/018-030-executable-kb-restart-and-state-sync.md`
- Purpose: move a narrow Amiga HUNK executable-format slice from report-only
  inventory toward accepted or parser-asserted KB records where committed local
  citations already justify that status.
- This issue must not touch Mac parser/listing/web files.

## Knowledge Delta

Add or update only narrow Amiga HUNK facts that can be justified from committed
local knowledge:

- HUNK file identification;
- executable/object/library distinction where already documented;
- section/block roles needed by existing parser behavior;
- relocation or symbol-table facts only if the committed evidence is strong
  enough for accepted/parser-asserted status.

Facts without sufficient evidence must stay candidate/deferred/report-only with
explicit blocker reasons.

Completed delta:

- Promoted `amiga.hunk.load_file.basic_backfill` from record-level
  `fact_state=candidate` and `kb_backed=false` to
  `fact_state=parser_asserted` and `kb_backed=true`.
- Kept the accepted slice narrow: HUNK_HEADER load-file identity,
  HUNK_UNIT/HUNK_LIB/HUNK_INDEX object/library container identity,
  HUNK_CODE/HUNK_DATA/HUNK_BSS section roles, and size-only HUNK_BSS.
- Kept relocation breadth, symbol/EXT details, runtime entry policy,
  overlay/loader variants, and full parser migration
  candidate/deferred/unsupported.
- Updated tests so unsupported/candidate promotion still fails closed and the
  record-level authority boundary is explicit.

## Default Behavior

Default parser behavior should remain unchanged unless the change is validation
or reporting only. Do not rework Amiga import or rendering as part of this
issue.

## Evidence Standard

Accepted facts require committed source citations or parser assertions that
explain the standard interpretation. Candidate/deferred facts must not be
consumed as accepted parser authority.

## Implementation Slice

AFK slice:

- audit current Amiga HUNK knowledge and parser assumptions;
- update the platform executable KB with the smallest justified accepted or
  parser-asserted Amiga record;
- update tests/validators so unsupported promotions fail closed;
- update Proposal 018 observations with remaining Amiga gaps.

## Research Completion Standard

Complete only after a first-pass inventory and a second-pass review against
current parser behavior. If evidence is insufficient, complete by recording a
blocked/candidate result rather than forcing accepted facts.

Completed with a first pass over `knowledge/amiga_hunk_file.json`,
`src/platform_amiga_hunk.c`, existing KB record state, and current platform
executable tests, followed by a second pass over the accepted parser-asserted
facts and candidate/deferred fields before editing.

## Completion Evidence

- `uv run python -m amiga_reversing.tools.platform_executable_formats validate`
  passed.
- `uv run python src/scripts/generate_platform_format_runtime.py` refreshed the
  KB-derived generated table.
- `uv run python -m pytest tests/test_platform_executable_formats.py -q` passed.
- `uv run python -m pytest tests/test_validate_018_issues.py -q` passed.

## Research Coverage

- [x] Current Amiga HUNK knowledge files checked.
- [x] Existing HUNK parser/report behavior checked.
- [x] Existing 018 Amiga report-only record checked.
- [x] Citation strength reviewed for every promoted fact.
- [x] Second-pass review checked for accidental parser behavior changes.

## Research Review

- [x] Accepted/parser-asserted facts have citations or assertion rationale.
- [x] Candidate/deferred facts are not consumed as accepted.
- [x] Mac and Atari files were not changed.
- [x] Proposal 018 records remaining Amiga gaps.

## Required Sign-Off

- [x] KB validation passes.
- [x] Targeted tests for platform executable formats pass.
- [x] No target source/render artifact churn was committed; only the
  KB-derived generated fact table changed.
