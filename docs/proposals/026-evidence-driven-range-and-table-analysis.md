# Proposal 026: Evidence-Driven Range and Table Analysis

Status: in progress

## Purpose

Make code/data/text/table ownership a general C analysis result instead of a
collection of local renderer choices.

Proposal 025 made string and text rendering more evidence-driven. The next
remaining problem is broader: the analysis still needs a single way to decide
what every byte range is when evidence conflicts.

The recurring failures have the same shape:

- printable bytes are sometimes really code;
- valid opcodes are sometimes really data;
- referenced labels can be created without the data block being split at the
  definition point;
- tables are sometimes capped or scanned as a fixed list of discovered targets
  instead of represented as a durable table shape;
- renderers sometimes know something that should have been C analysis metadata.

This proposal is the working plan. We will not create issue files for it unless
the work grows beyond this document. Implementation should proceed directly from
this proposal, updating it as the model becomes more precise.

## Target Outcome

The C analysis engine should own a durable range model:

```text
bytes + executable format facts + platform facts + decoded instructions + xrefs
  -> range candidates
  -> positive and negative evidence
  -> conflict arbitration
  -> accepted code/data/text/table records
  -> labels and xrefs materialized from accepted records
  -> renderers consume records without re-deciding ownership
```

Rendered source should become a direct projection of accepted C records:

```asm
lookup_table_00020CA0:
    dc.l abs_0_00010CC0
    dc.l abs_0_00010CCC
    dc.l abs_0_00010CD8

abs_0_00010CC0:
    bclr.b d1,(a0)
    bclr.b d1,$0028(a0)
    bclr.b d1,$0050(a0)
    jmp (a3)
```

The important point is not that this output is prettier. The important point is
that the table, target labels, target code ranges, and xrefs all come from the
same accepted C evidence.

## Non-Goals

This proposal does not try to solve every semantic naming problem.

Out of scope:

- human-quality function names;
- game-specific symbolic names without proof;
- per-target renderer hacks;
- raising arbitrary target caps as a substitute for a table model;
- silently degrading to raw bytes when an analysis/render limit is reached;
- Python-only fixes for ownership decisions;
- accepting text, code, or table claims from byte shape alone.

Python may render, export, report, and test. It should not make C analysis
decisions about what a byte range means.

## Tutorial: Why Range Arbitration Exists

The same bytes can be plausible text, code, or table data.

Example from Starglider-like output:

```asm
    dc.b $2D,$7C,$00,$07,$00,$00,$00,$00,$4E,$75
    dc.b $2D,$7C,$00,$07,$80,$00,$00,$00,$4E,$75
    dc.b "NuNu    ",$00
```

The last line is printable and NUL-terminated. Shape alone says "string".
Nearby bytes also include `4E 75`, an `rts` opcode, and code-shaped sequences.
Shape alone can also say "code".

Neither answer is acceptable by itself. The C engine needs a conflict record:

```text
range 00004000..00004009
  text candidate:
    positive: printable bytes, NUL terminator
    negative: no pointer/API/table evidence
  code candidate:
    positive: nearby valid instruction island, terminal opcode pattern
    negative: no accepted entrypoint/xref
  arbitration:
    no accepted owner
    render as residual bytes or reviewable uncertain range
```

That is better than emitting a confident false string or a confident false code
block.

## Range Model

The C analysis should represent every accepted or disputed range with a common
shape.

Illustrative internal record:

```c
typedef enum M68kRangeKind {
    M68K_RANGE_CODE,
    M68K_RANGE_TEXT,
    M68K_RANGE_POINTER_TABLE,
    M68K_RANGE_RELATIVE_TABLE,
    M68K_RANGE_STRUCTURED_DATA,
    M68K_RANGE_PLATFORM_METADATA,
    M68K_RANGE_RESIDUAL,
    M68K_RANGE_CONFLICT,
} M68kRangeKind;

typedef enum M68kEvidenceKind {
    M68K_EVIDENCE_ENTRYPOINT,
    M68K_EVIDENCE_BRANCH_TARGET,
    M68K_EVIDENCE_POINTER_TARGET,
    M68K_EVIDENCE_INDEXED_TABLE_ACCESS,
    M68K_EVIDENCE_API_ARGUMENT,
    M68K_EVIDENCE_PLATFORM_RECORD,
    M68K_EVIDENCE_TEXT_SHAPE,
    M68K_EVIDENCE_TERMINATOR_SHAPE,
    M68K_EVIDENCE_CODE_SHAPE,
    M68K_EVIDENCE_OVERLAP_BLOCKER,
} M68kEvidenceKind;
```

The exact structs can follow existing project style, but the model needs these
properties:

- section and byte span;
- accepted kind or conflict kind;
- positive evidence;
- negative evidence;
- source xrefs and target xrefs where known;
- table membership where applicable;
- render role;
- confidence/status such as candidate, accepted, blocked, or deferred.

The renderer should not need to rediscover whether a block is a string table,
pointer table, code island, or residual bytes.

## Evidence Ranking

Evidence should be ranked by meaning, not by convenience.

Strong positive evidence:

