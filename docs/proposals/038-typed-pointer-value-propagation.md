# Proposal 038: Typed Pointer-Value Propagation and Symbolic Access Recovery

Status: In progress — 2026-07-29. The consumer model, canonical address-value
ownership, Proposal 039 corpus coverage, bounded candidate-merge soundness, and
Extension A (canonical indexed, affine, and interior-address expressions) are
complete. B--J remain ordered follow-on work.

## Problem

The analysis can know that a destination is a typed pointer field while still
treating an immediate written to it as an untyped scalar. For example, the
Pandora instruction:

```asm
move.l #$5CF4C,world_object_shared_prefix_interaction_message_ptr(a5)
```

writes a value to a known pointer field, yet the immediate can remain numeric
instead of being represented as an address to the corresponding source object.
That loses an object-graph edge, prevents typed propagation through later
loads/copies, and leaves the reconstructed source less meaningful than the
evidence permits.

This is a general analysis and rendering gap. It must not be fixed by naming
individual immediates, special-casing `world_object`, or adding renderer
fallbacks.

## Goal

Make a typed pointer destination a first-class semantic constraint on values
written to it. When a concrete immediate, relocation, or copied value is
stored into a proven pointer field, analysis must create an address-valued
fact with the field's pointee domain, propagate that fact through valid data
flow, and render it symbolically when it maps to representable source storage.

```text
typed pointer field + value-producing instruction
  -> typed address-value fact with provenance
  -> register / stack / global / field propagation
  -> concrete source target resolution
  -> Proposal 037 planned symbolic expression and declaration
  -> rendered source and source-quality evidence
```

No compatibility path, target-specific exception, or numeric fallback may hide
a failed symbolic representation of a value that analysis has classified as a
renderable typed pointer. Such a failure is an export diagnostic. Immediates
without pointer semantics remain numeric by an explicit semantic decision;
they are not speculative pointers.

### Main-task boundary

This proposal preserves proven address identity and pointee domain from value
creation through valid analysis transfer rules to a frozen render plan. It is
not a renderer-side operand rewrite: rendering consumes the planned expression
and must not rediscover pointer meaning from instruction text.

The completed path includes a direct source pointer, its lossless register and
storage transfers, a later reload, and at least one typed consumer. Consumers
are first-class analysis facts, not test assertions or renderer heuristics: a
typed storage write, a proven local-function argument, a proven platform/API
input, or a proven indirect-callback input.
It deliberately stops when identity, target mapping, a call contract, or a
control-flow merge is not proven. That boundary makes unknown and ambiguous
values durable analysis states rather than candidates for a numeric or
symbolic fallback.

While implementing the main task, maintain the deferred-extension section
below. When analysis encounters an indexed address, interior pointer, alias,
call/return contract, callback signature, table indirection, or composite
layout concern beyond this boundary, record the concrete evidence, the current
safe stop condition, the required fact/model extension, and its relationship
to the address-value representation. Do not silently expand 038 or work
around the concern in rendering; refine the corresponding deferred task so a
subsequent proposal can implement it cleanly.

## Semantic Model

### Address-valued facts

Introduce one durable address-value representation used by both analysis and
render planning, plus a separate durable consumer representation. The value
represents identity and provenance; the consumer records the independently
proven place at which that value is used. A value may have multiple consumers,
and a consumer references exactly one address-value fact, including a fact
whose terminal state is non-source, ambiguous, or invalid. They record:

- value origin: immediate, relocation, register, stack slot, static/global
  slot, pointer field, return value, or table element;
- address value or source/runtime mapping, addend, and address domain;
- pointee type/domain and pointer width;
- producing instruction and transfer provenance on the value; and
- consumer identity, kind, operand, pointee domain, and the durable storage or
  call-input contract that proves consumption, on the consumer record;
- confidence and the complete chain of propagation provenance.

A pointer value is distinct from a numeric constant even when both have the
same bits. It is created only when a proven destination/producer contract
requires a pointer: a typed field, typed slot, known API parameter or return,
typed table element, relocation, or existing address-value fact.

### Writes and propagation

The analyser must interpret writes before discarding immediate semantics:

1. Resolve the destination storage and its declared type.
2. If it is a pointer field, classify a compatible produced value as an
   address-valued fact in the field's pointee domain.
3. Resolve a source or runtime target only through the normal address mapping
   and ownership model.
4. Propagate the value through lossless register copies, address formation,
   stack/global stores and reloads, typed field loads/stores, and known
   function/API contracts. Observe a proven call input before its call can
   clobber the value; a locally preserved register is a transfer across that
   call, not a substitute consumer record.
5. Merge only equivalent address values and compatible pointee domains.

Conflicting values or incompatible types produce an explicit ambiguous value
state. Unknown calls and clobbers invalidate the affected propagated state.
No value is retained merely because its bit pattern looks address-like.

### Rendering closure

Proposal 037 owns rendering closure. This proposal supplies semantic
address-value facts and asks the shared resolver for a planned expression.

- A mapped, representable target produces one planned symbolic expression and
  a canonical planned declaration if it targets source storage.
- An unmapped external/runtime-only pointer remains an explicitly classified
  non-source value with its reason; it does not invent source storage.
- A contradictory promise to render a source pointer is an invalid plan and
  refuses export. It cannot silently become a numeric operand.

Renderers do not infer pointer meaning from an immediate. They consume the
typed address-value fact and the frozen render plan.

## Framework Changes

1. Replace scalar-only immediate handling at typed destinations with the
   address-value model.
2. Extend typed-flow state, joins, invalidation, and provenance export to
   carry address values and pointee domains across registers, stack slots,
   globals, fields, table elements, calls, and returns.
3. Introduce one common typed-consumer model for pointer stores and proven
   call inputs. It must retain the contract that justified consumption rather
   than encoding a call as a synthetic store or using a store as proxy
   evidence for a call. This is the framework mechanism used by analysis,
   reporting, and render planning; fixtures verify it but are not a substitute
   for it.
4. Make the source-analysis export expose these facts and their producer/
   consumer chain without relying on rendered text.
5. Teach the shared symbolic resolver to consume address-value facts for
   instructions, relocations, structured fields, and chained lookups.
6. Add normal Manual Action command support only where a reviewer must supply
   a missing durable type/field contract. Manual actions record the contract,
   never a one-off instruction rendering.
7. Remove any old scalar-immediate special cases made redundant by the common
   typed address-value path.

The address-value fact is a pre-render analysis fact. It is available to
typed-flow reporting, object/data xrefs, field and table consumers, and
indirect-call/callback recovery before render planning consumes it. No second
renderer-only pointer inference path may be introduced.

## Corpus Opportunity Audit

Start implementation with a fresh indexed-corpus audit. The existing pointer
store facts and type-flow reports already expose much of the needed evidence,
but the corpus must gain a first-class, stable row for this proposal's complete
opportunity shape:

```text
typed pointer consumer
  + address-valued producer
  + target-resolution result
  + render result
  + downstream propagation summary
```

Each row must identify the source/target by stable corpus identity and include:

- source kind: immediate, relocation, register, stack, field, return value,
  or table element;
- consumer kind: typed struct field, app slot, absolute slot, stack parameter,
  local-function argument, platform/API input, or indirect callback input,
  with its declared pointee domain and durable contract identity;
- resolution: resolved, finite candidates, ambiguous, invalid, external, or
  no proven pointer contract;
- render outcome: symbolic, explicitly non-source, or invalid;
- propagation depth and terminal reason; and
- whether the record is a positive fixture candidate, a negative scalar case,
  or an unresolved review opportunity.

The audit is a measurement and fixture-selection surface, not an automatic
mutation mechanism. It must not create labels, types, Manual Actions, or
source changes. Corpus rows are derived from durable analysis facts and retain
the provenance needed to reproduce their classification.

