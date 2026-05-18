# Proposal 013: LLM Web UI Verification Loop

Status: Draft.

This proposal defines the clean path for using the Proposal 007 and Proposal
009 web/debug/profiling surfaces to build and verify web UI changes without
blind patch-and-hope iteration.

Proposal 010 uses the same surfaces for the agentic reversing loop. This
proposal covers the other intended outcome: an LLM-assisted web UI development
loop where Codex can change the UI, exercise it like a user, prove durable
state, inspect performance spans, and report exactly which layer is correct or
wrong.

The target is not more screenshots. The target is a repeatable loop:

```text
name the user intent
  -> drive the real UI/API workflow
  -> assert durable state
  -> assert projection state
  -> assert browser state
  -> assert DOM as the final visible symptom
  -> cross refresh/reopen/restart boundaries when persistence matters
  -> inspect workflow_profile spans when UX feels slow
  -> record a concise report
```

## Checkpoint Index

- [ ] Clean Target Model
- [ ] Why This Exists
- [ ] Current Inputs
- [ ] UI Scenario Contract
- [ ] Tutorial: Verify A Simple Manual Edit
- [ ] Tutorial: Turn A User-Visible Bug Into A Fixture
- [ ] Tutorial: Check Durability Boundaries
- [ ] Tutorial: Diagnose Slow Or Blocking UX
- [ ] Tutorial: Verify In-Situ UI Updates
- [ ] Tutorial: Use Visual Checks As The Last Layer
- [ ] Tutorial: Write The LLM UI Verification Report
- [ ] Larger Architecture Observations
- [ ] Implementation Slices
- [ ] Artifact Ownership
- [ ] Non-Goals
- [ ] Acceptance Criteria
- [ ] Verification Plan
- [ ] Deletion Checklist

## Clean Target Model

The best clean version is a UI scenario harness:

```text
UI change or regression report
  -> scenario contract
  -> API workflow helper
  -> browser/CDP workflow helper
  -> semantic snapshot
  -> durability matrix
  -> workflow_profile summary
  -> human-readable report
```

Every state-changing UI workflow should be provable through one shared model:

```text
user intent
  has a named command or route
  has typed parameters
  has an authoritative mutation result
  has durable state stamps
  has projection stamps
  has browser debug state
  has final DOM evidence
  has declared durability boundaries
  has workflow_profile spans when latency matters
```

The LLM should not invent a separate UI automation interface. It should use the
same project interfaces as tests and users:

```text
GET /api/projects/{target}/listing
GET /api/projects/{target}/commands
POST /api/projects/{target}/commands/execute
ListingProjectionService.debug_state()
window.__amigaDebugState()
workflow_profile payloads
durability matrix helpers
CDP browser helpers
```

The browser DOM remains important, but it is the final visible layer, not the
source of truth:

```text
Manual Action Log
  -> effective metadata
  -> listing projection
  -> browser state
  -> DOM row
```

The clean report should make failures local:

```text
failed: projected listing
reason: post_comment was stored as pre_comment
durable state: Manual Action Log ok
effective metadata: wrong comment slot
browser state: faithfully rendered wrong projection
DOM: symptom only
```

## Why This Exists

The web UI has had the failure mode where an LLM changes code, the first visible
interaction appears to work, and the user later finds that the workflow is
broken:

```text
label edit appears to work
  -> refresh target
  -> nearby loc_/abs_ labels changed together

post-comment appears to work
  -> reload listing
  -> comment is now a pre-comment or appears on neighboring rows

manual edit appears to work
  -> UI flashes warning/yellow state-loss message
  -> row still updates, but user confidence is damaged

simple edit appears to work
  -> full progress dialog blocks browsing
  -> unnecessary analysis runs
```

Those are not only UI bugs. They are state-contract bugs. The right harness must
prove:

```text
which durable fact changed
which exact row/element it belongs to
which projection consumed it
which browser state rendered it
which expensive work did or did not run
```

Proposal 007 created the correctness pieces: stable locators, projection hash,
debug state, command routes, semantic assertions, and durability boundaries.
Proposal 009 created the performance pieces: workflow spans and browser/backend
correlation. This proposal turns those pieces into the default development loop
for web UI changes.

