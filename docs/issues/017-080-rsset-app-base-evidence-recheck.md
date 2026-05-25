# 017-080: RSSET App-Base Evidence Recheck

Status: complete
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Dependency: start after `017-079` callback lane closeout.
- Protocol area: refreshing the RSSET/app-base lane after callback tooling exhausted current Pandora evidence.
- Current proposal state: earlier 017 passes left RSSET groups, especially `$022E`, blocked by missing accepted base evidence.
- Desired proposal state after this issue: current RSSET blockers are rechecked against present tooling and classified into command-ready evidence, missing-evidence shapes, or no-longer-promising candidates.

## Protocol Delta

- Adds: current RSSET/app-base report refresh and blocker classification.
- Changes: old RSSET conclusions must be revalidated from current reports, not copied forward.
- Replaces: relying on stale `$022E` blocker notes.
- Leaves out of scope: speculative RSSET mutation, callback work, 012/018, Mac OS support, platform executable format KB/docs, and Mac targets.

## Default Behavior

- This issue is report/classification work unless a small report bug blocks correct classification.
- If a fixable report bug is found, implement the minimal code path with focused tests.
- No RSSET source mutation is allowed in this issue.
- If command-ready accepted base evidence exists, create a dependent implementation issue rather than mutating here.

## Pandora Proof

- Target: `amiga_disk_pandora-1988-firebird`
- Historical candidate: `rsset-raw-a6:022E` at `s0:000006E4`
- Expected report: current RSSET candidate report with grouped displacements, top blockers, accepted base evidence counts, and command readiness.
- Evidence packet expected: strongest active RSSET group with selected identity and exact blocker reason.

## Implementation Slice

- C fact graph/query work: only if current RSSET report lacks required C-owned facts to classify base evidence.
- Python/API/report work: rerun and summarize current RSSET reports; patch report output only if it cannot express the required blocker state.
- Journal/replay work: none.
- Renderer/verifier work: none.
- Tests: focused tests for any report-code change; otherwise issue validator and whitespace check.

## Research Coverage

- [x] `017-079` closeout checked before work.
- [x] Current RSSET report rerun.
- [x] Top RSSET groups listed with blockers and accepted base evidence counts.
- [x] Historical `$022E` state rechecked.
- [x] Missing evidence shape recorded precisely if still blocked.
- [x] Any report-code change covered by focused tests.
- [x] No callback, 012/018/Mac/platform-format files touched.

## Research Review

- [x] Conclusions are based on current report output.
- [x] Strongest RSSET candidate is selected or explicitly rejected.
- [x] Any command-ready result is deferred to a dependent implementation issue.
- [x] Proposal 017 living notes updated.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] `017-079` checked before work.
- [x] Real Pandora RSSET report rerun.
- [x] No source or journal writes performed.
- [x] Focused tests pass if code changed.
- [x] `amiga_reversing.tools.validate_017_issues` passes.
- [x] `git diff --check` passes.

## Completion Evidence

- Current report was rerun against the resolved Pandora listing target
  `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`;
  the disk/container target alone still has no listing, so it is not sufficient
  evidence for RSSET classification.
- The resolved listing opened successfully with `30398` rows. The RSSET report
  found `candidate_count=125`, `use_count=994`, and `safe_to_mutate=false`.
- Top report-only groups by current report order remain blocked by missing
  accepted base evidence:
  `rsset-raw-a6:02A6` (`same_displacement_use_count=38`),
  `rsset-raw-a6:033C` (`38`), `rsset-raw-a6:027B` (`26`),
  `rsset-raw-a6:022D` (`20`), `rsset-raw-a6:0232` (`20`),
  `rsset-raw-a6:0360` (`20`), `rsset-raw-a6:01E4` (`18`), and
  `rsset-raw-a6:0214` (`18`). Each has
  `accepted_base_evidence_count=0` and
  `status=missing_accepted_base_evidence`.
- Historical `$022E` at `s0:000006E4:op1` is no longer blocked in the current
  report. `rsset-raw-a6:022E` has `same_displacement_use_count=66`,
  `raw_or_weak_use_count=33`, `accepted_base_evidence_count=1`, and
  `evidence_search.status=accepted`.
- The accepted `$022E` selected identity is
  `addr=1764`, `hunk=0`, `operand_index=1`, `base_register=A6`,
  `displacement=558`, `stable_key=s0:000006E4:instruction:455`, rendering
  `bclr.b #1,app_022E(a6)`.
- Accepted base evidence is
  `decision-rsset-022e-accept-017-040` with
  `source_family=rsset_app_base`, `source_evidence_status=accepted`,
  `base_evidence_id=selected-base:A6:__amiga_app_base__`,
  selected-use path/lifetime scope, empty conflicts, and existing owner action
  `manual-6e574feccab748359c7577833fa718ba`.
- This issue performs no RSSET mutation. The implementable command/verifier
  follow-up is the dependent `017-081` issue.
