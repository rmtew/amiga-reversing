# Proposal 015: Agent reversing Pandora target

The scope of this proposal is that an agent runs the reversing loop using the
editing features added in proposal 014.

Status: closed after the 015-034 Pandora trial and final review.

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
6. Data/global naming only when the proposed name adds target semantics from
   contents, xrefs, or call context; type/class plus address is a framework
   naming-policy concern, not Pandora iteration progress.
7. EQU/value representation only through the separate semantic actions defined
   by proposal 014 boundaries.

Work depth-first by candidate family. Stay with the best family until it
produces real source improvement, saturates, or hits a blocker, then move to the
next family. Do not chase isolated raw displacements unless they unlock broader
base, structure, type, or naming improvement.

When generic `run-one` candidates become mechanical, low-value, or framework
policy work, switch to a Manual Review Items pass before continuing ordinary
planner iteration. Inspect the same review list surfaced by the Review dialog or
`inspect`, then choose only items that identify concrete Pandora source-quality
blockers: orphan code candidates, unreconciled data ranges, suspicious decode,
manual-seed conflicts, label scope conflicts, reproduction mismatches, and
typed/classification conflicts. For each candidate, collect the durable review
item id and evidence fingerprint, inspect surrounding listing/xrefs, discover
commands from the review item or affected range, and execute only if durable
identity, command support, type-specific verifier, and exact round-trip gates
are present. Reducing the review count is progress only when the underlying
source issue is resolved through a structured verified fact.

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

Typed data-backed names must still be semantic. A data class can make a row
safe to operate on, but renaming solely from class and address, for example
`string_XXXXXXXX`, `lookup_table_XXXXXXXX`, or `copper_list_XXXXXXXX`, is not
itself accepted Pandora progress unless the name captures program meaning from
the surrounding use. Treat generic class styling as an analyzer/framework
improvement or deferred work item.

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

### 015-003: Planner skipped generic runtime-address names

* Candidate: normal Pandora `run-one` after the exact round-trip baseline.
* Evidence: before the planner fix, the best `data_symbol.rename` candidate was
  `runtime_address_00000300`, derived only from an unclassified runtime address.
  That would add a low-value generic label while typed listing evidence existed
  for data such as `copper_list_000109EA`.
* Command: changed listing data-symbol planning so unclassified runtime-address
  refs do not create autonomous rename candidates. Runtime refs with a data
  class still produce typed names.
* Verifier: `tests\test_reversing_loop.py -q` passed, focused `ruff` passed,
  and Pandora `run-one` selected `data_symbol.rename` for hunk 0 `$000009EA`
  to `copper_list_000109EA`.
* Timing: focused pytest 2.55s; `run-one` 11.2s including command execution
  and exact reproduction.
* Result: the Manual Action Log now has one local rename action for
  `copper_list_000109EA`, and `reproduction.json` reports `status: exact`,
  `stale: false`, rebuilt SHA matching original.
* Review: the implementation blocks only no-class runtime-address names. It
  preserves typed runtime/data candidates and avoids committing target-local
  `.project.json` timestamp churn.
* Next recommendation: continue with typed data-block names or representation
  candidates; keep RSSET/app-base mutation paused until base evidence exists.

### 015-004: Named blitter source data reference

* Candidate: next Pandora `run-one` after `copper_list_000109EA`.
* Evidence: dry-run selected a typed `data_symbol.rename` from listing data-ref
  evidence at `s0:000007D2:instruction:509`, hunk 0 `$00057D00`, with data
  class `blitter_source`.
* Command: executed `data_symbol.rename` to `blitter_source_00077D00`.
* Verifier: command execution succeeded, Manual Action Log sequence 2 was
  appended locally, and `reproduction.json` reports `status: exact`,
  `stale: false`, rebuilt SHA matching original.
* Timing: dry-run 7.3s; execution 11.4s including exact reproduction.
* Result: rendered source can now refer to the blitter-source data location by
  a typed symbol instead of an anonymous runtime address.
* Review: this is a narrow output-affecting source-quality improvement with a
  supported command and exact round-trip. No support-code change was needed.
* Next recommendation: continue typed data-block renames while they remain
  data-class backed; inspect representation candidates before executing them.

### 015-005: Block data-ref rename churn and same-start duplicates

* Candidate: next Pandora dry-run after `blitter_source_00077D00`.
* Evidence: the planner first selected `data_symbol.rename_existing` at the
  already named `$00057D00`, changing `blitter_source_00077D00` to
  `blitter_destination_00077D00` from another use-site. After blocking that,
  it exposed the earlier copper-list rename as an open-ended same-start symbol
  that the row-backed candidate did not recognize.
* Command: changed data-ref candidates to skip conflicting existing names, and
  changed data-symbol existing-name lookup to treat an open-ended same-start
  data symbol as owning that address.
* Verifier: `tests\test_reversing_loop.py -q` passed with 281 tests, focused
  `ruff` passed, and Pandora dry-run now selects row-backed
  `data_symbol.rename_existing` for hunk 0 `$000009EA` to
  `copper_list_000209EA`.
* Timing: focused pytest 2.69s; final dry-run 7.3s.
* Result: the loop no longer churns an existing symbol between conflicting
  use-site data classes and no longer proposes duplicate same-start data symbols
  when an open-ended manual symbol already exists.
* Review: this corrects a real oversight found during post-commit iteration.
  The earlier data-ref copper-list action preserved exact round-trip but did
  not visibly improve the rendered label; the next mutation should use the
  row-backed data definition candidate instead.
* Next recommendation: execute the row-backed `copper_list_000209EA` correction
  and require exact round-trip plus visible projected label/source improvement.

### 015-006: Stale locator availability should not crash fallback

* Candidate: executing the row-backed `copper_list_000209EA` correction after
  dry-run.
* Evidence: `run-one` crashed while checking alternate command availability:
  `/commands` raised `missing_locator` for a stale row key from the candidate
  list instead of returning an unavailable command.
* Command: changed command availability probing to return an error payload for
  `CommandContractError`, letting planner fallback continue or block cleanly.
* Verifier: `tests\test_reversing_loop.py -q` passed with 282 tests, focused
  `ruff` passed.
* Timing: focused pytest 2.46s.
* Result: stale locator candidates are treated as unavailable instead of
  aborting the reversing loop.
* Review: support fix only; no Pandora mutation occurred.
* Next recommendation: rerun the row-backed typed data correction.

### 015-007: Named row-backed lookup table

* Candidate: next available typed data-backed Pandora action after stale
  locator fallback was fixed.
* Evidence: planner selected a data row at `s0:00000CA0:data:819`, hunk 0
  `$00000CA0-$00000CC0`, data class `lookup_table`.
* Command: executed `data_symbol.rename` to `lookup_table_00020CA0`.
* Verifier: Manual Action Log sequence 3 was appended locally;
  `reproduction.json` reports `status: exact`, `stale: false`, rebuilt SHA
  matching original.
* Timing: execution 12.7s including exact reproduction.
* Result: rendered source now uses `lookup_table_00020CA0` at the indexed
  `movea.l lookup_table_00020CA0(pc,d2.w),a1` reference and at the table
  definition.
* Review: pure Pandora iteration report; no support-code change. This is a
  typed data-backed improvement and RSSET/app-base remains report-only.
* Next recommendation: continue with typed data-backed candidates until the
  planner reaches non-data or unsupported actions.

### 015-008: Named row-backed copper list

* Candidate: next available typed data-backed Pandora action after the lookup
  table iteration.
* Evidence: planner selected a data row at `s0:00000ED8:data:929`, hunk 0
  `$00000ED8-$00000F54`, data class `copper_list`.
* Command: executed `data_symbol.rename` to `copper_list_00020ED8`.
* Verifier: Manual Action Log sequence 4 was appended locally;
  `reproduction.json` reports `status: exact`, `stale: false`, rebuilt SHA
  matching original.
* Result: rendered source now uses `copper_list_00020ED8` at the copper-list
  definition and the `lea.l copper_list_00020ED8(pc),a0` use feeding
  `cop1lc(a5)`.
* Review: pure Pandora iteration report; no support-code change. This remains
  typed data-backed work, and RSSET/app-base evidence remains report-only until
  accepted base evidence exists.
* Next recommendation: continue typed data-backed candidates until saturation,
  then inspect the next non-data-backed family before mutating.

### 015-009: Row-backed credit string exposed generic-name churn

* Candidate: next executed typed data-backed Pandora action after the row-backed
  copper-list iteration.
* Evidence: planner selected a data row at `s0:0000109E:data:1018`, hunk 0
  `$0000109E-$000010B9`, data class `string`.
