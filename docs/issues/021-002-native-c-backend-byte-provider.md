# 021-002: Native C Backend Byte Provider

Status: active
Type: AFK
Source proposal: docs/proposals/021-native-macos-code-source-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/021-native-macos-code-source-pipeline.md`
- Blocked by: 021-001.
- Current state: selected CODE bytes are extracted and then handed to a raw
  binary listing path.
- Desired state after this issue: backend APIs can accept the native Mac CODE
  descriptor and provide selected CODE bytes/provenance without exposing the
  source as raw Amiga.

## Start-Of-Issue Refresh

Review the descriptor produced by 021-001 and update exact field names in this
issue before coding. Do not invent a second descriptor shape.

## What To Build

Add a C/Python backend entry point for native selected Mac CODE byte access.

Required behavior:

- The backend takes source image, HFS path, and CODE resource id from the native
  descriptor.
- Returned payload includes selected CODE bytes or a byte view plus Mac
  provenance and shared executable range evidence.
- Failure cases distinguish missing HFS file, missing CODE resource, CODE 0
  metadata-only selection, and deferred/no-entry selected CODE.
- Public profile/source identity reports Mac CODE, not `amiga-raw`.
- Existing extraction helpers may be reused internally only where they do not
  define public source identity.

## Acceptance Criteria

- [ ] Native backend byte-provider API exists.
- [ ] MPW `Asm` CODE 1 returns bytes and shared range provenance.
- [ ] CODE 0 fails as metadata-only, not as decodable code.
- [ ] Deferred/no-entry CODE fails closed without promoting byte-entry evidence.
- [ ] Tests prove API/profile identity is Mac CODE, not raw Amiga.
- [ ] Proposal 021 records any remaining wrapper dependency.

## Blocked By

- 021-001

## Required Sign-Off

- [ ] No byte-entry or relocation/fixup promotion.
- [ ] Focused C/Mac backend tests pass.
- [ ] Cross-platform parser coverage still passes.
- [ ] `git diff --check` passes.

## Completion Evidence

Record API shape, success/failure proof, and remaining bridge callers.
