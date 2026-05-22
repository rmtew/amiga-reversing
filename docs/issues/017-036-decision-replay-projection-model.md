# 017-036: Decision Replay Projection Model

Status: planned

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: replayable Decision Journal semantics
- Blocked by: `017-034`, `017-035`
- Current proposal state: Decision Journal records are expected to be durable
  and inspectable, but not projected into an active analysis state.
- Desired proposal state after this issue: accepted, deferred, rejected, and
  superseded decisions can be replayed into an in-memory projection with clear
  active/inactive outcomes and no C fact mutation yet.

## Protocol Delta

- Adds: deterministic replay projection for journal decisions.
- Changes: journal records gain protocol meaning as active/deferred/rejected
  evidence state, while still not mutating C facts.
- Replaces: none.
- Deletes: none.
- Leaves out of scope: C fact graph insertion, command-gate activation,
  rendering, Manual Action Log replacement.

## Default Behavior

- Existing default analysis and reports remain unchanged unless an explicit
  validation/replay helper is invoked.
- Replay projection must be deterministic from current journal contents and must
  not write target state.

## Pandora Proof

- Target candidate: RSSET packet candidate `rsset-raw-a6:022E` at
  `s0:000006E4`.
- Evidence expected: replay can show whether a selected-use RSSET app-base
  decision is active, deferred, rejected, or superseded.
- Decision behavior: accepted facts become active only in the replay
  projection; deferred/rejected decisions remain inspectable blockers.
- Command gate behavior: gate remains blocked because the projection is not yet
  consumed by RSSET mutation.
- Render effect: none.
- Verifier/round-trip: no output-affecting verification required.

## Implementation Slice

- C fact graph/query work: none unless implementation evidence proves a small
  read-only type boundary is needed and the proposal is updated first.
- Python/API/report work: expose replay projection through internal helpers and
  tests, not default reports.
- Journal/replay work: active decision selection, supersession handling,
  conflict preservation, and invalid-record exclusion.
- Renderer/verifier work: none.
- Tests: active accept projection, defer/reject projection, supersession,
  duplicate/invalid exclusion, deterministic ordering, and no target mutation.

## Research Completion Standard

Record trace blocks for journal validation, packet identity, current report
accepted-evidence logic, and any existing projection/state model that could
conflict with replay.

## Research Coverage

- [ ] Decision Journal IO and validation surfaces checked.
- [ ] Current RSSET accepted-evidence classification checked.
- [ ] Existing Manual Action Log projection checked for replacement boundary.
- [ ] Active/inactive/superseded projection rules defined.
- [ ] Side-effect boundary checked so replay projection cannot mutate C facts
  or target state.

## Research Review

- [ ] Second pass checked trace blocks against named files/functions.
- [ ] Cross-references searched for missed hooks.
- [ ] Findings checked against current RSSET packet shape.
- [ ] Proposal updated if replay rules change the protocol.
- [ ] Next issue scope follows from the replay projection.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Protocol delta implemented as described, or proposal updated.
- [ ] Default behavior impact verified.
- [ ] Old code deleted, or deferred deletion blocker recorded.
- [ ] Replay projection tested.
- [ ] C fact mutation explicitly absent or deferred.
- [ ] Command gate refuses unsafe mutation.
- [ ] Render/verifier/round-trip checked where output-affecting, or explicitly
  not applicable because no output changed.
- [ ] Pandora proof recorded.
- [ ] Post-commit review found no unresolved worthwhile findings.
