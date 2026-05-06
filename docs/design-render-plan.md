# Deterministic Render Plan

Disassembly rendering should be deterministic source generation from C-owned
analysis facts. The web listing view and the full `.s` source file should not
use separate models, and the web path should not render a full source file only
to parse that text back into rows.

The desired model is:

```
analysis facts -> render plan -> source emission
                              -> windowed web rows
                              -> line/address/row mapping
```

This document is the work-in-progress plan for that model.

## Current Status

The retained implementation started as an isolated C render-plan module:

- `src/m68k_render_plan.h`
- `src/m68k_render_plan.c`
- `src/test_m68k_render_plan.c`

This module now proves the basic mechanics and is wired into the production
facts_v2 source/listing path: ordered rows, explicit line counts, byte offsets,
line lookup, source-offset lookup, runtime-address lookup, and full/window
emission from the same row text.

The module can also build body rows directly from `M68kSourceFileIR` sections
and statements. Production facts_v2 rendering now owns include, RS/app-slot,
equate, and body rows through the captured render plan.

Multi-line rows can now be visited as physical lines while preserving the owner
row and subline index. This keeps compatibility with the current web listing
shape without forcing source text reparsing.

The facts_v2 basic listing JSON path now builds its rows from a render plan
instead of duplicating a statement-render-and-split loop. The production
facts_v2 full listing path now also consumes the captured source render plan
for row emission instead of walking the full source text as the row stream.

Render plans now have a row-builder API for renderers that naturally emit a row
in fragments. This is intended for migrating facts_v2 source rendering without
rebuilding large temporary source text just to discover row boundaries.

facts_v2 source rendering now captures source rows during the C render walk.
The captured plan owns typed rows for sections, labels, instructions, data,
reserve spans, diagnostics, RS/header material, includes, and equates, and full
source text is emitted back from that plan. The profile exposes
`asm_source_plan_rows`, `asm_source_plan_lines`, and `asm_source_plan_bytes`;
Bloodwych now has fewer plan rows than physical source lines because multi-line
data spans stay attached to one analysis row. The full listing path still parses
the emitted source text to rebuild `M68kSourceFileIR` statement metadata before
row JSON is emitted, so the remaining bridge is the source-model rebuild, not
the source-plan construction.

An isolated C test now proves that full listing JSON emitted from a text-line
render plan remains stable for the same source model. The production DLL path
uses the same plan-backed row emitter. The old full listing source-text API has
been removed, so there is no separate raw source-text row loop to maintain.
Header collection for filtered listing rows now stops at the first section
directive instead of scanning the whole render plan before the row-emission
pass.
Full listing timing now separates the remaining source-model rebuild
(`source_model_seconds`) from render-plan row JSON emission
(`rows_emit_seconds`), so the next refactor can target the real leftover cost.
The full listing row emitter now consumes render-plan statement provenance when
available instead of depending only on section-line matching. The production
facts_v2 bridge still needs authoritative statement provenance added to its
captured plan before the source-model rebuild can be removed.
It can also resolve rows from plan-owned source section/offset ranges, which is
the lighter provenance shape the facts_v2 render walk can emit before exact
source-file statement indexes exist.
Render plans now have a typed header-hoist transform that orders include rows,
RS rows, and equate rows before body rows without parsing final source text.
Filtered full-listing header collection now also prefers typed render-plan row
kinds for include/RS/equate rows and first-section stop detection. The legacy
text classifier remains only for diagnostic/text-line bridge rows that do not
yet have semantic row kinds.
Render plans can now emit physical line windows directly from row ownership
metadata, including windows that start inside a multi-line row. This is the
generic primitive the web listing path needs before it can stop requesting a
whole source file for viewport-sized output.
The source-producing facts_v2 path has moved away from final-text header
rewrites. Header material such as includes and equates is captured as typed
source rows, then assembled with the body deterministically.

Render plans now own row text through a plan-local arena. The rows array remains
heap-resizable because row indexes and lookup structures need stable contiguous
storage during construction, while row text has one lifetime: the plan. Emitted
full-source and window strings remain separately heap-owned API return buffers.
Arena-backed plans must be transferred with `m68k_render_plan_move`, not raw
struct assignment.

facts_v2 source capture no longer builds a parallel full-source text buffer
while rows are being captured. Source fragments must be emitted inside an active
render-plan row; unplanned source text is treated as a source-render failure.
The full `.s` text is allocated once from the assembled plan at the API boundary.

