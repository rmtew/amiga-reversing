# Proposal 006: Target Import And Analysis Architecture

## Checkpoint Index

- [ ] Why This Exists
- [ ] Mental Model
- [ ] Current State Read
- [ ] Integration Findings
  - [ ] 1. Source Descriptor Resolution Is Stronger Than Target Creation
  - [ ] 2. Target Materialization Is Still Split Across Callers
  - [ ] 3. Raw-Binary Analysis Exists, But Raw-Binary Creation Is Missing
  - [ ] 4. Loader-Stage Target Creation Is Correctly Evidence-Based
  - [ ] 5. Analysis Facts Are Large, But Not Ready For A Broad Split
  - [ ] 6. Provenance Vocabulary Is Not Yet Clean
- [ ] Tutorial: Target Source Contract
  - [ ] Step 1: Treat `source_binary.json` As The Required Source Contract
  - [ ] Step 2: Keep Address Models Explicit
  - [ ] Step 3: Add Typed Source Provenance
  - [ ] Step 4: Reject Invalid Targets Before They Reach Analysis
- [ ] Tutorial: Target Materialization
  - [ ] Current Good Parts
  - [ ] Current Friction
  - [ ] Target Materialization Request
- [ ] Tutorial: Raw-Binary Project Creation
- [ ] Tutorial: Loader-Stage Targets
- [ ] Tutorial: Analysis Result Views
- [ ] Tutorial: Data Structure Enumeration
- [ ] Larger Architecture Observations
  - [ ] 1. Target Import Should Follow The Project's Generated-Knowledge Rule
  - [ ] 2. Source Metadata Should Be A Deep Module
  - [ ] 3. Materialized Targets Should Be Data, Not Guesses
  - [ ] 4. Whole-Target Scenarios Are The Right Test Level
- [ ] Forward Implementation Model
  - [ ] Source Descriptor Model
  - [ ] Target Materializer
  - [ ] Raw-Binary Create Flow
  - [ ] Disk And Loader-Stage Provenance
  - [ ] Analysis Result Views
  - [ ] Review And Manual Action Projection
  - [ ] Whole-Target Scenario Checks
- [ ] Target Artifact Ownership
- [ ] Non-Goals
- [ ] Proposed Rewrite
  - [ ] Slice 1: Materialization Diagnostic Inventory
  - [ ] Slice 2: Target Materializer
  - [ ] Slice 3: Raw-Binary Add Project
  - [ ] Slice 4: Typed Loader-Stage Provenance
  - [ ] Slice 5: Stable Analysis Result Views
  - [ ] Slice 6: Whole-Target Scenario Gate
- [ ] Acceptance Criteria
- [ ] Deletion Checklist
- [ ] Rewrite Acceptance Tests
- [ ] Verification

## Why This Exists

This project is moving toward explicit, reproducible target analysis. Original
bytes live under `bin/`, target outputs live under `targets/<name>/`, analysis
facts drive discovered code/data/ranges, and manual intervention lives in the
Manual Action Log.

Target import is the place where that discipline can either hold or leak.

The current codebase already has the important pieces:

- `source_binary.json` is the strict source descriptor for imported targets.
- `amiga_reversing/disasm/binary_source.py` validates hunk, disk-entry, and
  raw-binary source descriptors.
- `amiga_reversing/disasm/project_paths.py` requires a source descriptor when
  resolving a target.
- Disk import tests cover AmigaDOS and several custom/non-DOS paths.
- Bootblock/loader-stage child targets are materialized only when concrete bytes,
  load address, and entrypoint evidence exist.
- C facts already recover many runtime-copy, table, memory-layout, and platform
  facts.

The next problem is not "invent target metadata". The next problem is making
target creation as explicit and centralized as target resolution already is.

The goal is a clean import architecture where every target answers:

```text
Where did these bytes come from?
How are file offsets mapped to analysis/runtime addresses?
Why is this entrypoint valid?
What analysis facts were derived from it?
What review or reproduction status is still blocking trust?
```

## Mental Model

Think of target import as a contract chain:

```text
physical input
  -> extracted bytes
  -> source descriptor
  -> target metadata
  -> analysis facts
  -> review and reproduction status
```

