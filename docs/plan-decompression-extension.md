# Decompression Extension Plan

This plan records the long-term decompression model for Amiga target analysis.
Keep it aligned with `docs/design-decompression.md`, which records current
implementation state, and `docs/design-amiga.md`, which records Amiga platform
requirements, limitations, and regression rules.

This is a requirements and direction document. It should explain what the system
must preserve and what kind of analysis we want, not prescribe one temporary
implementation shape.

## Goals

- Recover source from packed Amiga targets without losing exact reproduction of
  the shipped parent binary.
- Treat decompressed bytes as first-class analysis products with provenance,
  relationships, load addresses, entrypoints, and role classification.
- Prefer native project-owned decompression and analysis in C.
- Use external decompression suites as identifiers, references, and test
  oracles, not as the final owner of project behavior when we can support the
  codec ourselves.
- Support both disposable packer wrappers and programs that use compression as
  a normal runtime subsystem.
- Keep derived targets useful to source renderers: labels, code discovery,
  hardware usage, data classification, and reproduction must improve, not just
  comments or reports.

## Platform Requirements

Amiga-specific behavior must follow `docs/design-amiga.md`.

Important constraints from that document apply here:

- Preserve Amiga HUNK relocation semantics, including section-base anchor
  relocations outside loaded payload ranges.
- Do not turn segment headers, low-memory vectors, or runtime absolute
  addresses into ordinary labels unless analysis proves that is the correct
  source model.
- Keep direct ExecBase loads at `$00000004.l` literal.
- Distinguish low-memory ExecBase access from copied executable code at address
  `$4`.
- Preserve source/reassembly correctness before accepting derived analysis.

When this plan discovers new Amiga-specific requirements, update
`docs/design-amiga.md` as the stable platform notes. Do not hide Amiga rules in
target metadata or generic M68K logic.

## Provider Policy

Provider priority should be:

1. Native project codec implementation in C.
2. Target-owned decruncher execution using our generated C simulator, when the
   output cannot be produced by a known native codec.
3. External suites such as Ancient or XFD for identification, comparison, and
   oracle tests.

If a compressor fingerprint is recognized and we have native support, run our
implementation first. External suites may validate expected bytes or identify a
variant, but they should not be the production behavior for supported codecs.

If an external suite recognizes a codec we do not yet support, C may emit an
unsupported/identified record with provenance and corpus tags. Materialization
through the external tool can remain a transitional feature only when it is
explicit, provenance-rich, and covered by reproduction tests.

Native implementations for codecs Ancient already identifies and decompresses
are deferred for now. The current priority is the unsupported class: targets
such as Damocles where external suites do not identify the packed program and C
must use target-owned decruncher evidence.

Python must not grow decompression scanning or execution heuristics. Python may
materialize project files only from C-emitted records.

## Native Codec Support

Native codecs should be added when corpus evidence shows recurring value.

Each codec needs:

- C fingerprint/identify logic.
- C decompressor.
- Bounded source range and output size handling.
- Checksums or internal validation where the format supports it.
- Corpus tags for codec id, variant, confidence, and source range.
- Isolated tests from synthetic streams or known tiny fixtures.
- Comparator tests against external tools where available.
- At least one real corpus target validation before enabling automatic
  materialization.

Codec knowledge belongs in decompression/platform code, not in Python wrappers
or target-local metadata.

## Target Decruncher Execution

Some targets do not expose a simple standalone packed stream. They contain code
that writes a runtime image to absolute memory and then branches into it, or
code that periodically decompresses runtime assets.

For those cases, use a C provider backed by our generated simulator.

Rules:

- Execute only from C.
- Use our generated simulator, not `machine68k`.
- `machine68k` may remain an independent oracle for simulator tests only.
- Seed memory and registers only from C analysis evidence.
- Bound instruction count, memory map, write ranges, and stop conditions.
- Stop on branch into produced output, unsupported instruction, illegal external
  access, trap/OS dependency, or budget exhaustion.
- Do not emulate an entire Amiga machine as part of decompression discovery.
- Do not materialize bytes unless the output range, load address, and use site
  are supported by evidence.

This path is for deterministic extraction from already-observed unpacking code,
not for speculative execution.

## Payload Roles

A produced payload must be classified before the UI or renderer treats it as the
main target.

Roles:

- `primary_program`: a disposable wrapper decompresses the real program and
  transfers control to it.
- `overlay_code`: decompressed code is entered temporarily while the parent
  remains meaningful.
- `runtime_data`: decompressed graphics, audio, maps, text, tables, or other
  data used by active code.
- `resident_codec`: the decompressor remains part of the program's runtime
  system.
- `unknown_runtime_payload`: output exists, but its role is not understood.

Only `primary_program` should naturally become the preferred default source
view. Other roles should be linked as participating target ranges or child
entities, not as replacements for the parent.

## Target Relationship Model

The model should represent decompression as an event graph:

```text
parent target
  -> decompression event
     -> source packed range
     -> decompressor code range
     -> produced runtime range
     -> derived target/entity
```

