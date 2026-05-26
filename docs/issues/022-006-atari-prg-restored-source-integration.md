# 022-006: Atari PRG Restored Source Integration

Status: active

## Proposal

Proposal: `docs/proposals/022-platform-executable-kb-display-pipeline.md`

## What to build

Move Atari ST PRG source/listing/artifact output onto the shared restored source
model. TEXT/DATA/BSS ownership and relocation/basepage/symbol references should
come from the shared model or explicit deferred placeholders.

Exact round-trip and reproduction behavior must remain green.

This must integrate with existing facts-v2 direct rebuild/reproduction compare
paths; source coverage is additional evidence, not a replacement for exactness.

## Acceptance criteria

- [ ] Atari TEXT/DATA/BSS ownership uses `restored_source_model_v1`.
- [ ] Atari relocation/basepage/symbol states map into shared source reference
      records or explicit deferred placeholders.
- [ ] Source/listing/artifact output exposes ownership and references.
- [ ] Exact round-trip and reproduction gates remain green.
- [ ] Direct rebuild/reproduction profiles still report exactness through the
      existing gates.
- [ ] Candidate/deferred states remain governed by Proposal 018.
- [ ] Legacy Atari display decisions duplicated by the shared model are deleted
      after replacement proof.
- [ ] Proposal 022 records any retained Atari extension work.

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
