# Proposal 025: Evidence-Driven String and Text Analysis

Status: active

## Purpose

Make string rendering a reliable analysis result, not a pretty-print side
effect.

Current output already finds useful strings, but it also shows the limits of
shape-only detection:

- real text blocks are sometimes only partly rendered as text;
- string tables are detected entry-by-entry instead of as one structured table;
- printable instruction bytes can become false string rows;
- Mac Pascal/symbol records need platform-specific handling that must not leak
  into Amiga or Atari targets.

This proposal is the working plan. We will not create separate issue files for
it. Implementation should proceed directly from this document, updating it as
the model becomes more precise.

## Current Behavior

The current string path is mostly C-owned in
`src/m68k_analysis_render_lookup.c`.

At render-lookup time, the analysis scans bytes that are not already owned by
accepted instructions, relocations, labels, anchors, or structured data. If a
span looks safe, it creates a structured data item:

```text
target bytes
  -> accepted code mask
  -> render lookup scan
  -> auto structured data item
  -> source_analysis.policy.structured_data_items[]
  -> rendered dc.b quoted text
  -> listing row data_class
```

Representative rendered output:

```asm
loc_0_00000026:
    dc.b "dos.library",$00    ; string
```

That is useful because it gives the user source, row metadata, and a durable
classification. The problem is that the classification reason is often implicit:
we can see `; string`, but not whether it came from a terminator shape, a pointer
table, an OS API argument, a Mac symbol record, or a nearby text cluster.

## Target Outcome

String analysis should produce explicit evidence-backed records before rendering.

Target model:

```text
bytes + accepted code + xrefs + platform metadata
  -> string candidates
  -> positive evidence
  -> negative evidence
  -> table/stream grouping
  -> structured data records
  -> readable source rendering
  -> fixture double-checks
```

Each accepted string-like range should have:

- byte range and terminator/range shape;
- source evidence: shape, access, table membership, platform record, or manual
  seed;
- confidence/status;
- negative evidence considered;
- render role: `string`, `string_table_entry`, `fixed_width_text_row`,
  `macos_symbol_string`, `string_control_stream`, etc.

Illustrative C-side record shape:

```json
{
  "kind": "string",
  "section_index": 0,
  "offset": 31264,
  "size": 10,
  "encoding": "ascii",
  "terminator": "nul",
  "evidence": ["printable_span", "pointer_table_target"],
  "negative_evidence": [],
  "table_id": "string_table_00007a44",
  "status": "accepted"
}
```

Rendering should become an effect of that model:

```asm
string_table_00007A44:
rank_ace_pilot:
    dc.b "ACE PILOT",$00
rank_commander:
    dc.b "COMMANDER",$00
```

## Why Shape Alone Is Not Enough

The same bytes can be valid text, code, or structured data depending on context.

Example: Starglider has printable-looking bytes that currently render as a
string:

```asm
    dc.b "NuNu    ",$00    ; string
```

But the surrounding bytes contain code-shaped material, including `RTS`
opcodes. `N`/`u` are also valid opcode bytes. The analysis should treat this as
negative evidence:

```text
candidate text span
  contains or neighbors accepted/orphan code pattern
  includes terminating instruction opcode sequence
  no string access evidence
  -> do not auto-accept as string
  -> optionally emit review signal
```

The goal is not to ban all printable instruction bytes. The goal is to avoid
claiming a string when the stronger evidence says this range is likely orphaned
code or mixed code/data.

## General Analysis Layers

### 1. Candidate Discovery

Candidate discovery is allowed to be broad, but must not be final.

General candidates:

- nul-terminated printable ASCII;
- `$FF`-terminated game text;
- CR/LF multiline text;
- adjacent short string clusters;
- fixed-width text rows;
- length-prefixed byte records;
- pointer-table targets;
- API argument targets.

Candidate example:

```asm
abs_0_00012E20:
    dc.b "EARTH ORBIT ESTABLISHED, MUTANT SPORES RELEASED.",$00
abs_0_00012E51:
    dc.b "TOTAL DESTRUCTION OF HUMANITY IMMINENT.",$00
abs_0_00012E79:
    dc.b $30,$31,$32,$33,$34,$35,$36,$37,$38,$39,$41,$42,$43,$44,$45,$46
    dc.b $00
```

The third row is a missed plain string candidate: `0123456789ABCDEF`.
Table/cluster context should help promote it.

### 2. Positive Evidence

Positive evidence increases confidence and may allow shapes that are too weak in
isolation.

Evidence sources:

- direct pointer table entry targets this offset;
- indexed string table access scans entries;
- OS/platform API metadata says a register or stack argument is a string
  pointer;
- code walks bytes until `0`, `$FF`, or fixed stride;
- neighboring entries form a consistent table;
- platform parser identifies a known string record format.

