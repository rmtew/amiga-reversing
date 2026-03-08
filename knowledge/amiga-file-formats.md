# Amiga Executable and Loadable File Formats

## 1. Amiga Hunk Format

The Amiga Hunk format is the native binary format of AmigaOS for executables, object files, and link libraries. All data is big-endian. All sizes are in longwords (4 bytes) unless noted.

### 1.1 Magic Numbers

| Format | Magic (hex) | Decimal |
|--------|-------------|---------|
| Loadable executable | $000003F3 (HUNK_HEADER) | 1011 |
| Object file / Link library | $000003E7 (HUNK_UNIT) | 999 |

### 1.2 Complete Hunk Type Table

From `dos/doshunks.h` (Release 45.1, V36.9):

| Hunk Type | Decimal | Hex | Purpose |
|-----------|---------|-----|---------|
| HUNK_UNIT | 999 | $3E7 | Compilation unit (object files) |
| HUNK_NAME | 1000 | $3E8 | Section name |
| HUNK_CODE | 1001 | $3E9 | Executable code segment |
| HUNK_DATA | 1002 | $3EA | Initialized data segment |
| HUNK_BSS | 1003 | $3EB | Uninitialized data (zero-filled) |
| HUNK_RELOC32 | 1004 | $3EC | 32-bit absolute relocations |
| HUNK_RELOC16 | 1005 | $3ED | 16-bit PC-relative relocations |
| HUNK_RELOC8 | 1006 | $3EE | 8-bit PC-relative relocations |
| HUNK_EXT | 1007 | $3EF | External symbol definitions/references |
| HUNK_SYMBOL | 1008 | $3F0 | Symbol table (debug) |
| HUNK_DEBUG | 1009 | $3F1 | Debug information |
| HUNK_END | 1010 | $3F2 | Hunk terminator |
| HUNK_HEADER | 1011 | $3F3 | Executable file header |
| *(1012 unused)* | | $3F4 | |
| HUNK_OVERLAY | 1013 | $3F5 | Overlay module reference |
| HUNK_BREAK | 1014 | $3F6 | Overlay module terminator |
| HUNK_DREL32 | 1015 | $3F7 | 32-bit data-relative relocation |
| HUNK_DREL16 | 1016 | $3F8 | 16-bit data-relative relocation |
| HUNK_DREL8 | 1017 | $3F9 | 8-bit data-relative relocation |
| HUNK_LIB | 1018 | $3FA | Library container |
| HUNK_INDEX | 1019 | $3FB | Library index |
| HUNK_RELOC32SHORT | 1020 | $3FC | Compact 32-bit relocation (16-bit offsets) |
| HUNK_RELRELOC32 | 1021 | $3FD | PC-relative 32-bit relocation |
| HUNK_ABSRELOC16 | 1022 | $3FE | Absolute 16-bit relocation |

Extended (MorphOS/AmigaOS 4):

| Hunk Type | Decimal | Hex | Purpose |
|-----------|---------|-----|---------|
| HUNK_PPC_CODE | 1257 | $4E9 | PowerPC code segment |
| HUNK_RELRELOC26 | 1260 | $4EC | 26-bit PC-relative relocation (PPC) |

Aliases defined in doshunks.h:
- HUNK_ABSRELOC32 = HUNK_RELOC32
- HUNK_RELRELOC16 = HUNK_RELOC16
- HUNK_RELRELOC8 = HUNK_RELOC8

### 1.3 Memory Type Flags (in hunk size longwords)

The upper bits of hunk size entries encode memory requirements:

| Bit | Name | Hex Mask | Meaning |
|-----|------|----------|---------|
| 29 | HUNKB_ADVISORY | $20000000 | Advisory (linker hint) |
| 30 | HUNKB_CHIP | $40000000 | Must be in Chip RAM (DMA-accessible) |
| 31 | HUNKB_FAST | $80000000 | Should be in Fast RAM |
| 30+31 | (both set) | $C0000000 | Extended: read additional ULONG for mem attrs |

The actual hunk size in longwords = value & $3FFFFFFF (lower 30 bits). Multiply by 4 for byte size.

When both bits 30 and 31 are set ($C0000000), an additional longword follows containing extended memory attribute flags (exec.library memory attributes).

### 1.4 HUNK_HEADER Structure (Executable Header)

