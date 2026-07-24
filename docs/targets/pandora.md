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

### Confirmed shared data

| Address | Symbol | Current interpretation |
| --- | --- | --- |
| `$0005DD00` | `audio_master_volume` | Default master-volume word, initialized to `$0040`; later used by proximity audio logic. |
| `$0005E5F6` | `audio_channel_playback_states` | Four instances of the recovered 0x26-byte `audio_channel_playback_state` record.  The prior apparent second-record extension was listing fragmentation. |
| `$0005E690` | `audio_channel_dma_configurations` | Four instances of the recovered 0x0c-byte `audio_channel_dma_configuration` record. |
| `$0005DDD4` | `audio_pitch_scalars` | Bounded 110-word pitch-scalar lookup table used to scale sample periods. |
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

`world_object_ptr_table` is a bounded 36-element long-pointer array followed
by its null terminator.  `scan_world_objects_for_proximity` advances through
that exact range and branches to context handling at the terminator; subsequent
longwords belong to a different table.

`active_world_object_static_ptr_table` starts at the second pointer and has 35
entries before the same terminator.  It intentionally excludes the player and
is used by `update_active_world_object_positions`; the similarly named runtime
equate is a separate active-table pointer slot.

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
initializes tilemap/player/UI state, installs the static active-table pointer
and count, then iterates every `world_object_ptr_table` entry to reset per-object
state and resolve item names.

That initialization loop proves the shared prefix's current/initial pairs:
`selected_item_id`/`initial_selected_item_id`,
`world_object_flags`/`initial_world_object_flags`, and
`item_state`/`initial_item_state`.  It also resets `interaction_timer` and
uses `item_definition_id` to resolve each object's item-name pointer.
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
each world object's `item_name_ptr`.

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
`app_world_interaction_audio_flags` at `+0x033e`. The first holds independent
one-shot guards for the Musician, Chemist, Technician, Wackobrain, Squash
player, and Diabetic paths. The second contains audio-pending gates: the
Menial droid and Gardener callbacks set bits 1 and 2 before starting their
feedback sequence, then clear them only after channel 2's playback-tick
counter reaches zero. Both bytes are reset by `initialize_world_state`.

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

## Maintenance rule

Add entries only when they are represented by durable facts or are clearly
marked as a working interpretation/open question.  When a discovery changes,
update the durable fact first, regenerate and verify the target, then revise
this map with the relevant address and evidence.
