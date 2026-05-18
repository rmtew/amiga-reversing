# Proposal 011: Atari ST Platform Knowledge

Status: Draft.

This proposal defines the clean path for Atari ST platform knowledge. The goal
is to replace scattered Atari ST facts with a traceable, reportable, generated
knowledge chain.

Atari ST support should not pretend to have an Amiga-style NDK. The source
material is weaker and more fragmented. The clean version is still disciplined:
parse what can be parsed, cite and review what must be asserted, generate
runtime metadata from structured artifacts, and make remaining gaps visible.

Classic Mac OS/m68k is tracked separately in
`docs/proposals/012-classic-mac-os-m68k-platform.md`. That proposal is a
cross-platform pressure test for the same platform architecture, not part of
this Atari ST cleanup.

## Checkpoint Index

- [ ] Clean Target Model
- [ ] Why This Exists
- [ ] Current Inputs
- [ ] Source Inventory Schema
- [ ] Source Tier Policy
- [ ] Tutorial: Build The Atari Platform KB Report
- [ ] Tutorial: Normalize Existing Atari ST Parsers
- [ ] Tutorial: Add Corrections And Parser Assertions
- [ ] Tutorial: Evaluate External Sources
- [ ] Tutorial: Generate Runtime Metadata
- [ ] Tutorial: Target-Driven Gap Reporting
- [ ] Larger Architecture Observations
- [ ] Implementation Slices
- [ ] Artifact Ownership
- [ ] Non-Goals
- [ ] Acceptance Criteria
- [ ] Verification Plan
- [ ] Deletion Checklist

## Clean Target Model

The best clean version is a platform knowledge chain:

```text
local sources / discovered internet sources
  -> source inventory with availability, tier, and decision
  -> parser extraction where possible
  -> cited parser assertions or reviewed corrections where necessary
  -> knowledge/atari_st_*.json
  -> generated src/generated/atari_st_*.c/.h
  -> C loader, analyzer, renderer, writer, and reproduction consumers
  -> report/check and target gap feedback
```

The contract for every runtime fact is:

```text
fact used by runtime code
  has one owning structured KB entry
  has one source inventory record or correction record
  has provenance and review state
  is carried into generated runtime metadata
  is checked for drift and missing citation
```

Runtime code should not know whether a name came from Devpac, EmuTOS, Hatari,
an official PDF, or a reviewed correction. Runtime code should only consume
generated tables.

Provenance belongs in reports and review tools:

```c
/* desired C shape: generated facts only */
const AtariStOsCallInfo *call = atari_st_os_find_call(1, opcode);
if (call != NULL) {
    render_symbol(atari_st_os_name(ATARI_ST_OS_NAME_DOMAIN_SYMBOL, call->symbol_id));
}
```

The generator may know how to emit C. It should not be the long-term owner of
platform truth:

```python
# desired Python shape: generator reads structured facts
facts = load_json("knowledge/atari_st_os_parsed.json")
corrections = load_json("knowledge/atari_st_corrections.json")
emit_atari_st_os_runtime(merge_reviewed_facts(facts, corrections))
```

## Why This Exists

The project already has useful Atari ST support:

- PRG/TOS/TTP loading
- GEMDOS disk handling
- generated PRG and disk format runtime helpers
- OS trap naming
- Devpac include files
- round-trip and backend tests

The problem is not absence of support. The problem is mixed ownership:

```text
some facts are in committed JSON
some facts are parsed from local external sources
some facts live in generator logic
some facts are in local notes
some facts may be hardcoded in C
some facts depend on untracked source clones
```

The proposal exists to make those boundaries visible first, then move toward
one auditable model.

## Current Inputs

Committed Atari ST knowledge:

```text
knowledge/atari_st_prg_file.json
knowledge/atari_st_disk_file.json
src/generated/atari_st_prg_file_runtime.*
src/generated/atari_st_disk_file_runtime.*
src/generated/atari_st_os_runtime.*
```