* Command: executed `data_symbol.rename` to `string_0002109E`.
* Verifier: Manual Action Log sequence 5 was appended locally;
  `reproduction.json` reports `status: exact`, `stale: false`, rebuilt SHA
  matching original.
* Result: rendered source now uses `string_0002109E` at the string definition
  for the visible credit text and at the `lea.l string_0002109E(pc),a3` use
  before the string rendering call.
* Review correction: this was exact and type-safe, but it was still a
  mechanical class/address rename. It should not be used as a model for future
  Pandora work. Future target renames should apply semantic program meaning,
  for example a credit-text name, or defer generic `string_` styling to the
  analyzer/framework.
* Observation: the immediately preceding dry run reported a different typed
  data-backed candidate than the execute pass applied. Because the executed
  action was still row-backed, command-supported, and exactly verified, this did
  not block Pandora progress. Logged as deferred tooling follow-up D008.
* Review: pure Pandora iteration report; no support-code change. RSSET/app-base
  evidence remains report-only until accepted base evidence exists.
* Next recommendation: continue typed data-backed candidates only when the
  action adds semantic target meaning; otherwise implement the generic naming
  policy once or log it as deferred framework work.

### 015-011: Planner skips generic typed-data names

* Candidate: Pandora dry-run after 015-010's semantic-name policy update.
* Evidence: `run-one --dry-run` still selected
  `data_symbol.rename_existing` for row `s0:000009EA:data:656`, hunk 0
  `$000009EA`, name `copper_list_000209EA`. The name was only
  `<data_class>_<runtime_address>` styling, and the same dry-run contained many
  similar `string_XXXXXXXX` candidates.
* Command: changed planner skip policy so `data_symbol.rename` and
  `data_symbol.rename_existing` candidates whose proposed name exactly matches
  the generated class/address form remain visible in ranked/skipped candidates
  but are not eligible for autonomous `run-one` execution.
* Verifier: `tests\test_reversing_loop.py -q` passed with 284 tests; focused
  `ruff` passed; the original Pandora dry-run now marks the copper-list and
  string candidates with stop reason
  `data symbol name is only class/address styling`.
* Timing: focused pytest 2.57s; focused ruff 0.3s; Pandora dry-run 7.0s.
* Result: target iterations no longer spend mutations on generic typed-data
  label styling. The next selected candidate is `representation.character` for
  `andi.b #63,d1`.
* Review: support-code fix only; no Pandora mutation occurred and exact
  round-trip was not required. The surfaced representation candidate appears
  syntax-driven rather than semantic, because `#63` in `andi.b #63,d1` is likely
  a bit mask, not a question-mark character.
* Next recommendation: fix or block generic printable-immediate character
  representation before executing another Pandora mutation.

### 015-012: Character representation skips bit masks

* Candidate: printable-immediate representation candidate surfaced by 015-011.
* Evidence: Pandora dry-run selected `representation.character` for
  `s0:00000C28:instruction:760`, source text `andi.b #63,d1`, proposing to
  render the mask value as `#'?'`.
* Command: changed listing representation candidate mining to skip printable
  byte immediates used by bitwise immediate opcodes `andi.b`, `eori.b`, and
  `ori.b`.
* Verifier: `tests\test_reversing_loop.py -q` passed with 285 tests; focused
  `ruff` passed; the original Pandora dry-run now selects the next
  representation candidate at `s0:00006088:instruction:3320`, source text
  `subi.b #32,d0`.
* Timing: focused pytest 2.88s; focused ruff 0.9s; Pandora dry-run 7.0s.
* Result: the loop no longer proposes character rendering for obvious bit-mask
  immediates. Arithmetic ASCII-offset candidates remain eligible.
* Review: support-code fix only; no Pandora mutation occurred and exact
  round-trip was not required. The fix is intentionally narrow to the observed
  false positive.
* Next recommendation: inspect the `subi.b #32,d0` context; execute only if the
  surrounding flow supports ASCII/font-index semantics.

### 015-013: Render ASCII space in lowercase fold

* Candidate: Pandora representation candidate at
  `s0:00006088:instruction:3320`.
* Evidence: listing window around hunk 0 `$00006088` shows
  `cmp.b #$61,d0`, branch if below, then `subi.b #32,d0`, followed by
  `lsl.w #3,d0` and `add.l app_01E8(a6),d0` before drawing. This supports
  ASCII lowercase-to-uppercase/font-index semantics for subtracting space.
* Command: executed `representation.character` for the immediate value 32 at
  `subi.b #32,d0`.
* Verifier: Manual Action Log sequence 6 was appended locally; durable payload,
  semantic reload, projected listing row, and exact round-trip all passed.
  `reproduction.json` reports `status: exact`, `stale: false`, rebuilt SHA
  matching original.
* Timing: listing context query 3.9s; command execution 11.4s including exact
  reproduction; projection check 3.8s.
* Result: projected source now renders `subi.b #' ',d0`, making the ASCII
  folding intent visible at the font-index calculation.
* Review: output-affecting Pandora mutation only. Target-local Manual Action
  Log state remains local; `.project.json` timestamp churn is not meaningful
  and should not be committed.
* Next recommendation: continue with the next representation candidate only
  after checking nearby comparison/arithmetic context; otherwise move to the
  next non-generic candidate family.

### 015-014: Render ASCII space in font table index

* Candidate: Pandora representation candidate at
  `s0:00006160:instruction:3412`.
* Evidence: listing context shows a byte read from `(a3)+`, zero terminator
  check, `subi.b #32,d0`, indexed load from `$0(a4,d0.w)`, then scaling and
  adding `app_01F0(a6)` before glyph/render work. This supports space-based
  ASCII-to-font-table indexing.
* Command: executed `representation.character` for the immediate value 32 at
  `subi.b #32,d0`.
* Verifier: Manual Action Log sequence 7 was appended locally; durable payload,
  semantic reload, projected listing row, and exact round-trip all passed.
  `reproduction.json` reports `status: exact`, `stale: false`, rebuilt SHA
  matching original.
* Timing: listing context query 3.7s; command execution 11.1s including exact
  reproduction; projection check 3.7s.
* Result: projected source now renders `subi.b #' ',d0`, making the
  string-to-font-index mapping clearer.
* Review: output-affecting Pandora mutation only. Target-local Manual Action
  Log state remains local; `.project.json` timestamp churn is not meaningful
  and should not be committed.
* Next recommendation: inspect the next `subi.b` representation candidate before
  execution; repeated ASCII/font-index candidates may justify a stronger
  grouped report or candidate rationale.

### 015-015: Seed callback-driven orphan code from review items

* Candidate: Pandora Manual Review Items pass for medium-confidence
  `orphan_code_candidate` entries.
* Evidence: after opening the listing artifact, the Review surface reported
  111 items: 9 `orphan_code_candidate` entries and 102 low-confidence
  `unreconciled_data_range` entries. The actionable entries were selected from
  durable review item ids plus listing context, not from count reduction:
  * `orphan_code_candidate:h0:$00000aa2-$00000ab8`, fingerprint
    `4f09083a4463059f7464d0a751b6caf34d6d4e71da99e8ee59730625c413dc86`,
    is loaded with `lea.l abs_0_00010AA2(pc),a0` and stored to
    `app_0360(a6)`, the callback slot later reached by indirect `jsr (a0)`.
  * `orphan_code_candidate:h0:$00000d9c-$00000dae`, fingerprint
    `8a0be6cfc1b01cec4afa9e0c391678fad9eb7153d0f319ce8bf901e010e30dc2`,
    is loaded into `a3`; the accepted drawing dispatch at
    `abs_0_00010C58` reaches continuation code through `jmp (a3)`.
* Command: executed `review.seed.code` for both review item ids through the
  command catalog.
* Verifier: Manual Action Log count advanced locally from 7 to 9; both
  manual-seed state checks passed; exact reproduction was rerun after each
  seed and remained `status: exact`, `stale: false`, rebuilt SHA matching the
  original.
* Timing: review summary/listing query about 5.4s; first command plus exact
  reproduction 8.7s; second command plus exact reproduction 8.7s.
* Result: rendered source now shows the callback chain at
  `abs_0_00010AA2`/`abs_0_00010AB8` and the drawing continuation at
  `abs_0_00010D9C` as instructions instead of raw bytes. Review count dropped
  from 111 to 109 because the underlying code classification issues were
  resolved.
* Review: remaining orphan-code review items still need item-specific evidence.
  Several are terminal-decode-only or adjacent to plausible code, but command
  availability alone is not sufficient. The `abs_0_00010DAE` continuation was
  exposed by the second seed but is not currently a surfaced orphan-code review
  item, so it was left unchanged.
