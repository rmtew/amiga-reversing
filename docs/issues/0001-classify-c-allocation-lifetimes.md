# Classify C allocation lifetimes

Type: AFK

## Parent

[C Arena Ownership Refactor PRD](../prd/c-arena-ownership-refactor.md)

## What to build

Create an allocation inventory for `src` that classifies every raw allocation, free, and arena creation by lifetime. This is the tracer bullet that makes later arena migrations deliberate instead of opportunistic.

Write the inventory to `docs/c-arena-allocation-inventory.md`.

## Acceptance criteria

- [x] Every `malloc`, `calloc`, `realloc`, `free`, and `arena_create` site in tracked `src` files is listed.
- [x] Each site is classified as `workflow`, `result`, `caller_freed_output`, `external_read_buffer`, `test_only`, or `keep_heap_for_now`.
- [x] Each `keep_heap_for_now` entry has a short reason.
- [x] Inventory identifies the first modules eligible for raw-allocation source-scan guards.
- [x] Standard verification for later implementation issues is documented as `cmd /c src\precommit.bat`.

## Blocked by

None - can start immediately