Amiga example: `dos.library` is strong because API metadata knows an input is a
string pointer:

```asm
    lea.l loc_0_00000026(pc),a1
    jsr _LVOFindResident(a6)

loc_0_00000026:
    dc.b "dos.library",$00    ; string
```

This is better than text-shape alone. The call contract proves why the bytes
are string data.

### 3. Negative Evidence

Negative evidence blocks or downgrades candidates.

Blockers:

- accepted code overlap;
- relocation overlap;
- label/anchor inside a candidate unless it is a proven table boundary;
- structured data overlap;
- orphan-code signal inside or adjacent to the candidate;
- likely instruction island with terminal opcodes such as `4E 75`;
- high-bit Pascal-looking records on non-Mac platforms.

Starglider false-positive shape:

```asm
    dc.b $2D,$7C,$00,$07,$00,$00,$00,$00,$4E,$75
    dc.b $2D,$7C,$00,$07,$80,$00,$00,$00,$4E,$75
    dc.b "NuNu    ",$00    ; string
```

The nearby `4E 75` bytes are not proof by themselves, but combined with no
string access evidence and code-shaped context they should prevent auto-accept.

### 4. Grouping

Many failures are table failures, not individual-string failures.

The engine should identify:

- `string_table`: contiguous nul/`$FF` terminated entries;
- `pointer_string_table`: pointer table targets strings;
- `fixed_width_text_table`: constant-width rows;
- `control_string_stream`: text interleaved with display/control bytes;
- `length_prefixed_string_table`: proven length-byte records;
- `macos_symbol_string_table`: Mac high-bit symbol records.

Pandora example:

```asm
abs_0_0001A25C:
    dc.b $00,$00,$20,$20,$20,$20,$20,$4E,$4F,$54,$48,$49,$4E,$47,$00
    dc.b "Wrench",$00
    dc.b "Acid",$00
    dc.b "Electroboost",$00
```

This should be seen as a table. Once table membership is proven, short entries
like `Acid` should not depend on the generic minimum-length heuristic.

Magicland example:

```asm
abs_0_00064398:
    dc.w $000C,$02A0    ; lookup_table
    dc.b "MAGICLAND DIZZY!",$00
    dc.b $00,$00,$05,$15,$00
    dc.b "AMIGA AND ST VERSIONS CODED BY",$00
    dc.b $00,$00,$09,$1C,$E0
    dc.b "DEREK LEIGH-GILCHRIST.",$00
    dc.b $00,$00,$0D,$31,$E0
    dc.b "ALL ARTWORK BY",$00
    dc.b $00,$00,$0C,$39,$C0
    dc.b "LEIGH CHRISTIAN.",$00
    dc.b $00,$00,$00,$76,$20
    dc.b "COPYRIGHT 1991 CODEMASTERS SOFTWARE LTD.",$FF,$00
```

The current general fix recognizes the final copyright row by using nearby
structured-string context. 025 should replace that narrow rule with an explicit
`control_string_stream` or `display_text_record_stream` model.

## Platform-Specific Rules

### Amiga

Amiga should combine general data analysis with Amiga OS metadata:

- library vector input types such as `STRPTR`, `BSTR`, or known string pointer
  arguments;
- resident structures such as `RT_NAME` and `RT_IDSTRING`;
- game text patterns only when supported by table/access evidence or strong
  cluster context;
- hardware/display code should not affect string classification except where it
  proves text output flow.

Good current examples:

```asm
resident_name:
    dc.b "icon.library",$00
resident_idstring:
    dc.b "icon 34.2 (22 Jun 1988)",$0D,$0A,$00
```

Magicland file names:

```asm
    dc.b "SPRITES1.RAW",$00    ; string
    dc.b "PANEL.RAW",$00       ; string
    dc.b "HEIGHT.DATA",$00     ; string
```

These are likely file/resource strings. Future analysis should be able to bind
them to disk/file loading call sites or target child-resource relationships when
the evidence exists.

### Mac OS

Mac high-bit Pascal/symbol records are platform-specific and must remain gated
on the Mac backend.

Current accepted shape:

```asm
CODE_1_data_pascal_string_00002066:
    dc.b $87,"GETRSRC",$00,$00

CODE_1_data_pascal_string_0000209a:
    dc.b $8A,"GETFONTNBR",$00,$00,$00
```

Rules:

- high bit set on length byte;
- low 7 bits give payload length;
- printable payload;
- optional zero padding;
- Mac platform backend only;
- no code/relocation/structured-data conflict.

Rejected shape:

```text
same high-bit bytes on Amiga/Atari
  -> not macos_symbol_string
  -> do not infer generic Pascal string
```

Mac can still contain ordinary strings and command text:

```asm
    dc.b $13,"-d [&]name='string'"
```