* Next recommendation: continue the Manual Review Items pass with the remaining
  orphan entries; execute only items with concrete control-flow, callback,
  dispatch-table, or same-family source context plus the manual-seed verifier.

### 015-016: Seed handler-stub orphan code from review items

* Candidate: remaining medium-confidence `orphan_code_candidate` entries in
  the `abs_0_0005D2FE`/`abs_0_0005D330` handler-dispatch region.
* Evidence: three review items were embedded in a run of accepted code stubs
  that set `d0` selector values and branch to `abs_0_0005D330`, followed by
  adjacent accepted state/handler routines:
  * `orphan_code_candidate:h0:$0004d304-$0004d30a`, fingerprint
    `c2d9aaf1469ee3730611e381723c21830eb3397013de9cb66cebc16263ab90dc`,
    decodes as `move.w #$300,d0` then `bra.b abs_0_0005D330`.
  * `orphan_code_candidate:h0:$0004d320-$0004d326`, fingerprint
    `9cbe2b6d3ef83dbf01f5d309bf166db2ec44f98bc338a931d4fc3036741eaa20`,
    decodes as `move.w #$30F,d0` then `bra.b abs_0_0005D330`.
  * `orphan_code_candidate:h0:$0004d34c-$0004d368`, fingerprint
    `6d66834fa6e036c53a5bd3cf536a563e19953acbce60fbb95c914ad9317b5cbb`,
    decodes as a state-gated handler that sets `app_033D(a6)`, calls
    `abs_0_0005D7DE`, and returns before the accepted routine at
    `abs_0_0005D368`.
* Command: executed `review.seed.code` for all three durable review item ids.
* Verifier: Manual Action Log count advanced locally from 9 to 12; each
  manual-seed state check passed; exact reproduction was rerun after each seed
  and remained `status: exact`, `stale: false`, rebuilt SHA matching the
  original.
* Timing: three command/reproduction/verification cycles took about 20.2s
  total.
* Result: rendered source now shows `abs_0_0005D304`,
  `abs_0_0005D320`, and `abs_0_0005D34C` as code. Review count dropped from
  109 to 106, leaving four `orphan_code_candidate` entries.
* Review: this remained within the surfaced review-item path and did not clear
  any item by acknowledgement. The larger raw region after `abs_0_0005D37E`
  still looks like plausible handler code, but there is no current surfaced
  review item for most of it; broad conversion remains out of scope without a
  durable item/evidence path.
* Next recommendation: inspect the remaining four orphan-code review items and
  record blockers for any item that has only terminal-decode evidence.

### 015-017: Block remaining terminal-decode-only review items

* Candidate: final Manual Review Items pass over the four remaining
  `orphan_code_candidate` entries and the low-confidence
  `unreconciled_data_range` list.
* Evidence: the Review surface now reports 106 items, including four orphan
  code candidates:
  * `orphan_code_candidate:h0:$00001094-$0000109e`, fingerprint
    `73a73a274dfa43adf52bf5543003daabde3eae3262bd235f819bbacdd5d7d3f9`,
    sits between an accepted `rts` and credited text data.
  * `orphan_code_candidate:h0:$00002656-$00002664`, fingerprint
    `8e4ecf8c5246b7fcd1f2478ada78dd549ba43e6e0888f5adbfb23f4394968917`,
    decodes as a short interrupt-level/callback-slot helper but has no
    accepted inbound reference.
  * `orphan_code_candidate:h0:$00006014-$0000602a`, fingerprint
    `4533eb5476c056a2f2d5634d706dd9bb548a59ea21ae8b37733949437a16e629`,
    is part of a plausible bit-test helper sequence but has no accepted
    inbound reference.
  * `orphan_code_candidate:h0:$0004b0ce-$0004b0ea`, fingerprint
    `faa21cb8c92384da034d56ed2901619f446e1e7b0404541a6439caf88d4bfb53`,
    begins a large plausible code/data region after pointer-store setup, but
    the selected item still has no accepted inbound reference.
* Command: no mutation. Catalogs expose `review.seed.code` and
  `review.resolve.data_or_padding` for orphan items, and many data seed roles
  plus `review.resolve.opaque_data` for unreconciled data ranges.
* Verifier: not run for a mutation. The exact reproduction report remains
  `status: exact`, `stale: false` from 015-016.
* Timing: listing search for accepted references to the four labels took about
  4.8s; review item refresh took about 3.7s.
* Result: no remaining item was cleared. Command availability alone would only
  reduce review count; it would not add a verified source fact.
* Blockers:
  * orphan code items need accepted inbound control-flow, callback-slot,
    dispatch-table, or same-family evidence before `review.seed.code` is safe,
  * data ranges need type-specific evidence before selecting a data role or
    resolving as opaque data,
  * the callback-slot/stored-pointer report in D001 remains the right support
    path for items like `$00002656`.
* Review: this pass intentionally stops broad orphan-code conversion. The
  supported action/verifier path works when evidence is concrete, but the
  remaining review items do not yet meet the evidence threshold.
* Next recommendation: pause Manual Review Item mutation here; resume with a
  targeted stored-pointer/callback-slot report or another source-converging
  candidate family rather than clearing terminal-decode-only items.

### 015-018: Report callback-slot targets before mutation

* Candidate: D001 stored callback slot support for `app_0360`, after the
  Manual Review Items pass stopped on missing callback evidence.
* Evidence: added `reversing_loop callback-report`, backed by listing rows and
  Review item identities. The Pandora report finds one `app_0360` consumer:
  `movea.l app_0360(a6),a0` at `s0:000008FE:instruction:587`, followed by
  `jsr (a0)` at `s0:00000902:instruction:588`.
* Result: the report finds seven PC-relative assignments into `app_0360`.
  Six already target rendered instructions. One concrete missed target remains:
  `lea.l abs_0_00010E14(pc),a0` at `s0:00000E0A:instruction:925`, stored by
  `move.l a0,app_0360(a6)` at `s0:00000E0E:instruction:926`, while
  `s0:00000E14:data:929` still renders as `dc.b`.
* Blocker: the matched Review item for `$00000e14-$00000ed8` is
  `unreconciled_data_range`, fingerprint
  `82394e9037d6abc31417c8c3a395470b04581fee5f3328c9f78b05788f601f91`, not
  `orphan_code_candidate`. The report therefore marks the action blocked
  (`review_item_is_not_code_classification`) instead of treating a data-range
  review item as safe for `review.seed.code`.
* Command/verifier: no Pandora mutation. Support code was verified with
  `ruff check amiga_reversing\disasm\callback_slot_report.py
  amiga_reversing\reversing_loop.py tests\test_callback_slot_report.py` and
  `python -m pytest tests\test_callback_slot_report.py
  tests\test_reversing_loop.py -q` (`288 passed`).
* Review: this fixes the missing report surface from D001 without clearing any
  review item. It also exposes the next real blocker: either callback-backed
  targets need a code-classification review item, or the row/range
  classification path needs an explicit verifier-backed rule for this evidence
  chain.
* Next recommendation: before converting `abs_0_00010E14`, choose the clean
  supported path: promote callback-backed data targets into durable
  `orphan_code_candidate` review items, or document/use an explicit
  `row.seed.code` verifier path for callback report evidence.

### 015-019: Classify the callback-reached palette handler

* Candidate: `abs_0_00010E14`, the remaining `app_0360` stored target found by
  `callback-report`.
* Evidence: `s0:00000E0A:instruction:925` loads
  `abs_0_00010E14(pc)` into `a0`; `s0:00000E0E:instruction:926` stores `a0` to
  `app_0360(a6)`; the interrupt path reads `app_0360(a6)` into `a0` and calls
  `jsr (a0)`.
* Command: executed `row.seed.code` on durable listing row
  `s0:00000E14:data:929`. This used the row classification path rather than
  `review.seed.code`, because the surfaced Review item was still
  `unreconciled_data_range`, not `orphan_code_candidate`.
* Verifier: Manual Action Log count advanced locally from 12 to 13; manual seed
  state matched `hunk: 0`, `addr: 3604`, `end: 3620`, `kind: code`; exact
  reproduction reran and remained `status: exact`, `stale: false`, rebuilt SHA
  matching the original
  `70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
* Result: `abs_0_00010E14` now renders as code. The newly exposed code includes
  a palette/COP register-looking loop, then further callback-slot stores to
  `abs_0_00010E4E` and back to `abs_0_00010DE0`; those new stored targets also
  render as code. Refreshing `callback-report` for `app_0360` now reports nine
  assignments and `concrete_missed_code_target_count: 0`.
* Review: this did not clear a Review item by count reduction. It resolved the
  concrete source issue found by D001 with a supported row classification
  command plus manual-seed and exact-round-trip verification.
* Observation: after the seed, a listing `source_offset` window for `$0E14`
  could anchor earlier than the requested address; `_listing_all_rows` still
  showed the correct rows. Record this as a query-surface follow-up if it
  repeats.

### 015-020: Name the tilemap base app slot

* Candidate: D003 RSSET/app-base coverage for the raw `$01BE(a6)` slot.
* Evidence: `$01BE(a6)` is initialized once with `move.l #$4000,$01BE(a6)` at
  `s0:00009EE0:instruction:7149`, then used as a long base pointer in tile or
  address calculations: `movea.l $01BE(a6),a4` and
  `add.l $01BE(a6),d0` in the blitter setup around `s0:00006752`.
