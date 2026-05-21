# Proposal 012: Classic Mac OS M68K Platform

Status: in progress; C-backed Mac project payload, selected CODE listing path,
and framework cleanup are implemented. The committed example target remains
open.

This proposal defines the path to a viewable Classic Mac OS m68k starter target.
The first milestone is deliberately narrow but has two linked views:

```text
semantic source view:
  resources/platform_macos/MPW-GM.img.bin
    -> HFS files MPW-GM/MPW/Examples/AExamples/Sample*
    -> MPW assembly/Rez/make source structure
    -> generated Mac OS facts
    -> web UI source/segment/resource/call view

binary container view:
  resources/platform_macos/MPW-GM.img.bin
    -> HFS file MPW-GM/MPW/Tools/Asm
    -> data fork + resource fork
    -> CODE resources
    -> web UI binary/container/listing view
```

The goal is not full Classic Mac OS emulation, full Segment Loader behavior, or
complete Toolbox annotation. The goal is to prove that the platform layer can
render useful Classic Mac OS source semantics and recognize/import a real Mac
m68k executable container without forcing either into Amiga HUNK or Atari PRG
assumptions. The proof is not complete until the durable platform path follows
the same C-backed architecture used by Amiga and Atari ST.

Proposal 011 covers Atari ST platform knowledge cleanup. This proposal is the
Mac counterpart and architecture pressure test.

## Section Index

- Target Outcome
- Why This Exists
- Evidence
- Current Inputs
- Research Path Before Issue Breakdown
- Platform Shape
- Build Provenance And Deferred Roundtrip Model
- Provenance And KB Policy
- Implementation Quality Policy
- Implementation Slices
- Issue Breakdown Seed
- Artifact Ownership
- Non-Goals
- Acceptance Criteria
- Verification Plan
- Open Questions
- Closeout Checklist

## Target Outcome

The first useful Mac support milestone has two linked parts:

```text
Semantic source baseline:
  render MPW-GM/MPW/Examples/AExamples/Sample with source files, segments,
  routines, resources, build provenance, and cited Mac OS call annotations.

Executable container baseline:
  import MPW-GM/MPW/Tools/Asm as a Classic Mac OS target and view its data fork,
  resource fork, CODE resources, and selected CODE listing in the web UI.
```

Minimum behavior:

- Recognize the source as Classic Mac OS, not as a flat binary.
- Preserve provenance back to `resources/platform_macos/MPW-GM.img.bin`.
- Select `MPW-GM/MPW/Tools/Asm` from the HFS catalog.
- Report file type `MPST`, creator `MPS`, data fork size, and resource fork size.
- Parse the resource map.
- List `CODE` resources.
- Treat `CODE 0` as jump-table/application metadata, not ordinary code.
- Treat nonzero `CODE` resources as candidate m68k code segments.
- Import at least one selected segment into a target project.
- Preserve the `Asm` data fork as data/string material, not code.
- Render `Sample` by source file, segment, routine, resource, and build recipe.
- Annotate cited system calls and common Classic Mac OS call patterns seen in
  documentation or MPW-GM examples.
- Show the imported target through the existing web UI project/listing path.
- Report unsupported details explicitly.

Unsupported at the starter level:

```text
complete Segment Loader emulation
complete jump-table fixup interpretation
relocation and loader patching
full resource semantics
complete trap/API annotation coverage
runtime reproduction
```

This gives a concrete acceptance test while keeping the first implementation
small enough to verify.

## Why This Exists

The project already supports two m68k platform shapes:

```text
Amiga:
  HUNK executables, disks, NDK-derived OS knowledge, custom chips

Atari ST:
  PRG/TOS/TTP executables, GEMDOS disks, traps, Devpac/EmuTOS/Hatari sources
```

Classic Mac OS is a third shape:

```text
Mac OS:
  data forks, resource forks, Finder metadata, MacBinary/NDIF/HFS,
  CODE resources, Segment Loader conventions, ROM/Toolbox traps
```

Adding a viewable Mac target should expose platform assumptions in import,
listing, source export, generated metadata, API payloads, and the web UI. Those
assumptions should be fixed generically where possible, not hidden inside Mac
special cases.

Longer term, comparable platform facts may help porting assistance between
Mac OS, Amiga, and Atari ST. That is not the first implementation goal.

## Evidence

Local documentation supports the resource-centric executable model:

```text
ext/docs_macos/Inside_Macintosh_Volume_I_1985.md
  page 117: files have data and resource forks; application code lives in the
  resource fork and may be split into resources.

ext/docs_macos/Inside_Macintosh_Volume_II_1985.md
  pages 69-71: the Segment Loader uses CODE resources; CODE 0 contains the
  jump table; CODE 1 is the main segment.
```

The MPW-GM image provides a real candidate artifact:

```text
MPW-GM/MPW/Tools/Asm
type: MPST
creator: MPS
data fork: 10752 bytes
resource fork: 213850 bytes
```

The current resource-fork inspector finds:

```text
ext/macos_tools/mpw_gm/asm_code_resources.json
  CODE resources: 28
  total CODE payload bytes: 206404
  CODE 0: jump-table/application metadata
  named segments: Main, Init, Macros, OpTable, Pass2, Directives, ...
```

This is enough to justify the starter import path.

## Current Inputs

Committed or locally derived inputs already present:

```text
resources/platform_macos/MPW-GM.img.bin
ext/docs_macos/*.md
ext/docs_macos/*.source.json
ext/macos_includes/mpw_gm/Interfaces/
ext/macos_includes/mpw_gm/index.json
ext/macos_includes/mpw_gm/inventory.json
ext/macos_tools/mpw_gm/source.json
ext/macos_tools/mpw_gm/asm_code_resources.json
knowledge/mac_os.json
knowledge/macos_source_inventory.json
src/scripts/extract_classic_hfs.py
src/scripts/inspect_mac_resource_fork.py
tests/test_mac_resource_fork.py
```

Implemented research/prototype paths:

```text
Mac source structure, Rez/resource, and MPW build provenance parsers
generated Mac OS runtime metadata tables and C consumer lookup tests
reusable resource fork and MPW Asm CODE container import helpers
MPW/Tools/Asm HFS file/fork metadata and CODE 1 Main listing smoke test
starter Classic Mac OS source/container web payload and renderer branch
optional fixture/resource documentation and Mac source inventory check
```

Still required before this proposal is complete:

```text
Mac platform parsing/import logic promoted to C where Amiga/Atari equivalents
  already live in C
full Classic Mac OS target lifecycle creation in project JSON
server API emits a real `macos` project payload
web UI opens that payload through the normal project route
generated Mac OS metadata feeds render/analysis, not handcrafted Python dicts
selected CODE segment renders as actual m68k listing rows in the web UI
shared platform abstractions are extended where Mac exposes framework gaps
committed illustrative Mac OS target/subtarget under `targets/`
complete Segment Loader relocation/fixup interpretation
byte-for-byte MPW Asm/Link/Rez roundtrip
complete Toolbox/OS trap/API annotation coverage
cross-program source-to-CODE segment mapping
```

## Research Path Before Issue Breakdown

Before splitting this proposal into implementation issues, do a short research
pass over the MPW image, example source, resource scripts, headers, tools, and
Markdown manuals. The goal is to decide what the first analysis should
recognize, and to make those decisions evidence-backed.

The research should produce a committed summary, likely
`docs/macos-initial-analysis-research.md`, plus any structured metadata that is
small, source-derived, and useful for checks.

Research inputs:

```text
tmp/MPW-GM-extracted/data/MPW-GM/MPW/Examples/AExamples/
  Count.a
  FStubs.a
  MemorySrc.a
  Sample.a
  SampleMisc.a
  Sample.inc1.a
  Count.r
  Sample.r
  MakeFile
  Sample.make
  Instructions

tmp/MPW-GM-extracted/data/MPW-GM/MPW/Examples/32BitAExamples/
tmp/MPW-GM-extracted/data/MPW-GM/Interfaces&Libraries/Interfaces/
tmp/MPW-GM-extracted/data/MPW-GM/Interfaces&Libraries/Libraries/
tmp/MPW-GM-extracted/data/MPW-GM/MPW/Tools/

ext/docs_macos/Inside_Macintosh_*.md
ext/docs_macos/MPW_and_Assembly_Language_Programming_for_the_Macintosh_1987.md
ext/docs_macos/Programming_With_Macintosh_Programmers_Workshop_1987.md
```

Research questions:

```text
Which example programs are best starter fixtures?
Which source-level calls and macros appear repeatedly?
Which calls compile down to Toolbox/OS traps?
Which calls use parameter blocks or A-line trap conventions?
Which resource types are required to understand application shape?
Which startup/runtime/library objects appear in Link recipes?
Which data structures can be cross-checked against MPW headers?
Which doc pages cite the same facts seen in source or binaries?
Which facts are useful for porting reference even if not needed for loading?
```

Expected outputs:

```text
ranked starter fixture candidates
example build recipe inventory
source call/macro inventory
resource type inventory
candidate trap/API facts with citations
candidate structure/type facts with citations
list of generated macos .c/.h tables needed for baseline analysis
known unknowns and deferred roundtrip-only facts
concrete issue breakdown for source rendering and binary container import
```

This research pass should prefer source examples over tool binaries when
choosing the first semantic target. MPW `Asm` is useful as a real executable
container; small examples such as `Count`, `Sample`, or `Memory` are more useful
for validating that the analysis renders understandable Classic Mac OS program
intent.

## Platform Shape

Mac support must keep these layers separate:

```text
transport wrapper:
  MacBinary, NDIF, BinHex, raw files, disk images

filesystem/container:
  HFS/MFS catalog, Finder type/creator, data fork, resource fork

resource format:
  resource header, resource map, type list, reference list, names, payloads

executable/code:
  CODE 0 application metadata, nonzero CODE segments, Segment Loader conventions

platform APIs:
  OS traps, Toolbox traps, Resource Manager, File Manager, runtime glue
```

The starter implementation needs only a thin vertical slice:

```text
HFS catalog file -> resource fork -> CODE resources -> m68k segment bytes
```

It should not flatten this into a generic binary import. The fork/resource
metadata is platform data and must survive into the target metadata.

## Build Provenance And Deferred Roundtrip Model

The starter Mac goal is not byte-for-byte rebuild. The primary value is a
rendered, analyzed, editable source view that is good enough to use as a
porting reference and to cross-check OCR/manual-derived knowledge. Still, the
build model matters because it explains what each file contribution means:

