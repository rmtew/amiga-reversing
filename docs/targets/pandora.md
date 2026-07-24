# Pandora design and implementation map

This is a human-facing map of corroborated Pandora discoveries.  It is a
secondary index, not an authority: C analysis facts and the target Manual
Action Log remain the source of truth, and the generated target source must
never be edited to match this document.

## Evidence convention

- **Confirmed**: supported by generated source, xrefs, and a durable target
  fact/action.
- **Working interpretation**: useful name or relationship supported by current
  code, but not yet a complete record-layout recovery.
- **Open**: a concrete next question, not a claim about the binary.

All addresses below are Pandora runtime absolute addresses.  The target is
rendered from `targets/amiga_disk_pandora-1988-firebird/targets/` and each
output-affecting slice must retain full-file exact reassembly.

## Audio subsystem

### Confirmed control flow

| Address | Symbol | Role |
| --- | --- | --- |
| `$0005D7DE` | `initialize_audio_player` | Initializes the player-owned audio state, resets hardware channels, and builds four channel records from a selected sequence. |
| `$0005D872` | `reset_audio_channels` | Clears channel activity/state and disables Amiga audio DMA/volumes. |
| `$0005D8CC` | `enable_active_audio_channel_dma` | If the player enable latch is set, restores ADKCON, enables the four Paula DMA bits, and marks the player active. |
| `$0005D8FE` | `update_audio_channels` | Per-update service routine for active audio channels. |
| `$0005E4AE` | `dispatch_audio_channel_updates` | Dispatches the four playback-state/DMA-configuration pairs to the shared channel service helper. |
| `$0005E512` | `service_audio_channel_playback` | Services one active channel: countdowns, period/sample offset updates, envelope volume, and DMA commit. |
| `$0005E378` | `initialize_audio_sample_metadata` | Lazily parses packed sample metadata into a table used by playback. |
| `$0005E3EC` | `start_audio_sequence` | Selects a sequence, resets channel playback state, loads per-channel configuration, and enables audio DMA. |
| `$000652FE` | `update_player_proximity_audio` | Adjusts audio behavior from player-world proximity. |

`start_audio_sequence` calls `initialize_audio_sample_metadata` before it
copies a selected configuration into a channel playback state and programs
the four Paula audio channels.  The caller at `$0005D330` preserves the
general registers around this call, which supports treating it as a subsystem
entry rather than an inline helper.

## Starfield initialization

`finish_starfield_initialization` at `$00010D68` is the indirect continuation
selected by the preceding star/palette setup routine through `a3`. It advances
the generated-star buffer, clears a 24-word state region, sets the star/UI
latch at `app_027B` bit 2, initializes the `$10` countdown at `app_0285`, and
returns. Its former raw bytes are therefore executable starfield setup code.

The shared pseudo-random state is initialized by
`seed_pseudorandom_state_from_beam_position`, which selects one of four
`pseudorandom_seed_values` using the custom chip's beam-position register.
`advance_pseudorandom_state` then runs a 32-step bitwise state transition.
The star motion/initialization routines and gameplay update path both consume
the resulting values.

`reset_star_motion` supplies a star record with randomized position and
velocity plus its default lifetime. During initial starfield construction,
`initialize_star_motion_with_random_lifetime` invokes that reset and chooses a
fresh lifetime in the accepted randomized range; expired stars return through
the reset path from `update_star_motion`.

`initialize_starfield` at `$00010D20` builds 100 star records and returns at
its terminal `RTS`; `update_starfield` at `$00010D8A` is the separate per-frame
routine, likewise bounded by an `RTS`. `clear_star_pixel` and
`render_star_pixel_by_lifetime` share the coordinate-to-bitplane calculation,
then select one of eight continuations from the 32-byte
`star_plane_bit_operation_dispatch` at `$00020CA0`. Each entry is a verified
absolute code pointer to a three-plane `bclr`/`bset` combination followed by
`jmp (a3)`: the caller supplies that continuation for either star-record setup
or the next iteration of the frame update. The table is therefore an eight-long
pointer dispatch, not raw data adjacent to code.

## Bitmap pixel-bit helpers

