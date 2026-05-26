# 022-011: Cross-Platform Closeout Proof

Status: active

## Proposal

Proposal: `docs/proposals/022-platform-executable-kb-display-pipeline.md`

## What to build

Close Proposal 022 by proving the restored source model works across all three
platform tracks and by deleting completed 022 issue files.

Closeout must prove the implemented path, not just summarize issue completion.

## Acceptance criteria

- [ ] Amiga HUNK restored source ownership and references are active.
- [ ] Amiga exact round-trip and reproduction proof passes.
- [ ] Atari PRG restored source ownership and references are active.
- [ ] Atari exact round-trip and reproduction proof passes.
- [ ] Mac CODE selected executable source has full ownership coverage.
- [ ] Mac CODE source-level relocation/reference representation is active.
- [ ] Mac executable-relevant placeholders are active.
- [ ] Mac has no round-trip claim.
- [ ] Web/API exposure is active.
- [ ] Source coverage verifier passes expected targets and fails covered
      negative cases.
- [ ] Listing artifact analysis/source/window/navigation APIs expose restored
      source evidence where applicable.
- [ ] Proposal 022 records closeout proof, retained future work, and UI
      follow-up notes.
- [ ] Completed 022 issue files are deleted after their work is committed.

## Verification

Run at minimum:

```powershell
cmd /c src\precommit.bat
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-macos-c-backend --current-amiga-hunk --current-atari-prg
uv run python -m pytest tests\test_macos_c_backend.py tests\test_macos_project_payload.py tests\test_macos_target_artifact.py tests\test_macos_web_view.py tests\test_web_app_source.py -q
git diff --check
```

## Blocked by

- `docs/issues/022-010-delete-superseded-source-display-paths.md`
