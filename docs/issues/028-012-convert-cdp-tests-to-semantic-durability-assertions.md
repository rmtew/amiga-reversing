Status: Blocked
Parent proposal: docs/proposals/007-web-ui-durability-and-state-correctness.md

## What to build

Update critical CDP tests so they assert API state, projection state, browser debug state, and DOM state for persistent workflows instead of only first-glance DOM changes. Add the first LLM-operable verification smoke workflow using the same surfaces.

## Acceptance criteria

- [ ] Critical mutation workflows assert durable state, projected listing state, browser session state, and visible DOM state.
- [ ] CDP failure output identifies whether divergence is in API, projection, browser listing model, cache invalidation, or DOM rendering.
- [ ] Tests that depend on old row index, stable key, row id, or row snapshot authority are rewritten or deleted.
- [ ] Persistent workflows include refresh/reopen and durability boundary assertions where expected.
- [ ] No broad sleep/retry helper is added to hide stale state races.
- [ ] CDP tests reuse the shared workflow semantic assertion helpers from 028-007 instead of duplicating a browser-only state contract.
- [ ] One smoke workflow verifies initial state, selects a target row by locator, discovers an available command, executes it, and asserts durable/projection/browser/DOM effects using only debug state, command catalog data, locators, and final visible checks.
- [ ] The smoke workflow is documented or structured so an LLM browser agent can follow the same steps without row text, row index, or timing assumptions.
- [ ] The smoke workflow names the server debug route and browser debug hook it uses, and fails if it falls back to row text, screenshots, arbitrary sleeps, or live internal object reads.

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
