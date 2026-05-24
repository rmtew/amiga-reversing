# Proposal 019: Platform Executable KB Parser Consumption

Status: active. Proposal 018 is complete as the executable-format KB authority;
Proposal 019 owns the implementation work that makes platform parsers consume
and emit that authority consistently across Mac OS, Amiga, and Atari ST.

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
  "unreported_platforms": [],
  "unreported_records": []
}
```

If a platform parser cannot produce a real current-output fixture yet, the
issue implementing that platform must add the smallest synthetic or committed
fixture-backed parser summary needed to prove the same path. It should not
complete by merely documenting that the platform remains unreported.

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
