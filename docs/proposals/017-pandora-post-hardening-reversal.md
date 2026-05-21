# Proposal 017: Pandora Post-Hardening Reversal

Status: active after review. The refreshed 017-027 rerun found no remaining
command-backed mutation, but review reopened verifier hardening and a required
Pandora exercise pass before final closeout.

Proposal 015 is the historical Pandora trial archive. Proposal 016 hardened the
loop surfaces found during that trial. This proposal owns the next focused
Pandora reversing pass using those hardened surfaces.

## Target

- Game target: `targets\amiga_disk_pandora-1988-firebird`
- Sub-target: `amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`
- Rendered source:
  `targets\amiga_disk_pandora-1988-firebird\targets\amiga_raw_pandora_3e1ee0f1_bk_00_000000e8\pandora_3e1ee0f1_bk_00_000000e8.s`

The sub-target is resettable unless a later issue explicitly promotes target
state as canonical. Do not treat timestamp-only `.project.json` changes or
local Manual Action Log churn as meaningful progress.

## Purpose

Continue Pandora source-quality improvement after 016, but avoid another broad
trial loop. Work from durable evidence, 016 reports, Review Items, and command
catalogs. Each accepted action must improve the rendered source or fix a
measured blocker needed for that improvement.

## Post-016 Rules

- Use `docs\agents\reversing-loop.md`.
- Use 016 outputs as guidance:
  `immediate-ref-report`, `a5-hardware-report`, selected-action traceability,
  evidence-led orphan-code scoring, and Review dialog items.
- Treat A5 hardware report output as non-durable linear listing-state
  candidate evidence only. It cannot drive hardware register rendering until a
  real accepted path/lifetime scope exists.
- Exact round-trip remains mandatory for output-affecting actions.
- Prefer structured durable facts over comments: data roles, app/global slot
  names, typed fields, code/data/string/table classification, callback targets,
  interpreted references, and ownership-backed generated descendants.
- Do not perform generic class/address renames such as `string_XXXXXXXX` as
  Pandora progress. If generic styling is desired, log framework policy work.
- Use query/report APIs before full `.s` scans. Full source rendering is for
  broad orientation, final comparison, or fallback when cheaper surfaces cannot
  answer the question.
- Profile slow phases instead of normalizing slow loop progress. Fix only
  measured bottlenecks needed for the active Pandora work.
- Record deferred findings in this proposal as they are encountered, then
  either resolve them or promote them to issues.

## Issues

1. `017-001`: post-hardening baseline and candidate queue.
2. `017-002`: immediate runtime-reference triage and promotion path.
3. `017-003`: A5 path/lifetime provenance before hardware rendering.
4. `017-004`: evidence-led Review Item source-quality pass.
5. `017-005`: RSSET/app-slot refinement from accepted evidence.
6. `017-006`: measured loop-performance fixes from Pandora work.
7. `017-007`: operand-level interpreted immediate-reference command and
   verifier.
8. `017-008`: CFG-backed A5 path/lifetime proof report.
9. `017-009`: RSSET candidate discovery for remaining raw A6 operands.
10. `017-010`: planner treatment for low-value representation candidates.
11. `017-011`: A5 accepted-evidence hardware render gate report.
12. `017-012`: immediate-reference report mutation gate.
13. `017-013`: A5 hardware-reference command and verifier.
14. `017-014`: A5 custom-register base-offset report identity.
15. `017-015`: A5 zero-displacement hardware-ref rendering.
16. `017-016`: A5 accepted-provenance verifier status.
17. `017-017`: A5 `intreq(a5)` focused hardware-ref mutation.
18. `017-018`: A5 `bltafwm(a5)` focused hardware-ref mutation.
19. `017-019`: remaining render-safe A5 hardware-ref sweep.
20. `017-020`: immediate-reference report candidate write policy.
21. `017-021`: A5 report suppression for already-recorded hardware refs.
22. `017-022`: current gate closeout.
23. `017-023`: tracked Pandora render evidence for 017 source changes.
24. `017-024`: A5 symbol-delta/address-mode-preserving rendering.
25. `017-025`: accepted RSSET app-base evidence for raw A6 candidates.
26. `017-026`: source-offset immediate-reference policy and verifier path.
27. `017-027`: rerun gate and independent 017 regression review.
28. `017-028`: A5 entry-comment source-output verifier hardening.
29. `017-029`: RSSET accepted-evidence conflict-shape hardening.
30. `017-030`: Pandora exercise pass over the reopened 017 surfaces.

