# Proposal 007: Web UI Durability And State Correctness

## Checkpoint Index

- [ ] Why This Exists
- [ ] Mental Model
- [ ] Current State Read
- [ ] Integration Findings
  - [ ] 1. `app.js` Owns Too Much Mutable State
  - [ ] 2. Listing Identity Is Mixed Across Row Index, Address, Stable Key, And Text
  - [ ] 3. Server Listing State Is Split Across Global Caches And Route Logic
  - [ ] 4. Manual Mutations Need One Durable Source Of Truth
  - [ ] 5. UI Preferences Persist View State Without A Shared State Contract
  - [ ] 6. CDP Tests Catch Regressions, But They Are Not A State Contract
  - [ ] 7. Browser-Visible Success Can Hide Wrong Durable State
  - [ ] 8. Refresh, Restart, And Cache Boundaries Are First-Class Requirements
  - [ ] 9. Manual Action Projection Needs Semantic Assertions
  - [ ] 10. Debuggability Is Part Of Correctness
- [ ] Tutorial: Durable Workflow Harness
  - [ ] Step 1: Define A Workflow State Contract
  - [ ] Step 2: Run The Same Workflow Across Durability Boundaries
  - [ ] Step 3: Assert Semantic State, Not Just DOM Shape
  - [ ] Step 4: Make Historical Bugs Permanent Fixtures
- [ ] Tutorial: API-First Workflow Tests
- [ ] Tutorial: UI State Model Checks
- [ ] Tutorial: Debug State Surface
- [ ] Tutorial: Scenario Fixtures And Golden Semantic Snapshots
- [ ] Larger Architecture Observations
  - [ ] 1. Server And Project State Should Be Authoritative
  - [ ] 2. UI State Should Be Reconstructable
  - [ ] 3. Browser Tests Should Be Deep, Not Numerous
  - [ ] 4. Persistence Is A Cross-Cutting Contract
  - [ ] 5. Refactor The State Pipeline, Do Not Preserve Fragile Seams
- [ ] Forward Implementation Model
  - [ ] Web State Contract
  - [ ] Listing Session Model
  - [ ] Server Projection Service
  - [ ] Manual Mutation Pipeline
  - [ ] Durability Matrix
  - [ ] API And CDP Workflow Harnesses
  - [ ] Semantic Snapshot Reporter
  - [ ] Debug State Surface
  - [ ] LLM Verification Surface
  - [ ] Invariant Checks
- [ ] Artifact Ownership
- [ ] Non-Goals
- [ ] Proposed Rewrite
  - [ ] Slice 1: Extract Listing Projection Service
  - [ ] Slice 2: Workflow Contract Inventory
  - [ ] Slice 3: Delete Target UI Edits And Unify Manual Mutation Pipeline
  - [ ] Slice 4: API Workflow Harness
  - [ ] Slice 5: Refactor Browser Listing State
  - [ ] Slice 6: Durability Matrix
  - [ ] Slice 7: Browser Debug State Hook
  - [ ] Slice 8: CDP Semantic Assertions
  - [ ] Slice 9: Historical Bug Fixtures
- [ ] Acceptance Criteria
- [ ] Deletion Checklist
- [ ] Rewrite Acceptance Tests
- [ ] Verification

## Why This Exists

The web UI is fragile in ways that ordinary end-to-end tests do not always
prove. A change can look correct during an interactive check, then fail after a
browser refresh, server restart, target reopen, or cache clear. The current CDP
suite is valuable, but it tends to encode specific regressions after they are
found.

The goal is to make UI correctness harder to fake. A workflow should not be
accepted because the first visible DOM update looked right. It should be
accepted because the same user intent survives the boundaries that real users
hit:

```text
action
  -> API result
  -> immediate UI state
  -> browser refresh
  -> target reopen
  -> server restart
  -> cache/local storage clear where relevant
  -> semantic state still correct
```

This proposal lists stronger options. The best path is not to delete CDP tests.
The best path is to make CDP one layer in a durability strategy.

Because this project is the only consumer of the web UI, compatibility is not a
constraint. If a workflow is hard to prove because the underlying model is
confused, the right fix is to refactor the model and update callers, not bolt a
test harness onto the confusion.

## Mental Model

Think of the web UI as a projection pipeline:

```text
user action
  -> API command
  -> durable project state
  -> Manual Action Log / project config / preferences
  -> effective metadata
  -> listing and review projection
  -> client view state
```

The important question is not "did the button update the screen?" It is:

```text
For every workflow that changes state:
  What durable fact should exist?
  Which projection should reflect it?
  Can the UI reconstruct the same visible state from durable facts?
  Does the state remain correct after refresh, restart, and reopen?
```

That turns UI testing into a state contract. DOM checks become one consumer of
the contract, not the contract itself.

## Current State Read

The repository already has useful pieces, but the current shape explains why
the UI remains fragile.

Client state is centralized in one large mutable object in
`amiga_reversing/web/app.js`. It mixes project identity, listing window state,
selection, virtual scrolling, navigation history, manual edit pending state,
command palette state, reproduction state, corpus browser state, and UI
preference restore/save state.

Server state is centralized in `amiga_reversing/disasm/server.py`. Route
dispatch, listing artifact cache management, presentation-only manual action
dirty flags, review item cache, async job state, UI preference persistence, and
manual action execution all live in the same module.

Listing projection today crosses several boundaries:

```text
C backend listing artifact
  -> server global listing artifact cache
  -> server annotation/projection helpers
  -> `/api/projects/<target>/listing`
  -> app.js virtual listing window
  -> DOM row rendering
  -> selection and command context rebuilt from row snapshots
```

Manual UI mutations currently cross two durable-state paths. The first path is
the Manual Action Log flow:

```text
manual action catalog
  -> `/manual-action-catalog/execute`
  -> append Manual Action Log entry
  -> classify refresh as analysis/project/local
  -> maybe mutate local listing rows optimistically
  -> maybe mark presentation dirty
  -> maybe clear listing artifact cache
  -> maybe refresh project/listing
```

The target route model should be command-oriented instead:

```text
GET /api/projects/{project_id}/commands
POST /api/projects/{project_id}/commands/execute
```

Mutation commands append Manual Action Log entries and return mutation results.
Non-mutating commands return command-specific navigation, clipboard, or
inspection results.

The server command catalog lists availability and effect classification.
Execution can stay client-side for commands that need no server state, such as
simple clipboard or local navigation commands. Commands that need durable state,
projection state, generated data, or validation execute through
`/commands/execute`.

Command availability must be derived from the current projection/context. The
client may cache availability only within this key:

```text
projection_hash
selected locator(s)
element_id when present
command context kind
```

Invalidate command availability on projection hash change, selection change,
element change, or context-kind change.

The second path is `target_ui_edits.json`, written through
`target_ui_edits.py` and `/target-edits`. That split is part of the problem, not
state to preserve. Existing targets can be reset and reimported, so the clean
target architecture has one semantic UI mutation source: the Manual Action Log.
`target_ui_edits.json` is deleted as durable state rather than migrated.
Existing `ui_preferences.json` files and target-local Manual Action Logs are
also reset instead of migrated, because they store old fallback-heavy locators
and action payloads.