* Command: executed `target.rsset_region.add` with
  `layout_name: app`, `base_symbol: __amiga_app_base__`, `offset: $01BE`,
  `size: 4`, `storage_kind: pointer`, `symbol: app_tilemap_base`.
* Verifier: Manual Action Log count is 14; semantic reload matched
  `catalog-rsset-region-app-01BE`; exact reproduction reran and remained
  `status: exact`, rebuilt SHA matching the original
  `70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
* Result: rendered source now defines `app_tilemap_base RS.L 1`, renders
  `move.l #$4000,app_tilemap_base(a6)`, and replaces repeated raw `$01BE(a6)`
  uses with `app_tilemap_base(a6)`.
* Review: this used a target-level RSSET region command rather than selected
  `rsset.binding.report`, because selected raw-displacement reports still lack
  accepted base evidence and remain read-only. Adjacent dimension/index fields
  such as `$01BA`, `$01BC`, `$01C2`, and `$01C4` look related but need their own
  evidence and naming pass.

### 015-021: Name tilemap row and column app slots

* Candidate: D003 RSSET/app-base coverage for the adjacent raw `$01BA(a6)` and
  `$01BC(a6)` word fields.
* Evidence: the scroll/update flow stores clamped/scaled coordinates into these
  fields: `$01B8(a6)` is shifted by four and stored to `$01BC(a6)`, while
  `$01B6(a6)` is shifted by four and stored to `$01BA(a6)` around
  `s0:00007D86`. The blitter/tile calculation then multiplies `$01BC(a6)` by
  the row stride, adds `$01BA(a6)`, scales the result, and adds
  `app_tilemap_base(a6)` around `s0:0000675E`.
* Command: executed `target.rsset_region.add` for `$01BA` as
  `app_tile_column` and `$01BC` as `app_tile_row`, both with
  `layout_name: app`, `base_symbol: __amiga_app_base__`, and `size: 2`.
  Follow-up `target.rsset_region.edit` actions removed the weak
  `storage_kind: scalar` hint after review.
* Support fix: the first projection rendered both 2-byte manual app regions as
  `RS.L 1`. Fixed `m68k_render_ir.c` so canonical app-layout policy regions
  (`layout_name: app`, `base_symbol: __amiga_app_base__`) keep their explicit
  region size when formatting app RSSET directives. Added a C regression for a
  2-byte app policy region without an app-layout flag.
* Verifier: Manual Action Log count is 18; semantic reload shows `$01BA` and
  `$01BC` effective metadata with `size: 2`; `cmd /c src\precommit.bat`
  passed; Pandora exact reproduction reran and remained `status: exact`,
  `stale: false`, rebuilt SHA
  `70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
* Result: rendered source now defines `app_tile_column RS.W 1`,
  `app_tile_row RS.W 1`, and `app_tilemap_base RS.L 1`. Listing projection
  shows four `app_tile_column` uses, four `app_tile_row` uses, and six
  `app_tilemap_base` uses, including `mulu.w app_tile_row(a6),d0`,
  `add.w app_tile_column(a6),d0`, and `clr.w app_tile_column(a6)`.
* Review: this is a source-quality improvement and exposed a real support-code
  defect. Remaining nearby offsets such as `$01C2`, `$01C4`, `$01D4`, and
  `$01D8` still need separate evidence; the selected-use
  `rsset.binding.report` path remains blocked by missing base evidence and no
  bind/refine command.

### 015-022: Name tilemap dimension app slots

* Candidate: D003 RSSET/app-base coverage for the adjacent raw `$01C2(a6)` and
  `$01C4(a6)` word fields.
* Evidence: initialization stores `#$5A` to `$01C2(a6)` and `#$81` to
  `$01C4(a6)` beside the `app_tilemap_base` initialization at
  `s0:00009EE0:instruction:7149`. The tilemap address calculation loads
  `$01C2(a6)`, multiplies it by `$01C4(a6)`, scales by four, and adds the
  result to `app_tilemap_base(a6)` around `s0:0000675E`. The same flow then
  uses `$01C2(a6)` as the row stride for `app_tile_row`/`app_tile_column`
  indexing. `$01C4(a6)` is also used as a vertical clamp bound after subtracting
  the visible 8-tile window and shifting to pixel units around `s0:0000818A`.
* Command: executed `target.rsset_region.add` twice through the target command
  catalog: `$01C2`, `size: 2`, `symbol: app_tilemap_width`; `$01C4`,
  `size: 2`, `symbol: app_tilemap_height`; both use `layout_name: app` and
  `base_symbol: __amiga_app_base__`.
* Verifier: Manual Action Log count is 20 with head hash
  `fb63e29b334ea4c8a4ec7b5d0a451d7c2a192df8afd3bbab4d8dfec97e50ab83`;
  semantic reload shows both RSSET regions with `size: 2`; exact reproduction
  reran and remained `status: exact`, `stale: false`, rebuilt SHA
  `70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
* Result: rendered source now defines `app_tilemap_width RS.W 1` and
  `app_tilemap_height RS.W 1`. Listing projection shows five rendered uses of
  each field, including `move.w #$5A,app_tilemap_width(a6)`,
  `move.w #$81,app_tilemap_height(a6)`,
  `mulu.w app_tilemap_height(a6),d3`, and
  `mulu.w app_tilemap_height(a6),d0`.
* Review: this continues the same D003 cluster through a supported target-level
  RSSET command and exact verifier. Remaining `$01D4/$01D8/$01DC` long fields
  look like display/copper buffer pointers, but their semantics are broader
  than tilemap indexing and need a separate evidence pass before naming.

### 015-023: Name display bitplane base app slot

* Candidate: D003 RSSET/app-base coverage for the raw `$01DC(a6)` long field.
* Evidence: `$01DC(a6)` is initialized to `#$78000` during startup beside the
  `$01D8(a6)` and `$01D4(a6)` buffer setup. During the frame-buffer swap at
  `s0:000005A8`, the value moved into `$01D4(a6)` is also stored into
  `$01DC(a6)`. The interrupt/display routine at `s0:0000094E` loads
  `$01DC(a6)` into `a0` and writes `a0`, `a0+$28`, `a0+$50`, and `a0+$78` to
  custom chip bitplane pointer registers `$00E0/$00E4/$00E8/$00EC`, making it
  the display bitplane base.
* Command: executed `target.rsset_region.add` through the target command
  catalog with `layout_name: app`, `base_symbol: __amiga_app_base__`,
  `offset: $01DC`, `size: 4`, `storage_kind: pointer`, and
  `symbol: app_display_bitplane_base`.
* Verifier: Manual Action Log count is 21 with head hash
  `9d6c2c565c7b82ba502e4832c9f263faafc30f169d75472ed4b8bd995578c525`;
  semantic reload shows `$01DC` as a 4-byte pointer RSSET region; exact
  reproduction reran and remained `status: exact`, `stale: false`, rebuilt SHA
  `70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
* Result: rendered source now defines `app_display_bitplane_base RS.L 1` and
  renders the three concrete uses:
  `move.l #$78000,app_display_bitplane_base(a6)`,
  `move.l d0,app_display_bitplane_base(a6)`, and
  `movea.l app_display_bitplane_base(a6),a0`.
* Review: this is a narrow source-quality improvement with direct hardware
  evidence. `$01D4(a6)` and `$01D8(a6)` are still not named: they are swapped
  around the frame loop and also feed drawing/blitter routines, so front/back or
  draw/display names require stronger lifetime evidence than the current pass
  has.

### 015-024: Name text cursor pointer app slot

* Candidate: D003 RSSET/app-base coverage for the raw `$01E4(a6)` long field,
  which had the highest remaining raw A6 use count in the current listing scan.
* Evidence: text rendering at `s0:00006056` saves `$01E4(a6)`, reloads it into
  `a1`, writes glyph bytes through `a1`, advances `a1`, and stores the updated
  pointer back to `$01E4(a6)`. Newline handling restores the saved pointer and
  advances it by `$0500`. Coordinate setup routines at `s0:00006108` and
  `s0:00006126` compute a screen address from x/y inputs and store it to
  `$01E4(a6)`. Additional text/glyph routines increment the same field by one,
  four, or `1280` bytes as they advance their destination cursor.