- executable entrypoint;
- branch or call target from accepted code;
- table target reached by accepted indexed access;
- pointer loaded into a documented API string/buffer argument;
- platform parser record with exact bounds;
- relocation or executable-format record with exact ownership.

Medium positive evidence:

- local table shape confirmed by a nearby indexed load;
- consistent neighboring table entries;
- string/text cluster with consistent terminators and no conflicting owner;
- fixed-width or control-separated text stream with surrounding structured
  evidence.

Weak positive evidence:

- printable bytes;
- valid opcode stream;
- plausible NUL, `$FF`, or length prefix;
- English-looking words.

Weak evidence can create candidates. It must not create accepted ownership when
stronger context conflicts.

## Conflict Arbitration

The analysis should fail closed when ownership conflicts.

Example arbitration ladder:

```text
accepted code overlap
  beats text shape

accepted platform metadata
  beats generic text/code shape

accepted table descriptor
  beats one large string candidate spanning table boundaries

branch/call target from accepted code
  beats orphan text shape

orphan code shape without xref
  may block weak string acceptance
  but does not become accepted code by itself
```

The output should make uncertainty explicit in data, not in noisy comments.

Good residual rendering:

```asm
unknown_0_00004000:
    dc.b $2D,$7C,$00,$07,$00,$00,$00,$00,$4E,$75
```

Bad confident rendering:

```asm
    dc.b "NuNu    ",$00
```

if the only evidence is printable shape and there is nearby orphan-code
evidence.

## Table Descriptor Model

The current fixed target-set approach is not the right long-term shape. Tables
should be represented as descriptors, not as an arbitrary number of discovered
entries.

Illustrative descriptor:

```c
typedef enum M68kTableEncoding {
    M68K_TABLE_ABSOLUTE_LONG,
    M68K_TABLE_SECTION_RELATIVE_WORD,
    M68K_TABLE_BASE_RELATIVE_WORD,
    M68K_TABLE_STRING_POINTERS,
    M68K_TABLE_FIXED_RECORDS,
} M68kTableEncoding;

typedef struct M68kTableDescriptor {
    uint32_t section_index;
    uint32_t offset;
    uint32_t entry_size;
    uint32_t entry_count;
    M68kTableEncoding encoding;
    uint32_t target_base_section;
    uint32_t target_base_offset;
    uint32_t index_register;
    uint32_t access_instruction_offset;
} M68kTableDescriptor;
```

The final implementation can use existing naming and storage conventions. The
important capabilities are:

- describe the whole table range;
- iterate entries on demand;
- materialize labels for referenced targets;
- split data rows at label boundaries;
- attach xrefs from the accessing instruction to the table and from table
  entries to targets;
- avoid fixed limits such as "first 64 targets".

## Tutorial: Pointer Table

Pandora has absolute-address lookup table evidence like this:

```asm
    movea.l abs_0_0005CA6C(pc,d0.w),a0

abs_0_0005CA6C:
    dc.l $0005CCF5
    dc.l $0005CD0B
    dc.l $0005CD25
```

The correct C analysis is:

```text
accepted instruction:
  indexed long load from pc-relative table

table descriptor:
  kind: absolute_long
  range: abs_0_0005CA6C..abs_0_0005CA78
  target domain: mapped section addresses

entry iteration:
  0005CCF5 -> materialize abs_0_0005CCF5
  0005CD0B -> materialize abs_0_0005CD0B
  0005CD25 -> materialize abs_0_0005CD25
```

Rendering then follows naturally:

```asm
abs_0_0005CA6C:
    dc.l abs_0_0005CCF5
    dc.l abs_0_0005CD0B
    dc.l abs_0_0005CD25
```

No Python special case should be needed.

## Tutorial: Word-Relative Dispatch Table

Another Pandora shape uses a word table and a runtime base:

```asm
    add.b d0,d0
    lea.l abs_0_0005DCE8(pc),a2
    movea.w $0(a2,d0.w),a2
    jmp $0(a3,a2.w)
```

The table values are not absolute addresses. They are offsets relative to the
target base in `a3`.

The descriptor should record that:

```text
table:
  kind: base_relative_word
  table_base: abs_0_0005DCE8
  target_base: proven value in a3
  entry_size: 2
  signedness: platform/operation proven
```

The renderer should emit source-compatible expressions:

```asm
dispatch_0005DCE8:
    dc.w target_0005DD20-target_base_0005DD00
    dc.w target_0005DD34-target_base_0005DD00
```

If the assembler syntax or local style needs a different expression form, that
is a renderer concern. The C-owned fact is the same: entries are relative table
members with target xrefs.

## Tutorial: String Table

Starglider has text entries and a pointer table:

```asm
rank_ace_pilot:
    dc.b "ACE PILOT",$00
rank_commander:
    dc.b "COMMANDER",$00

rank_name_table:
    dc.l rank_ace_pilot
    dc.l rank_commander
```

The important general analysis is bidirectional:

```text
pointer table targets printable NUL-terminated ranges
  -> promote targets to string_table_entry

string cluster has consistent terminators
  -> helps bound the table target range

accepted code indexes the pointer table
  -> confirms table role and target xrefs
```

