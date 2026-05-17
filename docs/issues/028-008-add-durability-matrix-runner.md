Status: Blocked
Parent proposal: docs/proposals/007-web-ui-durability-and-state-correctness.md

## What to build

Add a durability matrix runner that applies standard boundaries to API workflow assertions so persistent state is proven after refresh, reopen, restart, and cache changes where relevant.

## Acceptance criteria

- [ ] Matrix boundaries include immediate, browser refresh equivalent, target reopen, server restart where practical, new context/storage clear where relevant, and project cache clear.
- [ ] Each workflow declares which boundaries it must survive and which are intentionally transient.
- [ ] At least one representative manual mutation workflow passes immediate, refresh, target reopen, and restart/cache assertions.
- [ ] Matrix implementation avoids sleep/retry/cache-reset workarounds that hide state reconstruction bugs.
- [ ] Matrix failure output reports the boundary that failed and the semantic layer that diverged.

## Files likely touched

- shared workflow helper module
- API workflow tests

## Blocked by

- docs/issues/028-007-add-api-workflow-harness.md

## Required tests

- At least one manual mutation durability matrix test.
