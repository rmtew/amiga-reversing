# 017-037: RSSET Decision Evidence Flow

Status: planned

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: first packet-to-decision-to-gate evidence flow
- Blocked by: `017-036`
- Current proposal state: RSSET evidence packets and Decision Journal replay
  exist separately.
- Desired proposal state after this issue: the RSSET packet/gate can consult a
  replayed Decision Journal projection as accepted/deferred/rejected evidence
  without enabling mutation until all safe gates are satisfied.

## Protocol Delta

- Adds: RSSET evidence packet integration with replayed Decision Journal
  decisions.
- Changes: accepted RSSET app-base evidence can come from the replay
  projection instead of report-private/manual-state semantics.
- Replaces: report-private accepted RSSET evidence classification for the
  selected v2 slice only, if implementation evidence proves the replacement
  boundary is safe.
- Deletes: any replaced selected-slice report-private code, if cutover happens
  inside this issue.
- Leaves out of scope: broad RSSET migration, broad Pandora mutation run,
  rendering, UI.

## Default Behavior

- Default behavior changes only if the selected RSSET evidence surface cleanly
  cuts over to v2 with tests proving no regression.
- Otherwise the integration remains explicit/internal and mutation remains
  blocked.

## Pandora Proof

- Target candidate: RSSET packet candidate `rsset-raw-a6:022E` at
  `s0:000006E4`.
- Evidence expected: packet output shows whether accepted/deferred/rejected
  journal decisions satisfy or block app-base evidence.
- Decision behavior: journal accept can satisfy the accepted-base-evidence lane
  only when selected-use identity, path/lifetime scope, and empty conflicts are
  exact.
- Command gate behavior: mutation remains blocked unless all gates are present;
  missing scope/verifier gates must be named explicitly.
- Render effect: none unless a later gate issue is also completed.
- Verifier/round-trip: no output-affecting verification required.

## Implementation Slice

- C fact graph/query work: add only the minimum read/query boundary needed for
  RSSET gate evidence, or document why the selected slice remains Python-side.
- Python/API/report work: connect packet/gate evidence to replay projection for
  the selected RSSET candidate.
- Journal/replay work: consume accepted/deferred/rejected projection state.
- Renderer/verifier work: none.
- Tests: accepted exact selected-use decision, rejected/deferred blockers,
  mismatched identity rejection, non-empty conflicts rejection, missing
  path/lifetime scope rejection, and no unsafe mutation.

## Research Completion Standard

Record trace blocks for RSSET packet generation, replay projection, command
catalog gates, current report-private accepted-evidence paths, and the selected
Pandora candidate.

## Research Coverage

- [ ] RSSET packet and gate code checked.
- [ ] Decision replay projection checked.
- [ ] Command catalog gate logic checked.
- [ ] Report-private accepted-evidence logic checked for replacement boundary.
- [ ] Pandora selected-use identity and blocker evidence checked.

## Research Review

- [ ] Second pass checked trace blocks against named files/functions.
- [ ] Cross-references searched for missed hooks.
- [ ] Proposal updated if RSSET evidence flow changes the protocol.
- [ ] Next issue scope follows from the RSSET decision flow.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Protocol delta implemented as described, or proposal updated.
- [ ] Default behavior impact verified.
- [ ] Old code deleted, or deferred deletion blocker recorded.
- [ ] RSSET decision evidence flow tested.
- [ ] Command gate refuses unsafe mutation unless all gates are present.
- [ ] Render/verifier/round-trip checked where output-affecting, or explicitly
  not applicable because no output changed.
- [ ] Pandora proof recorded.
- [ ] Post-commit review found no unresolved worthwhile findings.