Those should eventually be separated from symbol records using table/access
context, not only byte shape.

## Rendering Policy

Rendering should make source more readable without losing exactness.

Preferred output:

- quote printable bytes;
- keep terminators explicit: `$00`, `$FF`;
- split long CR/LF text into readable source rows;
- avoid redundant comments where the row is self-evidently string data;
- keep comments only when they add classification or field meaning.

Starglider CR/LF block should not be one huge unreadable row:

```asm
credits_text:
    dc.b $0D,$0A,$0A
    dc.b "Starglider was written by ",$0D,$0A
    dc.b "     Jez San and Rich Clucas of",$0D,$0A
    dc.b "Argonaut Software, London, England.",$0D,$0A
    dc.b $00
```

The source must remain byte-exact. This is presentation over the same structured
range, not semantic rewriting.

## Implementation Plan

### Step 1: Make String Evidence Explicit

Add a C-owned string evidence model near the current structured-data inference.

Minimum internal fields:

```c
typedef struct M68kStringEvidence {
  uint32_t section_index;
  uint32_t offset;
  uint32_t size;
  uint32_t terminator_kind;
  uint32_t encoding_kind;
  uint32_t positive_flags;
  uint32_t negative_flags;
  uint32_t table_id;
  uint32_t role;
} M68kStringEvidence;
```

Do not expose this shape prematurely if the existing structured data item can
carry the needed fields. The important part is that tests can prove which
evidence path accepted or rejected a range.

### Step 2: Split Candidate Discovery From Acceptance

Current scanning often discovers and accepts in one pass. Refactor toward:

```text
discover candidate
  -> collect positive evidence
  -> collect negative evidence
  -> decide accepted/deferred/rejected
  -> emit structured item only when accepted
```

This makes false positives testable.

### Step 3: Add Table/Stream Classifiers

Add table classifiers before isolated-string fallback:

```text
pointer table targets strings
  -> pointer_string_table

three or more nearby terminated entries
  -> string_table

constant-width printable rows
  -> fixed_width_text_table

text separated by short control byte packets
  -> control_string_stream
```

Table membership should allow shorter strings and internal control separators,
but only within the table bounds.

### Step 4: Add Negative Code Evidence

Use existing accepted-code and orphan-signal machinery.

Rules:

- accepted code overlap blocks string acceptance;
- likely orphan-code island inside candidate blocks shape-only string acceptance;
- terminal opcode bytes in context become negative evidence;
- positive access evidence may downgrade this to review instead of hard reject,
  but must not silently emit misleading string rows.

### Step 5: Improve Rendering

Renderer should consume structured string roles:

- ordinary strings render as quoted `dc.b`;
- long multiline strings split at CR/LF and source width;
- string tables render labels at entry boundaries;
- fixed-width tables render one row per record where possible;
- Mac symbol records keep length byte and padding explicit.

Avoid noisy comments:

```asm
dc.b "Wrench",$00
```

is usually clearer than:

```asm
dc.b "Wrench",$00    ; string
```

Field comments remain useful when a platform structure proves meaning:

```asm
dc.l resident_idstring    ; APTR RT_IDSTRING
```

## Test Strategy

025 needs two linked test layers.

### Canonical No-Fixture Tests

These should live in the C test suite and use small byte arrays.

Required coverage:

- nul-terminated ASCII accepted;
- `$FF`-terminated game text accepted;
- CR/LF multiline text accepted and rendered readably;
- accepted-code overlap rejected;
- orphan-code-like printable bytes rejected;
- adjacent string table accepted;
- short entry accepted only by table membership;
- pointer table to strings promotes entries;
- fixed-width text table not misclassified as length-prefixed;
- Magicland-style control-separated stream accepted as a stream;
- Mac high-bit symbol record accepted on Mac;
- same high-bit bytes rejected on Amiga/Atari;
- source-analysis cap behavior remains bounded.

### Fixture Double-Checks

Fixture tests should cite exact target rows and should be optional where they are
expensive. They are not the primary specification, but they prove the real
targets still exercise the canonical cases.

Use these examples:

- Starglider `NuD0        00000000` false positive;
- Starglider `NuNu    ` false positive;
- Starglider CR/LF credits block;
- Starglider rank table around `ACE PILOT` and `COMMANDER`;
- Pandora title/credits block beginning near `string_0002109E`;
- Pandora `0123456789ABCDEF`;
- Pandora item table around `Wrench`, `Acid`, `Electroboost`;
- MonAm text cluster around `pc =`, `Bus error`, `Text:`, `BSS :`,
  `Filename`;
- Magicland intro/copyright stream near `abs_0_00064398`;
- Mac MPW `GETRSRC`, `GETFONTNBR`, `STRINGCVT`;
- Mac MPW ordinary command strings such as `-d [&]name='string'`.