Regenerate the corpus before implementation and save its aggregate counts and
representative stable rows as the Proposal 038 baseline. Use observed rows as
real-target regression and integration evidence; do not treat a category's
absence as evidence that it has no valid semantics, because a target may lack
the durable pointer contract needed to emit it. Select focused C fixtures for
the complete source/destination/propagation matrix, including categories not
yet observed in the corpus, and select Pandora only as one proof target.
Regenerate the same report after each major slice and report both resolved
gains and any new invalid/ambiguous cases.

### Superseded pre-039 baseline — 2026-07-28

A fresh, read-only full corpus build completed with 428 entries, 3,734,243
xrefs, 582,446 listing snippet rows, 230 type-flow report rows, and 56
unresolved typed-field rows. The typed-pointer opportunity report found:

```text
typed pointer-store rows: 0
targets with a pointer-store row: 0
source/destination/resolution/render/provenance categories: none
```

This is a meaningful baseline, not a zero-opportunity claim. The current
indexed corpus does not emit any `pointer_store` analysis fact for its
analysed executable inputs. Pandora is present as a derived raw-binary project
target, but that project-target catalog row deliberately records reproduction
and decompression metadata only; it does not run source analysis over the
reconstructed target. Therefore this corpus cannot yet supply the positive,
propagated, external, ambiguous, or scalar-negative fixture candidates required
by this proposal.

The audit command itself is intentionally derived and read-only. It records a
stable xref/listing locator when a pointer-store fact exists and streams the
xref artifact, so reporting remains bounded for a full corpus. It does not
create labels, types, Manual Actions, or source output.

Before implementation may claim corpus coverage, Proposal 039 must provide the
normal corpus analysis input model: analysable reconstructed project targets
and typed pointer-store facts must reach the common corpus stream. That is a
general source-analysis path with the same durable facts as executable inputs,
not a Pandora export, a manual fixture injection, or an inferred operand-text
scan. After that dependency is complete, regenerate this baseline and select
the required fixture categories from observed rows.

### Post-039 corpus baseline — 2026-07-28

Proposal 039 is complete and the fresh full corpus now includes reconstructed
raw-binary project targets in normal source analysis. The read-only
pointer-value opportunity report now contains 45 typed pointer-store rows for
one target (Pandora):

```text
source kinds: immediate 4, propagated 41
destination kinds: app_slot 24, struct_field 21
resolution: resolved 25, finite_candidate_targets 2, unknown_target 18
render outcome: symbolic_now 4, needs_address_value_propagation 21,
                not_symbolic 20
```

This is the implementation baseline for this proposal. It proves that the
common audit stream now carries observed positive opportunities, including the
Pandora world-object pointer-store class, without a target-specific corpus
path. It does not cover every semantic category: the current corpus has no
emitted relocation, stack, return-value, scalar-negative, or conflicting-join
pointer-store fixture. Those gaps are missing durable input contracts, not
negative evidence. Focused C fixtures must cover the full semantic matrix;
observed corpus rows remain the real-target integration and regression set.

### Interim first-slice corpus audit — 2026-07-28

The same full, read-only build completed after the first implementation slice:
378 analysed inputs (319 file entries and 59 reconstructed project targets),
45 Pandora pointer-store rows, and stable xref identities for every row. The
source/destination/resolution counts are unchanged because this work preserves
analysis facts rather than inventing target evidence. Their producer facts are
now explicit:

```text
immediate producer provenance: 4
other producer provenance: unknown 28, field_pointer 9, app_slot 3, static_data 1
render outcome: symbolic 4; non-source 41; invalid 0
```

The four symbolic rows are the four immediate pointer stores. The report now
reads each outcome, origin, terminal state, and transfer depth from the durable
address-value fact; pointer-store-local producer markers have been deleted. It
includes Pandora's
`interaction_message_ptr` store at stable key `s0:0004D3D2:instruction`.
The remaining propagated stores retain their actual non-immediate provenance
and remain unresolved review opportunities when no producer expression is
proven. They are not numeric renderer fallbacks.

The concrete Pandora branch is narrower than an earlier review description:
`interact_with_chemist` writes `abs_0_0005CF4C` to
`world_object_shared_prefix_interaction_message_ptr(a5)` and branches to
`interact_with_hooligan_or_robomechanic`, but that destination does not reload
the field. The separately observed reload belongs to a different control-flow
path, so treating it as the same value would be a false interprocedural alias.
Pandora remains the real-target direct symbolic-store proof. A focused CFG
fixture supplies the required same-object field-store/reload/consumer proof.

### Current consumer-model corpus audit — 2026-07-28

After the common consumer model was added, the final fresh normal eight-worker
corpus build completed all 428 entries in 524.8 seconds. It produced 3,095,963 xrefs,
460,240 listing snippet rows, 241 type-flow rows, and 65 unresolved typed-field
rows. The read-only pointer-value report now reads consumer facts rather than
using pointer-store records as a proxy:

```text
typed address-value consumers: 71 across 8 targets
consumer kinds: storage 45, local_function_input 18, platform_api_input 8
callback_input: unavailable in the current corpus
producer origins: immediate 11, field_pointer 9, app_slot 3,
                  static_data 1, unknown 47
resolution: resolved 48, finite candidates 2, unknown target 18,
            external 2, invalid target 1
render outcome: symbolic 9, non-source 61, invalid 1
Pandora: 63 consumers, including the direct interaction_message_ptr store
```

The unavailable callback category is a corpus-coverage result, not a narrowed
semantic boundary: focused C fixtures exercise an accepted bounded callback
table contract, alongside local-function, generated platform/API, storage, and
unknown-call-negative consumers. The report has no
`needs_address_value_propagation` outcome. Its non-source, ambiguous, external,
and invalid rows retain their explicit terminal state rather than receiving a
numeric rendering fallback.

## Pandora Proof Scope

Use the world-object interaction/callback swath as the real-target direct
symbolic-store proof, beginning with
`world_object_shared_prefix_interaction_message_ptr` in
`interact_with_chemist`. Establish the target object/range only from existing
mapping, xrefs, and typed-flow evidence; do not manufacture a reload or a
consumer relationship when control flow does not prove it.

The combined proof must demonstrate Pandora's direct typed pointer store and a
focused same-object CFG field store/reload/consumer. It must remain valid for
other pointer-field types without code changes.

## Acceptance Criteria

- A fresh corpus baseline and post-change report expose the typed-pointer
  opportunity rows above, with stable identity, provenance, aggregate counts,
  and no source mutation side effect.
- The corpus audit records every observed typed-consumer opportunity with its
  stable identity, consumer contract, and classification. Pointer-store rows
  remain one consumer category. A category omitted because no analysed target
  has the required durable contract is reported as unavailable, never treated
  as a negative case or used to narrow the implementation.
- Focused C fixtures cover representative positive, negative-scalar, external,
  ambiguous, and propagated cases. Corpus rows are selected as real-target
  integration cases where available, rather than requiring the corpus alone to
  supply every category or relying solely on Pandora.
- Focused C fixtures cover a typed pointer-field immediate store, relocation
  pointer store, register copy, stack/global round trip, typed field reload,
  compatible and conflicting joins, a preserved local-call input, a proven
  generated platform/API input, a proven accepted callback input, call
  clobbering, and a chained lookup. The fixtures assert the shared consumer
  facts and the planner's stable-identity linkage; rendered text alone is not
  evidence of either.
- The deferred-extension section is updated as relevant bounded-analysis
  concerns are encountered, with concrete trigger evidence and the required
  future model change; it contains no renderer workaround or unreviewed scope
  expansion of this proposal.
- A scalar immediate written to a non-pointer field remains numeric and creates
  no address-value fact or label obligation.
- A pointer-like immediate with no proven pointer contract remains numeric for
  an explicit reason; no heuristic address guessing is introduced.
