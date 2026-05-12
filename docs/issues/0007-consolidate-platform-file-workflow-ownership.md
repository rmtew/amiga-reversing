# Consolidate platform file workflow ownership

Type: AFK

## Parent

[C Arena Ownership Refactor PRD](../prd/c-arena-ownership-refactor.md)

## What to build

Consolidate repeated platform-file workflow ownership for object loading, effective policy, profile collection, source analysis, diagnostics, and JSON/text output. Local C APIs may change to make ownership explicit and remove old cleanup adapters.

## Acceptance criteria

- [x] Platform file workflows use explicit workflow/result/output ownership.
- [x] Repeated cleanup patterns are concentrated in workflow-owned state.
- [x] Plain text/byte outputs crossing Python or CLI edges are **Caller-Freed Output Buffers**.
- [x] No internal compatibility/fallback ownership paths are added.
- [x] Existing platform file, decompression, and C-backend tests pass.

## Blocked by

- [0002-add-arena-stats-and-tests.md](0002-add-arena-stats-and-tests.md)