## Current Inputs

Useful existing concepts and artifacts:

```text
ListingRowLocator
projection_hash
Manual Action Log
Authoritative Mutation Result
ListingProjectionService.debug_state()
window.__amigaDebugState()
workflow_profile / WorkflowSpan
tests/workflow_harness.py
tests/test_web_e2e_cdp.py
manual command execution route
durability matrix runner
```

Relevant proposal history:

```text
001 manual review UI workflow UX goals
007 durable state and LLM verification surface
009 workflow profiling and browser/backend correlation
010 agentic reversing loop using the same interfaces
```

The missing artifact is a first-class UI scenario report and playbook that says
how an LLM should use those surfaces while developing the web UI.

## UI Scenario Contract

Add a small scenario contract for user-visible web workflows.

Suggested shape:

```json
{
  "schema_version": 1,
  "scenario_id": "manual-comment-edit-local-row",
  "target_id": "bloodwych",
  "intent": "Edit the post-comment on one listing row.",
  "entry": {
    "kind": "visible_listing_row",
    "locator": {
      "target_id": "bloodwych",
      "row_key": "source:00004c60",
      "projection_hash": "..."
    },
    "element_id": "comment:post"
  },
  "command": {
    "id": "comment.edit",
    "params": {
      "slot": "post",
      "text": "loads map pointer"
    }
  },
  "expected": {
    "manual_action_delta": 1,
    "semantic_fact": {
      "kind": "comment",
      "slot": "post",
      "text": "loads map pointer"
    },
    "affected_locator_count": 1,
    "forbidden_effects": [
      "neighbor_row_comment_change",
      "pre_comment_change",
      "unrelated_label_alias_change"
    ]
  },
  "durability": [
    "immediate",
    "browser_refresh",
    "target_reopen",
    "project_cache_clear"
  ],
  "ux": {
    "must_not_show_modal_progress": true,
    "expected_visible_feedback": "success_highlight",
    "may_continue_browsing": true
  }
}
```

The contract is intentionally user-intent shaped. Tests can derive API calls,
CDP actions, semantic assertions, and reporting from it.

## Tutorial: Verify A Simple Manual Edit

Start with the representative workflow: edit a row comment through the normal
command route.

Textual flow:

```text
open target
  -> read server debug state
  -> read browser debug state
  -> select a visible row by ListingRowLocator
  -> ask command catalog for comment.edit
  -> execute comment.edit
  -> assert mutation result
  -> assert Manual Action Log count/head hash changed
  -> assert effective metadata has one post-comment
  -> assert listing projection has one affected row
  -> assert browser debug state matches projection hash
  -> assert DOM row displays the post-comment
```

Example Python helper shape:

```python
def assert_manual_comment_edit_scenario(harness, target_id, locator, text):
    before = harness.snapshot(target_id)

    commands = harness.commands(target_id, context={"locator": locator})
    assert commands.has("comment.edit")

    result = harness.execute(
        target_id,
        "comment.edit",
        context={"locator": locator, "element_id": "comment:post"},
        params={"slot": "post", "text": text},
    )

    after = harness.snapshot(target_id)

    assert result.ok
    assert after.manual_action_log_count == before.manual_action_log_count + 1
    assert after.effective_metadata.has_post_comment(locator, text)
    assert after.projected_listing.row(locator).post_comment == text
    assert after.projected_listing.only_locator_changed(locator)
```

Example browser/CDP helper shape:

```python
def assert_browser_matches_projection(cdp, server_snapshot, locator):
    browser = cdp.evaluate("window.__amigaDebugState()")

    assert browser["project"]["target_id"] == server_snapshot.target_id
    assert browser["listing"]["projection_hash"] == server_snapshot.projection_hash
    assert locator in browser["listing"]["visible_locators"]
    assert browser["mutation"]["pending_mutation_id"] is None
```

The key rule:

```text
DOM success without semantic success is failure.
Semantic success without final visible DOM success is also failure.
```

## Tutorial: Turn A User-Visible Bug Into A Fixture