The event should record:

- provider id and version/stamp
- codec id or simulated-decruncher id
- parent target id
- source section/file offset and packed size
- decompressor code range when known
- output load address, size, and hash
- entrypoint or first use site
- role and confidence
- acceptance/rejection reason
- reproduction status for parent and child
- whether the parent remains active after output is produced

This graph must support multiple produced payloads from one parent and multiple
parents sharing the same codec implementation.

## Corpus Indexing

Corpus indexing should make decompression evidence searchable without mutating
targets.

Required tags/xrefs:

- codec id and variant
- provider id
- native-supported vs external-identified
- simulated-decrunch candidate
- payload role
- source packed range
- output load address
- entrypoint/use site
- materializable vs unsupported vs rejected
- rejection reason
- comparable pattern tags for recurring decruncher shapes

Pattern-specific tags should be added when more than one target shows the same
valuable shape. Bloodwych, Carrier Command, Damocles, Magicland, Conqueror, and
other corpus comparators should be used as real examples, not hidden specs.

## Acceptance Gates

Keep automatic materialization conservative:

- Packed source must not overlap accepted code unless C analysis has explicit
  evidence that the bytes are embedded data or runtime output.
- Output must have bounded size and deterministic bytes.
- Load address and entry/use site must be known for executable output.
- Data output must have a plausible consumer or platform use.
- Parent reproduction must remain exact.
- Child reproduction must be exact for raw/materialized payloads.
- Rendering must not introduce fragile absolute addends over source ranges.
- Derived labels must not mask low-memory Amiga vectors or HUNK relocation
  anchors.

Failing a gate should produce an indexed work item, not a guessed child target.

## Regression Risks To Avoid

- Replacing relocatable HUNK anchor expressions with numeric constants.
- Rendering low-memory ExecBase as an ordinary label.
- Treating runtime copied code, vector slots, and hardware registers as one
  generic absolute-address bucket.
- Creating child targets from weak external-tool micro-hits.
- Letting Python identify, execute, or classify decompression independently of
  C.
- Treating every decompressed payload as a replacement main program.
- Losing parent exact reproduction while improving child analysis.
- Adding comments-only gains without improving analysed source structure.

## Work Stages

1. Record current external-provider behavior and keep Carrier RNC as the first
   proven materialized child.
2. Defer native rewrites of codecs Ancient already identifies and decompresses.
   Keep those as provider-backed evidence while higher-value unsupported cases
   are addressed.
3. Add a C event model that separates codec identity, decompressor code,
   produced bytes, role, and target relationship.
4. Add role classification and UI/corpus tags.
5. Add the C simulator-backed decrunch provider for targets where provider
   identification is insufficient but code evidence is strong.
6. Expand corpus comparators and pattern tags so new heuristics are validated
   beyond one target layout.
7. Keep `docs/design-amiga.md` updated whenever decompression exposes new
   Amiga-specific rendering or reproduction constraints.

## Current Implementation Notes

- Carrier RNC remains the first proven materialized child.
- Ancient-backed scanning still exists for codecs without native project
  support.
- A bounded C simulator run primitive now exists as the first substrate for
  target-owned decruncher execution. It is generic simulator infrastructure,
  not a Damocles-specific workaround.
- C analysis now exposes first-class `decompression_events[]` records alongside
  packed payloads and derived target suggestions. Events carry `payload_role`,
  `payload_role_confidence`, `parent_remains_active`, `event_kind`, and
  `event_id`. Corpus indexing tags these event fields so event and role work can
  be queried across targets without treating every output as a replacement
  target.
- C analysis now emits unsupported self-decrunch events when analysed code
  writes to an absolute runtime range and transfers control there. Damocles is
  the first real proving target for this path. Corpus indexing currently also
  finds Voodoo Nightmare and Magicland Dizzy as Amiga comparators for the same
  unsupported event class.
- Simple self-contained self-decrunch events can now be probed with the
  generated simulator and report `simulated_output_observed` plus output range
  and stop metadata.
- Simulator probing now seeds absolute source memory from C policy runtime
  ranges/execution views when those mappings are explicit, covered by an
  isolated regression with an absolute source read.
- Simulated output events now include `simulated_output_sha256`, and corpus
  indexing exposes a `decompression:simulated_output_hash` tag.
- Simulator output range now comes from concrete write tracing, not post-run
  memory diffs, so writes are retained even when the value equals the prior
  memory byte.
- Simulator write tracing now retains merged concrete write ranges and accepts
  the output range containing the transfer target, rather than the broad min/max
  span. This keeps unrelated scratch or hardware writes out of simulated payload
  hashes.
- Simulator-backed decrunch runs now have a generic external-write policy. The
  Amiga platform uses generated hardware-register metadata for that policy, so
  hardware side-effect writes can be allowed without treating them as payload
  memory and without hardcoding Amiga addresses in the simulator.
- The next implementation step is extending simulator-backed output capture for
  real unsupported events with inferred memory-map seeding where justified and
  conservative materialisation gates.
