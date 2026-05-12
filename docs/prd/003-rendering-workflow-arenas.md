# Rendering Workflow Arenas

## Status

Approved for tasking after PRD 001 issues complete.

## Problem

Rendering paths still allocate temporary indexes, queues, layout arrays, include caches, and section writers on the heap even though their lifetime is one rendering workflow or a nested rendering pass.

## Goal

Move render lookup, source IR rendering, and source file emission temporary storage to **Workflow Arena** ownership with **Scratch Mark** boundaries for nested passes.

## Scope

- Migrate render lookup temporary graph/index/queue storage.
- Migrate source IR render temporary label indexes, include caches, and section counters.
- Migrate source file emit temporary layout arrays, logical offsets, section writers, and intermediate writer buffers.
- Keep public text/byte outputs as **Caller-Freed Output Buffers** where they cross the Python/CLI boundary.
- Use **Arena Builder** primitives for growable temporary collections.

## Non-Goals

- Do not change source rendering behavior or assembler output.
- Do not migrate durable result objects here.
- Do not introduce global or thread-local scratch arenas.
- Do not add compatibility shims for old allocation paths.

## Acceptance

- Touched rendering workflow paths no longer use heap-owned temporary arrays except at public caller-freed output boundaries.
- Scratch marks are used for nested temporary passes that can rewind before workflow return.
- No returned output points into a **Workflow Arena**.
- Before/after notes report raw heap allocation site count changes in touched modules.
- Existing source rendering, project rebuild, and round-trip tests pass.

## Later Task Slices

- Render lookup workflow arena migration.
- Source IR render workflow arena migration.
- Source file emit workflow arena migration.
- Output boundary regression tests.

## Issues

- [003-001 Render Lookup Workflow Arena](../issues/003-001-render-lookup-workflow-arena.md)
- [003-002 Source IR Render Workflow Arena](../issues/003-002-source-ir-render-workflow-arena.md)
- [003-003 Source File Emit Workflow Arena](../issues/003-003-source-file-emit-workflow-arena.md)
- [003-004 Render Output Boundary Guards](../issues/003-004-render-output-boundary-guards.md)
