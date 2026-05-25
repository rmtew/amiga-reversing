# 021-003: Native Listing And Analysis Artifact

Status: active
Type: AFK
Source proposal: docs/proposals/021-native-macos-code-source-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/021-native-macos-code-source-pipeline.md`
- Blocked by: 021-002.
- Current state: Mac listing and analysis are wrapped around an `amiga-raw`
  listing artifact.
- Desired state after this issue: Mac listing and analysis artifacts use the
  native Mac CODE source path and report native Mac CODE identity.

## Start-Of-Issue Refresh

Review 021-001 and 021-002 completion evidence. The native listing path must use
their descriptor/API shape, not recreate raw-source plumbing under a new name.

## What To Build

Route Mac listing and analysis through the native Mac CODE source path.

Required behavior:

- `build_macos_project_listing_artifact_profile` or its replacement constructs a
  native Mac CODE artifact from the descriptor.
- `analysis_payload`, source text profile, summary, navigation, and row windows
  report `backend: macos-code` and native source kind.
- `wrapped_backend: amiga-raw` disappears from active Mac CODE profiles.
- Row provenance keeps HFS path, resource id/name, shared candidate range, and
  deferred evidence.
- CODE 0 remains metadata-only and unrenderable as instructions.
- Candidate CODE rows remain visibly candidate.

## Acceptance Criteria

- [ ] Mac listing artifact no longer reports wrapped `amiga-raw`.
- [ ] Mac analysis payload contains shared executable ranges from native source
  identity.
- [ ] Mac source text headers report native CODE source identity.
- [ ] Mac window/navigation rows retain Mac provenance.
- [ ] Tests fail if the active path falls back to the raw bridge.
- [ ] Existing Mac target artifact tests still pass or are updated to the native
  identity.
- [ ] Proposal 021 records old listing/analysis paths now eligible for deletion.

## Blocked By

- 021-002

## Required Sign-Off

- [ ] No fact promotion.
- [ ] No target-source churn unrelated to native identity.
- [ ] Focused Mac listing/artifact tests pass.
- [ ] Focused C backend tests pass if backend artifact code changes.
- [ ] `git diff --check` passes.

## Completion Evidence

Record profile before/after, native analysis payload proof, and deletion
candidates for 021-005.
