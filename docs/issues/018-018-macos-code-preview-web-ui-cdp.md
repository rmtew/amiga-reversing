# 018-018: Mac OS CODE Preview Web UI And CDP Verification

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: Mac OS CODE resource web/UI consumption and browser
  verification
- Blocked by: `018-017`
- Current proposal state: 018-017 added `preview_windows` and
  `candidate_code_preview` descriptors to the Mac project payload and committed
  target artifact, but the web UI still renders only the raw `code_resources`
  inventory and selected CODE listing panel. The preview descriptors are not yet
  visibly consumed through the normal Mac project page.
- Desired proposal state after this issue: the Mac project web UI makes
  `code_resource_details` and `preview_windows` inspectable in the browser, and
  CDP verification proves the visible page preserves CODE 0 metadata-only
  handling, selected CODE 1 listing behavior, candidate preview rows, and
  deferred relocation state.

## Knowledge Delta

- Adds: web/UI rendering obligations for Mac CODE resource details and preview
  windows.
- Changes: 018-017 preview data becomes user-visible, not artifact/payload-only.
- Replaces: web UI showing only raw CODE resource inventory plus selected CODE
  listing.
- Deletes: no candidate/deferred evidence.
- Leaves out of scope: accepted relocation/fixup interpretation, accepted
  byte-entry validation, full non-selected listing routes, complete source
  recovery, and byte-for-byte roundtrip.

## Default Behavior

- CODE 0 must remain metadata/jump-table-only in the UI.
- Selected CODE 1 must keep the existing full listing panel and route behavior.
- Non-selected previews must be labelled candidate and bounded.
- Relocation/fixup state must remain visible as deferred.
- The UI must not imply that preview rows are accepted disassembly or complete
  segment coverage.
- Do not create legacy/compatibility paths; extend the current `macos` project
  renderer cleanly.

## Evidence Standard

- Browser-visible text must distinguish:
  - CODE 0 metadata/jump table;
  - selected CODE 1 full listing;
  - non-selected candidate preview windows;
  - resources with no safe preview and their evidenceful reason;
  - deferred relocation/fixup state.
- Preview rows shown in the UI must carry or display enough fact/status context
  to preserve candidate/deferred meaning.
- CDP/browser verification must inspect the actual rendered Mac project page,
  not only raw payload JSON or string snapshots.

## Implementation Slice

- Extend `amiga_reversing/web/app.js` Mac rendering so
  `binary_container_view.code_resource_details` is visible.
- Render per-CODE detail rows/cards with stable, compact layout:
  CODE id/name, role, kind, fact/status, listing kind, preview status, and
  relocation state.
- Render preview rows from `preview_windows` for non-selected CODE resources,
  clearly labelled as candidate and bounded.
- Render no-preview reasons for resources without safe preview ranges.
- Keep selected CODE 1 listing panel behavior unchanged.
- Add focused JS/server tests if an existing harness covers Mac rendering.
- Add or extend CDP browser verification so it opens the Mac project page and
  asserts visible UI text for CODE 0, CODE 1, at least one candidate preview row,
  and deferred relocation/fixup state.
- Update Proposal 012, Proposal 018, and `docs/platform-executable-formats.md`
  with the UI/CDP state.

## Research Completion Standard

Record trace blocks for:

- current Mac project web render path;
- current CDP test harness and how to run it;
- chosen UI shape for CODE details and preview windows;
- browser-visible assertions selected for CODE 0, CODE 1, candidate previews,
  no-preview reasons, and deferred relocation;
- any CDP environment limitations encountered.

## Research Coverage

- [x] Current Mac web render path traced.
- [x] Current CDP test harness traced.
- [x] Existing Mac project payload fields checked.
- [x] UI shape selected for CODE details and preview windows.
- [x] CDP assertions selected.
- [x] 012/018 wording checked before implementation.

## Research Review

- [x] Second pass checked CODE 0 is not rendered as ordinary code.
- [x] Second pass checked selected CODE 1 full listing still works.
- [x] Second pass checked candidate preview rows are visible and labelled
  candidate.
- [x] Second pass checked deferred relocation/fixup state is visible.
- [x] CDP verification inspects the browser-rendered Mac project page.
- [x] Proposal 012/018 docs updated with exact UI state.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Mac web UI consumes `code_resource_details`.
- [x] Mac web UI consumes `preview_windows`.
- [x] CODE 0 renders metadata/jump-table-only in the UI.
- [x] Selected CODE 1 listing panel remains available.
- [x] Non-selected preview rows are visible and labelled candidate/bounded.
- [x] No-preview reasons are visible for resources without safe previews.
- [x] Deferred relocation/fixup state is visible.
- [x] Candidate/deferred facts are not promoted to accepted output.
- [x] Relevant web/render tests pass.
- [x] CDP browser verification passes or an environment blocker is documented
  with exact command/output.
- [x] `amiga_reversing.tools.validate_018_issues` passes.
- [x] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

- Traced the normal Mac project UI path through `renderClassicMacProject` and
  `renderClassicMacContainerView` in `amiga_reversing/web/app.js`.
- Extended the Mac container UI to render `code_resource_details`,
  `preview_windows`, candidate preview rows, no-preview reasons, and deferred
  relocation/fixup state.
- Preserved the selected CODE 1 listing panel and route behavior.
- Added browser-source assertions for the new Mac CODE detail renderer and
  styles.
- Added CDP verification that opens the rendered Mac project page and checks
  visible CODE 0 metadata, CODE 1 full listing state, candidate/bounded preview
  rows, no-preview reasons, and deferred relocation/fixup state.
- Updated Proposal 012, Proposal 018, and
  `docs/platform-executable-formats.md` with the UI/CDP state.
- Validation run:
  `uv run python -m amiga_reversing.tools.platform_executable_formats validate`
- Relevant tests:
  `uv run python -m pytest tests\test_macos_web_view.py tests\test_web_app_source.py tests\test_macos_project_payload.py tests\test_macos_target_artifact.py tests\test_web_e2e_cdp.py::test_brave_cdp_macos_code_details_show_candidate_previews -q`
- CDP result: the focused browser test passed.
