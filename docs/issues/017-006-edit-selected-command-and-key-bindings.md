# 017-006: Edit Selected Command And Key Bindings

## Parent

[PRD 017: Inline and Palette Parameter Sessions](../prd/017-inline-and-palette-parameter-sessions.md)

## Related PRDs

- [PRD 008: Command Palette and Default Key Bindings](../prd/008-command-palette-and-key-bindings.md)
- [PRD 011: Structured Contextual Action Metadata](../prd/011-structured-contextual-action-metadata.md)

## Type

AFK

## Labels

done

## What to build

Add the catalog-driven **Edit Selected Command** and default key bindings for comment, representation, semantic interpretation, and label rename.

## Acceptance criteria

- [x] `.` invokes the catalog-provided primary edit action for the current **Listing Selection**.
- [x] If no primary action is dominant, `.` shows explicit edit alternatives.
- [x] `;` opens comment edit, `r` opens representation choice, `s` opens semantic interpretation, and `F2` opens label rename when valid.
- [x] Key bindings appear in command palette entries.
- [x] UI priority is catalog-driven, not hardcoded by key handler.
- [x] Tests cover selected label, comment, literal, semantic operand, ambiguous context, and no editable context.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Completion Notes

- Direct bindings resolve through contextual catalog queries before falling back to target-level panels.
- `.` sorts editable actions by `interaction_schema.primary_rank`.

## Blocked by

- [017-003: Inline Text Editors For Labels And Comments](017-003-inline-text-editors-for-labels-and-comments.md)
- [017-004: Representation Choice Grid](017-004-representation-choice-grid.md)
- [017-005: Semantic Filtered Chooser Mechanics](017-005-semantic-filtered-chooser-mechanics.md)
