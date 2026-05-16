# 011-001: C Listing Element Metadata

## Parent

[PRD 011: Structured Contextual Action Metadata](../prd/011-structured-contextual-action-metadata.md)

## Type

AFK

## Labels

done

## What to build

Extend cached C listing row payloads so contextual actions can identify operands, immediates, literals, symbols, equates, app-slot references, typed accesses, and source byte spans without parsing rendered text.

## Acceptance criteria

- [x] Listing rows expose structured element metadata for current command-palette action families.
- [x] Immediate/literal metadata includes value, width where known, operand index where applicable, hunk/source offset, and stable row identity.
- [x] Symbol/equate/app-slot references include symbol, access role, operand index where applicable, and stable row identity.
- [x] Any instruction-derived fields are produced from generated/spec-driven decode metadata, not downstream hardcoding.
- [x] C/backend tests cover representative instruction operands, data directives, labels, and symbol/equate references.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- None
