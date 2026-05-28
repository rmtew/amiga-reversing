# Proposal 027: Native Unpacker Execution Decompression

Status: Proposed.

This proposal explains two failed decompression cases, Damocles Tetragon
section 2 and Conqueror's embedded ByteKiller/CRUN-style decruncher. Both point
at the same architectural need: target-owned unpackers should be executed with
our M68K executor, not replaced by brittle inferred or hand-coded models.

## Checkpoint Index

- [ ] Problem Statement
- [ ] Tutorial: Existing Decompression Support
- [ ] Tutorial: The Damocles Tetragon Failure
- [ ] Tutorial: The Conqueror Relocated Decruncher
- [ ] Principle: The Target-Owned Unpacker Is The Spec
- [ ] Tutorial: Executor-Based Native Unpacking
- [ ] Validation Gates
- [ ] Compatibility With Existing Working Targets
- [ ] Proposed Implementation Slices
- [ ] Acceptance Criteria
- [ ] Non-Goals

## Problem Statement

We currently have at least two ways to arrive at misleading decompression state:

1. A recognized unpacker can be materialized by a hand-coded clone that does not
   match the native target-owned stub.
2. A relocated unpacker can be present in the binary, but not surfaced as a
   decompressed child because we only render the original packed bytes.

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

The second is different. It materializes bytes, but the configured entrypoint is
not credible code:

```asm
abs_0_00059484:
    or.b d0,(a2)+
    andi.w #139,$6311(a0)
    dc.b $43,$0B,$01,$01,$0C,$00,$44,$00
```

That is a failed materialization, not a disassembler problem. The output is
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
they produce a byte image whose entrypoint fails code validation.

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

## Principle: The Target-Owned Unpacker Is The Spec

For target-owned unpackers, the native stub is the most precise specification.
It already encodes the real variant details. A handwritten C clone or an
external XFD routine is a derived interpretation and can drift.

The proposed rule:

```text
When an unpacker routine is present in the target, execute that routine unless
there is a stronger reason not to.
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
runtime unpacker.

## Tutorial: Executor-Based Native Unpacking

The reliable path is to add a native unpacker materializer that uses our M68K
executor. It should cover both marker-recognized unpackers and relocated
runtime-copy unpackers.

### Step 1: Find The Unpacker Event

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
  "copied_stub_runtime_address": 4,
  "decompressor_runtime_address": 64,
  "load_address": 1024,
  "entrypoint": 1024
}
```

These events should mean "candidate native unpacker", not "trusted
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

The executor should observe writes, not assume every byte between `$1000` and
the largest touched address is meaningful code.

### Step 4: Run With Bounded Stops

The run should stop on one of a small number of meaningful conditions:

```text
final PC == known entrypoint
  -> candidate success, validate output

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

### Step 5: Materialize From Observed Writes

The output range should be derived from runtime writes and final transfer
evidence:

```text
observed writes
  -> merge contiguous payload writes
  -> choose range containing known entrypoint
  -> materialize that range
  -> validate as code-bearing payload
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

This avoids declaring an enormous memory span as a primary program merely
because the stub touched or scanned it. It also avoids using the original file
bytes at the destination address when the real payload is only produced at
runtime.

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
recognize marker or handoff
  -> execute native code
  -> observe writes
  -> validate payload
  -> materialize
```

Custom C unpackers and XFD-derived implementations then become optional
accelerators. They are acceptable only when they are tested against executor
output for real fixtures or when no target-owned code is available.

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
  "observed_write_ranges": [
    {"start": 4096, "end": 497097}
  ]
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
    validate_entrypoint();
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
payload_role == primary_program
validation == valid
```

Invalid or unresolved native execution should become parent review state, not a
raw child containing misleading bytes.

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
```

The desired end state is valid materialized children for real code-bearing
outputs, not merely blockers.

## Acceptance Criteria

- Damocles section 1 still materializes the known valid payload.
- Damocles section 2 is attempted through native executor materialization.
- If section 2 materializes, `$59484` validates as reachable M68K code.
- If section 2 does not materialize, diagnostics identify the failed native
  execution condition.
- Conqueror is attempted through native executor materialization.
- If Conqueror materializes, output has `load_address=$400`,
  `entrypoint=$400`, and a size derived from observed writes/header evidence.
- Import never creates a primary-program child from bytes that fail entrypoint
  validation.
- Existing non-Tetragon decompression paths continue to pass their current
  fixtures.
- The C Tetragon clone and XFD-derived routines are no longer the only source
  of truth for target-owned unpackers.

## Non-Goals

- Do not remove all static decompressors.
- Do not require a full Amiga emulator.
- Do not accept byte-exact round-trip as proof of decompression correctness.
- Do not hardcode Damocles- or Conqueror-only output bytes or hashes as the
  solution.
