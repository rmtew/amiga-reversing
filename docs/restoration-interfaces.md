# Restoration interfaces

The UI, CLI and MCP adapter use the same resident project server and restoration
operations. Native facts, Manual Action Log and Decision Journal remain the
owners of state. The adapters neither parse rendered assembly nor maintain a
second semantic store.

## Run locally

```sh
uv sync --extra mcp --no-dev
make -j4
uv run --no-dev --extra mcp python -m amiga_reversing.tools.disasm_server --host 127.0.0.1 --port 8123
```

Open `http://127.0.0.1:8123/<target-id>`, select a source row and choose **Restore**.
The panel exposes bounded exploration, inspection, catalog-backed interpretations,
exact verification, configured runtime probes, review and undo/redo. The existing
Navigate panel also fetches references on demand with explicit next-page controls.
A rejected or stale change retains the interpretation form; inspect the new state
before deciding whether to resubmit it.

The `oracle` extra is separate from portable development dependencies. It resolves
public PyPI `machine68k`; it does not reproduce the former repository-local patched
Windows wheel (`0.4.2.dev0+g61600df53.d20260308`). That wheel was absent in this
cloud checkout. Moving the optional dependency does not assert compatibility of
version-specific oracle tests.

Persistent native row and window responses project exposed `bytes` from each
row's canonical source offset, including later lines of grouped scalar arrays.
The byte cache is bounded; missing or incomplete bytes are not full-field proof.
The forward-only preview can retain a parent span for grouped data lines, so its
metadata must not be used as per-line byte evidence. Use the persistent lookup
for source-value validation and catalog mutations.

## CLI

```sh
python -m amiga_reversing.tools.restoration --target TARGET state
python -m amiga_reversing.tools.restoration --target TARGET query \
  --kind symbols --query descriptor --limit 20 --expected-revision REVISION
python -m amiga_reversing.tools.restoration --target TARGET query \
  --kind references --symbol SYMBOL --limit 20 --expected-revision REVISION
python -m amiga_reversing.tools.restoration --target TARGET inspect \
  --section-index 0 --source-offset 0x6676 --expected-revision REVISION
python -m amiga_reversing.tools.restoration --target TARGET query \
  --kind functions --section-index 0 --source-offset 0x6676 \
  --relation unresolved_transfers --expected-revision REVISION
python -m amiga_reversing.tools.restoration --target TARGET query \
  --kind typed_pointers --struct-name TYPE --exceptions-only --limit 20 --expected-revision REVISION
```

Poll `state` until `ready` before querying. Stop if its job reports `failed` and
inspect the retained error: status reads do not retry a failed build for the
same revision. A changed revision or an explicit listing-build request can
start a new build. Responses include `revision`,
`subject_revision`, explicit scope and unknowns. Pages contain `items`, `total`
and `next_cursor`; send that cursor with the same query and revision to continue.
The server rejects stale cursors rather than joining different snapshots.

`typed_pointers` selects canonical bound fields with explicit pointer semantics.
Use `struct_name` and/or `section_index`, with optional `source_offset` (inclusive)
and `end_offset` (exclusive), to inspect a source family. Interval bounds require
the section and select **field starts**; returned fields retain their complete
native extent even if an upper bound cuts through one. Selection happens before
native row lookup, so unselected families do not inflate work or counts. Cursors
bind the complete filter set and refuse reuse with another interval.
Its total and outcome/reason
counts cover the entire selected population, while field details are paged.
With `exceptions_only: true`, `total` counts unresolved/invalid fields and
`population_total` retains the full denominator. The UI's **Pointer exceptions**
button uses this same operation; resolved and null fields need no individual action.
The native render plan owns each resolution; the report does not infer pointers
from names, comments, or numeric values. Source boundaries, missing mappings,
conflicts and missing native results remain explicit. For a standalone summary:

```sh
python -m amiga_reversing.tools.typed_pointer_report --target TARGET --summary
```