The adjacent four routines at `$00015FFE..$00016055` implement a consistent
one-pixel operation on a byte-addressed bitmap. They preserve `d0-d1`, derive
the containing byte as `x >> 3`, invert the low bit index with `x xor 7`, and
operate through `a0` using `d1` as the index. `test_bitmap_pixel_bit`,
`toggle_bitmap_pixel_bit`, `clear_bitmap_pixel_bit`, and
`set_bitmap_pixel_bit` use the corresponding `BTST`, `BCHG`, `BCLR`, and
`BSET` instructions. Their terminal `$4E75` words establish four separate
code boundaries immediately before the text-rendering routine at `$00016056`.

## RGB12 palette helpers

The helper group at `$0001255E..$00012654` manipulates Amiga RGB12 colors as
three independently stored component words. `unpack_rgb12_palette_components`
splits each packed palette word into those component slots;
`add_rgb12_palette_components` and `subtract_rgb12_palette_components` apply
the corresponding three packed-nibble deltas and repack the result; and
`clear_rgb12_palette_components` clears the component buffer. These are
separate code routines, not palette data, each bounded by an RTS.

The immediately following `set_copper_interrupt_callback_atomic` at
`$00012656` preserves the status register, raises the interrupt mask, stores
`a0` in `app_copper_interrupt_callback`, and restores the status register.
It is therefore the atomic installer for the copper interrupt callback rather
than an inline palette-data tail.

## Audio shared data

| Address | Symbol | Current interpretation |
| --- | --- | --- |
| `$0005DD00` | `audio_master_volume` | Default master-volume word, initialized to `$0040`; later used by proximity audio logic. |
| `$0005E5F6` | `audio_channel_playback_states` | Four instances of the recovered 0x26-byte `audio_channel_playback_state` record.  The prior apparent second-record extension was listing fragmentation. |
| `$0005E690` | `audio_channel_dma_configurations` | Four instances of the recovered 0x0c-byte `audio_channel_dma_configuration` record. |
| `$0005DDD4` | `audio_pitch_scalars` | Bounded 72-word pitch-scalar lookup table used to scale sample periods; it ends immediately before the pitch-command offset table. |
| `$0005E6C0` | `audio_sequence_channel_configurations` | 29 instances of the recovered 0x16-byte sequence-channel configuration record. |
| `$0005E93E` | `audio_sample_address_base` | Long address base used with a selected sample-address offset during channel service. |
| `$0005E942` | `audio_sequence_envelopes.envelope_offsets` | Six signed word offsets from `initialize_audio_player`, selecting six high-bit-terminated envelope byte streams. |
| `$0005DEB0` | `audio_sample_metadata` | Eleven instances of the recovered 0x0c-byte runtime sample-metadata record. |
| `$0005EAD8` | `packed_audio_sample_stream` | Eleven packed sample records, each with a six-byte `(byte_size, playback_rate)` header followed by an exact-length payload. |

The recovered DMA configuration layout is:

| Offset | Field | Width | Evidence |
| --- | --- | --- | --- |
| `+0` | `sample_ptr` | long | Copied to the selected Paula audio pointer register. |
| `+4` | `sample_length` | word | Copied to the selected Paula length register. |
| `+6` | `sample_period` | word | Copied to the selected Paula period register. |
| `+8` | `sample_volume` | word | Copied to the selected Paula volume register. |
| `+10` | `enabled` | byte | Tested before a configuration is committed to DMA. |
| `+11` | `start_pending` | byte | Set by sequence start and cleared by the channel service helper. |

This is represented in the target as one 48-byte data-block layout binding a
four-element array of `audio_channel_dma_configuration`, rather than four
independent offset annotations.

The playback-state records are likewise represented as one 152-byte layout
binding a four-element `audio_channel_playback_state` array. Confirmed fields
include period delta/reset/current values, the selected half-word of the
period and sample-address delta values, countdowns, active state, sequence
index/pointer, and the sequence envelope countdown. Byte `+21` remains raw:
it is read by the service routine but its role is not yet established.

The sequence configuration table is a 638-byte layout containing 29 records.
`start_audio_sequence` uses the sign-extended low byte of its selector as the
record index, then copies one 22-byte configuration into the corresponding
playback state. Its fields therefore share the same period, sample-offset,
timer, sequence and update-control semantics as playback offsets `+0..+21`.
The final `update_disabled` byte is tested by the channel service routine to
skip per-tick updates for that configuration.