The only state retained through the reset is intentional test fixture data that
still proves behavior we care about. Those fixtures must be rewritten to the new
Manual Action Log and `ListingRowLocator` shape. Incidental historical target
state is discarded.

Durable UI location is persisted through `ui_preferences.json`, with
`listing_location` containing a blend of row index, address, section offset,
stable key, row text, scroll top, and window start. That is pragmatic, but it is
not a single state contract.

The test suite has real coverage:

- `tests/test_web_e2e_cdp.py` drives browser workflows through CDP.
- `tests/cdp_brave.py` provides the browser harness.
- `tests/test_disasm_server.py` covers many server/API routes.
- `tests/test_web_app_source.py` checks client source contracts.
- CDP tests already cover listing selection, first-open behavior, command
  palette actions, manual seeds, comments, navigation, virtual listing fetches,
  and full-enrichment transitions.

Implementation evidence checked while preparing this rewrite:

```text
server.py owns _PROJECT_C_LISTING_ARTIFACT_CACHE,
_PROJECT_LISTING_CACHE_KEY, _PROJECT_LISTING_PRESENTATION_DIRTY,
_PROJECT_ANALYSIS_REVIEW_ITEMS_CACHE, listing jobs, route dispatch, and
manual-action cache invalidation

server.py exposes /manual-action-catalog, /manual-action-catalog/execute,
/manual-actions, /target-edits, /listing, /listing/navigation, /listing/open,
and ui-preferences routes in one route layer

manual-action-catalog context currently accepts row_index, row_indexes, and row
snapshots as authority before building Manual Action Log payloads

app.js stores listingRows, listingSelection, and virtualListing in one broad
state object, sends row_index plus row snapshots to the command palette, applies
local manual effects, and calls /target-edits for inline target edits

ui_preferences.py persists row_index, stable_key, row_code, address, section
offset, scroll_top, and window_start as one fallback-heavy location shape

target_ui_edits.py writes a second durable mutation source, effective_metadata
and reproduction consume its stamp, and profile_set_targets.py currently copies
target_ui_edits.json into generated profile-set targets

tests/test_disasm_server.py and tests/test_web_e2e_cdp.py frequently seed or
clear private _PROJECT_* server globals, while tests/test_web_app_source.py
currently asserts the presence of /target-edits and local manual effect paths
```

The gap is architectural, not only test volume. Tests are often forced to reach
into `state`, patch server globals, or assert late DOM symptoms because the
system does not expose one durable workflow state model.

The gap is not "no tests". The gap is that a test may prove the initial visible
interaction but not prove the durable state contract. That leaves bugs where:

```text
first render is correct
refresh is wrong
server restart is wrong
cache refresh is wrong
manual action log is correct but projection is stale
projection is correct but UI selection points at the wrong row
UI local state hides missing server state
```

## Integration Findings

### 1. `app.js` Owns Too Much Mutable State

The client has one broad `state` object. That object is convenient, but it
collapses several different lifetimes:

```text
durable project state
reconstructable listing session state
transient UI overlay state
in-flight request state
optimistic manual edit state
debug/statistics state
```

The proposal should formalize a refactor, not a test-only wrapper:

```text
state.project
state.projectData
state.listingRows
state.listingSelection
state.virtualListing
state.manualEdit
state.uiPreferences
state.navigation
```

should move toward explicit internal models inside `app.js`:

```text
ProjectSession
ListingSession
SelectionModel
ManualMutationState
NavigationSession
PreferenceSync
```

Each module should expose a small state contract and transition functions. DOM
handlers should call transitions. Tests should exercise transitions without a
browser where possible. This proposal does not require splitting `app.js` into
multiple files; keeping one file is preferred while the state contract is being
stabilized.

### 2. Listing Identity Is Mixed Across Row Index, Address, Stable Key, And Text

Current listing selection and restoration use several fallback identities:

```text
row_index
addr
section_index + source_offset
runtime_address
stable_key
row_code
scroll_top
window_start
```

This exists in `ui_preferences.json`, selection state, command palette row
snapshots, and virtual listing anchor logic. The mixture is a symptom: there is
no one canonical listing row locator.

The web-state contract should expose one row identity name: `row_key`.
`stable_key` and `row_id` are current implementation details to replace at the
route/client/preference/debug boundaries.

The cleaner model is a projection-service-owned `ListingRowLocator`. It should
wrap authoritative row identity emitted by the C backend plus projection context
owned by `ListingProjectionService`. The C backend should emit the stable row
identity fields, including `row_key`, `section_index`, `start_offset`,
`end_offset`, `addr`, `runtime_address`, and `kind`. The projection service
validates those facts, computes `projection_hash`, and exposes the locator
contract to callers.

```json
{
  "target_id": "bloodwych",
  "projection_hash": "hash-of-projected-row-inputs",
  "row_key": "s0:00001000:code",
  "section_index": 0,
  "start_offset": 4096,
  "end_offset": 4100,
  "kind": "code",
  "storage_address": 4096,
  "runtime_address": null
}
```

Rules:

```text
row_key is the preferred identity
row_key is opaque and callers must not parse it
target_id is required even when the route path already names the project
server routes must reject locators whose target_id does not match the route target
section_index + start_offset + end_offset + kind is the recovery identity
zero-width rows use start_offset == end_offset
end_offset may be null only when a row genuinely lacks offset semantics and
recovery is still unique
storage_address and runtime_address are navigation helpers
projection_hash detects stale locators across refresh/restart
row_index is a viewport position, not identity
row_code and row text are diagnostics, not recovery identity
```

`row_index` may remain as listing-window metadata for virtualization, rendering,
and debugging:

```text
window_start
relative_index
absolute_row_index
```

It must not be persisted as durable location, sent as a mutation subject, used
for recovery, or included in the command-availability cache key.

URL/deep-link state is internal web-state navigation, not a human-facing
permalink format. Use precise locator-compatible fields directly:

```text
row_key
projection_hash
section_index
start_offset
end_offset
kind
storage_address when present and useful
runtime_address when present and useful
```

`projection_hash` should be present by default. If it is stale, resolve by the
recovery fields and persist/replace the repaired locator where appropriate.

Do not add extra symbol/address mapping merely to make URLs readable. Also do
not use `row_index`, `row_code`/text, or legacy `stable_key`/`row_id` names in
new URL state.

Rows without offset semantics should be rare and non-semantic: generated header
comments, policy-driven blank/styling rows between sections or blocks, and
generated non-user-editable annotations. They may be rendered and navigated past,
but they should not accept mutation commands unless they have another explicit
durable domain identity.

Those structural rows may still have `row_key` for rendering and navigation
stability, but they must be explicit about mutability:

```text
kind: blank | header | annotation
mutable: false
recovery: best effort or section-level only
```

`mutable` belongs to the resolved row payload, not to `ListingRowLocator`.
The locator identifies and recovers the row. The current projected row states
whether it can be used as a mutation subject.

The command catalog should distinguish action effects:

```text
mutation
navigation
clipboard
inspection
```

