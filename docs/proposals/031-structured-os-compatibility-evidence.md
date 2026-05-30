# Proposal 031: Structured OS Compatibility Evidence

Status: Complete.

The rendered source currently prints AmigaOS compatibility as a flat comment
block. It is useful, but too noisy:

```asm
; OS compatibility
;   minimum required: 1.3
;   observed API availability: 1.2, 1.3
;   observed FD/interface versions: v33
;   max requirement drivers:
;     _LVOAllocMem at section_0+$000000AC requires 1.3
;     _LVOOpenLibrary at section_0+$000000E8 requires 1.3
;     _LVOOpenLibrary at section_0+$00000102 requires 1.3
;     _LVOOpenLibrary at section_0+$0000011C requires 1.3
```

The problem is not the evidence. The problem is that the human header is trying
to be both a compact source comment and a raw proof dump. This proposal keeps
the raw C-owned evidence, adds structured grouped records, and renders a concise
header by default.

## Checkpoint Index

- [x] Problem Statement
- [x] Tutorial: Raw Evidence Versus Presentation
- [x] Tutorial: What A Grouped Record Is
- [x] Proposed C Model
- [x] Rendering Contract
- [x] JSON And Report Contract
- [x] Generalization Beyond AmigaOS
- [x] Implementation Slices
- [x] Tests And Fixture Proof
- [x] Acceptance Criteria
- [x] Non-Goals
- [x] Completion Notes
- [x] Later Observations

## Problem Statement

The current header has three issues.

First, repeated call-site records dominate the top of the source even when they
say the same thing:

```text
_LVOOpenLibrary at section_0+$000000E8 requires 1.3
_LVOOpenLibrary at section_0+$00000102 requires 1.3
_LVOOpenLibrary at section_0+$0000011C requires 1.3
```

Second, wording such as `observed API availability: 1.2, 1.3` is ambiguous. It
does not clearly say that 1.3 is the required floor and 1.2 is lower-version API
evidence seen along the way.

Third, `observed FD/interface versions: v33` appears beside OS requirements even
though it is interface metadata, not another OS floor.

The source header should answer the user's first question quickly:

```text
What OS level does this target appear to require, and why?
```

The exact call-site evidence should remain available to tools, reports, tests,
and reviewers without overwhelming the generated assembly.

## Tutorial: Raw Evidence Versus Presentation

Raw evidence is per call site:

```c
typedef struct M68kOsRequirementDriver {
    const char *call_name;
    const char *available_since;
    uint16_t section_index;
    uint32_t section_offset;
} M68kOsRequirementDriver;
```

That is the right durable fact. It tells us exactly where the requirement came
from.

Presentation evidence is grouped for humans:

```text
1.3:
  _LVOAllocMem x1
  _LVOOpenLibrary x3
  _LVOOpenDevice x1
```

Both forms should come from the same C-owned analysis result:

```text
analysis facts
  -> raw requirement drivers
  -> grouped requirement drivers
  -> compact source header
  -> detailed JSON/report evidence
```

Python should not infer, regroup, or reinterpret these compatibility facts. It
may serialize or display the C-produced model.

## Tutorial: What A Grouped Record Is

A grouped record combines equivalent requirement drivers while preserving the
locations that caused the group.

Raw records:

```json
[
  {
    "call": "_LVOOpenLibrary",
    "available_since": "1.3",
    "section": 0,
    "offset": 232
  },
  {
    "call": "_LVOOpenLibrary",
    "available_since": "1.3",
    "section": 0,
    "offset": 258
  },
  {
    "call": "_LVOOpenLibrary",
    "available_since": "1.3",
    "section": 0,
    "offset": 284
  }
]
```

Grouped record:

```json
{
  "call": "_LVOOpenLibrary",
  "available_since": "1.3",
  "count": 3,
  "locations": [
    {"section": 0, "offset": 232},
    {"section": 0, "offset": 258},
    {"section": 0, "offset": 284}
  ]
}
```

Rendered source:

```asm
;   requirement drivers:
;     1.3: _LVOOpenLibrary x3
```

The header stays compact. The grouped record still has enough evidence for a
reviewer to drill down into exact offsets when needed.

## Proposed C Model

Extend the target platform summary so C owns both raw and grouped evidence.

Illustrative shape:

```c
typedef struct M68kOsRequirementLocation {
    uint16_t section_index;
    uint32_t section_offset;
} M68kOsRequirementLocation;

typedef struct M68kOsRequirementGroup {
    const char *call_name;
    const char *available_since;
    uint32_t count;
    M68kOsRequirementLocation locations[M68K_OS_REQUIREMENT_LOCATION_CAPACITY];
    uint32_t location_count;
    bool locations_truncated;
} M68kOsRequirementGroup;

typedef struct M68kTargetOsCompatibilitySummary {
    const char *platform_name;
    const char *required_floor;

    M68kOsRequirementDriver raw_drivers[M68K_OS_REQUIREMENT_DRIVER_CAPACITY];
    uint32_t raw_driver_count;
    bool raw_drivers_truncated;

    M68kOsRequirementGroup requirement_groups[M68K_OS_REQUIREMENT_GROUP_CAPACITY];
    uint32_t requirement_group_count;
    bool requirement_groups_truncated;

    const char *lower_observed_versions[M68K_OS_VERSION_CAPACITY];
    uint32_t lower_observed_version_count;

    const char *interface_versions[M68K_OS_INTERFACE_VERSION_CAPACITY];
    uint32_t interface_version_count;
} M68kTargetOsCompatibilitySummary;
```

