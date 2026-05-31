# Proposal 027: Native Decompression Execution And Materialization

Status: implemented for in-executable native decompression; loader/file-backed
compressed payloads are identified when disk/file loading and target-owned
acceptance evidence reconcile, but materialization still requires replayed
native decompressor execution.

This proposal explains three failed decompression/materialization cases:
Damocles Tetragon section 2, Conqueror's embedded ByteKiller/CRUN-style
decruncher, and Magicland Dizzy's disk-loaded target-owned decompression
candidate. They
point at the same architectural need: target-owned decompression routines should
be executed with our M68K executor, their writes should be observed, and the
resulting outputs should be materialized according to proven role. Hand-coded
or inferred models can help recognize or compare, but they must not be the
authority when native target code is present.

## Checkpoint Index

- [x] Problem Statement
- [x] Tutorial: Existing Decompression Support
- [x] Tutorial: The Damocles Tetragon Failure
- [x] Tutorial: The Conqueror Relocated Decruncher
- [x] Tutorial: Magicland Disk-Loaded Asset Decompression
- [x] Principle: The Target-Owned Decompressor Is The Spec
- [x] Tutorial: Executor-Based Native Decompression
- [x] Output Roles And Materialization Policy
- [x] Validation Gates
- [x] Compatibility With Existing Working Targets
- [x] Proposed Implementation Slices
- [ ] Acceptance Criteria
- [x] Non-Goals

## Problem Statement

We currently have at least three ways to arrive at misleading decompression
state:

1. A recognized unpacker can be materialized by a hand-coded clone that does not
   match the native target-owned stub.
2. A relocated unpacker can be present in the binary, but not surfaced as a
   decompressed child because we only render the original packed bytes.
3. A loader/decompressor can produce non-executable assets or data, but our
   current child-target model mostly thinks in terms of executable payloads.

Damocles shows the first failure. It contains two recognized Tetragon
unpackers. The first currently materializes a useful code-bearing payload:

```text
parent hunk section 1
  -> " TETRAGON " marker
  -> C Tetragon reimplementation
  -> raw payload at $40000
  -> entrypoint $40000
  -> valid M68K code and data
```

The second originally exposed the failure mode. The static clone materialized
bytes, but the configured entrypoint was not credible code:

```asm
abs_0_00059484:
    or.b d0,(a2)+
    andi.w #139,$6311(a0)
    dc.b $43,$0B,$01,$01,$0C,$00,$44,$00
```

That was a failed materialization, not a disassembler problem. The output was
round-trippable because source export can preserve bytes, but byte preservation
does not prove the bytes are the correct decompressed program.

Conqueror shows the second failure. The parent program contains a two-stage
bootstrap:

```text
startup code
  -> copies a tiny relocation routine to $000004
  -> relocation routine copies the decruncher to $000040
  -> decruncher unpacks a PC-relative payload to $000400
  -> final jump enters $000400
```

The rendered source at `$400` is still the packed/pre-decompression image, so
it decodes as unrealistic code-like noise. The correct payload is the runtime
bytes written by the decruncher, not the original bytes sitting at that address
in the file.

Magicland Dizzy shows the third failure. The target has real disk-access code
and a loader-adjacent routine that appears to process loaded data after a
target-owned long-word acceptance check. The apparent packed input is passed
through `a0`, output is written through caller-provided `a3`, and control
returns to the parent flow. That is a candidate target-owned decompression
case, but not a primary-program self-decrunch shape until C analysis reconciles
the file/disk load with the routine call and observed writes:

```text
disk/file loader
  -> reads bytes from source media
  -> target code accepts/rejects the bytes
  -> calls target-owned processor/decompressor
  -> routine writes data through a3
  -> returns to caller, no final transfer into output
```

The clean answer is not to force this into the existing executable child path.
It should be represented by the same native execution/write-observation model,
then materialized as an asset/data output only when the source provenance, call
state, output range, and role are proven. There is no framework-level Magicland
format handler here: either analysis proves the load and decompression path, or
the bytes remain an unresolved compressed/loaded payload.

## Tutorial: Existing Decompression Support

The current import pipeline has three broad decompression paths.

### 1. Static Format Decompressors

For recognized packed formats with stable container metadata, we can call a
format-specific decompressor:

```text
packed range + codec id + declared size/address
  -> decompressor
  -> binary.bin
  -> source_binary.json
```

This works when the packed data format is well understood and the target is not
using a custom runtime stub.

### 2. Self-Decrunch Execution

For code that writes an unpacked payload at runtime, the C backend can simulate
the decrunch routine and observe writes:

