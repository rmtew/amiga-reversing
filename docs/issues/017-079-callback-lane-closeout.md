# 017-079: Callback Lane Closeout

Status: active
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: closing the current Pandora callback lane honestly before switching to the next 017 source-progress lane.
- Current proposal state: `017-074` through `017-078` improved callback tooling but did not produce a safe source mutation. The current Pandora callback report has no actionable callback-derived code candidate.
- Desired proposal state after this issue: callback-lane progress and final blockers are summarized in one durable place, the current report is rerun, and the next 017 lanes are selected for code-bearing work.

## Protocol Delta

- Adds: callback lane closeout and next-lane selection.
- Changes: callback work stops being the default 017 path unless new evidence appears.
- Replaces: continuing to create callback follow-ups when current Pandora evidence is exhausted.
- Leaves out of scope: source mutation, new callback heuristics, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- No target state, Decision Journal, generated source, verifier artifact, or metadata write is allowed.
- The issue must summarize tooling progress, not redo implementation.
- The closeout must identify which next 017 lanes are ready for independent work.
- If the callback report unexpectedly produces an actionable candidate, do not mutate source in this issue; create a separate code-bearing follow-up.

## Pandora Proof

- Container target: `amiga_disk_pandora-1988-firebird`
- Resolved listing target:
  `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`
- Expected callback state: no `callback_orphan_code_signals`, `safe_to_mutate=false`, and mutation blocked by `ready_callback_review_item`.
- Expected next-lane candidates: RSSET/app-base, A5 path/lifetime, immediate source/runtime references, and shared address-provenance reuse if justified by non-callback lanes.

## Implementation Slice

- C fact graph/query work: none.
- Python/API/report work: rerun current reports and summarize output.
- Journal/replay work: none.
- Renderer/verifier work: none.
- Tests: run `validate_017_issues` and `git diff --check`; focused code tests are not required unless the worker changes code, which this issue should not do.

## Research Coverage

- [ ] `017-074` through `017-078` completion evidence checked.
- [ ] Current Pandora callback report rerun and summarized.
- [ ] Callback tooling progress summarized: target resolution, blocker triage, offset recovery, recovered target classification, and local consumer dataflow.
- [ ] Final callback blockers recorded.
- [ ] No current callback mutation candidate confirmed, or a separate follow-up created if one appears.
- [ ] Next 017 lanes selected.
- [ ] No 012/018/Mac/platform-format files touched.

## Research Review

- [ ] Closeout does not overstate callback source progress.
- [ ] Final blockers are stated as current evidence, not permanent truth.
- [ ] Next-lane selection is based on current report surfaces.
- [ ] Proposal 017 living notes updated with the closeout.

## Required Sign-Off

- [ ] Proposal context checked before work.
- [ ] Current callback report rerun.
- [ ] No source or journal writes performed.
- [ ] Next-lane issue list confirmed.
- [ ] `amiga_reversing.tools.validate_017_issues` passes.
- [ ] `git diff --check` passes.

