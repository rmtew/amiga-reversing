# Pandora relocation: relative frame step

The approved continuation implements native relative frame-prefix interpretation
and fixes signed address-source arithmetic in the shared generated simulator.
It does not complete the proposed keyboard move from `$397C..$39FC` to
`$C7F000..$C7F080`. Native build still refuses five obligations; no changed-layout
Pandora payload, reservation or gameplay run exists.

Balanced stack saves/restores and direct calls now support a positive borrowed
caller fixture. Corrupt return slots, unknown aliases, SP replacement/escape,
unmodeled exceptions and conflicting joins refuse. Queries explicitly distinguish
relative stack effects from an absolute SP. CALL/RTS effects and protected PC slot
widths consume generated CPU stack data. ADDA/SUBA WORD extension consumes the
existing KB property; unsigned pointer arithmetic removes signed-overflow UB.
Linux test executable isolation now preserves its `$ORIGIN` shared-library lookup.

## Current target evidence

Fresh listing service: `http://127.0.0.1:8123/`, Pandora path
`/amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.
It is loopback only. The service uses the rebuilt native backend; owned Copperline
oracle processes exit after testing.

| Root source offset | First refusal | Reason |
| --- | --- | --- |
| `$690` | `$6AE`, A6 camera-state write | Unknown address/frame alias |
| `$86A` | `$882`, A6 last-key write | Unknown address/frame alias |
| `$2D2A` | `$2D58`, RTS | Unproved borrowed caller frame |
| `$9062` | `$90BE`, A6 modal-state write | Unknown address/frame alias |
| `$9C76` | `$464`, MOVE to SR | Unmodeled exception/supervisor transition |

The direct `$2704` reference and `$9F58` reset cursor remain closed. The plan
contains two supported rewrites and five open obligations; the verified build
returns a refusal and writes no artifact. Relative balance does not prove absolute
stack bounds, disjoint A6/object addresses or interrupt preservation. Proposal 044
records these requirements and the gates for any future conditional contract.

Expanded source C and independent vasm each reproduce all **376,832** original
bytes, SHA256 `70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
Fresh service receipt:
`72dc63468ced439280f34b87a01dfc877e67e37307806bc74b6995d3f87ecefb`.
Expanded source SHA256 remains
`b5c29658451d7a775aadc1cd574dcee25528bbe477362372b0fb47abfd1b913d`.
The actual prior compact ZIP was independently reassembled with the current C
backend and vasm; every byte matches. Its source SHA256 remains
`974bd68621c39c2a94a9bc457cd5bd6e5bb74ecab0e3d2c964b7beb6e20b306c`.
No target actions, review decisions or asset bytes changed in this continuation.

## Reproduction and limits

```sh
cd /workspace/amiga-reversing
make -j4
COPPERLINE_BINARY=/workspace/copperline-assessment/squashfs-root/usr/bin/copperline \
COPPERLINE_ROM=/path/to/legal/kick13.rom .venv/bin/python -m pytest \
  tests/test_memory_regions.py tests/test_memory_frame_arithmetic.py \
  src/tests/test_m68k_simulator_abstract.py \
  src/tests/test_generate_c99_simulator_subset.py tests/test_derived_artifact.py \
  tests/test_copperline_control.py tests/test_copperline_runtime.py \
  tests/test_copperline_session.py -q
```

Result: **181 passed** with actual Copperline enabled. Nine vasm-encoded ADDA/SUBA
cases agree with the real emulator, including source width and preserved SR.
Unknown/source-pointer and signed/wrapping boundaries have conservative tests.
These are synthetic CPU oracles; the earlier original-layout eight-phase keyboard
baseline remains separate evidence and was not a relocated run.

Full native tests retain the same two failures demonstrated on clean `7896c865`:
pointer-table pointee propagation and unknown decompression identification. No
new full-suite failure appeared. The generator reproduces its committed output.
Independent review passes the relative-frame/simulator step with final file hashes.

Bounded local evidence is under `.runtime-state/pandora-analysis/keyboard-relocation/`:
`tests-frame-final.log`, `native-frame-tests.log`,
`independent-frame-prefix-review.json`, `frame-prefix-service-{state,facts,plan,verification}.json`,
`frame-prefix-build-refusal.json`, and `frame-prefix-compact-verification.json`.
