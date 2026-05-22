# 017-036: Decision Replay Projection Model

Status: active

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: replayable Decision Journal semantics
- Blocked by: `017-034`, `017-035`
- Current proposal state: Decision Journal records are durable, inspectable,
  and dry-run-validatable through `decision-journal-report`, but not projected
  into active decision state.
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
- Projection helper name: add `project_decision_journal(records)` in the
  Decision Journal module, or update this issue before implementation if a
  better local name is required by code evidence.
- CLI/API exposure: extend explicit `decision-journal-report` output with a
  `projection` object. Do not add a second command unless implementation
  evidence proves that is cleaner and the proposal is updated.

## Projection Contract

The projection is an in-memory summary derived only from a valid current
journal. Invalid records and invalid journals must not produce active accepted
facts. The output should include:

- `valid`: whether projection was produced from a valid journal.
- `diagnostics`: projection-specific diagnostics, plus journal validation
  blockers when projection cannot be produced.
- `accepted_facts`: active `accept_fact` decisions that are not superseded.
- `deferred_facts`: active `defer_fact` decisions that are not superseded.
- `rejected_facts`: active `reject_fact` decisions that are not superseded.
- `superseded_decision_ids`: decision ids hidden by supersession.
- `active_decision_ids`: non-superseded decision ids considered by projection.
- `by_candidate_id`: grouped active accepted/deferred/rejected decisions by
  `candidate_id`.
- `by_selected_identity`: grouped active accepted/deferred/rejected decisions by
  a stable selected-identity key.

Projection rules:

- The input journal must be valid under `validate_decision_journal_records`.
- `supersede_decision` removes the superseded decision id from active
  accepted/deferred/rejected buckets.
- `replacement_decision_id`, when present, is informational only in this issue;
  it does not make a forward reference active.
- `accept_fact` entries become active accepted facts only when their own record
  validates and they are not superseded.
- `defer_fact` and `reject_fact` entries remain active blockers/negative
  decisions only when their own record validates and they are not superseded.
- Unknown or malformed records remain diagnostics only and cannot affect active
  projection.
- Projection never calls C analysis, Manual Action Log projection, command
  catalog, renderer, verifier, or append helpers.

## Pandora Proof

- Target candidate: RSSET packet candidate `rsset-raw-a6:022E` at
  `s0:000006E4`.
- Evidence expected: `decision-journal-report` can show whether a selected-use
  RSSET app-base decision is accepted, deferred, rejected, or superseded in the
  projection.
- Decision behavior: accepted facts become active only in the replay
  projection; deferred/rejected decisions remain inspectable blockers.
- Command gate behavior: gate remains blocked because the projection is not yet
  consumed by RSSET mutation.
- Render effect: none.
- Verifier/round-trip: no output-affecting verification required.

## Implementation Slice

- C fact graph/query work: none unless implementation evidence proves a small
  read-only type boundary is needed and the proposal is updated first.
- Python/API/report work: expose replay projection through
  `decision-journal-report` only.
- Journal/replay work: active decision selection, supersession handling,
  conflict preservation, candidate/selected-identity grouping, and
  invalid-record exclusion.
- Renderer/verifier work: none.
- Tests: active accept projection, defer/reject projection, supersession,
  duplicate/invalid exclusion, malformed journal projection block,
  deterministic ordering/grouping, CLI projection JSON output, and no target
  mutation.

## Research Completion Standard

Record trace blocks for journal validation, packet identity, current report
accepted-evidence logic, existing Manual Action Log projection, command-gate
inputs, and any existing projection/state model that could conflict with
replay.

## Research Coverage

- [ ] Decision Journal IO and validation surfaces checked.
- [ ] Current RSSET accepted-evidence classification checked.
- [ ] Existing Manual Action Log projection checked for replacement boundary.
- [ ] Current command-gate inputs checked to prove projection is not consumed
  yet.
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
- [ ] `decision-journal-report` projection output tested.
- [ ] C fact mutation explicitly absent or deferred.
- [ ] Command gate refuses unsafe mutation.
- [ ] Render/verifier/round-trip checked where output-affecting, or explicitly
  not applicable because no output changed.
- [ ] Pandora proof recorded.
- [ ] Post-commit review found no unresolved worthwhile findings.
