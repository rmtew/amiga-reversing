# 021-007: Native Mac CODE C Artifact Entrypoint

Status: active
Type: AFK
Source proposal: docs/proposals/021-native-macos-code-source-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/021-native-macos-code-source-pipeline.md`
- Proposal 021 status remains complete. This is a post-closeout cleanup issue
  for a retained implementation nuance, not a new proposal.
- Current state: selected Mac CODE listing/analysis has native public identity,
  but `c_backend._source_file_for_c_backend()` still writes selected CODE bytes
  to a temp file and invokes the generic C listing artifact as internal
  `"amiga-raw"` transport.
- Desired state after this issue: selected Mac CODE listing/analysis has a
  native C artifact entry point, so the active selected CODE path does not need
  temp-file raw transport or an internal `"amiga-raw"` backend label.

## What To Build

Add a native C/Python listing artifact path for `MacosCodeResourceSource`.

Required behavior:

- Python passes `MacosCodeResourceSource` to a native Mac CODE artifact entry
  point rather than converting it to a temp raw file.
- C receives selected CODE bytes, resource offset address model, Mac CODE
  backend/source identity, and shared executable range provenance.
- The normal m68k decode/render pipeline may still be reused internally, but
  public and internal artifact profile state for this path must be `macos-code`,
  not `"amiga-raw"`.
- CODE 0 remains metadata-only and cannot enter the artifact as code.
- Candidate CODE remains candidate-only; relocation/fixup state remains
  deferred-only.
- Do not change project preview decoding in this issue.

## Acceptance Criteria

- [ ] `MacosCodeResourceSource` no longer flows through
  `_source_file_for_c_backend()` as a temp `"amiga-raw"` source.
- [ ] Native Mac CODE artifact/profile state reports `backend: macos-code` and
  `source_kind: macos_code_resource` without profile normalization hiding raw
  internals.
- [ ] Selected CODE listing, analysis, source text, row windows, and navigation
  still work for MPW `Asm` CODE 1.
- [ ] Tests fail if selected CODE artifact construction calls the raw backend
  transport for Mac CODE.
- [ ] 018 authority remains intact: no byte-entry, relocation, or fixup
  promotion.
- [ ] Proposal 021 records the cleanup result and any retained blocker.

## Blocked By

- None. Proposal 021 closeout must already be present.

## Required Sign-Off

- [ ] No new proposal created.
- [ ] No fact promotion.
- [ ] Mac focused backend/listing/artifact tests pass.
- [ ] Combined 020 coverage passes.
- [ ] `git diff --check` passes.

## Completion Evidence

Record the native artifact API shape, removed raw transport, focused proof, and
any remaining Mac CODE raw transport blocker.
