# Proposal 028: Control-Flow-Derived Table Bounds and Data Reference Analysis

Status: In progress.

Proposal 025 made string/text acceptance evidence-driven. Proposal 026 made
range and table ownership a C-owned analysis result. The next gap is deeper:
many tables are now represented cleanly, but their bounds and targets are still
often limited by local shape checks rather than by the code that consumes them.

This proposal moves table sizing, table entry interpretation, and table-backed
data discovery into general C data-flow analysis.

## Checkpoint Index

- [ ] Problem Statement
- [ ] Tutorial: Why Table Bounds Belong To Control Flow
- [ ] Tutorial: Indexed Dispatch Table
- [ ] Tutorial: String Pointer Table
- [ ] Tutorial: Word-Offset Text Table
- [ ] Tutorial: Invalid Or Incomplete Entries
- [ ] Tutorial: False Code Islands And Text Blockers
- [ ] Tutorial: Character Constants And Fixed Tokens
- [ ] Invariant: No Bounded Fallbacks
- [ ] Core C Model
- [ ] Platform Extension Boundary
- [ ] Renderer Contract
- [ ] Implementation Slices
- [ ] Tests And Fixture Proof
- [ ] Related But Out Of Scope
- [ ] Verification Plan
- [ ] Acceptance Criteria
- [ ] Non-Goals
- [ ] Later Notes

## Problem Statement

The current range/table model prevents several old failures:

- fixed render caps no longer silently truncate known table output;
- labels are materialized at accepted table targets;
- table/conflict ownership lives in C instead of Python;
- weak string/code shape no longer overrides stronger evidence.

That is necessary, but not sufficient. A table is not fully understood merely
because bytes look like repeated words or longs. The strongest evidence is the
consumer code:

```asm
    cmpi.w  #24,d0
    bhi.w   out_of_range
    add.w   d0,d0
    move.w  table(pc,d0.w),d0
    jmp     table_base(pc,d0.w)
```

This tells us more than raw bytes can:

```text
index domain: 0..24
entry size: 2 bytes
entry count: 25
encoding: signed/unsigned word offset depending on the consumer
target base: table_base
stop reason: proven compare bound, not arbitrary scan limit
```

The analysis needs to preserve those facts as a descriptor. Without that, the
renderer either emits too little, emits guessed symbolic labels, or leaves useful
source as anonymous bytes.

The same analysis should also prevent the opposite failure: valid-looking
instructions or printable bytes must not become accepted ownership without real
control-flow, data-flow, table, API, relocation, platform, or manual evidence.
This is why Proposal 028 covers both table bounds and the data-reference facts
that make table targets meaningful.

## Tutorial: Why Table Bounds Belong To Control Flow

Shape-only table scanning is weak evidence.

This byte pattern might be a word table:

```asm
data_00002000:
    dc.w $0004,$0008,$000C,$0010
```

But the consuming code decides what it means:

```asm
    andi.w  #3,d0
    add.w   d0,d0
    move.w  data_00002000(pc,d0.w),d1
```

The C engine can derive:

```text
mask #3 -> index values 0..3
scale by 2 -> word entries
pc-relative read -> table base data_00002000
read target register d1 -> scalar table, not code dispatch
entry count -> 4
```

Now compare a similar-looking dispatch:

```asm
    cmpi.w  #3,d0
    bhi.s   default
    add.w   d0,d0
    move.w  jump_offsets(pc,d0.w),d0
    jmp     jump_base(pc,d0.w)
```

This derives a different descriptor:

```text
entry count -> 4
encoding -> pc-relative word dispatch
target base -> jump_base
entries -> code target offsets
```

The renderer should not infer either meaning from repeated words. It should
print what the C descriptor proves.

## Tutorial: Indexed Dispatch Table

Common M68K dispatch code:

```asm
dispatch:
    subq.w  #1,d0
    bmi.s   default
    cmpi.w  #5,d0
    bgt.s   default
    add.w   d0,d0
    move.w  case_table(pc,d0.w),d0
    jmp     case_base(pc,d0.w)

case_table:
    dc.w case_1-case_base
    dc.w case_2-case_base
    dc.w case_3-case_base
    dc.w case_4-case_base
    dc.w case_5-case_base
    dc.w case_6-case_base
```

The C data-flow model should record:

```text
consumer offset: dispatch+...
index register: d0
normalization: d0 = input - 1
range: 0..5
scale: 2
entry count: 6
entry size: 2
table base: case_table
target base: case_base
target kind: code
```