If one entry is missed by shape, table membership can still accept it. If one
printable span is not referenced by table or API evidence and conflicts with
code evidence, it should not be accepted merely because it looks textual.

## Tutorial: Label Splitting

A recurring failure is a referenced label that exists logically but is not
emitted at the definition point because the data row was not split.

Bad output:

```asm
CODE_26_data_dispatch_table_00000936:
    dc.b $00,$08,$00,$12,$00,$1E,$00,$28

; elsewhere:
    bra.w CODE_26_loc_0000093E
```

If `CODE_26_loc_0000093E` is accepted, the owning range must either split or
reject the overlap. A label cannot be materialized only at use sites.

Correct model:

```text
range 00000936..0000093E:
  table/data

range 0000093E..:
  code target
```

Correct output:

```asm
CODE_26_data_dispatch_table_00000936:
    dc.b $00,$08,$00,$12

CODE_26_loc_0000093E:
    move.w d1,(a1)
```

This is a general C range-splitting responsibility. Mac, Amiga, and Atari
renderers should all benefit from the same rule.

## Platform Extensions

The core range and table model should be platform-neutral. Platform extensions
should only contribute evidence that is truly platform-specific.

### Amiga

Amiga extensions can provide:

- hunk section/load boundaries;
- relocation ownership;
- Amiga OS library call contracts;
- hardware register address ownership;
- common executable/decruncher entrypoint evidence;
- disk-resource provenance when future disk read analysis proves exact bytes.

Example:

```asm
    lea.l message(pc),a1
    move.l #message_end-message,d3
    jsr _LVOWrite(a6)
```

Amiga DOS metadata can prove that `a1` is a buffer and `d3` is the length for
`Write`. The text buffer classification is still core C range analysis; the API
contract is Amiga-specific evidence.

### Atari ST

Atari extensions can provide:

- PRG/TOS executable bounds;
- relocation/fixup ownership;
- GEMDOS/BIOS/XBIOS call contracts where available;
- platform-specific absolute address regions.

The table and range arbitration model should remain the same as Amiga.

### Classic Mac OS

Mac extensions can provide:

- CODE resource segment bounds;
- CODE 0 jump-table and routing metadata when parser-proven;
- resource metadata ranges;
- Pascal/symbol string records only where the executable/resource parser proves
  exact record shape;
- unsupported/deferred records where exact format evidence is missing.

Mac must not promote byte-entry, relocation/fixup, source-to-CODE, or non-CODE
payload facts beyond the executable-format KB state.

## Renderer Contract

Renderers should consume accepted C records.

Renderer responsibilities:

- choose syntax;
- wrap long byte/text rows;
- emit includes and headers in platform style;
- print labels and xrefs from C facts;
- preserve exact bytes;
- stay assembler-compatible.

Renderer non-responsibilities:

- deciding whether bytes are code or text;
- inventing table boundaries;
- creating target labels that C analysis did not accept;
- suppressing conflicts by formatting around them;
- using comments as a substitute for structured records.

Comments should explain durable semantics. They should not be debug output for
why the renderer guessed a row.

## Testing Strategy

Tests should have two layers.

### Isolated C tests

Use small synthetic byte fixtures that do not depend on target files.

Required representative tests:

- printable NUL text with no conflict becomes a candidate, not necessarily
  accepted;
- accepted code overlap blocks text;
- branch target forces row split at the target label;
- pointer table materializes target labels and emits symbolic entries;
- indexed word-relative table creates a descriptor and target xrefs;
- arbitrary target count is handled by descriptor iteration, not a fixed cap;
- orphan code shape can block weak string acceptance without becoming accepted
  code;
- API buffer evidence accepts exact bounded text when length and pointer are
  both proven.

### Fixture-backed tests

Use imported target binaries as correctness double-checks.

Representative fixtures:

- Starglider false `NuNu`/`NuD0` text cases stay unaccepted unless stronger
  evidence appears;
- Starglider rank string table renders as table-backed strings;
- Pandora `abs_0_0001A25C` string table renders as a complete table;
- Pandora absolute and relative dispatch tables render symbolic entries and
  materialized target labels;
- MonAm mixed string table entries such as `Current Breakpoints:` and
  `Checking for libfile..` render consistently;
- Magicland structured control-separated text remains byte-preserving and does
  not regress.

Fixture tests should cite the target and source offset they are derived from so
that failures are easy to inspect.

## Verification

Output-affecting changes require:

```text
cmd /c src\precommit.bat m68k_ir
uv run python -m pytest tests\test_c_backend.py -q
uv run platform-rendered-source-roundtrip
git diff --check
```

When `.s` output changes, regenerate all tracked rendered source files before
committing and verify the round-trip report:

- full-file exact where the container can be reproduced;
- content exact where the container shape is known unsupported;
- explicit unsupported for platforms such as current Mac source assembly.

The report should not silently skip platforms.

## Completion Criteria

This proposal can close when:

- C analysis has a general accepted/conflict range model;
- C analysis has table descriptors with entry iteration instead of fixed target
  caps;
- label materialization and row splitting are driven by accepted C ranges;
- renderers no longer make ownership decisions for the covered cases;
- Amiga, Atari, and Mac platform extensions contribute only platform-specific
  evidence;
