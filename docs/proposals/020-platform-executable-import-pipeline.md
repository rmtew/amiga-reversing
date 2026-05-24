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

Completed inventory:

| Platform | Current parser/summary path | Current analysis/listing path | Current artifact/API path | 020 replacement map |
| --- | --- | --- | --- | --- |
| Amiga HUNK | `platform_file_inspect_path_json_alloc` parses through `platform_file_inspect_path_json` and `inspect_object_json`; 019 refs are emitted in `src/platform_file_json.c` for executable `amiga-hunk` summaries. | `source_binary.json` kind `hunk_file` resolves to `HunkFileBinarySource`; `c_backend._source_file_for_c_backend` selects backend from path; `CListingArtifact.create` calls `platform_file_facts_v2_listing_artifact_path_create`; C builds `M68kObject`, `M68kSourceAnalysisIR`, and `M68kRenderPlan`. | Server/project listing routes use `build_project_listing_artifact_profile`; upload validation uses `validate_amiga_hunk_executable_with_c_backend`; disk imports create child targets with `source_binary.json`; round-trip/verifier paths use facts_v2 direct rebuild and reproduction compare. | 020-002 defines shared ranges; 020-003 moves HUNK CODE/DATA/BSS/BSS-size refs from inspect-only JSON into that model; 020-006/020-007 make listing and analysis consume it; 020-008 may delete direct section-kind-to-listing assumptions only after HUNK listing/artifact/rebuild proof passes. |
| Atari ST PRG | Same C inspect surface as Amiga, selected by backend `atari-st`; 019 refs are emitted in `src/platform_file_json.c`; disk/file corpus discovery uses `build_platform_file_manifest.py` to identify `.prg` entries from Atari disk manifests. | `source_binary.json` disk entries resolve through `DiskEntryBinarySource`; `_source_file_for_c_backend` extracts the entry to a temp file and chooses backend from disk path; the same facts_v2 listing artifact functions produce analysis, source text, windows, navigation, and row lookups; include dir switches to Atari Devpac includes. | Disk browser marks `atari_st_executable`; profile-set import creates Atari resource targets; reproduction code supports backend `atari-st` with Atari include dir and known relocation-target refusal handling. | 020-004 must preserve TEXT/DATA/BSS, loaded TEXT+DATA target space, and candidate/deferred relocation/basepage/symbol limits in shared ranges; 020-008 may delete Atari-specific manifest/listing assumptions only after PRG corpus, listing, and reproduction proof covers them. |
| Classic Mac OS CODE | C path is separate: `platform_file_macos_hfs_code_summary_json_alloc` parses HFS catalog, forks, resource fork, CODE metadata, `code_segment_map`, and `selected_code`; `platform_file_macos_hfs_code_resource_bytes_alloc` extracts selected CODE bytes. Python `macos_asm_container.py` still performs additional HFS/resource inventory wrapping. | Mac listing is an adapter, not native platform import: `macos_listing_source.build_macos_code_listing_source` calls the C summary/extractor, writes selected CODE bytes to a temp `RawBinarySource`, and wraps the generic C listing artifact as backend `macos-code`; rows are post-processed to attach Mac provenance and hide Amiga section header rows. | `build_macos_project_payload`, `macos_target_artifact`, `macos_web_view`, server project payload/listing branches, and web tests consume Mac-specific payload fields: `resource_fork`, `code_segment_map`, `selected_code_segment`, candidate previews, non-CODE placeholders, and unsupported/deferred facts. | 020-005 must move C CODE layout/classification into the shared model before Python payloads consume it; 020-006 must replace the raw-binary wrapper/post-filter with shared range rendering; 020-007 must import Mac provenance/fact refs into analysis state; 020-008 may delete Python-only Mac CODE projection helpers only after web/API/artifact parity proves replacement. |

Current proof commands and tests:

- Cross-platform KB/parser fact gates:
  `uv run python -m amiga_reversing.tools.platform_executable_formats validate`;
  `uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-macos-c-backend --current-amiga-hunk --current-atari-prg`;
  `uv run python -m pytest tests\test_platform_executable_formats.py -q`.
