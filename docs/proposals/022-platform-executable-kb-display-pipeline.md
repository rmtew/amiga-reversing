# Proposal 022: Platform Restored Source Model

Status: active

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

### 022-010: Delete Superseded Compatibility Paths

Delete display/source compatibility paths made obsolete by the restored source
model.

Required result:

- Deletions are backed by replacement tests.
- No dual default behavior remains.
- Public API compatibility fields are removed only after consumers migrate.
- Amiga/Atari exact gates and Mac source-quality gates still pass.

### 022-011: Cross-Platform Closeout Proof

Close the proposal by proving all platform outcomes together:

- Amiga round-trip exact with restored source ownership and references.
- Atari round-trip exact with restored source ownership and references.
- Mac CODE selected executable source has full ownership coverage, source-level
  relocation/reference representation, executable-relevant placeholders, and no
  round-trip claim.

## Acceptance Criteria

- `restored_source_model_v1` exists and is C-owned.
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