`mutable: false` blocks mutation actions. It does not block non-mutating actions
such as copying text, navigating near a section, revealing a source location, or
inspecting a generated annotation.

If `row_key` cannot be expressed cleanly from current listing rows, refactor the
C listing payload and server projection to emit enough authoritative facts. Do
not add more fallbacks to `app.js`, and do not let `ListingProjectionService`
accumulate adapter debt around an awkward row payload.

Stale locator policy:

```text
navigation and view restore may repair a stale locator by recovery identity and
then persist the repaired locator

mutation commands must fail on stale projection_hash unless the projection
service can prove the locator still resolves uniquely to the same semantic row
```

Failed mutation commands may return repair information, but they still fail:

```text
ok: false
code: stale_locator
repair.possible: true
repair.locator: repaired current locator
```

The client may refresh, reselect, and retry. The server must not silently apply a
mutation after repair unless it has proven exact semantic equivalence.

For mutation auto-apply, "same semantic row" means:

```text
target_id matches
row_key matches, or recovery identity matches exactly
kind matches
durable domain identity matches when the row has one
the current projection resolves the locator uniquely
```

Text changes alone do not make a row different. Row split/merge,
reclassification, missing recovery identity, or ambiguity must fail the
mutation.

Examples of durable domain identity:

```text
manual review item id
symbol or label id
data seed id
instruction/data fact id when emitted
section or block id for structural actions
```

Durable ids should be emitted by the layer that owns the fact:

```text
C analysis/listing emits instruction, data, block, and generated fact ids
Python manual/review layers emit manual review, action, label, and seed ids
ListingProjectionService combines owned ids into the projected row payload
```

`projection_hash` is not merely the C listing artifact cache key. It identifies
the projected row model the browser sees. It must change when any input that can
change visible/projected rows changes:

```text
C listing artifact cache key
effective metadata hash
Manual Action Log count/head hash
manual projection overlay inputs
review annotation inputs when they affect listing rows, row actions, warnings,
selection validity, or row decorations
```

State that only feeds a separate panel should have its own explicit hash or
state contract instead of being folded into `projection_hash`.

Compute `projection_hash` lazily with memoization. The memoization key should be
the explicit projected-row inputs, such as artifact cache key, effective
metadata hash, Manual Action Log count/head hash, manual projection inputs, and
relevant review inputs. Do not eagerly recompute it in unrelated mutation/job
paths.

Keep `effective_metadata_hash` separate in payloads. It identifies durable
semantic metadata state; `projection_hash` identifies the projected listing row
model. Debug output and tests should be able to distinguish those layers.

### 3. Server Listing State Is Split Across Global Caches And Route Logic

`server.py` owns listing artifact caches:

```text
_PROJECT_C_LISTING_ARTIFACT_CACHE
_PROJECT_LISTING_CACHE_KEY
_PROJECT_LISTING_PRESENTATION_DIRTY
_PROJECT_ANALYSIS_REVIEW_ITEMS_CACHE
```

The same module also routes HTTP requests and decides whether a manual action
clears analysis, marks presentation dirty, or reuses an artifact.

This should become a `ListingProjectionService` instance, not a new set of
module globals:

```text
load/rebuild listing artifact
compute projection hash
apply manual projection overlays
return listing windows by locator
return navigation/review summaries
clear or preserve caches after a mutation
explain cache/projection state for debug/tests
```

Routes should call this service. Tests should assert the service contract
directly. CDP should consume the same state summaries through API/debug
payloads.

### 4. Manual Mutations Need One Durable Source Of Truth

Manual action execution currently returns an application description that can
produce local effects, pending ranges, reconciliation, and different refresh
modes. The client can also apply fallback local edits for comments. The server
can either clear the listing artifact cache or mark presentation dirty depending
on action kind. Separately, `/target-edits` and `target_ui_edits.py` provide
another durable edit source for UI-originated changes.

That flexibility is the source of many "looks fixed until refresh" failures.
The future model has one durable semantic mutation path:

```text
validate command context
append durable action
compute mutation result from durable state
return new projection hash
return affected row locators
client requests authoritative listing projection
client may animate affected rows, but does not own the fact
```

Optimistic local effects should be removed or narrowed to purely visual pending
indicators. Durable facts should always be reconstructed from the server
projection.

`target_ui_edits.json` is not an input to this new model. Reset/reimport drops
old target-local UI edits. Supported semantic UI edits become Manual Action Log
actions; unsupported edit kinds are either re-expressed in that model or
deleted.

### 5. UI Preferences Persist View State Without A Shared State Contract

`ui_preferences.py` persists `listing_location`, reproduction view choices, and
source export assembler choices. The listing location is useful, but it stores
a bundle of fallbacks without a named semantic contract.

Refactor target:

```text
ViewSessionState
  target_id
  listing_locator
  viewport_anchor
  selected_row_locator
  focused_row_locator
  selection_anchor_locator
  selection_focus_locator
  ordered_selected_locators
  navigation_stack
  profile/view preferences
```

The persisted view state should use the same listing locator type that the
server listing projection emits. On stale target id or stale projection hash,
the UI should degrade deterministically to entrypoint or first row.

Preference persistence should store the locator, including `projection_hash`,
plus recovery identity:

```text
row_key
projection_hash
section_index
start_offset
kind
viewport anchor
selection/focus locators when useful
```

On load:

```text
if projection_hash matches, restore exactly
if projection_hash is stale, repair by recovery identity
if repair is unique, persist the repaired locator
if repair fails, fall back to entrypoint or first row
```

Navigation history should use the same locator and repair policy. In-memory
back/forward entries store `ListingRowLocator` plus viewport anchor. Restore is
exact when the hash matches, repaired when recovery identity resolves uniquely,
and skipped or dropped when the row can no longer be recovered.

### 6. CDP Tests Catch Regressions, But They Are Not A State Contract

CDP tests are good at proving that a specific browser workflow works end to end.
They are weaker at proving the full state model because they usually assert what
the browser currently shows.

During the refactor, preserve CDP tests that prove user-visible behavior. Rewrite
tests that depend on old `row_index`/`stable_key`/row-snapshot contracts, and
delete tests whose only purpose is preserving obsolete internals.

Useful CDP assertion:

```text
Click rename label.
Observe the listing row text changed.
```

Stronger durability assertion:

```text
Click rename label.
Assert API/log state changed.
Refresh browser.
Assert listing row text is still changed.
Restart server.
Reopen target.
Assert effective metadata and listing state are still changed.
```

The second test proves the workflow. The first test proves only the first
projection.

### 7. Browser-Visible Success Can Hide Wrong Durable State

The UI can cache selected rows, listing text, project preferences, active target
state, and pending operation state. A cached value can make an interaction look
right while the durable project state is wrong or incomplete.

This is especially risky for:

```text
selected row and focused row
manual label/type/comment actions
render profile and reproduction profile choices
last-open target and last-open row
review item resolution state
command palette applicability
API calls that trigger reanalysis or listing refresh
```

The durable fact should be named before the test is written.

### 8. Refresh, Restart, And Cache Boundaries Are First-Class Requirements

For stateful UI work, these are not optional stress tests. They are part of the
definition of done.

Durability boundaries:

