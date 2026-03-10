# Amiga IFF Format Reference

Auto-generated from `scripts/parse_iff_specs.py`. See `amiga_iff_formats.json` for machine-readable version.

## IFF Container (EA IFF 85)

Byte order: **big-endian** (Motorola)

### Chunk Header (8 bytes)
| Offset | Type | Field | Description |
|--------|------|-------|-------------|
| 0 | CHAR[4] | ckID | 4-byte ASCII chunk identifier |
| 4 | ULONG | ckSize | data byte count (excludes header + pad) |

Every chunk padded to even length. Groups: FORM (typed container), LIST (ordered collection), CAT (unordered), PROP (shared properties).

### Generic Chunks (valid in any FORM)
| ID | Name | Description |
|----|------|-------------|
| ANNO | Annotation | Free-text annotation string |
| AUTH | Author | Author/creator name string |
| NAME | Name | Name of art, music, etc. |
| TEXT | Text | Unformatted ASCII text |
| (c)  | Copyright | Copyright notice string |
| FVER | File Version | AmigaOS 2.0+ $VER: version string |
| JUNK | Junk | Always ignore this chunk (padding/alignment) |

## FORM ILBM — Interleaved Bitmap

Raster bitmap image with color map, optional mask, and Amiga viewport modes. The standard Amiga image format used by DPaint, PPaint, and virtually all graphics software.

Grammar: `FORM ILBM { BMHD [CMAP] [GRAB] [DEST] [SPRT] [CAMG] [CRNG*] [CCRT*] [BODY] }`

### BMHD — Bitmap Header (required)

Struct: `BitMapHeader` (20 bytes)

| Offset | Type | Field | Description |
|--------|------|-------|-------------|
| 0 | UWORD | w | raster width in pixels |
| 2 | UWORD | h | raster height in pixels |
| 4 | WORD | x | image position X (pixels) |
| 6 | WORD | y | image position Y (pixels) |
| 8 | UBYTE | nPlanes | number of source bitplanes (depth) |
| 9 | UBYTE | masking | 0=none, 1=hasMask, 2=hasTransparentColor, 3=lasso |
| 10 | UBYTE | compression | 0=none, 1=byteRun1 |
| 11 | UBYTE | pad1 | unused, set to 0 |
| 12 | UWORD | transparentColor | transparent color number (for masking 2 or 3) |
| 14 | UBYTE | xAspect | pixel aspect ratio width (10 for 320x200) |
| 15 | UBYTE | yAspect | pixel aspect ratio height (11 for 320x200) |
| 16 | WORD | pageWidth | source page width in pixels |
| 18 | WORD | pageHeight | source page height in pixels |

### CMAP — Color Map

Color register values as RGB triplets. Count = ckSize / 3.

Struct: `ColorRegister` (3 bytes)

| Offset | Type | Field | Description |
|--------|------|-------|-------------|
| 0 | UBYTE | red | red intensity 0-255 |
| 1 | UBYTE | green | green intensity 0-255 |
| 2 | UBYTE | blue | blue intensity 0-255 |

*Amiga OCS/ECS has 4-bit DACs — use high nibble only. AGA has 8-bit. n_colors = ckSize / 3, normally 2^nPlanes.*

### GRAB — Hotspot

Struct: `Point2D` (4 bytes)

| Offset | Type | Field | Description |
|--------|------|-------|-------------|
| 0 | WORD | x | hotspot X relative to upper-left |
| 2 | WORD | y | hotspot Y relative to upper-left |

### DEST — Destination Merge

Struct: `DestMerge` (8 bytes)

| Offset | Type | Field | Description |
|--------|------|-------|-------------|
| 0 | UBYTE | depth | bitplanes in original source |
| 1 | UBYTE | pad1 |  |
| 2 | UWORD | planePick | scatter source planes into dest (bit per plane) |
| 4 | UWORD | planeOnOff | default data for non-picked planes |
| 6 | UWORD | planeMask | gate: 1=write to this dest plane, 0=leave alone |

### SPRT — Sprite

Struct: `SPRT` (2 bytes)

| Offset | Type | Field | Description |
|--------|------|-------|-------------|
| 0 | UWORD | precedence | sprite precedence (0=foremost) |

### CAMG — Amiga Viewport Mode

Struct: `CAMG` (4 bytes)

| Offset | Type | Field | Description |
|--------|------|-------|-------------|
| 0 | ULONG | viewModes | Amiga viewport mode flags |

Constants:

- `HAM` = 0x0800 — Hold-And-Modify mode
- `EHB` = 0x0080 — Extra-Half-Brite mode
- `LACE` = 0x0004 — Interlace mode
- `HIRES` = 0x8000 — High resolution (640 px wide)
- `HAM8` = 0x0800 — HAM8 (AGA, 8 planes)
- `SUPERHIRES` = 0x0020 — Super high resolution (1280 px wide)
- `DUALPF` = 0x0400 — Dual playfield mode

