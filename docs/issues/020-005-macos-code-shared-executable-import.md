# 020-005: Mac CODE Shared Executable Import

Status: active
Type: AFK
Source proposal: docs/proposals/020-platform-executable-import-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/020-platform-executable-import-pipeline.md`
- Blocked by: 020-002 and review of at least one completed platform migration.
- Current state: Mac CODE has C-backed classification and starter listing
  surfaces, but it must be represented through the same shared executable model
  rather than a Mac-only range surface.
- Desired state after this issue: Mac HFS/resource/CODE classified ranges flow
  through shared executable ranges while preserving 018 deferred boundaries.

## What To Build

Migrate current Mac CODE classified range output onto the shared executable
model. CODE 0 must remain metadata-only. Nonzero CODE resources must expose
accepted metadata, candidate code windows, no-preview reasons, and deferred
relocation/fixup state through shared ranges.

Do not promote the current nonzero CODE byte-entry heuristic.

## Acceptance Criteria

- [ ] Current MPW `Asm` Mac CODE summary emits shared executable ranges.
- [ ] CODE 0 is metadata-only and cannot be decoded as instructions.
- [ ] Nonzero CODE candidate windows remain candidate-only.
- [ ] Relocation/fixup state remains deferred-only.
- [ ] Existing Mac artifact/web/listing tests consume or validate shared range
  output.
- [ ] Proposal 020 records any Mac-specific model extension needed by the other
  platforms.

## Blocked By

- 020-002
- Review of 020-003 or 020-004 completion

## Required Sign-Off

- [ ] No Mac byte-entry fact promotion.
- [ ] No relocation/fixup implementation without accepted evidence.
- [ ] No Mac-only compatibility path kept as active default.
- [ ] `platform_executable_formats validate` passes.
- [ ] Mac focused parser/listing/artifact/web tests pass.
- [ ] `git diff --check` passes.

## Completion Evidence

Record the Mac raw summary, artifact/listing proof, and any old Mac path now
eligible for deletion in 020-008.
