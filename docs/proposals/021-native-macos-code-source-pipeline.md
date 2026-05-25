# Proposal 021: Native Mac CODE Source Pipeline

Status: active. Proposal 020 completed the shared executable import pipeline:
Mac CODE now exposes `platform_executable_summary_v1` ranges, but selected CODE
listing still travels through a temporary `RawBinarySource` byte bridge and
appears internally as wrapped `amiga-raw`.

## Purpose

Make Classic Mac OS CODE resources a first-class source path instead of a raw
byte transport workaround.

This is architecture and implementation cleanup, not semantic promotion. Proposal
018 remains the authority for executable-format facts. If Mac byte-entry,
relocation, fixup, or non-CODE semantics are candidate/deferred/unsupported in
018, 021 must carry that state through visibly and must not upgrade it to
accepted behavior.

## Target Outcome

A Mac CODE listing should be understandable as Mac CODE from source selection to
analysis, listing, artifact, and API output:

```text
Mac HFS image + file path + CODE resource id
  -> native Mac CODE source descriptor
  -> C-backed selected CODE byte provider with Mac provenance
  -> shared executable ranges from Proposal 020
  -> analysis/listing/artifact/web payloads with backend macos-code
```

The important visible change is that the user no longer sees a Mac CODE target
as a raw Amiga byte stream with Mac annotations pasted around it. The target is
Mac CODE, backed by shared executable ranges and existing evidence authority.

## Tutorial Example

The native source descriptor should be small and explicit:

```json
{
  "kind": "macos_code_resource",
  "source_image": "resources/platform_macos/MPW-GM.img.bin",
  "hfs_path": "MPW-GM/MPW/Tools/Asm",
  "resource_type": "CODE",
  "resource_id": 1,
  "address_model": "macos_code_resource_offset"
}
```

The resulting listing/analysis profile should identify the path directly:

```json
{
  "backend": "macos-code",
  "source_kind": "macos_code_resource",
  "wrapped_backend": null,
  "executable_model": "platform_executable_summary_v1",
  "executable_ranges": [
    {
      "role": "candidate_code",
      "resource_id": 1,
      "load_offset": 40,
      "fact_id": "macos.code_resource.movea_stack_a0.boundary.candidate",
      "fact_status": "candidate",
      "parser_use": "candidate_only"
    }
  ],
  "executable_deferred": [
    {
      "kind": "relocation_breadth",
      "fact_id": "macos.segment_loader.relocation_fixups.deferred",
      "fact_status": "deferred",
      "parser_use": "deferred_only"
    }
  ]
}
```

The source may render candidate code bytes, but the status remains candidate.
CODE 0 remains metadata-only. Relocation/fixup details remain deferred.

## Non-Negotiable Direction

- Do not promote Mac byte-entry, relocation, fixup, source-to-CODE, or non-CODE
  resource facts.
- Do not keep dual default behavior once a native path proves parity.
- Do not hide blockers behind report-only work; either implement the next native
  path slice or record the exact blocked deletion.
- Keep Mac project/artifact/web behavior visible while replacing the transport
  path underneath it.
- Remove the raw bridge only after native listing, analysis, and artifact parity
  prove it is no longer needed.

## Implementation Slices

### 021-001: Native Mac CODE Source Descriptor

Completed descriptor slice:

- Added `MacosCodeResourceSource` with source image path, HFS path, resource
  type/id, optional resource name, `macos_code_resource_offset` address model,
  display path, target-local analysis cache path, and stable cache identity.
- Added `macos_code_source_descriptor_from_project`, which resolves the
  committed MPW `Asm` project origin into that descriptor and fails closed when
  required origin fields are missing or invalid.
- `build_macos_code_listing_source` now constructs and carries the native
  descriptor before the temporary byte bridge. Listing/rendering behavior is not
  migrated in this slice.

Current raw bridge callers and replacement order:

1. `macos_listing_source._temporary_code_binary_source` still materializes the
   selected CODE bytes as a temporary `RawBinarySource`; 021-002 replaces byte
   access with a native Mac CODE provider.
2. `build_macos_project_listing_artifact_profile` still passes that temporary
   source to the generic C listing artifact; 021-003 replaces the listing and
   analysis artifact identity.
3. Mac project/artifact/web payloads still consume compatibility fields around
   `selected_code_segment`, `code_layout`, and preview rows; 021-004 migrates
   public payload assumptions after native listing parity.

### 021-002: Native C Backend Byte Provider

Add a C/Python backend entry point that accepts the native Mac CODE descriptor
and creates the selected CODE byte view with Mac provenance and shared executable
range evidence. It may internally read bytes, but the public artifact/profile
path must be Mac CODE, not raw Amiga.

### 021-003: Native Listing And Analysis Artifact

Route Mac listing and analysis through the native Mac CODE source path. Profiles,
analysis payloads, source headers, row provenance, and navigation should report
`macos-code` / `macos_code_resource` directly and retain shared executable
ranges.

### 021-004: Project, Artifact, And Web Payload Migration

Move Mac project payloads, target artifact rendering, and web/API listing
surfaces off wrapped raw-source assumptions. Existing Mac visibility for CODE 0,
candidate previews, orphan ranges, non-CODE placeholders, and deferred fixups
must remain.

### 021-005: Delete Raw Bridge And Superseded Paths

Delete `_temporary_code_binary_source` and any active `RawBinarySource` bridge
behavior proven replaced by 021. Keep no compatibility branch for the old default
path. Retain only explicitly blocked public compatibility fields that still have
consumers.

### 021-006: Closeout Proof

Run the full Mac-focused and cross-platform proof. Proposal 021 closes only when
Mac CODE is native through source selection, listing, analysis, artifact, and API
paths, and when the old raw bridge is deleted or has a precise out-of-scope
blocker.

## Acceptance Criteria

- Mac CODE has a native source descriptor.
- Mac CODE listing/analysis no longer reports as wrapped `amiga-raw`.
- Shared executable ranges from 020 remain the authority for Mac CODE range
  roles/statuses.
- Candidate/deferred/unsupported facts remain non-accepted.
- CODE 0 remains metadata-only.
- The raw byte bridge is deleted after replacement proof, or the exact remaining
  blocker is recorded as future work.
- Mac project/artifact/web tests continue to prove existing user-visible
  behavior.
- Cross-platform 020 parser coverage remains green.

## Verification Plan

Minimum proof for each implementation issue:

```powershell
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-macos-c-backend --current-amiga-hunk --current-atari-prg
uv run python -m pytest tests\test_macos_c_backend.py tests\test_macos_target_artifact.py tests\test_macos_project_payload.py tests\test_macos_web_view.py tests\test_web_app_source.py -q
git diff --check
```

Closeout must also run the focused C backend/listing tests and repository
precommit gate.

## Issue Ordering

- 021-001 starts first.
- 021-002 follows 021-001.
- 021-003 follows 021-002.
- 021-004 follows 021-003.
- 021-005 follows 021-004.
- 021-006 closes the proposal after all previous issues complete.

## Non-Goals

- Promoting Mac byte-entry candidate evidence.
- Implementing Mac relocation/fixup semantics.
- Source-to-CODE recovery.
- Non-CODE resource decoding.
- UI redesign beyond removing raw-wrapper assumptions from existing views.