- isolated C tests cover the core model;
- fixture tests cover the TODO-derived examples;
- rendered source round-trip has no regressions.

## Implementation Progress

### Pass 1: Source-Analysis Range Ownership Records

The first implementation pass adds C-owned range ownership records to section
analysis.

Current records are projected from facts the C engine already owns:

```text
accepted CFG block
  -> range_ownership kind=code status=accepted

structured data policy item
  -> range_ownership kind=text/table/structured_data/platform_metadata

orphan code signal with nearby data conflict
  -> range_ownership kind=conflict status=conflict
```

The range record carries:

- `start_offset` and `end_offset`;
- kind and status;
- positive and negative evidence flags;
- source pattern and semantic role where applicable;
- table kind where applicable;
- conflict state where applicable.

This deliberately does not change rendered source yet. The point of this pass is
to make the C analysis output describe ownership directly so later rendering and
review code can consume a single model instead of re-deciding ownership.

Example JSON shape:

```json
{
  "start_offset": 6,
  "end_offset": 14,
  "kind_name": "table",
  "status_name": "accepted",
  "table_kind": "pointer",
  "source_pattern": "indexed_local_pointer_read"
}
```

Covered by C tests:

- `source_analysis_range_ownership_records_code_text_and_table`
- `source_analysis_range_ownership_exports_conflict`

This pass satisfies the first implementation-order item and creates the target
surface for the next passes. It does not yet complete descriptor-based table
iteration or renderer consumption.

### Pass 2: Section Table Descriptors

The second implementation pass adds per-section C table descriptors beside the
range ownership records.

The descriptors are projected from structured table facts the C engine already
accepts:

```text
structured table item
  -> table_descriptor
      range: start_offset..end_offset
      entry_size / entry_count
      table_kind
      base_expression
      source_pattern
      target and consumer links where proven
      accepted/conflict status
```

This is intentionally not a renderer workaround. It gives later renderer and
listing code a section-local table contract without having to rescan policy
items or infer entry counts from raw bytes.

Example JSON shape:

```json
{
  "start_offset": 6,
  "end_offset": 14,
  "entry_size": 4,
  "entry_count": 2,
  "table_kind": "pointer",
  "source_pattern": "indexed_local_pointer_read",
  "consumer_section_index": 0,
  "consumer_offset": 0
}
```

Covered by C tests:

- `source_analysis_range_ownership_records_code_text_and_table`
- `source_analysis_table_descriptor_exports_conflict`

This pass advances the descriptor work but does not yet replace existing
table-entry rendering or materialize labels from descriptors. The next pass
should consume these descriptors for label splitting and table iteration.

### Pass 3: Descriptor Iteration and Limit Hardening

The third implementation pass removes source-visible fixed limits from several
table paths and makes remaining target-set caps explicit failures.

Implemented changes:

- long absolute dispatch tables can be carried as table descriptors and iterated
  at the indirect control site instead of materializing a capped target array;
- PC-relative and base-relative word dispatch tables use structural bounds and
  target evidence instead of the old 32-entry or 64-byte render caps;
- direct indexed word-offset reads such as
  `adda.w $0(a0,d0.w),a1` attach the proven target base to the table record, so
  render output can keep symbolic `target-base` expressions;
- target-set cap hits now report `table_target_set_limit` as a hard analysis
  failure instead of silently rendering anonymous bytes;
- table scans that need only validation/counting can run without a destination
  target array.

The Bloodwych table at `abs_0_0001A31C` is the representative regression check:
the accepted word-offset table now stops at `$0C5D`, and the following
control/text bytes remain raw bytes instead of being swallowed into the table.

### Pass 4: Fixture-Backed Descriptor Proof

The fourth pass adds target-derived proof for the descriptor behavior that was
previously verified mostly through synthetic C fixtures.

Covered examples:

- Pandora raw BK target:
  - the `word_offset_string_table` descriptor is accepted as a 114-entry
    relative-data lookup table with a proven target base;
  - the absolute CODE dispatch table is accepted as a 33-entry
    `absolute_code_dispatch` descriptor instead of a capped target set.
- Bloodwych:
  - the real 73-entry indexed word table is accepted with exact descriptor
    bounds;
  - the rendered source keeps `$0C5D` as the final table word and leaves the
    following `$FC,$1E...` control/text bytes outside the table.

Covered by:

- `test_real_dll_026_table_descriptors_use_evidence_bounds_not_caps`

### Pass 5: Dynamic Source-Analysis Structured Data

The fifth pass fixes a capacity boundary that showed up only on a real imported
target after regenerating every tracked `asm.s`.

`amiga_disk_search-for-the-king-the-1991-accolade-disk-1-of-5__amiga_hunk_king_481902ec`
produces more than 256 generated structured data records. Treating the fixed
`M68kAnalysisPolicy` seed array as the generated-analysis storage cap was the
wrong model:

```text
M68kAnalysisPolicy
  bounded input ABI / user seed compatibility mirror

M68kSourceAnalysisIR
  arena-owned generated analysis records
  no source-visible fixed structured-data cap
```

Implemented changes:

- generated auto structured-data records are appended to dynamic
  `M68kSourceAnalysisIR` storage;
- the first 256 records are still mirrored into `M68kAnalysisPolicy` for the
  existing bounded ABI surface;
- source-analysis JSON, listing metadata, table descriptors, and range ownership
  consume the dynamic source-analysis accessor instead of the fixed policy
  array;
- hitting the old fixed seed-array size no longer refuses source analysis or
  drops accepted C records from reports;
- synthetic C coverage now proves 300 generated string records survive in source
  analysis while the compatibility mirror remains bounded.

Covered by:

- `facts_v2_source_analysis_retains_many_auto_structured_strings`

The latest verification pass regenerated all 36 tracked target `.s` files and
produced no source diffs. `platform-rendered-source-roundtrip` reported 34/36
full-file exact, 1 content-exact-only, 1 unsupported, and 0 failures. Full
Python tests and the C `m68k_ir` precommit gate also passed after this pass.

### Pass 6: Completion Audit

The current implementation is materially beyond the initial record-shape pass,
but the proposal should stay open until the remaining renderer/adapter split is
fully collapsed.

Proven current state:

- C source analysis owns accepted/conflict range records and exports them in
  source-analysis JSON.
- C source analysis owns table descriptors for the covered pointer, absolute
  dispatch, word-relative dispatch, keyed long-relative dispatch, and
  table-backed string cases.
- Table descriptor iteration now covers real wide target sets that previously
  hit fixed render/trace caps.
- C rendering materializes required labels and splits raw data plan rows at
  accepted data boundaries.
- C rendering materializes table target labels for pointer tables and accepted
  dispatch tables instead of leaving referenced labels undefined.
- Weak string/text shape is not enough to accept false strings in the
  TODO-derived Starglider cases.
- Coupled API pointer-and-length evidence is represented as accepted C-owned
  text range ownership with `api_argument`, `structured_data`, and `text_shape`
  evidence, not just as a rendered-source formatting choice.
- The fixture-backed checks now cover Pandora, Bloodwych, MonAm, Magicland, and
  Starglider representative cases.

Still open before this proposal can close:

- The range ownership model is not yet the single primary owner for every
  renderer decision. Some renderer paths still consume structured-data records
  directly, with range records/descriptors acting as the durable mirror.
- Platform evidence adapters are present for the covered facts, but the proposal
  should not claim every Amiga, Atari, and Mac executable/platform ownership
  source has been normalized into the same adapter layer.
- Conflict reporting is good enough for the covered table/text/code cases, but
  the manual-review/UI policy for every unresolved conflict type remains a
  later integration step.

## Implementation Order

1. Add the C range/conflict record shape without changing rendering. Done in
   Pass 1.
2. Migrate existing string/text structured-data ownership into the range model.
   Started in Pass 1 and expanded by Pass 5; generated records now live in
   dynamic source-analysis storage, with range ownership projected from that
   C-owned storage.
3. Add general label materialization and row splitting from accepted ranges.
   Covered for required data-boundary labels, raw data row splits, pointer-table
   data targets, and accepted dispatch-table targets.
4. Replace fixed table target storage with table descriptors and iterators.
   Started in Pass 2 and extended through Pass 5. The old 32-entry render-lookup
   cap for word-relative dispatch table spans and the old 64-byte PC-relative
   lookup span cap have been removed;
   those scans now stop on structural boundaries and accepted target evidence.
   Any remaining source-visible cap hit must become an explicit
   analysis-incomplete/conflict state, not a fallback to anonymous bytes.
   Generated source-analysis structured data is no longer capped by the fixed
   policy seed array; see Pass 5.
5. Port existing pointer-table and relative-table recognizers onto descriptors.
   Covered for the current pointer, absolute dispatch, word-relative dispatch,
   keyed long-relative dispatch, and table-backed string examples.
6. Add arbitration rules for orphan code vs weak text shape. Covered for the
   current false-string and nearby-code/table cases; broader manual-review
   policy remains open.
7. Add platform evidence adapters for Amiga, Atari, and Mac where facts already
   exist. Partially covered. Do not close this item until the adapter boundary is
   audited platform by platform.
8. Update renderers to consume the accepted records only. Partially covered.
   Do not close this item while renderer paths still consult structured-data
   records directly instead of a single range/table owner abstraction.
9. Add isolated C tests and fixture-backed tests. Partially covered. The
   explicit pointer-plus-length API buffer test now proves both dynamic
   source-analysis structured-data storage and accepted C range ownership for
   the exact bounded span. Continue adding tests only where they prove renderer
   migration, platform-adapter normalization, or unresolved conflict handling.
10. Regenerate source and run full rendered-source round-trip. Done for Pass 5:
    all 36 tracked `.s` files regenerated with no target diffs; round-trip
    report was 34/36 full-file exact, 1 content-exact-only, 1 unsupported, and
    0 failures.

### Pass 7: Renderer Ownership View

The seventh pass starts collapsing renderer ownership decisions onto a
range-owned surface.

Implemented changes:

- added `M68kRenderRangeOwnershipView`, a small renderer-facing view of the
  same C range ownership shape exported in source analysis;
