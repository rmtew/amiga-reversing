# 017-031: Evidence-Driven Analysis Architecture Inventory

Status: active

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: evidence-driven analysis architecture inventory
- Current proposal state: 017 defines the Evidence-Driven Analysis Protocol as
  the master working specification, but the concrete rewrite scope is not fixed
  until current analysis architecture is researched.
- Desired proposal state after this issue: 017 includes a checked architecture
  map, reuse/replace findings, rewrite-scope boundaries, and a recommended
  first implementation slice.

## Protocol Delta

- Adds: verified current-architecture inventory for target load,
  auto-analysis, fact/state ownership, reports, commands, rendering,
  verification, and Pandora-specific surfaces.
- Changes: proposal rewrite scope from preliminary direction to research-backed
  plan.
- Replaces: none.
- Deletes: none.
- Leaves out of scope: v2 implementation, default behavior changes,
  opportunistic refactors, old-code deletion, broad Pandora mutation runs.

## Default Behavior

- Unchanged, v2 internal only: no v2 implementation in this issue.
- Switched surface to v2: none.
- Deleted old surface path: none.
- User-visible behavior: none, except updated proposal/issue documentation.

## Pandora Proof

- Target candidate: current Pandora RSSET/A5/immediate report surfaces,
  especially `rsset-raw-a6:022E`, source-offset immediate `s0:000009A6`, and
  A5 hardware/base evidence surfaces.
- Evidence packet expected: not implemented here; research must define what the
  first packet slice should cover.
- Decision behavior: not implemented here; research must map current
  Manual Action Log behavior and recommend Decision Journal replacement scope.
- Command gate behavior: not implemented here; research must map current
  command catalog/planner/verifier flow.
- Render effect: not implemented here; research must map current source
  export/render projection flow.
- Verifier/round-trip: not implemented here; research must map current verifier
  and round-trip layers.

## Implementation Slice

- C fact graph/query work: research current C analysis ownership and query
  shape only.
- Python/API/report work: research current orchestration, reports, APIs,
  command catalog, and planner only.
- Journal/replay work: research current Manual Action Log and replay behavior
  only.
- Renderer/verifier work: research current render/export and verifier paths
  only.
- Tests: no implementation tests required unless narrow inspection tooling is
  added to answer the research.

## Research Coverage

- [ ] Target load lifecycle traced, or marked out of scope with reason.
- [ ] Post-load auto-analysis hooks traced, or marked out of scope with reason.
- [ ] C analysis ownership mapped, or marked out of scope with reason.
- [ ] Python orchestration ownership mapped, or marked out of scope with reason.
- [ ] Platform-specific extension points mapped, or marked out of scope with reason.
- [ ] Fact/state sources inventoried, or marked out of scope with reason.
- [ ] Derived-state/replay assumptions inventoried, or marked out of scope with reason.
- [ ] Reports/candidate generation traced, or marked out of scope with reason.
- [ ] Command catalog/planner flow traced, or marked out of scope with reason.
- [ ] Legacy Manual Action Log flow traced, or marked out of scope with reason.
- [ ] Render/export flow traced, or marked out of scope with reason.
- [ ] Verifier/round-trip flow traced, or marked out of scope with reason.
- [ ] Pandora RSSET/A5/immediate surfaces mapped, or marked out of scope with reason.
- [ ] Hidden couplings/risks listed, or marked out of scope with reason.
- [ ] Reuse/replace candidates classified, or marked out of scope with reason.
- [ ] First implementation slice recommended, or blocker recorded.

If research discovers another relevant subsystem, add it to this checklist
before continuing. The issue is not complete until the expanded checklist is
signed off or explicitly marked out of scope with reason.

## Research Review

- [ ] Second pass checked file/function coverage.
- [ ] Cross-references searched for missed hooks.
- [ ] Findings were checked against Pandora current surfaces.
- [ ] Proposal updated with model corrections and rewrite-scope findings.
- [ ] Next issue scope follows from the inventory.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Protocol delta implemented as described, or proposal updated.
- [ ] Default behavior impact verified.
- [ ] Old code deleted, or deferred deletion blocker recorded.
- [ ] Evidence packet shape tested.
- [ ] Decision/replay behavior tested where applicable.
- [ ] Command gate refuses unsafe mutation.
- [ ] Render/verifier/round-trip checked where output-affecting.
- [ ] Pandora proof recorded.
- [ ] Post-commit review found no unresolved worthwhile findings.
