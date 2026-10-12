# Pandora restoration inventory and status

Baseline snapshot: 2026-10-12, merged source `22e55bb5`, restoration revision
`2f142cd09c5eae6d1edd001af3acfb2909098713d6a8f513eadda5c7279ba42e`.
All offsets here are section 0 source offsets, with exclusive range ends, unless
explicitly called runtime addresses. This report indexes native facts and
canonical history; it does not replace them. See the [full plan](pandora-restoration-plan.md).

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

“Unknown” below is an analysis status, not failure of exact source reproduction.
No subsystem is declared fully restored by the inventory.

| Subsystem / source region | Status | Evidence and next question |
| --- | --- | --- |
| Bootstrap `0x00..0x52` | Reviewed interpretation; exact rebuild passed | Four labels and two comments describe fixed-base overlap-safe movement. Full-file C and vasm match; this does not establish alternate-base execution. |
| Runtime initialization `0x46A..0x5D6` | Setup interpretation reviewed; deeper callees partial | Fixed workspace/supervisor entry, stack reset, initial buffer banks and IRQ setup are accepted. Continue dependent world/resource initialization. |
| Interrupt hub `0x8E4`, frame service `0x94E` | Dispatch and frame-latch semantics reviewed | Sampled source priority, bounded saves, display pointer updates and completion latch are accepted. Helper/callback effects and allocation bounds remain partial. |
| Title/starfield `0xBA8..0xF54` | Partial | Existing named star routines and dispatch facts; audit table bounds, continuations and state ownership. |
| World command interpreter `0x13F4`, table `0x1432..0x14B6` | Handler identity and operand behavior reviewed | All 33 displaced labels corrected through real catalog/runtime identities; 34 comments describe handlers and dispatch. Delay/equality/flag predicates corrected. Script instances, pointer targets and callee effects remain to recover. |
| World/object/map logic and records | Partial | Existing object structures and link tables; follow interpreter consumers, proximity and object lifetimes. |
| Inventory `0x26EC..0x2B7E` | Partial | Names/fields exist; recover side effects and transitions after call identity reconciliation. |
| Text/overlay `0x6332..0x66A0` | Partial | Reconcile 128-byte clear versus 64-byte layout and indirect callback ownership. |
| Tile/geometry `0x6728..0x7216` | Partial | Identify buffer ownership, geometry extents and blitter/DMA address constraints. |
| Frame/gameplay `0x9C00` | Partial | Resolve absolute callees, frame wait/input helpers and front/back/display pointer lifetimes. |
| Security/trade/NPC callbacks | Partial | Existing names require contracts and cross-checks against world state/message consumers. |
| Audio `0x4D7DE..0x4E9D6` | Partial | Four-channel structures exist; recover command/state contracts and distinguish A3 module base/A6 hardware base. |
| Samples `0x4EAD8` onward | Partial / boundaries pending | Existing eleven packed-sample lengths need owner/consumer and exact extent reconciliation. |
| Large unclaimed intervals and uncopied tail | Unknown | Trace consumers and address-bearing content before claiming resource boundaries or opaque export safety. |
| Alternate execution layout | Not implemented/proven | Classify every address family, then test actual changed code/data/DMA placements and reject illegal layouts. |

The parallel asset-export task owns INCBIN packaging and assembler support.
This ledger can supply reviewed boundaries; it will not create a competing
export path. Original disk/loader parity remains explicitly out of scope.

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