The exact names can follow the current `m68k_ir.h` style. The important
contract is:

- raw drivers remain exact call-site evidence;
- grouped drivers are derived by C, not by renderers;
- truncation is explicit and testable;
- lower-version API evidence is separated from the required floor;
- FD/interface metadata is not presented as an OS requirement.

Grouping key:

```text
available_since + call_name + owning library/interface when known
```

The owning library/interface key is important for future targets where the same
symbol text could appear in different namespaces.

## Rendering Contract

The default assembly header should be short and source-oriented:

```asm
; AmigaOS compatibility, inferred from recovered OS calls
;   required OS floor: 1.3
;   evidence: highest recovered API requirement is 1.3
;   requirement drivers:
;     1.3: _LVOAllocMem, _LVOOpenLibrary x3, _LVOOpenDevice, _LVOFindTask, _LVOAllocSignal x2
;   lower-version APIs also observed: 1.2
;   interface metadata: FD v33
```

Rendering rules:

- omit empty lines rather than printing `unknown` filler;
- never print call-site offsets in the default source header;
- print `xN` only when `N > 1`;
- group by required version, preserving first-evidence order inside each group;
- if any group or location list is truncated, print a concise review warning;
- detailed offset evidence belongs in JSON/report output, not the top of
  `asm.s`.

If the analysis cannot prove a floor, the header should say that directly:

```asm
; AmigaOS compatibility
;   required OS floor: unknown
;   evidence: no recovered OS calls with version metadata
```

## JSON And Report Contract

Machine-readable output should expose both compact groups and raw evidence.

Illustrative JSON:

```json
{
  "os_compatibility": {
    "platform": "amigaos",
    "required_floor": "1.3",
    "evidence": "highest_recovered_api_requirement",
    "requirement_groups": [
      {
        "available_since": "1.3",
        "call": "_LVOOpenLibrary",
        "count": 3,
        "locations": [
          {"section": 0, "offset": 232},
          {"section": 0, "offset": 258},
          {"section": 0, "offset": 284}
        ]
      }
    ],
    "raw_drivers": [
      {
        "available_since": "1.3",
        "call": "_LVOOpenLibrary",
        "section": 0,
        "offset": 232
      }
    ],
    "lower_observed_versions": ["1.2"],
    "interface_metadata": ["FD v33"]
  }
}
```

This gives developers a stable diffable report while keeping the rendered source
readable.

## Generalization Beyond AmigaOS

The model should not be named around Amiga-only concepts where the concept is
general.

General fields:

```text
platform_name
required_floor
requirement_driver
requirement_group
interface_metadata
```

Platform-specific evidence can still carry Amiga details:

```text
call: _LVOOpenLibrary
owner: exec.library
interface_metadata: FD v33
```

Future Classic Mac OS or Atari ST compatibility facts can reuse the same shape:

```text
Classic Mac OS
  required floor: System 7
  driver: Gestalt selector availability

Atari ST
  required floor: TOS version
  driver: OS call or executable header flag
```

Those platforms should only populate this model once the parser or analysis has
real evidence. The proposal does not authorize shape guesses.

## Implementation Slices

1. Keep existing raw driver collection unchanged.

   The current summary builder already knows which calls imply which OS version.
   Preserve that as the raw evidence source.

2. Add C grouping during summary build.

   Pseudocode:

   ```c
   for each raw_driver:
       group = find_group(raw_driver.available_since,
                          raw_driver.owner,
                          raw_driver.call_name);
       if group does not exist:
           group = append_group(...);
       group.count++;
       append_location_or_mark_truncated(group, raw_driver.location);
   ```

3. Split floor and lower observed versions.

   Pseudocode:

   ```c
   required_floor = highest_version(raw_drivers.available_since);

   for each observed_version:
       if version_less_than(observed_version, required_floor):
           append_lower_observed_version(observed_version);
   ```

4. Update source rendering to consume grouped records.

   The renderer should not regroup. It should only format the C model:

   ```c
   render_required_floor(summary->required_floor);
   render_grouped_requirement_drivers(summary->requirement_groups);
   render_lower_observed_versions(summary->lower_observed_versions);
   render_interface_metadata(summary->interface_versions);
   ```

5. Add JSON/report output for raw and grouped evidence.

   Reports should make exact offsets available without putting them in the
   source header.