The source descriptor is the join between bytes and analysis.

Examples:

```text
AmigaDOS ADF
  -> file entry "C/Game"
  -> disk-entry source descriptor
  -> hunk/load metadata
  -> disassembly and facts
  -> round-trip/review status
```

```text
Non-DOS boot disk
  -> bootblock reads sectors to $70000
  -> raw-binary child target with disk-read provenance
  -> runtime-absolute load and entry metadata
  -> disassembly and facts
  -> review status until reproduction is meaningful
```

```text
User imports loose raw code
  -> uploaded binary bytes
  -> raw-binary source descriptor supplied by user
  -> explicit address model, load address, entrypoint, and code start
  -> disassembly and facts
  -> review status
```

The clean rule:

```text
A target is materialized only when the project has bytes plus enough address
evidence to analyze those bytes correctly.
```

Inferred-only ranges are analysis evidence. They are not targets.

The desired direction is:

```text
callers describe evidence
TargetMaterializer writes target artifacts
ProjectPaths resolves target artifacts
analysis consumes resolved artifacts
review/reproduction consumes analysis facts
```

Callers should not know the complete filesystem ceremony for a target.

## Current State Read

The codebase is already close to the target model.

Current strong pieces:

```text
amiga_reversing/disasm/binary_source.py
  Source descriptor validation.
  Raw-binary address-model rules.
  Local-offset and runtime-absolute entrypoint mapping.

amiga_reversing/disasm/project_paths.py
  Project path resolution.
  Mandatory source descriptor loading.
  Disk child target lookup through disk manifests.

amiga_reversing/amiga_disk/project.py
  ADF import.
  Bootblock/loader-stage child target materialization.
  Evidence-based non-creation for incomplete bootblock disk reads.

amiga_reversing/disasm/server.py
  Add Project flow for ADF and hunk uploads.
  Project creation wiring for web usage.

src/m68k_analysis_facts_v2.c
  Runtime views.
  Table candidates.
  Orphan code.
  Memory layout.
  Platform disk/read facts.
```

Tests already cover important behavior:

```text
raw-binary target path resolution
raw entrypoint validation
runtime-absolute first-open UI navigation
local-offset first-open UI navigation
ADF import
non-DOS bootblock and bootloader target discovery
incomplete bootblock disk-read non-creation
```

The remaining weakness is not lack of concepts. It is split ownership.

Textual shape today:

```text
server import
  writes target project artifacts for hunk/ADF paths

disk import
  writes target project artifacts for disk-entry and loader-stage paths

tests
  hand-write target project artifacts for focused cases

project_paths
  later validates and resolves what those callers wrote
```

The better shape:

```text
server import
disk import
tests
  -> TargetMaterializer
       -> validates source descriptor
       -> writes project artifacts
       -> updates parent/child discovery state
       -> returns resolvable target path
```

## Integration Findings

### 1. Source Descriptor Resolution Is Stronger Than Target Creation

Resolution already has a real source descriptor model.

Illustrative current descriptor:

```json
{
  "kind": "raw_binary",
  "path": "targets/manual_blob/source.bin",
  "address_model": "runtime_absolute",
  "load_address": 24576,
  "entrypoint": 24608,
  "code_start_offset": 0
}
```

That descriptor can be validated and resolved. The project can use it to map
runtime addresses back to file offsets.

Creation is weaker. Multiple callers still write descriptor-shaped dictionaries
directly. That means the Interface is deep when reading but shallow when writing.

Target shape:

```text
one source descriptor model
one materialization writer
all callers pass typed evidence into that writer
```

### 2. Target Materialization Is Still Split Across Callers

Creating a target currently means knowing several files and relationships:

```text
copied or extracted source bytes
.project.json
source_binary.json
target_metadata.json
disk manifest child rows
optional execution views
optional parent target relation
```

That knowledge appears in import code and tests. It should be one Module.

Current risk:

```text
new caller writes a valid source_binary.json
but forgets target_metadata.json
or forgets parent manifest update
or uses a provenance field no loader validates
```

Target behavior:

```text
TargetMaterializer accepts one request.
TargetMaterializer writes all required artifacts.
TargetMaterializer fails before partial target creation when evidence is invalid.
```

### 3. Raw-Binary Analysis Exists, But Raw-Binary Creation Is Missing

Raw-binary consumption is not speculative. The resolver and UI tests already use
raw-binary descriptors.

The missing path is product creation:

```text
Add Project upload path:
  .adf -> amiga-disk
  other -> amiga-hunk
```

That suffix classification is too narrow for loose raw code or manually supplied
loader stages.

Target behavior:

```text
Add Project raw-binary mode:
  source file
  address model
  load address when runtime_absolute
  entrypoint
  code start offset
  CPU/platform metadata
  display name
```

There should be no inference fallback. Missing load or entry metadata is a
validation error.

### 4. Loader-Stage Target Creation Is Correctly Evidence-Based

The disk importer already has the right rule:

```text
concrete disk bytes + concrete load address + concrete entrypoint
  -> child target

incomplete read or inferred-only range
  -> analysis/review evidence, not a target
```

This should be preserved and made more explicit through typed provenance.

Target provenance shape:

```json
{
  "kind": "bootblock_disk_read",
  "parent_disk_id": "game_disk",
  "disk_byte_offset": 11264,
  "disk_byte_size": 4096,
  "source_kind": "logical_disk_offset",
  "read_instruction_offset": 186
}
```

The provenance answers why a child target exists. It should not be loose extra
JSON that only one writer understands.

### 5. Analysis Facts Are Large, But Not Ready For A Broad Split

`src/m68k_analysis_facts_v2.c` is broad. That alone is not the problem.

The analysis work is coupled because these facts inform each other:

```text
instruction walk
runtime views
platform disk reads
runtime copies
table candidates
orphan code
memory layout
review blockers
```

Splitting internal helper logic before stable result Interfaces exist would
create shallow Modules.

Target extraction:

```text
keep instruction-walk implementation local
export stable result views once multiple callers consume them
```

### 6. Provenance Vocabulary Is Not Yet Clean

Bootloader execution views currently use `seed_origin: "autodoc"` for
analysis-derived memory-copy evidence.

That is misleading. `autodoc` should mean NDK/AutoDoc-derived knowledge. A
runtime copy recovered from a bootblock should use provenance like:

```text
analysis_fact
bootloader_analysis
platform_disk_read
runtime_copy_evidence
```

The exact spelling matters less than the ownership rule:

```text
primary OS/NDK knowledge provenance and recovered target evidence provenance
must not share one name.
```

## Tutorial: Target Source Contract

The source contract says what bytes analysis is allowed to interpret and how file
offsets map to analysis addresses.

### Step 1: Treat `source_binary.json` As The Required Source Contract

Every target should have exactly one source descriptor.

Illustrative hunk descriptor:

```json
{
  "kind": "hunk_file",
  "path": "targets/bloodwych/source"
}
```

Illustrative disk-entry descriptor:

```json
{
  "kind": "disk_entry",
  "path": "targets/game_disk/files/C/Game",
  "parent_disk_id": "game_disk",
  "entry_path": "C/Game"
}
```

Illustrative raw descriptor:

```json
{
  "kind": "raw_binary",
  "path": "targets/manual_stage/source.bin",
  "address_model": "runtime_absolute",
  "load_address": 458752,
  "entrypoint": 458752,
  "code_start_offset": 0
}
```

The descriptor is not optional metadata. It is the target source Interface.

### Step 2: Keep Address Models Explicit

Raw binaries need explicit address semantics.

Runtime-absolute:

```text
file offset $000000
  -> runtime address $070000

entrypoint $070020
  -> local file offset $000020
```

Descriptor:

```json
{
  "kind": "raw_binary",
  "address_model": "runtime_absolute",
  "load_address": 458752,
  "entrypoint": 458784,
  "code_start_offset": 0
}
```

Local-offset:

```text
file offset $000000
  -> analysis address $000000

entrypoint $000020
  -> local file offset $000020
```

Descriptor:

```json
{
  "kind": "raw_binary",
  "address_model": "local_offset",
  "entrypoint": 32,
  "code_start_offset": 0
}
```

