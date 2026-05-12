# Parser Workflow and Result Split

## Status

Approved for tasking after PRD 001 issues complete.

## Problem

Parser modules allocate transient parse state and durable parsed result internals with the same heap tools. Temporary names, debug payloads, symbol lists, and container records are easy to over-retain or free piecemeal.

## Goal

Make parser ownership explicit: temporary parse state uses a **Workflow Arena**, while returned parsed object internals use a **Result Arena**.

## Scope

- Migrate Amiga HUNK parser temporary strings, symbol names, debug payloads, and list-building state.
- Migrate Atari/container parser paths with the same lifetime split where allocation inventory shows matching patterns.
- Allow Local C API changes to pass explicit workflow/result arenas.
- Ensure durable parsed objects own their internals through a result arena.
- Use **Arena Builder** primitives for parser append/list construction.

## Non-Goals

- Do not change binary/container semantics.
- Do not keep legacy parser allocation APIs.
- Do not modify vasm, Musashi, or oracle behavior.
- Do not mark entities verified without existing round-trip/type-specific checks.

## Acceptance

- No temporary parse pointer is stored in returned parser results.
- Parser result destroy paths tear down a **Result Arena** instead of freeing migrated internals piecemeal.
- Workflow parse allocations are released before the top-level parse call returns.
- Container/reproduction tests cover migrated parser paths.
- Before/after notes report raw heap allocation site count changes in touched modules.
- Existing precommit and relevant round-trip tests pass.

## Later Task Slices

- Amiga HUNK parser split.
- Atari parser split.
- Platform disk/container parser split.
- Atari disk parser split.
- Parser lifetime regression tests.

## Issues

- [004-001 Amiga HUNK Parser Ownership Split](../issues/004-001-amiga-hunk-parser-ownership-split.md)
- [004-002 Atari Parser Ownership Split](../issues/004-002-atari-parser-ownership-split.md)
- [004-003 Platform Disk Container Parser Ownership Split](../issues/004-003-disk-container-parser-ownership-split.md)
- [004-004 Atari Disk Parser Ownership Split](../issues/004-004-atari-disk-parser-ownership-split.md)
- [004-005 Parser Lifetime Regression Coverage](../issues/004-005-parser-lifetime-regression-coverage.md)
