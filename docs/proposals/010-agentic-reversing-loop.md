# Proposal 010: Agentic Reversing Loop

Status: Draft.

This proposal defines the missing orchestration layer on top of Proposal 007
and Proposal 009: a repo-visible reversing loop harness plus an agent playbook
that lets an LLM operate the reversing process through normal project
interfaces.

## Checkpoint Index

- [ ] Why This Exists
- [ ] Mental Model
- [ ] Current State Read
- [ ] Integration Findings
  - [ ] 1. The Operable Surface Exists, But The Loop Is Not Encoded
  - [ ] 2. Agent Decisions Need Repo-Visible Inputs And Outputs
  - [ ] 3. Reversing Actions Need Verification Contracts
  - [ ] 4. Refactoring Needs A Trigger, Not A Vibe
  - [ ] 5. Stop Conditions Must Be Explicit
- [ ] Tutorial: Reversing Loop Harness
  - [ ] Step 1: Define Iteration State
  - [ ] Step 2: Discover Candidate Work
  - [ ] Step 3: Execute Through Normal Command Paths
  - [ ] Step 4: Verify And Record The Result
- [ ] Tutorial: Target Workspace Hygiene
- [ ] Tutorial: Agent Playbook
- [ ] Tutorial: Refactor-As-You-Go Loop
- [ ] Larger Architecture Observations
  - [ ] 1. The Harness Should Be A Deep Module
  - [ ] 2. The Agent Should Not Get Private Powers
  - [ ] 3. Reports Are Part Of The Interface
  - [ ] 4. Verification Should Be Layered
- [ ] Forward Implementation Model
  - [ ] Agent Workspace Model
  - [ ] Target Cleanliness Contract
  - [ ] Reversing Loop Harness
  - [ ] Work Item Model
  - [ ] Action Candidate Model
  - [ ] Iteration Report
  - [ ] Agent Playbook
  - [ ] Refactor Trigger Policy
- [ ] Artifact Ownership
- [ ] Non-Goals
- [ ] Proposed Rewrite
  - [ ] Slice 1: Agent Playbook Draft
  - [ ] Slice 2: Target Workspace Hygiene Report
  - [ ] Slice 3: Safe Clean-Run Cleanup
  - [ ] Slice 4: Reversing Loop Read-Only Report
  - [ ] Slice 5: Run Identity And Report Storage
  - [ ] Slice 6: One Manual Mutation Iteration
  - [ ] Slice 7: Verification And Durability Contract
  - [ ] Slice 8: Refactor Trigger And Profiling Policy
  - [ ] Slice 9: End-To-End Agent Smoke
- [ ] Acceptance Criteria
- [ ] Deletion Checklist
- [ ] Rewrite Acceptance Tests
- [ ] Verification

## Why This Exists

Proposal 007 made the web UI and API state durable enough for an LLM to operate
without scraping incidental DOM text. Proposal 009 made workflows observable
through shared profile spans. Together they provide the buttons and gauges.

The missing layer is the loop:

```text
inspect current target state
  -> choose the next reversing action
  -> apply the action through normal project interfaces
  -> regenerate affected outputs
  -> verify semantic state and round-trip behavior
  -> inspect workflow spans
  -> decide whether to continue, refactor, or stop
```

Today, Codex can perform those steps manually, but the project does not yet have
a repo-visible harness or playbook that makes the loop repeatable. That means
agent work depends too much on conversational memory and local judgment.

The goal is to make autonomous or semi-autonomous reversing work boring:

```text
same command paths as the UI
same durable state as manual review
same workflow profiles as humans inspect
same verification gates as code changes use
same reports after every iteration
```

## Mental Model

Think of the agent as an operator of project workflows, not a privileged
subsystem.

```text
LLM agent
  -> reversing loop harness
  -> command routes / project services
  -> Manual Action Log / generated facts / source rendering
  -> listing projection / debug state / workflow profile
  -> verification gates
  -> iteration report
```

