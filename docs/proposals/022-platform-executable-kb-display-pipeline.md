# Proposal 022: Platform Restored Source Model

Status: active

Reopened after closeout review for `022-012`: Mac project/web payloads still
contain Python-side restored-source synthesis and verifier claims. The completed
`022-011` proof remains a snapshot, not final closure, until Mac restored-source
records are consumed from the C-owned model or fail closed.

## Purpose

Build the shared restored-source model that turns executable-format KB facts
into source-level code/data representation for Amiga HUNK, Atari ST PRG, and
Classic Mac OS CODE.

Proposal 018 established executable-format KB authority. Proposal 020 moved
parser/import/listing gates onto `platform_executable_summary_v1`. Proposal 021
made Mac CODE a native source path with neutral flat M68K buffer internals.

022 is the next implementation step. It is not only display cleanup. It defines
the model a restored source listing must satisfy:

```text
platform_executable_summary_v1
  -> restored_source_model
  -> source_ownership_ranges
  -> source_reference_records
  -> platform_extensions
  -> source_coverage_verifier
  -> source/listing/artifact/web/API output
```

017 remains separate. 017 owns evidence-review and analysis-loop protocol. 022
owns platform executable source reconstruction and display fidelity.

## Platform Outcomes

Amiga HUNK and Atari ST PRG remain rebuild-capable targets. Any 022 change for
them must preserve exact round-trip and reproduction gates.

Classic Mac OS m68k is a restored-source disassembly target, not a round-trip
resource rebuild target. Mac CODE must reach the same basic source-level
standard expected of restored Amiga/Atari source: code ranges, data ranges,
metadata, relocation/reference effects, placeholders, labels, provenance, and
clear status. It does not need to rebuild the resource fork byte-for-byte.

## Core Model

The restored source model is shared. Platform-specific code should extend it,
not fork it.

Core records:

- `source_ownership_ranges`: every rendered byte/range owned by code, data,
  BSS, metadata, relocation/fixup, padding, placeholder, or unknown.
- `source_reference_records`: relocations, fixups, address references, symbol
  references, and source-level links between code/data/resource concepts.
- `source_line_groups`: source rows grouped by ownership and reference context.
- `source_coverage_verifier`: gap/overlap/status checks for rendered source
  ownership.
- `round_trip_requirement`: exact for Amiga/Atari where supported, absent for
  Mac CODE.
- `platform_extensions`: platform-specific facts attached to shared records.

Platform extensions:

- Amiga: HUNK ids, CODE/DATA/BSS sections, relocation hunks, symbols/debug when
  available, exact rebuild metadata.
- Atari: PRG TEXT/DATA/BSS, relocation table/basepage/symbol details, exact
  rebuild metadata.
- Mac: CODE resource id/name, CODE 0 metadata, Segment Loader fixups, A5/world
  conventions, executable-relevant resource placeholders.

## Current Implementation Anchors

022 must extend the existing implementation seams instead of creating a
parallel report-only model.

Anchors to reuse or deliberately replace:

- `src/platform_executable_summary.h` is the imported executable fact layer. The
  restored source model consumes this layer and must not duplicate KB authority.
- `src/m68k_render_plan.h` already gives rendered rows stable row ids, row
  kinds, source ranges, runtime ranges, statement metadata, source bytes, data
  class flags, and line windows. 022 should attach ownership/reference state to
  this row/render-plan layer or to an adjacent C-owned structure emitted with
  it.
- `amiga_reversing/disasm/c_backend.py` exposes `CListingArtifact` analysis,
  source text, summary, navigation, row-window, source-offset row,
  runtime-address row, and anchor-window APIs. These are the Python/web/API
  seams for restored source evidence.
- Amiga/Atari exactness is currently enforced through facts-v2 direct rebuild,
  reproduction compare, and repository precommit gates. Source coverage reports
  are additional evidence, not replacements for exactness.
