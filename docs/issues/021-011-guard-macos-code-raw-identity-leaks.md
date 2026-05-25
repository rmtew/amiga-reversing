# 021-011: Guard Mac CODE Raw Identity Leaks

Status: active

## Proposal

Proposal: `docs/proposals/021-native-macos-code-source-pipeline.md`

## Context

After 021-010, Mac CODE should no longer depend on `amiga-raw` for selected
CODE artifact rendering or candidate preview decoding. This needs a focused
regression guard so the old transport cannot quietly return.

## What to build

Add tests or validator checks that prove Mac CODE artifact paths do not leak
raw Amiga identity through public profiles or through the Mac CODE C buffer
entry point implementation boundary.

This is a guard issue, not a semantic-promotion issue. It must not change Mac
byte-entry, relocation/fixup, source-to-CODE, or non-CODE resource statuses.

## Acceptance criteria

- [ ] Tests fail if selected Mac CODE listing, source text, summary, navigation,
      row windows, or project preview profiles report `backend: amiga-raw`.
- [ ] Tests fail if those public profiles expose `wrapped_backend: amiga-raw`.
- [ ] A source-level or unit-level guard covers the Mac CODE C buffer artifact
      path so it cannot reintroduce `amiga-raw` policy/object setup.
- [ ] Existing `RawBinarySource` tests remain valid for actual raw binary
      sources.
- [ ] Platform executable coverage remains `invalid: 0`.
- [ ] Proposal 021 records the regression guard and what it deliberately does
      not prove.

## Verification

Run at minimum:

```powershell
uv run python -m pytest tests\test_macos_c_backend.py tests\test_macos_project_payload.py tests\test_macos_target_artifact.py tests\test_macos_web_view.py tests\test_web_app_source.py -q
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-macos-c-backend --current-amiga-hunk --current-atari-prg
git diff --check
```

## Blocked by

- `docs/issues/021-010-move-macos-code-buffer-artifact-off-amiga-raw.md`