- A mapped typed pointer produces a durable address-value fact with provenance,
  one planned symbolic expression, and a canonical declared source target.
- A typed pointer whose promised source target cannot be represented fails
  source export with a diagnostic; it does not regress to a numeric fallback.
- Address-valued facts propagate only through valid transfer rules and are
  invalidated by conflicts and clobbers.
- A candidate-set merge that exceeds the representable bounded set must clear
  the concrete address identity and produce an explicit non-symbolic terminal
  state. It must never retain a subset of candidates or preserve a previously
  resolved target as though the omitted paths did not exist.
- Renderer/source-quality evidence comes from the planned expression, not from
  a separate typed-flow-to-label path.
- Pandora renders the verified world-object pointer store as the planned source
  expression. Focused fixtures follow the same address value through a
  same-object field reload to a typed consumer and through a proven call-input
  consumer. They must reject a changed or unproven base-object identity or
  call contract rather than creating an interprocedural alias.
- Pandora has no duplicate declaration, synthetic label, dangling symbolic
  expression, or source-quality workaround introduced by the change.
- `M68kAddressValueIR` is the sole durable owner of an address value's source
  value, provenance, resolution, target, candidate set, terminal state, and
  render outcome. A storage record owns only its storage-specific destination
  contract and its link to that value; it cannot retain a second mutable copy
  of address-value state.
- Resolution is represented by a generically named address-value model. No
  call consumer, render-plan path, or generic resolver depends on a
  pointer-store-named type or enum.
- Focused C and relevant Python tests pass; Pandora source analysis, internal
  assembly, source quality, and exact full-file round trip pass.

## Required Deletions

- Per-target immediate-address rendering exceptions.
- Renderer-time tests that infer pointer meaning from raw immediate values.
- Scalar-only typed-flow paths that discard a compatible pointer value at a
  typed destination.
- Pointer-store-only consumer assumptions, including any representation that
  encodes a proven call input as a synthetic storage write.
- Duplicated address-value facts in `M68kPointerStoreIR`, including copied
  source values, resolution, targets, candidate sets, provenance, or render
  state.
- Pointer-store naming or types in the shared address-value resolution model.
- Partial candidate-set retention after a bounded merge overflow.
- Numeric fallback after a typed, renderable source-pointer classification has
  been made.
- Manual actions or comments whose only purpose is to force an instruction's
  printed operand text.

## Completed Consumer-Model Slice

The initial slices established durable address-value facts for typed pointer
stores, explicit terminal/render states, planned-expression validation, and
same-object typed-field propagation. The common consumer model and its shared
target materialisation are complete:

1. Introduce a durable typed-consumer record that is independent of
   `M68kPointerStoreIR`, and make it the sole common consumption surface for
   analysis export, corpus reporting, and render planning. It must identify
   the consumer instruction operand, consumer kind, pointee domain, and the
   exact durable contract that proved consumption. Storage writes remain
   storage-specific records linked to the common address-value fact;
   local-function arguments, platform/API inputs, and callback inputs must
   not be encoded as synthetic stores. Address-value identity/provenance and
   consumer identity are separate: one value may feed several consumers, but
   each consumer links to one concrete or explicitly terminal address value.
2. Observe only contract-proven call consumers before call invalidation. Use
   the existing durable local-function register contracts, generated platform
   call-input contracts, and accepted callback signatures where they prove a
   pointer input. Unknown calls, untyped inputs, and unresolved indirect calls
   create no consumer and invalidate state under the existing clobber rules.
   Do not introduce heuristic call summaries, register-name conventions, or
   caller/callee fallbacks.
3. Link every supported typed consumption to an explicit consumer record and
   preserve the bounded producer-to-consumer transfer chain through the
   supported register, stack, global, typed-field, relocation,
   compatible-join, and known-call rules. Record an explicit terminal state
   when a value is invalidated, ambiguous, external, unrepresentable, or lacks
   a proven transfer contract. Do not infer a chain from rendered source text.
4. Extend source-analysis JSON and the corpus audit to expose the complete
   stable fact and its consumer: producer/consumer identities, consumer kind
   and contract, value/domain, target resolution, propagation depth, terminal
   state/reason, render outcome, and fixture/review classification.
   `needs_address_value_propagation` is not a render outcome and must not
   survive in the post-completion report.
5. Keep one render-plan path. The planner consumes the durable consumer and
   its linked address-value fact by stable identity, rather than recovering
   pointer meaning from instruction text, store records, or test-only side
   channels. A consumer operand with a mapped, representable source target
   receives that single planned expression; a non-source consumer remains
   explicitly non-source. A contradictory source-render promise must produce
   the explicit export diagnostic, never a numeric operand. No renderer may
   discover consumer semantics from operand text or duplicate the analysis
   resolver.
6. Strengthen the focused C fixture matrix so every supported transfer and
   invalidation asserts the durable value and consumer records, terminal state,
   and planned output where applicable. Include a proven local call input, a
   generated platform/API input, and an accepted callback input, plus negative
   untyped and unknown-call cases. Regenerate the full read-only corpus report and
   demonstrate Pandora's direct symbolic store plus the focused same-object
   field-store/reload/consumer chain; do not manufacture an interprocedural
   Pandora chain that its control flow does not prove.
7. Replace the interim audit claim with a post-completion report only after
   these conditions pass. Preserve unresolved rows as review opportunities and
   report unavailable consumer categories explicitly rather than hiding them.

## Completed Main-Task Slice: Canonical Address-Value Ownership

The completed consumer-model slice exposed one remaining transitional shape:
`M68kPointerStoreIR` still persists a duplicate copy of source-value,
resolution, target, and candidate facts already owned by `M68kAddressValueIR`.
The shared resolver currently operates over both representations. That is not
backwards compatibility to retain: it is redundant mutable state, permits
drift, and leaves generic call consumers coupled to pointer-store terminology.

The final migration made the address-value model canonical end to end:

1. Introduce a generic address-value resolution enum/type, move all generic
   consumer, value, resolver, planner, JSON, and corpus code to it, and remove
   the pointer-store-named resolution type. Preserve semantic states and their
   explicit terminal meanings; this is a representation migration, not a
   change in evidence policy.
2. Reduce `M68kPointerStoreIR` to a storage-consumer detail: destination
   identity/type/contract, source and destination operand identity as needed
   for the storage instruction, and `address_value_id`. Delete its duplicated
   address-value provenance, resolution, mapped target, candidate, and render
   fields. Do not add adapters, aliases, deprecated fields, or compatibility
   serializers.
3. Construct the canonical address value once, then link the storage consumer
   and storage detail to that identity. General call consumers and storage
   consumers must follow the same construction and target-materialisation
   path. The resolver may visit each canonical value once; it must not
   materialise a parallel store copy.
4. Make JSON export, source-quality validation, render planning, and the
   corpus audit read canonical address values through consumers. Retain a
   storage-specific JSON projection only where it describes the destination
   contract; it must reference the value by stable id rather than repeat its
   facts.
5. Update focused C fixtures to assert one canonical value linked to one or
   more consumers, including storage plus call consumers. Add regression
   checks that no pointer-store-specific resolution type or duplicated
   address-value field remains. Regenerate the Pandora source and rerun the
   full exact round trip, source-quality export, relevant Python tests, and the
   read-only corpus report.

This migration introduced no compatibility support. `M68kPointerStoreIR` is
now only a storage-destination record linked by `address_value_id`; all value
facts are owned by `M68kAddressValueIR`, and all consumers use the generic
resolution model. The resolver visits the unified transient consumer
observation once before the canonical analysis facts are emitted.

### Completion evidence — 2026-07-28

- `src/build.bat` and all 580 C unit tests passed. The focused branch-merge
  fixture verifies candidate-set merging on the unified consumer observation;
  the storage record retains no candidate or resolution state.
