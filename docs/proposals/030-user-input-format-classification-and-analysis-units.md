# Proposal 030: User Input, Format Classification, And Analysis Units

Status: Proposed.

The importer currently mixes three ideas in one place:

```text
what the user supplied
what executable or asset format it appears to be
what analysis should operate on
```

That worked while the project mostly handled Amiga HUNK files, but it becomes
unclear as Atari PRG, Classic Mac OS resource-fork programs, object files, raw
binaries, compressed payloads, and disk/container entries all need to enter the
same workflow. This proposal separates those layers so targets can preserve the
user-visible input while still deriving platform-specific executable facts in a
clean, C-owned way.

## Checkpoint Index

- [ ] Problem Statement
- [ ] Tutorial: Three Layers Instead Of One Enum
- [ ] Tutorial: Amiga HUNK
- [ ] Tutorial: Atari PRG
- [ ] Tutorial: Classic Mac OS HFS File With CODE Resources
- [ ] Tutorial: User-Supplied Raw Binary
- [ ] Proposed Data Model
- [ ] Classification States And Evidence
- [ ] C-Owned Responsibilities
- [ ] Python Responsibilities
- [ ] Source Export And Renderer Registry
- [ ] Migration From Current Source Kinds
- [ ] Tests And Fixture Proof
- [ ] Acceptance Criteria
- [ ] Non-Goals

## Problem Statement

Today `BinarySourceKind` carries too much meaning:

```text
HUNK_FILE
DISK_ENTRY
RAW_BINARY
MACOS_CODE_RESOURCE
```

Those names mix provenance and semantics:

- `DISK_ENTRY` says where bytes came from, not what they are.
- `HUNK_FILE` says the bytes are an Amiga executable container.
- `RAW_BINARY` says the bytes lack enough format metadata.
- `MACOS_CODE_RESOURCE` says the source is a selected platform resource, not an
  ordinary file.

This makes clean platform import harder. A user may load:

```text
an Amiga disk image
an Atari disk image
a standalone Amiga HUNK file
a standalone Atari PRG file
a Classic Mac OS HFS image
a Mac application file containing many CODE resources
a Mac object file
a raw binary blob
a compressed payload extracted from another target
```

The user-facing input should be preserved. Format classification should then
decide whether the input contains executable units, asset units, unsupported
containers, or raw bytes needing manual context.

## Tutorial: Three Layers Instead Of One Enum

The clean model has three layers.

```text
User input
  -> source classification
  -> analysis unit
```

Textual illustration:

```text
UserInputRecord
  kind: disk_image | file | resource_item | archive_member | raw_bytes
  path/provenance/container locator

SourceClassification
  kind: platform_executable | object_module | raw_binary | data_asset | container | unsupported
  platform: amiga | atari_st | macos | unknown
  format: amiga_hunk | atari_prg | macos_code_resource | raw_m68k | ...
  confidence: accepted | parser_asserted | candidate | deferred | unsupported
  evidence: KB refs, parser facts, signatures, user metadata, analysis facts

AnalysisUnit
  kind: platform_executable_unit | raw_binary_region | container_browser | asset
  byte source locator
  executable ranges
  entrypoints or entry candidates
  parser/use policy
```

This avoids the current ambiguity where `HUNK_FILE` is both a user-loaded file
and an executable format.

## Tutorial: Amiga HUNK

User supplies a standalone Amiga executable:

```text
resources/platform_amiga/Game
```

The importer records:

```json
{
  "user_input": {
    "kind": "file",
    "path": "resources/platform_amiga/Game"
  }
}
```

The platform parser classifies it:

```json
{
  "classification": {
    "kind": "platform_executable",
    "platform": "amiga",
    "format": "amiga_hunk",
    "confidence": "accepted",
    "kb_record_id": "amiga.hunk.load_file.basic_backfill"
  }
}
```

The analysis unit is then executable:

```json
{
  "analysis_unit": {
    "kind": "platform_executable_unit",
    "platform": "amiga",
    "format": "amiga_hunk",
    "sections": [
      {"name": "CODE_0", "role": "code", "stored_offset": 64, "load_offset": 0},
      {"name": "DATA_1", "role": "data", "stored_offset": 2048, "load_offset": 1984},
      {"name": "BSS_2", "role": "bss", "stored_offset": null, "load_offset": 4096}
    ]
  }
}
```

