# 017-092: Convert A5 To Lifetime Parent Fact Cascade

Status: active
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

- [ ] `017-089` review failure accounted for.
- [ ] Lifetime parent fact identity is stable.
- [ ] Derived children carry parent fact id and rule id.
- [ ] Unsafe uses remain blocked with reasons.
- [ ] Legacy manual state does not satisfy "new source progress".
- [ ] No 012/018/Mac/platform-format files touched.

## Research Review

- [ ] This is A5 cascade work, not selected-operand mutation.
- [ ] The real Pandora proof shows multiple derived effects or honestly blocks.
- [ ] The implementation does not add backwards-compatibility debt beyond documented transitional handling.
- [ ] Proposal 017 living notes updated.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] `017-091` complete.
- [ ] Focused A5 cascade tests pass.
- [ ] Real Pandora A5 cascade report produced.
- [ ] Exact round-trip passes for any source output change.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