`query` text is a case-sensitive literal substring of symbol names for `symbols`
and generated instruction text for `instructions`; it does not normalize numeric
values or search instruction annotations. Function queries match names without
case sensitivity. Nonempty text queries for `references`, `fields`, `edges` and
`gaps` are refused. Use their supported symbol, field or coordinate filters.

`inspect --row-kind label` selects the label catalog at an address. Function
relations include `callers`, `callees`, `ranges`, `owned_blocks`,
`unresolved_transfers`, `entry_evidence` and `name_evidence`. Ownership is a
conservative candidate, not proof of a complete function boundary.

Native CFG queries include accepted traced destinations for indirect transfers,
using each code-start fact's source section and instruction offset. A resolved
destination edge identifies a known candidate; it does not close the target set.
The unresolved edge remains alongside candidates because discovery does not
establish completeness across mutable stores or all callers. Table addresses,
cross-section aliases and unaccepted instruction starts are not destinations.

Discovery also recognizes an inline resume producer: an address register holds
the source instruction immediately after an unconditional transfer to shared
code. Its continuation provenance travels through the bounded work queue,
including previously accepted code and indirect table destinations. At most
eight distinct states are retained per instruction. Register overwrites and
opaque calls discard the affected provenance; an opaque call return clears all
register/cache values in this extended trace. Ordinary discovery retains its
existing short replay. Multiple traced producer destinations are reported as
`per_caller`, rather than as a jump-table proof. These are known paths, not an
exhaustive caller, lifetime, or callback-effects contract.

For mutation parameters use `--request request.json` (or `--request -` for stdin).
RSSET region renaming requires an explicit `size` from the current declaration.
An omitted extent can otherwise become four bytes and cover neighboring fields.
Existing add/edit defaults and historical records remain supported.

`target.data_block.layout.rename` takes an active manual `layout_id` and `name`.
It reuses the existing sparse layout-edit action, preserving the ID, range,
role, elements, type bindings and interpreted references. Unknown or removed
manual IDs are refused before append. This does not rename source symbols;
use inspected `label.rename` actions for those identities as a separate part
of the same swath. Seeded-only layouts must first have a supported manual
layout identity rather than relying on implicit range/default reconstruction.

`target.data_block.layout.describe` takes an active manual `layout_id` and a
nonempty `role`. It uses the same sparse edit/history path as layout rename,
preserving name, extent, unit, elements, type bindings and reference identities.
Use it to refine a resource's discovered uses without replacing its owner or
rewriting history. Unknown identities and stale revisions refuse the edit.

Current native boundary: an untyped layout element copies its owner role into
the seeded-entity subtype field, whose parser accepts at most 63 bytes. Use a
short role category and retain longer explanations in interpretation evidence
or source comments. A longer role can be accepted on an empty owner but will
fail native preflight when its first element is added; that failure appends no
action. General support for longer free-form roles remains open.

A row `label.rename` explicitly supersedes its predecessor name at the same
section/address within its address domain, including an older manual label
with a different ID. The renamed declaration takes precedence; unrelated
same-address aliases remain available. Repeated row renames retain their name
chain through replay and undo/redo. Original metadata and action history are
preserved. This avoids an accepted rename silently rendering the older name.

`target.data_block.elements.rename` accepts 1..1000 explicit `{layout_id,
offset, name}` selectors. It changes only names of active manual elements,
preserving their widths, types, binding IDs, binding provenance and reference
owners. Duplicate identities, unknown elements and non-name edits refuse the
whole append. Normal undo/redo applies to the single bulk action. This is useful
for propagating a reviewed owner identity without recreating every typed element.
RSSET aggregate extents support 1..32767 bytes through the catalog, metadata
projection and native policy; absolute-storage slots retain their separate limit.
The file is an object of operation parameters, without `operation`. For example:

```json
{
  "expected_revision": "REVISION_FROM_INSPECTION",
  "command_id": "comment.edit",
  "context": {"kind": "row", "locator": "USE_THE_ACTUAL_CATALOG_CONTEXT"},
  "parameters": {"text": "Concrete evidence-backed interpretation."},
  "evidence": {
    "question": "Which behavior does this source implement?",
    "reason": "Describe the inspected facts and the remaining uncertainty.",
    "source_evidence_status": "hypothesis",
    "source_evidence_refs": ["s0:00006676:instruction"]
  }
}
```

The context above is schematic: use the current native locator and element ID
when applicable, plus a command discovered in the catalog. Do not invent locators
or arbitrary manual payload kinds. Supported evidence status is `hypothesis` or `analysis_proven`.

Native policy storage permits 32,768 structured-data items and 32,768 named
labels, allocated on demand. Typed arrays count each expanded leaf field.
Overflow is refused before history append; the bounded counts still fit the
existing 16-bit native counters.

Use `interpret_batch` for a connected set of 1..100 interpretations from the same
inspected revision:

```sh
python -m amiga_reversing.tools.restoration --target TARGET interpret_batch --request batch.json
```

`batch.json` has one top-level `expected_revision` and an `entries` array. Each
entry contains `command_id`, the actual catalog `context`, `parameters` and
`evidence`, using the same shape as the singleton example above. Entries must
omit `operation` and `expected_revision`. All evidence references and command
contexts are checked against the same native artifact before any write. Identical
contexts reuse their resolved rows and catalog only within that preparation; each
command and its parameters are still validated independently. Catalog availability
uses the already validated context rather than resolving it a second time.
Displacement-use witnesses share one native scan within that locked preparation,
keyed by project/projection and artifact identity. This temporary index is discarded
before append, including failed preparations; it is never reused by another request.
The Manual Action Log validates the complete batch and appends it atomically; an
invalid final entry or stale revision leaves both histories unchanged. The
service applies the actions and invalidates the projection once, then returns
`actions`, per-entry `commands`, and the resulting revision. Inspect and verify
that resulting revision before review. Batches do not observe earlier entries
as fresh catalog state, so dependent commands require a new inspection.

For an already-discovered element command, the minimal context is
`{ "kind": "element", "locator": NATIVE_LOCATOR, "element_id": NATIVE_ELEMENT_ID }`.
The batch endpoint resolves that current native element and checks its catalog
before append. A separate client catalog read per operand is redundant when the
command contract is unchanged; preserve native identities and the inspected
revision rather than synthesizing operand values or silently refreshing state.

`target.function_summary.add` also accepts the canonical optional `results`,
`effects` and `note` fields. Explicit register effects must partition all sixteen
general registers; omitted effects remain unknown. The command validates the
complete summary before appending it. `inputs: []` is valid for an effect-only
leaf with no typed pointer arguments; an identity result or input-relative effect
still requires an existing input index. Empty and malformed input arrays remain
distinct. Native metadata reading accepts compact
and indented JSON for these arrays without changing the contract or ABI.

Bounded native callee inference may also publish a generated `hardware_base`
register result with a stable `hardware_base_id`. The proof starts without
caller hardware values, follows original register transfers, and requires the
same full address on every reached normal return. Such a result establishes a
fixed return value; it does not assert that the entry register is preserved.
Partial writes, unresolved calls, conflicting returns and proof limits retain
unknown state. This generated result is not a new target-metadata result kind;
reviewer-authored results remain restricted to `identity_input`. Hardware value
domains consume validated native address uses, including call/CFG proofs,
instead of requiring a second linear lifetime proof. Existing manual operand
representations take precedence over newly inferred value-domain expressions.
The symbol-element catalog does not yet expose numeric representation editing
for an already symbolized SDK literal; replay of earlier accepted bindings is
supported, while adding that editing path remains a separate command gap.

