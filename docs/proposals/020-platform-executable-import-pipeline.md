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
- 017-074 proved a container-resolution pattern for disk-level workflow reports: use source-backed target/project metadata to select a concrete disassemblable payload subtarget, report other manifest executable candidates for context, and fail closed when selection is ambiguous or no source-backed subtarget exists.

Search evidence used for this inventory:

- `rg "platform_file_inspect_path_json_alloc|_load_current|platform_executable_formats" amiga_reversing src tests`
- `rg "render_plan|listing_window|source_file|artifact|round|verify|coverage|disasm" amiga_reversing src tests`
- `rg "source_binary|manifest|imported_targets|amiga_hunk|atari|platform_file_manifest" src\scripts amiga_reversing`
- Focused reads of `amiga_reversing/disasm/binary_source.py`, `c_backend.py`, `macos_listing_source.py`, `macos_project_payload.py`, `macos_target_artifact.py`, `macos_asm_container.py`, `src/platform_file_lib.c`, and `src/platform_file_json.c`.

Next implementation issue: start `020-002-shared-executable-summary-model.md`.
It should add the C-owned model behind at least one parser fixture, then expose
shared ranges in inspect JSON without changing analysis/listing behavior yet.

### 020-002: Shared Executable Summary Model

Completed first slice:

- Added `src/platform_executable_summary.h` as the shared C-owned executable
  summary/range data shape.
- Wired the executable Amiga HUNK inspect path to build that model from the
  parsed `M68kObject` and expose `executable_model`,
  `executable_ranges`, and `executable_deferred` in raw
  `platform_file_inspect_path_json_alloc` JSON.
- Proved the current synthetic Amiga HUNK fixture emits shared CODE, DATA, and
  size-only BSS ranges with load offsets, nullable stored offsets, sizes,
  stored sizes, fact ids, fact states, and parser-use authority.
- Kept the existing `sections` and `fact_refs` surfaces intact so 019 coverage
  continues to validate the parser-owned refs.
- Represented runtime-entry uncertainty as deferred through
  `amiga.hunk.runtime_entry.deferred`; no candidate/deferred/unsupported fact
  is promoted to accepted output.

Model constraints for following slices:

- This is an additive parser-summary exposure only. It does not migrate
  analysis import, listing/rendering, Atari PRG, or Mac CODE.
- The first Amiga slice separates loaded-image offsets from original stored
  bytes: BSS has a `load_offset` and `stored_size: 0`, but no `stored_offset`.
- 020-003 should move the Amiga HUNK import path deeper onto this model before
  old section-kind assumptions are removed. 020-004 can reuse the same C shape
  for Atari PRG after the Amiga migration constraints are reviewed.

### 020-003: Amiga HUNK Shared Import Slice

Completed Amiga current-output migration:

- `_load_current_amiga_hunk_output()` now requires
  `executable_model == "platform_executable_summary_v1"` and validates CODE,
  DATA, and BSS `executable_ranges` from raw inspect JSON.
- BSS is required to remain size-only in the shared model:
  `load_offset` is present, `stored_offset` is null, and `stored_size` is 0.
- Runtime-entry uncertainty is required in `executable_deferred` with
  `amiga.hunk.runtime_entry.deferred`, `fact_status: deferred`, and
  `parser_use: deferred_only`.
- Current coverage proves Amiga refs from `$.executable_ranges[0..2]` and
  `$.executable_deferred[0]`; the older top-level `sections` and `fact_refs`
  remain only as compatibility surfaces and deletion candidates for 020-008.
- Regression coverage fails if old Amiga `sections`/`fact_refs` remain but the
  shared executable model is omitted.

### 020-004: Atari PRG Shared Import Slice

Completed Atari current-output migration:

- The executable Atari ST PRG inspect path now builds
  `platform_executable_summary_v1` and emits shared `executable_ranges` plus
  `executable_deferred` from C.
- TEXT is represented as role `code`, DATA as role `data`, and BSS as role
  `bss`, with loaded-image offsets separated from nullable stored offsets.
- CODE/DATA ranges carry
  `atari_st.prg.text_data_loaded_image.accepted` as parser-asserted accepted
  output. BSS remains candidate-only through
  `atari_st.prg.bss.header_only.candidate`, with `stored_offset: null` and
  `stored_size: 0`.
- Relocation breadth remains deferred through
  `atari_st.prg.relocation_terminator_variants.deferred` in
  `executable_deferred`.
- `_load_current_atari_prg_output()` now requires the shared model; regression
  coverage fails if old Atari `sections`/`fact_refs` remain but shared ranges
  are omitted.
- Current coverage proves Atari refs from `$.executable_ranges[0..2]` and
  `$.executable_deferred[0]`; the older top-level `sections` and `fact_refs`
  remain only as compatibility surfaces and deletion candidates for 020-008.

### 020-005: Mac CODE Shared Import Slice

Completed Mac current-output migration:

- `platform_file_macos_hfs_code_summary_json_alloc` now emits
  `executable_model: platform_executable_summary_v1`, `executable_ranges`, and
  `executable_deferred` from the C Mac CODE parser summary.