## Completion Criteria

025 is complete when:

- string acceptance records explicit evidence, not only byte shape;
- false-positive Starglider `Nu*` examples no longer render as accepted strings;
- Pandora, Starglider, MonAm, and Magicland text tables/streams render
  consistently;
- Mac high-bit symbol records remain platform-gated;
- representative no-fixture tests cover each rule;
- fixture-backed tests cite exact target examples;
- rendered-source round-trip remains unchanged or improves;
- no platform-specific string rule leaks into another platform.

## Non-Goals

- Do not build natural-language understanding.
- Do not guess game semantics from text content alone.
- Do not make Mac Pascal records a global string heuristic.
- Do not sacrifice byte-exact rendered-source round-trip for readability.
- Do not create issue files for this proposal.

## Implementation Notes and Later Observations

### 2026-05-28 pass

Implemented the first C-owned acceptance improvements in
`src/m68k_analysis_render_lookup.c`.

- Existing string-table context can now promote a later plain entry without
  spaces. This fixes the Pandora `0123456789ABCDEF` table row without making
  numeric-looking text globally valid.
- Shape-only strings adjacent to nearby terminal code context are rejected
  unless there is stronger boundary evidence. This removes the Starglider
  `NuNu    ` and `NuD0        00000000` false-positive rows while preserving
  Magicland display text streams and Pandora item-table strings.
- CR/LF-led multiline text now records an explicit `multiline_text` source
  pattern before it renders as a string. The rule requires bounded CR/LF text,
  a terminator, clear interior bytes, no accepted-code overlap, and for CODE
  sections a real label/anchor. This makes the Starglider credits and prompt
  blocks readable without accepting arbitrary printable bytes.
- The new behavior is covered by no-fixture C tests for table-context
  promotion, multiline text inference/rendering, and unlabeled
  orphan-code-shaped text rejection.

Target source was re-exported through `amiga-source-export --output` for all 36
tracked `.s` files. Mac artifact targets now participate in source export via
their artifact renderer; source assembly remains intentionally classified as
`unsupported_platform_source_assembly` by the rendered-source round-trip report.
Generated source-export timestamps were removed from headers so routine exports
do not churn committed target source.

Verification:

```text
cmd /c src\precommit.bat m68k_ir
uv run python -m pytest tests\test_source_export.py -q
amiga-source-export --output for all tracked target .s files
platform-rendered-source-roundtrip
```

Round-trip result after this pass:

```text
34/36 full-file exact
1/36 content-exact-only: amiga_disk_damocles-mercenary-ii-1990-novagen-cr-h__amiga_hunk_menu_252a2566
1/36 unsupported: macos_hfs_mpw_gm__macos_file_mpw_tools_asm
0 failures
```

Remaining observations for later 025 passes:

- Some target diffs include unrelated current-analysis improvements such as
  branch target symbolization and generated source-export headers. Those are
  useful but are not string-evidence semantics.
- The repeated `; string` comment remains noisy. It should be removed only
  after row metadata and role-specific comments still make string/data meaning
  inspectable.
- Magicland-style control/display streams are improved by table context but are
  not yet first-class `control_string_stream` records.
- The code-context negative evidence is intentionally narrow. A fuller orphan
  code/text arbitration pass should use explicit C analysis records rather than
  widening byte-neighborhood rules.

### 2026-05-28 evidence metadata pass

The string inference path now records explicit source-pattern evidence for the
major accepted auto-string classes that previously remained `unknown`:

- isolated nul/`$FF` terminated text records use `terminated_text`;
- label/anchor-bounded text records use `bounded_text`;
- adjacent short string clusters and table-context promotions use
  `string_table_sequence`;
- Magicland-style separator/control-byte record continuations use
  `control_string_stream` and carry the `STRING_CONTROL_STREAM` role flag;
- Mac high-bit symbol records and CR/LF multiline records keep their existing
  `macos_symbol_record` and `multiline_text` evidence.

This is deliberately metadata-only for rendered source: all 36 tracked `.s`
files re-exported successfully and no committed target source text changed. The
benefit is in `source_analysis.policy.structured_data_items[]` and JSON/listing
metadata, where reviewers and downstream tools can now distinguish shape-only
terminated text from sequence/table/stream evidence.

Verification:

```text
cmd /c src\precommit.bat m68k_ir
amiga-source-export --output for all tracked target .s files
platform-rendered-source-roundtrip
git diff --check -- . ':(exclude)TODO.md'
```

Round-trip result after this pass remained:

```text
34/36 full-file exact
1/36 content-exact-only: amiga_disk_damocles-mercenary-ii-1990-novagen-cr-h__amiga_hunk_menu_252a2566
1/36 unsupported: macos_hfs_mpw_gm__macos_file_mpw_tools_asm
0 failures
```