- moved label suppression, structured-data start boundaries, structured row
  clear checks, API text-buffer overlap checks, Mac symbol-string blockers,
  and pointer-table target string promotion checks to query the ownership view
  before consulting record-specific rendering details;
- kept syntax emission intentionally separate: structured-data items are still
  passed to the formatter when the accepted owner says that span should render
  as structured data.

This is not the final renderer migration. It removes another class of direct
ownership decisions from raw structured-data records, but some formatting paths
still need record-specific fields until the accepted range/table records carry
all renderer operands.

Verification after this pass:

```text
cmd /c src\precommit.bat m68k_ir
uv run python -m pytest tests\test_c_backend.py -q
uv run platform-rendered-source-roundtrip
git diff --check
```

All 36 tracked target `.s` files were regenerated with no target source diffs.
Round-trip remained 34/36 full-file exact, 1 content-exact-only, 1 unsupported,
and 0 failures.

### Pass 8: Ownership-Backed Blocker Checks

The eighth pass migrates the remaining analysis-time blocker checks that were
still asking "does a structured-data item cover this byte?" when they really
meant "does an accepted owner already cover this byte?".

Implemented changes:

- API string segmentation now treats existing text ownership as compatible and
  non-text ownership as a blocker;
- auto structured-data insertion checks existing range ownership before adding
  a new generated item;
- palette, multiline text, bounded text, string-sequence, PC-relative lookup,
  word-relative dispatch, postincrement table, and orphan-code blocker scans now
  stop on range ownership rather than raw structured-data records;
- table-backed string target promotion counts existing accepted text ownership
  through the range view.

Formatter paths still use structured-data records where they need record
payload such as symbol names, constants, field names, table encoding, or text
rendering details. That is intentional until range/table records carry those
renderer operands directly.

Verification after this pass:

```text
cmd /c src\precommit.bat m68k_ir
uv run python -m pytest tests\test_c_backend.py -q
uv run platform-rendered-source-roundtrip
git diff --check
```

All 36 tracked target `.s` files were regenerated again with no target source
diffs. Round-trip remained 34/36 full-file exact, 1 content-exact-only,
1 unsupported, and 0 failures.

### Pass 9: Lookup-Owned Range Records

The ninth pass makes the renderer's range ownership view durable inside
`M68kRenderLookup` instead of rebuilding ownership from structured-data records
on every query.

Implemented changes:

- `M68kRenderLookup` now stores range ownership records for policy-seeded and
  auto-generated structured data;
- ownership records refer to policy/auto structured-data entries by source and
  index, not by raw pointer, so auto structured-data array growth cannot leave
  stale ownership references;
- policy untyped byte placeholders remain lower priority than accepted auto
  owners at the same offset, preserving the previous replacement behavior;
- renderer ownership checks and source-analysis range export both read the
  lookup-owned range records;
- `render_lookup_range_ownership_uses_stable_auto_indices` proves the stable
  index behavior and placeholder priority directly.

Structured-data records are still the payload source for formatting fields such
as text kind, table encoding, names, comments, constants, and platform fields.
The ownership decision surface is now separate and lookup-owned for the covered
records.

Verification after this pass:

```text
cmd /c src\precommit.bat m68k_ir
uv run python -m pytest tests\test_c_backend.py -q
uv run platform-rendered-source-roundtrip
git diff --check
```

All 36 tracked target `.s` files were regenerated with no target source diffs.
Round-trip remained 34/36 full-file exact, 1 content-exact-only, 1 unsupported,
and 0 failures.

### Pass 10: Descriptor Export From Lookup-Owned Ranges

The tenth pass moves source-analysis table descriptor export onto the same
lookup-owned range ownership records used by renderer ownership checks.

Before this pass, table descriptors were exported by iterating the
`M68kSourceAnalysisIR` structured-data mirror:

```text
source_analysis.structured_data_items
  -> table_descriptors
```

That kept descriptors coupled to the compatibility/export copy of structured
data even after the renderer had a lookup-owned ownership surface. The export
path now hydrates each lookup range owner, selects accepted table-shaped owners,
and emits descriptors from that owner:

```text
M68kRenderLookup.range_ownerships
  -> hydrate policy/auto structured item by stable source/index
  -> accepted table owner
  -> table_descriptor
```

This preserves current descriptor fields while removing another source-analysis
mirror dependency from ownership export. It also keeps later auto-item updates
safe because descriptor fields are read from the current item during hydration,
not from a stale pointer captured before table metadata was refined.

Still intentionally open:

- table descriptors are still exported records, not the sole renderer operand
  source for every table syntax decision;
- structured-data items still carry payload fields such as exact data kind,
  text shape, table expression kind, target, consumer, and source pattern;
- a later pass should either make table descriptors lookup-owned first-class
  records or make structured data explicitly one payload view over accepted
  range/table ownership.

Verification after this pass:

```text
cmd /c src\precommit.bat m68k_ir
uv run python -m pytest tests\test_c_backend.py -q
uv run platform-rendered-source-roundtrip
git diff --check
```

All 36 tracked target `.s` files were regenerated with no target source diffs.
Round-trip remained 34/36 full-file exact, 1 content-exact-only, 1 unsupported,
and 0 failures.

