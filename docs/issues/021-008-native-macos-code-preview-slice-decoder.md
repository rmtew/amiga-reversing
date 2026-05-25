# 021-008: Native Mac CODE Preview Slice Decoder

Status: active
Type: AFK
Source proposal: docs/proposals/021-native-macos-code-source-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/021-native-macos-code-source-pipeline.md`
- Proposal 021 status remains complete. This is a post-closeout cleanup issue
  for the preview-only blocker recorded at closeout.
- Blocked by: 021-007 if that issue changes native Mac CODE byte/artifact APIs.
- Current state: `macos_project_payload._preview_decode_rows()` uses a bounded
  preview-only `RawBinarySource` to decode candidate preview bytes for UI
  display.
- Desired state after this issue: candidate preview rows decode through a native
  Mac CODE byte-slice decoder, with Mac provenance and candidate/deferred status
  visible, and no preview `RawBinarySource`.

## Start-Of-Issue Refresh

Review 021-007 completion evidence first. If 021-007 added a native Mac CODE
byte/artifact helper that can decode bounded slices, reuse it instead of adding
a second API.

## What To Build

Add a native Mac CODE preview byte-slice decoder and move project payload preview
rows onto it.

Required behavior:

- Inputs identify HFS image, HFS path, CODE resource id, byte range
  `load_offset`/`size`, and fact status/parser-use authority.
- Output rows retain Mac provenance, resource id/name, candidate/deferred fact
  ids, and bounded preview metadata.
- Candidate preview rows may decode bytes for display, but must remain
  candidate-only.
- Deferred/no-entry ranges must not become accepted code.
- Delete the preview `RawBinarySource` and temp raw artifact path once native
  preview decoding proves parity.

## Acceptance Criteria

- [ ] Native Mac CODE preview slice decoder exists.
- [ ] Project payload candidate preview rows use the native decoder.
- [ ] `macos_project_payload._preview_decode_rows()` no longer constructs a
  `RawBinarySource`.
- [ ] Candidate/deferred status remains visible in preview output.
- [ ] Existing Mac project/artifact/web tests still prove CODE 0, candidate
  previews, orphan ranges, non-CODE placeholders, and deferred fixups.
- [ ] Tests fail if preview decoding falls back to raw source transport.
- [ ] Proposal 021 records deletion of the final preview raw transport.

## Blocked By

- 021-007 if its native Mac CODE artifact/API changes preview decoder design.

## Required Sign-Off

- [ ] No new proposal created.
- [ ] No fact promotion.
- [ ] Mac project/artifact/web tests pass.
- [ ] Combined 020 coverage passes.
- [ ] `git diff --check` passes.

## Completion Evidence

Record decoder API shape, deleted preview raw path, visible preview proof, and
remaining future work if any.