```
Offset  Size    Field
------  ------  -----
0       ULONG   $000003F3 (magic)
4       ...     Resident library names (sequence of BSTR, terminated by ULONG 0)
                Each name: ULONG name_length_in_longs, then that many longs of chars
                Typically just a single ULONG 0 (no resident libraries)
var     ULONG   table_size (total number of hunks in file)
var+4   ULONG   first_hunk (first hunk slot number, usually 0)
var+8   ULONG   last_hunk (last hunk slot number = table_size - 1)
var+12  ULONG[] hunk_sizes[table_size] (one per hunk, with memory flags in upper bits)
```

After the size table, the actual hunk data follows sequentially.

### 1.5 HUNK_CODE / HUNK_DATA Structure

```
Offset  Size    Field
------  ------  -----
0       ULONG   hunk_type ($3E9 or $3EA), lower 30 bits only
4       ULONG   num_longs (data size in longwords)
8       data    num_longs * 4 bytes of code/data
```

The hunk type ID uses only the lower 29 bits ($1FFFFFFF mask) for identification; upper bits may contain flags.

### 1.6 HUNK_BSS Structure

```
Offset  Size    Field
------  ------  -----
0       ULONG   $000003EB
4       ULONG   num_longs (allocation size in longwords, no data follows)
```

### 1.7 HUNK_RELOC32 Structure

Patches absolute 32-bit addresses by adding the base address of the target hunk.

```
Offset  Size    Field
------  ------  -----
0       ULONG   $000003EC
4       ULONG   num_offsets (0 = end of relocation data)
        If num_offsets != 0:
8       ULONG   target_hunk_number
12      ULONG[] offset[num_offsets] (byte offsets into current hunk to patch)
        ...repeat (num_offsets, target_hunk, offsets) until num_offsets == 0
```

The loader adds `hunk_base_address[target_hunk]` to each ULONG at the given offsets within the current hunk's data.

### 1.8 HUNK_RELOC32SHORT Structure ($3FC)

Compact form using 16-bit values instead of 32-bit:

```
0       ULONG   $000003FC
4       UWORD   num_offsets (0 = end)
        If num_offsets != 0:
6       UWORD   target_hunk_number
8       UWORD[] offset[num_offsets]
        ...repeat until num_offsets == 0
        Pad to longword boundary if needed
```

### 1.9 HUNK_SYMBOL Structure

```
0       ULONG   $000003F0
4       ULONG   name_length_in_longs (0 = end of symbol table)
        If name_length != 0:
8       char[]  symbol_name (name_length * 4 bytes, NUL-padded)
var     ULONG   symbol_value (offset within hunk)
        ...repeat until name_length == 0
```

### 1.10 HUNK_DEBUG Structure

```
0       ULONG   $000003F1
4       ULONG   num_longs (total size of debug data in longwords)
8       data    num_longs * 4 bytes of debug data
```

Common debug format is LINE debug (magic $4C494E45 = "LINE"):
```
8       ULONG   $4C494E45 ("LINE")
12      ULONG   alloc_name_length (string length in longwords)
16      char[]  source_filename
var     ULONG   base_offset
var     pairs   {ULONG line_number, ULONG offset}[]
```

### 1.11 HUNK_EXT Structure and Sub-Types

```
0       ULONG   $000003EF
4       ...     sequence of entries, terminated by ULONG 0
```

Each entry begins with a packed longword:
```
Bits 31-24: sub-type (EXT_xxx constant)
Bits 23-0:  name_length in longwords
```

If name_length == 0, this is the terminator.

#### EXT Sub-Type Table

