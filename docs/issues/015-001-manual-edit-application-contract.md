# 015-001: Manual Edit Application Contract

## Parent

[PRD 015: Local-First Manual Edit Application](../prd/015-local-first-manual-edit-application.md)

## Related PRDs

- [PRD 006: Manual Action Catalog, API, and CLI](../prd/006-manual-action-catalog-api-cli.md)
- [PRD 007: Listing Selection and Keyboard Model](../prd/007-listing-selection-keyboard-model.md)
- [PRD 017: Inline and Palette Parameter Sessions](../prd/017-inline-and-palette-parameter-sessions.md)

## Type

AFK

## Labels

done

## What to build

Define the catalog action result contract for local-first manual edit application after **Manual Action Log** append succeeds. Every successful manual action should tell the UI what visible effect is known now, what row or range is affected, and what asynchronous reconciliation remains pending.

PRD 017 parameter sessions use this contract after commit so inline and palette-hosted edits apply through the same local-first path.

## Acceptance criteria

- [x] Successful manual action responses distinguish applied local effects, pending affected ranges, and completed reconciliation.
- [x] Failed action append returns no local visible patch.
- [x] Action results identify affected row/range context using structured listing metadata where available.
- [x] The contract supports both small edits and larger edits that need server-produced replacement rows.
- [x] Route/backend tests cover success, failure, known local effect, and pending affected range responses.
- [x] `src\precommit.bat` and relevant focused tests pass before commit.

## Completion

Catalog execution responses now include `application.local_effects`,
`application.pending_ranges`, and `application.reconciliation.required`.

## Blocked by

- [006-002: Catalog Action Execution](006-002-catalog-action-execution.md)
