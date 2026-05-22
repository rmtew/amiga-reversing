# 017-049: Decision Audit Verifier Artifact Ingestion

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: Decision Journal audit verifier-layer evidence
- Blocked by: `017-043`
- Current proposal state: `017-043` audit is conservative. It can match current
  packet/manual state, but generated-source and exact-round-trip layers remain
  `not_checked` with explicit blockers unless current verifier results are read
  or rerun.
- Desired proposal state after this issue: Decision Journal audit can report
  generated-source, negative-safety, semantic-reload, and exact-round-trip
  verifier layers from current verifier artifacts or live reruns, and keeps
  explicit blockers when those artifacts are unavailable.

## Protocol Delta

- Adds: verifier artifact ingestion for Decision Journal audit.
- Changes: audit verifier layers distinguish current passed, current failed,
  stale, unavailable, blocked, and not-applicable states from concrete verifier
  evidence.
- Replaces: `not_checked` blocker for supported decisions only when real current
  verifier evidence is available.
- Deletes: none unless temporary audit wording/helper code becomes redundant.
- Leaves out of scope: creating new source mutations, broad target sweeps, UI,
  and treating historical completion notes as current verifier artifacts.

## Default Behavior

- Audit remains read-only.
- Audit must not append to Decision Journal or Manual Action Log.
- Audit must not infer verifier success from fact type, manual state existence,
  issue text, or previous prose claims.
- Missing, stale, or mismatched verifier artifacts must remain explicit blockers.

## Evidence Contract

Verifier layer status may be `passed` only when the audit has current evidence
for the selected target and decision. The audit must check:

- selected decision id and selected identity;
- semantic reload/current packet match;
- generated-source verifier result for the selected scoped render effect;
- negative-safety verifier result for unrelated candidates/ranges;
- exact round-trip result for the current target state;
- artifact freshness or live rerun identity, including target and source state
  identity where available.

If any check cannot be performed, the layer must be `not_checked`, `blocked`, or
`unavailable` with a named blocker.

## Pandora Proof

- Use the real Pandora RSSET decision from `017-040` / binding from `017-039` as
  the first supported audit case.
- If current verifier artifacts are unavailable, either wire a live verifier
  rerun for this selected case or keep blockers and record what artifact support
  is missing.
- Do not mutate Pandora.

## Implementation Slice

- C fact graph/query work: none unless verifier freshness needs a narrow current
  state identity query.
- Python/API/report work: extend `decision-journal-report` audit to read or rerun
  verifier evidence for supported decisions.
- Journal/replay work: keep replay read-only; no append semantics change.
- Renderer/verifier work: reuse existing generated-source, negative-safety, and
  exact-round-trip verifiers where possible.
- Tests/proof: passed artifact/rerun case, missing artifact blocker, stale or
  mismatched artifact blocker, no append/no mutation, and Pandora proof.

## Research Completion Standard

Record trace blocks for current audit output, existing verifier functions,
artifact/state identity sources, exact round-trip path, no-append/no-mutation
behavior, and any artifact support deferred.

## Completion Evidence

- Added read-only ingestion of `decision_verifier_artifacts.json` for Decision
  Journal audit verifier layers.
- Layers can become `passed` only when artifact decision id, candidate id,
  selected identity, and `current=true` match the audited record.
- Missing artifacts keep explicit `generated_source_not_verified`,
  `negative_safety_not_verified`, and `exact_round_trip_not_verified` blockers.
- Stale/mismatched artifacts report explicit artifact blockers.
- Real Pandora RSSET audit remains conservative: semantic reload/current packet
  match is `passed`; generated-source, negative-safety, and exact round-trip are
  `not_checked` because no current verifier artifact was present.
- No mutation or append is performed by audit.

## Research Coverage

- [x] `017-043` audit output checked.
- [x] Existing generated-source verifier functions checked.
- [x] Existing negative-safety verifier support checked.
- [x] Exact round-trip verifier path checked.
- [x] Artifact/current-state identity sources checked.
- [x] No-append/no-mutation behavior checked.

## Research Review

- [x] Second pass checked trace blocks against named files/functions.
- [x] Cross-references searched for missed verifier/report hooks.
- [x] Historical prose/artifact inference risk reviewed.
- [x] Proposal updated with model corrections or deferred follow-ups.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Protocol delta implemented as described, or proposal updated.
- [x] Default behavior impact verified.
- [x] Old code deleted, or deferred deletion blocker recorded.
- [x] Verifier artifact/rerun behavior tested.
- [x] Missing/stale/mismatched blocker behavior tested.
- [x] No append/no mutation behavior tested.
- [x] Pandora proof recorded.
- [x] Post-commit review found no unresolved worthwhile findings.
