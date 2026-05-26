# 022-005: Amiga HUNK Restored Source Integration

Status: active

## Proposal

Proposal: `docs/proposals/022-platform-executable-kb-display-pipeline.md`

## What to build

Move Amiga HUNK source/listing/artifact output onto the shared restored source
model. CODE/DATA/BSS ownership and references should come from the shared model,
not duplicate display-only section inference.

Exact round-trip and reproduction behavior must remain green.

This must integrate with existing facts-v2 direct rebuild/reproduction compare
paths; source coverage is additional evidence, not a replacement for exactness.

## Acceptance criteria

- [ ] Amiga CODE/DATA/BSS ownership uses `restored_source_model_v1`.
- [ ] Amiga relocation/reference behavior maps into shared source reference
      records where currently supported.
- [ ] Source/listing/artifact output exposes ownership and references.
- [ ] Exact round-trip and reproduction gates remain green.
- [ ] Direct rebuild/reproduction profiles still report exactness through the
      existing gates.
- [ ] Candidate/deferred states, such as runtime entry uncertainty, remain
      non-promoted.
- [ ] Legacy Amiga display decisions duplicated by the shared model are deleted
      after replacement proof.
- [ ] Proposal 022 records any retained Amiga extension work.

## Verification

Run at minimum:

```powershell
cmd /c src\precommit.bat
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-macos-c-backend --current-amiga-hunk --current-atari-prg
git diff --check
```

## Blocked by

- `docs/issues/022-003-source-coverage-verifier.md`
- `docs/issues/022-004-shared-source-reference-records.md`