- Mac CODE still has public compatibility surfaces in `macos_project_payload.py`,
  `macos_target_artifact.py`, `macos_web_view.py`, and
  `amiga_reversing/web/app.js`: `selected_code_segment`, `code_layout`,
  `orphan_ranges`, `relocation_fixups`, `code_segment_map`, `preview_windows`,
  and `non_code_resource_details`. 022 should migrate consumers onto restored
  source records before deleting these fields.
- Current Mac Segment Loader relocation/fixup state is mostly represented as a
  deferred summary. 022 closeout requires source-level reference records or
  explicit placeholders for those effects; leaving only a broad deferred note is
  not sufficient.

## 022-001 Inventory And Replacement Map

Current ownership/range sources:

- Shared executable import authority is `platform_executable_summary_v1` in
  `src/platform_executable_summary.h` and its emitters in
  `src/platform_file_json.c`/`src/platform_file_lib.c`. Amiga and Atari ranges
  are derived from `M68kObject` sections as loaded-image `load_offset` spans
  with nullable stored offsets for BSS; Mac ranges come from CODE resource
  summary/layout facts.
- Rendered source ownership is currently implicit in `src/m68k_render_ir.c`:
  accepted instruction bytes render as instruction rows, fixup/anchor/structured
  data/string/unknown spans render as data rows, BSS/uninitialized spans render
  as reserve rows, and platform metadata renders as diagnostic or platform
  directive rows.
- `src/m68k_render_plan.h` is the correct attachment point for 022 output. Rows
  already carry row kind, section index, source offset/size, runtime range,
  statement metadata, source bytes, data class flags, labels, and line-window
  indexes.

Current relocation/reference sources:

- Amiga/Atari low-level relocation data enters through `M68kObject.fixups` and
  `M68kFixup` lookups. `src/m68k_analysis_facts_v2.c` turns fixups and traced
  address effects into xrefs, runtime-address refs, relocation anchors, and
  violation facts.
- `src/m68k_render_ir.c` renders fixup/anchor records as source data
  expressions today, but those references are not yet surfaced as a shared
  `source_reference_records` model.
- Mac Segment Loader relocation/fixup state is currently emitted mainly as
  deferred `relocation_fixups`/`executable_deferred` summary state. 022 must
  replace that broad-only surface with source-level reference records where
  evidence exists and explicit placeholders where it does not.

Current consumers:

- C listing artifacts in `src/platform_file_lib.c` expose analysis, source text,
  summary, navigation, row windows, source-offset row lookup, runtime-address row
  lookup, and anchor windows.
- `amiga_reversing/disasm/c_backend.py` is the Python API boundary for those
  artifact calls and for direct rebuild/reproduction comparison.
- `amiga_reversing/disasm/reproduction.py` owns Amiga/Atari round-trip report
  generation and remains the exactness proof surface.
- Mac project/artifact/web consumers are
  `amiga_reversing/disasm/macos_project_payload.py`,
  `amiga_reversing/disasm/macos_target_artifact.py`,
  `amiga_reversing/disasm/macos_web_view.py`, and
  `amiga_reversing/web/app.js`.

Legacy compatibility fields and deletion proof:

| Legacy field/path | Current role | Replacement restored-source record | Delete only after |
| --- | --- | --- | --- |
| `selected_code_segment` | Mac selected CODE identity/listing link | platform extension plus ownership model root | Web/API/artifact consumers read restored-source identity and listing link |
| `code_layout` | Mac CODE metadata/candidate/data spans | `source_ownership_ranges` | Mac selected CODE coverage verifier proves no silent gaps/overlaps |
| `orphan_ranges` | Mac candidate bytes outside selected code body | ownership ranges with candidate/unknown roles | Rows and web payload expose same span, reason, fact id/status/parser-use |
| `relocation_fixups` | Broad Mac deferred fixup note | `source_reference_records` plus placeholders | Source-level references/placeholders preserve deferred reason and provenance |
| `code_segment_map` | CODE 0 jump-table/resource routing | source references plus Mac platform extension | Navigation and artifact output link CODE resources through shared records |
| `preview_windows` | Candidate CODE previews for non-selected resources | placeholder/source-line groups over restored-source rows | Preview evidence is visible through shared rows or typed placeholders |
| `non_code_resource_details` | Unsupported resource inventory | executable-relevant resource placeholders | Placeholders expose type/id/name, size/hash, status, reason, provenance |
| ad hoc executable range JSON in listing profiles | Duplicate platform range summary | restored-source model derived from executable summary | C artifact APIs expose model and tests prove parity |

