# Proposal 023: Classic Mac OS Source Presentation

Status: complete

Current semantic closeout state:

- The committed MPW Tools `Asm.s` artifact is source-first: a compact identity
  header is followed by visible CODE source-body sections before broad
  supporting evidence.
- Every current CODE resource has a source-body section with stable section
  identity, C-owned restored-source evidence, range-level ownership, and a
  shared semantic source model exposed through API, artifact, and web views.
- CODE 0 renders structured application/jump-table context with generated
  target links only where evidence supports them. Nonzero CODE resources render
  supported executable body spans as semantic source rows: decoded M68K
  instructions, generated labels/xrefs, data/directive rows, and precise
  typed residuals.
- `binary_container_view.source_body_sections` and
  `binary_container_view.source_quality_gate` are shared API/web/artifact
  surfaces; the web view consumes those surfaces rather than inventing status.
- The source-quality gate now reaches
  `semantic_source_complete_for_known_bounds`. Current closeout metrics for the
  MPW Tools `Asm` fixture are 28 source sections, 28 semantic source models,
  315 instruction rows, 11768 data rows, 73 generated labels, and 88 generated
  xrefs.
- Mac byte-entry, Segment Loader relocation/fixup decoding, A5 lifetime
  semantics, non-CODE payload semantics, source-to-CODE mapping, and
  resource-fork round trip remain candidate/deferred/unsupported exactly as
  recorded by Proposal 018/024 evidence. Proposal 023 does not promote them.

Failed closeout review:

- The previous closeout treated byte-real source visibility as sufficient source
  presentation. That is not the intended outcome. A reverser still sees mostly
  `dc.b` rows, including CODE 1 body bytes, rather than analysed M68K source.
- `passed_with_deferred_semantics` is not a passing semantic source-quality
  state. It proves conservative accounting and absence of fake disassembly, not
  useful restored source.
- The source-quality gate is currently too shallow: it can pass when
  `renders_only_byte_real_rows` is true, reachable-code evidence is only a
  candidate marker, and labels exist without instruction/data/xref recovery.
- Proposal 023 remains active until the Mac fixture renders real CODE source
  where the bytes and local platform documentation support it, with residual
  byte-real placeholders only for precise spans that were actually attempted and
  still cannot be safely classified.

Scope distinction:

- 023 is responsible for platform-correct disassembled and partially analysed
  assembly output: CODE resource identity, segment/header boundaries, CODE 0
  routing where supported, instruction decoding, flow labels, xrefs,
  metadata/data/residual splits, trap/platform annotations where known, and
  precise placeholders for unsupported loader/runtime extensions.
- 023 is not responsible for intelligence-driven reversing conclusions such as
  meaningful routine names, original source symbol names, high-level routine
  purpose, tool-specific semantic labels, or global variable meanings that
  require human/LLM interpretation.
- Lack of human-quality names is not a blocker. The required baseline is the
  same kind of source presentation expected from Amiga/Atari targets before
  manual reversing: decoded assembly, stable generated labels, xrefs, typed
  ranges, and visible platform context.

Local documentation support:

- This is not blocked on a broad research pass. Local docs already establish
  that Classic Mac OS application code is stored in segmented `CODE` resources,
  that CODE 0 contains jump-table/application metadata, that CODE 1 is the main
  segment convention, and that MPW `Asm` owns 28 CODE resources in its resource
  fork.
- `docs/macos-file-structure.md` records the intended path as resource-fork
  CODE resources to segment metadata to M68K disassembly input.
- `docs/macos-initial-analysis-research.md` records MPW/Inside Macintosh
  evidence for CODE 0, CODE 1/Main, segment-name-to-CODE-resource convention,
  and the current MPW `Asm` expectation that CODE 1 is a 68K disassembly range.
- `docs/proposals/024-classic-mac-os-segment-loader-fixups.md` records the
  documented near/far CODE segment headers. For the current MPW fixture, many
  nonzero CODE resources use the documented far-model 40-byte header, code
  follows that header, and documented relocation offsets are zero. That means
  relocation/fixup decoding is not a prerequisite for the first semantic
  disassembly slice.

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

The example is not optional decoration. The closeout target is that CODE bytes
which are reachable or otherwise classifiable as M68K instructions render as
instructions with labels and references. Byte-real `dc.b` rows remain valid for
metadata, tables, padding, unknown residual spans, and unsupported extension
payloads, but they are not an acceptable final rendering for executable CODE
body spans that the local Mac executable structure and M68K decoder can analyse.

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
- CODE body bytes that are reachable from CODE 0 routing, segment headers,
  known entry/stub patterns, branch targets, JSR/BSR targets, jump tables, or
  decoder-discovered fallthrough render as M68K instructions unless a precise
  documented reason prevents classification;
