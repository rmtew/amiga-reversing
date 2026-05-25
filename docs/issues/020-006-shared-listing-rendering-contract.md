# 020-006: Shared Listing/Rendering Contract

Status: active
Type: AFK
Source proposal: docs/proposals/020-platform-executable-import-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/020-platform-executable-import-pipeline.md`
- Blocked by: completed/reviewed 020-003, 020-004, and 020-005.
- Current state: parser summaries can expose shared executable ranges, but
  listing/rendering may still use platform-specific range decisions or Mac
  raw-binary wrapping.
- Desired state after this issue: listing/rendering consumes shared executable
  ranges as the default executable-range contract.

## Start-Of-Issue Refresh

Before coding, read 020-003, 020-004, and 020-005 completion evidence in
Proposal 020. Update any exact field/path assumptions in this issue if 020-005
introduced a documented Mac extension. Do not start from pre-020-005 Mac field
names as authoritative.

## What To Build

Route listing/rendering decisions through the shared executable range model.
This is the first consumer migration after parser/current-output migration.

Required behavior:

- Amiga HUNK, Atari PRG, and Mac CODE executable range rendering must be driven
  by shared range role/status/fact data for migrated behavior.
- Metadata-only ranges must not decode as instructions.
- BSS/data ranges must not become instruction ranges just because they share a
  container with code.
- Candidate ranges may render bounded preview/listing rows only with visible
  candidate status.
- Deferred/unsupported state must remain visible in source/artifact/web output
  where the current UI/API exposes it.
- Remove or bypass no active behavior by compatibility flag; the shared contract
  must be the default for migrated paths.
- Do not import shared ranges into durable analysis state in this issue except
  where listing construction already requires the current in-memory view.

## Acceptance Criteria

- [ ] Renderer/listing has one shared executable-range consumption path for
  migrated executable ranges.
- [ ] Amiga listing/rendering uses shared ranges for CODE/DATA/BSS decisions.
- [ ] Atari listing/rendering uses shared ranges for TEXT/DATA/BSS decisions.
- [ ] Mac listing/rendering uses shared ranges for CODE metadata/candidate
  decisions without decoding CODE 0 as instructions.
- [ ] Candidate/deferred/unsupported states remain visible in outputs.
- [ ] Regression tests cover at least one metadata-not-code case.
- [ ] Regression tests cover at least one candidate-visible-but-not-accepted
  case.
- [ ] Existing exact artifact/round-trip checks remain exact where they were
  exact before this issue.
- [ ] Proposal 020 records which listing/rendering paths are now shared and
  which old paths are deletion candidates for 020-008.

## Blocked By

- 020-003
- 020-004
- 020-005

## Required Sign-Off

- [ ] No platform-specific renderer bypass remains active for migrated behavior.
- [ ] No metadata decoded as code.
- [ ] No candidate/deferred/unsupported state promoted to accepted rendering.
- [ ] Parser coverage still passes.
- [ ] Focused listing/artifact/web tests pass.
- [ ] Existing target artifact drift tests pass where touched.
- [ ] `git diff --check` passes.

## Completion Evidence

Record the exact shared rendering contract, proof output for each platform, and
the old rendering paths that are ready for 020-008 deletion.