The harness should answer these questions for every iteration:

```text
What target was inspected?
What unresolved work item was selected?
What evidence justified the action?
What command or code change was made?
What durable state changed?
What projection changed?
What verification ran?
What profile spans explain the cost?
What should happen next?
```

The agent playbook answers the policy question:

```text
Given those facts, what is the next allowed move?
```

## Current State Read

The project now has strong primitives:

```text
ListingRowLocator and projection_hash identify listing rows.
Command routes expose machine-readable command availability and execution.
Manual Action Log is the durable manual-review state.
ListingProjectionService exposes server debug state.
window.__amigaDebugState() exposes browser state for CDP/LLM checks.
WorkflowProfile records backend spans.
tests/workflow_harness.py asserts semantic workflow state.
CDP includes an LLM-operable command smoke workflow.
Round-trip verification and source rendering expose profile data.
```

The gap is orchestration. There is no single harness that owns:

```text
target workspace hygiene
target state summary
next candidate selection
action execution envelope
post-action verification matrix
profile summary
iteration report
stop reason
```

There is also no dedicated agent playbook that tells Codex how to use those
interfaces safely while reversing a target and improving support code.

Existing `targets/<target>/` directories may already contain stale generated
files, obsolete UI/manual state, partial manual progress, or broken results from
past agent attempts. The loop must not treat all target-local files as equally
authoritative. Before an autonomous run, the harness needs a cleanliness pass
that classifies target files and records which state is trusted, reset, or left
for user review.

## Integration Findings

### 1. The Operable Surface Exists, But The Loop Is Not Encoded

Proposal 007 and 009 intentionally avoided creating a separate agent-only API.
That remains correct. The loop should consume existing surfaces:

```text
GET /api/projects/{target}/listing
GET /api/projects/{target}/commands
POST /api/projects/{target}/commands/execute
ListingProjectionService.debug_state()
window.__amigaDebugState()
workflow_profile payloads
round-trip verification reports
```

But without a harness, an agent must rediscover the sequence every time. The
project should encode the sequence once.

Target shape:

```text
amiga_reversing.reversing_loop
  inspect_target()
  list_candidates()
  run_iteration()
  verify_iteration()
  write_report()
```

### 2. Agent Decisions Need Repo-Visible Inputs And Outputs

Agent decisions should be auditable from files or structured reports, not only
from chat logs.

An iteration report should include:

```json
{
  "target_id": "bloodwych",
  "iteration": 12,
  "selected_work_item": {"kind": "manual_review_item", "id": "..."},
  "evidence": {"xrefs_checked": true, "projection_hash": "..."},
  "action": {"kind": "command", "command_id": "comment.edit"},
  "durable_result": {"manual_action_id": "..."},
  "verification": {"round_trip": "passed", "semantic_state": "passed"},
  "workflow_profile": {"workflow_id": "manual_command_execution"},
  "next": {"recommendation": "continue"}
}
```

The report is not a second source of truth. It is the audit trail for what the
agent did and why.

### 3. Reversing Actions Need Verification Contracts

Different action classes need different checks.

Examples:

```text
comment or naming action:
  semantic state reload check
  listing projection check

data/code classification seed:
  analysis regeneration
  listing projection check
  focused round-trip check

source rendering or backend refactor:
  focused unit tests
  round-trip verification for affected target
  precommit when broad enough

performance refactor:
  workflow_profile before/after comparison
  no semantic regression
```

The harness should not accept "screen looked right" as enough.

### 4. Refactoring Needs A Trigger, Not A Vibe

One goal is to let an LLM improve and refactor supporting code while reversing.
That needs a policy so the agent does not rewrite code just because it can.

Valid refactor triggers:

```text
workflow_profile shows repeated cost in a named span
agent cannot express needed action through current APIs
verification failure points to missing state contract
manual workaround would violate project conventions
duplicated code blocks current next reversing action
```

Invalid triggers:

```text
style preference
speculative cleanup unrelated to current target
compatibility wrapper around obsolete state
new private agent-only path
```