### Pass 11: Table Target Labels From Range Owners

The eleventh pass migrates table target-label materialization onto the same
lookup-owned ownership surface.

Before this pass, long-table target labels were materialized by walking the
policy and auto structured-data arrays directly:

```text
policy.structured_data_items + lookup.auto_structured_data_items
  -> render_lookup_materialize_long_table_targets
```

That was another ownership decision hidden behind a structured-data list walk.
The path now iterates `M68kRenderLookup.range_ownerships`, hydrates each current
owner, accepts only table ownership, and then materializes labels from the table
payload:

```text
lookup.range_ownerships
  -> accepted table owner
  -> table target labels
```

This keeps target-label creation tied to the accepted range/table ownership
surface instead of to every structured-data payload that happens to exist.
Formatting still reads structured-data payload fields after ownership is proven;
that remains the correct split until the table descriptor itself becomes the
primary renderer operand.

Verification after this pass:

```text
cmd /c src\precommit.bat m68k_ir
uv run python -m pytest tests\test_c_backend.py -q
uv run platform-rendered-source-roundtrip
git diff --check
```

All 36 tracked target `.s` files were regenerated with no target source diffs.
Round-trip remained 34/36 full-file exact, 1 content-exact-only, 1 unsupported,
and 0 failures.

### Pass 12: Lookup-Build Table Labels From Range Owners

The twelfth pass removes the remaining policy-list walk that materialized
pointer-table and absolute-long lookup target labels during initial lookup
construction.

Before this pass, lookup construction had a direct policy scan:

```text
policy.structured_data_items
  -> pointer/absolute-long table payload
  -> target labels
```

That meant a table-shaped policy payload could still create labels without
first passing through the same range ownership surface used by descriptor export
and later table label materialization. The initial build path now iterates
`M68kRenderLookup.range_ownerships`, hydrates table owners, and only then reads
the pointer/absolute-long payload:

```text
lookup.range_ownerships
  -> accepted table owner
  -> pointer/absolute-long payload
  -> target labels
```

This leaves raw payload decoding where it belongs, but removes another direct
ownership decision from policy storage.

Verification after this pass:

```text
cmd /c src\precommit.bat m68k_ir
uv run python -m pytest tests\test_c_backend.py -q
uv run platform-rendered-source-roundtrip
git diff --check
```

All 36 tracked target `.s` files were regenerated with no target source diffs.
Round-trip remained 34/36 full-file exact, 1 content-exact-only, 1 unsupported,
and 0 failures.

### Pass 13: Structured Payload Lookup Through Range Owners

The thirteenth pass routes the renderer's structured-data payload lookup helper
through range ownership.

Before this pass, `lookup_structured_data_item_at_offset` and
`lookup_structured_data_item_covering_offset` had their own policy/auto array
search and priority rules:

```text
policy structured-data list
  -> auto structured-data index/list
  -> payload item
```

That duplicated ownership ordering beside the newer range model. The helpers
now ask the range owner first and return the hydrated structured-data payload
attached to that owner:

```text
lookup_range_ownership_at_offset / covering_offset
  -> hydrated accepted owner
  -> payload item for formatting
```

This keeps existing formatter code stable while making placeholder priority and
auto-item replacement follow the single lookup-owned ownership view. The old
section-matching helper became dead code and was removed.

Verification after this pass:

```text
cmd /c src\precommit.bat m68k_ir
uv run python -m pytest tests\test_c_backend.py -q
uv run platform-rendered-source-roundtrip
git diff --check
```

All 36 tracked target `.s` files were regenerated with no target source diffs.
Round-trip remained 34/36 full-file exact, 1 content-exact-only, 1 unsupported,
and 0 failures.

### Pass 14: Analysis Pointer-Table Passes From Range Owners

The fourteenth pass migrates the remaining analysis-side pointer-table target
passes from policy/auto structured-data list walks to exact range-owner
iteration.

Before this pass, pointer-table target label materialization and pointer-table
target string promotion each scanned both structured-data storage surfaces:

```text
policy.structured_data_items + lookup.auto_structured_data_items
  -> long pointer-table payload
  -> target labels / target string promotion
```

Those scans were ownership-sensitive because they could promote target labels
or target strings from any table-shaped payload they found. The passes now use
an exact indexed range-owner hydration helper:

```text
lookup.range_ownerships[index]
  -> lookup_range_ownership_at_index
  -> accepted table owner
  -> pointer-table payload
  -> target labels / target string promotion
```

This keeps payload decoding and table-entry interpretation in C, but the
decision to act on the payload now flows through the same accepted range
ownership records used by rendering and source-analysis export.

Verification after this pass:

```text
cmd /c src\precommit.bat m68k_ir
uv run python -m pytest tests\test_c_backend.py -q
uv run platform-rendered-source-roundtrip
git diff --check
```

All 36 tracked target `.s` files were regenerated with no target source diffs.
Round-trip remained 34/36 full-file exact, 1 content-exact-only, 1 unsupported,
and 0 failures.

### Pass 15: Amiga Resident Metadata From Range Owners