No code path should silently convert one model into the other.

### Step 3: Add Typed Source Provenance

Source provenance belongs with the descriptor when it explains why these bytes
and addresses are trusted.

Target shape:

```json
{
  "kind": "raw_binary",
  "path": "targets/disk/stage_000/source.bin",
  "address_model": "runtime_absolute",
  "load_address": 458752,
  "entrypoint": 458752,
  "code_start_offset": 0,
  "provenance": {
    "kind": "bootblock_disk_read",
    "parent_disk_id": "disk_000",
    "disk_byte_offset": 11264,
    "disk_byte_size": 4096,
    "source_kind": "logical_disk_offset",
    "read_instruction_offset": 186
  }
}
```

This keeps review questions attached to the target:

```text
Why is this a target?
Which parent media produced it?
Which recovered fact justified it?
Which byte range was copied?
Which runtime address was used?
```

### Step 4: Reject Invalid Targets Before They Reach Analysis

Required validation:

```text
unknown kind -> reject
missing source path -> reject
missing raw address model -> reject
runtime_absolute without load_address -> reject
entrypoint outside mapped bytes -> reject
code_start_offset outside source bytes -> reject
bootblock_disk_read provenance missing disk byte range -> reject
parent manifest update requested without parent target -> reject
```

Analysis should not repair invalid target metadata. Invalid target metadata is an
import/materialization error.

## Tutorial: Target Materialization

Target materialization is the write side of project creation.

### Current Good Parts

Current code already has strong consumers:

```text
ProjectPaths can resolve targets.
BinarySource can validate descriptors.
Tests can exercise raw descriptors.
Disk import can create child targets from concrete evidence.
```

That means the rewrite can centralize writing without inventing a new read model.

### Current Friction

The write ceremony is scattered:

```text
server import writes hunk/ADF project files
disk import writes child target files
tests hand-write descriptors and metadata
```

This is the same kind of duplication that Proposal 005 calls out for generated
forms: the model exists, but ownership is split.

### Target Materialization Request

Illustrative Interface:

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TargetMaterializationRequest:
    target_id: str
    display_name: str
    source_bytes_path: Path
    source_descriptor: dict
    target_metadata: dict
    parent_target_id: str | None = None
    update_parent_manifest: bool = False


def materialize_target(
    *,
    targets_root: Path,
    request: TargetMaterializationRequest,
) -> Path:
    """Validate source metadata and write one resolvable target."""
    ...
```

The real implementation should use typed descriptor/provenance classes where
practical. The important point is that callers supply evidence, not individual
file writes.

Target output:

```text
targets/<target_id>/
  .project.json
  source_binary.json
  target_metadata.json
  source bytes or pointer to imported bytes
```

Optional parent update:

```text
targets/<parent_disk>/
  disk manifest child target row
```

TargetMaterializer should own both writes when creating a child target is one
logical operation.

## Tutorial: Raw-Binary Project Creation

Raw-binary creation should be a strict Add Project mode.

Required user/API inputs:

```text
source file
display name
target id or generated target id
address model: local_offset | runtime_absolute
load address: required for runtime_absolute
entrypoint
code start offset
CPU/platform metadata
```

Server-side shape:

```python
def create_raw_binary_project(request: RawBinaryCreateRequest) -> ProjectInfo:
    source = RawBinarySource(
        path=request.stored_source_path,
        address_model=request.address_model,
        load_address=request.load_address,
        entrypoint=request.entrypoint,
        code_start_offset=request.code_start_offset,
    )
    return materialize_target(
        targets_root=targets_root,
        request=TargetMaterializationRequest(
            target_id=request.target_id,
            display_name=request.display_name,
            source_bytes_path=request.stored_source_path,
            source_descriptor=source.to_json(),
            target_metadata=request.target_metadata(),
        ),
    )
