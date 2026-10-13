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
```

Poll `state` until `ready` before querying. Stop if its job reports `failed` and
inspect the retained error: status reads do not retry a failed build for the
same revision. A changed revision or an explicit listing-build request can
start a new build. Responses include `revision`,
`subject_revision`, explicit scope and unknowns. Pages contain `items`, `total`
and `next_cursor`; send that cursor with the same query and revision to continue.
The server rejects stale cursors rather than joining different snapshots.

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

Run `interpret`, inspect its new revision, then `verify`. Verification returns a
`receipt_id`; review acceptance requires that receipt for the current subject.
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
inspect, interpret, interpret_batch, verify, probe, review, history and rollback. Read operations
are annotated read-only; mutations require explicit revisions. HTTP domain
refusals surface as MCP tool errors, without automatic retries.

The adapter uses the official `mcp>=2.3,<3` Python SDK, structured tool results and
stdio lifecycle: [SDK documentation](https://py.sdk.modelcontextprotocol.io/) and
[transport documentation](https://py.sdk.modelcontextprotocol.io/run/).