| Sub-Type | Value | Category | Format |
|----------|-------|----------|--------|
| EXT_SYMB | 0 | Definition | name + ULONG value |
| EXT_DEF | 1 | Definition | name + ULONG value (relocatable) |
| EXT_ABS | 2 | Definition | name + ULONG value (absolute) |
| EXT_RES | 3 | Definition | (no longer supported) |
| EXT_REF32 (ABSREF32) | 129 ($81) | Reference | name + ULONG ref_count + ULONG[] offsets |
| EXT_COMMON (ABSCOMMON) | 130 ($82) | Reference | name + ULONG common_size + ULONG ref_count + ULONG[] offsets |
| EXT_REF16 (RELREF16) | 131 ($83) | Reference | name + ULONG ref_count + ULONG[] offsets |
| EXT_REF8 (RELREF8) | 132 ($84) | Reference | name + ULONG ref_count + ULONG[] offsets |
| EXT_DEXT32 | 133 ($85) | Reference | name + ULONG ref_count + ULONG[] offsets (data-relative 32) |
| EXT_DEXT16 | 134 ($86) | Reference | name + ULONG ref_count + ULONG[] offsets (data-relative 16) |
| EXT_DEXT8 | 135 ($87) | Reference | name + ULONG ref_count + ULONG[] offsets (data-relative 8) |
| EXT_RELREF32 | 136 ($88) | Reference | name + ULONG ref_count + ULONG[] offsets (PC-relative 32) |
| EXT_RELCOMMON | 137 ($89) | Reference | name + ULONG common_size + ULONG ref_count + ULONG[] offsets |
| EXT_ABSREF16 | 138 ($8A) | Reference | name + ULONG ref_count + ULONG[] offsets (absolute 16) |
| EXT_ABSREF8 | 139 ($8B) | Reference | name + ULONG ref_count + ULONG[] offsets (absolute 8) |

Definition entries (sub-type < 128): type_and_name_len + name_data + ULONG value
Reference entries (sub-type >= 128): type_and_name_len + name_data + ULONG ref_count + ULONG offsets[ref_count]
COMMON entries: type_and_name_len + name_data + ULONG common_size + ULONG ref_count + ULONG offsets[ref_count]

### 1.12 HUNK_END Structure

```
0       ULONG   $000003F2
```

No additional data. Marks the end of a hunk block. Every CODE/DATA/BSS hunk must be terminated by HUNK_END.

### 1.13 HUNK_OVERLAY Structure

```
0       ULONG   $000003F5
4       ULONG   table_size (in longwords, actual data is table_size+1 longs)
8       ULONG   tree_size (tree depth = max path from root + 1)
12      ULONG[] tree_ptrs[tree_size - 1] (current node ordinates per level)
var     ULONG   0 (zero terminator)
var     entries overlay_entry[n] (8 longwords each)
```

Each overlay entry (32 bytes):

| Field | Offset | Size | Purpose |
|-------|--------|------|---------|
| file_position | 0 | ULONG | Byte offset to overlay module's HUNK_HEADER |
| reserved1 | 4 | ULONG | Must be 0 |
| reserved2 | 8 | ULONG | Must be 0 |
| overlay_level | 12 | ULONG | Depth from root (0 = direct child) |
| ordinate | 16 | ULONG | Horizontal position/unique ID within level |
| initial_hunk | 20 | ULONG | First hunk number when loaded |
| symbol_hunk | 24 | ULONG | Hunk containing the referenced symbol |
| symbol_offset | 28 | ULONG | Offset within hunk (entry = base + offset + 4) |

The overlay manager code sits in the first hunk (HUNK_CODE) with this layout:

| Offset | Size | Content |
|--------|------|---------|
| 0 | ULONG | $6000xxxx (BRA.W around magic) |
| 4 | ULONG | $0000ABCD (overlay magic identifier) |
| 8 | ULONG | File handle (filled by OS at load time) |
| 12 | ULONG | Pointer to HUNK_OVERLAY data |
| 16 | ULONG | Hunk table BPTR |
| 20 | ULONG | DOS global vector BPTR |

### 1.14 HUNK_BREAK Structure

```
0       ULONG   $000003F6
```

Used instead of HUNK_END to terminate overlay sub-modules. Tells LoadSeg to stop loading.

### 1.15 Library Format (HUNK_LIB / HUNK_INDEX)

Object libraries use HUNK_UNIT ($3E7) as the file magic, with HUNK_LIB ($3FA) and HUNK_INDEX ($3FB) providing indexed access to compilation units within the library.

### 1.16 Overall Executable File Structure

```
HUNK_HEADER
  resident_lib_names (usually just 0)
  table_size, first_hunk, last_hunk
  hunk_sizes[]

For each hunk (first_hunk to last_hunk):
  HUNK_CODE | HUNK_DATA | HUNK_BSS
    [HUNK_RELOC32]     (zero or more relocation blocks)
    [HUNK_RELOC32SHORT]
    [HUNK_DREL32]
    [HUNK_SYMBOL]      (optional symbol table)
    [HUNK_DEBUG]       (optional debug info)
  HUNK_END

[HUNK_OVERLAY]         (optional, for overlayed executables)
  overlay_table
  overlay_modules...
    HUNK_HEADER (sub)
    hunks...
    HUNK_BREAK
```

