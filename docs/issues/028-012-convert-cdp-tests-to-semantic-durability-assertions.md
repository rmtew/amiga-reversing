Status: Done
Parent proposal: docs/proposals/007-web-ui-durability-and-state-correctness.md

## What to build

Update critical CDP tests so they assert API state, projection state, browser debug state, and DOM state for persistent workflows instead of only first-glance DOM changes. Add the first LLM-operable verification smoke workflow using the same surfaces.

## Acceptance criteria

- [x] Critical mutation workflows assert durable state, projected listing state, browser session state, and visible DOM state.
- [x] CDP failure output identifies whether divergence is in API, projection, browser listing model, cache invalidation, or DOM rendering.
- [x] Tests that depend on old row index, stable key, row id, or row snapshot authority are rewritten or deleted.
- [x] Persistent workflows include refresh/reopen and durability boundary assertions where expected.
- [x] No broad sleep/retry helper is added to hide stale state races.
- [x] CDP tests reuse the shared workflow semantic assertion helpers from 028-007 instead of duplicating a browser-only state contract.
- [x] One smoke workflow verifies initial state, selects a target row by locator, discovers an available command, executes it, and asserts durable/projection/browser/DOM effects using only debug state, command catalog data, locators, and final visible checks.
- [x] The smoke workflow is documented or structured so an LLM browser agent can follow the same steps without row text, row index, or timing assumptions.
- [x] The smoke workflow names the server debug route and browser debug hook it uses, and fails if it falls back to row text, screenshots, arbitrary sleeps, or live internal object reads.

## Files likely touched

- `tests/test_web_e2e_cdp.py`
- CDP helper module
- shared workflow assertion helpers

## Blocked by

- docs/issues/028-008-add-durability-matrix-runner.md
- docs/issues/028-011-add-browser-debug-state-hook.md

## Required tests

- Focused CDP durability tests for critical persistent workflows.
- LLM-operable browser verification smoke test for one representative command workflow.

## Implementation

- Added a CDP smoke workflow for `comment.edit` that reads `window.__amigaDebugState()`, selects the row by locator, discovers `comment.edit` from `/commands`, executes it with locator context, reloads the target, and asserts durable/projected/browser/DOM state.
- The smoke uses `assert_manual_workflow_snapshot` so failures are attributed to durable state, projection, debug state, or DOM rendering instead of browser-only checks.
- The workflow records the server command route and browser debug hook it depends on and avoids row text, row index, screenshots, arbitrary sleeps, and live mutable state reads as oracles.
