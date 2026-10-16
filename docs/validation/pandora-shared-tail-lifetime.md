# Shared-tail placement and lifetime assessment

This checkpoint follows the existing shared-tail inventory and snapshot lifecycle
contracts. It adds a canonical overlapping storage identity and stack-top name,
not a relocated image. Current proof identifiers and native results are in
`pandora-shared-tail-lifetime.json`. Historical Copperline observations are reused
with their original limits; no new gameplay route or whole-file reading ran.

## Placement conclusions

| Family | Relationship that must be preserved | Current independent-move status |
|---|---|---|
| Hit snapshot `$77D00..$78000` and palette input `$77FE0..$78000` | The palette identity is the last 32 bytes of the 768-byte snapshot. Preserve this alias at offset `$2E0` unless a semantic split is independently established. The snapshot requires chip RAM. | Refused. Both identities now expose `coordinated_source_placement`; the single-region planner cannot move either independently. A union move is also unimplemented and unproved. |
| Seeded reset packet | Its ascending source `$70000..$7CD00` and destination `$70028..$7CD28` cover the shared tail and cross framebuffer-family boundaries. Preserve the transfer's address/geometry relationship or replace it with an independently verified equivalent. | Not an independent allocation boundary. Descriptor-only retargeting of the hit snapshot would leave this covering writer behind. Extents remain conditional on inherited area-mode/ascending state. |
| Body snapshot `$7F0..$10F0` | Initial descriptor storage is disjoint from the hit snapshot. Its normal capture/restore/recapture path was previously observed. | Separate candidate, not certified storage: original low-memory ownership, complete alias inventory and asynchronous consumers remain unproved. |
| Palette output `$134C2..$134E2` and fractional components `$13462..$134C2` | Distinct A0/A2 roots and fixed per-color element relationships. Shared-tail input is a different identity. | Separate CPU-data candidates; no new all-consumer/stack/phase certificate. Do not infer a mandatory physical adjacency or permission to move from these bounds. |
| Framebuffer banks and initialized overlay rectangles | Initialized screen fetches and bounded rectangles do not consume the hit tail, but reset reuse crosses their nominal region boundaries. | No independent-move proof. Changed geometry, generic unclipped producers and DMA phases remain open. |
| Two-byte `audio_master_volume` | Existing native closure rewrites its five accepted instruction sites without carrying an address-register pointer through IRQ saves. Its padded backing lease is eight bytes. | The existing bounded CPU-only independent candidate remains separate. Current native-plan result is recorded in the ledger; previous runtime comparisons retain their scenario limits. No new executable was built or run here. |

"Must preserve" describes the original behavior and current proof obligations;
it does not rule out a later, fully justified phase-specific split. The covering
reset transfer is an access relationship, not a claim that the whole range is one
exclusive allocation. The original loaded payload also initially covers the
tail; its later workspace reuse is distinct from reading preserved input bytes.

## Stack and interrupt boundaries

Original instructions `$47A` and `$4BA` establish A7 at runtime `$10452`, now named
`runtime_supervisor_stack_top`. That is an address, not an allocation extent or
a whole-program SP invariant. Known palette helper footprints and the corrected
CLR predecrement trace are usable relative evidence. The older
`pandora-shared-tail-contract.json` simulator-limit paragraph was superseded by
the already-published scalar EA fix; its former expected failure now passes.
The ordinary render prefix reaches its first spliced helper with entry SP+10;
the helper leaves SP two bytes above its pre-BSR value and escapes the copied
view. Fade-out consumes all 16 shared WORDs before its first escape. Nothing in
these traces supplies the absolute SP or ancestry of an unknown palette caller.

New original-code tests exercise the IRQ dispatcher's COPER, VERTB, BLIT and
combined-request branches with an explicit modeled hardware frame and the
original no-op callback. The dispatcher saves **five LONG registers (20 bytes)**;
the callback JSR adds four. At callback entry the interrupted A0 is `8(SP)`,
and the hardware frame starts at `24(SP)`. All five saved registers and the
hardware frame are intact when the handler reaches RTE. The combined-request
fixture takes COPER first. This establishes layout and priority for those inputs,
not asynchronous interrupt admission, arbitrary callback preservation or a stack
lower bound. Gameplay VBL's additional saves put interrupted A0 at `60(SP)` in
the audio callee, as the prior analysis records.

Setup clears INTENA and then enables master, COPER and VERTB; it does not enable
BLIT. A raw BLIT request still has a dispatcher branch, so it must not be
mistaken for an enabled interrupt or a global DMA fence. Recognized callback-slot
assignments and known direct edges do not establish entry into the palette
wrappers. Absence of an incoming edge does not establish unreachability. The audio
callback continuation through native indexed jump `$4DC2A` remains unresolved;
mutable stream cursor/command bounds and all saved-frame observers are not closed.

## DMA and phase boundaries

Capture writes all 768 snapshot bytes; restore reads all 768. The last 32 bytes
cannot be treated as a spare palette allocation. Packet waits acknowledge a
preceding BLIT completion under the existing serialized-token assumptions.
Restore returns and clears logical flags without a final wait; the next packet
wait is the relevant fence. CPU border/text after a clear is not a software
completion fence. Warm restart explicitly polls BBUSY before reuse.

Existing Copperline observations witness an original hit capture and direct
restore, sampled tail retention, and a separate body recapture cycle. They do not
prove a second hit-family capture, all-byte exclusivity, or exclusion of the
palette reader. No further route probe is justified until a concrete loader,
producer or indirect/callback edge reaches a palette prefix. The new simulator
tests use explicit frames and MMIO shadows; they perform no DMA or IRQ scheduling.

The next discriminating evidence is the palette caller/producer and its phase
relative to capture/reset, followed by absolute stack ownership and complete
callback/descriptor-mode bounds. A joint placement implementation would also need
to preserve every alias and DMA consumer, reserve chip memory before loading,
and fence live DMA before switching addresses. Current native refusals remain
in force; no conditional guard or broad alias proof has been substituted.

## Reproduction

Run the resident service from the repository with:

```sh
make -j2
.venv/bin/python -m amiga_reversing.tools.disasm_server --host 127.0.0.1 --port 8123
```

Use `amiga_reversing.tools.restoration` `state`, then revision-bound
`query --kind memory_regions` or `memory_plan --request request.json`. The two
region IDs are `pandora_ui_snapshot_hit` and
`pandora_work_buffer_palette_input`. The existing
`amiga_reversing.tools.pandora_shared_tail_inventory OUTPUT.json` remains a
read-only wider inventory. Focused checks:

```sh
.venv/bin/python -m pytest -q tests/test_memory_regions.py tests/test_derived_artifact.py tests/test_memory_frame_arithmetic.py tests/test_memory_pointer_liveness.py
.venv/bin/python -m pytest -q tests/test_pandora_interrupt_frames.py tests/test_pandora_snapshot_guards.py tests/test_pandora_framebuffer_lifetime.py tests/test_pandora_render_order.py
src/build/m68k_c_unit_tests.exe
```

Full C/vasm verification and append-only journal acceptance use the canonical
`verify` and `review_batch` operations. The ledger binds their final receipt,
source hash, action IDs, native overlaps/refusals and validation counts. Original
input bytes, assets and prior manual/review history remain preserved.