```

Strict behavior:

```text
runtime_absolute without load_address fails
entrypoint outside source range fails
code_start_offset past EOF fails
unsupported address model fails
ambiguous file suffix does not choose hunk mode automatically
```

The first-open UI behavior should continue to use the descriptor entrypoint:

```text
runtime_absolute entrypoint -> select row by runtime address
local_offset entrypoint -> select row by local analysis address
```

## Tutorial: Loader-Stage Targets

Loader-stage targets should remain evidence-driven.

Good creation chain:

```text
C facts recover platform disk read
  -> disk importer verifies concrete disk byte range
  -> disk importer copies exact bytes
  -> TargetMaterializer writes raw-binary child target
  -> child target records source provenance
```

Good non-creation chain:

```text
C facts recover possible disk read but missing byte length
  -> no child target
  -> review evidence remains visible
```

Do not convert inferred spans into targets just because they are useful to view.

Loader-stage descriptor example:

```json
{
  "kind": "raw_binary",
  "path": "targets/game_disk/stage_000/source.bin",
  "address_model": "runtime_absolute",
  "load_address": 458752,
  "entrypoint": 458752,
  "code_start_offset": 0,
  "provenance": {
    "kind": "bootblock_disk_read",
    "parent_disk_id": "game_disk",
    "disk_byte_offset": 11264,
    "disk_byte_size": 4096,
    "source_kind": "logical_disk_offset",
    "read_instruction_offset": 186
  }
}
```

The descriptor should be enough to explain the target without opening importer
code.

## Tutorial: Analysis Result Views

The C analysis module should expose stable result views before broad internal
splitting.

Current useful result families:

```text
runtime views
platform disk/read facts
runtime-copy facts
table candidates
orphan-code rows
memory-layout rows
review blockers
```

Illustrative C view:

```c
typedef struct M68kRuntimeViewRow {
  uint32_t file_offset;
  uint32_t runtime_address;
  uint32_t byte_length;
  const char *provenance_kind;
} M68kRuntimeViewRow;

typedef struct M68kAnalysisResultViews {
  const M68kRuntimeViewRow *runtime_views;
  size_t runtime_view_count;
  const M68kTableCandidateRow *table_candidates;
  size_t table_candidate_count;
  const M68kReviewBlockerRow *review_blockers;
  size_t review_blocker_count;
} M68kAnalysisResultViews;
```

The view Interface should be stable. The instruction-walk Implementation can
remain local.

Do not extract:

```text
one helper per instruction-walk micro-decision
generic plugin seams for hypothetical analysis passes
compatibility adapters for historical JSON shapes
```

Those would move complexity without improving locality.

## Tutorial: Data Structure Enumeration

Data structure enumeration should flow from evidence to review.

Target chain:

```text
C analysis facts recover concrete evidence
  -> stable result views expose evidence
  -> renderer/review code shows high-confidence candidates
  -> accepted user decisions enter Manual Action Log
  -> review items regenerate from current facts plus accepted actions
```

This preserves project conventions:

```text
C analysis facts are source of truth for discovered code/data/xrefs/ranges.
Manual Action Log stores user intervention.
entities.jsonl is retired state and must not become a dependency again.
```

Jump-table work:

```text
new target exposes unresolved C status
  -> add exact pattern support
  -> export table candidate row
  -> test against target evidence
```

Generic indirect calls/jumps should remain separate from table candidates.

Resident/device work:

```text
NDK/AutoDoc/OS KB symbols and layouts
  -> generated or validated OS structure knowledge
  -> C/platform facts identify resident/init/vector patterns
  -> labels, review facts, and source annotations
```

Runtime-built resident/device targets should update source only after clean direct
rebuild or explicit relocation/lifetime semantics exist.

## Larger Architecture Observations

### 1. Target Import Should Follow The Project's Generated-Knowledge Rule

The project rule for CPU/platform knowledge is:

```text
extract upstream
store structured facts
consume downstream
verify through oracles/tests
```

Target import should follow the same rule:

```text
extract media evidence upstream
store source/provenance descriptors
consume descriptors downstream
verify through analysis/review/reproduction tests
```

Heuristic import paths work against this. If a target is created, the evidence
should be visible.

### 2. Source Metadata Should Be A Deep Module

`binary_source.py` is already close to this. The deletion test says it earns its
place: without it, every caller would need to know source kinds, path rules,
address models, entrypoint mapping, and validation errors.

The next deepening is write-side ownership.

Deep Interface:

```python
descriptor = BinarySourceDescriptor.from_json(data, target_dir=target_dir)
descriptor.analysis_entrypoint()
descriptor.local_entrypoint()
descriptor.mapped_range()
```

Deep write Interface:

```python
target_path = materialize_target(targets_root=targets_root, request=request)
```

The caller should not know more than that.

### 3. Materialized Targets Should Be Data, Not Guesses

File signatures, packer guesses, and custom loader hints are useful reports.
They are not target creation authority unless they lead to concrete bytes,
address mapping, and entrypoint evidence.

Good chain:

```text
trusted signature KB
  -> likely format report
  -> explicit loader/materializer path
  -> target
