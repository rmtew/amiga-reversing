# PRD 015: Local-First Manual Edit Application

## Status

Complete as of 2026-05-16.

## Purpose

Make every manual edit feel local-first after durable **Manual Action Log** append. The UI should apply the best known local effect immediately, mark unresolved affected regions as in progress, and reconcile server-produced analysis/rendering results in place without blocking the viewport.

## Dependencies

- PRD 006: Manual Action Catalog, API, and CLI.
- PRD 007: Listing Selection and Keyboard Model.
- PRD 012: Command Parameter Editor.
- PRD 017: Inline and Palette Parameter Sessions, for interactive edit hosts that consume local-first application results.

## Scope

- Define a manual edit application contract that every catalog action uses after log append succeeds.
- Patch visible listing state when the action result has a known local effect.
- Mark affected visible rows or ranges as change-in-progress when server analysis/rendering must produce the final shape.
- Reconcile returned listing/review/reproduction updates in place without viewport-covering loading overlays.
- Preserve selection, scroll anchor, command palette state, dialog state, and movement through the viewport while work is pending.
- Keep the first implementation to one in-flight manual action per target, with later actions queued or blocked explicitly.

## Requirements

- **Immediate Manual Projection** occurs only after the related log append succeeds.
- Every successful manual action returns enough information for the UI to either patch known visible effects or mark affected rows/ranges as pending.
- Known local effects include label rename, comment edit, value representation, semantic hint, review-note state, and other actions whose visible effect is explicit in the action result.
- Larger actions, such as retyping data into structured blocks, keep the affected region visible and marked as change-in-progress until server analysis/rendering returns replacement rows.
- Server-side analysis or rendering may run asynchronously, but it must reconcile into the current viewport in place rather than requiring disruptive full listing regeneration as a user-visible step.
- Project badges, review counts, stale reproduction state, and affected listing rows refresh quietly without covering the viewport.
- While one action is in flight, later manual edits are queued or explicitly blocked with clear UI state; navigation remains available.
- If reconciliation invalidates the current **Listing Selection**, the UI reports precision loss rather than silently moving action target.

## Non-Goals

- Pre-write optimistic edits.
- Direct source-text mutation.
- Skipping required round-trip verification for source-affecting actions.
- Concurrent manual edit conflict resolution beyond a single in-flight action and optional queue.

## Verification

- Web source tests for post-append action-result application.
- CDP test that label rename updates the visible row without listing/reanalysis loading overlays.
- CDP or web test that a larger affected range remains visible as change-in-progress and is replaced in place.
- Tests proving failed action append does not patch visible listing state.
- Tests proving asynchronous reconciliation preserves selection, scroll anchor, and open command/dialog state where valid.
- Round-trip verification remains mandatory before source-affecting manual work can be marked clear.

## Issues

- [015-001: Manual Edit Application Contract](../issues/015-001-manual-edit-application-contract.md)
- [015-002: Local-First Visible Action Application](../issues/015-002-local-first-visible-action-application.md)
- [015-003: In-Progress Region Reconciliation](../issues/015-003-in-progress-region-reconciliation.md)
- [015-004: Manual Edit Queue and Status](../issues/015-004-manual-edit-queue-and-status.md)
- [015-005: PRD 015 Review and Tightening](../issues/015-005-prd-015-review-and-tightening.md)

## Open Questions

- Resolved: catalog execution returns an `application` object with
  `local_effects`, `pending_ranges`, and `reconciliation.required`.

## Completion Notes

- Manual catalog execution now returns a local-first application contract only
  after durable append succeeds.
- The web UI applies known local effects through one generic path and marks
  pending affected ranges for server reconciliation.
- Label rename and value representation are covered as concrete local effects.
- One in-flight manual edit is allowed; a second edit is blocked with clear
  status while navigation remains available.