Committed Devpac include sources:

```text
ext/atarist_includes/devpac_3_10/include/AESLIB.S
ext/atarist_includes/devpac_3_10/include/BIOS.I
ext/atarist_includes/devpac_3_10/include/GEMDOS.I
ext/atarist_includes/devpac_3_10/include/GEMMACRO.I
ext/atarist_includes/devpac_3_10/include/VDILIB.S
ext/atarist_includes/devpac_3_10/include/XBIOS.I
```

Optional or required local Atari ST sources currently used or referenced:

```text
resources/platform_atari_st/GEMDOS.TXT
resources/platform_atari_st/GEM_0042.pdf
resources/platform_atari_st/atari_st_disassembly_hints.json
resources/platform_atari_st/atari_st_hardware_registers.md
resources/platform_atari_st/atari_st_programming_notes.md
resources/clone_atari_st/emutos
resources/clone_atari_st/hatari
```

These Atari ST local source requirements are not yet documented in
`RESOURCES.md`. Slice 1 must add that documentation with expected paths,
acquisition notes, redistribution limits, and the generated artifacts that
depend on each source.

Current OS generation starts in:

```text
src/scripts/generate_atari_st_os_runtime.py
```

That script parses selected EmuTOS headers/docs and Devpac include equates for
GEMDOS, BIOS, and XBIOS. It also contains generator-owned rules about return
kinds, cleanup bytes, include mapping, name domains, and supported families.
Those rules must be audited and moved into structured facts where practical.

## Source Inventory Schema

Add:

```text
knowledge/atari_st_source_inventory.json
```

The inventory should keep separate fields for separate concerns. Do not collapse
availability, extraction state, review state, and planning decision into one
status.

Suggested shape:

```json
{
  "schema_version": 1,
  "sources": [
    {
      "id": "devpac-3.10-gemdos-i",
      "title": "Devpac 3.10 GEMDOS.I",
      "publisher": "HiSoft",
      "domain": ["gemdos", "trap-symbols", "include-symbols"],
      "tier": 1,
      "path": "ext/atarist_includes/devpac_3_10/include/GEMDOS.I",
      "url": null,
      "availability": "committed",
      "machine_readable": true,
      "citation_quality": "line",
      "parser_feasibility": "direct",
      "extraction_status": "parsed",
      "review_status": "not_applicable",
      "decision": "parse",
      "license_notes": "Committed project input; verify redistribution basis.",
      "known_conflicts": []
    },
    {
      "id": "emutos-bdosbind",
      "title": "EmuTOS bdosbind.h",
      "publisher": "EmuTOS project",
      "domain": ["gemdos", "trap-bindings"],
      "tier": 2,
      "path": "resources/clone_atari_st/emutos/include/bdosbind.h",
      "url": "https://github.com/emutos/emutos",
      "availability": "required_local",
      "machine_readable": true,
      "citation_quality": "line",
      "parser_feasibility": "direct",
      "extraction_status": "parsed",
      "review_status": "not_applicable",
      "decision": "parse",
      "license_notes": "Local clone required for regeneration.",
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

`missing_external` is an observed availability state, not a source decision.
`check` should fail only when the missing source is required for the selected
regeneration or check scope.

## Source Tier Policy

Tier 1:

- Official Atari / Digital Research docs, SDKs, headers, and Devpac-distributed
  includes.

Tier 2:

- EmuTOS source for documented TOS/GEMDOS/AES/VDI behavior where official
  material is incomplete.
- Hatari source where it models loader, trap, disk, symbol, or hardware
  behavior and no better official source is available.
- VASM/toolchain source and docs for executable/object formats or assembler
  compatibility.
- Well-known Atari ST programming references that are text-searchable and
  attributable.

Tier 3:

- Old PDFs, scans, web pages, forum posts, and recovered include files.

Tier 3 sources may be used only with provenance, citation quality, confidence,
review status, and a parser-replacement path.

Rule:

```text
No new Atari ST platform fact should be added directly to C consumers.
Facts must come from structured KB artifacts generated from parsed sources,
or from cited parser-asserted/correction records where parsing is not practical.
```

EmuTOS and Hatari are reference implementations, not official specifications.
When they supply behavior that official material does not cover, the inventory
record must say so explicitly.

## Tutorial: Build The Atari Platform KB Report

Start with a read-only command:

```powershell
uv run atari-platform-kb report
uv run atari-platform-kb check
```

The report is the first useful artifact because it makes current debt visible
without requiring broad parser work.

Initial report sections:

```text
Atari ST Platform KB

