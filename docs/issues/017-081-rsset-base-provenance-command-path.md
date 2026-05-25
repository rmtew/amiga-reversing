# 017-081: RSSET Base Provenance Command Path

Status: complete
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Dependency: start after `017-080` identifies a concrete RSSET base-evidence shape.
- Protocol area: implementing command/report/verifier support for RSSET base provenance if current evidence can justify it.
- Current proposal state: RSSET mutation is blocked until accepted app-base evidence can be represented and verified.
- Desired proposal state after this issue: the selected RSSET base-evidence shape either has a command-backed verifier path or is blocked with fixture proof explaining why it cannot be safely accepted.

## Protocol Delta

- Adds: RSSET base provenance command path, if justified by `017-080`.
- Changes: accepted base evidence must be durable, replayable, verifier-backed, and source-effective before it can affect rendering.
- Replaces: manual or report-only RSSET base assumptions.
- Leaves out of scope: broad RSSET refactors, callback work, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Unsafe base provenance must fail closed.
- Accepted evidence must use the Decision Journal or existing durable manual-state mechanism, whichever is already standard for this lane.
- A source-changing RSSET mutation requires generated-source effect and exact round-trip.
- If `017-080` finds no implementable evidence shape, this issue must be marked blocked or superseded with that reason instead of inventing one.

## Pandora Proof

- Target: `amiga_disk_pandora-1988-firebird`
- Selected candidate: from `017-080`, likely the strongest active RSSET group.
- Evidence packet expected: selected RSSET use path, base provenance, conflicts, command dry-run, durable decision/state replay, generated-source diff, verifier artifact, and exact round-trip if source changes.

## Implementation Slice

- C fact graph/query work: expose base provenance facts through normal analysis/export paths if Python cannot safely infer them.
- Python/API/report work: add or complete command dry-run/write path for accepted RSSET base evidence.
- Journal/replay work: accepted base evidence must replay into effective analysis state.
- Renderer/verifier work: add verifier artifact layers for semantic reload, generated-source effect, negative safety, and exact round-trip.
- Tests: fixture command tests, replay tests, verifier tests, and real Pandora dry-run/rerun.

## Research Coverage

- [x] `017-080` completion evidence checked before work.
- [x] Selected RSSET candidate and evidence shape named.
- [x] Command dry-run implemented or existing command verified.
- [x] Accepted state replays into report/effective analysis.
- [x] Generated-source effect tested when source change is expected.
- [x] Negative safety and exact round-trip gates enforced.
- [x] No callback, 012/018/Mac/platform-format files touched.

## Research Review

- [x] No helper-only path is closed as complete.
- [x] Any source effect comes through normal render/effective metadata paths.
- [x] If no source change occurs, the blocker is implemented and precise.
- [x] Proposal 017 living notes updated.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] `017-080` checked before work.
- [x] Focused command/replay/verifier tests pass.
- [x] Real Pandora RSSET rerun performed.
- [x] Exact round-trip passes for any source change.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

- `017-080` selected the already accepted RSSET candidate
  `rsset-raw-a6:022E` at `s0:000006E4:op1`.
- Current RSSET rerun reports the selected candidate as
  `evidence_search.status=accepted`, `journal_decision_evidence.status=accepted`,
  `journal_decision_evidence.accepted_count=1`,
  `command_support.bind.state=already_satisfied`, and
  `journal_mutation_gate.status=ready_for_mutation_issue`.
- The gate satisfied all required fields:
  `journal_accept`, `candidate_identity`, `selected_identity`, `fact_type`,
  `selected_use_scope`, `empty_conflicts`, `field_or_layout_refinement`,
  `render_support`, `generated_source_verifier`, and `exact_round_trip`.
- No new command implementation was needed in this issue. The existing
  Decision Journal path already records
  `decision-rsset-022e-accept-017-040` as active and source-effective.
- Current no-write verifier artifact for
  `decision-rsset-022e-accept-017-040` passed:
  `semantic_reload`, `generated_source`,
  `negative_safety`, and `exact_round_trip`.
- The generated-source verifier matched `app_022E` and no raw displacement
  token for the selected operand. Negative safety reported
  `same_decision_binding_count=1` and no unexpected same-displacement refs.
- Exact round-trip used the current `reproduction.json` and reported
  `status=exact`.
- No source, target metadata, Manual Action Log, Decision Journal write,
  verifier artifact write, generated output, 012, 018, Mac, or platform-format
  file was changed.
