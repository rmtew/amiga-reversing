# Decompression

Executable targets may not contain their final code or data in directly usable
form. They may contain a decompression stub and a compressed payload. Running
the stub may decompress the payload to an absolute address, then jump to an
entrypoint within the decompressed range.

The project model must represent this as related targets:

- The original packed file or hunk, reproduced exactly as the shipped bytes.
- A derived decompressed payload target, analysed and rendered as the source
  view the user most likely wants to work with.

The decompression stub is still real code and should remain inspectable and
reproducible. The decompressed payload is the better default target for source
recovery when it contains the actual game code and data.

This document is the work-in-progress plan. Update it as support becomes more
complete.

## Current Status

Carrier Command proves the concept for RNC1 payload discovery and one retained
decompressed child:

- Parent target:
  `amiga_disk_carrier-command-1994-kixx-budget__amiga_hunk_carrier_91b0ba24`
- Packed streams:
  hunk section offsets `$05E4` and `$4C40`; the retained child corresponds to
  file offset `$4C60`, hunk section offset `$4C40`
- Provider used:
  Ancient CLI, `RNC1: Rob Northen RNC1 Compressor (old)`
- Child target:
  `amiga_disk_carrier-command-1994-kixx-budget__amiga_raw_carrier_rnc_00004c60`
- Runtime view:
  load address `$4000`, entrypoint `$4000`

The parent and child are now linked in the disk manifest with `derived_targets`
and `derived_from`. The child records extraction provenance in
`decompression.json`. The disk UI can show the synthetic decompressed child
without pretending it is a filesystem entry.

A first C decompression provider layer now exists:

- `platform_file_decompression.c/.h` define the provider-facing identify path.
- Ancient is staged at `ext/tools/ancient/Ancient.exe`.
- `src/build.bat` fails fast if the staged Ancient provider binary is missing,
  so provider-backed decompression cannot silently disappear from a local build.
- `src/build.bat build-ancient-provider` rebuilds the local Ancient clone at
  `resources/clone_common/ancient` and refreshes the staged binary in
  `ext/tools/ancient/Ancient.exe` when that ignored source checkout is present.
- The C provider default resolves the staged Ancient path relative to the loaded
  module on Windows, so DLL callers do not depend on the process current
  directory. `AMIGA_ANCIENT_EXE` remains an explicit override.
- Windows provider calls launch Ancient without inheriting pytest or UI process
  capture handles. Both identify and decompress paths redirect output through
  explicit temporary files or `NUL`, and timed-out children are terminated.
- `platform_file_cli identify-packed-range` can identify an explicit byte range.
- `platform_file_cli decompress-packed-range` can materialise provider output
  and report packed/decompressed SHA-256 and decompressed size.
- Provider records include the staged provider path and executable SHA-256, so
  decompression provenance is tied to the exact Ancient binary used.
- The same identify/decompress records are exported through
  `platform_file_lib.dll` for the Python C backend wrapper.
- Facts-v2 analysis JSON now includes top-level `packed_payloads[]`,
  `derived_target_suggestions[]`, and `decompression_events[]` from C provider
  scanning of loaded target sections. Non-materialising suggestions and events
  include a `reason` field so callers can distinguish missing runtime evidence,
  conflicting runtime copies, copy size mismatch, and missing decompressed
  load/entry metadata.
- C can now promote a suggestion to `status: "materializable"` when a runtime
  copy/load address candidate is validated against the decompressed output's
  first decoded absolute control transfer. This uses generated M68K decode and
  effect metadata, not byte-pattern matching.
- Facts-v2 listing-with-analysis JSON uses the same decorated analysis object,
  so corpus indexing no longer loses decompression facts when it asks C for
  listing rows.
- Corpus usage indexing now turns those C-emitted records into searchable
  compression and derived-target feature tags/xrefs.
- Corpus usage indexing also walks nested disk project targets, so retained
  parent/child outputs under `targets/<disk>/targets/` are visible to corpus
  searches.
- Retained decompressed child targets now expose their existing
  `decompression.json` provenance as usage tags, including codec, packed
  offset, load address, and entrypoint.