- CODE/data/metadata/relocation/padding/unknown ownership is split inside each
  CODE resource; a whole-resource byte dump is not a completed source body for
  any resource with executable evidence;
- branch and call targets discovered by the disassembler become stable labels
  and xrefs in the source model and rendered artifact;
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

Semantic closeout gate:

- `passed_with_deferred_semantics` is a baseline state, not a closeout state.
- A closeout gate must fail if all executable CODE rows are byte-real data rows.
- A closeout gate must distinguish `byte_real_complete`,
  `semantic_source_partial`, and `semantic_source_complete_for_known_bounds`.
- `semantic_source_complete_for_known_bounds` requires decoded instructions,
  stable generated labels, xrefs, typed metadata/data/residual rows, and known
  platform/trap annotations where mechanically available. It does not require
  human semantic routine names or original source symbols.
- Any remaining deferred span must name the attempted evidence path: CODE 0
  routing, segment header, M68K decode, branch/call target following,
  relocation/fixup interpretation, A5 context, or local documentation gap.
- The proposal may close only at `semantic_source_complete_for_known_bounds`:
  all currently supported executable evidence has been consumed into source, and
  residual byte-real spans are narrow, typed, and justified.

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

For 023-018 through 023-022, the expected starting assumption is that local docs
are sufficient to proceed with semantic source rendering of currently supported
CODE body spans. If the implementation finds a narrow missing rule, the worker
must name the exact rule, cite the local search performed, update the relevant
proposal/issue, and still continue with the supported subset. A broad "missing
Mac documentation" blocker is not acceptable.

The worker must not confuse automated source presentation with completed human
reversing. Stable generated labels and mechanical xrefs are valid outputs for
023. Meaningful routine names, original source symbols, and intent comments are
later reversing work unless directly proven by source symbols, resource names,
platform ABI/trap knowledge, or accepted manual evidence.

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

Completed state:

- Project/API payloads expose `binary_container_view.source_body_sections` as
  the shared ordered section model used by both `Asm.s` and the web view.
- Web Mac source/container views list all CODE source sections from that shared
  model and distinguish selected/full, partial, and placeholder/deferred
  sections without synthesizing a separate status surface.
- Supporting CODE details, previews, non-CODE placeholders, and resource
  evidence remain available after the source-section view as supporting context.
- UI-only refinements remain non-blocking; source correctness depends on the
  shared source section model and the 023-017 quality gate.

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

Completed state:

- Proposal 023 is closed as visible Classic Mac OS source presentation for the
  committed MPW Tools `Asm` fixture.
- `Asm.s` starts with useful source after a compact header, every CODE resource
  is represented in the source body, CODE 0/CODE 1 structure is visible, and the
  023-017 quality gate is rendered before supporting evidence.
- Remaining semantic gaps are explicit candidate/deferred residuals with exact
  byte ranges and next implementation steps. No Mac round-trip or unsupported
  semantic promotion is claimed.
- Final proof passed: platform executable validate; platform executable
  coverage with current Mac/Amiga/Atari backends; focused Mac backend/project/
  artifact/web/source tests; C precommit; and `git diff --check`.

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

Completed state:

- Project/API payloads expose `binary_container_view.source_quality_gate`
  (`macos_source_quality_gate_v1`) and the committed MPW `Asm.s` renders the
  same checklist before supporting evidence.
- The current gate status is `passed_with_deferred_semantics`: source-first
  ordering, all CODE section visibility, range ownership coverage, stable
  labels, explicit candidate/deferred residual spans, and no fake instruction
  rendering are checked.
- The gate explicitly does not claim accepted byte-entry proof, decoded Segment
  Loader relocation/fixup semantics, A5 lifetime proof, or resource-fork
  round-trip support.
- CODE 1 remains candidate-only for entry/stub/body semantics. The improvement
  is that this state is now enforced and rendered as exact residual ranges with
  next implementation steps, not hidden behind plausible disassembly or broad
  orphan wording.

Post-review correction:

- This completed gate is retained only as a byte-real baseline gate. It must not
  be used to close 023 because it explicitly permits deferred executable
  semantics and can pass while the artifact still renders CODE bodies as `dc.b`.

### 023-018: Reopen Semantic Source Gate

Replace the byte-real closeout interpretation with an honest semantic source
quality gate.

Required outcome:

- Proposal 023 remains active until semantic source output exists for supported
  CODE body spans.