Round-trip and source-quality proof surfaces:

- Amiga/Atari exactness remains `cmd /c src\precommit.bat`, facts-v2 direct
  rebuild compare profiles, reproduction compare reports, and existing
  relocation/content exactness flags. Source coverage is additional evidence and
  cannot substitute for exact rebuild/reproduction proof.
- Mac proof is no-round-trip source quality: selected CODE listing/artifact/web
  tests, `platform_executable_formats` validate/coverage, candidate/deferred
  fact preservation, full selected CODE ownership coverage, source-level
  relocation/reference records or placeholders, and explicit `round_trip_required:
  false`.

First coding boundary for 022-002:

- Add a C-owned restored-source model adjacent to the render-plan/listing
  artifact layer, initially derived from `PlatformExecutableSummary` plus
  `M68kObject` section/CODE metadata. Expose it through a listing artifact
  analysis/API payload for one rebuilt platform path and one Mac CODE path before
  adding the verifier. This avoids a disconnected report-only implementation and
  gives 022-003 one authoritative model to validate.

UI follow-up observations:

- Existing web panels can display the new evidence without redesign, but later
  UI work should add ownership navigation, reference/fixup context, resource
  placeholder navigation, and side-by-side code/data/source views.

## Tutorial Example

A Mac CODE restored-source packet should be explicit about ownership and
references:

```json
{
  "model": "restored_source_model_v1",
  "platform": "macos",
  "source_kind": "macos_code_resource",
  "round_trip_required": false,
  "ownership_ranges": [
    {
      "role": "metadata",
      "space": "code_resource_payload",
      "start": 0,
      "size": 4,
      "resource_id": 1,
      "fact_status": "validated"
    },
    {
      "role": "candidate_code",
      "space": "code_resource_payload",
      "start": 40,
      "size": 28984,
      "fact_id": "macos.code_resource.movea_stack_a0.boundary.candidate",
      "fact_status": "candidate",
      "parser_use": "candidate_only"
    }
  ],
  "references": [
    {
      "kind": "segment_loader_fixup",
      "source_offset": 128,
      "target": "CODE:4+0x2a",
      "status": "accepted",
      "fact_id": "macos.segment_loader.fixup"
    }
  ],
  "placeholders": [
    {
      "kind": "resource_placeholder",
      "resource_type": "WIND",
      "resource_id": 128,
      "status": "unsupported",
      "reason": "referenced by executable source but payload decoder is out of scope"
    }
  ]
}
```

The rendered source should carry the same evidence:

```asm
; restored_source_model: v1
; source_kind: macos_code_resource
; resource: CODE 1 Main
; ownership: candidate_code payload[40..29024)
; fact: macos.code_resource.movea_stack_a0.boundary.candidate
; status: candidate parser_use=candidate_only
; fixups: segment_loader references attached where decoded

loc_0_00000000:
        movea.l (a7)+,a0
        move.l  a7,d0
```

For Amiga and Atari, the same model must also prove rebuildability:

```json
{
  "model": "restored_source_model_v1",
  "platform": "amiga-hunk",
  "round_trip_required": true,
  "round_trip": "exact",
  "ownership_ranges": [
    {"role": "code", "fact_status": "parser_asserted"},
    {"role": "data", "fact_status": "parser_asserted"},
    {"role": "bss", "stored_size": 0}
  ]
}
```

## Non-Negotiable Direction