- A C backend section-range decompression API can materialise bytes from a
  packed section offset emitted by analysis, so Python does not parse hunk
  section bytes to extract payloads.
- Imported disk project targets can now materialise decompressed raw child
  targets from C `derived_target_suggestions[]`, but only when the C record has
  `status: "materializable"` plus concrete source section, packed size,
  decompressed size, load address, and entrypoint metadata.
- Imported disk projects now also refresh an existing generated decompressed
  child from a matching C `materializable` record instead of silently skipping
  it, so stale provenance can be reconciled without deleting the child first.
- `amiga_reversing.tools.import_adf --refresh-decompressed --disk-id <id>` can
  apply new C materialisation records to an existing disk project.
- Carrier's retained-child RNC stream is identified both as an extracted range
  file and in the original parent file at offset `$4C40`. Parent analysis also
  identifies a smaller RNC stream at `$05E4`; it remains conservative because no
  load/entry metadata is proven for it.
- The C-decompressed Carrier output hash matches the existing derived child
  binary.
- Carrier's parent analysis now promotes the retained-child `$4C40` stream to
  `materializable`: runtime-copy evidence supplies load address `$4000`, and
  the decompressed output's first decoded absolute jump targets `$9B3A`, inside
  the decompressed image under that load base. Source rendering still keeps the
  parent stub jump numeric and does not create false source labels at
  `$4000`/`$4004`.
- Facts-v2 now preserves a separate non-materialising runtime-copy evidence
  record when a discovered copy conflicts with an already accepted runtime
  source view. Carrier uses this for the `$4C40 -> $4000` packed stream copy:
  it is useful decompression evidence, but it is not an ORG/source alias.
- Damocles shows the next unsupported class: visible self-decrunching code writes
  an absolute runtime image around `$40000` and jumps there, but Ancient
  `scan-json` does not identify that stream. C analysis now emits an explicit
  unsupported self-decrunch event for this code path with
  `provider_id: "m68k-sim-decrunch"` and
  `codec_support: "simulator_required"`. It is intentionally not materialised
  until simulator-backed output capture proves bounded bytes, load address,
  entrypoint, and reproduction.
- Corpus indexing validates that this is not just a Damocles-local shape:
  Voodoo Nightmare retains comparable unsupported Amiga self-decrunch evidence
  after provider-materialised and one-write noise is suppressed.
- Magicland Dizzy proper is currently an ORG/bootstrap runtime-copy case, not
  visible decompression. C records the copied runtime view at `$5BFF0`, uses a
  runtime-address reference to prove the copied range start, and seeds that
  range as `runtime_view_entry` so the rendered ORG payload becomes decoded
  source code rather than a decompressed child target.

Discovery, acceptance, extraction, and imported child materialisation are now
driven by C-emitted records. Corpus indexing remains deliberately non-mutating:
it reports C facts and retained child targets, while import/refresh commands
create or update project files.

## Target Architecture

C remains authoritative for analysis and target relationships.

Python may materialise files and project directories, but only from C-emitted
facts or records. Python must not grow decompression scanning heuristics.
Python must not execute decruncher stubs to discover bytes. If execution is
needed, it belongs in C using the generated project simulator.

Use project-owned decompression:

- C owns scanning ranges, overlap policy, result acceptance, provenance, corpus
  tags, and target relationship records.
- Native C codec implementations are preferred when a codec is recognized and
  supported by this project. Native implementations for codecs Ancient already
  identifies and decompresses are deferred for now; the active priority is
  unsupported target-owned self-decrunchers such as Damocles.
- External suites such as Ancient and XFD are useful for identification,
  variant comparison, reference material, and oracle tests. They should not
  remain the production decompressor for codecs we support natively.
- Current automatic scanning still delegates candidate discovery to Ancient
  `scan-json` where no native scanner exists. C applies source-analysis
  acceptance gates after provider validation: candidates must not overlap
  accepted code and must have sane packed/raw sizes with useful expansion before
  they become `packed_payloads[]`. Explicit range identify/decompress remains
  available for small or ambiguous payloads that a user selects directly.
