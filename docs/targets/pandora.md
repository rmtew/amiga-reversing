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

The target now has a shared 0x54-byte `world_object_shared_prefix` type.  Its
field facts come from the common scan loop rather than the player instance:
`interaction_callback` (`+0x04`), `context_callback` (`+0x0c`),
`interaction_data_ptr` (`+0x10`), `position_descriptor_ptr` (`+0x2c`),
position, `proximity_distance` (`+0x42`), flags, and the cooldown.  The prefix
is bound at the player entry; unclassified spans stay raw.  A complete
`world_object_record` layout remains open rather than inferred from that
minimum common prefix.

## Maintenance rule

Add entries only when they are represented by durable facts or are clearly
marked as a working interpretation/open question.  When a discovery changes,
update the durable fact first, regenerate and verify the target, then revise
this map with the relevant address and evidence.
