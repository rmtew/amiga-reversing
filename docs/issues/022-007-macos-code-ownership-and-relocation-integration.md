# 022-007: Mac CODE Ownership And Relocation Integration

Status: active

## Proposal

Proposal: `docs/proposals/022-platform-executable-kb-display-pipeline.md`

## What to build

Move Mac CODE source/listing/artifact/web/API output onto the restored source
model. Selected executable CODE payload bytes must have explicit ownership.
Segment Loader relocation/fixup effects must be represented as source-level
reference records or explicit placeholders.

Do not add a Mac round-trip claim.

Ground the migration in current Mac surfaces:
`macos_project_payload.py`, `macos_target_artifact.py`, `macos_web_view.py`,
`amiga_reversing/web/app.js`, and the Mac `CListingArtifact` wrapper.

## Acceptance criteria

- [ ] Every byte in the selected executable CODE payload is owned by metadata,
      code, data, relocation/fixup, padding, placeholder, or explicit unknown.
- [ ] Unknown ranges include byte span, status, reason, provenance, and
      source-visible rendering.
- [ ] Segment Loader relocation/fixup effects are represented as source-level
      references where evidence supports them.
- [ ] Custom or unresolved extension bytes render as placeholders with reference
      context.
- [ ] CODE resource identity and A5/world conventions are platform extensions
      over the shared model.
- [ ] Existing public Mac fields are not deleted until restored source records
      expose equivalent or better detail to artifact/web/API consumers.
- [ ] Candidate/deferred/unsupported facts remain non-accepted.
- [ ] Source/listing/artifact/web/API output exposes the restored source model.
- [ ] No Mac round-trip claim is introduced.
- [ ] Proposal 022 records any UI gaps discovered during implementation.

## Verification

Run at minimum:

```powershell
cmd /c src\build.bat
uv run python -m pytest tests\test_macos_c_backend.py tests\test_macos_project_payload.py tests\test_macos_target_artifact.py tests\test_macos_web_view.py tests\test_web_app_source.py -q
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-macos-c-backend --current-amiga-hunk --current-atari-prg
git diff --check
```

## Blocked by

- `docs/issues/022-003-source-coverage-verifier.md`
- `docs/issues/022-004-shared-source-reference-records.md`
- Review completed or current 022-005/022-006 assumptions before finalizing Mac
  integration.
