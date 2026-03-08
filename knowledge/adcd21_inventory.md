# Amiga Developer CD v2.1 — Inventory & Status

Mounted at: `D:/`

## NDK/ — Native Developer Kits

| Path | Description | Status |
|------|-------------|--------|
| `NDK/NDK_1.3/` | NDK 1.3 — includes (C/asm headers), autodocs | Superseded by 3.1 parse |
| `NDK/NDK_2.0/` | NDK 2.0 — includes, FD, autodocs | Not explored |
| `NDK/NDK_3.1/` | NDK 3.1 — FD files, autodocs, includes | **Parsed** → `amiga_os_reference.json` (1114 functions, 43 libs, 150 structs, 2078 constants) |
| `NDK/NDK_3.5/` | NDK 3.5 — docs, examples, includes, tools, tutorials | Not explored — may have new libs (Reaction, etc.) |
| `NDK/DEVELOPER_KITS` | Index/readme for NDK section | Not read |

### NDK potential next steps
- **NDK 3.5**: Has tutorials, examples, and new BOOPSI gadget classes (Reaction framework). Could parse for 3.5-era additions.
- **NDK 2.0**: Could diff FD files against 3.1 to find version markers lost in upgrade (1.2 vs 1.3 function differentiation).

## EXTRAS/ — Supplementary Developer Material

| Path | Description | Status |
|------|-------------|--------|
| `EXTRAS/DEVELOPMENT/OS_CHANGES/` | API change logs (1.3→2.04, 2.04→2.1, 2.1→3.0, 3.0→3.1) | **Parsed** → version tags in `amiga_os_reference.json` (624 functions tagged) |
| `EXTRAS/IFF/IFF_FORMS/` | IFF format specifications (ILBM, 8SVX, ANIM, etc.) | **Parsed** → `amiga_iff_formats.json` (4 FORMs, 20 chunks, 60 fields, 134 registry entries) |
| `EXTRAS/IFF/OLD_IFF_PACKAGES/` | Original EA IFF 85 specs (ILBM, 8SVX, SMUS, FTXT) | **Read** — used as source for ILBM/8SVX struct definitions |
| `EXTRAS/IFF/TEST_FILES/` | Sample IFF files | Low priority |
| `EXTRAS/BOOPSI/GI1/` | BOOPSI gadget examples | Low priority |
| `EXTRAS/BOOPSI/LED_IC/` | LED image class example | Low priority |
| `EXTRAS/MIDI/` | MIDI specifications/tools | Low priority |
| `EXTRAS/NETWORKING/` | Network development | Low priority |
| `EXTRAS/TOOLS/` | Developer tools | Not explored |

### EXTRAS potential next steps
- ~~**IFF_FORMS**: Parse IFF chunk specifications~~ — **Done**: ILBM, 8SVX, ANIM, ACBM parsed with full struct definitions.

## REFERENCE/ — ROM Kernel Manuals & Documentation

| Path | Description | Status |
|------|-------------|--------|
| `REFERENCE/ROM_KERNEL_MANUALS/HARDWARE_MANUAL` | Hardware Reference Manual (AmigaGuide) | **Parsed** (via HTML) → `amiga_hw_registers.json` (245 regs, 104 with bits) |
| `REFERENCE/ROM_KERNEL_MANUALS/LIBRARIES_MANUAL` | Libraries & Devices Manual (AmigaGuide) | Not explored — deeper OS programming reference |
| `REFERENCE/ROM_KERNEL_MANUALS/DEVICES_MANUAL` | Devices Manual (AmigaGuide) | Not explored |
| `REFERENCE/ROM_KERNEL_MANUALS/AUTODOCS/` | Autodoc files | Superseded by NDK 3.1 parse |
| `REFERENCE/ROM_KERNEL_MANUALS/FD/` | FD files | Superseded by NDK 3.1 parse |
| `REFERENCE/ROM_KERNEL_MANUALS/INCLUDES/` | Include files | Superseded by NDK 3.1 parse |
| `REFERENCE/ROM_KERNEL_MANUALS/TEXT_AUTODOCS/` | Plain text autodocs | Superseded |
| `REFERENCE/ROM_KERNEL_MANUALS/REFERENCES/` | Additional references | Not explored |
| `REFERENCE/ROM_KERNEL_MANUALS/LIB_EXAMPLES/` | Library programming examples | Low priority |
| `REFERENCE/ROM_KERNEL_MANUALS/HARD_EXAMPLES/` | Hardware programming examples | Low priority |
| `REFERENCE/HTML/HARDWARE_MANUAL.HTML` | HTML version of HW manual | **Source for our parser** (`tmp/Hardware_Manual.html`) |
| `REFERENCE/HTML/LIBRARIES_MANUAL.HTML` | HTML version of Libraries manual | Not explored |
| `REFERENCE/HTML/DEVICES_MANUAL.HTML` | HTML version of Devices manual | Not explored |
| `REFERENCE/HTML/I_AND_A_3.5.HTML` | Includes & Autodocs 3.5 (HTML) | Not explored — could supplement NDK 3.5 |
| `REFERENCE/HTML/I_AND_A_2.0.HTML` | Includes & Autodocs 2.0 (HTML) | Low priority |
| `REFERENCE/HTML/AMIGAMAIL_VOL2.HTML` | Amiga Mail Volume 2 (technical articles) | Not explored |
| `REFERENCE/INCLUDES_AND_AUTODOCS_3.5/` | Full 3.5 autodocs + includes (AmigaGuide) | Not explored — **high value** for 3.5 API coverage |
| `REFERENCE/AMIGA_MAIL_VOL1/` | Amiga Mail Volume 1 (technical articles) | Not explored |
| `REFERENCE/AMIGA_MAIL_VOL2/` | Amiga Mail Volume 2 (technical articles) | Not explored |
| `REFERENCE/DEVCON/` | Developer Conference proceedings (1988-1993) | Not explored — historical, possibly useful techniques |