## Current Gate State

The refreshed 017-027 rerun after reopened 017-025 catalog hardening recorded
this Pandora surface:

```text
immediate-ref-report:
  safe_to_mutate=false
  candidate_count=9
  command_candidate_count=0
  report_only_candidate_count=9
  remaining source family: source_offset

a5-hardware-report:
  safe_to_mutate=false
  accepted_path_lifetime_evidence_count=20
  existing_manual_state_uses=20
  command_candidate_count=0
  entry_comment_uses=1

rsset-candidate-report:
  safe_to_mutate=false
  candidate_count=125
  use_count=994
  status_counts:
    blocked=124
    already_recorded=1
  top_active_candidate=rsset-raw-a6:022E
  top_active_missing_gates: missing_accepted_base_evidence
  top_active_accepted_base_evidence_count=0
  top_active_catalog_state=report_only_same_displacement_app_slot_not_base_evidence

inspect:
  candidate_work_count=0
  review_state=clear
  round_trip_status=exact

run-one dry run:
  action=null
  planner_message=no supported source-converging command candidate
  remaining candidates are 221 generic data-symbol names and 4 low-value
  literal representation candidates
```

This is the refreshed 017 gate snapshot after the reopened work:

- `017-024`: implemented exact address-mode-preserving A5 rendering for the
  existing zero-displacement accepted ref by projecting a generated entry
  comment instead of changing operand syntax.
- `017-025`: removed the command catalog fallback that treated selected
  app-slot context as synthetic RSSET base evidence. Same-displacement/generic
  app-slot context remains report-only until real selected-use
  `rsset_app_base` provenance exists.
- `017-027`: reran the current gates after the reopened 017-025 fix; no
  command-backed, verifier-backed source-converging mutation remains.

Review reopened the track before final closeout:

- `017-028`: the A5 entry-comment verifier must prove the generated source text
  contains the generated comment, not pass from listing/UI comment state.
- `017-029`: accepted RSSET base evidence must require an explicit empty
  `conflicts` sequence; missing or malformed conflict state is not accepted
  evidence.
- `017-030`: after those fixes, do a demonstrable Pandora editing pass over the
  related source-converging surfaces, not just the new verifier changes. It
  should use the real target to exercise review/action discovery, candidate
  reports, command catalog entries, accepted/edit-blocked paths, verification,
  and source evidence capture before rerunning `017-027`.

The deferred `017-006` performance issue remains conditional; use it only when
a measured slow phase crosses its investigation threshold during active 017
work.

## Recommended Order

Start with `017-001`; it establishes the current safe work queue. Then choose
the first concrete candidate family from that queue. Prefer `017-002` for
data/reference work, `017-004` for review-item/code/data blockers, or `017-005`
for accepted app-base/RSSET opportunities. Do `017-003` only when A5 hardware
base proof is the active blocker. Use `017-006` whenever a measured slow phase
blocks normal iteration.

If the first pass reaches report-only blockers, continue with the follow-up
unblockers. Prefer `017-007` to unlock the concrete immediate-reference
candidate from `017-002`, `017-008` to turn A5 listing-state candidates into
accepted path/lifetime evidence, and `017-009` to expose RSSET/app-slot work
when the generic planner has no candidate. Use `017-010` if low-value
representation work repeatedly masks those higher-value blocked families.

