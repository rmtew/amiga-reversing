# Proposal 004: Amiga Platform Knowledge

Status: Ready for Proposal 004 follow-up implementation.
Status changed: 2026-05-17.

The Amiga platform KB work is no longer a broad "parse more ADCD" proposal.
The useful path is narrower: make current platform facts auditable, reviewable,
and generated all the way into the consumers that need them. The visible
outcome is not only better names. It is a coherent platform summary for each
target: memory map, OS compatibility, hardware/OS usage, unsupported container
state, and target-driven KB gaps.

Follow-up implementation lives in `docs/issues/004-*`. This proposal is the
durable spec.

## Checkpoint Index

- [ ] Why This Exists
- [ ] Mental Model
- [ ] Current State Read
- [ ] Integration Findings
  - [ ] 1. The NDK Parser Is Already The Strongest Part
  - [ ] 2. Hardware Knowledge Has Two Different Sources
  - [x] 3. Corrections Have Provenance And A Review Workflow
  - [x] 4. OS Compatibility Data Exists As A Target Summary
  - [x] 5. HUNK Runtime Metadata Owns Container Decisions
  - [x] 6. `HUNK_OVERLAY` Is Explicitly Unsupported
  - [x] 7. Target Gaps Can Drive Parser Expansion
- [ ] Tutorial: Platform KB Coverage Report
- [ ] Tutorial: Target OS Compatibility Summary
- [x] Tutorial: Corrections Review Flow
- [ ] Larger Architecture Observations
- [ ] Forward Implementation Model
- [ ] Non-Goals
- [ ] Proposed Rewrite
  - [ ] Slice 1: Platform KB Coverage Report
  - [x] Slice 2: Target OS Compatibility Summary
  - [x] Slice 3: Corrections Review Flow
  - [x] Slice 4: Generated HUNK Comparison Helpers
  - [x] Slice 5: Resolve `HUNK_OVERLAY`
  - [x] Slice 6: Target-Driven Platform Gap Report
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
- Target-level platform summaries: memory map, observed OS/API compatibility,
  interface versions, and platform gaps.

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
  -> target platform summary
  -> source header, web summary, export metadata, reports, and gap reports
```

The important question is not "how much ADCD have we parsed?" It is:

```text
For every platform fact used by runtime code:
  Which source owns it?
  Was it parsed, parser-asserted, seeded, or validated?
  Which generated artifact carries it?
  Which consumer relies on it?
  What target-level compatibility does observed use imply?
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

OS compatibility metadata now exists in generated runtime metadata and the
source-analysis target platform summary:

- `knowledge/amiga_ndk_other_parsed.json` keeps finer `available_since` values
  such as `1.1`, `1.2`, `2.04`, `2.1`, `3.0`, and `3.1`.
- `src/generated/amiga_os_runtime.*` exposes compatibility helpers and stores
  raw `available_since`, normalized `available_since_version`, and `fd_version`
  on library vectors.
- Source analysis records recovered platform calls with `available_since` and
  `fd_version`.
- JSON output exposes those per-call fields plus `platform_summary`.
- Source export renders the C-generated memory map and OS compatibility header
  from the same analysis path.

The clean fix is not to restore a legacy string generator. The clean fix is to
make target OS compatibility a generated summary artifact, then render that
same artifact in the web UI, exported source, and reports.

Hardware knowledge is present but uneven:

```text
hardware registers:        245
registers with bit data:   104
NDK hardware symbols:      133
```

Corrections have provenance and an operational review flow:

```text
corrections with review_status=seeded:     19
corrections with review_status=validated:  1
commands: corrections list/check/promote
```

HUNK metadata is split:

- `knowledge/amiga_hunk_file.json` defines the `HUNK_OVERLAY` enum id and also
  lists it in `load_file_valid_record_types`.
- The generated C/header runtime metadata has no `HUNK_OVERLAY` record kind or
  lookup case.
- `knowledge/amiga_hunk_format.md` documents an overlay payload shape.
- No primary-source fixture or parser test currently proves overlay support.