- `tests/test_target_usage_manifest.py` passed (30 tests).
- Pandora regenerated with exact full-file round trip and zero diff ranges.
  Its source-quality export reports 45 canonical address values, 63 consumers,
  45 storage details, zero blockers, and no source refusal.
- A fresh normal eight-worker corpus build completed 428 entries in 544.5
  seconds. The read-only consumer report contains 71 consumers across 8
  targets: 45 storage, 18 local-function inputs, and 8 platform/API inputs;
  outcomes are 9 symbolic, 61 non-source, and 1 invalid. No callback input is
  present in the current corpus, while the focused callback fixture remains
  coverage for that supported contract.

## Completion: Bounded Candidate-Merge Soundness — 2026-07-29

Review of the canonical migration found a soundness gap in the transient
consumer observation: `typed_pointer_candidates_merge` reported failure when a
join exceeded its four-value exact-candidate capacity, but the unified consumer
path ignored that result. It could therefore retain an earlier subset, which
could falsely appear resolved or less ambiguous than the control flow proved.
This was neither a compatibility concern nor an acceptable numeric fallback:
it was an incomplete analysis fact that required an explicit terminal state.

The completion implementation:

1. Defines one safe overflow transfer outcome for an address-valued
   candidate set: clear concrete identity, target, and candidate locations;
   retain no subset; and record a durable non-source terminal state/reason
   that states the bounded candidate merge exceeded analysis capacity.
2. Applies that outcome in every address-value candidate merge path, including
   the unified storage/call consumer observation and typed-flow joins. Do not
   introduce a larger hidden cap, keep an arbitrary first candidate, or add a
   renderer-side recovery path.
3. Ensures planning, JSON export, source-quality validation, and corpus audit
   distinguish this terminal state from a resolved, finite, external, invalid,
   or ordinary unknown target. It must receive no symbolic expression, label,
   declaration, or numeric rendering workaround.
4. Adds a focused fixture for a five-way compatible pointer join that
   reaches a storage consumer and a proven call consumer. Assert that neither
   consumer retains a concrete source target or candidate subset, that the
   terminal reason is durable, and that rendering remains exact without a
   symbolic expression for the unproven value.
5. Passed the release C suite (including 582 IR tests), 30 manifest tests, a
   fresh exact Pandora regeneration with zero diff ranges, and a fresh
   eight-worker corpus build in 437.6 seconds. The corpus audit reports 70
   consumers across seven targets (45 storage, 18 local-function inputs, and
   seven platform/API inputs), with no production candidate-overflow row and
   no partially retained candidate outcome.

This is a correctness completion, not an extension task. The following
extensions remain separate.

## Non-Goals

- Treating every large or aligned immediate as a pointer.
- Inventing target objects for unmapped runtime/external addresses.
- Replacing the shared render planner or adding a second symbol mechanism.
- Recovering full composite object layouts in this proposal.
- Whole-program alias inference, speculative call summaries, or retaining an
  address value across an unknown clobber.

## Deferred Composable Extensions After Completion

These are extension tasks, not hidden completion criteria for this proposal.
They must consume the address-value facts and render plans established here;
they must not recreate a second pointer-analysis or symbol mechanism.

For each item encountered during the main task, add a short dated entry under
its heading or bullet recording: the stable fixture/corpus/Pandora evidence;
why the main-task transfer rules correctly stop; the additional durable fact or
analysis model required; the expected render-plan consequence; and any
dependency on another deferred item. This turns the section into a precise
handoff design record while preserving the main task's boundary.

1. **Indexed, affine, and interior-address values.** Preserve element type,
   bounds, and addends through scaled indexing and address formation, so an
   address can resolve as an array element, field, or interior source range
   rather than only `symbol+offset`.

   *2026-07-28 handoff:* Pandora `s0:0004D3F0:instruction` reads an indexed
   pointer-table element (`abs_0_0005D416(pc,d0.w)`) before storing it in
   `interaction_message_ptr`. The current main path correctly stops because
   the scaled index does not prove a single address identity. A future fact
   needs table identity, element type, index domain/bounds, and addend; the
   render-plan consequence is a typed table-element expression only when that
   proof exists. This composes with pointer-table recovery below.

2. **Function summaries and callback contracts.** Derive proven typed pointer
   parameters, returns, escapes, clobbers, and indirect callback signatures;
   apply summaries interprocedurally only when their contract is durable.

   The main task consumes an already durable local-function, platform/API, or
   callback input contract as a consumer. This extension begins only where the
   framework must derive a new contract, preserve a return identity, or infer
   an escape; it must not be smuggled into the main task as a fallback summary.

   *2026-07-28 handoff:* resolved callback-slot stores such as
   `s0:000004B2:instruction` (`move.l a0,app_vertical_blank_callback(a6)`) do
   not retain a producer expression. The current main path correctly leaves
   them non-symbolic: no call/return or callback contract proves where `a0`
   came from. A future summary must carry return identity, escapes, clobbers,
   and callback signature; only then may the common render plan express the
   originating source value.

3. **Alias and control-flow refinement.** Distinguish identical object
   identity, compatible but unknown pointer domains, finite candidate sets,
   and invalidated aliases across joins and calls.

   *2026-07-28 handoff:* Pandora `s0:0004D410:instruction` and
   `s0:0004D560:instruction` store finite candidate values to
   `interaction_message_ptr`. The current main path preserves the candidates
   and does not invent a label or select one. A future model needs durable
   candidate-set identity and alias/join refinement; its render consequence is
   a symbolic expression only after a single compatible identity is proven.

4. **Pointer-table and chained-dereference recovery.** Carry the same facts
   through pointer tables, dispatch tables, object arrays, and repeated loads
   so typed indirect calls and data accesses compose.

   *2026-07-28 handoff:* the `s0:0004D3F0:instruction` indexed table read is
   also the concrete pointer-table trigger. It must consume the table/index
   fact from the indexed-address extension rather than introducing a renderer
   exception or a second source-symbol mechanism.

5. **Composable struct-instance and embedded-layout recovery.** Model one
   source range as ordered typed elements—prefixes, gaps, embedded records,
   arrays, and explicit overlays—using the reliable object edges from this
   proposal rather than a target-specific layout renderer.

### Implementation-ready extension subtasks

Every subtask extends the canonical address-value facts and the existing
render-plan path. None may add compatibility fields, heuristic recovery,
target-specific renderer exceptions, numeric fallback rendering, or a parallel
symbol mechanism.

#### A. Indexed, affine, and interior-address values

**Evidence and boundary.** Pandora `s0:0004D3F0:instruction` reads an indexed
pointer-table element (`abs_0_0005D416(pc,d0.w)`) before storing it in
`interaction_message_ptr`. The current model correctly stops because the
scaled index does not prove one source address.

**Work.** Add a durable address-expression fact containing base-object
identity, signed addend, element stride/type, and an index-domain proof. Add
transfer rules for effective-address formation, scaled indexes, and compatible
add/subtract operations. Validate bounds, alignment, overflow, and code/data
ownership before materialising a target.

**Investigation result (2026-07-29).** `M68kTableDescriptorIR`,
`M68kTableConsumerIR`, and `M68kTableEntryIR` already retain table range,
entry width/count, kind, target/consumer linkage, and mask/compare/loop index
domains; JSON already exports those facts. The new expression fact must link to
that existing table identity and its stable source coordinates, not copy table
bounds or introduce a second index classifier. Pandora's `andi.w #12,d0` plus
the four longword entries at `abs_0_0005D416` is the positive fixture.

**Acceptance.** Fixtures cover one indexed element, an in-range finite set, an
interior field address, and invalid/out-of-range cases. Rendering produces a
typed table-element or interior expression only for a proven identity; every
other case remains explicitly non-source. Pandora exports the table/index fact,
whether or not its present index domain is sufficient to render symbolically.

