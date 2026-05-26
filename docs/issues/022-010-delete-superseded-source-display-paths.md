# 022-010: Delete Superseded Source Display Paths

Status: active

## Proposal

Proposal: `docs/proposals/022-platform-executable-kb-display-pipeline.md`

## What to build

Delete display/source compatibility paths made obsolete by the restored source
model. Do not leave dual default behavior.

Use the deletion map from 022-001 and refresh it against the implementation
state from 022-002 through 022-009 before deleting anything.

## Acceptance criteria

- [ ] Every deleted path has explicit replacement tests.
- [ ] No default display/source path bypasses `restored_source_model_v1` when
      the model is available.
- [ ] Public API compatibility fields are removed only after current consumers
      migrate.
- [ ] Mac compatibility fields are either removed with replacement proof or
      explicitly retained with a named remaining consumer.
- [ ] Amiga exact gates remain green.
- [ ] Atari exact gates remain green.
- [ ] Mac source-quality gates remain green with no round-trip claim.
- [ ] Proposal 022 records the deletion table and any retained future work.

## Verification

Run at minimum:

```powershell
cmd /c src\precommit.bat
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-macos-c-backend --current-amiga-hunk --current-atari-prg
uv run python -m pytest tests\test_macos_c_backend.py tests\test_macos_project_payload.py tests\test_macos_target_artifact.py tests\test_macos_web_view.py tests\test_web_app_source.py -q
git diff --check
```

## Blocked by

- `docs/issues/022-005-amiga-hunk-restored-source-integration.md`
- `docs/issues/022-006-atari-prg-restored-source-integration.md`
- `docs/issues/022-007-macos-code-ownership-and-relocation-integration.md`
- `docs/issues/022-008-executable-resource-placeholders.md`
- `docs/issues/022-009-web-api-restored-source-exposure.md`