```text
immediate browser state
browser refresh
target close and reopen
server restart
new browser context
localStorage/sessionStorage clear
HTTP cache clear
project cache invalidation
analysis reload from disk
```

Not every workflow needs every boundary, but every persistent workflow needs a
declared boundary set.

### 9. Manual Action Projection Needs Semantic Assertions

Manual actions are not only UI events. They are domain facts. Tests should
assert the domain projection:

```text
manual action log entry exists
effective metadata contains the projected fact
listing row reflects effective metadata
source render reflects effective metadata when applicable
review item state reflects the projection
```

DOM text is useful, but it is a late-stage symptom. Tests should also assert the
earlier semantic layers.

### 10. Debuggability Is Part Of Correctness

When a browser test fails, it should be clear whether the bug is in:

```text
the browser component
the API command
durable storage
manual action projection
projection hash
review item regeneration
selection/focus state
stale cache invalidation
```

A test-only debug state surface can make CDP tests more precise and failures
less ambiguous.

## Tutorial: Durable Workflow Harness

The first useful piece is a harness that can run one workflow through several
durability boundaries. Start with a small number of high-value workflows rather
than broad browser coverage.

### Step 1: Define A Workflow State Contract

Each workflow should name:

```text
initial fixture
user action
durable expected state
projected expected state
visible expected state
durability boundaries
cleanup/reset behavior
```

Example contract:

```json
{
  "workflow": "rename_label",
  "initial_target": "fixture_target",
  "action": {
    "type": "manual_rename_label",
    "address": 4096,
    "name": "decode_intro"
  },
  "durable": {
    "manual_action_log_contains": "rename_label"
  },
  "projection": {
    "effective_label": "decode_intro"
  },
  "visible": {
    "listing_contains_label": "decode_intro"
  },
  "boundaries": ["immediate", "refresh", "reopen", "server_restart"]
}
```

The exact JSON is illustrative. The important rule is that the test knows what
state it is proving.

### Step 2: Run The Same Workflow Across Durability Boundaries

The harness should run the same assertions after each boundary:

```text
perform action
assert_state("immediate")
refresh browser
assert_state("after_refresh")
reopen target
assert_state("after_reopen")
restart server
assert_state("after_restart")
```

If a workflow is meant to be temporary client state only, declare that and prove
that it does not pollute durable state.

### Step 3: Assert Semantic State, Not Just DOM Shape

CDP should still inspect the DOM when the user experience matters, but the core
state assertions should be semantic:

```text
API: manual action log count/head hash
API: effective metadata for locator/range
API: listing row model for locator/range
API: review item state
DOM: visible row text and selected/focused row
```

This avoids brittle pixel or text-only tests while still proving the browser is
showing the right projection.

### Step 4: Make Historical Bugs Permanent Fixtures

Every bug that reaches the user should become one of:

```text
unit model test
API workflow test
durability matrix case
CDP semantic workflow test
scenario fixture snapshot
```

The fixture should reproduce the stale-state path, not merely the first visible
failure.

## Tutorial: API-First Workflow Tests

Most UI state bugs are also API/projection bugs. API tests are faster, easier to
debug, and can run across more combinations than CDP.

For each persistent workflow, test the backend path directly through the same
projection service used by routes:

```text
append manual action
reload project state
project effective metadata
ask ListingProjectionService for listing/window state
regenerate review items
assert expected state
```

API-first tests should cover:

```text
manual action log append-only behavior
effective metadata projection
listing model regeneration
review item regeneration
project config persistence
target reopen behavior
server restart behavior when practical
```

Then CDP tests only need to prove that the UI calls the right workflow and shows
the semantic result.

## Tutorial: UI State Model Checks

Client state should have a small explicit model. It should not be hidden inside
DOM state or incidental component variables.

State model examples:

```text
active target
selected row ids
focused row id
visible listing range
active filters
command palette context
pending operation
last navigation stack
cached projection hash
```

The implementation should expose enough deterministic model state for CDP and
source-level Python checks to exercise transitions without adding a JavaScript
test runner:

```text
open target
select row
shift-extend selection
apply filter
refresh listing model
navigate to reference
go back
receive changed listing rows
preserve or repair selection
```

Expected invariant:

```text
selected rows must exist in the current listing model
focused row must be either visible or recoverable by locator
commands must be derived from current semantic context
stale request sequences must not overwrite newer projection state
```

Do not add a new JavaScript test stack for this proposal. Keep
`tests/test_web_app_source.py` focused on source/contract checks, and prove
behavior through API tests, CDP semantic checks, and deterministic debug hooks.

## Tutorial: Debug State Surface

Add test-only or development-only debug state surfaces so tests can assert the
same facts a human would inspect manually without scraping DOM or private
globals.

Project-scoped server endpoint:

```text
GET /api/projects/{project_id}/debug/state
```

It should expose projection state, not DOM state:

```json
{
  "target_id": "bloodwych",
  "manual_action_log": {
    "count": 5,
    "head_hash": "..."
  },
  "listing": {
    "artifact_cache_key": "...",
    "projection_hash": "...",
    "effective_metadata_hash": "...",
    "visible_locators": [
      {
        "target_id": "bloodwych",
        "projection_hash": "...",
        "row_key": "...",
        "section_index": 0,
        "start_offset": 4096,
        "end_offset": 4100,
        "kind": "code",
        "storage_address": 4096,
        "runtime_address": null
      }
    ]
  }
}
```

Browser-side debug state should be a separate test hook, for example a CDP
callable `window.__amigaDebugState()`. It should return a copied JSON-safe
snapshot, not live internal objects:

```text
project id
projection hash
browser request sequence
visible locators
selected/focused locators
pending mutation id
```

CDP tests should compare the browser hook with the server endpoint.

The endpoint and browser hook are dev/test instrumentation. Automated tests may
depend on them, but user workflows must not. Their shape follows the internal
state contract and may change when that contract changes.

## Tutorial: Scenario Fixtures And Golden Semantic Snapshots

Use a few realistic target fixtures and save semantic snapshots for important
workflows.

Do not snapshot pixels. Do not snapshot the full DOM. Snapshot stable domain
models:

```text
manual action log summary
effective metadata summary
listing row model for selected ranges
review item summary
project config summary
navigation state summary
```

Good snapshot:

```json
{
  "locator": {
    "target_id": "bloodwych",
    "projection_hash": "...",
    "row_key": "...",
    "section_index": 0,
    "start_offset": 4096,
    "end_offset": 4100,
    "kind": "code",
    "storage_address": 4096,
    "runtime_address": null
  },
  "label": "decode_intro",
  "classification": "code",
  "effective_metadata_hash": "...",
  "manual_actions": ["rename_label"],
  "review_state": "resolved"
}
```

Bad snapshot:

```text
entire rendered HTML
pixel image of the listing
full generated analysis facts file
timestamped server payload
```

Snapshots should be stable enough that a diff points to a real behavior change.

## Larger Architecture Observations

### 1. Server And Project State Should Be Authoritative

The browser can cache for speed, but the source of truth should be durable
project state. After refresh or restart, the UI should reconstruct from server
and project data.

If the only correct state lives in browser memory, the workflow is fragile.