* Command: executed `target.rsset_region.add` through the target command
  catalog with `layout_name: app`, `base_symbol: __amiga_app_base__`,
  `offset: $01E4`, `size: 4`, `storage_kind: pointer`, and
  `symbol: app_text_cursor_ptr`.
* Verifier: Manual Action Log count is 22 with head hash
  `bbb4bb56bd9dcdf0ccff5c2e257fa0c0fb3613dcbdca420595de7f96db0c350d`;
  semantic reload shows `$01E4` as a 4-byte pointer RSSET region; exact
  reproduction reran and remained `status: exact`, `stale: false`, rebuilt SHA
  `70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
* Result: rendered source now defines `app_text_cursor_ptr RS.L 1` and the
  listing projection shows 19 rows containing `app_text_cursor_ptr`, including
  `movea.l app_text_cursor_ptr(a6),a1`,
  `move.l a1,app_text_cursor_ptr(a6)`,
  `addi.l #1280,app_text_cursor_ptr(a6)`, and
  `movea.l app_text_cursor_ptr(a6),a2`.
* Review: this is a supported, high-impact RSSET naming action. The name is
  intentionally about the mutable text/glyph destination pointer, not a broader
  framebuffer role, because some setup paths derive it from `$01D4(a6)` while
  others derive it from the fixed `$70000` screen base.

### 015-025: Name tilemap scroll origin app slots

* Candidate: D003 RSSET/app-base coverage for raw `$01B6(a6)` and `$01B8(a6)`,
  the pixel scroll origins feeding the already named tile row/column fields.
* Evidence: the update path at `s0:0000818A` clamps `$01B8(a6)` against
  `(app_tilemap_height - 8) << 4`, stores it back, shifts it right by four, and
  stores the tile result to `app_tile_row(a6)`. The same path adds
  `app_0296(a6)` to `$01B6(a6)`, stores it back, shifts it right by four, and
  stores the tile result to `app_tile_column(a6)`. Initialization at
  `s0:00009EE0` sets `app_tile_row` to 51, stores `51 << 4` into `$01B8(a6)`,
  and clears `$01B6(a6)`. The screen-bound helper at `s0:0000680A` uses
  `$01B6(a6)+320` and `$01B8(a6)+128`, matching pixel-space viewport extents.
* Command: executed `target.rsset_region.add` twice through the target command
  catalog: `$01B6`, `size: 2`, `symbol: app_tilemap_scroll_x`; `$01B8`,
  `size: 2`, `symbol: app_tilemap_scroll_y`; both use `layout_name: app` and
  `base_symbol: __amiga_app_base__`.
* Verifier: Manual Action Log count is 24 with head hash
  `52484268beb9eb71d4b9e1b99aaea643aac8c90984f7ae32860c5ad518b2515c`;
  semantic reload shows both RSSET regions with `size: 2`; exact reproduction
  reran and remained `status: exact`, `stale: false`, rebuilt SHA
  `70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
* Result: rendered source now defines `app_tilemap_scroll_x RS.W 1` and
  `app_tilemap_scroll_y RS.W 1`. Listing projection shows seven rows for each
  name, including `move.w app_tilemap_scroll_x(a6),d0`,
  `move.w d0,app_tilemap_scroll_x(a6)`,
  `move.w app_tilemap_scroll_y(a6),d0`, and
  `move.w d0,app_tilemap_scroll_y(a6)`.
* Review: this completes the high-confidence tilemap scroll/size/base cluster
  currently backed by direct same-flow evidence. Remaining raw slots should be
  treated as separate candidate families rather than folded into D003 by
  adjacency alone.

### 015-026: Name frame counter app slot

* Candidate: raw app-state coverage for `$01AA(a6)`, a repeatedly used long
  counter outside the tilemap RSSET cluster.
* Evidence: the display interrupt path at `s0:0000094E` increments
  `$01AA(a6)` before updating bitplane pointers. The callback at
  `s0:00000F54` also increments the same field. The wait helper at
  `s0:0000078E` snapshots `$01AA(a6)` and spins until it changes, and the
  timed loop at `s0:00000F88` compares `$01AA(a6)` against a saved value plus
  150 frames.
* Command: executed `target.rsset_region.add` through the target command
  catalog with `layout_name: app`, `base_symbol: __amiga_app_base__`,
  `offset: $01AA`, `size: 4`, and `symbol: app_frame_counter`.
* Verifier: Manual Action Log count is 25 with head hash
  `b413594f5355a6be58f889a12d674a0bcfe00e400297be4c2e4fac5e958eab2f`;
  semantic reload shows `$01AA` as a 4-byte RSSET region; exact reproduction
  reran and remained `status: exact`, `stale: false`, rebuilt SHA
  `70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
* Result: rendered source now defines `app_frame_counter RS.L 1` and the
  listing projection shows seven rows containing `app_frame_counter`, including
  `addq.l #1,app_frame_counter(a6)`,
  `move.l app_frame_counter(a6),d5`, and
  `cmp.l app_frame_counter(a6),d5`.
* Review: this is a supported, source-quality app-state name with direct timing
  evidence. It does not resolve the remaining higher-count pointer fields such
  as `$019E(a6)`, `$01D4(a6)`, or `$01D8(a6)`, whose object/buffer lifetimes are
  still ambiguous enough to require a separate evidence pass.

### 015-027: Name palette effect countdown app slot

* Candidate: raw app-state coverage for `$0195(a6)`, a byte countdown used by
  the palette/callback effect code.
* Evidence: the callback installed at `app_0360(a6)` steps through palette
  routines around `s0:00000DE0`, `s0:00000E14`, and `s0:00000E4E`. These
  routines wait for the raster position byte to change, copy palette words into
  custom chip color registers, then decrement `$0195(a6)` until zero before
  advancing the callback. Initializers set `$0195(a6)` to `$20`, `$18`, or `$08`
  for the active palette effect phase.
* Command: executed `target.rsset_region.add` through the target command
  catalog with `layout_name: app`, `base_symbol: __amiga_app_base__`,
  `offset: $0195`, `size: 1`, and `symbol: app_palette_effect_countdown`.
* Verifier: Manual Action Log count is 26 with head hash
  `076dea0c5d4541e010948c2b583b15fa7c0a696816497a55feabd22037c8e6fc`;
  semantic reload shows `$0195` as a 1-byte RSSET region; exact reproduction
  reran and remained `status: exact`, `stale: false`, rebuilt SHA
  `70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
* Timing: command execution appended the manual action in about 0.002s; listing
  projection regeneration/readback was about 9s; exact reproduction completed in
  about 1.2s.
* Result: rendered source now defines `app_palette_effect_countdown RS.B 1` and
  listing projection shows eight rows containing the name, including
  `subq.b #1,app_palette_effect_countdown(a6)`,
  `move.b #$18,app_palette_effect_countdown(a6)`, and
  `move.b #$20,app_palette_effect_countdown(a6)`.
* Review: the name is intentionally limited to the observed palette-effect
  countdown behavior. It does not classify the surrounding palette tables,
  callback slot type, or raw custom-register-looking A5 offsets, which need
  separate supported actions and verifier coverage.

### 015-028: Name input direction app slots

* Candidate: related raw app-state coverage for `$01C6(a6)`, `$01C8(a6)`, and
  `$01B2(a6)` in the joystick/input path.
* Evidence: `s0:000007F0` reads `joy1dat(a5)`, inverts it, derives a
  direction bitmask in `d0`, and derives signed step values in `d2`. It stores
  the horizontal step to `$01C6(a6)`, the vertical step to `$01C8(a6)`, and the
  direction mask to `$01B2(a6)`. The movement path at `s0:0000291A` gates on
  `$01B2(a6)`, applies `$01C6(a6)` to `app_0214(a6)`, multiplies non-zero
  horizontal input into `app_0226(a6)`, and applies `$01C8(a6)` to
  `app_0216(a6)` before storing vertical movement in `app_0228(a6)`.
* Command: executed three `target.rsset_region.add` commands through the target
  command catalog with app layout and `__amiga_app_base__` base symbol. The
  grouped fields were `$01C6` size 2 as `app_input_x_step`, `$01C8` size 2 as
  `app_input_y_step`, and `$01B2` size 2 as `app_input_direction_mask`.
