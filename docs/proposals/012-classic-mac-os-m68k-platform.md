# Proposal 012: Classic Mac OS M68K Platform

Status: Draft.

This proposal defines a future path for classic Mac OS / Macintosh m68k platform
support. The repo currently has no meaningful Mac OS platform support, no
committed Mac OS reference corpus, and no platform knowledge pipeline for Mac
executables, resource forks, filesystems, traps, or Toolbox/OS APIs.

The immediate purpose is not to implement Mac support in one step. It is to
define a source-discovery and minimal-support path that tests whether the
platform architecture is generic enough for three m68k platforms: Amiga, Atari
ST, and classic Mac OS.

Proposal 011 defines the Atari ST platform knowledge cleanup. This proposal
should reuse the same platform pattern where it fits, while deliberately
pressuring areas Atari ST does not cover: resource forks, Finder metadata,
MacBinary/BinHex wrappers, HFS/MFS, ROM/Toolbox traps, and application
packaging.

## Checkpoint Index

- [ ] Clean Target Model
- [ ] Why This Exists
- [ ] Current Inputs
- [ ] Source Inventory Schema
- [ ] Source Discovery Policy
- [ ] Tutorial: Build The Mac Platform KB Report
- [ ] Tutorial: Pick A Minimal Fixture
- [ ] Tutorial: Model File Containers And Resource Forks
- [ ] Tutorial: Add Trap/API Knowledge
- [ ] Tutorial: Generate Runtime Metadata
- [ ] Tutorial: Platform Architecture Pressure Test
- [ ] Larger Architecture Observations
- [ ] Implementation Slices
- [ ] Artifact Ownership
- [ ] Non-Goals
- [ ] Acceptance Criteria
- [ ] Verification Plan
- [ ] Deletion Checklist

## Clean Target Model

The clean Mac platform path should follow the same broad architecture as Amiga
and Atari ST:

```text
source discovery / fixture corpus
  -> source inventory with availability, tier, and decision
  -> parser extraction where possible
  -> cited parser assertions or reviewed corrections where necessary
  -> knowledge/mac_os_*.json
  -> generated src/generated/mac_os_*.c/.h
  -> platform loader, analyzer, renderer, writer, and reproduction consumers
  -> report/check and fixture feedback
```

The first useful question is:

```text
What is the smallest cited, tested platform slice that proves the codebase can
load, identify, and reason about a real m68k Mac artifact?
```

The target is not a full classic Mac OS environment. The target is a minimal,
legal, cited fixture path that proves the abstractions can handle a third m68k
platform without forcing Mac artifacts into Amiga HUNK or Atari PRG shapes.

Runtime consumers should see generated facts:

```c
/* desired C shape: generated Mac facts only */
const MacOsTrapInfo *trap = mac_os_find_trap(trap_word);
if (trap != NULL) {
    render_symbol(mac_os_name(MAC_OS_NAME_DOMAIN_TRAP, trap->name_id));
}
```

Provenance should stay in reports and review tools:

```text
Inside Macintosh / MPW / emulator source / file format reference
  -> inventory row
  -> parsed fact or correction
  -> generated runtime metadata
  -> runtime consumer
```

## Why This Exists

Amiga and Atari ST support exercise two platform shapes:

```text
Amiga:
  HUNK executables, libraries/devices, NDK-derived OS knowledge, custom chips

Atari ST:
  PRG/TOS/TTP executables, GEMDOS disks, traps, Devpac/EmuTOS/Hatari sources
```

Classic Mac OS is a third shape:

```text
Mac OS:
  data forks, resource forks, Finder metadata, MacBinary/BinHex wrappers,
  HFS/MFS disk images, ROM/Toolbox traps, resource-centric applications
```

Adding even minimal Mac support should reveal platform assumptions in import,
listing, source export, reproduction comparison, generated runtime metadata,
platform KB reporting, and web/API payloads.

Longer term, comparable platform facts may help with porting assistance between
Mac OS, Amiga, and Atari ST. That is not the first implementation goal.