`initialize_audio_sample_metadata` expands the packed stream into the metadata
array. Each destination entry holds a sample payload pointer at `+0`, its
Paula word length at `+8`, and the period derived from playback rate at `+10`;
the uninitialised four-byte span at `+4` remains explicit raw data. The 11
verified packed payload sizes are `$13EE`, `$0C4C`, `$121A`, `$157C`, `$14B4`,
`$07D0`, `$0040`, `$0040`, `$0010`, `$0008`, and `$0004` bytes.

### Open audio work

- Render the verified packed-sample headers at `$0005EAD8` structurally, then
  classify the sequence bytes beginning at `$0005E6C0` with verified record
  boundaries.
- Name the update helper blocks within `update_audio_channels` only after the
  repeated record fields and timer/envelope behavior are proven.

## Work-buffer helper

`prepare_work_buffer_arguments` at `$00017190` is a compact RTS-bounded code
entry following two null-terminated resource-name strings. It returns three
fixed work-buffer pointers in `a0`, `a1`, and `a2`, together with a count of 15
in `d7`. No direct caller has yet been recovered, so the name records the
observed register contract rather than assigning those buffers to a subsystem.

## Gameplay update and self-destruct sequence

`run_gameplay_update_loop` at `$00019C00` is the frame-level gameplay path
following the self-destruct text resources. It snapshots active world-object
links, swaps the front/back/display bitplane pointers, waits for the display
phase, then services inventory, scrolling-message, and panel input before
continuing the frame state machine.

`swap_tilemap_context` at `$0001921A` exchanges the current tilemap width,
height, column, row, and base pointer with the saved context at `$00018A18`.
The gameplay loop uses it on both sides of its mode transitions, preserving
the map-view state while a panel or other alternate context is active.

`render_tilemap_view_to_back_buffer` at `$00016728` draws the current tilemap
view into the back bitplane with the custom-chip blitter. It begins at the
configured tile row/column, performs 20 tile blits per display row across eight
rows, and wraps tilemap addressing at the current map boundary.

`blit_tile_to_bitplane` at `$000167B2` is its fixed-size blitter helper. It
waits for the previous blit, then copies one word per row for 16 rows from A0 to
A1, with a two-byte destination modulo. This is the fundamental 16-pixel tile
transfer used by the view renderer.

The loop calls `process_self_destruct_card_input` at `$00019CBE` when the
self-destruct panel is active. That routine accepts the permitted selected item
ids, records up to three resolved item-name pointers, starts feedback audio,
and advances the card-sequence state. `render_self_destruct_card_sequence` at
`$00019DC2` clears the sequence display buffer and renders the appropriate
prompt, selected cards, invalid-sequence, or initiated self-destruct message.

## World-object subsystem

### Confirmed player entry

`player_world_object` at `$0005C322` is the first entry in
`world_object_ptr_table`.  Direct consumers establish that it supplies the
player's world position at offsets `+0x30` (`world_x`) and `+0x32`
(`world_y`).  It also carries an object-state byte at `+0x48`: bit 1 is set
when interaction logic enters its pending state and tested before inventory
panel updates and proximity-context handling.  Other observed fields include
the byte at `+0x3d`, the byte at `+0x46`, the word at `+0x3c`, the pointer at
`+0x4e`, and the two-byte context-prompt cooldown at `+0x52`; their roles need
further cross-object comparison before becoming shared record fields.

`update_active_world_object_tile_regions` at `$0001248A` iterates the active
world-object pointer table and invokes `update_world_object_tile_region` at
`$00016DFE` for each entry. The callee follows the linked geometry records,
computes extrema, clips the resulting region against the tilemap, and submits
the corresponding blitter update. This formerly raw RTS-bounded loop is
therefore an active world-object tile-region update pass.

The adjacent table passes establish the linked-object lifecycle around that
update. `process_active_world_object_chains` visits each active object and
delegates to `render_world_object_geometry_chain` at `$00016F5C`, which walks
the `+0x14` geometry links and renders each node through
`render_world_object_geometry_node` at `$00016F6E`. `snapshot_active_world_object_links`
copies each active object's current link field from `+4` to `+8`, then walks
the child chain and copies each child's field at `+0` to `+4`. The fields
remain structurally unnamed until the broader shared world-object layout is
recovered, but these update-pass roles are directly supported by the copies
and traversal.