Important distinction:

```text
HUNK is not the generic term for a platform format.
HUNK is the Amiga executable format.
```

The future generic term is `platform_executable`.

## Tutorial: Atari PRG

Atari is similar but not identical:

```text
user file: GAME.PRG
classification: platform=atari_st, format=atari_prg
analysis unit: TEXT/DATA/BSS executable image
```

Example:

```json
{
  "classification": {
    "kind": "platform_executable",
    "platform": "atari_st",
    "format": "atari_prg",
    "confidence": "accepted"
  },
  "analysis_unit": {
    "kind": "platform_executable_unit",
    "entrypoints": [
      {
        "offset": 0,
        "source": "parser_header",
        "confidence": "accepted"
      }
    ]
  }
}
```

The renderer should not need Atari-only branches for ordinary source export.
It should receive executable ranges and labels from the shared analysis model.

## Tutorial: Classic Mac OS HFS File With CODE Resources

A Classic Mac OS application-like file is not a HUNK and not a flat binary.

User-visible path:

```text
HFS image: MPW-GM.img.bin
file: MPW-GM/MPW/Tools/Asm
resource fork: CODE 0, CODE 1, CODE 2, ...
```

Classification:

```json
{
  "classification": {
    "kind": "platform_executable_container",
    "platform": "macos",
    "format": "macos_hfs_file_with_code_resources",
    "confidence": "accepted",
    "children": [
      {"format": "macos_code_resource", "resource_type": "CODE", "resource_id": 0},
      {"format": "macos_code_resource", "resource_type": "CODE", "resource_id": 1}
    ]
  }
}
```

Analysis units:

```text
CODE 0
  role: application metadata / jump-table routing
  executable body: no

CODE 1..N
  role: executable segment/resource
  executable body: ranges from parser facts
  entrypoints: parser/user/generated evidence only
```

This lets the UI load the file the user actually sees while analysis can still
operate on resource-level executable units.

## Tutorial: User-Supplied Raw Binary

A user may load bytes with no container metadata:

```text
file: unknown.bin
```

Initial classification:

```json
{
  "classification": {
    "kind": "raw_binary",
    "platform": "unknown",
    "format": "raw_bytes",
    "confidence": "accepted",
    "reason": "no parser-proven executable container"
  }
}
```

Analysis can still inspect it:

```text
does it decode as 68k instructions?
does it contain Amiga library call patterns?
does it contain Atari GEMDOS/XBIOS/BIOS trap patterns?
does it contain Mac OS trap or CODE resource patterns?
does it have plausible entry stubs or relocation-looking data?
```

But clean disassembly is not enough to claim a platform.

```text
valid 68k code: accepted instruction evidence
platform identity: candidate unless parser/signature/user evidence proves it
entrypoint: candidate unless parser/user/control-flow evidence proves it
```

Example candidate record:

```json
{
  "classification": {
    "kind": "raw_binary",
    "platform": "unknown",
    "format": "raw_m68k_candidate",
    "confidence": "candidate",
    "evidence": [
      "high valid instruction density",
      "no accepted platform container signature",
      "entrypoint generated from clean decode island"
    ]
  }
}
```

The renderer may show useful decoded output, but review items must make the
platform and entry assumptions visible.

## Proposed Data Model

Introduce durable records that separate provenance, classification, and unit
selection.

Sketch:

```python
class UserInputKind(StrEnum):
    FILE = "file"
    DISK_IMAGE = "disk_image"
    CONTAINER_ENTRY = "container_entry"
    RESOURCE_ITEM = "resource_item"
    RAW_BYTES = "raw_bytes"


class ClassificationKind(StrEnum):
    PLATFORM_EXECUTABLE = "platform_executable"
    PLATFORM_EXECUTABLE_CONTAINER = "platform_executable_container"
    OBJECT_MODULE = "object_module"
    RAW_BINARY = "raw_binary"
    DATA_ASSET = "data_asset"
    COMPRESSED_PAYLOAD = "compressed_payload"
    UNSUPPORTED = "unsupported"


class AnalysisUnitKind(StrEnum):
    PLATFORM_EXECUTABLE_UNIT = "platform_executable_unit"
    RAW_BINARY_REGION = "raw_binary_region"
    CONTAINER_BROWSER = "container_browser"
    ASSET = "asset"
```