- `passed_with_deferred_semantics` is renamed or reclassified so no caller,
  artifact, proposal, or issue can treat it as final source-quality success.
- The gate fails semantic closeout when executable CODE body spans render only
  as byte-real `dc.b` rows.
- Gate output reports separate statuses for byte preservation, source ordering,
  semantic disassembly progress, xref/label recovery, and residual unknowns.
- Gate output distinguishes generated local labels/xrefs from human semantic
  names so lack of meaningful names cannot block semantic source closeout.
- Tests prove a byte-real-only CODE body cannot close 023.
- Gate text records that local docs already support the first semantic source
  slice; lack of Segment Loader fixup/A5 lifetime proof is not a blocker for
  disassembling current CODE body bytes.

### 023-019: Mac CODE Semantic Disassembly Model

Add the C-owned model needed to render Mac CODE payload bytes as analysed M68K
source rows where the bytes are executable.

Required outcome:

- The native Mac CODE path feeds classifiable CODE body byte spans into the
  shared M68K disassembly machinery without raw-file compatibility transport.
- The starting implementation scope includes nonzero CODE resources whose
  documented segment header identifies a code body: far-model code begins after
  the 40-byte header, near-model code begins after the 4-byte header.
- Far-model headers, CODE 0 metadata, and other non-instruction ranges remain
  typed data/metadata, not instructions.
- Current-fixture zero relocation offsets mean Segment Loader fixup decoding is
  not required before disassembling the supported CODE body bytes.
- Valid instruction rows carry CODE resource identity, payload offset, rendered
  text, size, bytes, flow classification, and source provenance.
- Generated labels are acceptable and expected for auto-discovered entrypoints,
  branch targets, call targets, data references, and residual placeholders.
- Invalid or unsupported spans become typed residual rows with exact byte ranges
  and reason.
- Tests cover CODE 1 entry/stub bytes rendering as instructions instead of
  `dc.b`, while header bytes remain metadata/data.

Completion state:

- Complete for the initial CODE 1 slice. `source_body_sections[].semantic_source`
  now carries `macos_code_semantic_source_v1` rows from the native Mac CODE C
  extractor through the shared M68K listing artifact path.
- CODE 1 far-model body rows begin at payload offset 40 and render decoded
  instructions plus generated labels/xrefs; the far-model header remains
  metadata/data.
- This does not close Proposal 023. CODE 0 routing labels, broader nonzero CODE
  flow, typed residual/data splitting, and final semantic-source closeout remain
  under 023-020 through 023-022.

### 023-020: CODE 0 Routing Seeds And Source Labels

Use documented CODE 0 and segment map structure to seed executable source
analysis instead of leaving routing as comments.

Required outcome:

- Parsed CODE 0 routing/jump-table evidence creates source labels and candidate
  entry seeds only where a real table/span exists.
- Labels created from CODE 0 evidence may be stable generated names. Human
  segment/routine names are not required unless the resource name or source
  evidence directly supports them.
- Local docs support CODE 0 as jump-table/application metadata and CODE 1 as
  the main segment convention; use that as the implementation boundary rather
  than treating CODE 0 routing as unknown.
- Absent spans such as `jt_first=65535 jt_count=0` remain unlinked/deferred and
  do not create fake dispatch xrefs.
- Valid CODE 0 links are visible in `Asm.s`, API, and web source sections as
  labels/xrefs, not only report prose.
- Tests cover linked CODE resources, absent-link resources, and the generated
  artifact labels.

Completion state:

- Complete. CODE 0 routing now emits generated source xref records from parsed
  jump-table entries to target CODE body payload offsets only when the target has
  a real executable span.
- The API exposes `generated_routing_xrefs` on CODE 0 and
  `incoming_code0_xrefs` on linked target sections; `Asm.s` and the web source
  panel render the same labels/xrefs.
- Current MPW evidence links CODE 0 entry 0 to CODE 27 payload offset 204.
  Absent or non-resolvable entries remain unlinked and do not become accepted
  dispatch claims.

### 023-021: Nonzero CODE Flow And Residual Classification

Follow executable code inside nonzero CODE resources and split source rows into
instructions, data/tables, metadata, and residual placeholders.

Required outcome:

- CODE 1 no longer stops at byte-real entry/stub/body rows when the M68K decoder
  can decode the reachable bytes.
- CODE 1 is the first required real fixture proof because local docs and current
  parser output identify it as `Main` with a far-model header and a code body
  after payload offset 40.
- Branch, call, jump, fallthrough, and return behaviour create stable labels and
  xrefs in the restored source model.
- Data discovered from instruction references is rendered as data rows, not
  undifferentiated candidate code.