```

Bad chain:

```text
byte pattern guessed packer
  -> silent unpack attempt
  -> target with unclear address provenance
```

### 4. Whole-Target Scenarios Are The Right Test Level

Unit tests prove descriptor rules. Whole-target scenarios prove the architecture.

Scenarios should assert visible states and key facts:

```text
target is resolvable
entrypoint opens correctly
analysis facts include expected runtime/platform evidence
review blockers are present or absent as expected
reproduction status is visible
child targets exist only when evidence is concrete
```

They should not snapshot entire generated source files.

## Forward Implementation Model

The end state should have one source contract and one materialization path.

```text
input media or user upload
  -> evidence extraction
  -> TargetMaterializer
       -> BinarySourceDescriptor validation
       -> target artifact write
       -> parent/child manifest update
  -> ProjectPaths resolution
  -> C analysis facts
  -> stable result views
  -> review/reproduction status
```

### Source Descriptor Model

The descriptor model owns:

```text
source kind
source path
address model
load address rules
entrypoint rules
code start offset rules
optional source provenance
validation error text
```

It should not own:

```text
project directory creation
parent manifest updates
web request parsing
analysis fact generation
```

### Target Materializer

The materializer owns:

```text
target directory creation
source byte placement
.project.json write
source_binary.json write
target_metadata.json write
parent manifest child-row updates
cleanup on validation failure where practical
```

It should consume source descriptors. It should not duplicate descriptor rules.

### Raw-Binary Create Flow

The raw-binary create flow owns:

```text
web/API request shape
user-facing validation errors
upload storage
calling TargetMaterializer
returning ProjectInfo
```

It should not infer missing load or entry metadata.

### Disk And Loader-Stage Provenance

Disk import owns:

```text
physical/media evidence extraction
bootblock disk-read fact interpretation
source byte extraction from disk image
materialization request construction
```

TargetMaterializer owns the write.

### Analysis Result Views

C analysis owns:

```text
instruction walk
runtime view recovery
table recovery
platform fact recovery
review blocker recovery
```

Stable result views own:

```text
small exported row shapes
counts and lookup helpers
JSON/UI/reporting consumption contracts
```

### Review And Manual Action Projection

Review owns:

```text
regenerating current review items
projecting accepted Manual Action Log entries
showing current blockers
```

Review should not depend on retired mutable `entities.jsonl` state.

### Whole-Target Scenario Checks

Scenario checks own:

```text
import setup
analysis run
selected visible status assertions
selected fact assertions
selected child target assertions
```

They should be small enough to diagnose and broad enough to catch architecture
regressions.

## Target Artifact Ownership

Ownership should follow the natural data flow.

```text
media/user import layer
  owns input capture and evidence extraction

BinarySourceDescriptor
  owns source descriptor schema and validation

TargetMaterializer
  owns target artifact writes and parent/child target updates

ProjectPaths
  owns resolving existing targets

C analysis facts
  owns discovered code/data/ranges/platform facts

Analysis result views
  owns stable exported fact rows

Manual Review
  owns regenerated review items and Manual Action Log projection

Reproduction
  owns reassembly/binary diff status
```

Expected target artifacts:

```text
targets/<target_id>/.project.json
targets/<target_id>/source_binary.json
targets/<target_id>/target_metadata.json
targets/<target_id>/<source bytes or imported source path>
```

Expected parent artifacts for disk/import trees:

```text
targets/<disk_id>/<disk manifest>
  child target rows
  extracted file rows
  loader-stage target rows
