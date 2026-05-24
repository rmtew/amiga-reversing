# 020-007: Analysis-State Executable Import

Status: active
Type: AFK
Source proposal: docs/proposals/020-platform-executable-import-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/020-platform-executable-import-pipeline.md`
- Blocked by: 020-003, 020-004, and 020-005.
- Current state: parser summaries and listing output can expose executable
  structure, but analysis state should not re-derive executable range roles from
  ad hoc platform JSON.
- Desired state after this issue: analysis import consumes the shared
  executable model as durable facts.

## What To Build

Feed shared executable ranges into analysis state through one import path. The
analysis state should receive range roles, source byte spans, provenance,
KB fact refs, candidate/deferred/unsupported markers, and stable identity.

This issue should choose the smallest current target/fixture set that proves the
path across all migrated platforms without broad target mutation.

## Acceptance Criteria

- [ ] A shared parser-summary-to-analysis import path exists.
- [ ] Amiga migrated ranges can enter analysis state through that path.
- [ ] Atari migrated ranges can enter analysis state through that path.
- [ ] Mac migrated ranges can enter analysis state through that path.
- [ ] Analysis facts preserve KB fact refs and non-accepted states.
- [ ] Tests prove analysis import does not reclassify candidate/deferred facts
  as accepted code.

## Blocked By

- 020-003
- 020-004
- 020-005

## Required Sign-Off

- [ ] No platform-specific analysis side route remains for migrated behavior.
- [ ] No broad target regeneration unless required by the tests.
- [ ] Parser coverage still passes.
- [ ] Focused analysis/import tests pass.
- [ ] `git diff --check` passes.

## Completion Evidence

Record the analysis-state fact shape and a small proof for each platform.