### 5. Stop Conditions Must Be Explicit

The loop needs bounded stopping rules.

Examples:

```text
round-trip parity improved and no next high-confidence item remains
verification failed and the cause is unknown after diagnosis
required oracle/tool is unavailable
next action would require user domain judgment
budget exhausted
support-code refactor is required before more reversing work is safe
```

Without stop conditions, `/goal` can keep driving effort after useful progress
has ended.

### 6. Agent Work Needs A Workspace Boundary

The agent needs a place to write reports and scratch evidence without polluting
durable target state.

Target directories should keep source-of-truth project state:

```text
targets/<target>/
  source/import facts
  Manual Action Log
  generated/rebuilt outputs
  target-tied reports
```

Agent run state should be separate:

```text
targets/<target>/agent/
  iteration reports
  cleanup reports
  proposed actions
  before/after verification records

work/agent/<run-id>/ or .agent/runs/<run-id>/
  disposable scratch evidence
  failed experiment notes
  temporary copied reports
```

Core rule:

```text
targets/<target>/ is durable project state.
agent run directories are scratch and audit state.
```

The exact scratch root can be chosen during implementation. The important part
is that temporary agent work is not mixed with durable facts.

### 7. Run Identity, Resume, And Rollback Need Contracts

Long-running agent work needs a stable run identity. The loop should not depend
on chat history to know whether it is continuing a previous run.

Required run state:

```text
run_id
target_id
mode
started_at
last_iteration_id
status
report_paths
```

Report writes should be append-only for history and atomic for the latest
pointer:

```text
targets/<target>/agent/reversing-loop.jsonl
targets/<target>/agent/latest-reversing-loop.json
```

Resume policy:

```text
continue mode may resume the latest non-terminal run when the last iteration is
complete and verification status is known

if the latest iteration is partial, the harness must report the partial state
and stop or start a new run explicitly

clean-run starts a new run_id

reimport starts a new run_id
```

Rollback policy:

```text
Manual Action Log is append-only.
Do not delete manual history to undo an agent action.
Undo by appending a corrective action when the domain supports it, or by
clean-run/reimport when the selected mode explicitly discards local manual
state.
```

### 8. The CLI Surface Should Be Stable

`/goal` needs one stable command surface to drive. The harness should expose a
small CLI, not only Python internals.

Illustrative command surface:

```text
uv run python -m amiga_reversing.reversing_loop hygiene --target <target>
uv run python -m amiga_reversing.reversing_loop clean-run --target <target>
uv run python -m amiga_reversing.reversing_loop inspect --target <target>
uv run python -m amiga_reversing.reversing_loop run-one --target <target> --dry-run
uv run python -m amiga_reversing.reversing_loop run-one --target <target>
```

The exact module path can change during implementation, but the proposal should
require a stable entrypoint.

## Tutorial: Reversing Loop Harness

The harness is a repo module and optional CLI that makes one reversing iteration
repeatable.

### Step 1: Define Iteration State

Create a small structured model:

```text
TargetState:
  target_id
  binary identity
  current projection hash
  manual action log count/head hash
  round-trip status
  unresolved review counts
  recent workflow profile summaries

ReversingWorkItem:
  id
  kind
  locator or durable domain id
  xrefs summary
  current confidence
  suggested action kinds

ReversingIterationReport:
  input target state
  selected work item
  action result
  verification result
  profile result
  stop/continue recommendation
```

### Step 2: Discover Candidate Work

Candidate discovery should start conservative:

```text
manual review items
unresolved labels near known code
data/code ambiguity rows
round-trip mismatch rows
high-cost workflow spans
```

For each candidate, the harness records why it is actionable:

```text
has stable locator
has xrefs
has command availability
has focused verification path
```

Low-confidence items should be reported, not auto-mutated.

### Step 3: Execute Through Normal Command Paths

The first write-capable slice should perform one safe manual mutation, such as a
comment edit or naming action, through the existing command route/service path.