### 1.17 Loader Processing Sequence

1. Read and validate HUNK_HEADER magic ($3F3)
2. Skip resident library names
3. Read table_size, first_hunk, last_hunk
4. Read hunk size table; allocate memory for each hunk using specified memory type flags
5. For each hunk slot:
   a. Read hunk type (CODE/DATA/BSS)
   b. Load code/data into allocated memory (BSS: zero-fill)
   c. Process any following RELOC blocks: for each offset, add target hunk's base address to the longword at that offset
   d. Skip SYMBOL/DEBUG blocks
   e. Read HUNK_END
6. Return pointer to first hunk (as BPTR segment list)

---

## 2. Amiga Bootblock Format

### 2.1 Bootblock Structure

The bootblock occupies the first 2 sectors (1024 bytes) of a floppy disk.

```
Offset  Size    Field
------  ------  -----
$00     ULONG   DiskType ('D','O','S' + flags byte)
$04     ULONG   Checksum
$08     ULONG   Rootblock (typically 880 for DD floppies)
$0C     varies  Boot code (1012 bytes max = 1024 - 12)
```

From `devices/bootblock.h`:
```c
struct BootBlock {
    UBYTE   bb_id[4];       /* 4 character identifier: "DOS" + type */
    LONG    bb_chksum;      /* boot block checksum (balance) */
    LONG    bb_dosblock;    /* reserved for DOS patch */
};
/* Boot code follows immediately at offset 12 */
```

### 2.2 DiskType Flags (byte at offset $03)

| Value | Hex | Filesystem |
|-------|-----|------------|
| 0 | $00 | OFS (Original File System) |
| 1 | $01 | FFS (Fast File System) |
| 2 | $02 | OFS + International mode |
| 3 | $03 | FFS + International mode |
| 4 | $04 | OFS + Directory Cache |
| 5 | $05 | FFS + Directory Cache |

Bit meanings in byte 3:
- Bit 0: FFS (set) vs OFS (clear)
- Bit 1: International character support
- Bit 2: Directory cache mode

### 2.3 Checksum Algorithm

The bootblock checksum uses additive carry wraparound such that all 256 longwords of the bootblock sum to $FFFFFFFF:

```
1. Set checksum field at offset $04 to 0
2. Initialize sum = 0
3. For each longword L in the 1024-byte bootblock (256 longwords):
   a. prevsum = sum
   b. sum = sum + L
   c. if (sum < prevsum) sum = sum + 1    ; add carry
4. checksum = ~sum (bitwise NOT)
5. Store checksum at offset $04
```

In 68000 assembly:
```
    lea     bootblock(pc),a0
    clr.l   4(a0)           ; clear checksum field
    moveq   #0,d0           ; sum
    move.w  #255,d1         ; 256 longwords - 1
.loop:
    add.l   (a0)+,d0
    bcc.s   .nocarry
    addq.l  #1,d0           ; wrap carry
.nocarry:
    dbf     d1,.loop
    not.l   d0              ; complement
    move.l  d0,checksum     ; store at offset 4
```

### 2.4 Boot Sequence

1. ROM reads first 2 sectors (1024 bytes) from track 0 into allocated memory
2. Validates DiskType starts with "DOS"
3. Validates checksum
4. If valid, jumps to offset $0C (byte 12) of the loaded bootblock

### 2.5 Register State on Bootblock Entry

| Register | Contents |
|----------|----------|
| A1 | Open trackdisk.device IOStdReq pointer |
| A6 | ExecBase (SysBase) |

The bootblock code:
- MUST be fully position-independent (loaded at arbitrary address)
- May use the IOStdReq in A1 for disk I/O but must not deallocate it
- May call exec.library functions via A6
- May allocate memory and load additional code from disk

### 2.6 Bootblock Return Convention

| Register | Meaning |
|----------|---------|
| D0 | 0 = success, non-zero = failure (triggers Alert and reboot) |
| A0 | Entry point address to jump to (only used if D0 = 0) |

After the bootblock returns with D0=0:
1. System frees the bootblock memory
2. System frees the boot picture memory
3. System closes the trackdisk.device IORequest
4. System jumps to address in A0

### 2.7 trackdisk.device I/O from Bootblock

The IOStdReq in A1 can be used directly for disk reads:

```
    move.l  a1,a5               ; save IORequest
    ; Set up read command
    move.w  #CMD_READ,IO_COMMAND(a5)
    move.l  #destination,IO_DATA(a5)
    move.l  #byte_count,IO_LENGTH(a5)
    move.l  #disk_offset,IO_OFFSET(a5)   ; byte offset on disk
    move.l  a5,a1
    jsr     _LVODoIO(a6)        ; synchronous I/O
```

Disk offset = (track * 11 * 512) + (sector * 512) for DD disks.

### 2.8 Physical Floppy Layout

- 3.5" DD disk: 80 cylinders, 2 sides = 160 tracks
- 11 sectors per track (no inter-sector gaps, Amiga custom format)
- 512 bytes per sector
- Total capacity: 160 * 11 * 512 = 901,120 bytes (880 KB)

MFM sector structure:
```
4 bytes:  Sync ($00, $00, $A1, $A1)
4 bytes:  Format/track/sector/offset info
16 bytes: OS recovery data
4 bytes:  Header checksum
4 bytes:  Data checksum
512 bytes: Sector data
```

---

## 3. Compressed Executable Formats

### 3.1 PowerPacker (PP20)

**Magic**: "PP20" (4 ASCII bytes at offset 0)
**Encrypted variant**: "PX20"
**LoadSeg variant**: "PPLS"

#### File Structure

```
Offset  Size    Field
------  ------  -----
$00     4 bytes "PP20" signature
$04     4 bytes Efficiency table (4 bytes, determines compression level)
$08     varies  Compressed data (decompresses backwards from end)
EOF-4   4 bytes Footer: bits 31-8 = uncompressed size (24-bit), bits 7-0 = unused bits count
```

#### Efficiency Table Values

| Bytes | Compression Level |
|-------|------------------|
| $09090909 | Fast |
| $090A0A0A | Mediocre |
| $090A0B0B | Good |
| $090A0C0C | Very Good |
| $090A0C0D | Best |

Each byte represents the bit length for encoding offsets at different sequence lengths.

#### Decompression

Decompression proceeds **backwards** from the end of compressed data toward the beginning:
- Control bit 0: Literal bytes mode (read 2-bit length, copy raw bytes)
- Control bit 1: Sequence/copy mode (read 2-bit length indicator, use efficiency table for offset bit length)
- Special case length=3 in literal mode: accumulate additional 2-bit chunks
- Special case length=5 in copy mode: 7-bit vs 1-bit offset selection with variable extension

### 3.2 File Imploder (IMP!)

**Magic**: "IMP!" (4 ASCII bytes at offset 0)

Games commonly re-encoded the magic to avoid detection:
- "ATN!" - Team 17 games
- "BDPI" - Dizzy's Excellent Adventures
- "CHFI" - Dizzy's Excellent Adventures (alternate)
- "EDAM" - Indy Heat
- "M.H." - Georg Glaxo
- "RDC9" - Telekommando 2

Four decrunch variants:
1. **Normal**: Scatter-decrunches into empty hunks matching original hunk configuration; crunched data appended as extra hunk, freed after decrunch
2. **Pure**: Same as Normal but operates within Forbid/Permit pair
3. **Library**: No embedded decrunch code; opens explode.library from disk
4. **Overlayed**: For programs with overlay hunks; adjusts overlay offset table

### 3.3 Crunch-Mania (CrM!)

| Magic | Variant |
|-------|---------|
| "CrM!" | Normal mode |
| "Crm!" | Normal, sample-optimized |
| "CrM2" | LZ-H mode |
| "Crm2" | LZ-H, sample-optimized |
| "crM!" | Normal, encrypted |
| "crm!" | Normal, sample, encrypted |
| "crM2" | LZ-H, encrypted |
| "crm2" | LZ-H, sample, encrypted |

### 3.4 Other Notable Cruncher Signatures

| Magic (offset 0) | Cruncher |
|-------------------|----------|
| "RNC",$01 | Pro-Pack Method 1 (Rob Northen) |
| "RNC",$02 | Pro-Pack Method 2 |
| "ICE!" | Pack-Ice 2.31-2.40 |
| "Ice!" | Pack-Ice 2.11-2.20 |
| "S404" | StoneCracker 4.10.x |
| "S403" | StoneCracker 4.02a |
| "S401" | StoneCracker 4.01 |
| "S310" | StoneCracker 3.10 |
| "S300" | StoneCracker 3.00 |
| "TPWM" | Turbo Packer |
| "FIRE" | Pack-Fire 2.01 |
| "LH" | P-Compress |
| "FAST" | FAST3/FAST4 |
| "BHC3" | Blue House Cruncher |
| "VDCO" | Virtual Dreams Cruncher |
| "XPKF" | XPK library system |
| "ATM5" | Atomik Cruncher 3.5-3.6 |
| "ATOM" | Atomik Cruncher 3.3 |

