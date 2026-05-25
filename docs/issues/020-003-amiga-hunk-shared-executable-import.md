# 020-003: Amiga HUNK Shared Executable Import

Status: active
Type: AFK
Source proposal: docs/proposals/020-platform-executable-import-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/020-platform-executable-import-pipeline.md`
- Blocked by: 020-002.
- Current state: 020-002 added `executable_model`,
  `executable_ranges`, and `executable_deferred` to raw Amiga HUNK inspect
  JSON, while the current-output loader and coverage proof still mainly prove
  the older top-level `fact_refs`/`sections` surfaces.
- Desired state after this issue: the Amiga HUNK current-output proof treats
  shared executable ranges as the canonical Amiga executable structure and
  fails if they disappear or drift from the older compatibility fields.

## What To Build

Make the current Amiga HUNK parser proof consume the shared executable model
introduced by 020-002.

The worker should keep this issue narrow:

- strengthen `_load_current_amiga_hunk_output()` or equivalent current-output
  helper so it requires `executable_model == "platform_executable_summary_v1"`;
- require CODE, DATA, and BSS `executable_ranges`;
- require BSS to have `stored_offset: null`, `stored_size: 0`, and a valid
  `load_offset`;
- require runtime-entry uncertainty in `executable_deferred`;
- keep `sections` and top-level `fact_refs` intact as compatibility surfaces
  for now, but do not let the current-output proof pass if shared ranges are
  missing;
- do not migrate listing/rendering or analysis import in this issue.

This is an Amiga current-output migration, not deletion. Any old path that is
now only compatibility should be recorded for 020-008.

## Acceptance Criteria

- [ ] Current Amiga HUNK fixture emits and the current-output helper requires
  `executable_model == "platform_executable_summary_v1"`.
- [ ] CODE/DATA/BSS shared ranges are required and validated from raw inspect
  JSON.
- [ ] BSS keeps `load_offset`, `stored_offset: null`, and `stored_size: 0`.
- [ ] Runtime-entry uncertainty is required in `executable_deferred` and remains
  `deferred_only`.
- [ ] Current coverage reports Amiga refs from `$.executable_ranges[...]` and
  `$.executable_deferred[...]`, not only from top-level `fact_refs`.
- [ ] Regression tests fail if shared Amiga ranges are omitted while old
  `sections`/`fact_refs` remain.
- [ ] No listing, analysis-state import, Atari PRG, or Mac CODE migration is
  performed in this issue.
- [ ] Proposal 020 records the migrated Amiga behavior.

## Blocked By

- 020-002

## Required Sign-Off

- [ ] No accepted fact promotion.
- [ ] Shared executable ranges are the active Amiga current-output proof.
- [ ] Old Amiga fields remain only as compatibility/deletion candidates.
- [ ] `platform_executable_formats validate` passes.
- [ ] Combined current coverage passes.
- [ ] `pytest tests\test_platform_executable_formats.py -q` passes.
- [ ] Focused Amiga C/backend tests pass if C behavior changes.
- [ ] `git diff --check` passes.

## Completion Evidence

Record the Amiga raw summary shape, coverage counts including
`executable_ranges`/`executable_deferred` paths, and any old Amiga path now
eligible for deletion in 020-008.