- For self-decrunching targets that no external provider identifies, add a
  second provider mode: bounded C execution using `m68k_simulate_step_concrete`.
  This is still provider-backed discovery, but the provider is our generated
  simulator plus C-side target evidence, not Python and not `machine68k`.
- `machine68k` may remain only as an independent oracle in simulator tests. It
  must not be used by decompression analysis, import, corpus indexing, or UI
  materialisation.
- A bounded C concrete-run primitive now exists for simulator-backed
  decrunchers. It executes generated simulator steps with a max-step limit and
  stop-PC range, and has isolated C unit tests. C also emits unsupported
  self-decrunch event records when analysed code writes to an absolute runtime
  range and transfers control there. Simple self-contained cases can now be
  probed with the generated simulator and emit `simulated_output_observed` with
  output range, write count, and stop metadata from actual simulator write
  tracing rather than memory diffs. Concrete writes are tracked as merged ranges,
  and the accepted output is the range containing the transfer target, so
  unrelated scratch or hardware writes do not widen the payload hash. The
  simulator seed now also honours C policy runtime ranges/execution views, so
  absolute source reads are supported when the source mapping is explicit.
  Simulated decruncher runs use a generic memory-policy callback for external
  writes; the Amiga platform supplies generated hardware-register metadata so
  progress/color/DMA side-effect writes do not abort extraction or become payload
  bytes. C analysis preserves traced setup state across an explicit
  same-section unconditional branch/jump over embedded data into a later
  decrunch stage, so the simulator can start from the proven setup entry
  without weak fallthrough guessing. For staged decrunchers, C now prefers a
  proven same-section CFG root that reaches the transfer site over the local
  contiguous scan start, so setup code before helper blocks or embedded data is
  represented as the decruncher entry. Simulated output records include a
  SHA-256 hash. Failed simulator attempts now keep the concrete stop reason,
  start PC, stop PC, step count, write count, and first diagnostic, so
  unsupported events point at the next missing simulator or memory-map
  capability. Simulator probing mirrors the loaded section at its inferred
  runtime load address and sizes bounded RAM from decoded absolute runtime
  literals. Damocles now reaches the transferred `$40000` image and records a
  simulated output range; this remains a bounded extraction run, not a general
  Amiga emulator.

The boundary is:

`C scan` -> `provider identify/decompress` -> `C packed_payload facts` ->
`Python materialises child target` -> `UI renders provenance`.

For simulated self-decrunchers the provider boundary is:

`C code/runtime-copy analysis` -> `C simulator provider` ->
`C bounded execution result` -> `C packed_payload facts` ->
`Python materialises child target` -> `UI renders provenance`.

## Simulated Self-Decrunchers

Some programs do not expose a packed stream that Ancient or XFD-style providers
can identify directly. They ship executable decruncher code that writes a
runtime image to absolute memory and branches to it. Damocles is the current
observed corpus example.

Support this with a narrow C runner around the generated concrete simulator:

- Seed memory from the loaded hunk/raw sections plus explicit runtime load
  mappings proven by C analysis.
- Seed registers only from analysed entrypoint state or clearly rendered stub
  constants. Do not guess game-specific register contracts.
- Run from an analysed decruncher entrypoint with a strict instruction limit,
  write-range limit, and memory map guard.
- Preserve setup state across explicit same-section unconditional branches or
  jumps over embedded data when the target is already an accepted code start.
  Do not infer continuity from a gap without that control-flow evidence.
- Derive the simulator entry from proven CFG reachability when a section entry,
  policy entry, or cross-section control target reaches the transfer site. Keep
  the local scan start only when no such root is proven.
- Stop only on a branch into the produced runtime image, unsupported instruction,
  illegal external access, trap/OS call, or instruction budget exhaustion.
- Accept only when the written output is contiguous or sectionable, the final
  control target lands inside it, and the source write ranges do not overlap
  accepted parent code except where C analysis already classifies them as
  runtime output.
- Emit provider provenance as `provider_id: "m68k-sim-decrunch"` with simulator
  build/tool stamps, entrypoint, stop reason, instruction count, written ranges,
  output hash, load address, and entrypoint.