For the current reopened continuation, do `017-028`, then `017-029`, then
`017-030`. Rerun `017-027` only after those are implemented and reviewed.

After `017-001`, proceed directly into the best safe mutation when durable
evidence, command support, verifier support, and exact round-trip gates are
present. Stop for human review only when the top candidate is ambiguous,
report-only, or needs new policy/tooling.

## Acceptance Criteria

Each accepted source-changing action must include:

- durable source evidence or accepted manual classification/override,
- source family and status compatible with the action,
- path/lifetime scope where the fact is not global,
- owning action id for generated descendants,
- action-specific verification,
- exact round-trip verification when output-affecting,
- a visible rendered-source improvement.

Support-code fixes are accepted only when tied to a concrete Pandora blocker,
verifier gap, command/catalog identity issue, or measured slow span. They need
focused tests and a rerun of the original Pandora action or report that exposed
the issue.

## Living Notes

Add meaningful observations here while working. Keep entries short and promote
repeatable work to `docs\issues\017-*`.

- 016 A5 output is useful for choosing candidate families, but it is explicitly
  not durable accepted hardware-base evidence.
- 017-001 baseline: hygiene and inspect are clean for
  `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`;
  Review Items are clear, round-trip status is exact, and no baseline candidate
  mutation was performed.
- The selected next family is `017-002` immediate runtime-reference triage.
  `immediate-ref-report` found concrete report-only candidates, including
  runtime/source-offset immediates, but planner writes remain blocked until
  verifier-backed immediate-reference interpretation exists.
- `a5-hardware-report` is deferred to `017-003`: it found many probable A5
  custom-register candidates, but all observed entries remain non-durable
  listing-state evidence with no accepted path/lifetime scope. Hardware register
  rendering remains blocked.
- The selected-action dry run currently prefers a mechanical printable byte
  immediate rendering action. That command is available, but it is lower value
  than reference/path provenance work and is not selected as 017 progress.
- 017-002 triage attempted the strongest immediate-reference family. The report
  found 10 accepted, conflict-free candidates; the best visible source-quality
  candidate is `s0:00006138` (`addi.l #458752,d0`) because it computes
  `app_text_cursor_ptr` from a runtime-address base. Promotion is blocked:
  there is no operand-level command to record a verified interpreted immediate
  reference, and no projection/semantic reload verifier for that rendered
  immediate-reference target. The report now exposes those gates structurally
  and keeps `symbolic_reference_allowed=false` and `rendering_allowed=false`.
- 017-003 checked the A5 hardware family without rendering. The concrete
  selected use was `s0:000004A6` (`move.w d0,dmacon(a5)`), reached from the
  linear A5 definition at `s0:00000498`. The report now gives this a concrete
  `linear_listing_between_a5_writes` scope, but its path/lifetime verdict is
  still `unknown` because no control-flow proof shows A5 remains `_custom` on
  every path to the use. Hardware register rendering remains blocked.
- 017-004 found no current Review Items or candidate work from the Review
  dialog source for the Pandora sub-target, so there is no durable Review Item
  to resolve. Review-count reduction is not treated as progress.
- 017-005 found no accepted RSSET/app-slot candidate in the current Pandora
  planner surface. A dry run selected `representation.character` after inspect
  returned no candidate work; no `target.rsset_region.*` or
  `rsset.binding.*` candidate was available. RSSET command/verifier plumbing
  exists, but this target currently lacks accepted source evidence for a new
  binding or field refinement.
- 017-006 did not identify a performance blocker. The active Pandora report and
  dry-run commands observed during this pass completed in roughly 8-9 seconds,
  below the issue's 30 second investigation threshold, so no speculative
  performance refactor was started.
- Follow-up unblockers were promoted from the blocked 017 pass:
  `017-007` for immediate-reference mutation/verifier support, `017-008` for
  CFG-backed A5 path/lifetime proof, `017-009` for RSSET candidate discovery,
  and `017-010` for planner handling of low-value representation candidates.