```text
source files
  -> Asm/C/Pascal compiler output object files
  -> Link output application/tool/driver segments and jump table
  -> Rez output resource data
  -> SetFile/Finder metadata
  -> final data fork + resource fork + file type/creator
```

Local documentation and examples show the basic assembly path:

```text
asm -p Coin.a
link -p Coin.a.o -o Coin
```

`MPW_and_Assembly_Language_Programming_for_the_Macintosh_1987.md` pages 37-39
describe `asm` producing an intermediary `.a.o` object file, then `link`
turning that object into a standalone application. The link progress report
mentions segments and jump-table entries.

The MPW-GM examples provide stronger build evidence:

```text
MPW-GM/MPW/Examples/AExamples/MakeFile
  Count:
    Asm Count.a
    Asm FStubs.a
    Link -w -c 'MPS ' -t MPST Count.a.o FStubs.a.o \
      "{Libraries}"Stubs.o \
      "{Libraries}"MacRuntime.o \
      "{Libraries}"IntEnv.o \
      "{Libraries}"ToolLibs.o \
      "{Libraries}"Interface.o \
      -o Count
    Rez Count.r -o Count -append

  Memory:
    Asm MemorySrc.a
    Link -da -t dfil -c movr -rt DRVR=12 -sg Memory MemorySrc.a.o -o Memory

MPW-GM/MPW/Examples/AExamples/Sample.make
  Sample:
    Link -o {Targ} Sample.a.o SampleMisc.a.o MacRuntime.o Interface.o
    SetFile {Targ} -t APPL -c 'MOOS' -a B
    Rez -rd -o {Targ} Sample.r -append
```

That research should record which bytes or metadata came from:

```text
Link-created CODE resources
Link-created jump-table/application metadata
linked runtime/library object code
Rez-created UI/application resources
Finder type/creator metadata
data fork payload, if any
```

For the first viewable target, byte-for-byte rebuild is explicitly deferred.
The useful output is a build-provenance model: enough to say which source,
object, library, resource, and Finder metadata inputs contributed to the final
artifact, without requiring the project to reproduce MPW Link/Rez output yet.

## Provenance And KB Policy

Runtime consumers should use generated or structured facts only:

```c
const MacOsTrapInfo *trap = mac_os_find_trap(trap_word);
if (trap != NULL) {
    render_symbol(mac_os_name(MAC_OS_NAME_DOMAIN_TRAP, trap->name_id));
}
```

Provenance belongs in reports, metadata, and review tools:

```text
Inside Macintosh / MPW image / MPW headers / parser output
  -> source inventory row
  -> parsed fact or reviewed correction
  -> knowledge/mac_os.json
  -> generated runtime metadata
  -> runtime consumer
```

Use one broad Mac OS knowledge file until a real split is justified:

```text
knowledge/mac_os.json
  _meta
  format_families
  api_families
  reviewed_corrections
```

Avoid one JSON file per Mac subsystem unless it removes real complexity. In
particular, do not drift back to scattered files such as
`mac_os_file_manager.json`, `mac_os_resource_manager.json`, and so on.

Source inventory rows should track:

```text
id
title
domain
tier
path / metadata_path
availability
machine_readable
citation_quality
parser_feasibility
extraction_status
review_status
decision
license_notes
known_conflicts
```

Allowed status vocabulary should stay aligned with the Atari ST proposal:

```text
availability: committed, optional_local, required_local, missing_external
extraction_status: parsed, parser_asserted, candidate, deferred, unsupported
review_status: not_applicable, seeded, validated
decision: parse, cite_manually, defer, unsupported
```

No Mac runtime fact should enter C consumers without structured provenance.

## Implementation Quality Policy

Classic Mac OS support must cleanly extend the core platform framework. It must
not add a legacy side path, compatibility shim, or Mac-only bypass for behavior
that should be represented generically.

The expected split is:

```text
C owns durable platform parsing, import, generated runtime tables, and listing
  data used by runtime consumers.
Python owns extraction orchestration, reports, tests, local fixture preparation,
  and editing/workflow layers over the C API.
```

If a Mac feature is implemented in Python but the equivalent Amiga or Atari ST
feature is implemented in C, the Mac feature is not complete until a C API or C
runtime path owns the durable behavior. Python may remain as a wrapper over that
C path, but it must not be the only implementation used by project import,
listing, metadata lookup, or web/API payload generation.

If the current framework cannot support Mac cleanly, the work must improve the
framework or raise the blocker. It must not work around the framework with a
parallel Mac-only route, duplicate metadata model, or hidden compatibility
branch.

This applies at least to:

```text
HFS/file/fork container parsing
resource fork parsing and CODE resource inventory
CODE 0 and nonzero CODE segment metadata
selected CODE segment listing input
generated Mac OS record/call lookup
project metadata emitted to the web API
```

## Implementation Slices

### Slice 0: Research And Fixture Selection

Complete the research pass before creating fine-grained implementation issues.
This slice chooses the first semantic fixture and records why.

Outputs:

```text
docs/macos-initial-analysis-research.md
ranked fixture candidates
example call/macro/resource inventory
data fork/resource fork interpretation
source segment rendering model
source segment to CODE resource mapping model
manual citations for baseline facts
first generated table list
deferred facts list
```

### Slice 1: Inventory And Evidence Baseline

Keep the committed source inventory, docs metadata, MPW include index, MPW HFS
inventory, and Asm CODE inventory valid.

Artifacts:

```text
knowledge/macos_source_inventory.json
ext/docs_macos/*.md
ext/docs_macos/*.source.json
ext/macos_includes/mpw_gm/inventory.json
ext/macos_tools/mpw_gm/source.json
ext/macos_tools/mpw_gm/asm_code_resources.json
docs/macos-file-structure.md
```

### Slice 2: Resource Fork Parser

Promote `src/scripts/inspect_mac_resource_fork.py` into reusable parser code or
keep the script as a thin CLI over reusable code. The parser should validate:

```text
resource data/map offsets
type list
reference list
resource names
payload offsets/sizes
CODE 0 metadata
nonzero CODE segment metadata
```

Tests should include synthetic fixtures so parser correctness does not depend
on committing MPW binary forks.

### Slice 3: Mac Container Recognition

Add Mac platform recognition for both starter paths:

```text
MPW-GM.img.bin -> raw HFS -> HFS catalog -> MPW-GM/MPW/Tools/Asm
MPW-GM.img.bin -> raw HFS -> HFS catalog -> MPW-GM/MPW/Examples/AExamples/Sample*
```

The importer should expose:

```text
volume name
file path
CNID
Finder type/creator
data fork size
resource fork size
selected resource fork hash
fork role: source text, executable CODE, data/string payload, editor metadata
```

### Slice 4: CODE Segment Import

Select a conservative first code segment, likely `CODE 1 Main`, and import it
as m68k bytes. Preserve segment metadata:

```text
resource type/id/name
payload offset/size/hash
role: code_segment
unsupported: relocation, complete Segment Loader fixups
```

`CODE 0` should become platform metadata:

```text
above_a5_size
below_a5_size
jump_table_length
jump_table_offset_from_a5
role: jump_table_segment
```

### Slice 5: MPW Source Structure Import

Parse only enough MPW source structure for the selected examples:

```text
source file
SEG name
PROC/FUNC routine boundaries
IMPORT/EXPORT symbol boundaries
RECORD/WITH layout scopes
Rez resource type/id declarations
makefile Asm/Link/SetFile/Rez recipe lines
```

Segment mapping must keep observed source facts separate from linked binary
facts:

```text
Sample source SEG 'Main' -> expected linked CODE resource name Main
MPW/Tools/Asm CODE 1 Main -> observed binary CODE resource
```

Do not infer that segments from different programs are the same.

### Slice 6: Project And Web UI View

Create a target/project that the existing web UI can open. The UI path should
show source structure, binary container metadata, and enough platform metadata
to make the source clear:

```text
platform: macos
source fixture: MPW-GM/MPW/Examples/AExamples/Sample
source pivots: file/segment/routine/resource/build recipe
binary fixture: MPW-GM/MPW/Tools/Asm
binary pivots: data fork/resource fork/CODE resource
file type/creator: MPST/MPS for Asm, TEXT/MPS for source files
selected binary segment: CODE 1 Main
unsupported: relocation/loader semantics/trap annotation
```

### Slice 7: MPW Build Provenance Discovery

Use the MPW manuals and bundled `AExamples` source to document how Asm, Link,
Rez, SetFile, object files, libraries, resource descriptions, file type/creator,
segments, and jump-table entries contribute to final artifacts.

The output should be a small build-provenance document or structured manifest
shape that answers:

```text
which source/object/resource files contribute to each final fork?
which tool creates CODE resources?
which tool appends non-CODE resources?
where is file type/creator assigned?
which linked libraries are copied into the final executable?
what would need byte-for-byte roundtrip later, and what is metadata-only?
```

### Slice 8: Generated Metadata Skeleton

Generate only facts consumed by the starter import and baseline analysis:

```text
format constants
resource type names
CODE role hints
trap/API names for cited examples
parameter-block shapes for cited examples
calling convention hints for cited examples
```

Input ownership stays in `knowledge/mac_os.json`; generated C owns runtime
tables only.

### Slice 9: Baseline Semantic Analysis

The first analysis pass should render example code as recognizable Classic Mac
OS programming, not just m68k instructions. Use documentation examples and
MPW-GM example source/binaries as the baseline corpus.

Initial output should cover only patterns seen in cited examples:

```text
Toolbox/OS trap names
known parameter-block calls
resource lookup/use patterns
Segment Loader and application startup patterns
MPW runtime/library call boundaries when identifiable
```

The data path should match the M68K KB pattern:

```text
manual md / example source / inspected binary evidence
  -> parsed or curated JSON with citations
  -> generated macos consumer .c/.h tables
  -> importer/listing/analysis annotations
```

No Mac semantic fact should be hardcoded directly in importers, renderers, or
web consumers. If the baseline code needs a name, call shape, or convention, it
must come from `knowledge/mac_os.json` or generated metadata with source
provenance.

### Slice 10: Trap/API Knowledge Growth

After the baseline examples are covered, add cited trap/API facts where they
improve the listing. Start with small families already supported by source
evidence:

```text
File Manager parameter-block traps
Resource Manager traps
Segment Loader traps
```

Seeded facts remain review debt until validated.

### Slice 11: Corrections Review Flow

Mirror the shared platform flow:

```powershell
uv run macos-platform-kb corrections list
uv run macos-platform-kb corrections check
uv run macos-platform-kb corrections promote <id> --reviewer <name>
```

Promotion rule:

```text
seeded -> validated requires citation, source_id, rationale, reviewer, date
validated entries keep source and citation
unknown review_status fails check
seeded consumed facts stay visible as review debt
```

### Slice 12: Architecture Generalization Review

After the first Mac target imports, review assumptions in:

```text
binary source kinds
target metadata JSON
generated runtime tables
source include paths
project creation
listing/export layout
web/API payloads
reproduction comparison
```

Fix generic platform assumptions where possible.

### Slice 13: Cross-Porting Feasibility Notes

Only after import/listing works, document which semantic facts would be needed
for Mac-to-Amiga or Mac-to-Atari assistance:

```text
OS call intent
graphics/sound/input API use
file/resource access
memory model assumptions
startup/runtime conventions
```

## Issue Breakdown Seed

The issue split should follow `docs/macos-initial-analysis-research.md` and keep
source rendering separate from binary container import while covering both in
the same starter milestone. Local working issues live under `docs/issues/`.

1. HFS/fork role inventory - implemented

```text
Classify source text, editor metadata, executable resource forks,
data/string payloads, and object payloads from MPW-GM inventory.
```

2. MPW source structure parser - implemented

```text
Parse INCLUDE, IMPORT, EXPORT, SEG, MAIN, PROC, FUNC, RECORD, WITH, and routine
boundaries from Sample/Memory/Count source.
```

3. Rez/resource ID parser - implemented

```text
Connect Sample.r declarations to Sample.h/Sample.inc1.a constants and source
call sites for MBAR, MENU, ALRT, DITL, WIND, RECT, SIZE, and cmdo.
```

4. Build provenance parser - implemented

```text
Parse Asm, Link, SetFile, Rez, object inputs, library inputs, output
type/creator, and program kind from Sample.make and MakeFile.
```

5. Baseline include/trap/record extractor - implemented

```text
Generate only cited records and calls used by the baseline examples:
Point, Rect, EventRecord, HVolumeParam, QDGlobals, WindowRecord, DCtlEntry,
SysEnvRec, and observed Toolbox/OS traps.
```

6. Mac source project model - implemented

```text
Represent Sample as source files, segments, routines, resources, build recipe,
and generated Mac facts. Keep this separate from executable CODE resources.
```

7. Concrete semantic render smoke tests - implemented

```text
Snapshot useful rendered output for Sample.a Initialize, SampleMisc.a GoGetRect,
MemorySrc.a PBHGetVInfoSync, and Count tool/runtime summary.
```

8. Real Asm CODE import

```text
Import MPW/Tools/Asm as HFS file metadata, data fork as data/string material,
resource fork, CODE 0 metadata, CODE 1 Main listing, and unsupported state.
```

9. Web UI source/container view - implemented

```text
Expose pivots by source file, segment, routine, resource, trap/API fact, binary
fork, CODE resource, and unsupported state.
```

10. Classic Mac OS resource documentation

```text
Document optional MPW-GM fixture paths and the Mac platform inventory check.
```

012-013. C-backed Mac platform parser/import parity - in progress

```text
Promote durable Mac HFS, fork, resource fork, CODE metadata, and selected CODE
segment import behavior into C APIs matching the Amiga/Atari platform boundary.
Keep Python as wrapper/report/editing code only.
The C resource-fork/CODE parser slice is implemented; HFS file/fork access,
Finder metadata import, Mac project metadata serialization, and normal API/web
payload routing remain.
The first HFS catalog metadata slice is implemented; catalog-extent fork
materialization is implemented; overflow extents and normal project/API
consumption remain. The first exported C platform-file summary API now feeds a
Python wrapper test for HFS file metadata, Finder type/creator, resource/CODE
inventory, selected CODE 1 byte metadata, and actual selected CODE 1 byte
extraction.
```

012-014. Mac project/API/web integration - blocked

```text
Create a real Mac OS project path whose server payload uses `macos` and whose
web UI opens through the normal project/listing route. Replace prototype
`classic_macos` identifiers rather than preserving aliases.
```

012-015. Generated Mac metadata consumption - implemented

```text
Feed source render and analysis from generated Mac OS metadata, not handcrafted
Python dictionaries in tests or view assembly.
```

012-016. Real CODE listing view - implemented

```text
Render selected nonzero CODE resources as actual m68k listing rows in the web
UI, not just a word preview in a container summary.
```

012-017. Core platform framework cleanup - implemented

```text
Remove any Mac-only side paths discovered during implementation by extending
shared platform source/container/project/listing abstractions cleanly.
```

012-018. Mac OS example target artifact - blocked

```text
Commit an illustrative evolving Mac OS target under `targets/macos_hfs_mpw_gm/`
with `MPW/Tools/Asm` as
`targets/macos_hfs_mpw_gm/targets/macos_file_mpw_tools_asm/asm.s`, rendered as
a whole Mac executable shape rather than a standalone CODE fragment.
```

## Artifact Ownership

Candidate artifacts:

```text
knowledge/mac_os.json
knowledge/macos_source_inventory.json
src/generated/mac_os_*.c/.h
src/scripts/inspect_mac_resource_fork.py
ext/macos_tools/mpw_gm/
ext/macos_includes/mpw_gm/
ext/docs_macos/
docs/macos-file-structure.md
docs/macos-build-model.md
docs/macos-initial-analysis-research.md
docs/macos-targets.md
docs/proposals/012-classic-mac-os-m68k-platform.md
targets/macos_hfs_mpw_gm/
RESOURCES.md
```

