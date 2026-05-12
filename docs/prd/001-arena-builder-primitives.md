# Arena Builder Primitives

## Status

Approved for tasking.

## Problem

Several C modules still use `malloc`, `calloc`, `realloc`, and `free` for append-style arrays or output accumulators whose lifetime already matches a **Workflow Arena** or **Result Arena**. Migrating each module directly would duplicate growable array logic and risk inconsistent ownership semantics.

## Goal

Provide small reusable **Arena Builder** primitives that make append-style arena-owned storage explicit, testable, and cheap to reuse across decode, facts, rendering, and parser code.

## Scope

- Add generic arena-backed growable array/builder support.
- Add typed wrappers or macros for common struct-array use.
- Define finalize semantics: finalized memory is arena-owned and is not individually freed.
- Support both **Workflow Arena** and **Result Arena** callers.
- Preserve arena allocation stats visibility.
- Document scratch conflict rules for nested temporary use.

## Builder Model

The first implementation uses arena-owned append chunks with flatten-on-finalize. This avoids hidden heap ownership, avoids requiring in-place arena reallocation, and keeps finalized storage contiguous for callers that need array indexing or sorted insertion.

Builders may use **Scratch Mark** staging only when the caller proves the scratch arena cannot conflict with the final destination arena. The default path must work with one explicit arena and no hidden fallback allocation.

## Non-Goals

- Do not migrate decode, facts, render, or parser users in this PRD.
- Do not add compatibility shims for older heap-owned vector APIs.
- Do not introduce virtual-reserved arenas, pools, or thread-local scratch arenas.

## Acceptance

- Builder tests cover append, growth, zero-length finalize, typed use, and ownership after arena reset/destroy.
- Callers cannot accidentally finalize into heap-owned storage.
- The primitive exposes enough capacity/length state for users that currently need sorted insertion or bulk append.
- Existing precommit passes.
- Allocation stats remain available for before/after reporting in later PRDs.

## Later Task Slices

- Generic builder implementation.
- Typed helper layer.
- Tests and documentation.

## Issues

- [001-001 Generic Arena Builder](../issues/001-001-generic-arena-builder.md)
- [001-002 Typed Arena Builder Helpers](../issues/001-002-typed-arena-builder-helpers.md)
- [001-003 Builder Stats and Scratch Contract](../issues/001-003-builder-stats-and-scratch-contract.md)