Rules:

```text
use ListingRowLocator, not row index or row text
use command availability before execution
append through Manual Action Log commands
return authoritative mutation result
capture workflow_profile
```

The harness may expose a dry-run mode that stops after candidate/action
selection.

### Step 4: Verify And Record The Result

After a mutation, the harness verifies the durable state:

```text
reload project state
recompute listing projection
assert expected locator/effective metadata
run durability boundary checks when applicable
run round-trip or focused checks when the action can affect output
write iteration report
```

The report should name the failing layer:

```text
candidate discovery
command availability
command execution
durable state
projection
round-trip
browser/debug state
performance/profile
```

## Tutorial: Target Workspace Hygiene

Before a reversing loop mutates a target, it should classify target-local files.
This is not a blind cleanup command. It is a state contract.

Classification:

```text
source/import fact:
  preserve unless explicitly reimporting

durable manual state:
  preserve for continuation mode
  reset only in clean-run mode

generated output:
  safe to regenerate through named commands

obsolete UI/manual state:
  delete or quarantine through named reset command

agent scratch/audit:
  preserve as report history or move to run workspace

unknown:
  stop or require explicit user approval before deletion
```

The hygiene report should include:

```json
{
  "target_id": "bloodwych",
  "mode": "inspect",
  "files": [
    {"path": "target_seeded_metadata.json", "class": "source_import_fact", "action": "preserve"},
    {"path": "target_ui_edits.json", "class": "obsolete_ui_state", "action": "delete_on_clean_run"},
    {"path": "ui_preferences.json", "class": "obsolete_or_local_ui_state", "action": "delete_on_clean_run"}
  ],
  "unknown_files": [],
  "safe_to_run": true
}
```

The first implementation must include an explicit allowlist inventory for known
target-local files. Illustrative initial classes:

```text
preserve source/import facts:
  target_seeded_metadata.json
  target_corrections.json
  import/source fact files identified by the target import path

reset obsolete/local UI or manual state in clean-run:
  target_ui_edits.json
  ui_preferences.json
  manual_actions.jsonl

regenerable/generated outputs:
  listing/source/rebuild/report artifacts produced by current tools

agent audit/scratch:
  targets/<target>/agent/*

unknown:
  anything not classified by the allowlist or import/generator inventory
```

The concrete inventory should be implemented from project constants or helper
functions where possible. The report must expose the effective classification so
future stale files are visible.

Cleanliness modes:

```text
inspect:
  classify only

continue:
  preserve durable manual state and continue from current target

clean-run:
  preserve source/import facts, reset generated/obsolete/local UI state, and
  start a fresh agent run

reimport:
  run the target import path and discard target-local generated/manual state
  according to import rules
```

Clean-run execution is separate from read-only hygiene:

```text
hygiene inspect:
  classify and report only

clean-run:
  delete only files classified as generated, obsolete UI/manual state, or local
  manual state
  preserve source/import facts
  preserve agent audit history unless explicitly pruning scratch
  stop on unknown files
  write a cleanup report before and after deletion
```

Rules:

```text
never silently trust old generated output
never silently delete source/import facts
never use obsolete UI state as durable intent
write every cleanup action to an agent report
stop on unknown files that could be durable project state
```

This protects the loop from verifying against polluted state left by previous
manual or agent attempts.

## Tutorial: Agent Playbook

The playbook is a short document for Codex. It should live near other agent
docs, for example:

```text
docs/agents/reversing-loop.md
```

It should include:

```text
entry commands
workspace and target cleanliness modes
decision order
allowed mutation paths
required checks after each action class
rules for xref inspection and naming
when to refactor support code
when to stop and ask the user
how to summarize iteration reports
```

Initial decision order:

```text
1. Run target workspace hygiene in inspect mode.
2. Choose continue, clean-run, or reimport mode.
3. Inspect target state and current round-trip status.
4. Pick the highest-confidence candidate with xrefs and a verifier.
5. Prefer durable manual commands over direct file edits.
6. Verify semantic state after every durable mutation.
7. Use workflow_profile spans before performance refactors.
8. Run focused tests after code changes.
9. Escalate to broader round-trip/precommit checks when behavior changes.
10. Stop on unknown target files, unknown verification failure, or missing
    domain judgment.
```

The playbook should be directive and short. The harness owns detail.

## Tutorial: Refactor-As-You-Go Loop

Refactoring is allowed only when it directly improves the current reversing
loop.

Refactor flow:

```text
observe blocker or hotspot
  -> name the blocking span/state contract/API gap
  -> write or update focused test
  -> make smallest support-code change
  -> rerun original reversing iteration
  -> record before/after evidence
```

Examples:

```text
locator_resolution span dominates repeated edits:
  optimize ListingProjectionService locality

agent cannot select a semantic item without DOM scraping:
  extend debug state or command metadata

round-trip report cannot point to a row:
  improve row mapping/report payload
```

## Larger Architecture Observations

### 1. The Harness Should Be A Deep Module

The harness earns its place if callers do not need to know every route,
projection helper, and verification detail.

Good interface:

```python
state = inspect_target(target_id)
candidates = list_candidates(state)
report = run_iteration(target_id, candidate_id, dry_run=False)
```

Bad interface:

```text
caller manually loads listing, patches globals, executes commands, reloads
state, runs tests, and hand-builds a report
```

### 2. The Agent Should Not Get Private Powers

The LLM should use the same interfaces as tests and the UI. If the agent needs
private access to do useful work, that is a signal the public project interface
is not deep enough.

Allowed:

```text
command routes
workflow harness helpers
debug state
round-trip reports
normal source edits with tests
```

Avoid:

```text
direct edits to retired state files
row-index mutation subjects
private server globals as normal workflow inputs
browser DOM scraping as the state oracle
```

### 3. Reports Are Part Of The Interface

The iteration report is how a long-running `/goal` remains inspectable. It
should be stable enough for tests and readable enough for humans.

Report locations should be explicit. Illustrative paths:

```text
targets/<target>/agent/reversing-loop.jsonl
targets/<target>/agent/latest-reversing-loop.json
```

### 4. Verification Should Be Layered

Not every iteration needs full precommit, but every iteration needs the right
proof.

Layer examples:

```text
semantic API assertion
durability matrix boundary
round-trip verification
source rendering check
focused unit test
CDP smoke
src/precommit.bat
```

The playbook should choose the narrowest check that proves the action, then
escalate when support code or output behavior changes.

## Forward Implementation Model

### Agent Workspace Model

Explicit locations for durable target state, agent audit reports, and
disposable scratch files.

### Target Cleanliness Contract

Classifier and report for target-local files, with named cleanup modes:

```text
inspect
continue
clean-run
reimport
```

### Reversing Loop Harness

Python module plus required stable CLI for hygiene, clean-run, inspect,
dry-run, run-one, and report.

### Work Item Model

Structured representation of actionable reversing work, backed by current
analysis facts, manual review items, listing locators, xrefs, and verification
availability.

### Action Candidate Model

Machine-readable action options:

```text
command action
manual seed action
code/support refactor action
verification-only action
ask-user action
```

### Iteration Report

JSON report recording state, evidence, action, verification, profile spans, and
next recommendation.

Reports use append-only history plus atomic latest-state files, keyed by
`run_id`.

### Agent Playbook

Short Codex-facing rules for operating the harness through `/goal` or ordinary
agent work.

### Refactor Trigger Policy

Rules that say when support-code changes are justified during reversing.

## Artifact Ownership

