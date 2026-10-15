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

`typed_pointers` selects canonical bound fields with explicit pointer semantics,
and supports only the optional `struct_name` filter. Its total and outcome/reason
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

The context above is schematic: copy the complete context and command from the
actual `inspect.commands` catalog. Do not invent locators or arbitrary manual
payload kinds. Supported evidence status is `hypothesis` or `analysis_proven`.

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
command and its parameters are still validated independently. The Manual Action Log validates the complete batch and appends it atomically; an
invalid final entry or stale revision leaves both histories unchanged. The
service applies the actions and invalidates the projection once, then returns
`actions`, per-entry `commands`, and the resulting revision. Inspect and verify
that resulting revision before review. Batches do not observe earlier entries
as fresh catalog state, so dependent commands require a new inspection.

`target.function_summary.add` also accepts the canonical optional `results`,
`effects` and `note` fields. Explicit register effects must partition all sixteen
general registers; omitted effects remain unknown. The command validates the
complete summary before appending it. `inputs: []` is valid for an effect-only
leaf with no typed pointer arguments; an identity result or input-relative effect
still requires an existing input index. Empty and malformed input arrays remain
distinct. Native metadata reading accepts compact
and indented JSON for these arrays without changing the contract or ABI.

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
as a platform symbol or target equate. The append preflight resolves one native
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
