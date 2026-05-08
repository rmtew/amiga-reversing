# M68K analysis plan: RSSET and absolute memory layout

This plan records the current RSSET survey and the next implementation rules.
It should be reviewed before more renderer changes are made.

## Objective

Build a C-owned model for persistent base-relative storage and absolute runtime
memory. Rendering should consume that model to emit `RSSET`, labels, platform
fields, and web UI navigation without confusing app storage, Amiga hardware, and
runtime-copied code.

## Current Implementation Notes

Commit `ff0753d8069cbf5495debcaa9536f8d5b940cafe` added a guard against treating
unknown `a6` displacements as app slots when the displacement matches generated
`_custom` hardware metadata.

Relevant current behavior:

- `render_state_operand_uses_app_base()` rejects registers already known as
  hardware bases.
- Unknown `a6` fallback is still allowed, but not for `_custom` register,
  register-field, or register-range offsets.
- `render_asm_app_extension_rs()` builds RSSET output from app-base field slots
  and metadata RSSET layout regions.
- Overlapping slots are currently emitted as alias `RSSET $xxxx` fragments.
- The RSSET slot list uses renderer scratch arena storage.

The test covering the hardware false-positive class is
`test_facts_v2_render_asm_source_does_not_infer_app_slot_from_unknown_a6_custom_offset`.

## Survey Method

Surveyed all rendered `.s` files currently under `targets/` and parsed top-level
`RSSET`, `app_* RS.*`, and unnamed `RS.*` rows. No duplicate RSSET symbol names
were found in the surveyed files.

## RSSET Survey

| Target source | Ranges | Origin and review |
| --- | ---: | --- |
| `carrier/.../c__loadwb_175153fc.s` | 1 | `RSSET 0`; small app-base layout. |
| `carrier/.../c__more_7c8dea18.s` | 1 | `RSSET 0`; small app-base layout. |
| `carrier/.../c__setpatch_50db5120.s` | 1 | `RSSET 0`; app-base storage. |
| `carrier/.../devs__parallel.device_0b78e156.s` | 1 | `RSSET LIB_SIZE`; resident device extension. |
| `carrier/.../devs__ramdrive.device_2c146d8c.s` | 1 | `RSSET LIB_SIZE`; resident device extension. |
| `carrier/.../devs__serial.device_ddfdac2b.s` | 9 | Main `LIB_SIZE` layout plus singleton overlays at `$0023,$0038,$0043,$0044,$0045,$0048,$01BD,$01C4`; not proven independent ranges. |
| `carrier/.../libs__icon.library_8bc90c0c.s` | 1 | `RSSET LIB_SIZE`; resident library extension. |
| `carrier/.../libs__info.library_3fb9d33a.s` | 1 | `RSSET LIB_SIZE`; resident library extension. |
| `carrier/.../libs__version.library_5059c1a5.s` | 1 | `RSSET LIB_SIZE`; resident library extension. |
| `carrier/.../amiga_raw_carrier_rnc_00004c60.s` | 1 | `RSSET 0`; decompressed raw target app layout. Needs absolute load range metadata. |
| `damocles/.../c__ed_fbb099a6.s` | 1 | `RSSET 0`; app-base storage. |
| `damocles/.../damocles_53b24620.s` | 1 | `RSSET 0`; app-base storage. |
| `damocles/.../devs__parallel.device_0b71ffaa.s` | 1 | `RSSET LIB_SIZE`; resident device extension. |
| `damocles/.../devs__printer.device_1aada1d4.s` | 1 | `RSSET LIB_SIZE`; resident device extension. |
| `ice_runner/.../bootloader_stage_1.s` | 1 | `RSSET 0`; bootloader/app storage. |
| `midwinter/.../bootblock.s` | 1 | `RSSET 0`; bootblock state. |
| `pandora/.../pandora_..._bk_00_000000e8.s` | 4 | Main `RSSET 0` plus overlays at `$01AD,$0287,$07EF`; raw absolute payload needs load/range tracking. |
| `search-for-the-king/.../king_481902ec.s` | 1 | `RSSET 0`; app-base storage. |
| `search-for-the-king/.../libs__icon.library_8bc90c0c.s` | 1 | `RSSET LIB_SIZE`; resident library extension. |
| `search-for-the-king/.../loadwb_f71d84f8.s` | 1 | `RSSET 0`; small app-base layout. |
| `starglider/.../c__binddrivers_0f9bcf15.s` | 1 | `RSSET 0`; small app-base layout. |
| `starglider/.../devs__parallel.device_0b78e156.s` | 1 | `RSSET LIB_SIZE`; resident device extension. |
| `starglider/.../devs__serial.device_ddfdac2b.s` | 1 | `RSSET LIB_SIZE`; resident device extension. |
| `starglider/.../libs__icon.library_8bc90c0c.s` | 1 | `RSSET LIB_SIZE`; resident library extension. |
| `starglider/.../libs__info.library_3fb9d33a.s` | 1 | `RSSET LIB_SIZE`; resident library extension. |
| `starglider/.../libs__mathieeedoubbas.library_3d4e4903.s` | 1 | Empty `LIB_SIZE` context; should be checked before retaining. |
| `starglider/.../libs__mathtrans.library_30d0f132.s` | 1 | Empty `LIB_SIZE` context; should be checked before retaining. |
| `starglider/.../libs__version.library_5059c1a5.s` | 1 | `RSSET LIB_SIZE`; resident library extension. |
| `starglider/.../sg_9832b282.s` | 1 | Large `RSSET 0`; app-base storage. |
| `starglider/.../system__diskcopy_c5715319.s` | 1 | `RSSET 0`; small app-base layout. |
| `voodoo-nightmare/.../run_df6ad190.s` | 1 | Large `RSSET 0`; app-base storage. |
| `targets/amiga_hunk_bloodwych/bloodwych.s` | 5 | Main `RSSET 0` plus byte overlays `$0001,$0003,$0005,$0007`; aliases inside one app layout. |
| `targets/amiga_hunk_genam/genam.s` | 5 | Main `RSSET 0` plus overlays `$021D,$023F,$057F,$10CC`; includes named `app_TimerBase`; not independent ranges. |
| `targets/amiga_hunk_magicland_dizzy_md/magicland_dizzy_md.s` | 1 | `RSSET 0`; minimal app/storage evidence. |
| `targets/amiga_hunk_monam302/monam302.s` | 5 | Main `RSSET 0` plus overlays `$0560,$0567,$082C,$0C6E`; includes named `app_ConsoleDevice`; not independent ranges. |
| `targets/amiga_hunk_voodoo_nightmare_run/voodoo_nightmare_run.s` | 1 | Large `RSSET 0`; app-base storage. |

