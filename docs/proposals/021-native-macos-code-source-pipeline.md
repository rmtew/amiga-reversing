# Proposal 021: Native Mac CODE Source Pipeline

Status: complete. Proposal 020 completed the shared executable import pipeline:
Mac CODE now exposes `platform_executable_summary_v1` ranges, and 021 moved the
selected CODE listing path to native `macos-code` identity.

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

Raw bridge callers recorded at 021-001 closeout, before later replacement:

1. `macos_listing_source._temporary_code_binary_source` materialized the
   selected CODE bytes as a temporary `RawBinarySource`; 021-002 began replacing
   byte access with a native Mac CODE provider, and 021-005 deleted this bridge.
2. `build_macos_project_listing_artifact_profile` passed that temporary source
   to the generic C listing artifact; 021-003 replaced listing and analysis
   artifact identity.
3. Mac project/artifact/web payloads consumed compatibility fields around
   `selected_code_segment`, `code_layout`, and preview rows; 021-004 migrated
   public payload assumptions after native listing parity.

### 021-002: Native C Backend Byte Provider

Completed native byte-provider slice:

- Added `macos_code_resource_byte_view_with_c_backend`, which accepts
  `MacosCodeResourceSource`, reads the HFS image/file/resource id from the
  descriptor, reuses the C Mac CODE summary/extractor internally, and returns a
  selected CODE byte view with Mac provenance and shared executable range
  evidence.
- Public provider identity is `backend: macos-code`,
  `source_kind: macos_code_resource`, and `wrapped_backend: null`; no public
  `amiga-raw` identity is exposed by this API.
- MPW `Asm` CODE 1 returns bytes plus the candidate shared executable range.
  CODE 0 fails as metadata-only, missing CODE resources fail as missing
  resources, and no-entry/deferred CODE fails closed without promoting
  byte-entry evidence.

Wrapper dependency recorded at 021-002 closeout, before later replacement:

- `build_macos_project_listing_artifact_profile` called
  `_temporary_code_binary_source` and then the generic raw C listing artifact.
  021-003 routed listing/analysis through the native provider so artifact
  profiles no longer report wrapped raw identity.

### 021-003: Native Listing And Analysis Artifact

Completed native listing/analysis identity slice:

- `build_macos_project_listing_artifact_profile` now returns active Mac listing
  profiles as `backend: macos-code` and `source_kind: macos_code_resource`.
- Analysis, source text, summary, navigation, and row-window profiles no longer
  expose `wrapped_backend: amiga-raw`.
- Mac source text headers include the native CODE source kind; row provenance
  keeps HFS path, resource id/name, shared candidate range, and deferred state.
- Analysis payloads continue to carry `platform_executable_summary_v1`,
  candidate CODE ranges, and deferred relocation/fixup evidence without fact
  promotion.

Deletion candidates handed to 021-005:

- `_temporary_code_binary_source` was internal byte transport for the generic C
  listing artifact.
- The generic raw listing artifact invocation inside
  `build_macos_project_listing_artifact_profile` was the replacement boundary
  before deleting raw bridge code.

### 021-004: Project, Artifact, And Web Payload Migration

Completed project/artifact/web migration:

- Mac project payloads now expose `native_source` at the project root,
  binary-container view, selected CODE segment, and selected listing route.
- Mac target artifact rendering prints native `source_kind` and `backend` for
  the selected CODE segment.
- Mac web/starter payloads expose the same native source identity for the
  binary container and selected CODE segment.
- Existing CODE 0 metadata, CODE coverage, candidate previews, orphan ranges,
  non-CODE placeholders, and deferred relocation/fixup explanations remain
  visible. Candidate/deferred facts remain non-accepted.

Retained public compatibility fields after 021-004:

- `selected_code_segment`, `code_layout`, `orphan_ranges`, and
  `relocation_fixups` remain public because existing artifact/web renderers and
  tests still consume them for user-visible CODE detail panes.
- 021-004 originally left project preview rendering with an internal
  `RawBinarySource` decode path for candidate preview rows; 021-005 recorded
  that as a non-public transport blocker. Post-closeout follow-up 021-008
  closed the blocker by routing preview rows through the native Mac CODE byte
  artifact helper, so project preview rendering no longer constructs
  `RawBinarySource` or temp raw files.

### 021-005: Delete Raw Bridge And Superseded Paths

Completed raw-bridge deletion slice:

| Old path | Replacement proof | Decision |
| --- | --- | --- |
| `macos_listing_source._temporary_code_binary_source` materialized selected CODE bytes as a temporary `RawBinarySource`. | `build_macos_project_listing_artifact_profile` now resolves a `MacosCodeResourceSource` descriptor and passes it directly to `build_listing_artifact_profile_from_binary_source`; `test_021_005_macos_listing_profile_uses_native_descriptor_not_raw_bridge` fails if the listing path stops using the native descriptor. | Deleted. |
| Active Mac CODE listing/analysis profiles stripped a wrapped raw profile after using the raw bridge. | 021-003/021-005 tests assert listing, analysis, source, and row-window profiles report `backend: macos-code`, `source_kind: macos_code_resource`, and no public `wrapped_backend`. | Old active behavior deleted; profile adjustment remains only to normalize the generic C artifact profile under native Mac identity. |
| Project/artifact/web public compatibility fields (`selected_code_segment`, `code_layout`, `orphan_ranges`, `relocation_fixups`). | 021-004 tests prove current payload consumers still use these fields for visible CODE coverage, candidate previews, and deferred fixup explanations. | Retained as public Mac evidence fields, not raw transport. |
| Project candidate preview row decoding in `macos_project_payload._preview_decode_rows`. | 021-008 routes bounded candidate preview bytes through `build_macos_code_bytes_listing_artifact_profile`; the preview path keeps native Mac CODE identity and no longer constructs `RawBinarySource` or temp raw files. | Resolved. |