- The KB-backed executable model feeds the restored source model.
- The restored source model owns user-visible source structure.
- C owns source ownership, reference records, validation, and verifier logic.
  Python may expose reports, tests, fixtures, web/API plumbing, and workflow
  commands.
- Amiga and Atari exact round-trip gates remain mandatory.
- Mac CODE must be source-level correct for reading, porting, and rebuilding
  knowledge manually, but no Mac resource round-trip is required.
- Mac Segment Loader relocation/fixup effects are required for closeout as
  source-level references/placeholders.
- Unknown ranges are allowed only when explicit: byte span, role, status,
  provenance, reason, and source-visible rendering.
- Do not keep duplicate default display/source paths after shared-model parity.
- Do not promote candidate/deferred/unsupported facts to accepted behavior.
- Do not mix 017 analysis protocol changes into this proposal.

## Implementation Focus

### 022-001: Restored Source Inventory And Deletion Map

Inventory current source/listing/artifact/web/API consumers and the current
ownership/reference assumptions for Amiga, Atari, and Mac.

This is not a blocker report. It must end with a concrete replacement map:

- current ownership/range sources;
- current relocation/reference sources;
- current source rendering consumers;
- current web/API consumers;
- legacy fields or paths to delete;
- proof required before each deletion;
- first coding issue selected.

The inventory must explicitly trace the current implementation anchors above
and decide whether each one is reused, extended, or deleted.

### 022-002: Shared Source Ownership Model

Add the C-owned `restored_source_model_v1` and `source_ownership_ranges` model.
It should represent code, data, BSS, metadata, relocation/fixup, padding,
placeholder, and unknown ownership over the source bytes relevant to each
platform.

Required result:

- One shared ownership model exists in C.
- At least one Amiga/Atari path and one Mac path emit or consume it.
- Ownership ranges carry KB fact id/status/parser-use where applicable.
- Gaps and overlaps are detectable.
- The model consumes `platform_executable_summary_v1` and reaches listing
  artifact/render-plan output, not only inspect JSON.

Completed initial ownership slice:

- Added the C-owned `RestoredSourceModel`/`RestoredSourceOwnershipRange` shape in
  `src/restored_source_model.h`.
- Listing artifact analysis JSON now exposes `restored_source_model:
  restored_source_model_v1`, `round_trip_required`, and
  `source_ownership_ranges`.
- Amiga HUNK and Atari PRG ownership ranges are derived from current executable
  section summaries over `loaded_image` byte space. Amiga/Atari round-trip
  remains required; Atari BSS remains `candidate`/`candidate_only`.
- Mac CODE byte artifacts expose selected-code ownership over
  `selected_code_bytes`, with `round_trip_required: false` and candidate
  byte-entry fact status preserved.
- This first model slice carries ownership only. Reference records, verifier
  decisions, and Mac placeholder expansion are left to 022-003 through 022-008
  so they do not get confused with ownership proof.

### 022-003: Source Coverage Verifier

Add the C-owned verifier for restored source ownership.

Required result:

- Verifier rejects silent gaps and overlapping ownership ranges.
- Verifier rejects role/status conflicts, such as accepted instruction rendering
  from data/BSS/metadata.
- Amiga/Atari verifier path is compatible with exact rebuild gates.
- Mac verifier covers selected CODE resource bytes and executable-relevant
  placeholders without claiming rebuild.
- Python exposes a report/test wrapper only after C owns the checks.
- Verifier results are available through `CListingArtifact` or an equivalent
  artifact API so CLI/web/API callers can use the same proof.

Completed initial verifier slice:

- Listing artifact analysis JSON now includes `source_coverage_verifier`.
- The C verifier detects initial/inter-range/trailing gaps, overlaps, malformed
  explicit unknown ranges, and instruction rows whose source bytes are owned by
  non-code ownership roles.
- Current Amiga/Atari and Mac CODE artifact paths emit passing verifier reports.
  Amiga/Atari still rely on exact rebuild/reproduction gates for binary
  correctness; verifier success only proves restored-source ownership coverage.
