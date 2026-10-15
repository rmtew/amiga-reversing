# Framework defect review, 2026-10-15

This is a bounded review of existing failure evidence, current source and small
isolated reproductions. It is not a new whole-suite run or a count of every
unimplemented instruction. Pandora's relocation and hardware contracts are
separate from framework bugs.

## Fixed in the current concrete-executor slice

`src/m68k_simulator.c` omitted the existing metadata-driven predecrement
preparation in several scalar operation paths. `CLR.W -(A7)` therefore wrote at
the old SP. The shared helper now runs before access for clear, condition stores,
logic, unary, shift/rotate, compare/test, multiply/divide and test-and-set paths.
Read/modify/write computes at the prepared address and writes back before the
single existing postincrement. TAS now also applies that final register update.
No instruction metadata, original target bytes or mnemonic-specific exception
was added. A7 BYTE stepping reuses the existing shared update rule.

`src/tests/test_m68k_simulator_ea_updates.py` covers all CLR sizes/address registers
in indirect/predecrement/postincrement modes, condition stores, related RMW and
read-only sources, memory neighbours, CCR, single-write ranges and rejected
wrapped accesses. Its six tests pass with 177 subtests. The wider simulator,
generator, MOVEQ, abstract, palette and render run passes 89 tests and 1175
subtests; the final six wrapped-access vectors were added and passed afterward.
The targeted native simulator suite passes all 30 cases. Changed C passes the
repository style checker. Nine representative CLR/Scc/RMW and alias-reproducer
encodings also match independent vasm.

The strict xfail in `tests/test_pandora_snapshot_guards.py` is removed: the original
rendering prefix now passes. It still reaches the modeled spliced return, with
SP `$900A` before the first render-wrapper call and `$900C` after the helper.
The fade-out counterpart has SP `$9000` then `$9002`. Both still build the return
PC from the low return WORD and following `$C0DE` WORD. The corrected stack
update changes evidence validity, not the palette control-flow conclusion.
Neither ordinary palette-entry reachability nor exclusive shared-tail ownership
is established. Concrete prefix evidence is distinct from abstract propagation.

## Confirmed remaining defects, in recommended order

1. **Two-memory-operand scheduling with the same address register.** The concrete
   executor reads both CMPM operands before applying their individual updates;
   extended arithmetic prepares both predecrements before either read. Isolated
   current-native reproductions: `cmpm.w (a0)+,(a0)+`, A0=32, WORDs 1/2, SR=$A710,
   ends A0=36 but CCR=$14 instead of $10. `addx.w -(a0),-(a0)`, A0=36, WORDs 2/1
   at 32/34, X=0, writes 4 instead of 3 at 32. See the compare and extend-arithmetic
   branches in `src/m68k_simulator.c`. This requires sequential operand access
   scheduling, not another CLR rule. Do not use such aliasing instruction traces
   as proof until fixed. Current Pandora CLR/scan witnesses do not use them.

2. **Abstract scalar auto-update semantics remain incomplete.** The concrete fix
   does not fix the abstract writer. With original bytes `4267` in a 64-byte
   section and abstract A7=section-pointer(32),
   `m68k_simulate_one_abstract_for_cpu` reports next A7=32 with no diagnostic;
   architectural predecrement requires 30. See `sim_write_operand_by_metadata`
   and the abstract CLEAR branch in `src/m68k_simulator.c`. Do not treat abstract
   stack addresses around these accesses as exact. A follow-up should define
   operand-access sequencing across abstract reads, writes and updates, including
   aliasing; it should not patch Pandora field facts to compensate.

3. **Static pointer-table pointee propagation baseline failure.** Existing native
   test `facts_v2_render_asm_source_propagates_pointer_table_pointee_type` in
   `src/test_m68k_ir.c` fails its `typed != NULL` assertion: after LEA table,
   `(A0)+ -> D2 -> A5`, the WORD field read at source offset 10 lacks the expected
   `world_y` recovered typed access. The table's pointee contract is present.
   The missing fact is confirmed; the deeper cause between table-load provenance,
   loop/guard merging and typed transfer is not yet isolated. The runtime-app-slot
   sibling test passes, so this is not evidence all pointer typing fails.
   `src/m68k_analysis_render_lookup.c` contains the relevant table-origin and
   typed-register transfer paths. Impact is missing source names/types, not a
   demonstrated execution or byte-reproduction failure. The latest world-pointer
   inventory independently exposes only 3 symbolic and 93 unresolved nonzero
   initial structured-query references; that limitation is retained rather than
   hand-mapped. Resumed source inspection finds those operands rendered
   symbolically (for example source $3012 is `dc.l world_object_megabio_feed`),
   while its listing row has no `pointer_resolution` member. Thus structured
   export completeness is a separate gap; unresolved query results do not mean
   the source is numeric or that the rendered expression supplies durable
   target-identity facts.

4. **Linux native decompression identity hashing.** Existing native test
   `decompression_identify_reports_unknown_payload_without_failure` in
   `src/test_platform_decompression.c` fails at the provider SHA256 length check
   (expected 64, got 0). `file_sha256_hex_local` in
   `src/platform_file_decompression.c` uses BCrypt on Windows and returns -1 with
   an empty hash on other systems; `fill_provider_metadata_local` ignores failure.
   The fixture additionally names a Windows-style Ancient executable/path, which
   is not a configured Linux provider. Unknown-input recognition can return
   normally while provider/source identity is absent. Fix host hashing and
   provider/fixture configuration together before trusting this native identity
   path. Current Pandora original-image and asset checks use Python SHA256 and
   are independently intact. No provider was installed or changed here.

The two named native baseline failures above reuse the recorded 807-pass/two-fail
run in `.runtime-state/pandora-analysis/moveq-render-lifecycle/native-tests.log`.
They were not hidden by skips, nor was the whole suite rerun just to recount them.
The current native run was restricted to the simulator suite.

## Limitations and gaps that are not established bugs

- The default Python baseline's Mac test needs absent
  `resources/platform_macos/MPW-GM.img.bin`; it fails before the intended assertion.
  Native-backend, browser/CDP, real-Copperline and full-reproduction skips are
  explicit build/input/opt-in gates, not passes. See `docs/linux-baseline-2026-10.md`,
  `tests/test_web_e2e_cdp.py`, `tests/test_full_reproduction_integration.py` and
  `tests/test_memory_frame_arithmetic.py`.
- `src/tests/test_m68k_simulator_oracle.py` marks Dn PACK/UNPK cases unsupported
  by machine68k; direct concrete tests cover them. An oracle limitation does not
  establish our implementation is wrong. No independent machine68k oracle was
  installed in this environment for the current slice.
- The historical source `$998A` incorrect-field report must not be repeated as
  currently confirmed: the current generated idle load identifies
  `world_position_state_record_state_node_ptr`, followed by the node clock reset.
  Broader interior-pointer propagation still needs conservative review.
- `$77FE0..$78000` shared hit/palette ownership, absolute caller/IRQ stack aliases,
  callbacks, blitter/DMA lifetimes, positive-X node/player-tail overlap, unknown
  helper effects and unchecked game selectors are unresolved Pandora contracts.
  They are not proven emulator defects. A historical timeout at `$27E0` was a
  wrong probe entry; the corrected `$27EA` body cycle succeeds in Copperline.

The installed Copperline is the checksum-verified official 1.0.0 stable release,
not an obsolete pre-1.0 build. Current main commits do not, by themselves, explain
these simulator defects. Exact executable/version/hash evidence and the release
link are in `docs/copperline-runtime.md`.