* Verifier: Manual Action Log count is 29 with head hash
  `62b9e2037c95141a2d56321949c9c950350304ca715280070198911de9407256`;
  semantic reload shows all three 2-byte RSSET regions; exact reproduction
  reran and remained `status: exact`, `stale: false`, rebuilt SHA
  `70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
* Timing: the grouped command execution completed under 1s; listing projection
  regeneration/readback was about 10s; reproduction status after rerun reported
  ready/exact.
* Result: rendered source now defines `app_input_x_step RS.W 1`,
  `app_input_y_step RS.W 1`, and `app_input_direction_mask RS.W 1`. Listing
  projection shows four rows containing `app_input_x_step`, three containing
  `app_input_y_step`, and three containing `app_input_direction_mask`.
* Review: this batch is a coherent same-surface app-state naming improvement,
  so grouping avoided one report/commit per mechanically similar field while
  keeping the evidence and verifier scope tight. It does not name adjacent
  pointer/buffer slots such as `$01D4(a6)`, `$01D8(a6)`, or `$01E0(a6)`, whose
  lifetimes remain ambiguous.

### 015-029: Name front/back bitplane buffer app slots

* Candidate: related raw app-state coverage for `$01D4(a6)` and `$01D8(a6)`,
  the long bitplane buffer pointers paired with the already named
  `app_display_bitplane_base`.
* Evidence: startup initializes and clears both buffers: `$01D8(a6)` is set to
  `$78000`, cleared, then set to `$70000` and cleared, while `$01D4(a6)` is
  initialized to `$78000`. The frame loop at `s0:000005A8` swaps `$01D4(a6)`
  and `$01D8(a6)`, then copies the new front value into
  `app_display_bitplane_base(a6)` for the interrupt display pointer update.
  The tile and object drawing paths use `$01D8(a6)` as the destination base:
  `s0:00006770` draws the tilemap into it, and the clipped blit paths around
  `s0:0000704A`, `s0:00007082`, `s0:000070F0`, and `s0:00007152` derive A2
  destinations from it. `$01D4(a6)` is also used by screen/text coordinate
  setup and reset by the screen-clear path at `s0:000066D6`.
* Command: executed two `target.rsset_region.add` commands through the target
  command catalog with app layout, `__amiga_app_base__` base symbol, size 4,
  and pointer storage kind: `$01D4` as `app_front_bitplane_base` and `$01D8` as
  `app_back_bitplane_base`.
* Verifier: Manual Action Log count is 31 with head hash
  `eebc1c617d44a1013e7331edfff796eb262c698a797fcea0ec9be315e9d44044`;
  semantic reload shows both 4-byte pointer RSSET regions; exact reproduction
  reran and remained `status: exact`, `stale: false`, rebuilt SHA
  `70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
* Timing: grouped command execution completed in about 1s; listing projection
  regeneration/readback was about 10s; exact reproduction remained ready/exact.
* Result: rendered source now defines `app_front_bitplane_base RS.L 1` and
  `app_back_bitplane_base RS.L 1`. Listing projection shows eight rows
  containing `app_front_bitplane_base` and ten rows containing
  `app_back_bitplane_base`.
* Review: this batch resolves the high-confidence front/back buffer pair while
  preserving `app_display_bitplane_base` as the value consumed by the interrupt
  display pointer update. `$01E0(a6)` is not included because current evidence
  only shows repeated stores of `$70000` before rendering calls, not a clear
  durable load/use role.

### 015-030: Name object focus and interaction app slots

* Candidate: related raw app-state coverage for `$019E(a6)` and `$01A2(a6)`,
  the object pointers shared by the nearby-object scan and interaction/effect
  paths.
* Evidence: the object scan around `s0:000082F0` iterates the object list,
  compares object position fields against the current/player object, updates
  the best distance, and writes the selected candidate pointer to `$019E(a6)`.
  Later paths test and load `$019E(a6)` before copying it into `$01A2(a6)` at
  `s0:00002F02`; the interaction/effect routines then repeatedly load
  `$01A2(a6)` into `a5` before checking object flags, object type, held item
  state, and applying interaction effects.
* Command: executed two `target.rsset_region.add` commands through the target
  command catalog with app layout, `__amiga_app_base__` base symbol, size 4,
  and pointer storage kind: `$019E` as `app_nearest_object_ptr` and `$01A2` as
  `app_interaction_object_ptr`.
* Verifier: Manual Action Log count is 33 with head hash
  `90d5c094ebf1bfe3001d8e3952899a4fbc12f45bf8c6289d7e6de0a797b93a1c`;
  semantic reload shows both 4-byte pointer RSSET regions; exact reproduction
  reran and remained `status: exact`, `stale: false`, rebuilt SHA
  `70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
* Timing: grouped command execution completed in about 1s; listing projection
  regeneration/readback was about 10s; exact reproduction remained ready/exact.
* Result: rendered source now defines `app_nearest_object_ptr RS.L 1` and
  `app_interaction_object_ptr RS.L 1`. Listing projection shows eleven rows
  containing `app_nearest_object_ptr` and nine rows containing
  `app_interaction_object_ptr`.
* Review: this batch keeps the names at pointer-role level because the concrete
  object struct fields are still unnamed. It does not classify the object-list
  base, inventory/pocket byte arrays at `$0196(a6)`/`$019A(a6)`, or item/object
  type values; those need their own supported evidence pass.

### 015-033: Support and name byte-array item app slots

* Candidate: blocked D012 app-state arrays at `$0196(a6)` and `$019A(a6)`,
  where four byte-sized item ids are cleared as longwords but later indexed as
  bytes.
* Evidence: `s0:000029EA` iterates four byte entries from both arrays and
  expands them through item-offset tables into pointer tables at
  `abs_0_00013416` and `abs_0_00013442`; interaction code swaps object item id
  byte `$0046(a4)` with indexed bytes from both arrays; `s0:00002778` checks
  item `$6C` across both arrays; the nearby failure string is
  `" IS TOO LARGE FOR YOUR POCKETS"` for the `$019A(a6)` path.
* Support-code fix: added a `byte_array` RSSET layout storage kind to target
  metadata, manual command schema validation, C policy loading/export, and
  rendering. Explicit byte-array regions now render as `RS.B <size>`, so a
  four-byte slot is not misdeclared as `RS.L 1`.
* Command: executed two `target.rsset_region.add` commands through the target
  command catalog with app layout, `__amiga_app_base__` base symbol, size 4,
  and byte-array storage kind: `$0196` as `app_carried_item_ids` and `$019A`
  as `app_pocket_item_ids`.
* Verifier: focused support tests passed
  (`tests\test_manual_action_catalog.py::test_target_rsset_layout_region_command_payload_accepts_byte_array_storage`,
  `tests\test_disasm_projects.py::test_load_target_metadata_preserves_extended_rsset_layout_metadata`,
  `tests\test_c_backend.py::test_real_dll_metadata_named_rsset_layout_renders_byte_array_kind`,
  `src\tests\test_ir_policy_dll.py::IrPolicyDllTests::test_effective_policy_exports_rsset_storage_kind_id`);
  ruff passed for touched Python files and import/error checks for the C DLL
  unittest; Manual Action Log count is 35 with head hash
  `89d206316f4711358fa29702dc246b66c408f9c54a9b98f5f5c02cbacc93e2bb`;
  semantic reload shows both byte-array RSSET regions; exact reproduction
  reran and remained `status: exact`, `stale: false`, rebuilt SHA
  `70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
* Timing: C DLL rebuild took about 17s; focused pytest took about 1s; grouped
  target command execution completed in under 1s; listing projection readback
  was about 10s; exact reproduction completed in about 21s.
* Result: rendered source now defines `app_carried_item_ids RS.B 4` and
  `app_pocket_item_ids RS.B 4`. Listing projection shows six rows containing
  `app_carried_item_ids` and five rows containing `app_pocket_item_ids`.
* Review: `$019A(a6)` has pocket-specific evidence from the failure path.
  `$0196(a6)` is deliberately named at the broader carried-item level because
  current evidence proves item-slot display/swap behavior but not a narrower
  left/right hand role. The new storage kind is intentionally explicit policy:
  plain size-4 app regions continue to render as long storage unless the
  command records byte-array semantics.

### 015-034: Render Pandora frame-counter byte suboffset uses

* Candidate: blocked D013 byte uses at `$01AD(a6)`, which are inside the
  existing four-byte `$01AA(a6)` `app_frame_counter` RSSET region.
* Evidence: 015-026 named `$01AA(a6)` as `app_frame_counter`; at
  `s0:00000F6A`, `btst.b #0,$01AD(a6)` gates the palette rotation path; at
  `s0:00002DA8`, `move.b $01AD(a6),app_022D(a6)` copies the low frame-counter
  byte to display/palette state.
