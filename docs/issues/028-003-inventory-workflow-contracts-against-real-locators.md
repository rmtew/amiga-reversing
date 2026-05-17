Status: Done
Parent proposal: docs/proposals/007-web-ui-durability-and-state-correctness.md

## What to build

Create a workflow contract inventory using the real `ListingProjectionService` locator and hash contract. Each persistent workflow should name its durable state, projected state, visible state, and durability boundaries.

## Acceptance criteria

- [x] Rename label, row comment, data/type/representation, review resolution, command range action, navigation, last-open location, and profile preference workflows are inventoried.
- [x] Each workflow records fixture target, locator shape, view session shape, mutation result shape, durable expected state, projected expected state, visible expected state, and required boundaries.
- [x] Workflows without a clean durable source of truth are marked as blockers for mutation/browser work rather than covered with CDP-only tests.
- [x] The inventory uses the service-emitted locator contract and does not invent a parallel paper model.
- [x] The inventory identifies current tests that prove only DOM or route symptoms and maps them to the future API/CDP workflow contract.

## Shared locator contract

Use the service-emitted `ListingRowLocator` as the only row identity shape:

```text
target_id
projection_hash
row_key
section_index
start_offset
end_offset
kind
storage_address
runtime_address
```

For range workflows, store an ordered list of those locators plus the active
`projection_hash`. Do not substitute row text, DOM index, `row_id`, or
`stable_key` as an identity model. Existing browser internals may still map
`row_key` to `stable_key` until 028-009/028-010, but new workflow contracts must
name `row_key` and `locator`.

## Workflow Inventory

### Rename label

- Fixture target: small binary listing with a label row and a following
  instruction row; current coverage in `tests/test_disasm_server.py` label
  catalog/execute tests and CDP label rename tests.
- Locator shape: single label row locator with `kind=label`,
  `section_index`, zero-width label offset, `storage_address`, and `row_key`.
- View session shape: selected row locator, focused element selector
  `{element_kind: "label", symbol}`, and scroll anchor locator.
- Mutation result shape: one `rename_manual_label` or
  `create_manual_label` action plus affected label-row locator and refresh mode.
- Durable expected state: Manual Action Log entry for label rename/create.
- Projected expected state: listing row label/text reflects the manual label
  and the projection hash changes or an affected locator is returned.
- Visible expected state: selected row still points to the label locator; DOM
  label text shows the new name.
- Required boundaries: immediate, browser refresh, target reopen, server
  restart.
- Blocker: current catalog route still accepts row snapshots and legacy
  selector params. 028-004 must make command execution resolve this through
  `ListingProjectionService`.

### Row comment

- Fixture target: instruction row with no comment, then the same row after a
  comment action; current coverage in route comment action tests and CDP inline
  comment tests.
- Locator shape: single row locator for the commented row.
- View session shape: selected row locator and optional inline editor session
  bound to that locator.
- Mutation result shape: `create_manual_comment` action, affected row locator,
  local presentation effect, and authoritative refresh hint.
- Durable expected state: Manual Action Log comment entry.
- Projected expected state: listing row includes `comment_text` and navigation
  comments include the same locator.
- Visible expected state: comment text renders once on the row and selection is
  unchanged.
- Required boundaries: immediate, refresh, target reopen, server restart.
- Blocker: `app.js applyInlineSubmittedFallback` still patches visible state
  locally; 028-006 must remove that fallback in favor of command mutation
  results.

### Data type and value representation

- Fixture target: data row with bytes and a typed-access candidate; current
  coverage in representation and metadata edit route tests.
- Locator shape: data row locator plus element selector
  `{element_kind: "data_literal"}` or typed-access element selector.
- View session shape: selected element locator, parameter session for type or
  representation, and scroll anchor locator.
- Mutation result shape: target metadata/type mutation or
  `create_manual_representation`, affected row locator, and projection refresh
  hint.
- Durable expected state: representation belongs in Manual Action Log; target
  metadata/type edits currently use `target_ui_edits.json`.
- Projected expected state: data row renders with requested representation or
  typed metadata.
- Visible expected state: row bytes/value display changes without losing
  selected element.
- Required boundaries: immediate, refresh, target reopen, server restart.
- Blocker: type/metadata edits lack a clean durable source because
  `target_ui_edits.json` is retired. 028-006 must move them into the unified
  command/manual mutation path before durability tests treat them as valid.

### Review resolution

- Fixture target: listing with an analysis review item and review note; current
  coverage in cached review state tests, review note edit/clear tests, and CDP
  review refresh tests.
- Locator shape: review item locator is derived from item scope. Row/range
  review items use one row locator or ordered range locators; target-level items
  use no listing locator.
- View session shape: selected review item id plus resolved row/range locators
  when available.
- Mutation result shape: review action (`resolve_review_item`,
  `edit_review_note`, `clear_review_note`, or generated seed action), affected
  item id, affected locators, and refresh mode.
- Durable expected state: Manual Action Log review action or note action.
- Projected expected state: regenerated review items no longer include the
  resolved item, or note state updates on matching locators.
- Visible expected state: review overlay count/status updates and affected row
  annotations update.
- Required boundaries: immediate, refresh, target reopen, server restart.
- Blocker: review catalog execution still identifies items by review index in
  route context. 028-004 should use command ids plus item ids/locators.

### Command range action

- Fixture target: two adjacent data rows or mixed selected rows; current
  coverage in range seed/semantic action route tests.
