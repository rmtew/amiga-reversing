# Proposal 004: Amiga Platform Knowledge

Status: Ready for Proposal 004 follow-up implementation.
Status changed: 2026-05-17.

The Amiga platform KB work is no longer a broad "parse more ADCD" proposal.
The useful path is narrower: make current platform facts auditable, reviewable,
and generated all the way into the consumers that need them.

Follow-up implementation lives in `docs/issues/030-*`. This proposal is the
durable spec.

## Checkpoint Index

- [ ] Why This Exists
- [ ] Mental Model
- [ ] Current State Read
- [ ] Integration Findings
  - [ ] 1. The NDK Parser Is Already The Strongest Part
  - [ ] 2. Hardware Knowledge Has Two Different Sources
  - [ ] 3. Corrections Have Provenance But No Workflow
  - [ ] 4. HUNK Runtime Metadata Is Not Used Everywhere
  - [ ] 5. `HUNK_OVERLAY` Is Half-Represented
  - [ ] 6. Target Gaps Do Not Drive Parser Expansion Yet
- [ ] Tutorial: Platform KB Coverage Report
- [ ] Tutorial: Corrections Review Flow
- [ ] Larger Architecture Observations
- [ ] Forward Implementation Model
- [ ] Non-Goals
- [ ] Proposed Rewrite
  - [ ] Slice 1: Platform KB Coverage Report
  - [ ] Slice 2: Corrections Review Flow
  - [ ] Slice 3: Generated HUNK Comparison Helpers
  - [ ] Slice 4: Resolve `HUNK_OVERLAY`
  - [ ] Slice 5: Target-Driven Platform Gap Report
- [ ] Acceptance Criteria
- [ ] Deletion Checklist
- [ ] Rewrite Acceptance Tests
- [ ] Verification

## Why This Exists

The project renders and analyzes Amiga binaries. To do that well it needs
Amiga-specific facts:

- OS libraries, functions, structures, constants, and version metadata.
- Hardware register names, bitfields, and include-backed symbols.
- HUNK container record ids, relocation kinds, and load-file structure.
- Corrections for source material that is sparse, inconsistent, or split across
  NDK files.

Those facts should be parser-owned and generated into runtime tables. Renderers,
analysis code, and reproduction comparison should consume those tables. They
should not reimplement Amiga platform knowledge locally.

## Mental Model

Think of the platform KB as a contract chain:

```text
ADCD / NDK / HRM source inventory
  -> parser extraction and cited parser assertions
  -> knowledge/*.json platform KB artifacts
  -> generated C/runtime metadata
  -> renderer, analyzer, loader, writer, and reproduction consumers
  -> coverage reports and target-driven gap reports
```

The important question is not "how much ADCD have we parsed?" It is:

```text
For every platform fact used by runtime code:
  Which source owns it?
  Was it parsed, parser-asserted, seeded, or validated?
  Which generated artifact carries it?
  Which consumer relies on it?
  Is missing or unsupported state explicit?
```

That makes the platform KB a traceability problem first and a parsing problem
second.

## Current State Read

The current implementation already has substantial NDK extraction:

```text
parsed include paths:      170
libraries:                 43
functions:                 1114
structs:                   334
constants:                 8600
value domains:             11
include min-version rows:  128
compatibility versions:    4
```

The separate NDK "other" metadata currently reports function release markers:

```text
1.1:   3
1.2:   55
1.3:   381
2.0:   435
2.04:  15
2.1:   38
3:     80
3.0:   1
3.1:   106
```

That means the old TODO note about "570 1.3 functions" is stale. There is
still version trust debt, but the parser has already refined a large part of
the original gap.

Hardware knowledge is present but uneven:

```text
hardware registers:        245
registers with bit data:   104
NDK hardware symbols:      133
```

Corrections have provenance but weak process:

```text
corrections with review_status=seeded:     19
corrections with review_status=validated:  1
```

HUNK metadata is split:

- `knowledge/amiga_hunk_file.json` defines the `HUNK_OVERLAY` enum id and also
  lists it in `load_file_valid_record_types`.
- The generated C/header runtime metadata has no `HUNK_OVERLAY` record kind or
  lookup case.
- `knowledge/amiga_hunk_format.md` documents an overlay payload shape.
- No primary-source fixture or parser test currently proves overlay support.

Runtime consumers are not equally clean. `src/platform_amiga_hunk.c` consumes
generated HUNK runtime metadata, but `src/m68k_reproduction_compare.c` still
hardcodes HUNK ids and skip logic.

## Integration Findings

### 1. The NDK Parser Is Already The Strongest Part

`src/scripts/kb/ndk_parser.py` parses FD files, autodocs, assembler includes,
type macros, OS changes, value domains, struct field bindings, and compatibility
metadata. `tests/test_parse_ndk.py` already covers many of these facts.

