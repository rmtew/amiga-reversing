# Shared restoration framework validation — 2026-10-12

The native Linux workbench now supports an iterative source restoration workflow
through the same server operations in its UI, CLI and stdio MCP adapter. This
extends the [initial architecture assessment](../linux-baseline-2026-10.md) and
[validated Copperline runtime](../copperline-runtime.md). Design and migration
review preceded implementation; final independent reviews found no blockers.

## Implemented boundary

- Native artifact queries return bounded symbols, typed references, instructions,
  CFG edges and field uses directly from native facts/render-plan structures.
  Function candidates, ownership and relations derive from CFG facts and expose
  uncertainty, including unresolved indirect calls. They are not reconstructed
  by parsing assembly or taking the range up to the next label.
- A resident restoration service owns discovery, inspection, catalog commands,
  interpretation, verification, question-led probes, review and history/undo.
  UI, CLI and the official MCP SDK adapter share that boundary. The adapter has
  nine domain tools and no independent analysis, storage or mutation path.
- Source/backend identity plus both histories bind concurrency revisions and
  cursors. Writes reject stale revisions. Verification uses a separate source
  subject revision, so appending a review does not invalidate its own proof.
- Existing Manual Action Log and Decision Journal remain authoritative. Old
  records and unknown fields are preserved byte-for-byte; missing evidence is
  explicitly unassessed. Cross-process target locks and validated atomic batches
  prevent lost writes and partial decision supersessions. Readers and artifact
  publication share the target lease. No second semantic database was added.
- Query/history pages are capped at 100 items and 64 KiB with explicit truncated
  previews. Navigation retrieves references on demand; old embedded reference
  arrays and browser reconstruction fallbacks were removed. Existing grouping
  and specialized suggestion functionality remain separate.
- C source include joins now work on Linux. Exact verification regenerates one
  canonical source and checks both the framework assembler and vasm against the
  entire original file. Probes run the verified rebuilt file, not a substituted
  original. Receipts are content-addressed, disposable evidence.

## Real Pandora iteration

Target: `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.

The anonymous helper at source `0x6668` now has the name
`clear_overlay_pointer_storage`. Its LEA references `ui_overlay_update_queue` at
`0xA862`; `MOVEQ #31`, `CLR.L (A0)+` and `DBF` clear 32 longwords (128 bytes),
followed by RTS. The direct caller is at `0xA01C`. Six canonical instruction keys
support the interpretation. This names the static memory effect; it does not
claim queue scheduling or prove runtime reachability of the helper.

The change went through `inspect → interpret → state → verify → probe → review`.
The prior 571,072 manual-log bytes were preserved exactly and one 1,218-byte
interpretation action was appended. A deliberate stale retry was refused and
left history unchanged. All 989 prior actions remain, with legacy evidence status
visible. The Decision Journal gained one supported tool-authored acceptance.
The regenerated `.s` includes the name at the helper and its caller. It also
refreshes the previously stale projection, including the prior zero-offset
encoding fix and current fact-derived data rendering; no assembly was hand-edited.

Both the C assembler and external vasm reproduce **376,832 bytes exactly**:

- Output SHA256: `70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
- Generated source SHA256: `0dc190c8825b3175561494cf8e39d48a022c386fc8291ec73dcf1cf0df1256ee`.
- Verification receipt: `89e322c2683fe75ea90f03c07d3acec9cd12256e567a83ec4a5307ceb5c183f1`.
- Probe receipt: `981726d289e42be85e83984a368d285d89fd5bb21177f2b516fd615d54629ebe`.
- Action: `manual-345dedff0c33467ab60279ed8881ad4e`.
- Decision: `restoration-fc5ecc0df81d4fe7855db6e207a0ca71`.

The actual rebuilt file passed `pandora-gameplay-entry` under Copperline 1.0.0,
A500 OCS/PAL, 68000, 512K chip + 512K slow and the existing user-supplied Kickstart.
The question was whether established gameplay checkpoints still execute after
the interpretation. Title (`0x10BA8`), UI initialization (`0x1079E`), gameplay
(`0x105D6`) and inventory handler (`0x128D4`) all hit with unique payload identity.
Input was held/released at scenario phase boundaries. The budget was 120 seconds;
the emulator exited after observation. No instruction trace was retained.
Acceptance preserves the same source subject as the exact verification.

## Retrieval and interface measurements

Final compact JSON data, including revision/provenance/unknowns:

| Request | Items | Bytes |
| --- | ---: | ---: |
| References to `enqueue_ui_overlay_update` | 13 | 3,388 |
| Instructions in source window `0x6668..0x66C8`, first page | 27 of 33 | 5,269 |

The old reference discovery required a 4,930,416-byte navigation response; the
prior rich 27-row response was 101,378 bytes. These are workflow payload
comparisons, not identical schemas: the new responses contain the requested
facts rather than unrelated navigation/listing decoration. Cursors retrieve the
remaining items. Live HTTP, CLI and actual MCP initialization/tool invocation
returned equal reference results. A real Chromium session opened Pandora,
queried and inspected facts, and followed navigation references without page
errors. A synthetic HUNK also exercised UI interpretation, exact 44-byte rebuild,
review/history and undo; final service regressions verify the corrected review
actor and current-proof behavior.

## Reproduction

```sh
cd /workspace/amiga-reversing
uv sync --extra mcp --no-dev
make -j4
make -C ext/vasm CPU=m68k SYNTAX=mot -j4
cp ext/vasm/vasmm68k_mot tools/vasmm68k_mot.exe
export COPPERLINE_BINARY=/path/to/official/copperline
export COPPERLINE_ROM=/path/to/user-supplied/kick13.rom
.venv/bin/python -m amiga_reversing.tools.disasm_server --host 127.0.0.1 --port 8123
```

Open `http://127.0.0.1:8123/` and select Pandora, then **Restore**. This is a
loopback service in the cloud environment, not a public or forwarded URL. The
runtime binary/ROM are external inputs; neither is committed. The separate
tennis checkout and its running work remain untouched.