```text
parent executable bytes
  -> seed runtime policy
  -> execute bounded M68K
  -> collect write ranges
  -> identify final transfer
  -> materialize observed output
```

This is the more reliable model because it follows the program's actual code.

### 3. Recognized Unpacker Signatures

Tetragon currently uses a recognized unpacker path. The backend finds the
marker and infers constants from nearby code:

```text
" TETRAGON " marker
  -> infer packed source offset
  -> infer postpass source range
  -> infer output start
  -> infer final entrypoint
  -> run hand-coded C Tetragon clone
  -> validate entrypoint
```

The key function shape is:

```c
collect_recognized_tetragon_events_for_section_local(...)
{
    find_marker(" TETRAGON ");
    infer_bounds_from_nearby_code();
    recognized_tetragon_try_unpack_event_local(...);
}
```

The hand-coded path is fast, but it is only correct when our inferred model
matches the native stub exactly.

### 4. Runtime Copy And Relocated Stub Detection

Some targets do not have a marker string. Instead, they expose the unpacker by
copying code to a low runtime address and jumping there:

```text
source code bytes
  -> copied to low memory
  -> executed from low memory
  -> write unpacked payload somewhere else
  -> jump to unpacked payload
```

This is visible in analysis as runtime-copy behavior and low-memory transfer
targets. It is not enough to classify the copied bytes as code. We also need to
execute the copied unpacker and materialize the observed output.

### 5. Loader-Owned Asset Decompression

Some targets decompress data that is not entered as code. The evidence looks
different:

```text
loader reads external bytes
  -> magic/header check identifies packed block
  -> decompressor is called like a subroutine
  -> output pointer is supplied by caller
  -> routine returns to caller
  -> later code consumes the output as tables, strings, graphics, maps, or audio
```

This is still native decompression. The output role is different. It should not
be rejected just because there is no final `jmp` into the produced bytes, and it
should not be promoted to executable source unless later control-flow evidence
proves code.

## Tutorial: The Damocles Tetragon Failure

The second Damocles stub tells us more than the C clone currently uses.

Textual sketch of the parent code:

```text
section 2 startup
  copies native stub bytes to runtime $100
  pushes $59484
  pushes $2700
  sets a0 to packed data
  jumps to $40(a2), where a2 points at copied stub base

copied stub at $100
  postprocesses data into target memory starting at $1000
  runs until source reaches $7FFFF
  jumps to $59484
```

The current C clone treats the marker as enough to reproduce the unpacker. It
does not execute the copied native stub. It therefore has to guess or duplicate:

- bitstream direction and long-reference width
- source cursor boundaries
- postpass escape semantics
- register state at handoff
- stack conventions
- final control transfer behavior
- any per-stub variant behavior

For section 1 those assumptions happen to produce valid code. For section 2
they originally produced a byte image whose entrypoint failed code validation.

The important lesson is:

```text
valid packed marker + produced bytes != valid decompressed payload
```

The acceptance proof must include code-bearing validation at the known
entrypoint.

## Tutorial: The Conqueror Relocated Decruncher

Conqueror is useful because the native routine is visible and matches a known
XFD family.

The target first enters supervisor mode, disables interrupts/DMA, then copies a
tiny helper to `$4`:

```asm
lea.l loc_0_00000148.l,a0
lea.l runtime_code_00000004.l,a1
move.w #$E,d0
copy_to_4:
    move.b (a0)+,(a1)+
    dbf.w d0,copy_to_4
```

That helper is a long-copy trampoline:

```asm
move.l (a0)+,(a1)+
subq.l #1,d0
bne.b copy_loop
jmp $00000064
```

The parent then asks the helper to copy the real decruncher and packed data to
`$40`:

```asm
lea.l loc_0_00000154.l,a0
lea.l $00000040.l,a1
move.l #$3A9,d0
jmp $00000004.l
```

The relocated decruncher starts at `$64`. It reads its local header at `$14C`
and writes backwards into an output buffer starting at `$400`:

```asm
abs_0_00000064:
    lea.l abs_0_0000014C(pc),a0
    lea.l abs_0_00000400.l,a1
    move.l (a0)+,d0       ; packed length: $0D70
    move.l (a0)+,d1       ; unpacked length: $1D00
    move.l (a0)+,d5       ; checksum
    movea.l a1,a2
    adda.l d0,a0
    adda.l d1,a2
```

The bitstream core is a backwards ByteKiller/CRUN-style loop:

```asm
move.l -(a0),d0
eor.l d0,d5
...
move #$10,ccr
roxr.l #1,d0
...
move.b d2,-(a2)
...
move.b $0(a2,d2.w),(a2)
```

