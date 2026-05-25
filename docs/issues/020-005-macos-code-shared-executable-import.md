# 020-005: Mac CODE Shared Executable Import

Status: active
Type: AFK
Source proposal: docs/proposals/020-platform-executable-import-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/020-platform-executable-import-pipeline.md`
- Blocked by: completed/reviewed 020-002, 020-003, and 020-004.
- Current state: Amiga HUNK and Atari PRG current parser outputs now use
  `platform_executable_summary_v1`. Mac CODE still exposes Mac-specific C/Python
  range structures and enters listing through a raw-binary wrapper.
- Desired state after this issue: current Mac CODE parser output exposes the
  same shared executable model, while preserving all 018 Mac deferred/candidate
  boundaries.

## Start-Of-Issue Refresh

Before coding, read Proposal 020 sections 020-002 through 020-004 and inspect
the current Amiga/Atari shared range output. Use that completed shape as the
model unless Mac CODE needs a documented extension. Record any extension in
Proposal 020 before depending on it in tests.

## What To Build

Migrate current Mac CODE classified range output onto the shared executable
model at the parser/current-output boundary.

Required behavior:

- `platform_file_macos_hfs_code_summary_json_alloc` output for the MPW `Asm`
  fixture must emit shared executable range data using
  `executable_model == "platform_executable_summary_v1"` or an explicitly
  documented compatible Mac extension of that model.
- CODE 0 must be represented as metadata-only and must not become decodable
  instruction bytes.
- Nonzero CODE layout ranges must preserve accepted segment/header metadata.
- Current candidate code windows must remain candidate-only.
- Relocation/fixup state must remain deferred-only.
- Orphan/non-CODE/unsupported visibility must not be lost from Mac project,
  artifact, or web payloads.
- No Mac byte-entry rule may be promoted from candidate/unknown to accepted.
- Do not migrate listing/rendering or analysis-state import beyond what is
  necessary to expose and validate the shared parser summary.

## Acceptance Criteria

- [ ] Current MPW `Asm` Mac CODE summary emits shared executable range output.
- [ ] CODE 0 is metadata-only and cannot be decoded as instructions.
- [ ] Nonzero CODE accepted metadata remains accepted only where 018 authorizes
  it.
- [ ] Candidate code windows remain candidate-only.
- [ ] Relocation/fixup state remains deferred-only.
- [ ] Existing Mac project/artifact/web payload tests either consume the shared
  output or prove existing visible Mac state was not regressed.
- [ ] Combined current coverage reports Mac shared range paths with no invalid
  fact refs.
- [ ] Regression tests fail if Mac CODE output drops the shared range model
  while old Mac-specific fields still exist.
- [ ] Proposal 020 records the Mac shape, any model extension, and paths now
  eligible for later replacement/deletion.

## Blocked By

- 020-002
- 020-003
- 020-004

## Required Sign-Off

- [ ] No Mac byte-entry fact promotion.
- [ ] No relocation/fixup implementation without accepted evidence.
- [ ] No Mac-only compatibility path kept as the active default for this slice.
- [ ] `platform_executable_formats validate` passes.
- [ ] Combined current coverage passes.
- [ ] `pytest tests\test_platform_executable_formats.py -q` passes.
- [ ] Mac focused parser/payload/artifact/web tests pass.
- [ ] Focused C/backend tests pass if C behavior changes.
- [ ] `git diff --check` passes.

## Completion Evidence

Record the Mac raw summary shape, coverage counts and paths, Mac focused test
results, and any old Mac path now eligible for 020-008.
