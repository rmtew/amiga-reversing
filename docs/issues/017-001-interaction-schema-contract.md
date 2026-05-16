# 017-001: Interaction Schema Contract

## Parent

[PRD 017: Inline and Palette Parameter Sessions](../prd/017-inline-and-palette-parameter-sessions.md)

## Related PRDs

- [PRD 006: Manual Action Catalog, API, and CLI](../prd/006-manual-action-catalog-api-cli.md)
- [PRD 011: Structured Contextual Action Metadata](../prd/011-structured-contextual-action-metadata.md)
- [PRD 012: Command Parameter Editor](../prd/012-command-parameter-editor.md)

## Type

AFK

## Labels

done

## What to build

Extend catalog action responses with context-specific **Interaction Schema** metadata that describes how a **Parameter Session** should collect parameters in palette and inline hosts.

## Acceptance criteria

- [x] Catalog entries can include interaction type, host suitability, option metadata, validation metadata, default selection, and typed preview metadata.
- [x] `parameter_schema` remains the authoritative validation/submission schema.
- [x] `interaction_schema` contains no backend HTML.
- [x] Interaction schema can describe text, choice-grid, and filtered-chooser sessions.
- [x] Backend and route tests cover schemas for at least one label edit, representation choice, and semantic chooser fixture.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Completion Notes

- Manual Action Catalog entries now expose `interaction_schema` for text, choice-grid, filtered-chooser, and generic form sessions.
- `primary_rank` lets the UI choose the default edit action without action-id heuristics.

## Blocked by

- [006-001: Review Item Action Catalog](006-001-review-item-action-catalog.md)
- [011-002: Structured Catalog Context Model](011-002-structured-catalog-context-model.md)
