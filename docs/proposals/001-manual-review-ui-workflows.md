# Proposal 001: Manual Review UI Workflows

## TODO Coverage

- `TODO.md` Unsorted: inline label rename instead of browser prompt.
- `TODO.md` Unsorted: manual edits should apply naturally without disruptive loading dialogs or visible reanalysis.
- `TODO.md` Unsorted: initial open location should select and center the entrypoint row when no persisted location exists.
- `TODO.md` Unsorted: user-created notes/bookmarks should appear in manual review.
- `TODO.md` Manual review/editing and analysis state.
- `TODO.md` WebUI notes and future directions.

## Current State

- Manual user intent is stored in the Manual Action Log and projected into effective metadata, per `docs/adr/0004-manual-action-log.md`.
- The shared Manual Action Catalog, command palette, listing selection, navigation, and semantic helper work already exists as PRDs 006-011 and related issue files.
- The web command palette currently asks for label names with `window.prompt` in `commandPaletteActionParameters()` in `amiga_reversing/web/app.js`.
- Manual metadata actions can currently reopen/rebuild listing artifacts through `refreshAnalysisAfterManualMetadataAction()` and `refreshListingAfterApiEdit()`, including progress/loading overlays.
- Listing row selection exists and can derive row/element context for catalog requests.
- CDP coverage already verifies the command palette can offer `Rename label` for a selected label row and execute it through the catalog path.

## Clean Near-Term Work

1. Replace `window.prompt` parameter collection with an in-app command parameter editor.
   - Keep command execution catalog-backed.
   - Render parameter controls from `parameter_schema`.
   - For label rename, show an inline text field in the command palette or a compact overlay anchored to the selected row.
   - Preserve keyboard flow: `p`, choose command, edit value, Enter submits, Escape cancels.

2. Add first-open entrypoint selection.
   - Use the existing `source_binary.json` entrypoint and listing rows.
   - When no explicit URL/navigation anchor and no persisted UI location exists, request or locate the entrypoint row after initial listing load.
   - Select that row and center it in the virtual listing viewport.
   - Keep this as UI navigation state, not a Manual Action Log entry.

3. Make simple manual edits feel local and immediate.
   - Apply an optimistic projection for edits whose visible effect is known: label rename, comment edit, value representation, semantic hint, review-note state.
   - Patch affected visible rows and review counts in memory after the action-log append succeeds.
   - Refresh project badges and stale reproduction state quietly, without viewport overlays.
   - Defer full analysis/listing regeneration to actions that genuinely change code/data classification, entrypoints, or analysis policy.
   - If a background refresh is required, keep current selection, scroll anchor, and command/dialog state stable.

4. Add user review notes/bookmarks as first-class manual actions.
   - Add catalog actions for selected row/range: `add_review_note`, `edit_review_note`, `clear_review_note`.
   - Store durable notes in the Manual Action Log.
   - Project notes into generated manual review items with a user-note kind and open/resolved state.
   - Display them in the Review dialog and listing context menu/palette.

5. Expose note and selection actions consistently.
   - Same action ids through Review dialog, command palette, HTTP API, and CLI.
   - No web-only action eligibility.
   - Existing Review item actions stay catalog-driven.

## Better Version

- Extend the structured listing element context model from PRD 011 before adding more element-specific actions.
- Give the C listing artifact stable element ids and byte ranges for labels, operands, literals, comments, and data blocks.
- Use those ids in Manual Action Log payloads instead of relying on rendered text or row indexes.
- Add a project-local UI preference file for non-domain state: last selected row, last scroll anchor, key-binding overrides, render profile choice, and reproduction profile choice.

## Larger Architecture Notes

- Manual Action Log should remain the durable domain history.
- UI preferences should not be mixed into the Manual Action Log because they are local workflow state, not reverse-engineering facts.
- The command palette should become the single parameterized command surface; Review buttons and context menus should be thin renderings of the same catalog entries.
- Avoid one-off dialogs for each command. Parameter schema rendering is the reusable path.
- Manual edit UX should distinguish durable write completion from expensive analysis refresh. The user should see the edit land first; background recomputation should only invalidate visible state when necessary.

## Verification

- Web source tests for parameter schema rendering and absence of `window.prompt` in catalog action execution.
- CDP test for renaming a label through the in-app parameter editor.
- CDP test that a label rename updates the visible row without showing listing/reanalysis loading overlays.
- CDP test for first-open entrypoint row selection and centered viewport.
- Backend tests for note/bookmark Manual Action Log records and projection into review items.
- Route and CLI tests for note actions.

## Review Sign-Off

Reviewed against `TODO.md` and current code on 2026-05-16, including the seamless manual-edit UX entry. Scope is coherent as proposal work; no implementation is claimed here.
