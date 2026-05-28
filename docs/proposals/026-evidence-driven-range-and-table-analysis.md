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

## Implementation Order

1. Add the C range/conflict record shape without changing rendering. Done in
   Pass 1.
2. Migrate existing string/text structured-data ownership into the range model.
   Started in Pass 1.
3. Add general label materialization and row splitting from accepted ranges.
4. Replace fixed table target storage with table descriptors and iterators.
   Started in Pass 2; descriptor records exist, iterator-driven rendering still
   remains.
5. Port existing pointer-table and relative-table recognizers onto descriptors.
6. Add arbitration rules for orphan code vs weak text shape.
7. Add platform evidence adapters for Amiga, Atari, and Mac where facts already
   exist.
8. Update renderers to consume the accepted records only.
9. Add isolated C tests and fixture-backed tests.
10. Regenerate source and run full rendered-source round-trip.

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