Ownership rule:

```text
structured KB owns facts
parsers own extraction from source artifacts
generators own C table emission
runtime consumers read generated metadata
reports own provenance and review visibility
```

## Non-Goals

- Do not promise full Classic Mac OS support in the first implementation.
- Do not require emulator automation for starter import.
- Do not require ROMs.
- Do not require complete Segment Loader emulation before a starter listing.
- Do not require byte-for-byte roundtrip for the porting/reference starter
  milestone.
- Do not claim roundtrip support unless the MPW Asm/Link/Rez build model is
  represented and tested.
- Do not commit copyrighted ROMs, system disks, or proprietary SDK contents.
- Do not add uncited Mac platform facts directly to C consumers.
- Do not split Mac knowledge into subsystem JSON files prematurely.
- Do not start cross-porting implementation before import/listing facts exist.
- Do not fold Mac OS into the Atari ST proposal.

## Acceptance Criteria

- A pre-issue research summary ranks MPW example fixtures and records the
  source/doc evidence used to choose the baseline analysis target.
- AExamples fork inventory identifies source data forks and low-value `MPSR`
  editor metadata resource forks.
- MPW `Asm` or a synthetic equivalent is recognized as Classic Mac OS input.
- The importer identifies data fork, resource fork, resource map, and `CODE`
  resources.
- Finder type/creator metadata is preserved.
- `Asm` data fork is represented as data/string payload, not executable code.
- `CODE 0` is represented as jump-table/application metadata.
- At least one nonzero `CODE` resource is listed as m68k code.
- `Sample` source is renderable by file, segment, routine, resources, and build
  recipe.
- Source segment mapping is distinct from observed binary `CODE` resources.
- The imported target is viewable in the web UI project/listing flow.
- The `macos` web payload is emitted by the normal server project API,
  not only by test fixtures or direct helper calls.
- Durable implementation names use `macos`, not `classic_macos`; no compatibility
  alias or migration shim is kept for the prototype name.
- Durable Mac platform parsing/import behavior lives behind C APIs wherever the
  Amiga or Atari ST equivalent is C-backed.
- Python Mac code is limited to wrappers, extraction/reporting, tests, and
  editing workflow layers over durable C behavior.
- Source/project rendering consumes generated Mac OS metadata rather than
  handcrafted duplicate dictionaries.
- The selected CODE segment is rendered as actual m68k listing rows in the web
  UI, with container metadata linked to that listing.
- Mac support extends shared project/source/container/listing abstractions; any
  framework gap is fixed or explicitly raised, not worked around.
- No Mac-specific compatibility branch, legacy payload, or duplicate metadata
  model remains on the completion path.
- A committed illustrative target exists at `targets/macos_hfs_mpw_gm/` with an
  `MPW/Tools/Asm` subtarget at
  `targets/macos_hfs_mpw_gm/targets/macos_file_mpw_tools_asm/`.
- The `Asm` subtarget commits `asm.s`, rendering the whole Mac executable file
  shape in readable period-authentic Mac assembly style: data fork/resource fork
  context, `CODE 0`, CODE segments, non-CODE resources, placeholders, and
  unsupported state.
- The committed target has regeneration/drift checks so `asm.s` does not go
  stale as rendering improves.
- Baseline analysis annotates cited Mac OS calls and call patterns visible in
  documentation or MPW-GM examples.
- Unsupported Mac platform areas are reported explicitly.
- Build-provenance notes identify Link/Rez/SetFile inputs and any deferred
  roundtrip gaps.
- Runtime-consumed Mac facts come from structured JSON or parser output.
- Source inventory and generated metadata checks catch drift.
- Adding Mac support records or removes exposed platform assumptions.

## Verification Plan

Initial tests:

```text
macos initial analysis research doc/check
source inventory schema tests
macos docs/source metadata checks
AExamples fork role check
AExamples source structure parser tests
AExamples source/resource/build rendering smoke test
resource map parser tests
CODE 0 metadata parser tests
MPW Asm CODE inventory drift check
MPW AExamples build recipe extraction/check
Mac input recognition test
Mac target project creation smoke test
m68k listing smoke test for selected CODE segment
baseline Mac semantic annotation smoke test
web UI project/listing smoke test
unsupported-state reporting test
cmd /c src\precommit.bat
```

Future tests:

```text
trap/API generated runtime tests
corrections list/check/promote tests
disk/file wrapper parser tests
byte-for-byte roundtrip tests, if roundtrip becomes a goal
cross-platform semantic mapping tests
resources documentation coverage tests
```

## Implementation Observations

- 012-001 implemented fork-role classification as an enrichment layer over
  `ext/macos_includes/mpw_gm/inventory.json`; the extractor keeps its historical
  inventory output unless `--fork-roles` is requested.
- The MPW `Asm` executable role can be classified from Finder metadata and local
  research, but the observed `CODE: 28` count remains evidence from
  `ext/macos_tools/mpw_gm/asm_code_resources.json`.
- Full-tree mypy currently has unrelated strict typing failures outside the Mac
  fork-role work; focused direct mypy is used for the new module until that
  wider baseline is cleaned up.
- 012-002 added a MacRoman MPW source structure parser. It records source-only
  SEG membership, routines, MAIN entry markers, imports/exports, records, WITH
  scopes, and line ranges. Local validation against ignored extracted AExamples
  sources succeeded, but committed tests use small fixtures because the full
  extracted source files remain local inputs.