Source inventory:
  committed: 8
  required_local: 3
  missing_external: 1
  parsed: 5
  candidate: 4
  deferred: 2

Format KB:
  PRG JSON: knowledge/atari_st_prg_file.json
  disk JSON: knowledge/atari_st_disk_file.json
  generated drift: none
  consumers: loader, writer, reproduction comparison

OS KB:
  GEMDOS: parsed Devpac + EmuTOS rows
  BIOS: parsed Devpac + EmuTOS rows
  XBIOS: parsed Devpac + EmuTOS rows
  AES/VDI: inventoried, not fully parsed
  generated drift: none

Corrections:
  seeded: 0
  validated: 0
  missing citation: 0

Hardware:
  source inventory: partial
  generated/runtime coverage: none
  target gap candidates: count only

Consumers:
  loader
  disk parser
  source renderer
  analyzer
  reproduction comparison
```

Strict checks should fail on:

```text
duplicate source ids
unknown availability / extraction_status / review_status / decision values
required local sources missing for selected scope
uncited parser assertions or corrections
unknown correction review statuses
hand-authored facts consumed by generators without provenance
generated artifact drift
malformed source inventory records
```

The first slice should not require internet access or new source parsing. It
should read the repo, report current state, and document missing local sources.

## Tutorial: Normalize Existing Atari ST Parsers

The existing OS generator already does real extraction. Normalize that work
before expanding scope.

Current source flow:

```text
EmuTOS bdosbind.h / biosbind.h / xbiosbind.h
EmuTOS doc/status.txt
Devpac GEMDOS.I / BIOS.I / XBIOS.I
  -> src/scripts/generate_atari_st_os_runtime.py
  -> src/generated/atari_st_os_runtime.c/.h
```

Clean source flow:

```text
source inventory
  -> parser extraction
  -> knowledge/atari_st_os_parsed.json
  -> generator
  -> src/generated/atari_st_os_runtime.c/.h