**Dependency and benefit.** This is the prerequisite for indexed work in D. It
turns raw address arithmetic into typed provenance and enables safe symbolic
indexed/interior operands without relaxing unsupported cases.

**Implementation progress (2026-07-29).** The first A slice now exports a
canonical `indexed_table` address-expression fact from source analysis.  It
links its consumer instruction and operand to the existing table descriptor by
stable section/offset coordinates, carries normalized table-relative addend,
decoded index register/scale, and element stride, and deliberately leaves
range, entry kind, and index-domain evidence owned by the descriptor and its
consumer.  It has no renderer-time reconstruction path.  The recovery merge
enriches an authoritative seeded pointer-table range with the decoded consumer
and index evidence while retaining that range's original entry-count proof.
Pandora now proves the intended four-longword table at `s0:0004D416`, its
`d0` mask domain `0..12`, a four-byte stride, and a zero normalized addend;
its exact full-file round trip passes.  Focused fixtures cover a local indexed
pointer table and a finite loop-bounded PC-relative table expression.  A
second completed slice adds `static_interior`: only an accepted decoded data
target strictly inside an accepted structured-data range may produce it; the
fact stores that range's generic base coordinates and a non-zero addend.  A
PC-relative `lea` fixture proves `base+2`; the producer rejects boundary,
zero-addend, unowned, conflicted, overflowing, or non-code candidates.
At that point Pandora exported no direct `static_interior` fact, which was a
normal absence of an accepted direct source-range proof rather than a rendering
fallback. The frozen render plan now consumes a matching `static_interior` fact, declares the base
range label, and renders `base+addend`; the former renderer-side accepted-code
anchor search has been removed. A fixture verifies both the rendered
`lea.l loc_0_00000006+2(pc),a1` and the planned base/addend. The affine
transfer slice now uses the shared CFG typed state rather than a back-scan: a
source-address register carries immutable origin coordinates plus one signed
accumulated addend, while retaining its resolved current target for existing
typed-flow clients. `lea`, compatible address-register copies, immediate
add/subtract, auto-update, and CFG joins transfer that one state; an
incompatible join, arithmetic overflow, or ordinary clobber clears it. Type
loss no longer incorrectly clears a still-proven source identity. The final
typed-flow pass exports `affine_address_evidence` (consumer, origin, target,
signed addend, and base register) into source-analysis JSON. Only the
source-quality pass may turn that evidence into `static_interior`, after it
verifies exact arithmetic and an accepted, unconflicted, strictly interior
source-data owner. This keeps derivation, ownership, and render planning in
one ordered graph without renderer reconstruction. A focused fixture proves
`lea` + `adda` + `(aN)` produces both evidence and an owned `base+2`
expression; a negative `adda #-1` fixture exports its evidence but cannot
materialise an out-of-range expression. Further negative fixtures prove that
signed-addend overflow and an unknown call both invalidate the affine identity;
the latter also fixed the pre-existing unsound behaviour in which an unknown
call retained typed registers without a preservation contract. Pandora now
exports 278 affine-use evidence records and 67 validated static-interior
expressions; its full-file reassembly remains exact. A separate copy/subtract
fixture proves that `movea` carries
the same origin and that `suba` derives the correct negative transfer addend
before source-quality normalises the final owned interior offset. Companion CFG
fixtures prove that an identical origin/addend survives a join and that
different addends invalidate the state. Together with the existing indexed
table planner fixture, this completes Extension A's expression and rendering
boundary; no renderer fallback or transfer-local representation remains.

**Planner progress (2026-07-29).** Every selected instruction expression now
retains the stable `address_expression` identity consumed from source analysis.
For a PC-indexed table expression, the planner verifies the exact base,
register class/index, scale, and decoded base target before attaching the table
label; it does not infer a selected element or copy table-domain state. The
finite loop-bounded fixture verifies that plan link, and the Pandora
`s0:0004D3F0` expression reaches the same common path. A structured-range
boundary fixture verifies that a zero-addend target cannot be materialised as
`static_interior`. The affine transfer implementation extends this same
expression identity; it does not create a transfer-local representation.

#### B. Function summaries and callback contracts

**Evidence and boundary.** Pandora `s0:000004B2:instruction` stores `a0` to
`app_vertical_blank_callback(a6)`, but no fact proves the origin of `a0`; its
non-symbolic output is therefore correct.

**Work.** Define durable function-summary facts for proven input contracts,
return identities, register preservation/clobbers, pointer escapes, memory
effects, and callback signatures.  An input or return may be a register, a
defined stack argument/result location, or an explicitly declared
multi-register value; its ABI ownership, width, and stack-cleanup rule are
part of the same fact.  Derive or accept summaries through the normal
analysis/action surface and apply them only at direct local calls and proven
callable-value edges, including callbacks and dispatch-table entries.  An
indirect target becomes callable only through D's proven table/load identity
and a compatible summary identity.  Unknown calls remain clobbers and create
no inferred summary.

**Investigation result (2026-07-29).** The current policy already has durable
`M68kAnalysisFunctionRegisterContract` and
`M68kAnalysisCallbackTableSignature` facts; the Manual Action catalog projects
both into effective metadata. Typed flow applies those facts at function entry,
records their consumers before invalidation, and has conservative local,
platform, and callback-table clobber paths. It also exports narrowly recovered
local-call summaries for known Amiga OS-vector wrapper effects, but those are
inferred platform-effect records rather than durable target function
interfaces; they do not model pointer return identity, escapes, or a general
preservation contract. This subtask must add one target summary
fact/action/projection pipeline and, where the common representation subsumes
the wrapper-specific record, migrate it rather than extending input contracts
or retaining parallel summary models.

**Migration inventory (2026-07-29).** Pandora's local action log has two
historical callback-signature creates (one removed) and nineteen historical
function-register-contract creates (one removed): nineteen active legacy
facts in total, comprising one callback-table interface and eighteen
direct-entry input facts. The migration fixture must include this shape: a
removed create must remain removed after conversion, and two inputs for the
same direct entry must become one summary with two ordered inputs rather than
two competing callable facts.

**Required common summary shape.** One stable callable-summary identity owns
all of the following, and every direct or indirect call refers to that identity
rather than copying interface text into a call-site record:

- callable location (a direct section/offset or a proven callable table-entry
  identity), ABI, and a finite ordered list of input locations;
- input and return value contracts, where a location is a register, stack
  offset, or ordered multi-register tuple and an identity transform may refer
  only to a declared input or a separately proven source identity;
- a complete caller-visible register/stack preservation and clobber partition;
- an explicit memory effect set (read, write, escape, or proven non-aliasing
  access) over durable storage/parameter identities; and
- callback bindings, which connect a proven table-entry callable identity to
  the same summary rather than representing a second callback-only interface.

Absent information is an explicit unknown effect, never implied preservation.
The policy, target metadata, Manual Action payload, effective projection, C
backend, JSON export, and tests must use this one representation.  Delete the
current function-register-contract and callback-table-signature facts/actions
and migrate the recovered local-wrapper effect to it; no adapter may retain
the old fields or reconstruct a summary from them.

**Acceptance.** Fixtures prove register and stack parameters, a multi-register
value, return, preserved value, a declared non-aliasing memory effect, and an
escaped callback value, plus unknown-call, conflicting-summary, incompatible
ABI, unmodelled-memory-effect, and missing-signature negatives. A planned
expression appears only when its complete call chain and every relevant memory
effect are proven. Pandora retains the current callback-store result unless a
durable summary supplies the missing proof.

Function-pointer fields and dispatch-table entries are callable contracts, not
untyped pointer exceptions. The summary representation must therefore cover
their parameter domains, return domain where proven, and call-clobber effects
through the same target-summary identity used by direct and callback calls.

