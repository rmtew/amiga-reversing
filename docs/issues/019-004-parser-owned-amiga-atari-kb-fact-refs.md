# 019-004: Parser-Owned Amiga/Atari KB Fact Refs

Status: active
Type: AFK
Source proposal: docs/proposals/019-platform-executable-kb-parser-consumption.md

## Proposal Context

- Source proposal: `docs/proposals/019-platform-executable-kb-parser-consumption.md`
- Current proposal state: 019-001 through 019-003 added current coverage hooks,
  but review of `43555c72` found Amiga/Atari `fact_refs` are synthesized by
  `platform_executable_formats.py` after parser inspection.
- Desired proposal state after this issue: Amiga HUNK and Atari ST PRG parser
  owned summaries carry executable-format KB refs directly, and coverage
  validates those refs without inventing them.

## Required Work

- Move Amiga HUNK KB ref emission onto the parser/import summary surface
  returned by `platform_file_inspect_path_json_alloc` for the `amiga-hunk`
  backend.
- Move Atari ST PRG KB ref emission onto the parser/import summary surface
  returned by `platform_file_inspect_path_json_alloc` for the `atari-st`
  backend.
- Keep fact states faithful to `knowledge/platform_executable_formats.json`;
  do not promote candidate/deferred facts.
- Keep `coverage --current-amiga-hunk` and `coverage --current-atari-prg`, but
  make them consume parser-owned refs. They may label sources and aggregate
  reports; they must not construct executable-format `fact_refs` from section
  kinds or fixture assumptions.
- Preserve the combined current coverage gate:

```powershell
uv run python -m amiga_reversing.tools.platform_executable_formats coverage `
  --current-macos-c-backend `
  --current-amiga-hunk `
  --current-atari-prg
```

## Non-Negotiable Boundary

The following is not sufficient:

```text
run parser -> inspect sections -> build fact_refs in coverage helper
```

The required shape is:

```text
run parser -> parser/import summary already contains KB refs -> coverage validates
```

If the cleanest implementation is in the C JSON producer, use that. If the
cleanest implementation is a shared parser/import summary wrapper used by all
consumers, it must still be upstream of coverage and covered by raw-summary
tests. Do not add a second legacy compatibility path.

## Tests

- Add or adjust tests that call the raw Amiga HUNK parser summary path and
  assert it contains `kb_record_id`, `fact_id`, `fact_status`, and `parser_use`
  before coverage wrapping.
- Add or adjust tests that call the raw Atari ST PRG parser summary path and
  assert it contains `kb_record_id`, `fact_id`, `fact_status`, and `parser_use`
  before coverage wrapping.
- Add regression coverage proving `coverage` no longer synthesizes Amiga/Atari
  fact refs when the raw parser summary omits them.
- Keep existing invalid-claim coverage behavior.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] Raw Amiga parser/import summary emits KB refs before coverage wrapping.
- [ ] Raw Atari parser/import summary emits KB refs before coverage wrapping.
- [ ] Coverage consumes Amiga/Atari refs unchanged except for source labeling
  and aggregation.
- [ ] No candidate/deferred/unsupported fact is promoted.
- [ ] No broad parser rewrite or legacy compatibility path added.
- [ ] `uv run python -m amiga_reversing.tools.platform_executable_formats validate`
  passes.
- [ ] Combined current coverage gate reports `parser_outputs: 3`, `invalid: 0`,
  and `unreported_platforms: []`.
- [ ] Focused platform executable tests pass.
- [ ] `ruff` and `git diff --check` pass.

## Completion Evidence

Record the final raw-summary proof for Amiga and Atari, the combined coverage
summary, focused test output, and any proposal observations before closing this
issue.
