# 021-001: Native Mac CODE Source Descriptor

Status: active
Type: AFK
Source proposal: docs/proposals/021-native-macos-code-source-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/021-native-macos-code-source-pipeline.md`
- Blocked by: none.
- Current state: Mac CODE listing uses a temporary `RawBinarySource` wrapper
  after C extracts selected CODE bytes.
- Desired state after this issue: selected Mac CODE can be represented as a
  first-class source descriptor without making raw bytes the source identity.

## What To Build

Add a native selected Mac CODE source descriptor and resolution path.

Required behavior:

- The descriptor records source image path, HFS path, resource type/id, resource
  name when known, address model, and cache identity.
- Existing Mac project origin can resolve to this descriptor.
- The descriptor does not promote byte-entry, relocation, or fixup facts.
- Existing raw bridge behavior may remain active after this issue, but it must
  consume or sit behind the native descriptor rather than being the only source
  identity.
- Proposal 021 records the exact bridge callers that later issues must replace.

## Acceptance Criteria

- [ ] A native Mac CODE source descriptor exists in code.
- [ ] Mac project source resolution can produce that descriptor.
- [ ] Cache/display identity is stable and includes image path, HFS path, and
  CODE resource id.
- [ ] Tests prove descriptor construction from the committed MPW `Asm` project.
- [ ] Tests prove invalid or missing Mac project origin fails closed.
- [ ] No listing/rendering migration is required in this issue.
- [ ] Proposal 021 records current raw bridge callers and replacement order.

## Blocked By

- None.

## Required Sign-Off

- [ ] No fact promotion.
- [ ] No broad target regeneration.
- [ ] Focused Mac source/project tests pass.
- [ ] `git diff --check` passes.

## Completion Evidence

Record the descriptor shape, proof tests, and bridge callers for 021-002/021-003.
