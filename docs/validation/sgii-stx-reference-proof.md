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

## Test gap and next gate

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

Proposal 047 requires agreement on replacement validation before implementing
our reader when a relevant reference suite is absent. Recommended replacement:
synthetic redistributable fixtures for each format branch; malformed bounds and
length tests under sanitizers; independent raw expected offsets/bytes; differential
comparison of native descriptors against pinned Hatari on this supplied input.
Include simple tracks, track-image-only records, duplicate IDs, CRC/RNF/deleted
status, fuzzy masks, revision-specific timing, sync offsets and unsupported flags.
Do not treat original-media parsing as that missing synthetic suite.

Native reader implementation, target import/schema migration and unrelated Amiga
restoration have not started. All supplied media remains private.
