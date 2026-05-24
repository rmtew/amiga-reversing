# 020-006: Shared Listing/Rendering Contract

Status: active
Type: AFK
Source proposal: docs/proposals/020-platform-executable-import-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/020-platform-executable-import-pipeline.md`
- Blocked by: at least one completed platform migration; final closeout blocked
  by 020-003 through 020-005.
- Current state: listing/rendering can still depend on platform-specific range
  decisions.
- Desired state after this issue: listing/rendering consumes shared executable
  ranges and visibly preserves accepted/candidate/deferred/unsupported state.

## What To Build

Route listing/rendering decisions through the shared executable range model.
Metadata-only ranges must not decode as instructions. Candidate ranges may
render bounded preview/listing rows only with visible candidate status.
Deferred/unsupported state must be visible in source/artifact/web output.

## Acceptance Criteria

- [ ] Renderer/listing has a shared executable-range consumption path.
- [ ] At least one migrated platform renders from shared ranges.
- [ ] After 020-003 through 020-005, all three platforms render through the
  shared contract where executable ranges are involved.
- [ ] Metadata-only ranges are blocked from instruction decoding.
- [ ] Candidate/deferred/unsupported states are visible in outputs.
- [ ] Regression tests cover at least one metadata-not-code case.

## Blocked By

- 020-003 or 020-004 for initial work
- 020-003, 020-004, and 020-005 for completion

## Required Sign-Off

- [ ] No platform-specific renderer bypass remains for migrated behavior.
- [ ] No metadata decoded as code.
- [ ] Existing target artifact drift tests pass where touched.
- [ ] Focused web/listing tests pass where touched.
- [ ] `git diff --check` passes.

## Completion Evidence

Record which platform outputs now render from shared ranges and which old
rendering paths are ready for deletion.