A target descriptor should look like:

```json
{
  "schema_version": 3,
  "user_input": {
    "kind": "container_entry",
    "container_project_id": "macos_hfs_mpw_gm",
    "path": "MPW-GM/MPW/Tools/Asm"
  },
  "classification": {
    "kind": "platform_executable_container",
    "platform": "macos",
    "format": "macos_hfs_file_with_code_resources",
    "confidence": "accepted"
  },
  "analysis_units": [
    {
      "kind": "platform_executable_unit",
      "platform": "macos",
      "format": "macos_code_resource",
      "resource_type": "CODE",
      "resource_id": 1
    }
  ]
}
```

Compatibility with current `source_binary.json` should be explicit:

```text
current HUNK_FILE
  -> user_input.kind=file
  -> classification.format=amiga_hunk
  -> analysis_unit.kind=platform_executable_unit

current DISK_ENTRY
  -> user_input.kind=container_entry
  -> classification is discovered from extracted entry

current RAW_BINARY
  -> user_input.kind=file/raw_bytes
  -> classification.kind=raw_binary
  -> analysis_unit.kind=raw_binary_region

current MACOS_CODE_RESOURCE
  -> user_input.kind=resource_item
  -> classification.format=macos_code_resource
  -> analysis_unit.kind=platform_executable_unit
```

## Classification States And Evidence

Every classification must state how strong it is.

```text
accepted
  parser-proven or KB-accepted format evidence

parser_asserted
  parser-owned assertion backed by documented KB comments

candidate
  plausible but not enough to drive accepted mutation or platform claims

deferred
  known concept exists but exact support/evidence is not implemented

unsupported
  known unsupported format or unsupported platform feature
```

Do not silently promote:

```text
clean instruction decode -> accepted platform
printable bytes -> accepted string
entry-looking stub -> accepted entrypoint
Mac CODE resource -> Amiga HUNK-like flat file
```

Instead, emit evidence:

```json
{
  "fact_status": "candidate",
  "parser_use": "review_only",
  "reason": "valid 68k decode island but no parser-proven entrypoint"
}
```

## C-Owned Responsibilities

C should own the heavy classification and executable facts:

- container/parser summaries for supported executable formats;
- executable ranges, metadata ranges, BSS/load/stored offsets;
- parser-owned KB fact refs;
- platform signatures and candidate classifiers;
- entrypoint sources and confidence;
- raw-binary decode confidence;
- analysis unit creation from parser facts;
- review blockers for candidate/deferred/unsupported facts.

Python should not become the place where format semantics are invented.

Suggested C-facing shape:

```c
typedef struct PlatformClassification {
    const char *kind;
    const char *platform;
    const char *format;
    const char *confidence;
    const char *kb_record_id;
    const char *fact_id;
} PlatformClassification;

typedef struct AnalysisUnit {
    const char *kind;
    const char *platform;
    const char *format;
    uint32_t unit_id;
    uint32_t range_count;
    const ExecutableRange *ranges;
} AnalysisUnit;
```

The exact representation may differ, but the boundary should be this clear:

```text
C emits classifications and units.
Python routes, displays, persists, and tests them.
```

## Python Responsibilities

Python should:

- preserve user input provenance in target metadata;
- call C classifiers/parsers;
- materialize child targets from accepted/candidate classifications;
- keep container browsing and target listing state separate;
- render source from C-owned rows/facts;
- expose registry-based source export;
- report blockers and unsupported facts without hiding the target.

Python may choose UX defaults:

```text
disk/container parent -> browser view
accepted executable unit -> target source/listing view
raw binary candidate -> review-first target view
unsupported object module -> metadata/unsupported view
```

Python must not:

- infer accepted platform identity from shape alone;
- guess entrypoints as accepted facts;
- treat Mac CODE as Amiga HUNK;
- use hidden fallback code paths that bypass registries or C facts.

## Source Export And Renderer Registry

Source export should remain registry-driven.

Current clean shape:

```text
source_export_payload
  -> artifact renderer registry if origin.renderer is declared
  -> binary-source renderer registry by source kind
```

Future shape after this proposal:

```text
source_export_payload
  -> artifact renderer registry
  -> analysis-unit renderer registry by analysis_unit.kind + platform + format
```

Example:

```python
SOURCE_UNIT_RENDERERS = {
    ("platform_executable_unit", "amiga", "amiga_hunk"): render_c_owned_executable_source,
    ("platform_executable_unit", "atari_st", "atari_prg"): render_c_owned_executable_source,
    ("platform_executable_unit", "macos", "macos_code_resource"): render_macos_code_source,
    ("raw_binary_region", "unknown", "raw_m68k"): render_raw_m68k_candidate_source,
}
```

No fallback branch should exist. If no renderer is registered, source export
should return an explicit unsupported/refused payload:

```json
{
  "status": "refused",
  "message": "no registered source renderer for platform_executable_unit/macos/object_module"
}
```

## Migration From Current Source Kinds

Slice 1: Add schema v3 alongside current descriptors.

```text
source_binary.json remains readable
target_input.json or source_target.json records new layered model
```

Slice 2: Generate v3 records for existing targets.

```text
HUNK_FILE -> platform_executable/amiga_hunk
RAW_BINARY -> raw_binary/raw_bytes
DISK_ENTRY -> container_entry + discovered child classification
MACOS_CODE_RESOURCE -> platform_executable/macos_code_resource
```

Slice 3: Move source export to analysis-unit renderer keys.

The existing `SOURCE_BINARY_RENDERERS` remains as a bridge only until
analysis-unit records are available for all imported targets.

Slice 4: Move project list/details UI to display:

```text
input kind
classification
analysis unit
confidence
unsupported/deferred blockers
```

Slice 5: Retire generic code that switches directly on `HUNK_FILE` except in
the Amiga HUNK parser/importer.

## Tests And Fixture Proof

Representative no-fixture tests:

```text
classify Amiga HUNK bytes -> platform_executable/amiga_hunk
classify Atari PRG bytes -> platform_executable/atari_prg
classify raw 68k bytes -> raw_binary/raw_m68k_candidate
classify unknown bytes -> raw_binary/unknown with review blocker
source export missing renderer -> refused, not fallback
```

Fixture-backed tests:

```text
Magicland Dizzy disk entry -> imported child HUNK executable
Atari PRG fixture -> TEXT/DATA/BSS analysis unit
MPW Tools Asm HFS file -> Mac CODE resource analysis units
MPW CODE 0 -> metadata/routing, not executable body
MPW CODE 1 -> platform executable unit, not Amiga HUNK
```

Regression tests should assert the important negative cases:

```text
clean raw decode does not set platform=amiga
Mac CODE resource does not set format=amiga_hunk
DISK_ENTRY alone does not imply executable
missing renderer does not use fallback output
candidate entrypoint does not become accepted entrypoint
```

## Acceptance Criteria

- User input provenance and executable classification are separate records.
- Amiga HUNK, Atari PRG, Mac CODE, raw binary, and disk/container entries can be
  described without overloading one enum.
- C emits or validates platform classifications and executable analysis units.
- Python routes and displays classifications without inventing accepted facts.
- Source export dispatches by registered artifact or analysis-unit renderer.
- No hidden fallback renderer exists.
- Existing targets migrate without losing source artifact paths or git-tracked
  rendered source.
- Full mypy, ruff, unit tests, CDP tests, and relevant round-trip checks pass.

## Non-Goals

- Do not implement Mac object-file linking in this proposal.
- Do not claim Mac ASM round-trip support.
- Do not promote Mac byte-entry, relocation/fixup, source-to-CODE, or non-CODE
  payload facts beyond current KB states.
- Do not infer platform identity from instruction validity alone.
- Do not force all user inputs to become executable targets.