- 012-003 added source-level Rez/resource parsing. It resolves Sample resource
  IDs from both `Sample.h` and `Sample.inc1.a`, inventories `Sample.r` and
  `Count.r` resource declarations, and connects assembly call sites to resource
  declarations. `ALRT`/`DITL` shared IDs require call-context resolution; `_Alert`
  must bind to `ALRT`, while `_GetResource` remains a caller-supplied ID lookup.
- 012-004 added source-level MPW build recipe provenance parsing. The parser
  records variables, object recipes, Link/SetFile/Rez commands, library inputs,
  output type/creator, and Count/Memory/Sample product metadata without claiming
  byte-for-byte roundtrip or executable `Asm` `CODE` import provenance. Real
  MacRoman make files decode MPW dependency/continuation glyphs as U+0192 and
  U+2202, so parser tests cover those forms separately from display-normalized
  text.
- Post-review cleanup tightened earlier Mac parsers: unresolved Rez resource ID
  expressions now remain unresolved instead of becoming numeric zero, MPW source
  logical-line parsing accepts MacRoman continuation glyphs as well as
  backslash, and fork role classification treats `XCOF`/`stub` library-like data
  forks as object payloads alongside `OBJ `.
- Follow-up verification aligned test gates with that cleanup: the active import
  policy now permits the Mac parsers' standard-library dependencies (`ast`,
  `operator`, `shlex`), and the agent-loop regression tests now expect generic
  class/address data-symbol styling to be skipped as non-semantic autonomous
  progress. Full `tests` passed after this adjustment.
- 012-005 added a narrow MPW include generator for baseline Mac OS records and
  calls. It keeps `_NumToString` as a package macro rather than an OPWORD alias,
  records `_PBHGetVInfoSync` A0/D0 protocol evidence, and generates C/H lookup
  tables with source path/line provenance. The generated table is now consumed
  by C runtime tests; source/project render integration remains part of the
  next Mac project-model/render slices because no Classic Mac backend object
  exists yet.
- 012-006 added a source-first Classic Mac OS project model that composes MPW
  source structure, Rez declarations/xrefs, build provenance, and generated Mac
  OS facts into navigable entities. It explicitly requires no built binary,
  ROM, or emulator, and keeps source `SEG` facts separate from observed `Asm`
  executable `CODE` resources.
- 012-007 added compact structured render smoke views for the source project
  model. The tests assert useful output for `Initialize`, `GoGetRect`, Memory's
  `_PBHGetVInfoSync` path, and the `Count` MPW tool/runtime/resource summary,
  while keeping unsupported `CODE` import and MPW roundtrip gaps visible.
- 012-008 added the binary-side MPW `Asm` container import. The importer uses
  the committed MacBinary NDIF fixture through the committed `ndif2raw`
  provider, extracts HFS forks in temp space, preserves Finder metadata,
  treats the data fork as data/string material, parses the resource fork,
  represents `CODE 0` as jump-table/application metadata, exposes all named
  `CODE` resources, and proves `CODE 1 Main` can pass through the existing raw
  m68k listing backend. Relocation/fixups, complete Segment Loader behavior,
  source mapping, and byte-for-byte roundtrip remain explicit unsupported
  state.
- 012-009 added the starter web payload and renderer branch for Classic Mac OS
  source/container views. The payload exposes source files, segments, routines,
  resources, build products, API facts, binary forks, `CODE 0`, `CODE 1 Main`,
  all `CODE` resources, unsupported state, and an explicit boundary that keeps
  `Sample` source facts separate from observed `MPW/Tools/Asm` binary facts.
  This is a view slice only; full Mac project creation and roundtrip remain
  outside the starter branch.
- 012-010 closed the immediate documentation gap for optional Mac fixture
  inputs: `RESOURCES.md` now records the MPW-GM image and `ndif2raw` provider
  paths used by the source/container tests, and `README.md` documents the
  `macos-platform-kb` report/check command for committed Mac source inventory
  metadata.
- 012-011 reconciled this proposal's current-state text with implemented code:
  the starter milestone now has source parsers, generated Mac OS runtime
  metadata, reusable resource/CODE parsing, MPW `Asm` container import, a CODE 1
  listing smoke path, and starter web payload/rendering tests. Full Mac target
  lifecycle creation, Segment Loader fixups, source-to-CODE mapping, and
  byte-for-byte roundtrip remain explicit future work.
- 012-012 replaced the stale unchecked checkpoint list with a neutral section
  index. Completed `docs/issues/012-*` files remain in place for now because
  the active thread objective still uses them as the per-issue evidence trail;
  deleting them is deferred until this working objective is closed.
- 012-015 removed the handcrafted Mac OS call/record table from source render
  tests. The generated runtime now emits `src/generated/mac_os_runtime.json`,
  source project assembly loads that generated metadata by default, and render
  payloads record the generated metadata source.
- Post-012-015 review found the remaining completion issues all depend on the
  same missing foundation: C-backed Mac HFS/resource/CODE import and a shared
  Mac project/listing schema. The Python helper path remains useful research
  evidence, but it must not be promoted as the durable implementation. 012-013
  now owns the C parser/import foundation work; 012-014, 012-016, 012-017, and
  012-018 remain blocked until that foundation is usable from the normal
  platform path.
