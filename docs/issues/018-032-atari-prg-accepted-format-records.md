# 018-032: Atari ST PRG Accepted Format Records

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Blocked by: `docs/issues/018-030-executable-kb-restart-and-state-sync.md`
- Purpose: move a narrow Atari ST PRG/TOS/TTP executable-format slice from
  report-only inventory toward accepted or parser-asserted KB records where
  committed local citations already justify that status.
- This issue must not touch Mac parser/listing/web files.

## Knowledge Delta

Add or update only narrow Atari ST facts that can be justified from committed
local knowledge:

- executable header identity and text/data/bss shape;
- relocation-table presence and parser-visible role where documented;
- symbol-table/debug records only if evidence is strong enough;
- TOS/TTP/PRG distinctions only where committed evidence supports them.

Facts without sufficient evidence must stay candidate/deferred/report-only with
explicit blocker reasons.

Completed delta:

- Promoted `atari_st.prg.gemdos_basic_backfill` from record-level
  `fact_state=candidate` and `kb_backed=false` to
  `fact_state=parser_asserted` and `kb_backed=true`.
- Kept the accepted slice narrow: 0x601A PRG magic,
  PRG_HEADER/TEXT/DATA/optional SYMBOL_TABLE/optional RELOCATION_STREAM
  sequence, TEXT/DATA/BSS region shape, and TEXT+DATA loaded-image relocation
  target space.
- Kept relocation-stream terminator variants, symbol-table details, GEMDOS
  basepage/runtime entry state, and full parser migration
  candidate/deferred/unsupported.
- Updated tests so candidate/deferred promotion still fails closed and the
  record-level authority boundary is explicit.

## Default Behavior

Default parser behavior should remain unchanged unless the change is validation
or reporting only. Do not rework Atari import or rendering as part of this
issue.

## Evidence Standard

Accepted facts require committed source citations or parser assertions that
explain the standard interpretation. Candidate/deferred facts must not be
consumed as accepted parser authority.

## Implementation Slice

AFK slice:

- audit current Atari executable knowledge and parser assumptions;
- update the platform executable KB with the smallest justified accepted or
  parser-asserted Atari record;
- update tests/validators so unsupported promotions fail closed;
- update Proposal 018 observations with remaining Atari gaps.

## Research Completion Standard

Complete only after a first-pass inventory and a second-pass review against
current parser behavior. If evidence is insufficient, complete by recording a
blocked/candidate result rather than forcing accepted facts.

Completed with a first pass over `knowledge/atari_st_prg_file.json`,
`src/platform_atari_st.c`, existing KB record state, and current platform
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

- [x] Current Atari ST executable knowledge files checked.
- [x] Existing Atari parser/report behavior checked.
- [x] Existing 018 Atari report-only record checked.
- [x] Citation strength reviewed for every promoted fact.
- [x] Second-pass review checked for accidental parser behavior changes.

## Research Review

- [x] Accepted/parser-asserted facts have citations or assertion rationale.
- [x] Candidate/deferred facts are not consumed as accepted.
- [x] Mac and Amiga files were not changed.
- [x] Proposal 018 records remaining Atari gaps.

## Required Sign-Off

- [x] KB validation passes.
- [x] Targeted tests for platform executable formats pass.
- [x] No target source/render artifact churn was committed; only the
  KB-derived generated fact table changed.
