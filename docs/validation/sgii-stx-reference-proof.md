# Starglider II STX reference proof

## Input access is fixed

The supplied ZIP is directly readable in the new task. No Library download,
network-setting change or alternate game image was needed. Nothing from the ZIP
is checked into Git.

- Archive: `Starglider 2 (1988)(Rainbird).zip`, 1,396,099 bytes.
- Archive SHA-256: `b90148a70ea0ab6a8b0422b42c28400c4a327fd797312ef6ead9dc7965bfcf7f`.
- One member: `Starglider 2 (1988)(Rainbird).stx`, 1,942,718 bytes.
- Member SHA-256: `6a25ccb01084c666241556e5f98fdfec260415bd9ca259ac688fddcaf99a2d22`.
- Contents identify STX version 3, imaging tool 1, revision 2. The filename does
  not authenticate the release. The archive identity is unchanged after parsing.

## External parser proof

Reference: Hatari `b18511507bcf48dcf11f32b555774ea2f5e93fd0`.
`tools/stx_reference_probe.py` compiles its unchanged `STX_BuildStruct`, free,
simple-sector and ID-CRC functions from an external pinned checkout, with its
header, constants and utilities. No Hatari implementation is vendored. Hatari's
GPL-2.0-or-later notices remain in that external checkout. This adapter is not
our native STX reader and does not run Hatari's FDC or boot the game.

Example, with private input and output paths:

```sh
ASAN_OPTIONS=detect_leaks=0 python tools/stx_reference_probe.py \
  --hatari /private/hatari-pinned \
  --image '/private/Starglider 2 (1988)(Rainbird).zip' \
  > /private/stx-reference-inventory.json
```

Address and undefined-behaviour sanitizers are enabled. This container's ptrace
prevents LeakSanitizer from operating; only leak checking was disabled. No bounds
or undefined-behaviour diagnostics occurred. All returned sector, fuzzy-mask and
track-image ranges were checked against their containing track. The report has
metadata and hashes, not game bytes. It remains private and is generated on demand.
The adapter is for a trusted research input, not a hardened arbitrary-file parser.

Observed inventory:

- 164 track/side instances: cylinders 0–81, both sides.
- 943 sector instances: 785 of 1,024 bytes and 158 of 512 bytes.
- 935 sectors have status zero. Eight have status `$88`: fuzzy data and CRC error.
- Eight 1,024-byte fuzzy masks, totalling 8,192 bytes. No variable-time sectors.
- Every track has flags `$61`, including a raw track image. Track images total
  1,031,657 bytes. Preserve bit 5 as observed rather than inventing its meaning.
- Six track instances have no sectors but retain track images: cylinder 1/side 0,
  79/0, 80/0, 80/1, 81/0 and 81/1. They are not established empty tracks.
- No duplicate CHRN IDs within an individual track instance in this input.
- All track blocks account for the complete file, with no trailing bytes.
- Track 0/side 0 has sector ID 1, 512 bytes at STX file offset 6,342.
  Its big-endian WORD checksum is `$1234`, consistent with an executable ST boot
  sector. Its SHA-256 is
  `07cb8e48b5da8ebb51841b54881b173d88833f2152230f71821838af1bef69f3`.

This is successful original-container parsing. It is not successful boot,
recovered main payloads, release authentication or protection/timing equivalence.
No protection, CRC, fuzzy data or original sectors were changed.

## Reference test gap

The pinned tree has STX code only in `src/floppies/stx.c` and its header. Searches
of the complete test tree, test registrations, tools and CI found no dedicated
STX suite or STX fixtures. The `hmsa` tool explicitly excludes STX; its tests are
not a substitute. No upstream STX suite was run or claimed.

Our adapter has ten local input/extraction checks and one real upstream-parser
check using a synthetic 512-byte sector track. Run them with:

```sh
HATARI_STX_REFERENCE=/private/hatari-pinned ASAN_OPTIONS=detect_leaks=0 \
  python -m unittest discover -s tests -p test_stx_reference_probe.py
```

## Native reader and import API

