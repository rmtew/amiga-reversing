# Proposal 020: Platform Executable Import Pipeline

Status: active. Proposal 018 established the executable-format KB authority,
and Proposal 019 made current parser summaries emit KB fact refs. Proposal 020
turns those foundations into the clean forward implementation: one shared,
C-owned executable import pipeline that parser summaries, analysis state,
listing/rendering, and verification all consume.

## Purpose

The project now has structured executable-format knowledge, generated runtime
fact tables, and parser-owned fact refs. That is necessary but not sufficient.
The implementation still risks remaining a set of platform-specific summary
and rendering paths unless executable structure flows through one durable model.

The intended implementation shape is:

```text
platform parser
  -> shared executable summary model
  -> analysis import facts
  -> listing/rendering ranges
  -> verifier and round-trip gates
```

This proposal is implementation work, not another read-only blocker map. It
must put code in place, migrate existing platform slices onto it, and delete
superseded paths once replacement behavior is proven.

## Relationship To 018 And 019

018 remains the authority for executable-format facts, fact states, source
policy, parser-use authority, and deferred/unsupported boundaries.

019 remains the proof that current parser summaries can emit and validate
`kb_record_id`, `fact_id`, `fact_status`, and `parser_use`.

020 consumes both:

- accepted/parser-asserted facts may authorize parser output;
- candidate/deferred/unsupported facts must stay visible and non-accepted;
- no parser, renderer, or importer may silently decode metadata as code;
- missing evidence blocks mutation/accepted behavior, not visibility.

## Target Outcome

A reversing user or agent should be able to load supported executable-bearing
formats through one implementation path:

```text
Amiga HUNK:
  HUNK_HEADER -> CODE/DATA/BSS sections -> shared executable ranges

Atari ST PRG:
  PRG header -> TEXT/DATA/BSS regions -> shared executable ranges

Classic Mac OS:
  HFS/resource fork -> CODE resources -> shared executable ranges
```

The shared model must represent:

- container identity and provenance;
- loadable code/data/BSS ranges;
- metadata-only ranges;
- candidate code ranges;
- entry candidates;
- relocation/fixup state;
- unsupported/deferred facts;
- original byte spans and hashes needed for exactness checks;
- KB fact refs that justify or limit parser behavior.

## Non-Negotiable Implementation Direction

The durable model is C-owned. Python may orchestrate reports, tests, fixtures,
and workflow commands, but it must not be the only owner of executable range
classification, parser-to-analysis import, or listing/rendering decisions.

Do not add compatibility shims or dual behavior. When a platform slice moves to
the shared path and tests prove equivalence or intended improvement, remove the
superseded path.

Do not reopen 018 to promote facts as a convenience. If a fact remains
candidate/deferred/unsupported in the KB, 020 must carry that state through the
pipeline visibly.

## Tutorial Shape

The result should be easy to understand from a small summary:

```json
{
  "platform": "amiga-hunk",
  "file_kind": "executable",
  "kb_record_id": "amiga.hunk.load_file.basic_backfill",
  "ranges": [
    {
      "role": "code",
      "status": "accepted",
      "start": 0,
      "size": 4,
      "fact_id": "amiga.hunk.code_data_bss.sections.accepted"
    },
    {
      "role": "bss",
      "status": "accepted",
      "start": 8,
      "size": 8,
      "stored_size": 0,
      "fact_id": "amiga.hunk.bss.size_only.accepted"
    }
  ],
  "deferred": [
    {
      "kind": "runtime_entry",
      "fact_id": "amiga.hunk.runtime_entry.deferred"
    }
  ]
}
```

The same structure should drive analysis import, listing windows, and verifier
proofs. Platform details remain platform-specific facts, but the consumer path
is shared.

## Implementation Slices

### 020-001: Current Import Pipeline Inventory

Find the current executable parser, summary, analysis-import, listing, target
artifact, verifier, and web/API paths for Amiga HUNK, Atari PRG, and Mac CODE.
This is only enough research to avoid missing a replacement boundary. It must
end with a concrete replacement map for 020, not a broad blocker report.