- Mac shared ranges use the same loaded-image split as Amiga/Atari:
  `load_offset` names the offset within the decoded CODE resource payload, while
  `stored_offset` names bytes in the resource-fork payload space. The Mac
  extension `stored_offset_space: resource_fork_payload` is emitted so later
  exactness/import gates do not mistake these values for whole-file source
  spans.
- CODE 0 is represented only as role `metadata` through
  `macos.code_resource.0.jump_table_metadata`; it is not promoted to decodable
  instruction bytes.
- Nonzero CODE segment/header metadata remains accepted through
  `macos.code_resource.nonzero.segment_header`. The `movea.l (a7)+,a0`
  byte-entry window remains role `candidate_code` with
  `macos.code_resource.movea_stack_a0.boundary.candidate`,
  `fact_status: candidate`, and `parser_use: candidate_only`.
- Segment-loader relocation/fixup breadth remains in `executable_deferred`
  through `macos.segment_loader.relocation_fixups.deferred`; no relocation/fixup
  fact was promoted.
- `_load_current_macos_c_backend_output()` now requires the shared model and
  fails closed if the old Mac-specific summary fields remain without shared
  executable ranges.
- Existing Mac project, artifact, web, `selected_code`, `code_segment_map`,
  orphan/non-CODE, and unsupported surfaces remain compatibility outputs and
  deletion candidates for 020-008 after 020-006/020-007 prove their shared
  replacements.

### 020-006: Shared Listing/Rendering Contract

Completed shared listing/rendering contract:

- Amiga HUNK and Atari PRG C listing artifact construction now validates the
  executable object against the shared executable range role/fact contract
  before render-plan creation. CODE/TEXT ranges may render as instructions;
  DATA and BSS ranges are refused as instruction roles, and BSS must remain
  stored-size-only.
- The Amiga/Atari listing contract carries the same parser fact authority as
  the shared summaries: Amiga CODE/DATA use
  `amiga.hunk.code_data_bss.sections.accepted`, Amiga BSS uses
  `amiga.hunk.bss.size_only.accepted`, Atari TEXT/DATA use
  `atari_st.prg.text_data_loaded_image.accepted`, and Atari BSS remains
  candidate-only through `atari_st.prg.bss.header_only.candidate`.
- Mac listing provenance now selects the active CODE range from
  `summary.executable_ranges` and fails closed when the shared model is absent.
  It no longer treats `selected_code.code.layout_ranges` as the listing
  authority. The temporary raw-binary bridge remains only as a byte transport
  for the selected shared CODE range until 020-008 removes the superseded
  wrapper path.
- CODE 0 and non-code Mac metadata remain non-instruction surfaces; selected
  CODE listing rows use the shared candidate range and keep
  `fact_status: candidate` visible in row provenance/source headers.
- Focused regressions prove decode-looking Amiga/Atari DATA and Atari BSS bytes
  are not rendered as instructions, and Mac listing fails if shared executable
  ranges are missing.

Deletion candidates for 020-008:

- Mac `selected_code.code.layout_ranges` listing selection in
  `macos_listing_source.py` is superseded by `executable_ranges`.
- The Mac temporary `RawBinarySource` bridge remains active as a transport only;
  remove it after 020-007 imports shared Mac range provenance into analysis and
  020-008 proves artifact/web parity.
- Amiga/Atari direct section-kind render assumptions are now guarded by the
  shared role/fact contract and can be consolidated with the 020-007 analysis
  import path.

### 020-007: Analysis-State Executable Import

Completed analysis-state executable import:

- C listing analysis JSON now imports the shared executable model at the
  analysis root as `executable_model`, `executable_ranges`, and
  `executable_deferred`.
- Amiga and Atari analysis import share the same range role/fact contract used
  by 020-006 listing validation. Each analysis range carries `section_index`,
  `role`, `load_offset`, nullable `stored_offset`, `size`, `stored_size`,
  `status`, `fact_id`, `fact_status`, and `parser_use`.
- Amiga analysis preserves accepted CODE/DATA/BSS authority and deferred runtime
  entry state. Atari analysis preserves accepted TEXT/DATA authority, keeps BSS
  candidate-only, and keeps relocation breadth deferred-only.
- Mac analysis payloads now carry `platform: macos`,
  `executable_model: platform_executable_summary_v1`, the selected shared CODE
  range from `executable_ranges`, `executable_deferred`, and Mac provenance.
  Candidate CODE remains candidate-only; byte-entry and relocation/fixup facts
  are not promoted.
- Focused regressions prove Amiga, Atari, and Mac analysis payloads contain
  shared executable ranges with KB fact ids, statuses, and parser-use authority.

Retained blockers and deletion candidates:

- Mac analysis still wraps a raw selected CODE byte artifact for instruction
  analysis. The analysis payload carries shared Mac provenance, but the
  transport wrapper remains a 020-008 deletion candidate after parity proof.
