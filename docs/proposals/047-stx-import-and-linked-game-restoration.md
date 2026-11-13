# Proposal 047: STX import and linked game restoration

Status: input access, pinned-reference comparison, native STX inspection and
physical-sector access are implemented and tested. The source-mapped ST main
load and its native decoder witness are recovered; see
[loader recovery](../targets/starglider2-st-loader-recovery.md). Linked-release
artifact/target integration, a bounded ST startup witness and two qualified
code/data matches are implemented; see [linked startup](../targets/starglider2-linked-startup.md).
Full legacy source-schema migration, wider correspondence/shared export and
normal-media boot qualification remain open. See
[validation and limits](../validation/sgii-stx-reference-proof.md).

## Goal and order

First prove read-only import of the supplied, unmodified Starglider II Atari ST
STX image using an existing parser as a reference. Then implement our own native
STX reader and extend the project model to connect platform releases, recovered
payloads and shared semantics. Preserve exact original builds on each platform.
The existing Amiga SGII restoration remains paused at `d75bcf8a`.

This is a clean schema upgrade for this repository and its check-ins. Migrate
existing target data and consumers, then remove superseded representations;
maintaining parallel legacy schemas or compatibility shims is not a goal.

## Current evidence and issues to discuss before implementation

- The exact supplied ZIP is readable directly in the new task. It contains one
  STX version-3/revision-2 image. Pinned Hatari parsing reports 164 track/side
  instances, 943 sectors, eight fuzzy/CRC-error sectors and six track-image-only
  instances. Input identities and commands are in the reference proof above.
  No game bytes are committed. Do not flatten away the exceptional records.
- Our current Atari ST reader, `src/platform_atari_st_disk.c`, consumes a flat
  sector image and boot-sector/FAT metadata. It has no STX decoder.