- The verifier currently validates ownership and rendered instruction role
  compatibility. It does not yet validate shared reference records or Mac
  executable-resource placeholders; those are 022-004 through 022-008 work.

### 022-004: Shared Source Reference Records

Add shared `source_reference_records` for relocations, fixups, address refs,
symbol refs, and platform extension references.

Required result:

- Amiga/Atari existing relocation/reference behavior can be represented through
  the shared record shape without losing round-trip proof.
- Mac Segment Loader fixups have a target representation even where a custom
  extension remains unresolved.
- Reference records attach to ownership ranges and source rows.
- Existing facts-v2 relocation/source counters and reproduction exactness data
  are reviewed so shared references do not weaken current Amiga/Atari behavior.

Completed initial reference-record slice:

- Added the C-owned `RestoredSourceReferenceRecord` shape.
- Listing artifact analysis JSON now exposes `source_reference_records`.
- Amiga/Atari object fixups map to shared `relocation_fixup` records attached
  to ownership ranges and render-plan row ids where a row exists. These records
  preserve candidate parser-use status and do not replace exact rebuild or
  reproduction relocation checks.
- Mac CODE emits a deferred `segment_loader_fixup_placeholder` reference so the
  Segment Loader effect has source-level representation without claiming decoded
  fixup semantics.
- Remaining platform extension work: richer target strings, symbol/address ref
  normalization, and decoded Mac Segment Loader/custom extension records belong
  to 022-007/022-008.

### 022-005: Amiga HUNK Restored Source Integration

Move Amiga source/listing/artifact output onto the shared restored source model.

Required result:

- CODE/DATA/BSS ownership comes from the shared model.
- Existing relocation/reference behavior maps into shared reference records.
- Exact rebuild and reproduction gates remain green.
- Legacy display decisions that duplicate the shared model are deleted after
  proof.
- Direct rebuild/reproduction compare remain the acceptance gates; source
  coverage cannot substitute for binary exactness.

Completed Amiga integration slice:

- Amiga HUNK listing artifact analysis exposes `restored_source_model_v1`,
  `source_ownership_ranges`, `source_reference_records`, and
  `source_coverage_verifier`.
- CODE/DATA/BSS ownership is derived from the shared loaded-image ownership
  model rather than a separate display-only model.
- Existing HUNK fixups map to shared `relocation_fixup` records attached to
  ownership ranges and render-plan row ids when available.
- Exactness remains governed by existing direct rebuild/reproduction gates;
  `cmd /c src\precommit.bat` passed after this integration.
- Runtime entry uncertainty remains deferred and non-promoted.

### 022-006: Atari PRG Restored Source Integration

Move Atari PRG source/listing/artifact output onto the shared restored source
model.

Required result:

- TEXT/DATA/BSS ownership comes from the shared model.
- Relocation/basepage/symbol states map into shared reference records or
  explicit deferred placeholders.
- Exact rebuild and reproduction gates remain green.
- Candidate/deferred states remain governed by Proposal 018.
- Direct rebuild/reproduction compare remain the acceptance gates; source
  coverage cannot substitute for binary exactness.

Completed Atari integration slice:

- Atari PRG listing artifact analysis exposes `restored_source_model_v1`,
  `source_ownership_ranges`, `source_reference_records`, and
  `source_coverage_verifier`.
- TEXT/DATA/BSS ownership is derived from the shared loaded-image ownership
  model. BSS remains candidate-only under Proposal 018 authority.
- Existing PRG fixups map to shared `relocation_fixup` records where parsed;
  broader relocation terminator variants remain deferred.
- Exactness remains governed by existing direct rebuild/reproduction gates;
  `cmd /c src\precommit.bat` passed after this integration.
- Retained extension work is richer symbol/basepage/reference normalization in
  later restored-source reference iterations; no candidate/deferred state was
  promoted.

### 022-007: Mac CODE Ownership And Relocation Integration

Move Mac CODE source/listing/artifact/web/API output onto the restored source
model.

