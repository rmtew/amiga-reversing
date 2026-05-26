# 017-092: Convert A5 To Lifetime Parent Fact Cascade

Status: completed
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Dependency: `017-091` must be complete first.
- Protocol area: A5 custom-base lifetime facts and derived hardware-register children.
- Current proposal state: A5 supports selected operand decisions, but `017-089` proved that is the wrong unit.
- Desired proposal state after this issue: accepting a bounded A5 custom-base lifetime derives every safe A5 hardware-register reference inside that lifetime and blocks unsafe uses with reasons.

## Protocol Delta

- Adds: `a5_custom_base_lifetime` parent fact and derived `a5_hardware_ref` children.
- Changes: A5 source progress comes from lifetime cascade, not one selected operand.
- Replaces: single selected A5 operand as the primary accepted fact.
- Leaves out of scope: bulk real-target acceptance without verifier, RSSET/immediate/callback rules, 012/018, Mac OS support, and Mac targets.

## Default Behavior

- A5 lifetime scope must be bounded by CFG/path proof, definitions, clobbers, calls, returns, save/restore, and unknown control flow.
- All safe A5 displacement uses inside the accepted lifetime become derived children.
- Uses outside the lifetime or past blockers must remain unchanged and report why.
- Existing Manual Action Log A5 refs must be treated as legacy state and must not be mistaken for new Decision Journal source progress.

## Pandora Proof

- Target: `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.
- Use a real A5 lifetime that has multiple safe derived hardware-register refs.
- Expected result: one accepted lifetime parent fact derives multiple children, including at least one child that was not already represented by legacy manual state if such a candidate exists; otherwise the issue must block and state the exact missing condition rather than claiming source progress.

## Implementation Slice

- C fact graph/query work: model lifetime parent and derived children in the cascade state.
- Python/API/report work: expose A5 lifetime packets and derived child summaries.
- Journal/replay work: accept/defer/reject lifetime parent facts, not only selected operand facts.
- Renderer/verifier work: render derived children through normal source output when verifier-safe.
- Tests: bounded lifetime derivation, clobber stop, branch/return stop, legacy manual-state non-progress detection, multiple derived children.

## Research Coverage

- [x] `017-089` review failure accounted for.
- [x] Lifetime parent fact identity is stable.
- [x] Derived children carry parent fact id and rule id.
- [x] Unsafe uses remain blocked with reasons.
- [x] Legacy manual state does not satisfy "new source progress".
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] This is A5 cascade work, not selected-operand mutation.
- [x] The real Pandora proof shows multiple derived effects or honestly blocks.
- [x] The implementation does not add backwards-compatibility debt beyond documented transitional handling.
- [x] Proposal 017 living notes updated.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] `017-091` complete.
- [x] Focused A5 cascade tests pass.
- [x] Real Pandora A5 cascade report produced.
- [x] Exact round-trip passes for any source output change.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

- Implemented `a5_custom_base_lifetime` parent fact construction in `inspect_cascade_state()`.
- Implemented `a5.lifetime.hardware_refs.v1` derivation so one lifetime parent derives all safe `a5_hardware_ref` children from the grouped lifetime payload.
- Unsafe A5 uses remain blocked with original report blockers such as `call before selected use may clobber A5`, `branch before selected use requires full CFG path proof`, and `return before selected use breaks local path proof`.
- Focused test: `test_cascade_report_derives_a5_lifetime_children_and_marks_legacy_non_progress`.
- Real Pandora cascade report produced by `uv run python -m amiga_reversing.reversing_loop cascade-report --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8 --listing-timeout-seconds 10`.

## Cascade Evidence

- Real Pandora summary: 11 parent facts, 22 derived facts, 817 blocked children, 12 exhausted facts, 312 review packets, fixed point reached after 2 iterations.
- A5 lane derives multiple children; real Pandora render effects show 20 `already_represented` A5 children and no false source progress claim for legacy Manual Action Log state.
- One non-legacy render effect remains `pending_baseline_delta_verifier`, so it is not written as source output.
- Baseline-delta verifier proof: already-represented children record baseline/effective state as already containing the effect; pending children carry `missing_baseline_without_parent_render`.
- Exact round-trip: no output-affecting source change was applied by this issue, so no rebuilt bytes changed.
- Not report-only: this issue added A5 parent/child cascade code and focused tests.