## Multi-Range Review

The current multi-RSSET files do not prove multiple independent memory ranges.
They are mostly alias overlays inside one base:

| File | Finding |
| --- | --- |
| Carrier `serial.device` | One `LIB_SIZE` device extension. Extra ranges are singleton offsets inside that layout. |
| Pandora extracted BK target | One main app layout. Extra ranges are aliases; the larger issue is absolute load/runtime range tracking. |
| Bloodwych | Main app layout with byte overlays at odd offsets. Not independent bases. |
| GenAm | Main app layout with singleton overlays and API-derived base slots. Not independent bases. |
| MonAm | Main app layout with singleton overlays and API-derived base slots. Not independent bases. |

Required change: represent these as one layout with alias fields unless C analysis
proves a distinct base id.

## Implementation Requirements

1. Add or refine C analysis records for base-relative layouts:
   - base id and name
   - base kind: app, resident extension, IORequest, metadata, absolute
   - base address if known
   - field offset, size, access width, read/write/address evidence
   - alias/overlay relationship
   - source instruction provenance
   - confidence and conflict state

2. Add absolute memory-layout records:
   - source section/file range
   - runtime destination base and extent
   - copied-code entrypoints
   - stack, bitplane, copper, audio, and app-storage ranges when detected
   - ownership conflicts and accepted-code overlap gates

3. Rendering rules:
   - emit one RSSET block per proven base layout
   - emit alias fragments only as overlays of that layout
   - never use RSSET for known hardware or platform struct fields
   - never use absolute label/addend tricks over code/data ranges
   - keep include region, RSSET region, then EQU/symbol region ordering

4. Web UI rules:
   - show memory layout ranges and conflicts from C analysis
   - navigate to source evidence for each range
   - distinguish app layout fields, aliases, hardware fields, copied runtime
     code, display memory, audio memory, and stack

## Open Checks Before Implementation

- Empty `LIB_SIZE` contexts in Starglider math libraries should be confirmed as
  intentional or removed from rendering.
- Large app layouts such as Carrier RNC, Starglider, and Voodoo need stricter
  overlap checks against accepted code and typed structs.
- Absolute raw/decompressed targets need load address, source extent, and entry
  range recorded in the same C analysis data used by rendering and the web UI.
- Existing alias emission should be backed by explicit alias facts rather than
  produced as a side effect of sorted slot overlap.