Current state after 021-005:

- Active selected Mac CODE source selection, listing, analysis, artifact, and
  web/API payload identity use native Mac CODE descriptors and report
  `macos-code`.
- No active selected Mac CODE listing/analysis path constructs
  `RawBinarySource` or reports wrapped `amiga-raw`.
- The bounded candidate preview decoder blocker recorded at 021-005 was later
  resolved by post-closeout follow-up 021-008.

### 021-006: Closeout Proof

Completed closeout proof:

- Native Mac CODE source descriptor is active in project resolution:
  `test_021_001_committed_mpw_asm_project_resolves_native_code_source_descriptor`.
- Listing/analysis/artifact/web paths report native Mac CODE identity:
  `tests\test_macos_c_backend.py tests\test_macos_target_artifact.py
  tests\test_macos_project_payload.py tests\test_macos_web_view.py
  tests\test_web_app_source.py -q` passed with 43 tests.
- Active raw bridge and wrapped raw backend are deleted from selected Mac CODE
  behavior: `test_021_005_macos_listing_profile_uses_native_descriptor_not_raw_bridge`
  proves the listing path passes `MacosCodeResourceSource`, not a temporary
  `RawBinarySource`.
- Shared executable ranges remain authoritative and candidate/deferred facts
  remain non-accepted: combined coverage passed with `invalid: 0`,
  `parser_outputs: 3`, `candidate: 126`, `deferred: 43`.
- Focused C/listing tests passed with 4 tests, including the 020 listing range
  checks and Mac CODE bytes feeding the shared listing artifact.
- Repository precommit passed: style OK, dead_code OK, unit OK, integration OK,
  explicit OK.
- `git diff --check` passed.

Post-closeout follow-ups completed without reopening Proposal 021:

- 021-007 added
  `platform_file_facts_v2_listing_artifact_macos_code_buffer_create`, a native
  Mac CODE C artifact entry point that accepts selected CODE bytes in memory and
  labels artifact profile state as `backend: macos-code`. The selected
  `MacosCodeResourceSource` path no longer flows through
  `_source_file_for_c_backend`, does not write selected CODE bytes to a temp
  file, and does not construct an internal `"amiga-raw"` artifact profile.
- 021-008 closed the candidate preview transport blocker by moving candidate
  preview decoding onto `build_macos_code_bytes_listing_artifact_profile`.
  `macos_project_payload._preview_decode_rows` no longer constructs
  `RawBinarySource` or temp raw files, while preview rows still carry
  candidate/deferred fact ids and parser-use state.
- Focused proof for 021-007/008: precommit passed; Mac focused tests passed
  with 45 tests; targeted mypy passed on changed Python files; combined 020
  coverage passed with `invalid: 0`.
- 021-009 added the neutral `m68k-flat-buffer` in-memory artifact path:
  `platform_file_facts_v2_listing_artifact_flat_m68k_buffer_create` owns
  flat local-offset object/policy setup directly. It renders flat bytes such as
  `20 5f 4e 75` without reporting `amiga-raw` and without using the Amiga raw
  policy/object loader boundary.
- 021-010 moved `platform_file_facts_v2_listing_artifact_macos_code_buffer_create`
  onto that neutral flat M68K object/policy path. Selected Mac CODE and preview
  byte artifacts still report `backend: macos-code`, but their C setup no
  longer calls the Amiga raw policy or raw object loader.
- 021-011 added regression guards for that post-closeout boundary. Tests now
  fail if selected Mac CODE listing, analysis, summary, navigation, source text,
  row-window, or preview surfaces expose `backend: amiga-raw` or
  `wrapped_backend: amiga-raw`; source-level guards also keep the Mac CODE
  buffer entry point and preview decoder off the old raw object/policy path.
  These guards prove identity and transport boundaries only; they deliberately
  do not promote Mac byte-entry, relocation/fixup, source-to-CODE, or non-CODE
  facts beyond their Proposal 018 states.

Final future work:

- Mac byte-entry, relocation/fixup, source-to-CODE, and non-CODE payload facts
  remain governed by Proposal 018 states and were not promoted by 021.
- The post-closeout low-level C buffer cleanup is complete. Selected and
  preview Mac CODE byte artifacts use Mac CODE identity over neutral flat M68K
  internals, with regression guards against raw identity leaks.

## Acceptance Criteria

- Mac CODE has a native source descriptor.
- Mac CODE listing/analysis no longer reports as wrapped `amiga-raw`.
- Shared executable ranges from 020 remain the authority for Mac CODE range
  roles/statuses.
- Candidate/deferred/unsupported facts remain non-accepted.
- CODE 0 remains metadata-only.
- The raw byte bridge is deleted after replacement proof; no Mac CODE selected
  listing or preview path has a remaining `RawBinarySource` transport blocker.
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
- 021-009 starts the post-closeout native buffer cleanup.
- 021-010 follows 021-009.
- 021-011 follows 021-010.
- 021-012 followed 021-011 and closed the post-closeout cleanup notes.

## Non-Goals

- Promoting Mac byte-entry candidate evidence.
- Implementing Mac relocation/fixup semantics.
- Source-to-CODE recovery.
- Non-CODE resource decoding.
- UI redesign beyond removing raw-wrapper assumptions from existing views.
