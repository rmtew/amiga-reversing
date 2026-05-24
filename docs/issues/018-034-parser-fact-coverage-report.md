# 018-034: Parser Fact Coverage Report

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Blocked by: `docs/issues/018-033-platform-executable-generated-fact-table.md`
- Purpose: report parser-emitted executable-format facts against the KB so
  accepted, candidate, deferred, unsupported, and invalid claims are visible in
  one place.

## Knowledge Delta

No new platform facts are required. This issue adds coverage reporting over
existing facts and parser output.

The report should answer:

- which parser-emitted facts are accepted and parser-consumable;
- which emitted facts are candidate/deferred/unsupported and therefore not
  accepted authority;
- which emitted facts are missing from the KB or have invalid parser-use state;
- which platform/parser areas are unreported.

Completed report surface:

- `amiga_reversing.tools.platform_executable_formats coverage` reads one or more
  JSON parser-output files via `--parser-output` and emits a JSON report.
- The report classifies every emitted `kb_record_id`/`fact_id`/`fact_status`/
  `parser_use` mapping as `accepted`, `candidate`, `deferred`, `unsupported`, or
  `invalid`.
- The CLI returns failure when invalid mappings are present, including unknown
  fact ids and candidate/deferred facts claimed as accepted parser output.
- The report lists unreported records/platforms so Amiga and Atari remain
  visible as absent parser-output coverage rather than silently treated as
  covered.
- Current Mac C backend summary output is covered in tests with accepted,
  candidate, and deferred fact refs.

## Default Behavior

No default target parsing or rendering behavior changes. This is a report and
validation surface. If any parser output is found invalid, fail closed in tests
or report blockers rather than silently accepting it.

## Evidence Standard

The report must be generated from current parser output and current KB-derived
fact metadata. Hardcoded pass lists are not acceptable except as explicit test
fixtures.

## Implementation Slice

AFK slice:

- add or extend a CLI/report command for parser fact coverage;
- include Mac current parser output;
- include Amiga/Atari coverage if current parser outputs are available without
  broad parser rewrites;
- add tests that reject unknown accepted claims and candidate-as-accepted
  promotions;
- update Proposal 018 with the resulting gap summary.

## Research Completion Standard

Complete only after checking all current parser fact producers found by repo
search and doing a second-pass review for missed emitted fact ids.

## Research Coverage

- [x] Mac parser fact producers checked.
- [x] Amiga parser fact producers checked or explicitly recorded as absent.
- [x] Atari parser fact producers checked or explicitly recorded as absent.
- [x] Platform executable KB facts checked through generated table.
- [x] Second-pass search for emitted fact id strings completed.

## Research Review

- [x] Coverage report distinguishes accepted from candidate/deferred output.
- [x] Invalid fact ids fail tests or produce explicit blockers.
- [x] Report does not mutate target state or generated source.
- [x] Proposal 018 records remaining coverage gaps.

## Required Sign-Off

- [x] Coverage command/report test passes.
- [x] Platform executable format tests pass.
- [x] Relevant parser/listing tests pass.

## Completion Evidence

- `uv run python -m amiga_reversing.tools.platform_executable_formats coverage`
  emitted a no-payload report listing all records/platforms as unreported with
  zero invalid refs.
- `uv run python -m pytest tests/test_platform_executable_formats.py -q`
  passed.
- `uv run python -m pytest tests/test_macos_c_backend.py -q` passed.
- `uv run ruff check amiga_reversing/tools/platform_executable_formats.py
  tests/test_platform_executable_formats.py tests/test_macos_c_backend.py`
  passed.
