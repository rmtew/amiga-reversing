# Proposal 046: Canonical memory regions and layout export

Status: **First delivery in progress: M0–M2 partial; M3 runtime checks active; M4 not delivered.**
Audit baseline: master `a814a2a47bbd87abb6d06e11d8b69908e8dfd9d5`, 2026-10-23.

## Implementation checkpoint (2026-10-23)

The independent-cursor inventory probe found a concrete initialization omission:
the sprite consumer fetched two more WORDs after the modeled 136 bytes. Across
two complete inventory frames, original `$653F8/$653FA` supplied `$A000/$4000`,
while moved `$E0088/$E008A` supplied zero. Three equal stopped buffer snapshots
had not covered that consumer footprint. The retained
[negative receipt](../../runtime/observations/pandora-cursor-inventory-boundary.json)
records this failure. The bounded correction models a 140-byte parent and a
separate four-byte loader-file seed from `$453F8`; guest startup copying is implemented. The corrected 28-phase pair completes
with matching phase/controller clocks and ordered inventory DMA, but strict
comparison refuses an eight-CCK natural HAND-boundary difference. The
[seed receipt](../../runtime/observations/pandora-cursor-loader-seed.json) records
298 focused passing tests and current exact verification; full runtime/output
qualification remains open. Deliberate original reliance versus
accidental control bytes is unknown. No surrounding data, font layout or other
initial cursor bytes are classified by this observation.


[Real profile build evidence](../../runtime/observations/pandora-canonical-layout-builds.json)
records five accepted API definitions and normal-export C/vasm agreement for
`pandora_original_ecs1m`, `pandora_image_80000_ecs1m` and
`pandora_cursor_e0000_ecs1m`. The original profile matches all 376,832 original
bytes. The independent cursor profile changes only four evidenced address
operands from the image-only profile. All 126 canonical asset byte intervals
remain unchanged; the explicit 256-byte packaging threshold emits 86 files and
retains 40 smaller intervals inline. Source-export/ bootstrap checks pass 38
tests. Current-subject default C/vasm verification is exact, receipt
`168dfee696e73907cbb7e1f2d37a1d433f9e0f50854f32f7d2884d4e320b38c5`.

The normal image payload differs from the prior patched experiment at one byte:
the existing bank-51 stored-mask pointer at source `$4C81A` now resolves from
`$55C90` to `$C5C90`. Its existing canonical absolute-reference fact and consumer
`$6F9A` explain this change; original activation is still conditional. Do not
silently revert it or reuse old runtime qualification solely by payload identity.
Fresh runtime/output checks are active, not accepted as complete. Native plan
contents now accompany their hash through the same export service so runtime
adapters consume canonical placements rather than reconstruct a Python model.
Full exports took 170.15/187.84/179.23 seconds in these single observations;
layout-only selection still rebuilds analysis. Frozen-plan reuse, runtime gates
and legacy-patcher removal remain open obligations. Image-only success cannot
close the independent workspace gate.

The normal image payload has now completed the uninterrupted cold 576-phase
saved-Earth route at HP49/frame14351, with all 509 controller calls acknowledged,
the full copied prefix read back at `$80000`, and both loss counters zero. Its
normal runtime adapter consumes the native plan and guards old CPU data ranges;
the old symbolic-patching builder is not called. 41 runner/export/ending/PCM
tests pass. This is gameplay qualification only: new matched output comparison,
independent cursor execution/DMA observation, legacy-builder retirement and
frozen-plan reuse are still open. Existing original output captures may be reused
only with their exact binary/emulator/ROM/profile/input and clock identities;
the corrected normal image is a different executable and is tested afresh.

The thin layout-selection adapters now forward the same canonical `layout_id`
through HTTP, restoration CLI, real MCP stdio and the existing palette parameter
editor. Unknown-layout refusals are not promoted to download/success. The isolated
MCP SDK 2.3.0 suite passes all nine tests; the UI handler's forwarding/refusal
paths execute under Node.js. This is service wiring, not browser E2E or runtime
qualification, and does not discharge frozen-plan reuse or patcher retirement.

### Earlier mechanism batches (historical)

The following results retain their per-batch limits; their then-pending steps
are superseded by the current checkpoint above.

[Canonical adoption evidence](../../runtime/observations/pandora-canonical-layout-adoption.json)
records 25 API-applied and reviewed facts: copied image, cursor workspace and
children, display roles, and twelve exact receptacle pointer fields. Explicit
runtime reference points retain their address domain without inferring pointee
extents. All 376,832 original bytes match through C and independent vasm
(receipt `c799cb96d22106b9cb3f47c5759c59c13fcce885c056b7696a1599994a7f2ff9`).
All 126 asset identities and 3,772 existing labels are preserved. Seven missing
SDK companions were restored from the identical tracked include set so the
owned package is reproducible; its ownership guard remains enabled.

