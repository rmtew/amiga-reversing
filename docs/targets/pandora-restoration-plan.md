# Pandora full source restoration

> Canonical memory-region/layout export is designed in
> [Proposal 046](../proposals/046-canonical-memory-layouts.md).
> Its first delivery includes canonical image/code, workspace and display
> base-plus-offset modelling, normal-export original and known `$80000` layouts,
> and at least one independently moved workspace or display block. Image-only
> qualification is an internal step, not completed delivery. Runtime allocation
> and OS-hosted output remain separate later gates. Current normal exports and
> the independent cursor move are implemented and runtime-qualified within the
> [milestone ledger](../../runtime/observations/pandora-layout-delivery-acceptance.json).
> Strict original-to-image HAND-cycle equality still refuses; no unconditional
> first-delivery or universal portability claim is made.

> Behavioural validation is tracked in [Proposal 045](../proposals/045-behavioural-validation.md).
> Its B01–B10 commitments distinguish framework capability from target coverage;
> its CPU and DMA results have bounded scopes. B07 and generic capability work
> remain paused. The original-layout review below is closed with explicit
> unknowns; no automatic capability continuation is selected. No B commitment
> closes on documentation alone.

Current alternate-layout management: the
[bounded HAND diagnosis](../../runtime/observations/pandora-HAND-causal-boundary.json)
keeps strict cycle equality unfulfilled. The
[independent display move](../../runtime/observations/pandora-canonical-display-qualification.json)
now qualifies E0000..ED000 with cursor still65370 and image80000, including cold
completion and scoped graphics/PCM equality. The
[bounded M5 implementation](../../runtime/observations/pandora-runtime-allocation-implementation.json)
now has [two allocator-selected completions and scoped output qualification](../../runtime/observations/pandora-runtime-allocation-qualification.json)
for the body snapshot at `$F568`/`$F5A8`, plus a corrected-loader unheld cold
completion. Native actual-base validation and tested failure unwind are implemented.
The [combined CPU-workspace/display layout](../../runtime/observations/pandora-canonical-cpu-workspace-qualification.json)
now qualifies independent keyboard `$6000`, app/raster `$6080` and grid `$6684`
through controlled and unheld completion plus exact scoped graphics/PCM. Its
conditional grid-end byte is backing only, not new semantic data. That footprint
supersedes independent placement assumptions for the two historical body bases;
their observed outputs remain recorded. Next: allocator-selected CPU bases and
native generated operand fixups, then successful DMA-safe cleanup and OS return.
Other low scratch and hardware/vector ownership remain open.
The [CPU fixup projection](../../runtime/observations/pandora-CPU-fixup-projection.json)
now has 20 passing focused tests but refuses the real target at `$78C4`. Four
fixed priest-passage cell writes exposed a known alternate-layout gap; the
existing route/output pass does not close it. Their canonical runtime domains
are now corrected and an unrepresentable absolute-W placement refuses; see the
[encoding boundary](../../runtime/observations/pandora-passage-relocation-boundary.json).
At app `$6080`, the actual cell `$8B44` also exceeds positive absolute-W reach.
The [explicit address-frame adoption](../../runtime/observations/pandora-passage-address-frame-adoption.json)
now supplies the conditional same-size form for the four stores. Full restored
C/vasm export and original exactness pass; the native CPU candidate has seven
fields and four frame guards. The
[CPU guest bridge](../../runtime/observations/pandora-CPU-guest-allocation-implementation.json)
now applies those LONG fields with checked frame guards, explicit prior-lease
ownership and tested pre-entry unwind. Both boot variants fit the existing
loader budget; 39 focused tests pass. Actual allocator returns, normal-input
passage/route qualification and matched output remain pending; modeled Exec
tests are not gameplay evidence.
[Proposal 046 continuation gates](../proposals/046-canonical-memory-layouts.md#managed-continuation-gates-2026-10-24)
state the evidence and acceptance for that slice, broader CPU workspace movement,
then separately scoped runtime allocation and OS entry/cleanup. This does not
reopen the completed original-layout review. Staged M5/M6 implementation is now
authorized after its concrete owner/fixup/lifecycle prerequisites are established.

Status: **original-layout reviewed closeout with explicit unknowns**.
[Final source-bound review](../validation/pandora-original-layout-closeout.json)
dispositions all 32 old unknown intervals and records the unchanged exact source,
remaining opaque/producer/continuation exceptions and stale-accounting limitation.
Full semantic restoration and native C remain unclaimed. Alternate-layout
execution now has the separately scoped
[experimental completion/output evidence](../../runtime/observations/pandora-relocated-output-validation.json);
normal canonical alternate-layout export is implemented with the scoped cursor
and display qualification linked above; runtime allocation and OS cleanup are not.
Initial baseline: merged `22e55bb5`.
This is a work plan and derived evidence index, not another semantic fact store.
Canonical native facts, Manual Action Log and Decision Journal remain authoritative.
The full-game objective is not satisfied by this plan or a few runtime checkpoints.

## Deliverables and separate correctness gates

1. **Original layout:** reproducible generated source for every byte of the
   376,832-byte unpacked payload, with C and independent vasm full-file equality
   to SHA256 `70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
   Unknown material stays explicit raw data until evidence justifies interpretation.
2. **Readable reconstruction:** source-coordinate coverage map with nonoverlapping
   intervals accounting for all payload bytes; subsystem boundaries, entry and
   exit contracts, data layouts/resource extents, meaningful names and comments.
   Each interpretation has source evidence and review status. Counts distinguish
   accepted code, candidate code, structured data and uninterpreted data; inferred
   function ownership and legacy annotations are never silently promoted to proof.
3. **Supported alternate layout:** explicit address-domain model and constraints,
   relocatable internal references including code operands and pointer tables,
   unchanged hardware/OS absolute references, and validated placement of mutable
   state, copied code and chip-visible resources. Build at a second legal base,
   inspect the actual changed relocations, and execute that rebuilt image under
   bounded, identity-checked observations. Successful original self-relocation
   alone does not meet this gate. Arbitrary-address portability is not promised.

Original disk image and loader parity are explicitly out of scope. The existing
packed/unpacked inputs and legal Kickstart can support analysis; no input download
or unrelated tennis changes are required.

## App-offset usage follow-up

The [static closure](pandora-restoration-status.md#app-use-static-closure-2026-10-21)
now accounts for174/178 prior omissions under explicit original-entry/stack
contracts, with four precise missing-entry sites. Across all729 A6 app candidates,
715 have original-entry links and14 occupy five retained conditional groups.
Positive alias readers/writers prevent dead-storage claims for+$190/+$2D4/+$368;
all24 app-address constructors are grouped into seven reviewed cursor contracts.
The finite remaining entry/intent evidence is listed, with no speculative next
batch selected. [Closure evidence](../validation/pandora-app-usage-closure.json)
and four C/vasm-exact source comments record the result.

The separately requested [app-offset audit](pandora-restoration-status.md#app-offset-usage-audit-2026-10-21)
now inventories all 7,059 accepted instructions and distinguishes 551 native app
attributions, 178 additional conditional A6 sites, 12 A6 audio-hardware writes,
indexed/range/cursor aliases and unresolved provenance. Its
[machine evidence](../validation/pandora-app-access-audit.json) is a derived
inventory, not another fact store. Enumeration does not certify exhaustive app
usage, complete field semantics, allocation, relocation or a C port. The qualified
closeout below and its explicit unknowns remain unchanged.

## Current closeout scope (2026-10-21, after `e19817e4`)

The five review obligations below are dispositioned in the
[final closeout](pandora-restoration-status.md#final-original-layout-reviewed-closeout-with-explicit-unknowns).
This accepts explicitly retained unknowns for a qualified original-layout review;
it does not promote their meanings, refresh unavailable native totals or certify
all historical M0–M6/B01–B10 gates. No additional task is selected by this plan.

The original-layout byte reconstruction is done and its qualified source review
is closed with explicit unknowns. Full semantic restoration, alternate-layout
execution and a native C game port remain separate outcomes. The following is the prioritized closeout list, not another fact
store. Its rows must finish with canonical evidence or an explicit, reviewed
limitation; another renamed field alone does not close a row.

| Priority / required original-layout question | Existing evidence and present limit | Acceptance condition | Next bounded action |
| --- | --- | --- | --- |
| 1. Reconcile the remaining byte partition | [Completeness baseline](pandora-completeness-baseline.json), [held-frame restoration](../validation/pandora-player-held-frame.json) and [charge-table restoration](../validation/pandora-combat-charge-plane-layout.json). The baseline's 6,446 unknown bytes predates the held-frame edit; existing weapon-table ownership also needs reconciliation with emitted rows. | Every old unknown interval is reconciled against current canonical ownership; accepted code/data and retained raw exceptions are distinguished, with no inferred padding or duplicate credit. | All 32 old intervals are dispositioned: three / 30 bytes already have bounded facts; 29 / 6,416 bytes remain explicit unknowns in that cohort. The full native partition remains stale because the resident API cannot export the required ownership/source-plan DTOs; no counter-only regeneration is selected. |
| 2. Adjudicate the three dominant raw spans | Source `$52..$456` (1,028 bytes), `$B4A8..$C3A8` (3,840), `$39DC8..$3A338` (1,392): 6,260 of the old 6,446 unknown bytes. [Dominant-range evidence](../validation/pandora-dominant-payload-evidence.json) and [access observations](../../runtime/observations/pandora-unknown-span-tracing.json) distinguish touched stack/scratch addresses from original byte purpose. | Positive producer/consumer or allocation evidence supports each interpretation, or a reviewed bounded opaque exception states exactly what remains unknown. No whole-span stack reservation, original scratch-seed meaning, or unused bank suffix is inferred from limited accesses. | Retain explicit unknown original stack/seed/suffix meanings and the separate opaque tail; no allocation/padding/non-use is inferred. The exhausted probes remain stopped. Reopen only with the final report's positive producer/consumer/format evidence. |
| 3. Resolve or bound control-flow and field ambiguities | [Indirect-dispatch audit](../validation/pandora-indirect-dispatch.json) has 22 reviewed sites; [current reconciliation](../validation/pandora-indirect-closeout.json) gives finite dispositions for the eight initially without known targets; later callback contracts add bounded knowledge, not global target closure. The [indexed-consumer review](../validation/pandora-indexed-consumers.json) partitions all 27 baseline dynamic records into seven understood reader groups. The old baseline lists 32 unresolved field accesses: four known LEA cursor advances, the already-reviewed `$790A` low-byte WORD probe, and 27 dynamic indexed operands. Native unresolved status does not mean these five lack an interpretation. | Each listed site/access has a current interpretation, supported original caller/target or field bounds, or an explicit dynamic limitation. Source/runtime aliases and copied or stack-spliced control flow must not acquire false function boundaries. | Eight indirect sites and all 27 indexed records have finite reviewed dispositions. Blitter/UI/XY activation and external continuation exceptions remain explicit; no unconditional target-set or arbitrary-input safety claim is required or added. |
| 4. Review subsystem source contracts | Existing status sections cover startup/IRQs, world commands/objects and scripts, input/timing, graphics/copper/blitter, UI/inventory/trading/terminal, NPC/combat/endgame, and audio/sequences/samples. Full function, object and resource denominators are unknown; candidate counts are not reviewed counts. | Each of these subsystem groups has an indexed entry/exit, important shared-state and data/resource boundary review, with remaining interpretation questions explicitly listed or accepted. Existing mature work is audited rather than renamed again. | Seven-group review is consolidated against mature evidence. No additional supported source correction was identified; conditional contracts and explicit exceptions are retained in the final report. |
| 5. Audit source presentation and deliver the original-layout closeout | [Latest source audit and exact receipt](../validation/pandora-indirect-closeout.json), canonical Manual Action Log and Decision Journal. Byte equality cannot detect lost symbolic meaning or incorrect prose. | Reproducible full C/vasm equality for all 376,832 bytes; labels and evidenced symbolic operands preserved; no unexplained ownership conflicts or possible code/data confusion hidden by raw emission; remaining raw exceptions and semantic limits reviewed and visible. | Final quality/preservation audit passes; source, metadata, package files and exact receipt identities still match. Deliverable: original-layout reviewed closeout with explicit unknowns. Stop this pass; full semantic restoration and M4/M5/native C remain unclaimed. |

Rows 1–5 record the completed qualified review and its retained exceptions, not a new task queue. The complete
semantic denominator and size of unresolved dynamic target sets have not been
established, so neither an overall completion percentage nor an ETA is supported.
A row needing unavailable evidence must retain its precise blocker; it must not
be silently replaced by an endless queue of cosmetic batches.

**Optional polish:** remaining internal branch names and the 47 numeric audio
control positions, formatting preferences, unused EQU/RS emission and font
presentation do not by themselves block original-layout closeout. Fonts and
EQU/RS policy remain outside the current scope. B07 reduction, a broader DMA value
oracle and UI capability work remain paused unless a concrete restoration
question establishes a need. Historical “next B07” recommendations are superseded.

**Separate work:** M4/M5 still require supported address domains, copied and
self-modifying code, chip-visible resource/alias constraints, and an actual
alternate-layout candidate executed at the changed addresses. No alternate-layout
safety is implied by exact original output. A native C game port has no accepted
complete translation or measured implementation denominator; the C disassembler
and generated CPU backend are tools, not a C port of Pandora. Neither that port
nor disk/loader parity is part of the original-layout closeout above.

## Initial inventory (historical baseline)

The initial shared-service snapshot reported 7,087 accepted instructions, 230 function
candidates, 2,096 symbols, 3,925 typed references, 3,364 CFG edges, 411 typed field
uses and 156 analysis review items. Counts are a dated snapshot, not completion
percentages. The complete byte partition is recorded in the status report; semantic resource
boundary reconciliation remains pending.
The 990 existing actions include 989 legacy/unassessed records. Preserve them.

Native startup evidence already distinguishes source location from execution
location: source `0x00..0x27` disables custom interrupts/DMA, discovers its own
load location with PC-relative addresses, copies 42 bytes from `0x28..0x51` to
absolute `0x300`, and jumps there. That helper chooses a forward or backward
byte copy according to source/destination ordering, copying `0x55370` bytes to
fixed `0x10000`, then transfers to `0x1046A`. The direct contract initially loads
at `0x20000`. These facts establish a fixed execution layout and overlapping-copy
requirements, not arbitrary-base support. The relationship between copy length
and the full payload tail must be audited before defining relocated layouts.

## Milestones and acceptance

| Milestone | Work | Acceptance evidence |
| --- | --- | --- |
| M0: complete inventory | Account for every byte; reconcile accepted code runs, data ranges, padding/raw regions, resources and overlaps. Inventory functions, indirect edges, pointer encodings and existing history. | Coverage partitions sum to 376,832 with no gaps/overlap; counts separate semantic certainty from byte coverage; every unresolved interval has a bounded next question. |
| M1: startup and relocation | Recover boot entry, copied helper, fixed execution continuation, stack/application state, interrupt installation, memory clearing/copying and all startup address assumptions. | Reviewed names/comments and register/memory contracts; copy source/destination/size/direction proven; code writes and resource tail classified; full exact rebuild. Runtime probes only for unresolved reachability/state. |
| M2: global program structure | Map startup-to-title-to-gameplay transitions, interrupt/callback ownership, shared application state, dispatch tables and lifecycle transitions. | Entry points and reachable dependencies indexed; each indirect transfer resolved with evidence or retained with a specific unknown; no next-label function-boundary assumptions. |
| M3: dependent subsystems | Restore graphics/copper/blitter, UI/text/inventory, world/map/object logic, input/timing, audio/sequences/samples and resource formats in dependency order. | Reviewed coherent batches with data bounds, call/data consumers, comments explaining behavior/invariants, exact original rebuild and relevant focused tests. Existing mature annotations are audited, not replaced indiscriminately. |
| M4: alternate-layout model | Classify internal relocatable addresses versus hardware/OS/fixed RAM/serialized values; model split regions, signed widths, alignment, relative tables, copied/self-modifying code and DMA restrictions. | Generic framework representation only where an actual recurring capability is missing; target-owned layout constraints; original-layout exactness unchanged; second-base relocation expected-value checks include positive and negative cases. |
| M5: alternate-base execution | Build and run an actually different supported execution layout with canonical source mappings. | Proven relocated code/data/table references and unchanged hardware/OS addresses; identity checks against relocated rebuilt bytes; verify actual PC, data and DMA addresses belong to the alternate layout and startup does not copy back to `0x10000`; attach layout configuration and source mapping to receipts; dependency-led behavior probes beyond original startup; forbidden placements rejected. |
| M6: full-game closeout | Audit remaining raw bytes, anonymous code/data, unresolved edges, comments, resource ownership, conditional paths and reverse-engineering claims. | Every payload region accounted for; remaining semantic uncertainties explicitly adjudicated rather than hidden; subsystem acceptance ledger complete; original exact rebuild reproducible and original-layout closeout questions above adjudicated. Alternate-layout acceptance remains a separate M4/M5 gate; a handful of checkpoints cannot close either scope. |

M4 may proceed alongside later M3 batches once startup/address constraints are
known. Alternate-base binary bytes are expected to differ where relocation is
required; only the original layout must match the original SHA exactly.

## Completion ledger and uncertainty

Maintain a derived per-subsystem/interval ledger referencing canonical actions,
source keys, review decisions and verification receipts. Each row records
unknown/hypothesis/reviewed/verified status, its blocker and next evidence question;
the ledger does not independently grant acceptance. Byte coverage is not semantic
completion. Original-layout closeout may retain explicitly reviewed bounded raw
exceptions as described above; this does not grant them a semantic interpretation.
For alternate-layout acceptance, opaque resources need understood ownership,
extent, consumers and relocation behavior. Unresolved
control-flow targets, conflicting source/runtime identities, unknown pointer
encodings, possible code misclassified as data and unexplained address-dependent
writes block full-game or alternate-layout completion. Report such blockers
explicitly rather than marking the containing subsystem complete.

Plan review approved inventory/startup work. Its requested ledger and actual
alternate-PC/data/DMA checks are incorporated above. Initial audit has also found
legacy handler labels with possible source/runtime coordinate confusion; those
records remain preserved pending dispatch/instruction corroboration.

## Batch protocol and general framework improvements

Use shared revision-bound operations: inspect → evidence-bearing catalog action
→ canonical regeneration → exact verification → question-led probe where needed
→ independent review → durable review decision. Capture old histories and preserve
existing bytes. Undo/redo appends corrections; never hand-edit generated `.s`.
Publish logical reviewed draft PRs; merging requires a new request for this task.

For a framework gap, demonstrate the recurring problem and identify its existing
owner before implementation. Extend native typed facts, shared service or existing
evidence/history models, with generic synthetic and preferably second-target
regressions. Migrate callers and remove superseded code when applicable. Keep
Pandora addresses, names, structures and layout assumptions in target-owned facts
or configuration. Do not add a second analysis pipeline or speculative abstraction.

Observed opportunities to review:

- Coverage queries: existing native region ownership/code runs/data descriptions
  need compact, revision-bound byte-accounting access. Inventory must not scrape
  generated assembly or pretend instruction queries describe all payload bytes.
- Evidence matching: symbols with absent source coordinates currently compare
  equal to legacy actions with absent subject coordinates, falsely attaching
  unrelated evidence. Require concrete identities, retaining valid zero offsets;
  generic null/partial-identity regressions will guard the fix.
- Candidate naming: native function candidates can retain generated aliases even
  when accepted rendered symbol facts have meaningful names. Assess canonical
  identity/provenance before changing projection; names alone cannot measure
  semantic completeness.

Major unresolved ambiguities that change supported layouts or user-facing scope
will be reported with the competing evidence. Missing analysis is analysis work;
it is not automatically a missing framework feature. Keep logs bounded and avoid
full instruction traces. Preserve the resident server between target operations.

Opaque asset packaging/INCBIN export is owned by a separate parallel task. This
work may classify asset boundaries and relocation needs, but will not implement
a competing exporter or edit its assembler/source-packaging path. Adoption will
follow independent review and coordinated integration.

## Walkthrough completion dependencies (current after saved-Earth qualification)

Current result: [qualified ending receipt](../../runtime/observations/pandora-saved-earth-walkthrough.json). The complete route is authored by `pandora_finale.complete`; checkpoint-development sections below retain their historical context.

The completion target is **Earth saved and player escaped**, not a kill count,
item count, or every optional encounter. Original-layout source is authoritative
for local predicates; the [published game hints](https://amiga.abime.net/1008)
provide an intended route lead. The full page could not be fetched (the network
proxy returned403); indexed hints corroborate Engineer/sonicdriver collection,
SDI disk from Captain, sonicdriver→Ochre trade, console submissions and Engineer
ID on departure. Treat unobserved travel/access dependencies as hypotheses.

| ID | Required objective / concrete completion predicate | Evidence and current state | Next bounded action |
| --- | --- | --- | --- |
| G01 | Remain active and preserve enough health/time for the ending | Complete cold route ends HP49, active; deadline nonzero at saved-Earth selection. Health95→70(Icelord)→49(Hooligan), then unchanged. | Complete for the qualified route. |
| G02 | Acquire SDI disk38 (`$26`) | Captain disk retained in pocket0, then consumed by original console input. | Complete. |
| G03 | Acquire Blue33/Scarlet35 and preserve them until submission | Both retained from Commander; distinct cards consumed at the console. | Complete. |
| G04 | Acquire Ochre36 (`$24`) | Normal sonicdriver5 trade after early Icelord defeat; Ochre retained and consumed at the console. | Complete. |
| G05 | Arm the self-destruct console | SDI38 then Scarlet35/Ochre36/Blue33 accepted: qualifying3, submitted3, stateFF. | Complete in continuous cold qualification. |
| G06 | Obtain escape authorization | HeldAWOL55 at descriptor21 sets eventbit4 after the wrapped return and empty-handed Thief crossing. | Complete. Engineer retained in pocket0. |
| G07 | Escape through tile236 while authorized | Horizontal input at the escape tile enters original source$4C994; eventbit3 set. | Complete. |
| G08 | Validate the successful ending, not merely an armed console | Original source$4C9DC selected saved-Earth pointer$5CAE5; stateFF, flags5C, nonzero deadline. Complete uninterrupted cold replay and movement inhibition observed. | Complete for the selected ending; optional encounters and title restart not required by this receipt. |

Source anchors are the existing named routines and tables in the target `.s`:
`process_self_destruct_card_input`, `validate_self_destruct_qualifying_card_count`,
`test_escape_authorization_for_requested_tile`, `latch_authorized_checkpoint_visit`,
`enqueue_game_outcome_and_rank_messages`, `captain_inventory_slots`,
`commander_inventory_slots`, `robomechanic_inventory_slots` and
`robomechanic_trade_offers`. No source/fact mutation is implied by this checklist.

**Historical route assessment (superseded by the qualified wrapped route):** Engineer50 is an evidenced exact-card engineering checkpoint
and intended-route item, but not a direct ending predicate. Sonicdriver5 has a
direct progression use as the Ochre trade. The Icelord's completion callback is
NULL and its inventory is Ice Pendant/Thermolance; none is a direct ending input.
Its defeat remains an optional tested detour, not certified golden-path progress.
Combat initialization also opens a shared passage tile, so NULL callback alone
does not prove absence of all traversal side effects. The completion prefix
omits Icelord and records its actual encountered Hooligan interaction instead. It consumed no tool/card and cost25HP. No mandatory item
has been irreversibly bypassed, but G02–G08 remain unfinished. Laser-rifle pickup
in the hints is not itself an ending predicate; any route-specific need must be
shown before calling it mandatory. Keep the earlier Icelord evidence as an
optional driver exercise, and do not replay that detour in the completion prefix
without a demonstrated dependency.

## Saved-Earth walkthrough qualified (2026-10-22)

[Ending receipt](../../runtime/observations/pandora-saved-earth-walkthrough.json)
records one uninterrupted cold direct-payload boot: **576 canonical
phases, 375 normal input events**, ending frame 14,332,
HP 49. No checkpoint loads occur in that qualification. Earlier
checkpoint branches are development evidence only. The original queue call at
source `$4C9DC` selected saved-Earth message pointer `$5CAE5`; self-destruct state
was `$FF`, event flags were `$5C` (authorization, escape and
outcome latched), and Earth deadline WORD was `0x8258`.
The next original instruction confirms movement inhibition.

The revised route defeats Icelord **before** sonicdriver5 is traded for Ochre,
retains its Thermolance11, and uses that weapon for Hooligan. Health is
95→70→49, then remains 49 through the ending. Icelord is a tactical prerequisite
of this chosen wrapped return, not a universal ending predicate. SDI38 and
three distinct intended code cards (Scarlet35, Ochre36, Blue33) are consumed.
Engineer50 crosses engineering and is pocketed through the Thief strip; held
AWOL55 then sets authorization at descriptor21 before the horizontal escape-tile
probe. This closes G01–G08 for **this route**, not every optional game objective.

The driver was useful for this extension: it preserved the item/health budget,
localized incorrect gate approaches and patrol crossings, and exposed the armed
console's different horizontal exit drift. Failed branches are retained in the
receipt with actual later diagnostic state, not recast as successful runs.
Section composition now retains compatible entry guards and rejects conflicts;
goal-search boundaries keep the next entry check after goal completion,
so transient combat positions are not required to match the later world state;
old Captain/Ochre/AWOL default authored identities are unchanged. The measured
577 authored stages (including initial handoff) and 375 events required increasing
the finite shared scenario limits to 768/512; per-phase bounds and release rules
are unchanged. **184 focused tests passed, no skips.**

No target source/binary was changed or regenerated: their previous byte-exact
receipt is preserved and their hashes were rechecked by every runner invocation.
This is original direct-payload gameplay, not original disk-loader parity or
proof of all DMA, memory usage, relocation or native-C behaviour. The original
successful outcome and escape transition are observed; reading every scrolling
message and the subsequent automatic title restart are outside this receipt.
Reproduce the declarative complete plan with
`python -m amiga_reversing.tools.pandora_finale --output /tmp/pandora-ending.json`,
then use the existing `copperline_session` target/ROM/direct-payload scenario
workflow. `--stage` emits bounded checkpoint-development sections;
`--checkpoint` makes only the complete recipe begin at the verified Commander
checkpoint and must not be described as a cold replay. The receipt binds actual
executed code, authored/compiled plans, reports and private checkpoint identities.

Raw media/checkpoints/captures stay private. PR5 remains unmerged and all nine
paused B07 files retain their prior hashes. **The requested successful-ending
walkthrough objective is complete; no further mandatory route step is queued.**

Earlier checkpoint and route-planning sections below are historical, including
statements that submissions, authorization or the ending were then pending.

### Historical required-route checkpoint

[Qualified evidence](../../runtime/observations/pandora-required-progression.json):
one uninterrupted cold boot, frame2572, player `(192,190)`, HP95, held Commander48,
carried `[50,5,0,0]`, pockets `[0,0,33,35]`. Lt Commander49 was exchanged into the
Commander body and remains recoverable there. Authorized-checkpoint count1/seen
bits2 match the Lt Commander gate branch. Self-destruct remains0 and Earth
deadline is nonzero; no ending is claimed. **Next required objective: Captain
SDI disk38**, using the now-held Commander card. Ochre route/trade remains an
independent unresolved dependency. Keep progressing G02–G08; this item milestone
is not walkthrough completion.

### SDI disk checkpoint

[SDI evidence](../../runtime/observations/pandora-sdi-progression.json) qualifies
one uninterrupted cold boot through218 phases/128 input events, frame4846,
player `(647,986)`, HP32, Commander48 held, carried `[50,5,49,38]`, pockets
`[0,0,33,35]`. No unique required item was lost. Leaving the Lt Commander gate
requires keeping49 until lateral drift clears its contact region; the Commander
card is protected through Thief's Y532 patrol by crossing empty-handed. The
selected corridor encounters Hooligan; twelve normal5-point hits defeated it,
costing63HP. This is a tactical choice on this route, not a direct ending test.

**Next: G04 Ochre36.** A revised staging goal below Robomechanic atY1606 has a
conditional model route. Carry Engineer50 through the engineering checkpoint,
switch to sonicdriver5 near Robomechanic, and verify the actual exchange. Then
prepare AWOL authorization and all console inputs before arming the3000-service
self-destruct timer. Blue/Scarlet and SDI are acquired; Ochre, AWOL and the ending
remain unfinished. Current HP32 is an observed active state and a navigation
assertion, not a restored/forced health value.

### Ochre checkpoint

[Qualified evidence](../../runtime/observations/pandora-ochre-progression.json):
293 phases/190 events from cold boot, no checkpoint load/intervention, frame8095,
HP32, `(556,1606)`, held Ochre36, carried `[48,50,49,38]`, pockets `[0,0,33,35]`.
NPC inventory/offer mutations separately verify the real exchange. The two
observed-Y patrol waits avoided another fight; this is a verified deterministic
prefix, not arbitrary patrol-phase safety. The first cold version failed closed
because post-trade checks ran before exchange; the corrected version checks them
in a separate final phase. 195 focused tests passed, no skips.

**Next required objective: G06 preparation, acquire AWOL55** from its officer
body `(944,1776)`. Existing source gives a64x32 body rectangle and first-slot
card55. A conditional approach ends inside that rectangle near `(934,1746)`;
validate live, pocket Ochre/AWOL and retain Engineer for departure. G05 console
submissions and G07/G08 escape/outcome remain unfinished. Do not arm the timer
before all items and the exit route are prepared.

### AWOL acquisition checkpoint

[Qualified evidence](../../runtime/observations/pandora-awol-progression.json):
340 phases/217 input events, no checkpoint load/intervention, frame8818,
HP32, `(934,1746)`, Engineer50 held; carried `[48,0,49,38]`, pockets
`[36,55,33,35]`. The first-slot AWOL card was pocketed and Engineer recovered.
Kwik-Kleen crossing uses actual observed position; correct body inventory uses
an owner predicate immediately after the original proximity update. The
12 focused recipe/player checks passed; no shared mechanism changed this batch.

**Next required action:** establish console entry and a viable exit route before
arming. G05 disk/code submissions are all pending; G06's AWOL acquisition is
done but checkpoint21 authorization/eventbit4 remains unobserved. G07/G08
Earth-saved escape are not complete. This checkpoint has every required item;
HP32 is retained rather than forced/reset.

### Return preparation and corrected tactical dependency

[Bounded return evidence](../../runtime/observations/pandora-return-preparation.json)
proves55 phases/45 normal-input events from the AWOL checkpoint, ending
`(1298,144)`, HP32, Engineer50 held, carried `[48,0,49,38]`, pockets
`[36,55,33,35]`. Source$9C00/$9C88 console entry/loop and normal exit are observed;
state0 remains checked. Engineering exit is clear. The original camera wraps at
Y2016 toY16 via$9960; the static terrain planner omitted this genuine transition.

The direct corridor triggers DeathFly combat; the wrap route triggers Icelord
combat at1298180. Actual Icelord setup is player5/reload3, opponent25/reload4,
HP32 versus95. An ending condition does not require an Icelord flag, but this
selected return path cannot assume the live encounter harmless. The next
concrete task is to clear it while sonicdriver5 is still owned, before the
Ochre trade, then carry **measured** health through subsequent fights and replay
the connected prefix/exit. Existing `12ceae72` fight evidence demonstrates the
Sonicdriver override; it does not validate the new composition or any weapon
pickup. A separately proved weapon route is an alternative, not yet available.

**G05–G08 remain open:** no disk/cards submitted, no descriptor21 authorization
observed, no Earth-saved escape. Current console is deliberately unarmed.
The complete inspection is a checkpoint extension, not a new full cold receipt.
15 focused player/recipe checks passed. No target output changes or redundant
whole-source generation accompany this result.