```text
amiga_reversing/reversing_loop.py or amiga_reversing/disasm/reversing_loop.py
  Owns target inspection, workspace hygiene, candidate selection, iteration
  reports, and loop orchestration.

amiga_reversing/reversing_workspace.py or equivalent
  Owns target file classification, run workspace paths, and cleanup reports.

scripts/reversing_loop.py or a module CLI
  Thin command-line entrypoint.

tests/test_reversing_loop.py
  Owns unit/API behavior for candidate selection and iteration reports.

tests/test_reversing_workspace.py
  Owns target-local file classification and cleanup-mode behavior.

tests/test_agent_reversing_loop.py, if needed
  Owns higher-level smoke behavior.

docs/agents/reversing-loop.md
  Owns Codex operating policy.

targets/<target>/agent/*.jsonl
  Owns generated iteration audit reports.

work/agent/<run-id>/ or .agent/runs/<run-id>/
  Owns disposable agent scratch data if implementation chooses an external run
  workspace.
```

The harness consumes Proposal 007 and 009 surfaces. It does not replace them.

## Non-Goals

This proposal does not create:

```text
a separate agent-only API
a general AI planner
an automatic decompiler
a bypass around Manual Action Log
a guarantee that every reversing decision is safe to automate
a requirement to run full CDP/precommit after every tiny manual annotation
```

## Proposed Rewrite

### Slice 1: Agent Playbook Draft

Write `docs/agents/reversing-loop.md` with the first operating policy.

Exit condition:

```text
Codex has concrete rules for target inspection, candidate choice, allowed
mutation paths, verification, refactor triggers, and stop conditions.
```

### Slice 2: Target Workspace Hygiene Report

Add a read-only target file classifier and hygiene report.

Exit condition:

```text
one command classifies target-local files, identifies stale/obsolete/generated
state, names unknown files, and recommends continue/clean-run/reimport safety
without deleting anything
```

### Slice 3: Safe Clean-Run Cleanup

Add the write-capable cleanup mode for classified target-local state.

Exit condition:

```text
clean-run mode deletes only classified obsolete/generated/local manual state,
preserves source/import facts and agent audit history, stops on unknown files,
and writes before/after cleanup reports
```

### Slice 4: Reversing Loop Read-Only Report

Add a read-only harness command that inspects a target and emits candidate work
without mutating state.

Exit condition:

```text
one command produces target state, unresolved candidate list, available
verification paths, and current profile/round-trip summary
```

### Slice 5: Run Identity And Report Storage

Add `run_id`, report storage, atomic latest reports, append-only history, and
resume rules.

Exit condition:

```text
the loop can start, resume, or reject a run based on explicit on-disk run state
without relying on chat history
```

### Slice 6: One Manual Mutation Iteration

Teach the harness to execute one safe command action through the existing
command route/service path.

Exit condition:

```text
dry-run chooses an action
run mode executes through Manual Action Log command path
result includes authoritative mutation result and workflow_profile
```

### Slice 7: Verification And Durability Contract

Attach the existing workflow harness and round-trip checks to iteration reports.

Exit condition:

```text
after a mutation, report proves reload/projection state and names the checked
boundaries; output-affecting actions run the relevant round-trip check
```

### Slice 8: Refactor Trigger And Profiling Policy

Add report support for profile hotspot summaries and support-code refactor
recommendations.

Exit condition:

```text
the harness can say "continue reversing", "run verification", "refactor this
named span/API gap", or "stop for user input" with evidence
```

### Slice 9: End-To-End Agent Smoke

Add a smoke that follows the playbook for one representative target/action.

Exit condition:

```text
the smoke uses locator-based selection, command discovery/execution, semantic
assertions, workflow_profile, and an iteration report; it does not scrape DOM
text or patch private state
```

## Acceptance Criteria

Required acceptance points:

```text
agent loop entrypoint exists and is documented
stable CLI exists for hygiene, clean-run, inspect, dry-run, and run-one
target workspace hygiene classifies stale, generated, obsolete, durable, and
unknown target-local files before mutation
clean-run mode preserves source/import facts and removes only classified
obsolete/generated/local state through named cleanup logic
agent scratch/audit files are separated from durable project state
run_id and report paths are explicit
history reports are append-only and latest reports are atomic
resume/partial-run behavior is explicit
rollback means append corrective action or clean-run/reimport, not silent manual
history deletion
read-only target inspection reports actionable work candidates
work candidates include durable identities or locators
mutation actions execute through existing command/manual action paths
iteration reports record evidence, durable result, projection state,
verification, workflow_profile, and stop/continue recommendation
semantic verification is required after durable mutations
round-trip verification is required for output-affecting changes
performance/refactor recommendations cite workflow_profile spans or API gaps
agent playbook defines allowed actions, required checks, and stop conditions
no agent-only private mutation path is introduced
tests prove at least one end-to-end iteration
```

## Deletion Checklist

Delete or avoid:

```text
agent instructions that rely on row index or row text as durable identity
direct writes to retired target UI state
temporary scratch files in durable target state
cleanup commands that delete unknown files
cleanup commands that delete source/import facts without explicit reimport mode
manual-action rollback by deleting history
report writes that can leave latest state half-written
loop logic embedded only in chat prompts
reports that cannot be regenerated from project state plus iteration result
private server global patching as normal harness behavior
DOM text scraping as semantic verification
unbounded "keep going" behavior without stop reasons
support-code refactors without a named blocker, failing test, or profile span
```

## Rewrite Acceptance Tests

Minimum tests:

```text
target workspace hygiene classifies known source/import facts as preserve
target workspace hygiene classifies obsolete UI/manual state as resettable
target workspace hygiene stops or warns on unknown possible durable files
clean-run cleanup preserves source/import facts
clean-run cleanup stops on unknown files
run identity creates append-only history and atomic latest report
resume rejects or reports partial iteration state
read-only target inspection returns target state and candidate list
candidate work item contains locator or durable domain id
dry-run iteration reports intended action without mutation
manual mutation iteration executes through command path
iteration report includes workflow_profile spans
semantic state is asserted after reload
durability boundary failure names the failing layer
output-affecting action requires round-trip verification
refactor recommendation requires profile/API-gap evidence
agent smoke follows the playbook for one representative action
```

## Verification

Required checks for implementation work under this proposal:

```text
focused target workspace hygiene tests
focused reversing loop tests
focused workflow harness tests
focused server command tests when command execution is touched
round-trip verification for output-affecting loop actions
CDP smoke only when browser/debug behavior changes
src/precommit.bat before closing the proposal follow-up
```

Useful report artifacts:

```text
target state summary
candidate work list
iteration report JSON
semantic snapshot diff
workflow_profile span summary
round-trip before/after summary
stop reason
```

Review rule:

```text
Do not accept an agent loop because Codex can perform the steps in chat. Accept
it when the repo exposes the steps, reports, and verification contracts needed
to repeat the loop safely.
```

## Implementation Notes

- 010-001 added `docs/agents/reversing-loop.md` as the short Codex-facing
  operating policy. It documents mode choice, required hygiene, locator-based
  mutations, xref checks, verification by action class, evidence-backed
  refactor triggers, and stop conditions. No automated tests were required for
  this documentation-only slice.
- 010-002 added a read-only target hygiene classifier in
  `amiga_reversing.reversing_workspace` plus the stable
  `python -m amiga_reversing.reversing_loop hygiene --target <target>` command.
  The initial allowlist is deliberately conservative: source/import facts and
  agent audit state are preserved, generated/obsolete/local manual state is
  resettable later, and unknown files make automated cleanup unsafe.
- 010-003 added `clean-run` cleanup as a classified file unlink pass. It writes
  before/latest cleanup reports under `targets/<target>/agent/`, preserves
  source/import facts and agent audit files, deletes only generated,
  obsolete-UI, and local manual state, and blocks without deletion when hygiene
  reports unknown files.
- 010-004 added a read-only `inspect` harness report. It combines hygiene,
  manual action log stamps, optional project/manual-review state, round-trip
  report status, conservative candidate work items, available verification
  paths, and an explicit `safe_to_mutate` gate.