`representation.hardware_offset` binds a decoded address-register displacement
to a registered SDK base's offset domain. The caller supplies `base_symbol`;
the command takes the encoded offset from the native listing element. Native
policy admission requires a known base and field, and rendering checks that
the instruction still contains that displacement. This preserves expressions
such as `aud0+ac_len(a6)` when A6 selects a channel with a runtime stride.
It asserts the literal's meaning, supplies SDK dependencies and access notes,
and creates no runtime address, register identity, or call-preservation fact.
The same SDK access notes also consume validated native hardware address uses,
so explanations survive call and CFG proofs alongside operand names. Pointer
notes inferred from a destination field yield to existing pointer-provenance
notes. Unknown calls and conflicting values remain conservative.

`target.code.hardware_indexed_input.add` declares an explicit entry precondition:
an address register equals a registered hardware base plus `stride` times the
low WORD of a data register. Its `hardware_indexed` object contains
`base_symbol`, `index_register`, `stride` and a sorted closed `index_values`
list of at most eight nonnegative members. The command also requires an entry
address, section, destination register and precondition note. Native admission
checks the registered base, register classes, set capacity and offset extent
before history is appended. Source comments say `INPUT contract`, rather than
presenting the destination as a fixed address or a recovered game struct.

The bounded hardware solver tracks low-WORD constants, moves, immediate shifts
and multiplies, ADDA.W, and DBF's separate backedge/exhaustion states. It unions
closed sets at joins and discards unknown or overflowing sets. Its fixed point
is independent of typed-memory propagation; an exhausted hardware proof budget
publishes no family facts. Calls, unmodelled/partial writes, memory loads and
address autoupdates invalidate the affected domain. Each member must resolve
to the same SDK register-family field before an automatic symbol/note is added.
The resulting `hardware_register_family` facts expose `relative_base_offsets`
and `proof_scope: analysis_entry_contracts`; `address` and `effective_address`
are null. `requires_indexed_input_contract` records whether such an explicit
indexed precondition supplied the bounds, including after scalar transfers and
joins. Literal offset interpretations remain valid fallbacks where these
bounds are unknown. An accepted input precondition is not proof that every
possible indirect caller or opcode supplies it.

Native policy storage accepts up to 16,384 structured data items and 16,384 named
labels after array fields expand. The merged pending interpretation is checked
against the actual binary before any Manual Action Log append; overflow refuses
the whole batch. These checked policy collections use owned heap storage and
retain their `uint16_t` count guards. The authoritative source-analysis arena
remains unbounded; exceeding its optional policy mirror does not discard facts.
When an interior boundary splits a valid typed field into raw rows, the first
fragment retains its field name and states how many of the field's bytes it
contains. Labels, relocation boundaries and bytes remain intact. Conflicted,
out-of-bounds or code-overlapping fields do not receive this fragment annotation.

Run `interpret`, inspect its new revision, then `verify`. Verification returns a
`receipt_id`; review acceptance requires that receipt for the current subject.
`review_batch` reviews 1–100 unique `action_ids` with one decision, reason and
current verification receipt. It validates every action and the complete
decision chain before one atomic append, including supersessions. Its bounded
response contains decision identities, one compact proof and the fresh revision.
A bounded `probe` associates its configured scenario with an explicit question
and verification receipt. “Not observed” records the tested conditions; it is
not proof of unreachability. `history` preserves decisions and shows whether
verification is current. `rollback` takes `action_id` and optional `redo: true`;
it appends through existing history rather than deleting annotations.

Normal target source output is configured through the revision-bound catalog command
`target.source_output.configure` in target context, with `mode` set to `inline`
(default) or `binary_assets`, and optional `minimum_asset_size` (default 256).
The Manual Action Log owns this presentation policy; undo/redo restores it.
Normal regeneration uses the same native asset planner as ZIP export and publishes
relative companion assets, SDK dependencies, and `source-package-manifest.json`.
The native planner uses the selected source symbol for both the asset label and
filename, with a separate target-scoped section/range identity. Unnamed assets
retain provisional names; portable collision handling belongs to that same
native planner. Python validates and publishes its inventory without deriving
asset purpose or boundaries.
Native manual label facts currently accept names up to 63 bytes; widening that
input capacity is separate from preserving names already present in the render
plan.
The manifest guards owned files against edits and removes only obsolete owned
companions. Classification, meaningful tables, pointers, relocations and ambiguous
ranges remain governed by native analysis. First adoption requires the current
canonical source to match freshly rendered inline source. Explicit ZIP export
continues to select its own presentation independently.

