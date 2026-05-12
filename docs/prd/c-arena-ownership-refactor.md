# C Arena Ownership Refactor PRD

## Purpose

Refactor C memory ownership around explicit arena lifetimes. The goal is not a small safe slice; it is a comprehensive cleanup that classifies every allocation site, converts workflow/result ownership first, and removes compatibility ownership paths rather than preserving old cleanup complexity.

## Background

The C codebase already has `util_arena` and arena-backed IR objects, but ownership is mixed with ad hoc `malloc`, `calloc`, `realloc`, and deep cleanup paths. This makes workflow failure paths noisy and obscures which memory is temporary, result-owned, or returned to Python/CLI callers.

ADR: [0002-c-arena-ownership.md](../adr/0002-c-arena-ownership.md)

## Terms

- **Workflow Arena**: temporary memory for one top-level C workflow call.
- **Scratch Mark**: rewind point inside a **Workflow Arena** for a local pass.
- **Result Arena**: memory owned by one result object and destroyed with that object.
- **Caller-Freed Output Buffer**: standalone text/bytes crossing a Python or CLI edge.
- **Local C API**: repo-local C interface that may change for cleaner ownership.

## Scope

- Classify all `src` allocation sites by lifetime.
- Improve `util_arena` with minimal stats and tests.
- Convert result/workflow-owned arrays and strings to explicit arenas.
- Start migration with `AsmSourceFile`.
- Refactor existing arena-backed IR objects to explicit **Result Arena** ownership.
- Introduce workflow modules for facts/source rendering/platform file workflows where they reduce cleanup spread.
- Add staged source-scan checks for migrated modules.

## Work Order

Issues in `docs/issues` are ordered by dependency. Work starts with `0001-classify-c-allocation-lifetimes.md`; later implementation issues should use the inventory instead of doing opportunistic allocation conversions.

The allocation inventory lives at `docs/c-arena-allocation-inventory.md`.

Standard verification command for implementation issues:

```powershell
cmd /c src\precommit.bat
```

## Non-Goals

- No global or per-thread scratch arena.
- No blanket ban on heap allocation.
- No individual free support in core `Arena`.
- No virtual-memory-reserved arena rewrite unless profiling later proves need.
- No compatibility/fallback ownership paths for internal migrations.

## Ownership Invariants

- A **Workflow Arena** is destroyed before its top-level call returns.
- A **Scratch Mark** is rewound before leaving its local pass.
- A **Result Arena** lives exactly as long as its result object.
- A **Caller-Freed Output Buffer** never points into a **Workflow Arena** or **Result Arena**.
- C modules that allocate internal pointers choose workflow or result ownership explicitly at their interface.
- Local C APIs may change when arena ownership gives a cleaner interface.
- Arena allocation failure returns structured errors/diagnostics; `Arena` itself stays low-level and returns `NULL`.

## Migration Phases

1. Allocation inventory
   - Classify every `malloc`, `calloc`, `realloc`, `free`, and `arena_create` in `src`.
   - Categories: `workflow`, `result`, `caller_freed_output`, `external_read_buffer`, `test_only`, `keep_heap_for_now`.
   - Write the inventory to `docs/c-arena-allocation-inventory.md`.

2. Arena foundation
   - Add current/peak/block allocation counters to `Arena`.
   - Add focused `util_arena` tests for stats, mark/rewind, reset, and block growth.
   - Keep linked-block growth.

3. First result migration
   - Convert `AsmSourceFile` to explicit **Result Arena** ownership.
   - Replace `realloc` append arrays with arena-backed append buffers.
   - Remove deep per-field free paths.
   - Add a source-scan allowlist blocking new raw allocation in migrated source model files.

4. IR arena cleanup
   - Refactor `M68kSourceFileIR` and `M68kSourceAnalysisIR` toward external **Result Arena** ownership.
   - Remove surprise nested arenas and compatibility create/destroy paths where internal callers can be updated.

5. Workflow cleanup
   - Introduce workflow-owned state for facts/source rendering paths.
   - Use **Scratch Marks** for pass-local arrays.
   - Keep returned text/bytes as **Caller-Freed Output Buffer** only at Python/CLI edges.

6. Platform workflow cleanup
   - Consolidate repeated object/policy/profile/analysis/JSON cleanup in platform file workflows.
   - Change local APIs rather than preserving old ownership adapters.

## Acceptance Checks

- `docs/c-arena-allocation-inventory.md` exists and covers every `src` allocation site.
- `cmd /c src\precommit.bat` passes for implementation issues.
- Existing Python C-backend tests pass.
- Migrated modules have no unclassified raw allocation calls.
- Returned Python/CLI text and byte buffers remain independently freeable.
- Arena stats appear in at least one workflow profile or debug path.