**Dependency and benefit.** Independent of A; composes with C and D. It makes
interprocedural pointer flow explicit and safely improves call, return, and
callback rendering.

#### C. Alias and control-flow refinement

**Evidence and boundary.** Pandora `s0:0004D410:instruction` and
`s0:0004D560:instruction` have finite candidate values for
`interaction_message_ptr`; the current model correctly does not select one.

**Work.** Introduce an identity/alias lattice distinguishing one proven object,
compatible unknown objects, finite candidate identities, candidate overflow,
and invalidated values. Refine register, stack, global-slot, field, and call
joins only from durable path evidence. Preserve provenance, cardinality, and
invalidation in canonical address-value facts.

**Investigation result (2026-07-29).** The current lattice is distributed
through `M68kRenderTypedRegValue`, `M68kRenderTypedStoredValue`,
`typed_reg_merge`, `typed_stored_value_merge`, and the stack/global/field-slot
merge callers. It already represents finite candidates and the explicit
overflow terminal, but not a first-class identity relation or a path predicate.
The extension must centralise the new relation in the shared typed value model
and make every existing merge/clobber path transfer it; it must not bolt a
second alias pass onto rendering.

**Acceptance.** Fixtures cover same-identity and compatible-domain joins,
finite candidates, predicate-refined resolution, clobber invalidation, and
candidate overflow. Only a single proven identity is rendered symbolically;
finite and overflow results never receive a symbolic target. Corpus reports
each lattice outcome distinctly.

**Dependency and benefit.** Composes with A and B but can start independently.
It reduces avoidable ambiguity while retaining the completed no-speculation
rule.

#### D. Pointer-table and chained-dereference recovery

**Evidence and boundary.** `s0:0004D3F0:instruction` is both an
address-expression and pointer-table case. Current analysis does not carry its
pointee identity through the load to the typed store.

**Work.** Consume the existing descriptor, consumer, entry, range-ownership,
and data-reference facts as one table-entry contract. Add typed load transfer
rules for object arrays, dispatch tables, and repeated field loads. Add only
the missing table-entry pointee and null/invalid-entry semantics, and validate
table bounds, entry representation, and pointee ownership before every
dereference.

**Investigation result (2026-07-29).** The renderer already recognises
pointer-table structured items and runtime pointer-table slots, and callback
dispatch has a narrow table-identity proof. Those paths are specialised and do
not yet yield a canonical address value for a general table load. The extension
must generalise that one proven table-entry-to-value transfer, then have the
existing consumer/planner path render it; it must remove rather than duplicate
any specialised value propagation made redundant by the common transfer.

**Acceptance.** Fixtures cover direct and indexed loads, null/invalid entries,
pointer-to-pointer chains, typed indirect calls, and dispatch targets. They
also prove that a data pointer cannot be called until a compatible callable
contract is linked to its loaded identity. Rendering uses the existing
table/object symbols only for proven links. Pandora gets a table-to-store proof
or a precise missing-fact report.

Null, sentinel, and invalid-entry semantics are part of the table-entry
contract. They are explicit terminal values, not absent target mappings, and
must remain non-symbolic unless a target's durable type contract assigns a
specific source-visible representation.

**Dependency and benefit.** Indexed table loads require A; a direct-load slice
may stand alone. This enables readable table, object-array, dispatch, and
chained field reconstruction.

#### E. Composable struct-instance and embedded-layout recovery

**Evidence and boundary.** Pointer and field facts exist, but source ranges
need one general representation for prefixes, explicit gaps, embedded records,
arrays, and overlays. Pandora's world-position/world-object families are the
intended proof domain.

**Work.** Extend structured-data/layout facts with composition trees of
ordered, non-overlapping owned elements and explicitly declared overlays. Each
element carries source range, type/size, ownership, and evidence. Make pointer
and field analysis resolve through those elements; unknown bytes remain gaps.

**Investigation result (2026-07-29).** Current Manual Actions and effective
metadata already support flat data-block layouts, typed elements, custom
struct bindings, fixed-stride arrays, custom fields, generated gaps, and
range-ownership conflict checks. They do not represent parent/child element
identity, an embedded-instance edge, or a validated explicit overlay. Pandora
already contains the suitable minimum proof: the 12-byte world-position
descriptor records have the eight-byte `world_position_descriptor_prefix` and
an explicit remaining four-byte gap. The new model must extend those existing
layout identities with composition, not replace the data-block or RS renderer.

**Acceptance.** Fixtures cover prefix-plus-gap, embedded record, instance
array, permitted overlay, rejected conflicting overlap, and embedded
pointer/field resolution. Pandora proves one composed layout with exact byte
coverage and exact reassembly; source uses existing struct declarations and
data bindings without redundant labels.

**Dependency and benefit.** It consumes the canonical value/consumer model and
composes strongly with D, but can otherwise proceed independently. It converts
isolated field facts into accurate, readable object instances without inventing
layout.

### Additional evidence-backed extension tasks

The following tasks were investigated after A--E. They are deliberately
grouped by their shared durable model, rather than added as one-off support for
the Pandora examples. They remain deferred work: the completed main task does
not imply any of these transfers.

#### F. Canonical relative/relocated expressions and storage access properties

**Evidence and boundary.** Facts-v2 already recognises relocation anchors,
`lea` PC-relative targets, platform PC-relative section anchors, and
PC-relative interior-data anchors. The renderer already has separate
PC-relative and base-relative spelling support. Those are decode/render facts,
however; `M68kAddressValueIR` currently has a scalar source value/target and
does not own a durable expression tree. Custom struct fields carry scalar or
pointer value kind, but no read/write/volatile/immutability property. Existing
platform range metadata also distinguishes runtime mappings without supplying
a unified object-access contract.

**Work.** Add one canonical address-expression node referenced by address
values. It expresses a source or runtime base identity, relocation provenance
where present, signed addend, PC/base-relative origin, and optional affine
index proof from A. Reuse existing decoder relocation/PC-target and range
ownership identities; delete renderer-only expression recovery when the common
node subsumes it. Add a storage-property fact to the same identity graph with
access intent (`read_only`, `write_only`, `read_write`, `volatile`) and lifetime
class (`immutable_source`, `persistent_state`, `transient_runtime`,
`hardware_or_platform`). A pointer type, address space, and storage property
remain distinct facts.

**Proof rule.** The expression is symbolic only if all of its terms map to one
representable source identity with valid signed arithmetic and ownership. A
runtime, hardware, external, volatile, mutable, or unclassified identity may
still be typed but cannot be constant-folded, made into source storage, or
treated as immutable. Relocation itself proves a link, not pointee type or
mutability.

**Acceptance.** Fixtures cover PC-relative, relocation-derived, base-relative,
and signed interior expressions; representable and non-source address spaces;
and read-only, mutable, and volatile stores/loads. They prove that the existing
PC-relative spelling comes from the canonical expression after migration, that
mutable/volatile values never receive immutable propagation, and that an
address-like scalar without an expression contract remains numeric. Pandora's
existing PC-relative `lea` sites provide a real-target migration regression.

**Dependency and benefit.** Extends A and the cross-cutting address-space rule.
It removes duplicate expression recovery while making relative references,
relocations, and access intent available to D/E and source-quality analysis.

#### G. Object-instance identity, alias lifetime, and write provenance

**Evidence and boundary.** Current typed flow preserves pointee struct names,
finite candidates, and explicit candidate overflow, but has no first-class
identity relation for a particular object instance or a mutation generation.
Pandora has a named `world_object_shared_prefix` and a `player_world_object`
data-block layout, but these prove type/range facts rather than that two
register paths name the same live instance. Existing clobber logic invalidates
register state conservatively; it does not record which object write made an
alias stale.