* Support-code fix: selected RSSET use-site bindings now resolve offsets inside
  a named RSSET region as `<region_symbol>+<delta>` instead of requiring an
  exact region start match or creating an overlapping slot. The C metadata
  parser and policy ABI now also accept long generated RSSET binding ids.
* Command: executed two `rsset.binding.bind` commands through the
  listing/command API with explicit A6 app-base evidence
  `selected-base:A6:__amiga_app_base__`: action
  `manual-5d8f01b9c5924605b924eb3296d883e6` for `s0:00000F6A` and action
  `manual-de8d9e46aba54273b712ee0218d7946e` for `s0:00002DA8`.
* Verifier: C backend rebuild passed; focused pytest passed for the existing
  selected-use binding tests plus the new suboffset regression; ruff import/error
  check passed for `tests\test_c_backend.py`; inspect reports Manual Action Log
  count 37, head hash
  `eefed19c83e02b0145c2b82c1ed0144e314339d2e069dd996557b5455c3846a0`,
  review state clear, and exact round-trip. Listing projection shows exactly
  `btst.b #0,app_frame_counter+3(a6)` at `s0:00000F6A` and
  `move.b app_frame_counter+3(a6),app_022D(a6)` at `s0:00002DA8`, with no
  remaining raw `$01AD(a6)` hits. Exact reproduction reran with `status: exact`,
  `stale: false`, and rebuilt SHA
  `70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
* Timing: C DLL rebuild took about 18s; focused pytest took about 1s; listing
  open/query was about 5s; exact reproduction source rendering was about 1s.
* Result: rendered source uses `app_frame_counter+3(a6)` for the two proven
  byte reads without introducing an overlapping `$01AD` app slot.
* Review: the bindings remain selected-use and path-specific. This does not name
  `app_022D` or infer a narrower frame-byte semantic. The binding-id parser gap
  was found after the first real Manual Action Log action and fixed before the
  second action.

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
  * fixed by 015-018: query/report for "stored pointer later consumed by
    indirect jump/call",
  * resolved for the concrete Pandora candidate by 015-019 through the supported
    `row.seed.code` path when Review item identity was data-range only.
* Pull-in condition: work on RSSET/app-slot provenance reaches function-pointer
  typed slots, or code/data classification stalls on stored callback targets.
* Status: fixed for the concrete `app_0360` missed target by 015-018 and
  015-019. Broader function-pointer slot typing remains future app-slot work.

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
* Update: 015-019 resolved the concrete `abs_0_00010E14` case through
  callback-slot evidence plus row classification. Broad terminal-decode
  heuristics remain out of scope for Pandora.

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
  * 015-020 resolved `$01BE(a6)` as `app_tilemap_base`, a long pointer
    initialized to `#$4000` and used as the base in tile/address calculations.
  * 015-021 resolved `$01BA(a6)` as `app_tile_column` and `$01BC(a6)` as
    `app_tile_row`, both 2-byte RSSET app fields used in tilemap indexing.
  * 015-022 resolved `$01C2(a6)` as `app_tilemap_width` and `$01C4(a6)` as
    `app_tilemap_height`, both 2-byte RSSET app fields used in tilemap sizing
    and indexing.
  * 015-023 resolved `$01DC(a6)` as `app_display_bitplane_base`, a 4-byte
    pointer RSSET app field copied into the custom chip bitplane pointer
    registers.
  * 015-024 resolved `$01E4(a6)` as `app_text_cursor_ptr`, a 4-byte pointer
    RSSET app field used as the mutable destination cursor for text/glyph
    rendering.
  * 015-025 resolved `$01B6(a6)` as `app_tilemap_scroll_x` and `$01B8(a6)` as
    `app_tilemap_scroll_y`, both 2-byte RSSET app fields used as pixel-space
    scroll origins for tilemap row/column derivation.
  * 015-028 resolved `$01C6(a6)` as `app_input_x_step`, `$01C8(a6)` as
    `app_input_y_step`, and `$01B2(a6)` as `app_input_direction_mask`, all
    2-byte input-state fields produced from `joy1dat(a5)` and consumed by the
    movement path.
  * 015-029 resolved `$01D4(a6)` as `app_front_bitplane_base` and `$01D8(a6)`
    as `app_back_bitplane_base`, the front/back bitplane pointers swapped each
    frame while `app_display_bitplane_base` feeds the interrupt display update.
* Expected source improvement:
  * report a coherent app/RSSET range candidate for the cluster,
  * bind/refine field names and widths from same-flow/same-displacement
    evidence once proposal 014 support allows it.
* Missing tool/report/action:
  * RSSET report that explains why adjacent offsets were named while these
    remained raw,
  * candidate grouping for repeated raw A6 offsets in a proven app-base
    lifetime.
* 015-002/015-003 follow-up: the element command surface now exposes
  `rsset.binding.report` for `$01D8(a6)`, but the report remains read-only for
  Pandora because `base_evidence_id` is null, source family is unresolved, and
  the blocker is `missing_base_evidence`. Same-displacement counts are useful
  (`$01D8(a6)` appears 9 times; `$01D4(a6)` appears 7 times), but not yet safe
  to bind.
* Pull-in condition: first Pandora RSSET/app-base pass begins.
* Status: partly fixed by 015-020 through 015-034. The trial named the
  high-confidence app-state fields for tilemap state, display/text pointers,
  frame state, input, bitplane buffers, object pointers, item arrays, and
  selected frame-counter byte uses. Adjacent raw fields remain open pending
  stronger names, accepted base/gap evidence, or a narrower semantic pass.
  `$01B2`, `$01C6`, and `$01C8` were later fixed by 015-028 as an input-state
  subgroup. `$01D4` and `$01D8` were later fixed by 015-029 as the front/back
  bitplane buffer pair.

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

#### D008: Dry-run and execute candidate drift

* Date/source: 015-009 Pandora row-backed string iteration.
* Location: `reversing_loop run-one --dry-run` followed by `run-one` for
  `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.
* Evidence:
  * dry run reported `data_symbol.rename_existing` for row
    `s0:000009EA:data:656` as `copper_list_000209EA`,
  * execute pass recomputed and applied `data_symbol.rename` for row
    `s0:0000109E:data:1018` as `string_0002109E`,
  * the executed action was valid, row-backed, and exact-round-trip verified.
* Expected source improvement:
  * make dry-run and execute action selection stable for the same project
    state, or report clearly when a selected action is skipped and why.
* Missing tool/report/action:
  * concise selected-action trace with skip reasons after command availability
    checks.
* Pull-in condition: drift repeats, hides an invalid action, or blocks typed
  data-backed iteration batching.
* Status: open.

#### D009: Generic data-class label styling belongs in framework policy

* Date/source: review of 015-009 row-backed string rename.
* Location: `data_symbol.rename` candidates whose proposed names are only
  `<data_class>_<address>`, such as `string_0002109E`.
* Evidence:
  * the row type and exact verifier made the action safe,
  * the resulting name did not add target semantics beyond class and address,
  * the visible string contents and call context could support a semantic
    target name, while generic `string_` styling should not need manual LLM
    iteration.
* Expected source improvement:
  * auto-analysis/rendering should apply generic class-based styling
    consistently when that policy is desired,
  * target-level LLM renames should use program meaning from content, xrefs,
    and call context.
* Missing tool/report/action:
  * analyzer/framework naming policy for anonymous typed data rows, or a
    planner filter that reports class/address-only renames as framework work
    instead of target progress.
* Pull-in condition: generic typed-row renames dominate the planner, or a
  target action needs to replace a generic name with a semantic one.
* Status: fixed for autonomous planner selection by 015-011. Framework-level
  automatic styling remains separate future policy work.

#### D010: Printable immediate character representation is too syntax-led

* Date/source: 015-011 Pandora dry-run after generic data-symbol names were
  skipped.
* Location: selected candidate
  `representation:s0:00000C28:instruction:760:0:63:character`.
* Evidence:
  * candidate evidence is only `byte_printable_immediate`,
  * source text is `andi.b #63,d1`,
  * rendering `63` as `#'?'` would likely obscure mask semantics.
* Expected source improvement:
  * character representation candidates should require semantic character
    context, such as compare/transform code around ASCII input or output, not
    mere printable byte values.
* Missing tool/report/action:
  * opcode/context-aware representation planning or a planner skip reason for
    printable-but-not-character-context immediates.
* Pull-in condition: immediate representation is the next selected Pandora
  action.
* Status: fixed for bitwise-immediate mask opcodes by 015-012. Broader
  opcode/context-aware representation policy remains open if arithmetic
  candidates prove weak.

#### D011: Manual seed verifier reports duplicate expected seeds

* Date/source: 015-015 review-item `review.seed.code` executions.
* Location: `_verify_manual_seed_mutation` verifier output for
  `orphan_code_candidate:h0:$00000aa2-$00000ab8` and
  `orphan_code_candidate:h0:$00000d9c-$00000dae`.
