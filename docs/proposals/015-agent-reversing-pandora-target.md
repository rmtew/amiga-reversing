# Proposal 015: Agent reversing Pandora target

The scope of this proposal is that an agent runs the reversing loop using the
editing features added in proposal 014.

## Goals

* Agent runs the reversing loop to trial the editing features added in
  proposal 014 on a real target.
* Agent fixes and improves editing functionality, verifier gaps, and workflow
  bugs when they block a worthwhile reversing action.
* Agent watches action duration and profiles slow workflow spans instead of
  accepting slow progress as normal.
* Agent records deferred findings in this proposal while working, then returns
  to triage and resolve them instead of losing them between focus areas.
* Agent must not perform manual reversing edits just to produce activity.
  Accept only actions that improve rendered source quality.
* Agent should move the source toward clean, correct, human-quality
  reconstructed source.
* If no solid progress can be made, or the target is already complete for the
  currently available action surface, stopping with a precise blocker is a valid
  result.

## Target

* Game target: `targets\amiga_disk_pandora-1988-firebird`
* Sub-target: `amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`
* Existing rendered source:
  `targets\amiga_disk_pandora-1988-firebird\targets\amiga_raw_pandora_3e1ee0f1_bk_00_000000e8\pandora_3e1ee0f1_bk_00_000000e8.s`
* Treat this sub-target as resettable for the trial. The previous
  `manual_actions.jsonl` was deleted and there is no manual state to preserve.

## Start Gate

Proposal 015 starts only after the current proposal 014 implementation pass has
addressed all current 014 issues.

Before the first Pandora mutation:

* review final proposal 014 commits/docs against the accepted 014 boundaries,
* confirm command catalog surfaces exist for the first candidate family,
* confirm planner and verifier gates are present,
* run the relevant focused tests/precommit checks,
* run `hygiene`,
* if hygiene is clean, allow one initial `clean-run` to establish the trial
  baseline.

## Starting Observations

Initial read-only inspection found that this target is useful for validating
proposal 014's source-converging action surface:

* The target already has exact reproduction, so output-affecting changes must
  preserve round-trip correctness.
* It is not a good first target for OS API/LVO recovery: the rendered source
  does not currently show `_LVO` calls.
* It is a good target for app/base provenance:
  * many rendered `app_XXXX(a6)` operands,
  * many remaining raw `$XXXX(a6)` operands,
  * a large generated application RSSET with obvious gaps.
* It has hardware/base provenance opportunities, especially repeated raw
  `$XXXX(a5)` operands that may correspond to hardware registers once base
  provenance is established.
* It has custom-struct opportunities, including repeated A2-relative accesses
  that look like a small object or movement structure.
* It has data-block opportunities: strings, lookup tables, sprites, copper
  lists, palettes, and many absolute runtime/data references.

## Operating Rules

The agent must follow `docs\agents\reversing-loop.md`.

In particular:

* Run hygiene before mutation.
* Use command discovery and command execution through the supported reversing
  loop or server command path.
* Do not directly edit target metadata or generated source to make reversing
  progress.
* Do not use row indexes, row text, DOM text, or screenshots as durable
  identity.
* Use proposal 014 as the capability map. If the best action lacks durable
  identity, command support, or verifier support, report that missing
  capability instead of bypassing it.
* Comments are allowed only for concrete semantic discoveries that cannot be
  represented with a more structured command.
* Do not treat `.project.json` timestamp-only changes or local Manual Action
  Log churn as meaningful progress.
* Record materially slow action phases in the iteration report with the command,
  target, elapsed time, and suspected span.
* When a useful observation is out of scope for the current action, add it to
  the deferred work log below with enough evidence to resume it later.
* Operate mainly through CLI/server APIs. Use the UI only for diagnosis or to
  inspect a missing surface.
* Continue only with owned or expected target-local state. Stop on unknown
  target-local state.

## Evidence And Query Policy

Full `.s` source rendering is for initial broad orientation, final
human-readable comparison, or fallback when cheaper query surfaces cannot answer
the question. Normal iterations should use listing/IR/provenance/query surfaces:

* listing artifact windows by source or runtime location,
* command catalogs from row, element, or range context,
* provenance and RSSET reports,
* reversing-loop candidate reports,
* cached listing projection and durable row locators,
* reproduction reports as verifier gates.

Raw `.s` scanning may discover candidates, but accepted actions require durable
evidence from listing rows, analysis facts, provenance reports, xrefs, or command
catalog payloads.

If a needed query surface is missing:

* one-off scripts are allowed only for read-only discovery,
* repeated or blocking needs should become clean reusable query/report APIs,
* do not bolt on narrow variants when a cleaner API refactor is needed.

Unknown or conflicting provenance is report-only until resolved. It may drive
better reports, classification work, or deferred tooling, but not writes.

## Candidate Order

Prefer candidates that are both high-value for Pandora and good validation of
proposal 014:

1. RSSET/app-base provenance for raw or weakly named A6-relative operands.
2. Same-flow/same-displacement RSSET propagation when accepted base evidence
   makes propagation verifier-safe.
3. Custom struct field rendering for repeated register-relative object access.
4. Data-block type binding for tables, sprites, copper lists, palettes, and
   platform structures.
5. Hardware-base provenance only when the base register lifetime is proven.
6. Data/global naming and EQU/value representation only through the separate
   semantic actions defined by proposal 014 boundaries.

Work depth-first by candidate family. Stay with the best family until it
produces real source improvement, saturates, or hits a blocker, then move to the
next family. Do not chase isolated raw displacements unless they unlock broader
base, structure, type, or naming improvement.

## Acceptance Criteria

Each accepted reversing action must have:

* durable source evidence or an accepted manual classification/override,
* a path/lifetime scope when the fact is not global,
* a source family and status compatible with the action,
* an owning action id for generated descendants,
* a visible rendered-source improvement,
* action-specific verification,
* exact round-trip verification when output-affecting.

Visible source-quality improvement means at least one of:

* rendered source becomes more semantic, such as named app slot, struct field,
  typed data block, platform register, or domain constant,
* a repeated raw pattern becomes a verified named or typed pattern,
* a generated descendant becomes owned and cleanly removable,
* review noise is reduced through a verified structured fact.

Reject placeholder comments, proof-only labels, weak-evidence renames, command
exercise, and direct metadata edits outside supported actions.

Manual override is exceptional and presumed to indicate tooling or evidence
failure unless proven target-local. If evidence is missing because the analyzer,
query, or verifier cannot expose what is knowable, fix or log tooling. If
evidence contradicts reality because analyzer/importer behavior is wrong, fix or
log that upstream. Use target-local override only for genuine target-specific
ambiguity or correction, and record the contradicted evidence id, scope,
cleanup, and follow-up question.

Hardware register rendering requires proven base register identity/lifetime. Do
not bind raw A5/Ax displacements to hardware registers just because an offset
matches.

Nested data-block/platform/custom struct rendering is allowed only when the full
rendered shape is evidenced and verifier-covered. Otherwise bind the outer data
block first and refine nested fields later.

Cascading actions require generated-descendant review:

* descendants reference the owning action,
* cleanup removes descendants,
* rendered changes match intended scope,
* unrelated source regions do not change,
* round-trip remains exact.

Support-code changes made during this proposal are accepted only when they are
needed for one of:

* a missing command required by the next worthwhile reversing action,
* a verifier gap that would otherwise make the action unsafe,
* a catalog identity/state contract gap,
* a reproducible workflow bug in the reversing loop,
* a repeated high-cost workflow span observed during real target work.

Support-code fixes require focused tests before commit, plus a rerun of the
original Pandora action that exposed the issue. If output-affecting, refresh
exact round-trip verification.

Widening the action surface is allowed when it is a justified extrapolation of
proposal 014's existing model, not a random divergence. Record the rationale and
update the proposal/docs when the widened surface becomes real support code.

## Performance Handling

The agent must treat reversing-loop latency as part of the target-work result,
not background noise.

For each iteration, record the wall-clock time for:

* hygiene,
* listing open/readiness,
* candidate/report generation,
* command discovery,
* command execution,
* semantic reload/projection,
* verifier checks,
* round-trip or focused source checks.

If an action feels slow enough to interrupt normal iteration, or a repeated span
dominates the workflow profile, the agent should:

1. Name the slow command and phase.
2. Capture the relevant `workflow_profile` span or add focused profiling if the
   existing report is too coarse.
3. Diagnose the cause before refactoring.
4. Fix only the measured bottleneck needed for continued target work.
5. Rerun the original Pandora action to prove the source-converging workflow is
   faster and still correct.

Do not refactor performance speculatively. A performance fix must cite the
observed slow span and the before/after verification.

Automatically investigate phases over 30 seconds, repeated dominant spans, or
latency that blocks interactive reversing flow. Do not optimize one-off slow
checks unless they recur or block progress.

## Reporting And Commits

Keep a living iteration report in this proposal until it becomes too large; then
split to `docs/reports/` and link it here.

Each meaningful iteration report entry should include:

* candidate,
* evidence,
* command,
* verifier,
* timing,
* result,
* generated descendants or cleanup notes when relevant,
* deferred findings,
* next recommendation.

Record meaningful failed/skipped candidates when they teach something durable:
missing command, insufficient evidence, conflict, verifier gap, performance
issue, or domain ambiguity. Omit low-value scan noise.

Commit tracked support/docs changes per coherent fix or milestone. Commit
proposal/report checkpoints when they explain a meaningful accepted source
improvement, blocker, or support-code fix. Do not commit Pandora Manual Action
Log state by default; summarize it unless the target state is explicitly
promoted as tracked/canonical.

Generated artifacts are allowed for verification, but are meaningful deliverables
only when they are intentional verified outputs of the accepted action.

## Domain Knowledge

Use conservative descriptive names from direct behavior and xrefs. Ask before
speculative game/lore names or weak semantic leaps.

Load knowledge files only when the current candidate needs them:

* hardware-base work: `knowledge/amiga-hardware.md`
* hardware nuance beyond the summary: `resources\Hardware_Manual.html`
* OS/library work: `knowledge/amiga-os.md`
* instruction semantics uncertainty: `knowledge/m68k.md`
* game-specific semantic naming: `knowledge/game-specific.md`

Comments are a last resort for concrete semantic discoveries when no structured
command exists. They must be evidence-backed, useful in source, and verified at
the intended location.

## Iteration Report

### 015-001: Disk-target hygiene classifier gap

* Candidate: Start gate hygiene for
  `amiga_disk_pandora-1988-firebird`.
* Evidence: initial `reversing_loop hygiene` reported unknown target-local
  files for disk import state and nested sub-target files:
  `manifest.json`, `target_state.json`, nested `.project.json`,
  `source_binary.json`, `target_metadata.json`, `binary.bin`, generated
  `.s`/`reproduction.json`, and local `ui_preferences.json`.
* Command: fixed `reversing_workspace` classification for disk project import
  state and `targets/<subtarget>/...` target-local files.
* Verifier: `tests\test_reversing_workspace.py -q` passed, focused `ruff`
  passed, and the original Pandora hygiene command now reports no unknown
  files with `safe_to_run: true`.
* Timing: focused pytest 0.97s; Pandora hygiene under 1s after the fix.
* Result: clean-run/continue/reimport are now available for Pandora without
  reviewing expected generated or source/import files as unknowns.
* Review: no Pandora Manual Action Log or rendered source mutation occurred.
  This is a support-code blocker fix only; round-trip verification was not
  required.
* Next recommendation: run Pandora `clean-run` once to establish the trial
  baseline, then inspect candidates using normal loop/query surfaces.

### 015-002: Listing element IDs from normalized rows

* Candidate: RSSET/app-base provenance report for raw A6 displacement
  `$01D8(a6)` at source offset `$00000552`.
* Evidence: normalized listing rows exposed `row_key` but
  `listing_element_contexts` built `row:displacement:...` element ids. The
  `/commands` element-context route rejected that advertised id; manually
  substituting the row key made the same command catalog available.
* Command: fixed listing element identity formation to prefer normalized
  `row_key`.
* Verifier: `tests\test_listing_context.py -q` passed, focused `ruff` passed,
  and the original Pandora element catalog probe now accepts
  `s0:00000552:instruction:338:displacement:1:operand`.
* Timing: focused pytest 0.04s; Pandora listing open/query about 5s.
* Result: element-context command discovery is now usable from normalized
  listing rows. The `$01D8(a6)` catalog exposes read-only provenance reports
  and `rsset.binding.report`, but no bind command yet.
* Review: this fixes a durable command-surface identity mismatch. It does not
  mutate Pandora source or Manual Action Log state; round-trip verification was
  not required.
* Next recommendation: run the report-only provenance/RSSET command for the A6
  cluster and stop if it lacks accepted base evidence for a safe binding.

## Deferred Work Log

Use this section as the live holding area for worthwhile observations found
while working the current Pandora action. The goal is to avoid derailing the
active task without losing follow-up work.

Each entry should include:

* date or iteration id,
* source location or command/report that exposed it,
* short evidence summary,
* why it is deferred,
* recommended next action,
* pull-in condition,
* status: `open`, `accepted`, `fixed`, `invalid`, or `out_of_scope`.

Review this log at candidate-family boundaries and blockers. Pull in items that
now unblock progress, recur, hit a verifier/performance threshold, or require
user/domain review. Otherwise keep them logged, create/attach a focused issue,
or mark why they are not part of proposal 015.

Triage by scope:

* general action-surface/tooling gaps: update/create a `014-*` issue,
* Pandora-specific reversing leads: keep here,
* reusable loop/process improvements: create a new issue only if they outgrow
  015,
* performance findings: keep here first, issue if not fixed immediately.

### Open Entries

#### D001: Stored callback slot should lead code discovery

* Date/source: initial Pandora source-quality review.
* Location:
  `targets\amiga_disk_pandora-1988-firebird\targets\amiga_raw_pandora_3e1ee0f1_bk_00_000000e8\pandora_3e1ee0f1_bk_00_000000e8.s`,
  around `abs_0_000108E4`, `app_0360`, and `abs_0_00010E14`.
* Evidence:
  * interrupt handler loads `app_0360(a6)` into `a0` and executes `jsr (a0)`,
  * several sites store PC-relative labels into `app_0360(a6)`,
  * at least one stored target, `abs_0_00010E14`, still renders as `dc.b`.
* Expected source improvement:
  * classify `app_0360` as a code/callback pointer slot,
  * surface assignments to it as code-target candidates,
  * convert accepted callback targets to code only through supported
    classification actions and exact round-trip verification.
* Missing tool/report/action:
  * query/report for "stored pointer later consumed by indirect jump/call",
  * candidate evidence that links the store site, slot identity, load site, and
    indirect control-transfer use.
* Pull-in condition: work on RSSET/app-slot provenance reaches function-pointer
  typed slots, or code/data classification stalls on stored callback targets.
* Status: open.

#### D002: Orphan-code heuristics should be evidence-led

* Date/source: initial Pandora source-quality review.
* Location: `abs_0_00010E14`, currently rendered as bytes after a store into
  `app_0360(a6)`.
* Evidence:
  * bytes begin with common 68000 code patterns such as `$41FA`,
  * a mid-block `$4E75` appears,
  * the stronger evidence is the callback-slot store/load/use chain in D001.
* Expected source improvement:
  * reduce missed code blocks without blindly converting arbitrary decodable
    bytes,
  * present "likely code" as a reviewable classification candidate with the
    reason chain.
* Missing tool/report/action:
  * orphan-code scoring that starts from durable control/data-flow evidence,
    then uses decode plausibility only as supporting evidence,
  * false-positive checks for all-zero garbage patterns, post-68000
    instructions, unexpected F-line/A-line use, and register-use anomalies.
* Pull-in condition: D001 produces stored code-pointer candidates whose targets
  are still rendered as data.
* Status: open.
* Scope note: subordinate to D001 during this proposal. Do not run a broad
  orphan-code heuristic pass for Pandora unless callback-slot evidence first
  produces concrete missed-code candidates.

#### D003: RSSET field coverage is inconsistent around app table state

* Date/source: initial Pandora source-quality review.
* Location: initialization and use of the `$01B8-$01F0` A6-relative cluster,
  including the sequence near `abs_0_00019F26`:

```asm
	move.l #$1AAFE,app_01F0(a6)
	clr.b app_020B(a6)
	moveq.l #51,d0
	move.w d0,$01BC(a6)
```

* Evidence:
  * nearby offsets render as `app_01F0(a6)` and `app_020B(a6)`,
  * related offsets such as `$01BC(a6)`, `$01BA(a6)`, `$01BE(a6)`, and
    `$01D8(a6)` still appear raw in related table/indexing code.
* Expected source improvement:
  * report a coherent app/RSSET range candidate for the cluster,
  * bind/refine field names and widths from same-flow/same-displacement
    evidence once proposal 014 support allows it.
* Missing tool/report/action:
  * RSSET report that explains why adjacent offsets were named while these
    remained raw,
  * candidate grouping for repeated raw A6 offsets in a proven app-base
    lifetime.
* Pull-in condition: first Pandora RSSET/app-base pass begins.
* Status: open.

#### D004: Rendered memory map mixes bootstrapping and runtime facts

* Date/source: initial Pandora source-quality review.
* Location: generated header memory map at top of the rendered source.
* Evidence:
  * header lists policy, discovered-copy, conflicting-copy, suppressed, and
    materialized entries in one flat list,
  * Pandora bootstrap copies `abs_0_00010028` to `$300` as a stub, then copies
    the loaded payload to `$10000` and enters around `$1046A`,
  * some suppressed entries appear to be duplicate off-by-one discovered copies.
* Expected source improvement:
  * separate bootstrap/copy evidence from the end-user runtime memory view,
  * present entrypoint, copied stub, materialized runtime payload, and conflicts
    with clearer labels and confidence.