### 2. UI State Should Be Reconstructable

Selections, focus, open target, and visible location should be reconstructable
from stable identifiers:

```text
target id
ListingRowLocator
projection hash
project config preference
```

Avoid state that can only be recovered by array index after rows are regenerated.

### 3. Browser Tests Should Be Deep, Not Numerous

CDP tests are expensive and harder to debug. They should cover critical
end-to-end workflows and durability boundaries.

Prefer this shape:

```text
many unit/model/API tests
several semantic snapshot tests
few deep CDP durability tests
```

Avoid creating a large suite of shallow CDP tests that only repeat DOM checks.

### 4. Persistence Is A Cross-Cutting Contract

Every feature that writes durable state should declare:

```text
where it is stored
how it is projected
how it is invalidated
how it is reloaded
which tests prove those steps
```

This should be part of review for web UI changes.

### 5. Refactor The State Pipeline, Do Not Preserve Fragile Seams

The repository has one consumer: this project. That makes compatibility shims
the wrong default. If server state, generated listing models, client caches, or
manual action projection expose the wrong shape, replace the shape and update
callers in one slice.

Bad direction:

```text
keep old route payloads because tests already know them
add a CDP wait/retry helper to hide stale state races
add one more client cache flag to patch refresh behavior
special-case a workflow after reload instead of fixing reconstruction
```

Good direction:

```text
define the authoritative state model
make API payloads carry stable locators and projection hashes
make UI reconstruction derive from server/project facts
delete obsolete client-only state
update all callers and tests to the new model
```

Avoid churn, but do not preserve an awkward model merely because existing code
uses it. Broad refactors are worthwhile when they remove ambiguity and make
state reconstruction mechanically provable.

## Forward Implementation Model

### Web State Contract

Create a Python-owned and JavaScript-consumed contract for state that crosses
server, projection, and browser boundaries. This should be explicit enough that
`tests/test_disasm_server.py`, `tests/test_web_app_source.py`, and
`tests/test_web_e2e_cdp.py` can all assert the same facts.

```text
target_id
project_generation
projection_hash
manual_action_log_count
manual_action_log_head_hash
effective_metadata_hash
listing_locator
selection_state
viewport_anchor
profile_preferences
```

The server should emit this contract. The client should store it as session
state. Tests should inspect it directly.

Route payloads that expose this state should carry a simple internal contract
marker:

```json
{
  "ok": true,
  "contract": "web-state-v1",
  "data": {}
}
```

The marker is not a compatibility promise. It exists so tests and code reviews
can see when a route is expected to follow the shared web-state contract.

State-contract errors should be typed:

```json
{
  "ok": false,
  "contract": "web-state-v1",
  "error": {
    "code": "stale_locator",
    "message": "...",
    "repair": {
      "possible": true,
      "locator": {}
    }
  }
}
```

Initial error codes:

```text
stale_locator
missing_locator
ambiguous_locator
target_mismatch
non_mutable_row
```

Use the marker only on routes that participate in the web-state contract:

```text
project payload when it carries view/listing state
listing window
listing navigation/context
command catalog and manual mutation execution
UI preferences load/save
debug state
```

Do not add it to unrelated utility routes, static assets, or disk/corpus
browsing unless they become part of this state contract.

Event/SSE payloads that affect listing or projection state should use the same
contract marker:

```text
listing artifact started/ready/failed
projection changed
manual mutation applied if it becomes evented
```

Unrelated log/status events do not need the marker unless they become part of
the web-state contract.

### Listing Session Model

Refactor `state.listingRows`, `state.listingSelection`, and
`state.virtualListing` into a `ListingSession` model.

Target responsibilities:

```text
current listing window
current projection hash
request sequence and abort controller
visible viewport anchor
selected row locators
focused row locator
selection anchor/focus locators
ordered selected locators
scroll restore policy
stale response rejection
```

The model should expose pure transition functions for:

```text
apply listing window
move focus
extend selection
restore persisted location
replace projection hash
reject stale response
```

DOM code should render the model. It should not be the model.

### Server Projection Service

Extract listing projection and cache policy from `server.py` into a service
class, such as `ListingProjectionService` in `listing_projection.py`. The server
owns one app-level instance; tests can create isolated instances.

Target API:

```python
service = ListingProjectionService(project_root=..., tool_registry=...)
projection = service.project_listing_state(project_id)
window = service.window(project_id, locator, count)
row_context = service.row_context(project_id, locator)
range_context = service.range_context(project_id, locators)
debug = service.debug_state(project_id)
service.reset_project(project_id)
```

This service should own:

```text
listing artifact cache
listing artifact close/dispose lifecycle
cache key comparison
artifact cache key
listing artifact job start/reuse/cancel lifecycle inside the same service
artifact-ready event state
projected-row input hashing
manual projection overlay inputs
review item projection cache
listing window lookup by locator
row/range context resolution by locator
projection hash
```

Routes become thin adapters.

### Manual Mutation Pipeline

Make the Manual Action Log the only durable semantic UI mutation source.
`target_ui_edits.json` does not participate in the new pipeline; targets are
reset/reimported instead of migrated. The client should not need ad hoc
"presentation only", "project refresh", or "analysis refresh" code paths.
Projection updates are expressed as artifact-cache identity plus
`projection_hash`.

Command-palette context should send locators, not full row snapshots as
authority:

```text
row action: ListingRowLocator
range action: ListingRowLocator[]
element action: ListingRowLocator + element_id
```

`element_id` is not part of `ListingRowLocator`. The locator identifies the row.
The element selector identifies a sub-row token or rendered element after the
row has been resolved against the current projection.

The browser selection model should keep both interaction state and exact command
state:

```text
selection anchor locator
selection focus locator
ordered selected locators for the current projection
```

Anchor/focus drives keyboard and range-extension behavior. Ordered locators are
sent for range commands so the server can validate the exact intended rows.

Those locators resolve through `ListingProjectionService` before they reach the
command catalog. The projection service answers "which current projected row or
range did this locator mean?" and rejects stale or missing locators with a clear
error. Element actions then validate `element_id` against the resolved current
row.

The command catalog answers "which commands are available for this
row/range/element, and what effect do they have?" The manual action catalog is a
mutation-command helper: it builds durable Manual Action Log payloads only for
commands whose effect is `mutation`.

Target mutation result:

```json
{
  "mutation_id": "...",
  "durable": {
    "manual_action_id": "...",
    "manual_action_log_count": 5,
    "manual_action_log_head_hash": "..."
  },
  "projection": {
    "projection_hash": "...",
    "effective_metadata_hash": "...",
    "affected_locators": []
  },
  "client": {
    "refresh": "listing_window",
    "flash_locators": [],
    "refreshed_window": null
  }
}
```

Mutation responses should not return arbitrary row fragments as local effects.
They return durable/projection metadata and affected locators. If the request
includes the current viewport anchor/count, the response may include a complete
authoritative refreshed listing window. The browser can animate
`flash_locators`, but it should refresh visible rows from authoritative
projection data.

### Durability Matrix

Define standard boundaries:

```text
immediate
browser_refresh
target_reopen
server_restart
new_browser_context
browser_storage_clear
project_cache_clear
```

