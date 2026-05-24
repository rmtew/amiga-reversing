# 020-002: Shared Executable Summary Model

Status: active
Type: AFK
Source proposal: docs/proposals/020-platform-executable-import-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/020-platform-executable-import-pipeline.md`
- Blocked by: 020-001.
- Current state: parser inspect summaries emit platform facts, but there is no
  shared C-owned executable range model consumed by later import/listing work.
- Desired state after this issue: the first shared executable summary/range
  model exists and one current parser fixture emits it with tests.

## What To Build

Implement the initial shared C-owned executable summary/range model. It must
represent container identity, range role, byte span, stored size, fact state,
fact id, parser-use authority, and deferred/unsupported markers.

Expose it through parser inspect JSON for one narrow current fixture. Prefer the
smallest platform fixture that proves the model without forcing all platforms
to migrate in this issue.

## Acceptance Criteria

- [ ] Shared C data shape exists for executable summary/ranges.
- [ ] Parser inspect JSON exposes shared ranges for at least one current
  executable fixture.
- [ ] Shared range output includes KB record/fact refs and fact states.
- [ ] Metadata/data/code/BSS-style roles can be represented without decoding
  metadata as code.
- [ ] Tests validate raw summary output before Python coverage wrapping.
- [ ] Proposal 020 records the chosen first fixture and any model constraints.

## Blocked By

- 020-001

## Required Sign-Off

- [ ] No Python-only durable model.
- [ ] No legacy compatibility path.
- [ ] Candidate/deferred/unsupported states remain non-accepted.
- [ ] `platform_executable_formats validate` passes.
- [ ] Focused tests for the touched parser path pass.
- [ ] `git diff --check` passes.

## Completion Evidence

Record the raw parser summary shape, the focused tests, and which platform
migration should use the model next.