`src/platform_atari_stx.c` is our C implementation. Its format offsets and flags
come from `knowledge/atari_st_disk_file.json` through the existing generator.
The format source is [Pasti File Documentation v0.5, sections 2.1–2.2.5](https://info-coach.fr/atari/documents/_mydoc/Pasti-documentation.pdf),
checked against the pinned Hatari parser. No upstream implementation is vendored.

The disk library detects STX by signature. Python's existing
`inspect_disk_with_c_backend` accepts the STX directly or as the sole disk in a
ZIP. Corpus input discovery also accepts `.stx`. The native CLI is:

```sh
src/build/platform_disk_cli.exe inspect-disk atari-st-disk /private/input.stx
src/build/platform_disk_cli.exe extract-stx-sector /private/input.stx 0 0 \
  > /private/boot-sector.bin
```

The two numbers are physical track-instance and sector-instance indexes from
inspection, not cylinder/head/sector IDs. Original source ranges remain the
basis for all extracted data. The SGII boot-sector extraction is 512 bytes and
matches the reference identity above. Inventories stay private and reproducible.

The C model retains original record order, duplicate identities, all header
values, sector-data offsets, track images, fuzzy masks, timing ranges and opaque
tails. CRC bytes are big-endian. Revision-2 timing sizes include their four-byte
header; timing values remain in their stored big-endian form. Revision-0 variable
timing is marked as an implicit Speedlock/Macrodos policy, not a nonexistent file
range. No fuzzy values are generated. Raw stored ranges remain available even
when normal reads are refused.

`atari_stx_read_chrn` requires both physical cylinder/side and the exact sector
ID bytes. It refuses ambiguous matches, including duplicate track instances.
`atari_stx_read_instance` uses an explicit physical identity. Both refuse absent
or fuzzy data, nonzero sector status and unsupported flags/record types. Failure
clears the output pointer and length. They provide stored stable bytes; they do
not implement WD1772 timing or disk rotation.

Limits: version 3, revisions 0 and 2. Invalid bounds, mismatched fuzzy/timing
lengths, impossible simple-track layouts and extra whole-file bytes are errors.
Unknown header/flag values and bounded track tails are retained for analysis.
Simple-track CRC and bit-position defaults are not stored in STX, so our reader
does not fabricate the values Hatari needs for FDC emulation. This is the sole
intentional descriptor difference in synthetic reference comparisons.

STX inspection reports `filesystem_status: not_analyzed` and no filesystem
entries. This does **not** mean the disk has no files. The existing FAT reader
still consumes flat images; it must not be fed an arbitrary flattened STX.
Stable-sector access is ready for loader reads or a future mapped FAT adapter.
No full-disk flattening, STX writing, FDC emulation, game boot or main-payload
recovery is claimed. Amiga target source, assets and restoration state are not
changed by this reader milestone.

## Replacement validation

The reference suite gap was reported and the replacement tests were authorized.
Run the complete affected suite on Linux with a built backend:

```sh
make -j4 all
STX_SANITIZERS=1 ASAN_OPTIONS=detect_leaks=0 \
HATARI_STX_REFERENCE=/private/hatari-pinned \
SGII_STX_IMAGE='/private/Starglider 2 (1988)(Rainbird).zip' \
AMIGA_INCLUDE_EXPLICIT_TESTS=1 AMIGA_INCLUDE_HEAVY_UNIT_TESTS=1 \
python -m unittest src.tests.test_platform_atari_stx \
  src.tests.test_platform_atari_st_disk src.tests.test_platform_disk_lib \
  src.tests.test_platform_disk_cli src.tests.test_platform_format_codegen \
  tests.test_stx_reference_probe -v
```

Result: 58 tests run; 57 pass and one existing Ice-ADF test is skipped because
its private fixture is absent. This includes generated-file identity/style
checks, flat Atari FAT and Amiga disk regressions, CLI extraction and ZIP
inspection. The native parser passes ASan/UBSan for every truncation and every
single-bit mutation of six synthetic fixtures. A separate seeded mutation test
checks 1,000 compound changes and failure cleanup.

Independent comparison covers simple tracks, empty/track-image-only tracks,
embedded sector data, duplicate IDs, missing data, fuzzy masks and revision-0/2
timing. On the actual SGII input, all 164 track and 943 sector descriptors and
all returned data/track/fuzzy hashes match pinned Hatari. No sanitizers report
bounds or undefined-behaviour errors. Original media is not committed or changed.
The host build is tested on Linux; the Windows build inputs/exports are updated
but were not executed here. No game-source regeneration was needed for this
container-reader change; exact-build gates remain required when recovered target
bytes or rendered assembly change.