Required result:

- Every byte in the selected executable CODE payload is owned by metadata,
  code, data, relocation/fixup, padding, placeholder, or explicit unknown.
- Mac Segment Loader relocation/fixup effects are represented as source-level
  reference records where evidence supports them.
- Custom or unresolved extension bytes render as placeholders with byte span,
  reason, status, provenance, and reference context.
- CODE resource identity and A5/world conventions are platform extensions over
  the shared model.
- No Mac round-trip claim is introduced.
- Existing Mac artifact/web fields are migrated only when restored source
  records expose equivalent or better source detail.

Completed 022-007 state:

- Mac project payloads attach `restored_source_model_v1` to selected CODE,
  selected listing descriptors, and per-CODE resource detail records. Existing
  public Mac fields remain in place for compatibility.
- Selected executable CODE payload bytes are covered by restored-source
  ownership ranges over `code_resource_payload`. Layout gaps become explicit
  `unknown` ranges with span, deferred status, provenance, reason, and
  source-visible placeholder rendering.
- Segment Loader relocation/fixup state is represented by deferred
  `segment_loader_fixup_placeholder` source reference records. No decoded fixup
  semantics or round-trip claim is introduced.
- CODE resource identity and A5/world runtime context are platform extensions.
  A5/world remains deferred context, not accepted byte-entry or storage proof.
- Mac target artifacts render the model, verifier result, ownership ranges,
  source references, CODE identity, and A5/world extension state. Existing web
  panels expose restored-source model counts and coverage through current
  Mac CODE detail rows; richer UI grouping remains 022-009 follow-up work.
- Focused proof passed with 36 Mac project/artifact/web/source tests.

### 022-008: Executable-Relevant Resource Placeholders

Add typed placeholders for executable-relevant Mac resources and custom
extensions referenced by CODE source.

Required result:

- Placeholder records include resource type/id/name when known, byte size/hash,
  reference sites, status, reason, and provenance.
- Broad non-CODE resource decoding is not added unless needed for executable
  source comprehension.
- Web/API payloads expose placeholders in a stable form.
- Placeholder identity must be stable enough for later UI/navigation work to
  link resource type/id/name back to source reference sites.

Completed 022-008 state:

- Mac project and web payloads expose `executable_resource_placeholders` for
  non-CODE resource inventory that can matter to executable comprehension.
- Placeholder records include resource type, id/name when known, resource
  count, byte size/hash when known, stable identity, status, reason,
  provenance, source-visible state, KB fact state where applicable, and
  reference-site records.
- Current reference sites are inventory-level because no direct CODE source
  reference offset is known yet. The placeholder schema keeps the source
  reference slot stable for later CODE-derived navigation.
- The Mac target artifact renders executable resource placeholders and their
  reference-site context. Broad non-CODE resource payload decoding remains out
  of scope.

### 022-009: Web/API Exposure And UI Follow-Up Notes

Expose restored source ownership, references, verifier results, and placeholders
through existing web/API surfaces. Do not redesign the UI.

Required result:

- Existing web/API consumers can inspect ownership and references.
- Old Mac-only fields stop being the only way to see CODE structure where shared
  records now exist.
- Obvious UI shortcomings are documented as future work: ownership navigation,
  relocation/reference context, resource placeholder navigation, and side-by-side
  code/data/source views.
- UI follow-up notes do not block 022 unless required evidence is not visible at
  all.
- The current Mac CODE web panel is an existing consumer to migrate, not a
  reason to build a new UI.

Completed 022-009 state:

- Existing Mac project/web/API payloads expose restored-source ownership
  ranges, source reference records, verifier results, platform extensions, and
  executable resource placeholders.
- The existing Mac web panel renders restored-source model status/counts and
  executable resource placeholders without a redesign. Existing listing,
  navigation, and window APIs remain usable.
- Future UI work: ownership-range navigation, richer relocation/reference
  context views, resource-placeholder navigation by stable identity, and
  side-by-side code/data/source views would improve inspection but are not
  required for evidence visibility.