If `case_4` is accepted code and `case_5` is not, the descriptor should still
represent the whole table. Individual entries then carry their own status:

```text
entry 0 -> accepted code target
entry 1 -> accepted code target
entry 2 -> accepted code target
entry 3 -> unresolved code target
entry 4 -> accepted code target
entry 5 -> numeric exact entry
```

Good rendered output:

```asm
case_table:
    dc.w case_1-case_base
    dc.w case_2-case_base
    dc.w case_3-case_base
    dc.w $003A
    dc.w case_5-case_base
    dc.w $004E
```

The unresolved entries stay numeric. The table does not truncate, and the
renderer does not invent labels.

## Tutorial: String Pointer Table

Pointer tables often prove strings that are too short or too odd-looking for
shape-only detection.

Example:

```asm
    move.w  item_index(pc),d0
    lsl.w   #2,d0
    movea.l item_name_table(pc,d0.w),a0
    jsr     draw_text

item_name_table:
    dc.l item_none
    dc.l item_key
    dc.l item_acid

item_none:
    dc.b $00
item_key:
    dc.b "KEY",$00
item_acid:
    dc.b "ACID",$00
```

The table access proves the pointer table. The API or local text consumer proves
the target role. The short text entries become accepted because of table/API
evidence, not because every short printable span is globally accepted.

The C record should look like:

```text
table descriptor:
  kind: absolute_pointer_table
  entry_size: 4
  entry_count: proven from index bound or structural stop
  target_kind: text_candidate
  consumer: draw_text argument a0

target entries:
  item_none -> accepted empty/control string if consumer permits empty
  item_key -> accepted string_table_entry
  item_acid -> accepted string_table_entry
```

If a target overlaps accepted code, the text entry is blocked and the table
entry remains numeric or conflict-marked.

## Tutorial: Word-Offset Text Table

Some games use compact word offsets into a text pool:

```asm
    andi.w  #$7F,d0
    add.w   d0,d0
    move.w  text_offsets(pc,d0.w),d1
    lea.l   text_pool(pc),a0
    adda.w  d1,a0
    jsr     print_text

text_offsets:
    dc.w text_hello-text_pool
    dc.w text_yes-text_pool
    dc.w text_no-text_pool

text_pool:
text_hello:
    dc.b "HELLO",$00
text_yes:
    dc.b "YES",$00
text_no:
    dc.b "NO",$00
```

Important nuance: a mask is range evidence, not necessarily an entry-count
proof. `andi.w #$7F,d0` says the runtime index is within `0..127`, but it does
not prove all 128 entries exist. The descriptor needs separate fields:

```text
index_value_domain: 0..127
entry_count_proof: structural table scan / compare / loop / explicit count
entry_count: only when proven
```

If only three entries are structurally valid, do not synthesize 125 extra
entries. If a later compare proves fewer entries than the mask, the compare wins
for bounds:

```asm
    andi.w  #$7F,d0
    cmpi.w  #2,d0
    bhi.s   default
```

Derived result:

```text
mask domain: 0..127
branch domain: 0..2
effective entry count: 3
proof: compare/branch
```

## Tutorial: Invalid Or Incomplete Entries

An entry can be valid table data without being a valid symbolic target.

Example:

```asm
case_table:
    dc.w case_a-case_base
    dc.w $0003
    dc.w case_c-case_base
```

If `$0003` points inside an instruction, the correct output is not:

```asm
    dc.w case_mid_instruction-case_base
```

The correct C result is:

```text
entry 1:
  raw_value: 3
  resolved_target: case_base+3
  status: conflict
  conflict_state: unresolved_code_target or interior_instruction_target
  render: numeric exact
```

This is a review signal. It might be intentional hand-written assembly, but it
must not become a portable symbolic expression until analysis or user evidence
proves that interpretation.

## Tutorial: False Code Islands And Text Blockers

Valid M68K decoding is not enough to accept code.

Starglider-style data can decode into plausible instructions:

```asm
loc_0_00006098:
    ori.w   #112,$0(a0,d0.w)
    ori.b   #136,d0
    dc.b    $00,$88,$00,$00,$00,$00,$01,$04
```

That should not be promoted as code merely because the disassembler can read
it. The C engine needs accepted inbound evidence:

```text
accepted code evidence:
  entrypoint
  branch/call target
  table target with accepted table descriptor
  callback/vector/API/platform evidence
  manual seed

weak code shape:
  valid opcode stream
  terminal instruction nearby
  plausible prologue bytes
```