This closely matches XFD's `ByteKillerClone.a` `(CRUN) Data Cruncher` core,
especially the `D_CRUN` loop:

```asm
Eoruj:
    move.l -(a0),d0
    eor.l d0,d5
    move.w #$0010,ccr
    roxr.l #1,d0
    rts
```

The XFD source is useful for naming the family and checking the algorithm, but
Conqueror does not present a clean `CRUN` file header. It embeds a customized
runtime routine. Treating it as a native-execution candidate is therefore more
reliable than trying to force it through XFD-style file recognition.

Successful native execution should look like:

```text
run copy-to-$4 bootstrap
  -> run copied long-copy helper
  -> run decruncher at $64
  -> observe writes to $400..$2100
  -> stop on final jump to $400
  -> validate $400 as code-bearing entrypoint
```

## Tutorial: Magicland Disk-Loaded Asset Decompression

Magicland's relevant loader/decompressor shape is recorded in TODO.md under
`Amiga/Magicland Dizzy resolved and deferred notes`. The important facts are:

```text
source disk exists in resources/platform_amiga/
disk project exists under targets/amiga_disk_magicland-dizzy-1991-codemasters-trsi-lsd/
MD child executable is rendered as targets/.../amiga_hunk_md_e066dc14/md.s
loader code accesses Amiga disk hardware directly
decompressor candidate is near abs_0_000647F2
target code contains a long-word acceptance check before calling the candidate
```

The current C analysis already improves the source around the disk helper by
rendering CIA/disk DMA names. That is source-quality progress, but it does not
prove which disk bytes become which decompressed outputs.

The target-owned asset path needs two extra kinds of evidence:

```text
external source provenance:
  disk/resource/container byte range read by the loader

call contract:
  packed input pointer
  output pointer
  output bounds or observed writes
  return-to-caller stop condition
```

Textual sketch:

```text
read disk/file bytes into buffer
  -> target-owned acceptance check
  -> a0 = accepted input block
  -> a3 = output buffer
  -> jsr abs_0_000647F2
  -> observed writes to output buffer
  -> return to caller
  -> later references classify output role
```

That last step matters. The output may be:

```text
text/string table
graphics/tile/map data
audio data
script/table data
secondary code
unknown bytes with proven provenance
```

Only secondary code should become a code child target. Data outputs should be
materialized as asset/data children with structured metadata and optional
renderer support. Unknown outputs should remain byte-preserving assets with
clear provenance, not invented semantic names.

## Principle: The Target-Owned Decompressor Is The Spec

For target-owned decompressors, the native routine is the most precise
specification. It already encodes the real variant details. A handwritten C
clone or an external XFD routine is a derived interpretation and can drift.

The proposed rule:

```text
When a decompression routine is present in the target, execute that routine
unless there is a stronger reason not to.
```

The handwritten decompressor can remain as:

- a recognizer
- a comparator
- a performance optimization after executor equivalence is proved
- a fallback for targets where execution is not yet possible

XFD sources can also remain useful as a knowledge aid:

- identify common decruncher families
- name algorithms and variants
- sanity-check length/checksum fields
- provide comparator implementations where the file format is explicit

They should not override the embedded routine when the target carries its own
runtime decompressor.

## Tutorial: Executor-Based Native Decompression

The reliable path is to add a native decompression materializer that uses our
M68K executor. It should cover marker-recognized unpackers, relocated runtime
copy unpackers, and loader-owned asset decompressors.

### Step 1: Find The Decompression Event

Keep the existing signature scan, but add runtime-copy/handoff scans:

```text
scan hunk sections
  -> find " TETRAGON "
  -> locate surrounding code window
  -> infer handoff site and obvious constants

scan hunk sections
  -> find copy-to-low-memory loops
  -> find transfer into copied code
  -> find copied-code transfer into output payload

scan loader/data-flow facts
  -> find packed-block magic checks
  -> bind loader source bytes to disk/resource/container range
  -> find decompressor call contract
  -> identify input and output pointer registers
```

The event is still useful metadata:

```json
{
  "codec_id": "tetragon",
  "source_kind": "recognized_unpacker",
  "source_section": 2,
  "unpacker_marker_offset": 96,
  "entrypoint": 365700
}
```

Conqueror should produce a different but compatible candidate:

```json
{
  "codec_id": "bytekiller-crun-like",
  "source_kind": "relocated_native_unpacker",
  "source_section": 0,
  "output_role": "primary_program",
  "copied_stub_runtime_address": 4,
  "decompressor_runtime_address": 64,
  "load_address": 1024,
  "entrypoint": 1024
}
```

