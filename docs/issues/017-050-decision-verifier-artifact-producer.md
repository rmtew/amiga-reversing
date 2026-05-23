# 017-050: Decision Verifier Artifact Producer

Status: completed

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

- [x] Current `017-049` audit and artifact ingestion behavior checked.
- [x] Existing generated-source verifier path checked.
- [x] Existing exact round-trip verifier path checked.
- [x] Current source-state identity source checked.
- [x] Negative-safety cases for the selected RSSET binding defined.
- [x] No-append/no-mutation behavior checked.
- [x] Target hygiene behavior for `decision_verifier_artifacts.json` checked.

## Research Review

- [x] Second pass checked trace blocks against named files/functions.
- [x] Cross-references searched for existing verifier artifact or report hooks.
- [x] Artifact freshness and selected-identity mismatch risks reviewed.
- [x] Proposal updated with model corrections or deferred follow-ups.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Protocol delta implemented as described, or proposal updated.
- [x] Default behavior impact verified.
- [x] Old code deleted, or deferred deletion blocker recorded.
- [x] Artifact producer success tested.
- [x] Stale/mismatched artifact rejection tested through audit ingestion.
- [x] Verifier failure/blocker behavior tested.
- [x] No append/no mutation behavior tested.
- [x] Pandora proof recorded.
- [x] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

- Added explicit API/CLI surface:
  `produce_decision_verifier_artifact(...)` and
  `reversing_loop decision-verifier-artifact --target ... --decision-id ...
  [--write]`.
- The producer is read-only by default and writes only
  `decision_verifier_artifacts.json` when `--write` is supplied. It does not
  append to `decision_journal.jsonl` or `manual_actions.jsonl`.
- Produced artifacts are current only after matching the active accepted
  Decision Journal record, current RSSET candidate identity, current
  source-state projection hash, reloaded semantic binding state, scoped
  generated-source render verifier, negative-safety verifier, and exact
  round-trip verifier.
- Failure cases return `status=blocked` and do not write artifacts. Covered:
  missing source-state identity, selected-identity mismatch, verifier failure,
  stale/mismatched ingestion, and no-append/no-mutation behavior.
- Real Pandora proof:
  - Before production, `decision-rsset-022e-accept-017-040` reported
    `generated_source`, `negative_safety`, and `exact_round_trip` as
    `not_checked` with explicit blockers.
  - Explicit producer write emitted
    `decision-verifier:decision-rsset-022e-accept-017-040:rsset-raw-a6:022E:490e27369b0c`
    with all three verifier layers passed.
  - After production, `decision-journal-report` reported
    `decision_journal`, `semantic_reload`, `generated_source`,
    `negative_safety`, and `exact_round_trip` as `passed` with no blockers.
  - `git diff -- decision_journal.jsonl manual_actions.jsonl
    pandora_3e1ee0f1_bk_00_000000e8.s` was empty for the target proof.
- Tests run: `uv run python -m pytest tests\test_reversing_loop.py -q`
  (`360 passed`).
- Deferred blockers: none.
