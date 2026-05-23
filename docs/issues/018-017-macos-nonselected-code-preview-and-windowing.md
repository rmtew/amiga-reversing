# 018-017: Mac OS Nonselected CODE Preview And Windowing

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: Mac OS CODE resource preview/listing usability after
  multi-CODE navigation
- Blocked by: `018-010`
- Current proposal state: every MPW `Asm` CODE resource appears in
  `binary_container_view.code_resource_details`, navigation groups, and the
  committed artifact. CODE 0 renders as metadata, selected CODE 1 keeps the
  detailed listing route, and other nonzero CODE resources currently expose
  structured placeholders with segment metadata, candidate code/data ranges,
  orphan ranges, and deferred relocation state.
- Desired proposal state after this issue: non-selected nonzero CODE resources
  expose bounded preview/listing windows derived from existing classified
  ranges, while candidate/deferred byte-entry and relocation semantics stay
  visibly unresolved.

## Knowledge Delta

- Adds: requirements for bounded preview/listing windows for non-selected Mac
  CODE resources.
- Changes: non-selected CODE resources become inspectable beyond placeholder
  metadata where classified candidate code ranges exist.
- Replaces: blanket structured placeholder output for every non-selected CODE
  resource.
- Deletes: no deferred/candidate state.
- Leaves out of scope: accepted relocation/fixup interpretation, accepted
  byte-entry validation, complete inter-segment control flow, byte-for-byte
  roundtrip, and source-to-CODE reconstruction.

## Default Behavior

- CODE 0 remains metadata/jump-table output, not ordinary m68k.
- Existing selected CODE 1 listing behavior must remain unchanged.
- Non-selected previews may use current candidate code ranges as candidate-only
  preview windows, not accepted executable entrypoints.
- Relocation/fixup state remains deferred-only unless a separate issue validates
  it.
- Previews must not hide orphan/data ranges or imply complete segment coverage.

## Evidence Standard

- Each preview window must carry resource id/name, payload hash, start/end/size,
  range kind, fact id, fact status, parser-use value, and unsupported/deferred
  reasons.
- Candidate preview rows must be labelled candidate at the payload, artifact,
  and test levels.
- If a CODE resource cannot receive a preview, the placeholder must say why
  using current structured evidence, not a generic failure.
- No preview may be emitted from bytes classified as metadata, orphan/data, or
  relocation/fixup state unless the row explicitly labels them as non-code.

## Implementation Slice

- Extend the Mac project payload detail model with preview descriptors for
  non-selected CODE resources where candidate code ranges exist.
- Add a reusable listing/window path for bounded candidate previews without
  making every non-selected resource the selected listing route.
- Render preview descriptors in the committed MPW `Asm` artifact after each
  CODE resource detail.
- Preserve structured placeholders only for resources with no safe candidate
  preview range.
- Add tests proving:
  - CODE 0 still has no code preview;
  - selected CODE 1 still uses the existing full listing route;
  - non-selected CODE resources with candidate code ranges expose candidate
    preview descriptors;
  - preview windows do not cover metadata/orphan/data ranges;
  - candidate/deferred facts are not promoted to accepted output;
  - parser fact output still passes validation.
- Update Proposal 012, Proposal 018, and `docs/platform-executable-formats.md`
  with the preview/windowing state.

## Research Completion Standard

Record trace blocks for:

- existing selected CODE listing route and which parts can be reused safely;
- current classified ranges for each MPW `Asm` CODE resource;
- preview size/window policy and why it is bounded;
- resources with no preview and the exact structured reason;
- evidence that previews are candidate-only and relocation/fixups remain
  deferred.

## Research Coverage

- [x] Current selected CODE listing route traced.
- [x] Current per-CODE detail payload shape traced.
- [x] MPW `Asm` candidate code ranges inventoried.
- [x] Preview size/window policy selected.
- [x] No-preview policy selected for resources without candidate code ranges.
- [x] 012/018 blocker wording checked before implementation.

## Research Review

- [x] Second pass checked CODE 0 is still metadata-only.
- [x] Second pass checked selected CODE 1 full listing still works.
- [x] Second pass checked non-selected previews are bounded to candidate code
  ranges.
- [x] Candidate preview rows are not labelled accepted.
- [x] Deferred relocation/fixup state remains visible.
- [x] Parser output passes fact-reference validation.
- [x] Proposal 012/018 docs updated with exact accepted/candidate/deferred
  state.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Non-selected CODE preview descriptors added to Mac project payloads.
- [x] Preview/listing windows are bounded by classified candidate code ranges.
- [x] CODE 0 remains metadata/jump-table only.
- [x] Selected CODE 1 detailed listing remains available.
- [x] Resources without safe preview ranges retain specific placeholders.
- [x] Candidate/deferred facts are not promoted to accepted output.
- [x] MPW `Asm` target artifact regenerated if output changes.
- [x] Parser fact output passes validation.
- [x] `amiga_reversing.tools.platform_executable_formats validate` passes.
- [x] `amiga_reversing.tools.validate_018_issues` passes.
- [x] Relevant Mac parser/listing/project tests pass.
- [x] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

- Traced existing CODE 1 listing through `macos_project_payload` and kept the
  selected full listing route unchanged.
- Added `candidate_code_preview` descriptors for non-selected nonzero CODE
  resources with classifier-backed candidate code ranges, capped at 64 bytes
  and labelled `candidate_only`.
- Kept CODE 0 preview-free, kept relocation/fixup state deferred, and preserved
  evidenceful no-preview placeholders for resources without candidate ranges.
- Regenerated the committed MPW `Asm` artifact with preview rows after CODE
  detail subviews.
- Updated Proposal 012, Proposal 018, and `docs/platform-executable-formats.md`
  with the current accepted/candidate/deferred state.
- Validation run:
  `uv run python -m amiga_reversing.tools.platform_executable_formats validate`
- Relevant tests:
  `uv run python -m pytest tests\test_macos_project_payload.py tests\test_macos_target_artifact.py tests\test_macos_asm_container.py tests\test_macos_c_backend.py -q`