* Evidence:
  * command execution returns both `action` and `actions`,
  * `_manual_seeds_from_durable_result` reads the same seed from both fields,
  * verifier output lists duplicate `expected_manual_seeds` and
    `matching_manual_seeds` while still passing correctly.
* Expected source improvement:
  * cleaner verifier reports for manual-seed actions, reducing review noise
    without changing target semantics.
* Missing tool/report/action:
  * de-duplicate verifier seed identities when `action` is also the first
    element of `actions`.
* Pull-in condition: fix when touching manual-seed verifier reporting or if the
  duplicate output starts obscuring real seed mismatches.
* Status: open.

#### D012: RSSET app-slot arrays need byte-array rendering support

* Date/source: 015-031 manual review of remaining raw Pandora A6 fields after
  `app_nearest_object_ptr` and `app_interaction_object_ptr`.
* Location: `$0196(a6)` and `$019A(a6)`.
* Evidence:
  * both slots are initialized with `move.l d0,$0196(a6)` and
    `move.l d0,$019A(a6)`, clearing four bytes each,
  * `s0:000029EA` iterates four byte entries from each slot and expands them
    through item-offset tables into pointer tables at `abs_0_00013416` and
    `abs_0_00013442`,
  * interaction code swaps object/item id byte `$0046(a4)` with indexed bytes
    from `$0196(a6)` and `$019A(a6)`,
  * the nearby failure string is `" IS TOO LARGE FOR YOUR POCKETS"`, and
    `s0:00002778` checks item `$6C` across both arrays.
* Expected source improvement:
  * name the two four-byte item-id slot arrays without pretending they are
    scalar longs,
  * preserve indexed byte access and four-byte zeroing evidence in the rendered
    RSSET layout.
* Missing tool/report/action:
  * fixed by 015-033: `target.rsset_region.add` now accepts a `byte_array`
    storage kind, and explicit byte-array slots render as `RS.B <size>`.
* Pull-in condition: app-slot byte arrays become the next best Pandora
  source-converging action, or typed app-slot array rendering is being changed.
* Status: fixed by 015-033. Pandora `$0196(a6)` and `$019A(a6)` were named
  through supported commands and exact round-trip verified.

#### D013: RSSET subfield accesses need alias/offset rendering

* Date/source: 015-032 manual review of remaining raw Pandora A6 fields.
* Location: `$01AD(a6)`, inside the existing 4-byte `app_frame_counter` region
  at `$01AA(a6)`.
* Evidence:
  * 015-026 named `$01AA(a6)` as `app_frame_counter` from frame increment and
    wait-loop evidence,
  * the remaining `$01AD(a6)` uses are byte accesses to the low byte of that
    long field: `btst.b #0,$01AD(a6)` controls the palette rotation path and
    `move.b $01AD(a6),app_022D(a6)` copies the current frame low byte when
    the surrounding display state allows it.
* Expected source improvement:
  * render byte-offset uses as an expression or alias of `app_frame_counter`
    rather than as a new independent raw app slot.
* Missing tool/report/action:
  * fixed by 015-034: selected `rsset.binding.bind` use-site bindings can now
    render displacements inside an accepted RSSET region as
    `<region_symbol>+<delta>` without adding an overlapping region.
* Pull-in condition: overlapping RSSET byte/word accesses become the next best
  source-converging action, or app-slot alias rendering is being changed.
* Status: fixed by 015-034. The two proved Pandora `$01AD(a6)` byte uses now
  render as `app_frame_counter+3(a6)` through supported commands, and exact
  round-trip was verified.

## Stop Conditions

Stop and report rather than continuing when:

* hygiene finds unknown target-local files,
* the next best source-converging action lacks supported command/verifier
  coverage,
* evidence is conflicting and cannot be classified or overridden safely,
* the path/lifetime scope is not provable,
* verification fails without a clear fix,
* the next action is only generic class/address label styling that belongs in
  analyzer/framework policy,
* only proof, fallback, placeholder, or makework actions remain.

If exact round-trip fails after a target action, diagnose and fix only if the
failure is clearly caused by the just-applied action or support code. Otherwise
stop with the failing action, verifier output, and rollback/cleanup
recommendation. Do not stack further target edits on a failed round-trip.

Prefer corrective MAL actions or supported cleanup commands for rollback. Use
`clean-run` only for initial baseline setup or abandoning resettable trial state,
not as normal rollback.

## Final Retrospective

Proposal 015 achieved its intended trial scope. The Pandora run exercised the
proposal 014 manual action surface on a real target, improved the rendered
source, exposed real support-code gaps, fixed the gaps that blocked worthwhile
target progress, and stopped with explicit remaining blockers instead of
continuing through weak evidence.

Source-quality improvements made:

* Restored the tracked Pandora `.s` render so source-control diffs show the
  visible outcome of the target trial.
* Added verified code classification for callback/handler ranges that were
  previously rendered as data.
* Replaced many raw A6 app-state operands with named RSSET fields, including
  tilemap state, display/text pointers, frame state, input fields, bitplane
  buffers, object pointers, and carried/pocket item arrays.
* Added selected-use RSSET binding for proven subfield accesses, rendering
  frame-counter byte reads as `app_frame_counter+3(a6)` without creating an
  overlapping app slot.
* Applied immediate representation only where surrounding code supported
  character semantics, and blocked syntax-only printable-immediate churn.

Support-code fixes made:

* Hardened planner selection against low-value generic data/class names and
  stale locator failures.
* Added a callback-slot report for stored code pointers consumed by indirect
  calls/jumps.
* Fixed app RSSET rendering for explicit 2-byte regions and added byte-array
  storage support.
* Extended selected RSSET use-site binding rendering to allow offsets inside an
  accepted region.
* Increased the C metadata binding-id capacity after real generated binding ids
  exceeded the old limit.

Review findings:

* No blocking correctness issue was found in the final 015 commits during
  closeout review.
* Output-affecting target changes consistently report exact round-trip
  verification, and final rendered-source evidence is now tracked.
* Closeout validation rebuilt the C artifacts and passed style/dead-code stages,
  but `src\build\m68k_c_unit_tests.exe` exited 1 without diagnostic output, so
  the full `src\precommit.bat` did not complete. This should be investigated as
  a validation/tooling issue before treating the whole tree as green.
* The main architectural weakness remains that many successful app-slot edits
  used target-level RSSET region commands. The selected `rsset.binding.report`
  path is still too often report-only because accepted base evidence and
  bind/refine ownership are incomplete.
* The app-slot naming pass should not continue indefinitely. Remaining raw A6
  fields need a new focused evidence family, not adjacency-driven naming.

Performance observations:

* Manual command execution was usually fast, often under one second for grouped
  app-slot actions.
* Listing projection/readback commonly took about 9-10 seconds.
* C DLL rebuild and final exact reproduction could dominate individual support
  fixes; 015-033 recorded about 17 seconds for rebuild and about 21 seconds for
  exact reproduction.

Deferred work remaining:

* D002: broad orphan-code heuristics remain open and should stay evidence-led.
* D006: immediate runtime-reference detection remains open.
* D007: A5 hardware-base lifetime proof remains open.
* D008: dry-run/execute candidate drift remains open.
* D011: duplicate expected manual seeds in verifier output remains open.
* Broader framework work remains for provenance-backed RSSET bind/refine
  actions and generated-descendant cleanup ownership.

Proposal 014 surfaces that worked well:

* Durable command ids and exact round-trip verification were sufficient for
  repeated target mutations.
* Review items were useful as a work queue when paired with durable ids and
  evidence fingerprints.
* Row-level code seeding and selected RSSET use-site bindings were useful
  escape hatches when the review item family was not specific enough.
* Recording deferred findings in the proposal prevented blockers from being
  lost between candidate families.

Proposal 014 surfaces that need redesign or follow-up:

* RSSET report/bind/refine needs accepted base evidence, durable ownership, and
  cleanup semantics strong enough to replace ad hoc target-level region adds.
* The planner needs better selected-action traceability when dry-run and
  execution diverge after availability checks.
* Manual seed verifier reporting should de-duplicate command payloads that
  expose the same action through both `action` and `actions`.
* Hardware-base provenance needs first-class lifetime/conflict reporting before
  A5-relative operands can safely render as custom register names.

Pandora should continue only as a focused follow-up target. The next Pandora
work should start from one of the remaining evidence families above rather than
another broad reversing-loop pass.

## References

* Reversing loop: `docs\agents\reversing-loop.md`
* Capability map:
  `docs\proposals\014-source-converging-manual-action-surface.md`
