# Pandora restoration inventory and status

## Canonical layout implementation checkpoint (2026-10-24)


[Live Copper constraint](../../runtime/observations/pandora-display-live-pointer-constraint.json)
now explains the first-surface mismatch causally. The D8000 profile completes
both controlled and unheld576-phase routes (HP49/frame14465 and14353), and matches
all phase clocks,509 calls, PCM and later selected output. It still fails graphics:
14 pixels differ on the first partial title surface. Four-frame bus traces show
two fetches interleaved between live high/low Copper writes: D0002/D0006 read
image/audio words3831/9699 instead of the original seeded zero reads70002/70006.
Those words contain14 set bits. This is not an initial-RAM seed hypothesis.

The retained sequence now has an explicit64-KiB parent alignment constraint.
Original70000 is valid; D8000 now refuses rather than being reported as qualified.
The next candidate is displayE0000..ED000 with cursor still65370, independently
of image80000. No simultaneous cursorE0000/display claim is made.73 focused tests
pass and full original C/vasm remains exact (`743e95a4…`). E-layout build and fresh
common-loader qualification are pending. The failed comparator remains failed;
no tolerance, crop, fitted delay or Copper timing change was introduced. This
runtime display issue is separate from the unchanged pre-GO eight-CCK finding.


The [status/ticker alias follow-up](../../runtime/observations/pandora-display-status-aliases.json)
retains a second real watch failure at frame944/source `$9ABE`/old `$77800`.
Two existing address expressions now render symbolically; original full C/vasm
remains exact (`7f2a2ce0…`). The repaired candidate rebuild/qualification is
pending; neither negative is erased or treated as a pass.

Active continuation: [display contract / retained failure](../../runtime/observations/pandora-display-initialization-contract.json).
The new 53,248-byte display-group candidate retains cross-bank clear and
snapshot/palette offsets, plus the two-byte priming seed. Initial title pixels
match, but its first full route stopped at frame595 on a proven stale overlay
base. Immediate-reference runtime-domain preservation is fixed and 177 focused
tests pass; original full C/vasm remains exact (`32a3c5a6…`). Repaired candidate
qualification is pending, not a display-completion claim. Broader movement,
allocator-selected loading and OS cleanup are authorized staged work; B07 stays
paused and the eight-CCK finding stays recorded without blocking that work.

[Independent workspace qualification](../../runtime/observations/pandora-canonical-workspace-qualification.json):
the normal image at `$80000` plus 140-byte cursor workspace at `$E0000` completes
saved Earth and escape through 576 normal-input phases. The unheld cold run ends
at HP49/frame14353 with both loss counters zero. Controlled original, image and
cursor runs each end at HP49/frame14465. These fresh runs use the same explicit
guest seed program; they are distinct from the earlier image-only frame14351 run.

Against the canonical image-only control, the independent cursor move passes
all 576 phase clocks/509 controller calls, eight exact selected frames and
24,726,568 exact float audio samples through EOF. Six sampled core DMA frames
match, with the same eight NULL-sprite reads at addresses0/2 explicitly outside
asset bounds. Two additional inventory DMA frames have no bounds findings and
identical streams; three stopped 140-byte snapshots/typed app pointers match.
[Output receipt](../../runtime/observations/pandora-canonical-cursor-output.json).

Original-to-image strict comparison still refuses the eight-CCK HAND-stop
difference; its cause is unknown. Stopped registers, all later phase/controller
clocks and eight selected images agree. Separately, PCM from each actual HAND
clock through EOF is exact; both clocks select sample441704. No shifted window,
tolerance, resampling or title crop was used, but this does not turn strict
bootstrap-cycle refusal into a pass.

The [retained 136-byte mismatch](../../runtime/observations/pandora-cursor-inventory-boundary.json)
led to the four-byte loader-file seed and 140-byte observed footprint. Guest
initialization runs before HAND/GO, with no host seed/gameplay-memory injection.
Original intent and any unobserved continuation remain unknown. All three normal
profiles preserve C/vasm agreement and all original 376,832 bytes remain exact
(receipt `da3c4265…`). 306 focused checks pass. No new unknown-byte reduction is
claimed. The nine paused B07 files match their saved hashes and remain untouched.

The target string-patching builder and alternate build CLI are retired; the
normal observer now consumes native bounds and shared launcher/callback options.
181 focused tests and a matching settled-title smoke pass; 24 retained DMA
frames replay unchanged. The older single-region service now delegates extent,
overlap and base-plus-offset calculations to the canonical layout module. It
retains Slow RAM/Exec lease, fixed-width ledger, initialization and proof semantics
as an adapter; those supported capabilities were not deleted or expanded into M5.
289 relevant regression tests pass. The final fresh original export retains
source/package equality and current C assembly matches the retained independent
vasm output for all 376,832 bytes. See the
[milestone acceptance ledger](../../runtime/observations/pandora-layout-delivery-acceptance.json).
Strict original HAND-cycle equality remains unfulfilled; unconditional first-delivery
closure is not claimed. Layout selection now reaches the common exporter through HTTP,
CLI, real MCP stdio and the palette; 48 interface tests and four server-route
tests pass. Browser E2E has not run.

[Native frozen-plan reuse](../../runtime/observations/pandora-layout-reuse-performance.json)
now takes 21.65/21.00 s for two warm cursor exports versus 290.25 s for the
fresh clean cursor export, with identical source/packages and no analysis calls
on the warm requests. All original/image/cursor C/vasm payload hashes are
unchanged. 280 relevant tests pass (240 deselected), including stale loaded-code,
input/fact invalidation, concurrent ownership and invalid-placement refusal.
Warm projection still copies 123.33 MB of row/declaration state and traverses
49,650 rows; this is scoped reuse, not universal incremental analysis. Image,
bootstrap/profile and structure-macro changes retain conservative rebuilds.
[Boot-only probes](../../runtime/observations/pandora-layout-preentry-clock-probe.json)
locate a difference before CMD_READ, without establishing the cause of the
controlled eight-CCK HAND stop. No full-route rerun or fitted delay was added.

### Current startup diagnosis and next implementation slice (2026-10-24)

[The bounded HAND investigation](../../runtime/observations/pandora-HAND-causal-boundary.json)
reproduces the exact eight-CCK difference before GO. Identical guest wait code and
all 17 observed register/PC boundaries match, including ROM interrupt entry;
`run_until` returns after the requested CCK at different instruction phases.
Earlier boot/read/interrupt scheduling remains the causal boundary: no evidence
identifies a target relocation defect or justifies a game patch. Strict comparison
remains refused. No fitted delay, comparator change, full route or regeneration.

The next proposed implementation slice is the display initialization/alias
contract: the cold seeded clear crosses `$70000..$7CD28`, both framebuffer roles
and reused storage. Resolve that producer together with bank swap, lower-screen
Copper, snapshot/palette containment and loader-tail initialization before
admitting another bank move. The
[managed continuation gates](../proposals/046-canonical-memory-layouts.md#managed-continuation-gates-2026-10-24)
also define a separate broader CPU-workspace gate, a bounded genuine runtime
allocation/loading gate, and OS entry/cleanup acceptance. Those later stages
remain proposals, not implementation or all-path equivalence claims.

### Earlier mechanism batches (historical)

These earlier receipts retain their original scope; pending steps are superseded
by the checkpoint above.

[Latest canonical adoption](../../runtime/observations/pandora-canonical-layout-adoption.json):
25 accepted API facts model the copied image, paired cursor workspace, display
roles and twelve receptacle pointers. Original C and independent vasm output
match all 376,832 bytes; 126 asset identities and 3,772 labels are preserved.
The focused layout/domain suite passes 72 tests (four deselected), including
refusal of split materialized views and partially covered moved references.
Seven missing include companions are restored without relaxing package guards.
M0–M2 remain partial: bootstrap contracts, real profiles and independently moved
block/output qualification are still pending. No new runtime result or unknown
byte classification is claimed. The nine paused B07 files are unchanged.

The next local mechanism slice supplies the retained prefix-copy contract and
typed bootstrap variant through normal catalog/MAL/native planning. Its focused
suite passes 336 tests (four deselected), including independently assembled
synthetic original/variant fixtures and stale/unsupported input refusal. This
does not yet qualify real Pandora layout profiles or independently moved storage.

[M0/M1 partial evidence](../../runtime/observations/pandora-memory-layout-baseline.json):
89 focused tests pass; native materialization indexing replaces view scans and
byte-by-byte span checks. The full original native source package and nine-region
projection remain unchanged. Baseline artifact/package costs are 202.04/8.30 s;
single before/after runs are not an overall speedup claim. The paired cursor
workspace is selected for constraint analysis, with control/DMA bounds still
pending. Canonical layout export and independent movement are not delivered;
first-delivery M1–M4 acceptance remains open. No new gameplay capture in this batch.

The subsequent M1 placement batch adds canonical region kinds/parents and named
fixed-layout definitions through the existing MAL/catalog/native query path.
225 focused tests pass; socket-enabled interface tests report seven passes and
one skip for the missing optional MCP SDK. Native `placement_valid` results retain
`export_ready: false`. Normal source export, bootstrap migration, real transport
qualification with that SDK and independent workspace movement remain open.

The source-preview batch adds canonical layout selection to the normal exporter,
with native base/offset planning and typed runtime-symbol/ORG projection. Synthetic
original/moved vasm fixtures and related regression suites pass (335 focused
tests). Native import now rejects scalar/mixed layout entries and fractional or
exponent numeric tokens. Package source/assets share one analysis artifact.
Exports remain explicitly runtime-unqualified; real Pandora bootstrap/reference
adoption, original/alternate build checks and independent-block gameplay/output
acceptance are still pending.

## Canonical layout design (2026-10-23)

[Proposal 046](../proposals/046-canonical-memory-layouts.md) audits the existing
region/address-domain/export implementation and the successful relocation
experiment. Its first delivery includes canonical image/code, workspace and
display base-plus-offset regions; normal-export original and known `$80000`
layouts; and at least one independently moved workspace or display block selected
from actual reference/alias/DMA constraints. Both region kinds are represented;
both need not physically move. Image-only qualification cannot close delivery.
Explicit bootstrap contracts, indexed resolution and deletion gates for the
experimental patches remain required. Runtime allocation and OS-hosted lifecycle
are separate later gates. This documentation revision implements no architecture
and performs no new runtime qualification.

## Relocated completion and scoped output comparison (2026-10-23)

[Final evidence](../../runtime/observations/pandora-relocated-output-validation.json)
records matched original/relocated cold runs on the same ECS/1MiB Chip profile:
576 phase clocks and509 controller calls agree; eight captured frames are pixel
identical and24,726,568 recorded post-GO float audio samples are byte-identical.
A separate cold final-payload run without the clock hold completes at HP49.
126 exported assets and all11 primary audio payloads are unchanged. Six sampled
DMA frames per layout preserve eight original NULL sprite-control reads at0/2
as an explicit bounds finding, not certified asset safety. Original byte-exact
source is retained; this is not every-frame/optional-path, original OCS/packed
boot or universal DMA equivalence. See the validation report for the explicit
pre-game HAND/GO fixture and loader-only opaque tail.

### Earlier gameplay-only milestone (superseded)

[Two cold relocated completions](../../runtime/observations/pandora-relocated-completion.json)
pass all576 phases at `$80000` on the separate ECS/1MiB Chip profile, HP49,
with the visible saved-Earth ending. Original byte-exact source is preserved.
126 exported asset files are unchanged; six complete sampled DMA frames have
no old-image transfers. Same-profile differential graphics/PCM validation is
now part of acceptance and remains in progress; these results do not claim it.


## Master consolidation (2026-10-23)

The user explicitly requested direct master publication and integration of PR5,
superseding the inherited no-merge constraint. No original user instruction to
hold PR5 or these nine working files could be established; the earlier hold
attribution was incorrect. Integration preserves all 148 PR-only commits via
merge `57640fe8` and the existing master watch/static reports. Experiment
`b3113d1b` is included by cherry-pick `cde86346`; it remains experimental and
stops at its first stale pointer, not a relocated walkthrough success.

The nine local B07 files were inspected and copied with hashes and a tracked
patch into the private `.runtime-state/pandora-consolidation-20261023` evidence
directory. They are a deterministic CPU controlled-negative reducer, service/MCP
hooks, tests and proposal-status edit. They are not accepted target behaviour
coverage or part of this consolidation. They remain unchanged and uncommitted in
the original working tree; this is preservation of unfinished work, not a user
publication hold. The two other untracked watch files are older copies of work
already integrated (master's test also checks missing queue-loss counters).

Fresh merged-source C and vasm assemblies both reproduce the complete
376,832-byte original, SHA-256
`70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
No source regeneration, gameplay rerun, relocation repair or B07 expansion was
performed for consolidation. Integration test results are recorded in the
[consolidation evidence](../../runtime/observations/pandora-master-consolidation.json).
The focused combined integration suite passed **438 tests with 3 skips** (two
real-emulator prerequisites and optional MCP SDK). A broader selection was
interrupted after **927 passes, 2 skips and one failure**: an old animation
inventory assertion expects 89 nodes, while current accepted metadata has 92.
That failure and three optional backend decompression/identification failures
reproduce on the unchanged PR checkout. They are reported, not hidden or counted
as green; no assertion or production code was weakened to publish the merge.


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

## Return-route prerequisite identified before arming (2026-10-22)

[Return preparation](../../runtime/observations/pandora-return-preparation.json)
records a complete **checkpoint-based extension**,55 phases/45 input events,
from the qualified AWOL cold checkpoint. It enters/leaves the console unarmed,
clears engineering holding Engineer50, and uses the game's explicit bottom-to-top
shaft wrap. Final frame11293: `(1298,144)`, HP32, held50; carried `[48,0,49,38]`,
pockets `[36,55,33,35]`. Console state0.15 focused player/recipe tests passed.
This is not an additional uninterrupted cold qualification or ending.

The static planner omitted camera wrap, so its no-bypass result around DeathFly
was incomplete. The actual source$9960 write sets Y16 after normal down input
reaches the2016 camera threshold; source$9966 and live state verify the transition.
No guest-state injection. The direct corridor encounters armed DeathFly; the
wrapped upper shaft encounters live Icelord. Its measured parameters are
25 damage/reload4 against current default5/reload3, with playerHP32 and NPC95.
Both rejected crossing probes are distinct from the healthy retained checkpoint.

**Next required prefix revision:** clear Icelord with sonicdriver5 **before**
trading that tool for Ochre, using the previously qualified special fight; then
remeasure health and validate the connected return. Retaining its Thermolance11
may improve subsequent combat but is not yet a validated pickup/route change.
Icelord is not an ending predicate; it is a demonstrated obstacle on this chosen
return route. Do not silently promote the earlier 'optional detour' assessment
to a guarantee that an alive Icelord can be ignored on every completion route.

All disk/code submissions, AWOL checkpoint authorization and Earth-saved escape
remain pending. The console stays unarmed while that route prerequisite is
unresolved. No executor/access blocker, target-byte change, extra generic
framework, memory-watch campaign, B07 work or PR merge. Earlier sections are
historical and their successful qualifications retain their original identities.

## Failure-snapshot reporting corrected (2026-10-22)

Failed movement summaries previously preferred the last canonical hit even when
a later diagnostic stop existed. That incorrectly paired later failure frames
with old healthy positions/HP. The observer now prefers the diagnostic stop on
failure and preserves the last canonical state separately;13 focused
recipe/player checks pass, including this regression.

Raw-report hash checks identify affected rejected runs in the SDI, Ochre and
AWOL evidence, now corrected in place with explicit correction metadata. The
first failed Ochre approach ended dead; the failed AWOL approach endedHP5.
These were discarded branches. **Successful cold qualifications, original
execution identities and healthy retained roots are unchanged**, including the
qualified AWOL checkpoint atHP32. No target/source bytes or B07 files changed.

## AWOL card acquired, ending still pending (2026-10-22)

[AWOL progression](../../runtime/observations/pandora-awol-progression.json)
qualifies one uninterrupted cold boot through340 phases/217 input events,
frame8818, `(934,1746)`, HP32. Engineer50 is held; carried items are
`[Commander48,empty,Lt49,SDI38]`; pockets are `[Ochre36,AWOL55,Blue33,Scarlet35]`.
All required console inputs are retained. AWOL **acquisition** is complete;
descriptor21 escape **authorization** has not yet been observed.

A rejected attempt identified actual Kwik-Kleen combat via pointer$5BBB6;
waiting outside its patrol enabled the crossing without damage. A second
failure opened the wrong inventory despite correct body geometry. Source/live
inspection identified the nearest-object context; waiting at post-proximity
source$5EA for AWOL ownership enabled the normal keypress/body-panel exchange.
12 focused recipe/player tests pass, no skips. Shared mechanisms are unchanged
from the195-test Ochre qualification. No new source/fact output, classification,
memory-watch campaign or B07 changes. PR5 remains unmerged.

**Next:** establish console entry and the departure/escape route before arming,
then submit disk38 and Scarlet35/Ochre36/Blue33, obtain AWOL authorization and
validate Earth-saved escape. No ending or original disk-loader parity claimed.
Earlier sections are historical.

## Required Ochre trade completed (2026-10-22)

[Ochre progression](../../runtime/observations/pandora-ochre-progression.json)
qualifies one **uninterrupted cold boot**, 293 phases/190 input events, ending
frame8095 at `(556,1606)`, HP32, Ochre36 held. Carried items are
`[Commander48,Engineer50,Lt49,SDI38]`; pockets retain Blue33/Scarlet35. The
Robomechanic now holds sonicdriver5, its selected inventory entry is `(5,40)`
and the sonicdriver offer is consumed. No required item lost.

The route crosses engineering with Engineer50 and waits on observed patrol Y
before crossing Defence Controller and Wackobrain. These waits needed92/111
visits; the real trade needed196. Shared bounded memory-goal polling now admits
up to1024 visits with explicit frame budgets; ordinary counted actions retain64.
The concrete full route fits512 phases/256 events. **195 focused tests passed**,
no skips. A failed first cold run exposed premature post-trade assertions;
postconditions now run after the trade goal, with a regression guarding this.

**Next: AWOL55 acquisition**, then prepare all console inputs, submit the disk
and three code cards, obtain escape authorization and verify Earth-saved escape.
No ending, disk-loader parity, arbitrary patrol safety, new source classification
or CPU/DMA access coverage is claimed. Source bytes and nine paused B07 files
remain unchanged; PR5 remains unmerged. Earlier sections are historical.

## Required SDI disk acquired (2026-10-22)

[SDI progression](../../runtime/observations/pandora-sdi-progression.json): one
**uninterrupted cold boot**,218 phases/128 input events, frame4846. Player
`(647,986)`, HP32, Commander48 held; carried `[Engineer50,sonicdriver5,Lt49,SDI38]`;
pockets2/3 retain Blue33/Scarlet35. No required item lost; no ending claimed.

Actual route obstacles are preserved: exact-card gate/lateral-drift sequencing,
Thief theft avoided by empty-hand crossing, and Hooligan combat identified from
a natural entry breakpoint rather than misreported as terrain. Twelve normal
5-point hits cleared that encountered opponent; this is not a universal ending
prerequisite. Movement now guards held items and reports combat coordinate bias;
post-fight HP32 is checked rather than reset. The existing bounds model admits
the original2-byte animation-toggle command, closing the patrol bounds used in
route diagnosis. Shared bounded capacities256/128 fit the concrete recipe.
**186 focused tests passed**, no skips. No target source change, new classified
bytes, repeated gap watches or B07 work. PR5 remains unmerged.

**Next required item: Ochre36** through the sonicdriver trade. The revised
below-patrol goalY1606 has a conditional route, with Engineer50 required at the
engineering gate. AWOL authorization, console arming and saved-Earth escape are
still pending in the [G01–G08 checklist](pandora-restoration-plan.md#walkthrough-completion-dependencies-2026-10-22-after-12ceae72).

## Required ending route corrected and advanced (2026-10-22)

The [finite G01–G08 checklist](pandora-restoration-plan.md#walkthrough-completion-dependencies-2026-10-22-after-12ceae72)
now targets **Earth saved and escaped**. The Icelord fight was an optional tested
detour on current evidence, not an established golden-path prerequisite. The
completion prefix omits it, preserves the sonicdriver for the required Ochre
trade and keeps Engineer ID for checkpoint use.

[Required-route evidence](../../runtime/observations/pandora-required-progression.json)
proves one uninterrupted cold boot to Lt Commander ID, guarded Commander access,
Commander ID and **Blue/Scarlet code cards**. Final frame2572: `(192,190)`, HP95,
Commander48 held; Engineer50/sonicdriver5 in carried0/1; Blue33/Scarlet35 in
pockets2/3. A linked post-run snapshot confirms self-destruct0, authorized count1/
seen2 and nonzero Earth deadline$9732. No injected state or optional fight.

Late Space release failure is preserved and diagnosed; an earlier original
body-entry release plus observed guest-release predicate lets inventory close.
The112-phase/66-event recipe uses bounded shared128/96 capacities and unique
repeated-action hooks. **165 tests passed**, no skips. Target source and the nine
paused B07 files remain unchanged; PR5 remains unmerged.

**Next required objective: Captain's SDI disk38.** Ochre trade, console arming,
AWOL authorization and the ending remain unfinished. A failed Robomechanic
model approach is an unresolved route question, not an unused/unreachable claim.
See [reproduction and limits](../copperline-runtime.md#required-ending-route-ids-blue-and-scarlet).

## Sonicdriver used to defeat Icelord (2026-10-22)

[Progression evidence](../../runtime/observations/pandora-icelord-progression.json)
records a complete **uninterrupted cold boot** through the prior item route,
new northern-area approach and Icelord fight. At **frame2444**, world gameplay
resumes at `(1298,206)`, HP70, sonicdriver `$05` held, Engineer `$32` retained in
carried slot0. Original combat initialization identifies the Icelord and applies
sonicdriver damage20. Five full hits and the defeated flag after normal cleanup
prove the objective. Opponent HP's final251 is signed BYTE underflow from15−20;
it is not mistaken for healing. Both combat-biased X coordinates are restored.

The existing driver supplied navigation, cursor, goal, guard and release actions.
19 model-suggested approach legs passed live; an observed initial-turn correction
seeded the model. A failed charge23 attempt was diagnosed from original even
increments and corrected to24. The full route uses64 phases/44 input events;
only the compiler's event cap was aligned with the runner's existing64. Focused
checks: **163 passed, no skips**. Qualification uses no checkpoint loads or
inside-run interventions; development replays remain clearly separate.

This is a genuine item-use/combat objective and new-area progression, not a
full walkthrough. No new watch campaign, source annotations, classified bytes,
state forcing or C/relocation work. Target source and the nine paused B07 files
remain unchanged; PR5 stays unmerged. This batch stops at the validated defeated
Icelord checkpoint. See [reproduction](../copperline-runtime.md#sonicdriver-defeats-icelord).

## State-aware player and new item progression (2026-10-22)

[Player evaluation](../../runtime/observations/pandora-player-evaluation.json)
qualifies two **continuous cold-boot** routes with identical action states and
frame/CCK input records, with no inside-run intervention. They reach terminal
entry, take the **Engineer `$32` card**, exercise its display update, retain it in
carried slot0, acquire **sonicdriver `$05`**, close inventory and return to the
world loop at **frame1226, `(640,734)`, HP95**. This is a new item checkpoint,
not a completed game or general security authorization. `$31` is Lt Commander;
the earlier development message misnaming `$32` is corrected before publication.

The known inventory/store/retrieve/deposit route also repeats identically.
A deliberately blocked east move ends at its30-frame budget with position
unchanged and input released. Reusable player actions now have explicit origin,
map, healthy-state and goal checks, finite visit/frame/wall bounds, and input
records; snapshot observers remain separate. Concrete development failures
exposed cursor braking, input-sampling phase and action-budget problems rather
than allowing silent route drift. The small composition now reuses those same
actions for card storage and tool acquisition.

**Useful within this route**, so it was used for that further progression.
It still needs reviewed waypoints/objectives and does not choose a full-game
strategy or recover from arbitrary combat. No retrospective agent-time speedup
is claimed; the evidence records actual runs and their wall times. Focused
runtime/session/player validation: **160 passed, no skips**. No new watch campaign,
source annotations or classified bytes; target bytes/source and the nine paused
B07 files remain unchanged. PR5 remains unmerged. See
[reproduction and limits](../copperline-runtime.md#state-aware-pandora-player).

## Watched terminal modal entry and nearby inventory (2026-10-22)

[Terminal evidence](../../runtime/observations/pandora-terminal-modal-memory-watch.json)
now establishes normal-input modal entry, beyond the earlier salvage deposit.
From the verified inventory root `(241,942)`, up 37/right 44/up 24/right 8/down 9,
then right reaches original `$8FF2` at frame 1148, player `(640,734)`, tile `$9C`.
The `$9074` service at 1151 and inspected private screenshot confirm the terminal
screen. Its map header changes from `$4000`,90×129 to `$18A20`,20×8; held/cache
ID remains `$36` Amy, HP 95. This does **not** establish card authorization.

**32 completed 120-frame-label CPU data windows**, covering entry/rendering and
nearby-inventory opening separately, watch all 14 gaps/750 bytes plus declared
`+$2D4`/`+$368`. No watched access or wall timeout occurred. Every endpoint
confirms the terminal header and expected UI state. Space opens nearby-object
inventory (`UI=$1C`, displayed IDs 5/50/0/0), explaining the retained failed
attempt that waited for the own-inventory branch. Normal direction exit reaches
`$9088`, restores the world header at `$90B0`, then returns to `$5D6`.

The failed southern route is diagnosed rather than retried: solid tile `$BA`
blocks `(458,950)`; a later detour contacts descriptor 18 at `(564,960)`, whose
exact-ID predicate requires Commander `$30`. A separate positive CPU watch
catches source `$801A` writing HP 95→85, with A1=`$58CD0`, while Amy `$36` is held.
Subsequent defeat/inhibition explains the later movement stop. This is a contact
checkpoint, not proof that every terminal requires Commander.

35 configuration variants validated; no shared-service or target source changes,
new semantic annotations or newly classified bytes. Existing exact source receipt
is retained without redundant regeneration. Nine paused B07 files are unchanged.
No-hit remains a non-pass bounded observation, never unused-memory proof. Watches
exclude approach, DMA and fetches; submission/authorization, other selections,
all aliases and full playthrough remain unproved. See
[reproduction and limits](../copperline-runtime.md#terminal-modal-entry-and-nearby-inventory-windows).

## Watched inventory and salvage deposit (2026-10-22)

[Interaction evidence](../../runtime/observations/pandora-app-interaction-memory-watch.json)
adds a validated normal-input route: own-inventory card store at frame 707,
retrieve at 725, approach `(150,950)` at 790, deposit commit/feedback at 793,
and return to the main loop at 795. Held/carried/deposit bytes confirm the
transfers of the initial `$36` card. The earlier reopen timeout is retained;
three main-loop visits after closing let the released key clear its latch.

Two verified checkpoints support **32 completed 120-frame-label CPU data
windows**: 14 gaps/750 bytes plus declared unresolved `+$2D4`/`+$368`, separately
for store and deposit. Every endpoint confirms its transfer; no watched access
was observed. These remain bounded non-pass observations, never unused-memory
proofs. The ordinary fresh route also verifies retrieval, but its open/close,
retrieve and approach work is outside the watch windows. No new source meaning
or classification is justified; target source remains unchanged.

This earlier milestone covers the salvage receptacle, **not terminal modal UI**. The nearest
identified modal terminal tiles are around `(672,976)`; one bounded approach
model returned unknown within 30,000 states; the later terminal milestone above
supersedes that approach limit with live normal-input entry. Other item/slot domains, growing
deposit prefixes, DMA and full-playthrough coverage remain open. Reproduction
uses the [existing checkpoint and session services](../copperline-runtime.md#inventory-and-salvage-deposit-interaction-windows).

## Earlier app-gap window and observed UI reader (2026-10-21)

[Earlier-window evidence](../../runtime/observations/pandora-app-early-memory-watch.json)
records completed frame-463→703 CPU data watches for all 14 gaps/750 bytes,
with no access observed in those windows. It also retains one partial wall
timeout (ending frame 583) and one boot-handoff failure; fresh retries completed.
Held-item snapshots change from zero to `$36` (`ITEM_ID_ID_AMY`), corroborating
handoff state without claiming a directly trapped handoff PC in these windows.

A targeted pre-overlay watch **did** observe `+$190`: source `$6130` reads WORD
`$0001` from physical `$3B8C` at frame 462. A second run reproduced the exact
stop event. Captured nearby-distance descriptor `(x=34,y=20,height=3)`, D7=4,
A4 at NULL `line_1`, and matching return frames identify the six-position text
loop's cursor setup: `(20+4+1)<<4 = $190`. The NULL test comes later. This closes
one original-UI reader/reachability question; it establishes neither a callback
role nor glyph/pixel access using that computed cursor, nor the pointer's intent.

The existing source comments/loop contracts remain accurate; no target source
or classification changed. Focused runtime/session checks: 148 tests passed.
No DMA, instruction-fetch, all-alias, manual-inventory or full-playthrough
coverage is claimed. Only `+$190` was watched before initial overlay drawing;
all other pre-overlay gaps and the declared-slot questions remain open.

## First app-gap memory-watch milestone (2026-10-21)

[Filtered runtime evidence](../../runtime/observations/pandora-app-memory-watch.json)
records 18 fresh original-payload runs: three startup controls and fifteen moving
runs covering all fourteen declaration gaps (750 bytes, watched individually).
The repeated boot/fire/card-transfer/19-down/21-right prefix has identical stop
events through watch arming at frame 798, player coordinates (388, 942, 0).

Startup read/write filters identify the existing `CLR.B (A0)+` at source $474,
including its zero write. No later CPU access was observed in the separate
three-second gap windows. These are **incomplete/timeout** observations, not
passes, unused-memory proofs or DMA coverage. The prefix before arming was not
watched. No semantic field claim or byte classification changes from this run.
See [reproduction and limits](../copperline-runtime.md#pandora-app-declaration-gap-watches).
The next evidence question is earlier proximity/text/card-transfer or inventory
activity; this first milestone does not claim a full playthrough.

## App-use static closure (2026-10-21)

The requested follow-up is complete within the available original-layout static
evidence. [Reproducible closure evidence](../validation/pandora-app-usage-closure.json)
resolves the ordinary base convention and identifies concrete alias consumers
and corrupting writers. It does **not** certify exhaustive runtime access,
unconditional dead storage, or a full semantic restoration. No further speculative
entry-path search is selected without the positive missing evidence below.

| Measured scope | Before / after and meaning |
| --- | --- |
| Complete accepted instruction check | All 7,059 retained instructions match original bytes and decode through the native Motorola-derived backend; zero decoder failures. No assembly-text parser supplies the conclusions. |
| A6 modifiers | Exactly 18: app bindings $48C/$8E8; hardware binding/arithmetic $4D978/$4D98E; fourteen reviewed restores. All MOVEM lists and EA updates are included. Only two accepted calls target the channel updater ($9D0/$FE2), both enclosed by matching A6 save/restore. IRQ entry resets A6 and all four exits restore the interrupted context. These are normal-return/valid-stack contracts, not hostile alias-safety proofs. |
| Prior 178 omitted A6 sites | Native CFG entry links covered 126. Joining 40 reviewed original-data edges covers 174: 166 scalar and eight indexed sites. Four retain an explicit missing-original-entry disposition; their field/formula meanings are not unknown. This does not mutate 178 native facts into unconditional proofs. |
| All A6 app candidates | 715 of 729 have original-entry links under the stated convention. The other 14 occupy five finite entry groups below. Twelve audio-hardware sites stay separate. Entry links are CFG possibilities, not observed gameplay. |
| Original target joins | All 35 object interaction/completion fields, five stored absolute calls in the reviewed 783-command corpus, eleven audio dispatch entries, and two explicit Copper callback transitions. Later pointer mutation and wider unchecked dispatch remain outside these initialized/stored contracts. |
| Cursor aliases | All 24 explicit app-address constructors are assigned to seven families. Bounds and unchecked variants are distinguished below. The 662 other register aliases are neither all app accesses nor proved non-app. |

The three named slots now have finite conclusions:

| Slot | Established use and aliases | Remaining semantic question |
| --- | --- | --- |
| `+$190` / physical $3B8C | Startup $4B6 writes one noop-function-pointer LONG. Both text-origin readers consume its high WORD for masked Y=25; the unchecked row helper consumes it for Y=200. | No independent pointer consumer/intent is established. The initial nearby-distance overlay now supplies one observed original UI caller (above). Its empty-position cursor lookup does not establish a callback role or intentional layout. |
| `+$2D4` / $3CD0 | $8366 mirrors the changed nearest-object pointer; $9FB2 clears it on restart. Unchecked row Y=362 reads its WORD. Carried/pocket transfer indices318/314 read and write it; displayed-ID index26 writes it. | Producer-defined shadow semantics are established. A dedicated pointer consumer and intentional retention purpose are not. It is not unconditionally write-only or dead. Keep the existing `app_02D4` symbol. |
| `+$368` / $3D64 | Startup zeroing and the raw IRQ callback read at $92E/$932 are established. Known CPU and original Copper policy leaves BLIT disabled. Row Y=436 reads the WORD; deposit scan overflow, inventory indices and submitted-name index15 can corrupt/write the slot. | No legitimate callback installer or original activation phase is established. Corrupt-state aliases are not evidence of a gameplay callback. Masking alone is not an all-entry unreachable proof. |

All 7,059 decoded absolute/immediate operands and canonical initialized pointer
seeds were checked for the three physical slot spans: no exact constant/seeded
pointer match. Direct A6 scalar overlaps are respectively one LONG store, two
LONG stores, and one LONG reader. These negative results exclude neither split/
computed addresses nor opaque/mutable data. Startup clear and the indexed/cursor
aliases are assessed separately; a missing named reader is never a no-reader proof.

| App-derived cursor family (origin count) | Consumer/range conclusion |
| --- | --- |
| Carried `+$196` (6), pocket `+$19A` (4) | Four-slot scans/copies are bounded. The selected transfer index is `(cursorY-139)>>3` as WORD; it has no independent four-slot test. Invalid rows2683/2651 target +$2D4; rows3867/3835 target +$368. Original four-row admission is a conditional contract. |
| Queue head `+$232` (4), limit `+$272` (4) | Sixteen LONG pointers, initialized tail and four-byte updates. Enqueue/pop sentinel touches extend through +$276. That inline range excludes the three questioned slots under valid tail protocol. Loaded text pointers are another mutable domain, not inline workspace cursors. |
| Displayed IDs `+$2BA` (2) | Four explicit name-list reads. The selected store shares the unchecked row-derived index: invalid rows347/1531 target +$2D4/+$368. |
| Deposited IDs `+$2DA` (2) | Reset clears exactly64 bytes; the zero scan is unbounded. A nonzero142-byte prefix reaches +$368. A lifetime deposit-count/zero-frontier bound is missing. |
| Submitted names `+$32C` (2) | Three declared LONGs and ordinary count progression0..3. Store count15 targets +$368; a display count of at least16 reads it. The instructions themselves do not bound corrupted counts. |

These are application contracts and alias witnesses, not a new generic pointer
analysis framework. Positive and negative original-routine tests model the stated
incoming registers/memory. They prove those source accesses under those inputs;
they do not promote modeled inputs into captured facts or normal gameplay.

The remaining entry inventory is finite and explicitly dispositioned:

| Entry question | App sites still conditional | Exact missing evidence |
| --- | --- | --- |
| $248A `update_active_world_object_tile_regions` | $248A/$2492, $6900/$6904/$690A, $6DBA/$6DBE/$6F22 (8) | No external accepted/native edge or reviewed original data target enters this background-restoration chain. An original computed/stack caller or retained execution entry would establish its actual caller context. |
| $2656 atomic Copper setter | $265C (1) | Actual caller/target producer. Existing original callback stores are direct and do not establish a caller of this helper. |
| $6DCA offset helper | $6DD6 (1) | Original caller or computed target. It has no accepted incoming call or reviewed initialized/stored target; its app input and unchecked formula remain conditional. |
| $4D34C proximity starter | $4D34C (1) | Original external caller/target. The known volume path calls initialization directly and does not establish use of this separate wrapper. |
| $4D4F2 sequence214 loop | $4D4F2/$4D4FA/$4D518 (3) | External entry/installed callback. Its internal back edge is not an external caller; none of the 35 original interaction fields selects it. |

The original 178 omissions contribute four of these sites: the three at
$6DBA/$6DBE/$6F22 and $6DD6. The other ten were already named native references;
this review does not mistake names for base proof. Searches cover the complete
accepted CFG (3,500 edges), native symbol/reference evidence, original canonical
object fields and reviewed stored script/audio target families. They cannot
settle unknown computed/external entries, opaque code/data, future record writes
or all runtime cursor values. No dead-code conclusion follows from these missing
entries, and arbitrary replacement-input safety is not an original-layout gate.

Validation: **53 unique tests pass**, including native register/list/update
positive and refusal cases, CFG edge limits, 19 original-routine alias cases
with valid-range controls, existing access-export tests and hardware-symbol
quality checks. No test skip is counted as a delivered result.

Four qualified source comments are recorded and accepted through MAL/DJ. Source
instructions, data, declarations, labels, SDK includes and existing symbols are
unchanged. C and independent vasm reproduce all376,832 bytes, receipt
`09beb8e8960b4082a3612057b9a4b6c7e3df4b4f34fbf2c190517f076adf5cbf`, source SHA
`2219a24b4c0d6346a08bc962cbe0b1d7efe16c02b07118f5a915374f1351045e`.
The first verify invocation was rejected by automatic approval review as an old
read-only-scope restriction; after checking the active changed-source annotations
and current authorization, the single scoped retry was approved and passed.

Two optional RSSET annotations encountered the existing128-region native limit.
Both were atomically undone through guarded MAL replay; four comments remain.
The one-at-a-time undo correctly could not repair130 to a still-invalid129;
the existing atomic two-undo API restored128. Histories are append-only. No cap
expansion, EQU/RS emission policy change, declaration-gap reduction or unknown-byte
classification credit is claimed. The earlier750 gap bytes remain a declaration
metric. The source-quality fixture's two silence-length expectations were updated
to the already published `AUDIO_PRIMARY_SILENCE_LENGTH_WORDS` spelling from
`a5be9edd`; the source was not changed to satisfy a stale `$20` literal expectation.

Reproduce from the retained identity-bound native evidence (no recollection or
source generation):

```sh
.venv/bin/python -m amiga_reversing.tools.pandora_app_usage_closure --output /tmp/app-closure.json
```

The command reproduces the static-analysis portion; `source_validation` records
the separate canonical exact receipt and accepted Decision Journal decisions.
The input graph and canonical metadata snapshot, decoder backend and auditor are
hash-bound in the report. New native register/EA facts use the same exporter as
the existing instruction query. No ROM, raw checkpoint, media or original opcode
payload is published. No new emulator capture, C port, relocation, font/bank45 or
B07 work was undertaken; all nine paused B07 files are preserved and PR #5 remains
unmerged.

## App-offset usage audit (2026-10-21)

The [baseline inventory at `61272d7a`](../validation/pandora-app-access-audit.json) and
[per-operand evidence](../validation/pandora-app-access-audit-sites.jsonl) enumerate
all **7,059 accepted native instructions / 3,649 explicit EA-shaped operand
sites** in one revision. EA sites include address computations, not just memory
reads/writes. This is a complete inventory of that accepted population, **not
exhaustive app usage or complete field semantics**. Opaque/unaccepted code,
indirect ranges and base provenance remain explicit limits.

| Current measure | Result and qualification |
| --- | --- |
| Native app attribution | 551 sites at 104 offsets: 182 read, 237 write, 118 read/write, 14 address uses. These categories are static native roles, not execution events. All 551 navigation references reconcile with the instruction inventory. |
| Additional A6 candidates | 178 sites omitted by native app attribution: 168 scalar uses at 24 offsets, plus ten indexed row-table sites. Conditional declaration joins assume A6=$39FC; they do not add base-flow proof or mean 178 unknown field meanings. Native form roles do not independently enumerate every RMW read side. |
| A6 audio hardware | 12 hardware-family writes, separated from app candidates. Each retains `_custom+16*channel`, channel set 0..3 and its required input contract; no concrete channel address is invented. |
| Concrete app-envelope references | Four address-only anchors at source $46A/$48C/$8E8 (workspace) and $A19C (grid). These are not four additional memory reads/writes. |
| Other register/record domains | 1,007 typed-record EA sites, 662 unresolved register aliases and 222 A7-based sites remain separate. A3 has 80 typed-record and 52 unresolved sites; A5 has 232 typed-record, 290 hardware and 51 unresolved sites. Register names alone do not establish ownership or disjointness. |
| Native conflicts | Twelve address-observation conflict records are retained outside the app-attributed/A6 population; none is silently promoted to app proof. |
| Declarations | 129 fields including six aliases; observed envelope `[0,$7F0)` = 2,032 bytes, declared union 1,282 bytes, 14 gaps / 750 bytes. This is neither allocation size nor a semantic completion percentage. |

The native app resolver can fall back to A6 when no value is known, and excludes
some hardware-register-shaped displacements. Thus both a rendered `app_*` name
and the absence of that name are inadequate base evidence. All 178 omitted A6
sites, formulas, widths and conditional joins are retained individually in the
report. No generated instruction text is parsed to obtain these counts.

Explicit A6 definitions at source `$48C` and IRQ `$8E8` bind `$39FC`. Audio
`$4D978/$4D98E` instead select `_custom+16*channel`; A3 audio-state-relative
accesses and object/UI record bases are separate domains. Push/pop pairs around
audio show intended preservation, not an all-caller saved-slot integrity proof.
These established context points do not propagate themselves through every call
and alias in this audit.

The ten indexed A6 sites have existing row-table contracts, not ten missing
field names. Every read/write below is conditional on the documented app base:

| Source sites | Existing index interpretation and bounds |
| --- | --- |
| `$9EC6` (write) | Producer emits 200 WORDs, 160*y, at offsets 0..398; range `[0,$190)`. |
| `$6112/$6130` (reads) | Text-origin helpers use byte displacement `16*(Y&31)`. The maximum read ends at offset 498; Y=25..31 reads beyond the 400-byte table. Masking is not clipping. |
| `$C80` (read) | Star projected Y plus 100 is doubled as WORD. The reader itself does not bound the index. |
| `$6DBA/$6DD6` (reads) | Back-buffer address and tile-offset helpers use signed WORD(2*Y), wrapped WORD arithmetic; no local bounds check. |
| `$7044/$7078/$70E6/$713E` (reads) | Geometry paths consume the post-clip/exchange Y through signed doubled-WORD indexing. Existing clipping/caller contracts are conditional, not a universal index/allocation proof. |

See the existing [framebuffer contracts](pandora.md) and
[indexed-consumer review](../validation/pandora-indexed-consumers.json); no new
runtime evidence or arbitrary-input guarantee is added here.

Cursor and physical aliases explain why declaration gaps or zero fixed-offset
matches do not mean unused storage:

- Startup at source `$46A` initializes A0 for the byte-clear loop over
  app `[0,$36C)`, including lower declaration gaps. The largest gap
  `$36C..$604` (664 bytes) is not thereby proved unused.
- Fourteen native app address uses form message-queue head/limit, displayed-ID,
  deposited-ID and submitted-name cursors. Another ten conditional A6 address
  uses form carried/pocket-ID cursors. Their later indirect accesses remain
  individually visible; the audit does not pretend each has closed provenance.
- The existing grid producer at `$A198..$A25C` writes fixed physical
  `$4000..$F568`, overlapping app `+$604..$7F0`. This covers the prefix and
  pointer 122's high WORD; its low WORD/BYTE supplies the established combat
  selector alias. It does not establish an app allocation extending to $F568.
- Six declarations have no fixed scalar match even after conditional joins:
  row-table prefix, queue-limit address, deposited-ID/name-pointer arrays, grid
  prefix and pointer-122 high WORD. Indexed/range/address use explains this
  result; zero matches is not an unused-field verdict.

Specific remaining questions are bounded and unchanged by enumeration:

- At source `$4B6`, startup stores a pointer at app `+$190` inside a declaration
  gap. The local base is established by `$48C`; a subsequent consumer remains
  unidentified. This is the only scalar candidate intersecting a declaration
  gap in the inventory (four bytes), before adding range/index contracts.
- `app_01AD` is a rendered byte alias inside the named frame-counter extent,
  not a new unnamed field. Actual generic LONG `app_02D4` has two listed writes
  (changed nearby-object pointer and initialization clear) and no listed reader;
  indirect consumption and lifetime remain unresolved. No rename is manufactured.
- App `+$368` has the interrupt callback reader and startup zeroing, but no
  established nonzero producer. Existing producer/continuation exceptions remain.
- Complete usage would require qualifying remaining base/cursor provenance and
  original index domains, including indirect writers/consumers and opaque code.
  The 662 unresolved aliases are not all app accesses, nor proven non-app uses.
  Absent static references do not prove unused data.

Reproduce a fresh native snapshot through the resident service, or reproject the
saved private evidence without another expensive analysis/paging pass:

```sh
.venv/bin/python -m amiga_reversing.tools.pandora_app_access_audit --output /tmp/app-audit.json
.venv/bin/python -m amiga_reversing.tools.pandora_app_access_audit --from-evidence --output /tmp/app-audit.json
```

Fresh pages are revision-bound and refuse previews, missing/nonadvancing pages,
changed identities or subjects. Saved instructions/navigation are identity-checked
under `.runtime-state/pandora-app-access-audit/`; raw instruction bytes stay there.
Published summary/site records carry the source, binary, backend, evidence and
auditor identities. `snapshot_only` explicitly labels reprojection of captured
facts rather than a new current-state read. The public site file is hash-bound
and contains no original instruction bytes or raw checkpoint/media payload.

One native analysis took about 307 seconds; the shared service's repeated
identity/history work made the full paginated collection take about 14 minutes.
This cost is recorded, not expanded into a general performance project. No source,
MAL or Decision Journal change was required. Source SHA remains
`15f28b305710b0c54affbd4b3eb6fa54744f67360b572812255e332959db7ee8`.
The service automatically ran its on-ready reproduction check and reported exact;
no explicit generation/export/verification or emulator capture was requested.
Focused audit/native-query tests: 22 pass. Existing restoration operations/read
snapshot/HTTP interface tests: 67 pass, one optional MCP SDK test skipped because
`mcp` is not installed. Initial network-sandbox socket setup errors were resolved
by the scoped local-HTTP test run. B07's nine files remain unchanged; PR #5 stays
unmerged. No unknown-byte reduction, C portability or relocation credit is claimed.

## Current closeout position (2026-10-21)

**Original-layout reviewed closeout with explicit unknowns** is complete.
The [final source-bound review](../validation/pandora-original-layout-closeout.json)
dispositions every old unknown interval and audits source/package/history
preservation. This is not full semantic restoration, alternate-layout safety or
a native C port. Canonical facts and histories remain authoritative; the report
is review evidence, not a new tracker or a new classification authority.

| Measure | Verified position and limit |
| --- | --- |
| Original-layout reconstruction | Done: all 376,832 bytes C/vasm exact in the latest [source-bound receipt](../validation/pandora-app-usage-closure.json). Disk/loader parity is outside this scope. |
| Code/data classification | Last full baseline: 24,308 code + 339,648 structured data + 1,690 table + 4,740 text + 6,446 unknown = 376,832. This partition is stale after the held-frame restoration; no fresh global unknown count is claimed. |
| Supported purpose | Latest union 283,380 / 376,832 bytes (75.2%), across 216 active assessments. This is bounded purpose accounting, not semantic completion; large graphics assets dominate the byte weight. The remaining 93,452 bytes lack purpose credit, which does not establish that they are all ununderstood. |
| Function/field understanding | Old snapshot: 273 function candidates, 973 resolved and 32 unresolved field-access records; candidates and access records are not complete function/field denominators. Current catalogue has 558 owners and 147 custom schemas; neither measures semantic completeness. |
| Readable source | Seven connected subsystem groups reviewed with explicit exceptions; final source-quality/preservation audit passes. Complete function/resource denominators remain unknown. The accepted label is original-layout reviewed closeout with explicit unknowns, not full semantic restoration. |
| Alternate layout / native C | Separate, unfinished deliverables. Original self-relocation, modeled calls and original-only DMA replay do not prove alternate-layout safety or a native C game port. No credible port percentage or overall ETA is available. |

All 32 old unknown intervals are dispositioned below: three intervals / 30 bytes
are already bounded by canonical table/frame facts; 29 intervals / 6,416 bytes
are retained as explicit unknowns. These are old-cohort review totals, **not a
fresh full-image native unknown count**. The opaque 27,792-byte uncopied tail
is a separate bounded exception. No source correction arose, so the existing
exact receipt is reused; no bookkeeping generation, test rerun or capture was
performed. B07 stays paused. Historical future-step recommendations below and
in Proposal 045 do not create a new task queue. This review stops here; only
new positive evidence listed in the final section would justify reopening an
exception. No overall semantic percentage or ETA is claimed.

The first reconciliation pass compared all 32 old unknown intervals with the
existing bounded data seeds. Only three intervals overlap such seeds:
`$8671..$8677` and `$8678..$867E` lie inside the two already-rendered seven-byte
weapon tables; `$4C376..$4C388` is the restored held-frame header. These 30 bytes
are existing facts, not new restoration credit or a freshly computed native
unknown total. The weapon-table native ownership discrepancy is retained as
a limitation of the stale full-image accounting.

The five non-dynamic field-gap records are also already interpreted in the
historical reviews below: `$1210`, `$132E`, `$1366` and `$139E` are LEA advances
by the ten-byte command extent; `$790A` is a WORD probe followed by a low-byte
comparison. They do not call for invented fields or larger structures. The 27
dynamic indexed records retain their bounded consumer/index obligations. This
is an accounting and evidence reconciliation, with no source or history edits.

> Current [subsystem source-contract review](#subsystem-source-contract-review-original-layout) consolidates the mature evidence.
> The historical checklist is not the current work queue. Seven subsystem groups
> have reviewed bounded contracts; remaining representation/producer/continuation
> exceptions are listed separately. This is not full semantic-restoration acceptance.

> Current indexed-consumer review: [27 records in seven groups](../validation/pandora-indexed-consumers.json).
> Reader formulas and bounded original domains were already understood; native
> indexed status is not 27 missing field meanings. Optional XY use still lacks
> an original nonzero producer. No new source contract was justified, so this
> reconciliation adds no source edit, generation, capture or classification credit.

> Current indirect-site review: [eight-site reconciliation](../validation/pandora-indirect-closeout.json).
> The old eight unresolved sites have finite per-site dispositions. Five stored
> absolute calls select four targets; no relative call occurs in the scoped 783
> commands. Initial interaction/completion targets already have contracts.
> This is original-layout reviewed closeout evidence, not full semantic restoration.

> Previous typed-data restoration: [primary audio control symbols](../validation/pandora-audio-control-symbols.json).
> Four control constants now name all opcode fields in 33 existing typed commands
> (41 BYTE fields across 22 programs).
> The original 29-program / 907-byte corpus and all 55 original list entries are
> audited; C/vasm exact. No new tests, captures or behavioural capability claim.

> Previous static restoration: [player held-frame header](../validation/pandora-player-held-frame.json).
> Corrected the player source-owner endpoint and exposed an 18-byte frame as two
> symbolic pointers and five geometry WORDs. C/vasm exact; 168 focused tests pass.
> B07 remains paused. The previous unknown-byte total has not been recomputed here.

> Previous static restoration: [combat-charge plane-byte layout](../validation/pandora-combat-charge-plane-layout.json)
> makes the 20 stored plane bytes and eight partial-cell masks explicit. C/vasm
> reproduced all 376,832 original bytes; its unknown count was 6,446. B07 and generic
> capability work are paused; the behavioural figures below are the earlier milestone.

> Current behavioural validation: [B01–B10 roadmap](../proposals/045-behavioural-validation.md),
> [natural H30/S13 evidence](../validation/pandora-behavioural-validation-natural-boundary.json).
> Five bounded predicates in three summaries: 25 CPU cases plus 65,536 BYTE inputs;
> three original-only DMA fixtures. Tests: 269 Python passed, one optional live MCP
> SDK transport skip. That batch left assembly unchanged and C/vasm exact; prior 30 native tests
> are historical, not rerun. Every B ID remains partial/open.

The [comparison identity correction](../validation/pandora-behavioural-validation-identities.json)
records reproduced false passes and fail-closed regressions. Candidate helper
bytes, current native proof, manifest/plan profile identity, executed backend and
loaded Python implementations are now checked. The focused suite passes 208
tests with one optional MCP SDK transport skip. This hardening adds no contracts,
CPU paths or DMA fixtures; prior receipt profiles are historical, not reusable
under the changed checker profile. The source and its exact-byte accounting are
unchanged.

The warm-start predicate admits six modeled alive-near/unarmed calls using a
private captured donor and a 256-instruction limit. It checks four channel
records' ordered initialization writes. The legacy predicate retains its
128-instruction limit and exclusions. Neither the captured CIAA debug snapshot
nor local CPU calls establish device behaviour or normal-gameplay reachability;
cold sample setup and later channel/program consumers remain excluded.

The second buffer fixture checks five configured blit jobs/1,280 observed events,
including256 mask, pixel and background reads each and128 FIFO scratch-to-bitmap
pairs. Its full5,120-event window also includes later blits and display reads;
not every event is attributed to the renderer. Bounded full-sidecar projections
recover evidence beyond the original report's337 omitted matches. Native and
profile-container frame labels remain separate. H32/shift4 is unchanged; final
pixels, global outside-ROI bounds, other callers and candidate DMA remain unproved.

The fixture-race regression reproduces a false pass after a reviewed capture was
swapped before consumption. The runner now hashes/parses one byte snapshot and
binds its consumed identity to the reviewed hash; the service checks the returned
identity too. The recorded82f1795e warm run consumed the reviewed hash, so no
published-run substitution is evidenced. Fresh qualification uses the hardened
profile; the older profiles remain historical.


The natural H30/shift13 fixture reaches runtime `$16A1E` from caller return
`$1715C`. Four configured jobs account for 960 DMA events within a 4,480-event
ordered replay window. It checks WORD control fields `$DFCA/$D000/$0782` and
per-channel address/width/order across a distinct height/shift setup. It does
not independently recompute masked pixels, establish clipping from H32, or prove
candidate equivalence, global clobbers or alias/lifetime safety. The consumed
manifest identity guard also closes an admission/consumption race; no published
substitution is evidenced. The then-proposed B07 replay/reduction, DMA value
oracle and interference sequence is now paused; the current closeout list above
supersedes that historical next-step recommendation.

Baseline snapshot: 2026-10-12, merged source `22e55bb5`, restoration revision
`2f142cd09c5eae6d1edd001af3acfb2909098713d6a8f513eadda5c7279ba42e`.
All offsets here are section 0 source offsets, with exclusive range ends, unless
explicitly called runtime addresses. This report indexes native facts and
canonical history; it does not replace them. See the [full plan](pandora-restoration-plan.md).

## Callback register and carry contracts

All thirteen distinct initialized interaction targets and four completion targets
preserve A5 on normal returns. Seventeen direct callable summaries record the
complete sixteen-register partition; memory and escape effects remain unknown.
The proof follows the original instructions and transitive helpers, including
the audio and font MOVEM saves and the item-adjustment object's saved A5.
Completion at source `0x93F4` has no caller save, unlike `0x7A00`; the known
callee contracts explain that bounded preservation requirement.

Interaction carry set requests the nonzero object message at `+$10`; clear
skips that dispatcher enqueue. It is not a general success result. The common
tail sets the WORD cooldown to 250. The musician can set carry without that
cooldown, while audio callbacks and the diabetic treatment path can change
state or enqueue messages and return carry clear. Sixteen source comments make
the individual conditions and caller behavior visible.

The original 35 objects' current and initial script pointers agree. All 783
original commands were checked; the 130 relative writes target repeat counters
and do not overlap callback slots. This snapshot does not close transitive
alias writes, arbitrary returned script pointers, future replacement, or the
callback target set for every gameplay phase. No unconditional type seed was
added after the indirect interaction call.

The normal summary command now preserves validated optional effects, results
and notes. Native reading of those four arrays accepts ordinary JSON indentation;
the existing schema and C ABI are unchanged. The framework/runtime checks pass
119 focused tests, including five JSON formats and final nonobject rejection.

The earlier Copperline probe released title fire but supplied no gameplay
movement. Its timeout PC `0x6F6E` is a geometry-rendering prologue, not an input
wait. Interaction is automatic proximity/cooldown dispatch. Starting movement
before the officer transfers a card would trigger the ID-card failure path.

Two fresh Copperline boots reproduce the nearby-interaction scenario. It waits
for card store `0x4B13C`,
observes selected card ID 54 and an undefeated player, then counts completed
movement at `0x9844`. Nineteen downward and twenty rightward moves take the
player from `(241,866)` through `(241,942)` to `(381,942)`. Static tile checks
derive this order; it avoids the lateral drift of turning downward after moving
horizontally. The observed nearest diabetic is at `(384,1026)`, distance 87.

The call at source `0x83FE` targets `interact_with_diabetic` at runtime
`0x5D568`. At return `0x8400`, A5 remains `0x5B728`; SR changes from `0x2000`
to `0x2008`, leaving carry clear. The selected card is not insulin, so this
follows the ordinary carry-clear return. The optional message pointer and
cooldown remain unchanged across that call. Each checkpoint validates original
payload identity and the canonical copied-view mapping. This validates one
normal-return path, not treatment, queue acceptance, all seventeen callbacks,
future target replacement or alternate-layout execution.
The checked-in [scenario](../../runtime/scenarios/pandora-nearby-interaction-callback.json)
and [compact observations](../../runtime/observations/pandora-nearby-interaction-callback.json)
retain the inputs, identities and measured state without large trace logs.
The seventeen new occurrence/runtime regressions bring the focused suite to
136 passing tests. Assembly and canonical histories are unchanged by this
runtime validation.

Whole-image C and independent vasm verification matches all 376,832 original
bytes, receipt
`0ae4dda5723549d0622415b96214d0700fbcb1b9113196f022c8c8cb3353626d`;
source SHA256
`30a68b6aae2fb74bf649b9bec2b9e2467a60041aa91af4af5d3cfc29b56d0d53`.
Independent source review confirms exactly sixteen comment additions with no
instruction or data changes. All 439 layouts, 33 types, 43 old summaries,
20 entry seeds, 98 old comments, 68 assets, nine SDK includes and both history
prefixes are preserved. The canonical Decision Journal accepts all 33 new facts.

## Rooted NPC animation families

The reviewed family describes 7,742 original bytes in 33 named ranges:
235 geometry headers, 57 render-state prefixes, 37 animation nodes, 34 frame
sequences and 28 position descriptors. Existing initialized object pointers and
typed behavior commands root these records. The 166 element groups reuse the
existing shared types; all 406 older layouts and 33 types are preserved.
Initial node modes are zero or four, and the new state prefixes have their
conditional-tail bit clear. These initial contents do not establish arbitrary
mutation, sequence replacement or lifetime behavior. The unproved 18-byte gap
at `0x49B86..0x49B98`, numeric generated-mask RAM addresses and NULLs remain explicit.

The complete candidate exceeded the old 8,192-label policy limit before any
target append. Checked owned policy storage now accepts 16,384 labels and data
items; the actual pending native projection uses 9,686 labels and 9,495 data
items. The authoritative analysis arena remains unbounded. Nineteen focused
Python/API tests and eight native storage tests pass, including deep cloning,
overflow refusal, duplicate handling and atomic history preservation. Rebuilding
the backend leaves the preceding target source unchanged and exactly reproduces
all 376,832 bytes through C and vasm.

Independent review reconstructs every new range's bytes and checks its expanded
typed fields, original pointer graph, exact history prefixes and unchanged 68
assets plus nine SDK files. The canonical Decision Journal accepts all 199 new
facts. Final C and vasm receipt:
`4563fbeb6523814d0354466493b7361535293de22765f32e064c3e413d778cbf`;
source SHA256:
`2a526875c7ebce6304747eabdd434cd473d1d7508e001eb4da934fe76d0ec578`.

Source review caught one new pointer field losing its annotation when an
interior render boundary split it into two raw rows. The native fallback now
retains the field name on its first fragment with an explicit partial width,
preserving every boundary and byte. The actual source gains exactly four such
annotations, including three existing fields; no symbols or declarations change
in this renderer correction. Three deterministic native boundary regressions
pass with exact six-byte reassembly, including conservative untyped/conflicted
cases. All 78 source-package/publication/field-encoding tests pass. The broader
native IR suite has 642 passing tests and the same previously documented
pointer-table-pointee propagation failure; no new failure was observed.

The retained BK stream's header, producer bounds and checksum establish that the
uncopied tail belongs to the historical decoded payload. Its initial-content
consumer and purpose remain unproved; the repeated pattern is not classified
as padding, unused storage or a resource. Callback A5 preservation and callback
slot writer coverage also remain separate open questions. No runtime or
alternate-layout execution claim follows from this static data-family work.

## Complete byte accounting, incomplete semantic recovery

The [coverage map](pandora-coverage-baseline.tsv) contains 281 disjoint intervals
covering `[0, 376832)` (`0x5C000`) exactly. It was derived from native
`M68kSectionAnalysisIR.range_ownerships`, with residual spans explicitly unclaimed.
It records 47 merged code intervals, 119 accepted-noncode intervals and 115
unclaimed intervals. A complete partition is not a claim of complete analysis.

| Baseline native classification | Union bytes | Payload share |
| --- | ---: | ---: |
| Accepted code | 24,394 | 6.47% |
| Accepted noncode | 13,619 | 3.61% |
| No native ownership record | 338,819 | 89.91% |

There are 368 bytes with multiple accepted ownership claims, retained as overlap
flags; none is a code/noncode overlap. Raw byte preservation already works for
unclaimed spans. Their purpose, boundaries and consumers are not thereby known.
The largest unclaimed spans are `0xB4A8..0x3D310` (204,392 bytes),
`0x3E3FA..0x486BA` (41,664), `0x55370..0x5C000` (27,792) and
`0x4E94E..0x552DE` (27,024). These are not automatically valid asset extents.

Other baseline counts: 7,087 instructions; 448 accepted code runs; 2,070 CFG
blocks; 230 function candidates; 3,364 edges, including 64 unresolved transfers
(51 calls, 13 jumps); 48 table descriptors; 390 resolved and 21 unresolved typed
accesses. Existing manual state includes 234 labels, 95 seeds, 16 structures,
67 data layouts, 44 app/RSSET regions and 18 callable contracts. Before the new
startup batch, no manual comments existed and all 18 contracts left their effects
unknown. Legacy names are evidence to audit, not automatic semantic proof.

## Constraints established by the startup audit

The direct contract loads at runtime `0x20000`. Source `0x00..0x27` discovers
its current base and copies a 42-byte helper (`0x28..0x52`) to runtime `0x300`.
The helper copies `0x55370` bytes to fixed runtime base `0x10000`, choosing a
forward/backward byte loop to avoid overlap, then jumps to `0x1046A`.
The remaining 27,792-byte file tail is nonzero and its role is unresolved.

The fixed continuation installs a handler at vector `0x6C`, uses custom-chip
base `0xDFF000`, fixed application state and framebuffer addresses `0x70000`
and `0x78000`. These require distinct address classes: internal relocatable
pointers, fixed platform addresses and target-owned placement constraints.
PC-relative access to the star dispatch table does not make its longword entries
relative. Audio also has a distinct word-offset-plus-base dispatch idiom.

Five native runtime views include the input overlay, the materialized main copy,
the low-memory stub and competing off-by-one views. They are not five proven
execution copies. Of 943 address observations, 53 are recognized writes and 25
are runtime-range writes. None of those 25 intersects accepted code; indirect
writes, unaccepted code and conflicting views prevent concluding no gameplay
self-modification. Startup copying executable bytes is already established.

## Correctness findings to resolve

- **CFG address domain:** source `0x9C2A` contains absolute JSR `0x107F0`.
  Existing native runtime-reference facts identify source `0x7F0`, but the CFG
  used `0x107F0` as a source offset in the baseline. The reviewed generic
  resolver now consumes native runtime-reference identity, with conservative
  ambiguity handling. Synthetic runtime-base and Hunk tests pass; the current
  Pandora service confirms source `0x9C2A` calls source `0x7F0`. No fixed subtraction belongs in the framework.
- **33 misplaced legacy labels, corrected in the handler batch:** opcode table `0x1432..0x14B6` contains runtime
  handler pointers, but their labels were recorded as source-domain addresses.
  Example: `world_object_command_set_position` was placed at source `0x11114`;
  the accepted handler at `0x1114` writes A4+2/A4+4 into the object's world_x/y,
  advances A4 by 6 and returns. Each handler needs semantic corroboration before
  corrective actions; the reviewed handler batch now preserves the old records
  and appends 33 removals, 33 corrected labels and 34 comments.
- **Overlay extent:** initialization clears 128 bytes, the accepted queue layout
  covers 64, and processing scans 16 pointers. Adjacent ownership must be resolved
  before expanding a structure or claiming scheduling behavior.
- **History gap:** a pre-existing sequence jump from expected 940 to 943 remains
  visible. Do not renumber or rewrite historical bytes to conceal it.

## Derived subsystem ledger

Historical source checkpoint (2026-10-14): scratch capacity and resolved caller family.
Proximity rendering reaches the active descriptor/attachment loop, the geometry
clipper, and the two edge helpers. The 318 typed original headers plus two
producer-selected 18-byte headers give a 320-header contract: heights 7..48,
row strides 1/2/4, and horizontal storage bounds. With unchanged headers and a
nonwrapping 320×128 view, retained height never exceeds the original height.
The native CPU replay checks 57,564 caller cases (29,020 scratch calls) and 294
helper-register cases against original bytes with abstract completed MMIO;
it executes CPU/control arithmetic, not DMA bus operations or timing.

Four two-WORD planes produce 16-byte scratch rows, requiring at most 768 bytes
at runtime `$1B3A8..$1B6A8` under that contract. A shared row type, bound constants
and render-phase capacity view record this envelope. The source cursor owner
stays 256 bytes; later rows can retain prior contents, and the remaining initial
backing bytes retain their unknown file meaning. Capacity/backing is established;
exclusive allocation, aliases and arbitrary replacement headers are not.

All 320 logical pixel/mask pairs correspond to the 59 existing producer banks
and fit their nominal spans. Two-WORD edge reads can reach a neighbouring WORD;
46 worst-case header envelopes exceed their producer-bank endpoint by two bytes.
The second-word helper can also read the background WORD before the destination.
The final selected scratch WORDs stay inside the staged span. These are programmed
access envelopes and conditional edge cases, not observed DMA fetches or proof
that neighbouring resources belong to the same frame.

Both helpers wait/ack before staging and final reads, then may return with the
final read still active. Known ordinary IRQ paths use CPU/audio operations;
warm restart waits for blitter busy before title CPU reuse. Later callback
replacements and trade fall-through aliases remain open. Prior boot observations
still distinguish cursor payload survival from source/table and loaded-tail reuse;
original uncopied file-tail purpose remains unproved.

Two new headers reuse the shared geometry schema without extending interaction
tails. All 443 old layouts, 35 old types, 273 references, 69 assets and nine SDK
includes are preserved. Thirteen normal catalog actions were reviewed and
journal-accepted against these proofs; 210 focused tests pass. The native pointer report now contains
2,609 fields: 2,022 symbolic, 584 NULL and the same three boundary fragments.
Expanded C/vasm receipt `140c4c154d25dbcc3151f93c45d594df691eceef1bf6ff471a3fb32b65d4e4c6`;
source SHA256 `b5c29658451d7a775aadc1cd574dcee25528bbe477362372b0fb47abfd1b913d`.
Actual compact ZIP also reproduces all 376,832 original bytes with C/vasm:
27 definitions, 1,501 compact records and 768 expanded fallbacks; compact source
SHA256 `c2aa0d456821d21a0cff268bd212010b9494bb1ea78eab01976fe7f7c37cb8f7`.
Machine evidence: `.runtime-state/pandora-analysis/scratch-bounds-followup/`.

Audio-volume relocation checkpoint (2026-10-15): **changed layout executes;
game-writer coverage remains incomplete**. The two-byte `audio_master_volume`
(source `$4DD00`, original runtime `$5DD00`, initial `$0040`) now has a native
five-entry fixed-width rewrite ledger targeting `$65400`. Both PC-displacement
reads retain their forms; the three absolute writes retain their WORD/WORD/BYTE
widths, including the high-byte writer. The logical two bytes use an eight-byte
lease. Accepted-reference closure does not prove all aliases or future resources.

The bootstrap ownership bug is fixed generally: marker storage, full loaded input
and declared destinations are reserved before CMD_READ, merging contained leases.
No allocator call can insert free-list metadata into loaded input afterward.
Initialization waits until native copied-game entry `$1046A`, after full input
and full `$55370`-byte copied-image verification, then writes/reads back exactly
`0040` and anchors reverse history. Consumed-input lifetime is an explicit
payload-bound contract; no integrity check was weakened. Native persistent owners,
runtime-equate extents and materialized views exclude conflicting placements.
Two normal reviewed facts record the volume and constructor-owned tilemap grid
`$4000..$F568`; keyboard work remains deferred.

The initial eight-phase comparison established both reads at `$65400`, with
matching note/envelope Paula outputs 64 and 64→48. A subsequent normal joystick
scenario now reaches **both WORD game writers in both layouts**: 21 canonical
phase hits after verified handoff, 231 accepted movement commits, inside position
`(752,314)` (distance 234), then outside `(724,314)` (distance 262). The D0 writer
at source `$55368` changes volume `0004→0006`; the immediate WORD reset at
`$5533C` changes `0001→0040`. The sampled note scales envelope 24 at volume 6 to
AUD3VOL=2. Relevant Paula values match, and the old `$5DD00` guard remains `0040`
throughout the relocated route. The derived full payload remains
`dc173a673cd8d939267952b9c15507529dec92e3f3d5f3597d57489635f0cfd1`.
The [normal-input scenario](../../runtime/scenarios/pandora-volume-proximity-writers.json)
and [compact observations](../../runtime/observations/pandora-volume-proximity-writers.json)
record full identities, initialization, writer values, output and remaining limits.

The **BYTE high-lane writer at `$552F0` remains unexercised**. The longer
[normal-input combat probe](../../runtime/scenarios/pandora-volume-feed-combat-probe.json)
reaches the Megabio Feed, opens inventory with `key 64` (Space), selects an empty
carried slot, then delivers six charged fire presses. Both layouts hit all 46
canonical phases. Each attack at charge 24 subtracts five from the low health byte:
`1D→18→13→0E→09→04→FF`; the game's signed-negative branch marks the Feed defeated
(flags `$66`). Player health ends at 80, with original/relocated game state and
relevant Paula captures matching. No guest state was forced.

This explains the remaining guard: combat's temporary world-X bias clears shared
audio flag bit 0 and restores volume `0040`; after defeat that flag remains clear.
The BYTE writer requires the defeated flag **and** shared audio bit 0 set, so its
entry guard bypasses the write in the sampled post-defeat state. This excludes
that observed transition, **not every normal gameplay path**. Bounded whole-program
queries find 13 named shared-flag accesses: initialization, the alive proximity
setter, the dead/far clears, a second setter at `$4D34C`, and unrelated-bit uses.
The second setter has no accepted incoming references/CFG edges; incomplete facts
and aliases still preclude a universal unreachability claim.

A direct weapon kill is a viable **static alternative**: main-loop source `$5F0`
processes the weapon ray before proximity audio at `$624`. One rifle hit deals 30
against the Feed's initial 29 HP. The callback and feedback path do not clear the
shared flag at A6+`$33D`: feedback uses the distinct byte at A6+`$33E`. Source
`$93FA` can mark the Feed defeated without the combat coordinate bias, leaving the
BYTE guard's two bits set in the same frame. Required predicates remain explicit:
normal rifle acquisition, selected item/ammo/fire edge, valid aim/live geometry,
unblocked ray and no earlier nearby encounter. The BYTE writer and its relocated
comparison remain unobserved; the successful WORD evidence is unchanged.

**Compact world model (2026-10-15).**
[`pandora_world_model`](../../amiga_reversing/tools/pandora_world_model.py) now
consumes native symbols, effective record schemas, original bytes and verified
checkpoints. It is a read-only, target-specific planning aid, not a second native
fact store or a full game-playing engine. [Model output](../../runtime/observations/pandora-world-model.json)
and [checkpoint input](../../runtime/observations/pandora-world-model-checkpoint.json)
make its assumptions inspectable.

| Model component | Established input / validation | Remaining boundary |
|---|---|---|
| Terrain | 43×30 selectors choose 3×3 records: 90×129 tiles, 16 pixels each; 512-bit collision table; six captured cells exactly match | Dynamic changes elsewhere are not inferred safe |
| Movement | X=7, Y=4, axis-only, direction-dependent lateral drift and native edge/feet probes; 30 original directional frame entries / 17 unique bounds | Camera/UI/inhibit/event state must also permit a step |
| Object event | Player `(808,794)`, pianist `(816,808)`, flags `$24`, selected item 9, matching nearest/interaction pointers | Other actors' live state and unresolved trade predicates remain unknown |
| Encounter transition | Model predicts combat inside strict 24×16 bounds; next checkpoint confirms UI `$02`, player `(10808,794)` and movement rejection | This is the cause of the upper-route stall, not a demonstrated collision wall |
| Pianist patrol | Original script and native opcode values yield X=816, Y=728…974; reload N executes N+1 moves; live script matches the admitted original cycle | A swept patrol envelope is conservative; delays are not a timing prediction |
| BYTE dependencies | Empty-slot rifle pickup `(1244,867)` → arm audio alive → direct weapon kill → both guard bits | No rifle pickup, weapon hit or BYTE write has yet been observed |

The previous terrain-only A* routes omitted the earlier nearby-combat transition.
Their counted-PC timeout captures were the **last successful movement**, not the
state at timeout. A focused capture identified the UI early exit; A3 had not yet
been bound to geometry and was not interpreted as a frame header. Expanding all
poses did not fix the missing event predicate. The first south-route stall's
cause remains unclassified.

The model now rejects the full rifle route when the pianist's entire patrol
keepout is enforced. It instead derives a conditional staging plan: **up 18, right
77, stop `(780,794)`**, one accepted-X-step margin west of that envelope, with
checks no more than eight accepted moves apart. This staging plan is not a new
runtime qualification. Before crossing, establish a short-horizon patrol/interaction
predicate from the actor's live script/countdown and position. Unknowns stop the
plan; another guessed route is not justified.

The framework already supplies native data/field/CFG queries, canonical runtime
views, read-only captures and bounded source-PC/input phases. The remaining general
runner improvement is a bounded alternative canonical stop/outcome (for example,
combat entry `$7792` during a movement phase) with state capture and immediate
input cleanup, followed by explicit predicted-state checks. Alternative stop outcomes remain proposed. Exact/masked captured-memory checks
are now implemented and stop subsequent phases on a mismatch. Revision-bound reuse of native compilation/PC
resolution can reduce minute-scale probe overhead; source/manifest checks must
remain. The generated CPU simulator can check focused instruction semantics but
is not a world/AI simulator. No large architecture or autonomous playing engine
is needed for this scenario.

[Reproduction and limits](../copperline-runtime.md) and the
[BYTE/efficiency assessment](../../runtime/observations/pandora-volume-byte-reachability.json)
retain the counterexamples. Seventeen focused model tests pass, including the
actual pianist script's N+1 range, encounter boundaries and the recorded
combat/movement transition. Existing runtime/native suites were not repeated.
Original binary/source hashes and prior WORD observations remain unchanged;
there are no new target facts, generated-source edits or forced guest states.

**Timing checkpoint after `6dc51ee0`.** The read-only patrol model now counts
eligible object-loop calls, including delay-on-zero dispatch and six mutable
script counters. Five consecutive live loop observations match exactly. It
rejects an immediate crossing, waits for the start of the pianist's 30-call rest
at Y=974, and checks all admitted camera-pause timings for a 28-move corridor
route. All 28 predicted player coordinates passed in original Copperline, ending
`(864,738)` with UI clear; captured patrol states match 49 eligible calls.

The public scenario checks exact/masked memory after canonical identity at every
visit and releases input on mismatch. Requested-PC absence still uses a short
phase deadline; alternative stop PCs are not implemented. This closes the
pianist crossing gap, not the weapon/BYTE goal. The flight-controller patrol at
X=1104 is the next actor gate. Three captures validate two consecutive updates
with the same interpreter; the player remains `(864,738)`. A 35-record snapshot
also locates the security officer `(1234,840)` near pickup. These observations do
not yet compose a safe weapon-acquisition route or its empty-slot/fresh-latch
predicates. The return/aim/ray path and original/relocated BYTE comparison remain
unobserved. The next staging candidate `(1074,738)` is unexecuted.

Focused timing/model/runtime/session tests: **112 passed**. The original
binary/source and previous WORD receipt remain unchanged; no native facts or
generated source were edited. See [timing and crossing reproduction](../copperline-runtime.md#pianist-timing-and-guarded-crossing).

**Normal rifle pickup checkpoint.** Verified local save/resume now binds snapshots
to payload, media, ROM, emulator/profile, layout manifest and canonical stopped
state. One fresh corridor root is followed by four independently owned movement/inventory
segments and an idle audit; root handoff/copy verification is explicitly inherited. All phase and
position assertions pass. The flight-controller crossing is qualified in the
forward direction, then normal inventory selection and pickup equip rifle 18 at
`(1228,874)` with HP 95, ammo `05,01` and the card stored in carried inventory.
Snapshots remain local; layout bindings prohibit sharing an original checkpoint
with a relocated run.

The [rifle receipt](../../runtime/observations/pandora-rifle-composition.json)
records the six-snapshot chain and remaining model boundary. A 382-move terrain
return candidate crosses both patrols in reverse. No patrol-cycle gate satisfies
the conservative timing windows for its 45-move reverse flight corridor, so the
return was not executed. Tighter cumulative camera-pause timing is the next
specific model requirement. A read-only capture verifies the live Feed body and correct map base `$4000`;
the first `$8880` assumption stopped at its guard. The revised candidate
`(808,154)` aims east and starts its ray inside the captured body on a clear tile.
Future live membership/geometry and normal arming/hit predicates remain
unobserved. BYTE execution and original/relocated comparison
are still outstanding; two-of-three writer coverage is unchanged.

Focused suite: **134 passed**. Original bytes/source and previous WORD evidence
are unchanged. No game predicate was edited. See [checkpoint reproduction and
limits](../copperline-runtime.md#verified-checkpoints-and-normal-rifle-pickup).

The canonical PC identity sampler now keeps its minimum 16-byte sample inside a
copied view near its end (the final RTS is at `$6536E`, view end `$65370`), including
preceding bytes and translating back to the exact source PC. Full HAND/copy hashes
and exact offset/base checks remain required. Compiler phase capacity is bounded
to 64 including handoff (at most 63 executable phases), within the runner's existing
64-executable-phase cap; this permits the longer diagnostic scene. 69 focused
runtime/session tests pass; control/symbol tests add 27 passes and two skips.
Independent read-only review found no correctness blocker. Original source/binary
hashes were rechecked unchanged, so the exact receipt below is reused without
repeating the unchanged native suite. Current bounded receipts are under
`.runtime-state/pandora-analysis/volume-writers/`.

361 focused tests pass; the full native suite retains the same two baseline
failures. Independent code review and the reproduced PC-displacement regression
pass. Both histories preserve their prefixes and append two reviewed facts.
Original source, binary and all source-package file hashes remain unchanged;
only package metadata identity changes. Final full C/vasm exact receipt:
`90d1ec6e769375d7f66424d92a4a154e8cf2fe4dbb6e9e7749a04f29b49a2e30`.
Bounded local receipts and preserved earlier archives:
`.runtime-state/pandora-analysis/volume-relocation/`.

Keyboard relocation checkpoint (2026-10-14): **incomplete**. One normal
interpretation/review records `keyboard_state` at original runtime
`$397C..$39FC` (128 bytes), with stable identity, alignment, persistent CPU
storage and no DMA requirement. Native region queries, revision-checked
placement/build operations and an exact derived-payload identity contract now
share the existing facts/history/service; no target-only patcher or second
semantic store was added.

The proposed `$C7F000..$C7F080` Slow RAM move is refused with five open roots.
First failures are source `$690` at `$6AE` (A6 camera-state write), `$86A` at
`$882` (A6 last-key write), `$2D2A` at `$2D58` (borrowed caller frame), `$9062`
at `$90BE` (A6 modal-state write), and `$9C76` at `$9C32` (A6 status write).
The direct `$2704` access and `$9F58` reset cursor bounds close, but are
insufficient to build. Other-base writes are not yet proved disjoint from live
return/saved-pointer frames, and caller prefixes need balanced-frame analysis.
Independent review approved conservative refusal after arithmetic, MOVEM span,
stack/callback/tail, mutable-index and CPU/EA guards. No derived Pandora artifact,
reservation or changed-layout execution has been observed.

A fresh normal Copperline boot verifies the complete original payload and hits
all eight keyboard phases. Reset clears all 128 bytes; raw keys 11/12 each set
only their own byte, release clears it, and normal gameplay camera-profile reads
change 1→0→1. Region-identity captures and independent original-address reads are
in `runtime/scenarios/pandora-keyboard-state.json`. The current Chromium UI shows
120 listing rows, the real region facts and five-obligation placement refusal.
The loopback service remains `http://127.0.0.1:8123/`.

141 focused tests pass, with two optional tests skipped. The full native suite
has the same two failures on clean prior commit `7896c865`: pointer-table pointee
type propagation and unknown decompression identification. Original expanded
C/vasm verification is exact for all 376,832 bytes, receipt
`75f1ea4bcebee3bb8c1e712c0fe172e4cefa02ca3dbf1c028f9e6a4ded877418`;
source SHA remains `b5c29658451d7a775aadc1cd574dcee25528bbe477362372b0fb47abfd1b913d`.
Actual compact ZIP also reproduces every original byte through C/vasm; its
source SHA is `974bd68621c39c2a94a9bc457cd5bd6e5bb74ecab0e3d2c964b7beb6e20b306c`
with 27 definitions, 1,501 records and 768 explicit fallbacks. All prior effective
facts, 78 companions, 69 original asset spans and both history prefixes are preserved. Machine evidence is under
`.runtime-state/pandora-analysis/keyboard-relocation/`; reproduction and the
first raw fixed-width runtime contract are in `docs/copperline-runtime.md`.

The approved continuation adds a native bounded frame-prefix interpreter. Balanced
MOVE/MOVEM saves, direct calls and affine SP effects now support ordinary borrowed
caller contexts; return-slot corruption, SP escape/replacement and ambiguous joins
refuse. Queries expose relative effects with `absolute_sp: null`. CALL/RTS spans
come from generated CPU stack effects. A discovered simulator gap is fixed through
the existing KB `source_sign_extend` property: ADDA/SUBA WORD sources sign-extend
in abstract/concrete simulation, and section-pointer arithmetic wraps without
signed-overflow undefined behavior. Linux test executables now carry their shared
backend into their isolated directory.

181 focused checks pass, including independent vasm encodings, actual Copperline
execution of nine arithmetic cases, unknown/boundary cases, positive balanced
caller contexts and conservative frame/control regressions. Independent review
passes this relative-frame step. Full native tests retain only the same two known
baseline failures. Fresh service queries still refuse all five roots; stronger
exception guarding now reports `$9C76` first at `$464` (`MOVE #$2700,SR`) instead
of the later A6 status write. Original expanded and compact reproduction remains
exact. Current machine evidence uses the `frame-prefix-*`, `tests-frame-final.log`
and `independent-frame-prefix-review.json` files in the same evidence directory.

This completes the relative-frame capability, not keyboard relocation. Absolute
stack bounds, other-base address provenance and interrupt preservation remain
unproved. [Proposal 044](../proposals/044-runtime-memory-relocation-proof.md)
records the required native domain and optional conditional execution contract;
conditional build/guard enforcement does not yet exist. No Pandora artifact was
built, reserved or executed at the new placement, and no new target/history facts
were added by this framework continuation.

The following closure investigation used fresh native instruction and caller
queries, without adding a proof assumption or changing target facts. Explicit A6
definitions are `$48C` and IRQ `$8E8` (application base `$39FC`), `$4D978` (custom
base) and `$4D98E` (audio channel arithmetic); `$1034` and `$97C8` restore A6 from
the stack. The audio callers visibly pair `$102A..$1034` and `$97BE..$97C8`
push/call/pop sequences. This identifies the preservation obligation; a matched
pop does not prove its saved slot remained intact through the callee.

The seven explicit SP definitions/adjustments are `$47A`, `$4BA`, `$609E`,
`$71A8`, `$71B2`, `$71C2` and `$71C6`. The first two initialize SP from the native
PC-relative `$10452` anchor. Their presence alone supplies neither an incoming
SP interval at a later keyboard root nor a complete future stack envelope.

The IRQ handler at `$8E4` saves D0/A0/A1/A5/A6, establishes A6/A5 at `$8E8/$8EE`,
dispatches a callback through one of three mutable application slots and has four
matching MOVEM/RTE exits. Those exits show intended register preservation, not
proof that callback writes cannot alias the saved frame. The keyboard producer at
`$86A` writes A1; its preceding `$862` LEA establishes CIA access through A0.
Closing that root still requires the incoming IRQ stack domain, the application
base at its call and preservation of both callback and interrupted frames.

The pause-gate root `$2D2A` has three resolved native callers: `$600`, `$902C`
and `$9C40`. Its returned A0 remains live into joystick handling, which writes
through A6. Thus merely dropping the caller-prefix obligation would not close the
alias obligations. The `$9C76` exit path reaches the `$464` SR write before A0's
independent replacement at `$49E`; skipping the mode transition would assume the
supervisor/frame condition that still needs proof. No addition in this
investigation closes any of the five roots; no broader abstraction was added.

Inspection of Copperline's pinned `v1.0.0` source was blocked by the network proxy
with `403 Forbidden` for the GitHub API tree request. That restricted fetch was
stopped without an alternate route. The local listing service remains available.
The before-execution/interrupt guarantees required for a conditional runtime guard
route have not been established, so that route cannot authorize a derived build.

The next step is shared native provenance/frame analysis establishing disjoint
application/object storage and balanced caller/callback stacks. Re-review those
five roots, then build the seven-rewrite artifact through the normal verified
operation, reserve its destination with checked Exec `AllocAbs`, and run the
same reset/press/release/gameplay scenario against the new region and old-address
guards. Original exactness and accepted-reference closure do not establish whole
game relocation, unknown aliases, arbitrary mutations or other scenarios.

“Unknown” below is an analysis status, not failure of exact source reproduction.
No subsystem is declared fully restored by the inventory.

Historical checklist (2026-10-14; superseded for current priorities by the
subsystem review at the end of this document): “documented” means the selected facts and
consumer contracts below are reviewed; “partial” retains a known semantic or
lifecycle limit. “Unanalysed” identifies the next evidence dependency, rather
than a new coverage metric. No row claims complete subsystem recovery.

Normal source regeneration now persists `binary_assets` presentation (minimum
256 bytes) through the Manual Action Log. The checked-in source uses relative
INCBIN companions recorded in its [ownership manifest](../../targets/amiga_disk_pandora-1988-firebird/targets/amiga_raw_pandora_3e1ee0f1_bk_00_000000e8/source-package-manifest.json).
Asset labels and filenames share the reviewed native purpose name; separate
section/range identities survive naming changes, with provisional names retained
where purpose is unknown.
Native classification and conservative boundaries still govern selection;
structured tables, pointers and ambiguous spans stay inline. This changes source
presentation, not the semantic recovery status below.

| Subsystem | Documented | Partial | Unanalysed / next dependency |
| --- | --- | --- | --- |
| Bootstrap / initialization | Fixed-base overlap-safe copy, continuation, supervisor/stack/workspace and initial buffers | Dependent resource setup and storage lifetimes | Copy-helper return lineage, temporal overwrites and alternate placement |
| IRQ / frame / gameplay | Dispatch priority, display pointer programming, completion latch; front/back swap and shared main/modal input, text and mission-timer services | Callback effects, input phases and buffer ownership | Complete allocation/lifetime and caller coverage |
| Title / starfield | Ten-byte record fields and five scoped A2 inputs; grounded post-reset continuation typing; ten initialized runtime samples match signed projection arithmetic | Byte 9 remains unknown; clear/render use continuation jumps; the 1000-byte runtime array is outside the absolute-storage command schema | Complete runtime ownership/lifetime, table bounds and indirect paths |
| World commands / objects | All 33 handler identities and operand contracts; 12 shared command schemas, 20 scoped handler inputs and 31 named operand uses; 17 records in the diabetic/officer programs now use those same formats, with named active/held and post-handoff waits; selected object prefixes; 780 commands and 1843 typed fields in all 26 initialized NPC streams; the remaining 14 streams add 238 source anchors and 238 relative WORD references with opcode names | The officer handoff inhibits opcode dispatch while delay continues to count down; restart can exchange active/saved states before restoring the initial cursor. External cursor writes and transitive callback effects remain open. Mutable scripts, raw pointer operands and arbitrary pointer/lifetime limits | Full-family capacity blockers are resolved with checked 8192-entry data/label storage and 512 manual references; remaining work is indirect/runtime effects and pointer/lifetime coverage |
| Combat / encounter | Proximity/trade entry, equipment reload/damage tables, player/opponent charge state, health overlays, hit feedback, charge gauge and defeat cleanup; initialized callback targets and their shared item-state helper | Four non-null callbacks among 35 initialized objects; callback precedes opponent deactivation; item-state addition wraps modulo 256 and skips flag-bit-1 objects. XY-copy and saved-state swap use typed object fields; the table wrapper loads A0 but the helper inherits A5 | Mutable callback replacements, fixed-RAM pointer purpose, complete state/pointer lifetimes and indirect callers; nine initialized saved-state pointers are null |
| Scene / tiles / geometry | Reviewed scene selectors, tile records and selected pixel/mask banks; mask-input/border consumers and shared 20×8 modal grid; fixed NPC and receptacle geometry/descriptor families | Receptacle deposit saves the attachment, completion/restart restores it and clears the saved pointer; restart clears the entire interaction flags byte, including proximity bit 0 | Remaining banks, complete write ownership, arbitrary attachment chains and DMA constraints |
| Entity animation / updates | Shared geometry/clock/draw-state contracts; directional and combat controllers; fixed NPC geometry, sequences, saved nodes/states and six descriptor/paired-state clusters. The existing 22-state table retains its exact 26-byte prefix; two checkpoint attachment states have a separate 52-byte owner. Shared rules cover 119 attachment fields; the diabetic first-attachment pose controller adds two frame descriptors, one node and its held/active pointer pair (62 bytes). The shared state exchanger is reversible and restarts only the incoming node | Initial 112-prefix attachment graph closes with 23 links, no cycles and maximum chain three. Original script/header counts ground 49 fixed sequence slots; the unproven 60-byte gap remains raw. Six receptacles retain explicit conditional pointer tails and six-byte interaction records. Numeric mask RAM values, nulls and shared state remain preserved | Mutable sequence replacements, conditional chain extensions, later attachment cycles/alias writes and complete caller/lifetime coverage |
| Player movement / collision / camera | Axis scaling, tile probes, request versus drift/commit, direction/idle modes, bitset and camera handoff; movement script, directional prefixes, copied-pointer links and corrected idle field; two typed camera countdown/margin profiles, sequential field reads and movement scroll triggers | Initialized-map restriction prefix, unchecked profile index and coordinates, and pointer/lifetime limits; ambiguous or inactive runtime mappings refused | Later exit-delay reset/writer coverage and reachable inherited state; failed ID-recheck continuation, status bit 6 meaning and ordinary-map admission of synthetic arithmetic cases |
| Inventory / trading / NPC | Diabetic selected/carried insulin and needle responses, self-destruct advice latch and read-only range predicate; four named ASCII responses (178 bytes). Four-entry records, 81 table identities, 175 typed address fields; current/initial inventory and offer pointers, source name pointers, shared empty-bank role, selected offer/reset/panel/name/pocket paths and proven item/name constants | Self-copy aliases; unmatched +8/+9 reaches setup/palette scratch. Original shared zero offers and clear trade-ready flags cannot arm a matching trade. Cursor domains, duplicated display identities and selected security callbacks remain qualified | Later alias/flag/pointer writers, complete callers, templates' write ownership and lifecycle |
| Mission / terminals / outcomes | Terminal versus self-destruct modal roles; SDI disk and qualifying-card count, submitted-name prefix, Earth BCD deadline versus armed main-loop countdown, outcome latch and salvage/defeat ranking; shared title/gameplay palette counter; decoded escape helper, six conditional 70-step reloads and distinct main/modal exit gates; fade/brain health latches | Local validation has no order/duplicate check; modal header changes role on swap; counts wrap and exit timing depends on service paths | Later delay reset/writer coverage, reachable zero/inherited states and complete writer/lifetime and domain coverage |
| Text / fonts / overlays | Compact/title fonts and rendering contracts; proportional UI font with 68 advance-plus-seven-row records and its 96-byte character map; renderer/cursor/shift state; all ten fixed 44-byte overlay descriptors; background capture/restore/clear register contracts, persistent 16-slot callback scan, 200-WORD raster lookup and split world/UI framebuffer addressing | Snapshot transfers preserve original rounding, inherited blitter state and restore byte-height wrap. Fixed snapshot extents and reset/palette-input overlaps are explicit; queue deduplication still permits recapture. Registration deduplicates only the non-NULL prefix; all ten initialized callbacks are NULL. Font bounds remain unchecked and straddle DMA can read a neighboring WORD. Header/pointer consumption is phase-dependent | Queue-processing gameplay reachability; 128-byte clear versus 64-byte queue and adjacent storage ownership; complete framebuffer/snapshot aliases and phase ordering, DMA completion, exclusive allocation/lifetime and arbitrary inputs |
| Audio / samples | Four-channel commands, lists, programs, pitch/volume and secondary streams; nine shared address rules distinguish 43 cold NULL bases/cursors; 29 pitch/primary-volume selector references and six secondary references; eleven sample extents, 64-byte silence and 640-byte secondary waveform owner | Original 858-token corpus yields pitch indices 22..58 within 72 WORDs; configured secondary DMA windows fit five 128-byte slices. Future selectors remain unchecked; primary/secondary marker and reload semantics differ; reset retains ticks and NPC pending bits | Mutable cursors, later/interleaved DMA writes, arbitrary replacement scripts, caller combinations and storage lifetime |
| Unclaimed resources / uncopied tail | Original bytes preserved by exact reassembly; mask-input and border prefixes, 910-cell mask bank and 29 modal tiles classified; six descriptor references corrected to canonical source coordinates | Known consumers establish selected physical prefixes; the first cold-title zero blit footprint covers the loaded-input tail. Three sampled tail windows become zero at title and two change again by UI entry; original purpose stays unproved | Original file-tail purpose, complete later writer/consumer coverage, DMA lookahead and scratch allocation bounds remain unknown |
| Alternate execution layout | Two-byte volume relocation: both normal game WORD writers agree | Nine bounded local CPU calls and all 65,536 direct BYTE-store words agree; normal-gameplay BYTE execution remains unobserved | Whole-game changed code/data/DMA placement, temporal/late lineage and unrestricted contexts remain unproven |

The scripted-pose checkpoint runs the original interpreter, both diabetic
callbacks and the shared controller in a bounded local CPU fixture. The first
attachment receives the controller once; 100 interpreter-delay counts select the
active frame and six select the held header. Primary state is unchanged. The
handoff helper has an input-only A5 object contract: player defeat skips it;
otherwise it transfers the selected item and clears the first inventory slot
before the state/UI callbacks. The giver becomes inactive: delay counts down
before the flag test, but later opcode dispatch stays inhibited. The nominal
long-delay tail alone therefore does not explain resumed behavior.

The shared helper is now `exchange_world_object_position_states`, reflecting its
two-way active/saved pointer exchange. It clears the incoming node hold bit and
frame/phase clock; a second call exchanges states back. Its complete register
partition preserves the caller's initial-flags byte in D0 on normal returns with
valid, disjoint records/stack. Memory/escape effects stay unknown. Restart calls
it only when current and initial inactive bits differ, then restores initial
flags; the later suffix restores the original script cursor and clears delay.
Four bounded CPU cases cover two exchanges in three mode/clock contexts and the
handoff prefix, countdown/inhibition, restart parity branch/cursor suffix and
re-entered introductory delay. Full queue/UI/audio calls and intervening restart
callees are outside those cases. The examined diabetic hint paths issue no controller replacement. Generic
combat, alternate scripts, later aliases and complete pointer/caller/lifetime
closure remain open.

The diabetic callback is a one-time self-destruct advice event, not a pose
transition in the examined paths. NPC-selected hypodermic plus player-selected
insulin and strict `abs(dx)<24`, `abs(dy)<16` WORD-coordinate tests set the latch
before attempting two hint queue entries. With a different player selection,
four carried IDs distinguish missing insulin from insulin carried but not
selected; selected insulin without the needle requests that prerequisite.
The shared `request_world_object_context_message` tail sets cooldown 250 and
carry. The advice path clears carry, leaves the selected items/inventories and
object/player records unchanged in the tested contexts, and keeps its latch even
if the queue is full. Global interaction-flags reset rearms the hint independently
of controller installation. The initialized pose mode stays zero/hold-only under
its script/controller paths; the callback leaves the controller and 100/6 loop
intact. This is not a universal absence-of-writers claim.

Thirteen original CPU cases cover positive/negative strict range edges, four-slot
scan bounds, both responses, selected-item/inventory preservation, advice queue
entries/refusal, latch/rearm and continued active/held poses. Full callback runs
use a preactivated valid queue to avoid entering text drawing; inactive-queue
rendering, hardware timing and ordinary gameplay reachability remain outside the
fixture. The leaf range helper has a reusable read-only, no-input-escape contract
and preserves all general registers except D0/A4. The prior shared prompt
contract and every initialized callback/script target are unchanged.

Native analysis now renders the
position-descriptor operand at source `0x938E` numerically across the helper's
unknown memory effects in a pointer-table loop. Its canonical type/table facts
are preserved; restoring that derived annotation requires a caller-visible
alias/lifetime proof rather than an unconditional type seed.

Reproduce with `.venv/bin/python -m pytest -q tests/test_pandora_scripted_pose.py tests/test_pandora_state_transitions.py tests/test_pandora_diabetic_interaction.py`.
The combined catalog/model/type/pointer suite passes 261 tests; the state-transition
and diabetic-callback cases are in the reproduction command above. Canonical review
preserves every other layout/type/contract/comment, all 30 initialized absolute
script targets, asset/include identities and both history prefixes. C and vasm
match all 376,832 original bytes, receipt
`48630088a3214fabb773fd0f442ff361846a27b95fbf64cb5c600ce38ec1d146`.
This is bounded CPU validation; normal-gameplay BYTE volume coverage remains
unobserved and clearance-route expansion remains paused.

Shared overlay pipeline checkpoint (2026-10-15): eight additional 44-byte
owners supply 136 typed fields, completing all ten initialized descriptors in one
shared format. Holding, health, nearby-character/carrying/distance, hit feedback,
body, backpack and pocket roles now name caller operands and field accesses.
These names describe initial roles; the distance descriptor is also reused by
the Earth-orbit countdown. All ten initialized callbacks remain NULL. The only
non-NULL initialized snapshot addresses, `$7F0` and `$77D00`, remain unresolved
runtime storage rather than asserted static assets. Shared bitmap and callback
fields now explicitly distinguish runtime-only storage from mapped code.

The named save/restore/clear primitives have complete general-register partitions
with memory/escape effects still unknown. Capture and restore round width upward;
clear rounds downward. Restore retains the original byte-sized height shift and
clears saved/ready bits after starting the transfer. Capture/restore inherit the
first-word mask and BLTCON1; clear resets BLTCON1. The callback scan visits exactly
16 slots, skips holes and inactive descriptors, preserves registrations, and
invokes a non-NULL callback with A5. Admission scans to the first NULL or matching
pointer without that 16-slot bound. The modeled full-prefix case can reach the
following slot; this does not establish its ownership or ordinary reachability.
The existing 128-byte clear still exceeds the known 64-byte queue owner; the
adjacent 64 bytes remain unclaimed. No ordinary invocation of the callback scan
has yet been recovered.

Sixteen bounded original-CPU cases cover every initialized geometry class,
odd-width and byte-height-wrap edges, inherited control state, register
preservation, callback scan/registration persistence and admission prefixes.
The MMIO shadow checks programmed blitter packets and CPU control only: it does
not emulate DMA, pixels, interrupts or completion timing. The combined focused
suite passes **290 tests**. Native checks pass **807**, with the same two baseline
failures (`facts_v2_render_asm_source_propagates_pointer_table_pointee_type` and
`decompression_identify_reports_unknown_payload_without_failure`). The generic
entry-comment capacity is now checked at 512 instead of 128; 129 distinct
comments render and rebuild, and overflow leaves both histories unchanged.
Rebuilding that backend alone preserved the baseline source byte-for-byte.

Canonical review preserves all prior facts except the three explicitly refined
primitive contracts and two shared pointer domains, every original byte,
asset/include identities and history prefixes. The 49 appended actions include
those contract refinements; they are not 49 independent new semantic facts.
C and independent vasm reproduce all 376,832 bytes, receipt
`e3bc3f211125c4698b4c6242faeb9dc1d72c21b9d229ec1da9d5892605550d13`.
Reproduce the focused additions with
`.venv/bin/python -m pytest -q tests/test_pandora_overlay_pipeline.py tests/test_comment_write_contract.py`.
The next material gap is shared framebuffer row/address production and buffer
swap/allocation lifetime, including the snapshot destinations and DMA consumers.
The numeric `0x938E` operand, normal-gameplay BYTE writer gap and stopped
clearance-route expansion above are unchanged.

Framebuffer/snapshot reuse checkpoint (2026-10-15, after the overlay descriptor
milestone): the row producer writes exactly 200 WORDs, `160*y`, into workspace
`$39FC..$3B8C`. Each raster row interleaves four 40-byte plane rows. The two text
origin helpers mask X to 63 and Y to 31, select row index `(Y&31)*8`, add X as a
WORD and sign-extend before adding the bank. This is not clipping: Y>=25 can read
adjacent workspace. Front-buffer text follows `app_front_bitplane_base`; overlay
text always uses bank0 at `$70000`. The named gameplay Copper list waits at
vertical `$AC` (128 rows after display start `$2C`) and installs `$75000+40*i`.
VBL installs the selected world-bank pointers first. Thus the world view swaps,
while the lower 72 UI rows remain fixed in bank0.

The normal memory-region and typed-reference facilities now record these fixed
physical access extents. `persistent` records the address identity, not persistent
contents, exclusive allocation, a DMA lease or a closed relocation proof.

| Runtime extent (end exclusive) | Demonstrated role |
| --- | --- |
| `$39FC..$3B8C` (400 bytes) | 200-WORD raster offsets, CPU only |
| `$70000..$77D00` (32,000 bytes) | Bank0: title/framebuffer reuse and fixed lower gameplay UI; chip DMA |
| `$78000..$7D000` (20,480 bytes) | Bank1's 128-row world display/render prefix; no claim about the remaining bank capacity |
| `$77D00..$78000` (768 bytes) | Initialized hit snapshot: 96 packed rows of four WORDs |
| `$7F0..$10F0` (2,304 bytes) | Initialized body snapshot: 192 packed rows of six WORDs |

The existing runtime-only snapshot field group resolves both non-NULL initialized
bitmap pointers to these bounded address symbols; all ten callbacks remain NULL.
The overlay pointer report has 77 NULL and 13 symbolic fields, with no unresolved
field in this family. That is address-resolution coverage, not allocation or
lifetime closure. Instruction-region reference discovery and typed data-field
resolution remain complementary. Native region references include explicit
`ambiguous_scalar_or_pointer` candidates (for example blitter-control and color
immediates numerically within the low body-snapshot range); those are not
confirmed pointer uses. Absence of a qualified instruction reference cannot
prove that snapshot storage is unused.

Priming uses one WORD at the hit snapshot address. The seeded copy's programmed
destination `$70028..$7CD28` crosses that snapshot and bank1's prefix; its zero
modulos, inherited BLTCON1 and lack of a final completion wait are preserved.
An existing queue match still requests a new capture when bit 6 is set, even if
saved/ready bits were already set. The saved bit does not guard the restore leaf.
Captures therefore do not establish immutable original-background contents.
Separately, `prepare_work_buffer_arguments` supplies A1=`$77FE0`, the last 32 hit
snapshot bytes, to the 16-WORD palette readers. The source now expresses that
physical alias through `WORK_BUFFER_PALETTE_INPUT_BASE`, whose EQU expression is
`UI_HIT_BACKGROUND_STORAGE+$2E0`. The preparation/unpack leaf is
checked; stack-trampoline caller reachability and phase exclusivity are unproved.
The discarded `$78000` stack arguments and unexplained app `+$1E0` role stay
uninterpreted.

Fifteen bounded original-CPU cases cover the row producer, valid and out-of-table
cursor calculations, reversible world-bank exchange, VBL's four plane-pointer
writes, both initialized snapshot packet extents, reset reuse, repeated capture
and the palette input alias. The MMIO shadow performs no DMA, pixel, IRQ or bus
arbitration simulation. Original WORD arithmetic, geometry rounding, restore
height wrap and asynchronous return behavior remain intact.

The reusable setup fix widens checked RSSET aggregate extents from 255 to 32,767
bytes through catalog validation, metadata projection and native policy, allowing
the full 400-byte row table to replace a partial/absent declaration. Extents 255,
256, 400 and 32,767 retain an adjacent declaration and reproduce exact bytes with
C and vasm; 32,768 is refused without changing history. The native structure keeps
its overall size and eight-byte prefix, but flags move within that prefix; native
objects and the ctypes mirror were rebuilt together for the widened field.
The rebuilt backend alone preserved the previous canonical source byte-for-byte.

The final combined applicable suite passes **414 tests**, with one skipped
independent Copperline arithmetic oracle because `COPPERLINE_BINARY` was unset.
Native checks pass **807**, with the same two baseline failures recorded above.
C and independent vasm reproduce all 376,832 original bytes, receipt
`163c58a36b2f3b4178a0df62fca7c31e7117a81c78b115cfa57e618f7bd09f0c`.
Reproduce the focused additions with
`.venv/bin/python -m pytest -q tests/test_pandora_framebuffer_lifetime.py tests/test_rsset_aggregate_extent.py`.
All previous layouts, schemas, call contracts, initialized script/callback
values, original binary, asset/include identities and history prefixes are
preserved; only the six scoped comments refine earlier/new rendering explanations.
No alternate-layout payload or new gameplay route was created. Native pointer,
alias/control-flow and asynchronous DMA obligations remain explicit. The next
material rendering gap is the phase/caller ordering that makes snapshot reuse
safe, including the work-buffer palette readers and completion before consuming
or replacing snapshots. This requires a bounded reachable-path question before
any hardware probe; a frame-completion latch alone is not a blitter fence.
The numeric `0x938E` operand and unobserved normal-gameplay BYTE volume writer
remain unchanged, and clearance-route expansion stays paused.

The native ownership snapshot immediately before the font/lifecycle batch has
55,391 unclaimed bytes, including the 27,792-byte uncopied tail. These are
classification counts, not a semantic completion score. Major open work is the
remaining resource producers/consumers and tail purpose; mutable callbacks,
sequence replacements and shared-state lifetimes; unresolved indirect transfers;
and the separate alternate-layout execution gate. Completion needs grounded
physical owners and address identities, qualified control/data-flow effects,
reviewed readable source and exact original reproduction. Alternate-layout
completion additionally needs execution evidence for an actually changed legal
layout, including its code, data and DMA addresses.

The normal native asset planner owns INCBIN selection and naming; the shared
publisher owns companion files. Original disk/loader parity remains explicitly
out of scope.

2026-10-14 command-operand checkpoint: 12 shared formats replace raw A4 offsets
in 20 handlers (31 native field bindings across 30 instructions). Three
sequence-command inputs refine six-byte prefixes without changing the other
node handlers. Eleven narration comments are withdrawn; six shared comments
retain loop, delay, address-base and callback-effect semantics. All unrelated
metadata, assets/owners and history prefixes are preserved. The normal journal
accepts 41 facts; 191 focused tests pass. Complete C/vasm reproduction is exact
for 376,832 bytes, receipt
`d6b3c4ea35990c404e537137730cb6b106dd10d48c792ba41ada8423eabda415`;
source SHA256
`cfe068408fcfec9bf33549a55de08695216c926937626e45bd3286de23f1c56b`.
Indexed relative-copy accesses and the heterogeneous interpreter cursor remain
untyped; pointer safety, mutable callback effects and lifetimes stay open.
No gameplay route was expanded and the BYTE coverage gap above is retained.

## Framework repairs accompanying the startup batch

- Null or missing source coordinates no longer match unrelated legacy evidence.
  Concrete section/offset identity is required, including valid offset zero.
- Native-derived comment preflight rejects oversized or lossy text before atomic
  history writes. Undo/removal of invalid legacy comments remains possible. An
  attempted long startup comment was undone through the shared service; its
  record remains intact. See [the limits and storage proposal](../proposals/043-native-comment-contract.md).
- Restoration status polling retains failed build errors without retrying.
  Explicit retries and changed revisions still build, and active retries take
  precedence over older failures.

Focused validation: 57 listing/restoration tests, 135 comment/manual-log/catalog/CLI
tests, 12 runtime-domain/function integration tests, and 636 native IR tests.
These are focused results, not a claim that the full repository suite is green;
the previously identified Ancient decompression baseline failure remains.

- Naming the bootstrap exposed a runtime operand selecting its storage label
  before ORG. The renderer now retains the separate aliases and selects the
  runtime alias for an absolute reference at a materialized range start. Four
  exact-byte synthetic cases cover generated/named aliases, interior labels and
  identity mappings. The failed target proof is retained, not marked accepted.

Exporter PR2 was integrated from `3d68fba0` without conflicts. After rebuilding
the combined backend, 116 focused restoration/runtime-label/package tests passed.
No new resource classification was added just to enable asset extraction.

## Preserved startup original-layout proof

The combined backend produced exact original bytes with both the project
assembler and vasm: 376,832 bytes, SHA-256
`70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
Verification receipt:
`3ac4af90cb7033c823720e589b6a918bcdd39c6796e0d8b13764908897f05438`.
The native service also confirms call source `0x9C2A` targets source `0x7F0`.
Post-integration native checks: 638 IR tests and five source-package tests pass;
the known Ancient unknown-payload identification test still fails.

The local service listens at `http://127.0.0.1:8123`; no public hosting was enabled.
Next substantive batch: corroborate and correct the 33 displaced world-command
handler identities, then recover their operand/effect contracts and startup
state dependencies. The full restoration and alternate-layout milestones remain
open; original disk/loader parity is outside scope.

## Next batch audit: world-command semantics (not yet accepted)

A bounded native query retrieved all 242 accepted instructions in
`0x1114..0x1432`, covering the 33 handlers and interpreter. This exposes semantic
errors as well as the displaced legacy coordinates:

- Opcode 5 / source `0x11A4` writes the word at script+2 to object+`0x44`, then
  advances the script by four bytes. The interpreter at `0x13FC..0x1406`
  decrements this field before resuming commands, so the old “repeat count” name
  should become a delay-setting interpretation.
- Opcodes 14/15 / `0x1258`, `0x1266` compare object X/Y against a pointed-to word.
  Inequality takes the normal eight-byte advance; equality takes the shared
  relative branch at `0x1222`. The old “skip if not equal” labels are misleading.
- Opcodes 10–13 use unsigned comparisons, with the same branch target formula:
  old script pointer + signed word at script+6 + 6. Normal advance is eight bytes.
- Opcode 6 / `0x11BC` decrements the mutable word at script+4 and branches by the
  signed word at script+6 while nonzero; at zero it reloads script+4 from script+2
  and advances eight bytes. Opcode 21 / `0x11AE` also writes within script-relative
  storage. These establish mutable script data, not modification of instructions.
- Opcodes 31/32 traverse attachment records seeking bit-3 set/clear respectively,
  then toggle bit 0 in the selected state node. The old opcode-31 “first
  attachment” name omits the predicate.

These are review candidates derived from native instructions, not accepted new
facts. Preserve the original names/history until the coordinated correction and
contract batch passes review and exact reproduction. Repeated per-label full
rebuilds would be wasteful; any batching improvement must keep shared catalog
validation, fresh revision checks, atomic persistence and evidence identities.

## Completed world-command batch

All 100 canonical actions were independently reviewed and accepted in the
Decision Journal: 33 removals of misplaced legacy labels, 33 replacements selected
through real source-row catalogs, and 34 semantic comments. The catalog records
replacement labels in the appropriate runtime domain, with canonical source row
keys; no blanket address subtraction was introduced. All 33 table references and
242 instruction byte strings were corroborated against native facts/original bytes.
Previous action and journal prefixes and the startup verification receipt remain
intact. Full C and vasm output is again exact at the original SHA-256, receipt
`ecb03b7dea04ea9ccbeb5514f9e46a077d423d4b51c2480dc3c64c2e91aacf09`.

This batch completes handler identity and instruction-level operand/advance
behavior. It does not finish world scripting: actual script bounds/instances,
indirect callee effects, record lifetimes and alternate-layout pointer treatment
remain open. The byte-classification table above remains the dated baseline;
semantic documentation alone does not establish new resource ownership.

The shared restoration service now supports bounded `interpret_batch`: one
inspected revision, all evidence/catalog validation before one atomic append and
one invalidation. Request-local context reuse avoids repeated catalog resolution
without retaining another fact store. Initial 102 focused tests passed; the reuse
follow-up passed 55 focused tests, including independent parameters, invalid-final
atomic refusal, request isolation and synthetic exact rebuilding.

Next connected audit covers runtime initialization and frame service. 165 saved
instructions establish the fixed workspace clear, supervisor entry, sampled IRQ
priority and frame-completion latch. Cursor-buffer ownership, callback clobbers
and complete buffer placement constraints remain questions for focused consumers.

## Completed initialization/frame/sprite batch

The second connected batch adds 11 canonical labels, 19 comments and three typed
app slots: status byte at `0x27B`, sprite-0 DMA pointer at `0x20C`, sprite-1 DMA
pointer at `0x210`. All 33 actions are independently reviewed and accepted in
the Decision Journal. Their evidence captures workspace clear `[0x39FC,0x3D68)`,
supervisor/TRAP0 entry and stack reset, fixed framebuffer setup, sampled IRQ
priority/fallback, precise saved-register subsets, frame-completion signalling,
blitter setup and cursor pointer/palette binding. All 472 distinct saved
instruction encodings were corroborated against the original.

The new slot names propagate to all 25 status-byte and four references per sprite
pointer. Full C and vasm output again matches the complete original payload,
receipt `c3e8572c84d71c55de745ed1c8eb8049f4c74f0960b5e04706008315ec45faf3`.
The earlier startup and handler receipts remain preserved historical evidence.

Native instruction queries now filter literal text before pagination; unsupported
text queries are refused rather than silently ignored. This narrowly supports
consumer discovery without another analysis store. 67 focused native-query and
restoration tests pass. Current native searches find exactly two `$65370` uses,
and confirm the pointer slots' blank/current/reset transitions.

Allocation extents, cursor pixel-data origin, all callback clobbers and legal
alternate placements remain unresolved. In particular, the seeded blit inherits
BLTCON1; its stated geometry is not proof of the whole framebuffer allocation.
A parallel read-only graphics audit has corroborated larger selector/definition
table bounds; canonical corrections and raw tile-read ownership are the next
resource slice, with descending-blit direction an explicit precondition.

## Completed world-tile table bounds

Two underbounded layouts and their arrays are corrected through six accepted
canonical actions. The selector table is `[0x3502,0x3F16)`: 1,290 big-endian words
(43 rows by 30 columns). The definition table is `[0x3F16,0x5FFE)`: 468 records
of 18 bytes, each containing nine word offsets. The original array names, kinds,
strides and hex representation are preserved. This adds 8,398 consumer-supported
structured bytes beyond the formerly declared table ends. The definitions stop
at the accepted code entry `test_bitmap_pixel_bit`; no code range was crossed.

Both inspected stages pass complete C and vasm equality. Final receipt:
`feadbea3a677f6481c0464c6e08416f7a88f1e0ec4e5b346588f161c8df8b866`.
The six actions are independently reviewed and accepted; old action/journal
prefixes and earlier receipts remain preserved.

The initializer expands the selectors into a 90-by-129 longword pointer grid
at runtime `[0x4000,0xF568)`. This is writable runtime workspace, not source-file
asset storage. It is an additional placement constraint for alternate layouts.
Tile offsets are multiples of 128 relative to runtime atlas base `0x1D0A8`
(source `0xD0A8` under the native copied view). Those offsets remain relative
values when an atlas base changes; they must not be blindly relocated as pointers.

The initialized map selects 475 distinct 128-byte tiles: 60,800 bytes in 25
intervals within `[0xD0A8,0x1CEA8)`. The 33 holes remain unclaimed. Independent
review establishes ascending blits for recognized normal-entry static writer
paths; unknown indirect/interior/external writers remain outside that contract.
Classification of those selected intervals is the next separate canonical slice;
the entire atlas envelope and its exclusive allocation are not thereby proven.

## Reviewed selected world-tile pixels

The 25 selected intervals now have canonical bitmap layouts and 128-byte array
elements: 475 records, 60,800 bytes. Layout creation and element assignment used
separate revision-bound batches, with fresh catalog identities for the second
stage. Independent review approved all 50 actions. All 33 holes, including tile
offset `0xF980`, remain unclaimed; the recognized ascending-blit entry paths do
not prove unknown writer behavior or exclusive ownership of the atlas envelope.

Both stages pass full C and vasm byte equality. Final receipt:
`309d42105184a55ea20424df088cdf39dfedc8167c4e84b5219d1a498e137c04`,
source subject `dbeff021c28c09f1b7488ed09dc881784f36c0b9c06c142d31f901b807b2591d`.
The generated source gains logical tile-index names and symbolizes the proven
builder base without changing original bytes. Journal acceptance is recorded
through the shared service; the original history prefixes remain intact.

A fresh native ownership snapshot at this source subject is recorded in
[`pandora-coverage-current.tsv`](pandora-coverage-current.tsv): 328 disjoint
intervals account for every payload byte. Native accepted code remains 24,394
bytes; accepted noncode is now 82,817 bytes; 269,621 bytes remain unclaimed.
Accepted ownership covers 107,211 bytes (28.45%), versus 38,013 bytes (10.09%)
in the dated baseline. This is ownership coverage, not semantic completion or
automatic acceptance of legacy annotations. The baseline snapshot is preserved.

The next input question concerns keyboard polling's absent-PORTS branch: it
skips loading CIAA into A0 but still performs two writes through A0+`0xE00`.
The caller's A0 contract is not yet established. The bounded scenario
`runtime/scenarios/pandora-keyboard-ack-a0.json` captures registers at the branch
and first write using the verified rebuilt payload. No speculative branch fix
or unconditional CIAA write interpretation is warranted.

The title/no-input probe timed out after ten seconds without reaching keyboard
polling; receipt `0a2c143401a2342f16935279635e08affda591ec4ebe34eb6dac062353c1e5dd`.
After the established title/UI/gameplay input sequence, both source `0x860` and
`0x886` hit with unique rebuilt-payload identity. At both points A0 was
`0xDFF010` and D0 was `0xFFF50160`: PORTS bit 3 was clear, and the pending byte
write address was therefore `0xDFFE10`. Receipt:
`652451a8bc8e9a6900a02b5a19173022359fec5053c053fe3a456debd09f8f59`.
This is one observed call after gameplay entry, not proof about every caller or
the bus effect of the write. The original bytes remain unchanged. Both owned
emulators exited; no instruction trace was collected.

## Completed input interpretation

Seven canonical actions are independently reviewed and accepted: rename source
`0x7F0` to `poll_joystick1_directions_and_fire`, add the scalar bytes
`app_input_fire_pressed_ff` at app offset `0x22F` and
`app_last_pressed_raw_key` at `0x222`, and add four semantic comments. The fire
byte propagates to all eight native uses; the key slot is stored only on press
on the inspected decoder path. The joystick mask uses up/down/left/right bits
0/1/2/3; opposed inputs retain both mask bits while left/up overwrite signed
steps. The routine returns that mask in D0, and its final Z flag ignores fire.

The key decoder bounds its fixed runtime state table to 128 bytes at
`[0x397C,0x39FC)`, storing FF for press and zero for release. This does not make
the table source-image data or prove every indirect user. The absent-PORTS
branch preserves the qualified A0-write observation above. Nineteen `MULU.W #1`
operations preserve the low word and zero-extend the first result; no fixed
elapsed-time claim is made. Review removed an unapplied destination-dependent
timing claim: [MC68000UM §8.3](https://www.nxp.com/docs/en/reference-manual/MC68000UM.pdf)
defines MULU's variable timing in terms of the source operand.

All 69 inspected instruction encodings match the original. Current source again
reproduces the entire original with C and vasm. Receipt:
`c9157906795e9fa396f8eb50894a3c4ab0312b65d92dc4150e61516922ebc0f3`,
source subject `23f77d51019537ca4063cd69bc6824c0050742ac144d6d0f615078333db0731f`.
History prefixes are preserved and the timestamp-only project update is removed.
This slice changes names and comments, not code bytes or original behavior.

## Reviewed graphics banks and packaged source

The next 62 canonical actions define 31 bitmap banks and their arrays, covering
115,872 bytes. The CPU mask builder reads four plane words per 16-pixel cell and
ORs them into one mask word. Three animation headers establish six-frame banks
with 32×32, 16×32 and 32×32 geometry. Other banks retain flattened pixel cells;
their individual image geometry is not established. The 1,392-byte gap at
`[0x39DC8,0x3A338)` and first bank `[0x3A738,0x3D338)` remain excluded. The latter
overlaps accepted code whose source/runtime discovery provenance needs review.
No speculative code withdrawal or arbitrary address subtraction is applied.

All 497 resource evidence instructions match original bytes. Full C and vasm
reproduction passed, receipt
`0ab558624a39b8ff3acc3e581a6f4d7075b1c4adb90745b76d7417e5673f9863`,
source subject `0626bd88d57152fcaa367207f502942c8d597f48941a488404a9c5338ca9dac5`.
All 62 actions were independently reviewed before acceptance; both durable
histories preserve their prefixes.

The 138 effective representation records exceeded the native fixed limit of
128. Generic policy storage now uses four inline records and bounded heap growth
to 4,096, with duplicate/conflict checks before capacity rejection, deep-copy
ownership and allocation-failure preservation. The C policy ABI changed; all
native aliases were rebuilt together before restarting the service. Validation:
31 focused Python tests, 638 native IR tests and three lifecycle tests passed.

The current ownership snapshot has 332 disjoint intervals: accepted code 24,394
bytes, accepted noncode 198,689 bytes and unclaimed 153,749 bytes. Accepted
ownership is 223,083 bytes (59.20%). These counts include existing accepted code
under provenance review; they do not measure semantic completion. The dated
baseline remains unchanged.

The real binary-asset package passes full C and vasm reproduction of all 376,832
original bytes. Its 48 assets contain 132,896 bytes, checked against the union of
reviewed bitmap intervals. Conservative packaging leaves other bytes inline.
Nine SDK includes are bundled. The include collector now handles balanced single
quotes used by the SDK while retaining containment and malformed-operand checks;
all 31 source-package tests pass. ZIP SHA256:
`91f31b4b75fe088d82542f48538dd9871cfd88dd30bb796cfee0a505f9253e11`.

```sh
.venv/bin/python -m amiga_reversing.tools.source_export \
  amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8 \
  --binary-assets --minimum-asset-size 128 --verify-package \
  --output .runtime-state/pandora-analysis/pandora-reviewed-graphics.zip --json
```

Full readable restoration and actual alternate-layout execution remain open.
Original disk/loader parity is outside this restoration's scope.

## Remaining mask banks and selected title records

Another 64 independently reviewed catalog actions define 26 remaining scene
mask-input banks and six selected title records, each with a bounded array.
The scene initializer at source `0x74FC..0x7712` supplies constant input/output
pointers and loop bounds to the same reviewed CPU mask builder. Native typed
references establish source coordinates directly. All 131 initializer encodings
match original bytes; the 26 source banks cover 38,224 bytes in
`[0x3EFA8,0x484F8)`. Their array stride is eight bytes per four-word cell.
Individual frame shapes and exclusive ownership remain unproven.

The direct title caller at source `0x1002` passes `PANDORA\0` from `0xA7D0` to
the large-character renderer. This proves only A,D,N,O,P,R: six 128-byte records
selected from base `0xC3A8` with `128*(character-'A')`. The copier transfers 32
rows of four bytes, starting at cursor+120 and stepping 160 output bytes per
row. All 47 inspected encodings match original bytes. These records use the
conservative `data` role; no complete alphabet or planar image format is claimed.

The final generated source again passes full C and independent vasm equality,
receipt `1ff4512783ca2aa510c6a82707176ccf22f76c5565c321a3bd3d2794d7860664`,
source subject `3b3a971b97506695e32e92c1f927a33d3590759dfc75d6a4bdd1760384703ce0`.
Both histories retain their prefixes. The current native partition has 342
disjoint intervals, accepted code 24,394 bytes, accepted noncode 237,681 bytes
and unclaimed 114,757 bytes. Ownership is 262,075 bytes (69.55%); semantic
completion and actual alternate-layout execution remain open.

A bounded native append diagnostic now establishes the questioned code's
discovery history: source caller `0x896C` first seeds/accepts `0x3D310` while only
the initial load view exists; the copied view appears later, and the final
native reference resolves the call to `0x4D310`. The inferred caller runtime
`0x2896C` does not prove actual loader-phase execution. The diagnostic retained
265 scoped events with no drops and left backend, metadata and histories
unchanged. A reviewed generic context/provenance repair is in progress; neither
the questioned code nor its overlapping resources has been reclassified here.

## Bounded audio input records

Fifty-eight independently reviewed actions clarify `audio_sample_record_stream`
and define 11 six-byte headers plus 11 sound-sample payloads, with scalar fields,
byte arrays and two qualified comments. Native PC-relative references establish
stream source `0x4EAD8` and metadata source `0x4DEB0`. The initializer's DBF count
10 proves 11 records, each containing a big-endian 32-bit byte length, 16-bit
period divisor and exactly that many payload bytes. It references payloads
directly; no decompression occurs on this path. Metadata stride is 12 bytes;
the initializer stores pointer, length/2 and low word of `0x369E99/divisor`.
All observed lengths are positive/even and fit DMA word counts; all divisors
are nonzero with 16-bit quotients. Records end at `0x5500A`: 25,906 bytes total,
including 66 header bytes and 25,840 payload bytes.

The recognized command path selects metadata by index, stores it at channel
state+18, and the playback path reads pointer0/length8/period10 into audio DMA
configuration. Custom-register base and 16-byte channel stride are established
by native instructions. This does not prove every command index or indirect
user. Record 7 is mutable: initialization fills its 64-byte payload with 32
bytes `0xC0` then 32 bytes `0x3F`. A later indexed word writer has unresolved
complete index bounds. No immutable/exclusive-allocation claim is made. The
following 64-byte silence-buffer candidate remains excluded pending lifecycle
and write evidence.

All 249 unique instructions across the saved audio packets match original bytes.
Both durable histories retain their prefixes. Final full C and vasm equality:
receipt `23a29bb05d7a0b65c8f7cf9f59eb5aa7b79170fedb57ccda6362e7348d3e7a53`,
source subject `41d1dff7118d62915d97b66323dcd662410648f8302c8d49966628961e5779a1`.
The current native partition has 344 disjoint intervals: accepted code 24,394
bytes, accepted noncode 263,587 bytes, unclaimed 88,851 bytes. Accepted ownership
is 287,981 bytes (76.42%), still distinct from semantic completion. Audio
sequence formats, remaining raw regions and actual alternate execution remain
open, as does the separate native discovery repair.

The updated standalone package also passes complete C and vasm equality. It
contains 70 conservative assets (175,072 bytes: 65 bitmap fragments and five
sound-sample fragments), nine SDK includes and generated source. Every asset's
bytes and SHA256 were checked against its original source interval, and every
interval lies within reviewed bitmap or sample-payload ranges. Headers, small
records and other material remain inline where extraction is not eligible.
ZIP SHA256: `a5c06a380cd24449693628abf01d3b92ea7055675865fe0e0d42ba80fbca3cec`.
Package manifest fingerprint:
`298a0031a6695e648be622a083f2817885e72b608e8c3e3766e7edbb4b852edc`.

```sh
.venv/bin/python -m amiga_reversing.tools.source_export \
  amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8 \
  --binary-assets --minimum-asset-size 128 --verify-package \
  --output .runtime-state/pandora-analysis/pandora-reviewed-scenes-and-audio.zip --json
```

## Approved narrower native refusal

The larger copied-code experiment was preserved and withdrawn from the active
source. The accepted replacement prevents premature absolute-code promotion from
unphased source roots; it adds 66 native lines and removes seven, without history,
return, replay or pruning machinery. Focused preservation/refusal cases and all
638 native IR tests pass. One independently checked frozen Pandora artifact
rebuilds all 376,832 original bytes exactly with C and vasm. Source `0x3D310` is
no longer accepted code; helper `0x4D310` remains unresolved and unaccepted. Neither
disputed interval nor its overlapping banks was classified. The earlier coverage
table and 76.42% value are pre-fix snapshots, not newly measured percentages.

Copy-helper return/stale-code behavior, temporal overwrites and late-arriving
execution lineage remain explicit limitations. Independent text/audio work may
continue after this bounded gate. The loopback service was rebuilt/restarted once
at `http://127.0.0.1:8123/` (PID 39298). See the
[scope, exact proof, reproduction and preserved experiment](../validation/pandora-entry-lineage-refusal.md).

## Conditional font records and text-plane contracts

Forty-nine independently reviewed actions are now accepted in the existing
Decision Journal: 21 data layouts, 21 arrays, a byte RSSET slot, three renderer
names and three qualified comments. Twenty additional large-selector records
contribute 2,560 bytes, each 32 rows of four bytes. Together with the previously
reviewed six title records, these cover the conditional zero-extended A..Z
selectors at `0xC3A8..0xD0A8`; only the original `PANDORA` uses were directly
corroborated at the title caller. Nonstandard W artwork is preserved. No full
table-end, arbitrary-input, exclusive-allocation or image-format claim is made.

The compact prefix contains 59 eight-byte records selected by ASCII 32..90 at
`0xA8E2..0xAABA` (472 bytes). Original bit matrices corroborate letters/digits
and blank/placeholder punctuation. Source `0x9FE0` stores immediate runtime
`0x1A7E2` in the font-pointer slot; its native operand reference provides the
canonical biased source anchor `0xA7E2`. It is not a PC-relative initializer.
The inspected string path zero-extends input and maps lowercase a..z to A..Z;
other control/high-byte bounds remain unresolved. All new font records retain
the conservative `data` role.

`app_text_plane_mask` at app byte `0x22D` is corroborated by 21 saved instruction
uses. The CPU glyph loop loads it once, consumes four successive low bits,
copies eight rows for selected planes and clears the other planes (row stride
160, plane stride 40). The blitter consumer also selects four planes but skips
unselected planes. Writers include descriptor byte 5, immediates and a frame
counter byte; no global upper-bit or colour/palette invariant is asserted.

The three named entries describe compact-string rendering, masked glyph copying
and incrementing the stored text origin. NUL stores the final A1 cursor. CR
advances the saved line origin by 1,280 bytes. Byte 1 increments the stored origin
by one byte and reloads A1 without consuming an operand; it leaves the separate
saved line origin unchanged. This distinction matters after prior glyphs have
advanced A1. A1..A3 are preserved by the glyph helper; D0..D2 are clobbered.
These are inspected contracts, not complete function-boundary/all-caller proofs.

Both stages pass full C and independent vasm equality. Final receipt:
`e4f55132e95d0e9a7ac7eb61e44556eea5eb64a601e46c677831259c9649d435`;
generated source SHA256:
`e2433a58cd3cd968538866a8727d1aedc6c3fcea9e5ee402cf000d8bb3e87326`.
Both histories preserve their earlier prefixes. The new conditional records add
3,032 bytes of reviewed data boundaries; this is not a recomputed native ownership
percentage. The pre-refusal coverage snapshot remains dated. No disputed
copied-code body, overlapping bank, audio stream grammar or alternate layout was
accepted as part of this slice.

## Bounded pitch and volume sequence records

Forty-seven independently reviewed actions describe two conservative `data`
layouts and 45 physical elements. The 13 reviewed pitch streams occupy
`0x4DE7E..0x4DEB0` (50 bytes), represented as byte arrays including their first
flagged byte. The consumer applies that byte's low seven bits to the note index,
then resets the next cursor to the selected start when bit 7 was set. Selectors
13..15 remain outside the reviewed table prefix; this does not establish invalid
input or the end of the complete table.

The 16 volume records occupy `0x4E9D6..0x4EAD6` (256 bytes), each with an unsigned
byte countdown-reload header and a byte-array body. Their first body bytes all
have bit 7 clear. Later flagged bytes hold the saved cursor and are reread on
eligible updates; their low seven bits supply the value scaled by master volume.
After initialization/reload, header values 1, 2 and 255 imply 2, 3 and 256 visits
to this update path between eligible reads, without a wall-clock timing claim.
The original NOP at `0x4EAD6..0x4EAD8` remains excluded.

All 83 newly inspected instructions (286 bytes) and the earlier 249 audio
instructions (956 bytes) match the original input. The signed selector-word
targets use the native PC-relative source anchor, without manual runtime-base
subtraction or fabricated relative-reference actions. Existing neighboring
layouts and all their elements/attributes are unchanged. Conditional consumer
bounds do not establish exclusive allocation, complete input coverage or memory
lifetime. Disputed copied code, its overlapping banks and alternate execution
remain unresolved.

Both dependent stages pass full C and independent vasm equality against all
376,832 original bytes. Final receipt:
`6a2b7d84d3aa66fa57343926d283e23e9da5e1105aaca079716536a534213ed5`;
generated source SHA256:
`88ebe7b17a8d3350357dae85d3bfd00f21819d2352aee3ccd99498160dde5a6c`.
Both existing histories retain their prior prefixes. The 306 newly structured
bytes are not a recomputed ownership percentage or a claim of full restoration.

The refreshed local package is
`.runtime-state/pandora-analysis/pandora-reviewed-text-and-audio.zip`. Its source
incorporates the narrow native refusal, font records and sequence layouts; both
C and vasm reproduce the complete original exactly. All 70 assets (175,072
bytes) and nine SDK includes are byte-identical to the previous reviewed package,
and all 80 source/asset/include manifest entries have matching sizes and hashes.
ZIP SHA256:
`730ccdfb11c2135fc052c3b70793771cbeea9fe223b92b89284ae14fbcbe0401`;
package manifest fingerprint:
`3edb6206d490bcc7c3b5a91084a05912f0ccf6b1b57f37e0c231c31077898102`.
These are different identities. The earlier ZIP and its receipts remain preserved.

```sh
.venv/bin/python -m amiga_reversing.tools.source_export \
  amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8 \
  --binary-assets --minimum-asset-size 128 --verify-package \
  --output .runtime-state/pandora-analysis/pandora-reviewed-text-and-audio.zip --json
```

## Audio command decoder and configuration cursor

Seven independently reviewed, journal-accepted catalog facts improve the decoder
through the existing framework.
Three handler names now describe their actual effects: command `83` enables
channel DMA and reloads duration; `85` sets the global note-offset byte; `8A`
stores a sign-extended operand byte in the newly named `audio_duration_multiplier`
word. The multiplier's consumer uses unsigned `MULU.W` and saves the low 16-bit
product, so neither positive values nor a real-time tempo rate is asserted.
Command `83` does not install a sample or clear the pending flag. The existing
silence handler's hardware writes remain conditional on its shadow-config flag.

The 48-byte channel structure gains only `channel_configuration_cursor_offset`,
a word at `0x0A`; all 22 previous fields and their attributes remain unchanged.
The configuration walker advances this byte offset by two, resetting the next
offset to two on a zero entry. The configuration-selection handler resets it to
zero. Complete configuration-list bounds and arbitrary-input safety are unknown.

A conservative `data` layout and 11-word array describe the physical dispatch
prefix `0x4DCE8..0x4DCFE` (22 bytes). The normal zero-extended byte decoder maps
conditional inputs `80..8A` to the 11 independently checked signed offsets and
accepted handler entries. Inputs `8B..9F`, a complete 32-word table and exclusive
allocation are not established. The mutable multiplier word at `0x4DCFE` is
excluded. The native indirect jump remains unresolved; no fabricated relative
references or register bindings were added. Eight already meaningful handler
names, neighboring layouts, disputed code and overlapping banks are preserved.

All 91 inspected instructions (340 bytes) match the original binary. Both
dependent stages reproduce the complete original with C and independent vasm.
Final receipt:
`9b785af8bae5901a731329b6290091db56bd980b57ab1a933afc603392ec5aaa`;
generated source SHA256:
`5ea74748e5d50cc51d615dd869ddf7a1de65125ee56c8d750204b56c2dc2cf59`.
Original output remains 376,832 bytes with SHA256 `70480017...`. Both histories
retain their earlier prefixes. Existing framework tests, gameplay observations
and the package at commit `61202504` retain their recorded scope and were reused;
the package was not regenerated for this semantic source slice. Copied-code
returns, temporal overwrites, late lineage and alternate execution remain open.

## Connected audio presets, configuration lists and programs

Ninety-six independently reviewed, journal-accepted facts connect the three
10-byte initialization presets to 12 zero-wrapped configuration lists (134
bytes), 32 logical program roots and 29 maximal physical program intervals (907
bytes). Three static immediate callers select presets 0, 1 and 2; this is
conditional source evidence, not complete caller coverage or runtime reachability.
Preset fields now distinguish configuration-list offsets from program offsets,
and expose the duration-multiplier and phase-increment bytes. Existing structure,
layout and field attributes are preserved except for the intended field names.

All 32 selected programs terminate in command `80`. Three shared-tail entries
remain visible at `0x4DFF6`, `0x4E03F` and `0x4E0BA`. Their containing programs
begin with `88 01`, which sets a per-channel note offset; entering the shared tail
skips that assignment and inherits state. Identical tails do not establish
identical execution. The single byte at `0x4E127` is excluded. Native indirect
dispatch remains unresolved; no fabricated relative references, register seeds
or copied-phase facts were introduced.

A four-byte layout names waveform direction and word-write offset at
`0x4DD10..0x4DD14`. From the original zero/zero state, a valid reviewed 64-byte
sample-7 pointer and only the inspected writer updates, offsets are even
`0..44`: an initial ascending pass followed by a `32..44` cycle. This conditional
relation does not establish actual initialization, complete writers or lifetime.
A separately inspected guarded sample initializer resets direction/offset to
zero/32 after filling the sample; that producer linkage remains the next connected
refinement rather than changing the original stored zero words.

The new physical layouts describe 1,045 bytes; including the existing 30-byte
preset records, this checkpoint connects 1,075 bytes. Neither count is a current
ownership percentage. Both dependent stages reproduce all 376,832 original bytes
with the C assembler and independent vasm. Final receipt:
`2ca4d0073643e30bc6608fab4b24d1f3b1ba02044c4d7a36f719c0fb38da0891`;
generated source SHA256:
`2e213f628357bbafc1c7f57f0b821cdb4c017377a860737c5ad2898b20a2701c`.
All 96 actions are accepted with that receipt, preserving both historical prefixes.
Existing framework tests, gameplay evidence and the package snapshot at
`61202504` retain their recorded scope and were reused. Disputed copied-code
bodies, overlapping banks, returns, temporal overwrites and late lineage remain
unresolved.

## Secondary audio envelopes, packed selectors and waveform producer

Sixteen independently reviewed and journal-accepted facts complete a connected
secondary audio slice. Seven elements refine the existing 120-byte layout without
changing its bounds, role, name or default unit: a separate four-byte sample-address
base and six marker-inclusive envelope streams (104 bytes), alongside the
unchanged six-word hex offset array. A negative envelope byte preserves the saved
pointer and previous volume; it does not apply the marker's low seven bits.
Reload interval H yields H eligible service visits (zero wraps through 256 byte
decrements), subject to duration and update-disable gates. This differs from the
primary volume player's H+1 countdown path and establishes no wall-clock rate.

Four name-only corrections distinguish paired 16-bit alternatives in existing
longword fields at offsets 4 and 10 of the 22-byte configuration and 38-byte
playback structures. ROR.B and conditional SWAP select a halfword; period addition
uses word arithmetic and sample addressing uses signed ADDA.W. Widths, types,
other fields, full bindings and all other attributes are preserved.

A conservative two-byte data layout at `0x4E68E..0x4E690` exposes the stored
high-byte voice selector and low-byte parameter selector. EXT.W followed by
unsigned MULU affects parameter indexing; unsigned physical byte rendering is
not a valid-input contract. The sole native caller at `0x4D33A` is in the disputed
helper region and supplies no accepted reachability or caller-domain proof.
There are no new interpreted relative references, register seeds or phase facts.

The sample initializer's guarded successful path fills 64 bytes, then stores
waveform direction/offset zero/32. Under a valid reviewed sample-7 pointer and only
the inspected updates, this begins a 12-state cycle with even offsets 32..44.
The original stored state remains zero/zero and adds transient offsets 0..30.
The revised writer comment connects these conditional producer/consumer facts;
actual initialization order, complete writers, copied phase and lifetime remain
unknown. The 120 current dispatcher instructions (420 bytes) and saved
producer/setter evidence match original bytes. No runtime observation was invented.

Both dependent stages rebuild all 376,832 original bytes exactly using C and
independent vasm. The rebuilt C output was independently byte-compared with the
original. Final receipt:
`c41caea3c0ff067fd3b1c411d8722ad7fdeba363ab6d60f5fa59306b3b7e1034`;
generated source SHA256:
`619e1212af81573144ad2040d279ed0dc441662a3a823c3a803a8a15f3dfbd75`.
The existing layout/type snapshots and both history prefixes are preserved.
This adds two physical bytes to the layout catalog and refines 108 existing bytes;
it is not a new ownership percentage. Package, framework-test and gameplay
results retain their earlier scope and were reused. The loopback service remains
available; no broad analyzer repair, emulator change or new input was required.

## Inventory, trading and panel selection

A connected non-audio checkpoint adds 171 independently reviewed and
journal-accepted facts through the existing catalog: two complete two-byte
record types, 80 new eight-byte data layouts, 81 four-entry structure bindings,
a typed panel-object pointer, a 15-byte pocket-restriction prefix and four
precise consumer contracts. The existing 114-word native name-offset table
retains its presentation and bounds. The
layouts add 655 source bytes; including the existing empty table and name-offset
layout, the connected source data totals 891 bytes. The four-byte application
slot is abstract state, not additional bytes in the source image. These counts
are not a refreshed native ownership percentage.

`inventory_item_slot` distinguishes the item ID and trade-value bytes;
`npc_trade_offer_entry` distinguishes the item ID and trade-threshold bytes.
The current/initial tables are supported by four-entry stride-two scans and
exact eight-byte reset copies. All 81 unique pointer identities (648 bytes)
come from original big-endian object fields, the current existing native copied
source view and fresh resident native row checks. Whole prefixes fit the source
view with no competing admissible identity or accepted code overlap. Native row
boundaries do not define record boundaries. The shared all-zero empty table uses
the inventory record representation while retaining its dual inventory/trade
use; all prior layout attributes, count/stride, name and representation are
preserved. Four inter-table gaps totaling 64 bytes remain excluded. This is
conditional source identity, not actual pointer execution, copy completion,
immutability or lifetime proof.

The matched-offer path requires its unsigned threshold to be below NPC item
state; an earlier fallback path is excluded from that predicate. Counteroffer
success chooses the smallest positive unsigned threshold-minus-value gap in
1..127, skips item IDs below two and keeps the first slot on ties. Four-entry
mutation searches can fall through after a failed match and write at table+8
(and read +9 on the offer path). The eight-byte read/reset prefix therefore does
not bound every mutation or make neighboring initial templates immutable.

The panel stores a candidate world-object pointer at application+0x358 before
collision/flag qualification. Nearby selection exchanges only an item-ID byte,
retaining the corresponding value byte. For W=((y-139) mod 65536)>>2, its byte
mask leaves D1.W=(W&FF00)|(W&6); only a zero high byte reduces this to offsets
0/2/4/6. The normal four rows 139/147/155/163 yield those offsets. Invalid cursor
states are not proven safe, and the nearby-panel exchange does not itself apply
the matched-offer threshold predicate. Existing object and application fields
and their attributes remain intact.

The name resolver masks an ID to seven bits and uses signed ADDA.W, while panel
refresh uses a word loaded into a pre-zeroed long register and unsigned ADD.L.
The existing 114-word physical prefix contains positive offsets 1..1137 from
the native `item_name_string_table` source anchor, so both agree for IDs 0..113.
Resolver IDs 114..127 and unmasked refresh IDs 114..255 remain outside that prefix.
Pocket restriction uses byte index ID>>3 and MSB-first bit (ID^7)&7; a set bit
blocks this pocket-exchange path and permits the timed too-large message. Its
15-byte physical prefix is conditional on the reviewed item-ID prefix; extra
bits 114..119 receive no valid-domain claim, and arbitrary byte IDs are unbounded.

The redundant generic HEX array annotation for the name-offset table was
rejected and withdrawn through one normal undo action because it hid useful
native string labels and symbolic offset expressions. Its bounds and consumer
contract remain supported. The original action, rejection and undo are preserved;
there are 173 appended action records and 171 active accepted facts. No renderer
or analyzer repair was introduced. A second-stage request with 53 redundant
evidence references was rejected before writing any action; an independently
reviewed 29-reference subset completed that stage.

Saved consumer packets match the original instruction bytes. Both dependent
stages and the final withdrawal checkpoint reproduce all 376,832 original bytes
with the C assembler and independent vasm, and the C outputs were independently
compared byte-for-byte. Final receipt:
`da68d63e91e30703b9e12343420df857b9670448adbff23c658985b471c01e87`;
generated source SHA256:
`747abefbb05bc1a77fdc4187d7bb3146442792d6b48957e07f7fb8fe6b0a3f9d`.
Both historical prefixes, all prior types, unaffected layouts, runtime references,
execution views, code-entry/register seeds and other semantic controls are
preserved. Existing framework tests and gameplay evidence retain their earlier
scope and were reused; no new runtime claim is made. No analyzer expansion,
backend rebuild, service restart or new input was required. Copy-helper returns,
temporal overwrites, late lineage, complete caller/state coverage and alternate
execution remain unresolved.

## Representative object-script programmer-source correction

A bounded source-quality pass replaces repetitive instruction narration in the
movement-flags, pointer-copy and six X/Y comparison handlers with concise names
and three command-specific operand layouts. `cmd_flags`, `cmd_copy` and `cmd_xy`
emit real RSRESET/RS declarations, and scoped typed input summaries render A4
operand fields, including the shared comparison tail. All known incoming tail
edges belong to the same comparison family. No command type is assigned to the
heterogeneous interpreter cursor. A5's existing object type and names remain
stable; the copy handler's final LEA length remains numeric.

The interpreter documentation now explains its object-script role, A4/A5 inputs,
word opcode and variable operand formats, stored continuation, delay countdown
and entry-only flag gate. One comparison-family comment explains unsigned
coordinate ordering and the signed displacement's command+6 base; the flags
handler retains its exceptional low-byte operand convention. The unknown flags
byte remains an explicit declaration gap. No gameplay motive, arbitrary pointer
validity, guaranteed loop termination or callee-effect contract is invented.
Other subsystems' comments and renderer-injected provenance remain outside this
representative correction; the entity preparation is preserved and unapplied.

The first exact-byte gate did not produce symbolic A4 operands. Its input
summaries were silently discarded because the existing command builder omitted
the required empty `results` list. Those ineffective actions were rejected and
retained in history, then replaced at the same canonical summary identities
through the corrected command. The producer repair adds only `results: []`; a
regression follows direct and callback-table catalog commands through Manual
Action projection into strict effective metadata with empty results and unknown
effects. There is no new renderer, LEA substitution or ABI machinery.

Independent final generated-source review checked all six comparison bodies and both tails,
the command fields, unchanged bare-indirect forms and unaffected source outside
the declarations, selected handlers/interpreter and dispatch references. The
corrected source reproduces all 376,832 original bytes with C and independent
vasm. Verification receipt: `e33fd57042d3807286a1938ef560539b879305722a19e81a3ef2f9f99421aaea`;
generated source SHA256: `f2838777d4157c2195525b832e8c58beede27100aaf1d76d4baa494480ccb367`.
All previous types, data bindings, register/code-entry seeds, runtime mappings
and history prefixes are preserved. The four focused catalog, effective
metadata, exact-addressing and function-fact suites pass: 126 tests. Ruff and
diff checks pass. The Python service was restarted to load the producer fix;
the native backend was unchanged. No new runtime execution claim is made.

## Entity animation and saved draw-state restoration

The next programmer-source batch connects animation updates, saved draw state,
background-tile restoration and current entity drawing. Shared comments explain
these purposes and the rectangle-union register contract instead of narrating
loads and stores. Concise routine names connect the phases; scoped input-only
summaries expose the existing state/descriptor fields in the generated bodies
without adding register-seed provenance comments. Both null-frame search and
attachment validity remain qualified in the evidence; later attachments do not
repeat the initial missing-saved-frame guard.

The descriptor's saved X/Y words fill its existing four-byte gap. Its world
array remains 22 records with stride 12; the player prefix widens from 8 to 12 bytes
without moving the state at offset 12 or changing its 30-byte extent. State pointers now
distinguish current and previous geometry while retaining the existing current
geometry binding and its collision variant. Animation nodes retain their 18-byte
basic extent: count and phase-step are bytes, index/phase remain a packed word,
mode flags and frame/XY sequence pointers have meaningful names, and byte +0xB
remains unknown. The conditional next-node pointer at+$12 is documented beyond
the basic record rather than silently expanding every record. The existing
47-entry frame-pointer array and its bindings remain unchanged.

The byte phase clock advances the index when its wrapped result is negative;
this is a bit7 test rather than carry or an asserted frame rate. End modes can
chain, hold the header or loop. Header-frame holding and later eligible XY
restoration have distinct timing, retained in sidecar evidence. Source review
also caught stale script comments that called held-header mode an active bit
and described only an index reset. Two shared node-selection/toggle contracts
now replace that wording; the redundant narrations were withdrawn through
normal undo, preserving historical evidence.

Independent review inspected the complete generated diff, actual node/sequence
records, symbolic geometry accesses, packed-byte expressions and all affected
consumer comments. Field/layout, typed-input and final consumer-documentation
checkpoints each reproduce all 376,832 original bytes with C and independent
vasm. Final receipt: `195e1f5f48c57d733c30c85e7902c6bb956b980d51d1d173651757bc4d4fc858`;
source SHA256: `ddbca66b055c06179eaae387d8b19047bb7320af23c7dda84ca02532c61e35e4`.
All unrelated types, data layouts, register/code-entry seeds, runtime references,
execution views and history prefixes are preserved. No analyzer/renderer
expansion, new input, native rebuild or runtime execution claim was needed.
Copied-code return lineage, temporal/late lineage, arbitrary pointer/chain
safety, complete sequence bounds and alternate placement remain unresolved.
The remaining script-handler presentation is a coherent quality pass; semantic
item IDs and then established constant domains take priority under the user's
expanded source-quality criterion.

## Semantic item IDs and source constants

Continuation checkpoint: 2026-10-13.

The original 114-word name prefix provides the item/name ID mapping. In
`death_fly_initial_inventory_slots`, the item bytes now name `ITEM_ID_DEATHSTING`,
`ITEM_ID_SUGAR_CUBE`, `ITEM_ID_ARAKNOID_EYE` and `ITEM_ID_EMPTY`. Each interleaved
`trade_value` remains numeric. ID zero points to an empty string and clears
slots/selections; ID one points to the padded `NOTHING` display name and is a
panel fallback for IDs below two. They are separate constants and meanings.

The scoped symbol path preserves the existing inventory/trade record types and
four-entry arrays. World-object selection and initial-selection bytes use the
same constants; the definition byte is a name-table selector and can name an
NPC rather than an inventory object. Existing role labels are preserved when
they differ from display names. Duplicate display identities 87, 91 and 93
remain numeric in those definition fields, with their ambiguity retained in
the evidence. The pointer-to-object table contains pointers rather than inline
fields and receives no such substitutions. IDs beyond the physical name prefix
remain unresolved.

Four additional proven code operands name Kriptonite, Bent coin, the NOTHING
display fallback and the Laser rifle range base. The latter still tests two
IDs, Laser rifle and Pulse cannon. In this batch, low-ID cutoffs, two-ID widths,
selection latches, register zero-extension, thresholds and unrelated equal
numerals stay numeric instead of receiving item-name symbols. Other established
domains can receive their own meaningful constants in later reviews. New source
names retain the original strings' spelling. Existing
item constants, name-offset expressions, type attributes, scalar overlays,
runtime identities, unknowns and historical action bytes remain intact.

This criterion applies to all established domains as each subsystem is reviewed:
IDs, opcodes, states, flags, masks and meaningful sizes. Bit indices used by
BTST/BSET/BCLR/BCHG must differ from masks used by AND/OR and stored flags.
Combination expressions must retain unknown residual bits and respect operand
width. At this item-ID checkpoint, native constant expressions supported
arithmetic, parentheses, left shifts and OR (`|`); prior full-source C/vasm gates
exercised emitted OR and shift expressions. Native `&`, complement `~`, XOR and right shift were then
unsupported. No Devpac compatibility is asserted. Width-bound clear masks can
use explicit supported subtraction such as `$FF-(MASK_A|MASK_B)` only with
bounded masks and exact independent proof.

A focused synthetic fixture now verifies that syntax with both assemblers:
ORI.B combines masks 1 and 8; ANDI.B uses the byte-clear value `$F6`; word/long
expressions preserve high literal bits and a byte expression retains unknown
bit `$40`. The framework and vasm match the full 56-byte HUNK, including the
independently checked 20-byte payload. SHA256:
`ac8abcd9000d956fef5aeda12b702653c879ee4cb61de8a83fda70c30997e760`.
Separate fixtures confirm native refusal of `MASK_A&MASK_B` and `~MASK_A`.
This is expression compatibility evidence, not a claim that target fields
automatically acquire such a domain or that all operand forms are covered.

Existing KB domains provide enums and OR flags; unknown residual bits cause
numeric fallback. Custom fields lack a domain property, target-local domains
are absent, and scoped `representation.symbol` accepts a named constant rather
than an arbitrary expression. These gaps do not block this item batch, which
uses the existing generic scoped path. A reusable field-domain path and validated
scoped expressions are candidates when the next subsystem needs them; none
should infer a domain merely from numerical equality. Native equate storage now
supports 512 distinct names. The catalog/redo path
checks the canonical candidate count, including generated reference equates,
against the native accessor before append; native parsing explicitly rejects
overflow. Updates of existing names remain valid at capacity. Focused fixtures
cover 512 names through C and vasm, a 513th-name refusal, duplicate updates,
atomic catalog rejection, generated equates and redo. The 14 reviewed mission
state, tile and event-bit constants use the existing scoped symbol path.
Proven record-size advances such as LEA's displacement need an appropriate
scoped displacement representation too; inventing an out-of-range struct field
solely to print a size name would encode the wrong fact.

Larger literal batches exposed repeated native navigation reads during command
validation. The small request-local reuse fix shares one snapshot only during
locked preparation, checks both projection and artifact identity, and clears
the snapshot before append/invalidation, including exception paths. Every
locator and selected element is still independently validated. The focused
batch/operation/projection gate passes 85 tests; the broader server gate passes
192 tests and retains the documented installed-inventory failure caused by the
missing Search for King manifest. No analyzer/renderer or native backend change
is involved.

All 81 inventory/trade bindings and the supported selection/name bytes in 35
inline object records are checked against the original binary. Every dependent
checkpoint passes full C and independent vasm reassembly; the final source
reproduces all 376,832 original bytes. Receipt:
`372a7d5736f59efa268303b0c5dd48deefa1e7b9e119f50c570ed4175730a725`;
source SHA256: `2367cb0c321e5a7cbf32e7adee80dbf6721efbdf0ade28ea051922688ad85436`.
The complete prior equate and representation entries are preserved, as are
unrelated metadata, record/layout attributes and history prefixes. Runtime
execution is not newly claimed by this static naming pass. The broader
opcode/state/flag/mask/size criterion is adopted, but its systematic application
and the reusable gaps above remain ongoing work rather than completed recovery.

## Native flag expressions and the next animation slice

Continuation checkpoint: 2026-10-13, after `61bd4659`.

The shared native constant parser now accepts bitwise AND (`&`) and unary
complement (`~`). Both operate on 32-bit values; byte/word clear masks should
explicitly retain their width, for example `($FF & ~MASK)`. The parser keeps its
existing arithmetic/shift ordering, inserts AND between shifts and OR, and
rejects negative or out-of-range left-shift counts. Unary negation uses unsigned
arithmetic before converting back, avoiding signed overflow in that touched
path. XOR, right shift, relocatable bitwise expressions and general arithmetic
overflow remain outside this extension.

Native and vasm have an existing precedence difference between arithmetic and
shifts/bitwise operators. Portable mixed expressions require explicit
parentheses; this extension does not silently redefine the previous grammar.
The focused parser suite passes 23 tests under undefined-behavior checking.
Fifteen permanent independent-oracle fixtures pass against the rebuilt
production backend, comparing complete HUNK output and independently expected
raw bytes. They cover byte/word/long data and immediates, complements, retained
unknown literal bits, high bits, shifts and parenthesized arithmetic. The native
suite retains its pre-existing Ancient unknown-payload identification failure,
also reproduced against the unchanged prior production backend.

Composite typed-field expressions are deferred for a specific transaction
boundary, described in [Proposal 014](../proposals/014-source-converging-manual-action-surface.md#deferred-scoped-constant-expressions).
Correct support needs candidate metadata projection before canonical history
append, width/value verification, lossless native storage and token-aware EQU
rename/removal. A server-only check would leave other producers unvalidated.
The existing canonical single-symbol representation remains suitable for the
observed animation records; no separate annotation store or target domain
registry is introduced.

The connected source slice names animation bit indices for hold-header (0),
skip-update (1), hold-at-end (2) and chain-at-end (3), plus the separately named
stored header-hold mask (1). Sixteen actual bit-operation operands and eighteen
typed mode bytes use those names. The six zero mode bytes remain numeric; no
combined animation flags are present in these records. Chain-at-end takes
priority over hold-at-end. End-hold selects the header frame immediately, with
optional header XY restoration on the next eligible held-header call. Existing
purpose-level routine comments remain intact. The unrelated script-search
state bit 3, phase arithmetic, unknown node byte and conditional extended-node
pointer remain distinct or unresolved.

`calculate_tilemap_buffer_offset` now uses `BITMAP_WORD_ALIGNMENT_MASK`, defined
as `($FF&~1)`, for its original ANDI.B immediate at source `$6DD0`. This clears
only bit 0 of the shifted X byte offset while preserving the upper register
byte; it does not promise aligned row offsets. It is a coordinate-alignment
mask, not an animation flag. No invented combination or blanket substitution
based on equal numbers is used.

The unchanged-source checkpoint with the rebuilt backend and both dependent
target stages pass complete C and independent vasm reproduction of all 376,832
original bytes. Final receipt:
`8428495754673fe51ca4a97b398f0a10b81a3d58781c5a82edfb04cccf27c80f`;
source SHA256: `69acf840c3f7bdab3cd66bd3841e359a0a6773a905c4c4b337378466fa952b0b`.
Independent review confirms that normalizing only the six EQU additions and
35 symbolic uses reproduces the entire `61bd4659` source. Existing EQU and
representation entries, all custom structures/layouts, the binary and both
history prefixes remain intact. All 41 actions are accepted through the normal
Decision Journal using the final receipt. The live native listing serves the
sixteen animation bit names, the alignment operand and stored hold-mask byte;
the restarted UI returns HTTP 200. No external hosting is enabled.
This is a bounded source-quality slice, not complete source recovery or a new
runtime behavior claim.

Reproduce the native build and permanent oracle fixtures from the repository:

```sh
make -j4
.venv/bin/python -m pytest -q tests/test_bitwise_expression_oracle.py
```

The loopback service was restarted once after the backend build, retaining
`http://127.0.0.1:8123/`. Native library aliases share SHA256
`d8ec03dc93150e0f1750b37081326f02db4be1b2fa1317041e681158a35f07ce`.

## Player movement, tile restrictions and camera handoff

Continuation checkpoint: 2026-10-13, after `7769dc98`.

This previously underdocumented gameplay path now distinguishes requested
motion, accepted requests and actual position updates. Word arithmetic scales
input X by seven and Y by four. Diagonal and zero requests take the idle path;
some state gates instead return without holding the node. Candidate bounds
combine object coordinates, animation offsets and current geometry. Horizontal
probes sample the chosen X edge at maximum Y minus four. Vertical probes sample
left plus three, midpoint and right minus four, using maximum Y minus three for
negative Y or maximum Y for positive Y. This is the inspected algorithm, not a
generic swept-rectangle collision guarantee.

The accepted request is saved separately for the selected-item effect ray.
On vertical movement the previous direction can request lateral drift: bit 2
adds seven, bit 3 subtracts seven and wins if both are set. Drift adjusts X and
suppresses Y commit. Otherwise the Y coordinate receives one map-height-times-16
wrap correction. The requested direction selects the animation node; only a
node change resets its packed index/phase. Idle or blocked movement holds the
header and clears skip-update. Scoped input facts expose existing object and
node fields at the actual established pointer points rather than asserting an
A4 object input before its LEA.

The renamed `test_msb_first_bitset_bit` is shared by all eight known item,
terminal and tile-mask callers. It preserves D0/D1, uses an unsigned word index
with MSB-first byte ordering and returns Z clear for a set bit; it checks no
table bound. The initialized selector/definition tables independently produce
475 distinct tile IDs with maximum 507, requiring the 64-byte physical movement
restriction prefix at source `$A822..$A862`. The adjacent overlay queue has its
own clear/read producers. Bits 508..511 retain unknown meaning. Dynamic or
arbitrary pointer-derived IDs, allocation ownership and copy/lifetime remain
unproven. Tile-cell lookup also retains its unchecked-coordinate and low-word
addition limits.

Named camera state connects movement's X/Y scroll requests to timed service and
redraw. One entry loads the byte countdown from the existing configuration
slot; another requests two service visits with zero deltas. Each eligible
service decrements the byte, advances/clamps Y and advances X while active, or
clears active state and deltas on expiry; both paths redraw. Zero countdown
wrap and arbitrary map/coordinate safety are not hidden by these names. The
configuration writer and complete callback/lifetime coverage remain unknown.

The original 272 movement instructions and their direct-helper evidence match
the binary. The first connected checkpoint adds 35 canonical facts and passes
full C and independent vasm reproduction of all 376,832 original bytes. Receipt:
`b2361742c4f45bf14b2aec879bdd511bbd03d9e12593e70dd14624e0e2c33cc7`;
source SHA256: `52ca2aa50f252f65bfd32b31a390e5565ab40e37269c2db8ce2b46cf6a2ccf06`.
All 35 actions are independently source-reviewed and accepted through the normal
Decision Journal with that receipt.
Prior structures, layouts, constants, native views and both historical prefixes
are preserved. No framework/backend change or new runtime claim is involved.

The idle pointer load at source `$998A` still has an incorrect inferred
geometry-field annotation. The following `$998C` clock reset now correctly names
the animation-node field. No safe per-instance override was found; removing the
shared geometry field would damage legitimate uses. Native interior-pointer
support already exists, so the current fact/anchor path needs diagnosis rather
than a claim that the architecture is absent. This remains a source-quality
blocker for complete recovery. Special tile-transfer roles and the positive-X
node's physical overlap with the player-state tail also remain explicit.

## Movement script and directional animation data

The connected data follow-through names and types the negative-X, positive-Y
and negative-Y animation headers and their physical frame-pointer prefixes.
Their 18-byte headers retain the established animation-node structure; the
pointer sequences contain eight, seven and seven longwords respectively,
including each held-header frame. These are bounded physical prefixes, not
proof of arbitrary sequence traversal, allocation or lifetime. The positive-X
header overlaps the existing player-state tail and remains deliberately
unreclassified until its dual role and phase ownership are resolved.

The 16-byte `player_movement_script_loop` now exposes its function-call, delay
and absolute-jump operands. Three opcode words use `WORLD_CMD_CALL_FUNCTION`,
`WORLD_CMD_SET_DELAY` and `WORLD_CMD_JUMP_ABSOLUTE`. Its delay word is mutable:
horizontal movement writes two, while vertical or idle movement writes one;
a blocked horizontal request can reach the idle overwrite. This is an
interpreter countdown operand, with no wall-clock or axis-selector claim.

The stored call pointer `$195E2` and self-jump pointer `$5C312` remain numeric.
Existing native copied-view facts identify source `$95E2` and `$4C312`, but the
current data-element reference producer and projection collapse encoded
runtime addresses with source offsets. The bounded extension required to
preserve both identities is recorded in Proposal 014; no target-specific base
subtraction or alternate mapping store was added.

The 64-byte tile restriction array exposed a metadata codec limit: its former
91-byte layout role became a seeded subtype with a 63-byte maximum. The failed
array fact was withdrawn normally, the empty layout replaced with the same
bounds/name/unit and a concise role, and the array rebound. All failed and
corrective records remain visible. A second supported metadata correction
removed redundant numeric formatting from the three opcode fields so their
symbol facts render, and retained the meaningful loop label. The binary style
currently renders only the first 16 restriction bytes; the full 64-byte
classification is bound, while the remaining bytes retain numeric hex output.
No framework change was made for this presentation limit.

Final whole-image C and independent vasm verification reproduces all 376,832
original bytes, with receipt
`e5f1c7be644fd9a35de603680839ab01c6ffbe2125cb1768a72925750545bd9a`
and source SHA256
`e12c74b7cacd49fec489a0d6fe7e5c0e5f48e058a1f8d59278668d64dd09b559`.
The seven new disjoint layouts describe 158 bytes. All 325 other pre-existing
layouts and all pre-existing structures, callable/input facts, application
slots and native views are unchanged. The sole old-layout replacement is the
documented tile-mask role correction. Both history prefixes and the original
binary are preserved; 36 new action records retain the failed attempt,
withdrawal and source-format corrections.

Independent review checks the complete rendered-source diff, all three opcode
symbols, the semantic loop anchor and both object script references. The normal
Decision Journal accepts the 34 eligible interpretation records against the
final receipt; the withdrawn failed array and its undo marker remain in history.
The live UI remains available at `http://127.0.0.1:8123/` without a backend
restart. Exact assembly and static consumer evidence do not establish emulator
execution or complete gameplay recovery.

## Rifle return assessment and local relocation boundary

The next bounded runtime slice reused the verified rifle checkpoint without
replaying acquisition. Decoded camera/script timing now fits seven neutral
transitions, the prior forward flight crossing (41 calls, bound 45), and all
45 positions of a reverse timing diagnostic (64 calls, bound 68). Horizontal
requests use delay two; vertical/idle use one. Camera bursts are charged once
per burst rather than at every move. This resolves the previous timing-model
blocker, subject to fixed profile and no new encounters/modal control.

It does not qualify the return. The diagnostic's final health check found HP44;
the stronger per-visit HP95 recipe stops at `reverse_34_up`. A normal prefix
probe stops before source `$887C` stores 44 over player HP95: the security
response subtracts 51 after failed held-ID clearance. Current zone is zero,
rifle18 fails, and carried Amy ID54 is outside accepted IDs48–53. Another valid
ID/trade is required; merely selecting Amy is insufficient. The intact rifle
checkpoint `(1228,874)` and healthy reverse staging `(1137,874)` remain reusable.
No successful return snapshot or aim/fire/hit is claimed. Further game quest
modeling is intentionally stopped for this two-byte relocation task.

A cheaper local CPU comparison binds the manifest and canonical checkpoint
donor, without editing guest state. The actual original/derived BYTE instruction
at source `$552F0` agrees for all 65,536 initial words, producing
`0x4000 | (input & 0xff)` with one byte write, equal registers/CCR/PC and preserved
guards. This models direct writer entry, not normal reachability. Whole-routine
comparison is refused: generated unsized bit-memory operands use longword reads
and writes despite the KB's existing byte rule; the observed BCLR footprint is
four bytes. No routine case is accepted. Proposal 044 records the upstream
binding/oracle work required before retrying; the native simulator is unchanged
and an independent machine68k oracle is unavailable.

Normal game writer coverage remains **two of three**; BYTE remains unobserved
in normal gameplay. Reproduction, expected partial-result exit2 and exact
evidence paths are in `docs/copperline-runtime.md`. This slice changes only
bounded tools/scenarios/evidence/docs/tests. Original binary SHA256 remains
`70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`,
and current rendered-source SHA256 remains
`b5c29658451d7a775aadc1cd574dcee25528bbe477362372b0fb47abfd1b913d`.
No source facts, generated target output, ROMs or guest snapshots are published.

Validation: **144 passed** across checkpoint/runtime/session, patrol/world/rifle
models and the new camera/local-CPU tests. The full 65,536-word CLI was rerun and
returned the expected exit2 with the routine-width refusal; its JSON matches the
published receipt. `git diff --check` passes. Original/source hashes were
rechecked; no output-affecting change requires new reassembly, so the previous
exact C/vasm receipt remains applicable. The listing UI responds HTTP200 on
`http://127.0.0.1:8123/`; no emulator process remains running.

## Generated bit-memory width binding repaired

The four-byte bit-memory blocker above is now fixed generally. The parser binds
the existing PDF-backed EA-category size rule into execution metadata; regenerated
form tables supply register/memory widths, and native reads/writes/EA updates and
bit flags consume that rule without requiring a decoded suffix. The obsolete
separate hardcoded bit-width choice is removed. Concrete bit predecrement now
uses the existing general pre-access helper. No Pandora CPU workaround or new
instruction facts were added.

The same provenance-bound full-routine comparison now accepts eight bounded
cases. Five modeled dead/armed cases execute the guard, reset helper, BYTE store
and return in 26 instructions per layout, with equal normalized CPU state/writes
and outputs `4040,4006,40ff,4055,40ff`. This is guarded local routine equivalence
under the existing generated CPU, not normal gameplay reachability or hardware
proof. The complete 65,536-word single-store result is unchanged and preserved.

One alive/near case still refuses its independent routine contract: concrete
SUBI data-register arithmetic uses the full register and leaves CCR unchanged,
so the BPL/NEG absolute-value path is wrong and volume 64 replaces expected 53.
Equal results across layouts do not discharge that defect. The partial CLI still
exits 2, now with `refused_local_routine_contract`; the historical width-refusal
receipt is retained alongside `pandora-volume-local-comparison-width-fixed.json`.
Proposal 044 records the new arithmetic gap and scope boundary. Clearance-ID
route expansion remains paused; no aim/fire/hit or normal BYTE success is claimed.

Validation: 176 focused tests and 32 abstract subtests pass; native simulator 29/29
(including 64 concrete bit combinations) pass. The full native suite retains its
two previously documented baseline failures; repository-wide style violations
remain in 24 unchanged files while all changed C/header/table files pass. Complete
rendered-source roundtrip is exact with zero differing ranges. Original/source
hashes and verified rifle checkpoint hashes remain unchanged. The rebuilt backend
is loaded by a restarted listing UI at `http://127.0.0.1:8123/`.

## Concrete SUBI width/CCR correction and bounded comparison completion

The preceding arithmetic refusal is now resolved in the general concrete ADD/SUB
path. A before/after minimal native regression reproduces word upper-bit
corruption and verifies D0 `$00070328` minus 840 becomes `$0007ffe0`, SR `$2019`.
The correction consumes existing width/CCR and source-extension metadata through
shared helpers, preserves narrow data destinations, and retains full-width
address arithmetic with unchanged SR. The boundary tests also expose a reversed
form's stale register-only access; general parser normalization and regenerated
KB execution bindings/simulator tables correct seven access entries across
ADD/AND/OR/SUB and PMOVE. No target-specific CPU workaround is used.

The same original/derived manifest/donor comparison now passes all nine bounded
routine cases and exits 0. The near-player call follows both negative-delta NEG
paths, returns in 21 instructions and writes 53 (`0035`); five modeled dead/armed
calls still execute the BYTE writer and return in 26 instructions per layout.
Normalized CPU states, control flow and writes agree. The complete 65,536-word
single-store result remains identical to earlier receipts. The new evidence is
`runtime/observations/pandora-volume-local-comparison-arithmetic-fixed.json`;
historical negative receipts are unchanged. This completes those local CPU
contracts, not normal gameplay BYTE reachability or arbitrary routine inputs.

Validation: 190 focused tests plus 1,004 subtests pass, native simulator 30/30
passes, and full-image rendered-source roundtrip is exact with zero differing
ranges. The full native run retains only its two documented baseline failures.
Changed C/header/table files pass style; no independent machine68k oracle is
available. Original/source, verified rifle snapshot and prior relocation evidence
remain intact. The service is restarted/reloaded for the new native backend.
Clearance gameplay remains paused; normal game writer coverage stays two of three.

## Whole-file reader review: palette, depth-sort scratch and ranged ammunition

Reviewed **P08–P11 and P20/P21: six accepted, zero rejected, zero deferred**.
The subsequent disposition of the other 42 reader proposals is recorded below.
P27/P28 mostly restate already documented behavior and are not counted as new discoveries. The reader's report
is a hypothesis source; current native locators, complete named xrefs, original
accesses and exact bytes were checked before the normal catalog actions.

Coordinates below are section-0 source offsets; the copied prefix's runtime
view adds `$10000`. No universal mapping or relocation safety is inferred.

| Source span | Accepted fact | Producers/consumers and limits |
|---|---|---|
| `$31AA..$322A` | `world_depth_sort_copy_scratch`, 32 descriptor pointers | `$849A` copies all 32 pointers before partitioning; a later call refreshes the scratch. This is mutable storage, not an immutable object inventory. |
| `$322A..$32AA` | `world_depth_sort_deferred_scratch`, capacity 32 descriptor pointers | `$84E0` appends the middle partition; `$84EA` consumes it backwards before sorting by descriptor WORD +6. The zero-middle case has no guard before predecrement, so the declared storage extent does not prove all-input bounds. |
| `$3462..$34C2` | `gameplay_palette_fractional_components`, 16 `rgb12_accumulator` records | Each six-byte record has red/green/blue WORD accumulators with four fractional bits. `$2614` unpacks nibbles shifted by four; add/subtract advance six bytes per color. |
| `$34C2..$34E2` | `gameplay_current_rgb12_palette`, 16 WORDs | Reset/fade helpers write it; Copper, cursor binding, health and inventory consume or modify it. It is not exclusively a world-only palette. |
| `$34E2..$3502` | `gameplay_palette_increment_rgb12`, 16 WORDs | `$7DD6` and `$A020` pass it as A1 with D7=15. Clear/add leave the input array unchanged in bounded tests; arbitrary later writers remain outside that claim. |
| `$924C..$9250` | `initial_ranged_weapon_ammunition` and `ranged_weapon_ammunition_remaining`, two bytes each | `$9F28` copies initial `5,1`; `$92AA/$92B6` selects and consumes one byte for item 18/19. These are consumable counts, not elapsed-tick cooldowns. The two obsolete cooldown layout owners were replaced through catalog remove/create/set actions. |
| `$9250` | `service_selected_ranged_weapon_fire` | Replaces the misleading `update_active_world_object_positions` source name. Fire-edge/held-fire, UI/object guards, zero ammunition, ray collision and damage uses establish the service role. No arbitrary ray-termination guarantee is added. |

The palette's prepared A1 input at `$77FE0..$78000` still aliases the final
32 bytes of hit-snapshot storage. These typed source regions do not establish
exclusive contents, phase separation, interrupt atomicity, allocation or DMA
lifetimes. The normal source now expresses the storage and references; no
new runtime memory-region/relocation ownership claims were added.

Validation: **44 focused tests pass**, including 12 new bounded original-CPU
cases for palette clear/add/unpack extents and values, scratch refresh and
partition behavior, empty-middle entry state, ammunition initialization,
new/held/released fire, empty counts and unsupported selected items. The sort
checks explicitly split at `$84BC/$84BE`: the existing simulator produces D5
`$000000FF` for original bytes `7AFF` (`MOVEQ #-1,D5`), whereas the PDF-backed
MOVEQ description in `knowledge/m68k_instructions.json` (page 238) specifies
sign extension to `$FFFFFFFF`. The suffix therefore takes that architectural
D5 value as an explicit modeled entry condition. This is not complete
whole-routine execution or a fix to the simulator. The general follow-up is to
consume the existing signed-immediate KB semantics in execution; do not patch
the target or special-case Pandora. No independent CPU oracle was installed.

```sh
.venv/bin/python -m pytest -q tests/test_pandora_palette_sort_ammunition.py tests/test_pandora_framebuffer_lifetime.py tests/test_pandora_world_model.py
```

The 23 catalog actions are accepted in the Decision Journal using exact receipt
`5763b6810d0d7f55808d6e50dbd85d6d633ca498711ea5a18fa670278ceea8ff`.
C and independent vasm reproduce all 376,832 bytes with original SHA256
`70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`;
rendered-source SHA256 is
`60597d4fd583a59cc247fdd6cd5c4dc7ab5979894c566795aa357fe00c626af7`.
Original assets/SDK files, previous unrelated facts and history prefixes remain
unchanged. The canonical `.s` was regenerated, never hand-edited. No framework
implementation changed, no broad migration was attempted, and PR 5 remains draft.

## Remaining whole-file proposal queue

The queue's per-proposal dispositions, unapplied components and exact receipts
are in `docs/validation/pandora-whole-file-queue-review.json`. Naming established
behavior is counted separately from newly recovered durable roles/types.

| Checkpoint | Reviewed proposals | Concrete result | Applicable verification |
|---|---|---|---|
| Frame/render | P01–P07, P12–P18, A01–A04 | 15 function symbols, four exact-width ticker/tile-grid app roles, two entry-only A5 overlay-descriptor types; no full blitter register/DMA contract or unused flag equates | 31 overlay/framebuffer tests; all 376,832 bytes exact with C/vasm; receipt `eb91ecd72b044faceceae766874e033a98b4aeca03e55bf73110d461987e5dbb` |
| Security/status | P19, P22–P26, A05–A14 | Six function symbols, three damage/clearance table names, ten app roles; deposit reset spans 64 bytes but insertion can reach adjacent +$31A; status duration counts space runs plus one nonspace presence, not characters/ordinary words | 12 new status/deposit tests; earlier fire-edge evidence reused; C/vasm exact; receipt `74f57913663fe635ffaaa39f5cdf90acaa2ebc9755f0ada9c6e6ad5b5dd6d28a` |
| Audio/closeout | P27–P34 | Eleven explicit signed handler references; eight shared three-byte offset commands; corrected packed-selector bytes; two mutable shift WORDs. P27 is naming formalization; P28/P34 already known; P29 selector-only restyling rejected; P33 noise/PRNG purpose not asserted | Eight original command/add-byte cases; all11 rendered references checked; C/vasm exact; receipt `8468e10602be39da44d6c5e5e8f1d5aadbad892da268de81768da64dd7082f40` |

All **42 remaining entries are dispositioned: 39 accepted wholly/partly, one
rejected, two already known with no change; no pending entries**. Together with
the initial six, this is 45 accepted proposals, not 45 new discoveries. The
three checkpoints append 78 accepted actions. Applicable runs pass 31 frame/UI,
12 status/deposit and eight audio cases; prior palette/ammunition evidence is
reused. Original binary/assets/SDK and unrelated facts/history remain intact.
Final rendered-source SHA256:
`e53a9c87ec70b043cb43f3d2823cd257c81bbb7c230719cd83ac2735785ccc7b`.

Genuine gaps remain the overlapping node view, unchecked array/selector paths,
full blitter/register/callback contracts, and asynchronous snapshot/framebuffer
lifetimes; shift-state noise purpose is unproved. Recommended next restoration
step: resume reachable capture/consume/reuse caller sequencing with the preserved
render-order investigation, resolving general KB-driven MOVEQ sign extension
before relying on affected CPU traces. Source `$938E` remains numeric across
unknown memory effects. No framework implementation or original instruction
bytes changed, and publication stays on draft PR 5 without merging.


## MOVEQ correction and snapshot sequencing follow-up

The earlier `$84BC` limitation is resolved. The KB already describes a signed
8-bit immediate and a long destination; generated operand metadata now carries
that encoded signed width into both abstract and concrete execution. No
mnemonic-specific rule, KB assertion or target-byte patch was needed. The sort
tests execute the original `MOVEQ #-1,D5` rather than injecting its result.
The historical split-test account above records the earlier checkpoint only.

Focused simulator/generator/arithmetic/abstract checks pass **49 tests and 1004
subtests**, including 4096 exhaustive MOVEQ register/byte/CCR combinations and
five abstract boundary cases. The final combined Pandora palette/sort/ammunition, overlay, framebuffer and
render-order run passes **47 tests**. Four original-CPU rendering order cases
pass in `tests/test_pandora_render_order.py`:

- Direct enqueue waits before capture and clear packets; CPU border/title and
  ready marking proceed without a further software completion poll.
- Original combat entry `$7792..$77B8`, with inventory closed, queues the
  opponent panel then captures the hit background at `$77D00` before its clear.
- Inventory close interior `$27AE` directly restores the body snapshot from
  `$7F0` with either value of the saved flag, an empty queue and NULL callback;
  the nearby panel subsequently waits before its clear. This is a conditional
  interior-path proof, not execution of the entire inventory close routine.

Current native named references identify direct restore callers at `$0720`,
`$27C0` and `$7A8E`, capture at `$66BE`, and border/clear at `$66C6/$66C2`.
The queue processor has no named direct references. That absence and initial
NULL callback values do not establish that it is unreachable or unused.

The tests explicitly supply INTREQR bit 6 between packets: the MMIO shadow
neither performs DMA nor clears its request register when INTREQ is written.
Consequently CPU flag clearing, ready marking and return do not certify DMA
consumption; observed CPU sequencing does not demonstrate a real hardware race.
Cold-start reachability, bus arbitration, snapshot reuse phases and the overlap
between hit snapshot tail `$77FE0..$78000` and palette input remain unresolved.
No new ownership or relocation permission follows from these tests.

Reproduction after `make -j4`:

```sh
.venv/bin/python -m pytest -q src/tests/test_m68k_simulator_moveq.py src/tests/test_generate_c99_simulator_subset.py src/tests/test_m68k_simulator_arithmetic.py src/tests/test_m68k_simulator_abstract.py
.venv/bin/python -m pytest -q tests/test_pandora_palette_sort_ammunition.py tests/test_pandora_render_order.py tests/test_pandora_framebuffer_lifetime.py tests/test_pandora_overlay_pipeline.py
```

The native suite reports 807 passing and the same two pre-existing failures:
`facts_v2_render_asm_source_propagates_pointer_table_pointee_type` and
`decompression_identify_reports_unknown_payload_without_failure`. Changed C
files pass the repository style check. Exact C/vasm receipt
`427ef725d9a438c6d4c8824cd6f97034b5e30491df15dc533ea35e6eb0241561`
reproduces all 376,832 original bytes. Source SHA256 remains
`e53a9c87ec70b043cb43f3d2823cd257c81bbb7c230719cd83ac2735785ccc7b`.
No target facts or generated assembly changed in this follow-up.

## Conditional snapshot lifecycle contracts

The connected caller/packet model is recorded in
`docs/validation/pandora-snapshot-lifecycle.json`. Four accepted catalog comments
at `$27C0`, `$6400`, `$66C2` and `$7A8E` now carry the timing semantics into the
normal source. They supplement existing field types and extents; no new memory
ownership or relocation declarations were created.

| Phase | Required ordering and meaning |
| --- | --- |
| Capture pending | Enqueue sets SAVED before calling capture. That flag does not certify completed pixels. Capture waits/acks the previous BLIT request, then starts its snapshot write. |
| Capture completed, overlay drawn | The immediately following clear waits/acks capture completion before starting its own DMA. CPU border/text and READY follow without a post-clear software poll. |
| Restore pending | Restore waits/acks the preceding packet, starts snapshot-to-screen DMA, then clears SAVED/READY and returns. The snapshot may still be a DMA source. |
| Next packet reuse | Another capture/clear/restore waits before starting its DMA, fencing the preceding packet under the normal serialized completion-request protocol. This is not an arbitrary CPU-write fence. |
| Warm restart | `$456/$45C` explicitly waits for DMACONR.BBUSY to clear before setup/title reuse. |

For body inventory, opening requires a nearby object, the collision-bounds guard
and its dead/object flag before `$2750` enters the body panel. Body capture is
queued first, followed by backpack and pocket panels. Close uses the nearby-object
inventory UI flag to select direct restore at `$27C0`; it does not test SAVED or
queue membership. The next nearby-character clear waits for restore completion.

For hit feedback, `$2F52` enters combat after the player/nearby-object/range/trade
guards. Entry closes an active inventory, queues the opponent panel, then captures
the hit background. Normal combat exit redraws nearby distance then restores the
hit snapshot at `$7A8E`; self-destruct expiry has another guarded restore at
`$0720`. A subsequent combat entry recaptures through bit 6 even if the descriptor
was already registered. The content lifetime therefore follows capture calls,
not registration lifetime or an immutable initial background.

These fences assume an enabled, single serialized blitter and a completion token
that has not been synthesized, consumed or made stale by another path. Setup
clears interrupt enables then enables master/VERTB/COPER, leaving BLIT disabled;
the level-3 handler nevertheless samples raw requests. The frame-completion latch
is not a blitter fence. Static caller edges and CPU prefixes alone do not prove gameplay reachability;
the runtime observation below now witnesses the hit capture/restore portion.

Remaining gaps are explicit: the hit-tail palette reader's indirect/stack entry
and phase exclusion, all alias writers, low body-storage allocation, and actual
CPU-versus-DMA ordering at the unfenced border/text boundary. No relocation
safety is inferred. The smallest remaining gameplay step is to capture the inventory-toggle guard
inputs at `$2736/$2748/$274A`, rather than assuming the post-combat body is still
the nearest object and within collision bounds.


The bounded original Copperline replay now witnesses hit capture, six Feed hits,
combat-exit direct restore and return to gameplay. Flags progress `$60` at capture,
`$E0` when the overlay is ready, and `$40` after restore. Numeric-offset
`custom.read` reports BBUSY clear and BLIT request set at the sampled post-capture,
post-clear and post-restore stops, with BLITHOG enabled and BLIT interrupt disabled.
This is observed completion by those stops, not an all-path bus-timing guarantee.
The first 64 and final 32 snapshot bytes change at capture and retain identical
hashes through overlay readiness, restore call and return; this samples 96 of
768 bytes and does not prove full-buffer exclusivity.
Correction: the next key64 attempt watches `$27E0`, a trade-announcement
instruction, rather than canonical body entry `$27EA`. Its timeout is invalid
negative body-entry evidence; downstream scripted body phases never run. Second combat recapture and palette-tail
phase exclusion remain unobserved. The compact receipt preserves this partial
outcome without publishing guest snapshots or retaining a full instruction trace.

The only support change lets scenario captures use Copperline's documented even
custom-register offsets below `$200`, retaining the sixteen-register bound.
Named DMACONR queries were refused, and debugger memory reads returned `FFFF`;
neither was used as hardware-status evidence. The combined focused suite passes
**103 tests**. C and vasm reproduce all **376,832 original bytes**, receipt
`9857609c4a334a758748c7c7c610ac05cae8001392542f0eb7ccddb724e5cdfa`;
source SHA256 is
`50610e260dbfc17f60c8f4f8a4f216b20543e8221de4924bf3e43f0ab6678ddb`.
All 78 packaged asset/include identities and previous history prefixes remain
intact. Four comments were added through catalog actions and accepted after
verification; the generated source was never hand-edited.

## Body-open guards and shared-tail control-flow follow-up

The saved post-Feed-combat execution now provides a measured inventory predicate,
rather than an assumed proximity condition. At `$2736`, nearest object is Feed
`$5C1D2`, flags `$66` include bit 1, and player XY is `(829,182)`. At `$26A4`,
the original pointer chain is descriptor `$5C2BE` -> state `$5C226` -> geometry
`$5C240`. Its current origin is `(832,168)` with extent `(64,32)` and zero state
and geometry offsets. The tested player point is `(845,213)`: X passes, while
`213 < 200` fails. That branch result follows from captured inputs and the
original tested predicate; the probe stops before the comparisons. These inputs predict a failed body guard. Independently, the historical
15-second probe used trade instruction `$27E0`, not canonical body entry `$27EA`;
its negative body-entry inference is withdrawn.

The original predicate at `$268E` preserves D0-D2/A0-A2, binds A4 to the player,
and sets carry only for a point strictly inside unsigned WORD bounds after
wrapping additions. Boundary equality fails. Four hypothetical upward commits would place the point at `(845,197)`, inside
the captured rectangle, but the first commit is not observed within ten seconds
and the original terrain model rejects up there. A bounded local terrain plan
then matches all 18 measured commits to `(822,146)`, point `(838,177)`. The
corrected body probe uses the canonical `$27EA` entry.

The shared-tail investigation also corrects an implicit control-flow assumption.
At `$71A2`, the palette return helper pushes a long pointer, advances SP by six,
then executes RTS. For a pre-BSR stack S, this returns with SP=S+2 and builds PC
from the BSR return's low WORD followed by WORD(S). At the four original sites
`$71E0/$71EE/$7220/$7230`, the resulting 24-bit target has high byte
`E2/F0/22/34`, outside the verified copied payload. The focused tests execute
BSR and the helper only, with modeled stack words, and stop before fetching the
computed target. No crash, intended purpose or wrapper unreachability is claimed.

Crucially, fade-out entry `$7216` unpacks the palette input at `$77FE0` **before**
its stack-splicing helper call at `$7220`. Thus even this control-flow limitation
does not prove hit-tail lifetime exclusion. Native direct-reference queries find
no named callers for either wrapper; constructed/indirect entries remain open.
Unchanged snapshot hashes cannot exclude palette reads. Ordinary balanced-call
fallthrough into the later fade loops must not be assumed.

Three new catalog comments at `$268E/$71A2/$7216` express these arithmetic and
temporal facts alongside existing types. Seventeen original-CPU geometry/stack
cases and the earlier applicable suites pass: **120 tests** total. C and vasm
reproduce all 376,832 original bytes, receipt
`825c8bc771a13ebb4f8692ba016da3866f183f8d017c92a5830d23ce414c0461`;
source SHA256 is
`842aebbab8d5a2d7b48c07da99e1cb0b9f7adb57a328ce97cd313d38f4d6f6de`.


The corrected original Copperline probe completes **all 37 source-row phases**:
18 individually checked movement commits reach `(822,146)`; body-open `$27EA`,
capture, close/direct restore, reopen and second capture into `$7F0` all occur.
The native branch reference, rather than a guessed address, identifies the entry.
A verified successor checkpoint is saved privately, linked to the normal Feed
root. No predicate, pointer, input cache or game storage was patched.

Both captures reach original BLTSIZE with A0=`$75518`, A1=`$7F0` and D1 low WORD
`$3006`: 192 packed rows of six WORDs, or 2,304 bytes. BLIT request is clear before
each capture and set at the first post-start stop; BBUSY is clear there. Body
flags progress `$40->$60->$E0->$40->$60->$E0` across capture/restore/recapture.
The six sampled chunks (384 of 2,304 bytes) change on first capture, stay stable
through restore and are identical after second capture. The second invocation
and completion are observed even though these sampled pixels match. Logical
flags remain distinct from completion guarantees, and no full-buffer exclusivity
or general bus-timing guarantee follows.

The resulting contract is conditional but reachable: open captures the current
background, close consumes it through direct restore, and reopen reacquires the
same storage via a new capture. Second **hit-family** capture, shared-tail palette
entry/exclusion, all alias/interrupt consumers and allocation remain open. The
fade-out's first shared-tail read cannot be dismissed on account of its later
stack behavior. Evidence and reproduction are in
`runtime/observations/pandora-snapshot-body-guards.json` and
`docs/copperline-runtime.md`. Original bytes, asset/include identities and prior
history prefixes remain preserved; publication stays on draft PR 5.

## Shared-tail access map and priority checkpoint

The current native inventory is reproducible with
`.venv/bin/python -m amiga_reversing.tools.pandora_shared_tail_inventory /tmp/pandora-shared-tail-native.json`
against the ready resident server. It enumerates **2,690 typed pointer fields**;
only the initialized hit descriptor's bitmap field targets the hit region.
There are 90 overlay pointer fields, ten bitmap fields (eight NULL, hit and body),
and two resolved bitmap consumers at `$633E/$63A6`. The native instruction-region
report has three roots and **three open obligations**. These roots include an
unused A4 setup and return/frame refusals; they are not three confirmed data
accesses. No obligation was cleared by adding comments.

`docs/validation/pandora-shared-tail-contract.json` records the known accesses,
conditions and phase edges; `pandora-shared-tail-native.json` preserves the native
snapshot. All intervals below are runtime, end exclusive.

| Producer/consumer | Shared-tail relationship | Required scope/ordering |
| --- | --- | --- |
| Direct-payload bootstrap load `$20000..$7C000` | Writes the tail as original input bytes | Earlier full handoff verification; original disk-loader parity remains unproved. Native prefix copy ends at `$75370` and excludes the tail. |
| Hit capture / restore `$77D00..$78000` | Capture writes and restore reads the entire tail | Initialized descriptor and ascending area mode. Known packet waits/acknowledgements order DMA; UI flags do not establish ownership. |
| Seeded reset copy | A reads `$70000..$7CD00`; D writes `$70028..$7CD28`, covering the tail in both | Ascending area mode, inherited BLTCON1; calls at `$F90/$546`; no final software wait. |
| Add `$71E8`, unpack `$721A`, subtract `$722A` | Each can read exactly `$77FE0..$78000` | Prepare binds A1 and D7=15. Unpack precedes the first escaped transfer; add/subtract require entry beyond an earlier spliced return. |
| Clear `$71DA` | No A1 input read | Writes 32 palette and 96 accumulator bytes at separate constant outputs, plus its stack spill. |
| Prime completion copy | Only `$77D00..$77D02` | Does not touch the tail. |
| Initialized display / UI rectangles | Their known bounded extents exclude the tail | This does not close unchecked/changed geometry or synthesized-address writes. |

The ten named palette-helper call sites are fully enumerated. Three potential
shared-input read sites remain; the other add bindings use `$10AE8`, `$10B68` or
`$134E2`, and clear never reads A1. In the render wrapper's ordinary prefix,
`D7=$7D22` is overwritten with 15 before use, A4=`$77FDE` is not dereferenced, and
stack arguments are discarded without an I/O call. The filename/count/pointer
combination therefore does not establish an executed loader or a 32,034-byte
allocation. The first palette call is clear, then the splicing helper leaves the
verified copied view before ordinary add-loop fallthrough.

Fade-out is different: its first unpack reads all 32 shared bytes and writes the
palette/accumulators before the spliced return. A bounded original-CPU prefix test
confirms that sequence. The modeled cases at all four direct helper sites, together with the original
stack operations, bound return targets independently of the following stack WORD. No escaped target is fetched;
no crash or wrapper unreachability is inferred.

Absolute caller SP remains unknown on the unconnected palette entry. Ordinary
palette spills occupy 16 bytes below clear's entry SP, 20 below unpack's, and up
to 52 below add/subtract's including the nested color helper, before caller/IRQ
frames. These possible aliases must be separated from the tail before claiming a
complete non-write contract. This is one reason the native frame obligations stay
open; unchanged snapshot samples cannot exclude reads or unknown frame aliases.

Validation passes **49 focused tests with one strict expected failure**. The new
rendering-prefix case exposes original `4267` (`CLR.W -(A7)`) writing at SP without
predecrement in the concrete simulator: SP `$9000` stays unchanged and WORD `$9000`
is cleared instead of WORD `$8FFE`. Its whole-prefix trace is excluded as proof;
the fade-out prefix and direct helper cases do not execute that instruction.
The general CLR defect is recorded for a separate tooling slice, not patched here.
Five catalog annotations are accepted. C and vasm reproduce all 376,832 bytes,
receipt `2b9309586da1e127a81e515c9892e7b33bb4fddaa4ffea8aab42d7fea78c7b1a`;
source SHA256 is
`1e46cd360d01afedb36021a834196206150d5d5ebe70aa720d502a99b02dc5cd`.
No new Copperline probe, memory allocation or relocation change was made.

Recommendation: return to broader object-state/animation and selector/scan
semantic restoration through native gaps. Keep this alias as a relocation
blocker. Further gameplay-route probing is low value until a concrete loader,
indirect caller or callback connects the palette prefix to a known phase. That
edge, absolute stack separation, all alias/interrupt consumers and general DMA
arbitration remain unresolved; second hit-family capture is also unobserved.
Fix CLR predecrement separately before relying on affected full-stack traces.

## Terminal location messages and card display selector

The next whole-program batch follows the terminal consumer through its complete
initialized data family, rather than treating default function IDs as a coverage
metric. Ten records at source `$8D54..$8FF1` contain a shared four-byte WORD X/Y
header followed immediately by variable ASCII/CR/NUL text. Three shared schemas
express the header, mapped-source message reference and mapped-source label
reference. Seventeen new disjoint layouts describe 730 bytes: ten message
records (664 bytes), five clearance strings (30), the eight-pointer display
selector (32), and the adjacent message-table NULL (4). The existing 40-byte
message-pointer layout keeps its identity and bounds. All eighteen pointer
entries now resolve symbolically through native source mapping; no manually
subtracted reference facts were added. Alignment bytes remain raw.

The original scan `$9140..$917A` terminates at NULL, not after ten records. It
subtracts, takes signed absolute values, and sums in WORD arithmetic; strict
unsigned improvement retains the first tie. An update puts the inline text
address (record +4) in A2. Its initial fallback is the first record's base, so
empty or malformed tables do not have a validated text-pointer result. The
physical table extent is not an admission guard. Focused execution includes an
explicit changed-data model with an eleventh record and a new sentinel, stopping
before display; this does not modify the original image.

The byte normalization at `$90F0` admits exactly item IDs 48..55 to the eight
clearance-label pointers at `$91CC..$91EC`. Their labels are Omega, Pi, Alpha,
Pi, None, Delta, None, None. This makes the already documented distinction from
the six-entry security table explicit in source structure; display membership
does not establish authorization. A scoped A1 header seed follows the nonnull
record load, and comments preserve the scan/selector algorithm contracts.

Reproduction, with the resident restoration service on localhost:8123:

```sh
.venv/bin/python -m pytest -q tests/test_pandora_terminal_messages.py tests/test_pandora_state_transitions.py tests/test_pandora_status_roles.py tests/test_pandora_snapshot_guards.py
.venv/bin/python -m amiga_reversing.tools.pandora_terminal_message_inventory docs/validation/pandora-terminal-messages.json
```

The combined original-CPU checks pass **49 tests with one strict expected
failure**, including fifteen new cases covering all ten locations, first ties,
WORD-distance overflow, sentinel extension, every byte item ID and all eight
label selectors. The existing `CLR.W -(A7)` predecrement failure remains
excluded as trace evidence; this terminal batch does not execute it. No general
simulator implementation or Copperline runtime route changed.

Broader gaps remain the overlapping positive-X node/player-tail view, unchecked
deposit/audio/other selector paths, source `$938E` across unknown helper memory
effects, mutable callbacks and saved-state validity, and asynchronous lifetimes.
The `$77FE0..$78000` shared hit/palette tail and its three native pointer/frame
obligations remain an explicit relocation blocker. No runtime allocation,
exclusive ownership, whole-file restoration percentage, or complete-game proof
is inferred from this batch. Function-candidate `loc_` IDs can survive accepted
source renames and must not be counted as unnamed semantic functions.

All 51 catalog actions are accepted in three verified stages. Final exact receipt:
`32f07b7e004b58fa843e32e809daa61a4b8eeac7ea3b51547e1c327fb0601acf`;
rendered-source SHA256:
`edc1838b6ece057f8823b9b11d387f7e4ae1f43229b26a14615f075336000133`.
C and independent vasm reproduce all 376,832 original bytes. The generated scan
identifies both postincrement reads as header `world_x` and `world_y`. The
read-only inventory is `docs/validation/pandora-terminal-messages.json`.
Original binary and all 78 packaged asset/include identities remain unchanged;
previous manual-action and decision-journal bytes remain intact as prefixes.

## World proximity scan and initialized pointer propagation

This connected follow-up distinguishes the scan's observed selection behavior
from a mathematical nearest-object reduction. At `$836A`, a newly selected
object overwrites D0 (the distance threshold) with its context cooldown and then
decrements nonzero values. If the optional message path is skipped, later objects
compare their WORD distance with that value. A zero cooldown then freezes selection;
a larger one can admit a farther object. An unchanged stored pointer bypasses
that overwrite and retains the distance threshold. Equal-distance ordering is
therefore conditional, unlike the terminal message scan's first-tie rule.
The optional enqueue saves only A0-A3; its spacing/duration computation overwrites
D0 again, so the cooldown-derived threshold is not a full-callback invariant.
Original instruction bytes and game behavior are unchanged.

The scan sets the per-object improvement bit on each admitted object and does
not clear earlier admissions retroactively. A separate first-context-visit bit
is set before inactive-object and NULL-message guards; it does not mean a
message was queued. Shared app bits distinguish changed-context refresh,
no-candidate admission and an empty-prompt display latch. These roles now have
symbolic bit indices at their original consumers. The no-candidate prefix
leaves the cached pointer/distance untouched; its downstream prompt service is
separate. Player descriptor XY synchronization happens before self-exclusion.
Subtraction, absolute value and addition retain WORD wrap, including a modeled
zero-distance wrap case. The pointer walk still uses NULL, without a physical
prefix count guard.

Two mapped-source reference schemas replace the address-domain ambiguity in
existing object/descriptor prefixes. This reuses their durable layout identities
and bounds: `$300A..$309A` has 35 object pointers and a NULL (the interior static
suffix starts at `$300E`); `$309A..$310E` has 29 descriptor pointers; and
`$310E..$318E` has 32 sort-source descriptor pointers. The latter two are distinct
physical prefixes inside the existing owner. Pointer counts are initialized
reference populations, not new object discoveries, runtime admission guarantees,
unique-object counts or ownership/lifetime proofs. Adjacent scratch and scalar
facts remain intact. The read-only native collector is
`amiga_reversing.tools.pandora_world_pointer_inventory`.

```sh
.venv/bin/python -m pytest -q tests/test_pandora_proximity_scan.py tests/test_pandora_terminal_messages.py tests/test_pandora_state_transitions.py tests/test_pandora_status_roles.py
.venv/bin/python -m amiga_reversing.tools.pandora_world_pointer_inventory docs/validation/pandora-world-pointers.json
```

The combined run passes **43 tests**, including twelve new bounded scan cases.
The tests use explicitly modeled table contents for candidate-order cases and
stop at `$83AE` before sorting, active-chain processing, interaction callbacks
or prompt rendering. They do not execute the known CLR predecrement defect.
The original input hash is checked by the fixture. No new Copperline probe,
framework implementation change or shared-tail relocation claim is involved.
The simulator/Copperline distinction and installed release provenance are also
recorded in `docs/copperline-runtime.md`.

The three stages append **28 accepted actions** (including two final comment
qualifications for the optional queue's D0 clobber). Final C/vasm exact receipt:
`934aeef23757132a548ba6503edf9768684e0170027e2f18d6e26c9927cd53a6`;
rendered-source SHA256:
`862da61d0e5cb735de20a6b44279831ed52df9a8132b07b57c4389738d081cde`.
All 376,832 bytes reassemble exactly. The native inventory in
`docs/validation/pandora-world-pointers.json` preserves encoded values and native
source identities; the original NULL is retained as an unresolved non-reference.
All 78 packaged asset/include identities and previous history prefixes remain
unchanged. Shared-tail relocation obligations and unknown callback/IRQ/DMA
lifetimes remain open. The next authorized tooling slice is the general CLR
predecrement fix, followed by rerunning the previously excluded palette prefix.

The complete audit exposes a remaining propagation gap: only two of the 35
nonzero object references and one of the 61 descriptor references have native
symbolic resolutions. The other 93 remain explicitly unresolved in the structured-query inventory,
although the generated source renders symbolic LONG expressions for them. Their accepted schema bindings do not
license a hand-subtracted target mapping. Completing the native structured-resolution export
for those generated operands is a follow-up; this checkpoint claims structured
prefixes and three structured-query resolutions. The rendered symbolic expressions
and structured query must not be conflated or joined by parsing source text.

## Concrete scalar EA update fix and palette trace recovery

The concrete executor now invokes its existing metadata-driven predecrement
preparation before scalar memory access, including CLR and condition stores,
logical/unary/shift RMW, compare/test, multiply/divide and TAS paths. RMW writes
reuse the read address; postincrement runs after the final access, including TAS.
No Pandora special case or new instruction/width rule was introduced. The
existing A7 byte-step rule is shared. All CLR sizes and address registers are
covered, along with sibling operations and rejected wrapped accesses.

The former strict expected failure in
`tests/test_pandora_snapshot_guards.py` now passes. Original `4267` predecrements
SP correctly; the complete render prefix reaches the modeled first spliced
return with the predicted stack state. The palette control-flow conclusion is
unchanged. The trace is now usable as bounded concrete evidence; ordinary
entry/phase reachability, absolute caller/IRQ stack separation and the shared
hit/palette tail still block relocation. This does not repair abstract scalar
EA updates or same-register two-memory operand scheduling; those separately
confirmed issues and their reproducers are in
`docs/validation/framework-defects-2026-10-15.md`.

```sh
make -j4
.venv/bin/python -m pytest -q src/tests/test_m68k_simulator_ea_updates.py src/tests/test_m68k_simulator_arithmetic.py src/tests/test_m68k_simulator_moveq.py src/tests/test_m68k_simulator_abstract.py src/tests/test_generate_c99_simulator_subset.py tests/test_pandora_snapshot_guards.py tests/test_pandora_palette_sort_ammunition.py tests/test_pandora_render_order.py
.venv/bin/python src/scripts/check_c_style.py src/m68k_simulator.c
```

The broad focused run passes 89 tests and 1175 subtests. The final EA matrix,
including six subsequently added wrapped-access cases, passes six tests and 177
subtests. The native simulator-only suite passes all 30 cases; the full native
suite was not rerun merely to recount baseline failures. Nine representative
CLR/Scc/RMW/alias-reproducer encodings agree with independent vasm. Exact C/vasm
receipt `662843b11ba5e9ad3a359d75f1b3d2d6af442e4b1b85ddf27b6b62d1f0dd34b4`
reproduces all 376,832 bytes. Source SHA256 remains
`862da61d0e5cb735de20a6b44279831ed52df9a8132b07b57c4389738d081cde`.
Original assets/includes and target histories are unchanged in this tooling fix.
The resident service was restarted to load the rebuilt C library; UI still
returns HTTP 200 at `http://127.0.0.1:8123/` (PID 200712).

## Five general framework defects resolved

The follow-up fixes all five confirmed defects from the 2026-10-15 ledger in
normal framework layers. Concrete source accesses and their updates complete
before destination evaluation for shared-register CMPM, ADDX/SUBX and MOVE.
Abstract scalar execution captures each updating operand address once, makes
its update visible to later operands, and reuses the captured address for RMW
writeback. Unknown/wrapped addresses do not produce invented memory facts;
existing PACK/UNPK and MOVEM multi-access executors are preserved. The test
ctypes state now declares the existing `sr_known`/reserved bytes explicitly.

Explicit pointer fields are planned independently of covering anchors/ranges,
and the listing JSON selects the most specific canonical field. It exports the
same native render-plan decision used by source rendering. Static table cursor
widening retains a homogeneous pointee type without inventing a concrete target
or bound; a known one-past load remains rejected. The original native pointee
baseline and its new one-past negative regression both pass. Eighteen Pandora
operand accesses now recover their existing object/descriptor field names,
including the proximity scan's position pointer, XY, flags, distance, cooldown
and context-message fields. No target-specific field seeds were added.

The fresh `pandora-world-pointers.json` now reports **96 symbolic nonzero
references, zero unresolved nonzero references, and one NULL**, agreeing with
all 97 rendered LONG rows. The previous 3/93 query/export gap is resolved by
native planning/JSON changes, without parsing source text or hand-mapping values.
All original object/descriptor layout identities and physical bounds remain.

Native file hashing now streams through the common host SHA256 helper, using
the existing BCrypt/OpenSSL dependencies. Decompression uses the same helper
for provider, source range and output identities. The Linux unknown-input fixture
uses the existing harmless `false` executable for metadata testing; no Ancient
provider was installed and codec interoperability is not claimed by that test.
Known vectors, chunk boundaries, errors and Python `hashlib` comparisons pass.

Validation after the combined changes: **811 native tests pass with no failures**,
including both longstanding baseline failures; **318 Python tests and 1581
subtests pass**, with one explicit opt-in Copperline execution oracle skipped.
C style has no new issues on changed lines. The broader applicable runs were
performed once after implementation. Full C and independent vasm reproduce all
376,832 bytes, receipt
`f7bd711ebfba35b769cfd7af280bf4a94592a20acdd9c92d6723c066a460916e`;
rendered-source SHA256:
`491f9194975382e9dbbfb3ade4a84f3eb8a391a0c895a3e6666fa3682fd86421`.
Original image SHA256 remains
`70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
All 78 packaged asset/include identities, target metadata and both histories
remain byte-identical. Generated source and package manifest were regenerated
normally. The restarted service (PID 204195) returns HTTP 200 on localhost:8123.

The reproduction commands and prior failure vectors are retained in
`docs/validation/framework-defects-2026-10-15.md`; the combined Python run covers
simulator/generator, pointer domains/reporting, restoration operations and the
bounded Pandora scan/palette/render witnesses. The shared hit/palette tail,
callback/IRQ/DMA lifetimes, unknown helper effects and unchecked game paths remain
separate restoration/relocation obligations. No PR merge, review-state change,
new gameplay route, ROM download or private-input copy was performed.

## Whole-file continuation: ranged-impact visual and point scan

The next connected batch restores five disjoint existing-format ranges, **214
bytes** in total: descriptor `$4859A..$485A6`, 26-byte render prefix
`$485B2..$485CC`, seven 18-byte geometry records `$4860A..$48688`, animation
header `$48688..$4869A`, and eight physical frame pointers `$4869A..$486BA`.
Addresses here are source offsets, established by native source mappings.
The adjacent second descriptor/state, earlier combat frame sequence, and gaps
between these ranges remain outside this classification. Combat feedback also
uses the newly typed render prefix; the ranged names identify this activation
path, not exclusive ownership of the storage.

Ten semantic code/text names connect the point scan, object-owner search,
blocked-tile and unmatched-hit paths, defeat path, force-field message and visual
activation helper. Existing record types now propagate through direct LEAs,
field loads and the helper's register-preservation contract. Four scoped register
facts cover the object candidate and three known coordinate-store consumers;
two immediate operands use existing domain bit names. All mutations use the
revision-checked catalog, not hand edits to generated assembly.

The original helper at `$9486` preserves D0-D7 and A2-A7 on a normal return with
valid fixed records/app base and disjoint stack. It loads A1 from the visual
state's descriptor field. All three direct call sites then store impact
coordinates through that returned descriptor. A changed descriptor-field test
confirms this is a load, not an immutable-address return guarantee. Two callers
can bypass activation when the hit state's interaction bit 0 is set: those paths
retain and update the incoming hit descriptor. Both bypasses are exercised.
The three A1 facts are valid descriptor types on both arms; they do not force a
particular address or automatically type hypothetical future callers. Memory
and escape effects remain unknown.

The initialized animation increments before selecting a cycling frame. Resetting
its clock to zero therefore selects physical sequence slots 2 through 7, then
held slot 0, which repeats the final geometry; this is not proof that slot 1 is
shown. Its independent timer starts at 25 **eligible service visits**. An
inactive-player guard skips timer service, and only the transition from 1 to 0
unbinds the animation node. Geometry is retained. These bounded CPU witnesses do
not establish drawing completion, seconds/frame timing or lifetime ownership.

The per-point scan traverses a NULL-terminated descriptor table, without using
the adjacent active-count slot. It excludes the player and visual descriptors,
then visits attachment states in order. Flag bit 6 skips the descriptor; bit 3
skips only that state. Descriptor coordinates, state offsets and geometry origins
compose in WORD arithmetic. For ordinary nonwrapping coordinates the signed
negative/unsigned extent tests implement half-open bounds. First matching table
entry wins. NULL resumes ray stepping; overall ray termination remains unproved.

The normal callable-summary path previously required a typed pointer input even
for a leaf whose useful contract is register preservation. The general catalog,
metadata model and native reader now accept `inputs: []`, preserving strict
member validation and rejection of references to nonexistent inputs. No dummy
input or target-specific native exception was added. Nineteen focused summary
checks pass, including catalog/history/native projection and exact assembly.
The combined applicable run passed **54 tests**; three additional original CPU
checks for both bypasses and the mutable descriptor passed separately. Together
these are **57 distinct focused cases**, including 25 ranged-visual/scan cases.
The previously green 811-native/318-Python baseline was reused, not rerun or
claimed as fresh validation of this small extension.

The read-only `pandora_ranged_visual_inventory` tool collects canonical bound
fields and authoritative native listing resolutions without parsing generated
source or translating encoded addresses itself. Its checked-in report is
`docs/validation/pandora-ranged-hit-visual.json`: **31 pointer fields, 25 symbolic,
five NULL, one unresolved `field_boundary`** at the final geometry mask field
(source `$4867A`). The six resolved mask references name existing generated
runtime mask storage. The boundary exception remains explicit; a symbolic
expression alone would not prove its extent or lifetime.

Reproduction from the repository root, with the resident localhost:8123 service
and built native backend:

```sh
make -j4
.venv/bin/python -m pytest -q tests/test_pandora_ranged_hit_visual.py tests/test_pandora_scripted_pose.py tests/test_pandora_palette_sort_ammunition.py tests/test_function_summary_catalog_effects.py -m 'not real_integration'
.venv/bin/python -m amiga_reversing.tools.pandora_ranged_visual_inventory /tmp/pandora-ranged-hit-visual.json
.venv/bin/python -m amiga_reversing.tools.rendered_source_roundtrip_report --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8 --update-rendered-source --no-write-report --json
```

The prebatch animation inventory found 85 NULL XY pointers and one field-boundary
exception among 86 headers; this batch does not invent an XY sequence to fill
that gap. The icelord boundary, positive-X player-tail overlap, adjacent visual
records, arbitrary callback effects and IRQ/DMA lifetimes remain open. The shared
`$77FE0..$78000` tail remains blocked for relocation. This is connected source
restoration, not a claim of whole-file completion or a relocated executable.

Final C and independent vasm verification reproduces all 376,832 bytes exactly.
Receipt: `070a1b7cd1fa0afbe096c318d79722f7672e98700b6baac7b9a9634b939caa32`;
rendered-source SHA256:
`36b0703b44bf05c6554563a836dda28d8d37f1cd1f4c31f51da0274a846179ce`.
The original image and all 78 asset/include identities remain unchanged; both
histories retain their published byte prefixes. This batch appends 30 actions
(including the final purpose-comment refinement) with matching accepted decisions.
Target metadata is unchanged. Changed C lines have no new style findings.
The resident service is PID 205091 at http://127.0.0.1:8123/. No runtime route
exploration or relocation was performed in this batch.

## Whole-file continuation: ranged ray tile sampling

From checkpoint `358a085b`, the connected follow-up examines `$92DE..$9322`,
before the restored per-point hit scan. Its source comment records an algorithm limitation rather than paraphrasing
individual instructions, through the inspected revision-bound command catalog.
An attempted symbolic tile-bank subtraction exposed a framework gap: the
catalog accepts a source label, but the native manual-representation reader
recognizes only platform symbols and target equates. The representation was
undone through the normal history API; the numeric operand remains. No
generated source is hand-edited. Supporting arbitrary canonical source symbols
needs a general native representation change and conservative regression tests;
adding a duplicate equate would only disguise that gap.

Coordinates advance with WORD arithmetic. Unsigned coordinate words are divided
by 16, the row is multiplied by hardcoded 90, and the column is added before two
WORD doublings. Clearing the upper word leaves a byte offset modulo 65,536.
This differs from assuming an unbounded linear array index or consulting the
current app tilemap width. The loaded tile pointer is converted to a 128-byte
bank index and tested in the existing MSB-first movement-block bitset. Set bits
select the blocked-tile visual path; clear bits restore the sampled coordinates
for descriptor collision testing.

A NULL descriptor-table entry resumes ray sampling. This loop has no range
counter or map clamp; zero step leaves the point unchanged on that back edge.
The bounded witnesses establish this recurrence, not whole-ray termination,
arbitrary tile-pointer validity or gameplay reachability of zero step. There
is no new permission to relocate the shared hit/palette tail, and no new
Copperline route exploration.

Twelve new original-CPU cases cover positive/negative/zero steps, coordinate
WORD wrap, grid-byte wrap, first/byte-boundary/last-known bit selectors, blocked
and clear branches, and NULL-scan resumption. The combined ray and prior impact
suite passes **37 tests**. Existing broad green baseline results are reused.

```sh
.venv/bin/python -m pytest -q tests/test_pandora_ranged_ray.py tests/test_pandora_ranged_hit_visual.py
```

C and independent vasm reproduce all 376,832 original bytes. Receipt:
`8b5ec5eb334efc61c50564f4152a07b6d52ed3df2dca11f2ea5d595fb13079d6`;
source SHA256 `3d58d217b7bd4e75108cb717dbc6e15509c0abca8fd47e530cc083497d8818e0`.
The surviving semantic comment is journal-accepted; the attempted representation
and its undo remain in append-only history. Original binary, target metadata,
asset/include contents and historical prefixes are preserved. The companion
[tail investigation](../validation/pandora-preserved-tail.md) distinguishes the
original unpack destination, fixed-copy extent and generated orphan label.
PR 5 remains open, unmerged and in its existing ready review state.

## Canonical address identities and preserved payload tail

The copied-call projection and operand source-symbol paths are repaired in
`1be7a2a9` and the following tail checkpoint. A call's attached canonical
section/offset now takes precedence over its original decode target when planning
source declarations. The orphan `$6AFFA` is gone; original decode facts and all
manual history remain. Source-symbol representations carry native coordinates,
rendered address view and value, validate the actual native operand/width before
append, pass the native codec, and follow renames without duplicating equates.
The subtraction at `$9302` now names `world_tile_pixels_000_through_011`.

Runtime-only scratch EQU references retain their names without asserting file
byte targets. Three retained analysis-only labels at source `$57D00`, `$57FDE`
and `$57FE0` no longer act as hidden rendering boundaries when absent from the
final source plan. The legacy unbounded blitter-source rename remains unchanged.
Actual emitted labels, code, relocations and structured ownership still guard
asset extraction. The normal `opaque_data` layout/raw-element commands preserve
all **27,792 bytes** at source `$55370..$5C000` as
`assets/preserved_uncopied_payload_tail.bin`. Its 144-byte prefix precedes the
27,648-byte patterned body; no purpose is invented for either.

The native boundary corrections also permit sixteen already-classified media
ranges to export as named assets, in addition to the opaque tail. No new media
format was inferred. The original 78 asset/include files remain byte-identical
and retained. Generated assembly shrinks from **1,322,155 bytes / 30,540 lines**
at `ffae9904` to **927,999 bytes / 24,497 lines**: **394,156 bytes (29.8%) and
6,043 lines fewer**. This moves bytes into faithful assets; it does not shrink
the game image or establish whole-file semantic completion.

Final validation passes **311 focused Python checks** and **812 native checks**,
including retained-analysis-label and full-tail-size asset cases. A broader
runtime/backend selection still has the same eight previous-renderer failures
(16 passes, two skips); their exact identities and comparison evidence are in
[the framework report](../validation/canonical-source-symbols.md).
C and independent vasm reproduce all **376,832** original bytes exactly.
Receipt: `0c11b57ba11fc0b92b6f84e360120cd3463aac16b314fef724d9b3b832bdd0b2`;
source SHA256 `63c2c28022bab20c5328ddaccabd2ae91da75774440c22bb09a794189a957d4b`.
The three new canonical actions are accepted against this final receipt; prior
history prefixes and the original binary remain intact.

[The tail report](../validation/pandora-preserved-tail.md) distinguishes original
unpack storage `$75370..$7C000` from the generated `$65370..$6C000` view and the
inspected fixed-copy bound. Runtime scratch overlaps the original unpacked
window; initial-content consumption, other indirect/load paths and fill purpose
remain unproved. The shared hit/palette tail remains blocked for relocation.
No additional Copperline route was explored. The resident service is PID 211346
at http://127.0.0.1:8123/; its target is ready and the UI returns HTTP 200.
PR 5 stays unmerged with its metadata and review state unchanged.

Detailed native identities, preservation checks, source-size measurements and
final proof are recorded in `docs/validation/pandora-tail-asset.json`.

The eight optional backend failures now have a complete pre-change comparison:
all tracked native sources at `ffae9904` were independently rebuilt and exactly
those eight unchanged test bodies were selected. All reproduce their current
errors, confirming no new regression among them. Three lack corpus inputs, two
have stale wire/key expectations, and three exercise older code-promotion or
presentation expectations. They were outside the earlier green focused baseline.
See [the failure-by-failure audit](../validation/backend-eight-failures.md) and
`docs/validation/backend-eight-baseline.json`; the former mixed-object renderer
comparison is no longer the sole basis for calling these pre-change failures.
No production code, target facts or PR metadata changed in this audit.


## Fresh whole-file pass: salvage eligibility

A new independent reading of the current restored source at `14bbb400` delivered
all 582,092 presentation bytes / 18,065 lines in 27 ordered chunks. Its new
proposal set is separate from the earlier 48-proposal queue. Ordered delivery
does not prove simultaneous retention. The first accepted swath is the previously
unclaimed 15-byte MSB-first bitset at source`$A813..$A822` (end exclusive), now
`salvage_item_eligibility_bits` with an explicit 15-byte binary array.

Native xrefs identify terminal deposit`$89EA` and four-carried-slot outcome
ranking`$4C9EA`; both test via`$5FFE` and increment `app_salvage_item_count`.
Original bytes`000001d8000000000000000000dd80` select 12 initialized item IDs.
The helper has no arbitrary-ID bounds check; 120 stored bits are not a 256-ID
guarantee. Ranking counts eligible occupied slots, including duplicates.

Three canonical actions are journal-accepted. **22 focused tests pass**, including
all 120 valid bit indices, six bounded terminal cases and three outcome cases,
plus the existing 12 status/deposit checks. C and independent vasm reproduce
all 376,832 original bytes exactly; receipt`74d949eb160c9ecceb3c08498455cb7d6d985bc175c46d950d961afc993fb884`;
source SHA256`05e1c0121f682bcbb1f7156a995c42da3d95ab70f1221345a5c0cdbce8b410da`. Original binary/assets/SDK,
prior history prefixes and unrelated facts remain intact. The shared-tail
relocation blocker is unchanged and no runtime route was explored.

The other four fresh swaths remain under review: actor display/owner identity,
overlay NULL-prefix behavior, title palette state and indexed glyph aliases.
The overlay's nonnull-only pointer advance was already recorded in an earlier
MAL rationale; any visible contract is a tested formalization, not a new discovery.
The per-swath ledger is `docs/validation/pandora-fresh-reading-review.json`.
Deferred backend test maintenance remains separate; PR5 remains unmerged, with
no routine title/body/review-state edits.


## Fresh-pass title palette, glyphs and overlay contract

Five exact title-data spans are now canonical: 16 current RGB12 WORDs at`$AC8`,
eight increment WORDs at`$AE8`, eight existing six-byte `rgb12_accumulator`
records at`$AF8`,32 current gradient WORDs at`$B28` and32 gradient increment
WORDs at`$B68`, ending at the next routine`$BA8`. The title initializer clears
all 32 gradient colors using 192 bytes of previously documented shared scratch,
but only the first 8 of 16 palette outputs. The star fade updates those 8 colors
and uses a 16-service-step byte counter. New exact-width app roles are
`app_title_raster_gradient_ptr` (+`$280`, 4 bytes) and
`app_title_star_palette_steps_remaining` (+`$285`, 1 byte). No scratch-lifetime
or device timing claim is added.

Twenty remaining title glyphs now carry index-derived B/C/E/F/G/H/I/J/K/L/M/Q/
S/T/U/V/W/X/Y/Z names. The original routine normalizes ASCII lowercase, subtracts
65 and selects 128-byte slots; D7=31/DBF establishes 32 four-byte rasters. The
bounded CPU witnesses check all 52 uppercase/lowercase indices and the first
raster/stride with guards, rather than retain overflowing full-copy traces.
PANDORA uses six distinct slots across seven characters. Malformed inputs are
still unchecked.

A visible contract on `draw_ui_overlay_text_lines` now states the stable-pointer
NULL-prefix behavior already recognized in an earlier MAL rationale: only
nonnull visits advance A4. Tests cover prefixes 0..6 in both text styles, leaving
poison string pointers after the first NULL unconsumed. This is a tested
formalization, not a newly found runtime defect or sparse-layout guarantee.

**55 focused checks pass** across new display-identity/prefix/title tests and
existing overlay/palette tests. All 38 actions are journal-accepted after C and
independent vasm reproduce all 376,832 original bytes exactly. Receipt
`7769e67a2f2ed3a8079827c2d731bfb784f4c562d1fbb9609677093f10a7c72a`; source SHA256
`2e3bc67abbd221a5667208843a3f63e04c2564bd9f8c303e883e0cb5c2bd1776`. Original binary/assets/SDK and history
prefixes remain intact. Actor-owner naming is the remaining fresh-pass swath.
PR5 remains unmerged; deferred backend maintenance and unrelated work are excluded.


## Fresh-pass actor identity correction and complete closeout

The remaining actor swath is accepted. Restart `$A0E4/$A0E8/$A0EC` resolves
object byte+`$4A` through the signed name-offset table and stores its initialized
display pointer at +0; the nearby-object overlay consumes that pointer. Original
CPU prefixes verify all eight identities independently of inventory contents.
These are initialized owner/display identities, not inferred artwork or perpetual
exclusive ownership of mutable state.

| Actor source | Previous owner prefix | Current owner prefix | Display ID / resolved name |
|---|---|---|---|
| `$4BA66` | `pianist` | `secdroid_alpha_1` | `$53` / Secdroid ALPHA 1 |
| `$4BB0E` | `wackobrain ` | `secdroid_delta_2` | `$58` / Secdroid DELTA 2 |
| `$4BABA` | `defence_controller` | `secdroid_delta_1` | `$57` / Secdroid DELTA 1 |
| `$4BB62` | `glass` | `secdroid_pi` | `$59` / Secdroid PI |
| `$4BBB6` | `kwik_kleen` | `secdroid_omega` | `$5B` / Secdroid OMEGA |
| `$4BC0A` | `flight_controller` | `secdroid_alpha_2` | `$54` / Secdroid ALPHA 2 |
| `$4943E` | `kriptonite` | `wackobrain_actor` | `$62` / Wackobrain |
| `$4C1D2` | `megabio_feed` | `pianist_actor` | `$5D` / Pianist |

The old "Pianist" encounter in the frozen planning observation is Secdroid
ALPHA 1 at `$4BA66`; the actual initialized Pianist at `$4C1D2` is the object
used by proximity music, previously named for Megabio feed. Wackobrain is at
`$4943E`, corroborated by its named interaction callback. The formerly
wackobrain-named object at `$4BB0E` is Secdroid DELTA 2. Raw historical receipts
and snapshots retain the names they recorded; they were not rewritten.

A scope-checked programmatic plan propagates these **eight semantic corrections**
through **602 source labels, 34 layouts and 355 typed element names**. These are
propagated names, not 991 independent discoveries. Existing typed layouts plus
explicit descriptor/saved-state/node/attachment pointer chains constrain the
selection. Complete native incoming pages cover 35 intervals / 270 references.
All layout/element shapes, binding IDs/provenance and interpreted references
compare unchanged. Six droids have distinct state records but share saved
artwork; generic fixed-NPC frame/table names remain legitimate shared aliases.
Global item strings/equates, original assets/SDK and history prefixes remain.

Two small catalog capabilities were necessary: identity-preserving manual
layout rename and bounded name-only bulk element rename. They use the normal
revision-checked path, preserve typed ownership and references, reject unknown
or duplicate element identities atomically, and support undo/redo. They were
published in `ca4d592d` and`39e67da9`; no native CPU/KB rules changed.

The independent rendered-name audit also found **118 shadowed renames**:
older manual labels had different durable IDs, so their old names still won
although the new row rename was recorded. The effective projection now retires
only explicit predecessor names at the same section/address in the same address
domain, prioritizes the requested declaration, and retains unrelated aliases.
Repeated row renames carry their name chain through replay and undo/redo. Raw
metadata/history are preserved. Native and actual rendered-source audits now
find all 602 new declarations at their original coordinates and none of the 602
retired spellings. The intermediate byte-exact receipt`d4959d6c64a0a34932fb6b6f6619e903ac51f1e603d9f60f58af643bf65a3b9e`
was insufficient to establish that source-quality contract; the final proof below
follows the fix. Earlier journal decisions remain with their supersessions.

The offline model now binds actors by source coordinate, uses the current
ammunition name, and exposes actor-neutral/current terminology while explicitly
retaining historical consumer keys. A live read of current native bindings and
the existing verified checkpoint succeeds with **both route searches disabled**.
No emulator operation, new route or new BYTE-path observation was performed.

Final validation: **262 Pandora tests**, **230 source-identity/framework tests**
and **62 effective-metadata checks** pass; an overlapping final target selection
passes 71. C and independent vasm reproduce all 376,832 original bytes exactly.
All 637 actor actions are accepted against final receipt
`54d4c229bd78cc51ac5f324d92a00b5ea56a979af6109643cafd5bc687976c4d`; source SHA256
`be39ad25e4da9fadbe25134a7c7d19acd6d53ce6451ce6c8bd6241021b39adc6`. Across the five fresh swaths, 678 new
manual actions are accepted. See `docs/validation/pandora-fresh-reading-review.json`
and the coordinate/rename audit `docs/validation/pandora-actor-identities.json`.

The cloud execution transport reconnected after validation and reset resident
processes. The service was restarted as PID 557 at http://127.0.0.1:8123/;
its target is ready, target UI returns HTTP 200, and the final source subject
and corrected native field name were checked unchanged.
The deferred eight-test maintenance patch remains byte-identical and uncommitted.
PR5 stays unmerged without routine metadata edits. Shared-tail relocation and
its allocation/caller/interrupt-lifetime obligations remain open; no exclusive
ownership, whole-file semantic completion or general index bounds are asserted.

## Shared-tail ownership and lifetime follow-up

The deferred eight-backend-test cleanup is published in `f5315cc4`, with paired
execution/data fixtures and independent C/vasm raw reconstruction. The configured
host vasm capability replaces its Linux-only helper path. Affected checks pass
9 cases and skip only the three recorded absent original inputs; 16 related
checks pass. Three failures exposed by a wider copied-code selection reproduce
with the pre-cleanup test bodies and remain separate. See
`docs/validation/backend-test-cleanup-2026-10-15.md`.

Canonical analysis now retains `pandora_work_buffer_palette_input`, the 32 bytes
at `$77FE0`, as an explicit alias within `pandora_ui_snapshot_hit`. The general
framework permits overlapping semantic region identities, projects their exact
intersection and offsets, and refuses independent single-region relocation.
Coincident, contained, enclosing, partial, adjacent and disjoint cases are tested,
along with history/undo/redo. No joint-move or phase-based split is implemented.
The original two setup LEAs now name `runtime_supervisor_stack_top` at `$10452`;
no allocation extent or all-path stack bound is invented.

The new original-code IRQ fixtures establish the dispatcher save/return layout
with explicit modeled hardware frames and the original no-op callback. They
confirm five LONG saves (20 bytes), the extra four-byte callback return slot,
interrupted A0 at callback SP+8, and intact saved registers/frame at RTE entry.
This is not arbitrary-callback or asynchronous hardware validation. The already
fixed CLR prefix passes; its older simulator-limit ledger paragraph is historical.

The defensible placement assessment is in
`docs/validation/pandora-shared-tail-lifetime.md`, with native proofs/refusals in
`pandora-shared-tail-lifetime.json`. Preserve the hit/palette alias relationship;
the covering reset blit is an additional cross-buffer writer. Palette caller,
producer and phase, absolute stack ownership, audio/other callback continuations,
changed DMA geometry and complete alias lifetimes remain open. The body snapshot
and palette output arrays are separate candidates, not newly certified moves.
The current independent volume plan still closes its five accepted references.
No new Copperline route, allocation, relocated artifact or whole-file reading ran.

Validation passes **124 framework checks** (one optional Copperline arithmetic
oracle skipped), **812 native checks** and **43 Pandora checks**, including five
new stack/IRQ cases. All 99 immutable tracked target files and prior history
prefixes remain unchanged. Two new actions and two review decisions append.
C and independent vasm reproduce all 376,832 original bytes exactly: receipt
`2824c4c9b75108e48467e32a6840549b4d27a6c4fc97879253c74cc3dcf4ddf4`,
source SHA256 `a0d7e192b08cdbe494344ef37e238c93067ed10310693034cf890ba76814efc8`.
The resident loopback service was restarted for the native backend change as
PID 1822 at http://127.0.0.1:8123/. PR5 remains unmerged, without metadata edits.

## Gameplay checkpoint policy and response state machine

Sixty-four accepted actions connect the eight-ID possession recheck, six-ID
selected clearance policy, 30x43 macrocell lookup and security damage/flash
service. Fifteen constants propagate to 25 actual operand sites, including all
known pending-recheck producers and initialization. Typed actor fields and
branch names replace numeric accesses; the existing palette owner retains its
shape. Original map cells distribute as 22/23/15/16 restricted cells at tiers
0/1/2/3, with 1214 unrestricted cells. No arbitrary-coordinate bounds are added.

A selected card must strictly exceed the zone tier. Valid clearance pauses the
response without clearing it; an active flash bypasses checkpoint/combat gates.
Damage changes only the HP low byte with a signed-result clamp. A normal flash
reload of 31 uses palette entries 1..30, then restores the saved color. The first live
inventory byte is reselected on response start, without consuming that slot.
These are original behaviors, not new game rules. The focused original-CPU suite
passes 15 checks, including 10 new cases covering all 1290 initialized cells and
all 256 selected item IDs at five zone values. No normal UI/audio route or
IRQ/ownership closure is inferred.

C and independent vasm reproduce all 376,832 original bytes exactly, receipt
`66b810b6db004709bbce4dd3c7a5a720c2efa497ae7955600842361340f7848e`. See `docs/validation/pandora-security-policy.json`.
The next connected gap is the anonymous shared defeat-state/animation family
used by ID failure, checkpoint damage and combat; shared-tail relocation stays
separate and unresolved.

## Shared player failure states and final-pose data

Twenty-six accepted actions restore six layouts covering 324 source bytes and
116 field instances: two final-pose geometries, two render-state prefixes, nine
additional shared animation frames, an 18-byte controller and 14 frame pointers.
The prior four-frame owner is unchanged. Defeat and escape share the final-pose
family; the escape store and all 14 frame fields resolve through the native
model automatically. One unknown header byte remains raw. Direct original-CPU
execution covers all 13 animation frames and the hold after 84 services.

The general catalog now supports sparse layout role descriptions, preserving
identity, extent, elements and references. Typed-pointer queries support bounded
source intervals, filtering before native lookup with scoped counts and bound
cursors. These remove metadata replacement and whole-family scan workarounds.
106 focused framework checks pass; 16 original-CPU cases pass collectively.
All 99 immutable tracked target files and prior history prefixes are preserved.

The initialized static state's NULL animation node makes the original exchange
helper clear bit 0 at absolute `$A` and WORD `$10`. So far this specific effect is
verified through an isolated original-code continuation, not a normal play-session
observation. Richard's follow-up asks whether genuine gameplay reaches it; that
focused investigation continues separately without altering canonical bytes.

C and vasm remain exact for all 376,832 original bytes, receipt
`65a94e792c8a308779fe30cc222b6e57038a4d954a58d275758f886669668b4a`. Native field/reference and preservation evidence is in
`docs/validation/pandora-security-defeat.json`. The local service is PID 4652,
target ready and UI HTTP 200. PR5 remains unmerged; relocation is unchanged.

## Descriptor partition and unsigned depth order

Twelve accepted canonical actions connect the recovered original-CPU evidence
to generated source: eight branch names, three descriptor-prefix register seeds
and one ordering/precondition comment. The 32-pointer snapshot feeds the three
groups: bit6 wins and retains front order; bit7 reverses back order; the deferred
middle is reverse-copied, then sorted by unsigned WORD world Y. Native propagation
names both comparison operands at `0x8522` and `0x8526`. The seeded state-pointer
load at `0x84C0` remained numeric at this stage; the reconciliation fix below
closes that native field-resolution question. Nonempty deferred input and tie stability remain unproved generally.

The recovered published head `e1eac3eb` passes 27 focused security, partition and
state-transition tests. Canonical verification after the annotation batch reproduces
all 376,832 bytes with C and independent vasm, receipt
`19e81b45193f3db3cb34b0495004a0c0f4f3a6635afc709a060328e813868495`.
Existing manual and decision history prefixes and original payload bytes are
preserved. See `docs/validation/pandora-descriptor-partition.json` for action IDs,
field sites and hashes. This is static restoration, not gameplay defeat proof.

The replacement worker recovered both published commits with identities intact.
The local canonical server now works through approved loopback access. Saved
checkpoint retrieval still fails through the supported Library route with
`Tunnel connection failed: 403 Forbidden`; no alternate transfer route was used.
The original-input NULL-node reachability investigation and any optional corrected
variant remain pending. The legal ROM and original decoded payload match their
recorded hashes; no emulator checkpoint or Copperline executable was transferred.

## Ordinary combat defeat reaches the NULL-node writes

The replacement worker recreated the documented corridor-to-rifle checkpoint
chain from the pinned Copperline release and existing legal ROM. Rifle pickup
and fresh-process audit passed at `(1228,874)`, HP 95, selected item 18. Neutral,
reverse-staging and first-security-damage scenarios also passed. No checkpoint
transfer or guest predicate edit was needed.

The former second-security-hit timeout was the wrong gate for the observed
route. A 160-service-call diagnostic shows combat flag bit 1 becoming set while
the security countdown remains 33 and HP falls to 0. The explicit original
combat probe then reaches `$79A8`, `$7A06`, `$868A` with A0=0, `$8694` with word
`$10` changed `$00FC`→zero, and return `$7A0A`. Byte `$A` was `$08` before and
after because bit 0 was already clear. This closes ordinary-input reachability
for this direct-payload route, not original-disk loader parity or all defeat
paths. Captures and checkpoint lineage are in
`runtime/observations/pandora-combat-null-node.json`.

The general explicit optional-patch builder now admits raw single-section,
fixed-size corrections against original hashes, expected bytes and canonical
instruction boundaries. With no enabled patch it emits the original unchanged.
The Pandora opt-in guard occupies the same 40 bytes at `$867E..$86A6`, exchanges
states normally, and skips only the reset of a NULL node. It needs 12 disjoint
writable stack bytes below entry SP instead of 8; no code cave or relocated code
is assumed. See `docs/optional-patches.md` and the annotated patch manifest.
Corrected gameplay has not been run: corrected behavior is presently a bounded
CPU/independent-assembly proof, distinct from original gameplay confirmation.

Validation covers 41 distinct focused tests across admission, assembler identity,
register/CCR/memory equivalence, NULL preservation, original policy/transitions,
and full original death callees with either helper. Canonical default source
still reproduces all 376,832 original bytes with C and independent vasm, receipt
`95a4fdbeb207af048a0afd556358d3a7e87f26a5f881d9cc6c4f7e4ec7b3f836`.
The one new source comment is accepted through the Decision Journal. Original
history prefixes and asset payloads are preserved. Optional output hashes and
scope are recorded in `docs/validation/pandora-optional-null-guard.json`.

## Corrected gameplay proof completed

The opt-in guard completed the same ordinary combat-defeat route from a fresh
corrected boot, through ten successful segments and build-bound checkpoints.
Original checkpoints are refused for the corrected context. All captures in the
eight shared pre-defeat segments match the original. The NULL exchange returns
with the same common registers and state behavior, while the illegal-instruction
vector remains `$00FC081C` instead of becoming `$0000081C`. The bus-error vector
remains `$00FC0818` in both runs; the original bit clear at byte `$A` was already
a value no-op. A separate non-NULL caller comparison matches registers and
record/vector bytes, with only the documented extra stack scratch difference.

Eight subsequent main-loop visits confirm HP 0, the defeated flag/static state,
combat mode cleared and intact vectors. The exit timer remains 70 in that bounded
window. There is no claimed visible improvement, crash/glitch consequence, or
full exit/title transition. Treat the low-impact bug as a proof case for the
general explicit optional-fix mechanism. See
`runtime/observations/pandora-corrected-combat-defeat.json` and
`docs/optional-patches.md` for evidence and reproduction.

Runtime admission now validates optional raw payloads against their complete
patch ledger and canonical boundaries, refuses source probes inside rewritten
ranges, and keeps snapshots tied to build identity. It shares one canonical
analysis snapshot within a CLI invocation without weakening hash checks.
127 focused framework tests pass. Default target source and payload remain
unchanged at the existing full C/vasm exact receipt.

## Typed descriptor load restored

The shared native register-seed path now clears stale table-origin metadata when
an explicit seed establishes an independent typed root. At `$84C0`, the accepted
A3 descriptor seed had retained origin `$31AA`; table-contract reconciliation
then discarded its field annotation. The formatter already supported the required
zero-displacement encoding. Canonical regeneration now emits
`movea.l world_position_descriptor_prefix_position_state_ptr.w(a3),a2`.
The following flags access and both depth comparisons retain their symbols.

The general fix applies to supported address/data register and array seeds;
unseeded or ambiguously bound table values retain their conservative checks.
The complete source diff changes one operand. All 86 asset identities, sizes and
hashes, and both manual/decision histories, remain unchanged. There are no new
manual seeds or direct generated-source edits.

All 814 native tests (650 IR tests) and four Pandora partition tests pass. The
new address-seed regression fails before the fix; the seed tests also check
provenance and absence of stale table origin. C and independent vasm reproduce
all 376,832 original bytes, receipt
`06fc580a878bf197df3ee041613c44530597082cd2ddf7efe1ac06e41e33216a`.
See `docs/validation/pandora-descriptor-seed-reconciliation.json` for hashes,
native reference evidence and limits.

Descriptor-count and supported position-state flag operands are now named at
51 uses: five instructions and 46 typed initializers, backed by six EQU
definitions. Bit-test indices and shifted initializer masks remain distinct;
unknown residual bits and the separate object-record combat bit stay numeric.
Shared fixes order final EQU definitions by dependency and preserve exact scalar
field symbols under typed containers. All 816 native tests, 62 focused metadata
tests and 40 affected Pandora CPU tests pass. C and vasm reproduce all 376,832
original bytes; 86 asset identities and payload hashes remain unchanged.
See `docs/validation/pandora-descriptor-partition.json` for the receipt and scope.

The positive-X boundary is now corrected: the concrete player uses the existing
26-byte render prefix, followed by an 18-byte animation node. The former overlap
came from its generic 30-byte state binding. Initialization and movement now name
`player_move_positive_x_animation`; its header and eight frame pointers use the
same types as the other directions. Idle changes hold/clock state within this
node; no player interaction-tail phase was established. Its byte +11 stays an
unknown gap. All 29 focused tests and exact C/vasm reproduction pass; 86 assets
are unchanged. See `docs/validation/pandora-player-directional-nodes.json`.

The guarded chain transition now uses a 22-byte extended schema containing the
existing 18-byte header and an absolute LONG successor pointer. Its three field
accesses are symbolic; only the guarded A0 context receives the extended type.
It resets and installs one successor per call, preserving all mode bits except
hold. There is no NULL/sentinel guard before successor writes. None of the 89
typed nodes or 77 typed-pointer targets has the chain bit set initially, so no
concrete record was widened or gameplay reachability asserted. All 17 focused
tests and exact C/vasm reproduction pass; data directives and 86 assets are
unchanged. See `docs/validation/pandora-chained-animation.json`.

The combined animation pass separates held and active records for all 63
established sequence starts (416 pointer entries), covering 89 initialized nodes,
26 script replacements and four proximity variants. The frame/XY consumers now
name the held-record skip and XY fields. Nonzero initial modes and remaining mode
bit operands use the established masks/indices. Counts and phase steps retain
their original values; replacement preserves both and the optional XY pointer.

A shared feedback-audio contract restores the identities of D1-D7/A1-A6 on normal
return, without imposing a game-specific pointee type on other callers. The
normal command path now supports the existing type-neutral identity model;
canonical tuple serialization and whitespace parsing are covered by positive and
conservative tests. Opaque-memory invalidation remains conservative without an
explicit identity result.

The inventory reports 70 to
78 named node-field accesses and
zero exceptions among 267 node pointers and 430 frame pointers (including NULLs).
Full C/vasm exactness preserves all 376,832 original bytes and 86 asset identities,
paths, sizes and hashes. Test results, the receipt, all sequence bounds and the
compact before/after inventory are in
`docs/validation/pandora-animation-subsystem.json`.

Remaining animation unknowns are the 14 trailing frame pointers at
`$491A4..$491DC` without an established sequence consumer, node byte `+11`, and
the physical meaning of proximity variant flag 5. No initialized node uses XY or
chaining, so their actual gameplay producers and scheduling remain unestablished.
Known count/sequence pairs fit; arbitrary later mutation and shared-node lifetime
are not proved by this static/local execution pass. Equal-depth tie behavior and
allocation lifetime remain separate engine questions. No further consequence
investigation is planned for the completed optional patch proof.

## Grouped animation gaps and primary audio dispatcher

The follow-up inspected the four animation gaps together. None acquired a new
supported meaning: all 89 known node bytes at +11 are zero; the four numeric
+11 accesses belong to keyboard/audio state. The optional XY field has only
known consumers, and no initialized node enables XY or chaining. Three flag-5
readers establish the proximity variant and X bias, without proving a physical
orientation. The 14 trailing frame pointers resemble two seven-entry sequences,
but have neither an established consumer nor literal pointers into their range
anywhere in the original image. Computed references and later mutations remain
open. No initial shared-node alias was found among the inspected typed render
states; script reuse does not establish lifetime or scheduling. The compact
[gap evidence](../validation/pandora-animation-gap-pass.json) retains these limits.

The next connected source batch restores primary audio dispatch contracts using
existing schemas. All 11 original signed-offset control handlers retain the
48-byte runtime and 12-byte DMA record bases to their decoder/exit continuations.
The shared note decoder uses the loaded or selected sample record. Twenty-five
canonical register facts restore **50 named field operands across 45
instructions**: runtime fields 46→82, resolved DMA fields 18→27, sample fields
7→12. One pre-existing unresolved secondary DMA access remains unchanged.
No new field meanings, table extents, or arbitrary-selector safety were asserted.

All 37 focused tests pass, including 11 original dispatch targets, four channel
stride producers, existing audio command cases and animation sequence regressions.
Full C and vasm reproduction matches all 376,832 original bytes, receipt
`4c9fbfc61b3d075199b627404ffef80d17fe859433eceb0266f98613dc7add21`.
All 86 asset identities, paths, sizes and hashes, all data directives and history
prefixes are preserved. See the [audio evidence](../validation/pandora-audio-dispatch-contracts.json).
Invalid opcodes, replacement program bounds, sample allocation lifetimes and
Paula DMA timing remain outside this local CPU/static proof.

## Shared audio state and program operands

The audio inventory covers 29 physical program intervals (907 bytes, 858 decoded
tokens) and their shared state consumers. All **42 numeric A3 state-access sites
now use named fields**. The sparse base view is relative to
`initialize_audio_player`; it does not classify intervening code as data or claim
allocation ownership. The 18-byte global record retains its unknown byte at +13.
Two dynamic indexed accesses remain unresolved in native type analysis.

Parameter-bearing command coverage increases **8→33 records**: 16 additional
pitch-modulation records expose opcode/step/limit, and nine channel-note-offset
records expose opcode/operand. All original program extents and three shared-tail
entry points remain intact. Unsupported control bytes and arbitrary replacement
sample/envelope selectors remain unbounded. The phase-increment copy has no
established reader, and the skip gate has no established enabling writer here.

The valid candidate exceeded the native 64-register-context capacity before any
history append. Capacity is now 256 with refusal beyond that bound; tests retain
65 and 256 entries and reject 257. The direct-loader ctypes fixture was also
stale and now matches the native policy ABI. All **816 native, 22 focused framework,
2 loader-ABI and 33 audio tests pass**, including 7,168 phase/counter cases,
all four reset pairs, the guarded eleven-sample initializer and all 25 new
parameter records.

All 76 canonical facts are verified against exact C/vasm reproduction of the
376,832-byte original, receipt
`6aca81da954ad25534cb3f93b04cd74520c77ab6c829e56900a6e4033f156847`.
All 86 asset identities, paths, sizes and hashes are unchanged. The
[compact inventory and evidence](../validation/pandora-audio-state-and-programs.json)
retain the remaining bounds, timing and lifetime limitations.


## Geometry clipping, attachment traversal and background restoration

The compact [programmatic stocktake](../validation/pandora-geometry-clipping.json)
uses canonical metadata and native query totals. The published starting head
`3a61f340` has 496 layouts, 61 structures, 82 callable summaries, 71 entry seeds
and 902 native field records (resolved and unresolved). The retained coverage
inventory partitions all 376,832
bytes into 344 intervals: 24,394 code, 263,587 accepted noncode and 88,851 unclaimed
bytes. That existing partition was checked, not rederived at this revision. Neither
raw preservation nor a classified opaque asset establishes semantic completion.
The final native snapshot has 7,043 instructions, 225 function candidates, 3,418
CFG edges and 89 review candidates; none is a completion score. Rerun the index
with `.venv/bin/python -m amiga_reversing.tools.pandora_restoration_stocktake`
against the ready resident service.

**74 accepted canonical actions** restore a connected rendering swath. Four
normal-return contracts preserve existing state/geometry identities across the
clipper, draw routine and both previous-geometry helpers. Native propagation
resolves **eight additional field operands** (902→910 total native field records),
including both attachment
traversals and every remaining numeric geometry dimension/stride read after
clipping. The final field inventory contains 883 resolved and 27 unresolved uses.
Two WORD span names replace **eight anonymous stores**. Five clip
constants name **15 operand sites** across every producer and both consumers.
**43 branch/helper declarations** now identify the previous-geometry union,
clipped tile-grid traversal and aligned/shifted drawing paths. Five comments
record the contracts and their limits. No generated source was edited manually.

The original point test rejects interior points because SWAP clears carry before
BCC; native CPU and independent Musashi execution agree. This is documented
behavior, without a correction or claimed gameplay consequence. The four side
flags also alias the rejection value 15, so both callers skip an enclosing
rectangle. Top clipping retains its original `Y+H+1-view_top` row arithmetic.
The two produced span slots have no established reader; they are not inferred
allocations or DMA sizes.

Validation passes **49 distinct focused tests** across the existing rendering,
framebuffer, snapshot and state suites and seven new geometry cases, plus
**816 native checks**. The new checks cover 1,156 rectangle boundaries, 49 point
cases, five independent Musashi point cases, ten drawing cases, three top-row
adjustments and both previous-geometry helpers. MMIO tests supply a ready-bit
shadow; they do not run a chipset or prove pixel output, DMA ordering or lifetime.

C and independent vasm reproduce all **376,832 original bytes** exactly, receipt
`ab1f896592710b0815dfb753baeaaadfdde9011f9ff7f8bee812ab57095bf9e0`. All **86 asset identities, names, paths, sizes and hashes**,
all data directives, 99 immutable tracked target files and both history prefixes
are preserved. The Decision Journal accepts all 74 new actions. No runtime setup,
optional-patch change, merge or PR-description edit was needed.

Semantic gaps remain in arbitrary coordinates/extents, mutable pointers and
attachment lifetimes, indirect effects, resource/tail purpose and audio/DMA
scheduling. The previously investigated animation and audio unknowns stay open.
Original-layout exactness does not close whole-game relocation: changed code,
data and DMA placement still needs reference, lifetime and execution evidence.
The next connected rendering gap is custom-register address context through the
tile copier's EXG path and its bounded DMA packet/extents.

## Scene blit packets and exchanged hardware base

The tile copier now tracks `_custom` through D4 and the D4/A5 exchanges,
rendering nine register operands symbolically. Twenty-eight accepted actions
add seven shared stride/size/control equates, seventeen operand bindings and
four bounded packet comments. The four masked helpers share the 160-byte
world row and the 16-byte staging row. The final edge copy reads one WORD
from each four-byte scratch pair and writes at a 40-byte row stride.
Initialized H<=48 gives a conditional 768-byte scratch extent; it is not an
allocation or replacement-admission proof. Zero tile dimensions underflow,
and final DMA starts can outlive the helper return.

Native hardware context follows full register values and simultaneous EXG.
Calls retain only registers proved preserved by an existing callable summary;
unknown calls and register changes discard the identity. This conservatism
also exposes earlier display/audio naming assumptions: boot/title return
values, the Copper callback return, and channel-relative audio bases need
further contracts. Those operands remain numeric; this projection no longer
selects `graphics/display.i`. No target seed was invented to hide the gap.
The SDK registry now admits registered constants such as INTB_BLIT and
INTF_BLIT even when unused constants lack source declarations, rejecting
mismatched values before appending history.

818 native tests, 75 focused context/query/symbol tests and 25 original-CPU
packet cases pass. The packet harness models registers, not pixel DMA.
All 86 asset hashes and both history prefixes are preserved. C and independent
vasm reproduce all 376,832 original bytes, receipt
`63c65ac70f7500726ceab857b58be86766251056f1f5cfa9d8724ffcee8c8a1b`.
See the [compact packet evidence](../validation/pandora-scene-blit-packets.json).

## Display return contracts

Of 27 reviewed display/audio register sites lost across calls or register
changes, 14 are now resolved: nine bootstrap display writes and five title
setup writes. Seven corresponding immediate expressions regain SDK symbols.
Three accepted canonical summaries record prime-blit, world-init
and starfield-init preservation. World initialization saves/restores A5 on its
sole normal exit; its six helpers leave A6 unchanged. Starfield initialization
leaves A5/A6 unchanged across its eight plane-operation continuations. Other
unproved effects remain conservative and memory/escape effects remain unknown.
These contracts assume valid original pointers and an ABI-disjoint stack.

The seeded-clear routine instead returns the fixed `_custom` address in A5.
Bounded native callee inference now represents that generated result separately
from preservation, requiring one full hardware address on every reached normal
return. Hardware value symbols consume the same native address facts and retain
accepted manual operand expressions. The display SDK include is restored
identically to the earlier published version; existing packet bindings survive.

At commit `06f34f30`, thirteen reviewed sites remained numeric: ten audio
accesses, two after the whole title function returns, and one after the Copper
callback. Audio computes
A6=`_custom+16*channel`, with original channel indices 0..3. A literal `_custom`
seed would erase this relationship. The rendering correction below preserves
this relationship through offset literals; callback/whole-title return closure
remains open. This batch does not claim pixel DMA, alias safety or arbitrary
replacement admission.

819 native tests, 71 focused framework/catalog tests and nine original-instruction
CPU cases pass. A broader existing decompression check still raises `KeyError:
codec_id`; its producer is unchanged here. All 86 assets and both historical
prefixes are preserved. C and independent vasm match all 376,832 original bytes,
receipt `cba1f3707d5fdb0dfc8fcb6c022613bcf1ec90de90fd7adda2713fe5734183b7`.
The [site-by-site evidence](../validation/pandora-display-return-contracts.json)
separates reviewed, resolved and remaining sites.

## Rendering quality correction

The rendering regression is corrected across the full source diff against
`8fcfd31f`. All 27 reviewed hardware sites are symbolic again, and all 19
remaining lost instruction/comment occurrences match that baseline. Display
bit expressions, window/fetch explanations, Copper-list pointers and audio
field names and notes are restored. No earlier annotation was disproved.

Thirteen accepted offset-domain representations name encoded SDK literals;
two accepted immediate representations restore DMAF_RASTER and INTF_COPER.
For audio, `aud0+ac_*` names the offset in the channel selected by
A6=`_custom+16*channel`; it does not assert a fixed A6 address. The bootstrap
and interrupt bindings likewise preserve intended offset names without
inventing whole-title or indirect-callback proofs. Conservative call/write
invalidation remains active. SDK access notes now consume native address
proofs as well as these explicit literal domains, retaining richer existing
pointer-provenance notes.

819 native tests and 298 focused framework/catalog/CPU tests pass, including a
source snapshot that failed before correction. C and independent vasm reproduce
all 376,832 original bytes, receipt
`6c32110f18577bdcf80d6b91e3b38d17722ab6e9ec1d8435ae3f1febf9ea81bb`.
All 86 assets and both history prefixes are preserved. An isolated build of the
`8fcfd31f` backend returns the identical missing-Ancient-provider payload for
the existing `codec_id` failure, establishing that it predates this correction.
See the [correction evidence](../validation/pandora-render-quality-correction.json)
and [SDK offset-domain contract](../restoration-interfaces.md). Runtime callback
closure, pixel DMA, alias safety and arbitrary replacement admission remain open.

## Audio channel-relative hardware

Twelve primary-player audio writes are reviewed as one group: ten in the main
channel loop and two in the silence opcode handler. All twelve now have native
closed hardware-family facts with base offsets `{0,16,32,48}`; previously none
had such a bounded fact. Ten already had valid accepted offset names. The two
silence writes now gain `aud0+ac_ptr` / `aud0+ac_len` and their pointer / 64-byte
length explanations. The corrected `27bc9a02` instruction names, inline notes
and standalone comments are preserved.

These twelve proofs depend on eleven explicit handler-entry input contracts:
A6=`_custom+16*D7.w`, with D7.w in 0..3, for original valid primary-player
dispatch. Existing handler discovery entries otherwise supply unknown register
values and erase the loop bounds. The contracts appear on complete separate
`INPUT contract` source lines. The independent bounded solver propagates low
WORD sets, ADDA.W and DBF backedge/exhaustion states, validates every candidate
against the same SDK family field, and records input dependence. It publishes
no fabricated single address and drops unknown, overflowing or unfinished
proofs. Calls and unsupported writes remain conservative. Accepted offset
renderings remain independent fallbacks.

The original instruction harness checks all eleven opcode handlers in all four
channels, including D7 upper-WORD sentinels and reset through RTS. Four producer
cases and four actual silence-handler channel-write cases bring that audio
group to 52 CPU cases. The native indirect jump at 4DC2A remains unresolved;
arbitrary handler entry, opcode/operand replacement and dispatch closure are
not proved by these input contracts. MMIO is a memory shadow, not audio output
or DMA timing.

819 native and 380 focused framework/catalog/CPU/source-quality tests pass.
C and independent vasm match all 376,832 original bytes, receipt
`5046acf61f021bc19c38f5276d168ad74c1bfc016a5bd301f07474b9c5b71cd0`.
All 86 assets and both historical prefixes are preserved. The `codec_id`
provenance question was closed by the preceding correction's isolated baseline
comparison; the missing Ancient provider is pre-existing and unchanged here.
See the [reviewed-versus-resolved evidence](../validation/pandora-audio-channel-hardware.json)
and [indexed input contract](../restoration-interfaces.md).


## Indirect dispatch and star color operations

The 22-site native indirect-transfer inventory now feeds 58 known destination
edges at 14 sites into the CFG, including the eight star operations and all 33
world-command handlers. Previously discovery knew these destinations but the
CFG omitted them. Every site retains its unresolved alternative: candidate
edges do not establish a complete target set. Runtime-mapped direct branches
now retain the existing bounded permission to replay distinct continuation
inputs; focused tests reproduce the previous lost-target behavior.

Eight star color writers and two continuations gain semantic names. One
canonical eight-entry signature records opaque A0/A3 pointer inputs; two source
comments explain the lifetime selector, three planes spaced 40 bytes apart,
and tail continuation. Original instruction checks cover every color with all
three original continuations, every valid lifetime, and the unsigned world
opcode guard. AND #7 bounds the pixel bit, not the star table index.

819 native and 283 focused tests pass. C and independent vasm reproduce all
376,832 original bytes, receipt `3ad5a1de386597905593f9ba670d22911c144e4c5d5183b2345cb5b95f52680e`. All 86 assets, both history prefixes,
and earlier symbolic instructions/comments are preserved modulo the ten label
renames. The [inventory and limits](../validation/pandora-indirect-dispatch.json)
record eight sites without known targets. The next swath is continuation
propagation through the longer star selector: native replay still recovers
only DAE per writer, despite the three reviewed original continuations.

## Starfield producer and continuation family

Native discovery now carries explicit inline resume producers through the longer
star selector and its table. All eight color writers expose the three original
continuations D68/D9C/DAE: 24 known tail edges instead of eight, and 3,492 CFG
edges overall. The bounded trace retains at most eight states per instruction;
opaque calls and overwritten registers discard provenance. Known targets remain
incomplete, and every indirect site retains its unresolved alternative.

Four shared dispatch/record-loop labels and six domain constants replace the
anonymous labels and eight numeric operands in the initializer, motion/reset,
selector and both 100-record loops. Original-code tests now exercise complete
initialization and update, including reset at lifetime 16 and the untouched
fourth plane. All earlier semantic lines and 86 companion assets are preserved.
819 native and 302 focused tests pass. C and independent vasm reproduce all 376,832 original bytes. Exact-build receipt:
`a70b10785df1d3d434cbaf7c5aef622b76c017029fa468b69e36a6ccdefe3547`.

The remaining eight unknown sites share four mechanisms: four mutable record
callbacks, two command-cursor callbacks, one Blitter callback slot, and one audio
dispatch. The native typed-field inventory contains 35 world objects (14 non-null
interaction callbacks and four non-null completion callbacks) and ten UI
descriptors with initially null update callbacks. Initialized values do not close
future stores or caller pointee domains. The next shared capability is tracing
the field-load/null-guard/D0-to-A0 call idiom with its record and store provenance;
these fields must not be promoted into unconditional complete target sets.

## IRQ/display literals and title raster phases

The eight indirect sites were reviewed together using the retained 35-object,
ten-overlay and command/audio inventories. Their mutable producer/domain limits
remain open. The saved nearby-interaction observation identifies the diabetic
at source 83FE -> 4D568 on one original card-selected path; the current command
catalog cannot attach a witnessed indirect CFG edge. No new complete target set
or arbitrary-callback preservation claim is admitted. Matching the shared
register/offset idiom alone would omit record-owner and store provenance.

The connected IRQ/title family gains 18 local/external names, six constants,
31 operand presentations and two RGB12 WORD layouts covering 80 bytes. IRQ
source tests and acknowledgements use SDK bit names, four bitplane/two sprite
pointer stores retain SDK register offsets, and the frame-completion bit name
covers all eight existing set/clear/wait uses. Literal offset bindings do not
prove A5 survives opaque callbacks. The title Copper list, three phase loops,
beam waits and rotation loop are named together. Counts are 32 current, 24 intro
and eight rotating raster lines; the rotating array contains sixteen WORDs,
all rotated on even frames. Existing meaningful names and comments are retained.

26 focused IRQ/title/hardware cases pass, including two new original-code frame
rotation cases. The unchanged native backend reuses its 819-test regression
result. Duplicate per-operand catalog reads were removed; the atomic endpoint
still validates every native selector and revision. Final C/vasm full-payload
receipt: `44d982824b2e1574d0b8998c3d66792c9a5823dfbdf906c42c03e0d1f9c5b413`.


## Overlay title masks and planar border records

The five-byte A-Z title font now has 26 named glyph records with explicit mask
rows. Six existing 32-byte border owners retain their IDs, names and extents,
with eight four-plane pixel rows each. Two shared types expose all 322 bytes as
semantic fields. Eight renderer/resource/edge-loop labels and three constants
complete the local unit; nine operand presentations reuse the shared 40-byte
stride and name the character base, edge DBF bias and 1280-byte cell-row step.

Three original-code tests cover 47 input scenarios: all 26 glyphs, all ten
initialized descriptor titles, empty text, four unchecked bytes and all six
border cells. Titles AND each mask across four packed planes from cursor+320;
even an empty title stores that adjusted cursor. BYTE subtraction wraps without
an alphabet guard, so unsupported input can consume neighboring resources.
The existing dimension-wrap and destination/ownership limits remain explicit.

20 existing overlay/descriptor regressions and the three new CPU tests pass.
The native backend is unchanged, so its 819-test gate is reused. Per-scenario
fixture reconstruction is avoided by exercising the family in three bounded
CPU fixtures. C and independent vasm reproduce all 376,832 original bytes,
receipt `250068d4cd806cbc836da926448527437faa6aea344d11315d9c57999cb037d8`.
Existing source annotations, all 86 assets and both history prefixes are
preserved; no generic local labels remain in the selected renderer units.

## Keyboard, joystick and key-consumer family

The 128-byte keyboard state producer and its main/modal consumers share a sparse
key-table type. Only the five consumed keys are named: two camera profiles,
Space inventory, F1 pause and F7 warm restart. A one-byte key-state type covers
the pause helper. Runtime address constants identify the table, its Space/F1
entries and the app-state base; they assert neither allocation nor relocation
closure. Cold startup clears 876 app bytes, while world restart clears exactly
128 key bytes. The app-state address anchor does not claim the sparse app type's
full extent.

Joystick masks retain opposed direction bits; signed steps favor left and up.
Inventory processing keeps its press latch across blocked releases. Pause waits
for release/press/release, inhibits the scrolling ticker, and leaves frame audio
and keyboard service active. Three F7 consumers enter the same Blitter-idle wait
and shared hardware setup. The absent-PORTS acknowledgement path still inherits
A0; its uncertain CIA write and the existing keyboard relocation limitations
remain unresolved.

Eight new bounded original-code tests cover every serial press/release byte,
all 32 joystick/fire combinations, pause transitions, inventory gates, exact
clear fences, three restart consumers and camera-key priority. Together with
existing interrupt, hardware-rendering and overlay regressions, 30 tests pass.
The rebuilt native backend passes all 819 tests. Its fixed custom-type capacity
is raised from 64 to 256 because Pandora's 63 existing types left insufficient
space for this family; three new tests cover 65/256 success and 257 refusal.
The legacy metadata test ABI now includes hardware-indexed seed fields, and
stale field-rendering expectations match current qualified symbols/comments.
The broader custom-type selection has nine passes and one separate unresolved
Hunk regression: a non-relocated numeric pointer is symbolized as a source
address. That Hunk renderer path is unchanged by this family.

The 78 accepted actions comprise two types, 21 block/routine names, 18 constants
and runtime anchors, five grounded register seeds and 32 operand presentations.
Original annotations and all 86 assets are preserved. C and independent vasm
reproduce all 376,832 original bytes, receipt
`0b1854723ec06b09bf3c35cca5f88e29baefe866bab6f6edf012e49ef01e64c5`.

## Counted descriptor and world-table traversal family

Nineteen local block names complete the seven connected draw, background,
snapshot, XY-copy, animation and script-traversal routines. Three grounded
register facts expose the animation attachment/flag fields and script object's
flags, including the retained A4 owner after direct animation update.
The shared outside-view flag is named at both geometry producers and all four
known consumers; the script wrapper's complete flag-1/flag-6 mask is symbolic.
No additional meaning is assigned to flag 6.

Six original-code tests exercise NULL-table and zero-count exits, exact counted
snapshot scope, linked attachment geometry, draw/restore loop-state preservation
with empty geometry, visibility-gated animation and all 35 script-table entries.
The XY wrapper traverses A1, assigns entries to A0, but repeatedly copies from
inherited A5; the old comment's A0 cursor typo is corrected without claiming it
updates every table object. Valid finite chains are test preconditions, not a
claim of cycle or pointer guards. The script wrapper skips blocked objects before
even servicing delay, unlike direct interpreter calls. The unreferenced background
wrapper is named from its code; absence of direct references is not proof it is
unreachable.

The backend is unchanged; its 819 native tests and prior geometry/animation
checks are reused. The separately deferred failing test remains
`tests/test_c_backend.py::test_real_dll_data_block_custom_struct_unaligned_repeated_field_reassembles`.
It uses one custom type and the Hunk renderer was unchanged by the earlier
64-to-256 capacity adjustment: the numeric-pointer/relocation defect predates
that adjustment and is outside this raw-image restoration family.

All 32 actions are accepted: 19 block names, three grounded register seeds,
two constants, seven operand presentations and the cursor-comment correction.
All three recovered field uses render symbolically, and no generic local labels
remain in the selected seven routines. Original SDK expressions/comments and
all 86 assets are preserved; both histories retain their original prefixes.
C and independent vasm reproduce every original byte, final receipt
`85ce60d127764d10ed0fc559bcc42e10cd6aa50c64da1a2a877029d0f6632c66`.

## RGB12 arithmetic, initial palette and transition consumers

The six component/palette primitives, current-palette hardware writer and
countdown-driven gameplay transition form one connected family. Their four
palette loops, transition body/return and initial palette/color-two alias are
named together. Existing six-byte `rgb12_accumulator` records are reused as four
grounded A2 input facts. Shared masks, shifts, strides and 8/16/32-color DBF
counts replace their supported literal operands in the primitives and callers.
The initial gameplay palette is sixteen RGB12 WORDs; restart restores only its
color-two WORD to AAA. The writer consumes exactly 32 bytes through eight LONG
stores beginning at the SDK `_custom+color` address.

Original arithmetic uses modulo-65536 component updates and WORD/BYTE packing,
with no clamping; out-of-range component bits can overlap neighboring output
bits. The leaf input D0 is ignored. Unpack copies each complete input WORD into
the palette while only its three low nibbles become Q4 accumulators. DBF helpers
process uint16(D7)+1 records and have no empty-count guard. Register restoration
and output fences are explicit; arbitrary source/output aliasing is not proven.
The title gradient's component storage still shares cursor-initializer scratch,
and the work-buffer stack-splicing paths retain their existing reachability and
phase-exclusion limits.

Setup's counter of 25 services waits eight calls, then adds seventeen palette
steps. The health-update latch is checked when the decremented counter reaches
one. Five new bounded original-code tests cover 160 add/subtract cases, all 4096
RGB12 combinations with upper input bits, six counted palette spans, all 256
counter inputs, the complete setup countdown and initial palette/reset/writer
fences. Source preflight exposed the source-only auto-update typing boundary.
The bounded cursor path now also models ordinary destination stores and
predecrement reads; generated metadata determines access roles and widths.
Field identities remain comment-only so original EA modes and bytes survive.
A7, multiple updates, multi-register transfers, conflicting bases and accesses
outside the known record remain conservative boundaries. The focused negative
fixture labeled CMPM used EOR bytes; vasm confirms the corrected CMPM encoding.
The rebuilt backend passes all 819 native tests, 26 cursor tests, 18 static
field-cursor checks and 19 palette/hardware cases. The separate pre-existing
Hunk numeric-pointer regression remains deferred.

All 70 actions are accepted: eight names, fifteen constants, four type seeds,
35 operand presentations, one palette owner, three element revisions and four
behavior comments. The final owner contains two WORD-array elements (2+14
colors) split at its retained color-two alias. All eighteen component reads and
writes have native field references; auto-update forms retain their exact EA
syntax with comment-only symbols. Prior SDK expressions/comments and all 86
assets are preserved, and both histories retain their original prefixes.
C and independent vasm reproduce all 376,832 original bytes, final receipt
`598506087f5d02a3d815885bb375175ddf37d91cfdfe2f080e12a789446d6d5e`.

## Camera profiles, coordinate service and movement selection

Six connected camera/profile and movement-selection routines gain complete local
naming, including the vertical wrap paths and shared movement return. The two
existing six-byte profile records retain their owner, type and every value; the
inset-margin record now has an explicit source alias. Shared camera-active bit,
refresh count and profile-index constants cover all inspected producers and
consumers, and movement-node selection reuses the existing direction bit names.
Tile/viewport dimensions, trigger padding and map guards are named together.

Six new original-code tests cover both profiles, all 256 countdown inputs,
WORD coordinate conversion/clamping, trigger equality and map guards, both
vertical wraps, forced refreshes and bounded repeated service prefixes. A zero
count wraps to 255 and advances coordinates even with the active bit clear; only
the expiry result clears deltas before rendering. The old implied active-flag
guard in the service comment is corrected. X is not clamped, while Y uses a
signed-negative test followed by the original unsigned upper-bound comparison.

Reloads four/six permit three/five movement visits, or 48/80 pixels. The original
48-pixel horizontal guard is unchanged for both profiles; a controlled inset-
profile entry at X=48 wraps X in the service prefix. These tests stop before the
renderer and do not prove full-frame completion or gameplay reachability at that
boundary. The unchecked profile index, WORD height arithmetic, shared return
paths and unnamed status-bit-six meaning remain explicit limits.

The backend is unchanged; its 819 native and 63 focused results are reused.
The pre-existing Hunk numeric-pointer regression remains deferred.

All 79 actions are accepted: twenty names, sixteen constants, 41 operand
presentations and two behavior comments. No generic local labels remain in the
selected six routines. Both profile records keep their original owner, type and
values, and all prior SDK expressions/comments and 86 assets are preserved apart
from the explicitly corrected active-flag implication. Both histories retain
their original prefixes. One final C/vasm gate reproduces all 376,832 original
bytes, receipt `2eba1a598b0b07ee392231a37b72113ed2bd5f8ad6d95943da0df698373a0b00`.

## Shared message FIFO, status duration and scrolling ticker

The eleven connected status/ticker entries now have complete local labels and
shared state names. Their queue is sixteen LONG pointers followed by a fixed
zero sentinel; the tail points at the next insertion slot. Both dequeue routines
shift all sixteen pointers and decrement the tail even when called empty. The
existing head declaration covers the complete inline pointer table, while the
limit and mixed context/status flag byte retain their original offsets.

Scrolling enqueue forces SR=$2700 on entry and SR=$2000 on every return, clearing
the earlier rejection carry instead of restoring caller SR. Status enqueue
stores ten times the measured spacing units modulo WORD before testing capacity,
even with an active status message or a full queue. The measurement counts space
runs plus one if any nonspace occurs, stopping at NUL or CR. Active duration zero
wraps to $FFFF; no guard is added. Switching from scrolling to status clears the
scrolling flag, resets the shared queue and clears the status band.

The ticker services its timer and palette flash even while inactive. It folds
every byte at or above ASCII `a` by clearing bit five, without a `z` upper bound.
It renders the current byte, including NUL, and then tests the next byte for
queue advancement. Seven rows each shift 39 bytes and receive glyph rows 1-7 at
their named insertion positions. Band clearing covers exactly 1280 bytes.

Six original-code tests cover controlled FIFO capacity/empty shifts, SR/CCR
returns, duration reset and wrap, timer/flash behavior, all 256 ticker byte
inputs, live queue cursors and exact band fences. The controlled font atlas and
RAM inputs do not establish actual-font bounds, arbitrary pointer validity or
gameplay reachability. The next-message duration test stops before proportional
text rendering; transitive renderer effects remain outside that prefix.

A small canonical command extension names fixed signed-word `d16(An)`
displacements through equal-valued target EQUs, with a second native decoded-byte
check. It preserves the base register, source auto-update and explicit zero-word
extension. Plain indirect, auto-update and PC-relative forms do not offer that
command. Sixteen new displacement cases, ten indexed-displacement checks, fourteen
hardware rendering regressions, four aggregate extent checks and the six message
tests pass. A second gap misclassified SR/CCR as source labels when rewriting
symbolic operands. The symbolic parser now retains the existing native special-
register classification; sixteen forward/backward EQU cases cover MOVE and
ORI/ANDI/EORI against numeric forms and independent vasm. All 66 focused and
819 native tests pass. The separate pre-existing Hunk numeric-pointer regression
remains deferred.

All 100 actions are accepted: 26 names, 27 constants, 39 operand presentations,
three shared-state declarations and five behavior comments. No generic local
labels remain in the selected eleven entries. All prior SDK expressions and
comments, all 86 assets and both history prefixes are preserved.
The final C/vasm gate reproduces all 376,832 original bytes with unchanged reviewed
source SHA256 `b71dbba8dc222e54edfb5226d2b954622c3bf243117f918a281601858a724737`, receipt
`fdf376b1ece01529ad6c7f9072682937fce0cf06d1d2a0aaa53d95e229fafc41`.

## Compact/proportional text records, cursor arithmetic and plane packets

The six connected compact/proportional text and cursor helpers gain complete
local control-flow names, shared cursor/plane constants and typed glyph reads.
The existing compact ASCII 32..90 owner remains exactly 59 eight-byte records;
its raw grouping becomes eight named bitmap rows per record under the existing
owner name `compact_font_ascii_32_through_90`. The encoded
character-zero indexing origin is named separately, 256 bytes before that owner.
Those earlier bytes retain their existing roles and are not classified as font
records. The proportional owner remains 68 sixteen-byte advance-plus-seven-row
records with its existing 96-byte character map. Its glyph pointer, destination
WORD cursor and BYTE pixel phase retain their original workspace offsets.

Compact text subtracts 32 from every byte at or above 97, including values above
`z`; the ticker's bit-five folding remains a separate rule. Byte one advances
the stored origin and reloads the live cursor. CR pops the separately saved line
origin, adds 1280 bytes and restarts, so prior glyph advances and stored-origin
edits do not change that CR origin. The compact copier loads the mask once and
copies or clears exactly eight bytes in each of four planes, preserving A0-A3.
Only the four low mask bits select planes; higher bits do not add planes.

The proportional renderer uses only the advance WORD's low byte. Phase plus
advance wraps as BYTE before comparison with sixteen. Equality advances the
WORD cursor by two bytes with a one-WORD blit; a greater BYTE result selects two
WORDs, source modulo -2 and a zero last-word mask. The retained phase is the low
nibble. A wrapped result below sixteen does not advance the cursor. The packet
uses native SDK channel/minterm and shift constants. The first-word mask remains
inherited; enabled planes poll/ack before launching, with no final completion
wait. Two-WORD source envelopes still include a neighbouring WORD.

Seven new original-code tests cover all 256 compact plane-mask bytes, complete
copy/clear fences and control strings, every declared proportional map entry,
2,786 phase/advance pairs, preserved registers, selected-plane MMIO packets,
pre-launch polling, empty text and signed WORD cursor wrap. Both cursor helpers
mask X/Y rather than clamp, and Y values beyond the 200-entry row table still
read adjacent workspace. All 96 declared map entries select one of the 68
existing proportional headers with the initialized font pointer. This narrow
fact does not establish validity for unchecked bytes, replacement font pointers,
compact out-of-owner characters, destinations or gameplay reachability. MMIO
shadows do not simulate acknowledgement side effects or pixel DMA.

Two prior character-style facts exposed a canonical presentation-edit gap:
new symbol styles accumulated beside the old style, triggering the native
conflict guard. Manual projection now selects the latest style for the exact
native section/span/operand owner, including overrides of legacy metadata.
History stays append-only; undo/redo restores the corresponding prior/latest
style. Other owners and native raw-metadata conflict guards stay independent.
Eighty-two focused checks cover replacement, legacy metadata, undo/redo, owner
separation, raw-policy conflicts, action-log behavior and hardware rendering.
The native backend is unchanged; its completed 819 native checks and previous
assembler checks are reused. The separate pre-existing Hunk numeric-pointer
regression stays deferred.

All 82 actions are accepted: seventeen names, eighteen constants with six
symbolic-display revisions, 31 operand presentations, three workspace-field
refinements, two glyph type inputs, one compact record type, one owner binding
and three behavior comments. Nine glyph reads have native field references; the
selected six routines have no anonymous local labels. The compact data now uses
its precise owner name in assembly. Prior SDK expressions/comments and all 86
assets are preserved outside that authorized glyph presentation; both histories
retain their original prefixes. The final C/vasm gate reproduces all 376,832
original bytes, receipt `86001ecbc830548b40cd075d120615a620b94ed08d1c14782235ca3bbdd24d28`.

## Masked-frame plane packets and WORD address helpers

Four masked-frame helpers and both related address helpers gain complete local
poll/return labels, SDK-derived mask/shift controls and symbolic geometry. The
related geometry caller uses the same row-table-origin and phase-mask constants.
EQU display choices are reviewed as part of the batch: formulas use symbolic
display, ordinary shifts use decimal and the full-WORD mask uses hex. No data
owners, frame bounds or original instructions change.

The cookie-cut minterm selects B under A and otherwise C: A is the shared mask,
B starts at pixel-source+2*plane, and C follows the destination at 40-byte plane
intervals. The aligned helper uses one WORD; the shifted helper uses two. Mask
row stride derives from the low input stride WORD divided by four; source and
background modulos retain WORD underflow/wrap for unchecked dimensions. All
packets inherit the first-word mask. Existing SDK register/control expressions
and scratch-envelope comments remain intact.

The edge helpers stage two-WORD pairs at scratch+4*plane with a sixteen-byte
row stride. The second-edge background begins one WORD before the destination.
Final copies read scratch or scratch+2 as 4H one-WORD rows, with source stride
four and destination stride forty. Earlier initialized-height and neighboring-
WORD envelope limits remain conditional programmed bounds, not a broader scratch
allocation or phase-exclusion proof. Each launch polls/acks the BLIT request;
a further poll precedes scratch reading. Final DMA can outlive return. These are
CPU-programmed packets, not observed DMA fetches.

Every variant restores D4-D7 through MOVEM.W, sign-extending the saved low WORDs,
even on the zero-height return. The aligned entry clears D6 before saving it.
Saved address registers are restored as LONGs. Only the low shift nibble reaches the
hardware fields; nonzero heights can wrap to a zero encoded height field. The
original zero test, WORD arithmetic, inherited state and lack of admission checks
remain unchanged.

The address helpers convert unsigned WORD X to an even byte offset, read through
signed WORD(2*Y), wrap the offset sum as WORD and use signed ADDA.W for a pointer.
The offset-only variant retains D2's high WORD and preserves D0/D1; it has no
known static callers, which does not establish unreachability. Neither helper
checks the 200-entry row-table boundary.

Seven new original-code tests cover 576 four-plane packet sequences, 2,520 WORD-
input boundary combinations, every plane/scratch poll barrier, register restores
and 200 remapped-workspace address cases. The remapped workspace backs signed
indices for arithmetic witnesses; it does not establish valid game coordinates.
The MMIO shadow performs no acknowledgement side effects or pixel DMA. Actual
allocation/admission, DMA completion and gameplay reachability remain open, as do
the previously stated font limits. The eight bytes between the first two helper
entries remain unclassified; their purpose and entry reachability are not claimed.
Native/framework code is unchanged, so prior native and focused results are reused.
The separate pre-existing Hunk numeric-pointer regression remains deferred.

All 93 actions are accepted: 22 local labels, eight constants, 59 operand
presentations and four behavior comments. All prior source annotations and SDK
expressions, data owners and 86 assets are preserved. Both histories retain
their old prefixes. Native EQU values/display choices and rendered routines
passed review before the single final C/vasm gate, which reproduces all 376,832
original bytes, receipt `79cf80bbf1620000c99d4af084d83a7a617a1591c4d0b67ac15903122adfca27`.

## Macro-tile expansion, viewport packets and modal map exchange

The fixed map builder consumes 43 rows of 30 macro-tile IDs. Each ID selects
one eighteen-byte definition containing nine unsigned WORD pixel offsets in
3x3 row/column order. Existing owners retain their exact bounds: 1,290 IDs at
`$3502..$3F16`, and 468 definitions at `$3F16..$5FFE`. The ID map gains a precise
shared name at both the builder and security-zone consumer; definitions gain
nine named row/column fields. All original IDs fit 0..467, and all definition
offsets are 128-byte aligned with maximum `$FD80`. This is original-table
evidence, not validation of replacement IDs or broader pixel allocation.

Expansion writes exactly 11,610 LONG pointers to the fixed runtime envelope
`$4000..$F568`, a 90-column by 129-row grid. Source offsets are zero-extended,
but record lookup uses the signed low WORD of ID*18. The footer separately
computes stride/size/end from current app dimensions and base; stride scaling
wraps as WORD before the unsigned height multiplication. Synthetic dimensions
can therefore describe bounds different from the fixed expansion.

The full viewport launches twenty columns by eight rows. Each packet copies
one WORD across 64 packed rows with destination stride forty. The next tile
row begins 2,560 bytes later. Source rows receive one grid-size subtraction
when they reach the end, while columns have no independent clamp or wrap.
Initial row*width multiplication retains its upper WORD while the column
addition and scaling wrap only its low WORD. Later row stepping uses signed
ADDA.W. The cell-address helper differs: its column addition wraps as WORD,
then pointer scaling uses LONG arithmetic. Its D0/D1 inputs are restored.
Packed viewport bounds retain unsigned WORD endpoint wrap without clipping.

The single-tile helper launches one WORD across sixteen packed rows, preserving
A5. Both helpers poll and acknowledge the BLIT request before launching; neither
waits after its final launch. The viewport inherits the first-word mask and
BLTCON1; the single-tile helper inherits both masks and BLTCON1. These programmed
packets do not prove ascending-mode DMA, completion, exclusive allocation or
valid arbitrary coordinates.

The modal helper exchanges width, height, column and row WORDs with its saved
header. It always selects the adjacent modal cell base, including on the second
exchange, and leaves derived stride/size/end untouched. Both exit callers
explicitly restore the world-grid base. Native typing now retains a bounded
one-past record cursor so all four backward header stores resolve to their
fields. Endpoint accesses remain unresolved; extra out-of-range postincrement
invalidates the cursor. This general change adds thirteen positive/conservative
BYTE/WORD/LONG tests and updates two existing endpoint expectations.

Nine original-code tests compare every expanded pointer and adjacent fences,
exercise five footer geometries, six signed record-index cases, 320 viewport
packets, ninety viewport arithmetic boundaries, both poll barriers, 196 cell
address/bounds combinations and two modal exchanges. The full-grid witness
moves its stack outside the destination envelope. The MMIO shadow performs no
DMA or acknowledgement side effects. All 819 native checks and 71 focused
cursor/hardware tests pass. Previously recorded font, scratch, gameplay and
unclassified eight-byte-gap limits remain open. The unrelated pre-existing
Hunk numeric-pointer regression stays deferred.

All 94 actions are accepted: seven names, 34 constants, 42 operand
presentations, five layout/type operations and six comment actions, including
one preservation revision. All 4,212 definition WORDs expose their row/column
field names; the selected routines retain no anonymous local labels. Previous
annotations/SDK expressions, owner identities/bounds, all 86 assets and both
history prefixes are preserved. Native EQU display choices and rendered units
were reviewed before the first C/vasm gate, receipt
`617dde1f00f0b06c6cdda4ab228f62ea19b2c757e131cc8b1a61edffb10a433b`.
The preservation audit then caught a replaced helper comment; its complete
original wording is retained with the arithmetic note appended. The final gate
again reproduces all 376,832 original bytes, receipt
`adf5914dfe606b4473b38fa755dc6b9dd8088fd9c85e9523f072ccb3d0ada48a`.
The comment revision changes no implementation; existing native/focused/CPU
results are reused. New coverage is in `tests/test_one_past_record_cursor.py`
and `tests/test_pandora_tilemap_grid.py`.

## Combat clocks, initialized selector alias and paired hit feedback

The detailed attack scheduler now has an original-code execution model, beyond
its earlier entry names and health-branch observations. Opponent reload one adds
two charge units, while other reloads add one; player reload one adds one and
other reloads add two. Both decrement BYTE counters before testing expiry, so
zero wraps. Only the opponent charge low BYTE is tested against 23; an attempted
attack clears the whole charge WORD before its comparand check. Player charge
updates instead reset unsigned WORD values above forty. Its descriptor flag WORD
must be negative before either clock or gauge work occurs.

Player fire tests the charge low BYTE: below seventeen clears charge, 17..22
selects half damage, 23..24 full damage, and 25..255 preserves charge. The later
gauge service can advance charge on the same visit. The old signed-versus-borrow
health note remains unchanged; tests expose wrapped positive opponent subtraction
results that survive where the player branch would defeat. This documents
original behavior, not a proposed gameplay correction.

The formerly anonymous selector is a concrete alias in the normal workspace.
With A6=`$39FC`, displacement `$7EE` reads the low WORD of grid cell 122:
`$39FC+$7EE = $4000+122*4+2 = $41EA`. Its low BYTE at `$41EB` also selects hit
patterns. The original builder expands macro ID 131's r1c2 offset `$6F00` into
pointer `$23FA8`, supplying WORD `$3FA8` and BYTE `$A8`. Thus this initialized
context gives the opponent comparand 84 and player/opponent feedback choices
2/0. All 4,212 original definition offsets have alignment that retains those
feedback choices. The two read views name this grid-cell relationship, not the
separate absolute PRNG state at `$7E8..$7EF`.

A new CPU witness runs the real grid builder with its stack outside the grid,
then executes both hit helpers and the 83/84 gate boundary against that stored
selector. Existing original-payload Copperline combat captures corroborate
A6=`$39FC`; they did not capture the selector and are not a new emulator run.
This is an initialized producer/consumer connection, not complete writer
coverage or a probability/distribution claim. Later cell changes, replacement
pixel offsets and remapped workspaces remain open.

Eight frame choices, the independently selected idle frame, and the second
visual descriptor/render state gain exact nonoverlapping owners totaling 232
bytes. Their reciprocal pointers, field accesses and all 512 selector cases
support the existing frame/descriptor/render types. The pointer table owns only
eight LONGs; its ninth unselected LONG remains raw. The two helpers update both
current and previous geometry and set ten-visit timers; expiry and explicit clear
update only current geometry. Normal-return contracts retain their tested
register identities and preserve unknown memory/escape effects. These contracts
require valid original records and a disjoint ABI stack; they do not prove alias
exclusion or lifetime for arbitrary replacements.

The per-object unsigned comparison consumes BYTE +$41. All 35 typed initializers
now expose that BYTE; +$40 remains unknown, while a symbolic WORD displacement
names the actual spanning read. Seven equipment pairs retain their byte widths;
lookup and full-register fallback differ in high-WORD and carry behavior.
Kriptonite reduction precedes Icelord/Thief overrides. Gauge tests compare every
CPU-written pixel byte and surrounding memory for all 41 normal charge states.

Thirteen distinct new CPU cases cover 256 item bytes, 24 equipment-override
cases, 144 opponent-clock states, 1,274 comparison boundaries, 2,560 health
subtractions, 1,536 player-fire states, 97 player-clock/gate states, 41 complete
gauge buffers, 512 feedback selections and sixteen timer pairs, plus the grid
alias witness. The 819 native checks are rerun after fixing a projection/render
omission exposed by the eight explicit table references. Each bounded absolute
reference now projects independently inside its array owner. Scalar array output
honors those spans. A canonical target that disagrees with the selected source
address retains its encoded-value symbol. The eight combat LONGs use the standard
encoded-value EQU spellings with explicit canonical targets and bidirectional
xrefs; this change introduces no new materialization/owner-expression inference.
The 150 focused checks cover
all three widths, removal, rejected crossing spans, native xrefs, exact rebuilt
bytes and mapping disagreement. Prior unaffected hardware results are reused.
The bounded one-past cursor behavior, SDK annotations, unknown
8-byte gap and previous font/scratch/ownership limits remain intact. The unrelated
Hunk numeric-pointer regression remains deferred. Full evidence and precise
limits are in `docs/validation/pandora-combat-scheduler.json`.

An additional opt-in bootstrap-copy fixture reports `full_source_policy_load_view`
where it expects `overlaid_by_runtime_copy`; it is not counted as passing. This
bootstrap-discovery boundary also reproduces with the published renderer in an
isolated temporary library and is recorded in the evidence file. The focused
reference tests explicitly preserve encoded values for suppressed copies.

The final C/vasm gate reproduces all 376,832 original bytes, receipt
`470e345b4786dd4f48489e7bc3c342975714bc47e017a8174a516ef6a65c69fd`.
The prior annotation audit passes, including all eight existing star-pixel pointer names. The earlier exact
gate was rejected for generalizing those scalar pointers; the corrected guard
applies only within wider owners. No target actions were accepted at that gate.

## Restart reconstruction, PRNG seeding and cursor row producer

The connected reset family now distinguishes runtime seed initialization from a
world restart. The seed entry selects four original LONG values with VHPOSR
WORD bits 2..3. Its stores write six bytes at absolute `$7E8..$7ED`, leaving the
prior WORD at `$7EE..$7EF` in the second state LONG. It then falls through into
one complete update. These absolute state bytes are separate from the existing
A6-relative grid-cell selector views.

Each update performs 32 bit steps: feedback is shift bit 3 XOR history bit 0;
shift left and append feedback, and latch outgoing bit 31 as history BYTE
`$00/$FF`. The high 24 history bits persist and do not affect output. D0/D1
return the second LONG, D2-D7/A1-A6 retain identity and the ABI stack balances.
The tests establish this arithmetic and retained seed tail, without a period,
entropy or gameplay-distribution claim.

A complete original reset witness covers all 35 sentinel-listed object records.
It restores initial flags, inventory and offer banks, selected item, item state,
HP and behavior script, recomputes the name from the current item-definition
byte, and clears script delay. Both banks copy eight
BYTEs forward; synthetic overlap tests expose the sequential copy effects, so
this is not a memmove contract. Perturbed NPC XY remain unchanged by this
routine; the player is reset separately, and later script execution is a
separate operation. Empty-table exit is also checked. The complete
reset leaves the absolute PRNG state unchanged while restoring mission/UI state,
3000 self-destruct service steps, Earth BCD `9999`, player XY `(241,866)`, camera
row 51 and the separate initial count of 67 active descriptors. The witness uses
valid original records and matching initial inactive parity; prior conditional
state-exchange and receptacle witnesses remain applicable to those branches.

The cursor producer handles sixteen input groups with sixteen-byte stride. It
copies the first two WORDs to rows at `$65374` and the next two to `$653B8`, then
skips eight bytes. Each output is 64 bytes; the preceding control LONGs remain
unchanged. This documents CPU writes in flat RAM, not file-backed allocation,
chipset DMA completion or complete pointer/writer ownership.

Eleven original-code cases cover 64 recurrence states, 256 chained updates,
76 beam/prior-tail combinations, history-bit independence, all 35 original
records, both overlap directions, null exit and all sixteen cursor groups.
The batch changes no framework or CPU implementation; the existing 819 native
and 150 focused framework results are reused. Unknown reset slots and the store
at `$64C0` receive no new interpretation. Existing owner extents, SDK/hardware
annotations, encoded-value names/canonical xrefs, both raw gaps and the separate
bootstrap fixture limitation remain preserved. Full evidence is in
`docs/validation/pandora-restart-random.json`. The 100 facts include 17 canonical
EQU aliases of existing RSSET fields, as required by the displacement catalog;
no new field widths or owner extents are introduced.

All 100 actions are accepted. The final C/vasm gate reproduces all 376,832
original bytes, receipt
`e6a4a304951afd1e41d8d86df378c2d875ee3a825400896acebdd0709319dbb8`. The audit preserves
every prior annotation/SDK expression, all owner identities/bounds, 86 assets,
reference spellings, both raw gaps and both history prefixes.

## Proximity audio transitions and fixed-center attenuation

The per-visit audio gate now names its complete local branch family and the
shared start latch. The native caller at source `$624` invokes the update. The
pianist's inactive bit inhibits it; otherwise it computes WORD magnitudes from
fixed `(840,168)`, sums in a WORD and compares unsigned with 256. Arithmetic
wrap is preserved: two `$8000` magnitudes sum to zero and enter the near branch.
Near visits store master-volume WORD `64-floor(distance/4)`, covering 64..1.

Interaction bit 0 starts mode 2 only on entry. Distance exit resets only on an
active edge and writes WORD `$0040`. Actor inhibition also resets only on an
active edge, but writes BYTE `$40` at the volume WORD's address, preserving its
low byte and producing `$40xx`. The source retains that original distinction.
The shared start helper saves D1-D7/A1-A6 and clears carry on return; the near
update instead saves only D0/D1/A6 around initialization. The shared helper's static reference
query found no callers, so no reachability or indirect-caller closure is claimed.

Fourteen original-code cases cover all 65,536 coordinate WORDs on each axis,
eight paired wrap/threshold cases, actor inhibition, real reset/initialization,
repeated visits and shared-latch register/carry behavior. They observe flat-RAM
CPU writes and normal return, without audible output or chipset DMA claims.
Initialization exceeds the bounded trace write-summary capacity; memory checks
do not assume that summary is complete. Existing records and a disjoint valid
stack are explicit assumptions.

All 33 facts are accepted: nine labels, six constants, fourteen operand styles
and four comments, reusing the existing inactive/latch symbols. Every prior
annotation and SDK/hardware expression, owner extent, asset, raw gap and history
prefix passes the preservation audit. The C/vasm gate reproduces all 376,832
original bytes, receipt `77904b2974ba3faf4cc3ab7d80d89d7e764f007e9ec67de99c7302dda96dc734`.
See `docs/validation/pandora-proximity-audio.json` for evidence and limits.
The separate bootstrap fixture boundary remains unchanged. The fixed reset store
at `$64C0` is resolved further in the following post-encounter section.

## Post-encounter passage and global item-state effects

The fixed absolute pointer at `$64C0` now names cell `(12,26)` of the original
90-column grid. Original macro selector 450, subcell 6, initializes it to tile
247, whose movement-block bit is set. Combat setup selects tile 49, whose bit is
clear. World restart restores tile 247. Completion restores tile 247 only when
the object's completion pointer is non-NULL, before calling it; NULL skips that
store. Priest completion selects tile 49 again. These are fixed-grid writes;
a different current `app_tilemap_base` does not redirect them. Complete indirect
writer/alias closure remains open.

Priest completion then enqueues the original 52-byte boast and falls through to
a shared `-15` item-state update. Bank-manager and thief completion use `+15`.
The sentinel table contains 35 original records, including the player. The
helper skips only inactive bit 1 and adds `D0.B` modulo 256: no saturation or
active-count bound, and duplicate pointers apply repeatedly. Item state retains
its established name; health, hostility or another gameplay meaning is not
proved. Every other record byte and the helper's general registers retain
identity in the checked returns. The original message spelling is preserved.

Three exact completion fields now carry explicit canonical references with
native incoming/outgoing coordinate checks; the existing readable callback
names and all owner extents remain intact. The local table-loop names, pointer
alias, named tile values, completion-field displacement and string name complete
this connected source family without changing behavior.

Seventeen original-code cases cover every byte delta/state pair, every flag
byte, both broadcasts over all 35 original records, duplicate/null tables, real
priest/bank-manager/thief callbacks and five completion-prefix variants. The
completion witnesses stop before state exchange at source `$7A06`; the existing
later NULL-node boundary is not repaired or counted as a passing full-combat
path. Flat RAM, valid original records and a disjoint stack are explicit limits;
bounded trace summaries are not treated as complete write logs.

All 31 actions are accepted, including seven presentation corrections. Every
prior annotation, hardware/SDK expression, callback spelling, owner bound, asset,
raw gap and history prefix passes the preservation audit. C/vasm reproduces all
376,832 original bytes, receipt
`1709c3d5c52e0a53dfd7c188d8e8f607cfc7ad72756990d7973b10f71e79a852`.
Evidence and limits are in `docs/validation/pandora-post-encounter-effects.json`.

The renderer now honors an explicit immediate value EQU over an automatic
address name while preserving explicit source/SDK names. Resolved pointer
analysis targets remain available, but unused automatic interior labels no
longer force existing assets inline. Mismatched immediate EQU values refuse
before append. All 819 native and 192 focused framework checks pass, including
eight new cases for direct/register-mediated stores in local and runtime
address models, retained targets, complete asset extents, C/vasm equality and
atomic refusal.

Two provisional forward asset-label expressions were replaced by equal numeric
runtime EQUs, with the proved owner/offset relationships retained in the evidence.
The C assembler's forward source-expression boundary is separate work; these
semantics do not require changing ownership or assembly dependency resolution.
The preparation benchmark was not repeated. The next useful gameplay swath is
the remaining item-transfer/inventory effect code around the completion callbacks.
The broader full-game and alternate-layout gates remain open.

## Trade selection, exchange and thief item loss

The nearby-object service and its direct trade helpers now have connected local
names and symbolic item IDs, readiness bits, field offsets and four-entry table
bounds. Existing public helper names remain unchanged. In particular,
`is_tradeable_item_id` sets carry for IDs 7..21 after subtracting 7 from the low
byte; this range drives combat-item selection. The main predicate returns carry
clear to request combat and carry set to suppress it. Its carry is not a general
trade-success result. A matched offer enters counteroffer selection only when
its threshold is strictly below the object's unsigned item state; the caller
returns carry set even if that selection succeeds with carry clear.

Counteroffers inspect four inventory pairs, skip IDs 0 and 1, and keep the first
smallest positive threshold/value gap. Only gaps 1..127 succeed. Selection copies
the ID and sets readiness bit 3 without consuming the slot. A later service visit
with fire pressed performs the exchange. Disabled objects are skipped; thief
handling clears held IDs 2..255 before readiness/fire checks and does not write
the received item into the thief inventory. Clearing readiness visits all 35
original table entries, including inactive objects.

Exchange preserves the original ordering and boundary behavior. The first
matching inventory ID is replaced before the offer search. A failed four-entry
search leaves its cursor at entry+8, so subsequent accesses can use +8/+9 beyond
the existing eight-byte owner. Exact table aliasing can make the earlier ID write
become the offer match and then be cleared. The owner bounds are retained. The
announcement also retains its original code/data boundary: its literal has no
NUL, and the following `MOVE.L D0,D7` opcode supplies another dot followed by NUL.

Twenty-five original-code CPU cases cover all item bytes, every threshold/state
and threshold/value pair, first matches and ties, all 25 found/missing exchange
index pairs, exact aliasing, all NPC flag bytes, all normal thief-taken IDs, and
complete paths through initialized original UI/audio routines. These are flat-RAM
witnesses with valid original records and a separate stack; they do not establish
DMA completion, arbitrary record lifetimes or full-game reachability.

The 78 accepted actions comprise 21 local labels, 14 equates, 36 operand bindings
and seven semantic comments. The target had reached the native 512-equate limit;
the coordinated bound is now 1,024. Forty-eight focused framework checks and all
819 native checks pass, including full-capacity cloning, both assemblers, duplicate
updates, real atomic overflow refusal and direct Python/C policy loading.
Bit-number operands carry no byte width;
the immediate-EQU validation now accepts equal decoded values for them while
retaining atomic refusal for mismatches. Six additional cases cover `BTST`,
`BSET` and `BCLR` through the normal catalog, C and vasm. The earlier preparation
benchmark was not repeated.

Every previous annotation and hardware/SDK expression, owner bound, asset, raw
gap and history prefix passes preservation checks. C and vasm reproduce all
376,832 original bytes; the receipt and supporting evidence are recorded in
`docs/validation/pandora-trade-selection.json`. The next connected question is
how selected combat items supply encounter statistics and defeat/transfer effects.
The broader full-game and alternate-layout gates remain open.

## Receptacle entry latching, attachment transfer and restart

The item-receptacle protocol now has named scan branches, role bits, distance
and transfer constants, a hit-point field expression, and a named brain-feedback
entry. Existing helper names are retained. The counted descriptor scan rejects
outside-view states first, then prioritizes checkpoint bit 4 over receptacle bit
2 and proximity-animation bit 0. An inactive player skips receptacle handling.

Receptacle distance uses wrapped WORD arithmetic on descriptor coordinates plus
state offsets and equal 16-pixel biases for both participants. The magnitudes
and their sum wrap; only an unsigned sum below 28 is near. A first near visit
sets attempt bit 0 before testing the saved attachment or held item. A busy hand
or incorrect return therefore consumes the attempt. Further near visits skip
work; a far visit clears only this bit, leaving the other seven flag bits
intact. There is no fire-button check in this protocol.

The historical `deposit_item_in_receptacle` entry saves the visual attachment,
detaches it from the state, and gives the required item ID to a player holding
ID 0 or 1. It does not filter the copied ID or reject a NULL attachment. When a
saved attachment is nonzero, an exact required/held BYTE match restores that
pointer and clears both saved pointer and held ID. Both successful paths exit
the entire descriptor service. An incorrect return attempts to enqueue the
existing message plus a blank message and continues the counted scan. The
existing six-byte interaction records and conditional state tails keep their
identities and bounds.

Brain pickup sets the existing event bit 0 once and assigns the whole HP WORD to
95, even when HP was higher. It then draws the health display and runs the
original feedback sequence `$11C`. While event bit 0 remains set, brain pickups
still transfer the item but skip this effect and its audio. The first-effect
path changes A4 to the health overlay and A5 to the player. These are original
effects, not gameplay repairs or a claim that the item always increases health.

Six explicit restart-pointer references now connect the existing 24-byte array
to its existing source owners, with incoming and outgoing native coordinate
checks. The first LONG remains numeric; the other five retain standard
encoded-value EQU spellings, with canonical relationships verified
independently. No source-owner label expression or runtime-view materialization
is forced. Restart visits exactly six entries, clears the whole interaction
flags BYTE, and restores then clears nonzero saved attachments. If states share
an interaction record, the first visit consumes its saved pointer; later aliases
retain their current attachments. All 64 saved-pointer presence masks were
checked on the six original records.

Thirty-three distinct original-code CPU cases cover both full WORD-axis sweeps,
wrapped sums, all state/player/latch/event flag bytes, all 65,536 return-ID
pairs, all copied IDs and held-ID eligibility, two-descriptor
early-exit/continuation, reentry, six complete brain-effect paths and ordered
restart aliases. Controlled UI mode makes selected-name refresh return
immediately; the brain cases execute health drawing and initialized original
audio. Flat RAM, the existing copied payload view, valid records and a separate
fresh call frame are explicit inputs. No DMA completion, arbitrary attachment
lifetime, copy completion or full-game reachability is established by these
witnesses.

All 45 actions are accepted: eight labels, ten equates, fifteen operand
bindings, six canonical references and six semantic comments. No framework
implementation changed; the prior 48 focused framework and 819 native checks are
reused. The preparation benchmark was not repeated. Previous annotations,
hardware/SDK expressions, owner bounds, assets, raw gaps and history prefixes
pass preservation. C and vasm reproduce all 376,832 original bytes. The
verification receipt and supporting evidence are in
`docs/validation/pandora-receptacle-protocol.json`. Checkpoint
contact/authorization and its attachment-hold traversal remain the next
connected control-flow question. Full-game and alternate-layout confidence
remain separate open gates.

## Checkpoint contact authorization and the connected escape latch

Checkpoint contact now has complete local branch names and symbolic card IDs,
rectangle bounds, coordinate biases, authorization bits and feedback requests.
The four descriptor identities retain their existing field labels and pointer
spellings. Native queries verify all six identity comparisons against those same
canonical owners. The shared `$102` feedback helper is named for both ID failure
and item handoff, retaining its three observed direct callers.

Contact first skips an inactive player or an already-triggered escape.
Descriptor XY plus state offsets and the player XY use wrapped WORD arithmetic.
Standard bias is 16 on each participant; descriptor identities 20 and 21 use Y
bias 32. The unsigned magnitudes are tested independently: X below 18 and Y
below 32, with no Manhattan-sum threshold. Far visits release the node
header-hold bit through the attachment chain, but leave movement inhibition and
the escape-card latch untouched. Near visits clear movement inhibition before
card checking.

Descriptor identities 18/19/20/21 require exactly ID Commander 48, ID Lieutenant
Commander 49, ID Engineer 50 and ID AWOL Officer 55. They select seen bits
0/1/2/3. An unrecognized descriptor that reaches the checkpoint path skips all
four card checks and shares bit 0. Within contact handling, only the in-range
identity 21 path clears and recomputes escape-card bit 4; a wrong card clears it
before damage, while far, inactive and escape-triggered visits preserve its
previous value.

Authorization sets the selected seen bit. A clear-to-set transition requests
feedback `$118` and increments the count BYTE, wrapping modulo 256. An already
set bit still holds the attachment chain but neither recounts nor requests that
feedback. Count is not recomputed from the bits. Both hold and release visit the
root and each non-NULL attachment, changing only node header-hold bit 0. They
retain all clock/phase bytes and other mode bits. The four original checkpoint
chains contain 1/1/2/2 states and six distinct nodes. Arbitrary replacement
chains, cycles and node lifetimes remain outside this proof.

A rejected card inhibits movement and subtracts ten from only the HP low BYTE.
Only wrapped results 1..127 survive; the high HP byte is retained on that path.
Results zero or 128..255 enter defeat before the computed low byte is stored.
Survivors draw health, request the shared `$102` feedback and return from the
whole descriptor scan. Defeat installs the existing animated state and geometry,
resets its node, marks the player inactive, exchanges active/saved states,
clears the whole HP WORD, loads exit delay 70 and queues the existing outcome
messages. This path also returns from the whole scan.

The connected movement consumer checks escape-card bit 4 and decoded tile low
WORD 236; it does not reread the selected card or checkpoint count. On
acceptance it installs the escape pose, removes its animation node, clears four
audio-local bytes, requests audio mode 1 and preserves A6 around initialization.
It presets the escape-triggered bit before the existing outcome helper, so that
helper preserves the inherited exit delay. Three complete original
consumer/callee paths retain delays 0/70/255. The tile-decoding prelude is
statically inspected; these executions start with an explicit decoded tile at
the guard, rather than proving movement, loader or joystick reachability.

Forty distinct original-code CPU cases cover 262,144 axis inputs at both Y-bias
modes, all 1,280 descriptor/card choices, both guard bytes, 1,024
seen-mask/index combinations, all count bytes, 512 chain-mode inputs and all HP
low bytes at four high-byte values. Full calls cover first/repeated
authorization, count wrap, two-descriptor continuation after feedback,
rectangular boundaries, three survivor and four animated-defeat/outcome paths,
all six original chain nodes, 1,536 escape flag/tile choices and the three
inherited-delay paths. Tests use initialized original UI/font/audio data, flat
RAM, explicit MMIO shadows and fresh disjoint call frames. DMA completion and
full-game runtime confidence remain separate open questions.

All 57 actions are accepted: fifteen labels, thirteen equates, twenty-one
operand bindings and eight semantic comments. No framework or CPU implementation
changed; the prior 48 focused framework and 819 native checks are reused, and
the preparation benchmark was not repeated. Every prior annotation, hardware/SDK
expression, owner bound, asset, pointer presentation, raw gap and history prefix
passes preservation. C and vasm reproduce all 376,832 original bytes. Evidence,
canonical relationships, scope and the verification receipt are recorded in
`docs/validation/pandora-checkpoint-contact.json`. The remaining
proximity-animation branch within the same descriptor service is the next
connected control-flow family; broader runtime and alternate-layout gates remain
open.

## Proximity sequence control and frame consumption

The remaining proximity branch of the descriptor service and the shared frame
consumer now have meaningful local names. State role bit 5 selects sequence bank
1 and descriptor X bias 8; otherwise bank 0 and bias 16 apply. Player XY and
descriptor Y use bias 16. Descriptor state offsets apply before the wrapped WORD
subtractions, negative magnitudes and sum. An unsigned sum below 44 selects
near; 44 or greater selects far. The sum can wrap, including to zero. The
earlier outside-view and role-priority rules remain unchanged. After that
dispatch, player inactive, escape-event and UI flags do not gate the proximity
branch.

An already-selected sequence pointer suppresses all node writes and feedback,
even when clock, mode or count are stale. A different pointer requests feedback
`$30F`, installs the sequence, clears header-hold bit 0, sets hold-at-end bit 2
and clears the clock WORD. Frame count, phase step, XY pointer, padding and all
other mode bits survive. The caller saves A0 around real feedback; the near
path's additional balanced push/pop is retained. Neither path consumes the
descriptor loop counter. Multi-descriptor tests include both changed/current
orderings and a later NULL-state descriptor.

The related consumer adds phase step to the phase BYTE modulo 256. Bit 7 of the
result advances the frame; addition carry is not the condition. At frame end,
chain mode wins over hold-at-end; otherwise the sequence loops. Those existing
chain and held/active XY semantics are retained. The proximity selector does not
normalize these retained playback inputs or make arbitrary counts safe for the
selected owner. For the original six-frame, step-64, non-chained nodes, complete
near and far cycles reach their held geometry after twelve animation calls.
Subsequent proximity visits keep the held node without restarting it.

The native source inventories contain eighteen descriptor pointers, fifty-four
pointer fields in their eighteen nodes, and twenty-eight held/active frame
pointers across four existing 28-byte sequence owners. Six stored node
selections point to far bank 0 and twelve to far bank 1. These stored inputs are
preserved; selection is driven by role flags and distance, without assuming that
the stored bank already matches the role. A changing-selection witness executes
real feedback on all eighteen original source nodes and checks their exact
retained fields. All four sequence LEAs retain their prior expressions and
canonical targets. The earlier numeric/encoded-value presentation boundary is
unchanged.

Twenty-eight distinct tests execute unmodified original code. They cover 262,144
axis words at both X biases, eight offset/wrapped-sum cases, all isolated role
flag bytes, 768 player/event/UI flag cases, 1,024 same-pointer node states, 512
paired mode/count/step store checks, four complete feedback/stack paths, both
near/far cycles for each bank, every phase/step BYTE pair, two multi-descriptor
scans and the eighteen original nodes. Existing audio-stub selection tests
remain local evidence and are not promoted to unmodified-call evidence. Earlier
published chain/XY and typed-bound proofs are reused. These are explicit-input
calls under the copied-payload view, flat RAM and valid audio data; no DMA,
audibility, arbitrary graph lifetime or full-game reachability is established.

All 32 actions are accepted: fourteen labels, four equates, nine operand
bindings and five semantic comments. One label introduces the proximity block;
the other thirteen replace anonymous locals. No framework or CPU implementation
changed; the prior 48 focused framework and 819 native checks are reused,
without repeating the preparation benchmark. All previous comments, SDK/hardware
expressions, layouts/types, owner bounds, assets, pointer forms, raw gaps and
history prefixes pass preservation. C and vasm reproduce all 376,832 original
bytes. Evidence and the verification receipt are in
`docs/validation/pandora-proximity-animation.json`. The partially documented NPC
item-handoff path and its panel/queue/state-exchange effects are a useful next
connected slice; full-game and alternate-layout confidence remain open.

## NPC item handoff and connected consumers

The officer handoff now uses the shared A5 world-object fields, named
return/state-exchange branches and the existing inactive/panel equates. The
adjacent inventory-close scan and holding-name branches also have meaningful
local symbols. Player inactive bit1 is the only entry guard; giver inactivity
does not prevent an explicit call. Transfer overwrites held ID with the selected
BYTE, including 0/1, clears selection and only the first inventory slot ID, and
sets giver inactive. The value byte and later slots survive, even if the
selected ID appears later in the inventory.

The fixed officer node reset remains separate from the state exchange's incoming
giver node reset. Both clear header-hold and the clock WORD; the outgoing giver
node is retained. No original stored pointer, initialized bank asymmetry,
frame/phase behavior or prior animation proof changed. A direct second handoff
can transfer 0 and exchange states back; script inactivity and direct-call
behavior must not be conflated.

When panel-active is set, the original routine saves D0/A0/A5 around panel
close. The close recomputes cached Kriptonite from four carried IDs, four pocket
IDs and held ID, retaining all other event bits. The handoff redraws nearby
carrying using the cleared giver selection, updates holding with 0/1 normalized
to NOTHING, and executes original feedback. Ten full cases verify both name
pointers with original message/UI/state/audio callees. Three further full cases
verify A5 retention through immediate message drawing with/without ticker clear,
and busy status with ticker clear. An explicit post-message type seed restores
the giver field names after native analysis conservatively drops the entry type
across the call. Existing body-restore and queue/DMA ordering evidence is
reused; these new full cases keep nearby-object inventory bit3 clear.

The exact 45-byte NUL-terminated handoff message has a bounded owner and
character representation. Its original Don"t spelling and quotes are preserved.
The following 48 bytes remain unclassified. Native incoming/outgoing queries
resolve the message LEA; the original typed script callback LONG at 23C8 still
resolves to collect_world_object_item. That data pointer explains a caller
absent from the ordinary code-reference query.

Twenty-one distinct unmodified-code CPU cases cover all 256 player flags,
selected IDs, giver flags, fixed-node modes and panel-gate flags; thirteen
complete handoffs; a second direct call; all nine Kriptonite locations plus
absence; and the original officer script. Under the explicit fixture inputs, the
script reaches handoff on interpreter service 95, then installs delay 10000 at
cursor 23D0 in the same service. Later calls count down before inactive dispatch
inhibits continuation. This proves a scoped original-script path, not
ordinary-gameplay reachability. Flat RAM, valid copied-view records/fonts/audio,
explicit busy/immediate status contexts and MMIO request shadows do not
establish DMA completion or audibility.

All 22 actions are accepted: eight local labels, one message label, two register
entry types and one explicit post-message giver type, two existing-equate
bindings, five semantic comments, one message owner and its character element,
plus one short-role refinement. C and vasm reproduce all 376,832 original bytes.
All earlier comments, SDK expressions, types/owner bounds, 86 assets, pointer
forms, raw gaps and history prefixes pass preservation. The untyped-element
native role limit (63 bytes) is documented in docs/restoration-interfaces.md;
the new owner uses the short message category and keeps its detailed evidence.
Longer free-form role support remains open. No framework implementation changed;
reuse 48 focused framework and 819 native checks and earlier related CPU proofs,
without repeating the preparation benchmark. Evidence and receipt are in
docs/validation/pandora-npc-handoff.json. The next connected question is which
original scheduling/scene conditions select this officer script and expose its
post-handoff state; full-game and alternate-layout confidence remain open.

## Unselected world-tile source cells and bounded native storage

The 33 previously unclaimed cells interspersed with the 25 established
world-tile asset owners now have individual 128-byte source owners. A shared
8-byte world_tile_planar_row contains four UWORD plane values; each cell binds
16 raster rows. This restores 4,224 source bytes as 528 rows and 2,112 typed
WORD fields. Existing asset files and owner identities/extents are retained; no whole-atlas envelope
owner or exclusive runtime allocation is introduced.

The established viewport packet reads 64 packed WORDs with source modulo 0 and
40-byte destination intervals. Together with the known display plane
interleaving, this gives four plane WORDs per 16-pixel raster row and 16 rows
per cell. All 33 cells decode as coherent pixel graphics under that layout. This
supports their source format; it does not establish use by the game. Each cell keeps its numeric atlas index. The grayscale contact sheet and its
numeric atlas-index legend are recorded in
docs/validation/pandora-unselected-world-tiles.json and
pandora-unselected-world-tile-cells.png.

None of these 33 cells is selected by the original 43x30 macro map. Cell 499
appears once, as scalar offset F980 in definition 447 r2c0; the original macro
map never selects 447. The other 32 cells are absent from all 468 definitions.
The previously restored 475 selected cells remain unchanged. Later mutation,
aliases and indirect writers can differ; this is not an exhaustive runtime
ownership, mask-writer or gameplay-reachability contract.

The full family was reviewed before mutation. Native row extents cover all 4,224
bytes, with 4,206 exposed bytes matching the original binary. One 34-byte folded
DCB row exposes only 16 bytes, so that prefix was not treated as full-field
proof. Final export compares every emitted typed WORD with the original bytes; a
fresh native window exposes the full 34-byte run as 17 WORD rows. The generic
folded-row cache boundary remains unchanged.

The complete 67-action candidate exposed both 16,384-entry native policy limits
before any target action was appended. Both pointer-backed collections now
permit 32,768 entries, retaining their 16-bit counters, dynamic allocation and
atomic overflow refusals. Updated tests cover complete boundary retention,
duplicate labels, 32,769-entry refusal, object enrichment, typed-array preflight
and wide reservation requests. All 22 focused capacity tests and 819 native
checks pass. The longer-role limit remains deferred: untyped owner role text
exceeding 63 bytes blocks element preflight, but the short world_tile_pixel_rows
category works here.

All 67 target actions are accepted: one shared row type, 33 disjoint owners and
33 typed arrays. Source review preceded both catalog batches; a final explicit
export followed their completion. C and vasm reproduce all 376,832 original
bytes. All previous names, fields, SDK expressions, comments, types/owner
bounds, 86 assets, pointer forms, raw gaps and history prefixes pass
preservation. Earlier unchanged tile-grid, packet and display CPU proofs are
reused; no new gameplay confidence, full audit or preparation benchmark is
claimed. The remaining semantic use of the unselected cells stays unknown.

### Typed tile assets retain compact source packaging

The 33 unselected atlas cells now render as individual 128-byte INCBIN assets.
Their atlas-index labels, exact owner bounds, sixteen-row arrays and all 2,112
typed plane fields remain in analysis. This corrects the expanded pixel WORD
output of the preceding slice without assigning unknown gameplay meanings.
The general binary-assets threshold is 128 bytes; seven other already-classified
small bitmap spans now export as well (40 new assets, 126 total). All 86 prior
asset identities, bytes and bounds remain unchanged. Source outside the exported
numeric payloads, SDK expressions, pointer forms, raw gaps and history prefixes
are preserved. All 376,832 bytes match the original through both C and vasm,
receipt c6b7d374f3711a317f3aa54ad1336e01cfeb5dbeebfad4009c6e6e44ee9e757d.
Five new typed-media tests, 40 existing package/policy tests, one full native/vasm
integration case and 820 native checks passed. Details and asset hashes:
`docs/validation/pandora-typed-media-incbin.json`.

### Outcome and rank selection

The connected outcome selector now names eleven branch stages and six literal
mercenary rating messages. Eight shared threshold/index constants replace ten
matching literals. The existing numeric salvage pointer table remains intact.
Nine new unpatched original-code CPU tests call the real status FIFO routines.
They cover all 256 self-destruct BYTE values across escape and zero/nonzero Earth
deadline inputs, all 256 defeat counts, all 128 prelatched event bytes, all 256
wrapping salvage counts with four duplicate eligible items, all 256 held IDs on
the posthumous path, repeated calls and queue occupancies 0/14/15/16.

The latch precedes all work. Negative self-destruct state takes priority; the
Earth WORD is tested for zero only. Exactly four carried IDs contribute, with
duplicates and BYTE wrap. Escape with count >= 6 selects science rating
min(count-6,4); otherwise mercenary thresholds are 5/10/12/14/18. Non-escape
always selects posthumous mercenary and sets bit 1 of the held-item ID, not
player flags. Full FIFO does not undo these effects; final rating still replaces
the shared duration. These are explicit copied-view CPU inputs, not a claim of
ordinary-gameplay reachability.

All 376,832 bytes match the original through C and vasm. Prior comments, types,
owner bounds, 126 assets, SDK and pointer expressions, raw gaps and histories
remain preserved. See `docs/validation/pandora-outcome-ranks.json` for native
coordinates, incoming references, test domains and the verification receipt.
Unselected atlas semantic use remains unknown.

### Self-destruct console input, validation and display

The connected console family now names fourteen branch stages and its nine-byte
card-number text, with ten shared card/count/plane/event constants, fourteen
equal-valued operand bindings and eight semantic comments. Existing app slots
and the twelve-byte submitted-name pointer prefix retain their names and bounds.
Twenty original-code CPU tests cover all BYTE values for UI flags, fire, selected
item cache, state, disk/card admission and both counters. Six qualifying orders,
three repeated-color triples and three invalid-color positions run through the
real audio dispatch, name resolver, holding UI and compact text renderer.

Input gates panel/no-fire/unchanged selection before updating the cache. A changed
held ID is cached before state and range checks; redraw then resamples holding.
State 0 consumes only SDI disk 38, advances to 1 and sets context bit6. State 1
consumes card IDs 32..37; only blue 33/scarlet 35/ochre 36 increment the qualifying
BYTE, including wrap. Three qualifying submissions arm FF without order or
uniqueness checks. Other qualifying counts reject 2. The full disk-to-three-blue
case preserves an explicitly inherited BEEF countdown throughout; arming does
not reload that counter. Ordinary-play timer state and later bit6 use stay open.

Name stores use submitted_BYTE*4 before incrementing; completion tests only the
incremented low BYTE for 3. All256 bounded prefix cases show the absence of a
three-slot guard. The declared three-pointer storage prefix is retained; synthetic
corrupt counts do not justify expanding ownership. Normal redraw chooses prompt 0,
card list 1, rejection 2 and accepted text for every other state. Validation success
enters the header/name path directly with FF, distinct from an ordinary FF redraw.
The clear prefix writes 384 thirty-byte plane rows at stride 40 from cell(2,2),
with every ten-byte row gap and both outer fences verified.

BLIT-ready MMIO is a RAM shadow and performs no DMA. Full rendering exceeds the
bounded range-summary capacity; tests inspect actual guest memory and return
state instead of claiming a complete write trace. No ordinary-gameplay admission,
exclusive storage or complete-writer confidence is added. Existing 820 native,
package-policy/media and outcome checks are reused without a framework change.
All 376,832 original bytes match through C and vasm; all previous source, comments,
fields/types/owners, 126 assets, SDK/pointer forms, raw gaps and history prefixes
are preserved. The 128-byte INCBIN policy and 2,112 typed tile fields remain intact;
unselected atlas gameplay use is still unknown. Receipt, native xrefs and test
domains: `docs/validation/pandora-self-destruct-console.json`.

### NPC item-response callbacks and selected service

Restored eight connected callbacks, their range/cooldown helpers and carry-controlled
message path: 48 accepted actions name thirteen branches, the four-pointer chemist
quote table, twelve exact ASCII messages (487 bytes), and matching constants/fields.
Eleven original-code tests in `tests/test_pandora_item_responses.py` cover all item
and latch bytes, range edges, all four choices through the real PRNG, inactive/panel
gates, cooldown WORD boundaries, and real carry/null/full-FIFO dispatch. Musician
gin sets a one-time latch without a cooldown; the chemist's latched Bible case can
fall through to NPC-held Shakespeare. Dispatch uses the +$10 interaction message;
queue refusal preserves callback effects. A decrement reaching zero dispatches on
the next eligible selected-object visit. Controlled RAM/queue calls add no ordinary
gameplay or hardware claim. C and vasm match all 376,832 original bytes, receipt
`aafb863b5f05ecc104195d4b75d9c7bf941281c0b20e914e0045e86d0ffe6c46`. Prior comments, fields/types/owners, SDK/pointer forms, raw gaps
and histories are preserved. All 126 assets, 2,112 typed tile fields and the
128-byte INCBIN policy remain intact; atlas gameplay use stays unknown. Unchanged
framework, console/outcome and package checks are reused; no new framework code.

### NPC feedback and secondary playback

Accepted 73 connected annotations for four feedback bodies and the secondary
voice producer/dispatcher/service: branch names, typed field/sizeof constants,
SDK AUDx writes and the 41-byte gardener message. Thirteen original-code tests in
`tests/test_pandora_feedback_playback.py` cover byte gates/counters/selectors,
Wackobrain's 43 declared headers, shared-channel preemption and real expiry/reset
paths, envelope/period boundaries and the paired interval WORD copy. Wackobrain
restarts on every eligible matching-geometry visit; the other handlers share
channel-2 ticks, and inactive reset can retain a pending nonzero count. Expiry
precedes update-disable; signed period clamping affects only the register write.
Sequence $214 has only its self-loop in current incoming references; external
use remains unknown. RAM/MMIO shadows establish no DMA, audible output or ordinary
gameplay call order. Before target mutation, an actual 26-byte instruction image
preflighted all EQU, zero-word/indexed-field and SDK forms through C and vasm.
Full-target C/vasm reproduces all 376,832 bytes, receipt `e3550d98e205676d94c1181fdd2315846eae564cc504c78c2f5be09e0a729330`.
Prior annotations, field/type/owner bounds, SDK/pointer forms and histories pass
preservation; all 126 assets, 2,112 typed tile fields and compact 128-byte INCBIN
policy remain unchanged. Earlier unchanged checks are reused; atlas use is unknown.

### Player movement probes and coordinate commit

Accepted 55 annotations: twelve branch names, twelve constants, 26 operand
bindings and five semantic comments. Horizontal movement probes its chosen edge;
vertical movement tests left, midpoint and right foot points in order. Only the
right vertical probe recognizes consoles, before its block-bit check. Tile actions
precede commit inhibition. Lateral drift changes X and suppresses Y commit while
recording and animating the requested axis. Y receives one WORD boundary correction;
vertical tile lookup drops the row product high WORD while the shared helper keeps
it. Status bit 6 is cleared by hold; its wider meaning remains unknown.

Eleven original-code tests in `tests/test_pandora_player_movement.py` cover all
UI/status/object, prior-direction and inhibition BYTEs, scaled axis WORD cases,
probe coordinates/order, all 508 tile IDs with original movement bits, console
priority, node reuse/switch/hold and coordinate/row-width boundaries. Controlled
RAM maps establish encoded behavior, not ordinary gameplay admission or atlas use.
A 64-byte instruction image preflighted every intended symbolic form before the
native batch. Full-target C/vasm matches all 376,832 original bytes, receipt
`b2609dd069779559fcdec4fa0fa8c70851a7fed56e9648d67a84c31c5a152cbc`. Previous source, comments, fields/types/owners, SDK/pointer
forms, raw gaps and histories pass preservation; all 126 assets, 2,112 typed tile
fields and the compact 128-byte INCBIN policy remain intact. Unchanged prior checks
are reused. Failed ID-recheck continuation remains open. Existing substantial
gaps also include mutable callbacks/state writers, complete buffer/DMA lifetimes,
remaining resource-bank semantics and the original uncopied-tail purpose.

### Inventory cursor selection and sprite handoff

Accepted 92 connected annotations: eleven branch names, six scalar names,
25 constants, 42 operand bindings and eight comments. Nearby inventory stages four
ID bytes separately from record value bytes; the existing four-byte staging owner
keeps its bounds. Eligible no-fire visits release selection even without motion.
Unit input starts motion that bypasses fire/release for eight X services (96 pixels)
or four Y services (8 pixels). Twelve original-code tests in
`tests/test_pandora_inventory_cursor.py`
cover byte gates/latches/classifiers, all joystick masks across cursor rows/columns,
WORD countdown wrap, real swaps, staging/name consumption and palette/header writes.

The three actual caller sequences remove an inherited-register ambiguity: latched
selection skips the player LEA, so main camera rendering leaves A4 at tile-grid
end for the subsequent +70 read. Both modal call pairs retain player A4. Context
bit 7 therefore cannot be assumed to cache the held item; no current downstream
consumer is established. The raw +70 operand retains its unproved base type.
Binding reinstalls sprite pointers independently of the hide latch; snapshotting
rearms hiding. VBL rewrites both headers even with blank pointers, preserving pixel
rows. Snapshot X/Y WORD stores have no established reader or restoration role.

A 148-byte instruction image preflighted every EQU, operand and scalar/array-alias
form through C and vasm before mutation. Full-target C/vasm matches all 376,832
original bytes, receipt `1154bdbbaca6bb04ed32efca2645c572e4afcc4309b5715f70d3b98e2902b85c`. Earlier source/comments,
fields/types/owner bounds, SDK/pointer forms, raw gaps and histories pass preservation;
all 126 assets, 2,112 typed tile fields and the 128-byte INCBIN policy remain intact.
Unchanged checks are reused. RAM/MMIO shadows perform no DMA and establish no ordinary
gameplay admission, complete writer/lifetime coverage or original tail purpose.

### Modal handoff and terminal display

Accepted 56 annotations: nineteen code stages, ten constants, sixteen operand
bindings, five ASCII headings/error strings (58 bytes) and six comments. Both
entries retain the active descriptor list/count, snapshot XY/attachment geometry
once and exchange front/back/display banks. Idle modal visits retain that snapshot
and omit world-script/self-destruct ticks. Initial release gates test directions,
independently of fire. Terminal normal exit waits for direction release; self-destruct
returns with direction held. Both restore the world header/base and request a
two-service zero-delta camera refresh without exchanging banks again.

Both actual F7 branches bypass that restoration. Warm setup through the next title
entry resets mission/UI but retains modal dimensions/base and the saved header.
Later title/restart behavior remains unproved; no intent or bug claim is added.
Terminal updates have no UI/fire gate, skip unchanged IDs, and resample holding
after display clearing. The renderer advances A3 to the adjacent second error line.
Ten original-code tests in `tests/test_pandora_modal_handoff.py` establish these
paths, exact clear fences and full eight-card/invalid-sample rendering. Existing
swap, camera, nearest-message and self-destruct input checks are reused.

A 72-byte original instruction preflight covers all new EQU/immediate/d16 forms.
Full-target C/vasm matches all 376,832 bytes, receipt `200054450739ccd31b5ceb2afebbb47bfb002bcf74706855c9848266dbcbc10f`.
Earlier source, comments, fields/types/owner bounds, SDK/pointer forms, raw gaps
and histories pass preservation; all 126 assets, 2,112 typed tile fields and the
128-byte INCBIN policy remain intact, including the exact caller-dependent A4
distinction. RAM/MMIO shadows perform no DMA or asynchronous frame production and
establish no ordinary admission, complete ownership/lifetime or whole restart.

### Title-to-gameplay restart consumers

Accepted 59 annotations: fifteen code stages, fourteen constants, twenty operand
bindings, logo/credits strings (125 bytes) and seven comments. Six original-code
tests in `tests/test_pandora_title_restart.py` carry world/terminal/self-destruct F7
paths through title, both initial bank renders, seven overlay registrations and
initial world updates to the main-frame wait. The retained 20x8/row51 case starts
its pointer walk at modal-base+4080. Per-bank row offsets are 4080,3520,2960,2400,
1840,1280,720,160: 140 of 160 packet reads lie outside the declared 640-byte modal
cell prefix. The renderer subtracts one grid size after each row. These are CPU
read addresses/programmed packets; DMA, pixels and ordinary admission are unproved.

Title reveal compares the LONG counter to entry+150 with wrap using equality.
Skipped equality skips the block; repeated equality repeats its drawing/audio
initialization. The two 16-step palette counters use foreground iterations, and
a first-poll fire can leave before reveal. The title audio service bit is set at
reveal and cleared by feedback start; gameplay VBL audio is independent. A bounded
$400..$7E8 runtime address view names the 100 ten-byte records without asserting
allocation/lifetime or a global typed-array owner; byte9 remains unknown. The
192-byte shared gradient prefix and following 64 seed bytes have explicit fences.

A 70-byte instruction preflight covers all fourteen EQU forms and immediate/d16
styles. Full-target C/vasm matches all 376,832 bytes, receipt `0a2ba9868ee40944a838a66e5a40dbbd3c8d285800367f6e79e6781799b9ec22`.
Earlier source/comments, fields/types/owner bounds, SDK/pointer forms, raw gaps
and histories pass preservation, including the exact prior A4 and F7 distinctions.
All 126 assets, 2,112 typed tile fields and the 128-byte INCBIN policy remain intact.
Unchanged checks are reused. No asynchronous IRQ/DMA, complete ownership/lifetime,
ordinary timing, resultant pixels or intent/bug claim is added.

### Earth countdown and four-digit text controls

Accepted 44 annotations: twelve code stages, one app scalar, eight constants,
fourteen operand bindings, two data names, a 17-byte ASCII alphabet and five
effective comments, including one appended scope clarification. The countdown
uses main/modal service visits: divider old1 reloads4 and decrements nonzero BCD;
old0 wraps to255. Every post-check visit with nonzero WORD and zero low BYTE
requests sequence $306, including visits between decrements. These are not seconds.

Normal valid-BCD zero-expiry notification follows drawing and its player/event
guards; combat skips that path. Later zero visits do not retry skipped warnings.
The separate SBCD-carry branch queues warnings before storing the high byte; its
explicit interior-entry test does not establish countdown inputs producing carry.
The existing warm-start/self-destruct writers and outcome consumer retain their
prior meanings. The formatter accepts all hexadecimal nibbles, blanks leading
zeros, and tracks nonzero before applying the low-four-bit text skip mask. A masked
nonzero still enables later zero digits. Masked bytes become control1, which the
existing compact renderer uses to advance stored origin; no cleared-pixel claim.
D0-D2/D7/A0-A1 and the buffer's following byte are preserved; status bit3 is scratch.

Eight original-code tests in `tests/test_pandora_earth_countdown.py` cover all
10,000 valid BCD values, all 256 divider/UI/mask bytes, expiry guards, all sixteen
nibbles and register/buffer fences. Musashi executes SBCD because the current
native simulator lacks it; native tests retain the real formatter/compact renderer.
The status FIFO remains real; audio requests are observed at caller entry. A
56-byte C/vasm operand preflight and a 25-byte legacy-name-priority reproduction
passed before target mutation. Full-target C/vasm matches all 376,832 bytes, receipt
`4b7572154ed87c9d85d616bd0196aacfe5a0995917703bc1bfae820394a828e2`. Earlier source/comments, types/fields/owner bounds, SDK/pointer forms, raw gaps and
histories pass preservation, including title/F7/A4 distinctions. All 126 assets,
2,112 typed tile fields and the 128-byte INCBIN policy remain intact. Unchanged
checks are reused; no framework change, asynchronous frames/DMA, ordinary
admission, visible pixels, complete ownership/lifetime or intent/bug claim.

### Missing-ID defeat continuation and exit clocks

Accepted 34 annotations: eleven code stages, eight shared defeat-geometry
names, three constants, eight instruction/typed-BYTE bindings and four comments.
Missing-ID failure executes health/outcome/audio work, even with a full FIFO, then
clears the pending bit and restores D0-D7/A0-A5. It exchanges animated defeat into
the descriptor, retaining the fixed movement state as saved, without setting the
commit-inhibit byte. The current movement call continues using fixed-state geometry
and can commit its requested axis step; the next call tests inactive and returns.
This closes the previously open failed-ID continuation under controlled inputs.

All three exit consumers decrement a BYTE: old 0 wraps to 255 and old 1 branches to
warm restart. Main pauses for active status context; both modal prefixes omit that
guard. Modal expiry reaches restart before normal world-context restoration; tests
stop at restart entry, retaining the earlier title/F7 scope and limits. Shared
frames 5..12 now have names at all references; node fields name thirteen active
frames and phase increment 40. Existing thirteen-frame/held-header checks are reused.
These names grant no exclusive art ownership or elapsed-time interpretation.

Seven original-code tests in `tests/test_pandora_id_defeat_continuation.py` cover
256 node modes with status-active context bytes, real callees/full FIFO, all four
directions with both inhibit states, subsequent inactive admission, all 256 exit
counter/player-flag/context bytes and a 70-service status-paused delay. No instructions
or callees are patched. Prior acceptance, static NULL-node, checkpoint, outcome,
countdown and title/restart checks are reused. Preflights preserve 34 instruction
bytes and the 20-byte node image (including RTS) through C and vasm. The current API
requires a current-subject receipt; comments were finalized before one full output
gate. All 376,832 bytes match, receipt `1be3c7783d7f31d59b8010e0ff620928714b5903172aef74d1d6efb3d247a491`.
Earlier source/comments, types/fields/owner bounds, SDK/pointer forms, raw gaps,
histories, 126 assets, 2,112 typed tile fields and the 128-byte INCBIN remain intact.
No framework change, asynchronous frames/DMA, visible pixels, ordinary gameplay
admission, complete lifetime or intent/bug claim is added.

### Script node selectors and interpreter continuation

Accepted 60 annotations: twenty-four code names, one raw-target name, nine
predicate/opcode/sizeof/field constants, twenty-one bindings and five comments.
Script installation restarts the incoming clock and clears held-header mode even
when the node is already selected; toggles preserve the clock. States sharing a
mutable node observe these changes while retaining separate cached geometry. The
original 26 typed sequence commands reference eight node identities; this does not
establish exclusive owners or ordinary runtime sharing between distinct states.
Sequence replacement preserves count, descriptor, step and XY fields. Cached geometry
waits for animation: in the tested count 3/phase 0/step 64 case, the second
eligible visit selects active index 1 using the existing signed-phase test.
Addition carry does not control this advancement.

Walkers choose the first matching root/attachment; head-only forms never fall back.
No NULL-root guard or cycle bound exists. Bit 3 is named for its command-selector
role; its wider visual meaning remains unknown. Original indirect dispatch stores
the returned cursor and then tests actor delay. The 33-pointer owner retains its
bounds; out-of-range opcodes target the original raw $4AFB bytes. Their execution,
exception behavior and fallthrough remain unproved. Repeat/copy/node strides use
canonical aliases of existing sizeof symbols; post-handler offsets retain their
existing object-field relationships through normal commands. No framework change.

Five original-code tests in `tests/test_pandora_script_node_selectors.py` cover
all eight commands and 256 head flag bytes through indirect dispatch plus real delay,
head-only/no-match/first-match behavior, same-node/shared-node changes, cached-geometry
continuation and finite-budget cycles without cursor commit. No instructions or
callees are patched. Existing 33-opcode, delay/repeat/callback, typed sequence,
diabetic-script and other subsystem checks are reused. All 90 preflight instruction
bytes, nine EQU forms and 21 operands are C/vasm exact before mutation. Comments
were finalized before one full output gate. All 376,832 bytes match, receipt
`b455b06f57a4d181d4b2dcc94116aca0087ddc24630622680fa500758ba62e9b`.
Earlier source/comments, fields/types/owner bounds, SDK/pointer forms, raw gaps,
histories,
126 assets, 2,112 typed tile fields and the 128-byte INCBIN remain intact, including
countdown, title/F7/A4 and defeat distinctions. No asynchronous frames/DMA, pixels,
ordinary admission, exclusive ownership, complete lifetime or intent/bug claim.

### Ranged fire and complete hit resolution

Accepted 52 annotations: twenty code stages, ten constants, fifteen operand
bindings and seven finalized comments. A press latches before held-ID/ammo checks:
invalid IDs and empty variants still consume it. Switching IDs neither rearms nor
refills the shared two-byte ammunition array; the original initializer copies 5/1.
UI/combat blocks release rearm while the active-player visual timer still ticks.
Inactive player skips both. Timer expiry unbinds its node while retaining geometry.
Aim uses the last accepted request, with WORD-wrapped first sample at
`player + 14 + 4*request`; the ray still uses fixed 90 columns and has no general
termination bound.

Damage arrays index laser rifle/pulse cannon: health 30/90, item state 50/100. Item
state clamps by signed result, not borrow. Positive HP results store; zero/negative
branches reach completion with the old HP byte still present. The four known initial
callbacks run before state exchange/inactive marking, without combat's pre-callback
passage reset; their own passage writes remain. Later callback mutation/memory
effects stay open. Under explicit retained table/state admission, another fatal
hit on an inactive victim exchanges states and increments the defeat BYTE again,
including wrap. This does not prove that normal world repartition admits it.
Unmapped hits return for either resistance-message bit value; the bit requests
warning text, without establishing wider force-field damage/solidity semantics.

Nine original-code tests in `tests/test_pandora_ranged_resolution.py` cover all 256
item-state/health bytes and both variants, full shots, all four known callbacks
plus NULL, state/counter/passage effects, repeated admitted hits, all 256 UI/player/
held-ID/fire/latch/ammo bytes, warnings, bounded zero-step nontermination and shared
ammo/reset copy. Real audio/status/state callees remain; no instructions are patched.
Unchanged geometry/ray/visual, ammunition, callback and other subsystem checks are
reused. All 60 preflight instruction bytes, ten EQU forms and 15 operands are C/vasm
exact before mutation. Comments were settled before one full output gate; all
376,832 bytes match, receipt `41347ea5de74415c2e899179aa791ff7e108d7f898638ce9a7ffa055a2ca0927`.
Earlier source/comments, fields/types/owner bounds, SDK/pointer forms, raw gaps,
histories, 126 assets, 2,112 typed tile fields and the 128-byte INCBIN remain intact,
including script clock/hold/cache, countdown, title/F7/A4 and defeat distinctions.
No framework change, DMA/pixels, audible output, elapsed-time, ordinary admission,
complete lifetime, intent or bug claim is added.

### Descriptor partition and ordinary retained-aim shot

Accepted 24 annotations: ten code stages, one tail label, three
pointer/gap constants, five operand bindings and five finalized comments. The
32-entry reorder preserves a 29-entry fixed prefix and six-entry fixed tail/NULL
within the 67-descriptor table. All 256 flag bytes use only bits 6/7 for partition,
with bit 6 priority. Front keeps order, back reverses it, and the nonempty deferred
middle sorts by unsigned Y. A four-entry original-code witness reverses equal-Y
identities across gap passes. The empty-middle guard is still absent; no general
lifetime invariant is asserted. Gap preparation/pass/exchange/return stages and
the fixed tail are now named, with explicit pointer stride and decay constants.

Original Copperline checkpoint evidence records all 67 live descriptors, cached
Feed geometry, and a flight-controller root that skips only its own state: its
linked attachment remains eligible. This does not establish an ordinary NPC hit.
One normal-input left+fire shot keeps player (1228,874) and prior rightward aim 7/0,
hits blocking tile 306 at its first sample (1270,888), and returns to the canonical
main-loop anchor. Player HP 95 and controller HP 55 remain. Initial ammo 5/1 stays;
mutable ammo 5/1 becomes 4/1. Earlier audit reads at $1924C captured initial ammo;
the audit now reads mutable $1924E. Cached neutral input A6+$1C6 is also distinct
from retained aim A6+$31C, now captured explicitly. Historical receipts are retained
with these corrections documented.

A separate eight-visit left-input window accepts aim (-7,0); after release and two
neutral visits, player (1207,874) fires through clear tile 92 at (1193,888) and stops
on blocking tile 64 at (1179,888). Both bounded shots return normally with one
round consumed. A prior two-visit direction window did not admit movement; its
negative result is kept explicit. No Feed return/BYTE write, successful NPC hit,
general ray termination, DMA/pixels or audible-output claim is added.

Three new CPU sorting tests and four receipt regressions pass. The receipt
regressions independently decode the original tile/block bit and geometry bounds,
check table membership and canonical original-payload stops, and distinguish both
ammunition arrays. The scoped documented headless runner succeeds; the initial
restricted startup exited 1 before any checkpoint observation. No framework change
was made. Existing partition/ray/hit/animation/callback and other subsystem checks
are reused. All 12 preflight instruction bytes, three equates and five quick/MOVEQ/
shift forms are C/vasm exact. All comments were finalized before one full output
gate: all 376,832 original bytes match, receipt `26d6b1ca47e731363c5c6fa1bc9a22a7fb48d3cf497dae957edbd48b56fa61af`.
Whole-source preservation permits only these names/operands/comments, including
one deliberately strengthened sort comment. Earlier fields/types/owner bounds,
SDK/pointer forms, raw gaps, append-only histories, all 126 assets, 2,112 typed tile
fields and the 128-byte INCBIN policy remain intact. Runtime evidence and bounded
reproduction scenarios are linked from `docs/copperline-runtime.md`.

### Terminal deposits, marker state and salvage ratings

Accepted 57 active annotations: three exact data owners and 54 dependent facts. The
previously opaque marker is now an 18-byte animation frame, 12-byte position
descriptor and 26-byte render prefix, exposing 21 named fields without extending
into the following squash-player record. Deposit and adjoining clearance branches
are named; six constants, one existing-EQU expression, ten scalar forms and shared
X/Y fields show UI/ID gates, wrapped distance, field offsets, fixed feedback and the
64-byte storage prefix. All five salvage-rating pointers and their NUL strings are
named and classified together, completing the deposit-to-outcome data family.

Held fire is a level gate. IDs 0/1, UI bits 1/2 and inactive player reject; accepted
items are appended to the first zero BYTE, holding is cleared, ID recheck is
requested, and salvage increments before feedback. Full real message FIFO does not
roll back these effects; UI/audio callees still run. Duplicate supplied held items
can be deposited repeatedly without a fresh fire edge. Distance sums wrapped WORD
magnitudes and compares unsigned with 24; there is no coordinate clamp. The 15-byte
salvage bitset covers 120 IDs; explicitly supplied IDs 120..255 index following
tile-block bytes instead. This is not ordinary acquisition evidence.

No capacity comparison bounds the deposit scan. Explicit full-prefix tests reach
adjacent modal cache and ranged-fire latch, and the latter inhibits a rifle shot
until release. The 64-byte physical declaration is retained. No ordinary full-buffer
occurrence is claimed. Depositing the only ID removes it from possession: the real
recheck stages defeat. A spare pocket ID prevents that defeat while empty holding
still fails selected-card clearance. Six explicitly supplied eligible deposits feed
the real escaped salvage rank, without a uniqueness check.

The marker belongs to the original 67-descriptor table but has no matching initial
35-object record. An admitted per-point ray test through both original tables shows
the offscreen anonymous-hit path moving its current XY; visible-hit handling instead
uses the flash descriptor. Deposit admission follows the changed center. The real
world initializer clears deposited IDs/count and fire latch, but retains marker XY
and modal cache in the tested state. This proves neither an ordinary marker shot nor
a gameplay exploit; subsequent title/modal/camera calls remain separate. The bounded
original north firing-line candidate stopped at combat UI visit 11/32 before firing,
preserving HP/ammo. Successful NPC targeting and the Feed/BYTE route remain
unproved.

Thirteen new original CPU cases and one new runtime-guard regression pass. All
callees/instructions remain original, with explicit RAM and MMIO inputs and no
DMA/pixels or audible-output claim. The 56 structured bytes, 54 scalar-preflight
bytes and 10 typed-field-preflight bytes pass C/vasm checks, including seven EQU
forms. Four redundant X/Y alias facts were undone through append-only history when
native typed fields took precedence. The dependent owner/type commands use normal
current-revision catalogs. Comments were finalized before one full output gate: all
376,832 original bytes match, receipt
`1205f41e438898e921f018c0e408cd5b7e46d98792392382df68552425deacfb`. Earlier
fields/types/owners/comments, SDK/pointer forms, raw gaps, append-only histories,
all 126 assets, 2,112 typed tile fields and the 128-byte INCBIN policy remain
intact. No framework change; unchanged prior subsystem checks are reused. Evidence
is in `tests/test_pandora_terminal_deposit.py`, with the bounded route guard added
to the existing rifle receipt and runtime guide.

### Primary audio sequencer

Accepted100 annotations complete the primary sequencer's connected control flow:
39 code stages,19 constants,32 scalar operand forms,one sample7 direction label
and nine purpose comments. Existing channel,DMA,sample/global/base structures and
all original selector/program table owners remain shared and unchanged. Canonical
SIZEOF and SDK expressions expose strides and DMA flags without losing hardware
register names or pointer presentations.

The four-channel pass stages sample resume independently from DMA pending. A
nonnegative LONG offset advances sample bytes and subtracts offset/2 from WORD
length; negative uses32-word silence. Countdown old1 clears note flags then fetches
tokens, old2 only conditionally clears a DMA bit, and old0 wraps toFFFF and updates
streams. Opcode83 and pending suppress the preexpiry DMA clear. Attack resets the
volume cursor, consumes an unmasked signed first byte, and leaves modulation state
intact; later volume visits apply low7 and retain a terminal-marker cursor. Header
H gives H+1 eligible visits between volume updates, including256 forFF. Volume
scaling keeps the product's low WORD before shifting6.

Pitch stream markers apply their low7 offset before looping; note/global/channel
sums wrap as BYTE before an unchecked scalar lookup. Signed BYTE pitch delta waits
without applying its prior accumulator, then accumulates/subtracts WORD values on
every pitch visit until note expiry clears the enable flag. Modulation uses exact
BYTE equality for turns, flips add/subtract at zero, and sign-extends its updated
value into wrapped WORD period arithmetic. Duration uses an unsigned WORD product
although command8A loads the multiplier from a signed BYTE. Selector physical
prefixes and the11-handler table remain distinct from unchecked encoded admission;
unknown control targets are never executed in the tests.

An explicitly injected out-of-prefix pitch selectorAF exposed missing MOVEA.W
source extension in the simulator. Concrete and abstract MOVE paths now consume
the existing Motorola-derived source_sign_extend metadata, without a mnemonic
special case or generated-table edit. Truncated symbolic pointers conservatively
lose identity; long pointers retain it. Ordinary MOVE.W remains unchanged. This
fix is a simulator correction, not a game-byte change or proof thatAF occurs in
normal programs.

Validation:12 original-code tests in `tests/test_pandora_primary_audio.py`
cover all256 tokens and multiplier
bytes, signed offsets, countdown/pending gates, all pitch marker bytes, signed
delta/WORD wrapping, all256 modulation flags with boundary values, volume intervals,
a real command chain and two complete services of all four original channels and
register banks. The38-test focused simulator run passes; the independent machine68k
oracle passes5 tests/74 subtests, including40 MOVEA extension vectors; C unit tests
pass. Explicit RAM/MMIO inputs establish CPU packets, not DMA timing or audible
output. Existing global phase/skip,guarded sample7 initialization/12-state cycle,
secondary-audio and table-prefix evidence is reused.

Every selected operand and EQU passes an isolated original-instruction C/vasm
preflight. One final full gate after annotations settle reproduces all 376,832 bytes
with C and vasm, SHA-256
`70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`,
receipt `4ae079c141db2ab5fe4c70e7908f9020adf5c28582f20282f18328c06d187ebc`. Whole prior source/comments/types/owners,all126 assets,
2112 tile fields,128-byte INCBIN policy,SDK forms,pointer expressions,raw gaps and
append-only histories remain preserved. No further NPC route exploration was used.

### Shared item and character display-name catalog

Accepted 222 facts complete the display-name pool and its references: 103
purpose-based names with explicit ASCII extents, one 114-WORD array in the
existing owner, 114 signed base-relative bidirectional references, and four
alias/boundary comments. All relative WORD expressions reference the names.
The existing 228-byte offset-table owner retains its identifier, bounds, role and name. Its stride-two array has no
explicit HEX representation: every WORD has a canonical string-minus-base
binding. These explicit references preserve source quality where required string
facts suppress native heuristic expressions. No overlapping string owner was
introduced, and all 284 earlier manual data references remain intact. Existing
item-ID constants and world-object role names are preserved. Character and item display names share
this catalog; the labels identify text, not unique actor or inventory identities.

Five alias groups remain explicit: IDs 14..18 share LASER RIFLE, 20..23 share
Ostronn egg, 85..87 share Secdroid DELTA 1, 90..91 share Secdroid OMEGA and 92..93
share Pianist. ID 0 selects an empty string; ID 1 selects five spaces plus NOTHING.
Raw inventory refresh and display fallback retain their different ID selection.
The final Amiga Computing name occupies 15 bytes with no local NUL. Original text
consumers terminate on the following first offset WORD's high byte, $00. An
explicit CPU-fixture change to that WORD extends the read by two printable bytes;
this establishes the dependency without claiming ordinary table mutation.

Five new original-code cases in `tests/test_pandora_item_name_catalog.py` pass.
The fixture records all 103 physical strings, their 114 ID mappings and exact
terminators. Every name passes through the real compact font's CPU writes and
through the proportional map/cursor path with all planes disabled. Full inventory
refresh covers all 114 mappings across both four-slot panels while preserving IDs
and saved registers. CPU RAM writes and packet/cursor behavior do not establish
displayed pixels, DMA timing or audio hardware output. No instructions are patched.
Existing renderer arithmetic, signed resolver/unsigned refresh and out-of-prefix
limits are reused; resolver IDs 114..127 and refresh IDs 114..255 remain outside
the supplied name-table prefix. The published MOVEA.W signed/unsigned boundary,
ordinary MOVE.W and independent oracle coverage is unchanged and was not rerun.

Isolated normal-command preflights reproduce all 1,382 original bytes covering
the pool and offset table with C and vasm, including empty/padded strings and the
non-NUL final extent and all 115 array/reference commands. Native query preflight
confirms all 114 target links across the 103 strings; current-target alias and
final-name queries corroborate their projected links. The combined owner
and dependent-reference request was rejected before any append; the owning array
was staged first at a fresh revision. Five normal interpretation batches were
followed by one final full gate after all annotations settled: all 376,832 bytes
match with C and vasm, SHA-256 `70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`,
receipt `5f4038698d62dd80035cd8c135bc65b8f58012ceb046fce266acc94a27157100`. Whole prior source/comments, types and owner bounds,
SDK/pointer forms, all 126 assets, 2,112 tile fields, 128-byte INCBIN policy, raw
gaps and append-only histories remain preserved. No framework or runtime-runner
change was needed.


## Overlay text, registration and startup-clear tail (2026-10-19)

Restored the connected row-clear, six-line text dispatch, callback readiness and
registration family with 53 accepted facts: 18 control stages, six constants,
17 symbolic operands, four continuations of the existing A5 descriptor type,
seven concrete comments and one 64-byte startup-clear tail owner. The existing
44-byte descriptor and 16-pointer registry remain shared and unchanged.

Six original-code CPU tests cover four-plane row clearing with BYTE dimension
wrap; unchecked wrapped WORD selected-line pointer indexing and the two cursor
phases; all 64 line-style combinations and NULL-prefix dispatch; all 256 state
bytes crossed with three style values and a NULL callback; and the exact
128-byte startup clear. An injected 32-nonzero-pointer prefix reaches the first
SPACE glyph during registration. Clearing the registry and tail excludes that
font write, which the original compact font copy subsequently reads. This is
controlled composition evidence; normal gameplay overflow and exclusive tail
ownership/later lifetime remain unproved. The indexed base aliases the shared
line_0_ptr field through a canonical EQU; the unchecked index and native
indexed_dynamic gap remain explicit. Fixtures patch no game instructions and
make no DMA/pixel claim.

The generic effective-metadata projection now forwards authored seed prose
without manufacturing comments from mode/data_role/unit/encoding controls.
Those controls remain in the Manual Action Log and structured metadata. This
removes 141 routine suffixes (139 strings and two pointer tables) from Pandora;
all authored comments remain, including metadata-looking authored prose in the
regression fixtures. Required code/data classification, role, encoding and
byte equality are tested independently. This is the canonical projection fix,
not a target-specific source filter. Hardware names such as bpl1mod(a5) and
aud0+ac_per(a6) remain present.

Validation: 59 effective-metadata tests and 18 selected native renderer tests
passed. Five overlay CPU tests passed initially; the corrected callback-slot
fixture then passed separately. Both actual-instruction C/vasm preflights passed
(17 operand forms plus six EQUs and a guarded 64-byte tail; eight descriptor
field instructions separately). A single final settled target gate reproduced
all 376,832 bytes with C and vasm, SHA-256
`70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`;
receipt `193965f9dd5548a840d1fac883a24a99dff56cfafe17d2bbd8ae63d63d095316`.
Preservation checks retain all 398 prior manual data references, previous
owners/layouts/types/RSSET regions, authored comments, 126 assets, 2,112 tile
fields, 128-byte INCBIN policy, SDK hardware forms and unproved raw gaps.
Manual Action Log and Decision Journal append exactly 53 records each.


## Read-only completeness baseline (2026-10-19)

The generic `restoration_accounting` command now derives independent accounting
from native ownership/CFG/type facts, the native source plan, effective metadata,
MAL/Decision Journal and the source-package manifest. The compact text baseline
is `docs/targets/pandora-completeness-baseline.txt`; the machine baseline is
`docs/targets/pandora-completeness-baseline.json`. It is a reproducible snapshot,
not a second tracker. Canonical input hashes bind it to the overlay checkpoint.
Target annotations and assembly remain unchanged by this feature.

Pandora's 376,832 stored bytes partition into 24,260 code, 339,098 structured data,
1,050 table, 4,166 text, 8,226 unknown and 32 native-conflict bytes. Compatible
broad data owners and leaf tables/strings share bytes without false conflict or
double counting; the four explicit native conflicts retain stable identities.
These classifications are not purpose-completeness claims. The report finds
265 function candidates (218 CFG-supported, 40 ambiguous, seven partial), 543
declared data owners and 126 asset emission chunks. Complete function/object/
semantic-resource denominators and purpose/confidence assessments remain unknown.

The app layout's observed [0,2032) envelope has 788 declared union bytes and
1,244 unknown bytes; its true allocation bounds and gap intent remain unproved.
Hardware/external observations account for 27 known-width union bytes and seven
unknown-extent observations. Native typed accesses include 964 resolved and 35
unresolved records; all 563 native data-reference records have accepted targets.
Eight indirect sites remain explicitly unresolved; the other native statuses
remain distinct from proof of complete transfer closure. Eighty generic labels
are review signals, not a demand for mechanical renaming.

The existing source/package-bound C+vasm receipt is reused as original-layout
verification. Final semantic review and relocation readiness are not assessed.
No overall percentage or implicit unused/padding inference is made. The native
source-plan DTO now exposes stored versus allocated extents, so BSS and trailing
workspace cannot inflate payload coverage; missing bounds remain unknown.

Validation includes 23 focused accounting tests, native raw/Hunk read-only and
BSS/exact-render checks, and the existing source-package and canonical-symbol/
operand regressions. Cases cover unknown gaps, compatible/nested owners, alias
unions, explicit/provisional conflicts, classification with unknown purpose,
partial RSSET/data layouts, INCBIN aliases, zero-width hardware observations,
stable unresolved identities, exact output with semantic gaps, stale receipts
and protection against canonical output paths. Ruff and diff checks pass.
Two independent projections of the same captured canonical facts produce
identical machine output; canonical target input hashes remain unchanged.


## Explicit purpose/confidence and a representative semantic baseline (2026-10-19)

The accounting feature now has a typed, bounded `PurposeAssessment` fact in the
canonical Manual Action Log projection. Normal `target.purpose.assess` and
`target.purpose.remove` catalog commands use the existing validated append,
replay, undo/redo and Decision Journal. This follows the existing separate-facet
pattern used for region facts; it creates no second tracker. Purpose claims stay
outside native analysis/rendering policy, so their metadata never appears in
assembly comments or changes the generated source. No architectural user
decision was required to add this independent evidence dimension.

Each claim explicitly declares coordinate space/bounds, purpose category,
concrete purpose, confidence, whole/partial scope and limits. Source scopes,
qualified base-relative layouts and observed absolute domains remain separate.
Only evidence-bearing, journal-accepted whole-scope claims support purpose bytes.
Low confidence is not promoted by acceptance; partial, provisional, deferred,
rejected, unmapped and overlapping claims earn no whole-scope credit. A supported
scope establishes the stated purpose, not complete fields, all writers, runtime
reachability, display/audio output, transfer closure or relocation readiness.

Three reviewed examples establish 122 distinct bytes: the 32-byte top-left UI
border cell (graphics), 64-byte mutable sample-7 buffer (audio), and 26-byte
terminal salvage marker render prefix (game data), all explicitly high confidence
with conditional limits. Evidence reuses original CPU tests and inspected
producer/consumer dataflow. The marker has six current native typed-pointer
records, including reciprocal descriptor and geometry links. The sample pointer
is computed by the original header walk and checked by guarded-initialization
CPU scenarios; its lack of ordinary static symbol references is not used as an
inference. The other 376,710 payload bytes remain purpose-unassessed. Names,
comments, accepted annotation counts and INCBIN are not imported as understanding.

The 339,098-byte `structured_data` counter is a coarse ownership/storage class:
native lowering mixes primitive BYTE/WORD/LONG fields from images, sample data,
records and other owners. It is not a purpose taxonomy. The report now exposes
existing native asset encoding evidence separately: 118 bitmap chunks / 241,376
union bytes, seven sound-sample chunks / 26,324 bytes, and one opaque tail /
27,792 bytes. The corresponding intersections with the coarse structured-data
class are retained explicitly (overlapping dimensions must not be summed).
Declared shared-schema instances are also indexed. Such encoding/layout evidence
can guide finer restoration; a concrete game role still needs scoped consumer
and behaviour evidence, as in the three examples above.

All 80 generic-label signals have source-coordinate listing links. Unknown
RSSET gaps retain their stable qualified identities and get neighboring field-use
links where evidence permits. Native app-slot references can retain generic
`app_XXXX` display aliases after field renaming; the report joins them by qualified
native app-slot layout and offset only when that domain is unambiguous. Equal
displacements in competing bases are not joined. Neighbor use never proves gap
use or unused/padding/reserved intent. The true workspace allocation extent stays
unknown.

Validation: 46 focused purpose/accounting tests pass, including native exact
output/no-comment-leak checks and normal existing-journal review. A broader
298-test action/catalog/replay/review/metadata regression run passed before the
final report-only link/format refinements. A full standard native collector
regenerated the baseline; deterministic reprojection of those same unchanged
facts verifies every result against it while adding qualified gap links.
Three MAL records and three journal decisions append to preserved history.
The required current-subject gate ran once, reused the resident native artifact,
and reproduced all 376,832 bytes with C and vasm: receipt
`7b52b651eb82f372edbc119ab221a02484c96a6fa55086899045a5be94036b32`. Source text, package manifest, all126 assets,
SDK forms, types, prior annotations and raw gaps remain byte-identical to
`7247bc48`. The next batch investigates the four native conflict ranges (32
bytes); they are not cleared by semantic-purpose bookkeeping.

## Native conflict reconciliation (2026-10-19)

All 32 previously reported conflict bytes were exporter accounting artifacts.
The native orphan signals had already distinguished these cases, but the range
exporter treated every candidate near data as conflicting ownership, including
suppressed candidates and candidates merely adjacent to data. It now exports a
conflict only for an unresolved candidate that actually overlaps data. Other
signals remain available for review; this does not promote code or resolve an
uncertain candidate by bookkeeping.

The four source ranges, with exclusive ends, reconcile as follows:

| Source range | Bytes | Existing native evidence | Correct classification |
| --- | ---: | --- | --- |
| `$1094..$109E` | 10 | Unresolved terminal-decode candidate; following text is adjacent, not overlapping | Unknown |
| `$E652..$E65A` | 8 | Candidate suppressed by accepted bitmap data | Structured data |
| `$F6C4..$F6CA` | 6 | Candidate suppressed by accepted bitmap data | Structured data |
| `$453B8..$453C0` | 8 | Candidate suppressed by accepted bitmap data | Structured data |

The regenerated partition therefore has zero native ownership-conflict bytes,
339,120 structured-data bytes and 8,236 unknown bytes. Other classes are
unchanged. The ten-byte candidate remains open as
`orphan_code_candidate:h0:$00001094-$0000109e`, with low confidence and no durable
executable evidence. Neither reachability nor deadness is established. The
bitmap encoding intersection now includes all 241,376 bitmap bytes. Explicit
purpose coverage remains 122 bytes; clearing a false conflict adds no semantic
purpose credit.

Validation includes the full native C unit suite, eight exporter status/relation
cases retaining a genuine unresolved-overlap positive case, and two native
end-to-end tests preserving both suppressed-overlap and unresolved-adjacency
signals without promoting them into executable control flow. The fresh target
gate reproduced all 376,832 original bytes with C and vasm, receipt
`24b0743585c46ebf5a4e135dc0af33d39b70775485ccba22ed535c2d78e6d6a4`.
Source text, package manifest, all 126 assets, Manual Action Log and Decision
Journal remain byte-identical to `a6d8ee95`. No target annotations were changed.

## Connected display workspace and tile-grid purpose (2026-10-19)

The next family was selected by inspecting the 35 native unresolved operand
records together with the workspace gaps, rather than treating either inventory
as blank or wholly unanalysed memory. The tile builder accounts for nine of the
27 `indexed_dynamic` records: its original multiply-by-18 and nine WORD reads
select an existing shared 3x3 definition. The native resolver still cannot prove
each dynamic address; the algorithm and original stored tables already have
stronger semantic evidence than that resolution status suggests.

One published batch adds three workspace declarations and 12 bounded purpose
assessments. Four original immediate LONG writes select
bank 0 at `$2AAA`, `$2ADC`, `$2B52` and `$9F1C`; all four now render with the
four-byte `app_framebuffer_bank0_ptr` field at A6+$1E0. A new parameterized
original-CPU check verifies each assignment and
untouched adjacent bytes. The slot's consumer, active rendering role and lifetime
remain unproved. No read is invented from adjacent text/display fields.

The assessments integrate existing producer/consumer and CPU evidence in bulk:

| Scope | Established purpose and evidence boundary |
| --- | --- |
| App `$000..$190` | Exactly 200 WORD row offsets, initialized to 160*y; text indexing can exceed this table for masked y>=25 |
| App `$1D4..$1E8` | Front/back/display pointer flow, the four fixed-bank pointer writes, and mutable text cursor; pointer roles remain distinct |
| App `$1BA..$1C6`, `$29A..$2A6` | Tile column/row/base/dimensions and derived size/end/stride; modal exchange can leave derived metadata stale |
| App `$604..$7F0` | First 123 LONG pointers of the fixed `$4000` grid, including the established combat selector's low-WORD alias |
| Source `$3502..$3F16` | All 1,290 stored macro-tile IDs, 43 rows by 30 |
| Source `$3F16..$5FFE` | All 468 nine-WORD definition records, with unsigned pixel offsets and unchecked signed WORD record-index arithmetic |
| Source `$A198..$A25C` | Complete original grid-builder routine and its current-metadata footer |
| Source `$AF9E..$B020`, `$B040..$B0E0` | All 26 title masks and five remaining border cells; the previously assessed first border cell is excluded |

`tests/test_pandora_tilemap_grid.py` independently models all 11,610 output
pointers and compares the entire original 46,440-byte grid, guards, saved
registers and footer state. It also tests modified/invalid IDs and wrapped WORD
arithmetic. `tests/test_pandora_framebuffer_lifetime.py` checks the whole row
table, both text-origin paths, world-bank exchange and four vblank plane
pointers. `tests/test_pandora_overlay_title_masks.py` exercises all masks, ten
initialized titles, unchecked byte indices and all six border cells. These are
CPU storage/address contracts, not actual DMA pixels, gameplay reachability or
exclusive lifetime proofs. Purposes come from these consumers and checks, not
from labels or declared encoding alone.

The other eight native `field_gap` records also need interpretation before
changing a layout. Four are LEA instructions advancing by a command's existing
ten-byte size (`$1210`, `$132E`, `$1366`, `$139E`), not reads of an absent member.
Three read IDs from later two-byte inventory records (`$27F8`, `$27FE`, `$2804`);
the existing inventory cursor test checks the staged IDs and preserved value
bytes. The last is a WORD probe at object+$40 (`$790A`), whose following
instructions compare its low byte; it does not justify expanding the shared
object prefix. The remaining dynamic families retain their exact native
records and original array/overlap semantics; they are not mechanically cleared.

The report now groups unresolved operands by native form and root layout, links
them to the listing, and separately attaches explicitly assessed enclosing
instruction purpose. All 35 statuses remain unresolved; nine acquire supported
grid-builder context without claiming field/index resolution. The text report
also exposes the native 118 bitmap / seven sample / one opaque asset inventories
underneath coarse storage classification. Encoding evidence does not establish
every resource's game role.

The largest apparent gap was not wholly unknown: the fixed `$4000` tile grid is
also A6+$604 when A6 is `$39FC`. Its first 122 complete pointers occupy 488 bytes,
followed by the high WORD of pointer 122; that pointer's existing low WORD at
A6+$7EE and BYTE at +$7EF retain their overlapping combat views. The new prefix
and high-WORD declarations recover 490 gap bytes without overlapping those
existing fields or expanding the app envelope. The complete-grid CPU test and
`test_original_grid_builder_supplies_the_overlapping_combat_selector` establish
the absolute writer and exact alias, including original pointer `$00023FA8`.
No allocation or exclusive workspace/grid lifetime is inferred.

Together with the four-byte slot, this reduces declaration-gap bytes in the
observed app envelope from 1,244 to 750. That is not an unknown-behaviour count.
The remaining `$36C..$604` gap stays unclassified: initialization clearing ends
at `$36C`, and absent named references do not prove unused or padding intent.
Likewise, unassessed legacy purpose metadata does not
invalidate existing evidence-backed restoration. Allocation bounds, complete
dynamic consumers and relocation readiness remain open.

Validation: 79 focused accounting/purpose and original-CPU tests pass, including
the additional grid/combat alias scenario. The final C and vasm gate reproduces
all 376,832 original bytes, receipt
`dee441b449490fa783ffec8a040f6a6158dbda5b02fed7574837b5cec2b6325a`.
All 126 asset records and SDK include identities are unchanged; the source diff
contains only three workspace declarations, the reduced raw gap and four
symbolic operands. Fifteen MAL records and fifteen journal decisions append to
preserved histories. The updated purpose totals are 11,612 payload bytes and
936 bytes in the separate app-relative view; these coordinate domains are not
added together. Native payload classification and the 35 unresolved operand
statuses remain independent of those assessments.

## Bounded inventory records: resolve members, retain dynamic addresses (2026-10-19)

Grouping the 35 unresolved operands selected the inventory family: three fixed
reads of later records and two indexed ID exchanges. Native tracking already
understood bounded record arrays, but the normal command/metadata path omitted
their count and the C importer never read its existing `array_length` variable.
That path now preserves an optional positive record count and section through
catalog commands, MAL replay/undo and native import. Legacy wire output is
unchanged when the count is omitted. Native import validates integer bounds and
matches the specific register; array-offset arithmetic uses a wide intermediate.
The first target rebuild exposed a renderer precedence bug: recovered array
fields displaced existing explicit EQUs and correctly failed the expected-symbol
invariant. A synthetic normal-catalog regression reproduces it. Validated
displacement EQUs now retain precedence over automatic field expressions;
symbol/value/width checks and unrelated SDK naming remain intact.

Two A0 contracts describe the existing four-record, eight-byte inventory prefix.
They reuse the two-byte ID/value schema without extending it or asserting total
allocation. The fixed reads at `$27F8`, `$27FE`, `$2804` resolve as members of
records 1, 2 and 3. The two indexed operands now use the existing ID member via
`INVENTORY_ITEM_ID_DISP`. Their indices remain dynamic: original BYTE masking
keeps them even but preserves high WORD-byte bits. Six original CPU scenarios
check all four nominal records and two out-of-prefix indices with value-byte
and memory guards. Trade misses at +8 and ordered alias effects remain intact.

Eight purpose scopes integrate the staging/exchange prefixes, packed carried,
pocket and display-ID workspace arrays, and all 69 existing inventory/reset
table owners (552 bytes in four contiguous groups). Seventy native object-pointer
outcomes resolve to exactly those 69 starts, counting the shared default once.
The original 35-object reset test checks all current/initial inventory copies;
panel and exchange tests establish the ID/value roles. Intervening unrelated
ranges are excluded. No complete allocation, all-consumer or lifetime claim is
made, and the byte-ID arrays retain their separate representation.

Remaining native groups after resolving the three fixed inventory members:

| Shared cause/family | Records | Retained obligation |
| --- | ---: | --- |
| Inventory indexed ID exchange | 2 | Even stride does not bound the index |
| Script command LEA advances | 4 | Address formation at the command extent, not missing members |
| Tile-definition indexed reads | 9 | Known record roles; dynamic addresses remain unresolved |
| Audio indexed cursors/configurations | 6 | Dynamic address/stride context remains explicit |
| Backward descriptor-reference lookups | 4 | Indexed reference-domain bounds remain unresolved |
| Frame/XY sequence indexing | 3 | Dynamic sequence selection remains unresolved |
| Script-relative WORD copy | 2 | Computed addresses outside the four-byte command header; do not invent fields |
| Overlay line-pointer indexing | 1 | Unchecked selected-line index |
| Combat WORD probe beyond shared prefix | 1 | Low-byte consumer does not justify expanding the shared owner |

Validation: 211 focused Python checks and the full native C suite pass, including
explicit-EQU/typed-array precedence and legacy SDK presentations. One successful
C+vasm gate reproduces all 376,832 bytes, receipt
`fb39f6877f5427e223bdf81a850d667bbe8fb30c1736df8a1cbf817d0d942b54`.
Thirteen MAL records and thirteen decisions append to preserved histories.
All 126 asset payloads, bounds, classifications and SDK includes are unchanged;
generated asset row IDs shift with the three added source-plan rows. The hardware
fixture recognizes the previously published equal-valued silence-length EQU and
checks its canonical value while retaining SDK spelling/comment checks.

Fresh native accounting confirms exactly three removed unresolved identities
(`$27F8`, `$27FE`, `$2804`) and none added: 967 resolved records, 32 unresolved
(five field gaps and 27 indexed records). Payload/workspace byte gaps remain
8,236/750. Supported purpose is now 12,242 payload bytes and 948 bytes in the
separate app-relative view; these are not an overall completion claim.

### Shared zero graphics bank (2026-10-19)

The previously unclassified 512 bytes at source `$4D5DE..$4D7DE` form the shared
zero graphics bank already named `blank_sprite_data`. This boundary comes from
original consumers: the idle feedback frame at `$48588` has stride 2 and height
16 (256 nominal planar bytes, 64 mask bytes); the second final-pose frame at
`$4C5A4` has stride 2 and height 32 (512 planar bytes, 128 mask bytes). Both pixel
and mask pointers select runtime `$5D5DE`. The maximum pixel extent ends at the
separately decoded audio entry; every original bank byte is zero. A normal data
owner with WORD representation now accounts for the full bank.

The same base is selected by the game-exit palette prefix, cursor hiding and
negative-modulo overlay clearing. The two existing frame mask fields now render
`blank_graphics_mask_data`, a 128-byte alias in their existing runtime mask
namespace. Their runtime-only domain and the shared frame schema are unchanged;
the stored zero resource is not reclassified as a generated mask allocation.
The original `blank_sprite_data` symbol and SDK register expressions remain.
Three purpose assessments cover the bank and the two 18-byte frame headers.

Thirteen original CPU checks pass: header/extent and exact sixteen-color palette
checks, ten existing overlay packets, and cursor hiding. These are stored-data
and CPU pointer/register contracts. They do not establish actual DMA output,
exclusive allocation, all consumers, ordinary gameplay reachability, immutability
or lifetime closure. The 768-byte scratch capacity view at `$B3A8` remains
separate from its 256-byte initial file owner: it does not establish the initial
meaning of the following unknown payload. Likewise, zero runs elsewhere and the
supervisor stack-top address alone do not establish allocation extents.

The five remaining non-dynamic native field records were reviewed: four are
script LEA advances at the command extent; `$790A` is a WORD probe beyond the
shared object prefix, with a low-byte consumer that does not justify a new
shared field. The 27 genuinely dynamic indexed records retain their obligations.

Final C+vasm verification reproduces all 376,832 original bytes, receipt
`628f4c08f2678cda95fda587dd65cd95d805668c97560f1def0730f2ff0416fb`.
Six MAL records and six decisions append to the preserved histories. All 126 asset identities, payload hashes, bounds, classifications
and SDK includes remain unchanged; generated source-row IDs shift with the
new explicit WORD-array rows. Source review after the first exact gate caught
the still-empty owner representation; a normal explicit array element completed it before
this final verification. No framework code or SDK presentation was changed.

Fresh native accounting: unknown payload falls from 8,236 to 7,724 bytes
(512 recovered); structured data rises to 339,632 bytes, with zero conflicts.
There are now 544 declared data owners. Supported payload purpose rises from
12,242 to 12,790 bytes, covering the bank and two frame headers; separate
app-relative purpose remains 948 bytes and its gap remains 750 bytes. Native
operand resolution remains 967 resolved and 32 unresolved (five field gaps,
27 dynamic indexed records). These counters are not whole-program semantic
completion or complete allocation denominators.

### Retained NPC animation records and compact typed fills (2026-10-19)

Eight unclassified spans contain a connected family of retained animation data:
15 additional frame headers, a menial-droid chained controller and return/hold
controller, a gardener render prefix and looping controller, and 15 additional
fixed-NPC frame references. The original pointers, adjacent canonical records
and actual animation reader establish their layouts. In particular, the first
menial node is the existing **22-byte chained type**: its LONG at +18 points to
the existing controller at `$4AE50`, rather than being an extra frame entry.
Its held prefix and seven active pointers occupy the following 32 bytes.

Eight original CPU checks exercise all 15 headers through the geometry-reader
prefix, the menial successor transition and hold-at-end behavior, the gardener
loop with unchanged XY, and the additional reference run's eight existing frame
targets. Pixel/mask pointers fit existing nominal bank prefixes. These are
conditional reader contracts. Some variants have no established incoming
reference, so the inferred additional-animation roles receive **medium** purpose
confidence. Activation, all callers, actual DMA reads/output, complete storage
allocation and lifetime remain unestablished. No held/active grouping is assigned
to the separate 15-pointer run. The retained gardener headers store stride 1
with width 32. Those original values are preserved; the tests establish what
the current reader loads and nominal prefixes, rather than silently changing
the stride or claiming a complete frame/DMA footprint. Existing shared schemas,
owners and workspace contracts remain intact.

The prior zero-bank rendering regression was a renderer omission: typed WORD
arrays used the numeric-list path, while repeated-fill formatting existed only
for raw bytes. The normal native renderer now emits `dcb.b/w/l` for uniform
literal leaves of at least eight units, within a single bounded leaf. It keeps
pointer/table expressions, value domains, named constants, explicit source-array
anchors, authored comments and element boundaries. Nonuniform data and scalar
field interiors retain their existing policy. The typed 256-WORD bank at
`blank_sprite_data` now renders as one `dcb.w $100,$0000` line; its typed owner
and purpose remain. The projection no longer fabricates a comment from the
bare `data` classification; authored comments and named members called `data`
remain meaningful. Two package-test assertions were updated for the already
published removal of synthetic `data_role=` suffixes; asset and assembly checks
remain in place.

Fifteen new compact-fill regression cases cover BYTE/WORD/LONG values, nonuniform
arrays, aligned and unaligned source-array anchors, interior/start comments,
separate owners, symbolic scalar entries, interpreted references and named
members. Every case reassembles with the native assembler and vasm. The 213
focused Python checks and full native C suite pass, in addition to the eight
original NPC CPU checks.

The chained record also exposed an embedded-record projection gap: its declared
18-byte header had been emitted as opaque bytes. Declared custom STRUCT members
now expand recursively only when the referenced type and exact size agree.
Leaves retain the embedded schema and reference domains; only the enclosing
record carries the owner span. Unknown, size-mismatched and cyclic members stay
opaque. Nine new cases cover single/array records, leading fields, multiple nesting
levels and those
conservative fallbacks; valid cases reassemble with both assemblers. This is the
only currently bound Pandora type with such an embedded member.

Final C+vasm receipt:
`5e039d975330552015e38433d5c85325fd00c2d194f67610c47ffa6d4dfa778c`.
All 376,832 original bytes match. Thirty-one MAL records and 31 decisions append
to preserved histories; all 126 asset identities, hashes, bounds, classifications
and SDK includes remain unchanged. Generated source-row IDs reflect the new
fields and compact fills. All 75 non-NULL pointer fields in the restored spans
render symbolically in the fresh native plan.

Fresh accounting records **502 bytes recovered**: unknown payload falls from
7,724 to **7,222 bytes**, with structured data at 340,134 bytes and zero conflicts.
There are 552 declared data owners. Explicit payload purpose is 13,292 bytes;
the eight new scopes retain their medium confidence and conditional limits.
The separate app-relative view remains at 948 purpose bytes and a 750-byte gap.
Native access counts remain 967 resolved and 32 unresolved (five field gaps and
27 dynamic indexed records), with no changed unresolved field identities. These
are bounded source/accounting gains, not a whole-program semantic completion
or complete allocation claim.

### Complete NPC, console and ending messages (2026-10-19)

Twenty complete NUL-terminated text spans now include their original quote
and CR bytes. Fourteen NPC messages are named from the existing context or
interaction pointer members of ten original world objects. The other six
retain the self-destruct prompt/card-label/rejected/accepted and ending names;
seven original LEA prefixes establish those roots. Three original CPU checks
verify the stored boundaries and original pointer loads, then consume every
full span through the compact reader with independent glyph-byte, cursor and
RAM-write expectations. Embedded punctuation remains byte `$22`, including the
`EARTH` punctuation and NPC quotations; CR remains `$0D`.

Nine purpose scopes cover the complete stored text and these local contracts.
Storage and pointer associations are established; ordinary activation, all
callers/writers, lifetime/allocation closure and actual display output remain
unassessed. This batch changes target facts and focused checks, without a
framework change. Generated-source review requires readable complete messages,
all fourteen NPC references using their names, the compact WORD-fill bank and
unchanged SDK expressions and assets.

Readability review after the first exact gate caught automatic recognition
regressing the related rejected-card middle line to hex. Its complete original
86-byte span is now explicit too, with its original producer and reader checked.
Final source review also requires every previously readable original data-string
literal to remain readable; exact bytes alone do not satisfy this check.

The final settled C/vasm receipt is
`9612c71d5e55aa78510deb55d25df9f8e17cb0d112944252837c6dc7600252b0`:
all 376,832 original bytes match. Four focused tests pass (three original CPU
message checks and the existing hardware-rendering guard). All 221 previous
readable data literals remain inside quoted data literals. Both histories retain
their complete prefixes and append 29 records each. All 126 asset payloads,
bounds, classifications and SDK include identities remain unchanged; the zero
bank stays one `dcb.w $100,$0000` directive.

Fresh accounting recovers **473 bytes**, reducing unknown payload from 7,222 to
**6,749 bytes** and raising text to 4,639 bytes. Structured data remains 340,134
bytes, with 552 declared owners and zero conflicts. Explicit supported payload
purpose is 14,036 bytes across 43 assessments; these overlapping evidence views
are not additional classified bytes. Generic label signals fall from 80 to 66.
The separate app view remains at 948 purpose bytes and a 750-byte gap. Native
accesses remain 967 resolved and 32 unresolved (five field gaps and 27 dynamic
indexed records), with the same unresolved field identities.

Export opportunity, deferred: `$C3A8..$D0A8` is a contiguous 3,328-byte A–Z
large-glyph prefix (26 existing 128-byte owners, including the retained nonstandard
W selector). The original selector/32-row copy establishes the related prefix;
it does not bound unchecked nonalphabet inputs or prove allocation lifetime.
These owners currently have role `data` and render inline. Native package export
already coalesces eligible contiguous rows, but requires supported media flags,
the same region ID and no interior labels (`m68k_source_package.c`, `eligible`
and `joins_asset_run`). A minimal general addition is an evidence-backed named
export-resource span independent of analysis owners, with glyph labels retained
as source-offset aliases (or slices of one file). This would allow one named
font asset without merging the glyph analyses or the preceding unknown scratch
tail. No grouping, media reclassification or asset-count change is made here.

### Retained scene geometry and idle reference (2026-10-19)

Three 18-byte scene headers at `$4C816`, `$4C828` and `$4C83A`, plus the retained
idle-geometry LONG at `$48606`, account for 58 bytes. They reuse the existing
frame/pointer schemas in three new owners, with three medium-confidence purpose
scopes. All seven pointer fields render symbolically. The bank-51 header uses a
stored-source mask; the bank-52 pair uses generated runtime mask inputs. Source
review after the first exact gate caught the shared frame type's runtime-only
mask domain leaving the stored mask numeric. One explicit leaf interpretation
records `$55C90 -> source $45C90` through the normal catalog, adding its mapping
alias while preserving the shared type and all generated-mask equates.

Six original CPU cases check four headers' pixel/mask inputs and packed clipping
bounds, the player's positive-X held selection under supplied mode, and the
feedback clear routine's direct idle target. The trailing LONG matches that
target but stays separate from the eight-entry indexed table; its consumption is
unestablished. Stored layout/local behavior and nominal bank bounds do not prove
ordinary activation, all consumers, DMA/display output or allocation/lifetime.
No framework or font-export change is included.

The player held header `$4C376..$4C388` remains unchanged: catalog creation refused
an overlap with `player_world_object` at `$4C322..$4C377`, one byte beyond its
84-byte fields. The refused batch appended no actions. Create/rename/describe/
remove are supported, but bounded owner resize is missing. A follow-up resize
must retain owner identity and elements/bindings, refusing excluded fields or
new overlaps. This slice preserves the player owner and completes only the
nonoverlapping records.

Final C/vasm receipt: `41d66f65aeffcb07271015a4af800db56cfa160fbb61fc4bb26346cb158c1ce2`.
All 376,832 original bytes match. Prior readable strings, compact fills, SDK
expressions and all 126 asset identities/bounds/classifications/hashes and SDK
includes are preserved. Existing owners, types, register seeds, workspace
contracts and prior equates remain intact. Both histories retain their prefixes
and append ten records each.

Fresh accounting reduces unknown payload from 6,749 to **6,691 bytes**; structured
data rises to 340,192 bytes, with 555 declared owners and zero conflicts. Explicit
supported payload purpose is 14,094 bytes across 46 assessments. The app view
remains at a 750-byte gap and 948 purpose bytes; native accesses remain 967
resolved and 32 unresolved (five field gaps, 27 dynamic indexed records), with
unchanged unresolved field identities. Generic label signals remain 66. These
are bounded storage/local-reader gains, with the player boundary blocker and
ordinary activation limits retained.

### Combined declaration/text audit and coordinate boundary (2026-10-19)

The 242-byte audit recovers **197 bytes**: six complete strings (101 bytes),
the overlay startup-clear tail (64 bytes in sixteen LONG units), and two retained
offer runs (32 bytes). Original descriptor pointers link `HIT`/`ENMY` to the two
overlay titles. The formatter text ends after four characters and NUL; its sixth
byte remains unknown. A supported partial-range command excludes the neighboring
instruction. Retained terminal blank text and `gunfire.dat` have stored bounds,
without an activation or file-load claim. The light-box/gin offer runs each keep
two separate four-entry prefixes; supplied original scans/threshold loads are
checked, without asserting incoming activation or a current/initial relationship.

The two unreferenced 16-byte zero tails and extra formatter byte remain unknown
(**33 bytes**). Both seven-byte weapon tables use existing bounded byte seeds,
and all 256 item-byte cases establish the seven pairs and fallback. Nevertheless,
full-image native ownership still covers only one byte per table, unlike the
isolated bounded-seed preflight: **12 bytes remain a native ownership/policy-
reconciliation blocker**. No new array or resize feature is added.

One bounded pass retains all **6,260 bytes** in the three large spans. The
3,840-byte `$B4A8..$C3A8` run has 178 nonzero bytes in its first 768 bytes and a
3,072-byte zero suffix. Its candidate blocks fail the known cursor seed's
skipped-half invariant (16/34/50 nonzero skipped bytes versus zero); no cursor
variants are inferred. The 1,392-byte `$39DC8..$3A338` run is zero, and the
1,028-byte `$52..$456` span is stack-adjacent, not a proved allocation. Cached
native direct-target sets are empty inside these spans; derived accesses and
initial file meaning remain unclosed. Scratch writes do not establish that meaning.

The original clear writes app `[0,$36C)` and stops at `$3D68`; the grid builder
separately selects `$4000` (app `+$604`). A guarded CPU check leaves the 664
intervening bytes untouched. These are write/root bounds, not allocation bounds.
General report wording now clarifies that observed-envelope gaps imply neither
allocated nor unused storage. All **750 coordinate-gap bytes** remain unknown,
including the other 86 prefix-gap bytes. The player owner overlap and deferred
font-grouping opportunity are unchanged.

Six original CPU checks and all 24 accounting tests pass. Final C/vasm receipt
`b45c5b16a2a82b644116d62ddc49782d68d547b080a3d4ec4f3e8a8804e9a8b9`
reproduces all 376,832 bytes. Prior readable literals, SDK expressions, compact
WORD blank bank and all 126 asset/SDK identities remain intact. Two owners are
added; only the prior clear-tail owner's elements change. Both histories preserve
their prefixes and append 26 records each.

Fresh accounting leaves **6,494 unknown payload bytes**, with 340,288 structured
bytes, 4,740 text bytes, 557 owners, zero conflicts and 64 generic label signals.
Supported purpose is 14,305 bytes across 57 assessments (a separate evidence view).
The 967 resolved/32 unresolved native accesses and unresolved field identities
remain unchanged. The audit closes 197 bytes, retains 33 evidence-limited bytes
and exposes the remaining 12-byte native coverage gap without an extra detour.

### Dominant-range evidence and bank-30 tracing limit (2026-10-19)

[Persisted observations](../validation/pandora-dominant-payload-evidence.json)
retain the finite original-CPU probes, packet inputs, 369-header audit and paired
capacity arithmetic. Bank 30 packs 5,264 pixel/1,316 mask bytes into spans matching
thirteen full-frame budgets of 6,656/1,664 bytes; suffixes are 1,392/348 bytes.
This supports a retained-capacity interpretation without proving its original
reservation or padding intent. Two modeled final-frame draws program a B-channel
envelope through runtime `$49DCA`, two bytes into the pixel suffix.

Actual chipset reads remain unobserved. The pinned Copperline 1.0.0 executable
and legal ROM are present, but the supported public session interface exposes
snapshots and write watches, not chipset read tracing; its parser rejects the
read-watch request before launch. No emulator replay, alternate control path,
upgrade or new runtime feature was attempted. This does not establish that the
underlying emulator fundamentally lacks tracing. Next required evidence is an
agent-attributed read trace for this single packet, plus producer/reservation
evidence for the complete suffix. No target facts or classifications change;
6,494 payload bytes and 750 workspace coordinate-gap bytes remain unknown.

### Bank-30 bounded watch implementation and live limitation (2026-10-19)

The supported Copperline session wrapper now accepts typed memory-access watches
at verified canonical source anchors. It resolves absolute or paused A-register
addresses, confirms the exact registered filter through `break.list`, retains
raw stop evidence, and removes its owned watch on every outcome. Mismatched
readback fails before resume; marker-value polling remains separate. Focused
runtime/control/checkpoint/symbol tests pass: 158, with two optional raw-emulator
tests skipped. Generated target source and analysis facts are unchanged.

[Live evidence](../../runtime/observations/pandora-bank30-access-watch.json)
records three bounded runs against the original payload. The original shifted
BLTSIZE instruction at source `$6B0A` was reached with B-source A0=`$3152E`,
BLTSIZE D7=`$0782` (two WORDs by 30 rows), and B-modulo D5=`12`. A read/blitter
watch on that programmed source timed out. An independent eight-second watch
on `$49DC8` also timed out; its registration and backend readback agree exactly
on address, read access and blitter class. Neither run observed a DMA read.

The failed control prevents treating the suffix timeout as proof of non-use.
The captured launch is not the modeled final-frame packet (`$49D16`, two WORDs
by 12 rows, modulo 12). Actual read-event operation and that packet's live
reachability remain unresolved. Named/numeric packet-register capture batches
returned RPC `-32007` before arming; the successful watch attempts omit them.
Official-source inspection was blocked by proxy HTTP 403 and a restricted
browser URL, with no retries or bypass. Copperline stays at 1.0.0 under the
existing 68000/OCS profile; the advertised 1.0.1 fast-CPU terminal-window fix
does not apply to the configured 68000. No new classification or whole-range
claim is made: 6,494 payload bytes and 750 workspace coordinate-gap bytes remain
unknown. The two-byte overfetch remains a programmed-envelope model, not an
observed chipset transaction.

### Bounded read-watch diagnosis (2026-10-19)

[Follow-up evidence](../../runtime/observations/pandora-read-watch-stop-diagnosis.json)
confirms the original draw path and CPU watch delivery. A one-second read/cpu
watch hit the stack WORD at `$10416` during the original MOVEM at `$16B0E`;
the value matches the saved stack, and the paused PC/SP reflect the completed
instruction. A subsequent two-second read/blitter watch on the next programmed
B-source `$31536` timed out despite exact filter readback. Execution advanced
91 frames and retired 752,370 instructions between the recorded stops, including
the intervening anchor wait.

A general transport defect was reproduced and corrected: deadline recovery
discarded the resumed-run and pause reply bodies. The wrapper now retains both
and the bounded stop-notification snapshot without promoting late events to
successful observations. The corrected live run contains only pause replies
and no queued stop notifications, so that defect is not established as the
cause of the missed blitter control. Focused checks pass: 161 tests, two optional
tests skipped. No new source inspection was attempted after the prior denials.

The precise remaining question is whether and how this build forwards blitter
B-source DMA reads to the registered read-watch dispatcher. The denied official
source inspection would be needed to inspect that hook; this dependent path is
stopped. No actual bank30 DMA read or last-frame packet is captured. Original
payload, generated source, classifications, 6,494 unknown payload bytes and 750
workspace coordinate-gap bytes remain unchanged.

### Primary sample-bank formats and waveform source (2026-10-19)

One connected restoration swath adds and accepts 95 catalog interpretations.
The [inventory and proof](../validation/pandora-primary-sample-bank.json) cover
the eleven variable-length records at `$4EAD8..$5500A`: 66 header bytes and
25,840 PCM payload bytes. All headers now use one six-byte
`audio_sample_header` schema, with qualified header identities instead of
generic `byte_length_N` labels. The first `audio_sample_record_stream` anchor
is preserved. Headers are separated by their payloads, not a contiguous array.

The guarded constructor, its three loops and return have purpose names. Nine
constants name the DBF terminal index, original period dividend, silence span,
waveform halves/levels, DMA WORD count and directional turn offsets. The period
dividend is not derived from the runtime PAL profile. A scoped header-cursor
input contract gives the two original postincrement reads their field names.
The 132-byte runtime descriptor table retains its eleven initial NULL pointer
fields: the constructor relation is documented without inventing encoded source
pointers to each payload.

The 16-, 8- and 4-byte stored square-wave cycles now expose negative and positive
halves (`C0` / `3D`). Recorded sound identities remain unknown. Sample7's stored
`C0` / `3E` bytes and its original runtime `C0` / `3F` initialization remain
distinct and unchanged. Its WORD cursor is now correctly named as a **byte
offset for a WORD write** in both the base view and source storage. The turn
constants do not assert global index, writer, allocation or lifetime closure.

Sixteen bounded purpose assessments add **26,218 supported bytes**, including
the constructor/writer, runtime descriptors, cursor state and silence buffer.
The already assessed 64-byte sample7 payload is excluded from new credit.
Supported payload purpose rises **14,305 -> 40,523 bytes** across 73 assessments;
this is separate from native classification. Unknown payload remains **6,494
bytes**, and the app coordinate gap remains **750 bytes**. There are still 265
function candidates, 557 declared owners and 126 asset chunks. Native resolved
field records rise **967 -> 969**; the 32 unresolved identities remain. Generic
label review signals fall **64 -> 50**, without a semantic-completion percentage.

Seven relevant original-CPU cases and the Pandora hardware-readability guard
pass. Full C and independent vasm output match all 376,832 original bytes,
SHA256 `70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`,
receipt `75e097551ee0eca7a800788ca9faaadaab2ab4d629e224e0e76ade863a76ffb2`.
All 126 asset identities/paths/sizes/hashes and all 16 SDK includes retain their
bytes; only native listing-row positions shift. Both durable histories retain
their prior prefixes. No framework change or new DMA experiment was needed.

The existing reachable draw values reconcile cheaply to a configured envelope
`$3152E..$316FE` (two WORDs, 30 rows, modulo12), not the modeled final bank30
packet. This is addressed-storage arithmetic, not observed DMA or meaningful
image-content bounds. The bank30 uncertainty remains parked.

## Planar mask reader and constant input contracts

Nine accepted facts connect the original mask reader to the existing shared
`world_tile_planar_row` format, name its two loop stages, expose the eight-byte
stride shift and document its count/cursor contracts. Four postincrement reads
now identify the four plane WORD fields. The inner helper saves/restores D0,
D7, A0 and A1; the wrapper advances cursors using WORD strides and ADDA.W sign
extension. Arbitrary counts remain unchecked.

All 59 original initializer packets execute in the CPU fixtures and produce the
expected mask WORDs from 172,640 input bytes into 43,160 mask bytes. Tests check
source preservation, output end fences and final cursor extents; a separate
case checks the helper's saved full registers. All 315 inspected instruction
encodings match the original. Sixty CPU cases and the hardware-readability
guard pass. C and independent vasm reproduce all 376,832 original bytes;
receipt `12fd3b4db1206de0bb1d0cebbc7ba0327f72e267a77a38bd35a517377db3ea21`.
All 126 assets, 16 SDK includes and both history prefixes are preserved.

Supported source purpose rises by 1,282 bytes to 41,805 across 75 assessments;
resolved native field records rise from 969 to 973, and generic labels fall from
50 to 48. Classification, 6,494 unknown payload bytes and all 40 unresolved
structure identities remain unchanged.

Physical type bindings for the 56 flat input banks remain unapplied: their
20,620 cells expand to 82,480 named WORD fields, exceeding the documented
32,768 native named-label capacity. Normal preflight refused that request before
history append. Existing physical arrays and the three six-frame groupings
remain intact. This is a bulk-typing capacity limit; the shared reader contract
is accepted. Individual image grouping, complete writers/lifetimes, allocation
and actual DMA reads remain unproved. The packet inventory and precise blocker
are in [the validation record](../validation/pandora-planar-mask-inputs.json).

## Compact array typing and shared mask-bank formats

The label-capacity blocker is resolved without increasing either native cap or
changing the ABI. The catalog retains an explicit `array` kind when binding a
structure. Packed uniform scalar arrays use the existing native typed-range
model, with the shared schema and canonical count/stride retained. Explicit
record views, pointers, gaps and field-specific presentations keep their leaf
projection. Interior cursors, named anchors and exact source bytes remain
covered by the regression fixtures.

Fifty-six accepted bank bindings describe 20,620 cells and 82,480 logical WORD
fields across 164,960 source bytes. The effective entity count stays at 18,304,
with existing identities preserved. Each bank now has one `ARRAY type[count]`
declaration and its existing INCBIN; the three six-frame groupings remain intact.
Native rendering no longer repeats a range's owner name on every data row.

Two further accepted facts declare the cursor seed destinations as runtime
namespaces with observed 64-byte startup write footprints. The native typer now
honors that domain instead of borrowing an unrelated structure from a numerically
overlapping image load view. The original CPU test checks both complete payloads,
final cursors and unchanged control LONGs; allocation and later lifetime remain
unproved. The cursor writes retain their previous source presentation.

The 219 selected metadata/catalog/storage checks, 208 range/domain/reference/
export checks and 820 native unit cases pass. Five failures in an additional
opt-in backend subset reproduce with the pre-change Python modules and native
library; their identities are retained in the validation record. Final C and
independent vasm output match all 376,832 original bytes, receipt
`151e0e02e6036c05b2b909937782f06606532a53de7438bec4f240d79312bca5`.
All 126 asset identities, classifications, paths, sizes, hashes and bytes, all
16 SDK includes and both history prefixes are preserved. Listing-row positions
can shift; the 910-cell bank's numeric presentation reduces from 543 to 455 rows.
Classification, purpose credit and all 40 unresolved structure identities remain
unchanged; this batch enriches the retained formats rather than claiming new
payload coverage.

## Retained feedback selector entries

Eight code-entry facts and eight explicit labels restore the previously unknown
48-byte span `0x4D2CE..0x4D2FE`. Each six-byte entry loads a packed channel/configuration
selector into D0.W and tail-branches to the existing shared feedback handler.
Six select channel 3/configuration 0; the others select channel 2/configuration 0
and channel 2/configuration 17. Names describe these established selectors and
retain distinct entry identities without inventing game-event or sound names.

The focused original-CPU test covers all eight entries with two D0 upper words
and four flag-byte inputs: 64 cases. It stops at the actual audio callee before
MMIO and checks the selector, preserved registers, title-service bit, 52-byte
MOVEM save and real return PC. No instruction bytes are patched. The current
native incoming-reference query finds no static references to this span;
ordinary activation, dynamic callers and audible/DMA behavior remain unproved.
The bounded assessment and entry inventory are retained in
[the validation record](../validation/pandora-retained-audio-entries.json).

C and independent vasm reproduce all 376,832 original bytes; final receipt
`76386fbb85d4e3f05f79fc9f2d9330c908b022f0fbc603cf1a7d1ceb8aa6d850`.
The 17 facts and 17 decisions preserve both prior history prefixes. All 126
assets and 16 SDK includes retain their identities, classifications, paths,
sizes, hashes and bytes. Unknown payload falls from 6,494 to 6,446 bytes;
supported source purpose rises from 41,805 to 41,853 across 76 assessments.
Prior field-access records, unresolved structure records and the 48 generic
label signals remain unchanged.

## Shared world and modal tile cell formats

The 25 established world-tile banks and the modal tile bank contain 504 cells
across 64,512 source bytes. Their existing owners, labels, cell counts and
128-byte strides are retained. The shared `world_tile_planar_cell` contains
sixteen embedded `world_tile_planar_row` records, exposing 32,256 logical WORD
fields through the existing four-plane row format. The 33 separately restored
unselected cells retain their existing sixteen-row bindings.

The original macro map selects exactly the 475 world cells in these banks.
The stored 20x8 modal pointer grid addresses all 29 modal cells and world cell
82; its 160 entries receive the shared cell pointee contract. These are original
stored selections and conditional reader contracts. They do not establish every
later consumer/writer, ordinary gameplay admission, actual displayed pixels,
DMA completion, complete allocation/lifetime or alternate-layout safety. The
retained feedback-entry activation limit from `4c7a6b1c` remains open.

The compact-array projection now accepts fully covered embedded custom records
with one common scalar width. It retains declared composition and rejects
unknown/cyclic or size-mismatched records, mixed widths, pointers, gaps and
field-specific presentations. Both ordinary embedded aliases and aliases from
a leading record that inherits the public owner name keep the leaf path.
Native capacities and the ABI are unchanged. A generic 640-record fixture
retains 40,960 logical WORD fields as one range and reproduces all bytes through
C and vasm; interior/one-past cursors and compact INCBIN export are covered.
Typed table references now use bounded owner-plus-offset expressions, avoiding
automatic interior labels that expand INCBIN banks. Single-record arrays also
retain compact storage; authored interior names keep their source boundary.
The 144 renderer/pointer/package checks, 59 metadata checks, five explicit-media
checks and 820 native cases pass, alongside the earlier 36 related tile/pointer
checks. The inventory and bounded evidence are in
[the validation record](../validation/pandora-tile-cell-formats.json).

All 55 facts have final accepted review against receipt
`26bdb38da5361365b9a5ce4c7893a3228f9a5694d045279f22036fff0aa25b78`;
C and independent vasm reproduce all 376,832 original bytes. All 126 assets
and 16 SDK includes retain their identities, classifications, paths, sizes,
hashes and actual bytes. All 557 owners and physical groupings, prior types and
contracts, and both history prefixes are preserved. Effective entities remain
18,304; logical fields use 26 compact cell ranges.

Supported source purpose rises by 65,152 bytes to 107,005 across 103 assessments.
Accepted native reference targets rise from 563 to 723. The 640-byte modal grid
moves from structured data to pointer-table classification. Unknown payload
remains 6,446 bytes, native field records remain 973 resolved/32 unresolved,
and the prior unresolved identity set and 48 generic-label signals are unchanged.

## Shared animation pixel formats and frame-pointer contracts

The three existing six-frame image banks retain their owners and frame pitches
of 512, 256 and 512 bytes. Eighteen stored headers establish 32x32, 16x32 and
32x32 frames respectively. Their source format is now composed from the shared
eight-byte four-plane word-column: a 32-pixel row contains two adjacent columns,
and each complete frame contains 32 rows. These bindings cover 7,680 bytes and
3,840 logical plane WORDs without flattening the accepted frame groupings.

The geometry reader multiplies the column count by eight for raster-row pitch,
advances pixels by eight bytes per horizontal column, and starts the four plane
sources at offsets 0/2/4/6. This layout is not the conventional arrangement of
two adjacent words from one plane. All eighteen mask pointers match the
original six-group initializer footprints. The three focused original CPU cases
pass mask values, output fences, unchanged source bytes and final cursors;
unchanged renderer and framework checks from `57af8454` are reused.

Both geometry views now give the pixel pointer the shared word-column pointee
contract. Of 368 original header values, 366 are aligned to eight-byte cells in
existing bitmap chunks; two use the already documented 512-byte shared zero
carrier. This is a first-cell format and conditional reader contract. It does
not close every other frame's extent, later mutation, ordinary activation,
actual pixel/DMA output, allocation/lifetime or alternate-layout safety. Mask
pointer domains and all other existing field properties remain intact. Declared
frame bytes describe the pixel format; shifted two-WORD packets can still read
a neighboring WORD, as the existing CPU packet contracts document.
The inventory and bounded evidence are in
[the validation record](../validation/pandora-animation-pixel-formats.json).

All 13 actions have accepted review against final receipt
`90a46255f8907855f805219487a666c397d1f1a097682ccd400cc797e9724314`;
C and independent vasm reproduce all 376,832 original bytes. The effective
projection is checked after the two field-specific updates. All 557 owners,
physical groupings, 126 asset files, 16 SDK includes and prior history bytes are
preserved; effective entities remain 18,304. Every currently emitted bitmap
chunk now has a source-format binding: 118 chunks across 241,376 bytes. This
does not establish individual image grouping for the flat scene banks.

Supported source purpose increases by 7,680 bytes to 114,685 across 106
assessments. Classification and 6,446 unknown bytes remain unchanged, as do
723 accepted native reference targets, 973 resolved/32 unresolved field records,
the prior unresolved identity set and 48 generic-label signals.

## Terrain offset and record-index relations

The existing 43x30 macro map contains 1,290 unsigned WORD indices into 468
18-byte definition records. Each record retains its nine named WORD offsets
into the pixel atlas. All 4,212 offsets are unsigned byte distances from source
`$D0A8`, aligned to 128-byte cells, with a maximum of `$FD80`. The 1,074 offsets
with bit 15 set must remain zero-extended. The original builder's clearing,
unsigned multiplication and long address additions establish both encodings;
its CPU test reproduces the complete 90x129 pointer grid and output fences.

Two compact range declarations now expose all 5,502 relations across 11,004
source bytes. The native reader retains each raw WORD, signedness, scale and
precise source/base/target coordinates; both xref roles are queryable. All 5,502
native records match the original binary independently. The existing 398
scalar declarations and 512-declaration capacity remain intact: the family
consumes two slots, giving 400 declarations. Native accepted reference targets
increase from 723 to 6,225.

The generated source replaces exactly 4,212 numeric pixel offsets with bounded
image-owner expressions. Every other source line is unchanged, including the
compact numeric macro map, SDK hardware symbols and all field annotations.
A same-owner record index keeps its raw numeric form instead of emitting a
cancelling owner-minus-owner expression. The reusable scaled form still
supports independently named records; C and vasm tests cover that spelling,
unsigned `$FFFF`, signed offsets and a 600-entry range. Invalid spans, mixed or
padded typed leaves, overlapping owners, wrong raw values and out-of-bounds
later targets are rejected.

All 146 reference-family tests, 135 related compact/pointer/package tests,
821 native cases and the original builder case pass. Both facts have accepted
review against receipt `89bce423b714742ae0f888f3436aad84e608eb33f16216c2368680dbc3223db7`. C and independent vasm reproduce
all 376,832 original bytes. All 557 owners, 73 types, 18,304 effective entities,
126 asset files, 16 SDK includes, physical groupings and prior history bytes
remain preserved. The inventory, exact receipt and full native parity check
are in [the validation record](../validation/pandora-terrain-reference-encodings.json).

This describes stored encodings and conditional reader behavior. The original
map selects 453 of the 468 records and 475 atlas cells; all records reference
476 cells, including cell 499 only in an unselected record. Arbitrary future
indices, allocation/lifetime, activation and actual DMA output remain outside
this proof. Supported source purpose remains 114,685 bytes across 106
assessments. Classification, 6,446 unknown bytes, 973 resolved/32 unresolved
native field records, unresolved identities and 48 generic-label signals are
unchanged.

## Scene frame layouts across the existing pixel banks

Original stored geometry and mask initializer footprints now establish 274
distinct frame spans across 41 existing scene pixel banks, covering 141,408
bytes and 70,704 plane WORDs. All 275 stored header occurrences agree, including
the two views of one shared frame. Their source footprints concatenate without
gaps, overlap or overrun, and every mask pointer matches the initializer's
runtime destination plus one quarter of its pixel offset.

The banks retain their physical owners and asset boundaries. Forty-seven new
frame formats and one shared 64-pixel storage row extend the established
eight-byte four-plane word-column. Twelve collection layouts describe variable
frame sequences, including one inline prefix for the 43-frame bank. Frames
taller than 32 rows and the large sequence use embedded prefixes to retain the existing 32-field
limit. The effective layouts reproduce the original row/column/plane ordering
of every WORD. Row capacity remains distinct from nominal display/collision
width; unused pixels are not inferred. Narrow, non-covering and conflicting
views remain unchanged, as do existing fonts and their groupings.

A renderer gap would have removed the declared type from 29 singleton bank
labels. Compact one-record arrays now retain `ARRAY Type[1]`; three older
compact single-cell labels gain the same missing annotation. Expanded records
retain their existing field comments. The two positive regression cases fail
before the fix; all 138 affected renderer/package tests and 821 native cases
pass afterward. The 60 original mask CPU cases from `8f1d1c74` are reused:
their binary inputs and reader/initializer instructions have not changed.

All 142 facts have accepted review against final receipt
`d4ed0bfe1ba727333ccc9265395c28ba172e760268ce3781fdbda8ade1c938b5`.
C and independent vasm reproduce all 376,832 original bytes. Apart from the 60 type declarations, 41 selected bank annotations and
three restored singleton annotations, source text is identical to `7833cd16`.
All 557 owners, 73 prior types, 18,304 effective entities, 126 assets, 16 SDK
includes, earlier references and history prefixes are preserved. Details and
per-bank footprints are in [the validation record](../validation/pandora-scene-frame-formats.json).

The 41 bounded graphics assessments increase supported source purpose from
114,685 to 256,093 bytes across 147 assessments. Classification, 6,446 unknown
bytes, 6,225 accepted native reference targets, 973 resolved/32 unresolved
field records, unresolved identities and 48 generic-label signals are
unchanged. Stored source views do not establish ordinary activation, shifted
DMA-read extents, actual pixels, exclusive allocation/lifetime, all later
writers or alternate-layout safety.

## Remaining scene frames and mask producer groups

Fourteen existing scene pixel banks now retain their supported frame or producer
group boundaries across 22,416 bytes and 11,208 plane WORDs. Nine banks contain
39 complete frame spans (8,592 bytes); five others contain 30 producer-defined
groups of 32 or 64 four-plane cells (13,824 bytes). All 68 stored headers agree
with their original source pointers and geometry words. The producer-group
headers start at group boundaries and their live spans fit within their groups.

Ten shared narrow-frame formats, two mixed frame collections and two linear
producer-group formats reuse the existing four-plane cell. Existing 16x16 cells
and wider frame formats are reused. These are embedded source layouts, not new
physical resources. Every effective scalar leaf retains its original offset
and plane order. Only the 14 declarations and 14 selected ARRAY annotations
change source text; SDK register expressions and field comments are preserved.

Producer groups do not imply complete images. Bank05 group2 has no stored
header and retains only its 64-cell input role. Trailing cells in shorter
header views are not called padding or unused pixels. Bank51 retains its
previously established stored-mask alias (`$55C90 -> source $45C90`) rather
than being forced onto a generated-mask destination. Existing font types,
owners and glyph groupings remain unchanged. Bank45's 1,136 bytes remain
unmodified because stride1 conflicts with nominal width32 and source pitches;
no alternate geometry is assumed.

All 42 facts have accepted review against receipt `f1f36e5b32da7d56958d6b6e0e899eaea6cce0ca83e0a033bd90cdb80029b568`. C and
independent vasm reproduce all 376,832 original bytes. All 557 owners, 133 prior
types, 18,304 entities, 126 assets, 16 SDK includes, earlier references and
history prefixes are preserved. No framework change was needed: the unchanged
138 renderer/package cases and 821 native cases from `1abc1671`, and 60
original mask CPU cases from `8f1d1c74`, are reused. Per-bank geometry, producer
packets, effective-layout and source-diff evidence are in
[the validation record](../validation/pandora-remaining-scene-layouts.json).

Fourteen bounded graphics assessments raise supported source purpose from
256,093 to 278,509 bytes across 161 assessments. Classification, 6,446 unknown
bytes, 6,225 accepted native reference targets, 973 resolved/32 unresolved
field records, unresolved identities and 48 generic-label signals are
unchanged. Original stored source roles do not establish ordinary activation,
actual output, shifted DMA bounds, exclusive allocation/lifetime, all later
writers or alternate-layout safety.

## Behavior operand types propagated from their handlers

The original dispatch table selects the established X/Y-add and delay handlers
for opcodes 0, 1 and 5. Their four-byte command formats now propagate to every
original occurrence across 24 behavior scripts: 64 X deltas, 65 Y deltas and
191 countdown values. The existing `cmd_axis_delta` and `cmd_delay` schemas
replace the generic word-operand binding on 320 commands (1,280 bytes). No new
schema is needed. A generated-label suffix matcher bug was fixed after source
review caught twelve unintended labels.

The handlers read the WORD at +2, update the selected coordinate or script
countdown WORD, and advance the command cursor by four bytes. Original dispatch
pointers, opcode/operand bytes, sizes and these accesses agree. WORD wrap is
preserved. Delay values need not be positive or nonzero, and their ticks do
not imply a fixed wall-clock duration. The original stored script graph is
distinct from ordinary activation, arbitrary later writes or a closed callback
target set. The previous original-script audit remains applicable because its
binary, dispatch and handler instructions are unchanged.

Source review proves exactly 320 operand comments change from `operand_word`
to `delta` or `ticks`. The matcher fix also suppresses 51 older unreferenced
generated field-label statements affected by the same earlier-name match.
Each has one original assembler occurrence and retains its exact metadata
identity; none is an explicit source anchor. Every other source character is
identical to `4096586c`, including all EQU/RS declarations, remaining symbols,
opcode expressions, instruction comments and SDK register expressions. The
former 320 derived operand aliases were not emitted. All 129
relative-copy commands and their authored offset aliases remain unchanged, as
do bank45 and all font owners/types/groupings. All 147 prior schemas, 557 owner
identities/extents, 18,304 entities, prior references and representations, 126
assets, 16 SDK files and both history prefixes are preserved. The only layout
metadata changes are the intended 320 bindings and 640 derived command fields.

No new EQU/RS definitions or symbolic operand expressions are added; the
reported gain is semantic field comments and handler-matching type bindings.

All 344 facts (320 bindings and 24 bounded script purposes) have accepted
review against receipt
`110913bda1a6aa2b8dea23d85240f874bc426c86a7b63c7ff8bfe2d27cadef55`.
C and independent vasm reproduce all 376,832 original bytes. The six focused
regression cases cover repeated names, singleton/repeated records and explicit
source anchors; five failed before the matcher fix.
All 61 affected renderer/struct/pointer cases and 821 native cases now pass.
EQU and RS declaration policy is unchanged. Per-script
occurrences, original operand words, handler contracts and preservation
evidence are in [the validation record](../validation/pandora-behavior-operand-types.json).

The 24 script scopes cover 3,918 bytes and increase supported source purpose
from 278,509 to 282,427 bytes across 185 assessments. Classification, 6,446
unknown bytes, 6,225 accepted native reference targets, 973 resolved/32
unresolved field records, unresolved identities and 48 generic-label signals
are unchanged.

### Focused dominant-span runtime tracing (2026-10-20)

[Published observation record](../../runtime/observations/pandora-unknown-span-tracing.json)
separates snapshots, CPU architectural events and physical chip-bus transfers.
The original direct payload reaches all 17 phases of the representative route:
entry-officer card transfer, 19 down and 20 right movement commits, nearby
interaction call/return, snapshot batches and a verified checkpoint. Original
loader/disk parity remains outside this experiment.

The restricted runtime now supports CPU ranges through the documented data-access
trap, plus bounded full slot profiles through the existing Copperline 1.0.0
profiler. A live positive control records 40 blitter WORD reads whose values all
match original target pixels. This independently validates DMA read capture;
it does not validate the previously unsuccessful single-address read watch.
No emulator change or denied source-access retry was needed.

Post-route capture records 256 blitter WORD writes and 128 reads within source
`$B4A8..$B5A8`. All 128 reads match preceding writes in the same profile frame;
they select the second WORD of each four-byte pair. Packets stage four planes
at scratch `$1B3A8+4p`, width two WORDs, height 32, destination modulo 12, then
copy 128 one-WORD rows from `$1B3AA` with source modulo 2. This agrees with the
already documented second-word edge renderer and demonstrates actual shared
scratch overlap. It does not explain the original seed bytes or reserve all
3,840 bytes. The snapshot's 178 changed bytes acquire new nonzero contents;
they were not cleared to zero. A three-second first-gameplay CPU write watch
times out while the buffer changes; that negative CPU window is distinct from
the later positive DMA window.

The inventory-handler RTS at source `$2918` reads LONG return address `$105DA`
from runtime `$1044E`; the accessing PC is independently byte-matched and differs
from the paused return PC. Stack bus activity is also observed. These establish
use of touched addresses, not a 1,028-byte stack allocation. The 1,392-byte bank-30
suffix remains unchanged in the route snapshots, with no transfer in these
specific startup/post-route profile windows. No defeat sequence or final-frame
packet is covered, so this is not evidence of non-use.

The four-frame aggregate retains only 4,096 of 11,991 matching transfers; all
aggregate counts still scan every slot. Re-filtering those same local sidecars
for the cursor gap retains all 384 relevant transfers without omission. Native
frame labels, first-partial flags and raw sidecar hashes are preserved; guest
states and unfiltered streams remain ignored locally. The focused suite passes
217 tests with two optional tests skipped. Target facts, generated assembly and
assets remain unchanged from `ac7a3801`, preserving its exact 376,832-byte receipt
`110913bda1a6aa2b8dea23d85240f874bc426c86a7b63c7ff8bfe2d27cadef55`.
The 6,446 unknown bytes remain explicit: runtime reuse alone does not justify a
new interpretation of their original contents. Fonts, bank 45 and EQU/RS policy
are unchanged.

A final two-frame probe binds that DMA to canonical source `$6C60` at native
frame 935. Entry registers give height 32, shift 4, pixel source `$50E08`, mask
`$685FC` and destination `$72A80`. Stack `$1042E` holds return `$17090` into
`draw_geometry_left_shifted_edge`; original BSR bytes at source `$708C` target
`$6C60` exactly. The full scratch window records 256 WORD writes and 128 reads
through `$1B5A8`, without omitted records; every read matches its preceding
write. A final canonical main-loop anchor is reached. All nine runs are complete;
the two negative CPU windows intentionally report timeout/incomplete, rather
than being presented as successful access observations. This closes the dynamic
producer/consumer question for the observed scratch rows without inventing an
original layout for the remaining bytes.


### Behavioural-validation programme: first bounded batch (2026-10-20)

[Proposal 045](../proposals/045-behavioural-validation.md) tracks B01–B10 with
separate capability and target-coverage status. The reversing-loop checklist now
requires contract/evidence identities, explicit outcomes, remaining obligations
and the next evidence question in each connected batch. No competing fact store
or tracker was added.

The existing volume comparator now uses an opt-in observer in the generated
Motorola-derived backend. It admits captured/modelled cells explicitly, refuses
required unknown reads and forbidden writes, and retains ordered accesses rather
than inferring equivalence from sorted/deduplicated final effects. CPU-only
predicates pass for all 19 admitted routine cases, including WORD-wrap boundaries,
and all 65,536 WORD inputs to the original/derived BYTE instruction. Receipt:
`45c0a0c720d059b0cf112327da8ed6c6b0917538c7b9781e788eedc1fbaaea7d`.
Modeled call frames, guard inputs and normalization of only the two-byte logical
volume location establish neither normal gameplay nor IRQ/Paula/DMA equivalence.

The genuinely different renderer case reuses Copperline, checkpoint binding and
full bus sidecars. Fresh original replay matches all 384 ordered transfers:
256 D writes and 128 A reads; every read follows and matches its producer. Exact
address order is checked, and an equal-final-buffer read-before-write mutant
fails. Receipt:
`1194ac8fe944667bd49ca76ea10a70c1f011430054b5950a688f080aaa36f737`.
This validates one bounded scratch predicate and repeatability, not a renderer
candidate, source/mask bounds, final bitmap, all-callers lifetime or relocation.

Both contracts are canonical function-summary notes created through the existing
command catalog and accepted through MAL/DJ review. Real pre-review evaluations
correctly returned missing-prerequisite despite passing predicates; fresh
content-addressed receipts qualify only after review. CLI/MCP/HTTP share one
restoration evaluator. Tests cover all outcome categories and stale identity
admission. The optional MCP SDK is absent, so live stdio transport is not claimed;
adapter forwarding and HTTP operations are tested.

[Public evidence](../validation/pandora-behavioural-validation-first-slice.json)
contains identities and summaries; captured register arrays, payloads, ROMs,
checkpoints and unfiltered streams remain local. C/vasm receipt
`3006167ec76ea06a645800f8ebeb3047bcc55e3ed317cb1b21a921e19b0e3f5f`
reproduces all 376,832 bytes. Assembly SHA remains
`85bfb2faaec8a717af0e240b9bbadf962269253d0cc1f8828fa73694bb09d0db`;
only package provenance changes for the two summary facts. No payload bytes are
newly classified; 6,446 remain unknown. Histories append two actions and two
decisions, preserving both prefixes. Fonts, bank 45, bank 30 and EQU/RS policy
are unchanged. All B IDs remain partial. The next question is admission of the
currently excluded audio-start path using captured inputs instead of shadow data.


## Combat-charge stored plane layout (2026-10-21)

Source `$82D4..$82F0` now exposes five groups of four binary plane bytes and
eight leading-bit masks. The charge producer at `$817A`, LONG reader at `$820A`,
partial masking at `$8216` and writer at `$823A` establish the layout: the writer
rotates each LONG by eight bits before each BYTE store, advances 40 bytes between
planes, and repeats over six raster rows. The established table-base symbol
and both physical owners remain intact. At charge 40, the lookahead reads the
mask prefix, but zero remainder suppresses partial drawing; this is not a claim
that arbitrary charge values are safe.

An aggregate-type trial produced misleading first-BYTE annotations on LONG
reads and was undone in the canonical history. Explicit scalar fields avoid
that inference without changing the renderer framework. Final source review
confirms only the table block changed, with all EQU/RS declarations preserved.
All 147 schemas, 557 owner identities/extents/roles and external assets remain
unchanged. There are 19 additional effective scalar entities, not 19 newly
classified bytes. The 28 already-classified bytes gain graphics purpose, moving
the source-purpose union from 282,427 to 282,455; unknown bytes stay at 6,446.

Final C/vasm full-file exact receipt: `e3dc4f9b72e38402e0750b7a14f45a546532ca9e2697df77741369dd56a16348`.
Both history prefixes survive; 23 accepted actions describe the final layout,
masks and purpose. No runtime capture or new test was needed, and the historical
41-charge CPU test was consulted without rerunning it. Behavioural contracts,
fixtures and B capability coverage are unchanged.

The small edit incurred four healthy whole-target generations of 282, 251, 258
and 241 seconds (17.2 minutes total), including two source-review corrections.
That is measured workflow overhead, not additional restoration coverage.
[Public evidence](../validation/pandora-combat-charge-plane-layout.json) records
the exact identities, canonical actions, scope checks and limits.


## Player held-frame header and owner boundary (2026-10-21)

The player owner now ends at `$4C376`, matching its existing 84-byte schema and
all bound fields, instead of including the first byte of the held-frame header.
The original owner action selected listing rows and recorded no field or
ownership meaning for that extra byte. The original node at `$4C744` selects
the sequence at `$4C756`, whose held entry points at the complete 18-byte header;
the shared reader at `$6F6E` consumes its two pointers and five geometry WORDs.
The reviewed 26 native player-root references, all-byte-alignment literal-pointer
audit and field/reset consumers support this explicit source boundary. They do
not prove runtime allocation, exclusive lifetime or absence of arbitrary aliases.

The header at `$4C376..$4C388` now reuses `WorldPositionAnimationFrame`, replacing
18 raw bytes with pixel/mask symbols and stride, height, width and XY fields.
It selects pixel bank 05+$400 and mask bank 05+$100, whereas the adjacent
cycling-frame group starts in bank 04. Original pointer values and nominal bank
bounds agree; this establishes storage selection, not a visual orientation.
Its existing `abs_0_0005C376` label and frame-sequence reference are preserved.
The player owner retains its ID, start, role, fields, bindings and references.
There are still 147 schemas; owners increase from 557 to 558 and effective
entities from 18,323 to 18,330. Supported source purpose increases by 18 already
bounded header bytes, from 282,455 to 282,473. Whole-target unknown-byte
accounting was not regenerated, so no updated global total is claimed.

The necessary framework addition is an end-only raw-section-0 owner resize
command. It refuses stale revisions/endpoints, out-of-file or empty ranges,
field/reference truncation, overlaps, runtime views and unsupported formats.
It uses the existing catalogue and atomic, append-only MAL/DJ paths, with
ordinary undo/redo. The changed mechanism and adjacent catalogue/history/service
checks pass all 168 tests, including deliberately invalid and stale cases.
Four target actions and four accepted decisions preserve both history prefixes.

One final generation after the reviewed metadata edits reproduces all 376,832
original bytes with C and independent vasm: receipt `641e2adf40c2d9471b4726b9d1855402fee625da8d14e6f111908fdaf756e667`.
Source review confines the diff to the header block and retains all prior labels,
EQU/RS declarations, other owners, schemas, references, assets and SDK files.
No new original-CPU test or runtime capture was needed. This is an 18-byte source
restoration and its bounded prerequisite, not a behavioural-programme milestone.
[Evidence and limits](../validation/pandora-player-held-frame.json) record the
proof, exact identities, invariant checks and measured generation costs.


## Primary audio control symbols (2026-10-21)

All 33 existing typed command records (90 bytes) now have symbolic opcode fields.
Four constants expose the original program-advance, global-note-offset,
pitch-modulation setup and channel-note-offset controls at 41 native BYTE rows
across 22 program records. Their meanings come from the original relative-WORD
dispatch table at `$4DCE8`, based on `$4D7DE`, and the named handlers; the
existing command schemas supply the matching operand widths. All note, selector,
duration and operand bytes remain unchanged, including signed note offsets and
modulation parameters. No new schema, field, owner or register seed is added.

The complete stored-format audit covers 29 program records (907 bytes), 88
controls and 12 original program lists. All 55 nonzero list entries select one
of 32 decoded token boundaries, including shared tails. Twenty-nine bounded audio
purpose facts increase supported source purpose from 282,473 to 283,380 bytes.
This establishes stored grammar and original list references, not dynamic
selector safety, later writes, gameplay activation, IRQ/DMA timing or sound.

Forty-two controls remain grouped with neighbouring bytes. Five additional
BYTE rows are shadowed by their containing array hex setting; their symbol
actions were undone without changing that policy. All 47 remain numeric.
The existing symbol command selects whole native data rows, so this batch deliberately leaves those
positions numeric rather than inventing partial selectors or splitting layouts.
The remaining source obligations are individual byte selection in grouped rows
and the interaction between explicit symbols and existing array formatting.
Neither is changed in this batch.

An isolated C/vasm preflight accepts all 41 selected expressions. The final
whole-target gate reproduces all 376,832 original bytes, receipt `0ef7834c3803e431a095cc7a822548605e9fa6be366de1c0a484050778c6e54a`.
Source review proves that only the 41 selected literal expressions and four new
constant definitions change. Every old label, EQU/RS definition and other source
character is preserved, along with all prior metadata, assets and SDK files.
The 79 initial actions, five corrective undos and 74 accepted decisions preserve
both history prefixes. Only the 74 final facts are accepted.
No framework change, new test or runtime capture was required. Whole-target
unknown-byte accounting was not recomputed; no classification reduction or
behavioural-programme milestone is claimed.

The independent resize review found no blocking invariant issue. Its limited
legacy numeric-string compatibility gap is recorded in the existing interface
documentation; no resize code or additional resize adoption is included here.
[Evidence and limits](../validation/pandora-audio-control-symbols.json) retain
the selected positions, dispatch proof, original corpus identities and receipt.

## Eight original indirect sites: reviewed original-layout closeout

[The bounded reconciliation](../validation/pandora-indirect-closeout.json) joins
the earlier native audit with the current canonical layouts and summaries.
“Unresolved” native target status does not mean the instruction or its caller is
unexplained. Conversely, known original pointers do not close future target sets.

| Source site | Current evidenced result | Genuine remaining question |
| --- | --- | --- |
| `$932` Blitter IRQ | Startup clears `app+$368` callback to NULL inside the `$36C`-byte clear. The consumer has no NULL guard. Setup masks BLIT, but dispatch samples raw requests. | No nonzero producer is established. Masking and absent named writes do not prove this branch unreachable or unused. |
| `$11DE` absolute script call | Five stored records select four targets: fixed diabetic start/toggle, item handoff and player movement. Wrapper saves A4/A5 and resumes at command+6. | Arbitrary cursors/replacement commands and callback memory/escape effects are not closed. Two fixed diabetic leaf contracts were missing and are restored in this batch. |
| `$11F2` relative script call | Signed displacement is from the opcode address; wrapper saves A4/A5 and resumes at command+4. No opcode22 occurs in 780 NPC commands plus the three-command player loop. | There is no stored original callee to invent. A computed/replaced cursor could invoke the implemented opcode; require a concrete producer before reopening. |
| `$6694` UI update call | All ten initialized descriptor callback fields are NULL. The persistent 16-slot scan visits holes, checks ready bit7 and guards a NULL callback; D7/A0 are saved. | No nonzero callback producer/target is established. Registration and readiness are not callback assignment. |
| `$7A00` combat completion | Four initial completion targets already have summaries. Caller saves A4/A5, ignores carry and calls before exchange/inactive marking; the nonnull path first blocks the priest passage. | Later completion-pointer replacement and transitive effects remain open. |
| `$83FE` nearby interaction | Fourteen nonnull fields select 13 initial targets among 35 objects. Existing 13 summaries preserve A5 on normal return. Carry requests the nonzero +$10 message, rather than reporting generic success. | Future callback targets and arbitrary effects remain open; bounded interaction observations do not close whole-game reachability. |
| `$93F4` ranged completion | Same four initial completion targets; unlike combat, this caller does not save A5. Their existing normal-return A5 contracts support its later object accesses; it performs no combat passage reset. | Replacement targets must meet that caller obligation. Preservation does not establish immutability or all effects. |
| `$4DC2A` primary audio | Eleven original signed-offset handlers and their register bases/decoder continuations are known. Runtime `$80..$9F` dispatch is wider than those 11 entries and unchecked. | `$8B..$9F`, replacement programs/selectors and a changed A3 base remain unbounded. Stored grammar is not a runtime guard. |

The stored audit reads all 780 canonical records in 26 complete NPC layouts and
the existing three-command player loop, against the original binary identity.
It does not discover all possible script cursors. The35 initial interaction and
completion fields and ten UI callback fields are audited separately. All 17
initial object target summaries already preserve A5 on normal returns; these
are retained rather than duplicated or generalized into a universal callback ABI.

The connected source change adds two missing summaries at `$4B0EA`/`$4B100`:
fixed diabetic pose installation/toggling, independent of caller A5. Both preserve
its type-neutral value on normal return. The first clobbers A0/A1, the second A0;
other general registers are preserved under the ordinary disjoint call-frame
assumption. Memory/escape effects remain explicitly unknown in the summary
schema. Source comments retain the existing controller caveat, explain fixed
rather than caller-selected state, and expose the Blitter startup-zero/no-guard
boundary. Existing labels, data layouts, bytes and histories are preserved.

No unconditional target set, unknown-byte reduction, purpose credit, DMA result,
relocation safety or full semantic-restoration completion is claimed. A missing
producer stays a named evidence obligation; it is not replaced by generic tests,
a new capture, or a fabricated callee. B07 remains paused.

This batch appends five MAL actions and five accepted DJ decisions. Function
summaries increase **93 → 95**; all previous summaries and other semantic
collections are preserved. The existing scripted-pose test passes **1/1**, with
no skips. One planned native generation takes **249.415 seconds**; C and vasm
reproduce all 376,832 bytes, receipt `d4fd9cb2cc9d6c1843f8e4f93207fb5599a62a0b29f1d2ac45cb3c50bdf6c49a`.
Source audit permits only the three semantic comment edits and preserves every
other source character, label, EQU/RS declaration and asset identity. The first
batch submission exceeded the existing 191-byte comment limit and appended
nothing; shortening those comments allowed the same facts without framework
changes. All nine paused B07 files remain unchanged. Global accounting was not
rebuilt separately; the previous unknown count remains explicitly stale.

The remaining producer questions are now finite: a nonzero Blitter callback
writer/alias and its branch conditions; a nonzero UI update-callback producer;
and replacement/mutable script, object and audio target domains. These are
specific evidence obligations, not eight anonymous routines awaiting names.
The two missing original fixed-pose contracts are filled; no other missing
original target contract was established by this audit. Continue with unresolved
dynamic consumer bounds only when their current evidence supports a concrete
source interpretation.

## Indexed consumers: finite original-layout reviewed inventory

[The seven-group inventory](../validation/pandora-indexed-consumers.json) assigns
each of the 27 baseline `indexed_dynamic` operand identities exactly once.
The scope is a qualified original-layout source review, not a fresh native
accounting run or complete semantic restoration. Existing reader semantics do
not need arbitrary hostile/replacement-input safety to be accurately documented.

| Consumer / source sites | Records | Existing bounded understanding | Remaining original-use question or limit |
| --- | ---: | --- | --- |
| Script copy `$11B2` operands 0/1 | 2 | Signed command displacement addresses a reload WORD and its adjacent remaining counter. All 130 stored copies match repeat records within their script owner. | Arbitrary cursors/relative writes remain unchecked; these addresses are not extra copy-header fields. No new missing original pair found. |
| Inventory exchange `$2A72/$2A76` | 2 | Four valid cursor rows give ID-byte offsets 0/2/4/6 in two-byte records, preserving value bytes. Existing source retains the `ANDI.B` high-byte caveat. | Backed four-record input is conditional; even stride does not bound arbitrary cursor words or prove allocation. No new field meaning is missing. |
| Audio `$4D804/$4D80E/$4D842/$4D850/$4E416/$4E476` | 6 | Three ten-byte presets select twelve existing program lists; channel pending is `12*channel+11`. All 29 secondary configurations select envelope indices 0..5, matching six declared offsets/targets. | Runtime preset/channel/configuration/envelope inputs are unchecked. Original stored domains and the existing conditional source contract are understood; replacements/device timing are separate. |
| Overlay line `$6640` | 1 | Wrapped WORD index times four, interpreted signed from descriptor+12; source explicitly has no six-line guard. | Existing boundary injections establish reader arithmetic, not original out-of-prefix activation. No descriptor enlargement is justified. |
| Deferred sort `$851A/$851E/$852C/$8530` | 4 | One-pointer-before base plus four-byte pair indices addresses the deferred array. The original 32 inputs partition into 26 deferred and six back-group records; unsigned-Y sort is documented. | Nonempty middle is an explicit precondition; empty-middle or arbitrary graph safety is not required to describe that contract. These are not four missing descriptor fields. |
| Animation `$95C6/$95D4/$95DA` | 3 | Held prefix plus four-byte active entries; XY pairs have X/Y WORDs. All 92 currently declared node records have nominal frame-pointer extents in existing layouts. | All 92 XY pointers are NULL. The two XY reads have known semantics but no established original nonzero producer. Retain the optional contract; do not infer unused storage or repeat the exhausted tail/proximity probes. |
| Tile expansion `$A1BE/$A1C8/$A1D4/$A1E0/$A1EC/$A1F8/$A204/$A210/$A21C` | 9 | All 1,290 map IDs fit 468 records; all 4,212 pixel offsets are aligned/bounded. Existing nine row/column roles and signed/unsigned address arithmetic are explicit. | Replacement IDs, viewport bounds, allocation and DMA remain separate. No missing original map/definition contract was found. |

The old animation inventory counted 89 initialized nodes. The current declared
record count is 92 because the retained menial chained/return nodes and gardener
node were restored later. Their already accepted owners provide 32/32/24 bytes
of held-plus-active pointer storage respectively. This reconciles a stale
inventory; it does not add three newly classified records or establish their
activation. Declared records and reachable initialized roots remain distinct.

Read-only consistency checks pass for the exact 27-ID partition, 130 copy pairs,
original sort flags at the canonical state offset +25, twelve preset/list links,
29 configuration indices, six envelope references and 92 nominal frame-pointer
bounds/NULL XY fields. Linked CPU/source tests are existing evidence, not rerun
for documentation. Source SHA remains
`15f28b305710b0c54affbd4b3eb6fa54744f67360b572812255e332959db7ee8`;
the source-bound C/vasm receipt from `59e77f9c` remains applicable. No target
facts, histories, labels, fonts, bank 45, EQU/RS policy or paused B07 files change.

All seven groups already have accurate reader interpretations in source and
canonical facts. No additional substantive source contract is supported by this
pass. The precise missing original-use evidence is an optional XY-sequence
producer; reopen it only on a concrete nonzero write/reference. Other unchecked
or replacement-domain caveats remain explicit without being turned into a quota
of mandatory hostile-input proofs. Native statuses, global classification,
purpose credit and overall semantic completion are unchanged. No necessary
source build arose, so global accounting was not regenerated for counters.

## Subsystem source-contract review: original layout

This is the current obligation-4 review, using existing canonical facts and
accepted batch evidence. It supersedes the **next dependency** column of the
2026-10-14 checklist, without rewriting that historical record. The unit here
is a connected source-contract group, not every possible function, caller,
mutation or runtime interleaving. Complete function/resource denominators remain
unknown; seven reviewed groups do not establish a semantic completion percentage.

| Subsystem and concrete source anchors | Reviewed original-layout contract and evidence | Explicit boundary; current disposition |
| --- | --- | --- |
| Startup, IRQ, title: `$00..$52`, entry `$46A`, IRQ `$8E4`/call `$932`, title `$F88` | Fixed overlap-safe prefix copy, supervisor/workspace/stack setup, IRQ priority/save frame, title/star producer and three continuations, reveal/audio phases, warm restart and initial gameplay consumers. [Restart evidence](../validation/pandora-restart-random.json), [indirect review](../validation/pandora-indirect-closeout.json); see the title-to-gameplay and starfield sections above. | Whole-stack allocation is not known. BLIT callback has startup zero/no known nonzero producer, and raw-request dispatch has no NULL guard. Star record byte9 remains unknown; its 1,000-byte runtime view is already represented. These are explicit limits, not a demand for arbitrary-callback safety or another star trace. |
| World scripts, objects and animation: handlers/interpreter `$1114..$1432`, table `$1432..$14B6`, reader `$951A`, indexed reads `$95C6/$95D4/$95DA` | All 33 handler roles, 780 NPC commands plus the three-command player loop, repeat/copy/node/sequence contracts, initial interaction/completion signatures, attachment and held/active frame layouts. [Operand evidence](../validation/pandora-behavior-operand-types.json), [indexed review](../validation/pandora-indexed-consumers.json), [fixed-pose/indirect contracts](../validation/pandora-indirect-closeout.json). | Optional XY has no initialized nonzero producer in 92 declared nodes. Retained-node activation, node+11 and wider visual meanings of conservative flag names remain unproved. Mutable targets/chains and out-of-range opcode behavior are explicitly unchecked, not new mandatory hostile-input work. |
| Input, movement and camera: movement `$95E2`, animation `$951A`, tile-cell service and two existing camera profiles | Axis-only request scaling, collision probes/commit, ID-failure continuation, idle/held modes, profile/wrap/countdown arithmetic and main/modal input/exit differences. See camera/profile, player-movement, missing-ID and title/restart sections and their linked original-code tests. | The old failed-ID continuation item is closed under its stated inputs. Unchecked profiles/coordinates and the unnamed wider meaning of status bit6 remain qualified. No full gameplay-admission proof is needed to retain the correctly described arithmetic. |
| Graphics, tiles, geometry and shared buffers: `$6A1E/$6C60/$6F6E`, tile builder `$9EBA`, definition reads `$A1BE..$A21C`, palette/helper sites `$71E0/$71EE/$7220/$7230` | Cell/plane/frame formats, original tile indices/offsets, clip/packet/edge scratch contracts, shared hit/palette alias, reset/restart waits and bounded original DMA observations. [Terrain](../validation/pandora-terrain-reference-encodings.json), [scene groups](../validation/pandora-remaining-scene-layouts.json), [shared-tail contract](../validation/pandora-shared-tail-contract.json). | Nominal source formats are established for all bitmap chunks; that is not an all-pixels or allocation claim. Palette stack-splicing targets leave the verified copied prefix; external continuations remain unknown. Original seed/suffix/tail purposes are separate exceptions below. DMA timing, exclusive lifetimes and alternate placement are not obligations to rewrite unchanged source. |
| Text, overlays, inventory and trade: selection `$2A32`, trade `$7BBA`, clear/queue `$6668/$6676`, indexed line `$6640`, storage `$A862..$A8E2` | Name/ID/value roles, cursor selection, offer/reset/pocket paths, six-line style dispatch, registry persistence/readiness, snapshot packets and the 64-byte registry plus 64-byte clear tail. [Indexed review](../validation/pandora-indexed-consumers.json); see inventory, shared-name and overlay-text sections. | The old 128-versus-64-byte clear discrepancy is documented, not pending structure expansion. Ten initial update callbacks are NULL; no nonzero producer is established. Fonts retain their reviewed conditional formats; arbitrary text/row/registry overflow and all aliases stay unchecked. No font or formatting work is selected. |
| NPC, combat, mission, terminals and outcomes: callbacks `$7A00/$83FE/$93F4`, ranged service `$9250`, terminal `$8FF2` | Initial object callbacks and carry/A5 consumers, proximity/ID/receptacle/trade effects, ranged hit/defeat, terminal versus self-destruct modes, BCD deadline and exit counters, ranking and restart consumers. [Actor identities](../validation/pandora-actor-identities.json), [console](../validation/pandora-self-destruct-console.json), [outcome/ranks](../validation/pandora-outcome-ranks.json), [indirect review](../validation/pandora-indirect-closeout.json). | Valid finite object/state graphs and explicit caller contexts are contract inputs. Repeated/wrapped counters, NULLs, unchecked card/name/graph cases and caller-dependent A4 behavior are preserved. Arbitrary replacement callbacks, all possible mission routes or proof of game-design intent are not missing original source annotations. |
| Audio and samples: initializer `$4D7DE`, dispatch `$4DC2A`, secondary start `$4E3EC`, samples from `$4EAD8` | Three presets/twelve lists, 29 programs and their parameter grammar, pitch/volume arithmetic, secondary configuration/envelopes, eleven sample extents and waveform mutation. [Audio state/programs](../validation/pandora-audio-state-and-programs.json), [control corpus](../validation/pandora-audio-control-symbols.json), [indexed review](../validation/pandora-indexed-consumers.json). | Runtime selectors are wider than stored tables. Global byte+13, the saved phase-increment copy's reader, skip-gate enabling writer and shift-state intent remain explicit unknowns. CPU packet semantics do not claim audibility, Paula timing, replacement-program safety or exclusive sample lifetimes. |

### Remaining original-layout acceptance questions, in priority order

1. **Reconcile and adjudicate representation exceptions (obligations 1/2).**
   The old unknown partition still needs reconciliation with the already typed
   weapon-table tails (`$8671..$8677`, `$8678..$867E`) and restored frame
   (`$4C376..$4C388`). The three dominant raw spans (`$52..$456`,
   `$B4A8..$C3A8`, `$39DC8..$3A338`) retain their specific stack/seed/suffix
   ambiguities. The opaque uncopied asset `$55370..$5C000` is bounded and
   preserved, but its original purpose is not thereby explained; it is not part
   of the old 6,446-byte unknown-classification count. The ten-byte candidate
   `$1094..$109E`, retained bytes `$6A16..$6A1E`, and residual small raw intervals
   must not acquire code/data/padding intent from pattern alone. **Acceptance:**
   justified interpretations or an explicit reviewed-unknown disposition for
   every residual interval, with accurate accounting and no double credit.
   **Next:** use the existing interval/fact reconciliation at final review; reuse
   a necessary native build for fresh accounting. No repeat scratch/bank-30
   probe or extra generation for counters is selected.
2. **Retain precise producer/continuation exceptions; obtain new evidence only
   for stronger claims.** At `$932`/`$6694`, nonzero Blitter/UI producers are
   unestablished; at `$95D4/$95DA`, optional XY use lacks an original producer.
   The four `$71E0/$71EE/$7220/$7230` stack-splicing calls have known local stack
   arithmetic but unexecuted external targets. Filename/arguments do not prove
   a loader or allocation. **Acceptance:** a concrete original writer/caller/
   continuation supports a stronger interpretation, or the final original-layout
   review explicitly retains these bounded unknowns. **Next:** reopen only on
   that new positive evidence. Existing consumer contracts already state the
   limits; no new capture, generic capability or repeated negative probe follows.
3. **Complete the final source review and label the result accurately
   (obligation 5).** **Acceptance:** all seven groups above have their concrete
   evidence and residual exceptions indexed, source names/types/SDK forms and
   canonical histories are preserved, and the original exact receipt is current.
   An accepted exception list permits the label **original-layout reviewed
   closeout with explicit unknowns**; it does not mean full semantic restoration,
   alternate-layout safety or a native C port. **Next:** adjudicate the residual
   exceptions and perform the final source-quality audit; reuse the existing
   exact receipt if source/metadata remain unchanged. Do not turn generic labels,
   purpose-byte gaps or arbitrary-input safety into another batch quota.

Existing accepted layout/reader facts deliberately preserve the unknown star
byte, animation flag intent/node byte and audio meanings above. Those reviews
accept bounded representations with explicit limits, not newly recovered meanings
or a blanket acceptance of whole-program completion. The `$36C..$604` app-relative gap and whole stack extent also remain
unclassified storage questions, separate from payload-byte accounting. Complete
asynchronous ownership, all possible mutations and changed-layout placement
belong to stronger claims than this original-source review.

No additional evidence-backed correction to a routine, field layout or source
contract was identified in this consolidation. No source edit is justified by the reviewed
evidence, so no target action, test suite, capture or generation was performed.
Current source remains the exact source of `59e77f9c`; `ca948c92` only reconciles
its indexed consumers. This review narrows the remaining questions rather than
claiming another subsystem was semantically completed.

## Final original-layout reviewed closeout with explicit unknowns

[Final evidence and identities](../validation/pandora-original-layout-closeout.json)
bind this disposition to the unchanged source of `59e77f9c`. Every range below
is section-0 source coordinates with an exclusive end. Review disposition is
not native classification promotion and does not invent a meaning from an
opcode pattern, zero bytes or a negative access window.

| Old unknown interval | Bytes | Final review disposition |
| --- | ---: | --- |
| `$52..$456` | 1,028 | Retain raw; known stack top does not establish complete extent/purpose. |
| `$1094..$109E` | 10 | Retain unresolved terminal-decode candidate; no accepted entry. |
| `$1113..$1114` | 1 | Retain single raw zero byte; no terminator/alignment/padding inference. |
| `$14B6..$14B8` | 2 | Retain raw guarded fallback; execution semantics unproved. |
| `$2B7D..$2B7E` | 1 | Retain single raw zero byte; no terminator/alignment/padding inference. |
| `$2EE5..$2EE6` | 1 | Retain single raw zero byte; no terminator/alignment/padding inference. |
| `$6A16..$6A1E` | 8 | Retain raw beside known masked-blit routine; no entry/layout inference. |
| `$718F..$7190` | 1 | Retain single raw zero byte; no terminator/alignment/padding inference. |
| `$8179..$817A` | 1 | Retain single raw zero byte; no terminator/alignment/padding inference. |
| `$864B..$864C` | 1 | Retain single raw zero byte; no terminator/alignment/padding inference. |
| `$8671..$8677` | 6 | Existing seven-byte weapon-table owner/seed; native counting remains stale. |
| `$8678..$867E` | 6 | Existing seven-byte weapon-table owner/seed; native counting remains stale. |
| `$8D53..$8D54` | 1 | Retain single raw zero byte; no terminator/alignment/padding inference. |
| `$8DA5..$8DA6` | 1 | Retain single raw zero byte; no terminator/alignment/padding inference. |
| `$8DDF..$8DE0` | 1 | Retain single raw zero byte; no terminator/alignment/padding inference. |
| `$8E7D..$8E7E` | 1 | Retain single raw zero byte; no terminator/alignment/padding inference. |
| `$8F0B..$8F0C` | 1 | Retain single raw zero byte; no terminator/alignment/padding inference. |
| `$8F25..$8F26` | 1 | Retain single raw zero byte; no terminator/alignment/padding inference. |
| `$8FF1..$8FF2` | 1 | Retain single raw zero byte; no terminator/alignment/padding inference. |
| `$9178..$917A` | 2 | Retain the two nonzero bytes; role unknown. |
| `$9485..$9486` | 1 | Retain single raw zero byte; no terminator/alignment/padding inference. |
| `$A25C..$A25D` | 1 | Retain single raw zero byte; no terminator/alignment/padding inference. |
| `$A7D8..$A804` | 44 | Retain raw inputs; loader/record interpretation unproved. |
| `$B120..$B130` | 16 | Retain zero tail; no allocation/padding/unused claim. |
| `$B250..$B260` | 16 | Retain zero tail; no allocation/padding/unused claim. |
| `$B4A8..$C3A8` | 3,840 | Retain original seed; later scratch accesses do not classify initial bytes. |
| `$39DC8..$3A338` | 1,392 | Retain zero suffix; no reservation/padding/non-use claim. |
| `$4C376..$4C388` | 18 | Existing 18-byte held-frame owner/type, restored after the player boundary correction. |
| `$4E127..$4E128` | 1 | Retain single raw zero byte; no terminator/alignment/padding inference. |
| `$4E364..$4E378` | 20 | Retain raw; no established program-entry/consumer contract. |
| `$4EAD6..$4EAD8` | 2 | Retain raw before sample bank; role unknown. |
| `$552CA..$552DE` | 20 | Retain raw; opcode/container resemblance is insufficient. |

All 32 intervals / 6,446 old-cohort bytes are covered exactly once. Three
intervals / 30 bytes have existing bounded facts; the remaining 29 intervals /
6,416 bytes are retained uninterpreted. No bytes were newly classified by this
review. In particular, subtracting these facts from an old total does not yield
a current native classification number.

The opaque asset `$55370..$5C000` separately preserves **27,792 original bytes**
through `preserved_uncopied_payload_tail`. Its original purpose and pre-overwrite
consumers remain unknown; byte preservation and later zeroing do not establish
unused data. Workspace questions are separate: the named app-relative gap
`$36C..$604` is 664 bytes, while the older **750-byte aggregate workspace-gap
metric** includes other gaps and is not refreshed here. The supervisor stack
top is known, but a whole allocation/all-path stack bound is not. None of these
workspace numbers is added to payload unknowns.

### Final quality and freshness audit

- The unchanged source, current effective metadata and complete source package
  match the existing C/vasm **376,832-byte full-file exact receipt**
  `d4fd9cb2cc9d6c1843f8e4f93207fb5599a62a0b29f1d2ac45cb3c50bdf6c49a`.
  The resident service confirms that receipt's subject is still current.
- All **126 assets, 16 SDK includes and the source file** match their manifest
  sizes/hashes. All noncomment source characters, **3,772 labels in order** and
  **2,824 EQU/RS declarations** remain unchanged since reviewed `e19817e4`.
  Twelve representative named display/audio SDK operand checks pass. The later
  three semantic comment edits are the already reviewed `59e77f9c` changes.
- Original bytes and target files are unchanged; both legacy history prefixes
  remain intact, including the recorded historical sequence gap. All nine
  paused B07 files retain their saved identities. No target fact/history write,
  new test, capture or generation occurred in this final review.
- **Stale:** the full native code/data/unknown partition (last unknown total
  **6,446**), native field-resolution/candidate counts and global workspace
  accounting. That baseline binds source
  `85bfb2faaec8a717af0e240b9bbadf962269253d0cc1f8828fa73694bb09d0db`,
  preceding the held-frame correction. The current native artifact is readable,
  but supported HTTP queries/navigation do not expose the complete ownership
  and source-plan DTOs needed by `build_accounting`; the offline accounting
  command constructs another whole artifact. No extra generation or new API
  was introduced just to replace the stale metric. This is an interface/freshness
  limitation, not a denied action or a pending build.
- **Current without native regeneration:** the canonical purpose union remains
  **283,380 source bytes across 216 active assessments** (all coordinate spaces
  counted for the assessment total). This is not semantic completeness. Current
  metadata retains **558 owners, 147 schemas and 95 function summaries**.

### Questions retained, and the evidence that would reopen them

1. **Original raw/opaque purposes:** a positive original producer/consumer,
   pre-overwrite use, format boundary or allocation/reservation record is needed
   to interpret the three dominant spans or opaque tail. Smaller intervals need
   an executable entry/xref or a complete data-format contract. Zero bytes,
   resemblance and absence of observed access are insufficient.
2. **Original nonzero activation:** an identity-bound writer/reference with
   owner/caller context is needed for Blitter/UI callbacks (`$932/$6694`) or
   optional XY (`$95D4/$95DA`). Their known readers and NULL initial values stay
   accurately qualified; unused/unreachable is not inferred.
3. **External continuation:** an original loader/indirect caller or code lineage
   beyond the four `$71E0/$71EE/$7220/$7230` stack-spliced transfers is needed to
   explain external execution/return. Known local arithmetic is not proof of an
   I/O loader, allocation, crash or unreachability. No repeated negative route
   or speculative new entry is selected.
4. **Unknown field intent:** positive original readers/writers or independent
   format evidence would be needed for star byte9, animation node+11/physical
   flag intent, and the audio global byte13/saved-increment reader/skip writer/
   shift-state intent. Existing conservative representations stand.

These are explicit exceptions, not newly manufactured tasks. The seven subsystem
contracts and the eight indirect/27 indexed cohorts retain their reviewed
conditional meanings. This closes the requested **original-layout reviewed
closeout with explicit unknowns** and stops this pass. It does not certify full
semantic restoration, every historical milestone/B01–B10 item, all possible
mutations or asynchronous DMA/Paula behavior, disk/loader parity, alternate
layout or native C portability. At that review PR #5 was unmerged; the later
master consolidation is recorded above. Fonts, bank45 and EQU/RS policy remain
unchanged.
