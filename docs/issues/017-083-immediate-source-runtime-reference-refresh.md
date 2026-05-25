# 017-083: Immediate Source/Runtime Reference Refresh

Status: complete
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Dependency: start after `017-079` callback lane closeout.
- Protocol area: refreshing immediate source/runtime reference evidence with the address-provenance lessons from callback work.
- Current proposal state: prior immediate-reference work left source-offset-looking candidates report-only unless accepted runtime-address provenance exists.
- Desired proposal state after this issue: current immediate candidates are separated into source offsets, runtime addresses, labels, constants, and unresolved values with provenance and source-safe command readiness where possible.

## Protocol Delta

- Adds: current immediate-reference refresh and address-provenance classification.
- Changes: immediate values should not stay in flat source-offset/report-only buckets when current metadata can distinguish address semantics.
- Replaces: stale immediate-reference conclusions from earlier 017 passes.
- Leaves out of scope: speculative source mutation, callback work, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- Ambiguous address interpretation must fail closed.
- Source offset, runtime address, label, and non-code constant interpretations must be distinct.
- If callback address-provenance logic is reusable, reuse it only through a clean shared path or create `017-084` dependency evidence.
- Any source change must use the existing immediate-reference command/verifier/round-trip gates.

## Pandora Proof

- Target: `amiga_disk_pandora-1988-firebird`
- Candidate source: current immediate-reference report.
- Evidence packet expected: strongest immediate candidates with literal width/syntax, address interpretation, source/runtime mapping, conflicts, command readiness, and blocker reason.

## Implementation Slice

- C fact graph/query work: expose row/runtime/source address facts if current immediate reports lack them.
- Python/API/report work: rerun and classify immediate-reference report; patch report output if address provenance is too weak.
- Journal/replay work: use existing immediate-reference decision/state path only if a candidate becomes safe.
- Renderer/verifier work: use generated-source and exact round-trip gates for any source effect.
- Tests: focused fixtures for source offset, runtime address, label, constant, ambiguous address, and unresolved immediate if code changes.

## Research Coverage

- [x] `017-079` closeout checked before work.
- [x] Current immediate-reference report rerun.
- [x] Candidates classified by address semantics.
- [x] Ambiguous and unsafe interpretations fail closed.
- [x] Reuse opportunity with callback address-provenance logic identified.
- [x] Any safe candidate processed through existing gates or deferred to a new implementation issue.
- [x] No callback mutation, 012/018/Mac/platform-format files touched.

## Research Review

- [x] Work does not count report-only source-offset hints as source progress.
- [x] Any code change improves reusable address-provenance/report behavior.
- [x] If no mutation occurs, blockers are structured and current.
- [x] Proposal 017 living notes updated.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] `017-079` checked before work.
- [x] Real Pandora immediate-reference report rerun.
- [x] Focused tests pass if code changed.
- [x] Exact round-trip passes for any source change.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

- Current report was rerun against the resolved Pandora listing target
  `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`;
  the disk/container target alone still has no listing.
- The resolved listing opened successfully. The immediate-reference report found
  `candidate_count=9`, `report_only_candidate_count=9`,
  `command_candidate_count=0`, `safe_to_mutate=false`, and mutation gate
  `status=blocked` with reason `remaining immediate reference candidates are
  report-only`.
- All current candidates are classified as `source_family=source_offset` with
  `write_policy.status=report_only`. No current runtime-address, label,
  constant, or ambiguity candidate is emitted by the report.
- The exact `017-057` candidate
  `immediate-runtime-ref:s0:000009A6:instruction:664:0:00001080`
  remains source-offset/report-only: `addi.w #4224,d1`, value `4224`,
  width `16`, target source offset `4224`, with reason `source-offset
  immediate matches are report-only until accepted runtime-address provenance
  exists`.
- Other current report-only source-offset candidates are at
  `s0:00006C48`, `s0:00006D96`, `s0:00007AD4`, `s0:00007B28`,
  `s0:00009302`, `s0:0003D7DE`, `s0:0004E544`, and `s0:0004E5EA`.
- No source progress is claimed from these report-only source-offset hints.
  Ambiguous or unsafe address interpretation remains fail-closed because no
  candidate has accepted runtime-address provenance.
- No code change or shared utility extraction is justified by this issue alone;
  it records the dependency outcome for `017-084`.
