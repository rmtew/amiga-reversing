# 020-004: Atari PRG Shared Executable Import

Status: active
Type: AFK
Source proposal: docs/proposals/020-platform-executable-import-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/020-platform-executable-import-pipeline.md`
- Blocked by: 020-002.
- Current state: Atari ST PRG emits parser-owned executable KB refs, but its
  executable structure does not yet emit the shared 020 `executable_ranges`
  model.
- Desired state after this issue: Atari PRG TEXT/DATA/BSS structure flows
  through shared executable ranges.

## What To Build

Extend the shared C-owned executable summary model from 020-002 to the current
Atari ST PRG inspect/current-output path.

The worker should mirror the Amiga shape where it fits:

- raw `platform_file_inspect_path_json_alloc` / `atari-st` output must include
  `executable_model == "platform_executable_summary_v1"`;
- TEXT should emit as role `code`, DATA as role `data`, and BSS as role `bss`;
- ranges must distinguish `load_offset` from nullable `stored_offset`;
- BSS must have `stored_offset: null` and `stored_size: 0`;
- accepted range facts must use the existing Atari KB facts, not new ad hoc
  strings;
- BSS header-only, relocation terminator variants, basepage/runtime, and symbol
  details must remain candidate/deferred/non-accepted where current 018/019
  facts require it;
- current coverage must consume the shared ranges without adding Python-side
  Atari range synthesis.

Do not migrate listing/rendering or analysis import in this issue.

## Acceptance Criteria

- [ ] Current Atari PRG fixture emits `executable_model`,
  `executable_ranges`, and non-accepted limit/deferred output where applicable.
- [ ] TEXT/DATA/BSS ranges are represented with load/stored offset semantics.
- [ ] BSS emits `stored_offset: null` and `stored_size: 0`.
- [ ] Accepted range refs validate against existing Atari KB facts.
- [ ] Candidate/deferred Atari facts remain non-accepted.
- [ ] Current coverage reports Atari refs from `$.executable_ranges[...]` and
  non-accepted limit/deferred paths where emitted.
- [ ] Regression tests fail if Atari shared ranges are omitted while old
  `sections`/`fact_refs` remain.
- [ ] No listing, analysis-state import, Amiga follow-up, or Mac CODE migration
  is performed in this issue.
- [ ] Proposal 020 records the migrated Atari behavior.

## Blocked By

- 020-002

## Required Sign-Off

- [ ] No accepted fact promotion.
- [ ] Shared executable ranges are the active Atari current-output proof.
- [ ] Old Atari fields remain only as compatibility/deletion candidates.
- [ ] `platform_executable_formats validate` passes.
- [ ] Combined current coverage passes.
- [ ] `pytest tests\test_platform_executable_formats.py -q` passes.
- [ ] `pytest tests\test_atari_platform_kb.py -q` passes.
- [ ] Focused C/backend tests pass if C behavior changes.
- [ ] `git diff --check` passes.

## Completion Evidence

Record the Atari raw summary, coverage counts, and any path now eligible for
deletion in 020-008.
