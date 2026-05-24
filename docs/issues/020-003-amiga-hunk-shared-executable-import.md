# 020-003: Amiga HUNK Shared Executable Import

Status: active
Type: AFK
Source proposal: docs/proposals/020-platform-executable-import-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/020-platform-executable-import-pipeline.md`
- Blocked by: 020-002.
- Current state: Amiga HUNK emits parser-owned executable KB refs, but its
  executable structure is not yet migrated through the shared 020 model.
- Desired state after this issue: Amiga HUNK CODE/DATA/BSS structure flows
  through shared executable ranges.

## What To Build

Migrate the current Amiga HUNK inspect/current-output path onto the shared
executable model. CODE, DATA, and BSS must be represented as shared ranges.
Size-only BSS must preserve stored-size semantics. Runtime entry and relocation
breadth must remain candidate/deferred according to 018.

## Acceptance Criteria

- [ ] Current Amiga HUNK fixture emits shared executable ranges.
- [ ] CODE/DATA/BSS and size-only BSS are represented with KB fact refs.
- [ ] Runtime entry and relocation breadth remain candidate/deferred where
  applicable.
- [ ] Coverage consumes the shared model without Amiga-specific synthesis.
- [ ] Focused tests fail if Amiga falls back to the old range path.
- [ ] Proposal 020 records the migrated Amiga behavior.

## Blocked By

- 020-002

## Required Sign-Off

- [ ] No accepted fact promotion.
- [ ] No old Amiga path kept as active default for migrated behavior.
- [ ] `platform_executable_formats validate` passes.
- [ ] Combined current coverage passes.
- [ ] Focused Amiga/platform executable tests pass.
- [ ] `git diff --check` passes.

## Completion Evidence

Record the Amiga raw summary, coverage counts, and any path now eligible for
deletion in 020-008.