**Work.** Extend C's identity lattice with stable instance identities for a
proven static object, a proven array/table element, or a named runtime storage
slot. Attach a monotonically derived write-provenance generation to each
mutable storage identity and carry alias edges only through lossless transfers.
Loads may reuse a value only when their storage identity and generation match;
stores create a new generation and invalidate dependent cached facts. Do not
invent heap allocation/lifetime recovery: unknown allocation, escaping pointer,
or opaque write produces an explicit invalidated/unknown state.

Calls consume B's memory-effect contract rather than a register-only
preservation rule: every opaque, incompatible, or potentially-aliasing write
invalidates the affected mutable instance generations.  A declared
non-aliasing read-only effect may preserve only the identities it explicitly
names; it cannot preserve memory merely because no register was clobbered.

**Proof rule.** Same type never means same instance. A field chain may render
with a coherent instance base only after an instance edge and compatible
generation are proven. An object mutation invalidates aliases according to the
declared storage property from F; immutable source storage is the only class
whose generation is stable by definition.

**Acceptance.** Fixtures cover two distinct same-typed objects, a lossless
copy retaining one identity, a mutable field write invalidating a prior loaded
pointer, an immutable source pointer retaining identity, and an unknown call
or escaped pointer invalidating it. Pandora must either demonstrate one
world-object instance chain or export the exact missing instance/lifetime
proof; it may not conflate all `world_object_shared_prefix` values.

**Dependency and benefit.** Requires C and F. It makes repeated object access
and stale-pointer prevention more accurate without speculative object recovery.

#### H. Interprocedural summary fixed point

**Evidence and boundary.** The framework has a reachable-code fixed point, and
typed flow has a bounded local callee preservation walk (depth four with fixed
work/visited limits). It also has durable register contracts and callback-table
signatures, plus a narrow recovered Amiga-wrapper effect record. It has no
call-graph/SCC summary solver, so recursive or mutually recursive pointer
return, escape, and preservation facts cannot converge as one general model.

**Work.** B's target summary becomes a monotone interface over canonical value
identities: typed inputs, returned identity transform, escapes, writes,
preserved/clobbered registers, and callback/indirect-call signature. Build a
direct/proven callback call graph from existing facts, condense it into SCCs,
and iterate summaries to a declared finite lattice fixed point. A summary is
usable only after its SCC reaches convergence; unresolved indirect edges,
unknown callees, or lattice-cap overflow yield explicit stop reasons. Migrate
the overlapping wrapper record into this representation rather than keeping a
parallel effect model.

**Proof rule.** No provisional result from an in-progress recursive summary may
reach rendering. Summary joins retain only identities valid on every returning
path, and any unmodelled write/escape invalidates the relevant value. SCC size,
iteration, and value-set limits are explicit terminal evidence, never silent
depth cutoffs or retained subsets.

**Acceptance.** Fixtures cover self recursion, mutual recursion, a convergent
typed return, an escaping callback, an SCC with one unknown callee, and a limit
overflow. JSON records the summary/SCC proof chain and terminal reason.
Existing direct/callback contract fixtures retain their results through the
common solver, and the old bounded-preservation result is removed or subsumed.

**Dependency and benefit.** Extends B and C. It converts presently local call
contracts into sound reusable interprocedural gains without a compatibility
summary path.

#### I. Relational path constraints and discriminated layout variants

**Evidence and boundary.** Table descriptors already preserve mask, compare,
and loop index domains, but they do not attach a predicate to a CFG edge or
relate `index`, stride, count, and a later access. The CFG carries only edge
kind. Custom structs and structured layouts are flat; they have no discriminant
field, legal variant set, or edge linking a tag comparison to an active layout.
Pandora's extensive shared world-object prefix makes this a plausible future
proof domain, but it presently supplies no accepted subtype/tag contract.

**Work.** Add canonical predicate facts tied to a CFG edge and originating
instruction: signed/unsigned equality or range, masked domain, affine relation,
and discriminant equality. Compose only predicates that dominate a consumer on
the same proven path. Add a discriminated-layout fact whose stable base layout,
tag field, legal tag/range, and variant layout identities are explicit. A
variant access resolves only when the active predicate proves exactly one legal
variant; otherwise it remains a base-layout/gap access or an explicit ambiguous
variant state.

**Proof rule.** A compare nearby in listing text is not a predicate proof.
Predicate scope ends at joins, writes to its inputs, calls that may clobber
them, or CFG paths not dominated by the condition. Overlaps are legal only as
declared variants selected by a discriminant; generic overlays do not imply a
union and cannot select a field.

**Acceptance.** Fixtures cover `index < count` plus stride, mask-derived
domain, predicate loss at a join, a tag-selected variant, unknown tag, invalid
tag, and overlap rejection. Rendering obtains a table element or variant field
only on the dominated path. Pandora reports a candidate only if an existing
tag/prefix/table fact supplies the complete durable contract; otherwise the
report names the missing discriminant evidence.

**Dependency and benefit.** Extends A, C, D, and E. It resolves avoidable
finite ambiguity and renders subtype-specific fields while preserving the
no-speculation rule.

#### J. Evidence-assisted unlock queue

**Evidence and boundary.** The corpus opportunity report already exposes
consumer outcomes and stop reasons, while Manual Actions can record several
durable facts. It does not compute which smallest missing fact would improve
the largest set of blocked canonical graph paths. Existing report aggregates
therefore measure work but do not prioritise the best review investment.

**Work.** Add a read-only derived report over canonical stop-reason evidence.
For each missing durable fact identity, group blocked values/consumers and
calculate the exact downstream renderable opportunities unlocked if that fact
were accepted. Rank only by stable, auditable measures such as affected
consumer count, direct xref count, expression depth, and target coverage; do
not predict semantics or mutate target state. Each row links to the normal
catalog action only when that action, its durable identity, and its verifier
already exist. Otherwise it reports a missing command-surface capability.

**Proof rule.** The queue proposes evidence to investigate, never an inferred
field name, type, table bound, signature, tag, or rendering. A row disappears
only when reanalysis removes its stop reason; accepting a fact that still fails
the graph proof produces a changed stop reason, not a claimed gain.

**Acceptance.** Fixtures construct several blocked consumers sharing one
missing table/domain or callable/layout fact, plus independent blockers and an
unsupported action. The report groups only the shared stable identity, gives a
reproducible rank and prospective impact, creates no Manual Action/output
change, and its before/after diff attributes each actual gain to the accepted
fact. A corpus run demonstrates at least one real grouped opportunity or
explicitly reports that no current corpus fact has multiple blocked dependents.

**Dependency and benefit.** Consumes the stop-reason, xref, action, and corpus
contracts above. It is the safe mechanism for converting analysis evidence
into fewer, higher-leverage manual fact decisions.

### Cross-cutting expression graph, review, and measurement contract

The extensions must improve one evidence graph, not independently make more
operands look symbolic.  The canonical address value remains the value node;
the extension-specific facts supply the proof edges that explain its identity,
type, range, and permitted transfers.  Render planning consumes that graph
once.  No extension may derive equivalent state again from rendered text or
from a target-specific scan.

#### Normalised stop reasons

The present terminal kind is deliberately coarse enough to preserve sound
output.  The extensions need a stable *why-not-further* classification beneath
it, so an unresolved row directs review to the missing fact rather than
presenting an undifferentiated "unresolved pointer".  Define one closed,
versioned stop-reason enum owned by the canonical address-value/expression
model.  Its members must describe proof boundaries, not renderer symptoms:

- missing or incompatible pointer/type contract;
- missing table descriptor, entry typing, index domain, bounds, alignment, or
  ownership proof;
- unknown, conflicting, or clobbering call/callback contract;
- identity conflict, finite candidate set, candidate overflow, or absent path
  predicate; and
