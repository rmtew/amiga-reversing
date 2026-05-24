# 020-004: Atari PRG Shared Executable Import

Status: active
Type: AFK
Source proposal: docs/proposals/020-platform-executable-import-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/020-platform-executable-import-pipeline.md`
- Blocked by: 020-002.
- Current state: Atari ST PRG emits parser-owned executable KB refs, but its
  executable structure is not yet migrated through the shared 020 model.
- Desired state after this issue: Atari PRG TEXT/DATA/BSS structure flows
  through shared executable ranges.

## What To Build

Migrate the current Atari PRG inspect/current-output path onto the shared
executable model. TEXT, DATA, BSS, and loaded TEXT+DATA target-space facts must
be represented as shared ranges. Basepage/runtime entry, relocation terminator
variants, and symbol-table breadth must remain candidate/deferred where 018
records them that way.

## Acceptance Criteria

- [ ] Current Atari PRG fixture emits shared executable ranges.
- [ ] TEXT/DATA/BSS and loaded-image target space are represented with KB fact
  refs.
- [ ] Runtime/basepage/symbol/relocation unresolved areas stay non-accepted.
- [ ] Coverage consumes the shared model without Atari-specific synthesis.
- [ ] Focused tests fail if Atari falls back to the old range path.
- [ ] Proposal 020 records the migrated Atari behavior.

## Blocked By

- 020-002

## Required Sign-Off

- [ ] No accepted fact promotion.
- [ ] No old Atari path kept as active default for migrated behavior.
- [ ] `platform_executable_formats validate` passes.
- [ ] Combined current coverage passes.
- [ ] Focused Atari/platform executable tests pass.
- [ ] `git diff --check` passes.

## Completion Evidence

Record the Atari raw summary, coverage counts, and any path now eligible for
deletion in 020-008.
