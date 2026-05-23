# 017-055: Pandora Read-Only Evidence Discovery Pass

Status: completed

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

- [x] Current Pandora inspect state checked.
- [x] Callback-slot report checked.
- [x] Immediate-runtime-reference report checked.
- [x] A5 hardware lifetime report checked.
- [x] RSSET candidate report checked.
- [x] Orphan/data-range surfaces checked where available.
- [x] No file diffs from discovery checked.
- [x] Follow-up candidate or pause conclusion recorded.

## Research Review

- [x] Second pass checked that no cosmetic/stale-artifact mutation was selected.
- [x] Candidate evidence classifications reviewed against the 017 protocol.
- [x] Missing tooling/verifier blockers recorded if encountered.
- [x] Proposal updated with the discovery result.

## Required Sign-Off

- [x] Proposal context checked before work.
- [x] Discovery commands and outputs summarized.
- [x] No target or generated file mutation performed.
- [x] Any follow-up issue contains exact gates and expected source improvement.
- [x] If no follow-up exists, pause recommendation remains explicit.
- [x] Post-commit review found no unresolved worthwhile findings.

## Completion Evidence

Pandora target:
`amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.

Read-only `inspect` still matches the `017-054` baseline:

- `safe_to_mutate=true`.
- `candidate_work=[]`.
- `mutation_readiness.safe_to_mutate=true`, `blockers=[]`.
- hygiene unknown files: `[]`.
- verification paths available: `semantic_reload`, `projection_check`, and
  `round_trip`.

Callback-slot report:

- 92 callback/app slots, 191 assignments, 3 consumers.
- 7 concrete missed-code-target assignments across 4 slots:
  `app_020C`, `app_0210`, `app_027C`, and `app_0280`.
- Assignment readiness: 180 `blocked`, 11 `already_code`, 0 ready.
- Concrete blockers are `missing_orphan_code_review_item`,
  `review_item_is_not_code_classification`, and `target_row_missing`.
- The report mutation gate now requires a ready callback review item plus exact
  round-trip. Current Pandora reports `safe_to_mutate=false`,
  `command_candidate_count=0`, and missing gate `ready_callback_review_item`.

Immediate-runtime-reference report:

- 9 candidates.
- All 9 are `accepted` as source-offset-looking references but `report_only`.
- Mutation gate is blocked with `command_candidate_count=0`,
  `report_only_candidate_count=9`, and reason
  `remaining immediate reference candidates are report-only`.
- Each candidate remains blocked from mutation because source-offset immediate
  matches are not accepted runtime-address provenance; command and verifier
  status are unavailable for those report-only candidates.

A5 hardware lifetime report:

- 525 CFG path/lifetime uses.
- 20 `accepted_custom_base`, 505 `unknown`.
- Rendering gate has accepted evidence and available verifier support, but
  `command_candidate_count=0`; missing gate is `command_candidate`.
- Unknown uses remain blocked by path/lifetime proof issues such as possible A5
  clobbering calls before the selected use.

RSSET candidate report:

- 125 candidates and 994 uses.
- 123 candidates are `blocked`, all by missing accepted base evidence.
- 2 candidates are `already_recorded` with bind state `already_satisfied`.
- No RSSET command candidate is available for a new mutation.

Orphan/data-range surface:

- Rechecked the available packet for
  `data-class-symbol:s0:000010F3:data:1111:0:000010F3:string_000210F3`.
- It remains `safe_to_mutate=false`, `mutation_policy=read_only`,
  `decision_lane.status=deferred`.
- `data_symbol.rename` remains blocked by `missing_direct_xref_evidence` and
  `missing_exact_round_trip_gate`.

Discovery mutation audit:

- Before documenting results, `git diff --name-only -- targets`, the 012
  proposal/issues, and the 018 proposal/issues was empty.
- No source, Manual Action Log, Decision Journal, verifier artifact, generated
  output, target metadata, tracked Pandora `.s`, 012, or 018 file was touched by
  the discovery commands.

Conclusion: 017 still has no useful unblocked Pandora mutation. The callback
report found the only fresh-looking evidence, but it is not a safe follow-up
candidate because every concrete target lacks the required durable orphan-code
review identity or is explicitly not a code-classification review item. Do not
open a mutation follow-up from this pass. Keep 017 paused and resume non-017
work where it is already scoped.