### 022-010: Delete Superseded Compatibility Paths

Delete display/source compatibility paths made obsolete by the restored source
model.

Required result:

- Deletions are backed by replacement tests.
- No dual default behavior remains.
- Public API compatibility fields are removed only after consumers migrate.
- Amiga/Atari exact gates and Mac source-quality gates still pass.

Completed 022-010 deletion table:

| Legacy field/path | 022-010 decision | Replacement / remaining consumer |
| --- | --- | --- |
| Mac target artifact selected `classified_layout` rendering | Deleted from default artifact output. | Restored-source `ownership_ranges` render metadata/data/candidate/unknown spans with status, provenance, and reason. |
| Mac target artifact selected/detail `orphan_ranges` rendering | Deleted from default artifact output. | Candidate data/unknown spans render through `source_ownership_ranges`; tests assert the old artifact section is absent. |
| Mac target artifact selected/detail `relocation_fixups` rendering | Deleted from default artifact output. | Deferred Segment Loader state renders through `source_reference_records` and `segment_loader_fixup_placeholder`. |
| Payload `selected_code_segment`, `code_layout`, `orphan_ranges`, `relocation_fixups`, `preview_windows`, `non_code_resource_details` | Retained as public compatibility/API data. | Current tests and web/API fixtures still consume these fields for selected CODE identity, preview rows, navigation anchors, and compatibility assertions. Default artifact/web evidence now exposes restored-source records where the shared model exists. |
| Web Mac CODE detail display | Migrated without redesign. | Existing panel displays restored-source model status/counts and executable resource placeholders; legacy fields are no longer the only visible evidence. |

Amiga/Atari exactness still depends on their rebuild/reproduction gates; this
deletion slice does not weaken those gates. Mac still has no round-trip claim.

### 022-011: Cross-Platform Closeout Proof

Close the proposal by proving all platform outcomes together:

- Amiga round-trip exact with restored source ownership and references.
- Atari round-trip exact with restored source ownership and references.
- Mac CODE selected executable source has full ownership coverage, source-level
  relocation/reference representation, executable-relevant placeholders, and no
  round-trip claim.

Completed 022-011 closeout proof:

- Amiga HUNK and Atari PRG listing artifact analysis emit
  `restored_source_model_v1`, `source_ownership_ranges`,
  `source_reference_records`, and passing `source_coverage_verifier` reports.
  Exactness remains enforced by existing rebuild/reproduction precommit gates.
- Mac CODE project, listing artifact, target artifact, and web/API surfaces
  expose restored-source ownership, reference records, verifier results,
  executable resource placeholders, and platform extensions. Mac keeps
  `round_trip_required: false` and makes no resource-fork round-trip claim.
- The verifier has positive coverage on current Amiga/Atari/Mac artifact paths
  and negative coverage for C failure modes: gaps, overlaps, malformed unknown
  ranges, and invalid instruction ownership.
- Completed 022 issue files were deleted only after durable conclusions were
  promoted into this proposal.
- Retained future work: richer Mac UI navigation for ownership ranges,
  relocation/reference context, executable resource placeholders, and
  side-by-side code/data/source inspection. Public Mac compatibility payload
  fields remain until current API consumers migrate fully to restored-source
  records.

Closeout review finding:

- The Mac selected CODE project/web path still has Python helpers that build
  `source_ownership_ranges`, `source_reference_records`, and a passing
  `source_coverage_verifier` from public compatibility fields when the payload
  lacks a restored-source packet. That is not acceptable as final 022 authority:
  Python may expose, render, and fail closed around restored-source records, but
  it must not synthesize verifier-successful restored-source evidence that the
  C-owned model did not emit.

### 022-012: C-Owned Mac Restored-Source Authority

Remove Python-side restored-source synthesis from the Mac project/web path and
make all Mac restored-source evidence come from the C-owned model or fail closed
with an explicit missing-model diagnostic.

Required outcome:

- Mac project/web/API payloads preserve C-emitted restored-source records without
  changing their ownership/reference/verifier meaning.
- If a selected CODE payload lacks C-emitted restored-source records, the project
  and web surfaces expose a missing-model/blocker state instead of constructing
  synthetic `source_ownership_ranges`, `source_reference_records`, or
  `source_coverage_verifier.ok: true`.
- Compatibility fields may remain for identity/navigation while current
  consumers need them, but they cannot be treated as restored-source authority.
- Tests prove both the normal current Mac fixture path and the fail-closed
  missing-model path.
- The proposal is marked complete again only after `022-012` is implemented,
  reviewed, and its conclusions are promoted here.

Final proof commands:

- `cmd /c src\precommit.bat`: passed.
- `uv run python -m amiga_reversing.tools.platform_executable_formats validate`:
  passed.
- `uv run python -m amiga_reversing.tools.platform_executable_formats coverage
  --current-macos-c-backend --current-amiga-hunk --current-atari-prg`: passed
  with `invalid: 0`, `parser_outputs: 3`.
- `uv run python -m pytest tests\test_macos_c_backend.py
  tests\test_macos_project_payload.py tests\test_macos_target_artifact.py
  tests\test_macos_web_view.py tests\test_web_app_source.py -q`: passed with
  48 tests.

## Acceptance Criteria

- `restored_source_model_v1` exists and is C-owned.
- Mac project/web/API surfaces consume C-owned restored-source records or fail
  closed; they do not synthesize verifier-successful restored-source evidence
  from compatibility fields.
- `source_ownership_ranges` cover relevant executable source bytes.
- `source_reference_records` represent relocation/fixup/address effects.
- `source_coverage_verifier` rejects gaps, overlaps, and invalid role/status
  renderings.
- Amiga and Atari remain exact round-trip capable.
- Mac CODE reaches restored-source quality without round-trip requirement.
- Mac Segment Loader relocation/fixup effects are represented as source-level
  references/placeholders.
- Executable-relevant resources/custom extensions have typed placeholders.
- Existing web/API surfaces expose the evidence.
- UI shortcomings found during implementation are documented as future work.
- Legacy source/display paths are deleted after replacement proof.
- 017 analysis protocol work remains separate.

## Verification Plan

Minimum proof for every implementation issue:

```powershell
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-macos-c-backend --current-amiga-hunk --current-atari-prg
git diff --check
```

Amiga/Atari source changes must also run exact rebuild/reproduction proof and
repository precommit:

```powershell
cmd /c src\precommit.bat
```

Mac source changes must run focused Mac C/backend/project/artifact/web tests:

```powershell
uv run python -m pytest tests\test_macos_c_backend.py tests\test_macos_project_payload.py tests\test_macos_target_artifact.py tests\test_macos_web_view.py tests\test_web_app_source.py -q
```

Closeout must run all applicable proof together.

## Issue Ordering

- 022-001 starts first.
- 022-002 follows 022-001.
- 022-003 follows 022-002.
- 022-004 follows 022-002 and should review 022-003 before finalizing verifier
  assumptions.
- 022-005 and 022-006 may run in parallel after 022-003 and 022-004.
- 022-007 follows 022-003 and 022-004, and should review Amiga/Atari lessons
  before finalizing Mac integration.
- 022-008 follows 022-007.
- 022-009 follows 022-007 and 022-008.
- 022-010 follows 022-005 through 022-009.
- 022-011 closes the proposal.
- 022-012 follows the closeout review finding and blocks final re-closeout.

## Non-Goals

- 017 evidence-review protocol changes.
- New auto-analysis decision protocol work.
- Classic Mac OS resource-fork round-trip.
- Broad non-CODE Mac resource decoding unrelated to executable source.
- Promoting candidate/deferred/unsupported facts to accepted behavior.
- UI redesign.
- Amiga overlay/runtime semantics beyond preserving existing round-trip.
- Atari relocation/symbol parsing beyond what restored-source references and
  current gates require.
