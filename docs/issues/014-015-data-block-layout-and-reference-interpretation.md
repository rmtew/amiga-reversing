Status: Investigation complete; implementation split
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Define the core, agent-visible model for structured data block editing. This is
not a UI editor first; it is durable source-converging capability that the
reversing loop can discover through the command catalog, apply through the
Manual Action Log, verify, and improve over time.

Problem:
Amiga game data often appears as opaque or partially understood byte ranges.
Existing support can classify a whole range, change a literal representation,
name a data symbol, define a struct, or seed a register base. Those mechanisms
do not compose into a durable model for a known-size data block whose elements
can be filled in incrementally, renamed, typed, rendered, and used as analysis
facts.

Investigation result:
Use a new first-class metadata family, not an overload of seeded entities,
manual representations, RSSET regions, custom structs, or runtime-address refs.
Those existing mechanisms remain inputs or projections. A data block layout is
the ordered source model that owns element offsets, widths, names,
representations, type bindings, and optional interpreted-reference semantics.

Chosen source model:
- `DataBlockLayout`: stable layout id, hunk/source range, optional runtime view
  identity, default unit, optional role, label/name, version, and provenance.
- `DataBlockElement`: layout id, offset, width, kind, optional name, optional
  array count/stride, representation, type binding, enum/equate domain,
  reference interpretation, and generated/manual provenance.
- Element kinds: scalar, array, struct, platform struct, pointer/reference,
  padding, gap, and raw.
- The first implementation slice should support scalar bytes/words/longs,
  arrays/runs, padding/gaps, names, and numeric/character representation only.
  Struct binding, platform structs, and interpreted references follow after the
  scalar layout verifier is proven.

Durable identity rules:
- Source-backed layout identity is `(target, hunk, source_start, source_end,
  layout_id)`.
- Runtime-backed layout identity is `(target, source/origin execution_view_id,
  source_start, source_end, runtime_start, runtime_end, layout_id)`. Runtime
  address alone is not durable enough because copied/relocated stages can share
  addresses or source bytes.
- Element identity is `(layout_id, offset)` for stable offset edits. Rename and
  representation changes carry previous name/kind only as context, not as
  required future state.
- Width/type edits may replace an element and invalidate overlapping generated
  element identities. Removal returns the covered bytes to explicit gaps/raw
  elements before rendering.

Manual Action Log schema:
- `create_manual_data_block_layout`: layout identity, source/range locator,
  optional runtime view identity, label/name, default unit, role.
- `edit_manual_data_block_layout`: layout id plus editable layout metadata.
- `remove_manual_data_block_layout`: layout id, with optional removal mode
  `raw|gaps|delete_generated`.
- `set_manual_data_block_element`: layout id, offset, width, kind, name, array
  count/stride, representation, type binding, domain, provenance.
- `remove_manual_data_block_element`: layout id and offset, returning the span
  to gap or raw rendering.
- `represent_manual_data_block_element`: layout id, offset, representation and
  optional symbolic/equate/domain payload.
- `bind_manual_data_block_element_type`: layout id, offset,
  custom/platform type id, array shape, and field path root.
- `interpret_manual_data_block_element_ref`: layout id, offset, width,
  reference kind, base/source evidence, signedness, scale, target locator,
  confidence, and xref-generation mode.

Command catalog surface:
- Command ids use dotted names such as `data_block.layout.create`,
  `data_block.element.set`, `data_block.element.represent`,
  `data_block.element.bind_type`, and `data_block.element.interpret_ref`; these
  map to the Manual Action Log action names above.
- Row/range commands create a layout from selected data rows or explicit source
  ranges.
- Element commands edit/remove/represent/type-bind one selected layout element.
- Target commands manage reusable enum/equate domains and platform/custom type
  references when the edit is not tied to a single row.
- The loop must report missing `data_block_*` support as a blocker. It must not
  compensate with direct metadata writes, comments, scripts, or UI-only state.

Projection and rendering plan:
- Effective metadata merges Manual Action Log layouts with target metadata and
  rejects overlapping manual layouts unless an edit explicitly replaces the
  older layout.
- Data roles provide coarse range intent; layouts provide element structure
  inside the range.
- Manual representations still describe individual literal display when there
  is no owning data-block element. Once an element exists, the element
  representation is authoritative for that span.
- Data-symbol names can name the block label or referenced target labels, but
  element names live on the layout.
- Target equates/enums provide reusable symbolic domains for element values.
- Target-local `EQU` definition value representation is owned by
  `014-020-target-equate-value-representation.md`; data-block layouts consume
  equate/enum domains rather than owning EQU definition rendering.
- Custom/platform structs are referenced by compact ids; parsed platform include
  text is not copied into every manual action.
- Rendering must preserve exact rebuild and degrade safely to `dc.*`/raw gaps
  when a higher-level notation is unavailable.

Platform type integration:
- Platform structs/enums are referenced by parsed include identity, such as
  include source plus symbol/type name or stable KB id.
- Custom structs use existing target custom struct identity by name plus field
  offsets.
- First platform-struct support should bind a field to a known type and verify
  rendered field paths only after `014-012` proves custom typed-field rendering.

Type-flow and xref projection:
- Interpreted refs should project into a dedicated manual interpreted-reference
  fact family first, then generate runtime-address refs/xrefs and symbolic
  representations where the reference kind is supported.
- Generated xrefs must be bidirectional and must be removable by deleting the
  owning layout element/ref interpretation.