The follow-up should not treat the NDK parser as missing. It should make its
output easier to audit and use.

### 2. Hardware Knowledge Has Two Different Sources

Hardware register extraction and NDK include symbol extraction are related but
not identical:

```text
HRM register facts:
  addresses, register widths, descriptions, some bitfields

NDK include symbols:
  custom chip names, CIA aliases, equates, bit macros, source ownership
```

The clean model is a coverage report that shows both sources and the join
between them. Broadly adding more include families before a target needs them is
low value.

### 3. Corrections Have Provenance But No Workflow

`knowledge/amiga_ndk_corrections.json` records seeded and validated facts, but
generation consumes them the same way. That is acceptable only while the review
debt is visible.

The missing piece is a command that lists seeded corrections, exposes citations,
and promotes entries only through an explicit review action.

### 4. HUNK Runtime Metadata Is Not Used Everywhere

The platform HUNK loader uses generated runtime metadata. Reproduction
comparison does not. It still carries local constants for HUNK ids, relocation
classification, section detection, and skippable records.

That duplicates platform format knowledge downstream from the KB. The rewrite
should move comparison onto generated helpers and delete the hardcoded HUNK
tables from `src/m68k_reproduction_compare.c`.

### 5. `HUNK_OVERLAY` Is Half-Represented

`HUNK_OVERLAY` is currently neither cleanly supported nor cleanly unsupported.
It is in the enum and valid-record list, but not in normalized record metadata.

Target behavior:

```text
Either:
  add cited record metadata plus fixture coverage

Or:
  remove it from valid load-file records and report it as explicit unsupported
  inventory until primary-source evidence exists
```

The current halfway state should not remain.

### 6. Target Gaps Do Not Drive Parser Expansion Yet

The project already has enough platform KB data to render many names and
constants. What is missing is a report that says:

```text
This target produced unresolved platform-looking values.
They resemble this include family or hardware range.
Parse or correct this source next.
```

That report should drive future include parsing and correction work.

## Tutorial: Platform KB Coverage Report

Start by making current state visible. Add a report command that reads existing
generated KB artifacts and prints a stable summary.

Canonical command surface:

```powershell
uv run amiga-platform-kb report
uv run amiga-platform-kb check
```

`report` is human-readable and does not fail merely because gaps exist. `check`
is strict and fails only for conditions that are meant to be enforced in the
current slice.

Initial report sections:

```text
Source inventory:
  ADCD inventory entries
  parsed source families
  candidate/deferred source families

NDK:
  include paths
  libraries
  functions
  function available_since counts
  structs
  constants
  value domains
  include min-version rows

Hardware:
  HRM registers
  HRM registers with bit definitions
  NDK hardware symbols
  joined/custom/CIA coverage

Corrections:
  seeded
  validated
  missing citation
  unknown review status

HUNK:
  enum ids
  normalized record types
  valid load-file record types
  unsupported or half-represented records
```

The report should use parsed JSON artifacts. It should not require an installed
NDK tree just to audit the current repository state.

## Tutorial: Corrections Review Flow

Corrections should remain useful, but review state must be operational rather
than decorative.

Read-only listing command:

```powershell
uv run amiga-platform-kb corrections list
```

Expected fields:

```text
id
category
symbol/function/structure
review_status
source file
citation
reason
```

Promotion command:

```powershell
uv run amiga-platform-kb corrections promote <id> --reviewer <name>
```

Promotion rules:

```text
seeded -> validated requires citation
validated entries keep source and citation
unknown review_status fails check
missing citation fails check
generation may consume corrections, but reports must distinguish seeded debt
```

This keeps parser-owned generated facts simple while preventing seeded
corrections from becoming invisible.

## Larger Architecture Observations

### 1. The Platform KB Needs A Source Map

`knowledge/adcd21_inventory.md` is useful, but source ownership should be
machine-readable enough for reports. The source map should distinguish:

```text
parsed
parser_asserted
seeded_correction
validated_correction
candidate
deferred
unsupported
```

### 2. Consumers Should Not Know Source Provenance

Renderers and analyzers should consume generated tables. They should not care
whether a name came from an NDK include, an autodoc overlay, HRM extraction, or
a validated correction. Provenance belongs in reports and review tools.

### 3. HUNK Runtime Metadata Should Own Container Decisions

Loader, writer, and reproduction comparison all need record ids and skip
classification. Those facts should come from generated HUNK metadata.

If a record is unsupported, that status should also be metadata, not a missing
case hidden in a C switch.

### 4. Parser Expansion Should Be Target-Led

