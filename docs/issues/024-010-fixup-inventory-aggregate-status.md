# 024-010: Fixup Inventory Aggregate Status

Status: complete
Type: AFK
Source proposal: docs/proposals/024-classic-mac-os-segment-loader-fixups.md

## Proposal Context

- 024-009 added documented far-model CODE relocation offset parsing.
- `segment_loader_fixup_inventory_v1` now derives its top-level status from
  records.
- Review found one residual policy gap: a future mixed fixture with both
  parseable and malformed records would currently report top-level `parseable`,
  which can hide malformed relocation metadata at the aggregate level.

## What To Build

Change the top-level inventory status to reflect the worst actionable state and
emit record counts by classification.

Required status order:

```text
malformed if any record is malformed
parseable if no records are malformed and at least one record is parseable
blocked otherwise
```

The decoder may later process parseable records in a mixed fixture, but the
aggregate inventory must still warn that malformed relocation metadata exists.

## Acceptance Criteria

- [x] Top-level `segment_loader_fixup_inventory_v1.status` is `malformed` when
      any record is malformed, even if another record is parseable.
- [x] Top-level status is `parseable` only when at least one record is parseable
      and no records are malformed.
- [x] Top-level status remains `blocked` for the current MPW `Asm` fixture.
- [x] Inventory JSON emits counts for `absent`, `parseable`, `unsupported`,
      `custom_unknown`, and `malformed` records.
- [x] Native C/API tests cover all-blocked, parseable-only, malformed-only, and
      mixed parseable+malformed aggregation.
- [x] Proposal 024 records the aggregate-status policy.

## Completed Result

- Aggregate policy moved into the C Mac resource model and is covered by native
  C tests.
- JSON inventory emits counts by classification.
- Mixed parseable+malformed input reports top-level `malformed`.
- Current MPW `Asm` remains `blocked` with all records counted as `absent`.

## Blocked By

- docs/issues/024-009-documented-code-segment-layout-parser.md

## Required Sign-Off

- [x] Native C unit tests pass.
- [x] Focused Mac backend tests pass.
- [x] Platform executable validate/coverage pass.
- [x] `cmd /c src\precommit.bat` passes.
- [x] `git diff --check` passes.