Weak code shape may create a review signal or block a weak string claim. It must
not create accepted code by itself.

The inverse failure is also important. Printable bytes can be polluted by an
embedded terminal opcode or an orphan instruction island:

```asm
    dc.b $4C,$DF,$7F,$FF,$4E,$75,$48,$E7
    dc.b "NuD0        00000000",$00
```

Here `4E 75` is `rts`, but that does not automatically prove code. It is
negative evidence against a shape-only string. The disposition should be:

```text
string candidate:
  positive: printable/NUL shape
  negative: nearby orphan terminal decode
  status: candidate or blocked, not accepted

code candidate:
  positive: terminal decode shape
  negative: missing inbound control-flow
  status: report-only orphan signal, not accepted
```

This keeps source conservative: exact bytes render, review can inspect the
signal, and neither code nor string is invented.

## Tutorial: Character Constants And Fixed Tokens

Some text-looking bytes are not strings. They are fixed tokens, magic values, or
four-character constants used by code.

Example:

```asm
    cmp.l   #'CODE',d1
    beq.s   is_code
    cmp.l   #'HUNK',d1
    bne.s   not_hunk
```

The bytes are printable, but the correct model is not a string range. It is an
immediate constant with a text representation because the instruction compares a
register to a fixed token.

Another example is a short inline text fragment adjacent to a proven string:

```asm
libs_prefix:
    dc.b "LIBS:"
library_name:
    dc.b "monam.libfile",$00
```

This can be accepted as text only if usage proves a bounded text span, such as:

```text
consumer passes pointer+length to an API
table entry bounds the text pool member
neighboring accepted string/table records prove a fixed-width row
manual seed declares exact text bounds
```

The C model should therefore distinguish:

```text
immediate_text_token:
  source: instruction immediate
  render: quoted immediate if assembler-compatible
  ownership: instruction operand, not data range

fixed_text_range:
  source: bounded data reference
  render: dc.b quoted bytes
  ownership: accepted text/data range
```

This gives readable source without globally accepting uppercase words or
English-looking fragments.

## Invariant: No Bounded Fallbacks

Capacity limits must not change analysis meaning.

Bad behavior:

```text
first 64 entries fit fixed array
remaining entries are dropped
renderer falls back to dc.b
round-trip still passes
```

That is a hidden analysis failure. The source remains byte-exact, but the user
loses real structure and the report looks intentional.

Correct behavior:

```text
descriptor iterator has dynamic storage or streaming access
all proven entries are representable
if storage cannot represent them:
  emit analysis_error / incomplete_analysis
  block symbolic promotion
  keep exact bytes
  report the capacity failure
```

This applies to:

- table entry sets;
- xref sets;
- generated labels;
- structured-data records;
- orphan-code signals;
- text/table target pools.

No implementation should fix a large target by increasing a magic number unless
that number is a documented file-format or platform limit. General analysis
result storage must be dynamic, paged, or explicitly error-producing.

## Core C Model

The C engine should add or extend table-consumer facts that sit beside range
ownership and table descriptors.

Illustrative shape:

```c
typedef enum M68kTableBoundProofKind {
    M68K_TABLE_BOUND_NONE = 0,
    M68K_TABLE_BOUND_MASK,
    M68K_TABLE_BOUND_COMPARE_BRANCH,
    M68K_TABLE_BOUND_LOOP_LIMIT,
    M68K_TABLE_BOUND_STRUCTURAL_STOP,
    M68K_TABLE_BOUND_PLATFORM_RECORD,
} M68kTableBoundProofKind;

typedef enum M68kTableEntryTargetStatus {
    M68K_TABLE_ENTRY_TARGET_NUMERIC = 0,
    M68K_TABLE_ENTRY_TARGET_ACCEPTED_CODE,
    M68K_TABLE_ENTRY_TARGET_ACCEPTED_DATA,
    M68K_TABLE_ENTRY_TARGET_ACCEPTED_TEXT,
    M68K_TABLE_ENTRY_TARGET_UNRESOLVED,
    M68K_TABLE_ENTRY_TARGET_CONFLICT,
} M68kTableEntryTargetStatus;
```

Descriptor extensions should be able to express:

- consumer instruction offset;
- index register and value domain;
- normalization such as subtracting a base value;
- scale;
- entry size;
- table base;
- target base;
- signedness;
- entry count and proof kind;
- stop reason;
- per-entry raw value, resolved target, and target status.

The engine should derive these from accepted instruction semantics and facts,
not from renderer text.

