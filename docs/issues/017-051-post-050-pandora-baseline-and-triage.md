# 017-051: Post-050 Pandora Baseline and Triage

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area: post-artifact Pandora baseline and next-candidate triage
- Blocked by: `017-050`
- Current proposal state: `017-050` can explicitly produce a current verifier
  artifact for the accepted Pandora RSSET decision and the audit can consume it
  as a complete five-layer proof.
- Desired proposal state after this issue: the current Pandora state after
  `017-050` is reproduced from commands, the productive/unblocked next work is
  identified, and any remaining blockers are recorded without speculative
  mutation.

## Protocol Delta

- Adds: a focused post-050 baseline and triage checkpoint.
- Changes: next Pandora work must be selected from current evidence, not from
  stale pre-050 blocker lists.
- Replaces: informal assumptions about what 050 unlocked.
- Deletes: none.
- Leaves out of scope: broad target mutation runs, cosmetic label cleanup, and
  accepting deferred facts without new durable evidence.

## Default Behavior

- Do not mutate Pandora during this issue unless a candidate already has durable
  evidence, command support, verifier support, and exact round-trip gates before
  any write.
- Do not rename generic labels just for readability.
- Do not treat the ignored `decision_verifier_artifacts.json` as tracked source
  evidence; it is regenerable local verifier state.
- If no safe mutation exists, record the blocker and recommend the next
  implementation or research issue.

## Evidence Contract

The issue must rerun and record the current result of:

- target hygiene;
- `decision-verifier-artifact` for
  `decision-rsset-022e-accept-017-040` in no-write mode;
- `decision-journal-report` after verifier artifact availability;
- focused source-offset immediate packet for `s0:000009A6:op0`;
- focused A5 path/lifetime packet for `s0:0000045C:op0`;
- focused orphan/data-range packet for `s0:000010F3`;
- RSSET candidate/report state around `rsset-raw-a6:022E`;
- planner/dry-run or equivalent current mutation candidate surface;
- exact round-trip state.

Each result must state whether it is ready, deferred, blocked, or complete, and
why.

## Pandora Proof

Use only the focused Pandora subtarget:
`amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.

The proof must show:

- the post-050 RSSET verifier chain is reproducible from the current target;
- the three deferred decisions from `017-046` through `017-048` remain deferred
  unless new durable evidence changes their status;
- no broad target mutation run was performed;
- no source, Decision Journal, or Manual Action Log change was made unless a
  fully gated safe mutation is discovered and separately justified.

## Implementation Slice

- C fact graph/query work: none unless a current proof command cannot answer an
  existing required evidence question.
- Python/API/report work: no new feature work expected; add only narrow proof
  helpers if a command cannot expose an already-computed result.
- Journal/replay work: inspect current state only.
- Renderer/verifier work: inspect current verifier results only.
- Tests/proof: command transcript or focused validation sufficient for docs-only
  completion; add tests only if a missing proof surface requires code.

## Research Completion Standard

Record trace blocks for each command/result, current blockers, any safe next
candidate, and any deferred follow-up issue needed before mutation.

## Research Coverage

- [x] Target hygiene checked.
- [x] RSSET verifier artifact producer checked.
- [x] Decision Journal audit checked.
- [x] Source-offset immediate packet checked.
- [x] A5 path/lifetime packet checked.
- [x] Orphan/data-range packet checked.
- [x] RSSET report/candidate state checked.
- [x] Planner/dry-run mutation surface checked.
- [x] Exact round-trip checked.

## Research Review

- [x] Second pass checked trace blocks against command output.
- [x] Cross-references searched for stale blocker assumptions.
- [x] Safe-mutation criteria reviewed before any write.
- [x] Proposal updated with current baseline and next step.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Protocol delta implemented as described, or proposal updated.
- [x] Default behavior impact verified.
- [x] Old code deleted, or deferred deletion blocker recorded.
- [x] No broad mutation run performed.
- [x] No source/journal/manual-state mutation performed unless fully gated.
- [x] Current Pandora baseline recorded.
- [x] Next issue or blocker identified.
- [x] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

Focused target:
`amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.

Trace results:

- Hygiene:
  `uv run python -m amiga_reversing.reversing_loop --project-root . hygiene
  --target ...` returned `safe_to_continue=true`, `safe_to_clean_run=true`,
  `safe_to_reimport=true`, `unknown_files=[]`. The existing
  `decision_verifier_artifacts.json` is classified as
  `local_verifier_state`/`regenerate_on_clean_run`, not tracked source
  evidence.
- Verifier artifact producer no-write:
  `produce_decision_verifier_artifact(..., write=False)` returned
  `status=passed`, `written=false`, and `generated_source`,
  `negative_safety`, and `exact_round_trip` all `passed`.
- Verifier artifact availability:
  the previously ignored artifact was stale for the current source-state
  identity, so the explicit producer was rerun with `write=True` to refresh
  only regenerable local verifier state. It returned `status=passed`,
  `written=true`, and all three verifier layers `passed`.
- Decision Journal audit:
  `inspect_decision_journal(...)` for
  `decision-rsset-022e-accept-017-040` returned all five layers
  `passed`: `decision_journal`, `semantic_reload`, `generated_source`,
  `negative_safety`, and `exact_round_trip`; `blockers=[]`.
- Source-offset packet:
  `query_source_offset_immediate_packet(...)` for
  `immediate-runtime-ref:s0:000009A6:instruction:664:0:00001080`
  returned `status=blocked`, `mutation_policy=read_only`,
  `safe_to_mutate=false`, `decision_lane.status=deferred`, and blockers
  `same_literal_only_not_durable_provenance`,
  `missing_accepted_runtime_address_provenance`,
  `missing_source_offset_decision_replay_support`, and
  `missing_source_offset_render_verifier_gate`.
- A5 packet:
  `query_a5_path_lifetime_packet(...)` for `s0:0000045C:op0` returned
  `status=accepted_existing_manual_state`, `mutation_policy=read_only`,
  `safe_to_mutate=false`, `decision_lane.status=deferred`, and blockers
  `already_recorded_in_manual_state` and `missing_command_candidate`.
- Orphan/data-range packet:
  `query_orphan_code_island_packet(...)` for
  `data-class-symbol:s0:000010F3:data:1111:0:000010F3:string_000210F3`
  returned `status=blocked`, `mutation_policy=read_only`,
  `safe_to_mutate=false`, `decision_lane.status=deferred`, and blockers
  `missing_direct_xref_evidence` and `missing_exact_round_trip_gate`.
- RSSET `022E` report:
  `inspect_rsset_candidates(...)` returned `status=already_recorded`,
  `safe_to_mutate=false`, bind `state=already_satisfied`, and existing manual
  state owned by `manual-6e574feccab748359c7577833fa718ba`. The
  `journal_mutation_gate` remains `ready_for_mutation_issue`, but the selected
  binding is already present, so no fresh mutation is unblocked.
- Planner/current mutation surface:
  `inspect_target(...)` returned one candidate,
  `manual_action_log_inconsistency:target`, with
  `suggested_action_kind=repair_manual_action_log`, `actionable=false`, and
  stop reason `candidate lacks locator, xref evidence, or verifier`. No
  planner-selected write candidate exists.
- Exact round trip:
  `_round_trip_state(...)` returned `available=true`, `status=exact`.
- No source/journal/manual mutation:
  `git diff -- decision_journal.jsonl manual_actions.jsonl
  pandora_3e1ee0f1_bk_00_000000e8.s` was empty after all proof commands.

Current conclusion:

- The post-050 RSSET verifier-backed chain is reproducible.
- Decisions from `017-046`, `017-047`, and `017-048` remain deferred/read-only.
- No useful 017 mutation is currently unblocked.
- Recommended next issue: investigate and define a safe repair/proof path for
  the current `manual_action_log_inconsistency:target` sequence mismatch before
  further 017 mutation work, or explicitly defer it if manual-log repair is
  outside the 017 protocol scope.

Verification:

- `uv run python -m amiga_reversing.tools.validate_017_issues`
- `git diff --check -- docs/issues/017-051-post-050-pandora-baseline-and-triage.md
  docs/proposals/017-evidence-driven-analysis-protocol.md`