- Amiga/Atari parser, listing, analysis, artifact, and reproduction coverage:
  `uv run python -m pytest tests\test_c_backend.py -q`;
  `uv run python -m pytest tests\test_benchmark_target.py tests\test_vasm_roundtrip.py -q`;
  `cmd /c src\precommit.bat` for native C parser/listing, integration, manifest, and explicit checks.
- Atari-specific evidence:
  `uv run python -m pytest tests\test_atari_platform_kb.py -q`;
  `src\scripts\build_platform_file_manifest.py` and `src\scripts\target_usage_manifest.py` cover Atari PRG corpus discovery.
- Mac CODE parser/payload/artifact/web evidence:
  `uv run python -m pytest tests\test_macos_c_backend.py tests\test_macos_project_payload.py tests\test_macos_asm_container.py tests\test_macos_web_view.py tests\test_web_app_source.py -q`;
  `uv run python -m pytest tests\test_web_e2e_cdp.py -q` for web/API rendering when browser/CDP is enabled.
- Required 020-001 hygiene: `git diff --check`.

Superseded path candidates, deletion blocked until replacement proof:

- `src/platform_file_json.c` inspect-only Amiga/Atari fact ref emission is a current compatibility surface; delete or reduce it only after shared summary JSON emits equivalent refs and 019 coverage remains green.
- Python coverage loaders `_load_current_amiga_hunk_output` and `_load_current_atari_prg_output` should become shared-model consumers after 020-003/020-004; they must not regain section-derived fact synthesis.
- `amiga_reversing/disasm/macos_listing_source.py` temporary `RawBinarySource` bridge and row post-filter are superseded by shared CODE ranges, but remain until Mac listing windows/source text prove parity.
- `amiga_reversing/disasm/macos_project_payload.py`, `macos_target_artifact.py`, and `macos_web_view.py` consume Mac-specific payload shapes; each can move field-by-field to shared ranges only after tests prove candidate/deferred/non-CODE visibility.
- Disk/file manifest import heuristics in `src/scripts/build_platform_file_manifest.py`, profile-set target import, and disk browser executable labels remain discovery surfaces; delete only after shared model appears in generated target manifests and disk browser payloads.

Implementation constraints found during 020-001:

- Amiga and Atari already share the C facts_v2 analysis/listing artifact pipeline; the missing piece is a shared executable range model upstream of analysis/rendering, not a new listing artifact architecture.
- Mac CODE currently does not enter C as a native `macos-code` backend. It is summarized by C, extracted to raw bytes, then rendered through `amiga-raw` plus Python provenance wrapping. This is the highest-risk replacement boundary for 020-005/020-006.
- `BinarySourceKind` has no Mac-specific source descriptor; Mac projects are recognized by `.project.json` origin and server/project branches. 020 must decide whether shared import introduces a Mac source descriptor or keeps project-origin import with C-owned range data.
- Existing web/API contracts depend on Mac-specific fields (`selected_code_segment`, `code_segment_map`, non-CODE details). Shared ranges must be additive or migrated with explicit web/API tests before old fields disappear.
- Candidate/deferred/unsupported KB states are already user-visible in Mac payloads and parser coverage; shared-model migration must preserve those states rather than normalizing everything to accepted code/data sections.

Search evidence used for this inventory:

- `rg "platform_file_inspect_path_json_alloc|_load_current|platform_executable_formats" amiga_reversing src tests`
- `rg "render_plan|listing_window|source_file|artifact|round|verify|coverage|disasm" amiga_reversing src tests`
- `rg "source_binary|manifest|imported_targets|amiga_hunk|atari|platform_file_manifest" src\scripts amiga_reversing`
- Focused reads of `amiga_reversing/disasm/binary_source.py`, `c_backend.py`, `macos_listing_source.py`, `macos_project_payload.py`, `macos_target_artifact.py`, `macos_asm_container.py`, `src/platform_file_lib.c`, and `src/platform_file_json.c`.

Next implementation issue: start `020-002-shared-executable-summary-model.md`.
It should add the C-owned model behind at least one parser fixture, then expose
shared ranges in inspect JSON without changing analysis/listing behavior yet.

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
