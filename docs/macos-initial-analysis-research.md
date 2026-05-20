# Classic Mac OS Initial Analysis Research

Status: research baseline for Proposal 012.

## Conclusion

Use two different first targets:

- Semantic source baseline: `MPW-GM/MPW/Examples/AExamples/Sample`.
- Real executable/container baseline: `MPW-GM/MPW/Tools/Asm`.

`Sample` is the best source-level fixture because it is a complete small
application with assembly source, shared include data, resource scripts, build
recipe, menu/window/event/resource use, segment directives, and Toolbox calls.
`MPW/Tools/Asm` remains the best real binary fixture because it already proves
HFS file metadata, resource-fork parsing, `CODE 0`, and nonzero `CODE`
segments on a real MPW tool.

Use `Memory` as the second semantic fixture for compact desk accessory and File
Manager parameter-block coverage. Use `Count` as the third fixture for MPW tool
runtime and shell I/O coverage.

## Source Set

Local source files inspected:

```text
tmp/MPW-GM-extracted/data/MPW-GM/MPW/Examples/AExamples/
  Instructions
  MakeFile
  Count.a
  Count.r
  FStubs.a
  MemorySrc.a
  Sample.a
  Sample.inc1.a
  SampleMisc.a
  Sample.h
  Sample.r
  Sample.make

ext/macos_includes/mpw_gm/Interfaces/AIncludes/
  Files.a
  Quickdraw.a
  Resources.a
  SegLoad.a
  Traps.a

ext/docs_macos/
  Inside_Macintosh_Volume_II_1985.md
  Inside_Macintosh_Volume_IV_1986.md
  MPW_and_Assembly_Language_Programming_for_the_Macintosh_1987.md
  Programming_With_Macintosh_Programmers_Workshop_1987.md
```

The extracted `AExamples` directory contains source and resource scripts, not
built example binaries. That means the first source-level analysis can be
validated against source semantics, while binary container parsing should keep
using the existing `MPW/Tools/Asm` resource fork.

## Ranked Fixture Candidates

1. `Sample`

Best first semantic fixture. It is explicitly described by the bundled
instructions as a simple MultiFinder-aware application, with source in
`Sample.a`, `SampleMisc.a`, `Sample.inc1.a`, resources in `Sample.r` and
`Sample.h`, and build instructions in `Sample.make`
(`AExamples/Instructions`:72-79). It exercises:

```text
application build path
APPL file metadata
multiple source files
SEG directives and cross-segment calls
A5/global data
Toolbox manager initialization
event loop
WaitNextEvent fallback path
menus, windows, alerts, regions, cursor handling
Resource Manager calls
Rez-authored UI resources
SIZE/resource-based memory intent
```

Risk: it is larger than the other examples. Keep the first semantic smoke test
small: decode includes, segments, resource IDs, a selected call list, and a
selected routine such as `Initialize` or `GoGetRect`.

2. `Memory`

Best compact second fixture. The instructions classify it as a desk accessory
that displays application heap, system heap, and boot disk free space
(`AExamples/Instructions`:108-114). It exercises:

```text
DRVR build path
desk accessory entry table
Device Manager control/status/open/close shape
QuickDraw drawing calls
Memory Manager calls
File Manager parameter-block call PBHGetVInfoSync
driver-style no-normal-A5-globals constraint
```

Risk: desk accessories are not the same shape as applications. Treat it as a
focused supplement, not the first platform path.

3. `Count`

Best MPW tool/runtime fixture. The instructions classify it as an MPW tool and
name its source/resource files (`AExamples/Instructions`:91-97). The makefile
builds it as type `MPST`, creator `MPS `, links `Stubs.o`, `MacRuntime.o`,
`IntEnv.o`, `ToolLibs.o`, and `Interface.o`, then appends `Count.r`
(`AExamples/MakeFile`:13-28). It exercises:

```text
MPW tool file metadata
MPW shell command-line runtime
standard input/output/error conventions
runtime calls such as open/read/write/getchar/exit/signal
cmdo resource for command dialog metadata
```