When the user reports a UI bug, the first durable output should be a scenario
fixture.

Example bug:

```text
Editing a local label at one address also changes the generated abs_ label for
the same address after target refresh.
```

Fixture shape:

```json
{
  "scenario_id": "label-edit-does-not-alias-local-and-absolute-labels",
  "intent": "Rename one local label without renaming distinct generated labels.",
  "command": {
    "id": "label.rename",
    "params": {"name": "load_level_header"}
  },
  "expected": {
    "semantic_fact": {
      "kind": "label",
      "scope": "selected_locator_only",
      "name": "load_level_header"
    },
    "forbidden_effects": [
      "pre_org_loc_label_changed",
      "post_org_abs_label_changed",
      "same_address_other_section_label_changed"
    ]
  },
  "durability": [
    "immediate",
    "browser_refresh",
    "target_reopen"
  ]
}
```

The test should reproduce the stale or aliased state path, not only click the
control that originally looked wrong.

Useful regression classes:

```text
wrong row identity:
  row index or address used where ListingRowLocator is required

wrong element identity:
  post-comment applied to pre-comment slot

wrong scope:
  one local edit changes sibling generated labels

wrong persistence:
  immediate browser state differs from reload state

wrong cache invalidation:
  stale projection overwrites fresh mutation result

wrong UX:
  cheap mutation shows modal progress or state-loss warning

wrong work:
  simple metadata edit triggers full analysis or listing regeneration
```

## Tutorial: Check Durability Boundaries

Persistent workflows must declare boundaries. The harness should apply only the
boundaries relevant to the scenario, but missing declarations are a defect.

Boundary flow:

```text
apply command
  -> immediate snapshot
  -> browser refresh equivalent
  -> target reopen
  -> project cache clear
  -> server restart when supported
  -> new browser context/storage clear when relevant
```

Example helper shape:

```python
def run_durability_matrix(scenario, harness):
    baseline = harness.run_scenario(scenario)

    for boundary in scenario.durability:
        snapshot = harness.apply_boundary(boundary, scenario.target_id)
        assert_semantic_result(scenario, snapshot)
        assert_projection_result(scenario, snapshot)
        assert_forbidden_effects_absent(scenario, snapshot)

    return baseline.report()
```

Failure messages must name the layer:

```text
durability boundary target_reopen: effective_metadata: missing post_comment
durability boundary browser_refresh: browser_state: stale projection_hash
durability boundary project_cache_clear: listing_projection: neighbor row changed
```

Do not fix durability failures with sleeps, broad retries, or client cache
clears. Fix reconstruction from durable state.

## Tutorial: Diagnose Slow Or Blocking UX

Slow manual edits need profile evidence before refactoring.

Expected trace:

```text
browser interaction
  -> API request id
  -> command_context
  -> locator_resolution
  -> command_catalog
  -> manual_action_append
  -> manual_action_application
  -> listing_cache_invalidation
  -> response_build
  -> browser fetch/render sample
```

Example report snippet:

```json
{
  "scenario_id": "manual-comment-edit-local-row",
  "ux_result": "too_slow",
  "request_id": "req-42",
  "workflow_profile": {
    "workflow_id": "manual_command_execution",
    "spans": [
      {"name": "locator_resolution", "seconds": 0.182, "module": "server"},
      {"name": "manual_action_append", "seconds": 0.006, "module": "server"},
      {"name": "response_build", "seconds": 0.011, "module": "server"}
    ]
  },
  "browser_profile": {
    "fetch_seconds": 0.024,
    "render_seconds": 0.019
  },
  "diagnosis": "locator_resolution dominates; optimize indexed row lookup"
}
```

Refactor trigger:

```text
observed slow or blocking UX
  -> span identifies owner
  -> focused test reproduces span shape or missing attribution
  -> smallest state/projection/profile fix
  -> rerun original scenario
```

Missing profile data is itself a workflow defect. If Codex cannot tell whether
time went to UI, Python, C, cache invalidation, or DOM rendering, add
instrumentation before optimizing.

## Tutorial: Verify In-Situ UI Updates

Simple manual metadata edits should feel local. They should not block the user
with a full progress dialog when the visible effect is known.