```

Candidate parsed OS shape:

```json
{
  "schema_version": 1,
  "calls": [
    {
      "family": "GEMDOS",
      "trap_vector": 1,
      "opcode": 61,
      "function_name": "Fopen",
      "symbol_name": "Fopen",
      "include_path": "GEMDOS.I",
      "source_id": "devpac-3.10-gemdos-i",
      "citation": {
        "path": "ext/atarist_includes/devpac_3_10/include/GEMDOS.I",
        "line": 42
      },
      "return_kind": "long",
      "cleanup": {
        "known": false,
        "bytes": null
      }
    }
  ]
}
```

Audit generator-owned rules:

```text
family include path mapping
original include filename mapping
trap vector per family
return kind inference
cleanup byte inference
name domain ids
supported families
symbol fallback names
```

Some of these are generator mechanics. Others are platform facts. Platform
facts should move to parsed JSON or corrections.

## Tutorial: Add Corrections And Parser Assertions

Add:

```text
knowledge/atari_st_corrections.json
```

Use corrections for:

- facts implied by source material but not directly parseable
- scan/PDF-derived facts not yet parseable
- conflicts between Devpac includes, EmuTOS, Hatari, and docs
- temporary hand-authored facts needed by generators

Suggested shape:

```json
{
  "schema_version": 1,
  "corrections": [
    {
      "id": "gemdos-fopen-cleanup-unknown",
      "category": "os_call_cleanup",
      "review_status": "seeded",
      "source_id": "emutos-bdosbind",
      "citation": {
        "path": "resources/clone_atari_st/emutos/include/bdosbind.h",
        "line": 120
      },
      "fact": {
        "family": "GEMDOS",
        "opcode": 61,
        "cleanup_known": false
      },
      "rationale": "Macro signature exposes trap call but not enough stack cleanup detail.",
      "parser_replacement_path": "Parse helper macro signatures or official binding docs.",
      "reviewer": null,
      "reviewed_date": null
    }
  ]
}
```

Commands should mirror the Amiga correction flow unless Atari ST needs a
specific divergence:

```powershell
uv run atari-platform-kb corrections list
uv run atari-platform-kb corrections check
uv run atari-platform-kb corrections promote <correction_id> --reviewer <name>
```

Promotion rule:

```text
seeded -> validated requires citation, source_id, rationale, reviewer, date
validated entries keep source and citation
unknown review_status fails check
seeded consumed facts stay visible as review debt
```

Parser assertions are acceptable when the source implies a fact but does not
state it in directly parseable form. They must cite the source and explain the
assertion. Downstream generators read parser assertions like any other parsed
fact; only reports distinguish the provenance.

## Tutorial: Evaluate External Sources

Source discovery is an implementation slice, not background research. The
output is committed inventory, not private notes.

Evaluation questions:

```text
Does this source improve a current domain?
Can it be parsed?
Can it be cited precisely?
Does it conflict with current KB?
Can it be mirrored or only referenced?
Should it become parsed input, cited correction input, deferred inventory, or
unsupported inventory?
```

Example inventory decision:

```json
{
  "id": "hatari-loader-source",
  "title": "Hatari PRG loader implementation",
  "publisher": "Hatari project",
  "domain": ["prg-loader", "symbol-table", "relocation"],
  "tier": 2,
  "path": "resources/clone_atari_st/hatari",
  "url": "https://git.tuxfamily.org/hatari/hatari.git",
  "availability": "optional_local",
  "machine_readable": true,
  "citation_quality": "line",
  "parser_feasibility": "targeted",
  "extraction_status": "candidate",
  "review_status": "not_applicable",
  "decision": "defer",
  "license_notes": "Reference implementation; use local clone for cited reads.",
  "known_conflicts": []
}
```

Local notes need the same treatment:

```text
resources/platform_atari_st/atari_st_hardware_registers.md
  -> promote durable facts into structured KB with citations
  -> keep narrative context as notes
  -> mark stale or deferred facts explicitly
```

## Tutorial: Generate Runtime Metadata

Generated runtime artifacts should be reproducible from structured inputs:

```powershell
uv run python src\scripts\generate_platform_format_runtime.py
uv run python src\scripts\generate_atari_st_os_runtime.py
```

The clean end state may split parsing and generation:

```powershell
uv run atari-platform-kb extract
uv run atari-platform-kb generate
uv run atari-platform-kb check
```

That split is only worth doing after the report identifies current parser and
generator ownership clearly.

Runtime generation cleanup should make these true:

```text
PRG/disk runtime facts come from knowledge/atari_st_prg_file.json and
knowledge/atari_st_disk_file.json.

OS runtime facts come from knowledge/atari_st_os_parsed.json plus reviewed
corrections.

C consumers include generated headers and do not embed new Atari ST fact maps.

Generated files carry source comments naming their structured KB inputs.
```

## Tutorial: Target-Driven Gap Reporting

Hardware and machine variant knowledge can sprawl. Do not start with broad
hardware extraction. Start with target evidence.

Add:

```powershell
uv run atari-platform-kb target-gaps <target>
```

Gap grouping:

```text
GEMDOS / BIOS / XBIOS trap call
AES / VDI call or macro
Devpac include constant
PRG loader / relocation / symbol-table metadata
GEMDOS disk structure
hardware register or memory map
unknown platform-looking value
```

Example output:

```text
Atari ST target gaps: carrier-command-st

