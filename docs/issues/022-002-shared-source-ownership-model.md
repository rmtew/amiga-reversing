# 022-002: Shared Source Ownership Model

Status: active

## Proposal

Proposal: `docs/proposals/022-platform-executable-kb-display-pipeline.md`

## What to build

Add the C-owned `restored_source_model_v1` and `source_ownership_ranges` model.
It must represent code, data, BSS, metadata, relocation/fixup, padding,
placeholder, and unknown ownership over executable source bytes.

Wire at least one Amiga or Atari path and one Mac path far enough to prove the
model shape against real current parser/import data.

Start from `platform_executable_summary_v1` and the render-plan/listing artifact
seams. Do not create a disconnected report that only mirrors inspect JSON.

## Acceptance criteria

- [ ] C owns the restored source model data shape.
- [ ] Ownership ranges carry role, byte space, start, size, fact id, fact
      status, parser use, and platform provenance where applicable.
- [ ] At least one Amiga or Atari path emits or consumes ownership ranges.
- [ ] At least one Mac CODE path emits or consumes ownership ranges.
- [ ] The model is reachable from a listing artifact/API path, not only a
      standalone parser report.
- [ ] Candidate/deferred/unsupported facts remain non-accepted.
- [ ] Tests prove basic ownership model emission/consumption.
- [ ] Proposal 022 records model constraints discovered during implementation.

## Verification

Run at minimum:

```powershell
cmd /c src\build.bat
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-macos-c-backend --current-amiga-hunk --current-atari-prg
git diff --check
```

## Blocked by

- `docs/issues/022-001-restored-source-inventory-and-deletion-map.md`