- For non-materialised events where simulation was attempted, still emit the
  simulator stop reason, stop PC, write count, and first diagnostic. Do not
  collapse all failures into an unidentified bucket.
- Runtime memory used by the simulator must come from analysis evidence:
  explicit policy runtime ranges, inferred event load address, and decoded
  absolute runtime literals. It may reserve bounded RAM around those discovered
  literals for target-owned workspaces, but must not allocate an unbounded
  machine image.

This provider is not a general emulator. It is a deterministic extractor for
already-observed decompression stubs. Unsupported results must be indexed as
work items rather than materialised.

## C Decompression Interface

The first narrow C interface has been added:

- `platform_file_decompression.h`
- `platform_file_decompression.c`
- provider implementation for Ancient CLI

Provider result records should include:

- codec id and display name
- provider id, executable path/version or commit
- confidence
- packed source kind, section index if applicable, offset, size, hash
- decompressed size and hash
- load address if known
- entrypoint if known
- evidence records linking code to the packed stream where available
- diagnostics for unsupported or ambiguous streams

C emits provider-backed records through platform analysis JSON as:

- `packed_payloads[]`
- `derived_target_suggestions[]`
- `decompression_events[]`
- corpus tags and xrefs derived from those records

The C side decides whether a provider result is accepted. Provider confidence
alone is not enough.

## Acceptance Rules

Accept a packed payload only when:

- The packed range does not overlap accepted code unless that overlap is already
  understood as data embedded in an accepted instruction stream.
- The provider validates the stream strongly enough for the codec.
- Packed and decompressed sizes are bounded and sane for the containing target.
  Automatic scan records reject micro-payloads and non-expanding ranges; explicit
  provider range calls can still inspect them.
- The parent source range, decompressed output, and hashes are recorded.
- The result does not suppress exact reproduction of the packed parent.

Unsupported or unknown compression must be represented explicitly. The packed
target remains valid and reproducible, but the embedded payload analysis must be
marked incomplete rather than guessed.

## Project Integration

For imported project targets and corpus targets, decompression support should
produce the same model:

- Packed parent target remains the exact shipped source.
- Decompressed child target is materialised when extraction is accepted.
- Parent manifest entry records `derived_targets`.
- Child manifest entry records `derived_from`.
- Child `.project.json` records origin and role.
- Child `decompression.json` records extraction provenance and hashes.
- Child `source_binary.json` records runtime absolute load/entry metadata.

The child target should be discoverable through the disk/project UI, but should
also be visibly synthetic and linked back to the packed parent.

## Corpus Integration

Corpus indexing should run the same C decompression discovery used for imported
projects. It must not create or modify targets; when it finds a materializable
payload, users apply that record through disk import or refresh.

Useful tags:

- `compressed-payload`
- compressor-specific tags such as `compressed:rnc1`
- `decompression:runtime_copy`
- `decompression:runtime_copy_conflicting`
- `decompression:runtime_copy_non_conflicting`
- copy-shape tags such as `decompression:runtime_copy_short` and
  `decompression:runtime_copy_oversize`
- `decompression-stub`
- `absolute-depack-dest`
- `decompressed-entrypoint`
- `derived-decompressed-target`
- `unsupported-compressor`
- `packed-or-transformed-payload`

Searches for analysis patterns should be able to include either packed parent
or decompressed child views.

## Reproduction Requirements

- The packed parent target must reproduce the original packed bytes exactly.
- The decompressed child target must reassemble to the decompressed bytes exactly
  where raw output reproduction is supported.
- If the packed stub is rendered as source, it remains independently
  reproducible with compressed payload bytes intact.
- Extraction metadata must make the decompressed bytes reproducible from the
  packed target and selected provider.

Raw binary reproduction is now wired through C render/assemble. Raw targets
assemble to the single section payload bytes rather than a hunk container.

## Observed Examples

### Carrier Command

Target:
`targets/amiga_disk_carrier-command-1994-kixx-budget/targets/amiga_hunk_carrier_91b0ba24/carrier_91b0ba24.s`

