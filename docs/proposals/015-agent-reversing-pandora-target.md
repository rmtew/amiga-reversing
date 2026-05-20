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
* 015-002/015-003 follow-up: the element command surface now exposes
  `rsset.binding.report` for `$01D8(a6)`, but the report remains read-only for
  Pandora because `base_evidence_id` is null, source family is unresolved, and
  the blocker is `missing_base_evidence`. Same-displacement counts are useful
  (`$01D8(a6)` appears 9 times; `$01D4(a6)` appears 7 times), but not yet safe
  to bind.
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
