Status: Done
Parent proposal: docs/proposals/007-web-ui-durability-and-state-correctness.md

## What to build

Remove the remaining browser-side `stableKey` / `stable_key` compatibility
aliases from `app.js` and make web listing state locator-only. This project is
the only consumer of the web UI, so no browser compatibility bridge is needed.

This follows the 028-013 audit finding that command execution, URL restore, and
persisted preferences already use `ListingRowLocator`, while `app.js` still
retains stable-key fallbacks for DOM attributes, navigation entries,
reproduction issue matching, and non-address viewport anchoring.

## Acceptance criteria

- [x] `app.js` uses `ListingRowLocator` / `row_key` as the only browser row
  identity model.
- [x] Rendered listing rows no longer emit or query `data-row-stable-key`.
- [x] `SelectionModel`, range selection, and rendered-selection repair do not
  store or compare `stableKey`, `focusStableKey`, `anchorStableKey`,
  `rangeStartStableKey`, or `rangeEndStableKey`.
- [x] Navigation entries carry locators or explicit locator-recovery fields,
  not `stableKey` / `stable_key`.
- [x] Viewport anchoring for non-address rows uses locator and recovery fields,
  not `stableKey` or row text as normal identity.
- [x] Reproduction issue matching uses locator/recovery identity where possible
  and keeps row-index/address matching only as diagnostics or source-report
  compatibility.
- [x] Command catalog requests and `/commands/execute` remain locator-only.
- [x] URL restore and `ui_preferences.json` remain locator-shaped and do not
  reintroduce stable-key fallback.
- [x] Tests that mention stable-key browser behavior are renamed or rewritten to
  assert locator/row-key behavior.
- [x] Final audit has no `stableKey` / `stable_key` references in `app.js`
  except comments in historical docs or explicitly justified non-browser input
  normalization outside the web-state contract.

## Implementation notes

Start with these known browser areas:

```text
data-row-stable-key rendering and DOM lookup
listingSelectionFromRow / SelectionModel snapshots
renderedRowForListingSelection
resolveRenderedListingRangeSelection
navigation entry capture and equality
viewport anchor capture/restore
reproduction issue row matching
corpus pending focus if it still passes stableKey through browser navigation
```

Do not replace `stableKey` with row index or row text. If a path cannot carry a
locator, extend the projection payload or state model so it can.

Manual Action Log payload builders may still emit legacy `stable_key` for
server-side matching until a separate server/manual-log cleanup removes that
shape. This issue is scoped to browser web-state aliases and browser-visible
contracts.

Implementation removed browser `stableKey` / `stable_key` aliases from
`app.js`, removed `data-row-stable-key`, and switched rendered row selectors to
`data-row-key`. Browser navigation entries now carry row locators generated
from projected rows. Selection and range repair now update stale selected
locators from the rendered row when recovery identity still points to the same
row, instead of keeping an obsolete locator or falling back to a stable-key
alias.

Unexpected finding: one CDP regression had been checking that a replaced
stable-key forced `precisionLost`. With locator-only state, the better behavior
is to repair the selection locator when section/offset recovery is still exact.
The test was updated to assert repaired `selection.locator.row_key` instead.

## Required tests

```text
uv run python -m pytest tests/test_web_app_source.py -q
M68K_RUN_BRAVE_CDP=1 uv run python -m pytest tests/test_web_e2e_cdp.py -q -k "selection or navigation or inline_parameter_sessions or llm_operable_command_smoke"
node --check amiga_reversing/web/app.js
cmd /c src/precommit.bat
```

## Blocked by

- docs/issues/028-013-historical-fixtures-and-stale-name-cleanup-audit.md
