# 022-012: C-Owned Mac Restored-Source Authority

Status: active
Type: AFK
Source proposal: docs/proposals/022-platform-executable-kb-display-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/022-platform-executable-kb-display-pipeline.md`.
- Dependency: `022-011` closeout snapshot exists, but review reopened 022 for this correction.
- Current state: Mac project/web payload helpers can synthesize restored-source ownership, reference records, and a passing verifier from compatibility fields.
- Desired state: Mac restored-source authority comes from the C-owned restored-source model, or consumers fail closed with an explicit missing-model diagnostic.

## What To Build

Remove Python-side Mac restored-source synthesis as an authority path. Project,
artifact, web, and API consumers may copy and render restored-source packets that
come from the C-owned model, but they must not manufacture
`source_ownership_ranges`, `source_reference_records`, or
`source_coverage_verifier.ok: true` from legacy Mac fields.

Compatibility fields such as `selected_code_segment`, `code_layout`,
`orphan_ranges`, `relocation_fixups`, and `preview_windows` may remain for
identity/navigation while current consumers still need them. They are not
restored-source evidence authority.

## Acceptance Criteria

- [ ] Mac project/web/API payloads preserve C-emitted `restored_source_model_v1` packets without changing ownership/reference/verifier meaning.
- [ ] If C-emitted restored-source data is missing, Mac project/web/API payloads expose a missing-model/blocker state instead of synthetic ownership/reference/verifier success.
- [ ] Python helper code no longer contains a fallback that builds verifier-successful restored-source records from `code_layout`/`relocation_fixups`.
- [ ] Current real Mac fixture tests still prove selected CODE restored-source records, Segment Loader placeholder references, executable resource placeholders, and `round_trip_required: false`.
- [ ] Negative tests prove missing restored-source data fails closed and no consumer can treat compatibility fields as durable restored-source authority.
- [ ] Proposal 022 records the final 022-012 result and is marked complete only if this issue is fully satisfied.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] Focused Mac C/backend/project/artifact/web tests pass.
- [ ] `uv run python -m amiga_reversing.tools.platform_executable_formats validate` passes.
- [ ] `uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-macos-c-backend --current-amiga-hunk --current-atari-prg` passes with `invalid: 0`.
- [ ] `cmd /c src\precommit.bat` passes.
- [ ] `git diff --check` passes.