The tile-region path also contains four compact helpers at
`$00016DCA..$00016DFC`. `calculate_tilemap_buffer_offset` derives the
word-aligned buffer offset from the coordinate and indexed row-offset table.
The other three are exact field-copy helpers: they copy the A5-relative
`+0x30` or `+0x36` value into the indirect record's `+4` slot, or copy `+0x30`
to `+0x36`. Their record fields remain intentionally descriptive rather than
speculative until the common layout is recovered.

The corresponding tilemap-render family is now named through the clipping
boundary: `get_tilemap_cell_pointer` converts pixel coordinates to the current
tilemap cell, `get_tilemap_view_bounds` prepares the scroll-relative view
limits, `clip_tile_region_to_view` derives the visible region and clip flags,
and `render_tilemap_view_to_back_buffer` submits the 20-by-8 tile view through
the blitter.

`tilemap_point_is_in_view` at `$00016828` is the companion fast predicate. It
compares a point supplied in D2/D3 with those scroll-relative bounds and returns
zero in D4 only for a point within the 320-by-128 view; it returns `-1` when the
point is outside.

`world_object_ptr_table` occupies `$0001300A` through `$00013099`: its 36
longwords are the player pointer, 34 static-object pointers, and the null
terminator.  The preceding word at `$00013008` is `$4e75` (`RTS`), which is a
hard code/data boundary.  `scan_world_objects_for_proximity` advances through
this exact range and branches to context handling at the terminator; subsequent
longwords belong to a different table.

`active_world_object_static_ptr_table` starts at the second pointer and has 34
entries before the same terminator.  It intentionally excludes the player and
is used by `update_active_world_object_positions`; the similarly named runtime
equate is a separate active-table pointer slot.

`active_world_object_ptr_table` is the separate 67-entry pointer array at
`$0001309A` through `$000131A5`, followed by its own null terminator at
`$000131A6`.  `initialize_world_state` installs this address and count `$43`;
the symbolic `EQU` is intentionally used because the renderer coalesces its
adjacent longword directives and cannot safely split them at that interior
address without a new directive-boundary fact.

`player_position_descriptor` at `$0005C71E` is the object referenced by the
player prefix at `+0x2c`.  Proximity scanning stores `world_x` and `world_y`
at its `+0x04` and `+0x06` words, while reset code restores its leading pointer.
All 35 non-null world-object entries use the same observed eight-byte prefix:
`position_state_ptr`, `world_x`, and `world_y`; the rest of each descriptor is
still raw pending record-specific evidence.

`update_active_world_object_positions` at `$00019250` runs in the main update
after nearby-object detection.  It derives the player-relative tile position,
then walks the active position-descriptor table while applying the current
object-position updates.

`initialize_world_state` at `$00019F26` is the corresponding producer.  It
initializes tilemap/player/UI state, installs the active-table pointer
and count, then iterates every `world_object_ptr_table` entry to reset per-object
state and resolve item names.

That initialization loop proves the shared prefix's current/initial pairs:
`selected_item_id`/`initial_selected_item_id`,
`world_object_flags`/`initial_world_object_flags`, and
`item_state`/`initial_item_state`.  It also resets `interaction_timer` and
uses `item_definition_id` to resolve each object's item-name pointer.

`adjust_active_world_object_item_state` at `$000186A6` applies a byte delta
from D0 to the `item_state` field of every eligible `world_object_ptr_table`
entry. Null entries and objects whose `world_object_flags` have bit 1 set are
skipped, establishing this as a shared state-update pass rather than an object
local helper.

The matching effect triggers are now explicit. `decrease_active_world_object_item_state`
at `$0005B0D6` queues the message "I am now stronger than you could possibly
imagine." and tail-calls that pass with D0 = `-15`. The two distinct, otherwise
identical `$0005B10A` and `$0005B112` entrypoints each tail-call it with D0 =
`+15`; they remain separately labelled because their dispatch contexts have not
yet been recovered.
The resulting long at prefix offset `+0x00` is represented as `item_name_ptr`.

