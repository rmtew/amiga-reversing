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

## Recommended Order

Start with `017-001`; it establishes the current safe work queue. Then choose
the first concrete candidate family from that queue. Prefer `017-002` for
data/reference work, `017-004` for review-item/code/data blockers, or `017-005`
for accepted app-base/RSSET opportunities. Do `017-003` only when A5 hardware
base proof is the active blocker. Use `017-006` whenever a measured slow phase
blocks normal iteration.

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