- 017-007 added the durable operand-level `immediate_ref.interpret` path for
  accepted interpreted immediate references. The report now exposes command and
  verifier support only when the candidate is accepted, conflict-free,
  runtime-address backed, and fits the selected operand width. Plain
  source-offset matches and the byte-sized `$523C` candidate remain report-only
  because address-shaped constants can also be masks or counts.
- 017-007 promoted Pandora `s0:00006138` (`addi.l #458752,d0`) after the
  command/verifier gates were present. The source export now renders
  `addi.l #imm_ref_h0_00050000_rt_00070000,d0`, with an xref to source offset
  `$50000` / runtime `$70000`, and the next instruction stores the result to
  `app_text_cursor_ptr(a6)`. The Manual Action Log advanced from 37 to 38 at
  head hash
  `924b8bd47d84ad8aabb01484808bf54f2e3434540480dd1b6fd1583f3cf5fa60`.
- 017-007 verification initially exposed a cache-ordering gotcha: command
  execution invalidates the listing cache, so render/xref verification must
  reopen the listing before checking projected operands. After reopening, the
  manual-log, semantic reload, rendered-source, xref-projection, and round-trip
  layers all passed; round-trip remained exact. Persisting a refreshed tracked
  `.s` export is separate from local Manual Action Log state.
- 017-010 changes the autonomous planner, not the manual command catalog:
  printable-byte `literal_representation` candidates from listing syntax are
  still reported but are now marked low value and skipped as autonomous
  progress unless accepted semantic evidence is attached. A Pandora dry-run
  now returns no action instead of selecting `representation.character`; the
  planner output keeps those skipped representation candidates and the existing
  generic class/address data-symbol blockers visible.
- 017-009 added a read-only `rsset-candidate-report`. Pandora reports 125
  grouped A6 displacement candidates from 994 uses; the top group is
  `rsset-raw-a6:022E`, but it is blocked by `missing_accepted_base_evidence`.
  The report exposes `rsset.binding.report` and catalog-visible
  `rsset.binding.bind` context while keeping `safe_to_mutate=false`; no target
  mutation was performed.
- 017-008 extends `a5-hardware-report` with a conservative straight-line CFG
  path/lifetime report. Pandora now classifies the selected `s0:000004A6`
  A5 use as `accepted_custom_base` with source evidence
  `a5-custom-cfg:h0:00000498->000004A6:op1:d0096`, but hardware register
  rendering remains blocked because verifier consumption/render support is
  still separate work.
- 017-011 makes that A5 rendering blocker explicit in report output:
  `cfg_path_lifetime_report` remains `safe_to_mutate=false` and
  `rendering_allowed=false` even when accepted path/lifetime evidence exists,
  and now names the missing `a5_hardware_ref.interpret` command and
  `a5_hardware_ref_state` verifier gates. Exact round-trip remains required
  for any future output-affecting hardware-register render mutation.
- 017-012 fixes a report-safety issue found during post-commit review:
  after the Pandora runtime-address immediate was promoted, the remaining
  `immediate-ref-report` candidates were accepted source-offset matches without
  command payloads. The report now exposes a `mutation_gate` and keeps
  top-level `safe_to_mutate=false` unless at least one command-backed
  `immediate_ref.interpret` candidate remains.
- 017-013 adds the durable A5 hardware-reference command/verifier path. Accepted
  CFG A5 uses now advertise `a5_hardware_ref.interpret` only when they carry
  accepted path/lifetime evidence, and the verifier requires Manual Action Log
  state in `a5_hardware_refs`, rendered symbolic operand state, and exact
  round-trip. Linear listing-state A5 candidates remain non-durable report
  evidence.
- After 017-013 support was present, Pandora `s0:000004A6`
  (`move.w d0,dmacon(a5)`) was recorded as durable A5 hardware-ref state from
  accepted evidence `a5-custom-cfg:h0:00000498->000004A6:op1:d0096`. The
  verifier passed manual-log, semantic reload, rendered-source, and exact
  round-trip layers. This did not require a broad Pandora mutation run.