## Current Inputs

Current repo search found no meaningful Mac OS platform support. Existing hits
are incidental references such as MacOSX in vasm documentation or unrelated
resource filenames in cloned projects.

There is currently no known committed equivalent of:

```text
knowledge/mac_os_*.json
src/generated/mac_os_*.c/.h
src/platform_mac_os*.c
resources/platform_mac_os
ext/mac_os_includes
```

This proposal should therefore begin with source discovery, source inventory,
and fixture selection.

Mac local/external source requirements must be documented in `RESOURCES.md`
when sources are selected. That documentation should include expected paths,
acquisition notes, redistribution limits, and which generated artifacts or tests
depend on each source.

## Source Inventory Schema

Add once sources are identified:

```text
knowledge/mac_os_source_inventory.json
```

Use the same inventory vocabulary as Proposal 011. Keep availability,
extraction state, review state, and planning decision separate.

Suggested shape:

```json
{
  "schema_version": 1,
  "sources": [
    {
      "id": "inside-macintosh-toolbox",
      "title": "Inside Macintosh Toolbox Reference",
      "publisher": "Apple",
      "domain": ["toolbox", "traps", "api"],
      "tier": 1,
      "path": "resources/platform_mac_os/inside_macintosh_toolbox.pdf",
      "url": null,
      "availability": "required_local",
      "machine_readable": false,
      "citation_quality": "page",
      "parser_feasibility": "manual_or_ocr",
      "extraction_status": "candidate",
      "review_status": "not_applicable",
      "decision": "cite_manually",
      "license_notes": "Local reference only; do not commit copyrighted PDF.",
      "known_conflicts": []
    }
  ]
}
```

Allowed values:

```text
availability:
  committed
  optional_local
  required_local
  missing_external

extraction_status:
  parsed
  parser_asserted
  candidate
  deferred
  unsupported

review_status:
  not_applicable
  seeded
  validated

decision:
  parse
  cite_manually
  defer
  unsupported
```

## Source Discovery Policy

Mac OS source discovery must produce committed inventory rows, not private
notes.

Initial source classes to investigate:

- Inside Macintosh volumes and related Apple developer references.
- MPW / classic Mac development headers if legally obtainable.
- Emulator/source references such as Mini vMac, Basilisk II, SheepShaver, or
  MAME Mac drivers where useful.
- File-format references for resource forks, MacBinary, BinHex, HFS/MFS, and
  application packaging.
- Existing open-source tools that parse classic Mac resource files or HFS.

No Mac platform fact should enter runtime consumers without structured
provenance. Sources that cannot be committed may still be referenced through
inventory rows and documented in `RESOURCES.md`.

## Tutorial: Build The Mac Platform KB Report

Start with a read-only command surface:

```powershell
uv run mac-platform-kb report
uv run mac-platform-kb check
```

The first report may say "no parsed sources yet". Its job is to establish the
inventory format, source decisions, fixture state, and unsupported areas.

Initial report sections:

```text
Classic Mac OS Platform KB

Source inventory:
  committed: 0
  required_local: 0
  candidate: 0
  parsed: 0

Fixture corpus:
  legal fixture: missing
  recognized Mac artifact: no
  m68k code region: no

Containers:
  MacBinary/BinHex: candidate
  data fork/resource fork: candidate
  HFS/MFS: deferred

Trap/API KB:
  Toolbox/OS traps: candidate
  generated runtime: missing

Architecture pressure:
  platform assumptions recorded: 0
```

Strict checks should fail on:

```text
duplicate source ids
unknown availability / extraction_status / review_status / decision values
required local sources missing for selected scope
uncited parser assertions or corrections
unknown correction review statuses
generated artifact drift once generation exists
fixture metadata malformed once fixtures exist
```

## Tutorial: Pick A Minimal Fixture

Pick one legally usable tiny m68k Mac artifact. The fixture should be small
enough to commit or generated from source in tests.

The first smoke test should prove:

```text
fixture recognized as Mac platform input
container metadata extracted
m68k code region identified
listing can be produced
unsupported parts are reported explicitly
```

