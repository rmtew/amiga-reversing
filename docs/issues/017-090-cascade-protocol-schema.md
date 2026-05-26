# 017-090: Define Cascade Protocol State And Schemas

Status: completed
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Dependency: none. This is the first cascade refocus issue.
- Protocol area: parent facts, derived facts, propagation rules, fixed-point state, and verifier deltas.
- Current proposal state: prior issues implemented selected-candidate decisions but not cascaded analysis.
- Desired proposal state after this issue: the repo has a concrete, documented schema for accepted parent facts, derived child facts, cascade provenance, invalidation, blockers, render effects, and verifier deltas.

## Protocol Delta

- Adds: first-class cascade state terminology and schema.
- Changes: new 017 work must model decisions as parent facts when they imply downstream analysis.
- Replaces: selected-row-only fact modeling as the default protocol.
- Leaves out of scope: implementing A5/RSSET/immediate/callback cascade rules, target state mutation, 012/018, Mac OS support, and Mac targets.

## Default Behavior

- Do not add a private schema inside one report.
- Define how parent facts, derived facts, blocked children, conflicts, render effects, and verifier deltas are represented.
- Define how derived facts link to parent fact ids and deterministic rule ids.
- Define fixed-point stop conditions and invalidation semantics.

## Pandora Proof

- Use current Pandora A5, RSSET, immediate, and callback reports as examples.
- Include the `017-089` failure as the negative example: current text is not proof of decision-caused source progress.

## Implementation Slice

- C fact graph/query work: document where cascade state must ultimately live and which existing C fact surfaces can be reused.
- Python/API/report work: define transitional JSON shapes for issue implementation.
- Journal/replay work: define accepted parent fact and derived fact relationships.
- Renderer/verifier work: define baseline-without-decision versus effective-with-decision verifier contract.
- Tests: schema validation or fixture tests for representative parent/child/blocker objects if code schema is added.

## Research Coverage

- [x] Proposal 017 cascade sections checked.
- [x] Existing A5, RSSET, immediate, and callback report shapes reviewed.
- [x] Parent fact schema defined.
- [x] Derived fact schema defined.
- [x] Blocked child and conflict schema defined.
- [x] Baseline delta verifier contract defined.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] This is a cohesive protocol foundation, not another report-only closeout.
- [x] The schema supports chained derived analysis to fixed point.
- [x] The schema makes stale/invalidated children disappear or recompute.
- [x] Proposal 017 living notes updated.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] Schema/docs/tests are committed.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

- Implemented `amiga_reversing.disasm.cascade` with schema helpers for parent facts, derived facts, blocked children, render effects, verifier deltas, validation, and deterministic state hashing.
- Added `tests/test_cascade.py` schema and fixed-point fixture coverage.
- Added `cascade-report` inspection wiring in `amiga_reversing.reversing_loop` as the transitional Python/API surface over existing C-owned listing and report facts.
- Validation commands run after the full 017-090 through 017-096 batch: `uv run python -m amiga_reversing.tools.validate_017_issues` and `git diff --check`.

## Cascade Evidence

- Parent fact schema implemented: `parent_fact()` carries `fact_id`, `fact_type`, `status`, `scope`, `provenance`, `conflicts`, `invalidated_by`, and source-state identity.
- Derived child schema implemented: `derived_fact()` carries `parent_fact_ids`, deterministic `rule_id`, scope, provenance, optional render effect, and optional verifier delta.
- Blocked child/conflict schema implemented: `blocked_child()` carries blockers, parent ids, rule id, scope, provenance, and conflicts.
- Baseline-delta verifier proof contract implemented in `verifier_delta()`: baseline/effective state, changed rows, bounded effect, negative safety, fixed point, and exact round-trip status are first-class fields.
- Fixed point behavior checked by `tests/test_cascade.py`; stale source identities and missing parent scopes fail closed.
- Not report-only: this issue added executable schema and validation code plus focused tests.