- Trap/toolbox calls are annotated where the opcode/platform knowledge is
  mechanically available; unknown calls remain ordinary decoded instructions
  with generated labels/xrefs.
- Each nonzero CODE resource records the attempted entry evidence and decode
  result, even when no accepted entry exists.
- Tests prove the artifact contains real instruction rows and recovered labels
  for at least the currently supported CODE 1 path, and that unsupported spans
  remain precise residuals.

Completion state:

- Complete for current parser-supported nonzero CODE spans. Semantic decoding now
  feeds all nonzero CODE resources with classifiable executable body ranges
  through the shared M68K listing artifact path.
- CODE 1 and other supported CODE resources render instruction rows,
  generated labels/xrefs, and data/directive rows instead of broad byte-real
  `dc.b` bodies.
- Decoded executable ranges no longer remain as broad candidate residuals.
  Remaining residuals are exact typed semantic gaps or non-code data/metadata
  ranges with candidate/deferred evidence.
- The source-quality gate now reaches
  `semantic_source_complete_for_known_bounds`; 023-022 owns the final closeout
  audit and deletion/promotion work.

### 023-022: Semantic Source Presentation Closeout

Close 023 only after the generated Mac source is visibly useful to a reverser,
not merely byte-accounted.

Required outcome:

- `Asm.s` contains source-first Mac CODE sections with real instruction/data
  rows for all supported executable spans.
- The source-quality gate reaches `semantic_source_complete_for_known_bounds`.
- The closeout explicitly distinguishes mechanical platform/auto-analysis output
  from future human/LLM reversing names and comments.
- The proposal records before/after evidence showing which CODE resources moved
  from byte-real rows to semantic instruction/data/source rows.
- Remaining placeholders are narrow, typed, justified, and linked to the next
  missing implementation.
- Closeout distinguishes real non-blocking gaps from completed work: source
  symbol recovery, full source-to-CODE mapping, Segment Loader fixup decoding
  for fixtures with nonzero relocation streams, A5 lifetime/global-base proof,
  and resource-fork round-trip remain out of this closeout unless implemented
  by supporting work.
- Platform executable validate/coverage, focused Mac tests, shared precommit,
  and artifact/API/web parity tests pass without weakening Amiga/Atari gates.

Completed state:

- `Asm.s` now exposes source-first CODE sections for all 28 CODE resources.
  CODE 0 remains metadata/routing source context; every nonzero CODE resource
  with supported executable evidence has a `macos_code_semantic_source_v1`
  model with decoded rows instead of relying on byte-real accounting alone.
- Current source-quality gate status is
  `semantic_source_complete_for_known_bounds`. Components are
  `byte_real_complete`, `source_first`,
  `semantic_instruction_rows_present`,
  `generated_labels_and_xrefs_present`, and `explicit` residual accounting.
- Before this semantic closeout, the reopened gate treated
  `passed_with_deferred_semantics` as only a byte-real baseline and CODE bodies
  still rendered mostly as `dc.b`. After 023-019 through 023-021, CODE 1 and
  other supported nonzero CODE spans feed through the shared M68K listing path:
  current MPW output has 315 instruction rows, 11768 data rows, 73 generated
  labels, and 88 generated xrefs across 28 semantic source models.
- Remaining gaps are non-blocking for 023 because they are outside semantic
  source presentation: original source symbol recovery, full source-to-CODE
  mapping, Segment Loader relocation/fixup semantics, A5 lifetime/global-base
  proof, non-CODE payload semantics, and resource-fork round-trip.
- Final proof passed: platform executable validate; platform executable
  coverage with current Mac/Amiga/Atari backends (`invalid: 0`); focused Mac
  backend/project/artifact/web tests (`58 passed`); shared precommit
  (`style`, `dead_code`, `unit`, `integration`, and `explicit` all OK); and
  `git diff --check` with only line-ending warnings.

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
- 023-018 reopens the failed semantic closeout and must happen before further
  closeout claims.
- 023-019 follows 023-018.
- 023-020 may run after 023-018 and should be reconciled with 023-019 before
  023-021.
- 023-021 follows 023-019 and 023-020.
- 023-022 closes the proposal only after 023-018 through 023-021 complete.

## Non-Goals

- Classic Mac OS resource-fork round-trip.
- Broad non-CODE resource decoding unrelated to executable source.
- Promoting Mac byte-entry, Segment Loader, A5, or resource facts beyond their
  evidence status.
- Treating evidence/report visibility as a substitute for source presentation.
- 017 cascade/evidence-review protocol work.
- UI redesign beyond making existing source evidence visible.