Observed:

- Stub compares against `#$524E4301`, the `RNC\1` marker.
- Parent rendered source references the packed range with
  `lea.l loc_0_00004C40(pc),a2`.
- The packed stream begins at hunk section offset `$4C40`, file offset `$4C60`.
- Ancient identifies it as `RNC1: Rob Northen RNC1 Compressor (old)`.
- Decompressed output is 359600 bytes.
- The decompressed image starts with an absolute jump and is analysed as a raw
  runtime image loaded at `$4000`.

Current retained output:

- Parent manifest entry has `derived_targets`.
- Child manifest entry has `derived_from`.
- Child `decompression.json` has packed/decompressed hashes and provider info.
- Disk CDP test verifies the child is shown as a decompressed RNC target.
- C CLI identifies the parent range:
  `platform_file_cli identify-packed-range <parent> 19552 168391`.
- C CLI decompresses the parent range to 359600 bytes with SHA-256
  `d37ec7db83012eba179956026b0677cfd46763d585722154f761bd6f6d2b5748`,
  matching the retained child `binary.bin`.
- Facts-v2 analysis of the Carrier parent hunk emits a packed payload at section
  offset `$4C40`, packed size 168391, decompressed size 359600, and the same
  decompressed SHA-256.
- The same C suggestion now includes runtime-copy evidence for `$4C40` copied to
  `$4000`, with copy size 168396 and `runtime_copy_conflicting: true`. It is
  now promoted to `materializable` only because the decompressed output's first
  decoded absolute jump targets `$9B3A`, inside the decompressed image when
  loaded at `$4000`.
- Facts-v2 analysis also emits Carrier's smaller RNC stream at section offset
  `$05E4`, packed size 18012, decompressed size 32032. It is deliberately not
  materialised without runtime metadata.
- Corpus usage indexing can tag that record as `compressed-payload`,
  `compressed:rnc1-old`, `decompression:provider:ancient-cli`, and
  `derived-decompressed-target`.
- Corpus usage indexing also preserves the C runtime-copy evidence as searchable
  tags and xrefs, including `decompression:runtime_copy`,
  `decompression:runtime_copy_conflicting`, and
  `decompression:runtime_copy_oversize` for the `$4C40` stream.
- Rebuilt corpus usage output finds the Carrier parent both as the file
  manifest target `amiga-hunk/5855d79d8920` and as the nested project target
  `amiga_disk_carrier-command-1994-kixx-budget/targets/amiga_hunk_carrier_91b0ba24`.
- The retained decompressed child target is searchable as `decompression:child`
  and `decompression:codec:rnc1-old`, with packed section offset `$4C40`,
  load address `$4000`, and entrypoint `$4000` from its provenance file.
- Python can call the C decompression provider through the C backend wrapper;
  tests cover unknown payload handling without Python-side identification.
- Python can also ask C to decompress a provider-backed packed section range
  from a platform file.
- Python disk import consumes C materialisation records conservatively:
  anything other than explicit `status: "materializable"`, missing load/entry
  records, failed extraction, or failed C analysis leaves only the packed parent
  target.
- The retained Carrier decompressed child passes exact raw reproduction:
  359600 rebuilt bytes, SHA-256
  `d37ec7db83012eba179956026b0677cfd46763d585722154f761bd6f6d2b5748`.

## Work Plan

1. Done: add the C decompression provider interface.
2. Done: wrap Ancient as the first provider for explicit range
   identification.
3. Done: add provider decompression output, size, and hash reporting.
4. Done: expose provider `packed_payloads[]` JSON through CLI, DLL, and
   facts-v2 analysis JSON.
5. Done: expose packed payload and derived target records as corpus usage
   tags/xrefs for later target selection.
6. Done: make listing-with-analysis JSON carry the same decompression fields as
   analysis-only JSON.
7. Done: Carrier RNC discovery is emitted from C analysis records.
   Runtime-copy evidence is now emitted for matching packed streams, including
   Carrier's conflicting `$4C40 -> $4000` copy. The `$4C40` child can now be
   promoted from C records by validating the decompressed image's initial
   control target against that runtime load base. The smaller `$05E4` stream
   remains non-materialising because it decompresses to data-like bytes and
   lacks load/entry evidence.