- 017-013 post-commit review exposed a report correctness blocker:
  `lea _custom+dmaconr,a5` was being treated as exact `_custom`, so `(a5)` was
  misidentified as `bltddat` instead of effective offset `$0002` / `dmaconr`.
  017-014 now carries `custom_base_offset` through A5 evidence and command
  payloads, accepts signed displacements only through valid effective offsets,
  blocks out-of-range effective offsets, and keeps zero-offset evidence ids
  stable.
- The first post-017-014 mutation, Pandora `s0:0000045C`, recorded durable
  `dmaconr` A5 hardware-ref state and passed manual-log and semantic-reload,
  but failed rendered-source projection. A forced `dmaconr(a5)` render changes
  the address mode because A5 already points at `_custom+dmaconr`, so 017-015
  keeps zero-displacement/non-zero-custom-base A5 refs semantic-only until
  exact symbol-delta rendering exists. Focused Pandora validation now blocks
  `s0:0000045C` with that reason while leaving `s0:000004A6` command-backed.
- The next safe A5 mutation selected Pandora `s0:000004AA` and rendered
  `intena(a5)` exactly, but the generic provenance wrapper rejected
  `source_evidence_status=accepted` even though the A5 action-specific verifier
  passed. 017-016 adds `accepted` to the generic accepted-provenance statuses;
  revalidation of action `manual-5f2c6ead224244dabec3cadaff7d2d98` now passes
  manual-log, provenance, semantic-reload, rendered-source, and exact round-trip
  layers.
- 017-017 continued the focused A5 path with the next unrecorded command-backed
  Pandora candidate, `s0:000004AE`, from evidence
  `a5-custom-cfg:h0:00000498->000004AE:op1:d009C`. Action
  `manual-c2202ab8723a407eb25ebccbfdf48476` renders `move.w d0,intreq(a5)`
  and passes manual-log, provenance, semantic-reload, rendered-source, and exact
  round-trip layers.
- 017-018 recorded the next render-safe A5 candidate, `s0:000004C0`, from
  evidence `a5-custom-cfg:h0:00000498->000004C0:op1:d0044`. Action
  `manual-fa2c2e177ce645968850a0e8c3779158` renders
  `move.w d0,bltafwm(a5)` and passes manual-log, provenance, semantic-reload,
  rendered-source, and exact round-trip layers.
- 017-019 exhausted the remaining render-safe, command-backed A5 candidates in
  the same accepted-evidence family. Fifteen additional A5 refs passed
  manual-log, provenance, semantic-reload, rendered-source, and exact round-trip
  verification; `a5-hardware-report` now has zero remaining unrecorded
  command-backed A5 candidates after existing manual refs are excluded. Blocked
  zero-displacement/non-zero-custom-base A5 refs remain semantic-only pending
  exact symbol-delta rendering support.
- 017-020 fixes the remaining immediate-reference report inconsistency found
  after the A5 sweep: top-level `mutation_gate.safe_to_mutate=false` was correct,
  but source-offset report-only candidates still advertised supported
  candidate-level write policy. Candidate policy now stays report-only unless an
  actual `immediate_ref.interpret` command payload is present.
- 017-021 fixes the analogous A5 post-sweep report state: accepted path/lifetime
  evidence remains visible, but A5 uses already present in
  `manual_state.a5_hardware_refs` no longer count as fresh command candidates.
  Pandora now reports the render-safe A5 queue as exhausted instead of inviting
  duplicate mutations.
- 017-022 records the current end state of the focused Pandora pass. The
  immediate-reference, A5, RSSET, and planner gates now all agree that no safe
  source-converging mutation remains without new evidence or tooling; remaining
  generic class/address data-symbol styling and low-value literal
  representation candidates are not accepted as 017 progress.