Forward EQU expressions over source or asset labels are not supported end to end
by the current C assembler, even when vasm accepts them. For a proved address
value, a numeric named EQU avoids that forward dependency while the evidence
retains its canonical owner/offset relationship. Extending forward dependency
resolution is separate work; do not accept a slice on vasm equality alone.

Custom pointer fields can explicitly declare `pointer_address_domain` as
`mapped_source` or `runtime_only`; omission retains the existing `legacy`
behavior. `mapped_source` requires a unique eligible source mapping and an
expression whose encoded value matches the original. `runtime_only` requires
`pointer_symbol_group` and never falls back to a source mapping. The normal
EQU command can declare a runtime address symbol with `address_domain: runtime`,
`group`, and a positive `extent_bytes`. These extents describe address symbols,
not allocated memory, pointee types, DMA safety, lifetime, or phase exclusivity.
Schema edits propagate through all bound instances; evidence remains required.

Optional structure macros are an export view of the same canonical schemas.
Choose **vasm + structure macros** in Export Source, or use:

```sh
python -m amiga_reversing.tools.source_export TARGET --structure-macros -o compact.s
python -m amiga_reversing.tools.source_export TARGET --structure-macros \
  --binary-assets --verify-package -o compact.zip
```

The HTTP export, restoration client/CLI and MCP export accept the same
`structure_macros` boolean. Expanded source remains the default; export reports
eligible instance and fallback counts. See [macro capabilities and limits](structure-macro-source-export.md).

## MCP

Launch the adapter through an MCP host's stdio configuration:

```json
{
  "mcpServers": {
    "amiga-restoration": {
      "command": "/absolute/path/to/amiga-reversing/.venv/bin/python",
      "args": ["-m", "amiga_reversing.tools.restoration_mcp", "--server", "http://127.0.0.1:8123"],
      "cwd": "/absolute/path/to/amiga-reversing"
    }
  }
}
```

The project server must already run. The adapter opens no listener and only
connects to a local HTTP origin. Its domain tools mirror state, export, query,
inspect, interpret, interpret_batch, verify, probe, review, review_batch, history and rollback. Read operations
are annotated read-only; mutations require explicit revisions. HTTP domain
refusals surface as MCP tool errors, without automatic retries.