- The Amiga/Atari C range import currently normalizes object sections into the
  shared contract inside the C analysis path. 020-008 should consolidate any
  duplicate summary/listing helpers that remain after closeout proof.

### 020-008: Remove Superseded Executable Paths

Completed deletion table and cleanup:

| Old path | Replacement proof | 020-008 decision |
| --- | --- | --- |
| Python current Amiga/Atari coverage loaders requiring legacy top-level `sections` before accepting current parser output. | 020-002/020-004 emit shared `executable_ranges`; 020-003 and 020-007 prove parser-owned fact refs and analysis import from shared ranges. | Deleted. `_load_current_amiga_hunk_output` and `_load_current_atari_prg_output` now require executable file kind plus shared executable ranges/fact refs, not legacy section presence. Regression tests pass summaries without `sections`. |
| C analysis import defaulting every non-Atari executable to the Amiga shared range authority. | 020-007 proved analysis import for Amiga/Atari, while Mac analysis wrapper supplies its own shared range provenance. | Deleted. Analysis JSON append now receives the explicit backend name from path/buffer/raw/listing artifact call sites, so raw or future non-Amiga executables cannot silently inherit Amiga facts. |
| Mac `selected_code.code.layout_ranges` as listing selection authority. | 020-006 made `macos_listing_source.py` fail closed unless `executable_model: platform_executable_summary_v1` and a selected `executable_ranges` CODE item are present. | Removed from listing selection. Retained only as compatibility payload details in project/artifact/web views until those public fields have explicit replacement consumers. |
| Mac temporary `RawBinarySource` bridge for selected CODE bytes. | 020-006/020-007 prove shared provenance around listing rows and analysis payload, but the generic C instruction decoder still requires byte transport. | Blocked, retained as transport only. Removing it needs a native Mac CODE byte-provider listing artifact, outside 020's proven replacement scope. |
| Top-level inspect JSON `sections` and `fact_refs`. | Shared ranges/deferred refs now drive coverage and current loaders, but older inspect/report/API tests still use these as broad parser inventory surfaces. | Blocked, retained as public inspect compatibility. They are no longer accepted as a replacement for shared executable ranges in current coverage/loaders. |
| Mac project/artifact/web `selected_code_segment`, `code_layout`, orphan, and relocation fields. | Shared ranges carry accepted/candidate/deferred authority, but existing UI/API tests still assert these fields for non-CODE visibility and deferred fixup explanation. | Blocked, retained as compatibility outputs with shared range requirements guarding parser/listing paths. |

Validation:

- `cmd /c src\build.bat`
- focused parser loader regressions for 020-008
- focused analysis/import/listing/artifact tests
- combined current coverage with Mac, Amiga, and Atari
- `git diff --check`

### 020-009: Cross-Platform Closeout Proof

Completed closeout decision:

Proposal 020 is complete. Amiga HUNK, Atari PRG, and Classic Mac OS CODE now
flow through `platform_executable_summary_v1` for executable-format parser
authority, range/status reporting, analysis import, and listing/rendering
guards. Candidate, deferred, and unsupported states remain non-accepted; Mac
byte-entry and relocation/fixup facts were not promoted.

Closeout proof:

- `uv run python -m amiga_reversing.tools.platform_executable_formats validate`
  passed.
- `uv run python -m amiga_reversing.tools.platform_executable_formats coverage
  --current-macos-c-backend --current-amiga-hunk --current-atari-prg` passed
  with `parser_outputs: 3`, `invalid: 0`, `unreported_platforms: []`, and
  visible `$.executable_ranges[...]` / `$.executable_deferred[...]` refs for
  all current platforms.
- Focused parser, analysis, listing, artifact, Mac project, Mac web, and web app
  source tests passed: `80 passed`.
- Repository precommit passed: style OK, dead code OK, unit OK, integration OK,
  explicit OK.
- `git diff --check` passed during final closeout.

Remaining future work is intentionally outside 020:

- Replace the Mac selected-CODE `RawBinarySource` byte-transport bridge with a
  native Mac CODE byte-provider listing artifact.
- Retire public inspect/API compatibility fields such as top-level `sections`,
  `fact_refs`, `selected_code_segment`, `code_layout`, orphan ranges, and
  relocation summaries only after downstream UI/API consumers move to shared
  ranges.
- Extend Amiga overlay/runtime entry handling and Atari relocation/symbol parsing
  under new issues without weakening 018 KB authority.

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
- 020-005 follows completed/reviewed 020-003 and 020-004.
- 020-006 follows 020-005 and must refresh assumptions from 020-003 through
  020-005 before coding.
- 020-007 follows 020-005 and must review 020-006 before finalizing import
  assumptions.
- 020-008 follows 020-006 and 020-007.
- 020-009 closes the proposal after all prior issues are complete.

## Non-Goals

- Promoting Mac byte-entry or relocation/fixup facts.
- Full Amiga HUNK overlay/loader migration.
- Full Atari PRG relocation/symbol parser migration.
- Mac source-to-CODE recovery.
- Non-CODE Mac resource payload decoding.
- UI redesign beyond consuming the shared model correctly.