### REFERENCE potential next steps
- **INCLUDES_AND_AUTODOCS_3.5**: Parse for additional structs, constants, and new library APIs not in NDK 3.1 (Reaction framework, new gadget classes).
- **LIBRARIES_MANUAL / DEVICES_MANUAL**: Prose documentation with deeper explanations of how libraries work — useful for understanding calling conventions and behavior, but not easily machine-parseable.

## DEVINFO/ — Developer Information

| Path | Description | Status |
|------|-------------|--------|
| `DEVINFO/BLACKLIST/` | Software compatibility blacklist | Not explored |
| `DEVINFO/DEVICEDEVELOPMENT/` | Device driver development | Low priority |
| `DEVINFO/EXEC_AND_POWERPC/` | Exec + PowerPC transition docs | Low priority |
| `DEVINFO/INTUITION/` | Intuition programming notes | Not explored |
| `DEVINFO/STYLE/` | UI style guide | Low priority |
| `DEVINFO/TRACKDISK64/` | 64-bit trackdisk commands for >4GB devices (1996) | Read — not relevant to game reversing (floppy/CD era) |
| `DEVINFO/NETWORKING/` | Network stack docs | Low priority |
| `DEVINFO/REQUIREDREADING` | Essential developer reading list | Not read |
| `DEVINFO/ROMKERNELMANUALS` | ROM Kernel Manual info/errata? | Not read |

### DEVINFO potential next steps
- **REQUIREDREADING / ROMKERNELMANUALS**: Quick reads to check for errata or corrections to parsed data.
- **TRACKDISK64**: May document extended disk access relevant to HD/CD games.

## CD32/ — CD32 Development

| Path | Description | Status |
|------|-------------|--------|
| `CD32/BUILDCD/` | CD-ROM mastering tools | Low priority |
| `CD32/CD32-TOOLS/` | CD32-specific tools | Not explored |
| `CD32/CD32_SUPPORT/` | CD32 support libraries/docs | Not explored — may have Akiko chip docs |
| `CD32/XL_TOOLKIT_1.1/` | CDXL animation toolkit | Not explored |
| `CD32/ISO9660TOOLS_V1.04/` | ISO9660 filesystem tools | Low priority |
| `CD32/XLEXAMPLE/` | CDXL examples | Low priority |

### CD32 potential next steps
- **CD32_SUPPORT**: Akiko chip register documentation would be valuable for CD32 game reversing.

## CDTV/ — CDTV Development

| Path | Description | Status |
|------|-------------|--------|
| `CDTV/CDTVTOOLS-11/` | CDTV tools v1.1 | Low priority |
| `CDTV/CDTVTOOLS-20/` | CDTV tools v2.0 | Low priority |
| `CDTV/CDXLTOOLS*` | CDXL animation tools (3 packages) | Low priority |
| `CDTV/ISODEVPACK-41/` | ISO development package | Low priority |

## CONTRIBUTIONS/ — Third-Party Developer Contributions

| Path | Description | Status |
|------|-------------|--------|
| `CONTRIBUTIONS/OLAF_BARTHEL/` | Olaf Barthel — likely bsdsocket.library, serial | Not explored |
| `CONTRIBUTIONS/RALPH_BABEL/` | Ralph Babel — Guru Book author, Amiga internals | Not explored |
| `CONTRIBUTIONS/HEINZ_WROBEL/` | Heinz Wrobel — system internals | Not explored |
| `CONTRIBUTIONS/THOMAS_RICHTER/` | Thomas Richter — datatypes, graphics | Not explored |
| Others | Various third-party contributions | Not explored |

## Other Top-Level Files

| Path | Description | Status |
|------|-------------|--------|
| `GUIDE/` | ~500+ AmigaGuide files — developer articles index | Not explored |
| `INTERNATIONAL/` | Localization resources | Low priority |
| `EA/ST/` | Electronic Arts? Unclear content | Not explored |
| `ALPHA.GUIDE` | CD table of contents | Not read |
| `CD-ROM.GUIDE` | CD-ROM development guide | Not read |

---

## Priority Queue (for reversing knowledge base)

1. ~~**IFF format specs**~~ — **Done**
2. **NDK 3.5 includes/autodocs** (`REFERENCE/INCLUDES_AND_AUTODOCS_3.5/` or `NDK/NDK_3.5/`) — newer API coverage
3. **CD32 support** (`CD32/CD32_SUPPORT/`) — Akiko chip, CD32-specific hardware
4. ~~**TRACKDISK64**~~ — not relevant (>4GB device support, post-game era)
5. **Amiga Mail** (`REFERENCE/AMIGA_MAIL_*/`) — technical articles with programming patterns