The target now has a shared 0x54-byte `world_object_shared_prefix` type.  Its
field facts come from the common scan loop rather than the player instance:
`interaction_callback` (`+0x04`), `context_callback` (`+0x0c`),
`interaction_data_ptr` (`+0x10`), `position_descriptor_ptr` (`+0x2c`),
position, `proximity_distance` (`+0x42`), flags, and the cooldown.  The prefix
is bound at the player entry; unclassified spans stay raw.  A complete
`world_object_record` layout remains open rather than inferred from that
minimum common prefix.

The same prefix now records its inventory/trade state as resettable pointer
pairs: `inventory_slots_ptr`/`initial_inventory_slots_ptr` at
`+0x14`/`+0x1c`, and `trade_offer_table_ptr`/`initial_trade_offer_table_ptr` at
`+0x18`/`+0x20`.  Inventory UI and NPC trade code each consume four two-byte
entries from the current tables; `initialize_world_state` copies eight bytes
from each corresponding initial table to restore the current state.

`default_empty_item_slots` at `$0001B3A0` is the shared, eight-byte zero
initializer used by all four player inventory/trade pointers.  It is now an
explicit four-element word table rather than part of the preceding anonymous
12-byte zero fill.  The range is represented through the general target
data-block layout/element commands, which also support an exact source
subrange when a decoded listing row is broader than the recovered object.

### Confirmed item-name lookup

`resolve_item_name` at `$00012B7E` masks an item id to seven bits, doubles it,
then reads a signed/relative word from `item_name_offset_table` at `$0001A6DC`.
That bounded 114-word lookup table ends exactly at `$0001A7C0`; every entry is
an offset into the NUL-terminated `item_name_string_table` beginning at
`$0001A25C`.  Inventory refresh uses the same two-table calculation for each
carried and pocket item, while `initialize_world_state` uses it to populate
each world object's `item_name_ptr`.  Its durable layout is one `word`
`item_name_offset_lookup` range; an earlier duplicate-create/remove sequence
was reconciled so the review projection now reflects the one effective table
rather than retaining a stale overlap blocker.

### Confirmed interaction helpers

`restore_world_object_position_state` at `$0001867E` clears the active
position-state flags/timer and restores the preceding state link through the
object's position descriptor.  It is used when interaction and position update
paths return an object to its prior state.  `enqueue_status_message` at
`$000199DE` appends an `a0` string to the scrolling status-message queue,
initializing the queue/timing when necessary; trade, receptacle, and contextual
interaction paths all use this common entry.

### Confirmed object-interaction callback dispatch

`invoke_nearby_object_interaction` reads the shared-prefix long at `+0x04`,
calls it indirectly when non-null, and treats carry set on return as
"interaction handled". When the callback leaves carry clear, the caller uses
the prefix long at `+0x10` as an optional status-message string and passes it
to `enqueue_status_message`. This establishes `interaction_callback` as a
code-pointer field, rather than merely an opaque longword.

The world-object table references 13 distinct callback entrypoints. They are
seeded as code and labelled through the target command surface; this was needed
because an indirect pointer alone cannot safely create a control-flow entry in
the analyzer.

| Address | Callback | Referencing object/item |
| --- | --- | --- |
| `$0005D37E` | `interact_with_musician` | Musician (`$40`) |
| `$0005D3A2` | `interact_with_hooligan_or_robomechanic` | Hooligan (`$4E`) and Robomechanic (`$41`) |
| `$0005D3AE` | `interact_with_sec_officer` | Sec officer (`$43`) |
| `$0005D3BE` | `interact_with_chemist` | Chemist (`$45`) |
| `$0005D3FC` | `interact_with_bank_manager` | Bank manager (`$4F`) |
| `$0005D426` | `interact_with_priest` | Priest (`$49`) |
| `$0005D432` | `interact_with_technician` | Technician (`$4B`) |
| `$0005D44A` | `interact_with_wackobrain` | Wackobrain (`$62`) |
| `$0005D496` | `interact_with_menial_droid` | Menial droid (`$51`) |
| `$0005D4C4` | `interact_with_gardener` | Gardener (`$47`) |
| `$0005D520` | `interact_with_squash_player` | Squash player (`$4C`) |
| `$0005D538` | `interact_with_driffid` | Driffid (`$4A`) |
| `$0005D568` | `interact_with_diabetic` | Diabetic (`$46`) |