Expected UX contract:

```text
manual action append succeeds
  -> affected visible row is patched or refreshed in place
  -> success feedback is local to affected row
  -> no modal progress for cheap metadata-only edit
  -> selection and viewport anchor stay stable
  -> user can keep browsing while background stale-state work runs
```

Scenario UX assertions:

```json
{
  "ux": {
    "must_not_show_modal_progress": true,
    "must_not_show_state_loss_warning": true,
    "selection_stable": true,
    "viewport_anchor_stable": true,
    "affected_rows": [
      {"locator": "...", "feedback": "success_highlight"}
    ]
  }
}
```

Browser-side assertion shape:

```python
def assert_in_situ_success(cdp, locator):
    state = cdp.evaluate("window.__amigaDebugState()")

    assert state["mutation"]["pending_mutation_id"] is None
    assert state["selection"]["selected_locator"] == locator
    assert not state["ui"]["modal_progress_visible"]
    assert not state["ui"]["state_loss_warning_visible"]
    assert locator in state["ui"]["recent_success_locators"]
```

If the browser debug hook cannot expose this state cleanly, the client state
model needs cleanup. Do not fall back to screenshot-only verification for
interaction state.

## Tutorial: Use Visual Checks As The Last Layer

Visual checks are still useful for layout, affordance, and final visible state.
They should not be the semantic oracle.

Use visual checks for:

```text
row feedback color and duration class
modal/progress absence
command palette parameter editor layout
text clipping or overlap
selection/focus styling
scroll anchor behavior
```

Do not use visual checks for:

```text
whether a Manual Action Log entry exists
whether effective metadata has the right slot
whether a locator is stale
whether a nearby generated label was corrupted
whether analysis ran unnecessarily
```

Example final DOM assertion:

```python
def assert_visible_post_comment(cdp, locator, text):
    row = cdp.find_row_by_locator(locator)
    assert row.query_selector(".comment-post").inner_text() == text
```

The DOM selector should use locator-backed row metadata when available. Avoid
row index, incidental text, arbitrary sleeps, and screenshots as authority.

## Tutorial: Write The LLM UI Verification Report

Every non-trivial web UI change should leave a concise verification report.

Suggested report shape:

```json
{
  "schema_version": 1,
  "change_id": "manual-comment-editor-local-update",
  "scenarios": [
    {
      "scenario_id": "manual-comment-edit-local-row",
      "target_id": "bloodwych",
      "command_id": "comment.edit",
      "result": "passed",
      "semantic_state": "passed",
      "projection_state": "passed",
      "browser_state": "passed",
      "dom_state": "passed",
      "durability": {
        "immediate": "passed",
        "browser_refresh": "passed",
        "target_reopen": "passed"
      },
      "ux": {
        "modal_progress": "absent",
        "state_loss_warning": "absent",
        "success_feedback": "affected_row_only"
      },
      "workflow_profile": {
        "request_id": "req-42",
        "slowest_span": "locator_resolution",
        "slowest_seconds": 0.018
      }
    }
  ],
  "residual_risk": [
    "server_restart boundary not run in focused local check"
  ]
}
```

Human-readable summary:

```text
Manual comment edit passed semantic, projection, browser, and DOM checks.
Refresh and target reopen preserved the post-comment. No neighboring rows or
pre-comment slots changed. The workflow did not show modal progress or state
loss warnings. Slowest span was locator_resolution at 18ms.
```

Reports may be generated in test output first. They become committed artifacts
only if they are useful for historical scenario inventory.

## Larger Architecture Observations

### 1. LLM Operability Is A Code Quality Property

If an LLM has to infer state by scraping DOM text, waiting arbitrary durations,
or reading private mutable globals, the UI contract is weak for humans too.

Good shape:

```text
typed command
stable locator
authoritative result
debug state
semantic assertion
profile spans
```

Weak shape:

```text
click this visible text
wait two seconds
look for another text string
assume the durable state matched
```

### 2. UX Correctness And Durability Are The Same Problem

The user-visible experience depends on durable state reconstruction:

```text
fast local feedback
  only trustworthy if reload/reopen proves the same fact

green success highlight
  only trustworthy if the authoritative mutation result identifies the row

no state-loss warning
  only trustworthy if stale responses cannot overwrite fresh state
```

Do not treat "looks right now" and "is right after refresh" as separate
acceptance categories.

### 3. UI Work Should Not Trigger Broad Reanalysis By Default

Manual metadata edits should be local unless their action class changes code or
data classification, entrypoints, analysis policy, or source rendering inputs.

The harness should report unnecessary work:

```text
comment.edit triggered C analysis: unexpected
label.rename invalidated unrelated listing cache: unexpected
type.change triggered source regeneration: expected
entrypoint.add triggered analysis: expected
```

### 4. Debug State Should Be Small And Honest

`window.__amigaDebugState()` should expose client state needed to verify the
contract. It should not become a second application model.

If tests need too many special debug fields, simplify the state model or move
the relevant state into an explicit session object.

### 5. Rewrite Awkward State Shapes Instead Of Wrapping Them

This project has one consumer. If an old route payload, row id, client cache, or
state flag makes correctness hard to prove, replace it and update callers.

Better rewrite direction:

```text
row-index selection
  -> ListingRowLocator selection

optimistic text patch with no reconciliation
  -> Authoritative Mutation Result plus in-situ projection update

DOM-only command context
  -> command context from locator and element_id

ad hoc progress modal
  -> action-class refresh policy plus workflow_profile spans
```

### 6. Scenario Fixtures Are Design Memory

Historical UI bugs should not live only in chat logs. A scenario fixture records
the user intent, wrong behavior class, durability boundary, and semantic oracle.

## Implementation Slices

### Slice 1: UI Scenario Schema And Report Writer

Add a small scenario/report model near the existing workflow harness.

Candidate artifacts:

```text
tests/ui_scenarios/
tests/ui_scenarios/manual_comment_edit.json
tests/ui_scenarios/label_scope_no_alias.json
amiga_reversing/disasm/ui_verification_report.py
```

Exit condition:

```text
one scenario fixture can be loaded, validated, and reported without opening a
browser
```

### Slice 2: API Scenario Runner

Build an API-first runner over existing command and projection services.

It should:

```text
load scenario
resolve locator
query command availability
execute command
read mutation result
read semantic/projected state
assert forbidden effects
emit report
```

Exit condition:

```text
comment.edit and label.rename scenarios pass through API-only semantic checks
```

### Slice 3: Durability Matrix Integration

Connect scenario declarations to the Proposal 007 durability matrix.

Exit condition:

```text
scenario failures name boundary and semantic layer
```

### Slice 4: Browser Scenario Runner

Extend CDP helpers so a scenario can drive the browser only where browser
behavior matters.

It should:

```text
read window.__amigaDebugState()
select rows by ListingRowLocator
open command UI or use command route depending on scenario
assert browser state
assert final DOM state
avoid row text, row index, screenshots, sleeps, and private globals as oracles
```

Exit condition:

```text
one representative manual edit scenario passes API, browser state, and DOM
assertions
```

### Slice 5: UX Contract Assertions

Add scenario fields for:

```text
modal progress absence
state-loss warning absence
selection stability
viewport anchor stability
affected-row success feedback
ability to continue browsing during background work
```

Exit condition:

```text
cheap metadata edit proves local feedback without modal progress or stale-state
warning
```

### Slice 6: Workflow Profile Attachment

Require scenario reports to include workflow spans when the workflow emits them.

Exit condition:

```text
manual edit report correlates browser request id, backend workflow_profile, and
browser fetch/render sample
```

### Slice 7: Historical Bug Fixture Pack

Add fixtures for the known classes:

```text
post-comment stored as pre-comment
comment appears on neighboring row
local label edit aliases generated abs_/loc_ labels
yellow state-loss warning despite successful mutation
modal progress shown for cheap metadata edit
unnecessary analysis triggered by comment or label edit
stale projection overwrites fresh mutation
```

Exit condition:

```text
each historical class has either a passing regression fixture or a documented
reason it cannot yet be expressed
```

### Slice 8: Codex Web UI Change Playbook