C line numbers in this module are zero-based. User-facing UI code may translate
to one-based display line numbers at the boundary.

## Problem

The current full web listing path can become:

```
analysis -> full .s text -> parse .s text -> listing rows -> JSON
```

That has several problems:

- Rendered text becomes an accidental authority instead of a final output.
- The same source structure is rediscovered after it was already known.
- Whole-file work is done when the UI only needs a window of rows.
- Line counts, blank lines, headers, labels, sections, and row anchors are
  implicit side effects of string emission.
- Performance mistakes are harder to see because rendering, reparsing, and JSON
  row building are mixed together.

The full `.s` file remains important. It is the source form that must be
reassembled for reproduction. The issue is not full source output itself; the
issue is treating full source text as the intermediate data structure for the
web API.

## Goals

- Keep C analysis authoritative.
- Preserve exact reproduction and direct source correctness.
- Produce full source and web listing rows from the same render plan.
- Know the line count of every row before emission.
- Map line number to row, row to line number, and address or offset to row.
- Support fast windowed rendering without emitting unrelated source text.
- Make header ordering deterministic:
  includes first, then RS/app-slot regions, then equate/symbol regions, then
  sections.
- Keep blank-line policy explicit and testable.
- Allow later incremental UI updates around a stable row or address anchor.
- Keep generic behaviour in generic C analysis/rendering.
- Keep Amiga behaviour in Amiga platform metadata or platform code.
- Do not hardcode M68K instruction knowledge in the renderer.
- Keep memory ownership simple and explicit. Avoid per-row or per-line heap
  churn; use arenas for same-lifetime transient render data where suitable, and
  refactor ownership boundaries when that is needed to make arena use clean.
  Render-plan row text is same-lifetime data and is arena-owned; row-builder
  scratch and API output strings remain outside that arena.

## Non-Goals

- This is not a UI-first feature.
- This is not Python or JavaScript analysis.
- This is not manual target annotation.
- This is not a change to assembler semantics.
- This is not a reason to keep both legacy and new listing paths indefinitely.

## Core Model

The C backend should build a `RenderPlan`.

A render plan is an ordered collection of regions. Each region contains ordered
rows. Rows own their source line count and can emit their source text on demand.

Suggested top-level types:

- `RenderPlan`
  - Owns all regions.
  - Owns cumulative line indexes.
  - Owns lookup indexes for line, row, section offset, and runtime address.
- `RenderRegion`
  - Groups related rows.
  - Examples: includes, RS/app slots, equates, section body.
- `RenderRow`
  - Stable row id.
  - Row kind.
  - Region id.
  - Optional section index.
  - Optional section offset and byte range.
  - Optional runtime address range.
  - Exact physical line count.
  - Cumulative start line.
  - Cumulative start byte and byte count.
  - Render payload.
  - Analysis provenance and dependencies.

Blank lines should be rows or explicit row-owned line counts. They should not be
hidden formatting side effects.

## Row Kinds

Initial row kinds should cover the existing source forms without inventing a new
language:

- include
- blank
- rsset
- rs field
- equate
- section directive
- org directive
- label
- instruction
- data directive
- reserve directive
- platform directive
- diagnostic

A row may own more than one physical line. For example, a long data item may
render as several `dc.b` lines while still being one analysis row. The mapping
must therefore support `row id + subline`.

If later UI work needs every physical line to have its own stable identity, that
should be added as a subline index, not by reparsing source text.

## Line Accounting

Line counts are computed during plan construction.

Example:

| Row kind | Source | Line count |
| --- | --- | --- |
| include | `INCLUDE "hardware/custom.i"` | 1 |
| blank | empty line | 1 |
| section | `SECTION section_0,code` | 1 |
| blank | empty line | 1 |
| label | `loc_0_00000000:` | 1 |
| instruction | `moveq.l #0,d0` | 1 |

The plan then computes cumulative `start_line` values. Line lookup is a binary
search over these ranges:

```
row.start_line <= line < row.start_line + row.line_count
```

Policy choices, such as whether a section is followed by a blank line, should
change plan construction. They should not be hidden inside source string
formatting.

## Mapping

The render plan must support:

- `line -> row`
- `row -> start line`
- `row + subline -> physical line`
- `section + offset -> row`
- `runtime address -> row`
- `target-local source offset -> row`