* Missing tool/report/action:
  * memory-map report with distinct categories for copy policy, discovered copy
    evidence, runtime occupancy, entrypoints, and unresolved/conflicting copies.
* Pull-in condition: none for the normal Pandora reversing loop. Promote to a
  separate memory-model/tooling issue if memory-map confusion blocks
  reproduction diagnostics or runtime-address interpretation.
* Status: out_of_scope for the Pandora reversing loop.

#### D005: Runtime memory use should include accessed absolute regions

* Date/source: initial Pandora source-quality review.
* Location: runtime/app-base setup and low-memory absolute stores.
* Evidence:
  * `abs_0_0001046A` loads `$000039FC` as the app/RSSET base,
  * generated equates already identify runtime-like addresses such as
    `blitter_source_00077D00`,
  * repeated stores such as `move.l #$24C28,$64C0.w` write runtime-looking
    values into a low-memory absolute slot.
* Expected source improvement:
  * report known runtime-used regions from access evidence, not only copy-map
    evidence,
  * distinguish app-base memory, hardware/blitter buffers, low-memory slots, and
    source-payload runtime references.
* Missing tool/report/action:
  * runtime-address-use report for absolute stores/loads and immediate values
    that point into known source/runtime ranges.
* Pull-in condition: none for the normal Pandora reversing loop. Promote to a
  separate memory-model/tooling issue if runtime-address-use reporting becomes a
  blocker for data/global naming or interpreted references.
* Status: out_of_scope for the Pandora reversing loop.

#### D006: Immediate runtime references need better detection

* Date/source: initial Pandora source-quality review.
* Location: `abs_0_0001A12E`.

```asm
	move.l #$5C72A,abs_0_0005C71E.l
```

* Evidence:
  * immediate `$5C72A` falls into the rendered source/runtime address space,
  * destination is an absolute location in the same target address family.
* Expected source improvement:
  * surface immediate values that likely reference source/runtime locations,
  * allow accepted values to become symbolic refs or data-block interpreted refs
    only when the value/source family and verifier support are present.
* Missing tool/report/action:
  * query/report for immediate constants that match known runtime/source ranges,
    with source-family and conflict status.
* Pull-in condition: data-block reference interpretation or source/global naming
  work starts on Pandora.
* Status: open.

#### D007: A5 hardware-base lifetime proof

* Date/source: follow-up review of Pandora source-quality notes.
* Location: repeated A5-relative hardware-looking operands across the rendered
  source, alongside proven `_custom` base setup such as `lea.l _custom.l,a5`.
* Evidence:
  * many accesses already render as `_custom` fields when base evidence is
    direct,
  * repeated raw `$xxxx(a5)` operands remain where the base lifetime is not yet
    proven strongly enough,
  * offset matching alone is unsafe because A5 is also used for non-hardware
    pointers in other routines.
* Expected source improvement:
  * report A5 lifetime ranges that are proven to be hardware-base `_custom`,
  * render hardware register names only for accepted lifetimes,
  * leave unknown or conflicting A5-relative operands raw/report-only.
* Missing tool/report/action:
  * provenance report for hardware-base register lifetimes, including
    definitions, uses, clobbers, save/restore boundaries, and conflicts.
* Pull-in condition: hardware-base provenance becomes the active candidate
  family after RSSET/custom-struct/data-block work, or raw A5 accesses block a
  concrete source-converging action.
* Status: open.

## Stop Conditions

Stop and report rather than continuing when:

* hygiene finds unknown target-local files,
* the next best source-converging action lacks supported command/verifier
  coverage,
* evidence is conflicting and cannot be classified or overridden safely,
* the path/lifetime scope is not provable,
* verification fails without a clear fix,
* only proof, fallback, placeholder, or makework actions remain.

If exact round-trip fails after a target action, diagnose and fix only if the
failure is clearly caused by the just-applied action or support code. Otherwise
stop with the failing action, verifier output, and rollback/cleanup
recommendation. Do not stack further target edits on a failed round-trip.

Prefer corrective MAL actions or supported cleanup commands for rollback. Use
`clean-run` only for initial baseline setup or abandoning resettable trial state,
not as normal rollback.

## Final Retrospective

At the end of the proposal 015 trial, record:

* source-quality improvements made,
* support-code fixes made,
* performance findings and fixes,
* deferred work remaining,
* proposal 014 surfaces that worked well,
* proposal 014 surfaces that failed or need redesign,
* whether Pandora should continue as an ongoing target after the trial.

## References

* Reversing loop: `docs\agents\reversing-loop.md`
* Capability map:
  `docs\proposals\014-source-converging-manual-action-surface.md`