The fixture should not require a full emulator or a copyrighted ROM. If no
legal binary fixture is available, generate a small resource/container fixture
from source data in tests.

## Tutorial: Model File Containers And Resource Forks

Mac support must separate these layers:

```text
transport wrapper:
  MacBinary, BinHex, raw files, disk image

filesystem/container:
  HFS, MFS, data fork, resource fork, Finder metadata

executable/code:
  CODE resources, jump tables, segments, init/runtime conventions

platform APIs:
  OS traps, Toolbox traps, ROM APIs, resource manager calls
```

Resource forks are core, not optional. For Mac applications, resources often
describe the application structure. A loader that sees only a flat data fork
misses the platform's semantic center.

Minimal resource metadata shape:

```json
{
  "schema_version": 1,
  "resources": [
    {
      "type": "CODE",
      "id": 1,
      "name": null,
      "offset": 4096,
      "length": 128,
      "attributes": [],
      "source_id": "fixture-minimal-mac-app"
    }
  ]
}
```

## Tutorial: Add Trap/API Knowledge

Mac OS API calls are commonly trap-based. A useful analyzer needs trap names,
calling conventions, parameter/return facts, and source provenance.

Add:

```text
knowledge/mac_os_traps.json
knowledge/mac_os_corrections.json
```

Candidate trap fact:

```json
{
  "schema_version": 1,
  "traps": [
    {
      "trap_word": 41385,
      "name": "GetResource",
      "family": "ResourceManager",
      "source_id": "inside-macintosh-toolbox",
      "citation": {
        "path": "resources/platform_mac_os/inside_macintosh_toolbox.pdf",
        "page": 123
      },
      "review_status": "seeded"
    }
  ]
}
```

Correction commands should mirror the shared platform flow unless Mac needs a
specific divergence:

```powershell
uv run mac-platform-kb corrections list
uv run mac-platform-kb corrections check
uv run mac-platform-kb corrections promote <correction_id> --reviewer <name>
```

Promotion rule:

```text
seeded -> validated requires citation, source_id, rationale, reviewer, date
validated entries keep source and citation
unknown review_status fails check
seeded consumed facts stay visible as review debt
```

## Tutorial: Generate Runtime Metadata

Use generated runtime metadata once the source shape stabilizes:

```text
knowledge/mac_os_file_format.json
knowledge/mac_os_resource_format.json
knowledge/mac_os_traps.json
knowledge/mac_os_corrections.json
  -> src/generated/mac_os_*.c/.h
```

The first generator can be skeletal. It should prove the ownership pattern:

```text
structured KB owns facts
generator emits C tables
runtime consumers read generated metadata
reports own provenance and review visibility
```

## Tutorial: Platform Architecture Pressure Test

After the minimal fixture works, review whether code still assumes Amiga or
Atari shapes:

```text
binary source kinds
platform metadata JSON
generated runtime tables
source include paths
reproduction comparison
web/API platform payloads
target import
listing/export layout
```

Record architecture assumptions as explicit follow-up work. Do not hide them
inside Mac-specific compatibility code.

## Larger Architecture Observations

### 1. Platform Code Must Not Assume Amiga Or Atari Shapes

Mac OS should be allowed to have resource-centric structure without forcing it
into HUNK or PRG concepts.

### 2. File Containers And OS Metadata Are Separate Axes

Mac support may need disk image parsing, wrapper parsing, resource parsing, code
segment parsing, and OS API parsing as separate layers.

### 3. Weak Sources Need The Same Provenance Model

Like Atari ST, Mac OS may need local PDFs, scans, headers, emulator sources, and
tooling references. Use the shared inventory fields rather than inventing a
Mac-only status model.

### 4. Cross-Porting Requires Comparable Semantic Facts

Longer-term porting assistance depends on comparable facts:

```text
OS call intent
graphics/sound/input API use
file/resource access
memory model assumptions
startup/runtime conventions
```

## Implementation Slices

### Slice 1: Source Discovery, Inventory, And Resources Documentation