Risk: it is MPW-shell-specific and less representative of ordinary Macintosh
applications. Use it for tool/runtime analysis after `Sample`.

4. `MPW/Tools/Asm`

Best real executable resource-fork fixture. It has known file type `MPST`,
creator `MPS `, data/resource forks, and 28 `CODE` resources recorded in
`ext/macos_tools/mpw_gm/asm_code_resources.json`.

Risk: it is too large and lacks source in the current tree. Use it to validate
container/CODE parsing and listing, not as the first semantic truth source.

## Build Model Findings

The MPW manual shows the basic source-to-application path:

```text
asm -p Coin.a
link -p Coin.a.o -o Coin
```

The same section explains that `asm` creates `.a.o` object output and `link`
turns object output into a standalone application
(`MPW_and_Assembly_Language_Programming_for_the_Macintosh_1987.md`, source
pages 38-39, lines 1827-1901). The link progress report includes segment and
jump-table counts (lines 1921-1958).

The bundled examples show three concrete build shapes:

```text
Sample:
  Asm -> .a.o objects
  Link -> application
  SetFile -> APPL/MOOS metadata
  Rez -append -> resources

Count:
  Asm -> Count.a.o and FStubs.a.o
  Link -t MPST -c 'MPS ' -> MPW tool
  Rez -append -> cmdo resource

Memory:
  Asm -> MemorySrc.a.o
  Link -da -t dfil -c movr -rt DRVR=12 -sg Memory -> desk accessory/driver
```

`Sample.make` lines 59-71 provide the clearest application build recipe.
`MakeFile` lines 13-35 provide the MPW tool and desk accessory recipes.

## File And Resource Structure Findings

The manuals support treating the resource fork as core platform structure, not
optional metadata:

- `Programming_With_Macintosh_Programmers_Workshop_1987.md`, source pages
  65-66, describes data and resource forks, resource type/id/name lookup, the
  resource map, and calls such as `GetResource`.
- The same manual source page 114 distinguishes `APPL`, `MPST`, and `DRVR`
  program locations and launch contexts.
- Source page 129 describes multiple `CODE` resources, segment names becoming
  `CODE` resource names, `CODE` resource 1 as `Main`, and `CODE` resource 0 as
  the jump-table initializer.
- `Inside_Macintosh_Volume_II_1985.md`, source pages 65-71, describes Segment
  Loader behavior, `UnloadSeg`, jump-table entries, `CODE 0`, and the `CODE 0`
  header fields.

Initial resource-script coverage should include:

```text
Sample.r:
  MBAR, MENU, ALRT, DITL, WIND, RECT, SIZE

Count.r:
  cmdo

Memory:
  DRVR created by Link recipe, not a separate Rez script in AExamples
```

## Sample Resource Linkage

`Sample` has enough resource/source cross-reference evidence to drive a useful
first UI view.

`Sample.r` declares:

```text
type 'RECT'                         Sample.r:59
resource 'MBAR' (rMenuBar)          Sample.r:66
resource 'MENU' (mApple)            Sample.r:71
resource 'MENU' (mFile)             Sample.r:83
resource 'MENU' (mEdit)             Sample.r:115
resource 'MENU' (mLight)            Sample.r:135
resource 'ALRT' (rAboutAlert)       Sample.r:150
resource 'DITL' (rAboutAlert)       Sample.r:166
resource 'ALRT' (rUserAlert)        Sample.r:204
resource 'DITL' (rUserAlert)        Sample.r:221
resource 'WIND' (rWindow)           Sample.r:245
resource 'RECT' (rStopRect)         Sample.r:250
resource 'RECT' (rGoRect)           Sample.r:254
resource 'SIZE' (-1)                Sample.r:261
```

`Sample.h` defines the same public IDs for Rez/C-side source:

```text
rMenuBar=128, rAboutAlert=128, rUserAlert=129, rWindow=128
rStopRect=128, rGoRect=129
mApple=128, mFile=129, mEdit=130, mLight=131
iAbout=1, iQuit=12, iStop=1, iGo=2
kMinSize=23, kPrefSize=35
```

`Sample.inc1.a` defines the assembly-side names:

```text
rMenuBar=128, rUserAlert=129, rWindow=128, rAboutAlert=128
rStopRect=128, rGoRect=129
AppleMenu=128, FileMenu=129, EditMenu=130, LightMenu=131
AboutItem=1, QuitItem=12, StopItem=1, GoItem=2
MinHeap=21*1024, MinSpace=8*1024
```

Source call sites then use these IDs:

```text
Sample.a:339      _GetNewWindow with rWindow
Sample.a:348      _GetNewMBar with rMenuBar
Sample.a:364      GoGetRect with rStopRect
Sample.a:373      GoGetRect with rGoRect
Sample.a:581      _Alert with rAboutAlert
SampleMisc.a:259  _Alert with rUserAlert
SampleMisc.a:123  _GetResource with 'RECT' and caller-supplied ID
```

The first resource parser does not need full Rez semantics. It needs enough to
emit:

```text
resource type
resource id expression
resolved id when backed by Sample.h or Sample.inc1.a
resource attributes such as preload/purgeable
resource-to-source references
```

## Data Fork Findings

The HFS inventory shows several different "data" meanings. The importer and UI
should not treat every data fork as executable input.

For `AExamples`, the data fork is the useful source artifact:

```text
path                                  type  creator  data   resource
MPW/Examples/AExamples/Sample.a       TEXT  MPS      40288  430
MPW/Examples/AExamples/SampleMisc.a   TEXT  MPS      32361  430
MPW/Examples/AExamples/Sample.inc1.a  TEXT  MPS      11971  430
MPW/Examples/AExamples/Sample.r       TEXT  MPS       6283  430
MPW/Examples/AExamples/Sample.make    TEXT  MPS       2517  430
MPW/Examples/AExamples/Count.a        TEXT  MPS      15714  430
MPW/Examples/AExamples/MemorySrc.a    TEXT  MPS       8048  430
```

The 430-byte resource forks on these source files contain only two `MPSR`
resources in sampled files (`Sample.a` and `Sample.r`). Treat these as MPW
editor/resource metadata, not semantic source for the first pass. Preserve their
existence and hashes in provenance, but parse the data fork for source text.

For MPW tools, the executable code is resource-fork centric:

```text
MPW/Tools/Asm
  type: MPST
  creator: MPS
  data fork: 10752 bytes
  resource fork: 213850 bytes
  CODE resources: 28
```

The `Asm` data fork begins with table-like binary data and contains assembler
diagnostic strings such as invalid constant, invalid opcode, invalid register
list, and related messages. It should be preserved and rendered as a data/string
range, not treated as code. The `Asm` resource fork owns the `CODE 0` jump table
metadata and nonzero `CODE` segments.

For MPW object and library files, the data fork is likely the object/library
payload:

```text
type OBJ   object files
type XCOF  PowerPC-oriented object files
type stub  shared-library stubs
```

Object/library parsing is useful for future build provenance, but should not
block the first source rendering and CODE-resource listing work.

## Source Rendering Model

The first rendered source view should preserve MPW source structure rather than
flattening everything into one disassembly-like file.

Recommended project shape:

```text
Mac target
  Source Files
    Sample.a
      globals/data declarations
      segment Initialize
        Initialize PROC
      segment Main
        DoContentClick PROC
        DoUpdate PROC
        ...
    SampleMisc.a
      segment Initialize
        GoGetRect FUNC
      segment Main
        IsDAWindow FUNC
        IsAppWindow FUNC
        ...
    Sample.inc1.a
      macros
      equates
      RECORD layouts
    Sample.r
      resource declarations
    Sample.make
      build recipe
  Binary Containers
    MPW/Tools/Asm
      data fork
      resource fork
      CODE resources
```

For source files, render MPW directives as structural annotations:

```text
SEG 'Initialize'     -> starts or resumes source segment Initialize
SEG 'Main'           -> starts or resumes source segment Main
PROC/FUNC            -> routine boundary
EXPORT/IMPORT        -> cross-file or cross-segment symbol boundary
RECORD/WITH          -> structure/layout scope
OPWORD $Axxx         -> trap alias source in includes
```