```

Consumer-only code:

```text
disassembly generation
web navigation
review item regeneration
reproduction checks
scenario tests
```

Consumer-only means these files may resolve descriptors and report status. They
should not decide how to write a valid target directory.

## Non-Goals

This proposal should not grow into every import or analysis idea.

Non-goals:

```text
adding broad compatibility adapters for historical target metadata shapes
splitting facts_v2 only to reduce line count
creating raw/non-DOS child targets from inferred-only ranges
silently inferring raw-binary load or entry metadata
requiring external reverse-engineering facts for normal operation
making file-signature guesses create targets without a loader/materializer path
expanding mojibake checks into a punctuation or style policy
restoring entities.jsonl or mutable entity verification state
```

No backward compatibility layer is required for invalid target metadata. Existing
test fixtures may be migrated to the new materializer when that simplifies the
model.

External reverse-engineering facts can exist later as optional imports with
provenance. They should not be required for tests, normal rendering, precommit,
target status, or reproduction checks.

## Proposed Rewrite

Because this repository is the only consumer of these target artifacts, the best
path is a direct rewrite toward one materialization path. A short diagnostic
inventory is useful first so existing writers are visible before deletion.

End state:

```text
import evidence or raw-binary request
  -> TargetMaterializer
       -> BinarySourceDescriptor validation
       -> target artifacts
       -> optional parent manifest update
  -> ProjectPaths
  -> analysis facts
  -> review/reproduction
```

### Slice 1: Materialization Diagnostic Inventory

First inventory every current code path that writes target artifacts.

Purpose:

```text
list all source_binary.json writers
list all target_metadata.json writers
list all .project.json writers
list all parent manifest child-target writers
list tests hand-writing descriptors
identify descriptor extras not validated by binary_source.py
```

This inventory is not the architecture. It is a bootstrap measuring tool with a
short lifetime.

Exit conditions:

```text
all current writers are known
all descriptor extra fields are classified
tests needing fixture materialization are identified
TargetMaterializer Interface can cover every legitimate writer
```

### Slice 2: Target Materializer

Add the write-side Module.

Required behavior:

```text
accept one materialization request
validate source descriptor before writing
write required target artifacts
update parent manifest when requested
fail on invalid or incomplete evidence
return a path ProjectPaths can resolve
```

Then replace direct writers in:

```text
server hunk/ADF import path
disk-entry target creation
bootblock/loader-stage target creation
tests that hand-write complete targets
```

### Slice 3: Raw-Binary Add Project

Add the missing product path.

Required behavior:

```text
raw-binary create route accepts explicit address metadata
runtime_absolute requires load_address
entrypoint is validated against mapped bytes
code_start_offset is validated against source length
created target opens at descriptor entrypoint
creation routes through TargetMaterializer
```

This slice converts existing raw-binary support into an end-to-end workflow.

### Slice 4: Typed Loader-Stage Provenance

Move disk/read descriptor extras into typed provenance.

Required behavior:

```text
bootblock_disk_read provenance has required fields
invalid provenance fails before target write
child target descriptor explains byte source and address evidence
incomplete bootblock reads do not create child targets
```

This slice prepares custom/non-DOS track work without adding heuristic target
creation.

### Slice 5: Stable Analysis Result Views

Extract only result Interfaces with multiple consumers.

Initial candidates:

```text
runtime views
platform disk/read facts
runtime-copy facts
table candidates
memory-layout rows
review blockers
```

Do not split instruction-walk internals in this slice. The purpose is a stable
consumer Interface, not line-count reduction.

### Slice 6: Whole-Target Scenario Gate

Add named scenario checks after the write path is unified.

Initial scenarios:

```text
AmigaDOS hunk imported from ADF
non-DOS bootblock with materialized loader stage
non-DOS bootblock with incomplete disk-read evidence and no child target
user-created runtime-absolute raw binary
user-created local-offset raw binary
```

Each scenario should assert selected facts and statuses, not entire source
snapshots.

## Acceptance Criteria

These criteria are the minimum bar for accepting the rewrite.

Required acceptance points:

```text
source_binary.json is mandatory for every target resolved by ProjectPaths

