# 017-090: Define Cascade Protocol State And Schemas

Status: active
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

- [ ] Proposal 017 cascade sections checked.
- [ ] Existing A5, RSSET, immediate, and callback report shapes reviewed.
- [ ] Parent fact schema defined.
- [ ] Derived fact schema defined.
- [ ] Blocked child and conflict schema defined.
- [ ] Baseline delta verifier contract defined.
- [ ] No 012/018/Mac/platform-format files touched.

## Research Review

- [ ] This is a cohesive protocol foundation, not another report-only closeout.
- [ ] The schema supports chained derived analysis to fixed point.
- [ ] The schema makes stale/invalidated children disappear or recompute.
- [ ] Proposal 017 living notes updated.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] Schema/docs/tests are committed.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