Address and offset mappings are not always identical. Runtime copied code,
absolute ORG ranges, relocated hunks, decompressed payloads, and hardware
addresses can all require different provenance.

The row should therefore record both source provenance and runtime provenance
where they are known.

## Emission

Full source emission:

```
for each row in plan order:
    emit row text
```

Windowed web emission:

```
find first row for requested line, row, address, or offset
emit only rows needed for the requested window
```

The same row emitter must be used for full source and windowed web output. A
window emitted from row N must match the same rows sliced out of full source
emission.

The reproduction path should use full source emitted from the render plan. The
web path should use the same render plan directly and should not parse full
source text back into listing rows.

## Incremental Analysis

The first implementation does not need incremental UI updates, but the model
should not block them.

Rows should record enough dependencies to allow later invalidation:

- section layout facts
- labels and symbols
- instruction decode facts
- data classification facts
- platform symbol facts
- source mapping facts

Later, when analysis improves a region, the UI can keep the user's anchor by
row id or by section/address provenance, rebuild the affected rows, then request
a fresh window around the anchor.

## Correctness Rules

- C analysis remains authoritative.
- Source text is an output, not an intermediate analysis database.
- Render-plan provenance must be assigned when the renderer knows the row's
  semantic origin. Do not recover provenance later by classifying final emitted
  text lines.
- Header ordering must be a render-plan transform over typed rows, not a text
  rewrite followed by row reclassification.
- No M68K instruction facts are hardcoded in the render plan.
- Instruction rendering continues to use generated M68K knowledge.
- Amiga hardware and OS names come from platform metadata or platform code.
- Header ordering is explicit: includes, RS/app slots, equates, sections.
- Multiple ORG/code-range cases must preserve exact source reproduction.
- Data classification used for rendering must not overlap accepted code.
- Full source emission must reproduce the target when reassembled, except for
  already accepted hunk structure differences.

## Migration Plan

1. Add isolated C `RenderPlan`, `RenderRegion`, and `RenderRow` types.
2. Add fixture-only C tests for line counts, blank rows, and row ordering.
3. Add C tests for line-to-row and offset-to-row mapping.
4. Add C tests proving window emission equals the same slice of full emission.
5. Attach the plan to one small GenAm or MonAm fixture.
6. Add at least one real corpus comparator for any generalized heuristic.
7. Use Bloodwych as the pressure target after the generic fixture passes.
8. Replace the web listing source-reparse path with render-plan row emission.
9. Make full `.s` source output use the same plan where practical.
10. Remove superseded legacy listing paths after parity tests pass.

The first retained step should be small: a synthetic render-plan fixture that
proves line accounting and window emission. Do not start by rewriting the whole
renderer.

This first step now exists. A GenAm-style source-IR fixture now proves direct
body-row plan construction, and facts_v2 basic plus full listing rows now use
render-plan line streams. Production facts_v2 source rendering now captures a
semantic source plan during rendering and emits the final `.s` source from that
plan. The next step is to stop rebuilding `M68kSourceFileIR` from emitted
source text for the full listing path by carrying enough statement/source
metadata in the authoritative plan or source analysis.

## Required Tests

- C unit tests for row ordering and line counts.
- C unit tests for line, row, address, and offset mapping.
- C unit tests for header ordering:
  includes, RS/app slots, equates, sections.
- C unit tests proving window emission matches full-source slices.
- A GenAm or MonAm regression before using Bloodwych as the proving target.
- Bloodwych source/reproduction pass after integration.
- Web API test proving a listing window is produced without reparsing full
  source text.
- Timing comparison for Bloodwych and at least one comparator target.

## Open Questions

- Should diagnostics be standalone rows, or attached to the following source
  row?
- Should large data blocks be one row with many sublines, or split into several
  data rows at directive boundaries?
- Which header spacing policies should be user-configurable, and which should
  be fixed platform/source style?
- How should row ids remain stable when analysis splits one unknown/data row
  into several typed rows?
- How much runtime copied-code and ORG provenance must exist before the web path
  switches to render-plan rows?

## Current Anti-Pattern To Remove

The web listing path should stop relying on full source text as the row model.
The intended replacement is:

```
C analysis facts -> C render plan -> JSON rows
```

Full source output remains available:

```
C analysis facts -> C render plan -> .s source
```

Both outputs must stay byte-for-byte consistent for the rows they share.
