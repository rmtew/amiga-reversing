# Proposal 017: Pandora Post-Hardening Reversal

Status: proposed.

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