Parsing more ADCD is useful only when it improves current reversing work or
removes visible platform gaps. The project should prefer small source-family
expansions tied to target reports over broad speculative ingestion.

## Forward Implementation Model

### Source Inventory

Promote enough source inventory into machine-readable form for coverage reports.
Markdown can remain the human narrative, but counts and statuses should come
from structured data.

### Platform KB Coverage Report

Build one command that summarizes NDK, hardware, corrections, and HUNK state
from committed artifacts.

### Corrections Review

Add a small command surface for listing and promoting corrections. Keep the JSON
format simple and preserve citations.

### HUNK Metadata Helpers

Generate helper functions for:

```text
record id -> record metadata
record id -> load-file validity
record id -> skippable/debug/symbol/relocation category
record id -> section/data/bss category
relocation id -> relocation width/kind
```

Then replace local reproduction-comparison HUNK knowledge with those helpers.

### Overlay Support State

Resolve `HUNK_OVERLAY` in one issue. If primary-source evidence and fixtures are
available, support it. If not, remove it from valid record types and record it
as unsupported inventory.

### Target Platform Gap Report

Add a report that groups unresolved platform-looking target output by likely
owner:

```text
custom chip address range
CIA address range
exec.library / dos.library / graphics.library style LVO
known include family
unknown absolute platform-looking value
```

Use that report to choose future parser expansions.

## Non-Goals

- Broad ADCD expansion without a target-driven gap.
- HUNK overlay support without primary-source evidence or fixture coverage.
- Compatibility shims for old generated artifact shapes.
- Runtime consumers that reimplement platform facts already present in the KB.
- Treating seeded corrections as fully reviewed facts in reports.

## Proposed Rewrite

### Slice 1: Platform KB Coverage Report

Tracked by `docs/issues/030-001-add-platform-kb-coverage-report.md`.

Add `amiga-platform-kb report` and `amiga-platform-kb check`. The first slice is
mostly read-only: it should report current NDK, hardware, corrections, source
inventory, and HUNK coverage from committed artifacts.

### Slice 2: Corrections Review Flow

Tracked by `docs/issues/030-002-add-amiga-ndk-corrections-review-flow.md`.

Add commands/tests for listing seeded corrections and promoting them to
validated with preserved citation and review provenance.

### Slice 3: Generated HUNK Comparison Helpers

Tracked by `docs/issues/030-003-generate-hunk-comparison-from-platform-runtime-metadata.md`.

Generate or expose HUNK helper functions from platform format metadata and move
`src/m68k_reproduction_compare.c` onto those helpers. Delete duplicated HUNK
constants and local skip classification.

### Slice 4: Resolve `HUNK_OVERLAY`

Tracked by `docs/issues/030-004-resolve-hunk-overlay-support-state.md`.

Make overlay state explicit. Prefer unsupported inventory unless the issue adds
primary-source layout evidence and fixture tests in the same change.

### Slice 5: Target-Driven Platform Gap Report

Tracked by `docs/issues/030-005-add-target-driven-platform-gap-report.md`.

Report unresolved platform-looking symbols and addresses by likely owner so
future KB parsing follows observed target needs.

## Acceptance Criteria

- Current platform KB state is visible through one report command.
- Strict checks fail on malformed correction metadata and half-represented HUNK
  record state.
- `src/m68k_reproduction_compare.c` no longer hardcodes HUNK ids or record
  categories that generated HUNK metadata can provide.
- `HUNK_OVERLAY` is either supported with cited fixture coverage or explicitly
  unsupported.
- Future include/source expansion is driven by target gap reports.

## Deletion Checklist

When a `030-*` issue is completed:

- Promote any durable reasoning back into this proposal.
- Delete the issue file if it is completed, abandoned, or superseded.
- Remove stale TODO entries that the report/check now owns.
- Keep generated artifacts and source inventory consistent.

## Rewrite Acceptance Tests

Minimum verification for code-changing follow-up issues:

```text
focused tests for the changed report/review/runtime behavior
uv run amiga-platform-kb report
uv run amiga-platform-kb check
cmd /c src\precommit.bat
```

Additional verification by touched area:

```text
NDK/parser changes:
  uv run python -m pytest tests\test_parse_ndk.py -q

corrections review:
  focused CLI/unit tests for list, check, and promote behavior

HUNK runtime metadata:
  regenerate platform format runtime artifacts
  run C tests touching platform HUNK loader/writer/comparison

target gap reporting:
  fixture target with known platform-looking unresolved values
```

If a required external tool is unavailable, the issue is not silently done.
Record the skipped command, why it could not run, and what narrower available
check was run instead.

## Verification

This proposal was reviewed against current repository artifacts on 2026-05-17.
No implementation is claimed here beyond the proposal and issue rewrite.