StoneCracker 2.70-2.81 uses efficiency bytes at offset 3: $08-$0E.
StoneCracker 2.92/2.99 uses 4-byte efficiency tables at offset 0: $08090A08 through $08090A0E.

### 3.5 Common Re-encoded Signatures

Many games re-encode the cruncher magic to prevent easy identification/decrunching:

| Apparent Magic | Original Format | Game/Source |
|----------------|----------------|-------------|
| "ATN!" | IMP! | Team 17 games |
| "FUCK" | PP20 (encoded) | Arabian Nights |
| "CHFC" | PP20 | Sky High Stuntman |
| "----" | PP20 | Karamalz Cup |
| "-AD-" | CrM! | Arise |
| "MICK" | Ice! | Oscar ECS |
| "TSM!" | Ice! | Oscar AGA / Trolls / Elvira |
| "FORM" | CrM2 | Various |
| "PACK" | PP20 or CrM! | Various |
| "PaCK" | CrM! | Stardust |
| "DCS!" | CrM! | Dual Crew Shining |
| "GC!",$02 | RNC | Amiga Power coverdisks |
| "CRND" | ByteKiller | X-Out, Killing Game Show |

Some crunchers place their ID at EOF instead of offset 0:
- "Ice!" at EOF: Pack-Ice 1.13
- "data" at EOF: ByteKiller Pro 1.0
- "MARC" at EOF: Mercenary III, Flimbo's Quest (ByteKiller)
- "*FUNGUS*" at EOF: Switchblade, Zool, Elf

### 3.6 XPK Library System

**Magic**: "XPKF" (4 ASCII bytes)

XPK is a standardized compression framework with pluggable sub-libraries:
- SQSH: LZ + 8-bit delta (optimized for samples/modules)
- NUKE: Optimized LZ77
- And many others

The XPKF header identifies which sub-library was used for compression.

### 3.7 ByteKiller Format

ByteKiller and ByteKiller Pro are common in games from the late 1980s. The format has no standard magic -- games use custom identifiers. Some store the header at the start of the file, others at the end. Data may be stored forwards or backwards. Common identifiers include "CRND", "CRUN", "ARP3", "ARPF", "xVdg".

---

## 4. WHDLoad Slave Format

WHDLoad is a modern (1996+) system for running old games/demos from hard disk. The slave file is a standard Amiga hunk executable with a specific header structure at the start of its code section.

### 4.1 Slave Header Structure

The slave header begins at offset 0 of the first code hunk's data:

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 0 | 4 | ws_Security | `moveq #-1,d0` + `rts` ($70FF,$4E75) -- returns -1 if run directly |
| 4 | 8 | ws_ID | "WHDLOADS" (8 ASCII bytes) |
| 12 | 2 | ws_Version | Required WHDLoad version (WORD) |
| 14 | 2 | ws_Flags | Configuration flags (WORD) |
| 16 | 4 | ws_BaseMemSize | Required base memory size (ULONG) |
| 20 | 4 | ws_ExecInstall | Must be 0 (ULONG) |
| 24 | 2 | ws_GameLoader | Relative pointer to loader entry point (WORD, base-relative) |
| 26 | 2 | ws_CurrentDir | Relative pointer to data directory name (WORD, 0=none) |
| 28 | 2 | ws_DontCache | Relative pointer to no-cache pattern (WORD, 0=none) |

Version 4+ additions:

| 30 | 1 | ws_keydebug | Raw key code for debug exit (BYTE) |
| 31 | 1 | ws_keyexit | Raw key code for normal exit (BYTE, typically $59=F10) |

Version 8+ additions:

| 32 | 4 | ws_ExpMem | Expansion memory size/location (ULONG) |

Version 10+ additions:

| 36 | 2 | ws_name | Relative pointer to program name string (WORD) |
| 38 | 2 | ws_copy | Relative pointer to copyright string (WORD) |
| 40 | 2 | ws_info | Relative pointer to info string (WORD) |

