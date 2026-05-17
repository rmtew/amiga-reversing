Status: Blocked
Parent proposal: docs/proposals/007-web-ui-durability-and-state-correctness.md

## What to build

Create a workflow contract inventory using the real `ListingProjectionService` locator and hash contract. Each persistent workflow should name its durable state, projected state, visible state, and durability boundaries.

## Acceptance criteria

- [ ] Rename label, row comment, data/type/representation, review resolution, command range action, navigation, last-open location, and profile preference workflows are inventoried.
- [ ] Each workflow records fixture target, locator shape, view session shape, mutation result shape, durable expected state, projected expected state, visible expected state, and required boundaries.
- [ ] Workflows without a clean durable source of truth are marked as blockers for mutation/browser work rather than covered with CDP-only tests.
- [ ] The inventory uses the service-emitted locator contract and does not invent a parallel paper model.
- [ ] The inventory identifies current tests that prove only DOM or route symptoms and maps them to the future API/CDP workflow contract.

## Blocked by

- docs/issues/028-001-extract-listing-row-locator-projection-tracer.md
- docs/issues/028-002-move-listing-cache-and-jobs-into-projection-service.md

## Required tests

- None required beyond doc review; this issue produces implementation inventory.