### 020-002: Shared Executable Summary Model

Add the first shared C-owned executable summary/range model and expose it
through parser inspect JSON. The first slice may be narrow, but it must be real:
at least one current parser fixture must emit shared ranges and tests must
validate fact refs, range roles, byte spans, and state.

### 020-003: Amiga HUNK Shared Import Slice

Move the current Amiga HUNK parser summary into the shared executable model.
CODE/DATA/BSS and size-only BSS must appear as shared ranges. Runtime entry and
relocation breadth must remain deferred/candidate where 018 says so.

### 020-004: Atari PRG Shared Import Slice

Move the current Atari ST PRG parser summary into the shared executable model.
TEXT/DATA/BSS and loaded TEXT+DATA target space must appear as shared ranges.
Basepage/runtime entry and relocation/symbol details must remain
candidate/deferred where 018 says so.

### 020-005: Mac CODE Shared Import Slice

Move the current Mac CODE classified ranges into the shared executable model.
CODE 0 must remain metadata-only. Nonzero CODE ranges must keep accepted
segment metadata, candidate code windows, and deferred relocation/fixup state.
No Mac byte-entry rule may be promoted.

### 020-006: Shared Listing/Rendering Contract

Make listing/rendering consume shared executable ranges rather than platform
side decisions. Metadata-only ranges must not decode as instructions.
Candidate/deferred state must be visible in source/artifact/web output.

### 020-007: Analysis-State Executable Import

Feed shared executable ranges into analysis state through one import path.
Analysis should receive durable range roles, provenance, fact refs, and
candidate/deferred markers instead of re-deriving them from ad hoc parser JSON.

### 020-008: Remove Superseded Executable Paths

Delete old per-platform/ad hoc executable summary, range classification, and
rendering paths that are replaced by 020. Keep no compatibility branch for the
old behavior.

### 020-009: Cross-Platform Closeout Proof

Rerun the full cross-platform proof. Amiga, Atari, and Mac must all flow through
the shared model; parser fact coverage must pass; target artifacts must stay
exact where expected; and candidate/deferred/unsupported states must remain
non-accepted.

## Acceptance Criteria

- A shared C-owned executable summary/range model exists.
- Amiga HUNK, Atari PRG, and Mac CODE current parser paths emit or consume that
  model.
- Analysis import consumes the shared model.
- Listing/rendering consumes classified ranges from the shared model.
- Verifier/coverage gates prove parser facts, byte spans, and fact states.
- Candidate/deferred/unsupported facts remain non-accepted.
- Superseded ad hoc paths are removed once replacement slices pass.
- No 012/018 closeout claim is weakened or reopened without a specific KB
  authority change.

## Verification Plan

Minimum proof for each implementation issue:

```powershell
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-macos-c-backend --current-amiga-hunk --current-atari-prg
uv run python -m pytest tests\test_platform_executable_formats.py -q
git diff --check
```

Implementation slices must also run the focused parser/listing/target tests for
the platform they touch. Closeout must run the repository precommit gate.

## Issue Ordering

- Start with 020-001.
- 020-002 follows 020-001.
- 020-003 and 020-004 may run in parallel after 020-002.
- 020-005 should start after 020-002 and after reviewing lessons from either
  020-003 or 020-004.
- 020-006 follows at least one completed platform migration and closes after
  all three platform migrations are represented.
- 020-007 follows 020-003 through 020-005.
- 020-008 follows 020-006 and 020-007.
- 020-009 closes the proposal after all prior issues are complete.

## Non-Goals

- Promoting Mac byte-entry or relocation/fixup facts.
- Full Amiga HUNK overlay/loader migration.
- Full Atari PRG relocation/symbol parser migration.
- Mac source-to-CODE recovery.
- Non-CODE Mac resource payload decoding.
- UI redesign beyond consuming the shared model correctly.
