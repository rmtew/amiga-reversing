# 017-084: Shared Address Provenance Utility

Status: deferred
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Dependency: start only after at least one non-callback lane, preferably `017-080` or `017-083`, proves shared source-offset/runtime-address/label provenance is needed.
- Protocol area: extracting repeated address-provenance logic into a reusable analysis utility without speculative refactoring.
- Current proposal state: callback work introduced useful source-offset/runtime-address/label provenance, but it should not be generalized until another lane needs the same behavior.
- Desired proposal state after this issue: duplicated address-provenance code is replaced by a shared, tested utility only where reuse is proven by active 017 lanes.

## Protocol Delta

- Adds: shared address-provenance utility if justified by RSSET/immediate/A5 follow-up work.
- Changes: address semantics should be represented consistently across callback and non-callback lanes.
- Replaces: duplicated ad hoc source/runtime/label interpretation.
- Leaves out of scope: speculative framework rewrites, platform KB changes, callback behavior changes not needed for reuse, 012/018, Mac OS support, and Mac targets.

## Default Behavior

- Do not start this issue until a non-callback lane demonstrates the reuse need.
- Preserve callback behavior unless the migration is explicitly covered by tests.
- Ambiguous address interpretation must continue to fail closed.
- The utility must expose provenance, not just resolved integers.

## Pandora Proof

- Source lanes: selected outputs from `017-080`, `017-083`, or another non-callback 017 lane.
- Expected proof: at least two lanes use the same utility for source offset, runtime address, label, constant, ambiguous, and unresolved cases.
- Evidence packet expected: unchanged or improved report output with provenance preserved.

## Implementation Slice

- C fact graph/query work: if address provenance belongs in exported C-owned data, expose it there before Python utility extraction.
- Python/API/report work: extract shared utility and migrate only proven call sites.
- Journal/replay work: unchanged.
- Renderer/verifier work: unchanged unless migration affects source output, which should be avoided.
- Tests: utility unit tests plus regression tests for every migrated lane.

## Research Coverage

- [ ] Dependency evidence from `017-080`, `017-083`, or another non-callback lane checked.
- [ ] Reuse need demonstrated by at least two call sites.
- [ ] Shared utility preserves source offset, runtime address, label, constant, ambiguous, and unresolved cases.
- [ ] Callback behavior regression-tested if callback code is migrated.
- [ ] Non-callback lane behavior regression-tested.
- [ ] No 012/018/Mac/platform-format files touched unless explicitly required by the proven dependency.

## Research Review

- [ ] This is not speculative cleanup.
- [ ] The utility reduces duplication or prevents divergent address semantics.
- [ ] Existing source output remains stable unless a verifier-backed issue authorizes change.
- [ ] Proposal 017 living notes updated.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] Dependency issue evidence checked before work.
- [ ] Utility tests pass.
- [ ] Migrated lane tests pass.
- [ ] Exact round-trip passes for any source change.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

## Deferred Evidence

- Dependency evidence was checked after `017-080` and `017-083`.
- `017-080` selected RSSET `$022E`, but its current evidence is already carried
  by the RSSET report, Decision Journal projection, and no-write verifier
  artifact. It does not require source-offset/runtime-address/label provenance
  reuse from callback logic.
- `017-083` reran current immediate-reference evidence and found only nine
  `source_family=source_offset` report-only candidates, with zero command
  candidates and no accepted runtime-address provenance.
- No non-callback lane currently demonstrates two active call sites needing a
  shared source-offset/runtime-address/label provenance utility. Extracting one
  now would be speculative cleanup, which this issue explicitly forbids.
- This issue is deferred rather than completed. It should be reopened only when
  a non-callback lane has concrete duplicate provenance logic to migrate and
  tests for every migrated lane.