In another shell (set `T` to the target ID above):

```sh
.venv/bin/python -m amiga_reversing.tools.restoration --target "$T" state
.venv/bin/python -m amiga_reversing.tools.restoration --target "$T" query \
  --kind references --symbol enqueue_ui_overlay_update --limit 25
.venv/bin/python -m amiga_reversing.tools.restoration --target "$T" inspect \
  --section-index 0 --source-offset 0x6668 --row-kind label
.venv/bin/python -m amiga_reversing.tools.restoration --target "$T" verify \
  --expected-revision REVISION_FROM_CURRENT_STATE
```

Poll state until ready. Use the returned revision/catalog context for mutations;
copy the new verification receipt into probe/review requests. Detailed request
schemas and stdio configuration are in [Restoration interfaces](../restoration-interfaces.md).
A fresh checkout needs the original target payload before Pandora can open;
synthetic HUNK tests remain available without proprietary inputs.

## Tests and limits

Commands executed from this checkout include:

```sh
.venv/bin/python -m pytest -q
make test
.venv/bin/python -m pytest -q -o addopts='' \
  tests/test_restoration_operations.py tests/test_restoration_artifact_lifetime.py \
  tests/test_function_facts.py
.venv/bin/python -m pytest -q tests/test_active_imports.py
```

- Default suite: **1,512 passed, 65 skipped, 355 deselected, one failed**. The
  failure is the absent `resources/platform_macos/MPW-GM.img.bin` fixture.
- Native suite: **772 passed**, one known Ancient decompression-provider failure.
- Final operations/artifact-lifetime/function-fact tests: **34 passed**. Cover
  stale cursors/writes, source-byte identity, review proof/supersession, oversized
  legacy previews and concurrent artifact publication/clear/read leases.
- Independent migration reviewer: **117 passed**, including original manual-log
  preservation, undo/redo and decision projection. Windows locking was inspected
  but not executed on this Linux host.
- Server route tests: **192 passed**; the excluded installed-server inventory
  case needs the missing Search for King disk manifest. Focused native query,
  full-file verification and transport tests pass, including adversarial limits.
- **15 actual Chromium/CDP tests passed** for command/review flows, references,
  105-reference pagination, source-coordinate jumps and virtual navigation.
  CLI/MCP/web-source interface tests: **27 passed**. Live browser/stdio smoke
  additionally verifies the running service, not only imports or mocks.
- Import-boundary tests: **5 passed**. Scoped Ruff and `git diff --check` pass.
  Checking every changed Python file also reports three pre-existing Ruff
  diagnostics: import order in `c_backend.py` and two prefix/suffix checks in
  `reversing_workspace.py`. All other changed Python files pass. No claim is
  made for a full strict-mypy, Windows runtime or corpus-oracle pass.

Local receipts/logs live under `.runtime-state/restoration/`; they are not a
second fact store and can be regenerated. The optional public-PyPI machine68k
extra replaces an unresolvable local Windows wheel reference for portable setup;
it does not claim equivalence to that formerly patched oracle.

Remaining work is semantic restoration, especially indirect dispatch and queue
processing. Existing 20/60-second queue probes reach enqueue but do not observe
processing. Original-loader comparison still needs the original Pandora ADF.
Keep those as separate evidence questions; do not infer complete emulator parity
from exact assembly or four gameplay checkpoints. No broad target naming pass,
proprietary input download, public hosting or merge is part of this change.