Runtime consumers now share generated HUNK runtime metadata. The loader and
writer already consumed it, and reproduction comparison now uses generated HUNK
record lookup, section, terminator, relocation, EXT, and BSS/data
classification helpers instead of local HUNK id constants.

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

### 3. Corrections Have Provenance And A Review Workflow

`knowledge/amiga_ndk_corrections.json` records seeded and validated facts.
`amiga-platform-kb corrections list/check/promote` now makes that review state
operational: seeded review debt is visible, validated entries require review
provenance, and promotion records reviewer/date without changing source facts.

### 4. OS Compatibility Data Exists But Is Not A Target Summary

The parser and generated runtime still know about OS/API availability:

```text
raw available_since values:
  kept in parsed NDK JSON

runtime compatibility enum:
  used by generated C metadata

per-call recovered metadata:
  available_since and fd_version stored in source analysis
```

The missing piece is aggregation. A target should have one platform summary that
answers:

```text
Which OS/API versions are observed?
What minimum OS version is implied by the observed calls?
Which FD/interface versions are used?
Which calls force the maximum?
Which observed calls are suspicious for the target's expected era/profile?
```

This summary should own the source-header lines. The web UI and export path
should consume the same summary. Do not add separate UI/export/header
implementations that recompute compatibility.

The runtime model should preserve raw `available_since` text in addition to any
normalized enum/rank. Losing `1.2` into `1.3`, or `3.0` into `3.1`, makes the
summary less useful for fingerprinting and target review.

### 5. HUNK Runtime Metadata Owns Container Decisions

The platform HUNK loader, writer, and reproduction comparison now use generated
runtime metadata for record ids and record-category decisions. Comparison keeps
binary comparison policy locally, but HUNK format facts come from
`src/generated/amiga_hunk_file_runtime.*`.

### 6. `HUNK_OVERLAY` Is Explicitly Unsupported

`HUNK_OVERLAY` is now cleanly unsupported. It remains in the enum inventory for
diagnostics, is removed from valid load-file record types, and is listed in
unsupported record inventory until primary-source evidence and fixture coverage
exist.

Target behavior:

```text
Either:
  add cited record metadata plus fixture coverage

Or:
  remove it from valid load-file records and report it as explicit unsupported
  inventory until primary-source evidence exists
```

The previous halfway state should not return.

### 7. Target Gaps Can Drive Parser Expansion

The project already has enough platform KB data to render many names and
constants. `amiga-platform-kb target-gaps <target>` now gives a conservative
target-level report that says:

```text
This target produced unresolved platform-looking values.
They resemble this include family or hardware range.
Parse or correct this source next.
```

That report should drive future include parsing and correction work. Candidate
matches remain review inputs, not KB facts.

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
  raw function available_since counts
  normalized compatibility enum counts
  FD/interface version counts
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

## Tutorial: Target OS Compatibility Summary

The target summary is the clean replacement for the old compatibility header.
It is not a UI string and not an export-only decoration.

First create the target platform summary as the owner of generated header
content. Move the existing memory map header under that summary owner, then add
OS compatibility beside it. This avoids two independent header systems.

Build one generated-analysis summary from recovered platform calls and runtime
address facts:

```json
{
  "memory_map": {
    "ranges": []
  },
  "os_compatibility": {
    "minimum_required": "3.1",
    "status": "observed",
    "observed_available_since": ["1.3", "2.0", "3.1"],
    "observed_fd_versions": ["34", "36", "38", "40"],
    "expected_profile": {
      "source": "target_metadata",
      "minimum_expected": "1.3"
    },
    "maximum_required_calls": [
      {
        "library": "utility.library",
        "function": "GetUniqueID",
        "available_since": "3.1",
        "fd_version": "39",
        "section_index": 0,
        "offset": 1234
      }
    ]
  }
}
```

`status` values:

```text
observed:
  at least one recovered OS call has availability metadata

no_os_calls:
  no recovered OS calls were observed; do not infer an OS requirement

unknown:
  recovered OS calls exist, but none carry usable availability metadata
```

Version ordering must include raw Amiga OS availability values, not just the
current generated enum buckets:

```text
1.0 < 1.1 < 1.2 < 1.3 < 2.0 < 2.04 < 2.1 < 3.0 < 3.1 < 3.5
```

