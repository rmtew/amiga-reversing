# 017-061: Callback Target Data/Code Classification Proof

Status: completed
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

- [x] Current callback report rerun for Pandora.
- [x] Current review items inspected for both target rows.
- [x] Current orphan/code-island or data-range packet inspected where applicable.
- [x] Xrefs and control-flow reachability checked.
- [x] Overlap/range classification checked.
- [x] Each row classified as code, data, table, or ambiguous/deferred with reason.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] Confirmed `unreconciled_data_range` was not treated as code without proof.
- [x] Confirmed no mutation path was exposed.
- [x] Confirmed no source, Manual Action Log, Decision Journal, verifier artifact, generated output, or target metadata was modified.
- [x] Proposal 017 living notes updated.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] 017-056 completion evidence used as the starting point.
- [x] Output remains read-only.
- [x] Any support-code change is tied to a concrete read-only correctness blocker.
- [x] Focused tests pass if code changes.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

Pandora target:
`amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.

Read-only evidence commands:

- `uv run python -m amiga_reversing.reversing_loop callback-report --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`
- Read-only live project review-item/candidate inspection after listing open.

Current callback report rows:

| Store | Target row | Bytes/rendered data | Review item | Classification |
| --- | --- | --- | --- | --- |
| `s0:00000542:instruction:350` (`app_027C`) | `s0:0000076E:data:493` | `dc.b $08,$88,$06,$66`; range continues with nonzero byte data through `s0:0000078E` | `unreconciled_data_range:h0:$0000076e-$0000078e` | ambiguous/deferred, not code-accepted |
| `s0:00000D4E:instruction:909` (`app_027C`) | `s0:00000AC8:data:743` | `dcb.b $20,$00`; range contains zero-fill plus small nonzero data at `s0:00000AE8`; target starts at the zero-fill head | `unreconciled_data_range:h0:$00000ac8-$00000ba8` | data-like/deferred, not code-accepted |

Review-item/candidate evidence:

- Both review items are `unreconciled_data_range`, low confidence, source
  `analysis`, and message `Range has no accepted code, data, metadata, policy,
  or manual seed evidence`.
- Candidate extraction reports `has_xrefs=false`, no `orphan_code_score`,
  `actionable=false`, and stop reason `candidate lacks locator, xref evidence,
  or verifier`.
- Current callback report shows stores into `app_027C`, but the filtered
  `app_027C` report has no indirect consumer. The store evidence alone is not
  durable inbound control-flow reachability.
- No current packet/report surface provides explicit empty conflicts,
  accepted code range proof, render support, or exact verifier gates for either
  row.

Classification result:

- `s0:0000076E`: ambiguous/deferred. It is a nonzero data-range head and has
  callback-store evidence, but no xrefs, no indirect consumer, no orphan-code
  signal, and no verifier-backed code classification. Do not treat as code.
- `s0:00000AC8`: data-like/deferred. It is zero-fill at the target start
  inside a larger unreconciled data range; all-zero bytes are a false-positive
  risk for code promotion. Do not treat as code.

Next safe path: if this family is pursued later, create a read-only
classification issue that adds durable callback-consumer/control-flow evidence
and false-positive checks before any code seed command is allowed. This issue
does not expose a mutation path.

No code changed, so no focused tests were required beyond issue validation and
diff checks.