The same model should expose data-reference facts used by table targets:

- pointer plus length;
- pointer plus terminator contract;
- fixed-width row count;
- immediate fixed-token operand;
- table target pool bounds;
- accepted text/data/code owner at the resolved target;
- negative evidence such as accepted-code overlap, interior instruction target,
  orphan terminal decode, or structured-data overlap.

These facts should attach to C entities that already exist in the analysis:
instructions, operands, table descriptors, range ownership records, labels, and
platform/API facts. Python should only display or export them.

## Platform Extension Boundary

This proposal is primarily platform-neutral.

Core C analysis owns:

- instruction semantics;
- register/data-flow facts;
- index bounds;
- table descriptors;
- target resolution;
- conflict states.

Platform extensions may contribute:

- executable section bounds;
- relocation/fixup ownership;
- API contracts such as text buffer pointer/length arguments;
- platform record bounds such as Mac CODE 0 jump-table metadata;
- API return and argument type metadata as evidence for later type propagation;
- known address-space ownership such as Amiga hardware or Atari TOS regions.

Platform extensions must not invent table entries by target name or target
fixture. They provide facts; the shared C table engine consumes those facts.

## Renderer Contract

Renderers consume table descriptors and range ownership.

Renderer responsibilities:

- choose assembler syntax;
- emit labels for accepted targets;
- keep unresolved entries numeric;
- preserve exact bytes;
- render conflict state in reports/metadata, not as noisy inline debug comments.

Renderer non-responsibilities:

- proving table bounds;
- widening tables after a cap;
- accepting string targets from shape alone;
- turning interior targets into labels;
- deciding whether unresolved code is real code.

Readable output should improve only when C evidence improves. For example:

```asm
    cmp.l   #'CODE',d1
```

is a renderer syntax choice over an immediate-token fact, while:

```asm
libs_prefix:
    dc.b "LIBS:"
```

is a renderer syntax choice over an accepted bounded text range. The renderer
must not use the same printable-byte heuristic to create both.

## Implementation Slices

The work should be implemented as small C-owned vertical slices. Each slice
should improve source quality only where evidence is proven, regenerate tracked
source after output-affecting changes, and preserve rendered-source round-trip.

### 1. Table Consumer Fact Records

Add table-consumer records that can be attached to accepted instruction facts:

```text
consumer instruction
  -> index register
  -> table base operand
  -> access width
  -> target register/value
```

This slice should not change rendering. It creates the durable analysis surface
that later slices consume.

### 2. Index Domain And Scaling

Derive value domains from simple, local instruction evidence:

```asm
    andi.w  #$1F,d0
    cmpi.w  #12,d0
    bhi.s   default
    add.w   d0,d0
```

The model must keep mask domain and compare/branch domain separate. A mask can
bound possible values without proving all entries exist.

### 3. Descriptor Bound Proofs

Extend table descriptors with proof fields:

```text
entry_count
entry_count_proof
index_value_domain
stop_reason
consumer_offset
```

Structural scans may still supply a stop reason, but they must not override a
stronger compare/branch or platform-record bound.

### 4. Per-Entry Target Status

Represent every proven entry without requiring every entry to become symbolic:

```text
raw value -> resolved target -> target owner/status -> render form
```

Accepted targets render symbolically. Unresolved, interior, conflicting, or
unsupported targets render numeric/exact and emit structured conflict evidence.

### 5. Data-Reference Facts

Generalize the same evidence path for non-dispatch data:

- pointer plus length;
- pointer plus terminator contract;
- immediate fixed token;
- fixed-width row;
- table-backed text/data target;
- accepted API argument/return type evidence.

These facts should improve strings and data only when they prove exact bounds.

### 6. False-Code And Weak-Text Arbitration

Move Starglider-style false opcode islands and terminal orphan blockers onto
the same conflict/evidence model:

```text
valid decode without inbound evidence -> report-only code-shape signal
printable text with nearby report-only code-shape signal -> blocked/candidate
accepted branch/table/API evidence -> accepted owner
```

This prevents both false code and false strings.

### 7. Capacity Failure Hardening

Audit table-entry, xref, label, structured-data, and orphan-signal storage. Any
source-visible capacity hit must become an explicit incomplete-analysis result
or use dynamic/paged storage. It must not silently drop records and fall back to
anonymous bytes.

### 8. Platform Adapter Audit

Verify Amiga, Atari, and Mac adapters only contribute facts:

```text
platform parser/API/runtime fact
  -> shared C data-reference/table model
  -> renderer/report projection
```

