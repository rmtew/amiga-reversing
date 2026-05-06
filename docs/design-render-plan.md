# Deterministic Render Plan

Disassembly rendering should be deterministic source generation from C-owned
analysis facts. The web listing view and the full `.s` source file should not
use separate models, and the web path should not render a full source file only
to parse that text back into rows.

The desired model is:

```
C-owned analysis artifact -> render plan -> source emission
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
data spans stay attached to one analysis row.

An isolated C test now proves that full listing JSON emitted from a text-line
render plan remains stable for the same source model. The production DLL path
uses the same plan-backed row emitter. The old full listing source-text API has
been removed, so there is no separate raw source-text row loop to maintain.
Header collection for filtered listing rows now stops at the first section
directive instead of scanning the whole render plan before the row-emission
pass.
Full listing row JSON now consumes render-plan statement metadata directly for
the production facts_v2 path. Source-plan rows carry statement kind,
instruction metadata, source range, and original source bytes where the render
walk already has them. The full listing API no longer parses emitted `.s` text
back into `M68kSourceFileIR` before row JSON emission, and the obsolete
`source_model_seconds` profile field has been removed. Listing-only requests
now capture the source plan without allocating the full `.s` API string.
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
facts_v2 now also exposes direct C listing-window JSON emission from the render
plan, with a regression proving the window matches the same slice from full
listing rows. The web route is not switched to call it per request because that
would redo full analysis on scroll; the route needs a cacheable plan or compact
row-window artifact lifetime first.
The C listing-window emitter streams selected rows directly into the final JSON
builder; it does not allocate a temporary rows JSON string and copy it into the
payload. An isolated C regression now covers listing-window JSON parity with a
full render-plan row slice.
The full listing job now caches serialized row artifacts alongside the Python
row objects. Indexed and address-anchored web windows can be served from that
compact artifact after the job finishes, avoiding repeated dataclass-to-JSON
row serialization on scroll while still avoiding on-demand C analysis.
Address-anchored serialized windows use a display-order block-max index so the
lookup avoids a full-row scan without changing behaviour for non-monotonic ORG
or runtime-address layouts.
This Python-side serialized row cache is transitional. The intended endpoint is
not more server cache layers; it is a C-owned analysis/render-plan artifact,
keyed by the same effective target inputs, that can answer listing-window and
navigation requests without rebuilding analysis and without Python retaining a
parallel row model.
The first C artifact boundary now exists as an opaque
`PlatformFileListingArtifact`: path and raw-binary create APIs build and retain
the loaded object, effective policy, source analysis, facts_v2 profile, and
render plan, and repeated window calls emit from that retained C state. This is
now wired into full-listing generation so the server can keep the C artifact
for later index-window requests after the full listing job completes.
The source-producing facts_v2 path has moved away from final-text header
rewrites. Header material such as includes and equates is captured as typed
source rows, then assembled with the body deterministically.

Render plans now own rows and row text through a plan-local arena. The row
array remains contiguous, but growth uses arena allocate-and-copy instead of
heap realloc/free churn. Returned row pointers are immediate-use handles; code
must keep row indexes for long-lived references. Emitted full-source and window
strings remain separately heap-owned API return buffers. Arena-backed plans
must be transferred with `m68k_render_plan_move`, not raw struct assignment.
Full-source emission uses stored row byte counts rather than rediscovering row
lengths from text.

facts_v2 source capture no longer builds a parallel full-source text buffer
while rows are being captured. Source fragments must be emitted inside an active
render-plan row; unplanned source text is treated as a source-render failure.
The full `.s` text is allocated once from the assembled plan at the API boundary.

Full-listing header rows and app-slot listing analysis scratch data now use
builder-local arenas. These structures are created for one JSON emission pass,
share one lifetime, and no longer maintain nested heap/free ownership inside
the row walk. App-slot summary, interval, field-reference, and header-row
scratch also uses the same arena with marks for per-region temporary data.
Render lookup owns its lookup-table and lookup-result arrays through a
lookup-local arena. Short-lived typed-flow graph scratch remains separately
owned because it is reset per analysis pass, not retained with the lookup.

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
- Cache the C-level analysis/render-plan artifact for the web route, so
  repeated listing windows reuse authoritative C state instead of rebuilding
  analysis or growing Python-side row caches.
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

The server should not need to keep a second authoritative model of rendered
rows. For interactive use, the C backend should expose either an opaque
analysis/render-plan session handle or a persisted listing artifact:

```
create artifact(binary, metadata, policy, effective cache key)
listing window by row/index/artifact
listing window by address/artifact
navigation and row count/artifact
destroy or invalidate artifact
```

The artifact owns the C analysis facts, render plan, row indexes, and
line/address/navigation indexes needed by the web route. It is invalidated when
the binary, metadata, policy, backend DLL/tool stamps, or effective target
cache key changes. Python may hold the opaque handle or artifact id, but must
not rebuild its own long-lived row database once this API exists.

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

## Arena Ownership

Arena use should follow real lifetime boundaries:

- A render plan owns rows and row text in a plan-local arena.
- Render-plan row arrays remain contiguous, but growth is arena
  allocate-and-copy. Old growth buffers die with the plan.
- Row pointers returned while appending are transient. Store row indexes, not
  row pointers, when a reference must survive later appends.
- Row-builder scratch remains reusable heap storage outside the plan arena.
- Header/listing scratch that lives for one JSON emission pass should be owned
  by the listing builder arena.
- Render-preview scratch that lives only while building one preview should use
  the preview scratch arena with mark/rewind scopes. This covers temporary
  tables such as app-slot RS sorting buffers and per-section CFG block-start
  maps; they must not allocate per invocation on the heap.
- Lookup-owned indexes and render-enrichment arrays should be owned by the
  lookup arena. Per-pass analysis scratch with a shorter lifetime should stay
  outside that arena.
- Analysis facts and source/object IR are authoritative inputs and must not be
  copied into render arenas unless the render path needs immutable row-local
  provenance.
- API return values such as full `.s` text and JSON strings remain heap-owned
  because callers free them after the C boundary.

Arena-backed objects must not be transferred by raw struct assignment. If an
owner crosses a boundary, provide a move function that destroys the destination
owner and reinitializes the source owner.

Do not add per-entry heap allocation for same-lifetime row/listing state. If a
structure currently cannot use an arena cleanly, refactor the ownership boundary
first instead of adding another local allocation convention.

The intended ownership map is:

- plan arena: durable rows and row text until the plan is destroyed or moved.
- lookup arena: indexes derived from facts/analysis for one render pass.
- preview scratch arena: temporary render-analysis buffers inside one preview
  build, always released with mark/rewind when the local phase ends.
- listing builder arena: JSON/listing enrichment scratch for one API emission.
- row-builder heap buffer: reusable mutable text staging before copying into the
  plan arena.
- API heap strings: caller-owned C boundary results freed by exported free
  functions.

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
semantic source plan during rendering, emits the final `.s` source from that
plan, and emits full listing rows from plan-owned statement metadata without
reparsing the emitted source text. Listing-only requests capture the plan
without producing the full-source API buffer; source-producing requests still
emit the `.s` text from the same plan.
Direct C listing-window JSON emission now exists and has a raw-binary
regression proving parity with a full render-plan row slice. This is not yet the
web route standard because the current DLL boundary does not preserve the built
plan between requests.
An opaque C listing artifact API now preserves that built state across multiple
window calls for both normal platform files and raw-binary targets. Real-DLL
regressions prove that repeated windows from one artifact match full listing row
slices, that full rows can be emitted from the same artifact, and that
raw-binary targets can use the same artifact boundary.
As an interim step, full listing jobs cache serialized row artifacts once and
indexed/address-anchored web windows slice that cache when it matches the
current project cache key. Address windows also cache display-order address
block maxima, preserving existing first-row-at-or-after semantics while reducing
per-scroll search work.
The next architectural migration is to replace that interim Python serialized
cache with a C-owned analysis/render-plan artifact. The artifact must be built
once per effective cache key and then serve full source, row windows,
address-anchored windows, row counts, and navigation from the same C state.
Index-window serving now uses the retained C listing artifact when it is valid;
address-anchored windows and navigation still use Python row/serialized caches
until the C artifact grows address/navigation APIs.

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
C analysis artifact -> C render plan -> JSON rows
```

The remaining web-path design issue is lifetime. Calling the C listing-window
function directly from `GET /listing` would be correct row emission but poor
product behaviour, because each scroll would rebuild analysis. The next clean
step is therefore a cacheable C analysis/render-plan artifact served by the
route. The current Python row and serialized-row caches are compatibility
bridges only; they should be removed once C can preserve and invalidate that
artifact cleanly.

Full source output remains available:

```
C analysis artifact -> C render plan -> .s source
```

Both outputs must stay byte-for-byte consistent for the rows they share.
