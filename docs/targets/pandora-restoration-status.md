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

Current checklist (2026-10-12): “documented” means the selected facts and
consumer contracts below are reviewed; “partial” retains a known semantic or
lifecycle limit. “Unanalysed” identifies the next evidence dependency, rather
than a new coverage metric. No row claims complete subsystem recovery.

| Subsystem | Documented | Partial | Unanalysed / next dependency |
| --- | --- | --- | --- |
| Bootstrap / initialization | Fixed-base overlap-safe copy, continuation, supervisor/stack/workspace and initial buffers | Dependent resource setup and storage lifetimes | Copy-helper return lineage, temporal overwrites and alternate placement |
| IRQ / frame / gameplay | Dispatch priority, display pointer programming, completion latch; front/back swap with display alias | Callback effects, input phases and buffer ownership | Complete allocation/lifetime and caller coverage |
| Title / starfield | Selected star routines, opcode handlers and dispatch identities | State ownership and continuation contracts | Remaining table bounds and indirect paths |
| World commands / objects | All 33 handler identities and operand contracts; selected object prefixes | Proximity, links and command callee effects | Script instances, arbitrary pointer targets and object lifetime |
| Scene / tiles / geometry | Reviewed scene selectors, tile records and selected pixel/mask banks | Geometry consumers and allocation/chain limits | Disputed banks, complete write ownership and DMA constraints |
| Entity animation / updates | Byte phase/count/mode fields, packed clock, saved XY/geometry, rectangle union and current drawing | Eligibility, variant geometry and complete caller/lifetime coverage | Conditional extended nodes, sequence bounds and attachment cycles |
| Inventory / trading / NPC | Four-entry records, 81 table identities, selected offer/reset/panel/name/pocket paths | Cursor domains, unmatched-search writes and selected security callbacks | Complete callers, templates' write ownership and lifecycle |
| Text / fonts / overlays | Reviewed compact and large fonts, masks and rendering contracts | Overlay callback ownership and 128-byte clear versus 64-byte layout | Queue-processing reachability and adjacent storage ownership |
| Audio / samples | Four-channel commands, lists, programs, pitch/volume, secondary streams; eleven sample extents and mutable writers | Phase, arbitrary selector and storage lifetime limits | Remaining caller/state combinations and write ownership |
| Unclaimed resources / uncopied tail | Original bytes preserved by exact reassembly | Known consumers establish only selected physical prefixes | Purpose and boundaries of remaining spans; no opaque-export safety claim |
| Alternate execution layout | Address-class constraints identified | Current source identities are conditional on native views | Changed code/data/DMA placement and temporal/late lineage remain unimplemented or unproven |

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
The remaining script-handler presentation is the next coherent quality pass.