Any platform path that directly accepts table/text/code ownership should be
migrated or documented as unsupported.

## Tests And Fixture Proof

No-fixture C tests should cover:

- compare/branch bound derives exact entry count;
- mask-only bound is recorded as a value domain but does not synthesize entries;
- scale inference derives entry size;
- pointer table target strings are promoted only with table/API evidence;
- unresolved code target entries stay numeric and conflict-marked;
- interior instruction targets do not become labels;
- valid-looking opcode islands without inbound evidence remain report-only;
- orphan terminal decode blocks weak string acceptance without accepting code;
- immediate four-character constants render from operand facts, not data ranges;
- bounded uppercase/punctuation fragments require usage evidence before text
  promotion;
- structural stop records why iteration ended;
- descriptor iteration handles large tables without fixed caps;
- capacity exhaustion produces an explicit analysis error/incomplete state, not
  a silent raw-byte fallback.

Fixture-backed tests should double-check representative target examples:

- Pandora absolute and word-offset tables;
- Bloodwych wide pointer/dispatch tables;
- Magicland control/text tables where code references prove shape;
- Starglider false string/code conflicts;
- MonAm/GenAm string and line-output tables;
- MonAm/GenAm immediate token comparisons and short fixed text fragments;
- Mac CODE 0/CODE N tables only where parser and CODE metadata provide exact
  bounds.

All fixture tests should cite target id, section/resource, and offset so a
failed assertion points to inspectable source.

## Related But Out Of Scope

TODO.md contains several adjacent concerns that should not be folded into this
proposal unless they directly provide table/data-reference evidence.

### API Type Propagation And Naming

Calls such as Amiga `OpenScreen` and `OpenWindow` should eventually propagate
types into `NewScreen`, `NewWindow`, returned `Screen *`, returned `Window *`,
RS-relative storage, and generated names such as `app_ScreenPtr`.

Proposal 028 may consume API argument/return type facts as evidence, but full
type propagation, structure-field rendering, and semantic naming should be a
separate proposal.

### External Resource Provenance

Magicland disk reads need an external-resource relationship model:

```text
disk routine -> track/sector bytes -> loaded buffer -> child target or data asset
```

That requires proving exact disk bytes and load sizes. It is not table-bound
analysis, although table/data-reference facts may later classify the loaded
payload.

### Decompression And Native Unpackers

Conqueror payload extraction and Magicland `MLDC` asset decompression belong to
Proposal 027 or a later asset-decompression proposal. Proposal 028 can classify
references to packed buffers or output buffers, but it does not execute or
replace decompression routines.

### OS Compatibility Header Presentation

The Amiga OS compatibility header needs presentation cleanup and clearer
deduplication. That is source-report UX work, not table/data-reference
analysis.

## Verification Plan

Output-affecting implementation slices must run:

```text
cmd /c src\precommit.bat m68k_ir
uv run python -m pytest tests\test_c_backend.py -q
amiga-source-export for every tracked target .s file
uv run platform-rendered-source-roundtrip
git diff --check
```

The round-trip report must continue to include all tracked platforms. Mac source
assembly may remain explicitly unsupported, but it must not be silently skipped.

For documentation-only edits to this proposal, `git diff --check` is sufficient
unless the edit changes source-generation instructions, acceptance criteria, or
verification expectations.

## Implementation Progress

### Pass 1: Table Consumer Fact Records

The first implementation pass adds first-class C table consumer records to
`M68kSectionAnalysisIR`.

Before this pass, table descriptors carried consumer offsets, but consumers were
not exported as their own analysis surface. That made later 028 work harder:
index-domain, scaling, target-register, and per-entry status facts had no stable
record to attach to.

Current record shape:

```text
table_consumer:
  consumer_offset
  table_section_index
  table_start_offset / table_end_offset
  access_width
  entry_count
  table_kind
  source_pattern
  optional index register
  optional target register
```

This pass derives the initial consumer record from table descriptors that
already have `has_consumer`, including conflict descriptors where the consumer
itself is still valid evidence. The index and target register fields are
nullable for now because existing descriptor data does not yet preserve them.
Later passes should fill those fields from instruction operands and data-flow
facts rather than guessing from rendered text.

The implementation deliberately does not change rendered source. It only makes
the consumer fact durable in source-analysis JSON, so future slices can attach
bounds and entry status without re-scanning renderer state.

Covered by:

- `source_analysis_table_descriptor_exports_consumer_fact`

Verification after this pass:

```text
cmd /c src\precommit.bat m68k_ir
uv run python -m pytest tests\test_c_backend.py -q
all 36 tracked `.s` files regenerated
uv run platform-rendered-source-roundtrip
```

The regenerated sources had no tracked `.s` diffs. Round-trip remained
`34/36` full-file exact, `1/36` content-exact-only, `1/36` unsupported, and
`0` failures.

### Pass 2: C-Owned Consumer Register Evidence

The second implementation pass keeps table consumer register evidence in C from
recognition through source-analysis export.

Before this pass, the newly exported `table_consumer` records had nullable
register fields even when the recognizer had already proven them from the
instruction operands. That lost useful evidence for later bounds and data-flow
work.

The C structured-data item now records:

```text
has_index_register
index_register_kind / index_register
has_target_register
target_register_kind / target_register
```

Those fields are copied into table descriptors and then into table consumer
records. Recognizers populate them only where the operand/data-flow match has
already proved the relationship:

```text
move.l  $0(a0,d0.w),d1
        index register  = d0
        target register = d1

move.w  table(pc,d0.w),d1
jmp     base(pc,d1.w)
        index register  = d0
        target register = d1
```

No rendered-source parsing is involved, and Python only mirrors the C struct
layout needed for tests. This keeps the C analysis engine as the owner of table
consumer facts.

Covered by:

- `facts_v2_indexed_local_base_auto_classifies_pointer_table`
- `source_analysis_table_descriptor_exports_consumer_fact`

Verification after this pass:

```text
cmd /c src\precommit.bat m68k_ir
uv run python -m pytest tests\test_c_backend.py -q
all 36 tracked `.s` files regenerated
uv run platform-rendered-source-roundtrip
```

The regenerated sources had no tracked `.s` diffs. Round-trip remained
`34/36` full-file exact, `1/36` content-exact-only, `1/36` unsupported, and
`0` failures.

### Pass 3: PC-Indexed ADD Dispatch Consumers

The third implementation pass extends the same consumer-register evidence to
the common two-step dispatch form:

```asm
    lea     case_base,a0
    adda.w  case_table(pc,d1.w),a0
    jmp     (a0)
```

The important fix is not Mac-, Amiga-, or target-specific. The C recognizer now
resolves the indexed source operand through the shared indexed operand target
helper, so address-register indexed and PC-indexed table bases use the same
analysis path. It also uses the shared indexed-or-PC-indexed EA predicate instead
of treating only address-register indexed operands as table consumers.

The resulting table consumer records preserve:

```text
index register  = d1
target register = a0
table base      = case_table
target base     = case_base
```

This closes one of the early 028 gaps where rendered source could show the
correct instruction operand while the exported table-consumer fact still lacked
the register evidence needed by later bound and data-reference passes.

Covered by:

- `facts_v2_pc_word_dispatch_descriptor_promotes_targets_beyond_inline_set`

Verification after this pass:

```text
cmd /c src\precommit.bat m68k_ir
uv run python -m pytest tests\test_c_backend.py -q
all 36 tracked `.s` files regenerated
uv run platform-rendered-source-roundtrip
```

The regenerated sources had no tracked `.s` diffs. Round-trip remained
`34/36` full-file exact, `1/36` content-exact-only, `1/36` unsupported, and
`0` failures.

### Pass 4: Entry Count Proof Surface

The fourth implementation pass adds an explicit C-owned proof field for table
entry counts. Existing descriptors already exposed `entry_count`, but did not
say why that count was valid. That was too weak for later bound and import gates
because consumers could not distinguish an accepted structured range from
consumer-derived structural analysis or relocation records.

Current proof categories:

```text
unknown
structured_range
consumer_structural_scan
relocation_record
platform_record
```

The field is carried on:

```text
M68kAnalysisStructuredDataItem
M68kTableDescriptorIR
M68kTableConsumerIR
listing/source-analysis JSON
```

The mapping is deliberately conservative. Existing indexed table and string
table recognizers report `consumer_structural_scan`: the consuming instruction
proves the table base and access shape, while the current table extent is still
the structural scan result. That is not yet a compare/branch bound proof, and
the JSON no longer leaves that ambiguity hidden.

Covered by:

- `source_analysis_range_ownership_records_code_text_and_table`
- `source_analysis_table_descriptor_exports_consumer_fact`
- `test_real_dll_026_table_descriptors_use_evidence_bounds_not_caps`

Verification after this pass:

```text
cmd /c src\precommit.bat m68k_ir
uv run python -m pytest tests\test_c_backend.py -q
all 36 tracked `.s` files regenerated
uv run platform-rendered-source-roundtrip
```

The regenerated sources had no tracked `.s` diffs. Round-trip remained
`34/36` full-file exact, `1/36` content-exact-only, `1/36` unsupported, and
`0` failures.

### Pass 5: Index Domain Evidence Surface

The fifth implementation pass adds explicit C-owned index-domain evidence to
table descriptors and table consumers. Entry count proof says why the table
span is accepted; index-domain proof says what the consuming code proves about
the register used to index the table.

Current exported domain facts:

```text
index_mask_domain    -> andi.w/and.w immediate mask, recorded as min/max
index_compare_domain -> cmpi.w/cmp.w immediate plus out-of-range branch
branch_mnemonic      -> branch instruction proving the compare-domain exit
```

The first implemented derivation covers the local 68000 word-dispatch idiom:

```asm
    andi.w  #$0007,d1
    cmpi.w  #5,d1
    bhi.s   default
    add.w   d1,d1
    lea.l   case_base.l,a0
    adda.w  case_table(pc,d1.w),a0
    jmp     (a0)
```

The C recognizer now records:

```text
index register        = d1
mask domain           = 0..7
compare domain        = 0..5
compare branch        = bhi
table/target register = case_table / a0
```

The derivation is intentionally conservative. It records only local contiguous
evidence, requires the word-index scale instruction before a word table access,
and does not convert the structural table extent into a compare-bound entry
count yet. Later passes can use these fields to promote a stronger
compare-bound proof without rereading source text or renderer output.

This pass also prevents later generic PC-relative read recognition from
overwriting a stronger dispatch source pattern on the same structured table
record.

Covered by:

- `source_analysis_table_descriptor_exports_consumer_fact`
- `facts_v2_pc_word_dispatch_descriptor_exports_index_domains`

Verification after this pass:

```text
cmd /c src\precommit.bat m68k_ir
uv run python -m pytest tests\test_c_backend.py -q
all 36 tracked `.s` files regenerated
uv run platform-rendered-source-roundtrip
```

The regenerated sources had no tracked `.s` diffs. Round-trip remained
`34/36` full-file exact, `1/36` content-exact-only, `1/36` unsupported, and
`0` failures.

### Pass 6: Exact Domain Entry Count Proof

The sixth implementation pass promotes domain evidence into an entry-count
proof only when it exactly matches the accepted table span.

Promotion rule:

```text
if compare_domain = 0..N and entry_count = N + 1:
  entry_count_proof = index_compare_domain
else if mask_domain = 0..N and entry_count = N + 1:
  entry_count_proof = index_mask_domain
else:
  keep the existing structural/relocation/platform proof
```

This is deliberately not a resizing rule. A compare or mask domain may be
recorded even when the current table extent is still structural; it becomes the
entry-count proof only when the table descriptor already has the matching
number of entries. That keeps 028 fail-closed: mismatched evidence is visible
to consumers, but does not silently crop, extend, or normalize the table.

The source-pattern setter now also preserves stronger entry-count proof when a
later weaker recognizer touches the same table record.

Covered by:

- `facts_v2_pc_word_dispatch_descriptor_exports_index_domains`

Verification after this pass:

```text
cmd /c src\precommit.bat m68k_ir
uv run python -m pytest tests\test_c_backend.py -q
all 36 tracked `.s` files regenerated
uv run platform-rendered-source-roundtrip
git diff --check
```

The regenerated sources had no tracked `.s` diffs. Round-trip remained
`34/36` full-file exact, `1/36` content-exact-only, `1/36` unsupported, and
`0` failures.

### Pass 7: Per-Entry Target Status Surface

The seventh implementation pass adds first-class C IR rows for individual table
entries. Descriptor-level bounds are not enough for later 028 consumers: each
entry needs its own raw value, resolved target, target status, and conflict
state so renderers and reports do not have to rediscover table semantics from
formatted source.

The new surface is:

```text
M68kTableEntryIR
section.table_entries[]
source-analysis JSON table_entries[]
```

Each row records:

```text
table_start_offset
entry_index
entry_offset
entry_size
raw_value / raw_value_width
table_kind / source_pattern
target_status
target_section_index / target_offset, when resolved
conflict_state
```

Initial C population covers the table shapes already represented by durable
structured table records:

```text
word relative dispatch/data lookup
keyed long relative dispatch
absolute long code dispatch
long pointer tables
numeric scalar entries
```

