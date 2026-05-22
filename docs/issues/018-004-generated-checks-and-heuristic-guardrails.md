# 018-004: Generated Checks And Heuristic Guardrails

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: generated validation and candidate/accepted parser boundaries
- Blocked by: `018-001`, at least one accepted platform record from `018-003`
- Current proposal state: facts can be represented, but tooling does not yet
  prevent candidate facts from being treated as accepted parser behavior.
- Desired proposal state after this issue: local tests/checks fail when a parser
  or renderer promotes heuristic-only executable facts.

## Knowledge Delta

- Adds: schema/data validation checks, accepted-vs-candidate guardrails, and
  reportable KB-backed parser coverage.
- Changes: 018-backed issues become mechanically harder to close prematurely.
- Replaces: purely manual review of heuristic promotion.
- Deletes: none.
- Leaves out of scope: migrating Mac parser/listing code, full precommit
  integration for legacy platforms, and rewriting historical parser behavior.

## Default Behavior

- Existing Amiga/Atari parser behavior remains unchanged.
- Existing Mac parser behavior remains unchanged until 018-005.
- Checks are blocking for new/adopted KB-backed parser slices and optional
  reports for legacy areas until they declare `kb_backed: true`.

## Evidence Standard

The guardrail must distinguish:

- validated/parser_asserted facts allowed for accepted parser output;
- candidate facts allowed only for reports/candidate ranges;
- deferred/unsupported facts that must emit placeholder, fail closed, or block
  closeout according to the KB.

## Implementation Slice

- Python tests/tooling: validate KB files and fact-state use.
- Generated checks: create the first check path from KB to parser expectation.
- Mac proof: show the current CODE entry heuristic cannot be labelled accepted
  without 018-003 validation.
- Proposal/issues: update if enforcement discovers missing issue protocol.

## Research Completion Standard

Record trace blocks for existing test/tool locations, schema validation method,
generated metadata patterns, and any check deliberately left report-only.

## Research Coverage

- [x] Existing KB/schema test patterns checked.
- [x] Existing generated metadata/check patterns checked.
- [x] Candidate-vs-accepted failure cases planned.
- [x] Mac heuristic guardrail planned.
- [x] Legacy report-only behavior scoped.

## Research Review

- [x] Second pass checked trace blocks against named files/functions.
- [x] Guardrails fail for candidate promotion.
- [x] Guardrails do not block untouched legacy parser behavior.
- [x] Proposal updated with enforcement rules or deferred follow-ups.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] KB validation checks added.
- [x] Candidate promotion failure tested.
- [x] Mac heuristic guardrail tested.
- [x] Legacy parser behavior unchanged unless explicitly adopted.
- [x] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

- Added `build_guardrail_report()` and the `guardrails` CLI mode to
  `amiga_reversing.tools.platform_executable_formats`.
- Guardrail report lists KB-backed records, report-only records, accepted
  parser fact ids, candidate-only fact ids, deferred fact ids, and unsupported
  fact ids.
- Added tests that candidate promotion fails and that the Mac
  `movea.l (a7)+,a0` candidate cannot become accepted parser output.
- Added tests that the 018-001 thin proof remains report-only while the
  018-003 Mac record is KB-backed.
- `uv run python -m pytest tests\test_platform_executable_formats.py -q`
  passed: 13 tests.
- `uv run python -m amiga_reversing.tools.platform_executable_formats guardrails`
  passed and emitted the expected report.
- `uv run ruff check amiga_reversing\tools\platform_executable_formats.py tests\test_platform_executable_formats.py`
  passed.
- Parser and renderer code paths were not changed.
