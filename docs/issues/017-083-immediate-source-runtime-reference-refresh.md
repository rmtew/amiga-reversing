# 017-083: Immediate Source/Runtime Reference Refresh

Status: active
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

- [ ] `017-079` closeout checked before work.
- [ ] Current immediate-reference report rerun.
- [ ] Candidates classified by address semantics.
- [ ] Ambiguous and unsafe interpretations fail closed.
- [ ] Reuse opportunity with callback address-provenance logic identified.
- [ ] Any safe candidate processed through existing gates or deferred to a new implementation issue.
- [ ] No callback mutation, 012/018/Mac/platform-format files touched.

## Research Review

- [ ] Work does not count report-only source-offset hints as source progress.
- [ ] Any code change improves reusable address-provenance/report behavior.
- [ ] If no mutation occurs, blockers are structured and current.
- [ ] Proposal 017 living notes updated.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] `017-079` checked before work.
- [ ] Real Pandora immediate-reference report rerun.
- [ ] Focused tests pass if code changed.
- [ ] Exact round-trip passes for any source change.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

