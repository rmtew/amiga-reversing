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

ready-for-agent

## What to build

Extend catalog action responses with context-specific **Interaction Schema** metadata that describes how a **Parameter Session** should collect parameters in palette and inline hosts.

## Acceptance criteria

- [ ] Catalog entries can include interaction type, host suitability, option metadata, validation metadata, default selection, and typed preview metadata.
- [ ] `parameter_schema` remains the authoritative validation/submission schema.
- [ ] `interaction_schema` contains no backend HTML.
- [ ] Interaction schema can describe text, choice-grid, and filtered-chooser sessions.
- [ ] Backend and route tests cover schemas for at least one label edit, representation choice, and semantic chooser fixture.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [006-001: Review Item Action Catalog](006-001-review-item-action-catalog.md)
- [011-002: Structured Catalog Context Model](011-002-structured-catalog-context-model.md)
