# 011-002: Structured Catalog Context Model

## Parent

[PRD 011: Structured Contextual Action Metadata](../prd/011-structured-contextual-action-metadata.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Add a structured row/element context model for the Manual Action Catalog. This model should normalize cached listing row payloads into stable row contexts and element contexts that web, API, and CLI callers can use consistently.

## Acceptance criteria

- [ ] Catalog row contexts and element contexts are distinct and serializable.
- [ ] Element contexts include kind, stable row identity, source location, and element-specific fields such as value, symbol, operand index, or access role.
- [ ] Invalid or stale element contexts return clear errors instead of falling back silently.
- [ ] Element-only actions cannot run against row-only context unless the action explicitly supports row fallback.
- [ ] Backend route tests cover valid row context, valid element context, stale element context, and row/element mismatch.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [011-001: C Listing Element Metadata](011-001-c-listing-element-metadata.md)
