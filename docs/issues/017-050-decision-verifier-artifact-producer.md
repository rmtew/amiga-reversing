# 017-050: Decision Verifier Artifact Producer

Status: active

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: Decision Journal audit verifier-layer evidence
- Blocked by: `017-049`
- Current proposal state: `017-049` can ingest
  `decision_verifier_artifacts.json` and keeps generated-source,
  negative-safety, and exact-round-trip layers blocked when no current artifact
  exists. The real Pandora RSSET audit still reports those layers as
  `not_checked`.
- Desired proposal state after this issue: the selected Pandora RSSET decision
  can produce or emit a current verifier artifact for the existing accepted
  journal decision, and the Decision Journal audit can consume that artifact so
  every required verifier layer is backed by current evidence.

## Protocol Delta

- Adds: a producer path for current Decision Journal verifier artifacts.
- Changes: supported accepted decisions can move from artifact ingestion only to
  a complete evidence chain: decision, semantic reload, generated source,
  negative safety, and exact round-trip.
- Replaces: manual or prose-only proof that verifier layers passed.
- Deletes: any temporary fixture-only artifact assumptions that become
  redundant.
- Leaves out of scope: new source mutations, new accepted decisions, broad
  Pandora mutation sweeps, UI, and support for unrelated candidate families.

## Default Behavior

- Default inspection and packet queries must remain read-only.
- Artifact production must be explicit. It must not run as an implicit side
  effect of `decision-journal-report`.
- The producer must not append to the Decision Journal or Manual Action Log.
- The producer must not mark any layer `passed` unless the current target state
  matches the selected decision identity and source-state identity.
- If any verifier cannot run or cannot prove scope, the artifact must either be
  omitted or carry a non-passed layer with a named blocker.

## Evidence Contract

For the real Pandora RSSET decision
`decision-rsset-022e-accept-017-040`, the produced artifact must identify:

- target id
  `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`;
- decision id `decision-rsset-022e-accept-017-040`;
- candidate id `rsset-raw-a6:022E`;
- selected identity `s0:000006E4:op1`;
- current source-state identity from the same source projection used by packet
  and audit matching;
- generated-source verifier result for only the selected RSSET binding;
- negative-safety result proving no unintended same-family or nearby source
  effects were introduced;
- exact round-trip result for the current target state.

The artifact must be acceptable to the `017-049` ingestion checks without
relaxing those checks.

## Pandora Proof

Use the already-mutated selected Pandora RSSET binding from `017-039` and the
accepted journal decision from `017-040`.

The proof must show:

- before artifact production, `decision-journal-report` reports
  generated-source, negative-safety, and exact-round-trip as `not_checked` with
  explicit blockers;
- artifact production emits or writes one current artifact for the selected
  decision;
- after artifact production, `decision-journal-report` reports
  `decision_journal`, `semantic_reload`, `generated_source`,
  `negative_safety`, and `exact_round_trip` as `passed`;
- no new Decision Journal record, Manual Action Log record, or source mutation
  is created by this issue.

## Implementation Slice

- C fact graph/query work: add only narrow current-source identity or scoped
  source-effect queries if existing report data cannot prove freshness/scope.
- Python/API/report work: add an explicit command or API helper that produces
  the verifier artifact for a selected accepted decision.
- Journal/replay work: consume existing projection only; do not change append or
  replay semantics.
- Renderer/verifier work: reuse current generated-source and exact round-trip
  verification paths, and add the narrow negative-safety check needed for the
  selected RSSET binding.
- Tests/proof: artifact producer success, stale source-state rejection,
  selected-identity mismatch rejection, verifier failure/blocker output,
  no-append/no-mutation behavior, and real Pandora proof.

## Research Completion Standard

Record trace blocks for the current `017-049` audit output, existing
generated-source verifier path, exact round-trip path, current source-state
identity source, Manual Action Log/no-append behavior, target hygiene handling
for `decision_verifier_artifacts.json`, and the proposed artifact command/API
surface.

## Research Coverage

- [ ] Current `017-049` audit and artifact ingestion behavior checked.
- [ ] Existing generated-source verifier path checked.
- [ ] Existing exact round-trip verifier path checked.
- [ ] Current source-state identity source checked.
- [ ] Negative-safety cases for the selected RSSET binding defined.
- [ ] No-append/no-mutation behavior checked.
- [ ] Target hygiene behavior for `decision_verifier_artifacts.json` checked.

## Research Review

- [ ] Second pass checked trace blocks against named files/functions.
- [ ] Cross-references searched for existing verifier artifact or report hooks.
- [ ] Artifact freshness and selected-identity mismatch risks reviewed.
- [ ] Proposal updated with model corrections or deferred follow-ups.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Protocol delta implemented as described, or proposal updated.
- [ ] Default behavior impact verified.
- [ ] Old code deleted, or deferred deletion blocker recorded.
- [ ] Artifact producer success tested.
- [ ] Stale/mismatched artifact rejection tested through audit ingestion.
- [ ] Verifier failure/blocker behavior tested.
- [ ] No append/no mutation behavior tested.
- [ ] Pandora proof recorded.
- [ ] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

Fill this section when completed with the artifact producer surface, verifier
layers proven, Pandora commands run, tests, and any deferred blockers.