### CRNG — Color Range

DPaint color cycling range. Can appear multiple times.

Struct: `CRange` (8 bytes)

| Offset | Type | Field | Description |
|--------|------|-------|-------------|
| 0 | WORD | pad1 | reserved, set to 0 |
| 2 | WORD | rate | color cycle rate (16384 = 60 steps/sec) |
| 4 | WORD | active | nonzero = cycling enabled |
| 6 | UBYTE | low | lower color register |
| 7 | UBYTE | high | upper color register |

### CCRT — Color Cycling Range and Timing

Graphicraft color cycling. Alternative to CRNG.

Struct: `CycleInfo` (14 bytes)

| Offset | Type | Field | Description |
|--------|------|-------|-------------|
| 0 | WORD | direction | 0=don't cycle, 1=forward, -1=backward |
| 2 | UBYTE | start | lower color register |
| 3 | UBYTE | end | upper color register |
| 4 | LONG | seconds | seconds between color changes |
| 8 | LONG | microseconds | microseconds between color changes |
| 12 | WORD | pad | reserved, set to 0 |

### BODY — Image Body (required)

Interleaved bitplane data. Each scan line = nPlanes rows (+ mask row if masking=1), each row = ceil(w/16) words. Rows may be ByteRun1 compressed.

### Compression

**byteRun1** (id=1): PackBits-style run-length encoding, applied per row

  Read next signed byte n
  If 0 <= n <= 127: copy next n+1 bytes literally
  If -127 <= n <= -1: replicate next byte (-n+1) times
  If n == -128: no-op (skip)
  Repeat until row complete

### Raster Layout

Bitplanes interleaved by row. Plane 0 = low-order bit of color index.
- Row width: `ceil(w / 16) * 2` bytes
- Scan line: plane 0 row, plane 1 row, ..., plane N-1 row, [mask row]
- Pixel order: left to right, MSB first within each byte

## FORM 8SVX — 8-Bit Sampled Voice

8-bit audio sample, either one-shot sound or multi-octave musical instrument with optional envelope.

Grammar: `FORM 8SVX { VHDR [NAME] [(c) ] [AUTH] [ANNO*] [ATAK] [RLSE] BODY }`

### VHDR — Voice Header (required)

Struct: `Voice8Header` (20 bytes)

| Offset | Type | Field | Description |
|--------|------|-------|-------------|
| 0 | ULONG | oneShotHiSamples | samples in high octave one-shot part |
| 4 | ULONG | repeatHiSamples | samples in high octave repeat part |
| 8 | ULONG | samplesPerHiCycle | samples/cycle in high octave (0=unknown) |
| 12 | UWORD | samplesPerSec | sampling rate in Hz |
| 14 | UBYTE | ctOctave | number of octaves of waveform data |
| 15 | UBYTE | sCompression | 0=none, 1=fibDelta |
| 16 | Fixed | volume | playback volume, Fixed 16.16 (0x10000=full) |

### BODY — Sample Data (required)

Signed 8-bit samples (-128..127). Highest octave first, each successive octave has 2x samples. Total = (2^0 + ... + 2^(ctOctave-1)) * (oneShotHiSamples + repeatHiSamples).

### ATAK — Attack Envelope

Piecewise-linear attack contour. Array of EGPoint, count = ckSize / 6.

Struct: `EGPoint` (6 bytes)

| Offset | Type | Field | Description |
|--------|------|-------|-------------|
| 0 | UWORD | duration | segment duration in milliseconds |
| 2 | Fixed | dest | destination volume factor (Fixed 16.16) |

### RLSE — Release Envelope

Piecewise-linear release contour. Same format as ATAK.

Struct: `EGPoint` (6 bytes)

| Offset | Type | Field | Description |
|--------|------|-------|-------------|
| 0 | UWORD | duration | segment duration in milliseconds |
| 2 | Fixed | dest | destination volume factor (Fixed 16.16) |

### CHAN — Channel Assignment

Struct: `CHAN` (4 bytes)

| Offset | Type | Field | Description |
|--------|------|-------|-------------|
| 0 | LONG | sampletype | 2=LEFT, 4=RIGHT, 6=STEREO |

*Stereo: BODY contains LEFT then RIGHT data, equal length.*

### PAN — Stereo Panning

Struct: `PAN` (4 bytes)

| Offset | Type | Field | Description |
|--------|------|-------|-------------|
| 0 | Fixed | sposition | stereo position: 0=right, Unity(0x10000)=left, Unity/2=center |

### Compression

