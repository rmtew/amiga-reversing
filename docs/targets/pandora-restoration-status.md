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
The other 42 reader proposals remain unapplied. P27/P28 mostly restate already
documented behavior and are not counted as new discoveries. The reader's report
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