6. Regenerate affected tracked `.s` outputs.

   The rendered comments change, so source output should be refreshed and
   round-trip checked.

## Tests And Fixture Proof

Representative C tests should not depend on external binaries. They should build
a small IR fixture with repeated OS calls and assert:

```text
required floor == 1.3
_LVOOpenLibrary group count == 3
group locations preserve all three offsets
lower observed versions contain 1.2
interface metadata contains FD v33
```

Renderer tests should assert compact output:

```asm
;   required OS floor: 1.3
;   requirement drivers:
;     1.3: _LVOAllocMem, _LVOOpenLibrary x3
```

And should reject the old noisy shape:

```text
section_0+$
observed FD/interface versions
max requirement drivers
```

Fixture proof should include at least one current Amiga target such as
`amiga_hunk_monam302`, because it has repeated requirement drivers and exposes
the original readability problem.

## Acceptance Criteria

- C summary contains exact raw drivers and derived grouped records.
- Default `asm.s` header is compact and does not list per-call-site offsets.
- JSON/report output preserves exact locations for every driver.
- Repeated calls render as grouped counts, for example `_LVOOpenLibrary x3`.
- Lower-version API observations are not confused with the required OS floor.
- FD/interface versions render as metadata, not compatibility requirements.
- Empty/unknown fields are omitted or explicitly marked unknown without filler.
- Truncation is explicit in C data and visible in report output.
- A representative C unit test covers grouping and location preservation.
- A fixture test covers a real target with repeated AmigaOS drivers.
- Round-trip verification passes for regenerated source outputs.

## Non-Goals

- Do not infer OS compatibility from symbol names without C-owned evidence.
- Do not move compatibility analysis into Python.
- Do not remove raw driver evidence.
- Do not add per-target formatting exceptions.
- Do not claim Classic Mac OS or Atari ST compatibility floors without accepted
  parser or analysis evidence.

## Completion Notes

Implemented in C as a target platform summary extension:

```text
M68kTargetOsCompatibilitySummary
  raw_requirement_drivers[]
  requirement_groups[]
  lower_observed_available_since[]
  truncation flags
```

The compact source header is rendered from those C-owned records. Python does
not group, infer, or reinterpret OS compatibility facts; it only receives the C
JSON model and orchestrates target regeneration/round-trip verification.

The implementation deliberately avoids duplicating group locations. Exact
locations live once in `raw_requirement_drivers[]`. Group records keep keys and
counts. JSON projects group `locations[]` from raw drivers when serializing the
report. This keeps memory bounded without adding heap allocations or arena
ownership where the current summary API does not need them.

Summary records store stable analysis/KB string references instead of copying
fixed-size symbol buffers. That keeps the value summary compact enough for DLL
call paths and avoids gratuitous memory use.

Representative rendered source changed from per-call-site offset dumps:

```asm
;   max requirement drivers:
;     _LVOOpenLibrary at section_0+$000000E8 requires 1.3
;     _LVOOpenLibrary at section_0+$00000102 requires 1.3
```

to compact grouped evidence:

```asm
; AmigaOS compatibility, inferred from recovered OS calls
;   required OS floor: 1.3
;   evidence: highest recovered API requirement is 1.3
;   requirement drivers:
;     1.3: _LVOFindResident
```

Large targets are summarized instead of emitting unreadable one-line API lists:

```asm
;   requirement drivers:
;     1.3: 277 recovered call sites across 61 API groups
;          first observed: _LVOAllocMem x5, _LVOOpenLibrary x3, ...
;          remaining groups: 53; inspect JSON report
```

Verification performed:

```text
cmd /c src\precommit.bat m68k_ir
uv run platform-rendered-source-roundtrip --update-rendered-source
uv run platform-rendered-source-roundtrip
uv run mypy
uv run ruff check
uv run python -m pytest tests -q
```

Rendered-source round-trip after regeneration:

```text
25/36 full-file exact
10 content-exact only
1 unsupported Mac OS rendered-source assembly
0 failures
```

## Later Observations

The legacy `max_requirement_drivers` JSON field remains for compatibility with
existing consumers. New consumers should prefer:

```text
raw_requirement_drivers
requirement_groups
lower_observed_available_since
interface_metadata
```

The current summary API is stack/value based. That is acceptable for the bounded
model now used here, but if future compatibility summaries grow to carry larger
evidence sets, the clean path is an explicit caller-owned arena or create/destroy
summary API. Avoid adding ad hoc heap ownership inside renderers or Python.

During implementation, a heavier version of the summary with duplicated grouped
location arrays reproduced the intermittent DLL access violation in
`test_platform_file_analysis_reports_cfg_for_certain_code`. The final compact
string-reference model passed that focused DLL test ten consecutive times.

Classic Mac OS and Atari ST still do not populate compatibility floors. That is
intentional until those platforms have parser or analysis evidence equivalent to
AmigaOS recovered OS calls.
