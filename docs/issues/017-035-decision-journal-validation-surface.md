# 017-035: Decision Journal Validation Surface

Status: planned

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: explicit actor/tool interaction with Decision Journal records
- Blocked by: `017-034`
- Current proposal state: Decision Journal records can be validated in memory,
  and `017-034` is expected to make them durable target-local state.
- Desired proposal state after this issue: a human, LLM, CLI caller, or API
  caller can inspect and validate journal state without replaying or applying
  any decision.

## Protocol Delta

- Adds: explicit validation/inspection surface for the per-target Decision
  Journal.
- Changes: journal validity becomes queryable through a supported tool/API
  boundary instead of test-only helpers.
- Replaces: none.
- Deletes: none.
- Leaves out of scope: active replay, C fact mutation, RSSET bind command
  activation, rendering, UI.

## Default Behavior

- Existing default reports/planner/render/verifier behavior remains unchanged.
- The new surface must be explicit: no automatic planner use and no implicit
  mutation during target load.

## Pandora Proof

- Target candidate: RSSET packet candidate `rsset-raw-a6:022E` at
  `s0:000006E4`.
- Evidence expected: validation surface reports journal state, active decision
  IDs, superseded decision IDs, malformed records, and blocked mutation status.
- Decision behavior: dry-run validation can explain accept/defer/reject record
  validity without applying it.
- Command gate behavior: `rsset.binding.bind` remains blocked.
- Render effect: none.
- Verifier/round-trip: no output-affecting verification required.

## Implementation Slice

- C fact graph/query work: none.
- Python/API/report work: expose journal validation through the most appropriate
  existing internal command/API surface.
- Journal/replay work: validation/inspection only.
- Renderer/verifier work: none.
- Tests: focused coverage for valid journal report, invalid journal report,
  dry-run candidate record validation, and no default behavior change.

## Research Completion Standard

Record trace blocks for inspected command/API surfaces, journal IO helpers,
planner/default behavior paths, and any relevant Pandora proof commands.

## Research Coverage

- [ ] Existing reversing-loop command/API patterns checked.
- [ ] Journal IO from `017-034` checked.
- [ ] Planner/default report hooks searched to prove no accidental activation.
- [ ] Diagnostic shape checked for human/LLM/CLI usefulness.
- [ ] Pandora proof path defined and recorded.

## Research Review

- [ ] Second pass checked trace blocks against named files/functions.
- [ ] Cross-references searched for missed hooks.
- [ ] Proposal updated if the validation surface changes the protocol.
- [ ] Next issue scope follows from the validation surface.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Protocol delta implemented as described, or proposal updated.
- [ ] Default behavior impact verified.
- [ ] Old code deleted, or deferred deletion blocker recorded.
- [ ] Validation surface tested for valid/invalid journals.
- [ ] Decision/replay behavior explicitly deferred.
- [ ] Command gate refuses unsafe mutation.
- [ ] Render/verifier/round-trip checked where output-affecting, or explicitly
  not applicable because no output changed.
- [ ] Pandora proof recorded.
- [ ] Post-commit review found no unresolved worthwhile findings.
