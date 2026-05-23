# 017-055: Pandora Read-Only Evidence Discovery Pass

Status: active

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: post-baseline evidence discovery after `017-054`.
- Current proposal state: `017-054` found no useful unblocked Pandora mutation
  candidate from the existing candidate queue or known packet lanes.
- Desired proposal state after this issue: a fresh, focused Pandora read-only
  discovery pass either finds a new durable candidate with exact mutation gates,
  or confirms that 017 should remain paused without touching 012/018.

## Protocol Delta

- Adds: one final 017-side discovery pass that searches current Pandora analysis
  outputs for new evidence packets instead of relying only on `candidate_work=[]`.
- Changes: 017 may resume only if this pass finds durable evidence that can be
  turned into a source-quality improvement with command support, verifier
  support, and exact round-trip.
- Replaces: treating the absence of default candidate work as proof that no
  focused read-only discovery is possible.
- Deletes: none.
- Leaves out of scope: broad target mutation runs, cosmetic label cleanup,
  generic label renaming, stale tracked `.s` edits, and 012/018 files.

## Default Behavior

- This issue is read-only unless it creates a follow-up issue for a separately
  scoped mutation.
- Do not write source, Manual Action Log, Decision Journal, verifier artifacts,
  generated output, metadata, or tracked Pandora `.s` during discovery.
- Do not rename generic labels or classify data from human preference alone.
- If a candidate lacks durable provenance, command support, verifier support, or
  exact round-trip, record the blocker and leave it deferred/report-only.

## Discovery Actions

- Reproduce current Pandora `inspect` state and confirm the baseline still has
  no default candidate work.
- Query available read-only reports beyond the already-known packet proofs:
  - callback-slot report
  - immediate-runtime-reference report
  - A5 hardware lifetime report
  - RSSET candidate report
  - orphan/code-island/data-range packet/report surfaces that are available
- For each surfaced item, classify it into one of:
  - already accepted/source-effective
  - already deferred/read-only
  - report-only/ambiguous
  - blocked by missing command support
  - blocked by missing verifier support
  - safe follow-up candidate
- A safe follow-up candidate must include:
  - durable selected identity
  - xref/path/lifetime/source-quality evidence
  - exact command/API surface needed
  - verifier layers needed
  - expected visible source improvement
  - exact round-trip availability

## Research Coverage

- [ ] Current Pandora inspect state checked.
- [ ] Callback-slot report checked.
- [ ] Immediate-runtime-reference report checked.
- [ ] A5 hardware lifetime report checked.
- [ ] RSSET candidate report checked.
- [ ] Orphan/data-range surfaces checked where available.
- [ ] No file diffs from discovery checked.
- [ ] Follow-up candidate or pause conclusion recorded.

## Research Review

- [ ] Second pass checked that no cosmetic/stale-artifact mutation was selected.
- [ ] Candidate evidence classifications reviewed against the 017 protocol.
- [ ] Missing tooling/verifier blockers recorded if encountered.
- [ ] Proposal updated with the discovery result.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] Discovery commands and outputs summarized.
- [ ] No target or generated file mutation performed.
- [ ] Any follow-up issue contains exact gates and expected source improvement.
- [ ] If no follow-up exists, pause recommendation remains explicit.
- [ ] Post-commit review found no unresolved worthwhile findings.