Each workflow opts into the boundaries it must survive.

### API And CDP Workflow Harnesses

Build one shared workflow assertion library. API tests call it after direct
route calls. CDP tests call it after browser actions.

The same assertion should be able to ask:

```text
what is the durable state?
what is the projected listing state?
what is the client session state?
what is visible in the DOM?
```

### Semantic Snapshot Reporter

Add stable report builders for selected target ranges:

```text
listing semantic rows
manual action summaries
effective metadata summaries
review item summaries
project config summaries
```

### Debug State Surface

Expose test-only debug state from the projection service and browser session
model:

```text
active target
artifact cache key
manual log count/head hash
effective metadata hash
projection hash
visible row locators
selected/focused locators
pending mutation id
browser request sequence
```

### LLM Verification Surface

The same state contract should make the UI operable by an LLM-driven browser
agent without relying on text scraping or timing guesses. This is not a separate
product API; it is a verification mode built from the command catalog, server
debug state, browser debug state, locators, and semantic assertion helpers.

The intended access surfaces are explicitly test/dev-only:

```text
GET /api/projects/{project_id}/debug-state
window.__amigaDebugState()
```

The exact names may change during implementation, but the slice must name one
server debug route and one browser debug hook. Browser verification must not
invent a separate DOM-scraping or screenshot-only path when these surfaces exist.

An LLM verification workflow should be able to:

```text
read server debug state
read browser debug state
assert projection/browser state match
choose a visible ListingRowLocator
ask the command catalog for available actions
execute a command by stable command id and typed parameters
assert durable state, projection state, browser state, and DOM state
repeat after refresh/reopen/restart boundaries
```

The first proving use should be a narrow smoke workflow that avoids bespoke DOM
knowledge except for the final visible assertion. It should demonstrate that an
agent can verify initial state, perform one representative command, and diagnose
which layer changed or diverged.

### Invariant Checks

Add cheap checks after every UI/API mutation in tests:

```text
selected row exists
focused row exists or is recoverable
manual action log is append-only
effective metadata recomputes deterministically
projection hash changes when durable/projection inputs change
stale responses do not overwrite fresh state
commands match current context
```

## Artifact Ownership

Ownership should follow the state pipeline.

Server projection layer owns:

```text
`amiga_reversing/disasm/listing_projection.py`
listing artifact cache and cache keys
projected-row input hashing
manual projection overlay inputs
listing row locators and windows
projection hash
review item projection cache
debug projection payload
```

Server route layer owns:

```text
`amiga_reversing/disasm/server.py`
HTTP parsing
route authorization/validation
calling projection/mutation services
serializing job state and event payloads
contract-version response envelope
```

Manual mutation layer owns:

```text
Manual Action Log append
manual action payload construction for mutation commands
effective metadata hash after mutation
affected listing locators
mutation result payload
```

Command catalog layer owns:

```text
available command listing for row/range/element context
action effect classification
delegation to manual action payload construction for mutation commands
non-mutating navigation/clipboard/inspection command metadata
```

Project preference layer owns:

```text
`amiga_reversing/disasm/ui_preferences.py`
view session persistence
listing locator persistence
profile/view preference persistence
stale preference detection
```

Client state layer owns:

```text
`amiga_reversing/web/app.js`
ListingSession model
SelectionModel model
NavigationSession model
PreferenceSync model
rendering those models into DOM
```

Tests own:

```text
workflow contracts
durability matrix execution
semantic snapshots
historical bug fixtures
CDP browser verification
```

State paths removed by the target architecture:

```text
server route code owning cache policy
browser DOM owning selection truth
manual action execution returning ad hoc refresh/local-effect paths
target_ui_edits.py and /target-edits as durable UI mutation sources
inline comment editing as a separate local patch path
row text used as normal identity
tests patching private server caches as the primary setup path
tests patching `_PROJECT_*` server globals instead of using
ListingProjectionService helpers
```

No browser component should become the only owner of durable user intent.

Existing responsibilities that remain valid:

```text
manual action append
project config persistence
target open/reopen semantics
effective metadata projection
listing model generation
review item regeneration
debug state payloads
```

## Non-Goals

Non-goals:

```text
replacing CDP tests
pixel-perfect screenshot testing as the primary proof
snapshotting entire HTML or full analysis facts
adding compatibility layers for old UI state
preserving or migrating target_ui_edits.json
preserving fragile client-only state semantics
preserving existing route/client/state APIs for compatibility
turning debug endpoints into stable user APIs
testing every branch through the browser
```

The goal is fewer false proofs, not more test volume for its own sake.
Compatibility is also a non-goal. Internal web UI APIs, state structures, cache
keys, and test helpers should be changed or deleted when a cleaner model makes
the workflow more provable.

## Proposed Rewrite

The executable issues under `docs/issues/028-*.md` are the implementation
breakdown for this proposal. Their dependency order is part of the design:

```text
028-001 service skeleton + locator tracer
028-002 move listing cache/jobs/debug state into ListingProjectionService
028-003 workflow contract inventory against real service locators
028-004 command routes with service-resolved locator contexts
028-005 reimport/profile-set cleanup for obsolete target-local UI state
028-006 delete target_ui_edits and unify mutation execution
028-007 shared API/CDP workflow semantic assertion helpers
028-008 durability matrix runner
028-009 app.js listing state models
028-010 locator-based preference, URL, and navigation persistence
028-011 browser debug state hook
028-012 CDP semantic durability assertions
028-013 historical fixtures and stale-name cleanup audit
```

Only `028-001` and `028-005` should be independently ready at the start.
Everything that depends on real locator resolution, command context validation,
or shared semantic assertions must stay blocked until its prerequisite module
exists. This keeps the implementation straightforward: each issue deepens the
state pipeline rather than adding a parallel test harness or legacy adapter.

### Slice 1: Extract Listing Projection Service

Move listing cache/projection ownership out of `server.py`. This slice also
delivers the real locator contract, because `ListingRowLocator` is only useful
when the service can emit, resolve, and validate it.

Changing the C backend listing payload is in scope for this slice when it keeps
the locator model clean. The service may normalize existing row facts, but it
must not paper over missing or ambiguous row identity with text, row indexes, or
client-side fallback conventions.

This slice removes old row identity names from web-facing payloads once callers
are updated. Do not expose both `stable_key`/`row_id` and `row_key` as a dual
contract.

Initial extraction:

```text
_PROJECT_C_LISTING_ARTIFACT_CACHE
_PROJECT_LISTING_CACHE_KEY
_PROJECT_LISTING_PRESENTATION_DIRTY
_PROJECT_ANALYSIS_REVIEW_ITEMS_CACHE
listing artifact job start/reuse/cancel state
artifact-ready event publishing state
_annotate_listing_payload
_project_listing_generation
listing window lookup by ListingRowLocator and navigation address
C backend listing payload fields needed for clean locator construction
authoritative C-emitted row_key
```

Target:

```text
server routes call a projection service
service emits ListingRowLocator values
service computes projection_hash
service resolves window(locator)
service resolves row_context(locator)
service resolves range_context(locator[])
service exposes server debug_state()
tests can instantiate isolated service instances
service reset/close hooks dispose cached artifacts
tests prove emit/resolve/stale-locator behavior without CDP
```