- Reference candidate: Hatari, inspected commit
  `b18511507bcf48dcf11f32b555774ea2f5e93fd0`:
  [STX implementation](https://github.com/hatari/hatari/blob/b18511507bcf48dcf11f32b555774ea2f5e93fd0/src/floppies/stx.c),
  [structures](https://github.com/hatari/hatari/blob/b18511507bcf48dcf11f32b555774ea2f5e93fd0/src/includes/floppies/stx.h),
  [test registration](https://github.com/hatari/hatari/blob/b18511507bcf48dcf11f32b555774ea2f5e93fd0/tests/CMakeLists.txt),
  [unit-test registration](https://github.com/hatari/hatari/blob/b18511507bcf48dcf11f32b555774ea2f5e93fd0/tests/unit/CMakeLists.txt).
  The parser source was retrieved for inspection. Those two test registrations
  contain no STX reference; a dedicated upstream STX suite was **not found** after the bounded audit. The
  parser itself has now read the supplied image with sanitizers; this is not an
  upstream test-suite pass.
  Replacement validation is authorized: synthetic branch fixtures, malformed
  input and sanitizer mutation checks, plus pinned-reference comparisons on
  synthetic cases and the supplied SGII image.
- Hatari's STX source declares GPL version 2 or later. Default design: use a
  pinned external reference and write our own implementation from documented
  format facts. Copying/adapting upstream implementation or tests requires an
  explicit reuse/license decision first; no third-party code is vendored here.
- Record the supplied image's provenance honestly. Keeping its bytes unchanged
  proves fidelity to that input; its filename alone does not authenticate a
  particular original release. Unexpected format/features or missing media
  must be discussed before expanding the scope.

## 1. Reference-parser and original-image proof — first milestone

1. Materialize the exact supplied ZIP through supported file access. List its
   entries safely, inspect size limits and extract only selected disk members
   into private storage. Record archive/member SHA-256, sizes and image count;
   identify STX by contents. Do not modify or rewrite the originals.
2. Obtain the pinned reference implementation, necessary headers/build inputs
   and license notices. Find its relevant tests, fixtures and expected results,
   including tests outside the top-level test directory. Record what exists,
   what was actually run and the coverage limits. Do not equate general emulator
   tests with STX parser tests.
3. Run the reference on every supplied SGII disk. Capture a compact track/side
   and sector inventory, stored data identities, flags and exceptional records.
   Keep fuzzy masks, timing data and optional track images associated with their
   source ranges. Preserve duplicate IDs and physical ordering.
4. Confirm input hashes before/after. Identify the boot track and the loader's
   available source bytes without patching protection, repairing CRCs, replacing
   sectors or converting the sole retained copy to a flat `.st` image.

Acceptance: reproducible command/tool revision, successful reference parsing of
all supplied disks, relevant test outcomes, unchanged input hashes, and explicit
unsupported/ambiguous features. No acceptance claim until the actual image has
been read. Container parsing does not establish successful boot, payload recovery
or protection/timing equivalence. Stop and discuss any blocking issue here.

## 2. Our native STX reader and import path

- Own the parser and disk facts in C alongside `platform_disk_lib` and the
  existing Atari disk reader; Python orchestrates imports and tests. Follow the
  structured platform-format knowledge and generated-metadata conventions.
- Expose original file ranges, track instances, sector instances and stable
  data, with status, fuzzy/timing masks and optional track data. A sector ID is
  not a unique physical instance. Unresolved reads stay explicit; never choose
  a duplicate silently or manufacture deterministic fuzzy bytes.
- Provide a sector-access interface for ordinary FAT consumers and loader-driven
  extraction. Flatten only a proven deterministic subset as a derived view,
  retaining its mapping and the authoritative original STX.
- Test bounds, truncated/overflowing lengths, unsupported versions, empty and
  irregular tracks, duplicate/missing IDs, CRC/status flags, fuzzy and timing
  records. Use small redistributable synthetic fixtures and upstream tests where
  permitted. Compare our descriptors and stable bytes with the pinned reference
  on SGII; shared-code self-comparison is not independent validation.

Acceptance: native inspect/import accepts the original image directly, retains
all relevant source/protection metadata and matches the reference on supported
records. Existing flat Atari and Amiga disk behavior remains covered. Writing
STX and complete FDC emulation are separate scope, not prerequisites for reading.

## 3. Recover ST payloads with reproducible provenance

Follow the actual boot loader and its filesystem, custom directory or raw-sector
read operations. Recover ordered extents, unpacking/copying, load addresses and
entry evidence through existing analysis and bounded runtime tooling where
necessary. A custom filesystem may expose logical entries; raw extents do not
become invented filesystem files. Preserve loaders, carriers and derived outputs.

Acceptance: reproducible disk-to-payload recipes, source coordinate mappings,
hashes and qualified load contexts. Distinguish metadata import, recovered game
code and a successful normal-media launch. Raise any requirement for new FDC or
runtime capability before undertaking it. Do not replace original instructions
or force guest state to obtain a match.

## 4. Unify game, release, artifact and target identities

Introduce a game-family identity with separate release members (platform,
edition and one or more media). Use one artifact/derivation model for filesystem
extraction, sector assembly, decompression, decoding and runtime capture. Preserve
existing origin and decompression evidence through migration, rather than copy
it into a second authoritative graph.

An artifact identifies bytes; an analysis target binds bytes to platform,
sections, load map, entries and an overlay/loading context. Coordinates explicitly
identify file, decoded track/sector, payload or runtime space. Identical blobs
may share storage while retaining distinct release and load contexts.

Update `amiga_disk/project.py`, project discovery, corpus manifests/browser and
restoration consumers through this shared model. Existing same-platform variant
comparison remains a distinct relationship. Remove migrated old fields and
paths after testing extraction equivalence, reference integrity and Amiga SGII
standalone rebuilding. Preserve original binaries, MAL/DJ decisions and unique
runtime evidence; obsolete derived indexes may be regenerated.

## 5. Cross-target correspondence and knowledge reuse

Add revision/hash-bound links between qualified ranges and semantic entities,
including split/combined components. Distinguish identical bytes, address-rebound
code, modified counterparts, differently encoded assets and platform-specific
implementations. Candidate discovery uses existing decoded instructions, CFGs,
validated address references, tables and asset relationships. Normalize proven
address bindings, not every immediate constant.

Validate representative SGII matches before bulk transfer. Shared semantic
identities carry roles/names; each target keeps addresses, layout bindings and
platform assumptions. Use revision-checked restoration commands and existing
review history to admit mappings and transfers. Mutations or changed input
hashes invalidate dependent claims. Matching names, routine shape or table size
alone cannot transfer bounds, ownership, lifetime or runtime proofs.

Acceptance: recover an evidenced routine and data/structure family automatically,
reject ambiguous/conflicting matches, and demonstrate actual ST source gains.
Keep only canonical accepted mappings and unique evidence; candidate rankings
and large derived match dumps are reproducible on demand, not committed churn.

## 6. Shared source export

First render each target independently and require exact native/vasm and clean
standalone rebuilding against its own original payload. Then render common game
modules with platform-specific implementations, assets and layout definitions
from canonical facts and accepted correspondences. There must be no separately
hand-maintained common assembly tree.

Acceptance: one documented source package builds both original payloads exactly,
with platform identity and provenance retained. Original disk reconstruction,
rewritten OS-friendly loaders, relocation and a new portable edition remain
separate deliverables. Do not declare the Amiga restoration complete from byte
exactness alone or require every unknown to be solved before a useful comparison.

## Execution discipline

The native reader milestone is delivered with the replacement validation above.
The ST loader recovery is delivered as a repeatable source-bound recipe; it is
not a normal-media boot. The linked catalog now binds the recovered ST artifacts
and references the existing Amiga source history. Next expand proven ST startup
and qualified matches before shared export; raise requirements for new runtime or FDC capabilities before implementing them. Keep changes
in substantial tested batches on the established master branch, with concise
current status and no repeated observation bundles. Reuse persistent analysis
processes and regenerate only at necessary validation checkpoints. No migration
or Amiga restoration resumption is authorized merely by recording this plan.

Related design: [executable imports](020-platform-executable-import-pipeline.md),
[Atari platform knowledge](011-atari-st-platform-knowledge.md),
[decompression relationships](../design-decompression.md),
[SGII current restoration queue](../targets/starglider2-restoration-plan.md).
