# 017-061: Callback Target Data/Code Classification Proof

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: data/code classification for callback targets.
- Current proposal state: 017-056 found 2 callback missed-code-target assignments where matching review items exist, but they are `unreconciled_data_range`, not code classification items.
- Desired proposal state after this issue: each target row has a read-only classification proof or an explicit ambiguous/deferred blocker.

## Protocol Delta

- Adds: read-only data/code classification evidence for two callback target rows.
- Changes: Proposal 017 living notes with classification result and next safe path.
- Replaces: no protocol model.
- Deletes: nothing.
- Leaves out of scope: mutation, source edits, Manual Action Log writes, Decision Journal writes, verifier artifact writes, generated output, target metadata, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Unchanged, v2 internal only: `unreconciled_data_range` items remain non-code until proven otherwise.
- Switched surface to v2: none.
- Deleted old surface path: none.
- User-visible behavior: no callback code seed/mutation command may become enabled.

## Pandora Proof

- Target candidates:
  - `app_027C` store `s0:00000542` to target row `s0:0000076E:data:493`
  - `app_027C` store `s0:00000D4E` to target row `s0:00000AC8:data:743`
- Evidence packet expected: target row bytes/decoded view if available, xrefs, callback-store evidence, current data-range review item, control-flow reachability, overlap/range classification, false-positive checks, and classification result.
- Decision behavior: no accept/defer/reject write; document proof or blocker only.
- Command gate behavior: callback seed command remains blocked unless a later issue creates a real code-classification review item with verifier gates.
- Render effect: none.
- Verifier/round-trip: no output-affecting verification unless support code changes.

## Implementation Slice

- C fact graph/query work: none unless current read-only range/xref evidence is incomplete for classification.
- Python/API/report work: inspect review item, row, xref, and orphan/data-range packet surfaces; add read-only diagnostic fields only if needed.
- Journal/replay work: none.
- Renderer/verifier work: none.
- Tests: focused read-only packet/report tests if output shape changes.

## Research Coverage

- [ ] Current callback report rerun for Pandora.
- [ ] Current review items inspected for both target rows.
- [ ] Current orphan/code-island or data-range packet inspected where applicable.
- [ ] Xrefs and control-flow reachability checked.
- [ ] Overlap/range classification checked.
- [ ] Each row classified as code, data, table, or ambiguous/deferred with reason.
- [ ] No 012/018/Mac/platform-format files touched.

## Research Review

- [ ] Confirmed `unreconciled_data_range` was not treated as code without proof.
- [ ] Confirmed no mutation path was exposed.
- [ ] Confirmed no source, Manual Action Log, Decision Journal, verifier artifact, generated output, or target metadata was modified.
- [ ] Proposal 017 living notes updated.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] 017-056 completion evidence used as the starting point.
- [ ] Output remains read-only.
- [ ] Any support-code change is tied to a concrete read-only correctness blocker.
- [ ] Focused tests pass if code changes.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.