Document the loop for future agent sessions.

Short version:

```text
1. Identify user intent and affected workflow.
2. Add or reuse a UI scenario fixture.
3. Make the UI/code change.
4. Run API scenario first.
5. Run browser scenario only when browser behavior changed.
6. Run durability boundaries for persistent state.
7. Read workflow_profile before performance refactors.
8. Report semantic/projection/browser/DOM result and skipped boundaries.
```

Exit condition:

```text
future Codex sessions have one repo-visible guide for UI verification work
```

### Slice 9: Final Tracking Cleanup

Promote durable issue notes into this proposal. Delete completed
`docs/issues/013-*` issue files if created. Remove stale TODOs.

## Artifact Ownership

Expected artifacts:

```text
docs/proposals/013-llm-web-ui-verification-loop.md
tests/ui_scenarios/*.json
tests/workflow_harness.py
tests/test_web_e2e_cdp.py
amiga_reversing/disasm/ui_verification_report.py
```

Ownership rule:

```text
scenario fixtures own user intent and expected behavior
API harness owns durable/projection assertions
CDP harness owns browser/DOM assertions
workflow_profile owns timing attribution
reports own human-readable diagnosis
```

## Non-Goals

- Do not create an agent-only web UI API.
- Do not replace Proposal 010's reversing loop.
- Do not make screenshots the semantic oracle.
- Do not add broad sleeps or retry loops as correctness fixes.
- Do not preserve row-index or rendered-text identity when locators exist.
- Do not require browser tests for workflows whose changed behavior is purely
  server/projection-side.
- Do not require live internet access.
- Do not make modal progress acceptable for cheap metadata edits by documenting
  it as current behavior.

## Acceptance Criteria

- A scenario fixture can express user intent, command, locator/element context,
  expected semantic fact, forbidden effects, durability boundaries, and UX
  expectations.
- API scenario runner can prove durable state, effective metadata, listing
  projection, and forbidden effects.
- Browser scenario runner can prove browser debug state and final DOM state
  without using row index, incidental row text, arbitrary sleeps, or screenshots
  as authority.
- Persistent scenarios run declared durability boundaries.
- Manual edit scenarios report workflow_profile spans when available.
- Cheap metadata edit scenarios assert no modal progress and no state-loss
  warning.
- Historical user-visible UI bugs become fixtures or explicitly documented gaps.
- LLM UI verification reports identify failures by layer: durable state,
  effective metadata, projection, browser state, DOM, or performance span.
- Future UI changes have a documented playbook for when to run API-only,
  browser/CDP, durability, profile, and full precommit checks.

## Verification Plan

Minimum verification:

```powershell
uv run python -m pytest tests\test_workflow_harness.py -q
uv run python -m pytest tests\test_disasm_server.py -q
uv run python -m pytest tests\test_web_app_source.py -q
uv run python -m pytest tests\test_web_e2e_cdp.py -q
```

Focused tests by touched area:

```text
scenario schema:
  fixture validation tests

API runner:
  comment.edit semantic/durability test
  label.rename forbidden-alias test

browser runner:
  debug state and DOM final assertion test

UX contract:
  no modal progress for cheap metadata edit
  no state-loss warning after successful mutation
  selection and viewport anchor stable

profiling:
  manual edit report includes workflow_profile and correlated browser sample
```

Broader verification:

```powershell
cmd /c src\precommit.bat
```

Run broader verification when a UI change affects shared command execution,
listing projection, manual action projection, source rendering, analysis, or
round-trip behavior.

## Deletion Checklist

Before closing this proposal:

- Promote durable issue reasoning into this proposal.
- Delete completed `docs/issues/013-*` issue files if they exist.
- Remove stale TODO entries for blind UI checks that are replaced by scenarios.
- Ensure scenario fixtures are documented.
- Ensure skipped durability boundaries are reported with reasons.
- Ensure no new row-index/rendered-text UI oracle was added where
  `ListingRowLocator` is available.
- Ensure cheap metadata edits do not require modal progress.

## Verification

Draft created from proposals 001, 007, 009, 010, and the structure of proposal
011. No code behavior changed.