Several callbacks compare `player_world_object_selected_item_id` with a
specific item id, and the Priest callback branches to the shared
Hooligan/Robomechanic routine when its state guard is already set.  The
item-name lookup table proves the following item requirements: Musician—Bottle
of gin (`$27`); Sec officer—Laser rifle (`$12`); Chemist—Bible (`$2c`) or
Shakespeare (`$2b`); Bank manager—Bent coin (`$64`); Technician—Globe
(`$2e`); Squash player—Squash ball (`$2f`); Driffid—Insecticide (`$2a`), Light
box (`$2d`), or Megabio Feed (`$67`); and Diabetic—Hypodermic (`$29`) or
Insulin (`$28`).  These are rendered as `ITEM_ID_*` equates at each operand.
The general `representation.symbol` command was added for this work: it
durably binds a target equate name to one immediate operand, instead of relying
on a target-specific renderer change.  The repeated flag/timer updates remain
the next connected interaction-state recovery task.

The callback family also establishes two one-byte A6-relative state regions:
`app_world_interaction_flags` at `+0x033d` and
`app_world_interaction_audio_flags` at `+0x033e`.  The first combines a
proximity-audio active latch (bit 0, maintained by
`update_player_proximity_audio`) with independent callback state: Musician
completion (1), Technician completion (2), Squash-player completion (3),
Diabetic treatment (4), Wackobrain feedback pending (5), and Chemist Bible
completion (7).  The second contains audio-pending gates: the Menial droid and
Gardener callbacks set bits 1 and 2 before starting their feedback sequence,
then clear them only after channel 2's playback-tick counter reaches zero.
Both bytes are reset by `initialize_world_state`.  The audio byte's bit 0 is
also used by the broader audio-player update path, so it remains intentionally
unnamed until that subsystem is recovered.

`app_ui_flags` at `+0x022e` is the shared byte that gates the callback audio
paths as well as inventory and message UI. Inventory-panel code proves bit 2
(`UI_FLAG_INVENTORY_PANEL_ACTIVE`) means the panel is active (set on open and
cleared on close), and bit 4 (`UI_FLAG_NEARBY_OBJECT_INVENTORY`) marks the
nearby-object inventory variant. The remaining bits are retained as
unnamed UI state: bit 1 suppresses callback feedback after a reset/modal path,
bits 3 and 5 accompany inventory feedback/selection, bit 6 initializes the
status-message queue, and bit 7 gates a main-loop UI update.

### Recovered orphan interaction-audio code

Two code blocks immediately following `interact_with_gardener` were previously
rendered as raw bytes despite valid M68K instruction streams and terminal or
backward control flow. `update_gardener_feedback_audio` at `$0005D4E2` tests
channel 2's playback ticks, clears the Gardener pending latch when playback
ends, and returns to the Gardener interaction callback. The adjacent
`update_interaction_audio_sequence_214` at `$0005D4F2` has the same latch/
playback-completion shape for sequence `$214` and audio-flag bit 3. The latter
is named `INTERACTION_AUDIO_FLAG_SEQUENCE_214_PENDING`. No world-object-table
or direct-pointer reference identifies its owner, so the routine name records
behavior rather than guessing an NPC.

`is_player_within_world_object_interaction_range` at `$00012664` compares the
player and selected object's coordinates and returns the condition code used by
the Musician and Diabetic paths. Its current bounds are an absolute Y delta
below 16 and an absolute X delta below 24. `start_feedback_audio_sequence`
at `$0005D330` preserves the caller register set around `start_audio_sequence`
and updates the interaction-audio state; its callers include the object
callbacks and inventory-panel feedback.

The callback implementation pass records `world_object_shared_prefix` as the
A5 entry type at all 13 callback entries.  Their rendered accesses now use the
shared field names (for example, `context_prompt_cooldown(a5)`), rather than
anonymous numeric displacements.  This uncovered and fixed a general renderer
contract: custom-structure field symbols are emitted as source-header `EQU`
definitions, so typed operands remain independently assemblable.  The command
surface now has a durable `target.code.register_seed.add` action for this
entry-specific type fact; the renderer deliberately applies such seeds only
at the exact function entry, not to unrelated preceding code.