The normalized enum can still exist for fast comparisons, but the raw string and
rank are the canonical summary inputs. A raw `1.2` must not become `1.3` in
the target summary.

Render it in source as generated comments next to the memory map:

```asm
; OS compatibility
;   minimum required: 3.1
;   observed API availability: 1.3, 2.0, 3.1
;   observed FD/interface versions: v34, v36, v38, v40
;   max requirement drivers:
;     utility.library/GetUniqueID at section_0+$000004D2 requires 3.1, fd v39
```

Expose the same object in listing summary JSON so the web UI can show it without
parsing comments. Source export should include the C-rendered header rather than
building a second compatibility header in Python.

Expected target profile comes from explicit target metadata first. If absent,
the report may use disk/project year as a candidate hint, but it must mark that
source as inferred and must not fail checks on inferred expectations.

Implementation rules:

```text
raw availability string:
  kept from parser output when known

normalized compatibility rank:
  generated from the same model for comparisons and max calculation

no-call state:
  represented explicitly; never treated as "requires 1.0" or "requires 1.3"

unknown-call state:
  represented explicitly; never collapsed into the oldest known version

fd_version:
  preserved as interface/library version text

source header and memory map:
  rendered from target platform summary only

web/export/API:
  consume target summary only
```

Because this repo is the only consumer, replace the current lossy runtime shape
directly. Do not add a compatibility bridge that keeps the old enum-only model
as the primary path.

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

### 3. Target Platform Summary Should Own Header Content

The memory map and OS compatibility header are both target summary facts. They
should be rendered from structured summary data, not from unrelated ad hoc
comment emitters.

Target shape:

```text
source analysis
  -> target platform summary
  -> render-plan source header rows for memory map and OS compatibility
  -> listing summary JSON
  -> source export payload
```

This lets the web UI, exported source, API clients, and tests agree without
parsing assembly comments.

### 4. HUNK Runtime Metadata Should Own Container Decisions

Loader, writer, and reproduction comparison all need record ids and skip
classification. Those facts should come from generated HUNK metadata.

If a record is unsupported, that status should also be metadata, not a missing
case hidden in a C switch.

### 5. Parser Expansion Should Be Target-Led

Parsing more ADCD is useful only when it improves current reversing work or
removes visible platform gaps. The project should prefer small source-family
expansions tied to target reports over broad speculative ingestion.

## Forward Implementation Model

### Source Inventory

Promote enough source inventory into machine-readable form for coverage reports.
Markdown can remain the human narrative, but counts and statuses should come
from structured data.

### Platform KB Coverage Report

Build one command that summarizes NDK, OS compatibility, hardware, corrections,
and HUNK state from committed artifacts.

### Target OS Compatibility Summary

Preserve raw function availability and FD/interface version metadata in
generated runtime structs. Aggregate observed calls and memory-map ranges into
one target summary. Render the source compatibility and memory-map headers from
that summary and expose the same summary to web/API/export paths.

Use this summary for:

```text
minimum OS requirement
OS/API vintage fingerprinting
unexpected-new-API review warnings
emulator/profile selection hints
target-driven parser correction priorities
```

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
- Reintroducing the old OS compatibility header as a separate string-only path.
- Keeping lossy enum-only availability as the primary runtime model.

## Proposed Rewrite

### Slice 1: Platform KB Coverage Report

Tracked by `docs/issues/004-001-add-platform-kb-coverage-report.md`.

Add `amiga-platform-kb report` and `amiga-platform-kb check`. The first slice is
mostly read-only: it should report current NDK, hardware, corrections, source
inventory, and HUNK coverage from committed artifacts.

### Slice 2: Target OS Compatibility Summary

Tracked by `docs/issues/004-002-add-target-os-compatibility-summary.md`.

Resolved in this slice: raw OS availability metadata is preserved through
generated runtime tables, recovered calls aggregate into
`platform_summary.os_compatibility`, source analysis JSON exposes that summary,
and the C-rendered source header emits OS compatibility beside the memory map.

### Slice 3: Corrections Review Flow

Tracked by `docs/issues/004-003-add-amiga-ndk-corrections-review-flow.md`.

