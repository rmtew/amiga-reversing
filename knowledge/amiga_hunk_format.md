# Amiga Hunk Binary Format

All data is **big-endian** (Motorola byte order).

## File Types

| Magic | Hex | Type | Description |
|-------|-----|------|-------------|
| HUNK_HEADER | $3F3 | Executable | Loadable by AmigaDOS (TYPE_LOADSEG) |
| HUNK_UNIT | $3E7 | Object | Linkable object file (TYPE_UNIT) |
| HUNK_LIB | $3FA | Library | Link library container |

## Hunk Type IDs

| Name | Dec | Hex | Description |
|------|-----|-----|-------------|
| HUNK_UNIT | 999 | $3E7 | Object file header |
| HUNK_NAME | 1000 | $3E8 | Section name |
| HUNK_CODE | 1001 | $3E9 | Executable code |
| HUNK_DATA | 1002 | $3EA | Initialized data |
| HUNK_BSS | 1003 | $3EB | Uninitialized data (zero-filled) |
| HUNK_RELOC32 | 1004 | $3EC | 32-bit absolute relocations |
| HUNK_RELOC16 | 1005 | $3ED | 16-bit PC-relative relocations |
| HUNK_RELOC8 | 1006 | $3EE | 8-bit PC-relative relocations |
| HUNK_EXT | 1007 | $3EF | External symbol defs/refs |
| HUNK_SYMBOL | 1008 | $3F0 | Symbol table (debug) |
| HUNK_DEBUG | 1009 | $3F1 | Debug information |
| HUNK_END | 1010 | $3F2 | Block terminator |
| HUNK_HEADER | 1011 | $3F3 | Executable header |
| HUNK_OVERLAY | 1013 | $3F5 | Overlay table |
| HUNK_BREAK | 1014 | $3F6 | Overlay terminator |
| HUNK_DREL32 | 1015 | $3F7 | 32-bit data-relative reloc |
| HUNK_DREL16 | 1016 | $3F8 | 16-bit data-relative reloc |
| HUNK_DREL8 | 1017 | $3F9 | 8-bit data-relative reloc |
| HUNK_LIB | 1018 | $3FA | Library container |
| HUNK_INDEX | 1019 | $3FB | Library index |
| HUNK_RELOC32SHORT | 1020 | $3FC | Compact 32-bit reloc (16-bit offsets) |
| HUNK_RELRELOC32 | 1021 | $3FD | PC-relative 32-bit reloc |
| HUNK_ABSRELOC16 | 1022 | $3FE | Absolute 16-bit reloc |

## Memory Flags (bits 30-31 of size longwords)

| Bits 31:30 | Hex Mask | Meaning |
|------------|----------|---------|
| 00 | $00000000 | Any memory |
| 01 | $40000000 | Chip RAM (MEMF_CHIP) |
| 10 | $80000000 | Fast RAM (MEMF_FAST) |
| 11 | $C0000000 | Extended: next ULONG has exec memory attrs |

Size in longwords = `value & 0x3FFFFFFF`; bytes = that × 4.

Hunk type ID = `value & 0x1FFFFFFF` (mask off flag bits).

## String Encoding (BSTR)

All strings are longword-aligned:
```
ULONG  length_in_longwords
BYTE[] chars[length * 4]   (NUL-padded to 4-byte boundary)
```
Length 0 = empty/terminator.

Example: "HELLO" → length=2, data="HELLO\0\0\0"

## HUNK_HEADER (Executable)

```
ULONG   $000003F3           ; magic
; Resident library names (usually just ULONG 0):
ULONG   name_len             ; 0 = end of list
[BYTE[] name_data]           ; if name_len > 0
...                          ; repeat until name_len == 0
ULONG   table_size           ; total number of hunks
ULONG   first_hunk           ; first slot (usually 0)
ULONG   last_hunk            ; last slot (= table_size - 1)
ULONG[] sizes[table_size]    ; allocation sizes (with mem flags in bits 30-31)
; If bits 30-31 == 11, read additional ULONG for extended mem attrs
```

## HUNK_CODE / HUNK_DATA

```
ULONG   type                 ; $3E9 (CODE) or $3EA (DATA), masked
ULONG   num_longs            ; size in longwords
BYTE[]  data[num_longs * 4]  ; actual content
```