`process_world_object_callback_queue` at `$00016676` is the corresponding
runtime dispatcher. It walks the 16 pointer slots at `$0001A862`, skips null
entries and objects whose signed status word at `+0x06` is non-negative, then
calls a non-null function pointer at `+0x28` while preserving the loop
registers. The immediately preceding routine clears those same 16 slots, so
the storage is an explicit callback queue rather than an untyped object list.

### Blank sprite datum

`blank_sprite_data` at `$0005D5DE` is a 512-byte zero-filled sprite datum.
Both copper-list families load it into sprite pointers, and display setup also
uses it as the blitter source for clearing.  Its fixed size and all-zero
contents are therefore intentional asset data, not padding between the
world-interaction callbacks and the audio-player code that follows.

### Audio channel runtime records

`audio_channel_state_records` at `$0005DD14` is the zero-initialized runtime
array for the four Paula audio channels. `initialize_audio_player` initializes
four entries with a `$30`-byte stride, and `update_audio_channels` independently
derives the same stride from its channel index before reading each entry's
sample and playback state. It now renders as the shared
`audio_channel_runtime_state` layout. The updater establishes command/note
state (`+0..3`), a program pointer and configuration offset (`+4`, `+8`),
looped pitch-sequence pointers (`+0x0c`, `+0x10`), sample-start and metadata
state (`+0x16`, `+0x18`), reload/update counters (`+0x1c`, `+0x1e`), a pitch
delta accumulator, and volume-sequence and pitch-modulation state through
`+0x2e`. Only the intervening bytes whose role is not yet proved remain typed
gaps.

The layout revealed a renderer defect when a record begins with an unknown
gap: generated references were changed to a synthetic `*_gap_0` label. The
general projection now preserves the data-block's public name at its first
directive, whether that directive is a leading gap or a recovered field, with
regression coverage for both cases. Partially recovered structures therefore
do not erase their own semantic base identity.

`audio_player_initialization_presets` starts at `$0005DF34`. The initializer
uses its mode argument times `$0a` as an index, so its first 30 bytes are three
10-byte `audio_player_initialization_preset` records. Each has two as-yet
unnamed byte controls followed by four named channel-program offsets; the
initializer walks those words while constructing the four runtime channel
states. The subsequent packed audio stream is deliberately not included in
that table until its format is recovered.

The packed-stream command decoder has two bounded relative-offset tables. For
command bytes `$a0..$ac`, `audio_pitch_sequence_offset_table` at `$0005DE64`
contains 13 word offsets rebased through the audio-player base; its default
target is `default_audio_pitch_sequence_stream` at `$0005DE7E`. For `$b0..$bf`,
`audio_volume_sequence_offset_table` at `$0005E9B6` contains 16 similarly
rebased word offsets for volume sequences. The sequence-byte encodings remain
raw until the command language is fully recovered.

### Audio sequence command dispatch

Bytes below `$a0` enter an eleven-entry relative-offset table,
`audio_sequence_command_dispatch_offsets` at `$0005DCE8`, again rebased from
`initialize_audio_player`. Its destinations at `$0005DC2E..$0005DCDC` are now
recovered code rather than a raw-byte island. They advance the channel program,
set pitch-delta and pitch-modulation state, set per-channel note/configuration
values, trigger the default sample path, reset channels, or update player-wide
controls before returning to the shared packed-stream decoder. The `$4e75` RTS
at `$0005DCDE` is a decisive code boundary within the dispatch island; it is
not an inline-data marker.

The adjacent audio-control globals now have xref-backed names. The byte at
`audio_update_phase_increment` (`$0005DD02`) is copied into the player control
area on initialization and multiplied by 16 to advance the update phase in
`update_audio_channels`. `audio_global_note_offset` (`$0005DD08`) is added to
every decoded note before the per-channel note offset. The long
`audio_silence_sample_ptr` (`$0005DD0C`) supplies the 64-byte fallback sample
to both the normal channel update and command 2. Finally,
`audio_sample_visualization_offset` (`$0005DD12`) indexes the seventh sample's
display data while the updater writes its oscillating visual pattern. The
surrounding bytes have no established independent consumers and remain raw.

## Maintenance rule

Add entries only when they are represented by durable facts or are clearly
marked as a working interpretation/open question.  When a discovery changes,
update the durable fact first, regenerate and verify the target, then revise
this map with the relevant address and evidence.