- Post-closeout review found follow-up rerun work that should remain in 017
  instead of being lost: 017 source-quality improvements are documented through
  local target/manual state but not a tracked rendered-source evidence artifact;
  zero-displacement or non-zero custom-base-offset A5 refs still need exact
  address-mode-preserving symbol-delta rendering; RSSET has 125 report-only A6
  candidates blocked by missing accepted app-base evidence; and remaining
  immediate source-offset candidates need a deliberate policy/verifier path
  before any mutation. These were promoted to `017-023` through `017-027`.
- 017-023 added `docs/validation/pandora-017-rerun-2026-05-21.md` as the
  tracked evidence boundary. No refreshed `.s` render was committed in this
  closeout; full 017 local/manual reproduction requires Manual Action Log count
  58 with head hash
  `3cbe93c200fd62d091b67c5b096c7b2221e3b57bf30f222272633a4342deed35`.
- 017-024 implemented the address-mode-preserving annotation/render path for
  accepted A5 refs that cannot safely become symbolic operands. Pandora
  `s0:0000045C` now renders an entry comment naming `dmaconr` while preserving
  `move.w (a5),d0`; the verifier checks that no unsafe `dmaconr(a5)` operand is
  emitted.
- 017-025 added selected-use, app-slot-context, and Manual Action Log evidence
  search to `rsset-candidate-report`. Pandora now reports 124 blocked RSSET
  groups plus one already-recorded `$01AD` group; the top active group
  `rsset-raw-a6:022E` still lacks accepted `rsset_app_base` evidence,
  selected-use path/lifetime scope, empty conflicts, and a selected A6 base id.
- Post-review 017-025 hardening made that blocker stricter: accepted RSSET
  base evidence must carry selected-use identity and a `selected_use`
  path/lifetime scope covering the exact A6 use. Sparse or broader evidence is
  rejected as report evidence, not consumed as durable mutation proof.
- 017-026 closes the immediate source-offset policy for Pandora: the 9 remaining
  source-offset candidates stay report-only until accepted runtime-address
  provenance exists.
- 017-027 reran the report surfaces and dry-run planner after `017-024` and
  `017-025`. Immediate refs remain 9 report-only source-offset candidates; A5
  has 20 accepted entries already in manual state, no fresh command candidates,
  and 1 address-mode-preserving entry-comment render; RSSET has 124 blocked
  groups plus one already-recorded `$01AD` group, with `rsset-raw-a6:022E` as
  the top active missing-evidence group. `inspect` reports no candidate work
  and exact round-trip, and `run-one --dry-run` returns no action.
- After post-review 017-025 hardening, the 017-027 gate was rerun again with
  the same mutation result: RSSET `rsset-raw-a6:022E` still has
  `accepted_base_evidence_count=0`, and stricter selected-use matching did not
  expose any command-backed Pandora mutation.
- Reopened 017-025 review found a catalog/report mismatch: the report rejected
  same-displacement app-slot context as non-durable evidence, but the command
  catalog still allowed selected app-slot context to synthesize
  `selected-app-slot:*` base evidence. App-slot context now remains report-only
  for `rsset.binding.bind`; focused Pandora rerun keeps `rsset-raw-a6:022E`
  blocked with `accepted_base_evidence_count=0`.
- Reopened 017-027 rerun after the 017-025 catalog hardening found no supported
  Pandora mutation: immediate refs are 9 report-only source-offset candidates,
  A5 has 20 accepted manual-state refs and 1 entry-comment render with no fresh
  command candidate, RSSET still has 125 candidates with top
  `rsset-raw-a6:022E` blocked by missing accepted base evidence, inspect is
  clear/exact, and dry run reports `no_candidate`.
- 017-028 hardened the A5 address-mode-preserving entry-comment verifier: it
  now requires generated source rendering to succeed and requires the generated
  source text to contain the expected entry comment. Listing/UI
  `comment_text` alone no longer satisfies the verifier, while unsafe symbolic
  operand text such as `dmaconr(a5)` remains rejected.
