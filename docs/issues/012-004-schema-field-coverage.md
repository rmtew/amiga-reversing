# 012-004: Schema Field Coverage

## Parent

[PRD 012: Command Parameter Editor](../prd/012-command-parameter-editor.md)

## Related PRDs

- [PRD 006: Manual Action Catalog, API, and CLI](../prd/006-manual-action-catalog-api-cli.md)
- [PRD 010: Semantic Helper Actions](../prd/010-semantic-helper-actions.md)
- [PRD 017: Inline and Palette Parameter Sessions](../prd/017-inline-and-palette-parameter-sessions.md)

## Type

AFK

## Labels

ready-for-agent

## What to build

Extend the palette-hosted **Command Parameter Editor** beyond the initial text field so current catalog schemas can render simple string, enum, boolean, and numeric parameters consistently.

This issue covers parameter validation field types. Rich host behavior, option previews, and filtered chooser mechanics are covered by PRD 017.

## Acceptance criteria

- [ ] Supported field types render from `parameter_schema` without action-specific UI branches.
- [ ] Defaults and required flags are honored for every supported type.
- [ ] Unsupported schema fields fail clearly instead of rendering broken controls.
- [ ] Tests cover at least one string, enum, boolean, and numeric schema.
- [ ] Existing rename-label behavior remains unchanged.
- [ ] `src\precommit.bat` and relevant focused tests pass before commit.

## Blocked by

- [012-002: Parameter Validation Feedback](012-002-parameter-validation-feedback.md)