Magicland should produce an asset-oriented candidate only after the loader,
input bytes, call state, and writes are reconciled:

```json
{
  "source_kind": "target_loader_decompression_candidate",
  "source_section": 0,
  "packed_source_provenance": {
    "container_kind": "amiga_disk",
    "status": "pending_disk_byte_binding"
  },
  "input_pointer_register": "a0",
  "output_pointer_register": "a3",
  "output_role": "asset_data"
}
```

These events should mean "candidate native decompression event", not "trusted
decompressed payload".

### Step 2: Reconstruct The Native Handoff

Instead of jumping straight into a C clone, replay or model the parent handoff.

For Damocles section 2, the handoff can be synthesized from the copied-stub
transfer:

```asm
lea.l abs_2_00000100(pc),a1
movea.l a1,a2
lea.l loc_2_0000006A-(*+2)(pc),a0
...
copy_stub:
    move.b (a0)+,(a1)+
    dbf.w d0,copy_stub
pea.l $00059484
pea.l $00002700
lea.l packed_data(pc),a0
jmp $0040(a2)
```

Executor setup can either run this parent prelude directly or synthesize the
equivalent state:

```c
NativeUnpackSeed seed = {
    .pc = copied_stub_base + 0x40,
    .a0 = packed_source_runtime_address,
    .a1 = packed_source_runtime_address,
    .a2 = copied_stub_base,
    .a5 = custom_color_register_or_safe_stub,
    .sp = scratch_stack_top,
};

push32(&seed, 0x00059484);
push32(&seed, 0x00002700);
```

Running the prelude is preferable when practical. Synthesizing is acceptable
when the handoff recognizer has enough evidence and the setup is recorded in the
event.

For Conqueror, the safer path is to run more of the native bootstrap because it
has nested relocation:

```text
start at post-supervisor setup
  -> copy helper to $4
  -> execute helper copy to $40
  -> execute decruncher at $64
```

The same materializer should support both modes:

```c
typedef enum NativeUnpackStartMode {
    NATIVE_UNPACK_START_REPLAY_PARENT_PRELUDE,
    NATIVE_UNPACK_START_SYNTHESIZED_HANDOFF,
} NativeUnpackStartMode;
```

Asset decompression adds a third start shape: replay a normal subroutine call
from the loader, or synthesize the call only when data-flow facts prove the
input/output register contract and the external packed bytes are available.

```c
typedef enum NativeDecompressionStartMode {
    NATIVE_DECOMP_START_REPLAY_PARENT_PRELUDE,
    NATIVE_DECOMP_START_SYNTHESIZED_HANDOFF,
    NATIVE_DECOMP_START_REPLAY_LOADER_CALL,
} NativeDecompressionStartMode;
```

### Step 3: Build The Runtime Memory Map

The executor needs the same memory view the unpacker expects:

```text
$000000-$0007FFFF  scratch/chip-like RAM
parent section bytes at their runtime locations
copied stubs at observed low-memory destinations
packed source bytes at observed/derived source address
stack in valid RAM
custom/CIA writes accepted or stubbed
```

Textual memory illustration:

```text
$000100  copied Tetragon postpass stub
$001000  expected output start
$0130B6  postpass source start candidate
$059484  known final entrypoint
$07FFFF  source end / upper RAM boundary
```

Conqueror memory illustration:

```text
$000004  copied long-copy trampoline
$000040  relocated decruncher and packed data
$000064  decruncher entry
$00014C  local packed header: packed len, output len, checksum
$000400  expected output start and final entrypoint
$002100  expected output end from $400 + $1D00
```

Magicland memory illustration:

```text
disk/file byte range  source bytes accepted by target loader code
runtime input buffer  accepted bytes copied by loader
runtime output buffer caller-provided a3 destination
decompressor routine  abs_0_000647F2 candidate
caller continuation   return address after jsr
```

The executor should observe writes, not assume every byte between `$1000` and
the largest touched address is meaningful code or meaningful asset data.

### Step 4: Run With Bounded Stops

The run should stop on one of a small number of meaningful conditions:

```text
final PC == known entrypoint
  -> candidate success, validate output

return PC == caller continuation
  -> candidate asset/data success, validate output role

PC leaves executable unpacker/range unexpectedly
  -> failed candidate

step budget exhausted
  -> failed candidate

invalid instruction in unpacker stub
  -> failed candidate
```

The stop condition should be part of the event record:

```json
{
  "execution_stop": "final_transfer",
  "final_pc": 365700,
  "write_range_start": 4096,
  "write_range_end": 497097
}
```