For code dispatch entries, the status is derived from the accepted-code maps:
accepted instruction starts become `accepted_target`; targets inside accepted
instructions become `interior_code_target`; in-section but unaccepted code
targets become `unresolved_target` with `unresolved_code_target` conflict
state. Numeric entries remain `numeric_exact`.

Covered by:

- `source_analysis_table_entry_exports_status`
- `facts_v2_pc_word_dispatch_descriptor_exports_index_domains`

Verification after this pass:

```text
cmd /c src\precommit.bat m68k_ir
uv run python -m pytest tests\test_c_backend.py -q
all 36 tracked `.s` files regenerated
uv run platform-rendered-source-roundtrip
git diff --check
```

The regenerated sources had no tracked `.s` diffs. Round-trip remained
`34/36` full-file exact, `1/36` content-exact-only, `1/36` unsupported, and
`0` failures.

### Pass 8: Table-Backed Data Reference Facts

The eighth implementation pass adds a shared C data-reference fact surface for
non-code table targets. Table entries now remain the per-entry record, while
data references expose the consumer-facing relationship:

```text
table entry -> accepted data target
```

The new surface is:

```text
M68kDataReferenceIR
section.data_references[]
source-analysis JSON data_references[]
```

The first producer is intentionally narrow and evidence-backed. When a
structured table entry resolves to an accepted non-code target, C emits a data
reference carrying:

```text
source_offset
source_kind = table_entry
table_start_offset
table_entry_index / offset / size
raw_value
table_kind / source_pattern
target_section_index / target_offset
target_status
evidence_flags
conflict_state
```

This covers pointer tables and relative data lookups without requiring Python
or reports to infer data references from rendered labels. Code dispatch entries
stay represented as table entries and code-start/control-flow facts.

Covered by:

- `source_analysis_data_reference_exports_table_entry`
- `facts_v2_indexed_local_base_auto_classifies_pointer_table`

Verification after this pass:

```text
cmd /c src\precommit.bat m68k_ir
uv run python -m pytest tests\test_c_backend.py -q
all 36 tracked `.s` files regenerated
uv run platform-rendered-source-roundtrip
```

The regenerated sources had no tracked `.s` diffs. Round-trip remained
`34/36` full-file exact, `1/36` content-exact-only, `1/36` unsupported, and
`0` failures.

## Acceptance Criteria

This proposal can close when:

- table descriptors carry consumer-derived bounds where the code proves them;
- mask, compare, branch, loop, and structural-stop evidence are recorded
  separately;
- table entry iteration has no source-visible fixed caps;
- capacity exhaustion is reported as incomplete analysis instead of silently
  falling back to unstructured bytes;
- unresolved or conflicting entries remain numeric/exact and reviewable;
- table-backed string/data/code targets are accepted only from durable evidence;
- valid-looking opcode islands without inbound evidence do not become accepted
  code and can block weak string claims;
- immediate character constants and bounded fixed text ranges are represented as
  separate C-owned facts;
- Amiga, Atari, and Mac paths use the same core C table model;
- all tracked target `.s` files are regenerated after output-affecting changes;
- rendered-source round-trip remains at least at the current status:
  full-file exact where possible, content-exact where container shape is known
  unsupported, explicit unsupported where source assembly is not available, and
  zero failures.

## Non-Goals

This proposal does not require:

- human symbol names;
- decompiler-style high-level switch reconstruction;
- full API-driven type propagation and semantic variable naming;
- disk/resource child-target provenance;
- source-compatible local labels for intentional interior-byte references
  without proof;
- per-target table whitelists;
- Python ownership decisions;
- changing unsupported Mac source assembly status;
- solving native unpacker/decompression execution, which belongs to Proposal
  027.

## Later Notes

- TODO.md still contains Mac container browsing work. That belongs to UI/import
  pipeline behavior, not table/data-reference analysis.
- TODO.md still contains Conqueror payload extraction and Magicland
  asset-decompression notes. Those should feed Proposal 027 or a later
  asset-decompression proposal.
- TODO.md still contains API type-propagation and semantic naming work. Proposal
  028 should expose enough data-reference facts for that later work to consume,
  but should not decide naming policy.
- TODO.md still contains OS compatibility header presentation concerns. Those
  should be handled as report/source UX cleanup after the underlying API facts
  remain stable.
- The current source round-trip baseline before Proposal 028 implementation is
  `34/36` full-file exact, `1/36` content-exact-only, `1/36` unsupported, and
  `0` failures. Implementation must preserve or improve that baseline.