- Type-flow from pointer/base fields should be automatic only for locally
  proven cases. Ambiguous propagation creates review items, not silent facts.
- RSSET/app-slot refinement composes through existing region and typed-access
  paths after the layout element can identify a base-relative field.

Auto-analysis integration:
- Scalar layouts in the first slice consume existing analysis evidence and
  affect rendering only; they must not silently create xrefs or type facts.
- Interpreted-reference elements may generate analysis-facing xrefs only through
  the dedicated interpreted-reference projection in `014-018`.
- Type/platform bindings may generate type-flow facts or review items only
  through the typed binding projection in `014-019`.
- Every generated analysis fact must retain the owning layout/element/ref or
  binding identity so removal can delete the derived fact exactly.
- Mistake recovery must be first-class: layout, element, interpreted-reference,
  type-binding, and domain actions need corrective remove/unbind/clear actions
  that restore prior raw/gap/rendered state or the previous projected fact
  without deleting unrelated user work.

Verifier plan:
- Replay verifier: Manual Action Log reload produces the same layout/element
  state.
- Render verifier: source includes the expected labels, directives, element
  widths, and representations.
- Exact rebuild verifier: direct rebuilt binary matches original.
- Removal verifier: deleting a layout/element returns the range to raw/gap
  rendering and removes generated facts.
- Xref verifier: interpreted refs create expected source/target xrefs and
  symbolic text.
- Type-flow verifier: supported type bindings produce expected propagated facts
  or expected review items.
- Loop verifier: command execution reports the action-specific verifier, not a
  generic round-trip fallback.

Real target example:
GenAm has an ASCII hex digit lookup table at `loc_0_00001442`. Current local
evidence:
- Code at `loc_0_0000140E` loads the table with
  `lea.l loc_0_00001442(pc),a0`.
- It reads `move.b $0(a0,d1.w),d1`.
- It treats negative values as invalid and combines non-negative nibble values
  into `d2`.
- Table bytes map ASCII `0` through `9` to `0..9`, `A` through `F` and lower
  case hex letters to `10..15`, and other entries to `$FF`.

Current rendering is an opaque generated lookup table:

```asm
loc_0_00001442:
    dcb.b $30,$FF ; lookup_table
    dc.b $00,$01,$02,$03,$04,$05,$06,$07,$08,$09,$FF,$FF,$FF,$FF,$FF,$FF ; lookup_table
    dc.b $FF,$0A,$0B,$0C,$0D,$0E,$0F ; lookup_table
    dcb.b $1A,$FF ; lookup_table
    dc.b $0A,$0B,$0C,$0D,$0E,$0F ; lookup_table
    dcb.b $19,$FF ; lookup_table
```

Proposed first-slice rendering keeps exact bytes but makes the layout durable:

```asm
loc_0_00001442:
    ; data_block_layout ascii_hex_digit_value
    dcb.b '0',$FF
    dc.b 0,1,2,3,4,5,6,7,8,9
    dcb.b 7,$FF
    dc.b 10,11,12,13,14,15
    dcb.b $1A,$FF
    dc.b 10,11,12,13,14,15
    dcb.b $19,$FF
```

This is not speculative: the table base, indexed read, invalid sentinel, and
nibble accumulation are all local xref-backed evidence. It is also deliberately
limited: it proves scalar layout and representation without requiring enum
domains, interpreted refs, or type-flow in the first slice.

Child implementation issues:
- `014-016-data-block-layout-core-metadata.md`: first-class layout/element
  metadata, Manual Action Log projection, identity, overlap/removal behavior.
- `014-017-data-block-layout-command-render-verifier.md`: command catalog,
  scalar layout rendering, replay/render/removal/exact rebuild verifiers, GenAm
  hex table smoke.
- `014-018-interpreted-data-reference-facts.md`: manual interpreted-reference
  facts, symbolic rendering, generated bidirectional xrefs, and removal.
- `014-019-data-block-type-binding-and-platform-structs.md`: custom/platform
  struct binding, enum/equate domains, arrays/nested structs, and type-flow or
  review-item projection.

Rejected alternatives:
- Extending `SeededEntityMetadata` only: it can classify/name a range but cannot
  own ordered child elements or generated per-element facts.
- Extending `ManualRepresentationMetadata` only: it controls display style but
  cannot express field width, type, arrays, gaps, or xrefs.
- Treating RSSET/custom structs as the general layout model: those are specific
  type systems and do not cover arbitrary byte tables or parser data.
- Runtime address as layout identity: copied/relocated execution views require
  source/origin identity as well.

Remaining unsupported sub-capabilities:
- Symbolic enum/equate domains for element values.
- Interpreted refs for absolute/runtime, base-relative, table-relative,
  PC-relative, signed displacement, and scaled-index values.
- Custom/platform struct field rendering inside arbitrary data blocks.
- Automatic type-flow from layout fields.
- UI editor affordances over the same durable model.

Acceptance criteria:
- Investigation deliverables above are summarized coherently in this issue.
- Proposal 014 matrix is updated with the chosen support model and unsupported
  sub-capabilities.
- One real target example identifies current rendering, proposed rendering,
  local evidence, and verifier expectations.
- Narrow child implementation issues exist for the accepted first slice and
  deferred reference/layout/type-flow capabilities.
- No production code path is changed by this investigation-only issue.

Cleanup / deletion:
Delete after the child implementation issues are closed and Proposal 014 is
updated with the final support state.