For Conqueror the equivalent success record would be:

```json
{
  "execution_stop": "final_transfer",
  "final_pc": 1024,
  "write_range_start": 1024,
  "write_range_end": 8448
}
```

For Magicland the equivalent success record would be:

```json
{
  "execution_stop": "return_to_loader",
  "return_pc": 419910,
  "write_range_start": 205312,
  "write_range_end": 209408,
  "packed_source_provenance_status": "proven"
}
```

### Step 5: Materialize From Observed Writes

The output range should be derived from runtime writes and final transfer
evidence:

```text
observed writes
  -> merge contiguous payload writes
  -> choose range containing known entrypoint for executable outputs
  -> or choose range written through proven output pointer for asset outputs
  -> materialize that range with output role metadata
  -> validate according to role
```

Pseudocode:

```c
ObservedRange payload = select_payload_range(
    writes,
    known_entrypoint,
    expected_role_code_bearing
);

if (!range_contains(payload, known_entrypoint)) reject();
write_output(memory + payload.start, payload.size);
```

For asset/data outputs:

```c
ObservedRange payload = select_payload_range_for_output_pointer(
    writes,
    output_pointer_register,
    proven_packed_source
);

if (!range_written_by_decompressor(payload)) reject();
write_asset_output(memory + payload.start, payload.size, output_role);
```

This avoids declaring an enormous memory span as a primary program merely
because the stub touched or scanned it. It also avoids using the original file
bytes at the destination address when the real payload is only produced at
runtime.

## Output Roles And Materialization Policy

Native decompression can produce different outputs. The materializer must record
the role explicitly instead of assuming every output is an executable child.

```text
primary_program:
  final transfer enters the output
  output becomes executable child target after code validation

secondary_code:
  later control/data-flow proves execution can enter the output
  output becomes code-bearing child or subrange after code validation

asset_data:
  loader/decompressor writes bytes and returns to caller
  later references or format evidence classify data role
  output becomes asset/data child, not executable source

unknown_data:
  packed provenance and writes are proven, semantic role is not
  output is byte-preserving data child with review status
```

This gives Magicland a first-class path. A loader-produced data output does not
need a fake entrypoint to be useful. It needs proven source media bytes, proven
decompressor execution, observed output writes, and conservative role
classification.

## Validation Gates

Executor output is accepted only when it passes payload validation.

For a code-bearing payload with known entrypoint:

```text
1. final executor transfer reaches the known entrypoint
2. entrypoint lies inside the materialized output range
3. facts_v2 decodes credible reachable code from that entrypoint
4. no unsupported-instruction demote at the entry block
5. required instruction validation does not fail
6. round-trip assembler output matches materialized bytes
```

For Damocles section 2, `$59484` is the hard gate. If the output at `$59484`
starts with junk like `or.b d0,(a2)+`, the event remains unresolved. The system
must then report "native execution did not produce a valid code-bearing
payload", not "decompressed primary program".

For Conqueror, `$400` is the hard gate. If the original bytes at `$400` decode
as junk, that is expected before decrunching. The accepted payload must be the
executor-observed bytes written to `$400`, and those bytes must validate as code.

For asset/data outputs, code validation is the wrong gate. The accepted output
must instead prove:

```text
1. packed input bytes have durable provenance from disk/resource/container data
2. executor starts from a proven loader call or proven synthesized call contract
3. writes are made by the decompressor into the candidate output range
4. the routine returns or reaches another documented non-entry stop condition
5. the output range bounds come from observed writes, header fields, or consumer
   evidence, not a guessed maximum buffer span
6. role is classified from evidence:
   - accepted data format/parser evidence
   - later references from code
   - text/table/graphics/audio signatures backed by consumer use
   - otherwise unknown_data
7. round-trip/export preserves the materialized bytes exactly
```

For Magicland, a magic-value acceptance check and the apparent `a0`/`a3` call
shape are not enough by themselves. The accepted asset output must bind the
input block to actual disk/file bytes and observe the decompressor writes. If
the source bytes cannot be bound, the event remains a candidate with
diagnostics.

## Compatibility With Existing Working Targets

This should not break working decompression targets.

The migration model:

```text
existing recognizer
  -> try executor materialization
  -> validate entrypoint and output role
  -> if valid, prefer executor output
  -> optionally compare C clone output
  -> keep old C clone only as fallback/comparator
```

For existing section 1 Damocles behavior:

```text
executor output sha256 == current C clone sha256
  -> mark executor validated
  -> keep same child target identity
```

For section 2:

```text
C clone output invalid at entrypoint
executor output valid
  -> replace stale child bytes with executor output

C clone output invalid
executor output invalid
  -> no child target
  -> parent event remains actionable with execution diagnostics
```

The long-term simplification is to move target-owned unpackers toward one common
path:

```text
recognize marker, handoff, or loader call
  -> execute native code
  -> observe writes
  -> classify output role
  -> validate payload according to role
  -> materialize
```

Custom C unpackers and XFD-derived implementations then become optional
accelerators. They are acceptable only when they are tested against executor
output for real fixtures or when no target-owned code is available.

For asset/data outputs the compatibility rule is similar:

```text
existing disk/resource import
  -> bind source bytes to loader reads
  -> execute decompressor call
  -> materialize asset only if provenance and writes are proven
  -> keep unknown outputs byte-preserving until consumer evidence classifies them
```

This avoids dragging every disk block into noisy targets while still letting
validated loader-produced assets become browseable children.

## Proposed Implementation Slices

### Slice 1: Event Model

Extend decompression events with native execution fields:

```json
{
  "native_execution_supported": true,
  "native_execution_status": "not_run|valid|invalid|timeout",
  "native_execution_stop": "final_transfer",
  "native_execution_final_pc": 365700,
  "native_execution_start_mode": "replay_parent_prelude",
  "output_role": "primary_program|secondary_code|asset_data|unknown_data",
  "observed_write_ranges": [
    {"start": 4096, "end": 497097}
  ],
  "packed_source_provenance_status": "not_needed|pending|proven|failed"
}
```

### Slice 2: Handoff And Relocation Recognizers

Recognize copied-stub handoff patterns:

```text
copy bytes to runtime stub
push final entrypoint
push status/register seed
jump into copied stub
```

Recognize nested relocated-decruncher patterns:

```text
copy helper to low memory
helper copies decruncher/blob to another low address
decruncher writes backwards into payload range
decruncher jumps to payload start
```

Recognize loader-owned asset decompression patterns:

```text
loader reads disk/resource/container bytes
magic/header check accepts packed block
caller sets input and output pointer registers
decompressor is called as subroutine
decompressor writes through the output pointer and returns
```

The recognizer should emit enough facts to seed execution without relying on
free-form comments.

### Slice 3: Executor Materializer

Add a materializer parallel to the current C clone:

```c
recognized_unpacker_try_execute_native_local(...)
{
    build_runtime_memory();
    replay_prelude_or_seed_registers_and_stack();
    run_executor_until_stop();
    collect_write_ranges();
    select_payload_range();
    classify_output_role();
    validate_output_for_role();
}
```

For loader-owned assets the same materializer must be able to build memory from
external source provenance:

```c
native_decompression_try_materialize_asset_local(...)
{
    bind_loader_reads_to_container_bytes();
    build_runtime_memory_with_packed_block();
    replay_loader_call_or_seed_call_contract();
    run_executor_until_return();
    collect_write_ranges();
    select_output_pointer_range();
    classify_asset_or_unknown_data();
}
```

### Slice 4: Comparator Mode

For known-good events, compare native execution output against the existing C
clone:

```text
same bytes
  -> C clone remains trusted accelerator

different bytes
  -> executor wins if validation passes
  -> record comparator mismatch
```

### Slice 5: Import Policy

Import should create child targets only for validated payloads:

```text
status == materializable
output_role == primary_program
validation == valid
```

Invalid or unresolved native execution should become parent review state, not a
raw child containing misleading bytes.

Asset/data outputs should use a parallel import rule:

```text
status == materializable
output_role in {asset_data, unknown_data}
packed_source_provenance == proven
write_range_validation == valid
```

These children are not executable targets. They are browseable materialized
outputs with source provenance, bytes, role evidence, and optional format
renderer metadata.

### Slice 6: Regression Fixtures

Add fixture assertions:

```text
Damocles section 1:
  executor materializes current valid payload

Damocles section 2:
  executor either materializes valid code at $59484
  or refuses with detailed native execution diagnostics

Conqueror:
  executor replays the nested relocation
  materializes output load=$400 entry=$400
  validates $400 as code-bearing payload

Magicland:
  executor binds loaded source bytes to disk/file provenance
  replays the loader-owned decompressor call from proven register/memory state
  materializes observed output writes as asset/data, not code
  refuses cleanly when disk-byte provenance is not proven
```

The desired end state is valid materialized children for real code-bearing
outputs and valid materialized asset/data children for non-executable outputs,
not merely blockers.

## Acceptance Criteria

