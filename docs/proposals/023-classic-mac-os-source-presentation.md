# Proposal 023: Classic Mac OS Source Presentation

Status: active

## Purpose

Bring Classic Mac OS m68k source presentation to the reasonable stopping point
for a non-round-trip platform: a reverser can load the target, inspect CODE
resources as platform source, navigate source-owned code/data/placeholder
ranges, and see relocation/resource/A5 context without hidden compatibility
paths or unsupported semantic promotion.

This builds on completed proposals:

- 020 owns shared executable import through `platform_executable_summary_v1`.
- 021 owns native Mac CODE byte/listing identity over neutral flat M68K buffers.
- 022 owns C-backed restored-source ownership, reference records, placeholders,
  and verifier packets.

023 is the next source-quality slice. It must use those foundations to make Mac
source useful at the same basic presentation level as Amiga HUNK and Atari PRG:
code and data areas are visible, ownership is verified, references are surfaced,
unsupported platform extensions are explicit placeholders, and Python/web/API
surfaces present C-owned evidence instead of inventing authority.

Mac still has no resource-fork round-trip requirement.

## Target Outcome

For the committed MPW `Asm` Mac target, the user-visible source state should be:

```text
HFS image + file path
  -> CODE resource inventory
  -> C-owned restored-source packet per executable CODE resource
  -> CODE 0 routing/reference context
  -> Segment Loader fixup records or typed placeholders
  -> A5/world/global-access context or typed placeholders
  -> source/artifact/web/API display
  -> verifier proving no silent source ownership gaps
```

A selected CODE resource should render like source, not like a raw blob with a
side note:

```asm
; source_kind: macos_code_resource
; resource: CODE 1 "Main"
; restored_source_model: v1
; verifier: ok
; round_trip_required: false
; references: CODE0 dispatch, segment_loader_fixup placeholders
; a5_context: deferred, visible at source rows that use A5-relative forms

CODE_1_00000028:
        movea.l (a7)+,a0
        move.l  a7,d0
```

An unresolved platform extension must still be inspectable:

```json
{
  "kind": "segment_loader_fixup_placeholder",
  "resource": "CODE:1",
  "source_offset": 128,
  "status": "deferred",
  "reason": "custom extension format not decoded yet",
  "source_visible": true
}
```

## Stopping Contract

023 is complete only when the Mac source presentation contract is true for the
current committed Mac fixture:

- every executable CODE resource is either rendered through a C-owned restored
  source packet or represented by a typed, source-visible deferred placeholder;
- CODE 0 contributes routing/reference context instead of remaining only a
  metadata note;
- Segment Loader relocation/fixup effects are represented as source reference
  records where decoded, or as byte/span-specific placeholders where not;
- A5/world/global-base evidence is visible as row/context metadata or typed
  placeholders without claiming accepted lifetime proof;
- executable-relevant non-CODE resources have stable placeholders linked from
  source context when evidence exists;
- ownership and verifier evidence is C-owned and fail-closed;
- Python/web/API surfaces display that evidence and do not synthesize passing
  restored-source facts;
- no Mac round-trip or resource rebuild claim is introduced.

## Implementation Direction

- Prefer C-owned model and verifier extensions over Python synthesis.
- Extend shared restored-source and render-plan records before adding Mac-only
  display fields.
- Use platform extensions for Mac-specific concepts: CODE resource identity,
  CODE 0 routing, Segment Loader fixups, A5/world context, and resource
  placeholders.
- Make placeholders precise: type, resource id/name where known, byte span or
  source row where known, status, reason, provenance, and source visibility.
- Delete superseded compatibility paths after replacement proof.
- Preserve Amiga/Atari exact gates when shared code changes.
- Keep 017 cascade/evidence-review work separate.

## Work Items

### 023-001: Mac Source Presentation Baseline Harness

Add a current-state harness that proves what the Mac fixture source presentation
does and does not provide through the same C-owned surfaces the user sees.

This is not a report-only blocker issue. It must add executable checks that fail
when Mac source presentation silently drops CODE resources, restored-source
packets, verifier state, source references, placeholders, or web/API exposure.

Completed baseline:

- The committed MPW `Asm` project payload test now requires every CODE resource
  detail to expose a C-owned `restored_source_model_v1` packet, passing
  verifier, ownership ranges, source reference records, CODE resource platform
  extension, and deferred A5/world context. This fails if any executable CODE
  resource disappears from the source presentation boundary.
