# 018-008: Parser Output Fact Validation And Mac OS Rendering Cleanup

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: closing post-review gaps in KB-backed parser output and Mac
  source rendering
- Blocked by: `018-004`, `018-005`
- Current proposal state: 018 has a schema, KB, guardrail report, issue
  validator, and Mac parser/listing labels. Post-completion review found that
  parser-emitted fact ids are not yet mechanically validated against the KB and
  one Mac raw rendering path still expects Amiga-style `SECTION code,code`.
- Desired proposal state after this issue: every parser-emitted fact id/status
  used by KB-backed Mac output resolves to executable-format KB data with
  matching status/parser-use semantics, and Mac source rendering does not use
  Amiga section syntax on any Mac path.

## Knowledge Delta

- Adds: parser-output-to-KB validation and Mac rendering style cleanup.
- Changes: 018-004/018-005 are no longer treated as sufficient closeout for
  parser consumption until this issue passes.
- Replaces: ad hoc parser fact-id strings that are not checked against KB
  records.
- Deletes: Mac-path dependence on Amiga `SECTION code,code` output.
- Leaves out of scope: complete relocation/fixup interpretation, byte-level
  CODE entry validation, Amiga/Atari parser migration, and MPW roundtrip.

## Default Behavior

- Existing Amiga/Atari parser behavior remains unchanged.
- The current Mac `movea.l (a7)+,a0` boundary remains candidate-only.
- No candidate/deferred fact may become accepted parser output.
- If a parser summary emits a `fact_id`, `fact_status`, or `parser_use`, it
  must be validated against `knowledge/platform_executable_formats.json`.

## Evidence Standard

- A parser-emitted `fact_id` must resolve to an item in the referenced KB
  record: sections, entrypoints, facts, or review items. Citation packet ids or
  `fact_candidate_id` values are not valid parser facts unless there is also a
  corresponding KB item/fact with the emitted id.
- Emitted `fact_status` and `parser_use` must match the resolved KB item.
- `accepted_parser_output` is legal only for `validated` or `parser_asserted`
  facts.
- `candidate_only`, `deferred_only`, and `unsupported_only` must remain
  non-accepted output.
- Mac source output must not contain Amiga-only section directives on any Mac
  target, artifact, project-payload, or raw CODE listing path.

## Implementation Slice

- Add a reusable test/helper that walks Mac parser summaries and validates every
  emitted `kb_record_id`, `fact_id`, `fact_status`, and `parser_use` against
  the executable-format KB.
- Fix the current invalid emitted fact id
  `macos.segment_loader.code_resources`: either emit the accepted KB item id
  such as `macos.resource_fork.code_resources.accepted`, or add a real KB item
  with the emitted id and matching validated status.
- Replace or validate C hardcoded fact-id/status/parser-use strings. Preferred:
  generate a small C fact table/header from the KB. Acceptable first step:
  tests fail if C-emitted constants drift from KB records.
- Update Mac raw CODE rendering so `tests/test_macos_asm_container.py` no
  longer expects `SECTION code,code`.
- Add regressions covering target artifact, project payload, C summary, and raw
  Mac CODE listing output.
- Update 012/018 docs if the accepted/deferred state changes.

## Research Completion Standard

Record trace blocks for:

- every parser/API field that emits `kb_record_id`, `fact_id`, `fact_status`,
  or `parser_use`;
- the KB lookup path used by tests/tooling;
- every Mac rendering path that can produce source text;
- the reason any remaining hardcoded C constants are temporarily allowed.

## Completion Evidence

- Added `validate_parser_fact_references()` and `record_item_by_id()` to
  `amiga_reversing.tools.platform_executable_formats`.
- Fixed the C-emitted code-segment fact id from
  `macos.segment_loader.code_resources` to
  `macos.resource_fork.code_resources.accepted`.
- Added parser-output validation over real Mac C summaries and Mac project
  payloads.
- Added negative tests for citation-packet `fact_candidate_id` misuse and
  status/parser-use drift.
- Added a C constant drift test for Mac fact-id string literals.
- Updated the raw Mac CODE listing test to use the Mac listing adapter and
  assert `SECTION code,code` is absent.
- Kept `macos.code_resource.movea_stack_a0.boundary.candidate` candidate-only;
  byte-entry and relocation/fixup semantics remain deferred/candidate.

Verification:

```text
cmd /c src\build.bat
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.validate_018_issues
uv run python -m pytest tests\test_platform_executable_formats.py tests\test_macos_c_backend.py tests\test_macos_project_payload.py tests\test_macos_asm_container.py tests\test_macos_target_artifact.py -q
uv run ruff check amiga_reversing\tools\platform_executable_formats.py amiga_reversing\disasm\macos_project_payload.py tests\test_platform_executable_formats.py tests\test_macos_c_backend.py tests\test_macos_project_payload.py tests\test_macos_asm_container.py
```

## Research Coverage

- [x] C parser summary fact-id fields inventoried.
- [x] Python project-payload/listing/artifact fact-id fields inventoried.
- [x] KB fact lookup helper designed against record sections, entrypoints,
  facts, and review items.
- [x] Existing Mac raw CODE rendering path checked.
- [x] Tests covering invalid citation-packet/fact-candidate ids planned.
- [x] 012/018 blocker wording checked after implementation.

## Research Review

- [x] Second pass checked all emitted fact ids resolve to KB items.
- [x] Second pass checked emitted status/parser-use matches KB status/parser-use.
- [x] Negative test fails when parser emits citation packet ids as fact ids.
- [x] Negative test fails when candidate output is marked accepted.
- [x] No Mac source path emits `SECTION code,code`.
- [x] Remaining deferred Mac CODE entry/relocation facts are still documented as
  deferred/candidate.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Parser-output-to-KB validation exists and is tested.
- [x] Invalid `macos.segment_loader.code_resources` parser fact id resolved.
- [x] C fact constants are generated from KB or drift-tested against KB.
- [x] Mac raw CODE rendering no longer uses Amiga `SECTION code,code`.
- [x] Target artifact, project payload, C summary, and raw Mac CODE tests pass.
- [x] `amiga_reversing.tools.platform_executable_formats validate` passes.
- [x] `amiga_reversing.tools.validate_018_issues` passes.
- [x] Post-commit review found no unresolved worthwhile findings.
