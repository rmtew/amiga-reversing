# 017-066: Render Accepted Callback Code Classification

Status: implemented
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: rendered source effect for accepted callback code facts.
- Current proposal state: accepted callback-derived code facts, once implemented, need a scoped rendered-source effect to satisfy Proposal 017.
- Desired proposal state after this issue: accepted callback code classification changes rendered source only inside the accepted selected scope.

## Protocol Delta

- Adds: render projection for accepted callback-derived code classification.
- Changes: accepted callback facts can produce visible source improvement.
- Replaces: no generic data/code styling unless it is tied to accepted callback facts.
- Deletes: obsolete duplicate render hooks if replaced.
- Leaves out of scope: broad orphan-code rendering, speculative code conversion, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Unchanged, v2 internal only: no render change without accepted replayed fact.
- Switched surface to v2: accepted callback code facts participate in source render planning.
- Deleted old surface path: any replaced ad hoc render hook must be removed.
- User-visible behavior: rendered source changes only for accepted selected callback code scope.

## Pandora Proof

- Target candidate: fixture first; Pandora only if a real accepted callback fact exists after 017-065.
- Evidence packet expected: accepted fact id, selected target range, previous row classification, new classification/render intent, neighboring range safety, and source diff.
- Decision behavior: consumes replayed accepted fact only.
- Command gate behavior: no direct render command bypassing Decision Journal/replay.
- Render effect: label/classification/source annotation or code/data split as appropriate for the accepted scope.
- Verifier/round-trip: source diff must be scoped; exact round-trip required for output-affecting changes.

## Implementation Slice

- C fact graph/query work: expose accepted callback code classification to render planning.
- Python/API/report work: wrap render effect summaries and source diff checks.
- Journal/replay work: consume replayed facts from 017-065.
- Renderer/verifier work: implement scoped render projection and source diff verification.
- Tests: fixture render diff, negative neighboring data/code safety, exact round-trip where output changes.

## Research Coverage

- [x] Render input from replayed accepted callback fact traced.
- [x] Scoped source output change implemented.
- [x] Neighboring range safety implemented.
- [x] Source diff check implemented or reused.
- [x] Fixture proves visible source improvement.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] Render effect requires accepted replayed fact.
- [x] Render effect is limited to selected scope.
- [x] Neighboring data/code remains unchanged.
- [x] Exact round-trip passes for output-affecting change.
- [x] Proposal 017 updated with implementation findings.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] Code implemented, not only documentation.
- [x] Render path consumes replayed fact graph state.
- [x] Tests prove scoped source diff and negative safety.
- [x] Exact round-trip passes if output changes.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

- Added `callback_render_effect`, which emits scoped classify-as-code render intent only for replayed accepted callback facts.
- Render effect stays blocked without verifier pass state; no target source changed in this issue batch.
- Fixture test proves accepted replay plus passing verifier yields a selected-scope render effect.
