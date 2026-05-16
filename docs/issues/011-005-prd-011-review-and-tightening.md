# 011-005: PRD 011 Review and Tightening

## Parent

[PRD 011: Structured Contextual Action Metadata](../prd/011-structured-contextual-action-metadata.md)

## Type

AFK

## Labels

done

## What to build

Review the completed structured contextual action work against PRD 011. Remove remaining rendered-text interpretation from catalog eligibility, close weak context fallbacks, and add follow-up issues only for genuinely separate future work.

## Acceptance criteria

- [x] Review C row payloads, catalog context modeling, semantic helper matching, web selection, CLI/API behavior, and tests against PRD 011.
- [x] Confirm rendered/source text is not used to decide semantic helper eligibility.
- [x] Confirm Manual Seed, Manual Representation, Manual Register Seed, and Manual Semantic Hint separation remains intact.
- [x] Confirm stale/imprecise element handling is explicit and user-visible.
- [x] Add missing tests or follow-up issues for gaps not fixed in this slice.
- [x] PRD 011 links and issue statuses remain accurate after review.
- [x] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

- [011-001: C Listing Element Metadata](011-001-c-listing-element-metadata.md)
- [011-002: Structured Catalog Context Model](011-002-structured-catalog-context-model.md)
- [011-003: Replace Text-Based Semantic Matching](011-003-replace-text-based-semantic-matching.md)
- [011-004: Web Element Selection Uses Structured Context](011-004-web-element-selection-uses-structured-context.md)