- 012-013 now has its first C-backed container slice: a native Classic Mac
  resource-fork parser that inventories resource types, extracts `CODE 0`
  jump-table metadata, extracts nonzero `CODE` segment metadata, and returns
  selected resource payload bounds without relying on the Python parser. This
  does not close the platform backend gap yet; C-backed HFS catalog/file/fork
  access, Finder metadata import, Mac project serialization, and normal API/web
  routing remain the next blockers.
- 012-013 now also has a read-only C HFS catalog metadata slice. It parses the
  MDB, catalog directory/file records, Finder type/creator, data/resource fork
  sizes, first-extent fork bounds, and CNID-derived file paths from synthetic
  HFS fixtures.
- 012-013 added C fork materialization across the three catalog extents and
  explicit reporting when overflow extents are still required. Real MPW fixture
  drift checks through this C path, overflow extent support, and normal
  project/API consumption remain out of scope for this slice.
- 012-013 now exposes a C-backed Mac HFS/CODE summary through
  `platform_file_lib` and wraps it from Python. The wrapper test proves the
  durable path owns HFS path lookup, Finder metadata, fork sizes, resource-fork
  parsing, `CODE` inventory, selected `CODE 1` byte metadata, and selected
  nonzero `CODE` byte extraction for listing/import consumers. The existing MPW
  `Asm` code-byte helper now uses that C path for nonzero CODE resources.
  Remaining work is to connect this summary into normal Mac project/API
  creation and add a real MPW fixture drift gate once overflow extents or
  fixture constraints make that safe.
- 012-014 blocker-removal started by replacing durable prototype payload
  identifiers with `macos` across helper payloads, source/container summaries,
  web rendering, and tests. No `classic_macos` compatibility alias was kept.
- 012-014 then added first-class `macos` project records and normal
  `/api/projects/<id>` payload emission from `macos_mpw_fixture` origin
  metadata. The payload uses the C HFS/CODE summary for the binary container
  view and carries provenance to the MPW-GM image plus committed source,
  resource, and build metadata. Selected CODE listing rows and a committed Mac
  target artifact remain separate 012-016/012-018 work.
- 012-013 is now closed for the current MPW `Asm` backend scope: a real
  MPW-GM fixture drift gate compares the C HFS/CODE summary against committed
  `asm_code_resources.json` metadata. Overflow extents remain a future backend
  extension for fixtures that actually need them, not a blocker for the current
  Asm path.
- 012-016 connects the selected `CODE 1 Main` segment to the normal listing
  flow. Mac projects now open `/listing/open`, build a C listing artifact from
  C-extracted CODE bytes, and render real m68k rows in the web Mac view with
  resource/fork/hash/unsupported metadata linked from the container summary.
  The listing is still a selected CODE-segment view, not complete Segment
  Loader reconstruction or full executable roundtrip.
- 012-017 reviewed the Mac project/listing path for framework cleanup after the
  C-backed and web/listing slices landed. The remaining stale starter-only web
  contract expected `generation: "macos_starter"` and the old
  `renderClassicMacProject(projectData)` signature; tests now assert the normal
  listing-backed render signature and absence of the starter generation literal.
  A compatibility-name scan found no remaining `classic_macos` Python/JS/test
  usage.

## Open Questions

- Should later target creation import all nonzero CODE resources as separate
  ranges? The starter container import now selects `CODE 1 Main` for listing
  and exposes the remaining `CODE` resources as inventory.
- Should the MPW Asm binary forks remain temporary-only, with committed metadata
  and hashes, or should any extracted fork be committed under `ext/`?
- Should resource-fork parsing live in `src/scripts` only for now or move
  directly into reusable platform runtime code?
- If roundtrip becomes a goal, should it start from an assembly example such as
  `Count` or from the MPW `Asm` executable itself?
- What target metadata field names should be shared across Amiga, Atari ST, and
  Mac for source container information?

## Closeout Checklist

Current state:

- The starter research slice is useful and tested, but it does not yet close
  this proposal.
- Completed `docs/issues/012-001` through `012-012` remain as evidence for the
  prototype/research path.
- Open completion issues must close the C/API/UI gaps before this proposal can
  move to implemented.

Full closeout requires:

- C-backed Mac parser/import APIs for platform behavior that Amiga/Atari already
  implement in C.
- A real Mac OS project record and server payload with durable `macos` data
  emitted through the normal API, replacing the prototype `classic_macos` name.
- Web UI navigation to the Mac source/container/listing view through the normal
  project flow.
- Generated Mac OS metadata consumed by render/analysis paths.
- A selected CODE segment rendered as actual m68k listing rows.
- An illustrative committed target/subtarget under `targets/macos_hfs_mpw_gm/`
  with `targets/macos_hfs_mpw_gm/targets/macos_file_mpw_tools_asm/asm.s`.
- `docs/macos-targets.md` explains Mac OS target layout, illustrative committed
  artifacts, manual/progress facts, and how to read the generated `.s`.
- Any shared framework limitations resolved in the core abstractions, or
  recorded as explicit blockers.
- No Mac-only workaround path kept as accepted design.
- Optional-fixture skips separated from required completion gates.

## Verification

Draft created after a repo search showed no meaningful current Mac OS platform
support. Revised after MPW `Asm` resource-fork inspection showed a concrete
viewable starter target:

```text
HFS file metadata -> resource map -> CODE segments -> m68k listing
```