The UI should allow at least these pivots:

```text
by source file
by segment name
by routine/function
by imported/exported symbol
by resource id/type
by generated trap/API fact
```

This gives porting users both the original source organization and the platform
semantics they need to compare with Amiga or Atari code.

## Segment Mapping Model

Segment mapping has two related but different views:

1. Source segment membership.
2. Linked `CODE` resource output.

Source membership is directly visible in MPW assembly. In `Sample.a` and
`SampleMisc.a`, `SEG 'Initialize'` and `SEG 'Main'` assign following routines to
those named segments. `Sample.a` also imports `_DataInit`, `Initialize`, and
other symbols from startup code. `MemorySrc.a` uses `MAIN`, because the desk
accessory is linked as `DRVR`, not as an ordinary segmented application.

Documentation connects source segments to linked resources:

- `Programming_With_Macintosh_Programmers_Workshop_1987.md`, source page 129,
  says segment names become `CODE` resource names generated by the MPW linker.
- The same page says `CODE` resource 1 is normally `Main`.
- `Inside_Macintosh_Volume_II_1985.md`, source pages 70-71, says `CODE 0`
  contains the jump table and application A5 size metadata.

For built applications, the intended mapping is:

```text
source SEG name
  -> linker segment name
  -> CODE resource name
  -> CODE resource id assigned by Link
  -> disassembly/code range
```

For the first implementation, this mapping should be represented as a partial
relation, not a guessed fact:

```text
source segment Main
  maps_to: CODE resource name Main
  evidence: MPW manual page 129
  status: expected_for_built_sample

MPW/Tools/Asm CODE 1 Main
  maps_to: binary CODE resource id 1 name Main
  evidence: inspected resource fork
  status: observed_binary
```

Do not infer that `Sample`'s exact source segments map to `MPW/Tools/Asm`
segments. They are different programs. Use `Sample` to define source rendering
and semantic analysis; use `Asm` to define executable container parsing.

## Call And Trap Findings

`Sample` gives broad Toolbox coverage. The first generated trap/API table
should be only large enough to annotate calls observed in the examples.
High-value calls from `Sample.a` and `SampleMisc.a` include:

```text
InitGraf, InitFonts, InitWindows, InitMenus, TEInit, InitDialogs, InitCursor
EventAvail, WaitNextEvent, GetNextEvent, SystemTask, SystemClick, SystemEdit
GetNewMBar, SetMenuBar, DrawMenuBar, MenuSelect, MenuKey, GetMenuHandle
GetNewWindow, FrontWindow, SelectWindow, DragWindow, BeginUpdate, EndUpdate
GetResource, Alert, OpenDeskAcc, CloseDeskAcc, ExitToShell, UnloadSeg
```

`MemorySrc.a` gives compact parameter-block and driver coverage:

```text
GetPort, SetPort, NewPtr, NewWindow, DisposeWindow, MaxMem, FreeMem
PBHGetVInfoSync, DisposePtr, NumToString, BeginUpdate, EndUpdate
```

`Count.a` gives MPW runtime/library calls rather than direct Toolbox focus:

```text
_RTInit, signal, exit, open, read, write, getchar, p2cstr, c2pstr
InitCursorCtl, RotateCursor, NumToString
```

The MPW includes already expose useful generated-KB input. Examples:

```text
Files.a:3671        _PBHGetVInfoSync: OPWORD $A207
Quickdraw.a:1380    _InitGraf:        OPWORD $A86E
Resources.a:425     _GetResource:     OPWORD $A9A0
SegLoad.a:134       _UnloadSeg:       OPWORD $A9F1
```

`Inside_Macintosh_Volume_IV_1986.md`, source pages 25-26, describes A-line
trap words, OS vs Toolbox trap word interpretation, and the role of bit 11.
That should be cited by the generated trap-word decoder.

## MPW Assembly Patterns To Recognize

The baseline renderer/analyzer should understand these MPW assembly constructs
well enough to avoid misrepresenting source:

```text
INCLUDE, IMPORT, EXPORT
PROC, FUNC, ENDP, ENDF
RECORD, ENDR, WITH
SEG
MAIN
STRING PASCAL
MACRO definitions and macro calls
OPWORD trap aliases from include files
A5-relative globals
A6 stack-frame records
Pascal stack calling pattern with caller parameters stripped by callee
```

These do not all need full assembler support initially. The first pass can
capture them as source annotations and metadata so rendered code explains what
is being seen.

## Initial Generated Tables

The first generated `src/generated/mac_os_*.c/.h` surface should be narrow:

```text
mac_os_resource_types:
  CODE, MBAR, MENU, ALRT, DITL, WIND, RECT, SIZE, cmdo, DRVR

mac_os_file_types:
  APPL, MPST, DRVR-related Link recipe metadata, creator codes seen in examples

mac_os_traps:
  trap name, trap word, family, source include path, prototype text when present

mac_os_call_patterns:
  stack-result space
  Pascal stack parameters
  A0 parameter-block result pattern
  handle result pattern
  no-return calls such as ExitToShell/exit

mac_os_segments:
  CODE 0 fields
  CODE 1 Main convention
  named segment to CODE resource name convention
```

The trap table can start from MPW AIncludes plus manual citations. Do not copy
the entire include set into runtime facts. Generate only facts consumed by the
baseline examples.

## Baseline Include Facts

The first generated metadata should come from MPW includes plus manual
citations, not from ad hoc renderer constants.

High-value records:

```text
MacTypes.a:
  Point: v@0, h@2, sizeof=4
  Rect: top@0, left@2, bottom@4, right@6, topLeft@0, botRight@4, sizeof=8

Events.a:
  EventRecord: what@0, message@2, when@6, where@10, modifiers@14, sizeof=16

Files.a:
  HVolumeParam: ioNamePtr@18, ioVAlBlkSiz@48, ioVFrBlk@62, sizeof=122

Quickdraw.a:
  QDGlobals: thePort@202, sizeof=206
  CurrentQDGlobals: biased so thePort is at offset 0 from A5-derived pointer

MacWindows.a:
  WindowRecord: windowKind@108, visible@110, refCon@152, sizeof=156

Devices.a:
  DCtlEntry: dCtlRefNum@24, dCtlWindow@30, dCtlDelay@34, dCtlEMask@36,
  dCtlMenu@38, sizeof=40

OSUtils.a:
  SysEnvRec: systemVersion@4, processor@6, hasColorQD@9, sysVRefNum@14,
  sizeof=16
```

High-value traps and call signatures observed in baseline examples:

```text
_InitGraf         Quickdraw.a:1380  OPWORD $A86E
_GetNextEvent     Events.a:457      OPWORD $A970
_WaitNextEvent    Events.a:475      OPWORD $A860
_EventAvail       Events.a:493      OPWORD $A971
_SystemTask       Events.a:617      OPWORD $A9B4
_GetNewMBar       Menus.a:2203      OPWORD $A9C0
_MenuSelect       Menus.a:1938      OPWORD $A93D
_GetMenuHandle    Menus.a:2323      OPWORD $A949
_GetNewWindow     MacWindows.a:803  OPWORD $A9BD
_Alert            Dialogs.a:736     OPWORD $A985
_ExitToShell      Processes.a:416   OPWORD $A9F4
_NewPtr           MacMemory.a:515   OPWORD $A11E
_FreeMem          MacMemory.a:1031  OPWORD $A01C
_PBHGetVInfoSync  Files.a:3671      OPWORD $A207, paramBlock in A0, OSErr in D0
_UnloadSeg        SegLoad.a:134     OPWORD $A9F1
_GetResource      Resources.a:425   OPWORD $A9A0
_NumToString      NumberFormatting.a:136 macro emits $A9EE with package selector
```

Useful prototypes are present adjacent to many OPWORD definitions. Examples:

```text
WaitNextEvent(EventMask eventMask, EventRecord *theEvent, UInt32 sleep,
  RgnHandle mouseRgn) -> Boolean
EventAvail(EventMask eventMask, EventRecord *theEvent) -> Boolean
GetNewMBar(short menuBarID) -> MenuBarHandle
GetNewWindow(short windowID, void *wStorage, WindowRef behind) -> WindowRef
GetResource(ResType theType, short theID) -> Handle
PBHGetVInfoSync(HParmBlkPtr paramBlock) -> OSErr
NumToString(long theNum, Str255 theString) -> void
```

## Baseline Analysis Goal

The first semantic smoke test should be able to render a selected `Sample`
routine with annotations like:

```text
SEG 'Initialize'              ; Classic Mac OS segment
_InitGraf                     ; Toolbox trap, QuickDraw initialization
_GetNewMBar                   ; Menu Manager resource-backed menu bar load
_GetResource 'RECT', id       ; Resource Manager lookup, returns Handle
_UnloadSeg routinePtr         ; Segment Loader call, may purge segment
```

For `Memory`, the smoke test should render:

```text
_PBHGetVInfoSync              ; File Manager HFS parameter-block call
HVolumeParam.ioVAlBlkSiz      ; field access from MPW Files.a structure
HVolumeParam.ioVFrBlk         ; field access from MPW Files.a structure
```

For `Count`, the smoke test should render:

```text
file type MPST / creator MPS
linked MPW runtime libraries
cmdo command resource
open/read/write/getchar/exit runtime calls
```

## Concrete Render Targets

These targets define what "viewable and useful" means for the first issue set.

1. `Sample.a -> Initialize`

Expected rendered structure:

```text
file: Sample.a
segment: Initialize
routine: Initialize PROC
imports: GoGetRect, AlertUser, SysEnvirons, TrapAvailable
stack frame: EventRecord local TheEvent
globals: G.InBackground, G.Stopped, QD.thePort
calls:
  _InitGraf       QuickDraw init, uses QD.thePort
  _InitFonts      Toolbox manager init
  _InitWindows    Window Manager init
  _InitMenus      Menu Manager init
  _TEInit         TextEdit init
  _InitDialogs    Dialog Manager init
  _InitCursor     cursor init
  _EventAvail     event queue probe
  _PurgeSpace     memory availability probe
  _NewPtr         pointer allocation
  _GetNewWindow   loads WIND rWindow
  _GetNewMBar     loads MBAR rMenuBar
  GoGetRect       loads RECT rStopRect / rGoRect in another segment
```

2. `SampleMisc.a -> GoGetRect`

Expected rendered structure:

```text
file: SampleMisc.a
segment: Initialize
routine: GoGetRect FUNC EXPORT
parameters: RectID, TheRect
resource call:
  _GetResource('RECT', RectID) -> Handle
data copy:
  Rect.topLeft and Rect.botRight copied from resource data to caller Rect
resource xrefs:
  rStopRect -> RECT 128
  rGoRect   -> RECT 129
```

3. `MemorySrc.a -> PBHGetVInfoSync site`

Expected rendered structure:

```text
file: MemorySrc.a
kind: desk accessory / DRVR source
entry shape: DAEntry open/control/status/close offsets
call site:
  _NewPtr CLEAR allocates HVolumeParam
  IOParam.ioNamePtr points at local volume-name buffer
  _PBHGetVInfoSync uses A0 parameter block and returns OSErr in D0
field reads:
  HVolumeParam.ioVAlBlkSiz
  HVolumeParam.ioVFrBlk
semantic result:
  free bytes = allocation block size * free block count
```

4. `MPW/Tools/Asm -> CODE 1 Main`

Expected rendered structure:

```text
file: MPW-GM/MPW/Tools/Asm
finder type/creator: MPST/MPS
data fork: data/string payload
resource fork:
  CODE 0 jump-table/application metadata
  CODE 1 Main code segment, 29024 bytes
  other named CODE segments visible in inventory
listing:
  m68k disassembly range from CODE 1 payload
unsupported:
  complete relocation/loader fixups
  source mapping
  exact MPW Link provenance
```

## Correctness Checks To Add

Before breaking implementation into issues, add or plan checks for:

```text
AExamples inventory distinguishes data forks and resource forks
AExamples source resource forks contain only expected MPSR metadata
AExamples inventory contains expected source/resource/make files
Sample.make build recipe parses Link/SetFile/Rez lines
MakeFile build recipe parses Count and Memory recipes
resource scripts expose expected resource type names
source segment parser recognizes SEG/PROC/FUNC/IMPORT/EXPORT
source segment map distinguishes observed source facts from linked CODE facts
generated trap table includes only cited baseline calls
trap words match OPWORD values in MPW includes
CODE 0 parser fields match Inside Macintosh source-page 71
MPW Asm CODE inventory does not drift
```

## Deferred Facts

Defer these until after the first viewable/semantic baseline:

```text
complete Segment Loader emulation
complete relocation/jump-table fixups
full MPW object format parsing
byte-for-byte Link/Rez roundtrip
complete Toolbox/OS trap database
Carbon examples
PowerPC/CFM-only include behavior
emulator execution
```

## Recommended Next Issue Breakdown

1. HFS/fork role inventory.
2. MPW source structure parser.
3. Rez/resource ID parser.
4. Build provenance parser.
5. Baseline include/trap/record extractor.
6. Mac source project model.
7. Concrete semantic render smoke tests.
8. Real `Asm` resource-fork/CODE import.
9. Web UI source/container view.

### Issue 1: HFS/Fork Role Inventory

Inputs:

```text
ext/macos_includes/mpw_gm/inventory.json
tmp/MPW-GM-extracted/data/MPW-GM/MPW/Examples/AExamples/
tmp/mpw_aexamples_probe/resource/MPW-GM/MPW/Examples/AExamples/
```

Deliverables:

```text
fork role classifier: source_text, editor_metadata, executable_resource_fork,
  data_string_payload, object_payload
checks for AExamples TEXT/MPS data forks and MPSR resource forks
checks for MPW/Tools/Asm MPST/MPS data/resource fork roles
```

### Issue 2: MPW Source Structure Parser

Parse:

```text
INCLUDE, IMPORT, EXPORT
SEG, MAIN
PROC, FUNC, ENDP, ENDF
RECORD, ENDR, WITH
```

Deliver a JSON structure that supports file/segment/routine/global views.

### Issue 3: Rez/Resource ID Parser

Parse enough `Sample.r`, `Sample.h`, and `Sample.inc1.a` to connect:

```text
resource declarations -> symbolic ids -> numeric ids -> source call sites
```

First required resource types: `MBAR`, `MENU`, `ALRT`, `DITL`, `WIND`, `RECT`,
`SIZE`, and `cmdo`.

### Issue 4: Build Provenance Parser

Parse `Sample.make` and `MakeFile` into:

```text
Asm source -> .a.o object
Link inputs/options -> output type/creator/program kind
SetFile type/creator attributes
Rez append inputs
linked library object names
```

### Issue 5: Baseline Include/Trap/Record Extractor

Generate a narrow `knowledge/mac_os.json` section or derived metadata for only
baseline-used facts:

```text
records: Point, Rect, EventRecord, HVolumeParam, QDGlobals, WindowRecord,
  DCtlEntry, SysEnvRec
traps/calls: observed Sample/Memory/Count calls only
citations: include path/line plus manual page where needed
```

### Issue 6: Mac Source Project Model

Represent `Sample` as source-first project data:

```text
source files
segments
routines
resources
build recipe
generated Mac facts
```

Keep this distinct from imported executable `CODE` resources.

### Issue 7: Concrete Semantic Render Smoke Tests

Implement render snapshots for:

```text
Sample.a -> Initialize
SampleMisc.a -> GoGetRect
MemorySrc.a -> PBHGetVInfoSync call site
Count -> tool/runtime summary
```

### Issue 8: Real Asm CODE Import

Use `MPW/Tools/Asm` for real binary support:

```text
HFS file metadata
data fork as data/string payload
resource fork parser
CODE 0 metadata
CODE 1 Main listing
unsupported state
```

### Issue 9: Web UI Source/Container View

Expose pivots:

```text
source file
segment
routine
resource
trap/API fact
binary fork
CODE resource
unsupported state
```
