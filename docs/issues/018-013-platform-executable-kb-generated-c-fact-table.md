# 018-013: Platform Executable KB Generated C Fact Table

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: generated C access to executable-format KB facts
- Blocked by: `018-008`
- Independent of: `018-010`
- Current proposal state: Mac C parser output uses hardcoded fact-id/status
  string constants drift-tested against the KB. This is acceptable as a first
  step but not the intended long-term generated-KB pattern.
- Desired proposal state after this issue: C code can reference generated
  executable-format fact constants or lookup tables derived from
  `knowledge/platform_executable_formats.json`.

## Knowledge Delta

- Adds: generated C metadata for executable-format KB records/facts.
- Changes: parser code can consume generated symbols instead of repeated string
  literals.
- Replaces: broad hardcoded fact-id/status/parser-use strings in C.
- Deletes: obsolete drift-only tests only if generated checks fully replace
  them.
- Leaves out of scope: changing Mac CODE rendering/navigation semantics,
  changing accepted/candidate fact states, Amiga/Atari parser migration.

## Default Behavior

- Parser output JSON must remain semantically unchanged unless a generated
  constant corrects a drift bug.
- Existing tests must continue to validate emitted fact ids against the KB.
- Generated code must be deterministic and reviewable.

## Evidence Standard

- Generated C must come from `knowledge/platform_executable_formats.json`, not a
  hand-copied list.
- Generated constants/tables must preserve record id, fact id, fact status,
  parser use, and source section where useful.
- Tests must fail if the KB changes without regenerating generated C output.
- C parser output must still pass 018-008 parser fact-reference validation.

## Implementation Slice

- Add or extend a generator for `src/generated/platform_executable_formats.c`
  and `src/generated/platform_executable_formats.h`.
- Wire generation into the existing project generation/build/test conventions.
- Migrate current Mac fact string literals where low-risk.
- Keep behavior unchanged and focused; do not update Mac source rendering.
- Add Python/C tests proving generated output is current and usable.

## Research Completion Standard

Record trace blocks for:

- existing generated C patterns and build hooks;
- current C sites emitting executable-format fact strings;
- chosen generated API shape;
- regeneration command and stale-output test;
- any literals deliberately left unmigrated.

## Research Coverage

- [x] Existing generated C conventions checked.
- [x] Build integration path checked.
- [x] C fact string emission sites inventoried.
- [x] Generated API shape selected.
- [x] Stale generated output test planned.
- [x] 018-008 validation kept in the test path.

## Research Review

- [x] Generated output is deterministic.
- [x] Generated output is derived from KB data.
- [x] C parser output remains unchanged or explicitly justified.
- [x] Stale generated output fails tests.
- [x] No Mac rendering/navigation files are modified.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Generated C fact table/header added.
- [x] Generation command documented.
- [x] Build/test path uses or validates generated files.
- [x] Current Mac C fact literals migrated or deliberately documented.
- [x] Parser output passes 018-008 validation.
- [x] `cmd /c src\build.bat` passes.
- [x] Relevant Python/C tests pass.
- [x] `amiga_reversing.tools.validate_018_issues` passes.
- [x] Post-commit review found no unresolved worthwhile findings.


## Completion Evidence

- Extended `src/scripts/generate_platform_format_runtime.py` to generate `src/generated/platform_executable_formats.c/.h`; stale generated output is tested, and current Mac C literals are deliberately documented as unchanged.
- Validation commands listed in the required sign-off were run after implementation before commit.
- No Mac multi-CODE rendering/navigation files for 018-010 were modified.