- Damocles section 1 still materializes the known valid payload.
- Damocles section 2 is attempted through native executor materialization.
- If section 2 materializes, `$59484` validates as reachable M68K code.
- If section 2 does not materialize, diagnostics identify the failed native
  execution condition.
- Conqueror is attempted through native executor materialization.
- If Conqueror materializes, output has `load_address=$400`,
  `entrypoint=$400`, and a size derived from observed writes/header evidence.
- Magicland loader-owned decompression is attempted through the same native
  execution/write-observation model.
- Magicland asset output is materialized only when the packed block is bound to
  exact source disk bytes and the decompressor writes are observed.
- Magicland asset output is classified as `asset_data` or `unknown_data` unless
  later evidence proves executable code.
- Import never creates a primary-program child from bytes that fail entrypoint
  validation.
- Import never creates an executable child for a return-to-caller asset
  decompression event without independent code-entry proof.
- Existing non-Tetragon decompression paths continue to pass their current
  fixtures.
- The C Tetragon clone and XFD-derived routines are no longer the only source
  of truth for target-owned unpackers.
- Asset/data materialization records source provenance, output role, observed
  write ranges, and role evidence in structured facts.

## Non-Goals

- Do not remove all static decompressors.
- Do not require a full Amiga emulator.
- Do not accept byte-exact round-trip as proof of decompression correctness.
- Do not hardcode Damocles- or Conqueror-only output bytes or hashes as the
  solution.
- Do not hardcode Magicland-only decompressed bytes or disk offsets as the
  solution.
- Do not classify non-executable decompressed output as code without control-flow
  or entrypoint evidence.
- Do not import every disk/resource block as a target. Only materialize outputs
  with proven loader/decompression provenance.

## Implementation Notes

Current implementation progress:

```text
runtime-copy facts
  -> materialized runtime views copied into simulator memory
  -> final transfer candidates from copied code are executed natively
  -> observed write range containing the transfer target is selected
  -> facts_v2 validates the resulting entrypoint before primary_program
```

This resolves the Conqueror class without a ByteKiller/CRUN file-format shortcut.
The C backend now detects the materialized runtime view at `$40`, starts native
execution at `$64`, observes writes to `$400..$2100`, validates `$400` as code,
and materializes the output as a primary-program raw child:

```json
{
  "event_id": "decompression:self_decrunch:section:0:00000040:00000400",
  "source_kind": "self_decruncher",
  "provider_id": "m68k-sim-decrunch",
  "load_address": 1024,
  "entrypoint": 1024,
  "simulated_output_size": 7424,
  "payload_role": "primary_program",
  "payload_role_confidence": "native_unpack_entry_validated"
}
```

Damocles section 2 now materializes through the normal disk refresh path as
`amiga_raw_damocles_53b24620_native_tetragon_02_00000060`. The child records
`provider_id=c-tetragon-native`, `load_address=$1000`, `entrypoint=$59484`,
`decompressed_size=$779C9`, and sha256
`34389204110c8bc4972eb3f0a7f8d1b73779fde10f1a5e48eb36b7c8068ea65a`.

Follow-up diagnosis showed why the static C Tetragon clone was not enough to
prove this target either way. The real bootstrap copies an overlapping runtime
stub from `$6A` to `$100`; the bytes at runtime are produced by forward copy
semantics, not by a raw storage slice. Single-stepping the copied stub exposed
two simulator coverage requirements:

```text
storage bytes alone
  != overlapping runtime-copy bytes

native simulator execution
  -> needs explicit memory-mapped hardware read/write policy
  -> needs generated CCR semantics from the PDF-backed M68K KB
  -> should be reconciled against machine68k/oracle cases systematically
```

The immediate fix keeps policy-driven hardware reads/writes narrow and derives
CCR behavior from `knowledge/m68k_instructions.json`, which is regenerated from
`resources/M68000PM_AD_Rev_1_Programmers_Reference_Manual_1992.pdf` plus
curated parser assertions where PDF extraction fails. The concrete bug was an
operation-type heuristic: `MOVE16`, `ADDA`, `SUBA`, `BRA`, and `PVALID`
inherited condition-code formulas they do not have. The parser now
attaches formulas only when parsed condition-code effects prove a CPU CCR write,
and the C simulator consumes the generated formula metadata instead of guessing
from mnemonic shape.

The broader follow-up is to enumerate concrete simulator edge cases with
oracle-backed single-step tests, especially read-modify-write operands,
predecrement/postincrement updates, MOVEM/MOVEP, bitfield operations, stack
frame instructions, exception/trap paths, `NEG` CCR exactness, and CCR/SR
immediate logical operations.

