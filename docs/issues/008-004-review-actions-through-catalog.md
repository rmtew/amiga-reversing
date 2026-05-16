# 008-004: Review Actions Through Catalog

## Parent

[PRD 008: Command Palette and Default Key Bindings](../prd/008-command-palette-and-key-bindings.md)

## Type

AFK

## Labels

done

## What to build

Prove the Review dialog and command palette execute the same catalog-backed actions, preserving existing review workflows while removing divergent UI behavior.

## Acceptance criteria

- [x] A Review dialog action and the matching palette action share the same catalog action id and execution path.
- [x] Existing review action e2e coverage still passes through the catalog-backed path.
- [x] No web-only manual action eligibility remains for catalog-covered review actions.
- [x] Tests cover at least one seed action and one resolve/acknowledge action from both surfaces.
- [x] `src\precommit.bat` and any relevant tests not covered by it pass before commit.

## Blocked by

- [006-002: Catalog Action Execution](006-002-catalog-action-execution.md)
- [008-002: Contextual Command Palette](008-002-contextual-command-palette.md)