Trap calls:
  trap #1 opcode 0x3d: named by Devpac, missing cleanup metadata

Hardware-looking addresses:
  $ff8240: candidate palette register, source not yet inventoried

PRG metadata:
  symbol table present, Hatari loader behavior candidate source
```

Target gaps should feed source discovery and parser expansion. If no current
target needs a hardware area, inventory it but defer extraction.

## Larger Architecture Observations

### 1. Runtime Consumers Should Not Know Provenance

Loader, analyzer, renderer, writer, and reproduction code should read generated
metadata. They should not care which source produced it.

This keeps runtime behavior stable while provenance improves:

```text
old source replaced by better source
  -> parsed JSON changes
  -> generated runtime changes
  -> consumers stay unchanged
```

### 2. Weak Sources Need Stronger Metadata

Atari ST will sometimes need weaker sources than Amiga. The answer is not to
avoid them. The answer is stronger provenance:

```text
source tier
citation
parser feasibility
review status
known conflicts
parser replacement path
```

### 3. Corrections Are Review Debt, Not Shame

Seeded corrections are useful when they unblock generation honestly. They
become harmful only when reports stop showing them.

### 4. Parser Expansion Should Follow Real Pressure

Parser work should follow target evidence and consumer needs:

```text
unresolved trap call
unknown include constant
suspicious PRG metadata
hardware-looking absolute address
disk/filesystem edge case
```

This avoids building a full Atari ST encyclopedia before the disassembly work
needs it.

### 5. This Is A Platform Pattern

This proposal should leave behind a reusable shape for weaker platforms:

```text
inventory
corrections
parsed facts
generated runtime metadata
target gaps
report/check
```

Classic Mac OS/m68k should be able to reuse the same conceptual architecture
even if the source material differs.

## Implementation Slices

### Slice 1: Source Inventory, Resources Documentation, And Audit Report

Add:

```text
knowledge/atari_st_source_inventory.json
atari-platform-kb report
atari-platform-kb check
RESOURCES.md Atari ST source entries
```

The report should read current committed artifacts, documented external-source
requirements, generated outputs, provenance gaps, and consumers. It should not
require internet access or new source parsing.

### Slice 2: Local Parser Normalization

Audit `src/scripts/generate_atari_st_os_runtime.py` and the platform format
generation path. Identify parsed facts, generator mechanics, parser assertions,
and hardcoded platform facts.

Move the first useful OS parsed output toward:

```text
knowledge/atari_st_os_parsed.json
```

### Slice 3: Devpac Include Parser Expansion

Normalize parsing for:

```text
GEMDOS.I
BIOS.I
XBIOS.I
AESLIB.S
VDILIB.S
GEMMACRO.I
```

Start with inventory and coverage reporting. Expand consumers only after parsed
facts are stable.

### Slice 4: EmuTOS And Hatari Extraction

Keep roles separate:

```text
EmuTOS:
  OS calls, loader behavior, structs/constants where official docs are weak

Hatari:
  emulator-observed loader/symbol/disk/hardware behavior where no better source
  exists
