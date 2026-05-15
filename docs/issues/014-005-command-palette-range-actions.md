# 014-005: Command Palette Range Actions

## Parent

[PRD 014: Range Listing Selection and Catalog Context](../prd/014-range-listing-selection-and-catalog-context.md)

## Related PRDs

- [PRD 008: Command Palette and Default Key Bindings](../prd/008-command-palette-and-key-bindings.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Render range catalog results in the command palette so best actions appear first and partial or unavailable actions show their reasons.

## Acceptance criteria

- [x] Range-context actions appear in the command palette for selected ranges.
- [x] Applicable actions are prioritized above partial and unavailable actions.
- [x] Partial and unavailable entries show concise reasons.
- [x] Executing a partial action uses only explicit applicable subranges.
- [x] CDP coverage selects data rows, opens the palette, and verifies mixed eligibility ordering.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Completion

Command palette loads the range catalog for multi-row selection and renders
availability reasons inline.

## Blocked by

- [014-004: Mixed Range Action Eligibility](014-004-mixed-range-action-eligibility.md)