- missing composition ownership, illegal overlap, or untyped/invalid pointee;
  and
- null/sentinel semantics, an incompatible address space, or invalidated
  dependent evidence.

Each terminal value and blocked expression carries exactly one primary reason;
optional evidence links identify every contributing fact. Every bounded
analysis operation declares deterministic work, iteration, SCC, and candidate
limits at the model boundary; reaching a limit produces the relevant terminal
reason and does not retain an arbitrary partial state. Existing free-form
`terminal_reason` text becomes a generated explanation of this canonical
reason, not a second classification channel.  The design must migrate current
terminal outcomes to the enum and delete any duplicate per-report stop-reason
logic.  A well-typed expression may therefore remain explicitly non-symbolic;
that is a successful sound-analysis result, never a numeric rendering fallback
or a source-quality failure by itself.

#### Identity, type, and xref edges

New facts must reference stable existing identities rather than copy mutable
names, bounds, descriptions, or rendered spellings.  Add only the following
edge kinds as the applicable subtasks need them:

```text
address value -> expression proof -> table descriptor / entry / index-domain
address value -> consumer -> durable storage or callable contract
address value -> pointee identity -> later proven dereference or call target
layout instance -> ordered element -> embedded layout / gap / declared overlay
```

The source-analysis JSON and corpus rows derive their human-readable labels
from those identities at export time.  They must expose both directions of an
edge (producer-to-consumer and consumer-to-producer; table/layout-to-use and
use-to-table/layout) without denormalised arrays of copied descriptions.  A
missing reverse edge is a data-model defect, not something the renderer may
recover by scanning operands.

Pointee type and pointer value identity are separate: a type restricts valid
transfers and dereferences, while an identity names the one proven object,
table entry, interior range, or finite candidate set.  A type alone never
licenses a symbolic target.  Conversely, an identity is not usable through a
dereference until the edge supplies compatible pointer width, type, ownership,
null/invalid-entry semantics where relevant, and bounds evidence.

Every address identity and expression also carries one canonical address-space
classification: source image, target runtime RAM, hardware, OS/library, or
external/unmapped. The classification is a proof constraint, not a rendering
preference. Only source-image identities with representable ownership may
create source symbols; the other spaces receive their existing explicit,
non-source treatment unless a later proposal supplies a proven source-visible
mapping. This prevents a runtime or platform address from acquiring a false
source-storage identity merely because it has pointer type.

#### Review and Manual Action surface

The normal command/catalog path must be designed with B and E, rather than
retrofitted after analysis state exists.  A reviewer may add only durable
source facts: a callable interface/summary, callback signature, table entry
typing or index-domain proof, or a layout-composition/overlay declaration.
They may not attach a desired expression, force a value resolved, or suppress
a stop reason.  Each action requires a fact-specific verifier that checks its
identity, conflict/range rules, projection into analysis metadata, and its
effect on the canonical graph.  Removing or changing a fact must use the same
action model and atomically invalidate/recompute every dependent graph edge,
planned expression, xref, call-summary/SCC result, CFG-dependent transfer, and
aggregate row; it must not retain an obsolete compatibility projection. The
action result must report the invalidated stable identities, so review can
distinguish an evidence change from an unrelated rendering change.

#### Metrics and completion evidence

Extend the read-only opportunity report from the canonical graph, not an
extension-specific side channel.  It must count expression shapes (direct,
indexed, interior, table-load, returned, and composed-field as they become
supported), consumer kinds, terminal kinds, primary stop reasons, and
propagation/dereference depth.  It must also report invalid and conflicting
facts separately from unresolved ones.  Aggregates are for regression and
fixture selection only; no metric may cause automatic target mutation.

Each report regeneration must additionally provide a stable-identity
before/after diff: added, removed, and changed proof chains; symbolic outcome
changes; and stop-reason changes. A gain is attributable only when the diff
names the new or modified proof edge. Aggregate movement without that link is
diagnostic data, not evidence that rendering improved correctly.

For every newly symbolic result, export the shortest complete proof chain from
value producer through its expression, consumer, and any later dereference to
the source identity.  For every non-symbolic result, export its primary stop
reason and the stable identities of the missing or conflicting evidence.  This
gives review prioritisation, bidirectional navigation, and source-quality
diagnostics without lowering the proof threshold.

#### Migration invariants

Each subtask is complete only when its old specialised transfer, report
projection, and renderer inference have either become the common graph path or
been deleted.  There is no adapter that maintains both representations, no
fallback expression source, and no compatibility JSON field carrying
duplicated semantic state.  Fixtures must demonstrate the positive graph edge,
the relevant explicit stop reason, deletion of the superseded special case,
and exact reassembly.  Corpus output must distinguish the new expression shape
or stop reason from pre-existing categories rather than silently folding it
into `resolved` or `unknown`. Negative fixtures must also prove that numeric
values in typed-adjacent code, address-like scalars without a pointer contract,
null/sentinel values, and values invalidated by a clobber do not acquire an
address identity or a symbolic rendering.

For durable action-schema replacement, provide one explicit, versioned
off-line migration command that validates an entire affected target's local
action log, computes its active semantic state, and writes one canonical
summary fact per callable. Its deterministic migration report preserves every
source action identity and ordering, names the new summary identity and all
absorbed input facts, and records each retired create/remove's resulting
semantic state. This report is the historical audit artifact; the new log need
not preserve a one-to-one event shape when several retired inputs become one
summary. The command refuses unknown or conflicting legacy payloads before it
writes. The new runtime accepts only the new action schema; it never reads,
projects, or silently translates retired action kinds. The migration command
is conversion tooling, not a runtime fallback, and its fixture proves that a
retired action record is rejected after migration.

### Research-backed sequencing and common completion gate

1. Start A with the Pandora four-entry masked pointer table, because its
   descriptor, entry range, and index domain are already independently proven.
   First establish a canonical expression that references those facts; do not
   attempt general chained loads in the same slice.
2. Run C as the companion typed-flow cleanup: centralise identity-state joins
   before A or B adds another source of propagated identity. Its fixtures must
   preserve the completed candidate-overflow behaviour.
3. Start D only after A has supplied the table-entry expression contract. A
   direct non-indexed table-load fixture may be implemented first, but its
   representation must be the same one used by the indexed Pandora proof.
4. B can proceed independently once its durable target-summary action and
   projection are designed. Reconcile the existing recovered OS-wrapper effect
   summary during that design instead of adding a second general call model.
5. E can proceed independently from one existing flat data-block layout. Its
   first slice is prefix plus explicit gap; embedded layouts and overlays follow
   only after that ownership model is exact.
6. F follows A's canonical expression identity. Migrate an existing
   PC-relative `lea` proof before adding relocation/base-relative or access
   property forms, so the renderer has one expression source from the first
   slice.
7. G follows F and C. Start with a static or table-element instance and a
   single mutable write generation; do not begin with heap or allocator
   recovery.
8. H follows B and C. Build the summary lattice and SCC solver around existing
   direct/callback contracts, migrate the wrapper-specific effect, then admit
   recursive summaries only after the non-recursive fixed-point proof is exact.
9. I follows the relevant A/C/D/E edges. Establish CFG-edge predicate scope
   before connecting it to an indexed table or discriminated layout; no
   variant rendering begins from a merely nearby comparison.
10. J can start once the normalised stop-reason and bidirectional xref exports
    exist. It remains read-only and must use the normal action catalog rather
    than growing an agent-only recommendation or mutation path.

Every completed subtask must retain exact source reassembly, pass focused C and
Python projection tests, export the new durable fact in source analysis JSON,
and demonstrate one real target result or an explicit evidence-backed reason
that the selected Pandora example remains non-symbolic. The full corpus audit
must show the new outcome category separately; it must not reclassify an
unsupported case as resolved to improve reporting.