```

Do not blend official docs, reference implementation behavior, and emulator
behavior into one undifferentiated fact.

### Slice 5: Corrections Review Flow

Add:

```text
knowledge/atari_st_corrections.json
atari-platform-kb corrections list
atari-platform-kb corrections check
atari-platform-kb corrections promote <id> --reviewer <name>
```

Seeded corrections are visible review debt. Validated corrections require
source, citation, rationale, reviewer, and date.

### Slice 6: Runtime Generation Cleanup

Move hardcoded generator facts into parsed or correction data where practical.
Regenerate:

```text
src/generated/atari_st_prg_file_runtime.*
src/generated/atari_st_disk_file_runtime.*
src/generated/atari_st_os_runtime.*
```

### Slice 7: Target Gap Report

Add target-driven Atari ST gap reporting. Use real targets or fixtures to group
unresolved platform-looking values by likely owner.

### Slice 8: Internet Source Discovery And Evaluation

Evaluate external sources deliberately. Commit inventory rows with tier,
availability, parser feasibility, citation quality, and decision.

### Slice 9: Hardware And Machine-Variant Inventory

Inventory ST/STe/TT/Falcon hardware and machine-variant sources. Parse only
areas justified by target gaps or current consumers.

### Slice 10: Final Tracking Cleanup

Promote durable issue notes into this proposal. Delete completed
`docs/issues/011-*` issue files. Remove stale TODOs.

## Artifact Ownership

Expected artifacts:

```text
knowledge/atari_st_source_inventory.json
knowledge/atari_st_corrections.json
knowledge/atari_st_prg_file.json
knowledge/atari_st_disk_file.json
knowledge/atari_st_os_parsed.json         (candidate)
knowledge/atari_st_includes_parsed.json   (candidate)
src/generated/atari_st_*.c/.h
docs/proposals/011-atari-st-platform-knowledge.md
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

- Do not build a full Atari ST NDK replacement before auditing current sources.
- Do not add uncited platform facts directly to C consumers.
- Do not treat scans, web pages, or forum posts as validated facts without
  provenance and review status.
- Do not start broad hardware extraction before target gaps justify it.
- Do not make compiler fingerprinting part of this proposal.
- Do not require live internet access for ordinary report/check commands.
- Do not rely on private research notes that are not committed to the repo.

## Acceptance Criteria

- Current Atari ST source inventory is visible in one report.
- Atari ST local/external source requirements are documented in `RESOURCES.md`.
- Current generated Atari ST runtime artifacts can be traced to KB artifacts
  and source inventory.
- Devpac includes, EmuTOS, Hatari, GEMDOS docs, and local notes have explicit
  source roles.
- Inventory fields distinguish availability, extraction status, review status,
  and decision.
- Corrections distinguish `seeded` and `validated` review states.
- `atari-platform-kb check` fails on uncited consumed facts, unknown inventory
  field values, required external sources missing for selected scope, malformed
  correction metadata, and generated drift.
- Runtime consumers do not gain new handcoded Atari ST platform facts.
- Internet-discovered sources become committed inventory with tier and decision
  metadata.
- Hardware expansion is driven by target gap evidence unless a current consumer
  requires it.

## Verification Plan

Minimum verification:

```text
focused tests for atari-platform-kb report/check
focused tests for each parser/generator touched
uv run atari-platform-kb report
uv run atari-platform-kb check
cmd /c src\precommit.bat
```

Additional verification by touched area:

```text
format runtime generation:
  platform format codegen tests for atari_st_prg_file and atari_st_disk_file

OS runtime generation:
  tests proving GEMDOS/BIOS/XBIOS rows preserve source/provenance
  tests proving generated atari_st_os_runtime artifacts are current

corrections:
  list/check/promote tests

target gaps:
  fixture target with unresolved trap/include/hardware-looking values

internet source inventory:
  tests for source tier, URL/local mirror, parser feasibility, and decision

resources documentation:
  test or check that required_local inventory rows have RESOURCES.md coverage
```

## Deletion Checklist

Before closing this proposal:

- Promote durable issue reasoning into this proposal.
- Delete completed `docs/issues/011-*` issue files.
- Remove stale TODO entries.
- Ensure `atari-platform-kb report/check` are documented.
- Ensure generated artifacts are current.
- Record skipped external checks and why.

## Verification

Draft created after a repo-backed source read. Cohesion rewrite applied to make
the proposal read from clean target model to detailed implementation slices.