Version 16+ additions:

| 42 | 2 | ws_kickname | Relative pointer to Kickstart image filename (WORD) |
| 44 | 4 | ws_kicksize | Expected Kickstart image size (ULONG) |
| 48 | 2 | ws_kickcrc | Expected CRC16 of Kickstart image (WORD) |

Version 17+ additions:

| 50 | 2 | ws_config | Relative pointer to splash config string (WORD) |

### 4.2 Slave Identification

A WHDLoad slave can be identified by:
1. It is a valid Amiga hunk executable (starts with $3F3)
2. The first code hunk's data starts with $70FF4E75 (moveq #-1,d0 / rts)
3. Bytes 4-11 of the code data read "WHDLOADS"

All relative pointers (ws_GameLoader, ws_name, etc.) are WORD offsets from the start of the slave header (offset 0 of the code hunk data).

### 4.3 Common Flag Values (ws_Flags)

| Flag | Description |
|------|-------------|
| WHDLF_NoError | Don't display error requesters |
| WHDLF_ClearMem | Clear all base memory before loading |
| WHDLF_EmulTrap | Emulate TRAP instructions |
| WHDLF_NoKbd | Don't install keyboard handler |

---

## Sources

### Hunk Format
- [Amiga Development Wiki - Hunk File Format](http://amiga-dev.wikidot.com/file-format:hunk)
- [HandWiki - Amiga Hunk](https://handwiki.org/wiki/Amiga_Hunk)
- [d0.se - doshunks.h](https://d0.se/include/dos/doshunks.h)
- [Amiga Developer Docs - doshunks.h](http://amigadev.elowar.com/read/ADCD_2.1/Includes_and_Autodocs_2._guide/node0065.html)
- [Amiga Developer Docs - doshunks.i](https://amigadev.elowar.com/read/ADCD_2.1/Includes_and_Autodocs_2._guide/node0069.html)
- [Mark Wrobel - Amiga Machine Code Detour](https://www.markwrobel.dk/post/amiga-machine-code-detour-reverse-engineering/)
- [Ambermoon Hunks Documentation](https://github.com/Pyrdacor/Ambermoon/blob/master/Files/Hunks.md)
- [AmigaHunkParser (C parser)](https://github.com/emoon/AmigaHunkParser)
- [Amiga Overlay Format](http://megaburken.net/~patrik/Overlay/Overlay.txt)

### Bootblock Format
- [AmigaOS Wiki - Floppy Boot Process](https://wiki.amigaos.net/wiki/Amiga_Floppy_Boot_Process_and_Physical_Layout)
- [Amiga RKM Devices - Bootstrap Booting](http://amigadev.elowar.com/read/ADCD_2.1/Devices_Manual_guide/node007D.html)
- [Amiga RKM Devices - Appendix C](https://amigadev.elowar.com/read/ADCD_2.1/Devices_Manual_guide/node015A.html)
- [Nameless Algorithm - Amiga Bootblock](https://namelessalgorithm.com/amiga/blog/bootblock/)
- [ADFlib - ADF Info](https://github.com/adflib/ADFlib/blob/master/doc/FAQ/adf_info_V0_9.txt)

### Compression Formats
- [PowerPacker Decompiled Source](https://github.com/khval/powerpacker.library)
- [PowerPacker Decrunch (C++)](https://github.com/ipr/PowerPacker-decrunch)
- [QuickBMS PP20 Implementation](https://github.com/mistydemeo/quickbms/blob/master/compression/PP20.cpp)
- [Amiga-Stuff Cruncher ID List](https://www.amiga-stuff.com/crunchers-id.html)
- [Exotica - Imploder File Formats](https://www.exotica.org.uk/wiki/Imploder_file_formats)
- [Amiga Development Wiki - Unpacking](http://amiga-dev.wikidot.com/technique:unpacking)

### WHDLoad
- [WHDLoad Programming Guide](https://www.whdload.de/docs/en/howto.html)
- [WHDLoad Resload API](https://whdload.de/docs/autodoc.html)
- [Ghidra WHDLoad Loader (header structure)](https://github.com/apparentlymart/ghidra-amiga-whdload)
- [WHDLoad Slave Patches (examples)](https://github.com/MK1Roxxor/WHDLoad_Patches)
- [WHDLoad Slave Parser](https://github.com/osvaldolove/whdload-slave)