**fibDelta** (id=1): Fibonacci-delta encoding — 4 bits per sample, halves data size

  First 2 bytes: pad byte + initial 8-bit value
  Remaining bytes: each byte holds 2 nybbles (high first)
  Each nybble indexes delta_table, delta added to running value
  Output: 2*(n-2) samples from n input bytes

  Delta table: `[-34, -21, -13, -8, -5, -3, -2, -1, 0, 1, 2, 3, 5, 8, 13, 21]`

## FORM ANIM — Cel Animation

Animated sequence of ILBM frames. First frame is full ILBM, subsequent frames are delta-compressed differences. Uses double-buffering playback (each delta modifies frame 2 back).

Grammar: `FORM ANIM { FORM ILBM(frame1) [FORM ILBM(frame2..N)]* }`

- Frame 1: Full FORM ILBM with BMHD, CMAP, BODY (+ optional ANHD for timing)
- Frame 2: FORM ILBM with ANHD + DLTA (delta from frame 1)
- Frame 3+: FORM ILBM with ANHD + DLTA (delta from 2 frames back)
- Looping: last 2 frames duplicate first 2 frames

### ANHD — Animation Header (required)

Per-frame animation parameters. Replaces BMHD in delta frames.

Struct: `ANHD` (24 bytes)

| Offset | Type | Field | Description |
|--------|------|-------|-------------|
| 0 | UBYTE | operation | compression method: 0=direct, 1=XOR, 2=longDelta, 3=shortDelta, 4=generalDelta, 5=byteVertical, 6=stereo5, 74('J')=reserved(Eric Graham) |
| 1 | UBYTE | mask | XOR mode: plane mask (bit set = has data) |
| 2 | UWORD | w | XOR mode: width of delta area |
| 4 | UWORD | h | XOR mode: height of delta area |
| 6 | WORD | x | XOR mode: X position of delta area |
| 8 | WORD | y | XOR mode: Y position of delta area |
| 10 | ULONG | abstime | absolute time from first frame (1/60 sec jiffies) |
| 14 | ULONG | reltime | time since previous frame (1/60 sec jiffies) |
| 18 | UBYTE | interleave | frames back to modify (0=default=2 for double-buffering) |
| 19 | UBYTE | pad0 |  |
| 20 | ULONG | bits | option bits for methods 4&5 |

Option bits (ANHD.bits):

- Bit 0: 0=short data, 1=long data
- Bit 1: 0=set, 1=XOR
- Bit 2: 0=separate info per plane, 1=one info list for all planes
- Bit 3: 0=not RLC, 1=run-length coded
- Bit 4: 0=horizontal, 1=vertical
- Bit 5: 0=short info offsets, 1=long info offsets

### DLTA — Delta Data (required)

Frame difference data. Format depends on ANHD.operation.

Delta compression methods:

**Method 1: XOR**
  XOR between current and 2-frames-back, stored as ByteRun1 in BODY chunk

**Method 2: Long Delta**
  Changed longwords with offsets. 8 LONG pointers to per-plane data. Positive offset = skip + 1 longword. Negative offset = -(offset+2) then count + N contiguous longwords. Terminates with 0xFFFF.

**Method 3: Short Delta**
  Same as method 2 but with WORD-sized data instead of LONG.

**Method 4: General Delta**
  16 LONG pointers: 8 data + 8 offset/count lists. Supports short/long, horizontal/vertical, set/XOR, RLC options via ANHD.bits.

**Method 5: Byte Vertical (Jim Kent)**
  16 LONG pointers (first 8 used). Per-plane, per-column compression. Each column: op-count byte, then ops: skip (0x01-0x7F), uniq (0x80|count + literal bytes), same (0x00 + count + fill byte). Dest advances by bytes_per_row.
  - `0x01-0x7F` skip: skip N rows (advance dest by N * bytesPerRow)
  - `0x80-0xFF` uniq: copy (byte & 0x7F) literal bytes
  - `0x00` same: next byte = count, then byte = fill value, repeat count times

### Playback

- Buffers: 2
- Method: Double-buffered: display A, modify B with delta, flip. Delta for frame N modifies frame N-2.
- Timing: ANHD.reltime in jiffies (1/60 sec). Use VBlank interrupt for timing.

## FORM ACBM — Amiga Contiguous Bitmap

Like ILBM but with contiguous (non-interleaved) bitplane data. Faster loading from AmigaBasic. Uses ABIT chunk instead of BODY.

Grammar: `FORM ACBM { BMHD [CMAP] ABIT }`

### BMHD — Bitmap Header

Same as ILBM BMHD

### CMAP — Color Map

Same as ILBM CMAP

### ABIT — Amiga Bitplanes (required)

Contiguous bitplane data: all of plane 0, then all of plane 1, etc. Each plane = h * ceil(w/16) * 2 bytes.