Add:

```text
knowledge/mac_os_source_inventory.json
mac-platform-kb report
mac-platform-kb check
RESOURCES.md Mac source entries
```

Research and commit inventory rows. Identify what can be mirrored, parsed,
cited manually, deferred, or marked unsupported.

### Slice 2: Minimal Fixture Corpus

Find or generate a legally usable m68k Mac artifact for tests. The fixture must
not require copyrighted ROMs or system disks.

### Slice 3: Mac Binary/Resource Container Model

Model the minimum file/resource structure needed by the fixture. Treat resource
fork metadata as first-class platform metadata.

### Slice 4: Trap/API Knowledge Seed

Seed a cited trap/API knowledge shape with review status. Do not generate
runtime trap facts from uncited constants.

### Slice 5: Corrections Review Flow

Add:

```text
knowledge/mac_os_corrections.json
mac-platform-kb corrections list
mac-platform-kb corrections check
mac-platform-kb corrections promote <id> --reviewer <name>
```

### Slice 6: Generated Runtime Metadata Skeleton

Generate minimal runtime tables from structured JSON.

### Slice 7: Import And Listing Smoke Test

Prove that a Mac fixture imports and produces a useful listing with explicit
unsupported metadata.

### Slice 8: Architecture Generalization Review

Review and remove platform assumptions exposed by adding a third m68k platform.

### Slice 9: Cross-Porting Feasibility Notes

Document which semantic facts would be needed to support Mac-to-Amiga or
Mac-to-Atari porting assistance.

## Artifact Ownership

Candidate artifacts:

```text
knowledge/mac_os_source_inventory.json
knowledge/mac_os_file_format.json
knowledge/mac_os_resource_format.json
knowledge/mac_os_traps.json
knowledge/mac_os_corrections.json
src/generated/mac_os_*.c/.h
resources/platform_mac_os/
docs/proposals/012-classic-mac-os-m68k-platform.md
RESOURCES.md
```

Ownership rule:

```text
structured KB owns facts
generators own C table emission
runtime consumers read generated metadata
reports own provenance and review visibility
```

## Non-Goals

- Do not promise full classic Mac OS support in the first implementation.
- Do not add uncited Mac platform facts directly to C consumers.
- Do not commit copyrighted ROMs, system disks, or proprietary SDK contents.
- Do not make emulator automation a prerequisite for the first fixture import.
- Do not start cross-porting implementation before import/listing facts exist.
- Do not fold Mac OS into the Atari ST proposal.

## Acceptance Criteria

- Source discovery produces committed inventory with availability, extraction
  status, review status, tier, citation quality, parser feasibility, and
  decision fields.
- Mac local/external source requirements are documented in `RESOURCES.md`.
- No Mac OS runtime fact reaches C consumers without structured provenance.
- A legal tiny fixture is identified or generated.
- The fixture can be recognized as Mac platform input.
- A m68k code region can be listed.
- Resource/container metadata is represented explicitly, even if incomplete.
- Unsupported Mac platform areas are reported, not silently ignored.
- Adding Mac support identifies and records platform abstraction assumptions
  that need cleanup.

## Verification Plan

Initial tests:

```text
source inventory schema tests
mac-platform-kb report/check tests
fixture recognition test
container/resource metadata smoke test
m68k listing smoke test
unsupported-state reporting test
cmd /c src\precommit.bat
```

Future tests:

```text
trap/API generated runtime tests
corrections list/check/promote tests
resource map parser tests
disk/file wrapper parser tests
cross-platform semantic mapping tests
resources documentation coverage tests
```

## Deletion Checklist

Before closing this proposal:

- Promote durable issue reasoning into this proposal.
- Delete completed `docs/issues/012-*` issue files.
- Remove stale TODO entries.
- Document `mac-platform-kb report/check` if implemented.
- Record skipped external checks and why.

## Verification

Draft created after a repo search showed no meaningful current Mac OS platform
support. Updated to align with the shared platform knowledge pattern from
Proposal 011.