The fifteenth pass migrates Amiga resident-context metadata reads from direct
policy structured-data scans to accepted range owners.

Before this pass, RS/layout rendering helpers checked `policy.structured_data`
directly for resident metadata:

```text
policy.structured_data_items
  -> RT / resident autoinit metadata
  -> resident library context and resident sizeof value
```

Those facts are platform metadata ownership records. The helpers now iterate
hydrated range owners and only consume payloads classified as
`platform_metadata`:

```text
lookup.range_ownerships[index]
  -> accepted platform_metadata owner
  -> Amiga resident payload
  -> RS/layout context
```

This is a platform-adapter cleanup rather than a renderer formatting change:
the Amiga-specific interpretation remains Amiga-specific, while the decision to
consume the bytes flows through the shared C range ownership model.

Verification after this pass:

```text
cmd /c src\precommit.bat m68k_ir
uv run python -m pytest tests\test_c_backend.py -q
uv run platform-rendered-source-roundtrip
git diff --check
```

All 36 tracked target `.s` files were regenerated with no target source diffs.
Round-trip remained 34/36 full-file exact, 1 content-exact-only, 1 unsupported,
and 0 failures.

## Open Design Questions

- What is the smallest status vocabulary that covers candidate, accepted,
  blocked, conflict, and deferred without duplicating manual review state?
- Should table descriptors live beside structured data items, or should
  structured data become one view over accepted range records?
- How should large descriptor-derived xref sets be paged or reported in JSON
  without bloating every normal analysis output?
- Which conflicts should produce manual review items, and which should simply
  render as residual bytes?

These are implementation questions, not reasons to keep ownership decisions in
renderers.

## Later Notes

- `src/benchmark.json` is still rewritten by the C precommit path with timing
  churn. That is unrelated to range/table analysis and should be handled as a
  tooling hygiene item so verification does not create avoidable review noise.
- `platform-rendered-source-roundtrip` previously rewrote target-local
  `reproduction.json` files while only reporting status. That report command now
  calls reproduction in non-persisting mode so volatile timestamps, timings, and
  mtime-based tool stamps do not create review noise.
- The current range ownership projection is intentionally a mirror of existing
  accepted facts. Later passes should make it the primary owner model used by
  table descriptors and renderers.
- All tracked target `.s` files were regenerated after the C range/table changes.
  The current `platform-rendered-source-roundtrip` result is 34/36 full-file
  exact, 1 content-exact-only target, 1 unsupported target, and 0 failures. The
  content-exact-only target is
  `amiga_disk_damocles-mercenary-ii-1990-novagen-cr-h__amiga_hunk_menu_252a2566`
  because its rendered-source rebuild differs only in HUNK container shape/size,
  not payload semantics. The unsupported target is the Mac MPW Asm artifact,
  which is still intentionally excluded from source assembly.
- Regeneration showed the useful effect of moving table facts into the C-owned
  model: accepted absolute/pointer dispatch entries in Pandora and Bloodwych now
  render symbolic table entries where the target is an accepted boundary.
- Regeneration also exposed the correct conservative policy for PC-indexed
  dispatch bases that resolve inside an instruction or to an otherwise
  unaccepted code target. Those entries now stay numeric/exact in rendered
  source and the C model marks the table/range with an unresolved-code-target
  conflict. Future review UI should surface those cases for user confirmation
  before promoting any intentional local-label expression.
- Removing the fixed 32-entry word-dispatch render cap makes the Mac CODE_1
  table at `CODE_1_data_000013b8` render as a larger word-relative dispatch
  table instead of a raw byte block. This is the intended direction: table size
  comes from structural bounds and accepted targets, while unresolved entries
  remain numeric rather than guessed.
- Hitting a source-visible target/table limit is an analysis failure signal.
  It should either be eliminated through descriptor iteration, or reported as a
  hard incomplete-analysis/conflict condition that blocks promotion. It should
  not silently fall back to byte rendering, because that hides inferior bounds
  behind source output that looks intentional.
- The fixed `M68kAnalysisPolicy` structured-data array is now explicitly a
  bounded input/ABI compatibility surface, not generated-analysis capacity.
  Future generated record types should follow the same pattern: dynamic C-owned
  source-analysis storage first, bounded mirrors only where an existing public
  API requires them.
- The decompression analysis JSON path now uses an isolated scratch arena for
  temporary event arrays. The previous shared-analysis-arena use was a valid
  repro of a nested arena lifetime/reentrancy hazard; future arena work should
  clarify which nested analysis paths may use shared arenas and add a focused
  contract test for that rule.
- The Voodoo same-process access violation was reproduced with a repeat-loop
  harness and fixed in the C renderer. Accepted-code range construction was
  scanning allocation/render extents while its byte ownership map represented
  stored bytes only. The fix keeps accepted-code range scans bounded to stored
  section bytes, preserving allocation-size metadata without reading past the
  map for Amiga sections with uninitialized tails.
- The Mac listing-artifact path now normalizes MacBinary/NDIF images through the
  same HFS-byte helper used by the import and payload paths before calling the C
  HFS parser. The C artifact path also reports concrete HFS/CODE creation
  failures instead of collapsing bare parser/load exits into a generic message.
