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

Carrier Command proves the concept for one RNC1 payload:

- Parent target:
  `amiga_disk_carrier-command-1994-kixx-budget__amiga_hunk_carrier_91b0ba24`
- Packed stream:
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
- `platform_file_cli identify-packed-range` can identify an explicit byte range.
- `platform_file_cli decompress-packed-range` can materialise provider output
  and report packed/decompressed SHA-256 and decompressed size.
- The same identify/decompress records are exported through
  `platform_file_lib.dll` for the Python C backend wrapper.
- Facts-v2 analysis JSON now includes top-level `packed_payloads[]` and
  `derived_target_suggestions[]` from C provider scanning of loaded target
  sections.
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
- Carrier's RNC stream is identified both as an extracted range file and in the
  original parent file at offset `$4C40`.
- The C-decompressed Carrier output hash matches the existing derived child
  binary.
- Carrier's parent analysis intentionally still emits `needs_runtime_metadata`
  for the derived target suggestion: the observed `$4000` jump is also an
  in-section absolute source address, so it must not be promoted to load/entry
  metadata until copied-runtime evidence proves that relationship.

This is not yet clean general support. Discovery, acceptance, extraction, and
child materialisation are not yet driven end-to-end by C-emitted records.

## Target Architecture

C remains authoritative for analysis and target relationships.

Python may materialise files and project directories, but only from C-emitted
facts or records. Python must not grow decompression scanning heuristics.

Use provider-backed decompression:

- C owns scanning ranges, overlap policy, result acceptance, provenance, corpus
  tags, and target relationship records.
- Providers own compressor knowledge:
  identification, header validation, packed/depacked sizes, checksum validation
  where available, and optional decompression.
- Ancient is the first provider because it already supports many formats.
- XFD is useful reference material, but should not be broadly integrated until a
  real target requires it.

The boundary is:

`C scan` -> `provider identify/decompress` -> `C packed_payload facts` ->
`Python materialises child target` -> `UI renders provenance`.

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
- corpus tags and xrefs derived from those records

The C side decides whether a provider result is accepted. Provider confidence
alone is not enough.

## Acceptance Rules

Accept a packed payload only when:

- The packed range does not overlap accepted code unless that overlap is already
  understood as data embedded in an accepted instruction stream.
- The provider validates the stream strongly enough for the codec.
- Packed and decompressed sizes are bounded and sane for the containing target.
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
projects.

Useful tags:

- `compressed-payload`
- compressor-specific tags such as `compressed:rnc1`
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
  `platform_file_cli identify-packed-range <parent> 19552 168397`.
- C CLI decompresses the parent range to 359600 bytes with SHA-256
  `d37ec7db83012eba179956026b0677cfd46763d585722154f761bd6f6d2b5748`,
  matching the retained child `binary.bin`.
- Facts-v2 analysis of the Carrier parent hunk emits a packed payload at section
  offset `$4C40`, packed size 168397, decompressed size 359600, and the same
  decompressed SHA-256.
- Corpus usage indexing can tag that record as `compressed-payload`,
  `compressed:rnc1-old`, `decompression:provider:ancient-cli`, and
  `derived-decompressed-target`.
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
7. Partly done: Carrier RNC discovery is emitted from C analysis records.
   Runtime load address and entrypoint are still target metadata/manual
   materialisation, so child target creation is not fully C-record driven.
8. Add isolated C tests for provider result acceptance, code-overlap rejection,
   and parent/child relationship output.
9. Done: add Python access to C section-range decompression.
10. Done: include nested disk project targets in corpus usage indexing.
11. Done: index retained decompressed child provenance from `decompression.json`.
12. Partly done: imported disk projects can materialise child targets from
   complete C records. Corpus indexing still indexes retained children and C
   facts, but does not create new child targets.
13. Done: add a non-Carrier comparator regression using the Voodoo Nightmare
   `Trainer` RNC1 payload from the corpus resources.
14. Done: raw decompressed child reproduction assembles C-rendered raw source
   to payload bytes and compares against the decompressed binary.

## Current Corpus Query Proof

After rebuilding `corpus/target_usage_manifest.jsonl`:

- `compressed:rnc1-old` finds Carrier in both the file manifest and nested disk
  project target views.
- `compressed-payload` also finds comparator RNC1 targets, including
  `3D Construction Kit II` `EditFile/runner.exe`, `3DEDIT`, `3DSOUND`,
  `3DMAKE`, and `Voodoo Nightmare` `Trainer`.
- `decompression:child` finds the retained Carrier decompressed raw child and
  exposes the existing load/entry metadata.
- These matches come from C `packed_payloads[]` records, not Python compression
  scanning, or from retained child provenance already written by the project.
