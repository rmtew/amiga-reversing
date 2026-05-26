# Proposal 023: Classic Mac OS Source Presentation

Status: active

Reopened after the post-closeout artifact review: the C-owned restored-source
evidence exists, but the committed MPW `Asm.s` artifact is still report-first
and selected-CODE-centric. 023 is not complete until the visible source file
itself improves for a reversing user: real source must lead the artifact, every
CODE resource must have a visible source section or typed placeholder section,
CODE 0 routing must render as structured source data/context, and broad evidence
inventories must not swamp the front of the listing.

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

023 is the source-quality slice. It must use those foundations to make Mac
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

The committed `Asm.s` artifact must be source-first. A short identity header is
acceptable, but broad resource inventories, verifier dumps, per-CODE evidence
records, and unsupported-resource summaries belong after the source sections or
in a sidecar artifact. The first useful screen of `Asm.s` should show executable
Mac source, not pages of report comments.

Every CODE resource must be represented in the source body. A resource that
cannot yet be fully decoded still needs a stable section with a typed reason and
conservative bytes/placeholder rows, so a reverser can see that it exists and
where future work belongs:

```asm
; CODE 2: source placeholder, candidate bytes preserved
CODE_2_start:
        dc.b    $00,$00,$00,$00
        ; deferred: no accepted entry/lifetime proof yet
```

CODE 0 is source context, not just a report. Its jump-table and segment-routing
metadata should render as structured data with labels and links to CODE
sections where the parsed evidence supports that relationship:

```asm
CODE_0_jump_table:
        dc.l    CODE_27_start
        ; validated CODE 0 dispatch reference
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

- the generated `Asm.s` artifact is source-first: after a short header, real
  source sections appear before broad inventory/report comments;
- every executable CODE resource is either rendered through a C-owned restored
  source packet or represented by a typed, source-visible deferred placeholder;
- every executable CODE resource has a visible source-body section or
  placeholder section in `Asm.s`, not only a leading report entry;
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

Post-closeout correction:

- The previous 023 closeout proved C-owned evidence availability, not visible
  source quality. It allowed `Asm.s` to begin with a large report preamble and
  left the artifact effectively selected-CODE-centric. That is insufficient.
  The active 023-011 through 023-016 work restores the intended user-visible
  contract without promoting Mac byte-entry, Segment Loader, A5, or resource
  facts beyond their evidence status.

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

## Execution Standard

023 is implementation work, not a blocker-discovery track. The worker must make
visible source-output progress unless a fact is genuinely unknowable from the
target bytes plus the repository's Mac documentation and executable KB.

When an implementation detail seems missing, the required path is:

1. Inspect the current target bytes, parser output, restored-source packets, and
   generated `Asm.s` artifact.
2. Read the local Mac references first: `docs/macos-file-structure.md`,
   `docs/macos-initial-analysis-research.md`, `docs/macos-targets.md`,
   `docs/proposals/012-classic-mac-os-m68k-platform.md`,
   `docs/proposals/018-platform-executable-format-knowledge.md`,
   `docs/proposals/021-native-macos-code-source-pipeline.md`, and
   `docs/proposals/024-classic-mac-os-segment-loader-fixups.md`.
3. If the local documentation contains the needed rule, formalize it in the C
   parser/model or executable KB and continue the issue.
4. If the local documentation exposes a narrow missing KB fact, add the fact,
   provenance, tests, and continue the issue.
5. Only if the byte evidence and local documentation still do not support a
   semantic claim may the output use a conservative placeholder. That placeholder
   must still be source-visible, byte-preserving where bytes exist, labelled with
   a precise reason, and covered by tests.

The worker must not stop with a vague blocker, broad report-only output, or
selected-CODE-only output. Any remaining placeholder must be the result of this
documented implementation attempt, not a substitute for doing it.

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

Completed CODE 0 routing state:

- C-owned Mac restored-source packets now include CODE 0 routing records in
  `source_reference_records`: CODE 0 emits `code0_routing_table`, and nonzero
  CODE resources emit `code0_dispatch_reference` with CODE resource identity,
  CODE 0 jump-table offset/size, validated status, provenance, source
  visibility, and the accepted segment jump-table fact.
- Project/API and target artifact tests require these records. The facts remain
  accepted only for CODE 0/jump-table structure; byte-entry and Segment Loader
  semantics remain candidate/deferred.

### 023-004: Segment Loader Fixup Source Records

Replace broad relocation/fixup notes with source-level records: decoded records
where evidence supports them, and span-specific placeholders where decoding is
not yet implemented.

Completed Segment Loader source record state:

- The C-owned `segment_loader_fixup_placeholder` now carries CODE resource
  identity, `code_resource_payload` byte-space, source offset, source range
  start/end/size, status, provenance, and source visibility.
- Placeholder reason now distinguishes unsupported custom extension decoding
  from missing evidence: the current fixture has source spans but Segment
  Loader relocation/fixup custom extension decoding remains unimplemented and
  deferred.
- Artifact/API tests require the placeholder kind, deferred fact, resource id,
  and source range so the presentation cannot regress to a broad-only note.

### 023-005: Mac Address And A5 Context Presentation

Surface Mac address-space and A5/world/global-base context at source rows and
reference records without promoting lifetime proof. A5-relative uses should be
visible and navigable as candidate/deferred context.

Completed address/A5 context state:

- C-owned Mac restored-source packets now expose `platform_extensions.address_model`
  with payload offset space, local source offset space, deferred runtime address
  model, and C provenance.
- `source_reference_records` include `a5_world_context_placeholder` records with
  CODE resource identity, source offset, deferred status, provenance, and source
  visibility. This makes A5/world context visible in the same reference path
  without claiming accepted lifetime proof.
- `platform_extensions.a5_world` remains deferred and source-visible with C
  provenance; no parser fact or accepted status is asserted for A5 lifetime.

### 023-006: Executable Resource Placeholder Linking

Link executable-relevant non-CODE resource placeholders back to source context
where evidence exists. Keep broad resource parsing out of scope unless needed
for source comprehension.

Completed placeholder linking state:

- Project/API and web payload placeholders now carry a stable
  `macos-resource:<image>:<hfs-path>:<type>:*` identity through the placeholder,
  source-context summary, and reference-site record.
- Current non-CODE executable-resource placeholders remain type-level inventory
  records. Because no CODE routing, Segment Loader fixup, or restored-source
  reference currently targets those non-CODE resource types, each placeholder is
  explicitly `source_context.status: unlinked` with the reason recorded on both
  the source context and reference site.
- The target artifact renders placeholder source-context status, stable
  identity, and reference-site link status, so a reverser can navigate from the
  source-visible inventory context to the placeholder identity without treating
  unsupported resource payloads as decoded.

### 023-007: Source Display And API Consolidation

Make source/artifact/web/API output consume the shared records from 023-002
through 023-006. Delete compatibility display paths that are no longer needed.

Completed display/API consolidation state:

- The Mac project/API and target artifact paths consume the shared
  per-CODE `source_presentation_status`, C-owned restored-source ownership,
  source reference records, platform extensions, and executable resource
  placeholder records built by 023-002 through 023-006.
- The web renderer now displays per-CODE source presentation status, restored
  source reference kinds, A5/world status, and executable resource placeholder
  source-context/link status directly from those shared records.
- The web renderer no longer falls back from the top-level executable resource
  placeholder API to nested resource-fork compatibility data. Missing restored
  source still fails closed as `restored_source_missing`; no passing verifier or
  ownership evidence is synthesized in Python or web code.
- Remaining UI limitations are presentational only: the current web panel shows
  compact summaries rather than a dedicated cross-linked resource/source
  navigation UI. That is future UI work and does not block the source evidence
  contract.

### 023-008: Cross-Platform Source Presentation Closeout

Prove the final Mac source presentation contract alongside Amiga/Atari exact
gates and close the proposal.

Final closeout state:

- Proposal 023 is complete for the committed MPW `Asm` fixture as starter
  Classic Mac OS source presentation, not as resource-fork round-trip support.
- Every executable CODE resource is visible in `code_resource_details` with
  `source_presentation_status`. Current fixture CODE resources are covered by
  C-owned `restored_source_model_v1` packets with verifier state, ownership
  ranges, source reference records, and stable CODE identities; missing future
  packets fail closed as typed deferred source placeholders.
- CODE 0 routing, Segment Loader fixup placeholders, A5/world context,
  address-space context, and executable non-CODE resource placeholders are
  visible through the same source/API/artifact/web surfaces. Mac byte-entry,
  Segment Loader relocation/fixup decoding, and A5 lifetime semantics remain at
  their existing candidate/deferred evidence states.
- Non-CODE resource payloads remain placeholders. Current placeholders are
  stable by resource type and explicitly unlinked because no CODE routing,
  fixup, or restored-source reference targets those resource types yet.
- Python/web/API presentation consumes C-owned restored-source evidence and
  does not synthesize passing verifier, ownership, or restored-source authority.
- Final proof passed: executable-format KB validation; executable-format
  coverage against current Mac C backend, current Amiga HUNK, and current Atari
  PRG outputs; focused Mac backend/project/artifact/web/source tests; C
  precommit; and `git diff --check`.

Closeout review finding:

- The C-owned source reference records overstate two Mac reference facts. First,
  nonzero CODE resources with no CODE 0 jump-table span still get a validated
  `code0_dispatch_reference`. A resource with `first_jump_table_entry_offset:
  65535` and `jump_table_entry_count: 0` has no accepted dispatch span and must
  not receive a validated source reference. Second, CODE 0 gets a
  `segment_loader_fixup_placeholder` even though it is metadata/routing, not a
  normal executable CODE segment fixup span. Both defects make the source
  presentation look more proven than the parsed evidence supports.

### 023-009: Guard CODE 0 Dispatch References

Fix nonzero CODE source reference records so validated `code0_dispatch_reference`
records are emitted only when the parsed CODE segment has a real CODE 0
jump-table span.

Required outcome:

- CODE resources with `first_jump_table_entry_offset == 0xffff` or
  `jump_table_entry_count == 0` do not emit validated CODE 0 dispatch
  references.
- If user-visible context is still useful for those resources, it is emitted as
  a typed deferred/unlinked placeholder, not as accepted routing.
- Tests cover both a real dispatch span and an absent span.
- The generated MPW `Asm` artifact no longer shows validated CODE 0 dispatch
  references for resources whose segment map says `jt_first=65535 jt_count=0`.

Completed corrected dispatch-reference behavior:

- The C-owned restored-source reference builder now emits validated
  `code0_dispatch_reference` records only when a nonzero CODE resource has both
  `first_jump_table_entry_offset != 0xffff` and `jump_table_entry_count > 0`.
- Current MPW `Asm` CODE 1 has `jt_first=65535 jt_count=0`, so its restored
  source records keep the deferred Segment Loader placeholder and A5/world
  context but no accepted CODE 0 dispatch reference.
- Current MPW `Asm` CODE 27 has a real CODE 0 jump-table span and still emits a
  validated `code0_dispatch_reference` targeting `CODE:27`.

### 023-010: Keep CODE 0 Free Of Segment Loader Fixup Placeholders

Fix CODE 0 restored-source reference records so metadata/routing CODE 0 does not
receive a Segment Loader fixup placeholder unless there is explicit evidence for
one.

Required outcome:

- CODE 0 keeps routing/metadata source references.
- CODE 0 does not emit `segment_loader_fixup_placeholder` for the normal
  metadata/routing packet.
- Nonzero CODE resources keep span-specific Segment Loader placeholders where
  evidence remains deferred.
- Tests cover CODE 0 and nonzero CODE behavior, and the MPW `Asm` artifact
  reflects the corrected records.

Completed corrected CODE 0 reference behavior:

- CODE 0 restored-source records now contain the validated `code0_routing_table`
  reference and deferred A5/world context only; the normal metadata/routing
  packet no longer receives a `segment_loader_fixup_placeholder`.
- Nonzero CODE resources still keep span-specific deferred
  `segment_loader_fixup_placeholder` records with resource id, byte space,
  source offset/range, deferred fact state, provenance, and source visibility.
- Artifact and project/API tests now fail if CODE 0 regresses to broad
  fixup-placeholder output or if an absent CODE 0 jump-table span is promoted
  to a validated dispatch reference.

### 023-011: Source-First `Asm.s` Artifact Contract

Move the Mac target artifact from report-first to source-first output.

Required outcome:

- `Asm.s` starts with a short identity/header block followed by actual restored
  source or source placeholder sections.
- Broad file/resource inventory, coverage tables, verifier dumps, and per-CODE
  evidence records move behind the source body or to a sidecar artifact.
- Tests fail if the first useful lines of `Asm.s` are dominated by report
  comments instead of source rows.
- No C-owned evidence is deleted; only its artifact placement changes unless a
  sidecar replacement is added.

Completed state:

- `Asm.s` uses a compact identity header, then the selected CODE restored-source
  context and source listing.
- Broad file/resource inventory, CODE coverage, CODE details, non-CODE
  placeholders, and unsupported-runtime notes remain in `Asm.s` after the source
  body under `; Supporting evidence follows after the source body.`
- Artifact tests assert this ordering so report-first output cannot silently
  return.

### 023-012: All-CODE Source Body Sections

Render every executable CODE resource as a visible source-body section.

Required outcome:

- Every CODE resource in the committed MPW `Asm` fixture has a stable source
  section label or typed placeholder section in `Asm.s`.
- Fully covered CODE resources render their restored-source rows.
- Deferred or partial CODE resources render conservative source-visible
  placeholder/data rows with resource id, status, reason, and byte span where
  known.
- The artifact no longer depends on a selected-CODE-only body to represent the
  program.
- Tests compare CODE resource inventory against source-body section labels so a
  CODE resource cannot silently disappear from visible output.

Completed state:

- `Asm.s` now renders a source-body section for every current MPW `Asm` CODE
  resource before the supporting-evidence report.
- Every CODE source section renders exact payload bytes as labelled `dc.b` rows
  for each C-owned layout range. Candidate/deferred semantic claims remain
  candidate/deferred, but non-selected CODE resources are no longer preview-only
  placeholders.
- Artifact tests compare the C-backed CODE inventory against source-body section
  identities and fail if the artifact regresses to selected-CODE-only output.

### 023-013: CODE 0 Structured Source Context

Render CODE 0 routing as structured source context rather than a leading report
table.

Required outcome:

- CODE 0 has a source-body data section with labels for parsed routing/jump-table
  structures.
- Validated CODE 0 dispatch references link to the corresponding CODE section
  labels where evidence exists.
- Resources with absent jump-table spans remain unlinked/deferred and are not
  promoted to accepted dispatch targets.
- Tests cover CODE 0 table rendering, linked CODE 27 behavior, and absent-link
  behavior for CODE resources such as CODE 1.

Completed state:

- `Asm.s` labels every CODE source section and renders CODE 0 application
  metadata/jump-table labels in the source body.
- The parsed CODE 0 row links to `macos_code_CODE_27` only as candidate target
  interpretation while keeping the jump-table layout fact validated.
- CODE 1 remains absent from accepted CODE 0 dispatch links. CODE 0 row bytes are
  now source-visible from the C-backed CODE payload extractor, closing the former
  raw-entry byte gap without promoting candidate target semantics.

### 023-014: CODE 1 Entry, Stub, And Residual Span Presentation

Use the known CODE resource layout to make CODE 1 visibly understandable.

Required outcome:

- The far-model segment header is separated from executable body output and not
  presented as orphan code.
- The current leading CODE 1 stub is labelled/classified using accepted
  structure where possible, or marked as a precise deferred entry/stub
  placeholder where evidence is still insufficient.
- Residual candidate bytes after the stub are rendered under a clear
  code/data/unknown/deferred ownership label instead of a vague orphan label.
- Tests assert the CODE 1 section contains the real code start after metadata,
  clear labels, and no misleading orphan terminology.

Completed state:

- `Asm.s` labels the CODE 1 far-model header as accepted metadata
  `payload[0..40)` and renders exact byte-real source rows instead of depending
  on the broad selected executable decoder listing.
- The candidate entry/stub span is explicit as `payload[40..62)` /
  `selected_code_bytes[0..22)`, with the missing accepted byte-entry proof named
  directly.
- The remaining CODE 1 body is labelled `payload[62..29024)` as candidate
  executable body with Segment Loader relocation/fixup interpretation still
  deferred, and artifact tests reject vague orphan-code wording.

### 023-015: Mac Source Artifact Web/API Parity

Make the web/API source views follow the same source-first, all-CODE contract as
`Asm.s`.

Required outcome:

- API/web payloads expose the source-body ordering and per-CODE section identity
  used by the artifact.
- Source navigation can list all CODE source sections and distinguish full,
  partial, and placeholder sections.
- Broad evidence remains available as supporting context, but not as the primary
  source view.
- Tests cover artifact/API/web parity for section count, section ids, and
  deferred/source-visible status.

### 023-016: Visible Mac Source Presentation Closeout

Close 023 only after the committed MPW `Asm.s` artifact shows visible reversing
improvement and passes the 023-017 source-quality gate.

Required outcome:

- Proposal 023 records the corrected final state and no longer claims success
  merely from evidence/report availability.
- The generated `Asm.s` first screen is source-first and contains real Mac CODE
  source/placeholder sections.
- Every CODE resource is visibly represented in source body output.
- CODE 0 context and CODE 1 entry/stub/residual-span presentation are covered by
  tests.
- 023-017 proves the source is not merely rearranged report output: reachable
  code, labels, xrefs, byte ownership, and residual unknown accounting are
  explicitly checked.
- Platform executable validate/coverage, focused Mac tests, and shared
  precommit proof pass without weakening Amiga/Atari gates.

### 023-017: Source Quality Analysis Gates

Add gates that prevent 023 from closing on tidy but shallow source output.

Required outcome:

- The worker regenerates the committed MPW `Asm.s` artifact and records the
  visible before/after improvement in Proposal 023.
- Every CODE resource has a per-byte or range-level ownership summary:
  metadata, code, data, fixup/relocation, padding, placeholder, or unknown. No
  vague orphan bucket is allowed.
- Reachable code analysis uses CODE 0, segment headers, branch targets,
  JSR/BSR targets, jump tables, and known entry/stub patterns as evidence where
  available.
- Bytes not proven as code do not render as plausible instructions. They render
  as data, unknown, or source-visible placeholders until analysis supports code.
- Stable labels exist for CODE sections, entrypoints, jump-table targets, branch
  targets, data references, and placeholders where evidence supports them.
- Source output splits code/data/metadata/residual spans clearly inside each
  CODE resource instead of rendering one flat blob.
- Any remaining unknown/deferred span names its exact byte range, reason,
  attempted local-docs/KB rule, and next required implementation.
- Closeout includes a source-first review checklist over the actual generated
  `Asm.s`: first screen, all CODE sections, CODE 0, CODE 1, residual spans,
  labels, xrefs, and absence of report spam.

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
- 023-009 and 023-010 reopen the post-closeout reference accuracy findings.
  They should be done together or in that order because both touch the same
  C-owned Mac source reference record builder.
- 023-011 reopens the visible artifact quality track and starts immediately.
- 023-012 follows 023-011.
- 023-013 may run after 023-011, but its final artifact placement should be
  reconciled with 023-012.
- 023-014 follows 023-011 and may run in parallel with 023-012/023-013 if it
  does not change section identity.
- 023-015 follows 023-012 through 023-014.
- 023-017 follows 023-012 through 023-014 and may run alongside 023-015.
- 023-016 closes the reopened proposal after 023-011 through 023-015 and
  023-017 complete.

## Non-Goals

- Classic Mac OS resource-fork round-trip.
- Broad non-CODE resource decoding unrelated to executable source.
- Promoting Mac byte-entry, Segment Loader, A5, or resource facts beyond their
  evidence status.
- Treating evidence/report visibility as a substitute for source presentation.
- 017 cascade/evidence-review protocol work.
- UI redesign beyond making existing source evidence visible.
