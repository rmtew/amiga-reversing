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
- `platform_file_cli identify-packed-range` can identify an explicit byte range.
- `platform_file_cli decompress-packed-range` can materialise provider output
  and report packed/decompressed SHA-256 and decompressed size.
- The same identify/decompress records are exported through
  `platform_file_lib.dll` for the Python C backend wrapper.
- Carrier's RNC stream is identified both as an extracted range file and in the
  original parent file at offset `$4C60`.
- The C-decompressed Carrier output hash matches the existing derived child
  binary.

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

C should next emit these records through platform analysis JSON as:

- `packed_payloads[]`
- `derived_target_suggestions[]`
- corpus tags

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

Raw binary reproduction is still a gap for the Carrier child. The child renders
and benchmarks, but reproduction currently reports unsupported because raw output
assembly is not wired as an exact reproduction backend.

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
- Python can call the C decompression provider through the C backend wrapper;
  tests cover unknown payload handling without Python-side identification.

## Work Plan

1. Done: add the C decompression provider interface.
2. Done: wrap Ancient as the first provider for explicit range
   identification.
3. Done: add provider decompression output, size, and hash reporting.
4. Partly done: expose provider `packed_payloads[]` JSON through CLI and DLL.
   Still missing platform analysis JSON integration and
   `derived_target_suggestions[]`.
5. Move Carrier RNC discovery from manual materialisation into C-emitted
   records.
6. Add isolated C tests for provider result acceptance, code-overlap rejection,
   and parent/child relationship output.
7. Add Python materialisation from C records only.
8. Apply the pipeline to corpus indexing and imported project targets.
9. Add comparator targets for at least one non-Carrier packed payload before
   broadening policy.
10. Wire raw decompressed child reproduction so source can be assembled and
   compared to the decompressed bytes.