Followed by zero or more: RELOC, SYMBOL, DEBUG hunks. Terminated by HUNK_END.

## HUNK_BSS

```
ULONG   $000003EB
ULONG   num_longs            ; allocation size (no data in file)
```

## HUNK_RELOC32

```
ULONG   $000003EC
; Repeat:
ULONG   num_offsets           ; 0 = end
ULONG   target_hunk           ; which hunk to relocate against
ULONG[] offsets[num_offsets]   ; byte offsets to patch in current hunk
; ...until num_offsets == 0
```

Processing: at each offset, add `base_address[target_hunk]` to the 32-bit value.

## HUNK_RELOC32SHORT (Compact)

```
ULONG   $000003FC
; Repeat:
UWORD   num_offsets           ; 0 = end
UWORD   target_hunk
UWORD[] offsets[num_offsets]
; ...until num_offsets == 0
; UWORD padding if not longword-aligned
```

## HUNK_SYMBOL

```
ULONG   $000003F0
; Repeat:
ULONG   name_len              ; 0 = end
BYTE[]  name[name_len * 4]    ; NUL-padded
ULONG   value                 ; offset within hunk
; ...until name_len == 0
```

## HUNK_EXT

```
ULONG   $000003EF
; Repeat:
ULONG   type_and_len          ; bits 31-24 = sub-type, bits 23-0 = name_len
                               ; 0 = terminator
BYTE[]  name[name_len * 4]
; Then depends on sub-type:
```

### EXT Sub-Types

| Name | Value | Category | Extra Fields |
|------|-------|----------|-------------|
| EXT_SYMB | 0 | Def | value |
| EXT_DEF | 1 | Def (reloc) | value |
| EXT_ABS | 2 | Def (absolute) | value |
| EXT_REF32 | 129/$81 | Ref (32-bit) | ref_count + offsets |
| EXT_COMMON | 130/$82 | Ref (32-bit common) | common_size + ref_count + offsets |
| EXT_REF16 | 131/$83 | Ref (16-bit) | ref_count + offsets |
| EXT_REF8 | 132/$84 | Ref (8-bit) | ref_count + offsets |
| EXT_DEXT32 | 133/$85 | Ref (data-rel 32) | ref_count + offsets |
| EXT_DEXT16 | 134/$86 | Ref (data-rel 16) | ref_count + offsets |
| EXT_DEXT8 | 135/$87 | Ref (data-rel 8) | ref_count + offsets |
| EXT_RELREF32 | 136/$88 | Ref (PC-rel 32) | ref_count + offsets |
| EXT_RELCOMMON | 137/$89 | Ref (PC-rel common) | common_size + ref_count + offsets |
| EXT_ABSREF16 | 138/$8A | Ref (abs 16) | ref_count + offsets |
| EXT_ABSREF8 | 139/$8B | Ref (abs 8) | ref_count + offsets |

Definitions (sub-type < 128): name + ULONG value
References (sub-type >= 128): name + ULONG ref_count + ULONG[] offsets
Common refs ($82, $89): name + ULONG common_size + ULONG ref_count + ULONG[] offsets

## HUNK_DEBUG

```
ULONG   $000003F1
ULONG   num_longs             ; size of debug data
BYTE[]  data[num_longs * 4]
```

LINE debug format: starts with "LINE" ($4C494E45), then BSTR filename, then offset/line pairs.

## HUNK_END

```
ULONG   $000003F2
```

## HUNK_OVERLAY

```
ULONG   $000003F5
ULONG   table_size            ; in longwords
BYTE[]  overlay_data[(table_size + 1) * 4]
```

## File Layout (Executable)

```
HUNK_HEADER
  lib_names, table_size, first, last, sizes[]
For each hunk:
  HUNK_CODE | HUNK_DATA | HUNK_BSS
    [HUNK_RELOC32 ...]
    [HUNK_SYMBOL]
    [HUNK_DEBUG]
  HUNK_END
[HUNK_OVERLAY ...]
```

## File Layout (Object)

```
HUNK_UNIT
  unit_name (BSTR)
For each section:
  [HUNK_NAME]
  HUNK_CODE | HUNK_DATA | HUNK_BSS
    [HUNK_RELOC32 ...]
    [HUNK_EXT]
    [HUNK_SYMBOL]
    [HUNK_DEBUG]
  HUNK_END
```