- The committed Mac target artifact test now requires broad restored-source
  rendering counts for model, verifier, and source reference records, plus
  executable resource placeholders.
- The Mac web payload test now requires selected CODE web/API restored-source
  authority, verifier state, ownership ranges, source reference records, and
  executable resource placeholders.
- Current blocker for 023-002 and later: baseline proves per-CODE packets are
  visible in project/artifact surfaces, while richer CODE 0 routing references,
  span-specific Segment Loader placeholders, A5 row context, and linked
  non-CODE source reference sites still need the later 023 slices. Candidate and
  deferred facts remain candidate/deferred; no Mac round-trip claim was added.

### 023-002: All CODE Resource Restored-Source Coverage

Move beyond selected-CODE-only confidence. Every executable CODE resource in the
Mac fixture must have either a C-owned restored-source packet with ownership
coverage or an explicit typed deferred source placeholder.

Completed per-CODE coverage:

- Mac project/API `code_resource_details` now exposes
  `source_presentation_status` for every CODE resource. C-owned restored-source
  packets report `kind: c_owned_restored_source_packet`, `status: covered`,
  stable `macos-code:CODE:<id>` identity, verifier state, ownership range
  count, source reference count, provenance, and source visibility.
- If a CODE resource lacks a C-owned packet, the status fails closed as
  `kind: typed_deferred_source_placeholder`, `status: blocked`, with resource
  identity, reason, provenance, and `source_visible: true`; compatibility
  fields are not treated as restored-source authority.
- The Mac target artifact renders the per-CODE source presentation status before
  the restored-source packet detail, so the committed artifact fails tests if
  executable CODE resources are silently omitted.
- CODE 0 remains metadata/routing-oriented but is explicitly represented with a
  C-owned restored-source packet and covered source presentation status.

### 023-003: CODE 0 Routing And Source References

Use CODE 0 as platform routing evidence. Represent CODE 0 dispatch/resource
relationships as source reference records or typed placeholders that link CODE
resources together.

### 023-004: Segment Loader Fixup Source Records

Replace broad relocation/fixup notes with source-level records: decoded records
where evidence supports them, and span-specific placeholders where decoding is
not yet implemented.

### 023-005: Mac Address And A5 Context Presentation

Surface Mac address-space and A5/world/global-base context at source rows and
reference records without promoting lifetime proof. A5-relative uses should be
visible and navigable as candidate/deferred context.

### 023-006: Executable Resource Placeholder Linking

Link executable-relevant non-CODE resource placeholders back to source context
where evidence exists. Keep broad resource parsing out of scope unless needed
for source comprehension.

### 023-007: Source Display And API Consolidation

Make source/artifact/web/API output consume the shared records from 023-002
through 023-006. Delete compatibility display paths that are no longer needed.

### 023-008: Cross-Platform Source Presentation Closeout

Prove the final Mac source presentation contract alongside Amiga/Atari exact
gates and close the proposal.

## Verification Plan

Minimum proof for every implementation issue:

```powershell
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-macos-c-backend --current-amiga-hunk --current-atari-prg
uv run python -m pytest tests\test_macos_c_backend.py tests\test_macos_project_payload.py tests\test_macos_target_artifact.py tests\test_macos_web_view.py tests\test_web_app_source.py -q
git diff --check
```

Shared restored-source/render-plan changes must also run:

```powershell
cmd /c src\precommit.bat
```

Closeout must include the full relevant Mac proof plus Amiga/Atari exact gates.

## Issue Ordering

- 023-001 starts first.
- 023-002 follows 023-001.
- 023-003 follows 023-002.
- 023-004 follows 023-002 and may run in parallel with 023-003 if it does not
  change CODE 0 assumptions.
- 023-005 follows 023-002 and may run in parallel with 023-003/023-004.
- 023-006 follows 023-003 and 023-004.
- 023-007 follows 023-003 through 023-006.
- 023-008 closes the proposal after all previous issues complete.

## Non-Goals

- Classic Mac OS resource-fork round-trip.
- Broad non-CODE resource decoding unrelated to executable source.
- Promoting Mac byte-entry, Segment Loader, A5, or resource facts beyond their
  evidence status.
- 017 cascade/evidence-review protocol work.
- UI redesign beyond making existing source evidence visible.