Current rendered-source proof after the Conqueror/Damocles refresh:

```text
Rendered source round-trip:
  27/38 full-file exact
  10 content-exact only
  1 unsupported Mac OS source assembly target
  0 failures
```

The Magicland loader/file-backed gap is now identified but not materialized. The
target source contains a loader-owned asset-processing shape:

```asm
cmpi.l #1296843843,(a0)
bne.b  ...
movea.l a0,a3
move.l d1,d0
bsr.w  abs_0_000647F2
```

The implementation now records only the proven generic layer: C-owned
loader/file transfer facts prove the Magicland MD target's exact target-loader
file names, destination addresses, offsets, and sizes. That is evidence of
disk/file loading, not evidence of decompression. It must not emit
`target_loader_file` decompression events until C analysis can reconcile the
loaded bytes with a proven processor/decompressor call and replay that call from
known register and memory state.

This is not a framework codec. The framework does not know `MLDC` as a
decompressor. The long word is only corroborating evidence because it appears in
target code and matches exact bytes loaded from the source disk. Files that do
not match that target-owned acceptance check remain ordinary loader/file
transfers, not compressed-payload events.

The remaining generic proof before materialization is:

```text
C loader/file transfer fact
  -> exact source disk/container/file byte range
  -> exact runtime destination buffer
  -> proven target-owned processor/decompressor call using that buffer
  -> replay from proven register/memory state
  -> observed writes
  -> materialize asset_data only from those observed writes
```

An earlier implementation attempted to bridge this by recognizing the
Magicland-specific magic and statically scanning later direct calls. That was
rejected: it was target-specific framework knowledge, produced false positives,
and was pathologically slow. The current correct state is to keep the proven
file-transfer facts, leave the possible asset payload unresolved, and require C
analysis to replay the processor/decompressor before it reports decompression or
materialization.

This keeps Python as orchestration only: C must emit the media-transfer and
decompression facts, C must materialize any selected event, and Python writes
the durable child target/manifest records from those facts.

## Trailing Observations For Later Work

Magicland should not become the only shape of loader-owned input. The useful
generalization is a C-owned media-transfer fact:

```text
loader evidence
  -> source provenance: OS file, target loader file, logical disk offset, raw track/sector span
  -> destination buffer and byte count when known
  -> optional loader mechanism: OS call, TRAP wrapper, subroutine loader, direct disk hardware DMA
  -> consumers: decompressor execution, asset materialization, later data/code role analysis
```

Magicland is one producer of that fact because its target code installs TRAP
handlers, hashes filename strings, resolves a target-owned disk directory, then
loads bytes into caller buffers. NDOS targets such as demos/loaders may produce
the same kind of fact through a different mechanism: a first-stage trackdisk
load, followed by target-owned disk hardware reads with no file name and no
TRAP call. Those should still feed the same decompressor/materializer if the
source span and destination buffer are proven.

The long-term rule is: decompression should consume proven media-transfer
outputs plus a proven processing call, not target names, standalone magic-byte
recognition, or a "codec" guess. Magic constants inside target code can be
evidence during replay setup, but they are not a decompression classifier.

Several existing recovered facts are currently produced in render-lookup code.
That is legacy coupling: rendering should consume analysis facts, not discover
semantic loader/decompression provenance. Proposal 027 should avoid adding new
render-owned source provenance. Moving unrelated render-lookup producers back
into analysis is valuable post-proposal cleanup, but it should be handled as its
own refactor unless a fact is required for this decompression/materialization
path.

Precommit also exposed an intermittent `test_ir_policy_dll` access violation in
`test_platform_file_analysis_reports_cfg_for_certain_code`. The observed shape is
a Windows DLL crash during the Python-driven C analysis policy test, while
focused reruns and the full `src/tests/test_ir_policy_dll.py` module have passed
afterward. That makes it a reliability failure, not a proven 027 behavior
regression.

Post-proposal work should turn this into a deterministic repro before changing
behavior:

1. Run the failing module in a loop until the access violation reproduces, then
   record the exact seed/order/process lifetime.
2. Check DLL allocation ownership around `*_json_alloc`/free pairs, arena-backed
   strings copied into exported JSON, callback/error-buffer lifetimes, and any
   shared static state reused across tests.
3. Use CdbX64 or an equivalent Windows debugger once the loop reproduces, so the
   crash site is a C stack frame rather than a Python symptom.
4. Add the smallest regression test that exercises the lifetime bug once the C
   cause is known.

This should remain separate from 027 unless the crash is proven to corrupt or
misreport decompression/materialization facts.