8. Done: provider result acceptance and parent/child materialisation are
   covered by C-backend and disk-import tests. Code-overlap rejection now has a
   synthetic C-backend regression proving an RNC-looking candidate inside
   accepted code does not become a payload. Carrier now has a real C-backend
   regression for promotion to `materializable` from runtime load evidence plus
   generated decode of the decompressed output.
9. Done: add Python access to C section-range decompression.
10. Done: include nested disk project targets in corpus usage indexing.
11. Done: index retained decompressed child provenance from `decompression.json`.
12. Done: imported disk projects can materialise or refresh child targets from
   complete C records. Corpus indexing indexes retained children and C facts,
   but target creation remains an explicit import/refresh operation.
13. Done: add a non-Carrier comparator regression using the Voodoo Nightmare
   `Trainer` RNC1 payload from the corpus resources.
14. Done: raw decompressed child reproduction assembles C-rendered raw source
   to payload bytes and compares against the decompressed binary.
15. Done: make the C Ancient provider default path independent of the caller's
   current working directory and cover it with the Voodoo comparator test.
16. Done: index decompression runtime-copy evidence and conflict shape as corpus
   tags/xrefs so Carrier-like parent/child reconciliation work can be selected
   by evidence, not by target name.
17. Superseded: local RNC header scanning was removed from analysis. Candidate
   discovery is provider-owned through Ancient `scan-json`; unvalidated
   header-shaped bytes produce no candidates.
18. Done: include provider executable SHA-256 in C provider JSON records.
19. Done: copy the rebuilt Ancient provider binary with `scan-json` support into
   `ext/tools/ancient/Ancient.exe` and route C candidate discovery through it.
20. Done: add a generic C-side automatic-scan usefulness gate after provider
   validation. This keeps explicit range decompression available but prevents
   tiny or non-expanding provider-valid micro-streams, especially weak
   `C: Compact` hits, from becoming automatic `packed_payloads[]`.
21. Done: add a build command for refreshing the staged Ancient provider binary
   from the local Ancient clone: `cmd /c src\build.bat build-ancient-provider`.
22. Done: add C-emitted non-materialisation/materialisation reasons to
   `derived_target_suggestions[]` and index them as corpus tags/xrefs.
23. Done: infer a materializable decompressed raw child when C analysis has a
   runtime load candidate and generated M68K decode proves the decompressed
   image's initial absolute jump stays inside that runtime image.
24. Done: refresh an existing imported decompressed child target from the C
   materialisation record instead of leaving stale generated provenance in
   place.
25. Done: expose decompressed-child refresh through the import CLI so existing
   disk projects can apply new C materialisation records without deleting the
   project.
26. Done: expose C simulator-proven self-decrunch output through a narrow C
   backend API, but do not promote observed bytes to a retained child unless C
   classifies the output as a replacement program. Damocles currently remains
   indexed evidence only: it writes a 1744-byte data-like range at `$40000`, but
   that range does not disassemble as a coherent program.
27. Done: imported decompressed-child refresh removes stale synthetic children
   when successful reanalysis no longer accepts the child.
28. Done: C analysis identifies Tetragon unpacker marker events. Damocles now
   reports two Tetragon candidates: hunk 1 compressed source at section offset
   `$100`, compressed-source section end offset `$428`, post-pass source
   `$4F92B..$50000`, escape `$11`, target start and entry `$40000`, and hunk 2
   compressed source at section offset `$14C`, compressed-source section end
   offset `$474B4`, post-pass source `$130B6..$7FFFF`, escape `$AD`, target
   start `$1000`, final entry `$59484`, copied stub storage `$6A`, runtime stub
   `$100`, and transfer offset `$40`. Target end remains unknown until unpack
   execution proves the output cursor.
