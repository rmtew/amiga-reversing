# 018-033: Platform Executable Generated Fact Table

Status: active

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Blocked by: `docs/issues/018-030-executable-kb-restart-and-state-sync.md`
- Best started after: `docs/issues/018-031-amiga-hunk-accepted-format-records.md`,
  `docs/issues/018-032-atari-prg-accepted-format-records.md`, and
  `docs/issues/018-037-macos-blocker-resolution-or-final-deferral.md`, if they
  finish cleanly.
- Purpose: make platform executable fact ids/status/parser-use values available
  through generated constants or tables instead of string-only scattered usage.

## Knowledge Delta

The KB remains the source of truth. This issue adds generated consumer-facing
facts derived from the KB. It must not alter fact meaning to fit the generator.

Generated output should preserve at least:

- fact id;
- platform;
- fact state;
- parser-use authority;
- owning record/archetype where applicable.

## Default Behavior

Default parser behavior should remain unchanged unless a consumer is switched
from a literal fact string to the generated equivalent with identical output.

## Evidence Standard

Generation must be reproducible from committed KB input. Tests must fail if a
generated table drifts from the KB or if a parser consumes a fact id that is not
present with the required parser-use authority.

## Implementation Slice

AFK slice:

- define the smallest generated table or constants shape needed by current
  parser/listing/report code;
- generate or update the file from `knowledge/platform_executable_formats.json`;
- update current platform executable tests to assert freshness;
- switch one low-risk consumer or report path if it removes literal duplication
  without changing behavior.

## Research Completion Standard

Complete only after checking current generator patterns and current parser fact
validation. Do not add a second source of truth; generated files must be
mechanical outputs of the KB.

## Research Coverage

- [ ] Existing generated-code patterns checked.
- [ ] Platform executable KB schema checked.
- [ ] Current parser fact validation checked.
- [ ] Current Mac parser fact literal use checked.
- [ ] Second-pass freshness/drift review completed.

## Research Review

- [ ] Generated facts preserve KB state and parser-use authority.
- [ ] Unknown or candidate-only facts cannot become accepted through generation.
- [ ] Tests prove generated output is fresh.
- [ ] Any consumer switch is behavior-preserving.

## Required Sign-Off

- [ ] Generation/freshness test passes.
- [ ] Platform executable format tests pass.
- [ ] Ruff/mypy or targeted static checks pass where touched.
