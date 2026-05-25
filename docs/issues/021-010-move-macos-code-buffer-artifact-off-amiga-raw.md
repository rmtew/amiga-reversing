# 021-010: Move Mac CODE Buffer Artifact Off Amiga Raw Internals

Status: active

## Proposal

Proposal: `docs/proposals/021-native-macos-code-source-pipeline.md`

## Context

021-007 added `platform_file_facts_v2_listing_artifact_macos_code_buffer_create`
so Mac CODE selected bytes and preview bytes no longer flow through Python temp
files or public `RawBinarySource` identity. The C implementation still uses
`amiga-raw` policy/object setup internally.

After 021-009 provides a neutral flat M68K buffer path, the Mac CODE buffer
artifact entry point should use it.

## What to build

Change the Mac CODE in-memory listing artifact entry point to use the native
flat M68K buffer path from 021-009. The public API remains Mac CODE shaped:
callers pass selected CODE bytes plus a Mac display path, and profiles/windows
continue to report `backend: macos-code` and `source_kind:
macos_code_resource` where applicable.

This must be a deletion/replacement of the remaining `amiga-raw` dependency in
the Mac CODE buffer artifact path, not another wrapper around it.

## Acceptance criteria

- [ ] `platform_file_facts_v2_listing_artifact_macos_code_buffer_create` no
      longer calls `configure_analysis_policy_for_alloc(..., "amiga-raw", ...)`.
- [ ] It no longer calls `load_raw_object_from_buffer("amiga-raw", ...)`.
- [ ] Selected `MacosCodeResourceSource` listing/artifact paths still bypass
      `_source_file_for_c_backend`.
- [ ] Candidate preview decoding still uses the Mac CODE byte artifact helper
      and does not construct `RawBinarySource` or temp raw files.
- [ ] Public Mac CODE profiles remain `backend: macos-code`; no public
      `wrapped_backend: amiga-raw` returns.
- [ ] Candidate/deferred Mac executable-format facts remain unchanged and
      non-promoted.

## Verification

Run at minimum:

```powershell
cmd /c src\build.bat
uv run python -m pytest tests\test_macos_c_backend.py tests\test_macos_project_payload.py tests\test_macos_target_artifact.py tests\test_macos_web_view.py tests\test_web_app_source.py -q
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-macos-c-backend --current-amiga-hunk --current-atari-prg
git diff --check
```

## Blocked by

- `docs/issues/021-009-native-flat-m68k-buffer-backend.md`
