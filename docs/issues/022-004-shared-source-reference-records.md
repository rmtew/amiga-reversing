# 022-004: Shared Source Reference Records

Status: active

## Proposal

Proposal: `docs/proposals/022-platform-executable-kb-display-pipeline.md`

## What to build

Add shared `source_reference_records` for relocations, fixups, address refs,
symbol refs, and platform extension references. References must attach to source
ownership ranges and source rows.

Review current facts-v2 relocation counters, reproduction exactness metadata,
manual/runtime address refs, and Mac Segment Loader deferred fixup state before
finalizing the shape.

## Acceptance criteria

- [ ] C owns the shared source reference record shape.
- [ ] Reference records can represent relocation/fixup/address/symbol effects.
- [ ] Amiga or Atari existing relocation/reference behavior maps into the shared
      shape without weakening round-trip gates.
- [ ] Existing Amiga/Atari relocation exactness/refusal information remains
      expressible.
- [ ] Mac Segment Loader fixups have a target/reference representation even
      where a custom extension remains unresolved.
- [ ] References carry status, provenance, fact ids, and parser use where
      applicable.
- [ ] Tests cover reference attachment to ownership ranges and source rows.
- [ ] Proposal 022 records any unresolved platform extension requirements.

## Verification

Run at minimum:

```powershell
cmd /c src\build.bat
uv run python -m amiga_reversing.tools.platform_executable_formats validate
git diff --check
```

## Blocked by

- `docs/issues/022-002-shared-source-ownership-model.md`
- Review `docs/issues/022-003-source-coverage-verifier.md` before finalizing
  verifier assumptions.
