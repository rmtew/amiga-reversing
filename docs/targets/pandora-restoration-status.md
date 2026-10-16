# Pandora restoration inventory and status

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

Latest source checkpoint (2026-10-14): scratch capacity and resolved caller family.
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

Current checklist (2026-10-14): “documented” means the selected facts and
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
| Player movement / collision / camera | Axis scaling, tile probes, request versus drift/commit, direction/idle modes, bitset and camera handoff; movement script, directional prefixes, copied-pointer links and corrected idle field; two typed camera countdown/margin profiles, sequential field reads and movement scroll triggers | Initialized-map restriction prefix, unchecked profile index and coordinates, and pointer/lifetime limits; ambiguous or inactive runtime mappings refused | Later exit-delay reset/writer coverage and reachable inherited state; shared positive-X node word and held-frame/player-layout boundary |
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
