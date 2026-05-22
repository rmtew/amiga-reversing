# 018-006: Amiga/Atari Backfill Plan And First Records

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: incremental Amiga and Atari executable-format KB adoption
- Blocked by: `018-001` for accepted records; research may happen earlier
- Current proposal state: 018 is driven by the Mac blocker, but the shared
  authority must also cover Amiga and Atari without forcing immediate full
  parser rewrites.
- Desired proposal state after this issue: Amiga and Atari have an explicit
  backfill plan and first schema-valid records for their highest-value
  executable-bearing formats.

## Knowledge Delta

- Adds: Amiga and Atari backfill register plus first records.
- Changes: existing parser assumptions become visible debt when not yet
  KB-backed.
- Replaces: invisible legacy assumptions for touched parser areas.
- Deletes: none.
- Leaves out of scope: full Amiga/Atari parser migration, exhaustive manuals,
  and incompatible modern sources.

## Default Behavior

- Existing Amiga/Atari parser behavior remains unchanged.
- Backfill records do not become blocking until a parser area declares
  `kb_backed: true`.
- Modern incompatible sources are not KB inputs.

## Evidence Standard

- Sources may be old/out-of-print platform manuals/books, compatible modern
  sources, project-observed facts, or parser assertions.
- Version/toolchain scope must be recorded.
- Existing parser assumptions may be represented as parser assertions only with
  reason and review status.

## Implementation Slice

- Amiga: first record for HUNK executable/object basics or a narrower
  high-confidence slice.
- Atari ST: first record for GEMDOS PRG/TOS/TTP basics or a narrower
  high-confidence slice.
- Backfill register: record parser assumptions still needing citations.
- Tests: schema validation for first records.
- No parser behavior changes.

## Research Completion Standard

Record trace blocks for existing Amiga/Atari parser code, existing project
knowledge, allowed source candidates, first-record scope, and assumptions
deferred.

## Completion Evidence

- Added report-only records:
  `amiga.hunk.load_file.basic_backfill` and
  `atari_st.prg.gemdos_basic_backfill`.
- Added source entries for the normalized HUNK/PRG KBs and current parser files.
- Recorded the backfill register in `docs/platform-executable-formats.md`.
- Both records set `kb_backed: false`, keep all first-record facts
  candidate/deferred/unsupported, and do not authorize accepted parser output.
- No parser or renderer code changed for 018-006.

Verification:

```text
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.platform_executable_formats guardrails
uv run python -m pytest tests\test_platform_executable_formats.py -q
```

## Research Coverage

- [x] Existing Amiga executable parser assumptions inventoried.
- [x] Existing Atari executable parser assumptions inventoried.
- [x] Allowed source candidates checked.
- [x] First Amiga record scope selected.
- [x] First Atari record scope selected.
- [x] Backfill-required entries listed.

## Research Review

- [x] Second pass checked trace blocks against named files/functions.
- [x] First records do not overclaim unsupported formats.
- [x] Parser assertions have reason and review status.
- [x] Legacy behavior remains unchanged.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] 018-001 schema respected.
- [x] First Amiga record schema-valid.
- [x] First Atari record schema-valid.
- [x] Backfill register created.
- [x] No parser behavior changed.
- [x] Post-commit review found no unresolved worthwhile findings.
