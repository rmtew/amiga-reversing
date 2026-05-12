# Decode and Facts Result Arenas

## Status

Approved for tasking after PRD 001 issues complete.

## Problem

`M68kDecodeIR` and `M68kFactIR` return durable result objects but still own internal arrays through scattered heap allocations. This creates mixed ownership inside result objects and keeps destroy functions coupled to per-array cleanup.

## Goal

Move decode IR and facts IR internal storage to explicit **Result Arena** ownership so each result object has one durable arena lifetime.

## Scope

- Migrate `M68kDecodeIR` section arrays, candidate arrays, and absent CPU arrays.
- Migrate `M68kFactIR` append arrays.
- Allow Local C API signature changes to pass or own explicit result arenas.
- Replace per-array frees with result arena teardown.
- Use **Arena Builder** primitives where append/growth is needed.

## Non-Goals

- Do not preserve old heap-owned result APIs.
- Do not keep compatibility wrappers.
- Do not change instruction semantics or generated M68K knowledge.
- Do not migrate rendering or parser temporary allocations here.

## Acceptance

- Decode and facts result internals are owned by a **Result Arena**.
- Destroy paths no longer free migrated internal arrays individually.
- No returned decode/facts pointer depends on a **Workflow Arena**.
- Tests cover result lifetime behavior where practical.
- Before/after notes report raw heap allocation site count changes in touched modules.
- Existing precommit and relevant round-trip tests pass.

## Later Task Slices

- Decode IR result arena migration.
- Facts IR result arena migration.
- Lifetime/assertion tests.

## Issues

- [002-001 Decode IR Result Arena](../issues/002-001-decode-ir-result-arena.md)
- [002-002 Facts IR Result Arena](../issues/002-002-facts-ir-result-arena.md)