- Locator shape: ordered list of row locators with shared `target_id` and
  expected `projection_hash`; stale locators recover only when each row has a
  unique recovery identity.
- View session shape: selection range `{anchor_locator, focus_locator,
  range_locators[]}`.
- Mutation result shape: command action list, affected range locators, pending
  reconciliation ranges, and refresh mode.
- Durable expected state: Manual Action Log action(s) for seeds, hints, labels,
  or comments.
- Projected expected state: regenerated facts or pending review state align with
  the same locator range.
- Visible expected state: selected range remains highlighted or is explicitly
  reconciled to returned affected locators.
- Required boundaries: immediate and refresh for pending actions; target reopen
  and server restart once command reconciliation is implemented.
- Blocker: current range route accepts row indexes and snapshots. 028-004 must
  reject ambiguous or stale ranges through service locator resolution.

### Navigation

- Fixture target: labels, API call, app-slot ref, runtime-address target, and
  duplicate storage offsets; current coverage in listing navigation route tests
  and CDP navigation tests.
- Locator shape: navigation entries should carry a row locator or enough
  address/source fields for `ListingProjectionService` to resolve one.
- View session shape: navigation session `{entry_id, locator, previous_locator,
  scroll_top}`.
- Mutation result shape: none for pure navigation; session state transition
  only.
- Durable expected state: none for transient navigation history.
- Projected expected state: target locator resolves to exactly one current row.
- Visible expected state: focused row is the resolved locator, not merely the
  first row with matching text/address.
- Required boundaries: immediate and browser refresh for current location;
  target reopen only when persisted as last-open location.
- Blocker: navigation entries and browser history still carry `stable_key` and
  row index. 028-009/028-010 must move them to locator state.

### Last-open location

- Fixture target: listing with entrypoint, selected non-entry row, and scrolled
  virtual window; current coverage in UI preference route tests and CDP restore
  tests.
- Locator shape: one row locator plus `scroll_top` and optional window start.
- View session shape: persisted preference
  `{locator, scroll_top, window_start, projection_hash}`.
- Mutation result shape: preference save result containing the sanitized locator
  and stale/valid status.
- Durable expected state: `ui_preferences.json` with locator-shaped
  `listing_location`.
- Projected expected state: on reopen, the locator resolves or reports stale
  recovery failure.
- Visible expected state: listing opens at the resolved row and preserves scroll
  when projection hash is still valid.
- Required boundaries: refresh, target reopen, server restart.
- Blocker: current `ui_preferences.json` stores `row_index`, `stable_key`,
  `row_code`, and address fields. 028-010 must replace that with locator-shaped
  preference state.

### Profile preference

- Fixture target: ready binary project with reproduction/source export profiles;
  current coverage in reproduction profile route tests and CDP source export
  palette tests.
- Locator shape: not row-bound. Profile commands may include current selection
  locator only for contextual UI return/focus.
- View session shape: selected profile id, source export assembler, and optional
  current locator for returning focus.
- Mutation result shape: profile preference result plus reproduction/job cache
  invalidation summary.
- Durable expected state: source export assembler view state belongs in
  `ui_preferences.json`; reproduction policy/profile currently writes through
  `target_ui_edits.json`.
- Projected expected state: reproduction/profile payload reports the chosen
  profile and invalidates stale reproduction jobs.
- Visible expected state: active profile badges/options reflect the chosen
  profile after reload.
- Required boundaries: immediate, refresh, target reopen, server restart.
- Blocker: reproduction policy/profile persistence is still backed by retired
  `target_ui_edits.json`. 028-006 must define the replacement durable state
  before browser durability assertions accept profile mutation as complete.

## Current Test Mapping

- Route symptom tests to convert into API workflow assertions:
  `test_route_manual_action_catalog_execute_appends_label_rename_override`,
  `test_route_manual_action_catalog_execute_appends_review_note_action`,
  `test_route_manual_action_catalog_execute_appends_representation_action`,
  `test_route_manual_action_catalog_execute_appends_valid_log_action`,
  `test_metadata_edit_route_invalidates_listing_and_reproduction`,
  `test_manual_action_route_appends_action_and_invalidates_analysis`,
  `test_route_reproduction_profile_list_show_set_without_manual_log`, and
  UI preference route tests.
- DOM symptom tests to convert into shared API/CDP semantic assertions:
  label rename, inline comment, review refresh, app-slot navigation, duplicate
  offset navigation, runtime-address navigation, source export palette, full
  enrichment scroll preservation, and selection restore tests in
  `tests/test_web_e2e_cdp.py`.
- Service-level tests already aligned with the contract:
  `tests/test_listing_projection.py` locator emit/resolve tests and cache/job
  lifecycle tests. Later workflow tests should reuse the same locator shape, not
  recreate row identity with DOM attributes.

## Follow-on Blockers

- 028-004: command/catalog execution must accept command contexts resolved by
  `ListingProjectionService`, including stale/ambiguous locator errors.
- 028-006: remove `target_ui_edits.json` as a durable state source for metadata
  and reproduction-profile workflows.
- 028-009/028-010: replace browser `stable_key`/row-index session and persisted
  preference state with locator state.
- 028-007/028-012: build shared semantic workflow assertions from this inventory
  so API and CDP tests verify durable, projected, session, and visible state.

## Blocked by

- docs/issues/028-001-extract-listing-row-locator-projection-tracer.md
- docs/issues/028-002-move-listing-cache-and-jobs-into-projection-service.md

## Required tests

- None required beyond doc review; this issue produces implementation inventory.