Do not split async listing jobs into a separate public service unless the
implementation proves a real need. Private helper classes are fine, but the
public ownership stays with `ListingProjectionService`.

The issue breakdown deliberately makes this two implementation steps:

```text
028-001 creates the service skeleton and routes the first locator-aware listing
tracer through it

028-002 moves the remaining cache, listing job, navigation, review annotation,
and debug-state ownership out of server.py
```

Implementation note from `028-001`: `ListingProjectionService` now owns the
first web listing-window normalization path. `/api/projects/{id}/listing` rows
return `row_key`, `locator`, `target_id`, `projection_hash`, recovery fields,
and address helpers, without top-level `row_id` or `stable_key`. The C backend
Python boundary attaches `row_key` from C-emitted row identity so projection does
not derive identity from row text or row index.

Remaining out of scope for `028-001`: command palette/catalog routes, internal
manual projection matching, navigation payloads, and browser state still contain
legacy row identity names until `028-004`, `028-009`, and `028-010` move those
contracts to locators. `028-002` still owns moving cache/job/debug state into
the service.

Implementation note from `028-002`: `ListingProjectionService` now owns the
listing artifact cache, cache keys, presentation-dirty state, cached review-item
projection, cache reset/close hooks, listing job start/reuse/cancel decisions,
and listing artifact-ready event payloads. `server.py` keeps the generic async
job transport and C-backend build adapter, but no longer owns the project
listing cache dictionaries. Browser tests seed cache state through service
helpers, and the frontend maps wire-level `row_key` back into its current
internal `stable_key` fields after fetch so the `/listing` API does not regain a
dual identity contract.

Remaining out of scope for `028-002`: command/catalog execution still passes
row snapshots and selector parameters rather than service-resolved locators.
Navigation payloads and persisted browser state still use legacy stable-key
field names internally until the locator command and browser-state slices replace
those contracts.

Do not implement `028-001` as a locator helper called from the old route globals.
That would preserve the shallow interface this proposal is trying to delete.

Exit condition:

```text
existing listing, navigation, and review API tests pass through the new service
with no compatibility wrapper around the old cache globals
```

### Slice 2: Workflow Contract Inventory

Inventory the workflows that change state and define the concrete locators and
state hashes that should survive refresh/restart. This runs after the
projection service starts emitting real locators, so the inventory uses the
service contract instead of inventing a parallel paper model.

Initial candidates:

```text
rename label
set data type
set value representation
add row/comment metadata
mark review item resolved
follow reference and go back
open target at last location
apply command palette action to selected rows
change render/reproduction profile
```

Output:

```text
workflow name
fixture target
listing locator shape
view session state shape
manual mutation result shape
expected durable state
expected projection
expected visible state
required durability boundaries
```

If the inventory shows that a workflow has no clean durable source of truth,
stop and refactor that workflow's state ownership before adding more browser
coverage.

### Slice 3: Delete Target UI Edits And Unify Manual Mutation Pipeline

Remove `target_ui_edits.py` and `/target-edits` as durable UI mutation paths.
Reset/reimport existing targets instead of migrating old `target_ui_edits.json`,
`ui_preferences.json`, or target-local Manual Action Log data, then replace ad
hoc local-effect/refresh-mode handling with one mutation result.

Initial code to fold:

```text
manual-action-catalog execute route
manual-actions route
target-edits route
target_ui_edits.py
app.js applyManualActionApplication
app.js applyInlineSubmittedFallback
inline comment submit handling
presentation-dirty cache behavior, replacing it with artifact cache key plus
projection hash
```

Target command routes:

```text
GET /api/projects/{project_id}/commands
POST /api/projects/{project_id}/commands/execute
```

UI mutations should use `/commands/execute`. A lower-level Manual Action Log
append API or service may remain for tests/admin mechanics, but browser
workflows should not bypass locator/context validation and command availability.

This is a hard deletion slice, not a compatibility bridge:

```text
inventory target_ui_edits call sites
replace supported flows with Manual Action Log commands
remove /target-edits route
delete target_ui_edits.py
delete or rewrite tests for old target UI edit behavior
update existing reimport/import paths to delete obsolete target-local state
```

The existing reimport command-line/import code should be tightened so reimport
means clean target-local UI state, not partial refresh. In particular,
profile-set target copying must stop copying `target_ui_edits.json`.

Implementation note from `028-005`: disk import/reimport now deletes
`target_ui_edits.json`, `ui_preferences.json`, and `manual_actions.jsonl` from
rewritten target directories. Profile-set target copying keeps only source/import
facts and no longer copies `target_ui_edits.json`. The tracked target-file
inventory classified `target_seeded_metadata.json` and `target_corrections.json`
as source/import facts to preserve. No extra obsolete generated local-state file
was found in tracked target fixtures.

Remaining out of scope for `028-005`: production readers and writers of
`target_ui_edits.py` still exist until `028-006` replaces those workflows with
authoritative Manual Action Log mutation results. `028-005` prevents stale
target-local UI/manual state from surviving reset/reimport boundaries; it does
not delete the old mutation path.

Reimport cleanup should delete:

```text
target_ui_edits.json
ui_preferences.json
target-local Manual Action Log
obsolete generated local state identified during implementation
```

Do not blindly delete source/import facts. Slice 3 should inventory target-local
files and classify them:

```text
keep source/import facts such as target_seeded_metadata.json unless they encode
obsolete UI/manual state

classify target_corrections.json during inventory before keep/delete

delete UI/manual state

rewrite intentional fixtures only
```

Target:

```text
append durable action
compute projection hash
return affected listing locators
refresh authoritative visible window
flash affected locators only as presentation
delete target_ui_edits.json as a durable state source
route inline comment edits through the same mutation result path
```

Exit condition:

```text
manual label/comment/representation/review workflows survive immediate,
refresh, target reopen, and server restart checks
no production workflow reads target_ui_edits.json
```

### Slice 4: API Workflow Harness

Create shared workflow helpers that run a workflow and assert semantic state
after project reload. API tests call them directly after route/service actions.
CDP tests later call the same assertions after browser actions and browser debug
state collection.

Exit condition:

```text
manual-action and preference workflows prove action -> reload -> projection
without a browser
CDP assertions can reuse the same semantic checks without inventing a parallel
browser-only state contract
```

### Slice 5: Refactor Browser Listing State

Split `state.listingRows`, `state.listingSelection`, and
`state.virtualListing` into explicit client models inside `app.js`. Keep one
client file for this refactor, but make the ownership clear.

Target:

```text
ListingSession applies listing windows by projection hash
SelectionModel stores row locators, not DOM rows or row text
PreferenceSync persists the same locator shape
NavigationSession uses locators for back/forward entries
```

Exit condition:

```text
selection restore, first-open entrypoint selection, virtual scrolling, and
navigation tests pass without depending on row text as normal identity
```

### Slice 6: Durability Matrix

Add a matrix runner that can apply refresh/reopen/restart boundaries.

Exit condition:

```text
manual-action workflow passes immediate, refresh, target reopen, and server
restart assertions
```

The matrix should expose state-model problems, not mask them. Do not add broad
retry loops, sleep-based stabilization, or client cache resets as a substitute
for deterministic state reconstruction.

### Slice 7: Browser Debug State Hook

Add the test-only browser debug hook that exposes active client state without
scraping the DOM. The server debug endpoint was delivered with
`ListingProjectionService`; this slice adds the matching JSON-safe browser
snapshot after the client models exist.

Exit condition:

```text
CDP tests can compare server debug state with browser project id, selected row,
projection hash, pending mutation id, and browser request sequence
```

If debug state needs to expose too many special cases, that is a signal to
simplify the underlying state model.

### Slice 8: CDP Semantic Assertions

Update critical CDP tests to assert semantic state through API/debug helpers in
addition to DOM state. Include the first LLM-operable verification smoke
workflow: it should drive one representative workflow through debug state,
locators, command availability, command execution, and shared semantic
assertions before doing a final DOM assertion.

Exit condition:

```text
CDP test failure says which layer diverged: API, projection, listing, or DOM
one smoke workflow can be followed by an LLM browser agent without row text,
row index, or timing assumptions
```

### Slice 9: Historical Bug Fixtures

Convert known fragile UI bugs into fixtures as the relevant subsystem is
touched. The final slice is an audit, not the first time fixtures are added.

Exit condition:

```text
every reported refresh/restart/cache bug gets a named regression fixture
fixtures are attached to the subsystem that owns the state contract they prove
CONTEXT.md and relevant docs use new terms and no longer describe retired state paths
```

Also update project terminology docs after implementation changes land:

```text
Immediate Manual Projection -> authoritative mutation result / projection refresh
Manual Action Catalog -> Command Catalog + Manual Action payload builder
Listing Selection -> locator-based selection
```

## Acceptance Criteria

Required acceptance points:

```text
state-changing UI workflows name their durable source of truth

state ownership is refactored when current APIs cannot express a clean durable
contract

listing rows expose a stable locator and UI selection uses that locator as
identity

row index is treated as viewport position, not durable identity

listing projection/cache policy is owned by a service instance, not route logic

browser listing state is split into explicit session/selection/preference
models or equivalent transition modules

manual mutations return one authoritative mutation result with durable action,
projection hash, and affected locators

manual mutation workflows are tested through action, projection, refresh, reopen,
and restart where persistence is expected

API workflow tests prove backend state and projection without a browser

CDP tests assert semantic state, not only visible DOM text

browser-local state is never the only source of durable user intent

selected/focused row state is validated after listing refreshes

stale async responses cannot overwrite newer listing/project state without
test coverage catching it

server restart and cache clear behavior are explicit in test contracts

historical UI bugs become durable regression fixtures

obsolete client/server state paths are deleted rather than compatibility-wrapped

debug output can identify whether failure is in API state, projection, listing
model, cache invalidation, or DOM rendering
```

## Deletion Checklist

Delete or replace these patterns when found:

```text
tests that prove only first-glance DOM changes for persistent workflows

client-only durable state

row selection stored only by visible array index

row text used as normal selection or preference identity when a stable locator
can be emitted

manual mutation tests that do not inspect projected effective metadata

CDP workflows with no refresh/reopen assertion for persistent changes

silent cache reuse after project state changes

server route code directly owning listing artifact cache invalidation

manual action response paths that require the browser to choose between several
ad hoc refresh modes

target_ui_edits.json or target_ui_edits.py used as durable UI mutation state

optimistic local listing mutations that are not immediately reconciled with an
authoritative projection

debugging helpers that scrape DOM when an API semantic assertion is available

compatibility wrappers around obsolete internal UI state

duplicate old/new route payload shapes kept for transition after all callers can
be updated

new tests that patch private `_PROJECT_*` server globals

existing `_PROJECT_*` global patching in tests when the touched behavior has a
ListingProjectionService helper

retry/sleep helpers used to paper over state races

golden snapshots of unstable full HTML, timestamps, or full analysis facts
```

## Rewrite Acceptance Tests

Minimum tests:

```text
listing projection service contract
  Given a cached artifact and manual state, return a listing window with stable
  row locators, projection hash, review annotations, and debug state.

listing locator durability
  Persist a listing locator through ui_preferences.json, reload preferences,
  reopen the target, and recover the intended row without row text fallback.

browser ListingSession model
  Apply stale and fresh listing windows out of order and assert only the fresh
  request/projection state reaches selected/focused state.

manual mutation result contract
  Execute a command action and assert the response contains durable action id,
  manual log count/head hash, projection hash, and affected locators.

API mutation durability
  Append a manual action, reload project state, recompute effective metadata,
  and assert the listing model reflects it.

CDP mutation durability
  Perform the same action in the browser, assert immediate DOM and semantic
  state, refresh, reopen target, restart server, and assert again.

LLM-operable browser verification smoke
  Read server debug state and browser debug state, select a row by locator,
  discover and execute one command by machine-readable command metadata, and
  assert durable/projection/browser state before the final visible check.

selected row refresh behavior
  Select a row, trigger listing reprojection, and assert selected/focused row
  is still valid or intentionally repaired.

stale response rejection
  Deliver an older listing/API response after a newer browser request sequence
  and assert the UI keeps the newer state.

debug state coverage
  Assert the debug state payload reports active target, manual action log count/head hash,
  projection hash, and selected row.

historical bug fixture
  Reproduce one previously reported refresh/restart/cache bug and keep it as a
  named regression.
```

## Verification

Required checks for implementation work under this proposal:

```text
focused API workflow tests
focused UI state model/source checks
focused CDP durability tests for changed workflows
LLM-operable browser verification smoke test for the representative workflow
tests/test_disasm_server.py for route/projection changes
tests/test_web_app_source.py for client contract/source changes
tests/test_web_e2e_cdp.py when web UI behavior changes
src/precommit.bat before commit
final stale-name/deletion audit
```

Final audit searches should include:

```text
target_ui_edits
stable_key
row_id
row_code as identity
manual-action-catalog
presentation dirty
_PROJECT_LISTING_*
row_index in mutation/preference context
```

Remaining references in production code must be removed or explicitly justified
as current implementation detail scheduled in the same slice. Historical docs
and tests may mention retired names only when describing removed behavior.
Generated listing JSON consumed by the web UI must use `row_key` and
`ListingRowLocator` fields, not `stable_key` or `row_id`. Private C internals
may use local names if they do not leak into the web-facing payload.

The final audit should distinguish allowed viewport/debug uses of `row_index`
from forbidden identity uses. `row_index` may remain a window position for
virtualization, rendering, corpus snippets, and diagnostics. It must not be the
subject identity for mutation commands, preferences, URL/deep-link state, or
Manual Action Log payload construction.

Useful report artifacts:

```text
workflow durability matrix summary
semantic snapshot diff
debug state payload on failure
manual action log count/head hash before and after action
projection hash and selected row summary
```

Review rule:

```text
Do not accept a persistent UI workflow because the first visible browser state
looks right. Accept it when durable state and reconstructed state are proven.
```