all new target creation goes through TargetMaterializer

TargetMaterializer validates source descriptors before writing target artifacts

TargetMaterializer writes .project.json, source_binary.json, target_metadata.json,
and parent/child manifest updates needed for one logical target creation

raw-binary Add Project exists as an explicit API/UI mode

raw-binary creation requires address model and entrypoint

runtime_absolute raw binaries require load_address

invalid entrypoint or code_start_offset rejects project creation

disk-derived loader-stage child targets require concrete bytes, load address, and
entrypoint

inferred-only disk spans do not create child targets

loader-stage source provenance is typed and validated

bootloader-analysis-derived execution views do not use autodoc provenance

analysis result views expose stable rows only where multiple consumers need them

facts_v2 instruction-walk internals remain local unless a real result Interface
requires extraction

manual review continues to regenerate from C facts plus Manual Action Log
projection

entities.jsonl remains retired and is not reintroduced as project state

whole-target scenarios cover representative import and raw-binary paths
```

## Deletion Checklist

Known deletion or fold-in targets:

```text
direct source_binary.json writes outside TargetMaterializer

direct target_metadata.json writes outside TargetMaterializer for new target
creation

direct .project.json writes outside TargetMaterializer for new target creation

disk child target manifest updates disconnected from target creation

tests hand-writing full target directories when TargetMaterializer can create
the fixture

ad hoc raw child descriptor extra fields not represented in typed provenance

suffix-only Add Project classification that cannot represent raw-binary mode

bootloader execution-view provenance that labels recovered analysis evidence as
autodoc

analysis result JSON/UI paths that duplicate row interpretation better owned by
stable result views

any dependency on retired entities.jsonl state
```

Temporary diagnostic inventory code should be removed once TargetMaterializer owns
all legitimate writers.

## Rewrite Acceptance Tests

Required rewrite tests:

```text
source descriptor validation
  Hunk, disk-entry, local-offset raw, and runtime-absolute raw descriptors load.
  Invalid entrypoint/code_start_offset/load_address combinations fail.

target materialization
  Materializer writes all required target artifacts.
  Materializer rejects invalid descriptors before creating a resolvable target.
  ProjectPaths can resolve every materialized target.

raw-binary API/UI creation
  Runtime-absolute raw project can be created.
  Local-offset raw project can be created.
  Runtime-absolute without load_address fails.
  Entrypoint outside mapped bytes fails.
  First-open navigation selects the descriptor entrypoint.

loader-stage materialization
  Concrete bootblock disk-read evidence creates a raw child target.
  Incomplete bootblock disk-read evidence does not create a child target.
  Child target descriptor contains typed provenance.
  Parent disk manifest records the child target.

provenance vocabulary
  Bootloader-analysis-derived execution views do not use autodoc provenance.
  NDK/AutoDoc-derived seeds still use explicit primary-source provenance.

analysis result views
  Runtime views, platform facts, table candidates, and review blockers are
  consumed through stable result rows where extracted.
  Instruction-walk internals are not exposed to UI/project code.

manual review state
  Review items regenerate from current facts and Manual Action Log projection.
  No test requires entities.jsonl.

whole-target scenarios
  ADF hunk import reaches expected visible status.
  Non-DOS materialized loader stage appears only with concrete evidence.
  Raw-binary projects open at the correct entrypoint.
```

## Verification

Required checks for implementation:

```text
unit tests for binary source descriptors
unit tests for TargetMaterializer
import tests for disk-entry and loader-stage targets
API tests for raw-binary project creation
CDP tests for first-open raw-binary entrypoint behavior
whole-target scenario tests for representative imports
C tests for any new table/resident/device analysis patterns
mypy for amiga_reversing/amiga_disk, amiga_reversing/disasm, amiga_reversing/tools
ruff check
precommit batch where relevant
```

Useful report artifacts:

```text
target materialization writer inventory
raw-binary create validation matrix
loader-stage provenance report
whole-target scenario summary
review blocker summary
reproduction status summary
```
