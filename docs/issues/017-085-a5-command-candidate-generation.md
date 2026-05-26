# 017-085: Generate A5 Hardware Command Candidates

Status: completed
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Dependency: none. This is the first active A5 implementation issue.
- Protocol area: turning accepted A5 path/lifetime evidence into actionable command candidates.
- Current proposal state: current Pandora A5 report has `525` uses, `20` accepted custom-base uses, verifier support, and `command_candidate_count=0`.
- Desired proposal state after this issue: accepted A5 custom-base uses produce fail-closed `a5_hardware_ref.interpret` command candidates with enough identity and evidence to support later Decision Journal acceptance.

## Protocol Delta

- Adds: command-candidate generation for A5 hardware references that already have accepted path/lifetime evidence.
- Changes: A5 report output must distinguish actionable accepted-use candidates from unknown/report-only uses.
- Replaces: the current blocked state where accepted A5 evidence cannot produce any command candidate.
- Leaves out of scope: rendering changes, Decision Journal writes, source output mutation, target metadata mutation, 012/018, Mac OS support, and Mac targets.

## Default Behavior

- Generate candidates only from accepted custom-base/path-lifetime evidence.
- Unknown A5 uses must remain non-actionable and keep their existing blockers.
- Candidate identity must be stable across report reruns and include target id, row key/source offset, operand index, register, displacement, custom-base offset, hardware register offset, and parent evidence id.
- Ambiguous or missing hardware-register knowledge must fail closed.

## Pandora Proof

- Target: `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.
- Starting fact: A5 report currently exposes `20` accepted custom-base uses and `0` command candidates.
- Expected result: the report exposes command candidates for accepted A5 uses only, while all unknown uses remain blocked.
- No source output or Decision Journal file should change in this issue.

## Implementation Slice

- C fact graph/query work: expose any missing listing/effective-metadata fields needed to identify accepted A5 use sites cleanly.
- Python/API/report work: add command-candidate generation to the A5 report path.
- Journal/replay work: unchanged.
- Renderer/verifier work: unchanged except for reporting candidate verifier requirements.
- Tests: fixture tests for accepted-use candidates, unknown-use non-candidates, ambiguous hardware-register failures, and stable identity.

## Research Coverage

- [x] Current A5 report shape checked before implementation.
- [x] Existing accepted custom-base evidence semantics understood.
- [x] Candidate identity includes source location, operand, register, displacement, hardware offset, and parent evidence.
- [x] Unknown uses remain blocked and are not promoted.
- [x] Ambiguous/missing register knowledge fails closed.
- [x] No 012/018/Mac/platform-format files touched.

## Research Review

- [x] This performs code implementation, not a report-only closeout.
- [x] Candidate generation is based on accepted evidence, not heuristic confidence alone.
- [x] The report explains why every non-candidate remains blocked.
- [x] Proposal 017 living notes updated with the implementation result.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] Focused A5 report tests pass.
- [x] Real Pandora A5 report shows nonzero command candidates for accepted uses.
- [x] Real Pandora unknown A5 uses remain non-actionable.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

- `a5-hardware-report` on the real Pandora target now reports `accepted_custom_base_evidence_count=20`, `command_candidate_count=20`, and `unknown=505`.
- Focused tests passed: `tests/test_reversing_loop.py -q -k "a5_decision or a5_hardware_lifetime_report or a5_path_lifetime_packet or query_a5_path_lifetime_packet or a5_hardware_ref_verifier"`.