The adapter uses the official `mcp>=2.3,<3` Python SDK, structured tool results and
stdio lifecycle: [SDK documentation](https://py.sdk.modelcontextprotocol.io/) and
[transport documentation](https://py.sdk.modelcontextprotocol.io/run/).

## Runtime memory regions and derived artifacts

`target.memory_region.add` records a stable region identity, original
address, size/alignment, CPU placement, persistent lifetime and DMA requirement
through ordinary revision-checked interpretation/history. `query` with
`kind: "memory_regions"` projects native instruction references and bounded
pointer-path obligations. Definitions do not assert relocation safety.
Distinct region identities may overlap: the native projection reports their
exact shared interval and offsets in `overlapping_regions`, with a
`coordinated_source_placement` obligation. A single-region plan refuses with
`overlapping_source_regions`; no joint-move or phase-based split is implemented.
Persistent storage does not mean immutable contents or exclusive ownership.
`source_domain: "mapped_source"` additionally requires a unique contiguous native
materialization for the initial bytes. Plans retain PC-displacement encoding when
the new signed displacement fits; indexed and PC-relative pointer producers remain
refusals. Logical byte extent is distinct from the padded eight-byte Exec lease.

`memory_plan` takes `expected_revision`, `region_id`, integer `destination` and
`memory_class` (`chip` or `slow` for the first A500 contract). Unsupported encoding,
placement, alias, control/frame or access paths remain explicit refusals. The
first proof covers accepted 68000 references and brief addressing forms only;
unclassified bytes, synthesized pointers and future callback changes stay outside
its scope. Lack of references never proves free storage.

`memory_build` additionally requires a current exact `verification_id`. A closed
native plan writes an immutable derived payload and exact instruction rewrite
ledger/manifest under `.runtime-state/restoration/derived/`; original source and
binary identity remain unchanged. The manifest binds both whole payload hashes,
region definition, placement, analysis subject and native plan. Mapped regions
also bind exact source initialization bytes. Runtime binding
recomputes the native proof and validates every changed byte. UI placement/build
controls, CLI operations and MCP tools use these same operations. Pandora's first
keyboard move currently refuses five obligations, so no relocated target artifact
has been built or executed.

Pointer references also expose `frame_prefix`: canonical entry, bounded relative
SP effects, path/state counts and an explicit `absolute_sp: null`. Balanced native
save/restore and direct-call prefixes can support a borrowed normal return;
unknown aliases and other frame effects still refuse. Relative balance does not
establish absolute stack ownership or separation from application/object writes.
[The next proof capability](proposals/044-runtime-memory-relocation-proof.md)
records address provenance and interrupt/context requirements. Conditional build
or runtime guard enforcement is not implemented.

Operand symbol presentations may select a canonical source declaration as well
as a platform symbol or target equate. Immediate target EQUs must match the
decoded unsigned or signed value before append. Decoded bit-number immediates
carry no byte width; equal-value EQUs remain valid for these operands. A requested
presentation can replace a generated immediate-address name; explicit source/SDK names remain
protected. A value EQU keeps resolved address-analysis facts but creates no
unused source-label obligation inside an asset. The append preflight resolves one native
render-plan declaration and persists `source_symbol` with `section_index`,
`source_offset`, `runtime_view` (0/1) and `encoded_value`. It checks the current
native operand value/width and address view before writing history. No Python
load-address arithmetic or generated-label parsing participates. Ambiguous,
missing and mismatched choices refuse the entire batch. The native renderer
checks the identity again and derives the current name from its coordinates,
so renaming a label preserves both the expression and its xref identity.

An explicit data layout with role `opaque_data` and a raw element can be
packaged as an INCBIN through the existing binary-assets output mode. This
classification preserves bytes with unknown purpose; it does not assert media
format, unused storage or relocation safety. Unclassified bytes remain excluded
from automatic asset extraction, and existing label, expression, fixup, ORG and
range-overlap guards still apply.

Typed record cursors support bounded ordinary source reads and destination
stores through postincrement or predecrement EAs. Generated access/width metadata
determines the field address and signed cursor step. Field references on these
modes are comment-only so their encoded syntax and bytes stay intact. A7,
multi-register transfers, multiple EA updates, conflicting base uses, pointer-table
cursors and accesses outside the known record keep their conservative boundary.
This is type/field evidence, not memory ownership or alias-exclusion proof.

A bounded record cursor may retain its one-past-end value after reading the
last field. A later predecrement can reenter that same record and resolve its
fields, including after the cursor is stored as an address. Reads or writes at
the endpoint remain unresolved; an invalid extra postincrement drops the cursor.
The final declared array element follows the same rule without inventing a next
element. Byte, WORD and LONG accesses retain their encoded auto-update syntax.

Brief address-register indexed operands expose their encoded signed-byte
`indexed_displacement` as an element. `representation.symbol` accepts only an
equal-valued canonical target EQU; the native renderer checks the actual decoded
displacement again and preserves the base register, index register, width and
scale. This names the fixed displacement only. It does not resolve the dynamic
index, infer a structure field, or prove array bounds. PC-indexed and full-extension
forms are outside this command's scope.

Fixed `d16(An)` operands similarly expose a signed-word `displacement` element.
Its symbol presentation requires an equal-valued canonical EQU and a second
native decoded-value check. The encoded word and base register remain intact,
including an explicit word extension for zero. Plain indirect, auto-update and
PC-relative operands do not offer this fixed-displacement command.

Function-summary commands also accept type-neutral `abi_pointer` inputs in
single-register or register-tuple locations. Combined with `identity_input`
results, these express shared save/restore wrappers without imposing a fixed
pointee type on every caller. Register preservation alone retains the existing
conservative treatment of storage-derived types across opaque memory effects.

Presentation edits replace the previous active style for the same native owner:
section, byte span and optional operand index. The action log remains append-only;
undo restores the preceding style and redo restores the edit. An explicit manual
edit also replaces a matching legacy metadata presentation. Different operands,
sections and spans remain independent, and conflicting raw metadata remains an
error rather than silently picking a winner.

Typed custom-structure fields inherit an owning layout's explicit `bitmap`,
`sound_sample` or `opaque_data` role for the existing binary-assets export.
Other descriptive roles do not become media classifications. Inline analysis
retains every typed field. The package projection omits an exact generated
field-name comment when coalescing its numeric bytes into INCBIN; manual, role
and additional comments survive. Interior labels, expressions, fixups, ORG and
overlap guards continue to bound or prevent extraction.

## Read-only completeness accounting

```sh
python -m amiga_reversing.tools.restoration_accounting --target TARGET \
  --verification-receipt RECEIPT.json \
  --json-output accounting.json --text-output accounting.txt
```

This offline report builds one native artifact from the current canonical
metadata; it needs no running server. It reads the Manual Action Log, validates
the Decision Journal and asset identities, and rejects canonical inputs that
change during collection. Only the requested report files are written; target
facts, source and review decisions are unchanged. The optional receipt is reused
only when its original, source and package hashes match and both C and vasm
reported exact original-layout output. Accounting never runs or substitutes a
new verification gate. The native source-plan DTO includes canonical stored and
allocated section extents, keeping BSS and allocation tails out of payload totals.

The JSON (`restoration-accounting/v1`) and compact text view separate:

- Disjoint native payload classification, provisional/conflicting claims and
  unknown gaps, with coordinate identities and native evidence anchors.
- Base-relative workspace envelopes, aliases, overlaps, unknown gaps, declared
  runtime regions and absolute observations. Coordinate spaces have no additive
  grand total; mapped-source views do not create extra payload bytes. Hardware,
  vectors and external cells are separate, including observations of unknown width.
- Discovered function candidates, declared data owners, explicit array/typed
  record counts and asset emission chunks. Their complete semantic denominators
  and unproved function/resource boundaries remain unknown.
- Purpose/confidence, native field and reference resolution, presentation signals,
  original-layout verification, final review and relocation readiness.

Native accepted classification is not semantic acceptance. The current canonical
models record useful annotation evidence, declared roles, ABI summaries and
review decisions, but have no separate bounded assessment of *complete purpose*.
This first report therefore exposes purpose/confidence as not separately assessed;
it does not promote names, comments, accepted formatting or INCBIN into proof.
Existing evidence remains discoverable through owner IDs, source coordinates,
MAL citations, native function-entry evidence and the Decision Journal. No parallel
tracker or assembly-comment metadata is introduced.

RSSET accounting uses native normalized layout/base identities. Its observed
minimum/maximum envelope is not a proved workspace allocation bound: unknown
prefix/suffix extents remain outside the denominator. Missing declarations or
observed accesses never prove unused storage. Data-layout `padding` elements
retain their explicit classification; workspace reserved/padding/unused intent is
reported unavailable where the canonical model does not encode it. Dynamic field
indices, unresolved references and indirect sites remain separate obligations.
Generic names are review signals only. No overall percentage is computed.

The Pandora baseline is in [pandora-completeness-baseline.json](targets/pandora-completeness-baseline.json)
and [pandora-completeness-baseline.txt](targets/pandora-completeness-baseline.txt).
