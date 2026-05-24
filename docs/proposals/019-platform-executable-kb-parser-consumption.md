# Proposal 019: Platform Executable KB Parser Consumption

Status: active. Proposal 018 is complete as the executable-format KB authority;
Proposal 019 has current-output coverage hooks for Mac OS, Amiga HUNK, and
Atari ST PRG, but review found the Amiga/Atari KB refs are still synthesized by
the coverage wrapper rather than emitted by the parser-owned summary surface.
The remaining work is to make parser output itself carry the executable-format
KB refs.

## Purpose

Proposal 018 created the executable-format KB and proved the Mac C backend can
emit fact refs that coverage checks against the KB. That is not the end state.
The correct end state is that every platform parser/import summary that knows
about executable structure emits stable KB fact refs for the facts it consumes
or reports:

```text
binary/container parser
  -> parser summary with kb_record_id/fact_id/fact_status/parser_use
  -> platform executable coverage
  -> accepted/candidate/deferred/unsupported/invalid report
```

This proposal moves beyond read-only blocker mapping. The work is to wire the
systems together so parser behavior is checked by the executable-format KB by
default. When a parser already uses a platform rule, it should say which KB fact
authorizes or limits that rule. When a parser cannot yet emit facts, that is an
implementation gap to close, not a permanent excuse to call the record
unreported.

## Relationship To 018

018 remains the authority for fact meaning, source policy, and fact state.
019 must not weaken or bypass it.

Allowed:

- consume accepted/parser-asserted KB facts in parser summaries;
- emit candidate/deferred/unsupported refs where parser output is intentionally
  limited;
- add current-output coverage hooks;
- update parser summary tests to enforce fact refs.

Not allowed:

- promote candidate/deferred/unsupported facts without 018-style evidence;
- encode executable-format rules directly in parser output without a KB fact id;
- reopen 018 just because a parser has not consumed an existing fact yet.

## Target Outcome

The coverage command should have current-output paths for the platform parsers:

```powershell
uv run python -m amiga_reversing.tools.platform_executable_formats coverage `
  --current-macos-c-backend `
  --current-amiga-hunk `
  --current-atari-prg
```

Expected result:

```json
{
  "summary": {
    "parser_outputs": 3,
    "invalid": 0
  },
  "unreported_platforms": []
}
```

The combined current-output gate now leaves no platform unreported. The only
remaining unreported record is the old Mac report-only thin proof; the current
Mac parser hook reports the accepted MPW application record. Amiga and Atari
current hooks currently prove parser execution plus wrapper validation, but
they must be tightened so the raw parser/import summaries carry the fact refs
before coverage sees them.

## Consumption Contract

Parser summary objects that emit executable-format facts use the same shape:

```json
{
  "kb_record_id": "amiga.hunk.load_file.basic_backfill",
  "container": {
    "fact_id": "amiga.hunk.header.accepted",
    "fact_status": "parser_asserted",
    "parser_use": "accepted_parser_output"
  },
  "regions": [
    {
      "kind": "code",
      "fact_id": "amiga.hunk.section.code.accepted",
      "fact_status": "parser_asserted",
      "parser_use": "accepted_parser_output"
    }
  ],
  "relocations": {
    "fact_id": "amiga.hunk.relocation_breadth.deferred",
    "fact_status": "deferred",
    "parser_use": "deferred_only"
  }
}
```

The exact field names may follow each parser's existing summary shape. The
important contract is that every emitted fact ref validates against
`knowledge/platform_executable_formats.json` and that accepted parser output is
impossible without accepted/parser-asserted KB authority.

## Implementation Slices

### 019-001: Amiga HUNK Current KB Fact Output

Teach the Amiga HUNK parser/import summary to emit refs for the accepted
parser-asserted HUNK record from 018:

```text
amiga.hunk.load_file.basic_backfill
HUNK_HEADER identity
CODE/DATA/BSS section roles
object/library container identity where applicable
size-only BSS
candidate/deferred/unsupported limits for unresolved breadth
```

The worker should prefer the narrowest existing parser summary surface that can
carry these refs into coverage. Do not rewrite HUNK import broadly.

Completion requires real code output: `coverage --current-amiga-hunk` must run
the Amiga HUNK parser/import path and emit meaningful fact refs. A zero-fact
hook or handcrafted dictionary is not acceptable.

Completed state: `coverage --current-amiga-hunk` writes a synthetic HUNK load
file with CODE, DATA, and BSS hunks, runs it through the real
`platform_file_inspect_path_json_alloc` / `amiga-hunk` parser path, then emits
refs for `amiga.hunk.load_file.basic_backfill`. The output includes accepted
parser-asserted refs for HUNK_HEADER, container basics, CODE/DATA/BSS section
roles, BSS size-only state, and a deferred runtime-entry limit.

### 019-002: Atari PRG Current KB Fact Output

Teach the Atari ST PRG parser/import summary to emit refs for the accepted
parser-asserted PRG record from 018:

```text
atari_st.prg.gemdos_basic_backfill
0x601A magic
PRG header sequence
TEXT/DATA/BSS region shape
TEXT+DATA loaded-image relocation target space
candidate/deferred/unsupported limits for runtime/basepage/symbol details
```

Again, use the smallest existing parser summary surface that can carry real
parser output into coverage.

Completion requires real code output: `coverage --current-atari-prg` must run
the Atari PRG parser/import path and emit meaningful fact refs. A zero-fact hook
or handcrafted dictionary is not acceptable.

Completed state: `coverage --current-atari-prg` writes a synthetic GEMDOS PRG
with 0x601A header, TEXT, DATA, BSS size, and relocation-stream terminator,
runs it through the real `platform_file_inspect_path_json_alloc` / `atari-st`
parser path, then emits refs for `atari_st.prg.gemdos_basic_backfill`. The
output includes accepted parser-asserted refs for magic/header, container
sequence, TEXT/DATA/BSS region shape, loaded TEXT+DATA relocation target space,
plus candidate/deferred limits for BSS header-only and relocation terminator
variants.

### 019-003: Cross-Platform Current Coverage Gate

Make the cross-platform coverage gate prove current parser consumption:

```powershell
uv run python -m amiga_reversing.tools.platform_executable_formats coverage `
  --current-macos-c-backend `
  --current-amiga-hunk `
  --current-atari-prg
```

