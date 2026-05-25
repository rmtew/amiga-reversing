# 021-009: Native Flat M68K Buffer Backend

Status: active

## Proposal

Proposal: `docs/proposals/021-native-macos-code-source-pipeline.md`

## Context

021-007 removed the visible Mac CODE raw transport, but the new C buffer
artifact entry point still configures and loads its in-memory bytes through the
`amiga-raw` backend internally. That is not the clean final architecture. Mac
CODE should be able to render flat selected CODE bytes without depending on
Amiga raw platform identity.

This issue creates the reusable low-level backend or policy path needed before
Mac CODE can stop using `amiga-raw` internals.

## What to build

Add a native platform-neutral flat M68K buffer path for in-memory executable
bytes. It should be suitable for selected Mac CODE bytes and any future
non-Amiga flat M68K byte source that needs local-offset disassembly.

The path must own its C policy/object setup directly. It must not be implemented
as a thin alias that calls `configure_analysis_policy_for_alloc(...,
"amiga-raw", ...)` or `load_raw_object_from_buffer("amiga-raw", ...)`.

The public artifact/profile identity for this issue can be neutral, for
example `m68k-flat-buffer`, but it must not be `amiga-raw`.

## Acceptance criteria

- [ ] A C-owned flat M68K buffer backend/policy path exists for in-memory bytes.
- [ ] The new path can build a listing artifact from bytes equivalent to
      `20 5f 4e 75` and render `movea.l (a7)+,a0` / `rts`.
- [ ] The new path does not call the `amiga-raw` policy or raw object loader.
- [ ] Tests fail if the new flat buffer artifact reports `backend:
      amiga-raw`.
- [ ] Existing Amiga raw binary behavior is unchanged and still covered.
- [ ] Proposal 021 records the new backend boundary and any intentionally
      retained generic M68K internals.

## Verification

Run at minimum:

```powershell
cmd /c src\build.bat
uv run python -m pytest tests\test_macos_c_backend.py tests\test_c_backend.py -q
uv run python -m amiga_reversing.tools.platform_executable_formats validate
git diff --check
```

## Blocked by

None - can start immediately.