The reviewed exporter boundary cases now refuse split materialized views and
typed extents partially intersecting a moved region, rather than silently
emitting a stale ORG/address. The focused final layout/domain suite passes 72
tests (four deselected); the adoption suite passed 125 (four deselected).
Canonical bootstrap variants, target layout profiles and independent-block
qualification remain open. Cursor control initialization/DMA continuation and
the existing snapshot/palette containment must be resolved for that admission.
These facts do not classify previously unknown bytes or qualify an alternate run.

The subsequent bootstrap slice adds one canonical, input-identity-bound retained
prefix-copy contract and layout references to it through the same catalog/MAL
path. Native and disjoint-forward variants retain the initializer; the latter
permutates the contracted two-byte instruction's address-register operands using
the generated encoder in the frozen plan. Input hash, copied image/helper views,
staging bounds, register shape and instruction admission have explicit refusal
tests. A suppressed helper source ORG is distinguished from the actual copied
helper. Synthetic native/variant fixtures assemble independently with vasm;
336 focused integration tests pass (four deselected). No target profile, moved
workspace or new gameplay/output result is qualified by this mechanism batch.
See [the interface contract](../restoration-interfaces.md#retained-bootstrap-layout-contracts).

[Baseline/index evidence](../../runtime/observations/pandora-memory-layout-baseline.json)
records cold native artifact/package measurements and selection of the paired
cursor-sprite workspace for bounded constraint analysis. The first M1 mechanism
indexes existing materialized views in the native artifact; it removes the
per-query view scan and per-byte mapped-span scan while preserving conflicting
and valid aliases. 89 focused tests pass; the full nine-region projection and
native source package are unchanged. Span lookup takes two operations for 16,
349,040 and 8,388,608 bytes; 128/256/512 disjoint intervals take 8/9/10 operations.
The two single artifact timings (202.04 s and 169.49 s) do not establish an
attributable speedup. The region-by-instruction scan remains.

This is not first-delivery closure. Cursor control initialization/DMA continuation
and placement constraints remain under review; canonical layout selection,
base-plus-offset export, bootstrap migration and independent movement are still
pending. No new emulator run or source-layout transformation is in this batch.

The M1 placement batch adds optional region kind/parent facts, identity-preserving MAL
updates, versioned fixed-layout definitions and native placement resolution,
exposed by the existing shared query service. A valid placement explicitly retains
`export_ready: false`; no renderer/bootstrap/reference claim follows. Original
records remain compatible. Both workspace and display participate in this model;
there is no alternate Python placement authority. The legacy builder refuses
extended hierarchical definitions until the normal layout export owns them.
225 focused native/schema/history/catalog/service tests pass. With socket access,
the existing transport suite reports seven passes and one optional-MCP-SDK skip.
The interface tests require socket access; optional MCP SDK absence remains an
explicit transport-validation gap, not a passing skip. Pandora adoption and
M2–M4 acceptance are still pending.

The subsequent source-preview batch selects canonical layouts through the normal
native exporter. Runtime equates, DMA symbols and runtime ORGs use base/offset
expressions; scalar values and source coordinates retain their domains. Synthetic
original/moved fixtures assemble independently with vasm to the expected full
bytes, including an independently moved workspace. This is mechanism evidence,
not Pandora gameplay acceptance. Exports bind the native placement-plan hash and
remain explicitly `source_only_unqualified`. Package export now constructs one
owned native artifact for source and assets, replacing duplicate analysis rather
than adding a cache. Two reviewed importer omissions (mixed/scalar layout entries
and truncated numeric tokens) are fixed with native malformed-input regressions.
335 focused tests pass across layout/region/history, source/export/package and
service operations. No new Pandora payload or emulator result is claimed by this
batch; bootstrap/reference adoption and M2–M4 acceptance remain open.

## Decision and scope

Extend the existing native address-domain, runtime-view and render-plan model
into one canonical layout model. A region describes an object and its storage
requirements; a layout assigns placements; typed references connect source
sites to objects. The normal exporter renders a validated, frozen plan. It must
not infer pointers from numbers or patch rendered strings to make a layout work.

The first delivery models image/code, workspace and display regions canonically,
renders their supported addresses as base-plus-offset relationships, and uses the
normal source-package path for the exact original layout, the demonstrated
`$80000` image layout, and an additional layout moving at least one independently
placed workspace or display block. Both workspace and display kinds must be
represented naturally; physically moving both is not required. Reproducing the
image experiment alone is an internal validation step, not completed delivery.
Block selection requires actual reference, alias, lifetime and DMA constraints;
unknowns restrict specific blocks rather than defer the entire capability.
Runtime allocation and an OS-hosted exporter remain separate, gated work, not
consequences of changing ORG. No universal portability, arbitrary-base safety,
native C port, semantic completion percentage or delivery ETA is claimed.

This document is an architecture/roadmap, not another target fact database.
Canonical facts, Manual Action Log (MAL) and Decision Journal (DJ) continue to
own interpretation and review. The existing working exports and private runtime
evidence remain available during migration. Replacement has explicit deletion
gates; permanent competing production paths are not the intended outcome.

## What exists, and what the experiment actually established

The audit examined the following implementation, not just earlier proposals:

| Existing owner / concrete seam | Implemented scope and limitation | Disposition |
| --- | --- | --- |
| `src/m68k_ir.h`: `M68kMemoryRegionIR`, `M68kRuntimeViewIR`, `M68kRuntimeViewRelationshipIR` | Stable region identity and original extent; mapped/runtime-only distinction; storage-to-runtime materialization. Region array is currently bounded at 16, with persistent CPU RAM and a DMA flag, not a hierarchy or multi-region placement model. | Extend these native identities and projections; do not introduce a parallel Python region graph. Replace fixed-capacity storage when measured use requires it, with explicit limits meanwhile. |
| `amiga_reversing/disasm/memory_regions.py`: `validate_region`, `relocation_plan`, `build_derived_artifact` | Exact supported fields; persistent CPU RAM only; native plan delegation; fixed-width byte rewrite ledger and immutable local artifact. | Retain command/service boundary and strict admission. Migrate definitions with versioned defaults; consolidate layout materialization rather than adding another patch writer. |
| `src/m68k_memory_region.inc`: `memory_region_append_facts`, `platform_file_facts_v2_listing_artifact_memory_region_plan_json_alloc` | Accepted instruction accesses, bounded proofs, overlaps, single-region placement; A500 Chip/Slow address checks and eight-byte Exec lease assumptions. Overlapping source regions refuse a single move. | Reuse proof obligations and diagnostics. Move profile-specific placement/reservation policy out of the generic planner. Retire the single-region planning implementation after its supported cases use the shared layout planner. |
| `src/m68k_memory_region_addresses.inc`: `mr_mapped_span`, `mr_source_address`, `mr_operand_address` | Canonical mapping/provenance, not source-text matching. Contiguity currently checks each byte; region projection scans instructions per region. | Preserve meaning, replace repeated scans with shared interval/reference indexes and equivalence tests. |
| `src/m68k_memory_region_proof.inc`, `src/m68k_memory_pointer_liveness.inc` | Bounded address/frame/alias reasoning with explicit unsupported paths; not whole-program or IRQ/timing closure. | Reuse as evidence providers. Never make their current all-path proof a prerequisite for merely reproducing an accurately restricted original-layout export. Never interpret a refusal as evidence of unused memory. |
| `amiga_reversing/disasm/target_metadata.py`, `manual_actions.py` | Pointer field domains/groups, target equate domains/extents, operand presentations; revision-checked region create/remove history. Existing `source`, `runtime` and `app` uses must retain their actual semantics. | Extend existing commands/schema and replay; no direct history edits or replacement `entities.jsonl`. Add identity-preserving updates rather than remove/recreate churn. |
| `src/m68k_ir.h`: `M68kAnalysisAbstractRegion`; `target_metadata.py`: `AbstractRegionMetadata` | Named non-overlapping source-section ranges used by callable summary effects, distinct from runtime placement regions. Target equate extents and app/record owners also describe different facets of storage. | Link summary/owner ranges to canonical storage identities through their source/view mapping; do not promote an effect range to an allocation or discard its effect semantics. Retire duplicated extent authority only after summary references retain identity and all bounds checks agree. |
| `src/m68k_render_plan.c`, `src/m68k_render_plan.h`; [Proposal 037](037-render-planning-and-symbolic-source-closure.md) | Planned instructions, expressions and declarations; declaration/header closure has remaining work. | One resolver for operands, fields, tables, declarations and packages. Close the affected declaration cases here, not a second layout-specific renderer. |
| `src/m68k_source_package.c`, `src/m68k_source_export.h`; `amiga_reversing/disasm/source_export.py`, `source_package.py` | Native package/export path, asset extraction and assembler profiles. Package eligibility checks consult fixups, expressions, labels and rows. | Add a selected validated layout to this path. Do not hide references inside an INCBIN region containing layout-dependent pointer fields. Share indexes where profiling identifies repeated containment scans. |
| `amiga_reversing/disasm/restoration.py`: `memory_plan`, `memory_build`; CLI/MCP/UI adapters | Shared resident-service admission, current revision and exact verification gates. | Extend once; adapters only serialize requests/results. Old single-region operation may translate to a one-placement request during migration, then lose its duplicate implementation. |
| `amiga_reversing/disasm/derived_artifact.py`: `validate_manifest`, `verify_native_binding` | Payload/manifest identity and fresh native proof binding; syntax validation alone is not proof. `exec_allocabs` is the currently admitted reservation contract. | Reuse identity/staleness safeguards. Version the manifest for layouts; retain read/verification of historical receipts without retaining old build engines. Do not label assembly-time export an Exec allocation proof. |
| `amiga_reversing/disasm/optional_artifact.py`: `validate`, `verify_binding`; `amiga_reversing/tools/optional_patch.py` | Explicit fixed-size correction ledger; validates canonical instruction boundaries, not an interior relocated source map or bootstrap lifecycle. | Keep independent optional corrections supported. Do not repurpose this patch format as the layout authority or treat boundary validation as permission to strip initialization. Remove any layout-only adapter if introduced during migration; do not delete unrelated correction functionality. |
| [Proposal 044](044-runtime-memory-relocation-proof.md) and its audio-volume/keyboard work | Narrow mapped-region execution/proof; keyboard remains conditional. | Preserve bounded results and unresolved facts. Consolidate address resolution; do not revive the deferred proof programme as a prerequisite for fixed-layout export. |
| `amiga_reversing/tools/pandora_minimal_rebase_experiment.py`: `symbolic_repairs`, `build`, `observe` | Successful identity-bound experiment, but source `replace` anchors, target constants and a separate build path; not general native plan admission. | Migrate reviewed reference families and bootstrap recipe into canonical facts/normal export. Delete `symbolic_repairs` and the alternate source builder after M3 acceptance. Retain history/receipts; extract only the still-needed observation adapter into the existing runner. |
| `amiga_reversing/tools/pandora_rebase_output_compare.py` and focused tests | Strict output comparator, fixed known route and explicit normalization/bounds limits. | Reuse as integration acceptance, bind the normal export manifest instead of experimental text identity. No new emulator or general verification programme. |

Existing relevant tests include `tests/test_memory_regions.py`,
`tests/test_derived_artifact.py`, `tests/test_source_export.py`,
`src/test_m68k_render_plan.c`, `src/test_m68k_source_package.c`,
`tests/test_pandora_relocated_ending.py` and
`tests/test_pandora_output_comparison.py`. Their existing presence does not mean
the proposed cases below are implemented.

### Pandora migration fixture and non-negotiable distinctions

The [final output receipt](../../runtime/observations/pandora-relocated-output-validation.json)
and [runtime account](../validation/pandora-saved-route-app-watch.md) are the
baseline, with first failures retained in the earlier observation receipts.

* Original input is 376,832 bytes (`$5C000`), SHA-256
  `70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
  Original C and vasm reconstruction remain exact.
* The demonstrated alternate profile is A500/ECS/PAL/68000 with **1 MiB Chip,
  512 KiB Slow, no Fast RAM**, not the original 512 KiB Chip/OCS profile. The
  experiment assembles at `$80000`; 7,059 accepted instruction extents retain
  their sizes. Fixed app base `$39FC`, workspaces `$65370`/`$653B4`, and display
  banks at `$70000` and `$78000` remain fixed. This is not relocation of every
  address or resource.
* The full file is staged at `$20000..$7C000`. The native 42-byte helper copied
  to `$300` moves only source `$00000..$55370` into `$80000..$D5370`.
  The final experiment changes the evidenced copy-direction comparison for
  this disjoint destination and retains the copy work/timing. Initialization
  enters at `$8046A`. Replacing that work with a branch completed gameplay but
  did not establish the required matched output.
* Source `$55370..$5C000` is an opaque **loader-only suffix**, initially backed
  at `$75370..$7C000`, later overwritten under the original lifecycle. It is
  not materialized at `$D5370`, not a hidden relocated asset fallback and not
  proven unused. Packaging/storage extent, assembly address and materialized
  execution extent must therefore be separate model properties.
* Existing MAL evidence names `bootstrap_to_fixed_execution_base` at source
  `$0` and `fixed_base_image_copy_stub` at `$28`, including the helper, interrupt/
  DMA quiescence and copy extent (actions at sequences 1014/1015 and comments
  following them). These are interpretations, **not an executable bootstrap
  replacement contract** today. `initialize_runtime_workspace` and subsequent
  trap/SR/vector/IRQ setup must not be stripped with the copy helper.
* Reviewed missed-reference families are the six restart receptacle pointers
  and six interaction-data pointers, player callback/self-jump, eight combat
  geometry references and two descriptors, and blank sprite/mask aliases.
  Examples: moved table `$C88AA` must reference `$C88C2`, not `$588C2`;
  `sprite_0005D5DE` denotes `blank_sprite_data`, not permanently `$5D5DE`.
  Original-base symbolic repairs already reproduce exact original bytes.
  These facts must become typed reference/declaration resolution, not a list
  of replacement strings transplanted into the exporter.

## Canonical design

### Ownership, coordinates and persistence

The native analysis owns discovered extents, references and materialization.
Evidence-backed manual corrections/configurations enter through revision-checked
analysis APIs, append MAL provenance and receive DJ review. An LLM may propose
them with source sites, producers/consumers and restrictions; it cannot establish
facts by editing emitted assembly or a private layout JSON. Target metadata
continues to carry supported import seeds, not a competing mutable authority.

Extend the existing schema with versioned region, layout, reference and bootstrap
records. Persist author intent in the existing target history; derive indexes,
resolved addresses, diagnostic sets and render plans from current facts. A layout
profile is a named canonical configuration referencing those identities, not a
second inventory of copied facts. Replaying old actions supplies only their
existing narrow defaults (persistent, CPU RAM, explicit DMA requirement); it
must not invent parentage, alias permission, relocatability or a phase lifetime.
Schema upgrades are tested, deterministic and explicit; no history rewriting.

Keep coordinate types distinct:

| Coordinate | Meaning |
| --- | --- |
| File/storage section + offset | Identity of input bytes and source annotations; invariant across placements. |
| Logical object/region ID + byte offset | Identity of referenced storage or code; independent of numerical placement. |
| Materialization/view ID + phase | Which storage bytes exist at a runtime location, including copied helpers and overlays. |
| Runtime address under a layout | Concrete CPU/bus address, checked against the selected machine profile. |
| Register-relative/app/record displacement | Offset within a proven base context; not automatically an image-relative pointer. |
| Fixed platform address | Hardware, vectors and explicit fixed memory; never rebased merely because its number falls in an image interval. |

A region has a stable ID, name, extent, optional parent+offset, content/storage
mapping, memory requirements and evidence/restrictions. Parentage describes
containment, not relocation coupling. An explicit placement-group constraint
can require shared translation or adjacency where consumers prove it. Otherwise
neighboring objects can move independently. Existing labels/field identities
survive; changing a placement cannot rename or change the meaning of an object.

Subregion declarations render, for example, `display_front EQU display_base +
front_offset`; source-owned content uses its canonical label where appropriate.
Image/code, workspace and display owners all participate in this first-delivery
model. Original placements may remain fixed where evidence requires them; a
base-plus-offset declaration alone does not establish permission to move it.
The expression tree carries the relation, not a string expression to reparse.
Emit only required declarations plus intentionally requested layout documentation,
in stable dependency order. Resolve genuine aliases to one object/offset; diagnose
incompatible names/domains. Do not turn this into an unrelated EQU/RS policy
rewrite or suppress useful hardware symbols.

### Constraints and valid overlap

Separate requirements from placements. Requirements include extent, alignment,
CPU addressability, Chip visibility for DMA, writable/executable use, fixed
address requirements and explicit distance/encoding constraints. Profiles supply
actual RAM apertures, reserved ranges, hardware capabilities and load protocol.
Do not conflate logical byte extent with allocator padding or an Exec lease.

Overlaps require one of three explicit relations: same storage identity via
alias/subregion, declared simultaneous shared storage with a compatible contract,
or a phase overlay with proved non-overlapping lifetimes and a handoff. Unrelated
conflicting writes refuse. A parent and its child are not a collision; two
different owners sharing bytes are not automatically compatible. An alias is
not a second allocation. A claimed lifetime needs initialization, consumers,
last-use/release and interrupt/DMA observer evidence; unknown lifetime is
conservatively overlapping. Do not infer free memory from absent references.

Distance constraints cover signed PC-relative operands/branches, indexed tables,
relative WORD entries, instruction alignment and representable DMA address bits.
Validate full access widths, not only pointer starts. Original export pins
instruction form/width, directive bytes, fill and branch choices. Alternate M1–M4
also pins the demonstrated widths; any overflow refuses with producer/target,
required range and source identity. No silent branch widening or relaxation.
A future explicit relaxation pass would need its own mapping, fixed-point size
resolution and acceptance; it is outside the first slice. Motorola-derived
encoding metadata remains authoritative, not mnemonic exceptions.

### References and deterministic rendering

Extend the existing planned expression/reference identity with target object +
addend + address domain/view, encoding and evidence. Required kinds are absolute
instruction operands; immediate address producers distinguished from scalars;
typed data/table pointers; relative entries; and grouped split DMA fields.
Preserve width, signedness, endianness, original encoding and any mutable/unknown
target restrictions. Pointer-looking unclassified WORDs/LONGs are not references.

Split high/low Copper/sprite/audio addresses share a single logical reference
with explicit field sites and bit slices. Validate pairing, carry behavior,
alignment, hardware bit availability and access phases. Do not independently
rebase halves or pair nearby numeric words heuristically. CPU writes which
construct pointers need their proven producer relation; unsupported computed or
mutable pointers remain named restrictions. Source pointers into aliases resolve
to the same canonical object, without discarding intentional offset aliases.

Pipeline: current native facts and selected profile -> indexed coordinate/
reference resolution -> placement and bootstrap validation -> frozen expressions,
declarations and materialization plan -> normal assembler-specific source package
-> assembly/verification receipt. Rendering consumes the frozen plan and adds no
facts. vasm is the first supported alternate-layout profile; Devpac and other
profiles must refuse unsupported cases rather than emit a numeric fallback.

Fixed hardware operands remain platform symbols. Fixed RAM may render a named
base+offset while still refusing movement. Raw assets stay byte-identical except
explicit typed relocation fields; packages split or render those fields instead
of hiding them inside immutable asset blobs. Deterministic ordering and identity
must be independent of insertion order, pagination or worker count.

Copied code has a storage identity and separate execution view; source references
and PCs are resolved in the correct phase/view. Self-modifying code requires
explicit write sites, writable extents, generated/reference fields and observers.
Unknown generated code or unresolved aliases block the affected transformation,
not original byte preservation. A full-image single-delta assumption is invalid
for the loader-only suffix and the helper executing at `$300`.

### Bootstrap and profile contracts

Model responsibilities before removal: load/decompress, copy/clear, stack and
workspace initialization, CPU mode/traps/vectors, interrupt/DMA ownership,
display/audio setup, and eventual cleanup. A replacement specifies source ranges,
entry preconditions, guaranteed postconditions, clobbers, resources, continuation,
materialization map and timing requirements. Each responsibility is retained or
replaced explicitly. Dependencies prevent deleting a copy routine while retaining
its implicit initialization assumptions. Merely naming a routine bootstrap does
not authorize stripping its bytes.

The first delivery includes `original`, a separately named fixed `$80000`
diagnostic profile, and a further evidenced fixed layout with an independently
moved workspace or display block. The first two retain the evidenced loader/copy
initialization sequence; the `$80000` profile has an explicit evidenced
copy-direction variant and ECS/1 MiB requirements. The additional block's legal
placement and initialization are selected from its actual constraints, not an
invented destination. It may use the original or known moved image placement;
the block's placement must not merely follow the image's translation.
Alternate builds need not equal original bytes, but each change must originate
in a typed reference, placement or reviewed bootstrap variant. Receipts enumerate
all changed fields/instructions, unmodified assets and remaining restrictions.

Assembly-time rebase solves symbols at build time and produces a fixed binary.
Runtime relocation instead emits fixups and a loader contract for an actual
allocated base. Runtime allocation additionally has failure, ownership, lifetime,
alignment and Chip requirements. OS-hosted operation also needs coherent hardware
takeover/release, vectors/interrupts/Copper/audio/blitter lifecycle, stack/mode and
error unwind. Exec allocation does not alone provide that lifecycle. A future
OS-hosted profile cannot reuse the game's supervisor/bootstrap teardown by
deleting a range and assuming the remainder is friendly.

### Diagnostics, identities and refusal

Every diagnostic names the layout/profile, canonical object/reference/source
site, competing view/owner if any, evidence and smallest missing obligation.
Distinguish conflict, unresolved provenance, unsupported encoding/profile,
out-of-bounds, missing bootstrap prerequisite, stale evidence and incomplete
analysis. Unknowns do not become null pointers, fixed constants or successful
skips. A user may retain a restricted original export; alternate export must
state exactly which unknowns prohibit which movement, without claiming global
safety from the successful route.

An export manifest binds binary, current canonical revision/schema, layout and
constraint set, bootstrap contract, native plan, exporter/backend and assembler
identity, assets and final package/payload. Reuse the existing immutable artifact
and consumed-identity checks. A changed placement, assumption or loaded backend
makes dependent receipts stale. Evidence files describe observations and hashes;
ROMs, media, raw checkpoints and PCM remain private. A historic manifest can be
read as history without being admitted for current execution.

## Performance and invalidation

Do not optimize by maintaining a second reduced-fidelity analysis. Build reusable
indexes in the resident native artifact over the existing facts. Let N be region/
view intervals, R references, I instructions and K returned overlap relations.

* Sorted, domain/phase-partitioned interval indexes resolve containment/overlap
  in `O(log N + K)` per query. A materialized contiguous span is proved by walking
  interval boundaries and consistent affine mappings, not its byte count.
* Build reference indexes by source site, target object/view and owning region
  in `O((N + R) log N + K)` time, with `O(N + R + K)` retained space. Batch overlap
  validation uses a sweep; unavoidable dense alias output can be quadratic and
  must be reported/bounded, not silently truncated.
* Plan a fixed-width layout by visiting affected objects/references once;
  ordinary resolution is `O(R log N + K)`, rather than a full I scan per region.
  Bounded control-flow/alias proof is a separate cost with explicit budgets;
  no claim that all proofs are logarithmic. Output/assembly/byte checks remain
  linear in emitted bytes plus assembler cost.
* Dependency edges link facts -> mappings/references -> expressions/declarations
  -> package chunks/receipts. A placement-only edit invalidates affected targets,
  incoming references, distance constraints and bootstrap products, not opcode
  discovery. A provenance/type edit invalidates its reachable users; profile
  changes invalidate legality and relevant render products. Ambiguous impact
  invalidates the whole plan. Compare incremental results to a fresh rebuild.

Current `mr_mapped_span` loops over every byte and resolves each separately;
`memory_region_append_facts` loops over planned instructions for each region.
`m68k_source_package.c` also has row-containment scans. These are audit leads,
not measured timing attribution. Instrument phase timing/counts/peak retained
bytes first. Avoid speculative global caches: index lifetime follows the native
artifact revision; any persisted derived cache must be content-addressed and
discardable, never authoritative. Share resolution with Proposal 037; follow
[Proposal 041](041-native-corpus-projection-engine.md) ownership boundaries and
[Proposal 039](039-corpus-build-performance-and-memory.md) deterministic resource
discipline without reopening their programmes.

M0 records a benchmark fixture specification: Pandora's 376,832-byte input and
7,059 accepted instructions; its actual current reference/interval counts;
original, known image and selected independent-block exports; cold artifact creation, warm layout-only edit,
one reference change and profile change. Record hardware/tool identities,
phase wall/CPU time, allocations/peak memory, output hashes and repeated-run
variation. Add deterministic synthetic 1x/2x/4x region/reference fixtures,
including nested aliases and sparse/dense overlaps. Report operation counts as
well as time so scaling failures are visible without machine-specific promises.
Accept the interval proof only when increasing span byte length at fixed interval
count does not increase mapping lookup count linearly. Accept reference indexing
when scan counts no longer grow as regions times instructions. Warm edits must
equal clean output and avoid unaffected discovery; report actual savings rather
than a target percentage. The initial design-only revision ran no performance
measurements; the implementation checkpoint above now supplies baseline and
index operation counts. No latency acceptance claim is yet established.

## Milestones and deletion gates

The table defines acceptance, not a claim that every mechanism exists. M0 and M1
have the partial implementation/evidence above; M2 has target profile builds and
M3 has begun runtime checks; M4–M6 are not started. M1–M4
form the required first delivery. Original, known-image and independent-block
validation are incremental internal steps; M2 or M3 alone cannot close delivery.
M5–M6 are distinct later decisions. Each batch
records mechanism delivered, target scope, tests/evidence, remaining restrictions
and removed implementation. Existing unfinished B07 files are independent and
remain untouched.

| Milestone / dependency | Deliverable and acceptance | Non-goals and deletion gate |
| --- | --- | --- |
| **M0: migration contract, block selection and baselines**; none | Inventory canonical image/code, workspace and display owners, reference families, bootstrap facts and exact experiment variants. Inspect concrete candidate blocks' CPU/alias/DMA/lifetime/initialization constraints and choose a supported independent move, recording specific restrictions on other blocks. Capture exporter/performance identities and focused fixtures; confirm existing exact/output receipts and private evidence availability without unrelated reruns. | No architecture implementation hidden in baseline collection. No experimental path removed yet. If no block can be justified, report the exact missing evidence and keep first delivery open; do not substitute image-only completion. |
| **M1: canonical layout planning**; M0 | Extend native region/view/reference schemas and revision-checked commands for image/code, workspace and display regions from the start. Model base-plus-offset subregions, independent placements, aliases, fixed RAM/hardware separation and indexed resolution. Include original, known-image and selected-block constraints. Test deterministic replay, valid containment/alias, invalid overlaps/alignments, stale edits, missing provenance and interval scaling. | No automatic placement solver or arbitrary overlays. Existing single-region service translates to shared planner only after its supported positive/refusal fixtures agree; delete its duplicate scan/policy engine at that point, retaining historical receipt verification. |
| **M2: normal exporter and internal baseline builds**; M1 | Render image/code, workspace and display bases/subregions naturally in the frozen native plan. Admit reviewed Pandora pointer families; resolve image symbols, tables, split sprite/Copper references and fixed buffers. Encode loader prefix/suffix, helper and timing-preserving bootstrap variant. Generate original and `$80000` packages; original C/vasm bytes exact, alternate matches the qualified payload or every difference has a reviewed typed cause. Verify widths and full-file/suffix placement; test overflow, partial split pointer, raw-asset fixups, copied-code view ambiguity and missing initialization refusal. | This is an internal step, not first-delivery completion; the independent block move is required by M4. No runtime allocation. Delete `symbolic_repairs`, ORG/comparison string replacements and experimental source builder only after this normal path passes; a thin observation client may temporarily consume either manifest until M3. No permanent dual build mode. |
| **M3: baseline runtime qualification and experiment retirement**; M2 | Run the existing 576-phase normal-input saved-Earth route on the normal-export known-image payload, actual moved-PC/old-range guards and zero loss counters; qualify unheld cold completion and same-profile controlled output comparison. Retain failure receipts and scoped asset/DMA/output checks below. Wire CLI/MCP/UI to the same service with repeated/stale/non-pass parity checks. | Baseline qualification does not close first delivery. No unrelated proof/fuzzing work. Remove experiment-only build/config admission and duplicate observation address constants once the runner consumes the shared layout map. Keep historic receipts/comparator; preserve reproducible original and alternate exports before deleting obsolete fixtures/code. |
| **M4: independent block move and first-delivery acceptance**; M1–M3 and M0's evidenced block constraints | Export one additional legal fixed layout independently moving at least one workspace or display block. Both kinds remain canonical base-plus-offset regions even if only one physically moves. Validate all relevant producers/consumers, alias/lifetime/initialization and CPU/DMA address construction; run focused negative constraints, existing route, unheld cold completion and matched output acceptance. Observe the actual new block addresses and unchanged or separately selected image placement. Report exact restrictions for blocks not moved. | Delivery closes only with original, known-image and independent-block acceptance plus required debt-removal gates. No requirement to move both workspace and display, no invented arbitrary placement or all-buffer safety claim. Delete selected-block mapping constants only when shared facts replace their consumers. Missing evidence blocks that move and delivery closure, not truthful partial reporting. |
| **M5: optional runtime allocation/relocation**; completed first delivery M4 and a separate decision | Format fixups from typed refs, loader/allocator failure/unwind and initialized materialization, Chip leases and actual-base observation. Positive and refusal fixtures plus relevant existing route/output qualification. | No claim of OS friendliness from AllocMem/AllocAbs alone. Retire fixed-address allocation assumptions in the shared path only after all admitted old cases have explicit policies; keep fixed-layout profiles as supported outputs, not duplicate engines. |
| **M6: optional OS-hosted profile**; M5 and reviewed lifecycle contracts | Explicit resource takeover/release, vectors/IRQ/DMA/Copper/audio/blitter, CPU mode/stack and restoration on exit/error; reviewed bootstrap replacement; real host integration evidence on a declared platform. | Not authorized implementation now; not universal portability. Never strip bootstrap until each responsibility has a verified replacement. Remove superseded takeover shim only after normal exporter/runner owns the complete contract. |

### Integration acceptance and limits

Reuse the existing evidence-producing route; do not count tests or extra fixtures
as gameplay progress. The baseline has 576 phases, 509 controller API calls
including release/cleanup, and 375 authored input events. The controlled pair
matches phase clocks and inputs, while the independent unheld cold run establishes
completion without the comparison clock fixture. Both use normal inputs, no
gameplay-state injection or restored checkpoints. Expected actual main-image PCs
shift by `$70000`; fixed helper/vector/hardware contexts are not false failures.

The comparison fixture is explicit startup provisioning: fresh reset/custom
direct-payload boot, natural HAND wait, common pregame CCK boundary, then the
existing HAND-to-GO host marker write at `$7FFF8`; no host game-register writes.
It is not original packed-disk boot or proof of identical pregame device state.
Keep the independent unheld run; no calibrated waveform shift may manufacture
an audio pass. Copy timing alone was insufficient without the common pregame
phase fixture. Changes to that contract require new evidence, not silent offsets.

Acceptance reuses asset identity checks (excluding enumerated typed reference
fields), eight exact RGBA frames and exact mixed 44,100 Hz stereo float32 PCM
over the declared post-GO interval. Existing eight points cover initial title
transition, overlay, proximity, Engineer transfer, first sonicdriver hit, console,
ending and settled title. The final baseline compares 24,726,568 float samples
without fitting, resampling, gain or omitted interior samples. Frame selection
must describe actual video state, not misread a per-star helper as a frame loop.

Six complete sampled DMA frames per layout are an additional bounded check,
not continuous DMA surveillance. CPU old-address observations are not DMA
coverage. Audio/Copper/bitplane/sprite checks and blitter physical Chip legality
retain their separate scopes. Eight unchanged original NULL sprite control reads
at addresses `$0`/`$2` remain an explicit bounds finding, **not certified sprite
asset safety**. The baseline verdict is `pass_with_original_bounds_findings`;
do not silently widen that exception to new invalid pointers. Eight matching
frames, sampled DMA and this route do not certify every frame, asset, optional
path, OS lifecycle or original OCS profile.

For the independently moved block, reuse these route/output gates and add the
specific CPU/DMA address observations required by its contract. Do not assume
the known image's sampled DMA coverage observes the new block's consumers.
Equivalent state/outputs do not alone prove all aliases relocated; combine them
with the selected block's typed reference ledger and explicit remaining limits.

## Decisions still requiring evidence

1. M0 must pin the exact canonical reference and bootstrap records needed for
   the existing alternate payload, including whether current typed facts suffice
   or need corrections. A successful patched export is not proof those facts
   already exist. No wider opcode or semantic reconstruction is presumed.
2. Choose stable profile/phase identifiers and schema migration details within
   existing MAL/native interfaces in M1. The proposed record contents above are
   a design contract, not an implemented public API spelling.
3. Retain fixed widths for the first slice. Any future instruction relaxation,
   overlay scheduler or general placement solver needs a separate justified
   decision rather than entering via convenience code.
4. Select the independent workspace/display block during M0, with its actual
   reference/alias/lifetime/DMA constraints. Implement its model with M1 and
   validate its move through M4. Unknowns must identify the affected block and
   missing evidence; they cannot blanket-defer both region kinds or turn
   image-only qualification into completed first delivery.
5. Runtime allocation and OS-hosted work require an explicit follow-up decision
   and concrete host/lifecycle evidence. Neither is needed to remove today's
   source-patching debt or to deliver the required original, known-image and
   independently moved-block layouts.

The next implementation action, if authorized, is M0 followed by M1–M4 as one
staged first delivery, reporting internal validation results without prematurely
closing delivery. M5–M6 remain separate decisions; implementation progress must
not silently broaden first-delivery scope into runtime allocation or OS hosting.
