# 022-013: Real C Validation For Mac Restored-Source Verifier

Status: active
Type: AFK
Source proposal: docs/proposals/022-platform-executable-kb-display-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/022-platform-executable-kb-display-pipeline.md`.
- Dependency: `022-012` moved Mac restored-source authority into C and removed Python verifier-success synthesis.
- Current state: the Mac C-owned restored-source packet emits `source_coverage_verifier.ok: true` and zero counts directly.
- Desired state: Mac `source_coverage_verifier` is computed by real C validation over emitted Mac ownership ranges.

## What To Build

Replace hardcoded Mac restored-source verifier success with shared or equivalent
C validation. The Mac packet may keep its platform-specific emission code, but
its verifier must be derived from the same ownership ranges the packet emits.

Python project/web fail-closed behavior from `022-012` must remain unchanged:
Python can preserve C-owned packets or expose `restored_source_missing`, but it
must not synthesize verifier-success evidence.

## Acceptance Criteria

- [ ] Mac `restored_source_model_v1` packets still include `authority: c_owned`.
- [ ] Mac `source_coverage_verifier` is computed in C from emitted ownership ranges, not hardcoded.
- [ ] The Mac verifier detects gaps in ownership ranges.
- [ ] The Mac verifier detects overlapping ownership ranges.
- [ ] The Mac verifier detects malformed explicit unknown ranges, including missing reason/provenance/source-visible detail.
- [ ] The Mac verifier detects invalid role/status combinations that would make rendered instruction ownership unsafe or misleading.
- [ ] Existing current Mac fixture tests still prove selected CODE ownership ranges, Segment Loader placeholder references, executable resource placeholders, and `round_trip_required: false`.
- [ ] Negative tests prove malformed Mac restored-source ownership cannot report `source_coverage_verifier.ok: true`.
- [ ] Proposal 022 records the completed 022-013 result and is marked complete only if this issue is fully satisfied.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] Focused Mac C/backend/project/artifact/web tests pass.
- [ ] `uv run python -m amiga_reversing.tools.platform_executable_formats validate` passes.
- [ ] `uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-macos-c-backend --current-amiga-hunk --current-atari-prg` passes with `invalid: 0`.
- [ ] `cmd /c src\precommit.bat` passes.
- [ ] `git diff --check` passes.