Resolved in this slice: `amiga-platform-kb corrections list/check/promote`
lists corrections with stable ids and citations, enforces review-state debt,
and promotes one seeded correction at a time with preserved citation/source
fields plus reviewer/date provenance.

### Slice 4: Generated HUNK Comparison Helpers

Tracked by `docs/issues/004-004-generate-hunk-comparison-from-platform-runtime-metadata.md`.

Resolved in this slice: `src/m68k_reproduction_compare.c` now consumes
generated HUNK runtime helpers for record lookup, section/terminator
classification, relocation metadata, EXT variants, and BSS-vs-payload
classification. Local HUNK record id constants were removed.

### Slice 5: Resolve `HUNK_OVERLAY`

Tracked by `docs/issues/004-005-resolve-hunk-overlay-support-state.md`.

Resolved in `10b4d05`: overlay state is explicit unsupported inventory. The
loader rejects overlay records with a named diagnostic, and platform KB strict
checks no longer report overlay as half-represented.

### Slice 6: Target-Driven Platform Gap Report

Tracked by `docs/issues/004-006-add-target-driven-platform-gap-report.md`.

Resolved in this slice: `amiga-platform-kb target-gaps <target>` reports
platform-looking target gaps grouped by likely owner/source family, including
custom chip ranges, CIA ranges, LVO-shaped offsets, known include constants,
unknown absolute values, and unexpected-new API usage from target platform
summary data. Explicit target OS expectations and inferred year hints are
distinguished in output.

## Acceptance Criteria

- Current platform KB state is visible through one report command.
- Target OS compatibility is available as structured summary data.
- The rendered source header includes memory map and OS compatibility from the
  same summary data used by web/API/export paths.
- Raw `available_since` and `fd_version` precision is preserved where known.
- No-call and unknown-version states are explicit and do not imply a false
  minimum OS requirement.
- Expected-profile warnings are based on explicit target metadata, or clearly
  marked as inferred when derived from project year.
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

target OS compatibility summary:
  fixture target with no recovered OS calls
  fixture target with recovered calls but unknown availability
  fixture target with recovered calls across multiple available_since/fd versions
  fixture target proving raw 1.2 and 3.0 survive target summary aggregation
  source-header test proving memory map and OS compatibility both render from target platform summary
  listing summary/API test proving structured summary is emitted

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
Slice 1 and completed follow-up slices are reflected in the notes below.

## Implementation Notes

Slice 1 added `amiga-platform-kb report` and `amiga-platform-kb check` against
committed artifacts only.

Slice 2 preserved raw Amiga OS availability in generated runtime metadata and
added target platform summary output. `amiga-platform-kb check` now passes: raw
values such as `1.2`, `2.04`, `2.1`, `3`, and `3.0` are no longer collapsed out
of runtime metadata. Source analysis JSON now exposes `platform_summary`, and
source rendering emits an OS compatibility header from recovered-call summary
data when analysis-backed source export is used. Explicit expected OS profile
metadata is still absent from target manifests, so inferred project-year warning
heuristics remain future work.

Slice 3 added `amiga-platform-kb corrections list/check/promote`. Correction
ids are stable derived ids unless an entry already has `id`; checks now fail for
unknown statuses, missing citations, duplicate ids, or validated entries without
review provenance. Promotion updates exactly one seeded correction to
`validated` and records `reviewed_by`/`reviewed_at`.

Slice 4 moved reproduction comparison onto generated HUNK runtime metadata.
`src/m68k_reproduction_compare.c` no longer carries local HUNK record id
constants or local relocation/EXT/section record-category tables. A focused C
metadata test covers the generated categories used by comparison.

Slice 5 resolved `HUNK_OVERLAY` by making it explicitly unsupported. The enum id
remains for diagnostics, but it is no longer a valid load-file record and the
loader now rejects it with a named unsupported-record diagnostic.

Slice 6 added `amiga-platform-kb target-gaps <target>`. The report is
read-only, groups platform-looking candidates by likely owner/source family,
references source/parser areas that would close the gap, and marks
unexpected-new API warnings as explicit target metadata or inferred year hints.