The closeout gate should fail on invalid accepted claims and should leave no
unreported platform records for the records whose parsers now emit fact refs.

Completed state: the combined command
`coverage --current-macos-c-backend --current-amiga-hunk --current-atari-prg`
reports three current parser outputs, `invalid: 0`, no unreported platforms,
and validated Amiga/Atari record refs. Candidate/deferred Mac, Amiga, and Atari
facts remain candidate/deferred in coverage output.

### 019-004: Parser-Owned Amiga/Atari KB Fact Refs

Move the Amiga HUNK and Atari ST PRG fact refs out of the coverage wrapper and
into the parser-owned summary surface consumed by coverage. The current
implementation runs the C parser paths, then `platform_executable_formats.py`
adds `fact_refs` based on the parsed section summary. That is useful proof of
parser reachability, but it is not the intended consumption contract.

The corrected shape is:

```text
platform_file_inspect_path_json_alloc
  -> parser/import summary containing kb_record_id/fact_id/fact_status/parser_use
  -> coverage labels source and validates refs without inventing them
```

Completion requires tests that inspect the raw Amiga and Atari parser summaries
before coverage wrapping and fail if those summaries contain no KB refs. The
coverage command may add source labels and aggregate results, but it must not
construct Amiga/Atari executable-format fact refs from section kinds itself.

## Review Finding

- Review of commit `43555c72` found that `coverage --current-amiga-hunk` and
  `coverage --current-atari-prg` run real C parser inspection, but
  `_load_current_amiga_hunk_output()` and `_load_current_atari_prg_output()`
  synthesize `fact_refs` after parsing. The C parser summaries themselves do
  not yet emit `kb_record_id`, `fact_id`, `fact_status`, or `parser_use`.
- This keeps Proposal 019 active until 019-004 makes the raw parser-owned
  summaries self-describing and coverage consumes those refs unchanged.

## Closeout Record

- 019-001 implemented the real Amiga HUNK current-output coverage hook.
- 019-002 implemented the real Atari ST PRG current-output coverage hook.
- 019-003 made the combined Mac/Amiga/Atari current-output coverage command a
  closeout gate.
- Completed issue files `019-001`, `019-002`, and `019-003` were deleted only
  after this proposal recorded their durable conclusions.
- 019-004 is active after review found that Amiga/Atari refs are wrapper-owned,
  not parser-owned.

## Acceptance Criteria

- Current-output coverage can include Mac, Amiga, and Atari parser outputs.
- Amiga HUNK parser/import output emits KB fact refs for its accepted 018 slice.
- Atari PRG parser/import output emits KB fact refs for its accepted 018 slice.
- The Amiga and Atari current-output hooks each emit at least one accepted or
  parser-asserted KB-backed fact ref and at least one non-accepted limit where
  the parser currently has candidate/deferred/unsupported breadth.
- Candidate/deferred/unsupported executable facts remain non-accepted.
- `coverage` reports `invalid: 0` for current outputs and fails closed for
  invalid accepted claims.
- Tests cover the parser output path, not only handcrafted coverage payloads.
- Tests assert raw Amiga and Atari parser/import summaries contain KB refs
  before coverage wrapping.
- Tests fail if either Amiga or Atari current-output coverage becomes an empty
  placeholder.
- Proposal 018 remains closed; any new evidence work becomes a separate future
  proposal or an explicit 018-style KB update only if real evidence appears.

## Non-Goals

- Full Amiga HUNK relocation/overlay parser migration.
- Full Atari runtime/basepage/symbol semantics.
- Mac byte-entry, relocation/fixup, or source-to-CODE implementation.
- Broad target artifact regeneration.
- Cosmetic parser summary rewrites.

## Verification Plan

Minimum verification for each issue:

```powershell
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.platform_executable_formats coverage ...
uv run python -m pytest tests\test_platform_executable_formats.py -q
git diff --check
```

Parser-specific issues must also run the relevant Amiga or Atari parser tests.