29. Done: native Tetragon unpack execution retains a payload only when C proves
   the packed trailer matches the post-pass range, post-pass consumption reaches
   the post-pass source end, the output cursor produces a bounded target range,
   and the final transfer lands inside that target. The Damocles real-data
   regression uses `tests/fixtures/hunk/damocles_tetragon_53b24620.bin` so it
   does not depend on mutable target inventory. Hunk 1 materializes
   `$40000..$50000`; hunk 2 materializes `$1000..$7C14A`. A second real-data
   comparator, `tests/fixtures/hunk/voodoo_ake_tetragon.bin`, proves the same
   native path on Voodoo Nightmare `ake.c` and materializes `$5C000..$65BA7`.
30. Done: C event emission suppresses a generic unknown self-decrunch event
   when a native recognized unpacker has already validated the same source
   section, load address, and entrypoint. This keeps broad simulator-required
   candidates as work items only while they are the best available evidence,
   and prevents Damocles/Voodoo native Tetragon coverage from being duplicated
   as stale unknown-decrunch work.
31. Done: the unknown self-decrunch simulator path is backed by a real
   Magicland Dizzy `TRAINER` fixture,
   `tests/fixtures/hunk/magicland_trsi_trainer_self_decrunch.bin`, instead of
   relying on optional corpus resources. The fixture exposed missing generated
   simulator coverage for extend arithmetic (`ADDX`/`SUBX`) and a too-small
   self-decrunch step bound. C simulation now reaches the transfer to `$20000`
   and materializes a 44220-byte payload with SHA-256
   `21ea11a46f008c69cca2795347eca093967191bf535b33c5ff3777619161999d`.

## Current Corpus Query Proof

After rebuilding `corpus/target_usage_manifest.jsonl`:

- `compressed:rnc1-old` finds Carrier in both the file manifest and nested disk
  project target views.
- `compressed-payload` also finds comparator RNC1 targets, including
  `3D Construction Kit II` `EditFile/runner.exe`, `3DEDIT`, `3DSOUND`,
  `3DMAKE`, and `Voodoo Nightmare` `Trainer`.
- Automatic provider scanning currently reports these unique codec tags:
  `rnc1`, `f`, `bk`, `c` (`C: Compact`), `rnc1-old`, `s310`, and `lsd`.
  The post-provider usefulness gate reduced `compressed:c` from 208 weak
  provider-valid micro-hits to 7 larger expanding candidates.
- `compressed:rnc2` has no current corpus hits after enabling provider-owned
  scanning; isolated C regressions assert that RNC-looking bytes are not accepted
  without provider validation.
- `decompression:child` finds the retained Carrier decompressed raw child and
  exposes the existing load/entry metadata.
- `decompression:codec:tetragon` and
  `decompression:provider:c-tetragon-signature` find Damocles plus the Voodoo
  Nightmare `ake.c` comparator as recognised native unpacker candidates. Native
  validated records now supersede exact same-target generic self-decrunch
  candidates; retained project children are produced only when imported project
  refresh materializes the accepted payload.
- `decompression:codec:unknown-self-decrunch` remains for target-owned
  decrunchers that are not yet recognized by a named native unpacker. The
  Magicland Dizzy `TRAINER` fixture proves the C simulator can materialize a
  large unknown runtime payload when execution reaches the transferred PC, but
  its role remains `unknown_runtime_payload`; Magicland Dizzy proper is tracked
  under ORG/runtime-view analysis, not decompression.
- `decompression:runtime_copy` finds Carrier parent evidence where C analysis
  associated packed streams with runtime copy ranges, including the conflicting
  `$4C40 -> $4000` copy.
- `decompression:runtime_copy_oversize` finds both Carrier parent streams:
  `$05E4` is copied as 18016 bytes over a 18012-byte provider range, and
  `$4C40` is copied as 168396 bytes over a 168391-byte provider range.
- `derived_target_suggestion_status:materializable`,
  `absolute-depack-dest`, and `decompressed-entrypoint` now find Carrier's
  `$4C40` stream from C analysis. The smaller `$05E4` stream remains
  `needs_runtime_metadata` with `runtime_copy_oversize`.
- These matches come from C `packed_payloads[]` records, not Python compression
  scanning, or from retained child provenance already written by the project.
